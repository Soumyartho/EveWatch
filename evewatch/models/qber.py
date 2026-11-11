"""QBER estimation: sacrifice a random sample of the sifted key and count errors."""

from __future__ import annotations

import numpy as np

from evewatch.models.types import QberReport, SiftedKey


def theoretical_qber(eve_probability: float, noise: float) -> float:
    """Expected sifted-key error rate for intercept-resend plus depolarizing noise.

    Eve alone gives p / 4 and noise alone gives strength / 2; the two act as
    independent bit-flip sources.
    """
    a, b = eve_probability / 4, noise / 2
    return a * (1 - b) + b * (1 - a)


def estimate_qber(
    sifted: SiftedKey,
    sample_fraction: float,
    threshold: float,
    rng: np.random.Generator,
) -> QberReport:
    """Publicly compare a random sample of the sifted key.

    The revealed bits are discarded. The session aborts if the error rate
    exceeds ``threshold``, or if the sifted key is too short to sample at all.
    """
    n = len(sifted)
    n_sample = min(n, max(1, round(n * sample_fraction))) if n else 0
    sample = np.sort(rng.choice(n, size=n_sample, replace=False))
    keep = np.setdiff1d(np.arange(n), sample)

    n_errors = int(np.count_nonzero(sifted.alice_key[sample] != sifted.bob_key[sample]))
    qber = n_errors / n_sample if n_sample else float("nan")

    return QberReport(
        sample_positions=sample,
        n_sample=n_sample,
        n_errors=n_errors,
        qber=qber,
        threshold=threshold,
        abort=n_sample == 0 or qber > threshold,
        alice_remaining=sifted.alice_key[keep],
        bob_remaining=sifted.bob_key[keep],
    )
