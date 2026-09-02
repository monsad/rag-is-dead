# Open WebUI na serwerze OpenVINO

Gotowa konfiguracja: interfejs webowy z czatem, bazami wiedzy i rozmową głosową,
podpięty pod serwer inferencji z modelami OpenVINO. Jedna komenda.

```bash
export INFER_KEY="sk-infer-..."
docker compose up -d
```

Potem `http://localhost:3000`. Pierwsze założone konto zostaje administratorem.

## Co to daje ponad `../asystent`

Wszystko to samo, plus interfejs, konta, historia rozmów, wgrywanie plików
przez przeglądarkę i rozmowa głosowa bez linii poleceń. Jeśli ktoś ma tego
faktycznie używać — używa tego, nie CLI.

`../asystent` zostaje do czego innego: tam widzisz każdy krok i możesz zmierzyć,
co się dzieje. Tutaj masz produkt, tam masz zrozumienie.

## Ustawienia, które robią różnicę

Domyślnie Open WebUI **wektoryzowałby dokumenty własnym modelem w kontenerze** —
serwer OpenVINO odpowiadałby wtedy tylko za czat, a całe wyszukiwanie działoby
się obok niego. Dlatego w `docker-compose.yml` są jawnie ustawione:

| ustawienie | po co |
|---|---|
| `RAG_EMBEDDING_ENGINE: openai` | embeddingi liczy serwer, nie kontener |
| `RAG_EMBEDDING_QUERY_PREFIX` / `CONTENT_PREFIX` | E5 rozróżnia pytanie od dokumentu po przedrostku |
| `RAG_RERANKING_ENGINE: external` | reranker też z serwera |
| `ENABLE_RAG_HYBRID_SEARCH` | wektory **i** BM25 naraz |
| `RAG_TOP_K: 20` → `RAG_TOP_K_RERANKER: 5` | najpierw zasięg, potem precyzja |

Przedrostki E5 są tu najbardziej podstępne: ich brak **niczego nie psuje
widocznie**. Nie ma błędu, nie ma ostrzeżenia — wyniki są po prostu gorsze,
a ty nie wiesz dlaczego.

Adres zewnętrznego rerankera musi być **pełną ścieżką do `/rerank`** — tak go
używa `ExternalReranker` w kodzie Open WebUI, nie doklejając nic od siebie.

## Pułapka, która kosztuje godzinę

**Zmienne środowiskowe działają tylko przy pierwszym starcie.** Open WebUI
zapisuje konfigurację do własnej bazy i od drugiego uruchomienia czyta ją stamtąd,
ignorując środowisko.

Jeśli już kiedyś uruchamiałaś Open WebUI, masz dwa wyjścia:

1. zmienić ustawienia w interfejsie: **Admin Panel → Settings → Documents / Audio**
2. albo zacząć od zera:
   ```bash
   docker compose down -v      # -v kasuje wolumen razem z kontami i rozmowami
   docker compose up -d
   ```

## Sprawdź, czy naprawdę używa serwera

Sama konfiguracja to za mało — trzeba zobaczyć, że działa:

1. **Admin Panel → Settings → Documents** — czy silnik embeddingów to `openai`
   i czy model to `multilingual-e5-large-int8`.
2. Wgraj dokument i obserwuj logi serwera kolegi. Powinny pojawić się wywołania
   `/embeddings`. Jeśli nie ma — wektoryzuje lokalnie i konfiguracja nie weszła.
3. Zadaj pytanie do wgranego dokumentu i sprawdź, czy odpowiedź cytuje źródło.
4. **Test na zmyślanie:** zapytaj o coś, czego w dokumentach nie ma. Dobra
   odpowiedź to „nie wiem". Ten test decyduje, czy narzędzie nadaje się do pracy.

## Zanim wrzucisz tam firmowe dokumenty

Treść plików trafia na serwer inferencji. Jeśli nie jest twój — wysyłasz je
komuś. Ustal czyj jest, co loguje i jak długo trzyma dane. Przy danych
osobowych to nie formalność.

Do własnego serwera: `export INFER_URL="https://twoj-serwer:11437/v1"`.

## Licencja

Open WebUI nie jest na klasycznym MIT — ma własną licencję z ograniczeniami
m.in. co do zmiany brandingu przy większych wdrożeniach. Do prywatnego użytku
i małego zespołu bez znaczenia; przed wdrożeniem u klienta przeczytaj warunki.
