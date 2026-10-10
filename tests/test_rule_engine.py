import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

from iff import config, detect, scenarios
from iff.protocol import Interrogator, make_response
from iff.rule_config import RuleConfigError, load_rules
from iff.rule_engine import EventRecord


EXAMPLE_RULE: Final = Path(__file__).resolve().parents[1] / "examples/rules/06-epoch-probe.yaml"


def _epoch_probe_events() -> list[EventRecord]:
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


def test_adding_r6_yaml_detects_stale_epoch_probes_without_code_changes(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    shutil.copytree(detect.RULES_DIR, rules_dir)
    events = _epoch_probe_events()
    before = detect.run_rules(events, rules_dir=rules_dir)

    shutil.copyfile(EXAMPLE_RULE, rules_dir / EXAMPLE_RULE.name)
    after = detect.run_rules(events, rules_dir=rules_dir)

    assert [(event["decision"], event["reject_stage"]) for event in events] == [
        ("REJECT", "EPOCH"), ("REJECT", "EPOCH"), ("REJECT", "EPOCH"),
    ]
    assert [alert["rule"] for alert in before] == ["R5_FAILURE_BURST"]
    assert after[:-1] == before
    assert after[-1] == {
        "rule": "R6_STALE_KEY_PROBE", "severity": "medium",
        "message": "Repeated EPOCH rejections within 10s; possible probing with stale keys.",
        "evidence": [1_000_000_000, 5_000_000_000, 11_000_000_000],
    }


@pytest.mark.parametrize("variant", ["two_events", "late", "outside_sector", "other_stage", "accepted"])
def test_r6_does_not_alert_when_window_conditions_are_unsatisfied(variant: str) -> None:
    events = _epoch_probe_events()
    variants = {
        "two_events": events[:2],
        "late": events[:2] + [{**events[2], "ts_ns": 11_000_000_001}],
        "outside_sector": events[:2] + [{**events[2], "bearing_deg": 40.001}],
        "other_stage": events[:2] + [{**events[2], "reject_stage": "TAG"}],
        "accepted": events[:2] + [{**events[2], "decision": "ACCEPT_FRIEND"}],
    }

    alerts = detect.run_rules(variants[variant], rules_dir=EXAMPLE_RULE.parent)

    assert alerts == []


def test_default_rules_path_is_independent_of_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    alerts = detect.run_rules(_epoch_probe_events())

    assert [alert["rule"] for alert in alerts] == ["R5_FAILURE_BURST"]


@pytest.mark.parametrize("document", [
    "id: BROKEN\nkind: unknown\n",
    "id: BROKEN\nkind: event\ncases: []\n",
    "id: BROKEN\nkind: event\ncases: []\nunsupported: true\n",
    "!!python/object/apply:os.system ['false']",
    "- not a rule mapping",
])
def test_invalid_rule_fails_with_its_file_path(tmp_path: Path, document: str) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(document, encoding="utf-8")

    with pytest.raises(RuleConfigError) as error:
        load_rules(tmp_path)

    assert error.value.path == path


def test_duplicate_rule_ids_are_rejected(tmp_path: Path) -> None:
    shutil.copyfile(EXAMPLE_RULE, tmp_path / "first.yaml")
    shutil.copyfile(EXAMPLE_RULE, tmp_path / "second.yaml")

    with pytest.raises(RuleConfigError, match="duplicate rule id"):
        load_rules(tmp_path)


def test_r6_demo_cli_preserves_alerts_and_adds_epoch_probe_detection(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts/demo_r6.py"

    result = subprocess.run([sys.executable, str(script)], cwd=tmp_path,
                            capture_output=True, text=True, check=True, timeout=10)

    alerts = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    assert [alert["rule"] for alert in alerts] == [
        "R5_FAILURE_BURST", "R5_FAILURE_BURST", "R6_STALE_KEY_PROBE",
    ]
    assert alerts[0] == alerts[1]
    assert alerts[2]["severity"] == "medium"
    assert alerts[2]["evidence"] == [1_000_000_000, 5_000_000_000, 11_000_000_000]
