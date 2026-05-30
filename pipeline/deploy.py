"""Publish docs/ to GitHub Pages: commit changed assets, push, ensure Pages
serves /docs on the current branch. Refuses if QA failed (unless forced)."""

import json
import subprocess
import sys

from pipeline.config import BUILD, ROOT


def _run(args, **kw):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, **kw)


def _qa_failed() -> bool:
    rep = BUILD / "qa-report.json"
    if not rep.exists():
        return False
    try:
        return not json.loads(rep.read_text()).get("passed", True)
    except Exception:
        return False


def _slug() -> str:
    return _run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]).stdout.strip()


def _gh_json(method, path, body):
    return _run(["gh", "api", "-X", method, path, "--input", "-"], input=json.dumps(body))


def _ensure_pages(slug: str, branch: str) -> str:
    body = {"source": {"branch": branch, "path": "/docs"}}
    if _run(["gh", "api", f"repos/{slug}/pages"]).returncode == 0:
        r = _gh_json("PUT", f"repos/{slug}/pages", body)
        return "updated" if r.returncode == 0 else f"update note: {r.stderr.strip()[:160]}"
    r = _gh_json("POST", f"repos/{slug}/pages", {**body, "build_type": "legacy"})
    return "created" if r.returncode == 0 else f"create note: {r.stderr.strip()[:160]}"


def deploy(force: bool = False) -> None:
    if _qa_failed() and not force:
        sys.exit("QA failed (build/qa-report.json). Fix and re-run, or use: audiobook deploy --force")
    _run(["git", "add", "docs"])
    if _run(["git", "status", "--porcelain", "docs"]).stdout.strip():
        _run(["git", "commit", "-q", "-m", "chore: publish audiobook assets"])
    branch = _run(["git", "branch", "--show-current"]).stdout.strip() or "main"
    push = _run(["git", "push", "-u", "origin", branch])
    if push.returncode != 0:
        sys.exit(f"push failed: {push.stderr.strip()}")
    slug = _slug()
    if not slug:
        sys.exit("could not determine repo via gh (is gh authenticated?)")
    status = _ensure_pages(slug, branch)
    owner, repo = slug.split("/")
    print(f"pushed {branch}; pages: {status}")
    print(f"live: https://{owner}.github.io/{repo}/")
