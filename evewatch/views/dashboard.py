"""Main dashboard page: composes sidebar, verdict, QBER meter, tables and key panel."""

from __future__ import annotations

import math

import streamlit as st

from evewatch.controllers.simulation_controller import run_simulation
from evewatch.models.types import SimulationParams, SimulationResult
from evewatch.views import gauge, key_panel, sidebar, tables, verdict


def _result_for(params: SimulationParams) -> SimulationResult:
    """Re-run only when the settings change, so typing a message keeps the same key."""
    if st.session_state.get("params") != params:
        st.session_state.params = params
        st.session_state.result = run_simulation(params)
    return st.session_state.result


def _summary(result: SimulationResult) -> None:
    report = result.qber_report
    final_len = len(result.final_key) if result.final_key is not None else 0
    qber = "n/a" if math.isnan(report.qber) else f"{report.qber:.1%}"

    cols = st.columns(4)
    cols[0].metric("Qubits sent", f"{result.params.n_qubits:,}", border=True)
    cols[1].metric("Sifted key bits", f"{len(result.sifted):,}", border=True)
    cols[2].metric("QBER", qber, border=True)
    cols[3].metric("Final key bits", f"{final_len:,}", border=True)


def render() -> None:
    st.title("EveWatch")
    st.caption(
        "BB84 quantum key distribution: Alice and Bob build a shared key, and an "
        "eavesdropper gives herself away by disturbing the qubits she measures."
    )

    params = sidebar.render()
    result = _result_for(params)

    verdict.render(result)
    _summary(result)
    gauge.render(result)

    transmission_tab, pipeline_tab, key_tab = st.tabs(
        ["Bits and bases", "Key pipeline", "Final key and encryption"]
    )
    with transmission_tab:
        tables.render_transmission(result)
    with pipeline_tab:
        tables.render_pipeline(result)
    with key_tab:
        key_panel.render(result)
