# ResNet-50 na CPU: FP32 vs BF16 vs INT8

Kwantyzacja post-training (NNCF) prawdziwego ResNet-50 do INT8 pod OpenVINO,
z **pomiarem dokładności na prawdziwych danych**, a nie tylko z benchmarkiem
prędkości. Wszystko na CPU — bez GPU i bez chmury.

## Wynik

ResNet-50 v1, 1000 zdjęć ImageNet (po jednym na klasę), OpenVINO 2026.3.1,
NNCF 3.3.0, kalibracja na 300 zdjęciach. Ten sam kod i ten sam plik INT8
puszczony na **dwóch różnych CPU**, bo tylko jeden z nich ma AMX.

### Maszyna A — Xeon @ 2.10 GHz, 4 vCPU (KVM), **z AMX** (`amx_tile`, `amx_int8`, `amx_bf16`, AVX512-VNNI)

OpenVINO raportuje `OPTIMIZATION_CAPABILITIES = [BF16, WINOGRAD, FP32, FP16, INT8, ...]`

| konfiguracja | precyzja jąder | top-1 | top-5 | latencja | p95 | przepustowość | rozmiar |
|---|---|---|---|---|---|---|---|
| FP32 (wymuszony) | f32       | 89.4% | 98.0% | 17.18 ms | 20.97 ms | 64 inf/s  | 102.5 MB |
| BF16 (domyślny)  | bf16      | 89.2% | 98.0% |  5.27 ms |  6.11 ms | 285 inf/s | 102.5 MB |
| INT8 (NNCF PTQ)  | int8+bf16 | 88.9% | 98.1% |  4.96 ms |  6.04 ms | 314 inf/s |  26.1 MB |

### Maszyna B — Xeon @ 2.80 GHz, 4 vCPU (KVM), **bez AMX** (AVX512-VNNI, brak `avx512_bf16`)

OpenVINO raportuje `OPTIMIZATION_CAPABILITIES = [WINOGRAD, FP32, INT8, ...]` — bez BF16

| konfiguracja | precyzja jąder | top-1 | top-5 | latencja | p95 | przepustowość | rozmiar |
|---|---|---|---|---|---|---|---|
| FP32 (wymuszony) | f32      | 89.4% | 98.0% | 17.26 ms | 20.47 ms | 61 inf/s  | 102.5 MB |
| BF16 (domyślny)  | f32      | 89.4% | 98.0% | 19.23 ms | 22.37 ms | 61 inf/s  | 102.5 MB |
| INT8 (NNCF PTQ)  | int8+f32 | 88.9% | 98.1% |  7.53 ms |  9.34 ms | 167 inf/s |  26.1 MB |

## Co z tego wynika

Zestawienie obu maszyn daje wniosek, którego żadna z nich osobno nie daje:

| | maszyna A (AMX) | maszyna B (bez AMX) |
|---|---|---|
| zysk z bf16 (sam hint, bez kwantyzacji) | **4.4x** | **0.99x** — hint zignorowany |
| zysk z INT8 ponad domyślną konfigurację  | **~1.1x** (w granicach szumu) | **2.7x** |
| zysk z INT8 ponad wymuszony f32           | 4.9x | 2.7x |
| rozmiar modelu                            | 3.9x mniej | 3.9x mniej |
| top-1 / zgodność predykcji z FP32         | 88.9% / 97.2% | 88.9% / 97.2% |

**Wartość kwantyzacji INT8 zależy od tego, czy procesor ma AMX — i to w drugą stronę,
niż podpowiada intuicja.** Tam, gdzie AMX jest, runtime domyślnie przechodzi na bf16
i sam zbiera 4.4x; INT8 dokłada już tylko tyle, ile mieści się w szumie pomiarowym.
Tam, gdzie AMX nie ma, `INFERENCE_PRECISION_HINT` na bf16 nie robi nic (dokumentacja
mówi wprost, że to hint, nie gwarancja — i tu widać to w liczbach), a INT8 zostaje
jedynym źródłem przyspieszenia i daje 2.7x.

Stałe w obu przypadkach są dwie rzeczy: **3.9x mniejszy model** i **identyczna jakość**
(88.9% top-1, ta sama predykcja co FP32 na 97.2% zdjęć — co do dziesiątej części procenta
na obu maszynach, bo kwantyzacja jest deterministyczna).

Praktycznie: na nowym Xeonie kwantyzuj dla rozmiaru modelu, nie dla prędkości.
Na starszym serwerze, laptopie bez AMX, NPU czy urządzeniu brzegowym — kwantyzuj dla prędkości.

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
- **Mediana z 3 powtórzeń + p95** — obie maszyny to współdzielone VM-ki pod KVM,
  pojedynczy pomiar potrafi się mylić o 20%. Dlatego zysk INT8 nad bf16 na maszynie A
  (~1.1x) jest opisany jako "w granicach szumu", a nie jako realne przyspieszenie.
- **Ta sama konfiguracja na dwóch CPU** — dopiero maszyna bez AMX pokazuje, ile
  z przyspieszenia dał sprzęt, a ile kwantyzacja. Bez tej kontroli obie hipotezy
  wyglądają w liczbach identycznie.
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
