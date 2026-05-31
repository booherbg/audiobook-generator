import pytest

from pipeline.config import KOKORO_MODEL

pytestmark = pytest.mark.slow


@pytest.mark.skipif(not KOKORO_MODEL.exists(), reason="Kokoro model not downloaded")
def test_synth_returns_audio():
    from pipeline.tts import KokoroTTS

    tts = KokoroTTS()
    samples, sr = tts.synth("Hello there, friend.", "af_heart")
    assert sr == 24000
    assert len(samples) > 1000
