"""Parity-based error correction (a simplified Cascade) for the sifted key.

Alice and Bob shuffle the key with a public permutation, cut it into blocks
and compare block parities over the public channel. A parity mismatch means
the block holds an odd number of errors; a binary search (one more parity per
step) finds one of them and Bob flips it. Every parity announced is one bit
leaked to Eve, which privacy amplification must remove afterwards.

Simplification versus full Cascade: there is no back-tracking into earlier
passes. Instead, extra cheap two-block passes run until several in a row come
back clean, and a final hash comparison confirms that the keys are equal.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

from evewatch.models.types import ReconciliationResult

DOUBLING_PASSES = 4  # passes with block size k, 2k, 4k, 8k
CLEAN_PASSES_REQUIRED = 8  # consecutive clean two-block passes before stopping
MAX_PASSES = 200


def _parity(key: np.ndarray, idx: np.ndarray) -> int:
    return int(key[idx].sum() & 1)


def _locate_error(alice: np.ndarray, bob: np.ndarray, idx: np.ndarray) -> tuple[int, int]:
    """Binary search for one error in a block with mismatching parity.

    Returns the position of the error and the number of parity bits revealed.
    """
    leaked = 0
    while len(idx) > 1:
        half = idx[: len(idx) // 2]
        leaked += 1
        if _parity(alice, half) != _parity(bob, half):
            idx = half
        else:
            idx = idx[len(idx) // 2 :]
    return int(idx[0]), leaked


def _run_pass(
    alice: np.ndarray, bob: np.ndarray, block_size: int, rng: np.random.Generator
) -> tuple[int, int]:
    """One pass over a fresh public shuffle. Returns (errors fixed, bits leaked)."""
    perm = rng.permutation(len(alice))
    fixed = leaked = 0
    for start in range(0, len(perm), block_size):
        idx = perm[start : start + block_size]
        leaked += 1
        if _parity(alice, idx) != _parity(bob, idx):
            pos, search_leak = _locate_error(alice, bob, idx)
            bob[pos] ^= 1
            fixed += 1
            leaked += search_leak
    return fixed, leaked


def _digest(key: np.ndarray) -> bytes:
    return hashlib.sha256(np.asarray(key, dtype=np.uint8).tobytes()).digest()


def reconcile(
    alice_key: np.ndarray,
    bob_key: np.ndarray,
    qber: float,
    rng: np.random.Generator,
) -> ReconciliationResult:
    """Correct Bob's key towards Alice's using public parity comparisons.

    ``qber`` is the estimate from the sampling step; it only sets the initial
    block size. ``rng`` drives the public shuffles (both parties share it).
    """
    alice = np.asarray(alice_key, dtype=np.uint8)
    bob = np.array(bob_key, dtype=np.uint8)
    n = len(alice)
    fixed = leaked = passes = 0

    if n > 0:
        half = max(1, math.ceil(n / 2))
        # About 0.73 / QBER gives roughly one error per block on the first pass.
        block = half if not qber > 0 else max(1, min(half, math.ceil(0.73 / qber)))

        for _ in range(DOUBLING_PASSES):
            f, l = _run_pass(alice, bob, block, rng)
            fixed, leaked, passes = fixed + f, leaked + l, passes + 1
            block = min(half, block * 2)

        clean_streak = 0
        while clean_streak < CLEAN_PASSES_REQUIRED and passes < MAX_PASSES:
            f, l = _run_pass(alice, bob, half, rng)
            fixed, leaked, passes = fixed + f, leaked + l, passes + 1
            clean_streak = 0 if f else clean_streak + 1

    return ReconciliationResult(
        bob_corrected=bob,
        n_corrected=fixed,
        leaked_bits=leaked,
        n_passes=passes,
        verified=_digest(alice) == _digest(bob),
    )
