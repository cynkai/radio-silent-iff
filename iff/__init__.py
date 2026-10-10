"""iff — radio-silent IFF authentication simulation (D4D x EDTH, Track 1 / Problem 04).

Simulation only. All cryptography uses standard, public primitives
(HKDF-SHA256 per RFC 5869, HMAC-SHA256, nonce challenge-response).
No hardware, no real RF, no measured performance figures.
"""
__all__ = [
    "config", "crypto", "channel", "protocol",
    "maneuver", "attacks", "events", "detect", "scenarios",
]
