# Czy „RAG is dead" wytrzymuje własny benchmark?

Prezentacja w tym repo twierdzi, że wyszukiwanie wektorowe przegrywa z agentem
czytającym dokumenty bezpośrednio. To teza. Ten katalog ją **sprawdza** —
na własnym korpusie prezentacji, po polsku, pięcioma metodami naraz.

Wynik może tezę potwierdzić albo zniuansować. Obie odpowiedzi są dobre;
niesprawdzona teza nie jest.

## Porównywane metody

| metoda | co robi | AI? |
|---|---|---|
| **BM25** | klasyczne dopasowanie słów kluczowych | nie |
| **BM25+stem** | to samo, z prymitywnym obcinaniem końcówek | nie |
| **e5 (INT8)** | wyszukiwanie wektorowe, `multilingual-e5-large-int8` | tak |
| **e5 + reranker** | wektory, potem cross-encoder `ms-marco-MiniLM` przestawia kolejność | tak |
| **qwen3 po spisie** | model dostaje spis fragmentów i sam wybiera, co przeczytać | tak |

Ostatnia metoda to odpowiednik podejścia „vectorless" z prezentacji: żadnych
wektorów, model nawiguje po strukturze jak człowiek po spisie treści.

Modele chodzą na serwerze inferencyjnym pod OpenVINO — **wszystkie skwantyzowane
do INT8/INT4**, czyli w tej samej technice, którą mierzy `../openvino-demo`.

## Cztery typy pytań — i po co ten podział

Średnia po wszystkich pytaniach ukrywa to, co najciekawsze. Dlatego 25 pytań
jest podzielonych na typy, a wynik raportowany osobno dla każdego:

| typ | co sprawdza | kto powinien wygrać |
|---|---|---|
| `doslowne` | pytanie ma te same słowa co dokument | BM25 |
| `fleksja` | te same pojęcia, inna forma gramatyczna | metody rozumiejące język |
| `parafraza` | to samo znaczenie, inne słownictwo | embeddingi |
| `koncepcyjne` | odpowiedź wymaga zrozumienia, nie dopasowania | reranker / model |

**To jest właściwe pytanie badawcze.** Nie „która metoda jest najlepsza", tylko
„która metoda wygrywa na jakim rodzaju zapytania" — bo to jest wiedza, z której
da się podjąć decyzję projektową.

## Dlaczego akurat polski

Angielski prawie nie odmienia. Polski owszem: „kwantyzacja / kwantyzacji /
kwantyzacją" to dla BM25 trzy różne słowa, a dla modelu językowego jedno pojęcie.
Publiczne benchmarki retrievalu są w większości angielskie, więc **przewaga
metod semantycznych nad słowami kluczowymi powinna być w polskim większa** niż
w danych, na których te metody są zwykle reklamowane.

Wariant `BM25+stem` jest po to, żeby oddzielić dwa efekty: ile z przewagi
embeddingów bierze się z rozumienia znaczenia, a ile ze zwykłego radzenia sobie
z końcówkami. Bez tego wariantu przypisywalibyśmy semantyce coś, co załatwia
obcięcie sześciu znaków.

## Uruchomienie

```bash
export INFER_KEY="sk-infer-..."          # klucz do serwera
python3 benchmark.py
```

Bez klucza policzy same warianty BM25 — dobry sposób, żeby sprawdzić, czy
wszystko działa, zanim ruszysz cudzy serwer.

Wyniki lądują w `wyniki.json`, a odpowiedzi serwera w `.cache/` — powtórne
uruchomienie nie generuje ruchu i daje identyczny wynik.

## Wynik bez serwera (zmierzony)

56 fragmentów, 25 pytań, recall@3:

| metoda | recall@1 | recall@3 | MRR | dosłowne | fleksja | parafraza | koncepcyjne |
|---|---|---|---|---|---|---|---|
| BM25 | 52.0% | 76.0% | 63.7% | 86% | 67% | 50% | 100% |
| BM25+stem | 60.0% | 80.0% | 71.8% | 100% | 67% | 67% | 83% |

Widać już wzorzec, którego oczekiwaliśmy: samo obcięcie końcówek podnosi
dosłowne z 86% na 100% i parafrazę z 50% na 67%. Metody modelowe dojdą po
uruchomieniu z kluczem.

## Jak zdefiniowana jest poprawna odpowiedź

Wzorcem nie jest identyfikator fragmentu, tylko **fraza, która musi w nim
wystąpić** (`questions.py`). Zmiana sposobu cięcia korpusu nie unieważnia więc
całego zestawu, a `python3 questions.py` sprawdza, czy każdy wzorzec nadal
trafia w 1–3 fragmenty. Wzorzec pasujący do połowy korpusu byłby bezużyteczny
i skrypt to zgłasza.

## Ograniczenia — czytać razem z liczbami

- **Korpus jest mały** (56 fragmentów, 18 tys. znaków). Przy takiej skali
  różnice kilku punktów procentowych to pojedyncze pytania, nie trend.
- **Pytania pisała jedna osoba znająca korpus.** To wprowadza skrzywienie:
  łatwiej nieświadomie ułożyć pytanie pod metodę, którą się lubi. Podział na
  typy ogranicza ten efekt, ale go nie usuwa.
- **Serwer jest cudzy i współdzielony** — czasy odpowiedzi są orientacyjne,
  jakość wyszukiwania nie.
- **Brak porównania INT8 z FP32.** Serwer wystawia tylko wersje skwantyzowane,
  więc nie wiemy, ile jakości retrievalu kosztuje sama kwantyzacja. To osobny
  eksperyment: ten sam e5 w FP32 lokalnie, te same pytania.

## Pliki

| plik | co robi |
|---|---|
| `corpus.py` | wyciąga tekst z prezentacji i dem, tnie na fragmenty |
| `questions.py` | 25 pytań z wzorcami + walidacja wzorców |
| `bm25.py` | BM25 od zera, z opcjonalnym obcinaniem końcówek |
| `client.py` | klient serwera (OpenAI-compatible) z cache'em |
| `benchmark.py` | uruchamia wszystkie metody i drukuje tabelę |
