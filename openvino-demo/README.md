# OpenVINO — mały projekt na start

Trzy skrypty, od "czy w ogóle działa" do lokalnych embeddingów na CPU.
Wszystko liczone przez [Intel OpenVINO](https://docs.openvino.ai/) — bez GPU,
bez chmury, bez wysyłania tekstu na zewnątrz.

## Instalacja

```bash
pip install -r requirements.txt
```

## 1. Hello OpenVINO

```bash
python3 01_hello_openvino.py
```

Buduje mini-MLP bezpośrednio w API OpenVINO (nic nie pobiera), kompiluje go na
CPU i pokazuje, jakie urządzenia widzi runtime.

```
OpenVINO 2026.3.1
Dostępne urządzenia: ['CPU']
  CPU: Intel(R) Xeon(R) Processor @ 2.10GHz

wejście  (1, 8): [0. 1. 2. 3. 4. 5. 6. 7.]
wyjście  (1, 4): [0.    4.848 0.    0.   ]
```

## 2. Sync vs Async

```bash
python3 02_benchmark.py 300
```

Ten sam model liczony pojedynczymi wywołaniami i przez `AsyncInferQueue`.
Pomiar z tego repo (Xeon 2.10 GHz, 2 strumienie):

| tryb  | czas / 300 inf. | przepustowość | latencja |
|-------|-----------------|---------------|----------|
| sync  | 165 ms          | 1816 inf/s    | 0.55 ms  |
| async | 66 ms           | 4574 inf/s    | 0.22 ms  |

**2.5x** za samo przełączenie na kolejkę asynchroniczną i `PERFORMANCE_HINT=THROUGHPUT`.
Na maszynie z większą liczbą rdzeni różnica rośnie.

## 3. Embeddingi + wyszukiwanie semantyczne

```bash
pip install "optimum[openvino]" transformers
python3 03_embeddings.py "jak przyspieszyć model na procesorze?"
```

`all-MiniLM-L6-v2` eksportowany do IR i liczony przez OpenVINO, mean pooling,
normalizacja L2 i ranking po kosinusie. Pierwsze uruchomienie pobiera model z
Hugging Face i zapisuje IR w `ov_model/` — kolejne startują z dysku.

To dokładnie ten krok, który w klasycznym RAG-u zwykle leci do zewnętrznego API:
tutaj dzieje się lokalnie, na CPU.

## Co dalej

- kwantyzacja INT8 przez [NNCF](https://github.com/openvinotoolkit/nncf) —
  zwykle 2–4x szybciej przy minimalnej stracie jakości,
- `device="NPU"` na procesorach Core Ultra,
- `benchmark_app` z paczki OpenVINO do porównań między urządzeniami.
