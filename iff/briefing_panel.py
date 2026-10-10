from collections.abc import Sequence
from html import escape

import streamlit as st

from .briefing import build_context, event_id, get_brief, verify_brief
from .events import Event
from .rule_engine import Alert


def _select_evidence(index: int) -> None:
    st.session_state.event_selection = index


def render_briefing(events: Sequence[Event], alerts: Sequence[Alert]) -> None:
    with st.container(border=True, key="situation_briefing"):
        st.subheader("상황 브리핑")
        if not events:
            st.caption("표시된 이벤트가 없습니다. 재생 후 브리핑을 확인하세요.")
            return
        with st.spinner("경보 해석 중…"):
            result = get_brief(build_context(events, alerts))
        verified = verify_brief(result.brief, events, alerts)
        st.markdown('<span class="console-badge neutral">LLM 생성 · 판정에 관여하지 않음 · '
                    f'근거 검증 {verified.passed}/{verified.total} 통과</span>', unsafe_allow_html=True)
        if result.cached_example:
            st.caption("캐시된 예시 · seed=42 전체 기록으로 만든 오프라인 예시입니다. "
                       "현재 표시 로그로 근거를 다시 검증했습니다.")
        st.caption("요약·권고는 해석이며 근거 검증 집계에 포함되지 않습니다.")
        st.text(result.brief.summary)
        indices = {event_id(event): index for index, event in enumerate(events)}
        for number, item in enumerate(verified.findings):
            valid = item.status == "통과"
            finding = item.finding
            text = escape(finding.text)
            if not valid:
                text = f'<span class="brief-unverified"><s>{text}</s> · 근거 없음</span>'
            st.markdown(f'<div class="brief-finding">{text}</div>', unsafe_allow_html=True)
            with st.container(horizontal=True):
                for evidence in dict.fromkeys(finding.evidence_event_ids):
                    st.button(evidence, key=f"brief_evidence_{number}_{evidence}", type="tertiary",
                              disabled=evidence not in indices, help="이벤트 상세 패널에서 근거 보기",
                              on_click=_select_evidence, args=(indices.get(evidence, 0),))
        with st.expander("운용자 검토 권고"):
            for recommendation in result.brief.recommendations:
                st.text(recommendation)
