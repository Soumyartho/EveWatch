"""Verdict banner: key safe / Eve detected / no key distilled."""

from __future__ import annotations

import streamlit as st

from evewatch.models.types import SimulationResult


def _ground_truth(result: SimulationResult) -> str:
    """What really happened on the channel (known only to the simulator)."""
    params, record = result.params, result.transmission
    if record.eve_intercepted is None:
        eve = "no eavesdropper was present"
    else:
        eve = f"Eve intercepted {int(record.eve_intercepted.sum()):,} of {params.n_qubits:,} qubits"
    noise = f"channel noise was {params.noise:.0%}" if params.noise > 0 else "the channel was noiseless"
    return f"What really happened: {eve}; {noise}."


def render(result: SimulationResult) -> None:
    report = result.qber_report
    eve_present = result.transmission.eve_intercepted is not None

    if result.status == "aborted":
        if report.n_sample == 0:
            st.error(
                "**Aborted.** No sifted bits were available for the error check.",
                icon=":material/block:",
            )
        else:
            st.error(
                f"**Eve detected - key discarded.** QBER of {report.qber:.1%} exceeds the "
                f"{report.threshold:.0%} abort threshold.",
                icon=":material/gpp_bad:",
            )
        if not eve_present and result.params.noise > 0:
            st.caption(
                _ground_truth(result)
                + " The errors came from noise alone, but Alice and Bob cannot tell noise from"
                " an eavesdropper using the QBER, so they must assume the worst."
            )
        else:
            st.caption(_ground_truth(result))

    elif result.status == "no_key":
        st.warning(
            f"**No key distilled.** QBER of {report.qber:.1%} passed the check, but error "
            "correction and privacy amplification used up every remaining bit.",
            icon=":material/warning:",
        )
        st.caption(_ground_truth(result))

    else:
        st.success(
            f"**Key safe.** QBER of {report.qber:.1%} is within the {report.threshold:.0%} "
            f"threshold; Alice and Bob share {len(result.final_key):,} secret bits.",
            icon=":material/verified_user:",
        )
        if eve_present:
            st.caption(
                _ground_truth(result)
                + " She stayed under the threshold; privacy amplification removes what she learned."
            )
        else:
            st.caption(_ground_truth(result))
