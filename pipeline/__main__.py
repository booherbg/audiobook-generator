"""audiobook CLI: generate | audition | list | deploy.

The pipeline is deterministic and contains no LLM. Finding a source from a free-text
description is Claude Code's job in-session; this CLI takes a URL or file.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

from pipeline import config
from pipeline.assemble import assemble_chapter
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


def clean_document(doc):
    for sec in doc.sections:
        cleaned = [clean_paragraph(p) for p in sec.paragraphs if not is_boilerplate(p)]
        sec.paragraphs = [p for p in cleaned if p]
    doc.sections = [s for s in doc.sections if s.paragraphs]
    return doc


def cmd_generate(args):
    voices_cfg, lexicon = load_voices()
    selected = args.voices.split(",") if args.voices else list(voices_cfg)
    for vid in selected:
        if vid not in voices_cfg:
            sys.exit(f"unknown voice id {vid!r}; known: {list(voices_cfg)}")

    src = resolve(args.resource)
    print(f"loading {src}")
    doc = clean_document(HTMLLoader().load(src))
    chapters = chunk_document(doc, max_min=args.max_chapter_min)
    if args.max_chapters:
        chapters = chapters[: args.max_chapters]

    book_id = args.id or slugify(args.title or doc.title)
    title = args.title or doc.title
    print(f"{len(chapters)} chapters; voices={selected}")

    from pipeline.tts import KokoroTTS  # lazy (loads model)

    engine = KokoroTTS()
    for vid in selected:  # clear stale chapter MP3s from a prior render
        vdir = config.AUDIO_ROOT / book_id / vid
        if vdir.exists():
            shutil.rmtree(vdir)
    book_chapters = []
    for ch in chapters:
        norm = [normalize(s, lexicon) for s in ch.segments]
        entry = {"index": ch.index, "title": ch.title, "files": {}, "duration": {}}
        for vid in selected:
            ref = voices_cfg[vid]["ref"]
            wav_dir = config.BUILD / "wav" / book_id / vid / f"chapter-{ch.index:02d}"
            shutil.rmtree(wav_dir, ignore_errors=True)
            wavs = engine.render_segments(norm, ref, wav_dir)
            out_mp3 = config.AUDIO_ROOT / book_id / vid / f"chapter-{ch.index:02d}.mp3"
            info = assemble_chapter(
                wavs, out_mp3, title=ch.title, album=title, artist=args.author or "", track=ch.index
            )
            shutil.rmtree(wav_dir, ignore_errors=True)
            entry["files"][vid] = out_mp3.relative_to(config.DOCS).as_posix()
            entry["duration"][vid] = round(info["duration"], 1)
            print(f"  ch{ch.index:02d} [{vid}] {info['duration']:.0f}s -> {entry['files'][vid]}")
        book_chapters.append(entry)

    book = {
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
    manifest = load_manifest(config.MANIFEST)
    insert_book(manifest, book)
    save_manifest(config.MANIFEST, manifest)
    print(f"manifest updated: {config.MANIFEST.relative_to(config.ROOT)}  ({book_id})")


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
    print(f"\nListen in {out_dir} and pick your two favourites.")


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
    from pipeline.assemble import measure_loudness, probe

    voices_cfg, lexicon = load_voices()
    doc = clean_document(HTMLLoader().load(resolve(args.source)))
    chapters = chunk_document(doc, max_min=args.max_chapter_min)
    manifest = load_manifest(config.MANIFEST)
    book = next((b for b in manifest["books"] if b["id"] == args.id), None)
    if not book:
        sys.exit(f"book {args.id!r} not in manifest")
    if len(chapters) != len(book["chapters"]):
        sys.exit(f"chapter count mismatch: source={len(chapters)} manifest={len(book['chapters'])}")
    voice_ids = [v["id"] for v in book["voices"]]
    sample_words = int(args.sample_sec / 60 * config.WPM)

    rows, overall = [], True
    for ch, mentry in zip(chapters, book["chapters"]):
        ref_full = " ".join(normalize(s, lexicon) for s in ch.segments)
        words = len(ref_full.split())
        ref_sample = " ".join(ref_full.split()[:sample_words])
        for vid in voice_ids:
            mp3 = config.DOCS / mentry["files"][vid]
            dur = probe(mp3)["duration"]
            loud = measure_loudness(mp3)
            silences = Q.measure_silences(mp3, min_dur=3.0)
            hyp = Q.transcribe_clip(mp3, args.sample_sec)
            wer = Q.wer(ref_sample, hyp)
            ok = (
                wer <= args.wer_max
                and abs(loud["input_i"] - config.LUFS) <= 1.5
                and loud["input_tp"] <= -0.5
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
                  f"dur={dur:4.0f}s {'OK' if ok else 'FAIL'}")
    report = {"passed": overall, "book": args.id, "wer_max": args.wer_max, "chapters": rows}
    (config.BUILD / "qa-report.json").write_text(json.dumps(report, indent=2))
    bad = sum(1 for r in rows if not r["ok"])
    print(f"\nQA {'PASSED' if overall else 'FAILED'} — {bad} issue(s); report: build/qa-report.json")
    if not overall:
        sys.exit(1)


def cmd_deploy(args):
    from pipeline.deploy import deploy

    deploy(force=args.force)


def main(argv=None):
    p = argparse.ArgumentParser(prog="audiobook", description="Local audiobook generator.")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate an audiobook from a URL or file")
    g.add_argument("resource")
    g.add_argument("--id")
    g.add_argument("--title")
    g.add_argument("--subtitle")
    g.add_argument("--author")
    g.add_argument("--date")
    g.add_argument("--description")
    g.add_argument("--source-url", dest="source_url")
    g.add_argument("--voices", help="comma-separated voice ids (default: all in voices.yaml)")
    g.add_argument("--max-chapters", type=int)
    g.add_argument("--max-chapter-min", type=float, default=config.MAX_CHAPTER_MIN)
    g.set_defaults(func=cmd_generate)

    a = sub.add_parser("audition", help="render short samples of candidate voices")
    a.add_argument("resource")
    a.add_argument("--voices", default="af_heart,af_bella,af_nicole,am_michael,am_adam,am_fenrir")
    a.set_defaults(func=cmd_audition)

    sub.add_parser("list", help="list the library").set_defaults(func=cmd_list)

    q = sub.add_parser("qa", help="audio quality check (WER, loudness, silence, duration)")
    q.add_argument("--id", required=True)
    q.add_argument("--source", default="build/magnifica.html", help="source the audio was rendered from")
    q.add_argument("--sample-sec", type=float, default=90.0)
    q.add_argument("--wer-max", type=float, default=0.12)
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
