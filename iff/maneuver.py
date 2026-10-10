"""Component 2: passive maneuver-signature identification (zero emission).

A key-derived bit pattern is flown as micro-yaw steps and recovered by an
observer from a noisy yaw track. Weak by design; used as the radio-silent
default mode, with component 1 reserved for on-demand confirmation.
"""
import numpy as np
from . import crypto, config


def expected_bits(master_key, epoch, unit_id, window, n_bits=None):
    n_bits = n_bits or config.MANEUVER_BITS
    uk = crypto.unit_key(master_key, epoch, unit_id)
    return crypto.maneuver_bits(uk, unit_id, window, n_bits)


def generate_yaw_series(bits, theta=None, t_bit=None, dt=None):
    theta = config.MANEUVER_THETA_DEG if theta is None else theta
    t_bit = config.MANEUVER_T_BIT_S if t_bit is None else t_bit
    dt = config.MANEUVER_DT_S if dt is None else dt
    n = int(round(t_bit / dt))
    series = []
    for b in bits:
        series += [theta if b == 1 else -theta] * n
    return np.array(series, dtype=float)


def observe(yaw_series, sigma, rng):
    return yaw_series + rng.normal(0.0, sigma, size=len(yaw_series))


def recover_bits(observed, n_bits, t_bit=None, dt=None):
    t_bit = config.MANEUVER_T_BIT_S if t_bit is None else t_bit
    dt = config.MANEUVER_DT_S if dt is None else dt
    n = int(round(t_bit / dt))
    bits = []
    for i in range(n_bits):
        seg = observed[i * n:(i + 1) * n]
        bits.append(1 if seg.mean() > 0 else 0)
    return bits


def hamming(a, b):
    return sum(int(x) != int(y) for x, y in zip(a, b))


def verify_maneuver(expected, observed_bits, k=None):
    k = config.MANEUVER_HAMMING_K if k is None else k
    return hamming(expected, observed_bits) <= k


def random_match_prob(n_bits=None, k=None):
    """Analytic P(a random bit pattern lands within hamming K of a target)."""
    from math import comb
    n = config.MANEUVER_BITS if n_bits is None else n_bits
    k = config.MANEUVER_HAMMING_K if k is None else k
    return sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
