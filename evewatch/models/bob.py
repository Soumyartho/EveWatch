"""Bob: random measurement bases, measures received qubits."""

from __future__ import annotations

import numpy as np

from evewatch.models import quantum


class Bob:
    def __init__(self, rng: np.random.Generator) -> None:
        self._rng = rng
        self.bits = np.empty(0, dtype=np.uint8)
        self.bases = np.empty(0, dtype=np.uint8)

    def measure(self, states: np.ndarray) -> np.ndarray:
        """Pick a random basis per qubit, measure, and return the resulting bits."""
        self.bases = self._rng.integers(0, 2, len(states), dtype=np.uint8)
        self.bits, _ = quantum.measure_qubits(states, self.bases, self._rng)
        return self.bits
