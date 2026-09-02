# Od czego zacząć

W tym repo są cztery projekty wokół OpenVINO. Ten plik mówi, w jakiej
kolejności je uruchamiać i po czym poznać, że działają.

```bash
./sprawdz.sh
```

Sprawdza Pythona, Dockera, klucz do serwera i połączenie — a potem wypisuje,
co możesz zrobić teraz. Zacznij od tego.

## Co tu jest

| katalog | co to jest | potrzebuje |
|---|---|---|
| `benchmark/` | pięć metod wyszukiwania na twojej prezentacji + lekcja matematyki | nic |
| `openvino-demo/` | kwantyzacja INT8 z pomiarem dokładności na dwóch procesorach | `pip install` |
| `asystent/` | pytania o twoje dokumenty w terminalu, z głosem | klucz do serwera |
| `openwebui/` | to samo, ale z interfejsem w przeglądarce | Docker + klucz |
| `genai/` | czy Prompt Lookup przyspiesza właśnie odpowiedzi RAG-owe | model lokalnie |

## Kolejność

### 1. Matematyka — 2 minuty, nic nie instalujesz

```bash
cd benchmark && python3 jak_to_dziala.py
```

Wyszukiwanie semantyczne rozpisane na trzech liczbach, krok po kroku.
**Gotowe, gdy** rozumiesz, dlaczego tekst A dostał 1.000, a B i C po 0.000.
Pozmieniaj `TEKSTY` w pliku i odpal ponownie.

### 2. Twój procesor — 30 sekund

```bash
cd openvino-demo && pip install -r requirements.txt && python3 check_cpu.py
```

**Gotowe, gdy** wiesz, czy masz AMX. To rozstrzyga, czy kwantyzacja da ci
przyspieszenie, czy tylko mniejszy model — czyli którą połowę historii o INT8
opowiadasz.

### 3. Benchmark wyszukiwania

```bash
cd benchmark && python3 benchmark.py
```

Bez klucza policzy same warianty BM25 (76% i 80% recall@3). Z kluczem dojdą
embeddingi, reranker i model nawigujący po spisie treści.

**Gotowe, gdy** widzisz, czy embeddingi wygrywają na parafrazach — tam BM25 ma
tylko 50%.

### 4. Asystent w terminalu

```bash
cd asystent
python3 client.py                      # co serwer faktycznie potrafi
python3 ingest.py ../rag-is-dead       # zbuduj indeks z prezentacji
python3 asystent.py "Kto to Boris Cherny?"
```

**Gotowe, gdy** przejdzie test na zmyślanie: zapytaj o coś, czego w dokumentach
nie ma („jaka jest stolica Australii"). Dobra odpowiedź to „nie wiem".

### 5. Interfejs webowy

```bash
cd openwebui && docker compose up -d      # http://localhost:3000
```

**Gotowe, gdy** w Admin Panel → Settings → Documents widzisz silnik `openai`
i model `multilingual-e5-large-int8` — a nie domyślny model kontenera.

## Gdy coś nie działa

| objaw | przyczyna |
|---|---|
| `Brak klucza` | `export INFER_KEY="sk-infer-..."` — działa tylko w tym oknie terminala |
| `Brak indeksu` | najpierw `python3 ingest.py <katalog>` |
| Serwer HTTP 401 | zły klucz albo wygasł — zapytaj kolegę |
| Zmiany w `docker-compose.yml` nic nie dają | Open WebUI zapisuje konfigurację przy pierwszym starcie, patrz `openwebui/README.md` |
| `SyntaxError` w skryptach | Python starszy niż 3.10 |

## Zanim wrzucisz gdziekolwiek firmowe dokumenty

`asystent/` i `openwebui/` wysyłają treść plików na serwer inferencji. Jeśli
serwer nie jest twój, wysyłasz je komuś. Ustal czyj jest i co loguje — przy
danych osobowych to nie formalność.
