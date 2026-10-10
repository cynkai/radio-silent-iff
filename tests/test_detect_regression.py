import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict, Unpack

import pytest

from iff import config, detect, scenarios
from iff.events import to_dicts


class EventFields(TypedDict, total=False):
    ts_ns: int
    unit_id: str
    epoch: int
    decision: str
    reject_stage: str | None
    bearing_deg: float
    range_m: float
    rtt_ns: float | None


@dataclass(frozen=True, slots=True)
class Case:
    name: str
    events: list[EventFields]
    d_max_m: float = config.DEFAULT_D_MAX_M


GOLDEN: Final = Path(__file__).parent / "fixtures" / "detect_legacy_alerts.json"


def _event(ts_ns: int, **changes: Unpack[EventFields]) -> EventFields:
    event: EventFields = {
        "ts_ns": ts_ns, "unit_id": "unit-a", "epoch": 100,
        "decision": "REJECT", "reject_stage": "TAG",
        "bearing_deg": 45.0, "range_m": 300.0, "rtt_ns": None,
    }
    return event | changes


def _cases() -> list[Case]:
    second = 1_000_000_000
    shared = _event(1)
    missing_timestamp = _event(1, reject_stage="NONCE", decision="NO_RESPONSE")
    del missing_timestamp["ts_ns"]
    cases = [
        Case("empty", []),
        Case("missing_timestamp_evidence", [missing_timestamp]),
        Case("mixed_order", [
            _event(90, decision="ACCEPT_FRIEND", unit_id="b", bearing_deg=10.0),
            _event(80, decision="ACCEPT_FRIEND", unit_id="a", bearing_deg=10.0),
            _event(70, reject_stage="NONCE"),
            _event(60, decision="ACCEPT_FRIEND", unit_id="a", bearing_deg=40.0),
            _event(50, reject_stage="RTT"),
            _event(40, decision="ACCEPT_FRIEND", unit_id="b", bearing_deg=40.0),
            _event(30, reject_stage="REVOKED"),
            _event(20, decision="ACCEPT_FRIEND", unit_id="a", bearing_deg=70.0),
            _event(10, reject_stage="NONCE"),
        ]),
        Case("revoked_stage_only", [
            _event(1, unit_id=scenarios.CAP.hex(), decision="ACCEPT_FRIEND"),
            _event(2, unit_id=scenarios.CAP.hex()),
            _event(3, unit_id="unlisted", reject_stage="REVOKED", decision="ACCEPT_FRIEND"),
        ]),
        Case("pair_exact_boundaries", [
            _event(11, decision="ACCEPT_FRIEND"),
            _event(22, decision="ACCEPT_FRIEND", bearing_deg=65.0, range_m=800.0),
        ]),
        Case("pair_bearing_over", [
            _event(11, decision="ACCEPT_FRIEND"),
            _event(22, decision="ACCEPT_FRIEND", bearing_deg=65.001),
        ]),
        Case("pair_range_over", [
            _event(11, decision="ACCEPT_FRIEND"),
            _event(22, decision="ACCEPT_FRIEND", range_m=800.001),
        ]),
        Case("pair_linear_bearing", [
            _event(11, decision="ACCEPT_FRIEND", bearing_deg=359.0),
            _event(22, decision="ACCEPT_FRIEND", bearing_deg=1.0),
        ]),
        Case("pair_different_epochs", [
            _event(11, decision="ACCEPT_FRIEND"),
            _event(22, decision="ACCEPT_FRIEND", epoch=101, bearing_deg=180.0),
        ]),
        Case("window_below_count", [_event(1), _event(2)]),
        Case("window_inclusive_boundaries", [
            _event(1), _event(2, bearing_deg=35.0),
            _event(1 + 60 * second, bearing_deg=55.0),
        ]),
        Case("window_bearing_outside", [
            _event(1), _event(2), _event(3, bearing_deg=55.001),
        ]),
        Case("window_time_outside", [
            _event(1), _event(2), _event(2 + 60 * second),
        ]),
        Case("window_first_qualifying_anchor", [
            _event(5 * second, bearing_deg=200.0),
            _event(4 * second, bearing_deg=200.0),
            _event(1 * second, bearing_deg=0.0),
            _event(3 * second, bearing_deg=190.0),
            _event(2 * second, bearing_deg=200.0),
        ]),
        Case("window_tied_timestamps", [
            _event(20), _event(10), _event(10), _event(30),
        ]),
        Case("window_same_reference_excluded", [shared, shared, _event(2)]),
        Case("window_equal_distinct_records_counted", [_event(1), _event(1), _event(2)]),
        Case("window_spans_units_and_epochs", [
            _event(3, unit_id="c", epoch=102),
            _event(1, unit_id="a", epoch=100),
            _event(2, unit_id="b", epoch=101),
        ]),
    ]
    for distance in (0.0, 2000.0, 5000.0):
        threshold = 0.9 * config.rtt_budget_ns(distance)
        missing_rtt = _event(7, decision="ACCEPT_FRIEND")
        del missing_rtt["rtt_ns"]
        cases.append(Case(f"rtt_boundaries_{distance:g}", [
            _event(1, decision="ACCEPT_FRIEND", rtt_ns=threshold),
            _event(2, decision="ACCEPT_FRIEND", rtt_ns=threshold + 1),
            _event(3, decision="ACCEPT_FRIEND", reject_stage="RTT", rtt_ns=threshold + 1),
            _event(4, decision="ACCEPT_FRIEND", rtt_ns=threshold - 1),
            _event(5, decision="ACCEPT_FRIEND", rtt_ns=2 * threshold),
            _event(6, decision="ACCEPT_FRIEND"), missing_rtt,
        ], distance))
    for seed in (7, 42):
        events = to_dicts([
            event for result in scenarios.run_all(seed=seed).values()
            for event in result["events"]
        ])
        cases.append(Case(f"scenarios_{seed}_original", events))
        cases.append(Case(f"scenarios_{seed}_unique_timestamps", [
            event | {"ts_ns": (len(events) - index) * second}
            for index, event in enumerate(events)
        ]))
    return cases


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.name)
def test_alert_json_bytes_match_legacy(case: Case) -> None:
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))[case.name].encode("utf-8")

    alerts = detect.run_rules(case.events, revoked_hex=[scenarios.CAP.hex()],
                              d_max_m=case.d_max_m)

    actual = json.dumps(alerts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert actual == expected
