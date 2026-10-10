from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from iff.attacker_cost import build_costs, probability_text


@pytest.mark.parametrize("scenario", ["S2", "S3", "S4", "S5", "S6", "S9"])
def test_cost_panel_displays_exported_probabilities_for_selected_attack(scenario: str) -> None:
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "app.py")).run(timeout=20)
    expected = [row for row in build_costs(root / "out") if row.scenario == scenario]

    app.selectbox(key="cost_attack").select(scenario).run(timeout=20)

    assert len(app.exception) == 0
    detail = app.dataframe[-1].value
    assert list(detail["성공 확률"]) == [probability_text(row) for row in expected]
    assert list(detail["유효 시간 상한(초)"]) == [
        "미측정" if row.valid_window_upper_s is None else f"{row.valid_window_upper_s:g}"
        for row in expected
    ]


def test_s8_dashboard_shows_grace_acceptance_then_revocation() -> None:
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "app.py")).run(timeout=20)

    app.radio(key="view_mode").set_value("선택 시나리오").run(timeout=20)
    app.selectbox(key="scenario").select("S8").run(timeout=20)

    assert len(app.exception) == 0
    assert len(app.success) == 1
    assert len(app.json) == 2
