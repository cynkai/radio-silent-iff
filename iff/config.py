"""All tunable parameters and ASSUMPTION_* constants in one place.

ASSUMPTION_* values are NOT measured. They are scenario defaults for the
simulation and every one of them is listed in README's "가정과 한계".
"""

# --- physical constant ---
C_M_PER_S = 299_792_458.0  # speed of light in vacuum

# --- ASSUMPTION constants (unmeasured, simulation defaults only) ---
ASSUMPTION_PROC_NS = 50_000          # responder processing delay (50 us)
ASSUMPTION_PROC_JITTER_NS = 5_000    # +/- jitter on processing delay (5 us)
ASSUMPTION_PROC_MAX_NS = 70_000      # max processing budget allowed in RTT check

# --- protocol parameters ---
EPOCH_SECONDS = 600
EPOCH_GRACE = 1            # accept current epoch and this many previous epochs
NONCE_BYTES = 8
UNIT_ID_BYTES = 4
TAG_BITS = 32             # truncated HMAC tag width (optical-bandwidth constraint)

# --- component 2 (maneuver signature) ---
MANEUVER_WINDOW_S = 60
MANEUVER_BITS = 16
MANEUVER_THETA_DEG = 8.0
MANEUVER_T_BIT_S = 1.5
MANEUVER_DT_S = 0.1
MANEUVER_HAMMING_K = 2

# --- channel defaults ---
DEFAULT_D_MAX_M = 2000.0   # max engagement range used to size the RTT budget
DEFAULT_P_BER = 0.0

TAG_BYTES = (TAG_BITS + 7) // 8


def rtt_budget_ns(d_max_m: float) -> float:
    """Upper bound on acceptable round-trip time: round-trip light time to
    d_max plus the allowed processing component."""
    return 2.0 * d_max_m / C_M_PER_S * 1e9 + ASSUMPTION_PROC_MAX_NS
