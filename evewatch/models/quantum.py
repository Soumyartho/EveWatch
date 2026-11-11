"""Quantum backend: single-qubit statevector simulation in NumPy.

A batch of N qubits is an array of shape (N, 2) holding the complex amplitudes
of |0> and |1>. BB84 never entangles qubits, so each one is simulated on its own.
"""

from __future__ import annotations

import numpy as np

Z_BASIS = 0  # computational basis  {|0>, |1>}
X_BASIS = 1  # Hadamard basis       {|+>, |->}

X_GATE = np.array([[0, 1], [1, 0]], dtype=complex)
H_GATE = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def apply_gate(states: np.ndarray, gate: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    """Apply a 2x2 gate to the qubits selected by ``mask`` (all qubits if None)."""
    out = states.copy()
    if mask is None:
        mask = np.ones(len(states), dtype=bool)
    out[mask] = states[mask] @ gate.T
    return out


def prepare_qubits(bits: np.ndarray, bases: np.ndarray) -> np.ndarray:
    """Encode bits as BB84 states: start in |0>, X gate for bit 1, H gate for the X basis."""
    bits = np.asarray(bits)
    bases = np.asarray(bases)
    states = np.zeros((len(bits), 2), dtype=complex)
    states[:, 0] = 1.0
    states = apply_gate(states, X_GATE, bits == 1)
    states = apply_gate(states, H_GATE, bases == X_BASIS)
    return states


def measure_qubits(
    states: np.ndarray, bases: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Measure each qubit in its given basis (Born rule).

    Returns the measured bits and the collapsed post-measurement states. The
    collapse is what makes an eavesdropper detectable: measuring in the wrong
    basis destroys the original state.
    """
    bases = np.asarray(bases)
    # Measuring in X is the same as applying H and then measuring in Z.
    rotated = apply_gate(states, H_GATE, bases == X_BASIS)
    p_one = np.abs(rotated[:, 1]) ** 2 / np.sum(np.abs(rotated) ** 2, axis=1)
    p_one = np.round(p_one, 12)  # keep deterministic outcomes exactly deterministic
    bits = (rng.random(len(states)) < p_one).astype(np.uint8)
    return bits, prepare_qubits(bits, bases)
