"""Zestaw pytań testowych z wzorcową odpowiedzią.

Wzorzec to FRAZA, która musi wystąpić we właściwym fragmencie — nie identyfikator.
Dzięki temu zmiana sposobu cięcia korpusu nie unieważnia całego zestawu.

Pytania są podzielone na cztery typy, bo to jest sedno eksperymentu: średnia po
wszystkich pytaniach ukrywa to, co ciekawe. Każda metoda wygrywa gdzie indziej.

  doslowne    — pytanie zawiera dokładnie te słowa co dokument (przewaga BM25)
  fleksja     — te same pojęcia, inna forma gramatyczna (test polskiej odmiany)
  parafraza   — to samo znaczenie, inne słownictwo (przewaga embeddingów)
  koncepcyjne — odpowiedź wymaga zrozumienia, nie dopasowania (przewaga rerankera)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    text: str
    gold: str      # fraza, która musi być we właściwym fragmencie
    kind: str


QUESTIONS = [
    # ─── dosłowne: słowa kluczowe wprost z korpusu ───
    Question("Kto powiedział, że wyszukiwanie agentowe działa lepiej niż RAG?", "Boris Cherny", "doslowne"),
    Question("Ile typów encji ma OmegaWiki?", "9 typów encji", "doslowne"),
    Question("Jaki jest koszt jednego zapytania w Agentic File Search?", "$0.001", "doslowne"),
    Question("Jaki wynik osiągnął Haiku z advisorem Opus na BrowseComp?", "41.2%", "doslowne"),
    Question("Ile tokenów liczy odpowiedź Advisora?", "400–700 tokenów", "doslowne"),
    Question("Po jakim czasie staleness check blokuje wywołania narzędzi?", "nie były aktualizowane od N sekund", "doslowne"),
    Question("Na czym polega Context Engineering?", "celowo strukturyzujesz co model widzi", "doslowne"),

    # ─── fleksja: inna forma gramatyczna niż w dokumencie ───
    Question("Po co komu proweniencja w bazie wiedzy?", "Proweniencja jest obowiązkowa", "fleksja"),
    Question("Jak chunkowanie wpływa na tabele finansowe?", "Chunking niszczy strukturę", "fleksja"),
    Question("Do czego służą pliki kognitywne agentowi?", "pliki kognitywne", "fleksja"),
    Question("Czym zajmuje się dispatcher w architekturze wielowarstwowej?", "Dispatcher", "fleksja"),
    Question("Jakie są typy relacji między encjami?", "9 typów relacji", "fleksja"),
    Question("Na czym polega hierarchiczne drzewo dokumentu?", "Hierarchiczne drzewo", "fleksja"),

    # ─── parafraza: to samo znaczenie, inne słowa ───
    Question("Dlaczego rozbijanie dokumentu na kawałki bywa szkodliwe?", "niszczy strukturę", "parafraza"),
    Question("Co zrobić, gdy model po dłuższej pracy zapomina, co miał robić?", "Attention Decay", "parafraza"),
    Question("Jak obsłużyć proste zadania bez płacenia za najdroższy model?", "Dispatcher", "parafraza"),
    Question("Dlaczego nie wiadomo, skąd wzięła się odpowiedź systemu?", "Black box retrieval", "parafraza"),
    Question("Co się dzieje z wektorami, gdy dokument się zmienia?", "Embedding drift", "parafraza"),
    Question("Gdzie agent zapisuje odkrycia, żeby nie zginęły przy przesunięciu kontekstu?", "odkrycia zapisywane od razu", "parafraza"),

    # ─── koncepcyjne: wymaga zrozumienia, nie dopasowania słów ───
    Question("Czy powiększenie okna kontekstu do miliona tokenów załatwi sprawę?", "Podnoszą sufit", "koncepcyjne"),
    Question("Kiedy klasyczne podejście wektorowe nadal się broni?", "RAG nadal ma sens", "koncepcyjne"),
    Question("Co wybrać do przeszukiwania długich raportów PDF?", "Długie PDF-y, raporty", "koncepcyjne"),
    Question("Od czego zacząć projektowanie systemu wyszukiwania?", "Zawsze zaczynasz od natury danych", "koncepcyjne"),
    Question("Czy taka wiki nie zamieni się z czasem w śmietnik?", "slop", "koncepcyjne"),
    Question("Jak podzielić pracę między model duży i mały?", "Mniejszy model zbiera kontekst", "koncepcyjne"),
]


def gold_ids(question: Question, chunks) -> set[str]:
    """Fragmenty uznane za poprawną odpowiedź — te, które zawierają wzorcową frazę."""
    needle = question.gold.lower()
    return {c.id for c in chunks if needle in c.text.lower()}


if __name__ == "__main__":
    from collections import Counter

    from corpus import load

    chunks = load()
    print(f"{len(QUESTIONS)} pytań, {len(chunks)} fragmentów")
    print(Counter(q.kind for q in QUESTIONS), "\n")

    problems = 0
    for q in QUESTIONS:
        ids = gold_ids(q, chunks)
        if not ids:
            print(f"  BRAK DOPASOWANIA  {q.kind:12} {q.text}\n     wzorzec: {q.gold!r}")
            problems += 1
        elif len(ids) > 3:
            print(f"  ZBYT OGÓLNY ({len(ids)})  {q.kind:12} {q.gold!r}")
            problems += 1

    print(f"\n{'wszystkie wzorce OK' if not problems else f'{problems} do poprawy'}")
