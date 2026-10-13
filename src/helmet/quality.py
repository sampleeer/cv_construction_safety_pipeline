"""Release criteria independent of the training framework."""
from __future__ import annotations

import math


def passes_gate(map50: float, no_helmet_recall: float, min_map50: float,
                min_no_helmet_recall: float) -> bool:
    values = (map50, no_helmet_recall, min_map50, min_no_helmet_recall)
    if not all(math.isfinite(value) and 0 <= value <= 1 for value in values):
        raise ValueError('Metrics and quality thresholds must be finite values in [0,1]')
    return map50 >= min_map50 and no_helmet_recall >= min_no_helmet_recall
