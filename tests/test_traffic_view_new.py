from pathlib import Path

from streamlit.testing.v1 import AppTest

from iff.traffic import TrafficInput, detect_traffic, generate_traffic, measure, sweep
from iff.traffic_view import performance_figure, traffic_until


def test_scrubber_uses_only_past_events_and_keeps_truth_separate():
    traffic = generate_traffic(TrafficInput(benign=10, attacks=10))
    cutoff = traffic.events[7].ts_ns
    visible = traffic_until(traffic, cutoff)
    assert visible.events == traffic.events[:8]
    assert visible.truth == traffic.truth[:8]
    alerts = detect_traffic(visible.events)
    assert all(stamp <= cutoff for alert in alerts for stamp in alert["evidence"])
    assert traffic_until(traffic, traffic.events[-1].ts_ns) == traffic


def test_bars_and_curve_use_engine_metrics():
    inputs = TrafficInput(benign=10, attacks=10)
    traffic = generate_traffic(inputs)
    metrics = measure(traffic, detect_traffic(traffic.events))
    measurements = sweep(inputs)
    chart = performance_figure(metrics, measurements, "ANY_RULE")
    assert list(chart.data[0].y) == [item.detection_rate for item in metrics]
    assert list(chart.data[1].y) == [item.false_positive_rate for item in metrics]
    assert list(chart.data[2].y) == [row.metrics[-1].false_positive_rate for row in measurements]


def test_traffic_initial_result_and_time_control():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.radio[0].set_value("공격 실험").run()
    traffic = generate_traffic(app.session_state.traffic_input)
    app.select_slider(key="traffic_time").set_value(traffic.events[9].ts_ns).run()
    assert not app.exception
    assert any("엔진 이벤트 10/300건" in item.value for item in app.markdown)
    assert len(app.tabs[1].get("plotly_chart")) == 2
