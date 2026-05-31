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

## Credits

Built by Blaine Booher with Claude. Narration by Kokoro. The first title is hosted by the
Vatican and reproduced here for accessible listening; the original is always the authority.
See `docs/about.html` for the colophon.
