"""02 — Sync vs Async: ile realnie daje AsyncInferQueue na CPU.

Ten sam model liczony dwa razy: pojedynczymi wywołaniami (sync) i przez
kolejkę asynchroniczną, która trzyma wszystkie rdzenie zajęte.

    python3 02_benchmark.py [liczba_probek]
"""

import sys
import time

import numpy as np
import openvino as ov
import openvino.opset13 as ops

IN_DIM = 512
HIDDEN = 1024
LAYERS = 4


def build_model() -> ov.Model:
    """Stos warstw gęstych — na tyle duży, żeby pomiar coś znaczył."""
    rng = np.random.default_rng(0)
    x = ops.parameter([-1, IN_DIM], dtype=np.float32, name="input")

    node = x
    dims = [IN_DIM] + [HIDDEN] * LAYERS
    for i in range(LAYERS):
        w = rng.standard_normal((dims[i], dims[i + 1])).astype(np.float32) * 0.02
        node = ops.relu(ops.matmul(node, ops.constant(w), False, False))

    node.set_friendly_name("output")
    return ov.Model([node], [x], "mlp_bench")


def bench_sync(compiled, batches) -> float:
    request = compiled.create_infer_request()
    start = time.perf_counter()
    for batch in batches:
        request.infer({0: batch})
    return time.perf_counter() - start


def bench_async(compiled, batches) -> float:
    queue = ov.AsyncInferQueue(compiled)
    start = time.perf_counter()
    for batch in batches:
        queue.start_async({0: batch})
    queue.wait_all()
    return time.perf_counter() - start


def main() -> None:
    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 200

    core = ov.Core()
    print(f"OpenVINO {ov.__version__} | CPU: {core.get_property('CPU', 'FULL_DEVICE_NAME')}")

    compiled = core.compile_model(build_model(), "CPU", {"PERFORMANCE_HINT": "THROUGHPUT"})
    streams = compiled.get_property("NUM_STREAMS")
    print(f"Strumienie inferencji: {streams} | próbek: {samples}\n")

    rng = np.random.default_rng(1)
    batches = [rng.standard_normal((1, IN_DIM)).astype(np.float32) for _ in range(samples)]

    bench_sync(compiled, batches[:20])  # rozgrzewka
    t_sync = bench_sync(compiled, batches)
    t_async = bench_async(compiled, batches)

    for label, elapsed in (("sync ", t_sync), ("async", t_async)):
        fps = samples / elapsed
        print(f"{label}: {elapsed * 1000:7.1f} ms  |  {fps:7.1f} inf/s  |  {elapsed / samples * 1000:5.2f} ms/inf")

    print(f"\nPrzyspieszenie async: {t_sync / t_async:.2f}x")


if __name__ == "__main__":
    main()
