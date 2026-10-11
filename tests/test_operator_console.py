import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from iff import detect, scenarios
from iff.events import to_dicts
from visual_selectors import motion_data, kpi_values


ROOT = Path(__file__).resolve().parents[1]


def test_all_tabs_render_without_exceptions() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"))

    app.run(timeout=20)

    assert not app.exception
    assert len(app.tabs) == 5
    assert all(len(tab.children) for tab in app.tabs)
    assert len(motion_data(app.tabs[0], "radar")) >= 1
    assert len(app.tabs[2].get("plotly_chart")) == 1
    assert len(app.tabs[3].get("plotly_chart")) == 3
    assert len(app.tabs[4].dataframe) == 2


def test_replay_reveals_exact_event_prefix_and_resets() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)
    results = scenarios.run_all(seed=42, include_grace=True, include_rogue=True)
    events = [event for result in results.values() for event in result["events"]]

    app.radio(key="view_mode").set_value("공격 재생").run(timeout=20)

    assert kpi_values(app)[0] == "0"
    for count in range(1, len(events) + 1):
        app.button(key="replay_next").click().run(timeout=20)
        shown = events[:count]
        alerts = detect.run_rules(to_dicts(shown), revoked_hex=[scenarios.CAP.hex()])
        assert not app.exception
        assert kpi_values(app) == [
            str(count), str(sum(event.decision == "ACCEPT_FRIEND" for event in shown)),
            str(sum(event.decision == "REJECT" for event in shown)),
            str(sum(alert["severity"] == "high" for alert in alerts)),
        ]
        spec = motion_data(app.tabs[0], "radar")[0]
        contacts = sorted((point["id"], point["range_m"], point["bearing_deg"])
                          for point in spec["events"])
        assert contacts == [(index + 1, event.range_m, event.bearing_deg)
                            for index, event in enumerate(shown)]
        assert len(app.tabs[1].dataframe[0].value) == count
    assert app.button(key="replay_next").disabled

    app.button(key="replay_reset").click().run(timeout=20)

    assert not app.exception
    assert kpi_values(app)[0] == "0"
    assert not app.button(key="replay_next").disabled
    assert len(app.tabs[1].dataframe[0].value) == 0


def test_c2_selection_has_no_rtt_gauge_and_seed_restarts_replay() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)

    app.radio(key="view_mode").set_value("선택 시나리오").run(timeout=20)
    app.selectbox(key="scenario").select("S6").run(timeout=20)

    assert not app.exception
    assert kpi_values(app)[0] == "2"
    assert len(motion_data(app.tabs[0], "radar")) == 1
    assert not app.tabs[0].get("plotly_chart")

    app.radio(key="view_mode").set_value("공격 재생").run(timeout=20)
    app.button(key="replay_next").click().run(timeout=20)
    app.sidebar.number_input[0].set_value(7).run(timeout=20)

    assert not app.exception
    assert kpi_values(app)[0] == "0"


def test_timeline_contains_only_s4_s8_events() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)
    results = scenarios.run_all(seed=42, include_grace=True)

    spec = json.loads(app.tabs[2].get("plotly_chart")[0].proto.spec)

    for trace in spec["data"]:
        events = results[trace["name"]]["events"]
        assert trace["text"] == [event.reject_stage or "ACCEPT" for event in events]
        assert trace["customdata"] == [[event.epoch, event.ts_ns, event.decision] for event in events]
        assert trace["x"] == [scenarios.EPOCH + 1 if trace["name"] == "S8" else event.epoch
                              for event in events]
