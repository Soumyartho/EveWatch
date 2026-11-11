"""Use a finished BB84 key for AES-GCM: Alice encrypts, Bob decrypts."""

from __future__ import annotations

from pathlib import Path

from evewatch.models import crypto
from evewatch.models.types import FinalKey, SimulationResult


def _final_key(result: SimulationResult) -> FinalKey:
    if result.final_key is None:
        raise ValueError("This session produced no key (aborted or reconciliation failed)")
    return result.final_key


def encrypt_bytes(result: SimulationResult, data: bytes) -> bytes:
    """Alice encrypts with her copy of the key."""
    return crypto.encrypt(data, _final_key(result).alice_bits)


def decrypt_bytes(result: SimulationResult, blob: bytes) -> bytes:
    """Bob decrypts with his copy of the key."""
    return crypto.decrypt(blob, _final_key(result).bob_bits)


def encrypt_text(result: SimulationResult, text: str) -> bytes:
    """Alice encrypts with her copy of the key."""
    return crypto.encrypt(text.encode("utf-8"), _final_key(result).alice_bits)


def decrypt_text(result: SimulationResult, blob: bytes) -> str:
    """Bob decrypts with his copy of the key."""
    return crypto.decrypt(blob, _final_key(result).bob_bits).decode("utf-8")


def encrypt_file(result: SimulationResult, source: str | Path, destination: str | Path) -> None:
    data = Path(source).read_bytes()
    Path(destination).write_bytes(crypto.encrypt(data, _final_key(result).alice_bits))


def decrypt_file(result: SimulationResult, source: str | Path, destination: str | Path) -> None:
    blob = Path(source).read_bytes()
    Path(destination).write_bytes(crypto.decrypt(blob, _final_key(result).bob_bits))
