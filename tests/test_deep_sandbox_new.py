from pathlib import Path

from streamlit.testing.v1 import AppTest

from iff.deep_sandbox import capture_sweep, relay_sweep


def test_relay_boundary_is_engine_derived():
    results, boundary = relay_sweep(42, 0)
    assert results[int(boundary)].event.decision == "ACCEPT_FRIEND"
    assert results[int(boundary) + 1].event.reject_stage == "RTT"
    assert len(results) == 201


def test_capture_revocation_and_expiry():
    assert [r.event.reject_stage for r in capture_sweep(None, 42, 0)] == [None, None, "EPOCH"]
    assert [r.event.reject_stage for r in capture_sweep(1, 42, 0)] == [None, "REVOKED", "EPOCH"]


def test_deep_controls_and_comparison():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.radio[0].set_value("공격 실험").run()
    app.slider(key="deep_delay").set_value(40).run()
    app.selectbox(key="deep_revocation").set_value(1).run()
    assert not app.exception
    assert len(app.tabs[2].get("plotly_chart")) == 2
    assert any("REJECT / RTT" in item.value for item in app.markdown)
