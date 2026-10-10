import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_all_record_hides_selector_and_groups_alerts() -> None:
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))

    app.run(timeout=20)

    assert not app.exception
    assert "scenario" not in [box.key for box in app.selectbox]
    rendered = "\n".join(element.value for element in app.markdown)
    assert "R3 ×2" in rendered
    assert "R7 ×2" in rendered
    assert "폐기 기체 활동 감지" in rendered
    assert "무응답" in rendered


def test_s9_radar_preserves_coordinates_and_displays_no_response() -> None:
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=20)
    app.radio(key="view_mode").set_value("선택 시나리오").run(timeout=20)

    app.selectbox(key="scenario").select("S9").run(timeout=20)

    assert not app.exception
    spec = json.loads(app.tabs[0].get("plotly_chart")[0].proto.spec)
    contacts = [trace for trace in spec["data"] if "customdata" in trace]
    assert len(contacts) == 1
    assert contacts[0]["marker"]["symbol"] == "x"
    assert contacts[0]["r"] == [600, 700]
    assert contacts[0]["theta"] == [280, 310]
    assert "무응답" in contacts[0]["name"]
    assert next(trace["text"] for trace in spec["data"] if trace["mode"] == "text") == ["S9a", "S9b"]
    assert "title" not in spec["layout"]["polar"]["radialaxis"]
