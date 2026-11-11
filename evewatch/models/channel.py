"""Quantum channel between Alice and Bob.

Stages are applied in order to the qubits in flight. The Eve module and the
depolarizing noise model plug in here as stages; with no stages the channel is ideal.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

Stage = Callable[[np.ndarray], np.ndarray]


class QuantumChannel:
    def __init__(self, stages: Sequence[Stage] = ()) -> None:
        self._stages = tuple(stages)

    def transmit(self, states: np.ndarray) -> np.ndarray:
        for stage in self._stages:
            states = stage(states)
        return states
