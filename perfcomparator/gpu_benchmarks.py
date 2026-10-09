"""Benchmarks GPU hors écran fondés sur WebGPU/wgpu."""

from __future__ import annotations

import math
import struct
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from time import perf_counter
from typing import TYPE_CHECKING

import wgpu

from .models import BenchmarkResult

if TYPE_CHECKING:
    from .benchmarks import BenchmarkContext

WEBGPU_REFERENCE = "W3C GPU for the Web Community Group, WebGPU, https://gpuweb.github.io/gpuweb/"
WGPU_REFERENCE = "PyGfx, wgpu-py documentation, https://wgpu-py.readthedocs.io/"


@dataclass(frozen=True)
class GpuAdapterSummary:
    """Adaptateur WebGPU adressable par l'option ``--gpu``."""

    index: int
    device: str
    backend: str
    adapter_type: str


def gpu_adapters() -> tuple[GpuAdapterSummary, ...]:
    """Liste les adaptateurs WebGPU dans l'ordre exposé par wgpu."""
    summaries = []
    for index, adapter in enumerate(wgpu.gpu.enumerate_adapters_sync()):
        info = dict(adapter.info)
        summaries.append(
            GpuAdapterSummary(
                index=index,
                device=str(info.get("device") or "inconnu"),
                backend=str(info.get("backend_type") or "inconnu"),
                adapter_type=str(info.get("adapter_type") or "inconnu"),
            )
        )
    return tuple(summaries)


@cache
def _adapter(gpu_index: int | None) -> tuple[wgpu.GPUAdapter, dict[str, object]]:
    adapters = wgpu.gpu.enumerate_adapters_sync()
    if not adapters:
        raise RuntimeError("Aucun adaptateur WebGPU compatible n'a été trouvé.")
    if gpu_index is not None:
        if gpu_index < 0 or gpu_index >= len(adapters):
            raise ValueError(
                f"Indice GPU {gpu_index} invalide ; choisir une valeur entre 0 et "
                f"{len(adapters) - 1}."
            )
        adapter = adapters[gpu_index]
    else:
        type_priority = {"discretegpu": 0, "integratedgpu": 1, "virtualgpu": 2, "cpu": 3}
        gpu_index, adapter = min(
            enumerate(adapters),
            key=lambda item: type_priority.get(
                str(dict(item[1].info).get("adapter_type", "")).casefold(), 4
            ),
        )
    info = dict(adapter.info)
    info["adapter_index"] = gpu_index
    return adapter, info


def selected_gpu_adapter(gpu_index: int | None = None) -> GpuAdapterSummary:
    """Résout la sélection explicite ou le choix automatique haute performance."""
    _, info = _adapter(gpu_index)
    return GpuAdapterSummary(
        index=int(info["adapter_index"]),
        device=str(info.get("device") or "inconnu"),
        backend=str(info.get("backend_type") or "inconnu"),
        adapter_type=str(info.get("adapter_type") or "inconnu"),
    )


@cache
def _device(gpu_index: int | None) -> tuple[wgpu.GPUDevice, dict[str, object]]:
    adapter, info = _adapter(gpu_index)
    if str(info.get("adapter_type", "")).casefold() == "cpu":
        name = str(info.get("device") or "inconnu")
        raise RuntimeError(
            f"{name} est un moteur WebGPU logiciel exécuté par le CPU, pas un GPU matériel."
        )
    return adapter.request_device_sync(), info


def _metadata(info: dict[str, object]) -> dict[str, int | str]:
    return {
        "gpu_index": int(info.get("adapter_index", -1)),
        "gpu_device": str(info.get("device") or "inconnu"),
        "gpu_backend": str(info.get("backend_type") or "inconnu"),
        "gpu_adapter_type": str(info.get("adapter_type") or "inconnu"),
        "wgpu_version": wgpu.__version__,
    }


