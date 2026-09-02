"""Klient serwera inferencji: tekst, wektory, reranking, mowa.

Samodzielny — ten katalog da się skopiować na inną maszynę i uruchomić.
Wymaga tylko standardowego Pythona.

    export INFER_KEY="sk-infer-..."
    export INFER_URL="https://biuro.cdest.eu:11437/v1"   # opcjonalnie
"""

import json
import mimetypes
import os
import secrets
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("INFER_URL", "https://biuro.cdest.eu:11437/v1").rstrip("/")
API_KEY = os.environ.get("INFER_KEY", "")

EMBED_MODEL = os.environ.get("INFER_EMBED", "multilingual-e5-large-int8")
RERANK_MODEL = os.environ.get("INFER_RERANK", "ms-marco-MiniLM-L6-v2-int8-ov")
CHAT_MODEL = os.environ.get("INFER_CHAT", "qwen3-14b-int4-ov")
ASR_MODEL = os.environ.get("INFER_ASR", "whisper-large-v3-int8-ov")
TTS_MODEL = os.environ.get("INFER_TTS", "speecht5-tts-ov")

TIMEOUT = 300


class ServerError(RuntimeError):
    pass


def _request(path: str, data: bytes, content_type: str, retries: int = 3) -> bytes:
    if not API_KEY:
        raise ServerError("Brak klucza. Ustaw: export INFER_KEY='sk-infer-...'")

    last = None
    for attempt in range(retries):
        req = urllib.request.Request(
            f"{BASE_URL}{path}", data=data,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": content_type},
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code in (400, 401, 403, 404, 422):
                raise ServerError(f"HTTP {e.code} na {path}: {body}") from None
            last = f"HTTP {e.code}: {body}"
        except Exception as e:
            last = repr(e)
        time.sleep(2 ** attempt)
    raise ServerError(f"{path} nie odpowiada po {retries} próbach: {last}")


def _post_json(path: str, payload: dict) -> dict:
    return json.loads(_request(path, json.dumps(payload).encode(), "application/json"))


def embed(texts: list[str], batch: int = 16) -> list[list[float]]:
    """Wektory dla listy tekstów. Przedrostki 'query:'/'passage:' dokłada wywołujący."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch):
        data = _post_json("/embeddings", {"model": EMBED_MODEL, "input": texts[i : i + batch]})
        out.extend(row["embedding"] for row in sorted(data["data"], key=lambda d: d["index"]))
    return out


def rerank(query: str, documents: list[str]) -> list[float]:
    """Trafność każdego dokumentu wg cross-encodera. 0.0 gdy serwer nie ma tego endpointu."""
    data = _post_json("/rerank", {"model": RERANK_MODEL, "query": query, "documents": documents})
    scores = [0.0] * len(documents)
    for row in data.get("results") or data.get("data") or []:
        idx = row.get("index", row.get("document_index"))
        if idx is not None and idx < len(scores):
            scores[idx] = row.get("relevance_score", row.get("score", 0.0))
    return scores


def chat(messages: list[dict], max_tokens: int = 700, temperature: float = 0.2) -> str:
    data = _post_json("/chat/completions", {
        "model": CHAT_MODEL, "messages": messages,
        "max_tokens": max_tokens, "temperature": temperature,
    })
    text = data["choices"][0]["message"]["content"]
    return text.split("</think>")[-1].strip()   # modele Qwen bywają gadatliwe „na głos"


def transcribe(audio: Path) -> str:
    """Nagranie -> tekst (Whisper). Multipart budowany ręcznie, bez zależności."""
    boundary = f"----ovbound{secrets.token_hex(12)}"
    mime = mimetypes.guess_type(audio.name)[0] or "application/octet-stream"

    parts: list[bytes] = []
    for name, value in (("model", ASR_MODEL), ("response_format", "json")):
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
        )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{audio.name}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n".encode()
    )
    parts.append(audio.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())

    raw = _request("/audio/transcriptions", b"".join(parts), f"multipart/form-data; boundary={boundary}")
    try:
        return json.loads(raw).get("text", "").strip()
    except json.JSONDecodeError:
        return raw.decode(errors="replace").strip()


def speak(text: str, out: Path, voice: str = "alloy") -> Path:
    """Tekst -> plik audio. Zwraca ścieżkę zapisanego pliku."""
    payload = {"model": TTS_MODEL, "input": text, "voice": voice, "response_format": "wav"}
    audio = _request("/audio/speech", json.dumps(payload).encode(), "application/json")
    out.write_bytes(audio)
    return out


def models() -> list[str]:
    req = urllib.request.Request(f"{BASE_URL}/models", headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return [m["id"] for m in json.loads(response.read())["data"]]


def sprawdz() -> dict[str, str]:
    """Sprawdza po kolei każdą funkcję serwera. Asystent działa nawet gdy część padnie."""
    status = {}
    for nazwa, probe in (
        ("modele", lambda: ", ".join(models())),
        ("embeddingi", lambda: f"wymiar {len(embed(['query: test'])[0])}"),
        ("reranker", lambda: f"{rerank('kot', ['kot śpi', 'auto jedzie'])}"),
        ("czat", lambda: chat([{"role": "user", "content": "Odpowiedz jednym słowem: działasz?"}],
                              max_tokens=2000)[:40]),
    ):
        try:
            status[nazwa] = f"OK — {probe()}"
        except Exception as e:
            status[nazwa] = f"NIEDOSTĘPNE — {e}"
    return status


if __name__ == "__main__":
    print(f"Serwer: {BASE_URL}")
    if not API_KEY:
        print("Klucz:  BRAK — export INFER_KEY='sk-infer-...'")
        raise SystemExit(1)
    for nazwa, wynik in sprawdz().items():
        print(f"  {nazwa:12} {wynik}")
