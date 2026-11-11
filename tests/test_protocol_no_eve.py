"""Without Eve and noise, QBER == 0."""

import numpy as np
import pytest

from evewatch.controllers.simulation_controller import run_simulation
from evewatch.models.types import SimulationParams


@pytest.mark.parametrize("seed", range(10))
def test_ideal_channel_has_zero_qber(seed):
    result = run_simulation(SimulationParams(n_qubits=1000, seed=seed))
    report = result.qber_report
    assert report.n_sample > 0
    assert report.qber == 0.0
    assert not result.aborted
    # The whole sifted key agrees, not just the sampled part.
    assert np.array_equal(result.sifted.alice_key, result.sifted.bob_key)


def test_sampled_bits_are_removed_from_the_key():
    result = run_simulation(SimulationParams(n_qubits=1000, sample_fraction=0.25, seed=0))
    report = result.qber_report
    assert report.n_sample + len(report.alice_remaining) == len(result.sifted)
    assert np.array_equal(report.alice_remaining, report.bob_remaining)


def test_same_seed_reproduces_the_run():
    a = run_simulation(SimulationParams(n_qubits=200, seed=42))
    b = run_simulation(SimulationParams(n_qubits=200, seed=42))
    assert np.array_equal(a.transmission.alice_bits, b.transmission.alice_bits)
    assert np.array_equal(a.transmission.bob_bits, b.transmission.bob_bits)


def test_single_qubit_run_does_not_crash():
    for seed in range(20):
        result = run_simulation(SimulationParams(n_qubits=1, seed=seed))
        if len(result.sifted) == 0:
            assert result.aborted


def test_invalid_params_are_rejected():
    with pytest.raises(ValueError):
        SimulationParams(n_qubits=0)
    with pytest.raises(ValueError):
        SimulationParams(eve_probability=1.5)
