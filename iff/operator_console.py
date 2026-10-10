from collections.abc import Sequence
from html import escape

import streamlit as st

from .console_charts import radar_figure, rtt_figure
from .events import Event, STAGES
from .rule_engine import Alert


def advance_replay(total: int) -> None:
    st.session_state.replay_index = min(st.session_state.replay_index + 1, total)
    st.session_state.pop("event_selection", None)


def reset_replay() -> None:
    st.session_state.replay_index = 0
    st.session_state.pop("event_selection", None)


def render_pipeline(event: Event) -> None:
    blocked = False
    for stage in STAGES[:-1]:
        state, label = "pass", "✓ 통과"
        if event.component != "C1":
            state, label = "wait", "— 해당 없음"
        elif blocked:
            state, label = "wait", "— 미도달"
        elif event.reject_stage == stage:
            state, label, blocked = "fail", "✗ 차단", True
        st.markdown(f'<div class="step {state}"><span>{stage}</span><span>{label}</span></div>',
                    unsafe_allow_html=True)
    if event.component == "C2":
        st.caption("C2는 C1 파이프라인을 사용하지 않습니다.")
        st.write(f"기동 해밍 검증: {event.reject_stage or event.decision}")
    elif event.rtt_ns is None:
        st.caption("RTT 단계 미도달 · 검증 RTT 기록 없음")
    else:
        st.plotly_chart(rtt_figure(event), width="stretch", key="rtt_gauge")


def render_radar_detail(events: Sequence[Event]) -> None:
    radar, detail = st.columns([2, 1], gap="large")
    with radar:
        st.subheader("접촉 현황")
        st.caption("시뮬레이션 기하 · 수락 초록 / 거부 빨강 · C1 원 / C2 다이아")
        st.plotly_chart(radar_figure(events), width="stretch", key="radar")
        st.caption("같은 좌표의 응답은 겹쳐 표시됩니다. 이벤트 선택에서 개별 기록을 확인하세요.")
    with detail:
        st.subheader("이벤트 상세")
        if not events:
            st.info("다음을 눌러 첫 이벤트를 재생하세요.")
            return
        index = st.selectbox("이벤트 선택", range(len(events)), index=len(events) - 1,
                             format_func=lambda i: f"#{i + 1} · {events[i].scenario} · "
                             f"{events[i].reject_stage or events[i].decision}", key="event_selection")
        event = events[index]
        st.caption(f"{event.component} · unit {event.unit_id} · epoch {event.epoch}")
        render_pipeline(event)


def render_alerts(alerts: Sequence[Alert]) -> None:
    if not alerts:
        st.caption("현재 표시된 이벤트에서 탐지된 경보가 없습니다.")
    for alert in alerts:
        st.markdown(
            f'<div class="console-row"><span class="console-badge {escape(alert["severity"])}">'
            f'{escape(alert["severity"])}</span> <strong>{escape(alert["rule"])}</strong><br>'
            f'{escape(alert["message"])}</div>', unsafe_allow_html=True)


def render_feed(events: Sequence[Event], alerts: Sequence[Alert]) -> None:
    feed, warnings = st.columns([3, 2], gap="large")
    with feed:
        st.subheader("이벤트 피드")
        st.caption("이벤트 시각(ts_ns) 내림차순 · 같은 시각이면 추가된 순서의 역순")
        if not events:
            st.caption("아직 재생한 이벤트가 없습니다.")
        ordered = sorted(enumerate(events), key=lambda pair: (pair[1].ts_ns, pair[0]), reverse=True)
        for index, event in ordered:
            accepted = event.decision == "ACCEPT_FRIEND"
            badge = "accept" if accepted else "reject"
            st.markdown(
                f'<div class="console-row"><span class="console-badge {badge}">'
                f'{"수락" if accepted else "거부"}</span> '
                f'<strong>#{index + 1} · {escape(event.scenario)} · {escape(event.component)}</strong> '
                f'&nbsp; {escape(event.reject_stage or event.decision)}<br>'
                f'{event.bearing_deg:g}° / {event.range_m:g} m · ts {event.ts_ns} ns<br>'
                f'{escape(event.note)}</div>', unsafe_allow_html=True)
    with warnings:
        st.subheader("탐지 경보")
        st.caption("로그 기반 경보 · 인증 판정과 별개")
        render_alerts(alerts)
