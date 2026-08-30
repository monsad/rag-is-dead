# Prompt Lookup decoding — czy przyspiesza właśnie RAG?

Eksperyment z biblioteki [OpenVINO GenAI](https://github.com/openvinotoolkit/openvino.genai),
na modelu językowym uruchamianym lokalnie na CPU.

## Hipoteza

**Prompt Lookup decoding** przyspiesza generowanie w sposób, który powinien
zależeć od tego, co model pisze — a nie tylko od tego, jaki to model.

Działa tak: zanim model policzy kolejny token, algorytm szuka w **prompcie**
fragmentu zaczynającego się tak samo jak to, co model właśnie napisał. Jeśli
znajdzie, zgaduje kilka następnych tokenów za darmo, a model tylko weryfikuje
je jednym przebiegiem zamiast liczyć po kolei.

Stąd przewidywanie:

> Odpowiedź RAG-owa w dużej mierze **cytuje dostarczony kontekst**, więc trafień
> będzie dużo. Odpowiedź „z głowy" nie ma czego cytować, więc trafień nie będzie.
> Przyspieszenie powinno pojawić się przy RAG-u i zniknąć bez kontekstu.

Jeśli to się potwierdzi, mamy optymalizację działającą dokładnie tam, gdzie
generuje się odpowiedzi z wyszukanych fragmentów — czyli w całym RAG-u.

## Dlaczego jest grupa kontrolna

Te same pytania są zadawane dwa razy: raz z fragmentem z korpusu prezentacji,
raz bez żadnego kontekstu. Bez tej drugiej grupy nie odróżnisz „prompt lookup
pomaga RAG-owi" od „prompt lookup pomaga zawsze na tym modelu" — a to są dwa
zupełnie różne wnioski.

To ten sam zabieg, co druga maszyna w `../openvino-demo`: efekt widać dopiero
wtedy, gdy masz z czym go porównać.

## Kontrola poprawności

Prompt lookup jest **bezstratny** względem dekodowania zachłannego — ma zwrócić
dokładnie ten sam tekst, tylko szybciej. Skrypt porównuje oba wyjścia i raportuje,
ile odpowiedzi jest identycznych. Kolumna `ten sam tekst` powinna pokazywać
komplet; rozjazd oznacza błąd konfiguracji, a nie ciekawy wynik.

Bez tego sprawdzenia „przyspieszenie" mogłoby po prostu oznaczać, że model
generuje coś innego, krótszego.

## Uruchomienie

```bash
pip install "optimum[openvino]" openvino-genai

# eksport modelu do formatu OpenVINO (~1 GB w INT4)
optimum-cli export openvino --model Qwen/Qwen2.5-1.5B-Instruct \
    --weight-format int4 ./model

python3 prompt_lookup.py ./model
```

Model 1.5B w INT4 chodzi sensownie na laptopowym CPU. Większy da wyraźniejsze
liczby, ale dłużej się czeka.

## Parametry, którymi warto pokręcić

| parametr | co robi | domyślnie |
|---|---|---|
| `NGRAM` | ile tokenów musi się zgodzić, żeby uznać trafienie | 3 |
| `CANDIDATES` | ile tokenów zgadujemy naprzód po trafieniu | 5 |

Małe `NGRAM` = więcej trafień, ale częściej fałszywych (weryfikacja je odrzuci,
czas przepadnie). Duże = trafienia rzadsze, za to pewne. To jest realny
kompromis do zmierzenia — druga krzywa, którą można z tego wyciągnąć.

## Czego ten eksperyment NIE mierzy

- **Jakości odpowiedzi.** Prompt lookup jej nie zmienia (i to sprawdzamy),
  więc nie ma tu czego oceniać.
- **Dekodowania spekulatywnego z modelem pomocniczym** — to osobna technika
  (`num_assistant_tokens` bez `max_ngram_size`), wymaga drugiego, mniejszego
  modelu. Warta osobnego eksperymentu.
- **Zachowania przy wielu równoległych zapytaniach.** Mierzymy pojedyncze
  generowanie; przy obciążonym serwerze rachunek wygląda inaczej.
