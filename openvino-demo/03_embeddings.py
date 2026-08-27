"""03 — Embeddingi lokalnie na CPU przez OpenVINO + mini-retrieval.

Model zdaniowy z Hugging Face jest eksportowany do IR i liczony przez
OpenVINO — bez GPU, bez API, bez wysyłania tekstu na zewnątrz.
Na końcu: proste wyszukiwanie semantyczne po kosinusie.

Wymaga dodatkowych paczek (patrz requirements.txt):
    pip install "optimum[openvino]" transformers

    python3 03_embeddings.py "twoje pytanie"

Pierwsze uruchomienie pobiera model z Hugging Face i zapisuje IR w ./ov_model,
kolejne startują już z dysku.
"""

import sys
from pathlib import Path

import numpy as np

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
IR_DIR = Path(__file__).parent / "ov_model"

DOCS = [
    "OpenVINO to toolkit Intela do inferencji modeli na CPU, GPU i NPU.",
    "Kwantyzacja INT8 przez NNCF potrafi przyspieszyć model kilkukrotnie.",
    "RAG dzieli dokumenty na chunki i wyszukuje je po podobieństwie wektorowym.",
    "Agent z dostępem do narzędzi może czytać pliki zamiast polegać na embeddingach.",
    "Kot śpi na parapecie i nie interesuje go żadna inferencja.",
]


def load():
    from optimum.intel import OVModelForFeatureExtraction
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if IR_DIR.exists():
        model = OVModelForFeatureExtraction.from_pretrained(IR_DIR, device="CPU")
    else:
        model = OVModelForFeatureExtraction.from_pretrained(MODEL_ID, export=True, device="CPU")
        model.save_pretrained(IR_DIR)
        tokenizer.save_pretrained(IR_DIR)
    return tokenizer, model


def encode(tokenizer, model, texts: list[str]) -> np.ndarray:
    """Mean pooling po tokenach + normalizacja L2 — standard dla MiniLM."""
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    hidden = model(**inputs).last_hidden_state.numpy()

    mask = inputs["attention_mask"].numpy()[..., None].astype(np.float32)
    pooled = (hidden * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
    return pooled / np.linalg.norm(pooled, axis=1, keepdims=True)


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "jak przyspieszyć model na procesorze?"

    tokenizer, model = load()
    doc_vecs = encode(tokenizer, model, DOCS)
    query_vec = encode(tokenizer, model, [query])[0]

    scores = doc_vecs @ query_vec

    print(f'Pytanie: "{query}"\n')
    for rank, idx in enumerate(np.argsort(-scores), start=1):
        print(f"{rank}. [{scores[idx]:.3f}] {DOCS[idx]}")


if __name__ == "__main__":
    main()
