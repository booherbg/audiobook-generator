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


def _book_dict(args, book_id, title, selected, voices_cfg, src, book_chapters):
    return {
        "id": book_id,
        "title": title,
        "subtitle": args.subtitle or "",
        "author": args.author or "",
        "date": args.date or "",
        "source_url": src if src.startswith("http") else (args.source_url or ""),
        "description": args.description or "",
        "cover": f"audio/{book_id}/cover.svg",
        "public": True,
        "has_guide": False,
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
    insert_book(manifest, _book_dict(args, book_id, title, present, voices_cfg, src, book_chapters))
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
    doc = clean_document(HTMLLoader().load(resolve(args.source)), _load_repairs(args.repairs))
    if args.chapter_map:
        doc = resection(doc, load_map(args.chapter_map))
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
            silences = Q.measure_silences(mp3, min_dur=3.0)
            hyp = Q.transcribe_clip(mp3, args.sample_sec)
            ref_sample = " ".join(ref_words[: max(len(hyp.split()), 1)])
            wer = Q.wer(ref_sample, hyp)
            ok = (
                wer <= args.wer_max
                and abs(loud["input_i"] - config.LUFS) <= 2.0
                and loud["input_tp"] <= 0.0  # no real clipping
                and len(silences) == 0
                and Q.within_duration_band(dur, words)
            )
            overall = overall and ok
            rows.append({
                "index": ch.index, "voice": vid, "wer": round(wer, 3),
                "lufs": round(loud["input_i"], 2), "tp": round(loud["input_tp"], 2),
                "dur": round(dur, 1), "words": words, "silences": len(silences), "ok": ok,
            })
            print(f"  ch{ch.index:02d} {vid:6s} wer={wer:.3f} lufs={loud['input_i']:5.1f} "
                  f"dur={dur:4.0f}s {'OK' if ok else 'FAIL'}", flush=True)
    report = {"passed": overall, "book": args.id, "wer_max": args.wer_max, "chapters": rows}
    (config.BUILD / "qa-report.json").write_text(json.dumps(report, indent=2))
    bad = sum(1 for r in rows if not r["ok"])
    print(f"\nQA {'PASSED' if overall else 'FAILED'} — {bad} issue(s) over {len(rows)} checks; "
          f"report: build/qa-report.json")
    if not overall:
        sys.exit(1)


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
    q.add_argument("--source", default="build/magnifica.html")
    q.add_argument("--sample-sec", type=float, default=90.0)
    q.add_argument("--wer-max", type=float, default=0.12)
    q.add_argument("--chapter-map", help="JSON file of [{title,anchor}] (must match the "
                                         "map used at generate time)")
    q.add_argument("--repairs", help="JSON {bad: good} map (must match generate time)")
    q.add_argument("--max-chapter-min", type=float, default=config.MAX_CHAPTER_MIN)
    q.set_defaults(func=cmd_qa)

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
