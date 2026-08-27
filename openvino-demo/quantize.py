"""Kwantyzacja INT8 (post-training) ResNet-50 przez NNCF.

FP32 ONNX -> OpenVINO IR -> PTQ na prawdziwych zdjęciach -> IR INT8.
Kalibracja nie wymaga etykiet ani trenowania — tylko reprezentatywnych danych.

    python3 quantize.py [liczba_probek_kalibracyjnych]
"""

import sys
import time

import nncf
import openvino as ov

from common import IR_FP32, IR_INT8, ONNX_MODEL, dataset, preprocess


def main() -> None:
    calib_size = int(sys.argv[1]) if len(sys.argv) > 1 else 128

    core = ov.Core()
    print(f"OpenVINO {ov.__version__} | NNCF {nncf.__version__}")

    model = core.read_model(ONNX_MODEL)
    ov.save_model(model, IR_FP32, compress_to_fp16=False)
    print(f"FP32 IR zapisany: {IR_FP32.name}")

    # Co 1000/calib_size-ty obraz — próbki rozłożone po wszystkich klasach,
    # a nie 128 psów z rzędu.
    samples = dataset()[:: max(1, 1000 // calib_size)][:calib_size]
    print(f"Kalibracja na {len(samples)} zdjęciach z {len(set(i for _, i in samples))} klas")

    calibration = nncf.Dataset(samples, lambda item: preprocess(item[0]))

    start = time.perf_counter()
    quantized = nncf.quantize(model, calibration, preset=nncf.QuantizationPreset.PERFORMANCE)
    elapsed = time.perf_counter() - start

    ov.save_model(quantized, IR_INT8)
    print(f"\nINT8 IR zapisany: {IR_INT8.name}  (kwantyzacja: {elapsed:.1f} s)")


if __name__ == "__main__":
    main()
