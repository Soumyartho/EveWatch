"""Statevector backend: encoding and measurement."""

import numpy as np
import pytest

from evewatch.models import quantum
from evewatch.models.quantum import X_BASIS, Z_BASIS

S = 1 / np.sqrt(2)


@pytest.mark.parametrize(
    "bit, basis, expected",
    [
        (0, Z_BASIS, [1, 0]),
        (1, Z_BASIS, [0, 1]),
        (0, X_BASIS, [S, S]),
        (1, X_BASIS, [S, -S]),
    ],
)
def test_prepare_gives_the_four_bb84_states(bit, basis, expected):
    state = quantum.prepare_qubits(np.array([bit]), np.array([basis]))[0]
    assert np.allclose(state, expected)


def test_same_basis_measurement_is_deterministic():
    rng = np.random.default_rng(0)
    bits = rng.integers(0, 2, 2000)
    bases = rng.integers(0, 2, 2000)
    measured, post = quantum.measure_qubits(quantum.prepare_qubits(bits, bases), bases, rng)
    assert np.array_equal(measured, bits)
    assert np.allclose(post, quantum.prepare_qubits(bits, bases))


def test_wrong_basis_measurement_is_a_coin_flip():
    rng = np.random.default_rng(1)
    n = 20_000
    bits = np.zeros(n, dtype=int)
    states = quantum.prepare_qubits(bits, np.full(n, Z_BASIS))
    measured, _ = quantum.measure_qubits(states, np.full(n, X_BASIS), rng)
    assert 0.48 < measured.mean() < 0.52


def test_measurement_collapses_the_state():
    rng = np.random.default_rng(2)
    n = 500
    states = quantum.prepare_qubits(np.zeros(n, dtype=int), np.full(n, Z_BASIS))
    x_bases = np.full(n, X_BASIS)
    first, post = quantum.measure_qubits(states, x_bases, rng)
    second, _ = quantum.measure_qubits(post, x_bases, rng)
    assert np.array_equal(first, second)
