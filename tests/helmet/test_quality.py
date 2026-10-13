import pytest

from src.helmet.quality import passes_gate


def test_high_average_map_cannot_hide_missed_helmet_violations():
    assert not passes_gate(.9, 0, .5, .6)
    assert passes_gate(.5, .6, .5, .6)
    assert not passes_gate(.49, .8, .5, .6)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -.1, 1.1])
def test_nonfinite_or_invalid_metrics_do_not_pass(value):
    with pytest.raises(ValueError):
        passes_gate(value, .8, .5, .6)
