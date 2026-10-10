from collections.abc import Sequence
from html import escape

import streamlit as st

from .console_charts import radar_figure, rtt_figure
from .events import Event, STAGES
from .rule_engine import Alert


ALERT_LABELS = {
    "R1_REPLAY_ATTEMPT": "응답 재전송 의심",
    "R2_RELAY_SUSPECT": "중계 공격 의심",
    "R3_REVOKED_UNIT_ACTIVE": "폐기 기체 활동 감지",
    "R4_CLONE_SUSPECT": "복제 기체 의심",
    "R5_FAILURE_BURST": "인증 실패 집중",
    "R6_STALE_KEY_PROBE": "만료 키 탐색 의심",
    "R7_ROGUE_INTERROGATOR": "가짜 질의기 · 질의 재방송 의심",
}


def advance_replay(total: int) -> None:
    st.session_state.replay_index = min(st.session_state.replay_index + 1, total)
    st.session_state.pop("event_selection", None)


def reset_replay() -> None:
    st.session_state.replay_index = 0
    st.session_state.pop("event_selection", None)


def render_pipeline(event: Event) -> None:
    if event.component == "CQ":
        st.info("무응답 · 질의 차단" if event.decision == "NO_RESPONSE" else "질의 인증 통과")
        st.caption(f"응답기 로컬 기록 · {event.reject_stage or '유효한 질의'}")
        return
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
        st.caption("시뮬레이션 기하 · 거리 (m) · 방위 (°)")
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
    grouped: dict[str, list[Alert]] = {}
    for alert in alerts:
        grouped.setdefault(alert["rule"], []).append(alert)
    for rule, group in grouped.items():
        alert = group[0]
        st.markdown(
            f'<div class="console-row"><span class="console-badge {escape(alert["severity"])}">'
            f'{escape(alert["severity"])}</span> <strong>{escape(rule.split("_")[0])} ×{len(group)}</strong><br>'
            f'{escape(ALERT_LABELS.get(rule, rule))}</div>', unsafe_allow_html=True)
        with st.expander(f'{rule.split("_")[0]} 원문 · {len(group)}건'):
            for item in group:
                st.text(item["message"])


def render_feed(events: Sequence[Event], alerts: Sequence[Alert]) -> None:
    feed, warnings = st.columns([3, 2], gap="large")
    with feed:
        st.subheader("이벤트 피드")
        st.caption("이벤트 시각(ts_ns) 내림차순 · 같은 시각이면 추가된 순서의 역순")
        if not events:
            st.caption("아직 재생한 이벤트가 없습니다.")
        ordered = sorted(enumerate(events), key=lambda pair: (pair[1].ts_ns, pair[0]), reverse=True)
        for index, event in ordered:
            badge, label = {"ACCEPT_FRIEND": ("accept", "수락"),
                            "REJECT": ("reject", "거부"),
                            "NO_RESPONSE": ("neutral", "무응답")}[event.decision]
            st.markdown(
                f'<div class="console-row"><span class="console-badge {badge}">'
                f'{label}</span> '
                f'<strong>#{index + 1} · {escape(event.scenario)} · {escape(event.component)}</strong> '
                f'&nbsp; {escape(event.reject_stage or event.decision)}<br>'
                f'{event.bearing_deg:g}° / {event.range_m:g} m · ts {event.ts_ns} ns<br>'
                f'{escape(event.note)}</div>', unsafe_allow_html=True)
    with warnings:
        st.subheader("탐지 경보")
        st.caption("로그 기반 경보 · 인증 판정과 별개")
        render_alerts(alerts)
