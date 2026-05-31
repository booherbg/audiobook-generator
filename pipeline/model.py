"""Lightweight data model shared across the pipeline."""

from dataclasses import dataclass, field


@dataclass
class Section:
    heading: str
    paragraphs: list[str] = field(default_factory=list)


@dataclass
class Document:
    title: str
    author: str
    sections: list[Section] = field(default_factory=list)


@dataclass
class Chapter:
    index: int
    title: str
    segments: list[str] = field(default_factory=list)  # ordered text to narrate
