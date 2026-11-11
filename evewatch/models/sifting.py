"""Public basis comparison; keep only matching-basis positions."""

from __future__ import annotations

import numpy as np

from evewatch.models.types import SiftedKey, TransmissionRecord


def sift(record: TransmissionRecord) -> SiftedKey:
    """Keep the positions where Alice and Bob happened to use the same basis.

    Only the bases are compared publicly; the bit values stay secret.
    """
    indices = np.flatnonzero(record.alice_bases == record.bob_bases)
    return SiftedKey(
        indices=indices,
        alice_key=record.alice_bits[indices],
        bob_key=record.bob_bits[indices],
    )