def _measure(
    device: wgpu.GPUDevice,
    encode: Callable[[int], wgpu.GPUCommandBuffer],
    target_seconds: float,
    synchronize: Callable[[], object],
) -> tuple[int, float]:
    warmup = encode(1)
    started = perf_counter()
    device.queue.submit([warmup])
    synchronize()
    warmup_seconds = max(perf_counter() - started, 0.000_001)
    repeats = max(1, min(512, math.ceil(target_seconds / warmup_seconds)))
    command = encode(repeats)
    started = perf_counter()
    device.queue.submit([command])
    synchronize()
    return repeats, perf_counter() - started


def _result(
    benchmark_id: str,
    name: str,
    description: str,
    value: float,
    unit: str,
    elapsed: float,
    info: dict[str, object],
    methodology: str,
    limitations: str,
    **parameters: float | str,
) -> BenchmarkResult:
    return BenchmarkResult(
        benchmark_id=benchmark_id,
        group="gpu",
        name=name,
        description=description,
        value=value,
        unit=unit,
        elapsed_seconds=elapsed,
        parameters={**_metadata(info), **parameters},
        methodology=methodology,
        limitations=limitations,
        references=[WEBGPU_REFERENCE, WGPU_REFERENCE],
    )


def gpu_compute_fp32(context: BenchmarkContext) -> BenchmarkResult:
    device, info = _device(context.gpu_index)
    element_count = 262_144
    operations_per_element = 256
    buffer = device.create_buffer(
        size=element_count * 4,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC,
    )
    shader = device.create_shader_module(
        code=f"""
        @group(0) @binding(0) var<storage, read_write> values: array<f32>;
        @compute @workgroup_size(256)
        fn main(@builtin(global_invocation_id) id: vec3<u32>) {{
            if (id.x >= {element_count}u) {{ return; }}
            var x = values[id.x] + f32(id.x % 97u) * 0.00001;
            for (var i = 0u; i < {operations_per_element // 2}u; i += 1u) {{
                x = x * 1.0000001 + 0.0000001;
            }}
            values[id.x] = x;
        }}
        """
    )
    pipeline = device.create_compute_pipeline(
        layout="auto", compute={"module": shader, "entry_point": "main"}
    )
    bind_group = device.create_bind_group(
        layout=pipeline.get_bind_group_layout(0),
        entries=[{"binding": 0, "resource": {"buffer": buffer}}],
    )

    def encode(repeats: int) -> wgpu.GPUCommandBuffer:
        encoder = device.create_command_encoder()
        compute_pass = encoder.begin_compute_pass()
        compute_pass.set_pipeline(pipeline)
        compute_pass.set_bind_group(0, bind_group)
        for _ in range(repeats):
            compute_pass.dispatch_workgroups(math.ceil(element_count / 256))
        compute_pass.end()
        return encoder.finish()

    repeats, elapsed = _measure(
        device,
        encode,
        context.profile.duration_seconds,
        lambda: device.queue.read_buffer(buffer, 0, 4),
    )
    check = struct.unpack("f", device.queue.read_buffer(buffer, 0, 4))[0]
    if not math.isfinite(check):
        raise RuntimeError("Le calcul GPU FP32 a produit une valeur invalide.")
    operations = element_count * operations_per_element * repeats
    return _result(
        "gpu.compute-fp32",
        "Calcul GPU FP32",
        "Charge arithmétique parallèle en simple précision.",
        operations / elapsed / 1_000_000_000,
        "GFLOP/s",
        elapsed,
        info,
        "Un shader WGSL applique 128 multiplications-additions à 262 144 valeurs FP32.",
        "Mesure un noyau synthétique FP32, pas les unités matricielles ou IA spécialisées.",
        element_count=element_count,
        operations_per_element=operations_per_element,
    )


