"""Catalogue et implémentation des benchmarks multiplateformes."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sqlite3
import tempfile
import zlib
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from .gpu_benchmarks import gpu_compute_fp32, gpu_image_filter, gpu_memory, gpu_raster
from .models import BenchmarkResult

MIB = 1_048_576

REFERENCE_LIBRARY = {
    "numerical-recipes": (
        "Press, W. H. et al., Numerical Recipes: The Art of Scientific Computing, "
        "3e éd., Cambridge University Press, 2007, chap. 7."
    ),
    "ieee-754": (
        "IEEE, IEEE 754-2019 — Standard for Floating-Point Arithmetic, "
        "https://standards.ieee.org/ieee/754/6210/"
    ),
    "nist-sha": (
        "NIST, FIPS PUB 180-4 — Secure Hash Standard, 2015, https://doi.org/10.6028/NIST.FIPS.180-4"
    ),
    "rfc-zlib": (
        "Deutsch, L. P., RFC 1950 — ZLIB Compressed Data Format Specification, 1996, "
        "https://www.rfc-editor.org/rfc/rfc1950"
    ),
    "rfc-deflate": (
        "Deutsch, L. P., RFC 1951 — DEFLATE Compressed Data Format Specification, 1996, "
        "https://www.rfc-editor.org/rfc/rfc1951"
    ),
    "amdahl": (
        "Amdahl, G. M., Validity of the Single Processor Approach to Achieving Large "
        "Scale Computing Capabilities, AFIPS 1967, https://doi.org/10.1145/1465482.1465560"
    ),
    "python-processes": (
        "Python Software Foundation, Process-based parallelism, "
        "https://docs.python.org/3.14/library/multiprocessing.html"
    ),
    "stream": (
        "McCalpin, J. D., Memory Bandwidth and Machine Balance in Current High Performance "
        "Computers, IEEE TCCA Newsletter, 1995, https://www.cs.virginia.edu/stream/ref.html"
    ),
    "snia": (
        "SNIA, Solid State Storage Performance Test Specification v2.0.2, 2020, "
        "https://www.snia.org/solid-state-sss"
    ),
    "rfc-json": (
        "Bray, T. (éd.), RFC 8259 — The JavaScript Object Notation Data Interchange "
        "Format, 2017, https://www.rfc-editor.org/rfc/rfc8259"
    ),
    "sqlite": (
        "SQLite Consortium, Transaction documentation, https://www.sqlite.org/lang_transaction.html"
    ),
    "pep-418": (
        "Langa, Ł., PEP 418 — Add monotonic time, performance counter, and process time "
        "functions, 2012, https://peps.python.org/pep-0418/"
    ),
    "webgpu": ("W3C GPU for the Web Community Group, WebGPU, https://gpuweb.github.io/gpuweb/"),
    "wgsl": (
        "W3C GPU for the Web Community Group, WebGPU Shading Language, https://www.w3.org/TR/WGSL/"
    ),
    "wgpu-py": "PyGfx, wgpu-py documentation, https://wgpu-py.readthedocs.io/",
}


@dataclass(frozen=True)
class BenchmarkDocumentation:
    """Protocole et réserves d'interprétation d'une mesure."""

    methodology: str
    limitations: str
    reference_ids: tuple[str, ...]
    unit: str


BENCHMARK_DOCUMENTATION = {
    "cpu.integer": BenchmarkDocumentation(
        "Boucle mono-processus combinant une récurrence congruentielle 32 bits, un décalage "
        "XOR et un masque. Le score compte les mises à jour d'état par seconde.",
        "Mesure surtout l'interpréteur CPython et les entiers Python ; ce n'est pas un test de "
        "qualité du générateur pseudo-aléatoire.",
        ("numerical-recipes", "pep-418"),
        "Mop/s",
    ),
    "cpu.float": BenchmarkDocumentation(
        "Boucle mono-processus appliquant sin et sqrt à des nombres en double précision. Le "
        "score compte les couples d'opérations par seconde.",
        "Inclut le coût des appels Python et de la bibliothèque mathématique du système ; les "
        "résultats ne représentent pas les FLOPS vectoriels maximaux.",
        ("ieee-754", "pep-418"),
        "Mop/s",
    ),
    "cpu.hash": BenchmarkDocumentation(
        "Hachage SHA-256 répété d'un bloc déterministe de 1 Mio ; le score est le débit des "
        "octets d'entrée en Mio/s.",
        "Peut utiliser une implémentation native ou des instructions matérielles ; le score "
        "caractérise l'ensemble CPython et bibliothèque cryptographique.",
        ("nist-sha", "pep-418"),
        "Mio/s",
    ),
    "cpu.compression": BenchmarkDocumentation(
        "Compression zlib niveau 6 répétée d'un bloc pseudo-aléatoire déterministe de 1 Mio ; "
        "le score est le débit d'entrée.",
        "Le bloc est peu compressible et ne représente pas tous les fichiers réels ; le débit "
        "dépend de la version native de zlib.",
        ("rfc-zlib", "rfc-deflate", "pep-418"),
        "Mio/s",
    ),
    "cpu.multicore": BenchmarkDocumentation(
        "La charge entière de cpu.integer est exécutée simultanément dans autant de processus "
        "que de processeurs logiques ; le score agrège leurs mises à jour.",
        "Le nombre de processeurs logiques n'est pas le nombre de cœurs physiques. La montée en "
        "charge dépend de l'ordonnanceur, du refroidissement et des coûts interprocessus.",
        ("amdahl", "python-processes", "pep-418"),
        "Mop/s",
    ),
    "memory.copy": BenchmarkDocumentation(
        "Copie répétée d'un tampon déterministe vers un tampon préalloué de même taille. Un "
        "octet copié compte une fois dans le débit en Mio/s.",
        "Test inspiré du noyau Copy de STREAM mais non conforme à STREAM ; selon le profil, le "
        "tampon peut tenir partiellement dans les caches du processeur.",
        ("stream", "pep-418"),
        "Mio/s",
    ),
    "storage.write": BenchmarkDocumentation(
        "Écriture séquentielle non tamponnée par Python d'un fichier temporaire, puis fsync. Le "
        "temps inclut la synchronisation demandée au système.",
        "Ce test court n'effectue ni préconditionnement ni mesure d'état stable SNIA ; caches, "
        "compression et politique du système de fichiers peuvent influer.",
        ("snia", "pep-418"),
        "Mio/s",
    ),
    "storage.read": BenchmarkDocumentation(
        "Prépare puis lit séquentiellement un fichier temporaire par blocs de 1 Mio. Le score "
        "divise sa taille par le temps de lecture.",
        "Le cache de pages du système peut servir une partie ou la totalité des données ; ce "
        "score n'est donc pas toujours le débit physique du support.",
        ("snia", "pep-418"),
        "Mio/s",
    ),
    "storage.random-read": BenchmarkDocumentation(
        "Lectures synchrones de blocs de 4 Kio, à profondeur de file 1 et positions déterministes. "
        "Le score est le nombre d'opérations par seconde.",
        "Le fichier est préparé juste avant la mesure et peut rester en cache ; ce protocole "
        "allégé n'est pas un test de conformité SNIA.",
        ("snia", "pep-418"),
        "IOPS",
    ),
    "storage.random-write": BenchmarkDocumentation(
        "Écritures synchrones de blocs de 4 Kio, à profondeur de file 1 et positions "
        "déterministes, suivies d'un fsync. Le score est exprimé en IOPS.",
        "L'endurance, l'état stable, le remplissage préalable et les différentes profondeurs "
        "de file ne sont pas couverts.",
        ("snia", "pep-418"),
        "IOPS",
    ),
    "application.json": BenchmarkDocumentation(
        "Un cycle désérialise puis sérialise un document déterministe de 1 000 objets avec le "
        "module json de la bibliothèque standard.",
        "Le document synthétique ne couvre ni toutes les formes JSON ni les bibliothèques tierces "
        "optimisées.",
        ("rfc-json", "pep-418"),
        "cycles/s",
    ),
    "application.sqlite": BenchmarkDocumentation(
        "Crée une base SQLite en mode WAL, insère toutes les lignes dans une transaction, valide "
        "puis exécute une agrégation filtrée.",
        "Le score mélange CPU et stockage et ne modélise ni concurrence, ni base durable, ni "
        "charge décisionnelle complexe.",
        ("sqlite", "pep-418"),
        "lignes/s",
    ),
    "gpu.compute-fp32": BenchmarkDocumentation(
        "Un shader WGSL applique 128 multiplications-additions à 262 144 valeurs FP32 ; "
        "le score compte 256 opérations par valeur.",
        "N'évalue ni les unités matricielles spécialisées, ni l'IA, ni le calcul FP64.",
        ("webgpu", "wgsl", "wgpu-py", "ieee-754"),
        "GFLOP/s",
    ),
    "gpu.memory": BenchmarkDocumentation(
        "Un shader WGSL copie un tampon GPU ; le débit compte les octets lus et écrits.",
        "Les caches et la mémoire unifiée peuvent influencer le résultat.",
        ("webgpu", "wgsl", "wgpu-py"),
        "Gio/s",
    ),
    "gpu.image-filter": BenchmarkDocumentation(
        "Un shader WGSL applique hors écran un filtre pondéré à cinq pixels voisins.",
        "Ne représente pas les codecs vidéo ni un moteur photo complet.",
        ("webgpu", "wgsl", "wgpu-py"),
        "Mpixel/s",
    ),
    "gpu.raster": BenchmarkDocumentation(
        "Un pipeline WGSL remplit répétitivement une texture RGBA8 hors écran.",
        "Mesure un remplissage simple, sans géométrie complexe ni ray tracing.",
        ("webgpu", "wgsl", "wgpu-py"),
        "Mpixel/s",
    ),
}


@dataclass(frozen=True)
class BenchmarkProfile:
    """Durées et volumes cohérents appliqués à toute la suite."""

    name: str
    duration_seconds: float
    memory_size_bytes: int
    disk_size_bytes: int
    random_operations: int
    sqlite_rows: int


PROFILES = {
    "quick": BenchmarkProfile("quick", 0.20, 8 * MIB, 16 * MIB, 512, 2_000),
    "standard": BenchmarkProfile("standard", 1.00, 64 * MIB, 128 * MIB, 4_096, 20_000),
    "thorough": BenchmarkProfile("thorough", 3.00, 256 * MIB, 512 * MIB, 16_384, 100_000),
}


@dataclass(frozen=True)
class BenchmarkContext:
    """Paramètres partagés, injectables dans les tests."""

    profile: BenchmarkProfile
    work_dir: Path
    workers: int
    gpu_index: int | None = None


BenchmarkRunner = Callable[[BenchmarkContext], BenchmarkResult]


def _pattern(size: int) -> bytes:
    """Construit rapidement un contenu déterministe sans chronométrer sa préparation."""
    pattern = bytes(range(251))
    return (pattern * (size // len(pattern) + 1))[:size]


@dataclass(frozen=True)
class BenchmarkDefinition:
    """Entrée publique du catalogue."""

    benchmark_id: str
    group: str
    name: str
    description: str
    runner: BenchmarkRunner


def _result(
    definition_id: str,
    group: str,
    name: str,
    description: str,
    value: float,
    unit: str,
    elapsed: float,
    **parameters: float | str,
) -> BenchmarkResult:
    documentation = BENCHMARK_DOCUMENTATION[definition_id]
    return BenchmarkResult(
        benchmark_id=definition_id,
        group=group,
        name=name,
        description=description,
        value=value,
        unit=unit,
        elapsed_seconds=elapsed,
        parameters=parameters,
        methodology=documentation.methodology,
        limitations=documentation.limitations,
        references=[REFERENCE_LIBRARY[item] for item in documentation.reference_ids],
    )


def _integer_worker(duration_seconds: float) -> tuple[int, float]:
    """Charge entière pure Python utilisée en mono et multicœur."""
    value = 0x12345678
    iterations = 0
    started = perf_counter()
    while perf_counter() - started < duration_seconds:
        for _ in range(2_000):
            value = ((value * 1_664_525 + 1_013_904_223) ^ (value >> 13)) & 0xFFFFFFFF
        iterations += 2_000
    if value == -1:
        raise AssertionError
    return iterations, perf_counter() - started


def cpu_integer(context: BenchmarkContext) -> BenchmarkResult:
    iterations, elapsed = _integer_worker(context.profile.duration_seconds)
    return _result(
        "cpu.integer",
        "cpu",
        "Entiers mono-cœur",
        "Arithmétique et opérations binaires en Python pur.",
        iterations / elapsed / 1_000_000,
        "Mop/s",
        elapsed,
        workers=1,
    )


def cpu_float(context: BenchmarkContext) -> BenchmarkResult:
    value = 0.5
    iterations = 0
    started = perf_counter()
    while perf_counter() - started < context.profile.duration_seconds:
        for index in range(1, 2_001):
            value = math.sin(value + index) + math.sqrt(index)
        iterations += 2_000
    elapsed = perf_counter() - started
    if value == -1:
        raise AssertionError
    return _result(
        "cpu.float",
        "cpu",
        "Flottants mono-cœur",
        "Fonctions mathématiques scalaires en double précision.",
        iterations / elapsed / 1_000_000,
        "Mop/s",
        elapsed,
        workers=1,
    )


def cpu_hash(context: BenchmarkContext) -> BenchmarkResult:
    block = _pattern(MIB)
    iterations = 0
    started = perf_counter()
    while perf_counter() - started < context.profile.duration_seconds:
        hashlib.sha256(block).digest()
        iterations += 1
    elapsed = perf_counter() - started
    return _result(
        "cpu.hash",
        "cpu",
        "SHA-256",
        "Débit de hachage SHA-256 sur blocs de 1 Mio.",
        iterations / elapsed,
        "Mio/s",
        elapsed,
        block_size_bytes=MIB,
    )


def cpu_compression(context: BenchmarkContext) -> BenchmarkResult:
    block = random.Random(42).randbytes(MIB)
    iterations = 0
    started = perf_counter()
    while perf_counter() - started < context.profile.duration_seconds:
        zlib.compress(block, level=6)
        iterations += 1
    elapsed = perf_counter() - started
    return _result(
        "cpu.compression",
        "cpu",
        "Compression zlib",
        "Compression zlib niveau 6 d'un bloc déterministe.",
        iterations / elapsed,
        "Mio/s",
        elapsed,
        block_size_bytes=MIB,
        compression_level=6,
    )


def cpu_multicore(context: BenchmarkContext) -> BenchmarkResult:
    workers = max(1, context.workers)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        list(executor.map(_integer_worker, [0.02] * workers))
        started = perf_counter()
        counts = list(executor.map(_integer_worker, [context.profile.duration_seconds] * workers))
        elapsed = perf_counter() - started
    iterations = sum(count for count, _ in counts)
    return _result(
        "cpu.multicore",
        "cpu",
        "Entiers multicœur",
        "Même charge entière répartie sur tous les processeurs logiques.",
        iterations / elapsed / 1_000_000,
        "Mop/s",
        elapsed,
        workers=workers,
    )


def memory_copy(context: BenchmarkContext) -> BenchmarkResult:
    size = context.profile.memory_size_bytes
    source = bytearray(_pattern(size))
    destination = bytearray(size)
    source_view = memoryview(source)
    destination_view = memoryview(destination)
    iterations = 0
    started = perf_counter()
    while perf_counter() - started < context.profile.duration_seconds:
        destination_view[:] = source_view
        iterations += 1
    elapsed = perf_counter() - started
    return _result(
        "memory.copy",
        "memory",
        "Copie mémoire",
        "Copie séquentielle entre deux tampons préalloués.",
        iterations * size / elapsed / MIB,
        "Mio/s",
        elapsed,
        buffer_size_bytes=size,
    )


def _free_disk_bytes(path: Path) -> int:
    if hasattr(os, "statvfs"):
        stats = os.statvfs(path)
        return stats.f_frsize * stats.f_bavail
    import shutil

    return shutil.disk_usage(path).free


def _require_disk_space(context: BenchmarkContext) -> None:
    context.work_dir.mkdir(parents=True, exist_ok=True)
    required = context.profile.disk_size_bytes * 2
    if _free_disk_bytes(context.work_dir) < required:
        raise RuntimeError(f"Espace disque insuffisant : {required / MIB:.0f} Mio requis.")


def _temporary_path(context: BenchmarkContext) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    directory = tempfile.TemporaryDirectory(prefix=".perfcomparator_", dir=context.work_dir)
    return directory, Path(directory.name) / "payload.bin"


def storage_write(context: BenchmarkContext) -> BenchmarkResult:
    _require_disk_space(context)
    directory, path = _temporary_path(context)
    block = _pattern(MIB)
    try:
        started = perf_counter()
        with path.open("wb", buffering=0) as stream:
            remaining = context.profile.disk_size_bytes
            while remaining:
                written = min(len(block), remaining)
                stream.write(block[:written])
                remaining -= written
            os.fsync(stream.fileno())
        elapsed = perf_counter() - started
    finally:
        directory.cleanup()
    return _result(
        "storage.write",
        "storage",
        "Écriture séquentielle",
        "Écriture d'un fichier temporaire suivie d'une synchronisation physique.",
        context.profile.disk_size_bytes / elapsed / MIB,
        "Mio/s",
        elapsed,
        file_size_bytes=context.profile.disk_size_bytes,
    )


def storage_read(context: BenchmarkContext) -> BenchmarkResult:
    _require_disk_space(context)
    directory, path = _temporary_path(context)
    block = _pattern(MIB)
    try:
        with path.open("wb", buffering=0) as stream:
            remaining = context.profile.disk_size_bytes
            while remaining:
                written = min(len(block), remaining)
                stream.write(block[:written])
                remaining -= written
            os.fsync(stream.fileno())
        bytes_read = 0
        started = perf_counter()
        with path.open("rb", buffering=0) as stream:
            while chunk := stream.read(MIB):
                bytes_read += len(chunk)
        elapsed = perf_counter() - started
        if bytes_read != context.profile.disk_size_bytes:
            raise RuntimeError("Lecture séquentielle incomplète.")
    finally:
        directory.cleanup()
    return _result(
        "storage.read",
        "storage",
        "Lecture séquentielle",
        "Lecture intégrale d'un fichier temporaire.",
        context.profile.disk_size_bytes / elapsed / MIB,
        "Mio/s",
        elapsed,
        file_size_bytes=context.profile.disk_size_bytes,
    )


def _random_offsets(file_size: int, operations: int, block_size: int = 4_096) -> list[int]:
    randomizer = random.Random(42)
    block_count = file_size // block_size
    return [randomizer.randrange(block_count) * block_size for _ in range(operations)]


def storage_random_read(context: BenchmarkContext) -> BenchmarkResult:
    _require_disk_space(context)
    directory, path = _temporary_path(context)
    block = bytes(4_096)
    operations = context.profile.random_operations
    offsets = _random_offsets(context.profile.disk_size_bytes, operations)
    try:
        with path.open("wb", buffering=0) as stream:
            for _ in range(context.profile.disk_size_bytes // len(block)):
                stream.write(block)
            os.fsync(stream.fileno())
        started = perf_counter()
        with path.open("rb", buffering=0) as stream:
            for offset in offsets:
                stream.seek(offset)
                if len(stream.read(len(block))) != len(block):
                    raise RuntimeError("Lecture aléatoire incomplète.")
        elapsed = perf_counter() - started
    finally:
        directory.cleanup()
    return _result(
        "storage.random-read",
        "storage",
        "Lecture aléatoire 4 Kio",
        "Lectures de blocs de 4 Kio à des positions déterministes.",
        operations / elapsed,
        "IOPS",
        elapsed,
        operations=operations,
        block_size_bytes=len(block),
    )


def storage_random_write(context: BenchmarkContext) -> BenchmarkResult:
    _require_disk_space(context)
    directory, path = _temporary_path(context)
    block = _pattern(4_096)
    operations = context.profile.random_operations
    offsets = _random_offsets(context.profile.disk_size_bytes, operations)
    try:
        with path.open("wb", buffering=0) as stream:
            stream.truncate(context.profile.disk_size_bytes)
        started = perf_counter()
        with path.open("r+b", buffering=0) as stream:
            for offset in offsets:
                stream.seek(offset)
                stream.write(block)
            os.fsync(stream.fileno())
        elapsed = perf_counter() - started
    finally:
        directory.cleanup()
    return _result(
        "storage.random-write",
        "storage",
        "Écriture aléatoire 4 Kio",
        "Écritures de blocs de 4 Kio suivies d'une synchronisation physique.",
        operations / elapsed,
        "IOPS",
        elapsed,
        operations=operations,
        block_size_bytes=len(block),
    )


def _json_payload() -> list[dict[str, object]]:
    return [
        {
            "id": index,
            "name": f"machine-{index}",
            "scores": [index * factor / 7 for factor in range(12)],
            "active": index % 2 == 0,
        }
        for index in range(1_000)
    ]


def application_json(context: BenchmarkContext) -> BenchmarkResult:
    payload = _json_payload()
    encoded = json.dumps(payload, separators=(",", ":"))
    iterations = 0
    started = perf_counter()
    while perf_counter() - started < context.profile.duration_seconds:
        json.loads(encoded)
        json.dumps(payload, separators=(",", ":"))
        iterations += 1
    elapsed = perf_counter() - started
    return _result(
        "application.json",
        "application",
        "JSON",
        "Sérialisation et désérialisation d'un document structuré.",
        iterations / elapsed,
        "cycles/s",
        elapsed,
        document_size_bytes=len(encoded.encode()),
    )


def application_sqlite(context: BenchmarkContext) -> BenchmarkResult:
    context.work_dir.mkdir(parents=True, exist_ok=True)
    directory = tempfile.TemporaryDirectory(prefix=".perfcomparator_", dir=context.work_dir)
    path = Path(directory.name) / "benchmark.sqlite3"
    rows = context.profile.sqlite_rows
    try:
        started = perf_counter()
        with closing(sqlite3.connect(path)) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                "CREATE TABLE scores (id INTEGER PRIMARY KEY, name TEXT, score REAL)"
            )
            connection.executemany(
                "INSERT INTO scores VALUES (?, ?, ?)",
                ((index, f"machine-{index}", index / 7) for index in range(rows)),
            )
            connection.commit()
            result = connection.execute(
                "SELECT COUNT(*), AVG(score) FROM scores WHERE id % 3 = 0"
            ).fetchone()
            if result is None:
                raise RuntimeError("Résultat SQLite absent.")
        elapsed = perf_counter() - started
    finally:
        directory.cleanup()
    return _result(
        "application.sqlite",
        "application",
        "SQLite",
        "Création, insertion transactionnelle et requête d'une base locale.",
        rows / elapsed,
        "lignes/s",
        elapsed,
        rows=rows,
    )


DEFINITIONS = (
    BenchmarkDefinition("cpu.integer", "cpu", "Entiers mono-cœur", "Python pur", cpu_integer),
    BenchmarkDefinition(
        "cpu.float", "cpu", "Flottants mono-cœur", "Calcul scientifique", cpu_float
    ),
    BenchmarkDefinition("cpu.hash", "cpu", "SHA-256", "Cryptographie", cpu_hash),
    BenchmarkDefinition(
        "cpu.compression", "cpu", "Compression zlib", "Compression", cpu_compression
    ),
    BenchmarkDefinition("cpu.multicore", "cpu", "Entiers multicœur", "Parallélisme", cpu_multicore),
    BenchmarkDefinition("memory.copy", "memory", "Copie mémoire", "Bande passante", memory_copy),
    BenchmarkDefinition(
        "storage.write", "storage", "Écriture séquentielle", "Débit disque", storage_write
    ),
    BenchmarkDefinition(
        "storage.read", "storage", "Lecture séquentielle", "Débit disque", storage_read
    ),
    BenchmarkDefinition(
        "storage.random-read",
        "storage",
        "Lecture aléatoire 4 Kio",
        "Réactivité disque",
        storage_random_read,
    ),
    BenchmarkDefinition(
        "storage.random-write",
        "storage",
        "Écriture aléatoire 4 Kio",
        "Réactivité disque",
        storage_random_write,
    ),
    BenchmarkDefinition(
        "application.json", "application", "JSON", "Traitement de données", application_json
    ),
    BenchmarkDefinition(
        "application.sqlite",
        "application",
        "SQLite",
        "Base de données locale",
        application_sqlite,
    ),
    BenchmarkDefinition(
        "gpu.compute-fp32", "gpu", "Calcul GPU FP32", "Calcul parallèle", gpu_compute_fp32
    ),
    BenchmarkDefinition("gpu.memory", "gpu", "Bande passante GPU", "Mémoire GPU", gpu_memory),
    BenchmarkDefinition(
        "gpu.image-filter", "gpu", "Filtre d'image GPU", "Traitement d'image", gpu_image_filter
    ),
    BenchmarkDefinition(
        "gpu.raster", "gpu", "Remplissage raster GPU", "Rendu hors écran", gpu_raster
    ),
)

CATALOG = {definition.benchmark_id: definition for definition in DEFINITIONS}
GROUPS = {
    group: tuple(item.benchmark_id for item in DEFINITIONS if item.group == group)
    for group in ("cpu", "memory", "storage", "application", "gpu")
}
GROUPS["all"] = tuple(CATALOG)


def resolve_benchmarks(names: list[str] | None, groups: list[str] | None) -> list[str]:
    """Résout l'union ordonnée des noms et groupes, ou toute la suite par défaut."""
    requested: list[str] = []
    for group in groups or []:
        if group not in GROUPS:
            raise ValueError(f"Groupe inconnu : {group}")
        requested.extend(GROUPS[group])
    for name in names or []:
        if name not in CATALOG:
            raise ValueError(f"Benchmark inconnu : {name}")
        requested.append(name)
    if not requested:
        requested.extend(GROUPS["all"])
    return list(dict.fromkeys(requested))
