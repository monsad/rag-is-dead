#!/usr/bin/env bash
# Sprawdza, czy masz wszystko, czego potrzebują projekty w tym repo,
# i mówi, co zrobić dalej.
#
#   ./sprawdz.sh

set -u

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
zle()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }
info() { printf "  \033[33m•\033[0m %s\n" "$1"; }

BRAKI=()

echo
echo "═══ Środowisko ═══"

if command -v python3 >/dev/null 2>&1; then
    WERSJA=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then
        ok "Python $WERSJA"
    else
        zle "Python $WERSJA — skrypty wymagają 3.10 lub nowszego"
        BRAKI+=("python")
    fi
else
    zle "Brak python3"; BRAKI+=("python")
fi

if command -v docker >/dev/null 2>&1; then
    ok "Docker jest (potrzebny tylko do openwebui/)"
else
    info "Brak Dockera — openwebui/ nie ruszy, reszta tak"
fi

python3 -c 'import openvino' 2>/dev/null \
    && ok "openvino zainstalowane (openvino-demo/ gotowe)" \
    || info "Brak openvino — potrzebne tylko do openvino-demo/: pip install -r openvino-demo/requirements.txt"

echo
echo "═══ Serwer inferencji ═══"

if [ -z "${INFER_KEY:-}" ]; then
    zle "INFER_KEY nie ustawiony"
    info "export INFER_KEY=\"sk-infer-...\""
    BRAKI+=("klucz")
else
    ok "INFER_KEY ustawiony (${#INFER_KEY} znaków)"
    URL="${INFER_URL:-https://biuro.cdest.eu:11437/v1}"
    ODP=$(curl -s -m 20 -w '\n%{http_code}' "$URL/models" -H "Authorization: Bearer $INFER_KEY" 2>&1)
    KOD=$(printf '%s' "$ODP" | tail -1)
    if [ "$KOD" = "200" ]; then
        LICZBA=$(printf '%s' "$ODP" | head -n -1 | grep -o '"id"' | wc -l | tr -d ' ')
        ok "Serwer odpowiada — $LICZBA modeli"
        printf '%s' "$ODP" | head -n -1 | grep -oE '"id":"[^"]+"' | cut -d'"' -f4 | sed 's/^/      /'
    else
        zle "Serwer nie odpowiada poprawnie (HTTP $KOD)"
        BRAKI+=("serwer")
    fi
fi

echo
echo "═══ Co możesz zrobić teraz ═══"
echo

if [ ${#BRAKI[@]} -eq 0 ]; then
    cat <<'TXT'
  Masz wszystko. Kolejność, którą polecam:

  1. Zrozumienie matematyki       cd benchmark && python3 jak_to_dziala.py
  2. Twój procesor                cd openvino-demo && python3 check_cpu.py
  3. Benchmark wyszukiwania       cd benchmark && python3 benchmark.py
  4. Asystent w terminalu         cd asystent && python3 ingest.py ../rag-is-dead
                                                 python3 asystent.py "Kto to Boris Cherny?"
  5. Interfejs webowy             cd openwebui && docker compose up -d
TXT
else
    echo "  Zacznij od tego, co nie działa:"
    for b in "${BRAKI[@]}"; do
        case "$b" in
            python) echo "    • zainstaluj Pythona 3.10+" ;;
            klucz)  echo "    • export INFER_KEY=\"sk-infer-...\"  (klucz od kolegi)" ;;
            serwer) echo "    • sprawdź klucz i adres serwera, ewentualnie zapytaj kolegę" ;;
        esac
    done
    echo
    echo "  Bez klucza i tak działa (nie wymaga serwera):"
    echo "    cd benchmark && python3 jak_to_dziala.py"
    echo "    cd benchmark && python3 benchmark.py     # same warianty BM25"
fi
echo