def gpu_memory(context: BenchmarkContext) -> BenchmarkResult:
    device, info = _device(context.gpu_index)
    size = min(context.profile.memory_size_bytes, 32 * 1_048_576)
    size -= size % 1_024
    element_count = size // 4
    source = device.create_buffer(
        size=size, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
    )
    destination = device.create_buffer(
        size=size, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC
    )
    device.queue.write_buffer(source, 0, struct.pack("I", 0xA5A5A5A5))
    shader = device.create_shader_module(
        code=f"""
        @group(0) @binding(0) var<storage, read> source: array<u32>;
        @group(0) @binding(1) var<storage, read_write> destination: array<u32>;
        @compute @workgroup_size(256)
        fn main(@builtin(global_invocation_id) id: vec3<u32>) {{
            if (id.x < {element_count}u) {{ destination[id.x] = source[id.x]; }}
        }}
        """
    )
    pipeline = device.create_compute_pipeline(
        layout="auto", compute={"module": shader, "entry_point": "main"}
    )
    bind_group = device.create_bind_group(
        layout=pipeline.get_bind_group_layout(0),
        entries=[
            {"binding": 0, "resource": {"buffer": source}},
            {"binding": 1, "resource": {"buffer": destination}},
        ],
    )

    def encode(repeats: int) -> wgpu.GPUCommandBuffer:
        encoder = device.create_command_encoder()
        compute_pass = encoder.begin_compute_pass()
        compute_pass.set_pipeline(pipeline)
        compute_pass.set_bind_group(0, bind_group)
        for _ in range(repeats):
            compute_pass.dispatch_workgroups(math.ceil(element_count / 256))
        compute_pass.end()
        return encoder.finish()

    repeats, elapsed = _measure(
        device,
        encode,
        context.profile.duration_seconds,
        lambda: device.queue.read_buffer(destination, 0, 4),
    )
    check = struct.unpack("I", device.queue.read_buffer(destination, 0, 4))[0]
    if check != 0xA5A5A5A5:
        raise RuntimeError("La copie GPU n'a pas produit le résultat attendu.")
    transferred = size * 2 * repeats
    return _result(
        "gpu.memory",
        "Bande passante GPU",
        "Copie parallèle entre deux tampons GPU.",
        transferred / elapsed / 1_073_741_824,
        "Gio/s",
        elapsed,
        info,
        "Un shader WGSL lit puis écrit un tampon ; les octets lus et écrits sont comptés.",
        "Le cache et la mémoire unifiée peuvent influencer le débit observé.",
        buffer_size_bytes=size,
        bytes_counted_per_element=8,
    )


def gpu_image_filter(context: BenchmarkContext) -> BenchmarkResult:
    device, info = _device(context.gpu_index)
    side = {"quick": 512, "standard": 1_024, "thorough": 2_048}.get(context.profile.name, 64)
    pixel_count = side * side
    size = pixel_count * 4
    source = device.create_buffer(
        size=size, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
    )
    destination = device.create_buffer(
        size=size, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC
    )
    device.queue.write_buffer(source, 0, struct.pack("f", 1.0))
    shader = device.create_shader_module(
        code=f"""
        @group(0) @binding(0) var<storage, read> source: array<f32>;
        @group(0) @binding(1) var<storage, read_write> destination: array<f32>;
        @compute @workgroup_size(16, 16)
        fn main(@builtin(global_invocation_id) id: vec3<u32>) {{
            if (id.x >= {side}u || id.y >= {side}u) {{ return; }}
            let x0 = max(1u, min({side - 2}u, id.x));
            let y0 = max(1u, min({side - 2}u, id.y));
            let p = y0 * {side}u + x0;
            destination[id.y * {side}u + id.x] =
                (source[p] * 4.0 + source[p - 1u] + source[p + 1u] +
                 source[p - {side}u] + source[p + {side}u]) / 8.0;
        }}
        """
    )
    pipeline = device.create_compute_pipeline(
        layout="auto", compute={"module": shader, "entry_point": "main"}
    )
    bind_group = device.create_bind_group(
        layout=pipeline.get_bind_group_layout(0),
        entries=[
            {"binding": 0, "resource": {"buffer": source}},
            {"binding": 1, "resource": {"buffer": destination}},
        ],
    )

    def encode(repeats: int) -> wgpu.GPUCommandBuffer:
        encoder = device.create_command_encoder()
        compute_pass = encoder.begin_compute_pass()
        compute_pass.set_pipeline(pipeline)
        compute_pass.set_bind_group(0, bind_group)
        for _ in range(repeats):
            compute_pass.dispatch_workgroups(math.ceil(side / 16), math.ceil(side / 16))
        compute_pass.end()
        return encoder.finish()

    repeats, elapsed = _measure(
        device,
        encode,
        context.profile.duration_seconds,
        lambda: device.queue.read_buffer(destination, 0, 4),
    )
    check = struct.unpack("f", device.queue.read_buffer(destination, 0, 4))[0]
    if not math.isfinite(check):
        raise RuntimeError("Le filtre GPU a produit une valeur invalide.")
    return _result(
        "gpu.image-filter",
        "Filtre d'image GPU",
        "Filtre spatial à cinq échantillons hors écran.",
        pixel_count * repeats / elapsed / 1_000_000,
        "Mpixel/s",
        elapsed,
        info,
        "Un shader WGSL applique un filtre pondéré à cinq pixels voisins.",
        "Ce noyau synthétique ne représente pas les codecs vidéo ni les moteurs photo complets.",
        width=side,
        height=side,
        samples_per_pixel=5,
    )


