"""Error correction, privacy amplification and AES-GCM round trip."""

import numpy as np
import pytest
from cryptography.exceptions import InvalidTag

from evewatch import config
from evewatch.controllers.simulation_controller import run_simulation
from evewatch.models import crypto
from evewatch.models.error_correction import reconcile
from evewatch.models.privacy_amplification import (
    amplify,
    binary_entropy,
    secure_key_length,
    toeplitz_hash,
)
from evewatch.models.types import SimulationParams


def noisy_pair(n, error_rate, seed):
    rng = np.random.default_rng(seed)
    alice = rng.integers(0, 2, n, dtype=np.uint8)
    flips = (rng.random(n) < error_rate).astype(np.uint8)
    return alice, alice ^ flips, int(flips.sum()), rng


# ---------------- error correction ----------------


@pytest.mark.parametrize("error_rate", [0.01, 0.03, 0.06, 0.10])
@pytest.mark.parametrize("seed", range(5))
def test_reconcile_fixes_all_errors(error_rate, seed):
    alice, bob, n_errors, rng = noisy_pair(2000, error_rate, seed)
    result = reconcile(alice, bob, error_rate, rng)
    assert result.verified
    assert np.array_equal(result.bob_corrected, alice)
    assert result.n_corrected == n_errors
    assert 0 < result.leaked_bits < len(alice)


def test_reconcile_still_works_when_the_qber_estimate_was_zero():
    alice, bob, n_errors, rng = noisy_pair(2000, 0.02, 11)
    assert n_errors > 0
    result = reconcile(alice, bob, 0.0, rng)
    assert result.verified


def test_reconcile_on_identical_keys_leaks_little_and_changes_nothing():
    alice, bob, _, rng = noisy_pair(1000, 0.0, 0)
    result = reconcile(alice, bob, 0.0, rng)
    assert result.verified
    assert result.n_corrected == 0
    assert result.leaked_bits < 40


def test_reconcile_does_not_modify_its_inputs():
    alice, bob, _, rng = noisy_pair(500, 0.05, 1)
    bob_before = bob.copy()
    reconcile(alice, bob, 0.05, rng)
    assert np.array_equal(bob, bob_before)


@pytest.mark.parametrize("n", [0, 1, 2, 3])
def test_reconcile_handles_tiny_keys(n):
    rng = np.random.default_rng(n)
    alice = rng.integers(0, 2, n, dtype=np.uint8)
    result = reconcile(alice, alice ^ 1, 0.5, rng)
    assert result.verified


# ---------------- privacy amplification ----------------


def test_binary_entropy_known_values():
    assert binary_entropy(0) == 0
    assert binary_entropy(0.5) == 1
    assert binary_entropy(0.11) == pytest.approx(0.4999, abs=1e-3)


def test_secure_key_length_formula():
    assert secure_key_length(1000, 0.0, 0, security_bits=0) == 1000
    assert secure_key_length(1000, 0.0, 100, security_bits=32) == 868
    assert secure_key_length(1000, 0.11, 0, security_bits=0) == pytest.approx(500, abs=1)
    assert secure_key_length(100, 0.11, 200, security_bits=32) == 0


def test_toeplitz_hash_matches_the_explicit_matrix():
    rng = np.random.default_rng(0)
    n, m = 40, 17
    x = rng.integers(0, 2, n, dtype=np.uint8)
    seed = rng.integers(0, 2, n + m - 1, dtype=np.uint8)
    matrix = np.array([[seed[i - j + n - 1] for j in range(n)] for i in range(m)])
    assert np.array_equal(toeplitz_hash(x, m, seed), (matrix @ x) % 2)


def test_toeplitz_hash_is_linear():
    rng = np.random.default_rng(1)
    n, m = 300, 120
    x, y = rng.integers(0, 2, (2, n), dtype=np.uint8)
    seed = rng.integers(0, 2, n + m - 1, dtype=np.uint8)
    assert np.array_equal(
        toeplitz_hash(x ^ y, m, seed), toeplitz_hash(x, m, seed) ^ toeplitz_hash(y, m, seed)
    )


def test_amplify_gives_matching_shorter_keys():
    rng = np.random.default_rng(2)
    key = rng.integers(0, 2, 1000, dtype=np.uint8)
    final = amplify(key, key.copy(), qber=0.03, leaked_bits=250, rng=rng)
    assert final.matches
    assert len(final) == secure_key_length(1000, 0.03, 250)
    assert 0.4 < final.alice_bits.mean() < 0.6


def test_one_differing_input_bit_gives_different_final_keys():
    rng = np.random.default_rng(3)
    key = rng.integers(0, 2, 1000, dtype=np.uint8)
    other = key.copy()
    other[500] ^= 1
    assert not amplify(key, other, 0.0, 0, rng).matches


# ---------------- AES-GCM ----------------


def test_aes_round_trip():
    key = np.random.default_rng(4).integers(0, 2, 256, dtype=np.uint8)
    message = "Quantum keys, classical message. ✔".encode("utf-8")
    blob = crypto.encrypt(message, key)
    assert message not in blob
    assert crypto.decrypt(blob, key) == message


def test_aes_wrong_key_is_rejected():
    key = np.random.default_rng(5).integers(0, 2, 256, dtype=np.uint8)
    wrong = key.copy()
    wrong[0] ^= 1
    with pytest.raises(InvalidTag):
        crypto.decrypt(crypto.encrypt(b"secret", key), wrong)


def test_aes_tampered_ciphertext_is_rejected():
    key = np.random.default_rng(6).integers(0, 2, 256, dtype=np.uint8)
    blob = bytearray(crypto.encrypt(b"secret", key))
    blob[-1] ^= 1
    with pytest.raises(InvalidTag):
        crypto.decrypt(bytes(blob), key)


def test_short_qkd_key_is_refused():
    with pytest.raises(ValueError):
        crypto.derive_aes_key(np.ones(config.MIN_AES_KEY_BITS - 1, dtype=np.uint8))


# ---------------- full pipeline ----------------


@pytest.mark.parametrize(
    "eve, noise", [(0.0, 0.0), (0.0, 0.08), (0.2, 0.0), (0.2, 0.05)]
)
def test_pipeline_ends_with_identical_secret_keys(eve, noise):
    result = run_simulation(SimulationParams(n_qubits=8000, eve_probability=eve, noise=noise, seed=0))
    assert not result.aborted
    assert result.reconciliation.verified
    assert result.final_key.matches
    assert config.MIN_AES_KEY_BITS <= len(result.final_key) < len(result.qber_report.alice_remaining)


def test_more_errors_mean_a_shorter_final_key():
    clean = run_simulation(SimulationParams(n_qubits=8000, seed=1))
    noisy = run_simulation(SimulationParams(n_qubits=8000, noise=0.1, seed=1))
    assert len(noisy.final_key) < len(clean.final_key) / 2


def test_default_parameters_yield_an_aes_capable_key():
    for seed in range(10):
        result = run_simulation(SimulationParams(seed=seed))
        assert len(result.final_key) >= config.MIN_AES_KEY_BITS


def test_aborted_session_produces_no_key():
    result = run_simulation(SimulationParams(n_qubits=4000, eve_probability=1.0, seed=2))
    assert result.aborted
    assert result.reconciliation is None
    assert result.final_key is None
