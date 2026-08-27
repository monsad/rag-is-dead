"""FP32 vs BF16 vs INT8 na CPU: dokładność, latencja, przepustowość, rozmiar.

Trzy konfiguracje tego samego ResNet-50, mierzone na tych samych 1000 zdjęciach
ImageNet (po jednym na klasę, etykieta wynika z nazwy pliku).

Uwaga metodologiczna: na procesorach z AMX (Xeon 4. gen wzwyż) OpenVINO
DOMYŚLNIE liczy model FP32 w bfloat16. Naiwne porównanie "FP32 vs INT8" mierzy
więc bf16 vs int8 i zaniża zysk z kwantyzacji. Dlatego f32 jest tu wymuszone
osobno przez INFERENCE_PRECISION_HINT.

    python3 evaluate.py
"""

import time

import numpy as np
import openvino as ov

from common import IR_FP32, IR_INT8, cached_inputs, labels

PERF_SAMPLES = 128
REPEATS = 3  # maszyna bywa współdzielona — z każdego pomiaru bierzemy medianę

CONFIGS = {
    "FP32":  (IR_FP32, {"INFERENCE_PRECISION_HINT": "f32"}),
    "BF16":  (IR_FP32, {}),                                  # domyślne na AMX
    "INT8":  (IR_INT8, {}),
}


def short_precision(name: str, hint) -> str:
    """Czytelna nazwa precyzji jąder obliczeniowych.

    Model INT8 raportuje bf16, bo NNCF kwantyzuje warstwy splotowe i liniowe,
    a reszta grafu zostaje w domyślnej precyzji urządzenia.
    """
    base = hint.get_type_name()  # "f32", "bf16", ...
    return f"int8+{base}" if name == "INT8" else base


def accuracy(compiled, inputs, truth) -> tuple[float, float, np.ndarray]:
    """Top-1, top-5 i wektor predykcji (do porównania modeli między sobą)."""
    preds = np.empty(len(truth), dtype=np.int64)
    top5_hits = 0

    for i in range(len(truth)):
        logits = compiled(inputs[i : i + 1])[compiled.output(0)].ravel()
        preds[i] = logits.argmax()
        top5_hits += int(truth[i] in np.argpartition(-logits, 5)[:5])

    return (preds == truth).mean() * 100, top5_hits / len(truth) * 100, preds


def latency(core, path, config, batches) -> tuple[float, float]:
    """Mediana i p95 latencji przy hincie LATENCY (jedno zapytanie naraz)."""
    compiled = core.compile_model(path, "CPU", {**config, "PERFORMANCE_HINT": "LATENCY"})
    request = compiled.create_infer_request()

    for x in batches[:16]:
        request.infer({0: x})

    times = []
    for _ in range(REPEATS):
        for x in batches:
            start = time.perf_counter()
            request.infer({0: x})
            times.append((time.perf_counter() - start) * 1000)

    del request, compiled
    return float(np.median(times)), float(np.percentile(times, 95))


def throughput(core, path, config, batches) -> float:
    """Przepustowość przy hincie THROUGHPUT i kolejce asynchronicznej."""
    compiled = core.compile_model(path, "CPU", {**config, "PERFORMANCE_HINT": "THROUGHPUT"})
    queue = ov.AsyncInferQueue(compiled)

    for x in batches[:16]:
        queue.start_async({0: x})
    queue.wait_all()

    runs = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        for x in batches:
            queue.start_async({0: x})
        queue.wait_all()
        runs.append(len(batches) / (time.perf_counter() - start))

    del queue, compiled
    return float(np.median(runs))


def main() -> None:
    core = ov.Core()
    print(f"OpenVINO {ov.__version__}")
    print(f"CPU: {core.get_property('CPU', 'FULL_DEVICE_NAME')}")
    print(f"Wsparcie sprzętowe: {core.get_property('CPU', 'OPTIMIZATION_CAPABILITIES')}\n")

    inputs = cached_inputs()
    truth = labels()
    batches = [np.ascontiguousarray(inputs[i : i + 1]) for i in range(PERF_SAMPLES)]

    results = {}
    baseline_preds = None

    for name, (path, config) in CONFIGS.items():
        compiled = core.compile_model(path, "CPU", config)
        precision = short_precision(name, compiled.get_property("INFERENCE_PRECISION_HINT"))
        print(f"{name}: jądra liczone w {precision}, mierzę dokładność na {len(truth)} zdjęciach...")

        top1, top5, preds = accuracy(compiled, inputs, truth)
        del compiled

        med, p95 = latency(core, path, config, batches)
        fps = throughput(core, path, config, batches)
        size = path.with_suffix(".bin").stat().st_size / 1e6
        agreement = 100.0 if baseline_preds is None else (preds == baseline_preds).mean() * 100
        baseline_preds = baseline_preds if baseline_preds is not None else preds

        results[name] = dict(top1=top1, top5=top5, med=med, p95=p95, fps=fps,
                             size=size, agree=agreement, precision=precision)

    header = f"\n{'':6}{'precyzja':>10}{'top-1':>9}{'top-5':>8}{'latencja':>11}{'p95':>8}{'inf/s':>9}{'rozmiar':>10}{'zgodność':>10}"
    print(header)
    print("-" * len(header.strip()))
    for name, r in results.items():
        print(f"{name:6}{r['precision']:>10}{r['top1']:8.1f}%{r['top5']:7.1f}%"
              f"{r['med']:9.2f}ms{r['p95']:6.2f}ms{r['fps']:9.1f}{r['size']:8.1f}MB{r['agree']:9.1f}%")

    fp32, int8 = results["FP32"], results["INT8"]
    print(f"\nINT8 vs FP32:  {fp32['med'] / int8['med']:.2f}x niższa latencja, "
          f"{int8['fps'] / fp32['fps']:.2f}x wyższa przepustowość, "
          f"{fp32['size'] / int8['size']:.2f}x mniejszy model")
    print(f"Koszt jakości: {int8['top1'] - fp32['top1']:+.1f} p.p. top-1, "
          f"{int8['top5'] - fp32['top5']:+.1f} p.p. top-5, "
          f"identyczna predykcja na {int8['agree']:.1f}% zdjęć")
    print(f"Zysk z samego AMX (FP32->BF16, bez kwantyzacji): "
          f"{results['BF16']['fps'] / fp32['fps']:.2f}x przepustowości")


if __name__ == "__main__":
    main()
