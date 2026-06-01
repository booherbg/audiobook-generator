"""audiobook CLI: generate | audition | list | qa | deploy.

The pipeline is deterministic and contains no LLM. Finding a source from a free-text
description is Claude Code's job in-session; this CLI takes a URL or file.

`generate` is resumable: chapters already rendered on disk are skipped, and the manifest
is rebuilt from whatever audio is present — so an interrupted run just continues.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

from pipeline import config
from pipeline.assemble import assemble_chapter, probe
from pipeline.chapter_map import load_map, resection
from pipeline.chunk import chunk_document
from pipeline.clean import clean_paragraph, is_boilerplate
from pipeline.load import HTMLLoader
from pipeline.manifest import insert_book, load_manifest, save_manifest
from pipeline.normalize import normalize
from pipeline.resolve import ResolveError, resolve

VOICES_FILE = Path(__file__).parent / "voices.yaml"


def load_voices():
    data = yaml.safe_load(VOICES_FILE.read_text())
    return data.get("voices", {}), (data.get("lexicon") or {})


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", (text or "").lower()).strip()
    return re.sub(r"[\s_-]+", "-", text) or "book"


def clean_document(doc, repairs=None):
    for sec in doc.sections:
        cleaned = [clean_paragraph(p, repairs) for p in sec.paragraphs if not is_boilerplate(p)]
        sec.paragraphs = [p for p in cleaned if p]
    doc.sections = [s for s in doc.sections if s.paragraphs]
    return doc


def _load_repairs(path):
    """Optional {bad: good} spacing-repair map for a source's export defects."""
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else None


def _book_dict(args, book_id, title, selected, voices_cfg, src, book_chapters, existing=None):
    """Build the manifest entry, PRESERVING existing metadata when an arg isn't supplied.

    A partial re-render (e.g. `generate --chapters 1:1` with no --subtitle) must not wipe
    the book's subtitle/date/author or flip flags like has_guide/wip back to defaults — a
    footgun that previously blanked metadata. Args override; otherwise keep what's there.
    """
    existing = existing or {}

    def keep(field, arg_val, default=""):
        return arg_val if arg_val else existing.get(field, default)

    return {
        "id": book_id,
        "title": title or existing.get("title", ""),
        "subtitle": keep("subtitle", args.subtitle),
        "author": keep("author", args.author),
        "date": keep("date", args.date),
        "source_url": (src if src.startswith("http")
                       else (args.source_url or existing.get("source_url", ""))),
        # Copyright/attribution line shown to readers (e.g. "© Libreria Editrice Vaticana").
        # Required where reproduction rests on a cite-the-copyright permission.
        "rights": keep("rights", getattr(args, "rights", "")),
        "description": keep("description", args.description),
        "cover": existing.get("cover", f"audio/{book_id}/cover.svg"),
        "public": existing.get("public", True),
        "has_guide": existing.get("has_guide", False),
        # preserve the work-in-progress flag across re-renders (only carry it if set)
        **({"wip": True} if existing.get("wip") else {}),
        "voices": [
            {"id": v, "label": voices_cfg[v]["label"], "engine": "kokoro", "ref": voices_cfg[v]["ref"]}
            for v in selected
        ],
        "chapters": book_chapters,
    }


def _write_manifest(args, book_id, title, chapters, selected, voices_cfg, src):
    """Rebuild the book entry from audio actually on disk (resume-safe).

    Scans EVERY voice configured in voices.yaml — not just the `selected` ones for this
    run — so a single-voice re-render (e.g. --voices male) never drops the other voice's
    chapters from the manifest. A voice is included if it has a chapter-01 mp3 on disk.
    """
    present = [v for v in voices_cfg
              if (config.AUDIO_ROOT / book_id / v / "chapter-01.mp3").exists()]
    book_chapters = []
    for ch in chapters:
        files, durs = {}, {}
        for vid in present:
            mp3 = config.AUDIO_ROOT / book_id / vid / f"chapter-{ch.index:02d}.mp3"
            if mp3.exists() and mp3.stat().st_size > 1000:
                files[vid] = mp3.relative_to(config.DOCS).as_posix()
                durs[vid] = round(probe(mp3)["duration"], 1)
        if files and len(files) == len(present):  # only chapters complete for all present voices
            book_chapters.append({"index": ch.index, "title": ch.title, "files": files, "duration": durs})
    manifest = load_manifest(config.MANIFEST)
    existing = next((b for b in manifest.get("books", []) if b.get("id") == book_id), None)
    insert_book(manifest, _book_dict(args, book_id, title, present, voices_cfg, src,
                                     book_chapters, existing))
    save_manifest(config.MANIFEST, manifest)
    print(f"manifest: {len(book_chapters)}/{len(chapters)} chapters, voices={present}", flush=True)


