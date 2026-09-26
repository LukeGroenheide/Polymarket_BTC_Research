"""Certified BTC V1 lifecycle timing for the currently approved buckets."""

from __future__ import annotations

from dataclasses import dataclass


LIFECYCLE40_VERSION = "btc_v1_lifecycle40_v1"
_DURATION_MS = {"5m": 300_000, "15m": 900_000, "1h": 3_600_000,
                "4h": 14_400_000, "1d": 86_400_000}


@dataclass(frozen=True)
class BTCTiming:
    bucket: str
    window_start_ms: int
    window_end_ms: int
    decision_cutoff_ms: int
    version: str = LIFECYCLE40_VERSION

    @property
    def decision_offset_seconds(self) -> int:
        return (self.decision_cutoff_ms - self.window_start_ms) // 1000

    @property
    def duration_seconds(self) -> int:
        return (self.window_end_ms - self.window_start_ms) // 1000

    @property
    def final_target_ms(self) -> int:
        return self.decision_cutoff_ms + 65_000


def lifecycle40(bucket: str, window_start_ms: int, window_end_ms: int) -> BTCTiming:
    """Bind T to an exact certified whole-second fixed-duration window."""
    if bucket not in _DURATION_MS:
        raise ValueError(f"Lifecycle40 is not implemented for BTC {bucket}")
    if (type(window_start_ms) is not int or type(window_end_ms) is not int
            or window_start_ms % 1000 or window_end_ms % 1000
            or window_end_ms - window_start_ms != _DURATION_MS[bucket]):
        raise ValueError("Certified BTC market window has the wrong duration or phase")
    duration_ms = _DURATION_MS[bucket]
    if (2 * duration_ms) % 5:
        raise ValueError("Lifecycle40 cutoff is not a whole millisecond")
    return BTCTiming(bucket, window_start_ms, window_end_ms,
                     window_start_ms + 2 * duration_ms // 5)
