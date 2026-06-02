"""Screen candidate Kokoro voices for a book and rank them objectively.

Usage: python scripts/audition_screen.py <book-id> [ref1,ref2,...]

Renders the first ~60 words of the book's source (the same sample `audiobook audition`
uses) in each candidate voice, transcribes it back with faster-whisper, and prints a
table ranked by WER (intelligibility) with loudness + sample-peak as sanity checks.

This is the picking method when you can't audition by ear: lower WER = the TTS speaks
that text more cleanly in that voice. Loudness reads ~-16 LUFS for all (the same loudnorm
the real render applies) and peak should be <0 (no clipping); WER is the discriminator.
The transcripts are printed too, so you can eyeball how each voice handles the source's
foreign phrases (Latin/Italian) — the pronunciation check (BACKLOG item) starts here.

MP3s land in build/audition/<ref>.mp3 so a human can also listen and confirm the pick.
"""

import json
import shutil
import sys

from pipeline import config
from pipeline import qa as Q
from pipeline.assemble import assemble_chapter, measure_loudness
from pipeline.clean import clean_paragraph, is_boilerplate
from pipeline.load import HTMLLoader
from pipeline.normalize import normalize

DEFAULT_REFS = ["af_bella", "bf_emma", "af_aoede", "am_fenrir", "bm_fable", "am_onyx"]


def clean_document(doc):
    for sec in doc.sections:
        cleaned = [clean_paragraph(p) for p in sec.paragraphs if not is_boilerplate(p)]
        sec.paragraphs = [p for p in cleaned if p]
    doc.sections = [s for s in doc.sections if s.paragraphs]
    return doc


def sample_text(doc, n=60):
    """First ~n words of the cleaned source — mirrors cmd_audition's sample."""
    sample = ""
    for sec in doc.sections:
        for p in sec.paragraphs:
            sample = " ".join((sample + " " + p).split()[:70])
            if len(sample.split()) >= n:
                break
        if sample:
            break
    return sample


def main():
    book_id = sys.argv[1] if len(sys.argv) > 1 else "laudato-si"
    refs = sys.argv[2].split(",") if len(sys.argv) > 2 else DEFAULT_REFS
    recipe = json.loads((config.ROOT / "data" / "books" / f"{book_id}.json").read_text())
    src = config.ROOT / recipe["source_file"]

    doc = clean_document(HTMLLoader().load(str(src)))
    sample = normalize(sample_text(doc))
    print(f"book: {book_id}  ({len(sample.split())}-word sample)\n{sample}\n", flush=True)

    out_dir = config.BUILD / "audition"
    out_dir.mkdir(parents=True, exist_ok=True)

    from pipeline.tts import KokoroTTS

    engine = KokoroTTS()
    rows = []
    for ref in refs:
        wavs = engine.render_segments([sample], ref, out_dir / ref)
        mp3 = out_dir / f"{ref}.mp3"
        assemble_chapter(wavs, mp3, title=f"audition {ref}")
        shutil.rmtree(out_dir / ref, ignore_errors=True)
        hyp = Q.transcribe_clip(mp3, 90)
        wer = Q.wer(sample, hyp)
        loud = measure_loudness(mp3)["input_i"]
        peak = Q.sample_peak_dbfs(mp3)
        rows.append({"ref": ref, "wer": wer, "lufs": loud, "peak": peak, "hyp": hyp.strip()})
        print(f"  rendered {ref:10s} wer={wer:.3f} lufs={loud:6.2f} peak={peak:6.2f}", flush=True)

    rows.sort(key=lambda r: r["wer"])
    print("\n=== ranked by WER (lower = clearer) ===")
    for r in rows:
        print(f"{r['ref']:10s} WER {r['wer']:.3f}  LUFS {r['lufs']:6.2f}  peak {r['peak']:6.2f}")
    print("\n=== transcripts (eyeball the Latin/Italian) ===")
    for r in rows:
        print(f"[{r['ref']}] {r['hyp']}")


if __name__ == "__main__":
    main()
