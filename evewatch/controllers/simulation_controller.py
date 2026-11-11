"""Runs one full BB84 session from SimulationParams."""

from __future__ import annotations

from evewatch.models.alice import Alice
from evewatch.models.bob import Bob
from evewatch.models.channel import QuantumChannel
from evewatch.models.eve import Eve
from evewatch.models.error_correction import reconcile
from evewatch.models.noise import DepolarizingNoise
from evewatch.models.privacy_amplification import amplify
from evewatch.models.qber import estimate_qber
from evewatch.models.sifting import sift
from evewatch.models.types import SimulationParams, SimulationResult, TransmissionRecord
from evewatch.utils.rng import spawn_rngs


def run_simulation(params: SimulationParams) -> SimulationResult:
    """prepare -> transmit -> measure -> sift -> QBER check -> error correction -> privacy amplification."""
    alice_rng, bob_rng, eve_rng, noise_rng, qber_rng, ec_rng, pa_rng = spawn_rngs(params.seed, 7)

    alice = Alice(alice_rng)
    bob = Bob(bob_rng)
    eve = Eve(eve_rng, params.eve_probability) if params.eve_probability > 0 else None
    noise = DepolarizingNoise(noise_rng, params.noise) if params.noise > 0 else None

    # Eve taps the line near Alice; the noise acts on the rest of the channel.
    stages = []
    if eve:
        stages.append(eve.intercept)
    if noise:
        stages.append(noise.apply)
    channel = QuantumChannel(stages)

    bob.measure(channel.transmit(alice.prepare(params.n_qubits)))

    transmission = TransmissionRecord(
        alice_bits=alice.bits,
        alice_bases=alice.bases,
        bob_bases=bob.bases,
        bob_bits=bob.bits,
        eve_intercepted=eve.intercepted if eve else None,
        eve_bases=eve.bases if eve else None,
        eve_bits=eve.bits if eve else None,
    )
    sifted = sift(transmission)
    report = estimate_qber(sifted, params.sample_fraction, params.qber_threshold, qber_rng)

    reconciliation = final_key = None
    if not report.abort:
        reconciliation = reconcile(report.alice_remaining, report.bob_remaining, report.qber, ec_rng)
        if reconciliation.verified:
            final_key = amplify(
                report.alice_remaining,
                reconciliation.bob_corrected,
                report.qber,
                reconciliation.leaked_bits,
                pa_rng,
            )

    return SimulationResult(
        params=params,
        transmission=transmission,
        sifted=sifted,
        qber_report=report,
        reconciliation=reconciliation,
        final_key=final_key,
    )
