"""Wspólne elementy: preprocessing ImageNet i zbiór ewaluacyjny."""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent
DATA = ROOT / "data"
IMAGES = DATA / "imagenet-sample-images"
ONNX_MODEL = DATA / "resnet50-v1-12.onnx"
IR_FP32 = DATA / "resnet50_fp32.xml"
IR_INT8 = DATA / "resnet50_int8.xml"

# Standardowa normalizacja ImageNet, wymagana przez resnet50-v1-12.
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess(path: Path) -> np.ndarray:
    """JPEG -> tensor NCHW 1x3x224x224: resize 256, center crop 224, normalizacja."""
    img = Image.open(path).convert("RGB")

    w, h = img.size
    scale = 256 / min(w, h)
    img = img.resize((round(w * scale), round(h * scale)), Image.BILINEAR)

    w, h = img.size
    left, top = (w - 224) // 2, (h - 224) // 2
    img = img.crop((left, top, left + 224, top + 224))

    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - MEAN) / STD
    return arr.transpose(2, 0, 1)[None, ...]


def dataset() -> list[tuple[Path, int]]:
    """Pary (ścieżka, prawdziwa klasa).

    Pliki nazywają się nXXXXXXXX_nazwa.JPEG, a indeksy klas ImageNet-1k są
    zdefiniowane jako posortowana kolejność identyfikatorów synsetów — więc
    pozycja pliku po sortowaniu JEST etykietą. Ground truth za darmo.
    """
    files = sorted(IMAGES.glob("n*.JPEG"))
    if len(files) != 1000:
        raise RuntimeError(f"Oczekiwano 1000 obrazów, znaleziono {len(files)}. Uruchom prepare.py")
    return [(f, i) for i, f in enumerate(files)]


def label_name(index: int) -> str:
    """Czytelna nazwa klasy, wyciągnięta z nazwy pliku."""
    return sorted(IMAGES.glob("n*.JPEG"))[index].stem.split("_", 1)[1].replace("_", " ")


CACHE = DATA / "preprocessed.npy"


def cached_inputs() -> np.ndarray:
    """Wszystkie 1000 zdjęć przetworzonych raz, trzymane jako memmap na dysku.

    Preprocessing to ~90 s; inferencja to sekundy. Bez cache'a mierzylibyśmy
    głównie Pillow, a nie OpenVINO.
    """
    samples = dataset()
    if not CACHE.exists():
        print(f"Preprocessing {len(samples)} zdjęć (jednorazowo)...")
        out = np.lib.format.open_memmap(
            CACHE, mode="w+", dtype=np.float32, shape=(len(samples), 3, 224, 224)
        )
        for i, (path, _) in enumerate(samples):
            out[i] = preprocess(path)[0]
        out.flush()
    return np.load(CACHE, mmap_mode="r")


def labels() -> np.ndarray:
    return np.arange(len(dataset()), dtype=np.int64)
