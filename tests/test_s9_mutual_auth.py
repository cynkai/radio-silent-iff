import hashlib
import hmac
import shutil
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from iff import crypto, detect, scenarios
from iff.events import to_dicts
from iff.protocol import Interrogator, Responder


def drone() -> Responder:
    return Responder(scenarios.FRIEND, scenarios.EPOCH,
                     {scenarios.EPOCH: crypto.iq_key(scenarios.MASTER_KEY, scenarios.EPOCH)},
                     {scenarios.EPOCH: crypto.unit_key(scenarios.MASTER_KEY, scenarios.EPOCH, scenarios.FRIEND)})


def test_issue_authenticates_and_drone_response_verifies() -> None:
    iq = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH)
    challenge = iq.issue(b"12345678", 0)
    key = crypto.hkdf(crypto.epoch_key(scenarios.MASTER_KEY, scenarios.EPOCH), b"iff-iq", b"", 32)
    expected = hmac.new(key, b"CQ12345678IQ-01" + scenarios.EPOCH.to_bytes(8, "big"), hashlib.sha256).digest()[:4]

    response = drone().respond(challenge, t_recv_ns=50_000)

    assert challenge.iq_tag == expected
    assert response is not None
    assert iq.verify(response).decision == "ACCEPT_FRIEND"


@pytest.mark.parametrize("field,value,stage", [
    ("iq_tag", b"bad!", "IQ_TAG"), ("interrogator_id", "fake", "IQ_TAG"),
    ("nonce", b"87654321", "IQ_TAG"), ("epoch", 99, "IQ_EPOCH"),
    ("epoch", 101, "IQ_EPOCH"),
])
def test_tampered_query_suppresses_response(field: str, value: bytes | str | int, stage: str) -> None:
    responder = drone()
    challenge = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH).issue(b"12345678", 0)

    response = responder.respond(replace(challenge, **{field: value}))

    assert response is None
    assert responder.events[-1].decision == "NO_RESPONSE"
    assert responder.events[-1].reject_stage == stage
    assert not responder.seen


def test_replay_cache_is_per_epoch_and_rejects_repeated_query() -> None:
    responder = drone()
    iq = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH)
    challenge = iq.issue(b"12345678", 0)
    assert responder.respond(challenge) is not None

    repeated = responder.respond(challenge)

    assert repeated is None
    assert responder.events[-1].reject_stage == "IQ_NONCE"


def test_rotated_provisioned_key_allows_same_nonce_in_new_epoch() -> None:
    responder = drone()
    iq = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH)
    responder.respond(iq.issue(b"12345678", 0))
    iq.current_epoch += 1
    responder.current_epoch += 1
    responder.iq_keys[iq.current_epoch] = crypto.iq_key(scenarios.MASTER_KEY, iq.current_epoch)
    responder.unit_keys[iq.current_epoch] = crypto.unit_key(scenarios.MASTER_KEY, iq.current_epoch, scenarios.FRIEND)

    response = responder.respond(iq.issue(b"12345678", 1))

    assert response is not None
    assert response.epoch == 101


def test_s9a_s9b_and_yaml_only_r7(tmp_path: Path) -> None:
    events, _ = scenarios.s9_rogue_interrogator(np.random.default_rng(42))
    rules = tmp_path / "rules"
    shutil.copytree(detect.RULES_DIR, rules, ignore=shutil.ignore_patterns("07-*"))
    assert detect.run_rules(to_dicts(events), rules_dir=rules) == []
    shutil.copyfile(detect.RULES_DIR / "07-rogue-interrogator.yaml", rules / "07-rogue-interrogator.yaml")

    alerts = detect.run_rules(to_dicts(events), rules_dir=rules)

    assert [(event.scenario, event.decision, event.reject_stage) for event in events] == [
        ("S9a", "NO_RESPONSE", "IQ_TAG"),
        ("S9b", "NO_RESPONSE", "IQ_NONCE"),
    ]
    assert [alert["rule"] for alert in alerts] == ["R7_ROGUE_INTERROGATOR"] * 2
    assert [alert["evidence"] for alert in alerts] == [[1_000_000], [3_000_000]]


@pytest.mark.parametrize("seed", [7, 42])
def test_s9_does_not_change_s1_through_s8(seed: int) -> None:
    original = scenarios.run_all(seed, include_grace=True)

    extended = scenarios.run_all(seed, include_grace=True, include_rogue=True)

    assert {name: extended[name] for name in original} == original
    assert all(result["match"] for result in original.values())
    legacy_alerts = detect.run_rules(to_dicts([e for r in original.values() for e in r["events"]]))
    extended_alerts = detect.run_rules(to_dicts([e for r in extended.values() for e in r["events"]]))
    assert [a for a in extended_alerts if a["rule"] != "R7_ROGUE_INTERROGATOR"] == legacy_alerts
