"""Klient serwera inferencji (API zgodne z OpenAI) + cache na dysku.

Cache jest tu z dwóch powodów. Po pierwsze serwer należy do kogoś innego i nie
wypada go orać przy każdym uruchomieniu. Po drugie benchmark powtarzany kilka
razy musi dawać ten sam wynik — a nie zależny od tego, czy sieć akurat kichnęła.

Konfiguracja przez zmienne środowiskowe:
    export INFER_KEY="sk-infer-..."
    export INFER_URL="https://biuro.cdest.eu:11437/v1"   # opcjonalnie
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("INFER_URL", "https://biuro.cdest.eu:11437/v1").rstrip("/")
API_KEY = os.environ.get("INFER_KEY", "")

EMBED_MODEL = "multilingual-e5-large-int8"
RERANK_MODEL = "ms-marco-MiniLM-L6-v2-int8-ov"
CHAT_MODEL = "qwen3-14b-int4-ov"

CACHE_DIR = Path(__file__).parent / ".cache"
TIMEOUT = 180


class ServerError(RuntimeError):
    pass


def _cache_path(kind: str, payload: dict) -> Path:
    key = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]
    return CACHE_DIR / kind / f"{key}.json"


def post(path: str, payload: dict, cache_as: str | None = None, retries: int = 3):
    """POST z cache'em na dysku i ponowieniem przy błędach przejściowych."""
    if cache_as:
        cached = _cache_path(cache_as, payload)
        if cached.exists():
            return json.loads(cached.read_text())

    if not API_KEY:
        raise ServerError("Brak klucza. Ustaw: export INFER_KEY='sk-infer-...'")

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )

    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                result = json.loads(response.read())
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (400, 401, 403, 404):          # nie ma sensu ponawiać
                raise ServerError(f"HTTP {e.code} na {path}: {body}") from None
            last = f"HTTP {e.code}: {body}"
        except Exception as e:                           # timeout, reset połączenia
            last = repr(e)
        time.sleep(2 ** attempt)
    else:
        raise ServerError(f"{path} nie odpowiada po {retries} próbach: {last}")

    if cache_as:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(result, ensure_ascii=False))
    return result


def embed(texts: list[str], batch: int = 16) -> list[list[float]]:
    """Wektory dla listy tekstów. Przedrostki 'query:'/'passage:' dokłada wywołujący."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch):
        chunk = texts[i : i + batch]
        data = post("/embeddings", {"model": EMBED_MODEL, "input": chunk}, cache_as="embed")
        vectors.extend(item["embedding"] for item in sorted(data["data"], key=lambda d: d["index"]))
    return vectors


def rerank(query: str, documents: list[str]) -> list[float]:
    """Punktacja trafności z cross-encodera. Zwraca wynik dla każdego dokumentu."""
    data = post("/rerank", {"model": RERANK_MODEL, "query": query, "documents": documents},
                cache_as="rerank")
    rows = data.get("results") or data.get("data") or []
    scores = [0.0] * len(documents)
    for row in rows:
        idx = row.get("index", row.get("document_index"))
        scores[idx] = row.get("relevance_score", row.get("score", 0.0))
    return scores


def chat(messages: list[dict], max_tokens: int = 400, temperature: float = 0.0) -> str:
    data = post("/chat/completions", {
        "model": CHAT_MODEL, "messages": messages,
        "max_tokens": max_tokens, "temperature": temperature,
    }, cache_as="chat")
    return data["choices"][0]["message"]["content"]


def models() -> list[str]:
    request = urllib.request.Request(f"{BASE_URL}/models",
                                     headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return [m["id"] for m in json.loads(response.read())["data"]]


if __name__ == "__main__":
    print(f"Serwer: {BASE_URL}")
    print(f"Klucz:  {'ustawiony' if API_KEY else 'BRAK — export INFER_KEY=...'}")
    if API_KEY:
        print(f"Modele: {models()}")
        v = embed(["query: test polaczenia"])
        print(f"Embedding OK, wymiar {len(v[0])}")
        try:
            print(f"Reranker OK: {rerank('kot', ['kot siedzi', 'samochod jedzie'])}")
        except ServerError as e:
            print(f"Reranker niedostępny: {e}")
