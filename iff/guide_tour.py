from typing import Final

import streamlit as st

from . import scenarios
from .console_charts import timeline_figure
from .experiment_presets import select_preset
from .operator_console import render_radar_detail


SCENES: Final = (
    ("문제: 응답한 기체를 믿어도 될까요?", "위치나 응답만으로 아군을 단정하지 않습니다. 아래 접촉은 지금 실행한 시나리오의 기록입니다.", ("S1", "S3", "S7")),
    ("C1 · C2 구조", "C1은 광학 질의와 응답을 검증합니다. C2는 기동 서명을 관측합니다. C2의 판정은 C1 파이프라인과 별개입니다.", ("S1", "S6")),
    ("정상 아군 · S1", "정상 응답이 각 검증 단계를 통과하는 모습을 확인하세요. 오른쪽 RTT는 엔진이 기록한 값입니다.", ("S1",)),
    ("재전송과 위조 차단", "기존 응답 재사용과 키 없는 태그 위조를 비교하세요. 이벤트를 선택하면 최초 차단 단계를 볼 수 있습니다.", ("S2", "S5")),
    ("중계와 RTT 경계", "응답이 올바르게 서명되어도 왕복 시간이 예산을 넘으면 거부합니다. 예산 안의 중계는 통과할 수 있습니다.", ("S3",)),
    ("포획 기체와 유예 구간", "유효 키를 가진 기체는 폐기 전까지 수락될 수 있습니다. 타임라인의 판정은 S4·S8을 실행한 결과입니다.", ("S4", "S8")),
    ("가짜 질의기에는 침묵 · S9", "인증되지 않거나 재방송된 질의에 응답기는 답하지 않습니다. 무응답을 C1의 거부나 RTT 측정으로 꾸미지 않습니다.", ("S9",)),
    ("직접 공격해보기", "다음 버튼으로 마지막 한계를 읽거나, 공격 실험으로 이동해 프리셋을 직접 실행하세요.", ("S3", "S4")),
    ("정직한 한계", "포획된 유효 키, 예산 안의 중계, 짧은 기동 서명에는 한계가 있습니다. 수락과 무경보는 안전의 보증이 아닙니다. 실기체·실채널 검증은 별도입니다.", ("S7", "S6")),
)


def start_tour() -> None:
    st.session_state.workspace = "기존 시나리오"
    st.session_state.tour_active = True
    st.session_state.tour_step = 0
    st.session_state.pop("event_selection", None)


def move_tour(delta: int) -> None:
    st.session_state.tour_step = max(0, min(len(SCENES) - 1, st.session_state.tour_step + delta))
    st.session_state.pop("event_selection", None)


def finish_tour() -> None:
    st.session_state.tour_active = False


def tour_experiment() -> None:
    finish_tour()
    st.session_state.workspace = "공격 실험"
    select_preset(0)


def render_tour() -> None:
    index = st.session_state.tour_step
    title, explanation, selected = SCENES[index]
    previous, progress, following, finish = st.columns([1, 2, 1, 1])
    previous.button("이전", key="tour_previous", on_click=move_tour, args=(-1,), disabled=index == 0)
    progress.caption(f"3분 가이드 투어 · {index + 1}/{len(SCENES)}")
    following.button("다음", key="tour_next", on_click=move_tour, args=(1,), disabled=index == len(SCENES) - 1)
    finish.button("투어 종료", key="tour_finish", on_click=finish_tour)
    st.progress((index + 1) / len(SCENES))
    with st.container(border=True, key="tour_scene"):
        st.subheader(title)
        st.write(explanation)
    results = scenarios.run_all(seed=42, include_grace=True, include_rogue=True)
    events = [event for name in selected for event in results[name]["events"]]
    if index == 7:
        st.button("프리셋으로 직접 공격", key="tour_experiment", type="primary", on_click=tour_experiment)
    if index == 5:
        st.plotly_chart(timeline_figure(events), width="stretch", key="tour_timeline")
    render_radar_detail(events, selection_key=f"tour_event_{index}")
    st.caption("장면의 접촉·판정·RTT·epoch는 기존 엔진을 실행한 기록입니다. LLM은 투어 판정에 관여하지 않습니다.")
