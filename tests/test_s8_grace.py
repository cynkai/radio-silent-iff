import numpy as np

from iff import config, crypto, scenarios
from iff.protocol import Interrogator, Response


def test_s8_accepts_old_key_then_rejects_revoked_unit_in_same_grace_epoch() -> None:
    rng = np.random.default_rng(42)

    events, expected = scenarios.s8_captured_key_grace(rng)

    assert [(event.decision, event.reject_stage) for event in events] == [
        ("ACCEPT_FRIEND", None), ("REJECT", "REVOKED"),
    ]
    assert expected == [("ACCEPT_FRIEND", None), ("REJECT", "REVOKED")]
    assert events[0].epoch == events[1].epoch == scenarios.EPOCH
    assert events[0].unit_id == events[1].unit_id == scenarios.CAP.hex()
    assert events[0].nonce_hex != events[1].nonce_hex


def test_captured_key_is_valid_until_grace_ends_and_revocation_overrides_grace() -> None:
    old_key = crypto.unit_key(scenarios.MASTER_KEY, scenarios.EPOCH, scenarios.CAP)
    nonce = bytes(config.NONCE_BYTES)
    response = Response(scenarios.CAP, scenarios.EPOCH, nonce,
                        crypto.response_tag(old_key, nonce, scenarios.CAP, scenarios.EPOCH),
                        t_recv_ns=50_000)
    at_end = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH + config.EPOCH_GRACE)
    after_end = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH + config.EPOCH_GRACE + 1)
    revoked = Interrogator(scenarios.MASTER_KEY, scenarios.EPOCH + 1, revoked={scenarios.CAP})
    for verifier in (at_end, after_end, revoked):
        verifier.issue(nonce, 0)

    results = [verifier.verify(response) for verifier in (at_end, after_end, revoked)]

    assert [(result.decision, result.reject_stage) for result in results] == [
        ("ACCEPT_FRIEND", None), ("REJECT", "EPOCH"), ("REJECT", "REVOKED"),
    ]


def test_extended_scenario_run_includes_s8_without_changing_s1_to_s7() -> None:
    baseline = scenarios.run_all(seed=42)

    extended = scenarios.run_all(seed=42, include_grace=True)

    assert extended["S8"]["actual"] == [("ACCEPT_FRIEND", None), ("REJECT", "REVOKED")]
    assert extended["S8"]["match"]
    for name, result in baseline.items():
        assert extended[name] == result


def test_s8_verifies_both_responses_in_next_epoch(monkeypatch) -> None:
    observed = []
    verify = Interrogator.verify

    def record_verify(self, response):
        observed.append((self.current_epoch, response.epoch, response.unit_id in self.revoked))
        return verify(self, response)

    monkeypatch.setattr(Interrogator, "verify", record_verify)

    scenarios.s8_captured_key_grace(np.random.default_rng(42))

    assert observed == [
        (scenarios.EPOCH + 1, scenarios.EPOCH, False),
        (scenarios.EPOCH + 1, scenarios.EPOCH, True),
    ]
