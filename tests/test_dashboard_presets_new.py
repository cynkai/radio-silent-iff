from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from iff.experiment_presets import PRESETS
from iff.sandbox import run_experiment


@pytest.mark.parametrize("index,decision,stage", [
    (0, "ACCEPT_FRIEND", None), (1, "REJECT", "RTT"),
    (2, "ACCEPT_FRIEND", None), (3, "NO_RESPONSE", "IQ_TAG"),
])
def test_presets_execute_engine(index, decision, stage):
    event = run_experiment(PRESETS[index][1]).event
    assert (event.decision, event.reject_stage) == (decision, stage)


def test_preset_buttons_and_conditional_controls():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
    app.radio(key="workspace").set_value("공격 실험").run(timeout=30)
    assert app.session_state.sandbox_run[1].event.decision == "ACCEPT_FRIEND"
    for index, (_, inputs) in enumerate(PRESETS):
        app.button(key=f"preset_{index}").click().run(timeout=30)
        assert not app.exception
        assert app.session_state.sandbox_run[1] == run_experiment(inputs)
    assert "sandbox_relay" not in [item.key for item in app.slider]
    assert "sandbox_epoch" not in [item.key for item in app.selectbox]
