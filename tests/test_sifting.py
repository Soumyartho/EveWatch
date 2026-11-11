"""Sifting keeps only matching-basis positions (about half of them)."""

import numpy as np

from evewatch.controllers.simulation_controller import run_simulation
from evewatch.models.sifting import sift
from evewatch.models.types import SimulationParams, TransmissionRecord


def test_sift_keeps_exactly_the_matching_positions():
    record = TransmissionRecord(
        alice_bits=np.array([1, 0, 1, 1, 0]),
        alice_bases=np.array([0, 1, 1, 0, 1]),
        bob_bases=np.array([0, 0, 1, 1, 1]),
        bob_bits=np.array([1, 1, 1, 0, 0]),
    )
    sifted = sift(record)
    assert sifted.indices.tolist() == [0, 2, 4]
    assert sifted.alice_key.tolist() == [1, 1, 0]
    assert sifted.bob_key.tolist() == [1, 1, 0]


def test_about_half_the_qubits_survive_sifting():
    n = 10_000
    result = run_simulation(SimulationParams(n_qubits=n, seed=3))
    assert 0.47 < len(result.sifted) / n < 0.53
