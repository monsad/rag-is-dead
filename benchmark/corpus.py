"""Korpus: tekst prezentacji i dem, pocięty na fragmenty do wyszukiwania.

Jeden slajd = jeden fragment. To naturalna granica tematyczna — autor sam
zdecydował, co idzie razem — więc nie zgadujemy, gdzie ciąć.
"""

import html as html_lib
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCES = [
    ("prezentacja", ROOT / "rag-is-dead" / "presentation.html", r'<div class="slide[^"]*"'),
    ("demo1", ROOT / "demo.html", None),
    ("demo2", ROOT / "demo2.html", None),
    ("demo3", ROOT / "demo3.html", None),
    ("demo4", ROOT / "demo4.html", None),
    ("demo5", ROOT / "demo5.html", None),
]

DROP_TAGS = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TAGS = re.compile(r"<[^>]+>")
SPACES = re.compile(r"[ \t]+")
BLANKS = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    title: str
    text: str

    def __str__(self) -> str:
        return f"[{self.id}] {self.title}"


def strip_html(fragment: str) -> str:
    fragment = DROP_TAGS.sub(" ", fragment)
    fragment = re.sub(r"<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", fragment, flags=re.I)
    text = html_lib.unescape(TAGS.sub(" ", fragment))
    return BLANKS.sub("\n\n", SPACES.sub(" ", text)).strip()


def first_heading(fragment: str) -> str:
    m = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", fragment, re.S | re.I)
    return strip_html(m.group(1)).replace("\n", " ")[:90] if m else ""


def split_slides(html: str, marker: str) -> list[str]:
    """Tnie po znaczniku slajdu, zachowując treść między kolejnymi wystąpieniami."""
    positions = [m.start() for m in re.finditer(marker, html)]
    return [html[a:b] for a, b in zip(positions, positions[1:] + [len(html)])]


def split_sections(html: str) -> list[str]:
    """Dla dem: tnie po nagłówkach, bo nie mają struktury slajdów."""
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    html = body.group(1) if body else html
    positions = [m.start() for m in re.finditer(r"<h[1-3][^>]*>", html, re.I)]
    if not positions:
        return [html]
    return [html[a:b] for a, b in zip(positions, positions[1:] + [len(html)])]


def passages(text: str, target: int = 420) -> list[str]:
    """Dzieli tekst slajdu na fragmenty ~target znaków, po granicach akapitów.

    Slajd bywa długi i porusza kilka wątków; przy 32 fragmentach w całym korpusie
    każda metoda trafiałaby przypadkiem. Drobniejszy podział sprawia, że ranking
    zaczyna cokolwiek znaczyć.
    """
    out, buf = [], ""
    for para in (p.strip() for p in text.split("\n") if p.strip()):
        if buf and len(buf) + len(para) > target:
            out.append(buf)
            buf = para
        else:
            buf = f"{buf}\n{para}" if buf else para
    if buf:
        out.append(buf)
    return out


def load() -> list[Chunk]:
    chunks: list[Chunk] = []
    for name, path, marker in SOURCES:
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        parts = split_slides(raw, marker) if marker else split_sections(raw)

        for i, part in enumerate(parts, start=1):
            text = strip_html(part)
            if len(text) < 120:  # puste slajdy tytułowe, separatory
                continue
            title = first_heading(part) or text.split("\n")[0][:90]
            for j, passage in enumerate(passages(text), start=1):
                if len(passage) < 60:
                    continue
                chunks.append(Chunk(id=f"{name}#{i}.{j}", source=name, title=title, text=passage))
    return chunks


if __name__ == "__main__":
    chunks = load()
    print(f"{len(chunks)} fragmentów, {sum(len(c.text) for c in chunks) // 1000} tys. znaków\n")
    for c in chunks:
        print(f"{c.id:16} {len(c.text):5}zn  {c.title}")
