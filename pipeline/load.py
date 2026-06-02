"""Loaders: turn a URL or file into a structured Document.

HTMLLoader auto-detects two layouts:
  * Vatican / MS-Word export: content in <p class="MsoNormal">, chapter titles are
    short all-caps paragraphs (a "CHAPTER X" label followed by the CAPS title),
    footnotes in <sup>/MsoFootnoteText. A leading table-of-contents collapses to
    empty sections and is dropped.
  * Generic: semantic <h1>-<h3> headings + <p> paragraphs.
Cleaning of footnote brackets / paragraph numbers is clean.py's job.
"""

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from pipeline.model import Document, Section

_HEADINGS = ("h1", "h2", "h3")
_SMALL = {"a", "an", "the", "and", "but", "or", "nor", "for", "of", "to", "in",
          "on", "at", "by", "with", "as", "from"}
_ACRONYMS = {"AI", "UN", "EU", "US", "GDP", "CEO", "DNA", "GMO"}
_CHAPTER_START = re.compile(r"^CHAPTER\b", re.IGNORECASE)


def _fetch(url_or_path: str) -> str:
    if url_or_path.startswith(("http://", "https://")):
        resp = httpx.get(
            url_or_path, follow_redirects=True, timeout=30,
            headers={"User-Agent": "audiobook-generator/0.1"},
        )
        resp.raise_for_status()
        return resp.text
    return Path(url_or_path).read_text(encoding="utf-8", errors="ignore")


def _text_no_sup(el) -> str:
    for sup in el.find_all("sup"):
        sup.decompose()
    return el.get_text(" ", strip=True)


def _is_caps_heading(text: str) -> bool:
    if len(text) > 70 or any(ch.isdigit() for ch in text):
        return False
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _smart_title(text: str) -> str:
    out = []
    cap_next = True
    for w in text.split():
        bare = w.strip(".,:;'\"()")
        if bare in _ACRONYMS:
            out.append(w)
        elif bare.lower() in _SMALL and not cap_next:
            out.append(w.lower())
        else:
            low = w.lower()
            out.append(low[:1].upper() + low[1:])
        cap_next = w.endswith((".", "!", "?", ":"))
    return " ".join(out)


def _sections_from_caps(paras) -> list[Section]:
    items = []
    for p in paras:
        t = _text_no_sup(p)
        if not t or set(t) <= set("_-—– .") or t == "[ Multimedia ]":
            continue
        items.append(t)

    caps = [_is_caps_heading(t) for t in items]
    n = len(items)

    # Skip a leading table of contents. Encyclicals open with "INTRODUCTION",
    # which also appears in the TOC, so start at its LAST occurrence (the body).
    intro = [i for i in range(n) if caps[i] and items[i].strip().upper() == "INTRODUCTION"]
    if intro:
        start = intro[-1]
    else:
        # Fallback: the heading preceding the first substantial body paragraph.
        first_body = next((i for i in range(n) if not caps[i] and len(items[i]) > 200), None)
        start = 0
        if first_body is not None:
            for j in range(first_body, -1, -1):
                if caps[j]:
                    start = j
                    break

    sections: list[Section] = []
    current: Section | None = None
    i = start
    while i < n:
        if caps[i]:
            if _CHAPTER_START.match(items[i]):
                parts = []
                j = i + 1
                while j < n and caps[j] and not _CHAPTER_START.match(items[j]):
                    parts.append(items[j])
                    j += 1
                heading = _smart_title(" ".join(parts) if parts else items[i])
                current = Section(heading, [])
                sections.append(current)
                i = j
            else:
                current = Section(_smart_title(items[i]), [])
                sections.append(current)
                i += 1
        else:
            if current is not None:
                current.paragraphs.append(items[i])
            i += 1
    return [s for s in sections if s.paragraphs]


def _sections_from_headings(soup) -> list[Section]:
    root = soup.find("main") or soup.find("article") or soup.body or soup
    sections: list[Section] = []
    current: Section | None = None
    collected = 0
    for el in root.find_all([*_HEADINGS, "p", "hr"]):
        # A horizontal rule after the body conventionally separates end-matter footnotes in the
        # plain-<p> Vatican layout (e.g. Laudato si' has ~170 reference paragraphs after an <hr>
        # that would otherwise be narrated). Stop once a real body has been collected; a stray
        # rule in the page header (before any content) is ignored.
        if el.name == "hr":
            if collected >= 8:
                break
            continue
        text = _text_no_sup(el)
        if not text:
            continue
        if el.name in _HEADINGS:
            current = Section(heading=text, paragraphs=[])
            sections.append(current)
        else:
            if current is None:
                current = Section(heading="", paragraphs=[])
                sections.append(current)
            current.paragraphs.append(text)
            collected += 1
    return [s for s in sections if s.paragraphs]


class HTMLLoader:
    def load(self, url_or_path: str) -> Document:
        soup = BeautifulSoup(_fetch(url_or_path), "lxml")
        title = soup.title.get_text(strip=True) if soup.title else ""
        all_p = soup.find_all("p")
        mso = soup.find_all("p", class_="MsoNormal")
        # Use the MS-Word/Vatican path only when MsoNormal is the document's body paragraph
        # style — a large set, or a clear majority of paragraphs — not a stray handful.
        # (Laudato si' has 4 boilerplate MsoNormal among 788 plain <p>; Rerum Novarum has none.
        # Both must fall through to the generic <p>/heading path below.)
        use_mso = len(mso) >= 50 or (bool(mso) and len(mso) * 2 >= len(all_p))
        sections = _sections_from_caps(mso) if use_mso else _sections_from_headings(soup)
        return Document(title=title, author="", sections=sections)


class PDFLoader:
    def load(self, url_or_path: str) -> Document:
        raise NotImplementedError("PDF support is a future addition (spec §20).")
