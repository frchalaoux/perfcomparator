from types import SimpleNamespace

import pytest

from perfcomparator import gpu_benchmarks


def test_gpu_selection_prefers_discrete_and_accepts_an_explicit_index(monkeypatch) -> None:
    adapters = [
        SimpleNamespace(
            info={
                "device": "GPU intégré",
                "adapter_type": "IntegratedGPU",
                "backend_type": "Metal",
            }
        ),
        SimpleNamespace(
            info={
                "device": "GPU dédié",
                "adapter_type": "DiscreteGPU",
                "backend_type": "Metal",
            }
        ),
    ]
    monkeypatch.setattr(gpu_benchmarks.wgpu.gpu, "enumerate_adapters_sync", lambda: adapters)
    gpu_benchmarks._adapter.cache_clear()

    try:
        automatic = gpu_benchmarks.selected_gpu_adapter()
        explicit = gpu_benchmarks.selected_gpu_adapter(0)

        assert automatic.index == 1
        assert automatic.device == "GPU dédié"
        assert explicit.index == 0
        assert explicit.device == "GPU intégré"
        with pytest.raises(ValueError, match="Indice GPU 2 invalide"):
            gpu_benchmarks.selected_gpu_adapter(2)
    finally:
        gpu_benchmarks._adapter.cache_clear()
        gpu_benchmarks._device.cache_clear()


def test_software_adapter_is_not_benchmarked_as_a_hardware_gpu(monkeypatch) -> None:
    adapter = SimpleNamespace(
        info={
            "device": "Microsoft Basic Render Driver",
            "adapter_type": "CPU",
            "backend_type": "D3D12",
        }
    )
    monkeypatch.setattr(gpu_benchmarks.wgpu.gpu, "enumerate_adapters_sync", lambda: [adapter])
    gpu_benchmarks._adapter.cache_clear()
    gpu_benchmarks._device.cache_clear()

    try:
        with pytest.raises(RuntimeError, match="moteur WebGPU logiciel"):
            gpu_benchmarks._device(None)
    finally:
        gpu_benchmarks._adapter.cache_clear()
        gpu_benchmarks._device.cache_clear()
