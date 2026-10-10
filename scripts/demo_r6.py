#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy==2.5.3", "PyYAML==6.0.3"]
# ///
# How to run:
#   python3 scripts/demo_r6.py (repository dependencies installed)
#   uv run scripts/demo_r6.py
# Install uv if needed: curl -LsSf https://astral.sh/uv/install.sh | sh

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iff import config, detect, scenarios
from iff.protocol import Interrogator, make_response
from iff.rule_engine import EventRecord


def build_epoch_probe_events() -> list[EventRecord]:
    """Generate EPOCH rejections through the real verifier using stale epoch keys."""
    interrogator = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH)
    events = []
    for index, (timestamp, bearing) in enumerate(((1_000_000_000, 30.0),
                                                 (5_000_000_000, 35.0),
                                                 (11_000_000_000, 40.0))):
        nonce = index.to_bytes(config.NONCE_BYTES, "big")
        interrogator.issue(nonce, timestamp)
        response = make_response(
            scenarios.MASTER_KEY, scenarios.EPOCH - config.EPOCH_GRACE - 1,
            bytes.fromhex("0000000e"), nonce, t_recv_ns=timestamp + 50_000,
        )
        result = interrogator.verify(response)
        events.append({
            "ts_ns": timestamp, "unit_id": response.unit_id.hex(), "epoch": response.epoch,
            "decision": result.decision, "reject_stage": result.reject_stage,
            "bearing_deg": bearing, "range_m": 300.0, "rtt_ns": result.rtt_ns,
        })
    return events


def main() -> int:
    events = build_epoch_probe_events()
    print(f"Current epoch: {scenarios.EPOCH} | Response epoch: {events[0]['epoch']}")
    for event in events:
        print(f"ts_ns={event['ts_ns']} bearing={event['bearing_deg']} "
              f"{event['decision']}/{event['reject_stage']}")
    with TemporaryDirectory(prefix="iff-r6-demo-") as temporary:
        rules_dir = Path(temporary) / "rules"
        shutil.copytree(detect.RULES_DIR, rules_dir)
        before = detect.run_rules(events, rules_dir=rules_dir)
        print("\nBefore YAML addition:")
        for alert in before:
            print(json.dumps(alert, ensure_ascii=False))

        source = ROOT / "examples/rules/06-epoch-probe.yaml"
        shutil.copyfile(source, rules_dir / source.name)
        print(f"\nAdd YAML: {source.relative_to(ROOT)}")
        after = detect.run_rules(events, rules_dir=rules_dir)
        print("After YAML addition:")
        for alert in after:
            print(json.dumps(alert, ensure_ascii=False))

    preserved = after[:len(before)] == before
    added = len(after) == len(before) + 1 and after[-1]["rule"] == "R6_STALE_KEY_PROBE"
    print(f"\nExisting alerts preserved: {preserved}")
    print(f"R6 added: {added}")
    return 0 if preserved and added else 1


if __name__ == "__main__":
    sys.exit(main())
