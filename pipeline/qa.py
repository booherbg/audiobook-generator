"""Audio QA helpers: intelligibility (WER vs source) and signal parsing for the
ffmpeg loudnorm / silencedetect output, plus a duration sanity check.
"""

import json
import re

import jiwer

from pipeline.config import WPM

_S_START = re.compile(r"silence_start:\s*([\d.]+)")
_S_DUR = re.compile(r"silence_duration:\s*([\d.]+)")


def _prep(s: str) -> str:
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate after lowercasing and stripping punctuation."""
    ref, hyp = _prep(reference), _prep(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return jiwer.wer(ref, hyp)


def parse_loudnorm(text: str) -> dict:
    """Parse ffmpeg loudnorm print_format=json output → integrated loudness + true peak."""
    start, end = text.rfind("{"), text.rfind("}")
    data = json.loads(text[start : end + 1])
    return {"input_i": float(data["input_i"]), "input_tp": float(data["input_tp"])}


def parse_silences(text: str) -> list[tuple[float, float]]:
    starts = _S_START.findall(text)
    durs = _S_DUR.findall(text)
    return [(float(s), float(d)) for s, d in zip(starts, durs)]


def within_duration_band(actual_sec: float, words: int, wpm: int = WPM, tol: float = 0.4) -> bool:
    expected = words / wpm * 60.0
    if expected <= 0:
        return actual_sec >= 0
    return abs(actual_sec - expected) <= tol * expected


def transcribe(path, model_size: str = "base") -> str:
    """Transcribe an audio file with faster-whisper (downloads model on first use)."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(path), language="en")
    return " ".join(s.text for s in segments)
