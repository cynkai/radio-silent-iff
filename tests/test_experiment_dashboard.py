from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from iff.briefing import Brief, BriefResult
from iff.briefing_session import BriefLimitReached, BriefSession, SESSION_LIMIT
from iff.sandbox import Attack
from visual_selectors import motion_data


ROOT = Path(__file__).resolve().parents[1]


def test_session_cache_and_budget_limit():
    session = BriefSession()
    result = BriefResult(Brief(summary="", findings=[], recommendations=[]), False)
    with patch("iff.briefing_session.get_brief", return_value=result) as generate:
        for _ in range(8):
            assert session.request("same") == result
        for index in range(SESSION_LIMIT - 1):
            session.request(str(index))
        with pytest.raises(BriefLimitReached):
            session.request("over budget")
    assert generate.call_count == SESSION_LIMIT
    assert session.request("same") == result


def test_failed_brief_attempts_also_exhaust_session_budget():
    session = BriefSession()
    with patch("iff.briefing_session.get_brief", side_effect=ConnectionError) as generate:
        for index in range(SESSION_LIMIT):
            with pytest.raises(ConnectionError):
                session.request(str(index))
        with pytest.raises(BriefLimitReached):
            session.request("retry")
    assert generate.call_count == SESSION_LIMIT


def test_dashboard_calls_llm_only_after_explicit_button():
    result = BriefResult(Brief(summary="", findings=[], recommendations=[]), False)
    with patch("iff.briefing_session.get_brief", return_value=result) as generate:
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)
        app.radio[0].set_value("공격 실험").run()
        app.button(key="FormSubmitter:sandbox_form-공격 실행").click().run()
        assert not app.exception
        generate.assert_not_called()
        assert app.session_state.sandbox_run[1].event.decision == "ACCEPT_FRIEND"
        app.button(key="sandbox_brief_generate").click().run()
        assert generate.call_count == 1
        app.button(key="sandbox_brief_generate").click().run()
        assert generate.call_count == 1


def test_sandbox_controls_and_traffic_render_engine_results():
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)
    app.radio[0].set_value("공격 실험").run()
    app.slider(key="sandbox_relay").set_value(40)
    app.button(key="FormSubmitter:sandbox_form-공격 실행").click().run()
    assert app.session_state.sandbox_run[1].event.reject_stage == "RTT"
    app.selectbox(key="sandbox_attack").select(Attack.ROGUE)
    app.button(key="FormSubmitter:sandbox_form-공격 실행").click().run()
    assert app.session_state.sandbox_run[1].event.decision == "NO_RESPONSE"
    assert not app.tabs[0].get("plotly_chart")
    app.button(key="FormSubmitter:traffic_form-트래픽 생성").click().run(timeout=20)
    assert not app.exception
    assert len(app.tabs[1].get("plotly_chart")) + len(motion_data(app.tabs[1], "radar")) == 2
    table = app.tabs[1].dataframe[0].value
    assert table.iloc[-1]["tp"] == 75
    assert table.iloc[-1]["fp"] == 0