def cmd_generate(args):
    voices_cfg, lexicon = load_voices()
    selected = args.voices.split(",") if args.voices else list(voices_cfg)
    for vid in selected:
        if vid not in voices_cfg:
            sys.exit(f"unknown voice id {vid!r}; known: {list(voices_cfg)}")

    src = resolve(args.resource)
    print(f"loading {src}", flush=True)
    doc = clean_document(HTMLLoader().load(src), _load_repairs(args.repairs))
    if args.chapter_map:
        doc = resection(doc, load_map(args.chapter_map))
        print(f"re-sectioned by chapter map: {len(doc.sections)} chapters", flush=True)
    chapters = chunk_document(doc, max_min=args.max_chapter_min)
    book_id = args.id or slugify(args.title or doc.title)
    title = args.title or doc.title

    # Ensure a cover exists so the library card never shows a broken image. A hand-made
    # cover is left untouched; this only fills the gap for a new book.
    from pipeline.cover import ensure_cover

    _, created = ensure_cover(book_id, title, args.author or "", args.subtitle or "")
    if created:
        print(f"wrote default cover: audio/{book_id}/cover.svg", flush=True)

    start, end = 1, len(chapters)
    if args.chapters:
        a, _, b = args.chapters.partition(":")
        start = int(a) if a else 1
        end = int(b) if b else len(chapters)
    if args.clean:
        for vid in selected:
            shutil.rmtree(config.AUDIO_ROOT / book_id / vid, ignore_errors=True)

    print(f"{len(chapters)} chapters total; rendering {start}..{end}; voices={selected}", flush=True)
    engine = None  # lazy: load the model only if something actually needs rendering
    for ch in chapters:
        if not (start <= ch.index <= end):
            continue
        norm = None
        expected_sec = len(" ".join(normalize(s, lexicon) for s in ch.segments).split()) / config.WPM * 60.0
        for vid in selected:
            out_mp3 = config.AUDIO_ROOT / book_id / vid / f"chapter-{ch.index:02d}.mp3"
            # Resume only if the file is plausibly complete. A render killed mid-chapter
            # (e.g. by a crash) leaves a too-short MP3 — re-render rather than skip it.
            if out_mp3.exists() and out_mp3.stat().st_size > 1000 and not args.force:
                actual = probe(out_mp3)["duration"]
                if actual >= 0.6 * expected_sec:
                    print(f"  ch{ch.index:02d} [{vid}] exists ({actual:.0f}s) — skip", flush=True)
                    continue
                print(f"  ch{ch.index:02d} [{vid}] partial ({actual:.0f}s/{expected_sec:.0f}s) — re-render", flush=True)
            if engine is None:
                from pipeline.tts import KokoroTTS

                engine = KokoroTTS()
            if norm is None:
                norm = [normalize(s, lexicon) for s in ch.segments]
            ref = voices_cfg[vid]["ref"]
            wav_dir = config.BUILD / "wav" / book_id / vid / f"chapter-{ch.index:02d}"
            shutil.rmtree(wav_dir, ignore_errors=True)
            wavs = engine.render_segments(norm, ref, wav_dir)
            info = assemble_chapter(
                wavs, out_mp3, title=ch.title, album=title, artist=args.author or "", track=ch.index
            )
            shutil.rmtree(wav_dir, ignore_errors=True)
            print(f"  ch{ch.index:02d} [{vid}] {info['duration']:.0f}s", flush=True)

    _write_manifest(args, book_id, title, chapters, selected, voices_cfg, src)


