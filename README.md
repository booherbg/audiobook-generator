# Audiobook Generator

Turn a freely-shared text into a chaptered audiobook with a clean, static web player.
First title: Pope Leo XIV's encyclical **_Magnifica Humanitas_** (on the human person in
the age of artificial intelligence).

**Live:** https://booherbg.github.io/audiobook-generator/

## How it works

Two halves joined by one file, `docs/manifest.json`:

1. **Pipeline** (`pipeline/`) — a deterministic Python CLI: URL → cleaned text → balanced
   chapters → [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) text-to-speech →
   loudness-normalized mono MP3 (ffmpeg `loudnorm` + `alimiter`) → manifest.
2. **Player** (`docs/`) — framework-free HTML/CSS/JS that reads the manifest and plays:
   play/pause, seek, ±15/30s, speed, voice switch, chapter nav, resume, Media Session
   lock-screen controls. No build step.

There is **no LLM in the pipeline** and **no API keys**. Finding a source from a free-text
description is done by Claude Code in-session (it returns a URL); the CLI takes the URL.

## Setup (macOS, Apple Silicon)

```sh
brew install espeak-ng ffmpeg
uv sync --extra dev                       # Python 3.12 venv + deps
uv run python -m pipeline.setup_models    # download the Kokoro model (~330 MB)
```

## Usage

```sh
uv run audiobook generate <url|file> --id <id> --title "..." --author "..."
uv run audiobook generate <url> --voices male --chapters 3:5   # resumable; subset re-render
uv run audiobook audition <url|file>      # render short samples of candidate voices
uv run audiobook list                     # show the library
uv run audiobook qa --id <id>             # WER (clarity) + loudness + clipping + duration
uv run audiobook deploy                   # commit docs/, push, ensure GitHub Pages
```

**Add a book by description:** ask Claude Code in this repo to find the canonical full
text of what you want; it returns a URL, then run `generate`. `generate` is **resumable**
(skips chapters already rendered, validates their duration) and **multi-voice safe** (a
single-voice re-render preserves the other voice in the manifest).

## Build your own / add a book

Two paths, both in the **[playbook](docs/playbook/README.md)**:

- **[Build your own local copies](docs/playbook/build-your-own.md)** of the books already here —
  render them to MP3 on your machine, or swap in a different voice. Just run scripts; audio is a
  regenerable build artifact (`audiobook regenerate <id>`), so this is a first-class workflow.
- **[Author a new book](docs/playbook/authoring-a-new-book.md)** from a text not yet here. Two
  parts: a deterministic *render* half, and an LLM-led *asset-preparation* half (cleaning,
  chaptering, the companion, the critic panel). **The pipeline has no LLM and no API keys** — the
  LLM is the operator/author who prepares the inputs; running the pipeline needs neither.

Deep references: [data contracts](docs/playbook/data-contracts.md) ·
[companion authoring](docs/playbook/companion-authoring.md) ·
[critic panel](docs/playbook/critic-panel.md) · [QA audit](docs/playbook/qa-audit.md). The contract
each edition satisfies is the [expansion spec](docs/superpowers/specs/2026-05-31-book-expansion-spec.md).

**What to add next:** [docs/WORK-QUEUE.md](docs/WORK-QUEUE.md) is the curated, copyright-vetted
reading list — Magnifica's references traced back through Catholic social teaching, the
philosophy of technology, and the ancients, plus world-wisdom and public-domain-sci-fi runs.

## Audio quality

Every track is mono 64 kbps MP3, loudness-normalized to −16 LUFS with a true-peak limiter
so nothing clips after MP3 encoding. `audiobook qa` transcribes a sample of each track with
a local Whisper model and compares word-error-rate to the source, and checks loudness,
clipping (sample peak < 0 dBFS), silence gaps, and duration. *Magnifica Humanitas* passes
34/34 (WER avg ~1.7%).

## Storage

Audio is committed directly under `docs/audio/` (GitHub Pages can't serve Git LFS). The
library is capped at the core set per `BACKLOG.md`; audio-heavy extras (a voiced commentary
track, an enriched "woven" edition) are deferred.

## Tests

```sh
uv run pytest                 # pipeline: cleaning, normalization, chunking, manifest, qa, cli
node --test docs/tests/*.mjs  # player logic: time, resume, voice-switch, view model
```

## License

The **code** (pipeline, scripts, web player, docs) is **[MIT](LICENSE)** — reuse the machinery
freely. The **content is not**: the source texts and rendered audiobooks remain © their respective
holders (e.g. © Libreria Editrice Vaticana, reproduced free/non-commercial/attributed/not-sold-
separately) or are public domain by age (e.g. *Rerum Novarum*, 1891). Reuse the pipeline under MIT;
your use of the books is governed by their own rights. See [LICENSE](LICENSE) for the full
code/content split and `docs/WORK-QUEUE.md` for the per-work copyright detail.

## Credits

Built by Blaine Booher with Claude. Narration by Kokoro. The first titles are hosted by the
Vatican and reproduced here for accessible listening; the original is always the authority.
See `docs/about.html` for the colophon.
