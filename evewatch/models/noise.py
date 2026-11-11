"""Depolarizing noise model (channel noise, distinct from eavesdropping)."""

from __future__ import annotations

import numpy as np

from evewatch.models.quantum import X_GATE, apply_gate

Y_GATE = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z_GATE = np.array([[1, 0], [0, -1]], dtype=complex)

# Index into this tuple is the value stored in ``DepolarizingNoise.paulis``.
PAULI_I, PAULI_X, PAULI_Y, PAULI_Z = 0, 1, 2, 3
_GATES = {PAULI_X: X_GATE, PAULI_Y: Y_GATE, PAULI_Z: Z_GATE}


class DepolarizingNoise:
    """Depolarizing channel: rho -> (1 - strength) * rho + strength * I/2.

    Simulated per qubit: with probability ``strength`` the qubit is hit by a
    Pauli chosen uniformly from {I, X, Y, Z}, which averages to the fully
    mixed state. Two of the four Paulis flip the bit in any given BB84 basis,
    so the sifted-key error rate from noise alone is strength / 2.

    Unlike Eve, the noise does not depend on anyone's basis choice and gives
    nobody any information about the key.
    """

    def __init__(self, rng: np.random.Generator, strength: float) -> None:
        self._rng = rng
        self.strength = strength
        self.paulis = np.empty(0, dtype=np.int8)  # which Pauli hit each qubit

    def apply(self, states: np.ndarray) -> np.ndarray:
        """Channel stage: apply random Pauli errors."""
        n = len(states)
        depolarized = self._rng.random(n) < self.strength
        self.paulis = np.where(depolarized, self._rng.integers(0, 4, n), PAULI_I).astype(np.int8)
        for pauli, gate in _GATES.items():
            states = apply_gate(states, gate, self.paulis == pauli)
        return states
