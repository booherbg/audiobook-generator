"""Generate a default house-style cover.svg for a book if one doesn't exist.

The manifest always references audio/<id>/cover.svg; without this, a new book ships a
broken image on the library card. A hand-made cover (e.g. Magnifica's, with a bespoke
emblem) is never overwritten — we only fill the gap. The default is text-first: title,
author, subtitle on the dark/gold house palette, with a simple book emblem.
"""

import html
from pathlib import Path

from pipeline import config

# Wrap a long title onto two lines so it fits the 600px canvas at 52px serif.
def _title_lines(title):
    words = title.split()
    if len(title) <= 11 or len(words) == 1:
        return [title]
    # split near the middle on a word boundary
    best, mid = 0, len(title) / 2
    acc = 0
    for i, w in enumerate(words[:-1]):
        acc += len(w) + 1
        if abs(acc - mid) < abs(best - mid):
            best = acc
            split = i + 1
    return [" ".join(words[:split]), " ".join(words[split:])]


def _svg(title, author, subtitle):
    lines = _title_lines(title)
    t = [html.escape(x) for x in lines]
    author = html.escape(author or "")
    subtitle = html.escape(subtitle or "")
    # Title baseline(s): one line centered, or two stacked.
    if len(t) == 1:
        title_svg = (f'  <text x="300" y="392" text-anchor="middle" '
                     f'font-family="Georgia, \'Times New Roman\', serif" font-size="52" '
                     f'fill="#ece6da" letter-spacing="1">{t[0]}</text>\n')
    else:
        title_svg = (
            f'  <text x="300" y="372" text-anchor="middle" font-family="Georgia, \'Times New Roman\', serif" '
            f'font-size="52" fill="#ece6da" letter-spacing="1">{t[0]}</text>\n'
            f'  <text x="300" y="430" text-anchor="middle" font-family="Georgia, \'Times New Roman\', serif" '
            f'font-size="52" fill="#ece6da" letter-spacing="1">{t[1]}</text>\n')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600" '
        f'role="img" aria-label="{html.escape(title)} cover">\n'
        '  <defs>\n'
        '    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">\n'
        '      <stop offset="0" stop-color="#241f17"/>\n'
        '      <stop offset="1" stop-color="#14110c"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        '  <rect width="600" height="600" fill="url(#bg)"/>\n'
        '  <rect x="28" y="28" width="544" height="544" rx="18" fill="none" '
        'stroke="#d9b25b" stroke-opacity="0.45" stroke-width="2"/>\n'
        '  <!-- default emblem: an open book -->\n'
        '  <g stroke="#d9b25b" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">\n'
        '    <path d="M300 176 C272 160 244 160 224 168 L224 246 C244 238 272 238 300 254 Z"/>\n'
        '    <path d="M300 176 C328 160 356 160 376 168 L376 246 C356 238 328 238 300 254 Z"/>\n'
        '    <line x1="300" y1="176" x2="300" y2="254"/>\n'
        '  </g>\n'
        f'{title_svg}'
        f'  <text x="300" y="486" text-anchor="middle" '
        f'font-family="-apple-system, Segoe UI, Roboto, sans-serif" font-size="20" fill="#a59c89">{author}</text>\n'
        f'  <text x="300" y="524" text-anchor="middle" '
        f'font-family="-apple-system, Segoe UI, Roboto, sans-serif" font-size="15" fill="#8a8170">{subtitle}</text>\n'
        '</svg>\n'
    )


def ensure_cover(book_id, title, author="", subtitle=""):
    """Write audio/<id>/cover.svg if it doesn't already exist. Returns the path and
    whether it was created (False if a cover was already present)."""
    out = config.AUDIO_ROOT / book_id / "cover.svg"
    if out.exists():
        return out, False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_svg(title, author, subtitle), encoding="utf-8")
    return out, True
