"""Eve: intercept-resend attack with configurable probability p."""

from __future__ import annotations

import numpy as np

from evewatch.models import quantum

NOT_INTERCEPTED = -1  # marker in Eve's basis/bit records for qubits she let pass


class Eve:
    """Intercepts each qubit with probability ``probability``.

    For an intercepted qubit she measures in a random basis and resends the
    collapsed state. Half the time her basis is wrong, and then Bob (measuring
    in Alice's basis) gets a random bit: 50% x 50% = 25% errors on intercepted
    qubits, so the sifted-key error rate is about 25% x p.
    """

    def __init__(self, rng: np.random.Generator, probability: float) -> None:
        self._rng = rng
        self.probability = probability
        self.intercepted = np.empty(0, dtype=bool)
        self.bases = np.empty(0, dtype=np.int8)
        self.bits = np.empty(0, dtype=np.int8)

    def intercept(self, states: np.ndarray) -> np.ndarray:
        """Channel stage: measure-and-resend a random subset of the qubits."""
        n = len(states)
        self.intercepted = self._rng.random(n) < self.probability
        self.bases = np.full(n, NOT_INTERCEPTED, dtype=np.int8)
        self.bits = np.full(n, NOT_INTERCEPTED, dtype=np.int8)

        hit = self.intercepted
        bases = self._rng.integers(0, 2, int(hit.sum()), dtype=np.int8)
        bits, resent = quantum.measure_qubits(states[hit], bases, self._rng)

        self.bases[hit] = bases
        self.bits[hit] = bits
        out = states.copy()
        out[hit] = resent
        return out
