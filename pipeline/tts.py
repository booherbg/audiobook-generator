"""Kokoro (ONNX) text-to-speech wrapper. One model load per process; renders each
text segment to its own WAV so assemble.py can insert paragraph pauses.
"""

from pathlib import Path

import numpy as np
import soundfile as sf

from pipeline.config import KOKORO_MODEL, KOKORO_VOICES


class KokoroTTS:
    def __init__(self, model=KOKORO_MODEL, voices=KOKORO_VOICES):
        from kokoro_onnx import Kokoro  # imported lazily (heavy)

        self._kokoro = Kokoro(str(model), str(voices))

    def synth(self, text: str, voice: str, speed: float = 1.0, lang: str = "en-us"):
        samples, sr = self._kokoro.create(text, voice=voice, speed=speed, lang=lang)
        return np.asarray(samples, dtype=np.float32), int(sr)

    def render_segments(self, segments, voice, out_dir, speed: float = 1.0) -> list[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, seg in enumerate(segments):
            text = seg.strip()
            if not text:
                continue
            samples, sr = self.synth(text, voice, speed=speed)
            p = out_dir / f"seg_{i:04d}.wav"
            sf.write(str(p), samples, sr)
            paths.append(p)
        return paths
