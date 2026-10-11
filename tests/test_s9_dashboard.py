import json
from pathlib import Path

from streamlit.testing.v1 import AppTest
from visual_selectors import motion_data


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
    spec = motion_data(app.tabs[0], "radar")[0]
    contacts = spec["events"]
    assert len({(point["component"], point["decision"]) for point in contacts}) == 1
    assert {point["symbol"] for point in contacts} == {"x"}
    assert [point["range_m"] for point in contacts] == [600, 700]
    assert [point["bearing_deg"] for point in contacts] == [280, 310]
    assert {point["decision_label"] for point in contacts} == {"무응답"}
    assert [label["text"] for label in spec["labels"]] == ["S9a", "S9b"]
    assert "title" not in spec["radialaxis"]
