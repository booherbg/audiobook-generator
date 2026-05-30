import numpy as np
import pytest
import soundfile as sf

pytestmark = pytest.mark.slow


def _tone(path, sr=24000, secs=0.5):
    t = np.linspace(0, secs, int(sr * secs), endpoint=False)
    sf.write(str(path), (0.1 * np.sin(2 * np.pi * 220 * t)).astype("float32"), sr)


def test_assemble_chapter(tmp_path):
    from pipeline.assemble import assemble_chapter

    w1, w2 = tmp_path / "a.wav", tmp_path / "b.wav"
    _tone(w1)
    _tone(w2)
    out = tmp_path / "ch.mp3"
    info = assemble_chapter([w1, w2], out, title="T", album="Al", artist="Ar", track=1, pause_ms=400)
    assert out.exists()
    assert info["channels"] == 1
    assert info["sample_rate"] == 44100
    assert 1.2 < info["duration"] < 1.7  # 0.5 + 0.4 pause + 0.5
