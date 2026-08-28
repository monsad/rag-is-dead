"""Co ten procesor potrafi i czego się po nim spodziewać przy kwantyzacji.

Nie wymaga pobranego modelu ani danych — działa od razu po instalacji OpenVINO.

    python3 check_cpu.py
"""

import os
import platform
import re
import subprocess

import numpy as np
import openvino as ov
import openvino.opset13 as ops

# Flagi, które faktycznie zmieniają wynik kwantyzacji.
INTERESTING = r"amx_[a-z0-9]+|avx512_bf16|avx512_fp16|avx512_vnni|avx512f|avx2"


def cpu_flags() -> set[str]:
    """Flagi ISA z /proc/cpuinfo (Linux) albo z sysctl (macOS)."""
    try:
        with open("/proc/cpuinfo") as f:
            text = f.read()
    except FileNotFoundError:
        try:
            text = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.leaf7_features", "machdep.cpu.features"],
                capture_output=True, text=True, check=True,
            ).stdout.lower()
        except Exception:
            return set()
    return set(re.findall(INTERESTING, text))


def cpu_name() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except FileNotFoundError:
        pass
    return platform.processor() or "nieznany"


def tiny_model() -> ov.Model:
    """Najmniejszy model z prawdziwym matmulem — tylko po to, by zapytać o precyzję."""
    x = ops.parameter([1, 64], dtype=np.float32)
    w = ops.constant(np.zeros((64, 64), dtype=np.float32))
    return ov.Model([ops.matmul(x, w, False, False)], [x], "probe")


def main() -> None:
    core = ov.Core()
    flags = cpu_flags()
    caps = core.get_property("CPU", "OPTIMIZATION_CAPABILITIES")

    print("=" * 68)
    print(f"CPU              {cpu_name()}")
    print(f"rdzenie          {os.cpu_count()} logicznych")
    try:
        with open("/proc/cpuinfo") as f:
            print(f"wirtualizacja    {'tak' if 'hypervisor' in f.read() else 'nie wykryto'}")
    except FileNotFoundError:
        pass
    print(f"OpenVINO         {ov.__version__.split('-')[0]}")
    print("=" * 68)

    amx = sorted(f for f in flags if f.startswith("amx_"))
    print(f"\nAMX              {' '.join(amx) if amx else 'BRAK'}")
    for flag in ("avx512_bf16", "avx512_fp16", "avx512_vnni", "avx512f", "avx2"):
        print(f"{flag:17}{'jest' if flag in flags else '—'}")

    print(f"\nOpenVINO widzi   {caps}")

    model = tiny_model()
    default = core.compile_model(model, "CPU")
    forced = core.compile_model(model, "CPU", {"INFERENCE_PRECISION_HINT": "f32"})
    auto_precision = default.get_property("INFERENCE_PRECISION_HINT").get_type_name()
    print(f"\ndomyślna precyzja jąder    {auto_precision}")
    print(f"po wymuszeniu f32          {forced.get_property('INFERENCE_PRECISION_HINT').get_type_name()}")

    print("\n" + "-" * 68)
    if amx and "BF16" in caps:
        print("WERDYKT: ten CPU ma AMX.")
        print("  * runtime sam przechodzi na bf16 — twój 'baseline FP32' JEST już przyspieszony")
        print("  * porównując FP32 z INT8 wymuś f32, inaczej mierzysz bf16 vs int8")
        print("  * po INT8 spodziewaj się głównie mniejszego modelu, nie wielkiego przyspieszenia")
    elif "avx512_vnni" in flags or "avx2" in flags:
        print("WERDYKT: brak AMX, ale jest przyspieszenie dla int8 (VNNI/AVX).")
        print("  * hint bf16 zostanie zignorowany — to hint, nie gwarancja")
        print("  * INT8 jest tu głównym źródłem przyspieszenia, spodziewaj się realnego zysku")
    else:
        print("WERDYKT: brak sprzętowego przyspieszenia dla int8/bf16.")
        print("  * po kwantyzacji spodziewaj się mniejszego modelu, prędkość może się nie zmienić")
    print("-" * 68)


if __name__ == "__main__":
    main()
