"""Per-qubit table for Alice, Eve and Bob, and the key pipeline chart."""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from evewatch.models.types import SimulationResult

BASIS_NAMES = np.array(["Z", "X"])
NOT_SEEN = "-"


def build_transmission_table(result: SimulationResult) -> pd.DataFrame:
    """One row per qubit: what each party chose and measured, and what became of the bit."""
    record, sifted, report = result.transmission, result.sifted, result.qber_report
    n = len(record.alice_bits)

    used_for = np.full(n, "discarded (bases differ)", dtype=object)
    used_for[sifted.indices] = "key"
    used_for[sifted.indices[report.sample_positions]] = "QBER sample (revealed)"

    match = record.alice_bases == record.bob_bases
    error = match & (record.alice_bits != record.bob_bits)

    table = pd.DataFrame(
        {
            "Alice bit": record.alice_bits,
            "Alice basis": BASIS_NAMES[record.alice_bases],
        }
    )
    if record.eve_intercepted is not None:
        hit = record.eve_intercepted
        table["Eve basis"] = np.where(hit, BASIS_NAMES[np.maximum(record.eve_bases, 0)], NOT_SEEN)
        table["Eve bit"] = np.where(hit, record.eve_bits.astype(str), NOT_SEEN)
    table["Bob basis"] = BASIS_NAMES[record.bob_bases]
    table["Bob bit"] = record.bob_bits
    table["Bases match"] = match
    table["Bit error"] = error
    table["Used for"] = used_for
    table.index.name = "Qubit"
    return table


def render_transmission(result: SimulationResult) -> None:
    table = build_transmission_table(result)
    choice = st.radio(
        "Show",
        ["All qubits", "Sifted key only", "Errors only"],
        horizontal=True,
    )
    if choice == "Sifted key only":
        table = table[table["Bases match"]]
    elif choice == "Errors only":
        table = table[table["Bit error"]]

    st.caption(
        f"{len(table):,} rows. Z is the computational basis, X the Hadamard basis. "
        "A bit error is a sifted position where Bob's bit differs from Alice's."
    )
    st.dataframe(table, width="stretch", height=420)


def _bar_colour() -> str:
    theme = getattr(st.context, "theme", None)
    return "#3987e5" if getattr(theme, "type", "light") == "dark" else "#2a78d6"


def render_pipeline(result: SimulationResult) -> None:
    """How many bits survive each stage, from qubits sent to final key."""
    report, rec = result.qber_report, result.reconciliation
    final_len = len(result.final_key) if result.final_key is not None else 0

    stages = pd.DataFrame(
        {
            "Stage": ["Qubits sent", "After sifting", "After QBER sample", "Final secret key"],
            "Bits": [
                result.params.n_qubits,
                len(result.sifted),
                len(report.alice_remaining),
                final_len,
            ],
        }
    )

    base = alt.Chart(stages).encode(
        y=alt.Y("Stage:N", sort=None, title=None, axis=alt.Axis(labelLimit=200)),
        x=alt.X("Bits:Q", title="Bits", axis=alt.Axis(grid=True, tickMinStep=1)),
        tooltip=["Stage", alt.Tooltip("Bits:Q", format=",")],
    )
    bars = base.mark_bar(size=20, cornerRadiusEnd=4, color=_bar_colour())
    labels = base.mark_text(align="left", dx=6).encode(text=alt.Text("Bits:Q", format=","))
    st.altair_chart((bars + labels).properties(height=200), width="stretch")

    if rec is None:
        st.caption("The session aborted at the QBER check, so no key finishing was run.")
        return

    cols = st.columns(3)
    cols[0].metric("Errors corrected", f"{rec.n_corrected:,}", border=True)
    cols[1].metric(
        "Parity bits leaked",
        f"{rec.leaked_bits:,}",
        border=True,
        help="Announced publicly during error correction; removed again by privacy amplification.",
    )
    cols[2].metric("Correction passes", f"{rec.n_passes:,}", border=True)
    if not rec.verified:
        st.warning("Error correction could not make the two keys equal, so no key was produced.")
