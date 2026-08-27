# ResNet-50 na CPU: FP32 vs BF16 vs INT8

Kwantyzacja post-training (NNCF) prawdziwego ResNet-50 do INT8 pod OpenVINO,
z **pomiarem dokładności na prawdziwych danych**, a nie tylko z benchmarkiem
prędkości. Wszystko na CPU — bez GPU i bez chmury.

## Wynik

ResNet-50 v1, 1000 zdjęć ImageNet (po jednym na klasę), Xeon Sapphire Rapids
(4 vCPU, AMX + AVX512-VNNI), OpenVINO 2026.3, NNCF 3.3, kalibracja na 300 zdjęciach:

| konfiguracja | precyzja jąder | top-1 | top-5 | latencja (mediana) | p95 | przepustowość | rozmiar | zgodność z FP32 |
|---|---|---|---|---|---|---|---|---|
| FP32 (wymuszony) | f32       | 89.4% | 98.0% | 17.18 ms | 20.97 ms | 64 inf/s  | 102.5 MB | — |
| BF16 (domyślny)  | bf16      | 89.2% | 98.0% |  5.27 ms |  6.11 ms | 285 inf/s | 102.5 MB | 99.8% |
| INT8 (NNCF PTQ)  | int8+bf16 | 88.9% | 98.1% |  4.96 ms |  6.04 ms | 314 inf/s |  26.1 MB | 97.2% |

**INT8 vs FP32: 4.9x przepustowości, 3.5x niższa latencja, 3.9x mniejszy model,
kosztem 0.5 punktu procentowego top-1.**

## Niuans, który zmienia interpretację

Większość porównań „FP32 vs INT8" na nowoczesnych Xeonach mierzy coś innego, niż deklaruje.

Na procesorach z AMX (Xeon 4. generacji wzwyż) OpenVINO **domyślnie liczy model
FP32 w bfloat16** — sprawdzisz to przez `INFERENCE_PRECISION_HINT` na skompilowanym
modelu. Jeśli nie wymusisz `f32`, twoim „baseline'em" jest już zoptymalizowany bf16.

Rozbicie zysku 4.9x:

- **4.4x** to samo przejście f32 → bf16 na AMX — **zero pracy, zero kwantyzacji**,
  wystarczy nie wymuszać f32,
- **~1.1x** to faktyczny zysk INT8 ponad bf16, i na tej maszynie mieści się on
  w rozrzucie między przebiegami.

Wniosek nie brzmi „kwantyzacja nie działa", tylko: **na sprzęcie z AMX realną
wartością INT8 jest 3.9x mniejszy model, a nie prędkość**. Prędkość dostajesz
od hardware'u za darmo. Zysk z INT8 rośnie tam, gdzie AMX nie ma: starsze Xeony,
Core bez AMX, NPU, urządzenia brzegowe.

Dlatego benchmark mierzy wszystkie trzy konfiguracje, a nie dwie.

## Metodologia

Rzeczy, które łatwo zrobić źle, a które psują wynik:

- **Ground truth za darmo** — indeksy klas ImageNet-1k to posortowana kolejność
  identyfikatorów synsetów, więc pozycja pliku po sortowaniu *jest* etykietą.
  Zero ręcznego mapowania.
- **Latencja i przepustowość to osobne pomiary** — latencja przy
  `PERFORMANCE_HINT=LATENCY` (jedno zapytanie naraz), przepustowość przy
  `THROUGHPUT` z `AsyncInferQueue`. Mierzenie obu na jednej konfiguracji zaniża
  jedno albo drugie.
- **Preprocessing cache'owany na dysku** — bez tego benchmark mierzy głównie
  Pillow, nie OpenVINO.
- **Mediana z 3 powtórzeń + p95** — maszyna bywa współdzielona, pojedynczy
  pomiar potrafi się mylić o 20%.
- **Zgodność predykcji, nie tylko top-1** — INT8 trafia w tę samą klasę co FP32
  na 97.2% zdjęć. Sam top-1 (-0.5 p.p.) ukrywa, że część przypadków się zmienia
  w obie strony.

Zbiór ewaluacyjny to 1000 zdjęć (po jednym na klasę), nie oficjalne 50 000 z walidacji
ImageNet — stąd top-1 89.4% wobec ~75% raportowanych dla ResNet-50. Do porównywania
konfiguracji między sobą to wystarcza; jako bezwzględna dokładność modelu — nie.

## Uruchomienie

```bash
pip install -r requirements.txt
python3 prepare.py     # model (98 MB) + 1000 zdjęć
python3 quantize.py    # FP32 -> IR -> PTQ INT8   (~20 s)
python3 evaluate.py    # tabela powyżej           (~3 min)
```

## Pliki

| plik | co robi |
|---|---|
| `prepare.py`  | pobiera ResNet-50 ONNX i zbiór zdjęć |
| `common.py`   | preprocessing ImageNet, etykiety, cache wejść |
| `quantize.py` | ONNX → IR FP32 → kwantyzacja INT8 przez NNCF |
| `evaluate.py` | dokładność + latencja + przepustowość + rozmiar |

## Co dalej

- `device="NPU"` na Core Ultra — tam INT8 nie ma konkurencji ze strony AMX,
- `nncf.quantize_with_accuracy_control` — kwantyzacja z twardym limitem straty
  dokładności, cofa do FP32 warstwy, które psują wynik najbardziej,
- ten sam pipeline na modelu embeddingowym zamiast ResNeta — czyli lokalny
  retrieval bez API.
