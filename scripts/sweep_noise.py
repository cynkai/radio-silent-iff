#!/usr/bin/env python3
"""Component-2 analysis sweeps -> out/roc.csv and out/relay_sweep.csv.

(a) maneuver: genuine accept-rate and replay accept-rate vs observation sigma
(b) list-size false-accept rate vs analytic approximation
(c) relay: S3 reject-rate vs relay_overhead (distance-bounding boundary)
"""
import os
import sys
import csv
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
from iff import scenarios, config, channel  # noqa: E402
from iff.maneuver import (expected_bits, generate_yaw_series, observe,  # noqa: E402
                          recover_bits, hamming, random_match_prob)
from iff.protocol import Interrogator, make_response  # noqa: E402
from iff.attacker_cost import write_attacker_cost

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
MK = scenarios.MASTER_KEY
EP = scenarios.EPOCH
FR = scenarios.FRIEND


def maneuver_roc(seed=42, trials=400):
    rng = np.random.default_rng(seed)
    exp = expected_bits(MK, EP, FR, 500)
    prev = expected_bits(MK, EP, FR, 499)
    gen_series = generate_yaw_series(exp)
    rep_series = generate_yaw_series(prev)
    rows = []
    for sigma in [0.0, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0]:
        gok = rok = 0
        for _ in range(trials):
            g = recover_bits(observe(gen_series, sigma, rng), len(exp))
            if hamming(exp, g) <= config.MANEUVER_HAMMING_K:
                gok += 1
            r = recover_bits(observe(rep_series, sigma, rng), len(exp))
            if hamming(exp, r) <= config.MANEUVER_HAMMING_K:
                rok += 1
        rows.append({"sigma_deg": sigma,
                     "genuine_accept_rate": gok / trials,
                     "replay_accept_rate": rok / trials})
    return rows


def list_size_false_accept():
    p = random_match_prob()
    rows = []
    for m in [1, 5, 10, 25, 50, 100, 200]:
        rows.append({"fleet_size": m,
                     "analytic_any_false_match": 1 - (1 - p) ** m,
                     "per_unit_prob": p,
                     "n_bits": config.MANEUVER_BITS,
                     "hamming_k": config.MANEUVER_HAMMING_K})
    return rows


def relay_sweep(seed=42, trials=200):
    rng = np.random.default_rng(seed)
    rows = []
    budget = config.rtt_budget_ns(config.DEFAULT_D_MAX_M)
    distance_m = 400.0
    for ovh in [0, 10_000, 20_000, 30_000, 40_000, 60_000, 100_000, 200_000]:
        rej = 0
        for _ in range(trials):
            iq = Interrogator(master_key=MK, current_epoch=EP)
            nonce = rng.bytes(config.NONCE_BYTES)
            iq.issue(nonce, 0)
            rtt = channel.round_trip_ns(distance_m, rng, relay_overhead_ns=ovh)
            resp = make_response(MK, EP, FR, nonce, t_recv_ns=int(rtt))
            if iq.verify(resp).reject_stage == "RTT":
                rej += 1
        rows.append({"relay_overhead_ns": ovh, "reject_rate": rej / trials,
                     "budget_ns": round(budget), "distance_m": distance_m,
                     "nominal_rtt_ns": 2 * channel.propagation_ns(distance_m) + config.ASSUMPTION_PROC_NS,
                     "seed": seed, "trials": trials})
    return rows


def _dump(name, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


def main():
    os.makedirs(OUT, exist_ok=True)
    roc = maneuver_roc()
    _dump("roc.csv", roc)
    _dump("list_size.csv", list_size_false_accept())
    _dump("relay_sweep.csv", relay_sweep())
    write_attacker_cost(Path(OUT))
    print("\nmaneuver ROC (sigma -> genuine / replay accept):")
    for r in roc:
        print(f"  sigma={r['sigma_deg']:>4}  genuine={r['genuine_accept_rate']:.3f}  "
              f"replay={r['replay_accept_rate']:.3f}")


if __name__ == "__main__":
    main()
