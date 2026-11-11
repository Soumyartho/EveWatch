"""QBER meter with the abort threshold marked."""

from __future__ import annotations

import math

import streamlit as st

from evewatch.models.qber import theoretical_qber
from evewatch.models.types import SimulationResult

SCALE_MAX = 0.5  # a QBER of 50% is pure randomness, so the scale ends there

# Status colours; each is always paired with a text label below the meter.
GOOD, WARNING, CRITICAL = "#0ca30c", "#fab219", "#d03b3b"


def render(result: SimulationResult) -> None:
    report = result.qber_report
    st.subheader("Quantum bit error rate")

    if report.n_sample == 0 or math.isnan(report.qber):
        st.info("No sifted bits were available to estimate the QBER.")
        return

    if report.qber > report.threshold:
        colour, state = CRITICAL, "above the abort threshold"
    elif report.qber > 0.7 * report.threshold:
        colour, state = WARNING, "close to the abort threshold"
    else:
        colour, state = GOOD, "below the abort threshold"

    fill = min(report.qber, SCALE_MAX) / SCALE_MAX * 100
    mark = min(report.threshold, SCALE_MAX) / SCALE_MAX * 100

    st.html(
        f"""
        <div role="img" aria-label="QBER {report.qber:.1%}, {state} of {report.threshold:.0%}"
             style="padding: 26px 0 4px 0;">
          <div style="position: relative; height: 14px; border-radius: 7px;
                      background: color-mix(in srgb, {colour} 22%, transparent);">
            <div style="width: {fill:.2f}%; height: 100%; border-radius: 7px;
                        background: {colour};"></div>
            <div style="position: absolute; left: {mark:.2f}%; top: -6px; width: 2px;
                        height: 26px; background: currentColor;"></div>
            <div style="position: absolute; left: {mark:.2f}%; top: -28px;
                        transform: translateX(-50%); font-size: 0.8rem; white-space: nowrap;
                        opacity: 0.75;">abort above {report.threshold:.0%}</div>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem;
                      opacity: 0.75; margin-top: 4px;">
            <span>0%</span><span>{SCALE_MAX:.0%}</span>
          </div>
        </div>
        """
    )

    expected = theoretical_qber(result.params.eve_probability, result.params.noise)
    st.markdown(
        f"**{report.qber:.1%}** measured, {state} "
        f"({report.n_errors:,} errors in {report.n_sample:,} sampled bits). "
        f"Theory predicts {expected:.1%} for these settings."
    )
