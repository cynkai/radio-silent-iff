from dataclasses import replace
from unittest.mock import patch

import pytest

from iff import protocol
from iff.sandbox import Attack, SandboxInput, pipeline_states, run_experiment


@pytest.mark.parametrize(("inputs", "decision", "stage"), [
    (SandboxInput(attack=Attack.RELAY, relay_us=25), "ACCEPT_FRIEND", None),
    (SandboxInput(attack=Attack.RELAY, relay_us=40), "REJECT", "RTT"),
    (SandboxInput(attack=Attack.CAPTURED, elapsed_epochs=1), "ACCEPT_FRIEND", None),
    (SandboxInput(attack=Attack.CAPTURED, elapsed_epochs=1, revoked=True), "REJECT", "REVOKED"),
    (SandboxInput(attack=Attack.CAPTURED, elapsed_epochs=2), "REJECT", "EPOCH"),
    (SandboxInput(attack=Attack.CAPTURED, elapsed_epochs=2, revoked=True), "REJECT", "EPOCH"),
    (SandboxInput(attack=Attack.ROGUE), "NO_RESPONSE", "IQ_TAG"),
    (SandboxInput(attack=Attack.QUERY_REPLAY), "NO_RESPONSE", "IQ_NONCE"),
    (SandboxInput(attack=Attack.REPLAY), "REJECT", "NONCE"),
    (SandboxInput(attack=Attack.FORGE), "REJECT", "TAG"),
    (SandboxInput(attack=Attack.BENIGN), "ACCEPT_FRIEND", None),
    (SandboxInput(attack=Attack.BENIGN, ber=1), "REJECT", "TAG"),
])
def test_sandbox_engine_verdict(inputs, decision, stage):
    result = run_experiment(inputs)
    assert (result.event.decision, result.event.reject_stage) == (decision, stage)


def test_verifier_output_is_projected_without_second_decision():
    actual_verify = protocol.Interrogator.verify
    observed = []

    def observe(iq, response):
        result = actual_verify(iq, response)
        observed.append(result)
        return result

    with patch.object(protocol.Interrogator, "verify", observe):
        event = run_experiment(SandboxInput()).event
    assert (event.decision, event.reject_stage, event.rtt_ns) == (
        observed[-1].decision, observed[-1].reject_stage, observed[-1].rtt_ns)


def test_seed_reproducibility_and_unreached_stages():
    inputs = SandboxInput(attack=Attack.FORGE, seed=9, ber=0.1)
    result = run_experiment(inputs)
    assert result == run_experiment(inputs)
    assert pipeline_states(result.event) == ("통과", "통과", "통과", "통과", "차단", "미도달")
    assert pipeline_states(replace(result.event, component="CQ")) == ("미도달",) * 6
