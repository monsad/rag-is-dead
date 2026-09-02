"""Buduje indeks z katalogu dokumentów.

    python3 ingest.py ~/dokumenty            # zbuduj / zaktualizuj indeks
    python3 ingest.py ~/dokumenty --dry-run  # pokaż, co by zaindeksował, bez serwera

Indeks trafia do index.json obok skryptu. Ponowne uruchomienie przelicza tylko
pliki, które się zmieniły — reszta jest przepisywana z poprzedniego indeksu.
"""

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import client

INDEX = Path(__file__).parent / "index.json"
ROZSZERZENIA = {".md", ".txt", ".html", ".htm", ".rst", ".csv", ".json", ".pdf"}
DOCEL_ZNAKOW = 700     # docelowa długość fragmentu
MIN_ZNAKOW = 80

TAGI = re.compile(r"<[^>]+>")
SKRYPTY = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
PUSTE = re.compile(r"\n{3,}")


def czytaj(path: Path) -> str:
    """Tekst z pliku. PDF tylko gdy jest pypdf — bez niego plik jest pomijany."""
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return ""
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)

    surowy = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in (".html", ".htm"):
        surowy = SKRYPTY.sub(" ", surowy)
        surowy = re.sub(r"<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", surowy, flags=re.I)
        surowy = html_lib.unescape(TAGI.sub(" ", surowy))
    return PUSTE.sub("\n\n", surowy).strip()


def tnij(tekst: str) -> list[str]:
    """Akapity sklejane do ~DOCEL_ZNAKOW. Granica akapitu to granica myśli."""
    fragmenty, bufor = [], ""
    for akapit in (a.strip() for a in tekst.split("\n") if a.strip()):
        while len(akapit) > DOCEL_ZNAKOW * 2:          # bardzo długi akapit tniemy po zdaniach
            ciecie = akapit.rfind(". ", 0, DOCEL_ZNAKOW) + 1 or DOCEL_ZNAKOW
            fragmenty.append(akapit[:ciecie].strip())
            akapit = akapit[ciecie:].strip()
        if bufor and len(bufor) + len(akapit) > DOCEL_ZNAKOW:
            fragmenty.append(bufor)
            bufor = akapit
        else:
            bufor = f"{bufor}\n{akapit}" if bufor else akapit
    if bufor:
        fragmenty.append(bufor)
    return [f for f in fragmenty if len(f) >= MIN_ZNAKOW]


def znormalizuj(v: list[float]) -> list[float]:
    skala = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / skala for x in v]


def zaladuj_indeks() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text())
    return {"model": client.EMBED_MODEL, "pliki": {}, "fragmenty": []}


def main() -> None:
    ap = argparse.ArgumentParser(description="Buduje indeks dokumentów dla asystenta.")
    ap.add_argument("katalog", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="pokaż fragmenty, nie licz wektorów")
    args = ap.parse_args()

    if not args.katalog.is_dir():
        sys.exit(f"To nie jest katalog: {args.katalog}")

    pliki = sorted(p for p in args.katalog.rglob("*")
                   if p.is_file() and p.suffix.lower() in ROZSZERZENIA and not p.name.startswith("."))
    if not pliki:
        sys.exit(f"Brak plików o rozszerzeniach {sorted(ROZSZERZENIA)} w {args.katalog}")

    stary = zaladuj_indeks()
    if stary["model"] != client.EMBED_MODEL:
        print(f"Model embeddingów się zmienił ({stary['model']} -> {client.EMBED_MODEL}) — przeliczam wszystko")
        stary = {"model": client.EMBED_MODEL, "pliki": {}, "fragmenty": []}

    stare_fragmenty: dict[str, list[dict]] = {}
    for f in stary["fragmenty"]:
        stare_fragmenty.setdefault(f["plik"], []).append(f)

    fragmenty: list[dict] = []
    nowe_pliki: dict[str, str] = {}
    do_policzenia: list[dict] = []
    bez_zmian = pominiete = 0

    for path in pliki:
        klucz = str(path.resolve())
        tekst = czytaj(path)
        if not tekst.strip():
            pominiete += 1
            continue

        suma = hashlib.sha256(tekst.encode()).hexdigest()[:16]
        nowe_pliki[klucz] = suma

        if stary["pliki"].get(klucz) == suma and klucz in stare_fragmenty:
            fragmenty.extend(stare_fragmenty[klucz])
            bez_zmian += 1
            continue

        for i, kawalek in enumerate(tnij(tekst), start=1):
            wpis = {"id": f"{path.name}#{i}", "plik": klucz, "nazwa": path.name, "tekst": kawalek}
            fragmenty.append(wpis)
            do_policzenia.append(wpis)

    print(f"Plików: {len(pliki)}  |  bez zmian: {bez_zmian}  |  do przeliczenia: "
          f"{len(pliki) - bez_zmian - pominiete}  |  pominiętych: {pominiete}")
    print(f"Fragmentów w indeksie: {len(fragmenty)}  (nowych: {len(do_policzenia)})")

    if args.dry_run:
        print("\n--dry-run: przykładowe fragmenty\n")
        for wpis in do_policzenia[:5]:
            podglad = wpis["tekst"].replace("\n", " ")[:110]
            print(f"  {wpis['id']:28} {len(wpis['tekst']):5} zn.  {podglad}...")
        return

    if do_policzenia:
        print(f"Liczę wektory dla {len(do_policzenia)} fragmentów...")
        # E5 wymaga przedrostka 'passage:' przy dokumentach — bez niego jakość spada
        wektory = client.embed([f"passage: {w['tekst']}" for w in do_policzenia])
        for wpis, wektor in zip(do_policzenia, wektory):
            wpis["wektor"] = znormalizuj(wektor)

    INDEX.write_text(json.dumps(
        {"model": client.EMBED_MODEL, "zbudowany": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "pliki": nowe_pliki, "fragmenty": fragmenty},
        ensure_ascii=False))
    print(f"\nZapisano {INDEX.name} — {len(fragmenty)} fragmentów, {INDEX.stat().st_size // 1024} KB")
    print("Teraz: python3 asystent.py \"twoje pytanie\"")


if __name__ == "__main__":
    main()
