"""AES-GCM encrypt/decrypt using the final QKD key."""

from __future__ import annotations

import os

import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from evewatch import config

NONCE_BYTES = 12


def derive_aes_key(key_bits: np.ndarray, min_bits: int = config.MIN_AES_KEY_BITS) -> bytes:
    """Turn the QKD key bits into a 256-bit AES key with HKDF-SHA256.

    The AES key is only as strong as the QKD key it came from, so keys with
    fewer than ``min_bits`` bits are rejected.
    """
    n = len(key_bits)
    if n < min_bits:
        raise ValueError(f"QKD key has {n} bits; at least {min_bits} are needed for AES")
    material = n.to_bytes(4, "big") + np.packbits(np.asarray(key_bits, dtype=np.uint8)).tobytes()
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"evewatch-bb84-aes-gcm")
    return hkdf.derive(material)


def encrypt(plaintext: bytes, key_bits: np.ndarray, min_bits: int = config.MIN_AES_KEY_BITS) -> bytes:
    """Return nonce || ciphertext+tag."""
    nonce = os.urandom(NONCE_BYTES)
    return nonce + AESGCM(derive_aes_key(key_bits, min_bits)).encrypt(nonce, plaintext, None)


def decrypt(blob: bytes, key_bits: np.ndarray, min_bits: int = config.MIN_AES_KEY_BITS) -> bytes:
    """Inverse of ``encrypt``. Raises cryptography.exceptions.InvalidTag on a wrong key."""
    nonce, ciphertext = blob[:NONCE_BYTES], blob[NONCE_BYTES:]
    return AESGCM(derive_aes_key(key_bits, min_bits)).decrypt(nonce, ciphertext, None)
