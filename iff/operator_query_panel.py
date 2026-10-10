from collections.abc import Sequence
from html import escape

import streamlit as st
from openai import OpenAIError
from pydantic import ValidationError

from .briefing import BriefUnavailable
from .briefing_session import BriefLimitReached, BriefSession, SESSION_LIMIT
from .events import Event
from .operator_query import EXAMPLE_QUESTIONS, request_answer, verify_answer
from .rule_engine import Alert


def render_operator_query(events: Sequence[Event], alerts: Sequence[Alert]) -> None:
    with st.container(border=True, key="operator_query"):
        st.subheader("운용자 질문")
        st.caption("LLM은 조회 필터만 해석합니다. 답변은 조회된 로그를 코드로 구성하고 문장별 근거를 검증합니다.")
        if not events:
            st.caption("조회할 이벤트가 없습니다. 공격 재생을 진행하세요.")
            return
        if "brief_session" not in st.session_state:
            st.session_state.brief_session = BriefSession()
        session = st.session_state.brief_session
        question = st.text_input("질문", value=EXAMPLE_QUESTIONS[0], key="operator_question", max_chars=500)
        clicked = st.button("질문 조회", key="operator_query_submit", type="primary")
        example = st.selectbox("검증된 캐시 예시 질문", EXAMPLE_QUESTIONS, key="operator_example")
        use_example = st.button("예시 답변 보기", key="operator_example_submit")
        if clicked or use_example:
            requested = example if use_example else question
            try:
                with st.spinner("필터 검증 및 로그 조회 중…"):
                    st.session_state.operator_answer = request_answer(session, requested, events, alerts, example=use_example)
                st.session_state.operator_answer_question = requested
            except (OpenAIError, ValidationError, BriefUnavailable, BriefLimitReached) as error:
                st.session_state.pop("operator_answer", None)
                st.info("필터를 검증하지 못했거나 호출 한도에 도달했습니다. 예시 질문 또는 기존 캐시를 확인하세요.")
                st.caption(type(error).__name__)
        st.caption(f"브리핑과 공유하는 세션 요청 {session.attempts}/{SESSION_LIMIT} · 같은 질문·로그는 캐시 재사용")
        answer = st.session_state.get("operator_answer")
        if answer is None:
            examples = [request_answer(session, item, events, alerts, example=True) for item in EXAMPLE_QUESTIONS]
            answer = examples[0]
            st.caption(f"기본 예시 · {EXAMPLE_QUESTIONS[0]}")
        else:
            st.caption(st.session_state.operator_answer_question)
        checks = verify_answer(answer, events, alerts)
        st.markdown('<span class="console-badge neutral">LLM 해석 · 판정 무관 · '
                    f'근거 검증 {sum(checks)}/{len(checks)}</span>', unsafe_allow_html=True)
        if answer.offline:
            st.caption("캐시 예시 · 현재 엔진 로그로 생성·재검증 · 외부 호출 없음")
        st.caption("룰 조회는 경보의 타임스탬프 근거 후보를 반환합니다. 같은 시각의 이벤트는 후보가 중복될 수 있습니다.")
        if not answer.sentences:
            st.info("현재 필터에 해당하는 로그가 없습니다.")
        for sentence, valid in zip(answer.sentences, checks):
            text = escape(sentence.text)
            if not valid:
                text = f'<span class="brief-unverified"><s>{text}</s> · 근거 없음</span>'
            st.markdown(f'<div class="brief-finding">{text}</div>', unsafe_allow_html=True)
            st.caption(" · ".join(sentence.evidence_event_ids))
        with st.expander("적용한 JSON 필터"):
            st.code(answer.filters.model_dump_json(indent=2), language="json", wrap_lines=True)
