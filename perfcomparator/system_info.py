"""Inventaire système portable, enrichi sans dépendance native."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import psutil

from .apple_models import apple_model_year
from .models import EnvironmentSnapshot, ProcessLoad, ReadinessSnapshot, SystemSnapshot


@dataclass(frozen=True)
class MachineIdentity:
    """Identité matérielle non unique, sans numéro de série ni UUID."""

    manufacturer: str | None
    product_name: str
    model_identifier: str
    product_sku: str | None


def _command(*command: str, timeout: float = 10) -> str:
    try:
        return subprocess.check_output(command, text=True, timeout=timeout).strip()
    except OSError, subprocess.SubprocessError:
        return ""


def _sysctl(name: str) -> str:
    return _command("sysctl", "-n", name)


def _memory_bytes() -> int | None:
    if sys.platform == "darwin":
        value = _sysctl("hw.memsize")
        return int(value) if value.isdigit() and int(value) > 0 else None
    if sys.platform.startswith("linux"):
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            return pages * page_size if pages > 0 and page_size > 0 else None
        except OSError, ValueError:
            return None
    if sys.platform == "win32":
        output = _command(
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory",
        )
        return int(output) if output.isdigit() and int(output) > 0 else None
    return None


def _hardware_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip("\x00\n ")
    except OSError:
        return ""


def _product_sku(value: object) -> str | None:
    """Écarte les SKU absents ou les valeurs génériques laissées par le fabricant."""
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())
    if normalized.casefold() in {
        "",
        "default string",
        "none",
        "not applicable",
        "not specified",
        "system product name",
        "to be filled by o.e.m.",
        "unknown",
    }:
        return None
    return normalized


def _machine_identity() -> MachineIdentity:
    if sys.platform == "darwin":
        output = _command("system_profiler", "SPHardwareDataType", "-json")
        try:
            item = json.loads(output).get("SPHardwareDataType", [])[0]
        except AttributeError, IndexError, json.JSONDecodeError, TypeError:
            item = {}
        if not isinstance(item, dict):
            item = {}
        product_name = item.get("machine_name")
        model = item.get("machine_model") or _sysctl("hw.model")
        product_sku = next(
            (
                _product_sku(item.get(field))
                for field in ("model_number", "part_number", "product_sku")
                if _product_sku(item.get(field)) is not None
            ),
            None,
        )
        return MachineIdentity(
            manufacturer="Apple",
            product_name=product_name if isinstance(product_name, str) else "Mac",
            model_identifier=model if isinstance(model, str) and model else "Mac",
            product_sku=product_sku,
        )
    if sys.platform == "win32":
        output = _command(
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_ComputerSystem | "
            "Select-Object Manufacturer,Model,SystemSKUNumber | ConvertTo-Json -Compress",
        )
        try:
            item = json.loads(output)
        except json.JSONDecodeError, TypeError:
            item = {}
        if not isinstance(item, dict):
            item = {}
        manufacturer = item.get("Manufacturer")
        model = item.get("Model")
        return MachineIdentity(
            manufacturer=manufacturer if isinstance(manufacturer, str) else None,
            product_name=model if isinstance(model, str) and model else "PC Windows",
            model_identifier=model if isinstance(model, str) and model else "inconnu",
            product_sku=_product_sku(item.get("SystemSKUNumber")),
        )
    manufacturer = _hardware_text("/sys/devices/virtual/dmi/id/sys_vendor") or None
    product_name = _hardware_text("/sys/devices/virtual/dmi/id/product_name")
    if not product_name:
        product_name = _hardware_text("/sys/firmware/devicetree/base/model")
    product_name = product_name or "Machine Linux"
    return MachineIdentity(
        manufacturer=manufacturer,
        product_name=product_name,
        model_identifier=product_name,
        product_sku=_product_sku(_hardware_text("/sys/devices/virtual/dmi/id/product_sku")),
    )


def _processor() -> str:
    if sys.platform == "darwin":
        return _sysctl("machdep.cpu.brand_string") or platform.processor() or "inconnu"
    if sys.platform == "win32":
        return platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "inconnu")
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith(("model name", "hardware")):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "inconnu"


def _physical_cpu_count() -> int | None:
    if sys.platform == "darwin":
        value = _sysctl("hw.physicalcpu")
        return int(value) if value.isdigit() and int(value) > 0 else None
    if sys.platform == "win32":
        value = _command(
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum",
        )
        return int(value) if value.isdigit() and int(value) > 0 else None
    try:
        physical_and_core: set[tuple[str, str]] = set()
        physical = core = "0"
        lines = Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines() + [""]
        for line in lines:
            if line.startswith("physical id"):
                physical = line.split(":", 1)[1].strip()
            elif line.startswith("core id"):
                core = line.split(":", 1)[1].strip()
            elif not line:
                physical_and_core.add((physical, core))
        return len(physical_and_core) or None
    except OSError:
        return None


def _gpu_devices() -> list[str]:
    if sys.platform == "darwin":
        output = _command("system_profiler", "SPDisplaysDataType", "-json")
        try:
            payload = json.loads(output)
            names = [item.get("sppci_model") for item in payload.get("SPDisplaysDataType", [])]
            return [name for name in names if isinstance(name, str)]
        except json.JSONDecodeError, AttributeError:
            return []
    if sys.platform == "win32":
        output = _command(
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
        )
        return [line.strip() for line in output.splitlines() if line.strip()]
    output = _command("lspci")
    return [
        line.split(": ", 1)[-1] for line in output.splitlines() if "VGA" in line or "3D" in line
    ]


def system_snapshot(work_dir: Path | str = ".") -> SystemSnapshot:
    """Capture le matériel, l'OS et l'interpréteur utilisés pour le rapport."""
    usage = shutil.disk_usage(Path(work_dir).resolve())
    identity = _machine_identity()
    return SystemSnapshot(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        model=identity.model_identifier,
        manufacturer=identity.manufacturer,
        product_name=identity.product_name,
        model_year=apple_model_year(identity.model_identifier, identity.product_sku),
        product_sku=identity.product_sku,
        processor=_processor(),
        physical_cpu_count=_physical_cpu_count(),
        logical_cpu_count=os.cpu_count() or 1,
        memory_bytes=_memory_bytes(),
        gpu_devices=_gpu_devices(),
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        python_executable=sys.executable,
        disk_total_bytes=usage.total,
        disk_free_bytes=usage.free,
    )


def _linux_temperature() -> float | None:
    temperatures: list[float] = []
    for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            value = float(path.read_text(encoding="utf-8").strip())
        except OSError, ValueError:
            continue
        celsius = value / 1_000 if value > 1_000 else value
        if -20 <= celsius <= 150:
            temperatures.append(celsius)
    return max(temperatures) if temperatures else None


def environment_snapshot() -> EnvironmentSnapshot:
    """Capture au mieux alimentation et pression thermique sans privilège."""
    if sys.platform == "darwin":
        battery = _command("pmset", "-g", "batt")
        thermal = _command("pmset", "-g", "therm")
        power_match = re.search(r"Now drawing from '([^']+)'", battery)
        limit_match = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", thermal)
        return EnvironmentSnapshot(
            power_source=power_match.group(1) if power_match else None,
            thermal_limit_percent=int(limit_match.group(1)) if limit_match else None,
        )
    if sys.platform.startswith("linux"):
        power_source = None
        for path in Path("/sys/class/power_supply").glob("*/online"):
            try:
                if path.read_text(encoding="utf-8").strip() == "1":
                    power_source = path.parent.name
                    break
            except OSError:
                continue
        return EnvironmentSnapshot(
            power_source=power_source,
            temperature_celsius=_linux_temperature(),
        )
    if sys.platform == "win32":
        battery = _command(
            "powershell",
            "-NoProfile",
            "-Command",
            "$b=Get-CimInstance Win32_Battery; "
            "if ($b -and $b.BatteryStatus -eq 1) {'Battery Power'} else {'AC Power'}",
        )
        return EnvironmentSnapshot(power_source=battery or None)
    return EnvironmentSnapshot()


def machine_readiness(sample_seconds: float = 1.0, process_limit: int = 5) -> ReadinessSnapshot:
    """Estime si la machine est suffisamment au repos pour commencer une campagne."""
    processes: list[psutil.Process] = []
    current_pid = os.getpid()
    for process in psutil.process_iter(["pid", "name"]):
        # Windows expose le pseudo-processus « System Idle Process » avec le PID 0.
        # Il ne représente pas une charge concurrente et ne doit pas être archivé.
        if process.pid <= 0 or process.pid == current_pid:
            continue
        try:
            process.cpu_percent(None)
        except psutil.AccessDenied, psutil.NoSuchProcess:
            continue
        processes.append(process)
    psutil.cpu_percent(None)
    time.sleep(sample_seconds)
    cpu_percent = psutil.cpu_percent(None)
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    observations: list[ProcessLoad] = []
    for process in processes:
        try:
            cpu = process.cpu_percent(None)
            memory_percent = process.memory_percent()
            name = process.name()
        except psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess:
            continue
        if cpu >= 2 or memory_percent >= 3:
            observations.append(
                ProcessLoad(
                    pid=process.pid,
                    name=name,
                    cpu_percent=round(cpu, 1),
                    memory_percent=round(memory_percent, 1),
                )
            )
    observations.sort(key=lambda item: (item.cpu_percent, item.memory_percent), reverse=True)
    observations = observations[:process_limit]
    warnings: list[str] = []
    if cpu_percent >= 15:
        warnings.append(
            f"Charge CPU initiale élevée ({cpu_percent:.1f} %) ; fermer les tâches actives "
            "et attendre le retour au repos."
        )
    if memory.available / memory.total < 0.20:
        warnings.append(
            f"Mémoire disponible faible ({memory.available / memory.total * 100:.1f} %) ; "
            "fermer les applications lourdes."
        )
    if swap.percent >= 10:
        warnings.append(
            f"Mémoire d'échange déjà utilisée à {swap.percent:.1f} % ; les résultats de "
            "mémoire et de stockage peuvent être perturbés."
        )
    busy = [item for item in observations if item.cpu_percent >= 10]
    if busy:
        names = ", ".join(f"{item.name} ({item.cpu_percent:.0f} %)" for item in busy[:3])
        warnings.append(f"Processus actifs détectés : {names}.")
    return ReadinessSnapshot(
        sample_seconds=sample_seconds,
        cpu_percent=round(cpu_percent, 1),
        memory_available_percent=round(memory.available / memory.total * 100, 1),
        memory_available_bytes=memory.available,
        swap_percent=round(swap.percent, 1),
        active_processes=observations,
        warnings=warnings,
        suitable=not warnings,
    )
