"""Central defaults and constants."""

# Above this error rate no secure key can be distilled (Shor-Preskill bound for BB84).
QBER_THRESHOLD = 0.11

# Large enough that a clean run still leaves 128+ final key bits for AES.
DEFAULT_N_QUBITS = 1024

# Fraction of the sifted key that Alice and Bob publicly sacrifice to estimate the QBER.
DEFAULT_SAMPLE_FRACTION = 0.5

# Extra bits removed during privacy amplification as a safety margin.
PA_SECURITY_BITS = 32

# Refuse to derive an AES key from fewer final key bits than this.
MIN_AES_KEY_BITS = 128
