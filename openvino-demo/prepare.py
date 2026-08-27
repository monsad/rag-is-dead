"""Pobiera to, na czym liczy reszta projektu: model i zbiór ewaluacyjny.

  * ResNet-50 v1 (FP32, ONNX Model Zoo) — 98 MB
  * 1000 zdjęć ImageNet, po jednym na klasę — etykieta zapisana w nazwie pliku

    python3 prepare.py
"""

import subprocess
import urllib.request

from common import DATA, IMAGES, ONNX_MODEL

MODEL_URL = (
    "https://media.githubusercontent.com/media/onnx/models/main/"
    "validated/vision/classification/resnet/model/resnet50-v1-12.onnx"
)
IMAGES_REPO = "https://github.com/EliSchwartz/imagenet-sample-images.git"


def main() -> None:
    DATA.mkdir(exist_ok=True)

    if ONNX_MODEL.exists():
        print(f"Model już jest: {ONNX_MODEL.name}")
    else:
        print(f"Pobieram {MODEL_URL.rsplit('/', 1)[-1]} (~98 MB)...")
        urllib.request.urlretrieve(MODEL_URL, ONNX_MODEL)

    if IMAGES.exists():
        print(f"Zdjęcia już są: {len(list(IMAGES.glob('n*.JPEG')))} plików")
    else:
        print("Klonuję zbiór 1000 zdjęć ImageNet...")
        subprocess.run(["git", "clone", "--depth", "1", IMAGES_REPO, str(IMAGES)], check=True)

    print("\nGotowe. Dalej:  python3 quantize.py  a potem  python3 evaluate.py")


if __name__ == "__main__":
    main()
