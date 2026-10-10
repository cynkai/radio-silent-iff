"""Idealized channel model for the simulation.

Honest limitation (also stated in README): real distance bounding is hard
because processing-delay jitter dwarfs light-travel time at these ranges.
This model only flags a relay when it adds delay beyond the jitter budget.
"""
from . import config


def propagation_ns(distance_m: float) -> float:
    return distance_m / config.C_M_PER_S * 1e9


def responder_delay_ns(rng) -> float:
    j = config.ASSUMPTION_PROC_JITTER_NS
    return config.ASSUMPTION_PROC_NS + int(rng.integers(-j, j + 1))


def apply_ber(tag: bytes, p_ber: float, rng) -> bytes:
    if p_ber <= 0:
        return tag
    bits = bytearray(tag)
    for i in range(len(bits) * 8):
        if rng.random() < p_ber:
            bits[i // 8] ^= (1 << (7 - i % 8))
    return bytes(bits)


def round_trip_ns(distance_m: float, rng, relay_overhead_ns: float = 0.0) -> float:
    """Challenge out + response back + responder processing (+ any relay)."""
    return 2.0 * propagation_ns(distance_m) + responder_delay_ns(rng) + relay_overhead_ns
