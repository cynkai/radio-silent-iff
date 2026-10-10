#!/usr/bin/env python3
"""Run every scenario, write out/events.jsonl and out/summary.csv, and print a
table comparing expected vs actual reject stages. Exit non-zero on mismatch."""
import os
import sys
import csv
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iff import scenarios, detect   # noqa: E402
from iff.events import write_jsonl, to_dicts  # noqa: E402
from iff.attacker_cost import write_attacker_cost

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    results = scenarios.run_all(seed=args.seed, include_grace=True, include_rogue=True)

    all_events = []
    rows = []
    all_match = True
    for name, r in results.items():
        all_events.extend(r["events"])
        rows.append({
            "scenario": name,
            "expected": " -> ".join(f"{d}/{s}" for d, s in r["expected"]),
            "actual": " -> ".join(f"{d}/{s}" for d, s in r["actual"]),
            "match": r["match"],
        })
        all_match = all_match and r["match"]

    write_jsonl(all_events, os.path.join(OUT, "events.jsonl"))
    with open(os.path.join(OUT, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["scenario", "expected", "actual", "match"])
        w.writeheader()
        w.writerows(rows)

    # detection alerts
    revoked_hex = [scenarios.CAP.hex()]
    alerts = detect.run_rules(to_dicts(all_events), revoked_hex=revoked_hex)
    write_attacker_cost(Path(OUT))

    print(f"\n{'SCN':<5}{'MATCH':<7}{'EXPECTED':<34}ACTUAL")
    print("-" * 90)
    for row in rows:
        print(f"{row['scenario']:<5}{str(row['match']):<7}{row['expected']:<34}{row['actual']}")
    print("\nDetection alerts:")
    for a in alerts:
        print(f"  [{a['severity']:<6}] {a['rule']}: {a['message']}")
    rule_names = {a["rule"] for a in alerts}
    print(f"\nR1 present: {'R1_REPLAY_ATTEMPT' in rule_names} | "
          f"R3 present: {'R3_REVOKED_UNIT_ACTIVE' in rule_names} | "
          f"R4 present: {'R4_CLONE_SUSPECT' in rule_names}")
    print(f"ALL SCENARIOS MATCH EXPECTED: {all_match}")
    sys.exit(0 if all_match else 1)


if __name__ == "__main__":
    main()
