"""01 — Hello OpenVINO.

Buduje maleńką sieć bezpośrednio w API OpenVINO (bez pobierania niczego
z internetu), kompiluje ją na CPU i uruchamia inferencję.

    python3 01_hello_openvino.py
"""

import numpy as np
import openvino as ov
import openvino.opset13 as ops


def build_model(in_dim: int = 8, out_dim: int = 4) -> ov.Model:
    """Mini-MLP: y = relu(x @ W + b). Wagi losowe, ale deterministyczne."""
    rng = np.random.default_rng(0)
    weights = rng.standard_normal((in_dim, out_dim)).astype(np.float32)
    bias = np.zeros(out_dim, dtype=np.float32)

    x = ops.parameter([-1, in_dim], dtype=np.float32, name="input")
    y = ops.matmul(x, ops.constant(weights), transpose_a=False, transpose_b=False)
    y = ops.add(y, ops.constant(bias))
    y = ops.relu(y)
    y.set_friendly_name("output")

    return ov.Model([y], [x], "mini_mlp")


def main() -> None:
    core = ov.Core()
    print(f"OpenVINO {ov.__version__}")
    print(f"Dostępne urządzenia: {core.available_devices}")
    for device in core.available_devices:
        name = core.get_property(device, "FULL_DEVICE_NAME")
        print(f"  {device}: {name}")

    model = build_model()
    compiled = core.compile_model(model, "CPU")

    x = np.arange(8, dtype=np.float32).reshape(1, 8)
    result = compiled(x)[compiled.output(0)]

    print(f"\nwejście  {x.shape}: {x.ravel()}")
    print(f"wyjście  {result.shape}: {result.ravel().round(3)}")


if __name__ == "__main__":
    main()
