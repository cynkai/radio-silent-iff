import numpy as np
from iff import config
from iff.maneuver import (expected_bits, generate_yaw_series, observe,
                         recover_bits, hamming, verify_maneuver, random_match_prob)

MK = b"\x09" * 32
EP = 100
UID = bytes.fromhex("0000000a")


def test_noiseless_recovery_exact():
    bits = expected_bits(MK, EP, UID, 500)
    series = generate_yaw_series(bits)
    rng = np.random.default_rng(0)
    rec = recover_bits(observe(series, 0.0, rng), len(bits))
    assert rec == bits
    assert verify_maneuver(bits, rec)


def test_replay_prev_window_rejected_noiseless():
    cur = expected_bits(MK, EP, UID, 500)
    prev = expected_bits(MK, EP, UID, 499)
    series = generate_yaw_series(prev)
    rng = np.random.default_rng(0)
    rec = recover_bits(observe(series, 0.0, rng), len(cur))
    assert hamming(cur, rec) > config.MANEUVER_HAMMING_K
    assert not verify_maneuver(cur, rec)


def test_random_match_prob_matches_empirical():
    rng = np.random.default_rng(3)
    n = config.MANEUVER_BITS
    target = [1, 0] * (n // 2)
    k = config.MANEUVER_HAMMING_K
    hits = 0
    N = 20000
    for _ in range(N):
        cand = list(rng.integers(0, 2, size=n))
        if hamming(target, cand) <= k:
            hits += 1
    emp = hits / N
    ana = random_match_prob()
    assert abs(emp - ana) < 0.01