def cmd_audition(args):
    src = resolve(args.resource)
    doc = clean_document(HTMLLoader().load(src))
    sample = ""
    for sec in doc.sections:
        for p in sec.paragraphs:
            sample = " ".join((sample + " " + p).split()[:70])
            if len(sample.split()) >= 60:
                break
        if sample:
            break
    sample = normalize(sample)
    out_dir = config.BUILD / "audition"
    out_dir.mkdir(parents=True, exist_ok=True)

    from pipeline.tts import KokoroTTS

    engine = KokoroTTS()
    for ref in args.voices.split(","):
        wavs = engine.render_segments([sample], ref, out_dir / ref)
        out_mp3 = out_dir / f"{ref}.mp3"
        assemble_chapter(wavs, out_mp3, title=f"audition {ref}")
        shutil.rmtree(out_dir / ref, ignore_errors=True)
        print(f"  {ref} -> {out_mp3}")
    print(f"\nListen in {out_dir} and pick two favourites.")


def cmd_list(args):
    manifest = load_manifest(config.MANIFEST)
    if not manifest["books"]:
        print("(no books yet)")
        return
    for b in manifest["books"]:
        voices = ",".join(v["id"] for v in b.get("voices", []))
        print(f"{b['id']}: {b['title']} — {len(b.get('chapters', []))} chapters [{voices}]")


def cmd_qa(args):
    from pipeline import qa as Q
    from pipeline.assemble import measure_loudness

    voices_cfg, lexicon = load_voices()
    # Default source / chapter-map / repairs from the book's recipe so QA re-cleans the text
    # EXACTLY as generate did — otherwise WER mismatches the audio and QA fails spuriously.
    # Explicit flags still override. (validate_guide.py auto-discovers the same way.)
    recipe_path = config.ROOT / "data" / "books" / f"{args.id}.json"
    recipe = json.loads(recipe_path.read_text()) if recipe_path.exists() else {}
    source = args.source or recipe.get("source_file") or recipe.get("source_url")
    if not source:
        sys.exit(f"no --source given and no recipe at {recipe_path}; pass --source")
    chapter_map = args.chapter_map or recipe.get("chapter_map")
    repairs_path = args.repairs or recipe.get("repairs")
    doc = clean_document(HTMLLoader().load(resolve(source)), _load_repairs(repairs_path))
    if chapter_map:
        doc = resection(doc, load_map(chapter_map))
    chapters = chunk_document(doc, max_min=args.max_chapter_min)
    manifest = load_manifest(config.MANIFEST)
    book = next((b for b in manifest["books"] if b["id"] == args.id), None)
    if not book:
        sys.exit(f"book {args.id!r} not in manifest")
    by_index = {c["index"]: c for c in book["chapters"]}
    voice_ids = [v["id"] for v in book["voices"]]
    sample_words = int(args.sample_sec / 60 * config.WPM)

    rows, overall = [], True
    for ch in chapters:
        mentry = by_index.get(ch.index)
        if not mentry:
            continue  # not rendered yet
        ref_full = " ".join(normalize(s, lexicon) for s in ch.segments)
        words = len(ref_full.split())
        ref_words = ref_full.split()[: sample_words + 40]
        for vid in voice_ids:
            mp3 = config.DOCS / mentry["files"][vid]
            dur = probe(mp3)["duration"]
            loud = measure_loudness(mp3)
            # Real maximum sample level (astats), not loudnorm's predicted inter-sample
            # true-peak: the latter routinely reads a hair above 0 on perfectly clean
            # spoken-word MP3s and is not meaningful for lossy audio. >= 0 dBFS here is
            # ACTUAL digital clipping. (See build/verify_all.py and the project memory.)
            peak = Q.sample_peak_dbfs(mp3)
            silences = Q.measure_silences(mp3, min_dur=3.0)
            hyp = Q.transcribe_clip(mp3, args.sample_sec)
            ref_sample = " ".join(ref_words[: max(len(hyp.split()), 1)])
            wer = Q.wer(ref_sample, hyp)
            ok = (
                wer <= args.wer_max
                and abs(loud["input_i"] - config.LUFS) <= 2.0
                and peak < 0.0  # no real clipping (astats sample peak)
                and len(silences) == 0
                and Q.within_duration_band(dur, words)
            )
            overall = overall and ok
            rows.append({
                "index": ch.index, "voice": vid, "wer": round(wer, 3),
                "lufs": round(loud["input_i"], 2), "peak": round(peak, 2),
                "dur": round(dur, 1), "words": words, "silences": len(silences), "ok": ok,
            })
            print(f"  ch{ch.index:02d} {vid:6s} wer={wer:.3f} lufs={loud['input_i']:5.1f} "
                  f"peak={peak:5.2f} dur={dur:4.0f}s {'OK' if ok else 'FAIL'}", flush=True)
    report = {"passed": overall, "book": args.id, "wer_max": args.wer_max, "chapters": rows}
    (config.BUILD / "qa-report.json").write_text(json.dumps(report, indent=2))
    bad = sum(1 for r in rows if not r["ok"])
    print(f"\nQA {'PASSED' if overall else 'FAILED'} — {bad} issue(s) over {len(rows)} checks; "
          f"report: build/qa-report.json")
    if not overall:
        sys.exit(1)


