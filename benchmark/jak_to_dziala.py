"""Wyszukiwanie semantyczne od zera, na trzech liczbach zamiast tysiąca.

Prawdziwy model daje 1024 liczby na zdanie. Tutaj robimy to samo na trzech,
które da się policzyć w głowie — bo mechanizm jest identyczny.

    python3 jak_to_dziala.py
"""

SLOWA = ["rag", "agent", "wektor"]

TEKSTY = {
    "A": "Agent przeszukuje repo, agent decyduje co czytać, agent weryfikuje",
    "B": "Naiwny RAG tnie dokument na chunki i wrzuca wektor do bazy, RAG szuka po wektorach",
    "C": "Kot śpi na parapecie",
}

PYTANIE = "Co robi agent, gdy przeszukuje pliki?"


def policz(tekst: str) -> list[int]:
    """Najprostszy możliwy wektor: ile razy pada każde z wybranych słów."""
    slowa = tekst.lower().replace(",", " ").split()
    return [sum(1 for s in slowa if s.startswith(kluczowe)) for kluczowe in SLOWA]


def iloczyn(a: list[float], b: list[float]) -> float:
    """Mnożymy liczby na tych samych miejscach i dodajemy wyniki."""
    return sum(x * y for x, y in zip(a, b))


def dlugosc(v: list[float]) -> float:
    """Twierdzenie Pitagorasa rozszerzone na dowolną liczbę wymiarów."""
    return iloczyn(v, v) ** 0.5


def znormalizuj(v: list[float]) -> list[float]:
    """Skracamy strzałkę do długości 1, zostawiając jej kierunek."""
    d = dlugosc(v) or 1.0
    return [x / d for x in v]


def main() -> None:
    print(f"Wybrane słowa (wymiary):  {SLOWA}")
    print(f"Pytanie:                  {PYTANIE!r}\n")

    q = policz(PYTANIE)
    print("KROK 1 — zamieniamy teksty na liczby (ile razy pada każde słowo)\n")
    print(f"  {'pytanie':10} {q}   <- {PYTANIE[:45]}")
    wektory = {}
    for nazwa, tekst in TEKSTY.items():
        wektory[nazwa] = policz(tekst)
        print(f"  {nazwa:10} {wektory[nazwa]}   <- {tekst[:45]}...")

    print("\nKROK 2 — iloczyn skalarny: mnożymy pary liczb i dodajemy\n")
    for nazwa, v in wektory.items():
        skladniki = " + ".join(f"{x}×{y}" for x, y in zip(q, v))
        print(f"  {nazwa}:  {skladniki}  =  {iloczyn(q, v)}")

    print("\nKROK 3 — problem: dłuższy tekst dostaje większe liczby\n")
    for nazwa, v in wektory.items():
        skladniki = " + ".join(f"{x}²" for x in v)
        print(f"  długość {nazwa} = pierwiastek({skladniki}) = {dlugosc(v):.2f}")

    print("\nKROK 4 — normalizacja: dzielimy przez długość, zostaje sam kierunek\n")
    qn = znormalizuj(q)
    print(f"  {'pytanie':10} {[round(x, 2) for x in qn]}")
    for nazwa, v in wektory.items():
        print(f"  {nazwa:10} {[round(x, 2) for x in znormalizuj(v)]}")

    print("\nKROK 5 — teraz iloczyn skalarny daje podobieństwo od 0 do 1\n")
    wyniki = sorted(
        ((iloczyn(qn, znormalizuj(v)), nazwa) for nazwa, v in wektory.items()),
        reverse=True,
    )
    for miejsce, (wynik, nazwa) in enumerate(wyniki, start=1):
        pasek = "█" * round(wynik * 30)
        print(f"  {miejsce}. {nazwa}  {wynik:.3f}  {pasek}")

    print(f"\nRANKING: {' > '.join(n for _, n in wyniki)}")
    print("\nTo jest całe wyszukiwanie semantyczne. Prawdziwy model różni się")
    print("tylko tym, że zamiast 3 policzonych słów daje 1024 liczby, które")
    print("kodują znaczenie, a nie samą obecność słowa.")


if __name__ == "__main__":
    main()
