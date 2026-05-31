"""Resolve a resource argument to a URL or local file path.

No LLM lives in the pipeline: a free-text *description* is not resolved here.
Finding a source from a description is Claude Code's job, in-session — it hands
back a URL, which this function accepts.
"""

from pathlib import Path
from urllib.parse import urlparse


class ResolveError(ValueError):
    """Raised when a resource is neither a URL nor an existing file."""


def resolve(resource: str) -> str:
    """Return the resource if it is an http(s) URL or an existing file path."""
    parsed = urlparse(resource)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return resource
    path = Path(resource).expanduser()
    if path.exists():
        return str(path)
    raise ResolveError(
        f"{resource!r} is not a URL or an existing file. "
        "Ask Claude Code to find the source, then pass the URL."
    )
