"""Sidebar controls. Returns the SimulationParams the user selected."""

from __future__ import annotations

import numpy as np
import streamlit as st

from evewatch import config
from evewatch.models.types import SimulationParams

MAX_SEED = 999_999


def _new_seed() -> None:
    st.session_state.seed = int(np.random.default_rng().integers(0, MAX_SEED + 1))


def render() -> SimulationParams:
    st.session_state.setdefault("seed", 42)

    with st.sidebar:
        st.header("Simulation controls")

        n_qubits = st.slider(
            "Number of qubits",
            min_value=64,
            max_value=8192,
            value=config.DEFAULT_N_QUBITS,
            step=64,
            help="How many qubits Alice sends. About half survive sifting.",
        )
        eve_probability = st.slider(
            "Eve interception probability",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            help="Chance that Eve measures and resends each qubit. Expected QBER is 25% of this.",
        )
        noise = st.slider(
            "Channel noise",
            min_value=0.0,
            max_value=0.5,
            value=0.0,
            step=0.01,
            help="Depolarizing strength of the channel. Expected QBER is half of this.",
        )

        with st.expander("Advanced"):
            sample_fraction = st.slider(
                "Fraction of sifted key sacrificed for the QBER check",
                min_value=0.1,
                max_value=0.9,
                value=config.DEFAULT_SAMPLE_FRACTION,
                step=0.05,
            )
            qber_threshold = st.slider(
                "Abort threshold (QBER)",
                min_value=0.01,
                max_value=0.25,
                value=config.QBER_THRESHOLD,
                step=0.01,
            )
            st.number_input(
                "Random seed",
                min_value=0,
                max_value=MAX_SEED,
                step=1,
                key="seed",
                help="The same seed and settings always reproduce the same run.",
            )

        st.button("New random run", on_click=_new_seed, type="primary", width="stretch")

    return SimulationParams(
        n_qubits=n_qubits,
        eve_probability=eve_probability,
        noise=noise,
        sample_fraction=sample_fraction,
        qber_threshold=qber_threshold,
        seed=int(st.session_state.seed),
    )
