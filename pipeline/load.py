"""Loaders: turn a URL or file into a structured Document.

HTMLLoader does a generic structural parse (headings → sections, <p> → paragraphs).
Site-specific tuning (e.g. vatican.va) happens where needed; cleaning is clean.py's job.
"""

from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from pipeline.model import Document, Section

_HEADINGS = ("h1", "h2", "h3")


def _fetch(url_or_path: str) -> str:
    if url_or_path.startswith(("http://", "https://")):
        resp = httpx.get(
            url_or_path,
            follow_redirects=True,
            timeout=30,
            headers={"User-Agent": "audiobook-generator/0.1"},
        )
        resp.raise_for_status()
        return resp.text
    return Path(url_or_path).read_text(encoding="utf-8", errors="ignore")


class HTMLLoader:
    def load(self, url_or_path: str) -> Document:
        soup = BeautifulSoup(_fetch(url_or_path), "lxml")
        title = soup.title.get_text(strip=True) if soup.title else ""
        root = soup.find("main") or soup.find("article") or soup.body or soup

        sections: list[Section] = []
        current: Section | None = None
        for el in root.find_all([*_HEADINGS, "p"]):
            text = el.get_text(" ", strip=True)
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

        sections = [s for s in sections if s.paragraphs]
        return Document(title=title, author="", sections=sections)


class PDFLoader:
    def load(self, url_or_path: str) -> Document:
        raise NotImplementedError("PDF support is a future addition (spec §20).")