def cmd_regenerate(args):
    """Rebuild a book end-to-end from its tracked recipe (data/books/<id>.json).

    Audio is a BUILD ARTIFACT, not a precious snapshot: everything needed to reproduce a book
    lives in git (the recipe + chapter map + repairs + companion script + voices.yaml), and the
    source text is fetched from its source_url. Re-running is resumable (chapters already on
    disk and plausibly complete are skipped), so this is safe to re-run after an interruption.
    Note: TTS/ffmpeg output is reproducible-in-spirit (a fresh QA-passing edition), not
    necessarily byte-identical to a previous render.
    """
    recipe_path = config.ROOT / "data" / "books" / f"{args.id}.json"
    if not recipe_path.exists():
        sys.exit(f"no recipe at {recipe_path}; recipes live in data/books/<id>.json")
    r = json.loads(recipe_path.read_text())
    print(f"regenerating '{r['id']}' from {recipe_path.relative_to(config.ROOT)}", flush=True)

    # Canonical text = the committed snapshot (data/sources/<id>.html) for byte-stable, offline,
    # vatican.va-independent reproduction. source_url stays as the human attribution reference.
    # If the recipe DECLARES a source_file, it must exist — failing loudly here beats silently
    # fetching the live URL and quietly breaking the offline/byte-stable guarantee.
    src_file = r.get("source_file")
    if src_file:
        snapshot = config.ROOT / src_file
        if not snapshot.exists():
            sys.exit(f"recipe declares source_file '{src_file}' but it's missing. Commit the "
                     f"source snapshot there (the canonical text), or remove source_file from "
                     f"the recipe to build from the live source_url instead.")
        resource = str(snapshot)
    elif r.get("source_url"):
        print("  WARNING: no source_file in recipe — building from the live source_url "
              "(not byte-stable; the page can drift or 404).", flush=True)
        resource = r["source_url"]
    else:
        sys.exit("recipe has neither source_file nor source_url")
    print(f"  source: {resource}", flush=True)

    # 1) Audio + manifest — reuse cmd_generate by constructing its args from the recipe.
    gen = argparse.Namespace(
        resource=resource, id=r["id"], title=r.get("title"), subtitle=r.get("subtitle"),
        author=r.get("author"), date=r.get("date"), description=r.get("description"),
        source_url=r["source_url"], rights=r.get("rights"),
        voices=",".join(r.get("voices") or []) or None,
        chapters=args.chapters, chapter_map=r.get("chapter_map"), repairs=r.get("repairs"),
        max_chapter_min=config.MAX_CHAPTER_MIN, clean=args.clean, force=args.force,
    )
    if args.skip_audio:
        print("  (skip-audio: rebuilding text/companion only, not MP3s)", flush=True)
    else:
        cmd_generate(gen)

    # 2) Persist the WIP flag from the recipe (generate preserves but never sets it).
    manifest = load_manifest(config.MANIFEST)
    for b in manifest.get("books", []):
        if b.get("id") == r["id"]:
            if r.get("wip"):
                b["wip"] = True
            else:
                b.pop("wip", None)
    save_manifest(config.MANIFEST, manifest)

    # 3) Companion + read-along + full-text, via the book's guide builder.
    builder = r.get("guide_builder")
    if builder:
        import importlib

        print(f"  building companion via {builder}", flush=True)
        importlib.import_module(builder).main(resource)

    print(f"regenerated '{r['id']}'. Run `audiobook qa --id {r['id']}` then `audiobook deploy`.",
          flush=True)


