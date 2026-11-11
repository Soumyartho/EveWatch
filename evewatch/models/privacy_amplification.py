"""Privacy amplification: hash the reconciled key down to a shorter secret key.

Eve may know part of the reconciled key: what she gained on the quantum
channel (bounded through the QBER) plus every parity bit announced during
error correction. Hashing with a randomly chosen 2-universal function
(a Toeplitz matrix) to a suitably shorter length leaves her with almost no
information about the result.
"""

from __future__ import annotations

import math

import numpy as np

from evewatch import config
from evewatch.models.types import FinalKey


def binary_entropy(p: float) -> float:
    """h(p) = -p log2 p - (1-p) log2 (1-p)."""
    p = min(max(p, 0.0), 1.0)
    if p in (0.0, 1.0):
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def secure_key_length(
    n: int, qber: float, leaked_bits: int, security_bits: int = config.PA_SECURITY_BITS
) -> int:
    """Final key length: n * (1 - h(QBER)) - leaked parity bits - safety margin.

    This is the asymptotic BB84 bound; finite-size corrections are ignored.
    """
    q = min(max(qber, 0.0), 0.5)
    return max(0, math.floor(n * (1 - binary_entropy(q))) - leaked_bits - security_bits)


def toeplitz_hash(bits: np.ndarray, out_len: int, seed_bits: np.ndarray) -> np.ndarray:
    """Multiply ``bits`` by an out_len x n Toeplitz matrix over GF(2).

    The matrix is defined by ``seed_bits`` (length n + out_len - 1), with
    entry (i, j) = seed_bits[i - j + n - 1]. That product is a slice of the
    convolution of the seed with the input.
    """
    n = len(bits)
    if out_len == 0 or n == 0:
        return np.zeros(0, dtype=np.uint8)
    if len(seed_bits) != n + out_len - 1:
        raise ValueError("seed_bits must have length n + out_len - 1")
    conv = np.convolve(seed_bits.astype(np.int64), np.asarray(bits, dtype=np.int64))
    return (conv[n - 1 : n - 1 + out_len] & 1).astype(np.uint8)


def amplify(
    alice_key: np.ndarray,
    bob_key: np.ndarray,
    qber: float,
    leaked_bits: int,
    rng: np.random.Generator,
    security_bits: int = config.PA_SECURITY_BITS,
) -> FinalKey:
    """Hash both parties' keys with the same public random Toeplitz matrix."""
    n = len(alice_key)
    out_len = secure_key_length(n, qber, leaked_bits, security_bits)
    seed_bits = rng.integers(0, 2, max(0, n + out_len - 1), dtype=np.uint8)
    return FinalKey(
        alice_bits=toeplitz_hash(alice_key, out_len, seed_bits),
        bob_bits=toeplitz_hash(bob_key, out_len, seed_bits),
    )
