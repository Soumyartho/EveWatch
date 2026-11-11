"""Seeded random-number helpers for reproducible runs."""

from __future__ import annotations

import numpy as np


def spawn_rngs(seed: int | None, n: int) -> list[np.random.Generator]:
    """Return ``n`` statistically independent generators derived from one seed.

    Each party (Alice, Bob, Eve, the channel, the QBER sampler) gets its own
    stream, so enabling Eve or noise does not change Alice's bits for a given seed.
    """
    return [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(n)]
