from pathlib import Path

from streamlit.testing.v1 import AppTest

from iff.guide_tour import SCENES


def test_tour_all_scenes_and_exit():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
    next(b for b in app.button if b.label == "① 3분 가이드 투어").click().run(timeout=30)
    for index in range(len(SCENES)):
        assert not app.exception
        assert SCENES[index][0] in [h.value for h in app.subheader]
        assert app.get("plotly_chart")
        if index == 2:
            assert app.selectbox(key="tour_event_2").options == ["#1 · S1 · ACCEPT_FRIEND"]
        if index < len(SCENES) - 1:
            app.button(key="tour_next").click().run(timeout=30)
    app.button(key="tour_previous").click().run(timeout=30)
    app.button(key="tour_experiment").click().run(timeout=30)
    assert app.session_state.workspace == "공격 실험"
    assert app.session_state.sandbox_run[1].event.decision == "ACCEPT_FRIEND"
    next(b for b in app.button if b.label == "① 3분 가이드 투어").click().run(timeout=30)
    app.button(key="tour_finish").click().run(timeout=30)
    assert not app.session_state.tour_active
    assert len(app.tabs) == 5
