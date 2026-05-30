from pipeline.qa import parse_loudnorm, parse_silences, wer, within_duration_band

_LOUDNORM = """
[Parsed_loudnorm_0 @ 0x600000]
{
	"input_i" : "-16.12",
	"input_tp" : "-1.40",
	"input_lra" : "9.80",
	"input_thresh" : "-26.30",
	"output_i" : "-16.00",
	"target_offset" : "0.12"
}
"""

_SILENCE = (
    "[silencedetect @ 0x] silence_start: 1.0\n"
    "[silencedetect @ 0x] silence_end: 4.0 | silence_duration: 3.0\n"
    "[silencedetect @ 0x] silence_start: 10.0\n"
    "[silencedetect @ 0x] silence_end: 10.5 | silence_duration: 0.5\n"
)


def test_wer_identical():
    assert wer("the human person", "the human person") == 0.0


def test_wer_one_substitution():
    assert abs(wer("the human person", "the human robot") - 1 / 3) < 1e-6


def test_parse_loudnorm():
    d = parse_loudnorm(_LOUDNORM)
    assert abs(d["input_i"] + 16.12) < 1e-6
    assert abs(d["input_tp"] + 1.40) < 1e-6


def test_parse_silences():
    assert parse_silences(_SILENCE) == [(1.0, 3.0), (10.0, 0.5)]


def test_within_duration_band():
    assert within_duration_band(60, 155)
    assert not within_duration_band(200, 155)
