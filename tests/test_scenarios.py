from iff import scenarios, detect
from iff.events import to_dicts


def test_all_scenarios_match_expected():
    results = scenarios.run_all(seed=42)
    for name, r in results.items():
        assert r["match"], f"{name}: expected {r['expected']} got {r['actual']}"


def test_r1_and_r3_alerts_fire():
    results = scenarios.run_all(seed=42)
    events = []
    for r in results.values():
        events.extend(r["events"])
    alerts = detect.run_rules(to_dicts(events), revoked_hex=[scenarios.CAP.hex()])
    rules = {a["rule"] for a in alerts}
    assert "R1_REPLAY_ATTEMPT" in rules
    assert "R3_REVOKED_UNIT_ACTIVE" in rules


def test_determinism_across_runs():
    a = scenarios.run_all(seed=7)
    b = scenarios.run_all(seed=7)
    for k in a:
        assert a[k]["actual"] == b[k]["actual"]


def test_s7_accepts_same_unit_at_two_positions_in_same_epoch() -> None:
    result = scenarios.run_all(seed=42)["S7"]
    events = result["events"]

    actual = [(event.decision, event.reject_stage) for event in events]

    assert actual == [("ACCEPT_FRIEND", None), ("ACCEPT_FRIEND", None)]
    assert result["expected"] == [("ACCEPT_FRIEND", None), ("ACCEPT_FRIEND", None)]
    first, second = events
    assert first.unit_id == second.unit_id
    assert first.epoch == second.epoch
    assert first.bearing_deg != second.bearing_deg
    assert first.range_m != second.range_m
    assert first.nonce_hex != second.nonce_hex


def test_r4_alert_fires_for_s7_alone() -> None:
    events = scenarios.run_all(seed=42)["S7"]["events"]

    alerts = detect.run_rules(to_dicts(events))

    clone_alerts = [alert for alert in alerts if alert["rule"] == "R4_CLONE_SUSPECT"]
    assert len(clone_alerts) == 1
    assert clone_alerts[0]["severity"] == "high"