def cmd_deploy(args):
    from pipeline.deploy import deploy

    deploy(force=args.force)


def main(argv=None):
    p = argparse.ArgumentParser(prog="audiobook", description="Local audiobook generator.")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate an audiobook from a URL or file (resumable)")
    g.add_argument("resource")
    g.add_argument("--id")
    g.add_argument("--title")
    g.add_argument("--subtitle")
    g.add_argument("--author")
    g.add_argument("--date")
    g.add_argument("--description")
    g.add_argument("--source-url", dest="source_url")
    g.add_argument("--rights", help='copyright/attribution line shown to readers, '
                                     'e.g. "© Libreria Editrice Vaticana"')
    g.add_argument("--voices", help="comma-separated voice ids (default: all in voices.yaml)")
    g.add_argument("--chapters", help="range to render, e.g. 1:3 (1-based, inclusive)")
    g.add_argument("--chapter-map", help="JSON file of [{title,anchor}] to re-section a "
                                         "source that has no usable headings")
    g.add_argument("--repairs", help="JSON {bad: good} map fixing missing-space export "
                                     "defects in the source HTML")
    g.add_argument("--max-chapter-min", type=float, default=config.MAX_CHAPTER_MIN)
    g.add_argument("--clean", action="store_true", help="delete this book's audio first")
    g.add_argument("--force", action="store_true", help="re-render chapters even if present")
    g.set_defaults(func=cmd_generate)

    a = sub.add_parser("audition", help="render short samples of candidate voices")
    a.add_argument("resource")
    a.add_argument("--voices", default="af_heart,af_bella,af_nicole,am_michael,am_adam,am_fenrir")
    a.set_defaults(func=cmd_audition)

    sub.add_parser("list", help="list the library").set_defaults(func=cmd_list)

    q = sub.add_parser("qa", help="audio quality check (WER, loudness, silence, duration)")
    q.add_argument("--id", required=True)
    q.add_argument("--source", help="source text (default: the book's recipe source_file/source_url)")
    q.add_argument("--sample-sec", type=float, default=90.0)
    q.add_argument("--wer-max", type=float, default=0.12)
    q.add_argument("--chapter-map", help="JSON file of [{title,anchor}] (must match the "
                                         "map used at generate time)")
    q.add_argument("--repairs", help="JSON {bad: good} map (must match generate time)")
    q.add_argument("--max-chapter-min", type=float, default=config.MAX_CHAPTER_MIN)
    q.set_defaults(func=cmd_qa)

    r = sub.add_parser("regenerate", help="rebuild a book end-to-end from its recipe "
                                          "(data/books/<id>.json) — audio is a build artifact")
    r.add_argument("id", help="book id with a recipe in data/books/<id>.json")
    r.add_argument("--chapters", help="range to render, e.g. 1:3 (1-based, inclusive)")
    r.add_argument("--clean", action="store_true", help="delete this book's audio first")
    r.add_argument("--force", action="store_true", help="re-render chapters even if present")
    r.add_argument("--skip-audio", action="store_true",
                   help="rebuild only text/companion/read-along, not MP3s (fast)")
    r.set_defaults(func=cmd_regenerate)

    d = sub.add_parser("deploy", help="commit docs/, push, ensure GitHub Pages")
    d.add_argument("--force", action="store_true", help="deploy even if QA failed")
    d.set_defaults(func=cmd_deploy)

    args = p.parse_args(argv)
    try:
        args.func(args)
    except ResolveError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
