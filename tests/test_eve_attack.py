"""Intercept-resend attack: QBER is about 25% x p, and full interception is detected."""

import numpy as np
import pytest

from evewatch.controllers.simulation_controller import run_simulation
from evewatch.models.eve import NOT_INTERCEPTED
from evewatch.models.types import SimulationParams

N = 40_000


def sifted_error_rate(result) -> float:
    """Error rate over the whole sifted key (tighter statistics than the sample)."""
    return float(np.mean(result.sifted.alice_key != result.sifted.bob_key))


def test_full_interception_gives_about_25_percent_qber_and_aborts():
    result = run_simulation(SimulationParams(n_qubits=N, eve_probability=1.0, seed=0))
    assert 0.23 < result.qber_report.qber < 0.27
    assert 0.24 < sifted_error_rate(result) < 0.26
    assert result.aborted


@pytest.mark.parametrize("p", [0.2, 0.4, 0.6, 0.8])
def test_error_rate_scales_as_quarter_of_p(p):
    result = run_simulation(SimulationParams(n_qubits=N, eve_probability=p, seed=1))
    assert sifted_error_rate(result) == pytest.approx(0.25 * p, abs=0.012)


def test_eve_intercepts_about_a_fraction_p():
    result = run_simulation(SimulationParams(n_qubits=N, eve_probability=0.3, seed=2))
    assert result.transmission.eve_intercepted.mean() == pytest.approx(0.3, abs=0.01)


def test_errors_only_occur_where_eve_used_the_wrong_basis():
    result = run_simulation(SimulationParams(n_qubits=N, eve_probability=0.5, seed=3))
    t = result.transmission
    idx = result.sifted.indices
    errors = t.alice_bits[idx] != t.bob_bits[idx]
    wrong_basis = t.eve_intercepted[idx] & (t.eve_bases[idx] != t.alice_bases[idx])
    assert not np.any(errors & ~wrong_basis)
    # A wrong-basis interception flips Bob's bit half the time.
    assert errors[wrong_basis].mean() == pytest.approx(0.5, abs=0.03)


def test_eve_learns_the_bit_when_her_basis_matches():
    result = run_simulation(SimulationParams(n_qubits=N, eve_probability=1.0, seed=4))
    t = result.transmission
    right_basis = t.eve_bases == t.alice_bases
    assert np.array_equal(t.eve_bits[right_basis], t.alice_bits[right_basis])


def test_untouched_positions_are_marked():
    result = run_simulation(SimulationParams(n_qubits=1000, eve_probability=0.5, seed=5))
    t = result.transmission
    assert np.all(t.eve_bases[~t.eve_intercepted] == NOT_INTERCEPTED)
    assert np.all(t.eve_bits[~t.eve_intercepted] == NOT_INTERCEPTED)
    assert np.all(t.eve_bases[t.eve_intercepted] >= 0)


def test_no_eve_leaves_her_record_empty():
    result = run_simulation(SimulationParams(n_qubits=100, seed=6))
    assert result.transmission.eve_intercepted is None


def test_adding_eve_does_not_change_alices_choices():
    clean = run_simulation(SimulationParams(n_qubits=500, seed=7))
    tapped = run_simulation(SimulationParams(n_qubits=500, eve_probability=1.0, seed=7))
    assert np.array_equal(clean.transmission.alice_bits, tapped.transmission.alice_bits)
    assert np.array_equal(clean.transmission.alice_bases, tapped.transmission.alice_bases)
    assert np.array_equal(clean.transmission.bob_bases, tapped.transmission.bob_bases)