def gpu_raster(context: BenchmarkContext) -> BenchmarkResult:
    device, info = _device(context.gpu_index)
    side = {"quick": 512, "standard": 1_024, "thorough": 2_048}.get(context.profile.name, 64)
    texture = device.create_texture(
        size=(side, side, 1),
        format=wgpu.TextureFormat.rgba8unorm,
        usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
    )
    shader = device.create_shader_module(
        code="""
        @vertex
        fn vs_main(@builtin(vertex_index) index: u32) -> @builtin(position) vec4<f32> {
            var positions = array<vec2<f32>, 3>(
                vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0));
            return vec4<f32>(positions[index], 0.0, 1.0);
        }
        @fragment
        fn fs_main(@builtin(position) position: vec4<f32>) -> @location(0) vec4<f32> {
            return vec4<f32>(fract(position.x * 0.013), fract(position.y * 0.017), 0.5, 1.0);
        }
        """
    )
    pipeline = device.create_render_pipeline(
        layout="auto",
        vertex={"module": shader, "entry_point": "vs_main", "buffers": []},
        fragment={
            "module": shader,
            "entry_point": "fs_main",
            "targets": [{"format": wgpu.TextureFormat.rgba8unorm}],
        },
        primitive={"topology": wgpu.PrimitiveTopology.triangle_list},
    )
    view = texture.create_view()

    def encode(repeats: int) -> wgpu.GPUCommandBuffer:
        encoder = device.create_command_encoder()
        render_pass = encoder.begin_render_pass(
            color_attachments=[
                {
                    "view": view,
                    "resolve_target": None,
                    "clear_value": (0.0, 0.0, 0.0, 1.0),
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                }
            ]
        )
        render_pass.set_pipeline(pipeline)
        for _ in range(repeats):
            render_pass.draw(3)
        render_pass.end()
        return encoder.finish()

    def synchronize() -> object:
        return device.queue.read_texture(
            {"texture": texture, "origin": (0, 0, 0)},
            {"offset": 0, "bytes_per_row": 256, "rows_per_image": 1},
            (1, 1, 1),
        )

    repeats, elapsed = _measure(device, encode, context.profile.duration_seconds, synchronize)
    device.queue.read_texture(
        {"texture": texture, "origin": (0, 0, 0)},
        {"offset": 0, "bytes_per_row": side * 4, "rows_per_image": side},
        (side, side, 1),
    )
    return _result(
        "gpu.raster",
        "Remplissage raster GPU",
        "Rendu répété d'un triangle plein écran hors écran.",
        side * side * repeats / elapsed / 1_000_000,
        "Mpixel/s",
        elapsed,
        info,
        "Un pipeline WGSL dessine un triangle couvrant une texture RGBA8 hors écran.",
        "Mesure surtout le remplissage simple, sans géométrie complexe ni ray tracing.",
        width=side,
        height=side,
        color_format="rgba8unorm",
    )
