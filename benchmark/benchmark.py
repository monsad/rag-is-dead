"""Pięć sposobów wyszukiwania na tym samym korpusie i tych samych pytaniach.

    export INFER_KEY="sk-infer-..."
    python3 benchmark.py

Bez klucza policzy tylko warianty BM25 — to wystarczy, żeby zobaczyć, czy
wszystko działa, zanim ruszymy cudzy serwer.
"""

import json
import re
import sys
import time
from pathlib import Path

from bm25 import BM25
from corpus import Chunk, load
from questions import QUESTIONS, Question, gold_ids

import client

TOP_K = 3
RERANK_DEPTH = 10


def _norm(vec: list[float]) -> list[float]:
    scale = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / scale for v in vec]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ─────────────────────── metody wyszukiwania ───────────────────────
# Każda dostaje pytanie i zwraca listę identyfikatorów fragmentów, od
# najtrafniejszego. Nic więcej — dzięki temu są porównywalne.

def make_bm25(chunks: list[Chunk], stem: bool):
    engine = BM25([f"{c.title}\n{c.text}" for c in chunks], stem=stem)

    def search(q: Question) -> list[str]:
        scores = engine.scores(q.text)
        order = sorted(range(len(chunks)), key=lambda i: -scores[i])
        return [chunks[i].id for i in order[:RERANK_DEPTH]]

    return search


def make_embeddings(chunks: list[Chunk]):
    # E5 wymaga przedrostków — bez nich model nie wie, co jest pytaniem,
    # a co dokumentem, i jakość spada. Najczęściej pomijany szczegół.
    vectors = [_norm(v) for v in client.embed([f"passage: {c.title}\n{c.text}" for c in chunks])]

    def search(q: Question) -> list[str]:
        query = _norm(client.embed([f"query: {q.text}"])[0])
        scores = [_dot(query, v) for v in vectors]
        order = sorted(range(len(chunks)), key=lambda i: -scores[i])
        return [chunks[i].id for i in order[:RERANK_DEPTH]]

    return search


def make_embeddings_rerank(chunks: list[Chunk], base):
    by_id = {c.id: c for c in chunks}

    def search(q: Question) -> list[str]:
        candidates = base(q)[:RERANK_DEPTH]
        docs = [f"{by_id[i].title}\n{by_id[i].text}" for i in candidates]
        scores = client.rerank(q.text, docs)
        return [i for _, i in sorted(zip(scores, candidates), key=lambda p: -p[0])]

    return search


def make_toc_agent(chunks: list[Chunk]):
    """Nawigacja po spisie treści — odpowiednik podejścia 'vectorless'.

    Model nie dostaje wektorów ani wyników wyszukiwania. Dostaje spis treści
    całego korpusu i sam wskazuje, co warto przeczytać — tak jak człowiek
    przeglądający spis rozdziałów.
    """
    toc = "\n".join(
        f"{n}. [{c.source}] {c.title} — {c.text.replace(chr(10), ' ')[:90]}"
        for n, c in enumerate(chunks, start=1)
    )

    def search(q: Question) -> list[str]:
        answer = client.chat([
            {"role": "system", "content":
             "Jesteś nawigatorem po dokumencie. Dostajesz spis fragmentów i pytanie. "
             "Wskaż numery fragmentów, które najprawdopodobniej zawierają odpowiedź. "
             "Odpowiedz WYŁĄCZNIE trzema numerami po przecinku, od najtrafniejszego. "
             "Bez wyjaśnień."},
            {"role": "user", "content": f"SPIS FRAGMENTÓW:\n{toc}\n\nPYTANIE: {q.text}\n\nNUMERY:"},
        ], max_tokens=800)

        # model bywa gadatliwy mimo instrukcji — bierzemy pierwsze sensowne liczby
        tail = answer.split("</think>")[-1]
        picked = [int(n) for n in re.findall(r"\b(\d{1,2})\b", tail) if 1 <= int(n) <= len(chunks)]
        seen, out = set(), []
        for n in picked:
            if n not in seen:
                seen.add(n)
                out.append(chunks[n - 1].id)
        return out[:TOP_K]

    return search


# ─────────────────────── pomiar ───────────────────────

def evaluate(name: str, search, chunks: list[Chunk]) -> dict:
    per_kind: dict[str, list[int]] = {}
    hits1 = hits3 = 0
    reciprocal = 0.0
    started = time.perf_counter()

    for q in QUESTIONS:
        gold = gold_ids(q, chunks)
        ranking = search(q)

        rank = next((i + 1 for i, cid in enumerate(ranking) if cid in gold), None)
        hits1 += rank == 1
        got3 = bool(rank and rank <= TOP_K)
        hits3 += got3
        reciprocal += 1 / rank if rank else 0.0
        per_kind.setdefault(q.kind, []).append(int(got3))

    total = len(QUESTIONS)
    return {
        "metoda": name,
        "recall@1": hits1 / total * 100,
        "recall@3": hits3 / total * 100,
        "mrr": reciprocal / total * 100,
        "s_na_pytanie": (time.perf_counter() - started) / total,
        "wg_typu": {k: sum(v) / len(v) * 100 for k, v in per_kind.items()},
    }


def main() -> None:
    chunks = load()
    print(f"Korpus: {len(chunks)} fragmentów · Pytania: {len(QUESTIONS)}\n")

    arms = [
        ("BM25", lambda: make_bm25(chunks, stem=False)),
        ("BM25+stem", lambda: make_bm25(chunks, stem=True)),
    ]
    if client.API_KEY:
        embeddings = make_embeddings(chunks)
        arms += [
            ("e5 (INT8)", lambda: embeddings),
            ("e5 + reranker", lambda: make_embeddings_rerank(chunks, embeddings)),
            ("qwen3 po spisie", lambda: make_toc_agent(chunks)),
        ]
    else:
        print("Brak INFER_KEY — liczę tylko BM25. Ustaw klucz, żeby dodać modele.\n")

    results = []
    for name, build in arms:
        try:
            results.append(evaluate(name, build(), chunks))
            r = results[-1]
            print(f"  {name:18} recall@3 = {r['recall@3']:5.1f}%   ({r['s_na_pytanie']:.2f} s/pytanie)")
        except client.ServerError as e:
            print(f"  {name:18} POMINIĘTE — {e}")

    kinds = ["doslowne", "fleksja", "parafraza", "koncepcyjne"]
    head = f"\n{'metoda':18}{'recall@1':>10}{'recall@3':>10}{'MRR':>8}" + "".join(f"{k:>13}" for k in kinds)
    print(head)
    print("-" * len(head.strip()))
    for r in results:
        row = f"{r['metoda']:18}{r['recall@1']:9.1f}%{r['recall@3']:9.1f}%{r['mrr']:7.1f}%"
        row += "".join(f"{r['wg_typu'].get(k, 0):12.0f}%" for k in kinds)
        print(row)

    Path("wyniki.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("\nZapisano wyniki.json")


if __name__ == "__main__":
    sys.exit(main())
