# Asystent — pytania o twoje dokumenty, lokalnie

Wskazujesz katalog z plikami. Zadajesz pytanie — tekstem albo głosem.
Dostajesz odpowiedź z odnośnikami do źródeł, opcjonalnie przeczytaną na głos.

Nic nie idzie do OpenAI ani do żadnej chmury. Wszystko liczy się na serwerze
z modelami OpenVINO — u ciebie albo u kogoś, komu ufasz.

## Po co to jest

Firmowe dokumenty, notatki, dokumentacja projektu, regulaminy — rzeczy, których
nikt nie pamięta i których nikt nie chce wysyłać do zewnętrznego API. Pytasz
zwykłym zdaniem, dostajesz odpowiedź z podaniem, z którego pliku pochodzi.

## Instalacja

Nie ma instalacji. Potrzebny sam Python 3.10+ i klucz do serwera:

```bash
export INFER_KEY="sk-infer-..."
python3 client.py            # sprawdza, co serwer faktycznie potrafi
```

`client.py` testuje każdą funkcję osobno i wypisuje, która działa. Asystent
radzi sobie również wtedy, gdy części brakuje — bez rerankera wyszukuje
gorzej, ale działa; bez syntezy mowy po prostu nie czyta na głos.

## Użycie

```bash
python3 ingest.py ~/dokumenty          # zbuduj indeks (raz)
python3 asystent.py "ile mam dni urlopu"
```

Dalej:

```bash
python3 asystent.py                    # tryb rozmowy
python3 asystent.py "..." --szukaj     # same fragmenty, bez modelu — szybkie
python3 asystent.py "..." --mow        # odpowiedź czytana na głos
python3 asystent.py --audio pytanie.m4a   # pytanie z nagrania
python3 asystent.py --nagraj 5         # nagraj 5 sekund z mikrofonu i zapytaj
```

Ponowne `ingest.py` przelicza **tylko zmienione pliki** — resztę przepisuje ze
starego indeksu. Możesz je uruchamiać po każdej zmianie w dokumentach.

Obsługiwane pliki: `.md`, `.txt`, `.html`, `.rst`, `.csv`, `.json` oraz `.pdf`
(jeśli masz `pypdf` — bez niego PDF-y są pomijane).

## Jak to działa

```
katalog plików
    ↓  ingest.py — tekst, podział na fragmenty po ~700 znaków
    ↓  multilingual-e5-large (INT8) — każdy fragment na wektor
index.json
    ↓
pytanie (tekst lub głos → whisper)
    ↓  e5 — pytanie na wektor, 20 najbliższych fragmentów
    ↓  ms-marco reranker — przestawia kolejność, zostaje 5
    ↓  qwen3-14b (INT4) — odpowiedź wyłącznie z tych 5, z numerami źródeł
odpowiedź  (opcjonalnie → speecht5 → głos)
```

Dwa etapy wyszukiwania, bo robią różne rzeczy: wektory szybko zawężają tysiące
fragmentów do dwudziestu, reranker dokładnie ocenia te dwadzieścia. Odwrotnie
się nie da — reranker na całym zbiorze byłby nie do zniesienia wolny.

Model dostaje instrukcję, żeby odpowiadać **wyłącznie z dostarczonych
fragmentów** i przyznawać się, gdy odpowiedzi tam nie ma. To nie gwarancja, ale
bardzo ogranicza zmyślanie — a numery źródeł pozwalają sprawdzić każde zdanie.

## Zanim wrzucisz tam firmowe pliki

**Treść dokumentów jest wysyłana na serwer inferencji.** Jeśli serwer nie jest
twój, to znaczy, że wysyłasz je komuś innemu — nawet jeśli to „tylko" kolega
z pracy i nawet jeśli sieć jest wewnętrzna.

To nie jest powód, żeby z tego nie korzystać. To powód, żeby najpierw ustalić,
czyj jest ten serwer, co loguje i jak długo trzyma dane. Przy dokumentach
z danymi osobowymi to nie jest formalność, tylko wymóg.

Do własnego serwera: `export INFER_URL="https://twoj-serwer:11437/v1"`.

## Ograniczenia

- **Podział po akapitach** — długa tabela rozjedzie się na kilka fragmentów.
  To ten sam problem, który krytykuje prezentacja w tym repo; tutaj też jest.
- **Indeks w JSON, wczytywany w całości** — do kilkudziesięciu tysięcy
  fragmentów w porządku. Przy większej skali potrzebna prawdziwa baza wektorowa.
- **Jakość zależy od tego, czy odpowiedź w ogóle jest w dokumentach.** Jeśli nie
  ma, dobry asystent ma powiedzieć „nie wiem" — i o to jest poproszony.
- **Whisper i synteza mowy nie były przetestowane** przez autora tego kodu na
  żywym serwerze; ścieżka tekstowa była. Jeśli audio nie zadziała, `client.py`
  powie, na czym się wywraca.

## Pliki

| plik | co robi |
|---|---|
| `client.py` | rozmowa z serwerem: wektory, reranking, czat, mowa |
| `ingest.py` | katalog dokumentów → `index.json` |
| `asystent.py` | wyszukiwanie, odpowiedź, tryb rozmowy, głos |
