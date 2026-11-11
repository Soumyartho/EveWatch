"""Depolarizing noise raises QBER predictably (strength / 2)."""

import numpy as np
import pytest

from evewatch.controllers.simulation_controller import run_simulation
from evewatch.models import quantum
from evewatch.models.noise import PAULI_I, DepolarizingNoise
from evewatch.models.types import SimulationParams

N = 40_000


def sifted_error_rate(result) -> float:
    return float(np.mean(result.sifted.alice_key != result.sifted.bob_key))


@pytest.mark.parametrize("strength", [0.05, 0.1, 0.2, 0.5, 1.0])
def test_noise_only_error_rate_is_half_the_strength(strength):
    result = run_simulation(SimulationParams(n_qubits=N, noise=strength, seed=0))
    assert sifted_error_rate(result) == pytest.approx(strength / 2, abs=0.012)


def test_small_noise_does_not_trigger_an_abort():
    result = run_simulation(SimulationParams(n_qubits=N, noise=0.05, seed=1))
    assert 0 < result.qber_report.qber < 0.05
    assert not result.aborted


def test_heavy_noise_aborts_even_without_eve():
    result = run_simulation(SimulationParams(n_qubits=N, noise=0.4, seed=2))
    assert result.transmission.eve_intercepted is None
    assert result.aborted


@pytest.mark.parametrize("p, strength", [(0.5, 0.1), (1.0, 0.2), (0.3, 0.3)])
def test_eve_and_noise_combine_as_independent_error_sources(p, strength):
    result = run_simulation(SimulationParams(n_qubits=N, eve_probability=p, noise=strength, seed=3))
    a, b = 0.25 * p, strength / 2
    expected = a * (1 - b) + b * (1 - a)
    assert sifted_error_rate(result) == pytest.approx(expected, abs=0.012)


def test_noise_errors_do_not_depend_on_the_basis():
    result = run_simulation(SimulationParams(n_qubits=N, noise=0.3, seed=4))
    t = result.transmission
    idx = result.sifted.indices
    errors = t.alice_bits[idx] != t.bob_bits[idx]
    in_x = t.alice_bases[idx] == quantum.X_BASIS
    assert errors[in_x].mean() == pytest.approx(errors[~in_x].mean(), abs=0.02)


def test_zero_strength_leaves_states_untouched():
    rng = np.random.default_rng(5)
    states = quantum.prepare_qubits(rng.integers(0, 2, 200), rng.integers(0, 2, 200))
    noise = DepolarizingNoise(rng, 0.0)
    assert np.array_equal(noise.apply(states), states)
    assert np.all(noise.paulis == PAULI_I)


def test_noise_keeps_states_normalised():
    rng = np.random.default_rng(6)
    states = quantum.prepare_qubits(rng.integers(0, 2, 500), rng.integers(0, 2, 500))
    out = DepolarizingNoise(rng, 1.0).apply(states)
    assert np.allclose(np.sum(np.abs(out) ** 2, axis=1), 1.0)


def test_adding_noise_does_not_change_alices_or_eves_choices():
    quiet = run_simulation(SimulationParams(n_qubits=500, eve_probability=0.5, seed=7))
    noisy = run_simulation(SimulationParams(n_qubits=500, eve_probability=0.5, noise=0.2, seed=7))
    assert np.array_equal(quiet.transmission.alice_bits, noisy.transmission.alice_bits)
    assert np.array_equal(quiet.transmission.eve_bases, noisy.transmission.eve_bases)
