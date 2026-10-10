from collections.abc import Sequence
from html import escape

import streamlit as st

from .briefing import Brief, BriefResult, SAMPLE_PATH, build_context, event_id, verify_brief
from .briefing_session import BriefSession, SESSION_LIMIT
from .events import Event
from .rule_engine import Alert


def _select_evidence(index: int) -> None:
    st.session_state.event_selection = index


def render_briefing(events: Sequence[Event], alerts: Sequence[Alert], *,
                    key: str = "situation_briefing", show_example: bool = True) -> None:
    with st.container(border=True, key=key):
        st.subheader("상황 브리핑")
        if not events:
            st.caption("표시된 이벤트가 없습니다. 재생 후 브리핑을 확인하세요.")
            return
        if "brief_session" not in st.session_state:
            st.session_state.brief_session = BriefSession()
        session = st.session_state.brief_session
        context = build_context(events, alerts)
        result = session.lookup(context)
        st.caption(f"세션 생성 요청 {session.attempts}/{SESSION_LIMIT} · 동일 컨텍스트는 캐시 재사용")
        if st.button("브리핑 생성", key=f"{key}_generate",
                     disabled=result is None and session.attempts >= SESSION_LIMIT):
            with st.spinner("경보 해석 중…"):
                result = session.request(context)
            st.rerun()
        if result is None:
            if not show_example:
                st.caption("브리핑 생성 버튼을 누르면 현재 결과를 해석합니다.")
                return
            result = BriefResult(Brief.model_validate_json(SAMPLE_PATH.read_text(encoding="utf-8")), True)
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
                    evidence_key = (f"brief_evidence_{number}_{evidence}" if show_example
                                    else f"{key}_evidence_{number}_{evidence}")
                    st.button(evidence, key=evidence_key, type="tertiary",
                              disabled=evidence not in indices, help="이벤트 상세 패널에서 근거 보기",
                              on_click=_select_evidence, args=(indices.get(evidence, 0),))
        with st.expander("운용자 검토 권고"):
            for recommendation in result.brief.recommendations:
                st.text(recommendation)
