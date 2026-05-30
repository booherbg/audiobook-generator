"""Assemble per-segment WAVs into one loudness-normalized, tagged MP3 via ffmpeg.

Stitching (with paragraph pauses) is done in numpy for format safety; ffmpeg
handles loudnorm + mono 64k MP3 encoding + ID3 tags.
"""

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from pipeline.config import LRA, LUFS, MP3_BITRATE, OUT_SR, PARA_PAUSE_MS, SAMPLE_RATE, TRUE_PEAK


def probe(path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    astream = next(s for s in data["streams"] if s["codec_type"] == "audio")
    return {
        "channels": int(astream["channels"]),
        "sample_rate": int(astream["sample_rate"]),
        "duration": float(data["format"]["duration"]),
    }


def stitch_wavs(wav_paths, out_wav, pause_ms: int = PARA_PAUSE_MS) -> Path:
    parts = []
    sr = SAMPLE_RATE
    for i, p in enumerate(wav_paths):
        data, sr = sf.read(str(p), dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        if i > 0 and pause_ms > 0:
            parts.append(np.zeros(int(sr * pause_ms / 1000), dtype=np.float32))
        parts.append(data)
    combined = np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)
    sf.write(str(out_wav), combined, sr)
    return Path(out_wav)


def encode_mp3(in_wav, out_mp3, title="", album="", artist="", track=0) -> Path:
    cmd = [
        "ffmpeg", "-y", "-i", str(in_wav),
        # loudnorm to -16 LUFS with a -1.5 dBFS peak ceiling → no sample clipping.
        "-af", f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA={LRA}",
        "-ac", "1", "-ar", str(OUT_SR), "-codec:a", "libmp3lame", "-b:a", MP3_BITRATE,
    ]
    for key, val in (("title", title), ("album", album), ("artist", artist)):
        if val:
            cmd += ["-metadata", f"{key}={val}"]
    if track:
        cmd += ["-metadata", f"track={track}"]
    cmd += [str(out_mp3)]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return Path(out_mp3)


def measure_loudness(path) -> dict:
    from pipeline.qa import parse_loudnorm

    res = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af",
         f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA={LRA}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    return parse_loudnorm(res.stderr)


def assemble_chapter(wav_paths, out_mp3, title="", album="", artist="", track=0,
                     pause_ms: int = PARA_PAUSE_MS) -> dict:
    out_mp3 = Path(out_mp3)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    combined = out_mp3.with_suffix(".combined.wav")
    stitch_wavs(wav_paths, combined, pause_ms)
    encode_mp3(combined, out_mp3, title, album, artist, track)
    combined.unlink(missing_ok=True)
    return probe(out_mp3)
