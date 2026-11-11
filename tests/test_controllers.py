"""Controller integration tests."""

import pytest

from evewatch.controllers import crypto_controller
from evewatch.controllers.simulation_controller import run_simulation
from evewatch.models.types import SimulationParams


@pytest.fixture(scope="module")
def session():
    return run_simulation(SimulationParams(n_qubits=4000, noise=0.03, seed=0))


def test_alice_encrypts_and_bob_decrypts_text(session):
    message = "Meet at the usual place at noon."
    blob = crypto_controller.encrypt_text(session, message)
    assert crypto_controller.decrypt_text(session, blob) == message


def test_file_round_trip(session, tmp_path):
    plain = tmp_path / "message.txt"
    encrypted = tmp_path / "message.enc"
    decrypted = tmp_path / "message.dec.txt"
    plain.write_text("BB84 secured file.\nSecond line.", encoding="utf-8")

    crypto_controller.encrypt_file(session, plain, encrypted)
    crypto_controller.decrypt_file(session, encrypted, decrypted)

    assert encrypted.read_bytes() != plain.read_bytes()
    assert decrypted.read_bytes() == plain.read_bytes()


def test_encryption_is_refused_after_an_abort():
    aborted = run_simulation(SimulationParams(n_qubits=2000, eve_probability=1.0, seed=1))
    with pytest.raises(ValueError):
        crypto_controller.encrypt_text(aborted, "hello")
