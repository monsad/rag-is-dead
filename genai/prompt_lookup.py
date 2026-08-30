"""Czy Prompt Lookup decoding przyspiesza właśnie odpowiedzi RAG-owe?

HIPOTEZA
    Prompt Lookup decoding zgaduje kolejne tokeny, szukając w PROMPCIE fragmentu,
    który zaczyna się tak samo jak to, co model właśnie pisze. Trafione zgadnięcie
    jest darmowe — model weryfikuje kilka tokenów naraz zamiast liczyć je po kolei.

    Odpowiedź RAG-owa w dużej części CYTUJE dostarczony kontekst. Odpowiedź "z
    głowy" nie ma czego cytować. Więc przyspieszenie powinno pojawić się przy
    RAG-u i zniknąć bez kontekstu.

    Jeśli tak jest — mamy optymalizację, która działa dokładnie tam, gdzie
    generowanie odpowiedzi z wyszukanych fragmentów, i nigdzie indziej.

GRUPA KONTROLNA
    Te same pytania bez kontekstu. Bez niej nie odróżnisz "prompt lookup działa"
    od "prompt lookup działa na tym modelu zawsze".

KONTROLA POPRAWNOŚCI
    Prompt lookup jest bezstratny względem dekodowania zachłannego — ma zwracać
    DOKŁADNIE ten sam tekst, tylko szybciej. Skrypt to sprawdza. Rozjazd oznacza
    błąd konfiguracji, nie ciekawy wynik.

Model trzeba najpierw wyeksportować do formatu OpenVINO:

    pip install "optimum[openvino]" openvino-genai
    optimum-cli export openvino --model Qwen/Qwen2.5-1.5B-Instruct \
        --weight-format int4 ./model

    python3 prompt_lookup.py ./model
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmark"))

import openvino_genai as ov_genai

from corpus import load
from questions import QUESTIONS, gold_ids

MAX_NEW_TOKENS = 200
NGRAM = 3            # ile tokenów musi się zgodzić, żeby uznać trafienie
CANDIDATES = 5       # ile tokenów zgadujemy naprzód


def build_prompts(limit: int = 8) -> tuple[list[str], list[str]]:
    """Dwie grupy promptów na tych samych pytaniach: z kontekstem i bez."""
    chunks = {c.id: c for c in load()}
    rag, bare = [], []

    for q in QUESTIONS:
        gold = sorted(gold_ids(q, list(chunks.values())))
        if not gold:
            continue
        context = "\n\n".join(chunks[i].text for i in gold[:2])
        rag.append(
            "Odpowiedz na pytanie WYŁĄCZNIE na podstawie poniższego fragmentu. "
            "Cytuj go dosłownie tam, gdzie to możliwe.\n\n"
            f"FRAGMENT:\n{context}\n\nPYTANIE: {q.text}\n\nODPOWIEDŹ:"
        )
        bare.append(
            "Odpowiedz na pytanie na podstawie własnej wiedzy. "
            "Odpowiedz wyczerpująco, kilkoma zdaniami.\n\n"
            f"PYTANIE: {q.text}\n\nODPOWIEDŹ:"
        )
        if len(rag) >= limit:
            break

    return rag, bare


def make_config(lookup: bool) -> ov_genai.GenerationConfig:
    cfg = ov_genai.GenerationConfig()
    cfg.max_new_tokens = MAX_NEW_TOKENS
    cfg.do_sample = False           # zachłannie — żeby oba przebiegi były porównywalne
    if lookup:
        cfg.max_ngram_size = NGRAM
        cfg.num_assistant_tokens = CANDIDATES
        assert cfg.is_prompt_lookup(), "prompt lookup się nie włączył"
    return cfg


def run(pipe, prompts: list[str], lookup: bool) -> tuple[list[float], list[str]]:
    cfg = make_config(lookup)
    speeds, texts = [], []
    for prompt in prompts:
        result = pipe.generate(prompt, cfg)
        metrics = result.perf_metrics
        speeds.append(metrics.get_throughput().mean)
        texts.append(result.texts[0] if hasattr(result, "texts") else str(result))
    return speeds, texts


def main() -> None:
    model_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "./model")
    if not model_dir.exists():
        sys.exit(f"Brak modelu w {model_dir}. Instrukcja eksportu na górze pliku.")

    print(f"Model: {model_dir}   n-gram: {NGRAM}   kandydatów: {CANDIDATES}\n")
    pipe = ov_genai.LLMPipeline(str(model_dir), "CPU")

    rag, bare = build_prompts()
    print(f"{len(rag)} promptów RAG-owych (z kontekstem) i tyle samo bez kontekstu\n")

    results = {}
    for nazwa, prompts in (("RAG (z kontekstem)", rag), ("bez kontekstu", bare)):
        print(f"  {nazwa}...")
        base_speed, base_text = run(pipe, prompts, lookup=False)
        look_speed, look_text = run(pipe, prompts, lookup=True)
        identyczne = sum(a.strip() == b.strip() for a, b in zip(base_text, look_text))
        results[nazwa] = {
            "bez": statistics.median(base_speed),
            "z": statistics.median(look_speed),
            "identyczne": identyczne,
            "n": len(prompts),
        }

    head = f"\n{'grupa':22}{'bez lookup':>13}{'z lookup':>12}{'zysk':>9}{'ten sam tekst':>16}"
    print(head)
    print("-" * len(head.strip()))
    for nazwa, r in results.items():
        print(f"{nazwa:22}{r['bez']:10.1f} t/s{r['z']:9.1f} t/s"
              f"{r['z'] / r['bez']:8.2f}x{r['identyczne']:>12}/{r['n']}")

    zysk_rag = results["RAG (z kontekstem)"]["z"] / results["RAG (z kontekstem)"]["bez"]
    zysk_bez = results["bez kontekstu"]["z"] / results["bez kontekstu"]["bez"]
    print(f"\nHipoteza zakładała zysk przy RAG-u i brak zysku bez kontekstu.")
    print(f"Wyszło: {zysk_rag:.2f}x przy RAG-u, {zysk_bez:.2f}x bez kontekstu "
          f"— różnica {zysk_rag / zysk_bez:.2f}x")

    rozjazdy = sum(r["n"] - r["identyczne"] for r in results.values())
    if rozjazdy:
        print(f"\nUWAGA: {rozjazdy} odpowiedzi się różni. Prompt lookup ma być bezstratny —")
        print("sprawdź, czy do_sample jest wyłączone i czy model nie ucina po max_new_tokens.")


if __name__ == "__main__":
    main()
