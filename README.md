# Audiobook Generator

Turn a freely-shared text into a chaptered audiobook with a clean, static web player.
First title: Pope Leo XIV's encyclical **_Magnifica Humanitas_** (on the human person in
the age of artificial intelligence).

**Live site:** https://booherbg.github.io/audiobook-generator/

## How it works

Two halves joined by one file, `docs/manifest.json`:

1. **Pipeline** (`pipeline/`) — a deterministic Python CLI: URL → cleaned text → balanced
   chapters → [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) text-to-speech →
   loudness-normalized mono MP3 (via ffmpeg) → manifest.
2. **Player** (`docs/`) — framework-free HTML/CSS/JS that reads the manifest and plays:
   play/pause, seek, speed, voice switch, chapter nav, resume, Media Session lock-screen
   controls. No build step.

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
uv run audiobook audition <url|file>      # render ~short samples of candidate voices
uv run audiobook qa --id <id>             # WER (clarity) + loudness + silence + duration
uv run audiobook deploy                   # commit docs/, push, ensure GitHub Pages
uv run audiobook list                     # show the library
```

**Add a book by description:** ask Claude Code in this repo to find the canonical full
text of what you want; it hands back a URL, then run `generate`.

## Quality

- **Clarity** is checked automatically: a local Whisper model transcribes a sample of every
  track and the word-error-rate is compared to the source (`audiobook qa`).
- Audio is mono 64 kbps MP3, normalized to −16 LUFS; chapters are balanced (no orphan tracks).

## Tests

```sh
uv run pytest                 # pipeline (text cleaning, normalization, chunking, manifest, qa)
node --test docs/tests/       # player logic (time, resume, voice-switch, view model)
```

## Credits

Built by Blaine Booher with Claude. Narration by Kokoro. The first title is hosted by the
Vatican and reproduced here for accessible listening; the original is always the authority.
