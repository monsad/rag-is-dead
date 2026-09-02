"""Asystent, który odpowiada na pytania o twoje dokumenty. Lokalnie.

    python3 asystent.py "ile mamy dni urlopu"      # pytanie z linii poleceń
    python3 asystent.py                            # tryb rozmowy
    python3 asystent.py --audio pytanie.m4a        # pytanie z nagrania
    python3 asystent.py "..." --mow                # odpowiedź na głos
    python3 asystent.py "..." --szukaj             # same fragmenty, bez modelu

Nic nie wychodzi poza serwer, na którym stoją modele.
"""

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import client

INDEX = Path(__file__).parent / "index.json"
KANDYDACI = 20      # ile fragmentów bierzemy z wyszukiwania wektorowego
KONTEKST = 5        # ile trafia do modelu po przesortowaniu


def wczytaj_indeks() -> list[dict]:
    if not INDEX.exists():
        sys.exit("Brak indeksu. Najpierw: python3 ingest.py ~/twoje/dokumenty")
    dane = json.loads(INDEX.read_text())
    if dane["model"] != client.EMBED_MODEL:
        sys.exit(f"Indeks zbudowany innym modelem ({dane['model']}). Uruchom ingest.py ponownie.")
    return [f for f in dane["fragmenty"] if "wektor" in f]


def szukaj(pytanie: str, fragmenty: list[dict]) -> tuple[list[dict], bool]:
    """Wektory wybierają kandydatów, reranker układa kolejność.

    Zwraca też informację, czy reranker faktycznie zadziałał — bo asystent ma
    działać również wtedy, gdy serwer go nie wystawia.
    """
    zapytanie = client.embed([f"query: {pytanie}"])[0]
    skala = sum(x * x for x in zapytanie) ** 0.5 or 1.0
    zapytanie = [x / skala for x in zapytanie]

    punkty = [(sum(a * b for a, b in zip(zapytanie, f["wektor"])), f) for f in fragmenty]
    punkty.sort(key=lambda p: -p[0])
    kandydaci = [f for _, f in punkty[:KANDYDACI]]

    try:
        oceny = client.rerank(pytanie, [f["tekst"] for f in kandydaci])
        posortowane = [f for _, f in sorted(zip(oceny, kandydaci), key=lambda p: -p[0])]
        return posortowane[:KONTEKST], True
    except client.ServerError:
        return kandydaci[:KONTEKST], False


def odpowiedz(pytanie: str, zrodla: list[dict]) -> str:
    kontekst = "\n\n".join(
        f"[{i}] ({z['nazwa']})\n{z['tekst']}" for i, z in enumerate(zrodla, start=1)
    )
    return client.chat([
        {"role": "system", "content":
         "Odpowiadasz na pytania wyłącznie na podstawie dostarczonych fragmentów. "
         "Po każdym twierdzeniu podaj numer fragmentu w nawiasie kwadratowym, np. [2]. "
         "Jeśli fragmenty nie zawierają odpowiedzi, powiedz to wprost i nie zgaduj. "
         "Odpowiadaj po polsku, zwięźle."},
        {"role": "user", "content": f"FRAGMENTY:\n{kontekst}\n\nPYTANIE: {pytanie}"},
    ])


def nagraj(sekundy: int, cel: Path) -> Path:
    """Nagrywa z domyślnego mikrofonu, jeśli w systemie jest sox albo ffmpeg."""
    if shutil.which("rec"):
        cmd = ["rec", "-q", "-r", "16000", "-c", "1", str(cel), "trim", "0", str(sekundy)]
    elif shutil.which("ffmpeg"):
        wejscie = {"darwin": ("avfoundation", ":0"), "linux": ("alsa", "default")}
        rodzaj, urzadzenie = wejscie.get(sys.platform, ("alsa", "default"))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", rodzaj, "-i", urzadzenie,
               "-t", str(sekundy), "-ar", "16000", "-ac", "1", str(cel)]
    else:
        sys.exit("Do nagrywania potrzebny jest sox (komenda 'rec') albo ffmpeg.\n"
                 "Możesz też nagrać czymkolwiek i użyć: --audio plik.m4a")

    print(f"Nagrywam {sekundy} s... mów.")
    subprocess.run(cmd, check=True)
    return cel


def odtworz(plik: Path) -> None:
    for gracz in ("afplay", "paplay", "aplay", "ffplay"):
        if shutil.which(gracz):
            args = [gracz, str(plik)]
            if gracz == "ffplay":
                args = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(plik)]
            subprocess.run(args, check=False)
            return
    print(f"(brak odtwarzacza w systemie — plik: {plik})")


def obsluz(pytanie: str, fragmenty: list[dict], args) -> None:
    zrodla, rerank_ok = szukaj(pytanie, fragmenty)

    if args.szukaj:
        print(f"\nZnalezione fragmenty{'' if rerank_ok else ' (bez rerankera)'}:\n")
        for i, z in enumerate(zrodla, start=1):
            print(f"[{i}] {z['nazwa']}")
            print(textwrap.indent(textwrap.fill(z["tekst"][:400], 92), "    "))
            print()
        return

    tekst = odpowiedz(pytanie, zrodla)
    print(f"\n{textwrap.fill(tekst, 92)}\n")
    print("Źródła:")
    for i, z in enumerate(zrodla, start=1):
        print(f"  [{i}] {z['nazwa']}")
    if not rerank_ok:
        print("  (reranker niedostępny — kolejność z samych wektorów)")

    if args.mow:
        plik = Path(__file__).parent / "odpowiedz.wav"
        try:
            odtworz(client.speak(tekst, plik))
        except client.ServerError as e:
            print(f"\nSynteza mowy niedostępna: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Lokalny asystent do twoich dokumentów.")
    ap.add_argument("pytanie", nargs="*", help="pytanie; puste = tryb rozmowy")
    ap.add_argument("--audio", type=Path, help="pytanie z pliku dźwiękowego")
    ap.add_argument("--nagraj", type=int, metavar="SEK", help="nagraj pytanie z mikrofonu")
    ap.add_argument("--mow", action="store_true", help="przeczytaj odpowiedź na głos")
    ap.add_argument("--szukaj", action="store_true", help="pokaż fragmenty, nie pytaj modelu")
    args = ap.parse_args()

    fragmenty = wczytaj_indeks()
    print(f"Indeks: {len(fragmenty)} fragmentów\n")

    if args.nagraj:
        args.audio = nagraj(args.nagraj, Path(__file__).parent / "pytanie.wav")

    if args.audio:
        pytanie = client.transcribe(args.audio)
        print(f"Usłyszałem: {pytanie!r}")
        obsluz(pytanie, fragmenty, args)
        return

    if args.pytanie:
        obsluz(" ".join(args.pytanie), fragmenty, args)
        return

    print("Tryb rozmowy. Pusta linia albo Ctrl-C kończy.\n")
    while True:
        try:
            pytanie = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not pytanie:
            return
        try:
            obsluz(pytanie, fragmenty, args)
        except client.ServerError as e:
            print(f"Błąd serwera: {e}")


if __name__ == "__main__":
    main()
