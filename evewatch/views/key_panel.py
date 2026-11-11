"""Final key display and AES-GCM encryption demo."""

from __future__ import annotations

import streamlit as st

from evewatch import config
from evewatch.controllers import crypto_controller
from evewatch.models.types import SimulationResult

PREVIEW_BYTES = 96


def _hex_preview(blob: bytes) -> str:
    text = blob[:PREVIEW_BYTES].hex()
    return text + (" ..." if len(blob) > PREVIEW_BYTES else "")


def render(result: SimulationResult) -> None:
    if result.status == "aborted":
        st.info("The session was aborted, so there is no key. Lower Eve's probability or the noise.")
        return
    if result.status == "no_key":
        st.info(
            "No secret bits were left after error correction and privacy amplification. "
            "Send more qubits or reduce the error rate."
        )
        return

    key = result.final_key
    st.markdown(f"**Final key: {len(key):,} bits**")
    st.code(key.hex(), language=None, wrap_lines=True)
    if key.matches:
        st.caption("Alice's and Bob's keys are identical.")
    else:
        st.error("Alice's and Bob's keys differ.")

    st.subheader("Encrypt a message with AES-GCM")
    if len(key) < config.MIN_AES_KEY_BITS:
        st.warning(
            f"AES needs at least {config.MIN_AES_KEY_BITS} key bits and this run produced "
            f"{len(key)}. Increase the number of qubits."
        )
        return

    left, right = st.columns(2)
    with left:
        message = st.text_area("Alice's message", "Meet me at the usual place at noon.", height=120)
        uploaded = st.file_uploader("...or a text file", type=["txt"])

    if uploaded is not None:
        plaintext, name = uploaded.getvalue(), uploaded.name
    else:
        plaintext, name = message.encode("utf-8"), "message.txt"

    blob = crypto_controller.encrypt_bytes(result, plaintext)
    recovered = crypto_controller.decrypt_bytes(result, blob)

    with right:
        st.markdown("**Ciphertext sent over the public channel**")
        st.code(_hex_preview(blob), language=None, wrap_lines=True)
        st.markdown("**Bob decrypts with his key**")
        st.code(recovered.decode("utf-8", errors="replace")[:2000], language=None, wrap_lines=True)
        st.download_button(
            "Download encrypted file",
            data=blob,
            file_name=name + ".enc",
            mime="application/octet-stream",
        )
