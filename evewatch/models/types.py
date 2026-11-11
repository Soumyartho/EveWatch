"""Dataclasses shared across layers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from evewatch import config


@dataclass(frozen=True)
class SimulationParams:
    """Inputs for one BB84 session."""

    n_qubits: int = config.DEFAULT_N_QUBITS
    eve_probability: float = 0.0
    noise: float = 0.0
    sample_fraction: float = config.DEFAULT_SAMPLE_FRACTION
    qber_threshold: float = config.QBER_THRESHOLD
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise ValueError("n_qubits must be at least 1")
        for name in ("eve_probability", "noise", "qber_threshold"):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0.0 < self.sample_fraction < 1.0:
            raise ValueError("sample_fraction must be strictly between 0 and 1")


@dataclass(frozen=True)
class TransmissionRecord:
    """Everything that happened on the quantum channel, one entry per qubit."""

    alice_bits: np.ndarray
    alice_bases: np.ndarray
    bob_bases: np.ndarray
    bob_bits: np.ndarray
    # Eve's view, None when no eavesdropper was present. Her bases and bits
    # hold -1 at positions she did not intercept.
    eve_intercepted: np.ndarray | None = None
    eve_bases: np.ndarray | None = None
    eve_bits: np.ndarray | None = None


@dataclass(frozen=True)
class SiftedKey:
    """Positions where Alice's and Bob's bases matched."""

    indices: np.ndarray  # positions in the original transmission
    alice_key: np.ndarray
    bob_key: np.ndarray

    def __len__(self) -> int:
        return len(self.indices)


@dataclass(frozen=True)
class QberReport:
    """Result of the public error check on a sacrificed sample of the sifted key."""

    sample_positions: np.ndarray  # positions within the sifted key that were revealed
    n_sample: int
    n_errors: int
    qber: float  # nan when there was nothing to sample
    threshold: float
    abort: bool
    alice_remaining: np.ndarray  # sifted key with the revealed sample removed
    bob_remaining: np.ndarray


@dataclass(frozen=True)
class ReconciliationResult:
    """Outcome of parity-based error correction."""

    bob_corrected: np.ndarray
    n_corrected: int  # bits Bob flipped
    leaked_bits: int  # parity bits announced publicly
    n_passes: int
    verified: bool  # hash comparison says both keys are now equal


@dataclass(frozen=True)
class FinalKey:
    """Secret key after privacy amplification, as held by each party."""

    alice_bits: np.ndarray
    bob_bits: np.ndarray

    def __len__(self) -> int:
        return len(self.alice_bits)

    @property
    def matches(self) -> bool:
        return bool(np.array_equal(self.alice_bits, self.bob_bits))

    def hex(self) -> str:
        """Alice's key as hex (zero-padded to a whole number of bytes)."""
        return np.packbits(self.alice_bits).tobytes().hex()


@dataclass(frozen=True)
class SimulationResult:
    """Full outcome of one BB84 session."""

    params: SimulationParams
    transmission: TransmissionRecord
    sifted: SiftedKey
    qber_report: QberReport
    # Both None when the session aborted; final_key is also None when
    # reconciliation could not make the keys equal.
    reconciliation: ReconciliationResult | None = None
    final_key: FinalKey | None = None

    @property
    def status(self) -> str:
        """'aborted' (QBER check failed), 'no_key' (passed, but nothing left) or 'secure'."""
        if self.qber_report.abort:
            return "aborted"
        if self.final_key is None or len(self.final_key) == 0:
            return "no_key"
        return "secure"

    @property
    def aborted(self) -> bool:
        return self.qber_report.abort
