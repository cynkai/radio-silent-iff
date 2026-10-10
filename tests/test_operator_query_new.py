from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from iff import detect, scenarios
from iff.briefing import event_id
from iff.briefing_session import BriefLimitReached, BriefSession
from iff.events import to_dicts
from iff.operator_query import (AnswerSentence, EXAMPLE_QUESTIONS, build_answer,
                                empty_filter, interpret_question, request_answer, select_events, verify_answer)


@pytest.fixture
def logs():
    events = [event for result in scenarios.run_all(seed=42, include_grace=True, include_rogue=True).values()
              for event in result["events"]]
    return events, detect.run_rules(to_dicts(events))


@pytest.mark.parametrize("changes", [
    {"bearing_min": -1., "bearing_max": 210.}, {"bearing_min": 200.},
    {"time_min_ns": 20, "time_max_ns": 10}, {"rule": "R999"},
    {"decision": "ACCEPT"}, {"unit_id": "drop table"}, {"sql": "select *"},
    {"time_min_ns": "100"},
])
def test_filter_schema_rejects_invalid_fields(changes):
    with pytest.raises(ValidationError):
        empty_filter(**changes)


def test_mocked_filter_conversion():
    response = MagicMock()
    response.choices[0].finish_reason = "stop"
    response.choices[0].message.refusal = None
    response.choices[0].message.content = empty_filter(bearing_min=190., bearing_max=210.).model_dump_json()
    with patch("iff.operator_query._setting", return_value="test"), patch("iff.operator_query.OpenAI") as sdk:
        create = sdk.return_value.__enter__.return_value.chat.completions.create
        create.return_value = response
        result = interpret_question(EXAMPLE_QUESTIONS[0])
    assert result.bearing_min == 190
    assert create.call_args.kwargs["response_format"]["json_schema"]["strict"]


def test_citation_must_exist_and_stay_inside_filter(logs):
    events, alerts = logs
    filters = empty_filter(bearing_min=190., bearing_max=210.)
    answer = build_answer(filters, events, alerts, offline=True)
    assert answer.sentences and all(verify_answer(answer, events, alerts))
    outside = next(event for event in events if event not in select_events(filters, events, alerts))
    bad = [AnswerSentence(text=answer.sentences[0].text, evidence_event_ids=["E-missing"]),
           AnswerSentence(text=answer.sentences[0].text, evidence_event_ids=[event_id(outside)]),
           AnswerSentence(text="근거 없는 수락 주장", evidence_event_ids=answer.sentences[0].evidence_event_ids)]
    assert verify_answer(answer.model_copy(update={"sentences": bad}), events, alerts) == [False] * 3


def test_all_filter_dimensions_and_wrapping(logs):
    events, alerts = logs
    event = events[0]
    filters = empty_filter(time_min_ns=event.ts_ns, time_max_ns=event.ts_ns,
                          unit_id=event.unit_id, decision=event.decision)
    selected = select_events(filters, events, alerts)
    assert event in selected
    assert all(item.ts_ns == event.ts_ns and item.unit_id == event.unit_id and item.decision == event.decision for item in selected)
    assert len(selected) < len(events)
    wrapped = select_events(empty_filter(bearing_min=270., bearing_max=30.), events, alerts)
    assert all(event.bearing_deg >= 270 or event.bearing_deg <= 30 for event in wrapped)
    assert select_events(empty_filter(rule="R3"), events, alerts)


def test_shared_quota_and_cache(logs):
    events, alerts = logs
    session = BriefSession(attempts=4)
    with patch("iff.operator_query._setting", return_value="test"), patch("iff.operator_query.interpret_question", return_value=empty_filter()) as interpret:
        first = request_answer(session, "first", events, alerts)
        assert request_answer(session, "first", events, alerts) == first
        assert session.attempts == 5 and interpret.call_count == 1
        with pytest.raises(BriefLimitReached):
            session.request("uncached briefing")
        with pytest.raises(BriefLimitReached):
            request_answer(session, "second", events, alerts)


def test_offline_examples_derive_current_logs_without_network(logs):
    events, alerts = logs
    session = BriefSession()
    with patch("iff.operator_query._setting", return_value=""), patch("iff.operator_query.OpenAI") as sdk:
        for question in EXAMPLE_QUESTIONS:
            answer = request_answer(session, question, events, alerts)
            assert answer.offline and answer.sentences and all(verify_answer(answer, events, alerts))
        sdk.assert_not_called()
    assert session.attempts == 0 and len(session.query_results) == 3


def test_query_app_calls_only_on_click():
    with patch("iff.operator_query._setting", return_value="test"), patch("iff.operator_query.interpret_question", return_value=empty_filter(rule="R3")) as interpret:
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
        interpret.assert_not_called()
        app.button(key="operator_query_submit").click().run()
        assert interpret.call_count == 1 and not app.exception
        app.button(key="operator_query_submit").click().run()
        assert interpret.call_count == 1
        assert app.session_state.brief_session.attempts == 1
