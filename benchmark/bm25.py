"""BM25 — klasyczne wyszukiwanie słów kluczowych, punkt odniesienia bez AI.

Implementacja własna (~40 linii), żeby nie ciągnąć zależności i żeby było
widać, co dokładnie liczymy.

Wariant `stem=True` obcina końcówki fleksyjne prymitywnie, po długości. To nie
jest poprawny stemmer polskiego — to najtańsza możliwa proteza, i właśnie o to
chodzi: pokazuje, ile daje sama świadomość, że polski odmienia słowa.
"""

import math
import re
from collections import Counter

WORD = re.compile(r"\w+", re.UNICODE)

K1 = 1.5   # nasycenie częstością termu
B = 0.75   # waga normalizacji długości dokumentu
STEM_KEEP = 6


def tokenize(text: str, stem: bool = False) -> list[str]:
    words = [w.lower() for w in WORD.findall(text) if len(w) > 1]
    return [w[:STEM_KEEP] for w in words] if stem else words


class BM25:
    def __init__(self, docs: list[str], stem: bool = False):
        self.stem = stem
        self.tokens = [tokenize(d, stem) for d in docs]
        self.lengths = [len(t) for t in self.tokens]
        self.avg_len = sum(self.lengths) / len(self.tokens)
        self.freqs = [Counter(t) for t in self.tokens]

        seen = Counter()
        for t in self.tokens:
            seen.update(set(t))
        n = len(self.tokens)
        # IDF w wariancie z wygładzeniem — nigdy ujemny
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in seen.items()}

    def scores(self, query: str) -> list[float]:
        terms = tokenize(query, self.stem)
        out = []
        for freq, length in zip(self.freqs, self.lengths):
            score = 0.0
            for term in terms:
                if term not in freq:
                    continue
                tf = freq[term]
                norm = tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / self.avg_len))
                score += self.idf[term] * norm
            out.append(score)
        return out


if __name__ == "__main__":
    from corpus import load
    from questions import QUESTIONS, gold_ids

    chunks = load()
    for stem in (False, True):
        engine = BM25([f"{c.title}\n{c.text}" for c in chunks], stem=stem)
        hits = 0
        for q in QUESTIONS:
            gold = gold_ids(q, chunks)
            best = max(range(len(chunks)), key=lambda i: engine.scores(q.text)[i])
            hits += chunks[best].id in gold
        print(f"BM25 {'ze stemmingiem' if stem else 'bez stemmingu':16} recall@1 = {hits}/{len(QUESTIONS)}")
