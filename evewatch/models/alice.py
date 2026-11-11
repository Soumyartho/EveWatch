"""Alice: random bits + random bases, encodes each bit as a qubit."""

from __future__ import annotations

import numpy as np

from evewatch.models import quantum


class Alice:
    def __init__(self, rng: np.random.Generator) -> None:
        self._rng = rng
        self.bits = np.empty(0, dtype=np.uint8)
        self.bases = np.empty(0, dtype=np.uint8)

    def prepare(self, n_qubits: int) -> np.ndarray:
        """Pick random bits and bases, and return the encoded qubits."""
        self.bits = self._rng.integers(0, 2, n_qubits, dtype=np.uint8)
        self.bases = self._rng.integers(0, 2, n_qubits, dtype=np.uint8)
        return quantum.prepare_qubits(self.bits, self.bases)
