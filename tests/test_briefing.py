import json
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError
import httpx
from streamlit.testing.v1 import AppTest

from iff import briefing, detect, scenarios
from iff.briefing import Brief, Finding, build_context, event_id, generate_brief, get_brief, verify_brief
from iff.events import to_dicts


@pytest.fixture
def logs():
    events = scenarios.run_all(seed=42, include_grace=True, include_rogue=True)["S3"]["events"]
    return events, detect.run_rules(to_dicts(events))


@pytest.fixture(autouse=True)
def isolated_api(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr(briefing.st, "secrets", {})
    briefing._cached_brief.clear()
    yield
    briefing._cached_brief.clear()


def valid_brief(events, alerts):
    return Brief(summary="경보 검토", findings=[Finding(
        text=f"unit_id={events[0].unit_id} 확인", evidence_event_ids=[event_id(events[0])],
        rule=alerts[0]["rule"])], recommendations=["원본 로그 확인"])


def test_mocked_response_passes_and_does_not_mutate_logs(logs, monkeypatch):
    events, alerts = logs
    before = deepcopy((events, alerts))
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("OPENAI_MODEL", "configured-test-model")
    response = MagicMock()
    response.choices[0].finish_reason = "stop"
    response.choices[0].message.refusal = None
    response.choices[0].message.content = valid_brief(events, alerts).model_dump_json()
    with patch("iff.briefing.OpenAI") as sdk:
        create = sdk.return_value.__enter__.return_value.chat.completions.create
        create.return_value = response
        result = verify_brief(generate_brief(build_context(events, alerts)), events, alerts)
    assert (result.passed, result.total) == (1, 1)
    assert create.call_args.kwargs["model"] == "configured-test-model"
    assert create.call_args.kwargs["response_format"]["type"] == "json_schema"
    assert (events, alerts) == before


@pytest.mark.parametrize("change", [
    {"evidence_event_ids": ["missing-event"]},
    {"text": "unit_id=deadbeef 확인"},
    {"text": "deadbeef 확인"},
    {"text": "unit_id=unknown-unit 확인"},
    {"rule": "R999_UNKNOWN"},
    {"evidence_event_ids": []},
])
def test_unknown_evidence_marks_only_affected_finding(logs, change):
    events, alerts = logs
    good = valid_brief(events, alerts)
    bad = Finding.model_validate(good.findings[0].model_dump() | change)
    result = verify_brief(good.model_copy(update={"findings": [good.findings[0], bad]}), events, alerts)
    assert (result.passed, result.total) == (1, 2)
    assert [item.status for item in result.findings] == ["통과", "근거 없음"]


def test_no_key_uses_sample_without_network(logs):
    with patch("iff.briefing.OpenAI") as sdk:
        result = get_brief(build_context(*logs))
    assert result.cached_example
    assert result.brief == Brief.model_validate_json(briefing.SAMPLE_PATH.read_text())
    sdk.assert_not_called()


def test_malformed_model_json_uses_sample(logs, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    response = MagicMock()
    response.choices[0].finish_reason = "stop"
    response.choices[0].message.refusal = None
    response.choices[0].message.content = '{"summary": "missing findings"}'
    with patch("iff.briefing.OpenAI") as sdk:
        sdk.return_value.__enter__.return_value.chat.completions.create.return_value = response
        result = get_brief(build_context(*logs))
    assert result.cached_example


def test_secrets_override_environment_and_default_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-test-only")
    monkeypatch.setattr(briefing.st, "secrets", {"OPENAI_API_KEY": "secrets-test-only"})
    assert briefing._setting("OPENAI_API_KEY") == "secrets-test-only"
    assert briefing._setting("OPENAI_MODEL", "gpt-4o-mini") == "gpt-4o-mini"


@pytest.mark.parametrize("failure", [
    APIConnectionError(request=httpx.Request("POST", "https://api.openai.com")),
    briefing.BriefUnavailable("refused"),
])
def test_failure_is_cached_and_uses_sample(logs, monkeypatch, failure):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    with patch("iff.briefing.generate_brief", side_effect=failure) as generate:
        first = get_brief(build_context(*logs))
        second = get_brief(build_context(*logs))
    assert first.cached_example and second == first
    assert generate.call_count == 1


def test_context_hash_reuses_response_and_changes_invalidate_cache(logs, monkeypatch):
    events, alerts = logs
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    with patch("iff.briefing.generate_brief", return_value=valid_brief(*logs)) as generate:
        first = get_brief(build_context(events, alerts))
        second = get_brief(build_context(list(reversed(events)), alerts))
        get_brief(build_context(events, []))
    assert not first.cached_example and first == second
    assert generate.call_count == 2


def test_context_contains_only_permitted_projection(logs):
    context = json.loads(build_context(*logs))
    assert set(context) == {"events", "alerts"}
    assert all(set(event) == {"event_id", "unit_id", "reject_stage"} for event in context["events"])
    assert all(set(alert) == {"rule", "severity", "evidence_event_ids"} for alert in context["alerts"])


def test_sample_verifies_against_source_logs():
    events = [event for result in scenarios.run_all(seed=42, include_grace=True, include_rogue=True).values()
              for event in result["events"]]
    alerts = detect.run_rules(to_dicts(events), revoked_hex=[scenarios.CAP.hex()])
    result = verify_brief(Brief.model_validate_json(briefing.SAMPLE_PATH.read_text()), events, alerts)
    assert result.total > 0 and result.passed == result.total


def test_evidence_button_selects_matching_detail():
    app = AppTest.from_file(str(briefing.SAMPLE_PATH.parents[1] / "app.py")).run(timeout=20)
    sample = Brief.model_validate_json(briefing.SAMPLE_PATH.read_text())
    evidence = sample.findings[0].evidence_event_ids[0]
    app.button(key=f"brief_evidence_0_{evidence}").click().run(timeout=20)
    events = [event for result in scenarios.run_all(seed=42, include_grace=True, include_rogue=True).values()
              for event in result["events"]]
    assert not app.exception
    assert event_id(events[app.selectbox(key="event_selection").value]) == evidence
