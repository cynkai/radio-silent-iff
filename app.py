"""Radio-silent IFF simulation dashboard.

Run: python3 -m streamlit run app.py
"""
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iff import scenarios, detect, config, channel
from iff.events import to_dicts
from iff.maneuver import (expected_bits, generate_yaw_series, observe,
                          recover_bits, hamming, random_match_prob)
from iff.protocol import Interrogator, make_response
from iff.attacker_cost import captured_window_text
from iff.attacker_cost_panel import render_attacker_cost_panel
from iff.console_style import apply_console_style
from iff.console_charts import timeline_figure
from iff.operator_console import render_radar_detail, render_feed, render_alerts, advance_replay, reset_replay

st.set_page_config(page_title="IFF · 운용자 콘솔", layout="wide", initial_sidebar_state="collapsed")
apply_console_style()
st.warning("시뮬레이션 — 실기체·실채널 측정값이 아닙니다. "
           "표준 공개 암호 기법(HKDF/HMAC)을 사용하며 하드웨어는 없습니다.")
st.title("IFF / 운용자 콘솔")
st.caption("광학 인증 C1 · 기동 서명 C2  /  Radio-silent identification")
kpi_strip = st.container(key="kpi_strip")

sb = st.sidebar
sb.header("분석 파라미터")
seed = sb.number_input("시드", value=42, step=1)
d_max = sb.slider("d_max (m)", 500, 5000, int(config.DEFAULT_D_MAX_M), 100)
sigma = sb.slider("관측 노이즈 σ (deg)", 0.0, 80.0, 5.0, 1.0)
K = sb.slider("해밍 허용치 K", 0, 6, config.MANEUVER_HAMMING_K)
budget = config.rtt_budget_ns(d_max)
sb.caption(f"한계 분석 RTT 예산 ≈ {budget/1000:.1f} µs")
sb.caption("시드 외 실험 파라미터는 한계 분석용입니다. 콘솔은 시나리오의 기본 설정을 표시합니다.")

results = scenarios.run_all(seed=seed, include_grace=True)
all_events = [event for result in results.values() for event in result["events"]]
if st.session_state.get("replay_seed") != seed:
    st.session_state.replay_seed = seed
    st.session_state.replay_index = 0

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["① 운용자 콘솔", "② 이벤트 로그", "③ 포획 기체", "④ 한계 분석", "⑤ 공격자 비용"])

with tab1:
    scn = st.selectbox("시나리오", list(results), key="scenario")
    mode = st.radio("표시 범위", ["전체 기록", "공격 재생", "선택 시나리오"], horizontal=True, key="view_mode")
    if mode == "공격 재생":
        next_column, reset_column, progress_column = st.columns([1, 1, 4])
        next_column.button("다음", key="replay_next", disabled=st.session_state.replay_index >= len(all_events),
                           on_click=advance_replay, args=(len(all_events),))
        reset_column.button("초기화", key="replay_reset", on_click=reset_replay)
        progress_column.caption(f"S1 → S8 · {st.session_state.replay_index} / {len(all_events)} 이벤트")
        visible_events = all_events[:st.session_state.replay_index]
    elif mode == "선택 시나리오":
        visible_events = results[scn]["events"]
    else:
        visible_events = all_events
    alerts = detect.run_rules(to_dicts(visible_events), revoked_hex=[scenarios.CAP.hex()])
    with kpi_strip:
        metrics = st.columns(4)
        metrics[0].metric("질의 수", len(visible_events), help="표시된 이벤트 수입니다. C2 관측 판정도 포함합니다.")
        metrics[1].metric("수락", sum(event.decision == "ACCEPT_FRIEND" for event in visible_events))
        metrics[2].metric("거부", sum(event.decision == "REJECT" for event in visible_events))
        metrics[3].metric("high 경보", sum(alert["severity"] == "high" for alert in alerts))
    render_radar_detail(visible_events)
    render_feed(visible_events, alerts)
    with st.expander("선택 시나리오 원본 기록", expanded=False):
        rng = np.random.default_rng(seed)
        scenario_functions = {**scenarios.ALL, "S8": scenarios.s8_captured_key_grace}
        events, expected = scenario_functions[scn](rng)
        for event in events:
            st.json(to_dicts([event])[0])
        if [(event.decision, event.reject_stage) for event in events] == expected:
            st.success("기대 결과와 일치: True")
        else:
            st.error("기대 결과 불일치")

with tab2:
    st.subheader("표시 중인 이벤트 로그")
    st.caption("콘솔의 표시 범위와 공격 재생 단계에 연동됩니다.")
    st.dataframe(to_dicts(visible_events), width="stretch", hide_index=True)
    render_alerts(alerts)

with tab3:
    st.subheader("포획 키 / epoch 타임라인")
    captured_events = [*results["S4"]["events"], *results["S8"]["events"]]
    st.plotly_chart(timeline_figure(captured_events), width="stretch", key="epoch_timeline")
    st.info(captured_window_text())
    st.caption("S4는 새 epoch를 주장하며 옛 키로 서명해 TAG에서 거부됩니다. "
               "S8은 E+1 검증기가 이전 epoch 응답을 수락한 뒤 폐기 시 REVOKED로 거부합니다.")
    st.caption("EPOCH는 유예 종료 규칙의 경계 표시입니다. S4·S8에 EPOCH 거부 이벤트는 없습니다. "
               "같은 epoch의 응답은 행으로 구분하며, 위치는 실제 경과시간을 뜻하지 않습니다.")
    render_alerts(detect.run_rules(to_dicts(captured_events), revoked_hex=[scenarios.CAP.hex()]))

# ---------------- Tab 4 ----------------
with tab4:
    st.subheader("(a) 중계(relay) 탐지 경계")
    rng = np.random.default_rng(seed)
    ovhs = [0, 10_000, 20_000, 30_000, 40_000, 60_000, 100_000, 200_000]
    rates = []
    for ovh in ovhs:
        rej = 0
        for _ in range(200):
            iq = Interrogator(master_key=scenarios.MASTER_KEY, current_epoch=scenarios.EPOCH, d_max_m=d_max)
            nonce = rng.bytes(config.NONCE_BYTES); iq.issue(nonce, 0)
            rtt = channel.round_trip_ns(400.0, rng, relay_overhead_ns=ovh)
            r = make_response(scenarios.MASTER_KEY, scenarios.EPOCH, scenarios.FRIEND, nonce, t_recv_ns=int(rtt))
            if iq.verify(r).reject_stage == "RTT":
                rej += 1
        rates.append(rej / 200)
    fig = go.Figure(go.Scatter(x=[o/1000 for o in ovhs], y=rates, mode="lines+markers"))
    fig.update_layout(height=260, xaxis_title="중계 추가 지연 (µs)", yaxis_title="RTT 거부율",
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True, key="relay")
    nominal_boundary = (budget - 2 * channel.propagation_ns(400.0) - config.ASSUMPTION_PROC_NS) / 1000
    st.caption(f"명목 탐지 경계 ≈ (RTT 예산 − 기본 왕복) ≈ {nominal_boundary:.3f}µs. "
               "명목 경계는 지터와 무관하며, 경계 주변 성공률은 지터의 영향을 받습니다.")

    st.subheader("(b) 기동 서명 — 관측 노이즈 대 수락률")
    rng = np.random.default_rng(seed)
    exp = expected_bits(scenarios.MASTER_KEY, scenarios.EPOCH, scenarios.FRIEND, 500)
    prev = expected_bits(scenarios.MASTER_KEY, scenarios.EPOCH, scenarios.FRIEND, 499)
    gs, rs = generate_yaw_series(exp), generate_yaw_series(prev)
    sigmas = [0, 5, 10, 15, 20, 30, 40, 60, 80]
    gacc, racc = [], []
    for sg in sigmas:
        g = r = 0
        for _ in range(300):
            if hamming(exp, recover_bits(observe(gs, sg, rng), len(exp))) <= K:
                g += 1
            if hamming(exp, recover_bits(observe(rs, sg, rng), len(exp))) <= K:
                r += 1
        gacc.append(g/300); racc.append(r/300)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sigmas, y=gacc, mode="lines+markers", name="정상 아군"))
    fig2.add_trace(go.Scatter(x=sigmas, y=racc, mode="lines+markers", name="이전 window 재현"))
    fig2.update_layout(height=260, xaxis_title="관측 노이즈 σ (deg)", yaxis_title="수락률",
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True, key="maneuver")

    st.subheader("(c) 아군 목록 크기 대 C2 오수락률 (해석적)")
    p = random_match_prob(k=K)
    ms = [1, 5, 10, 25, 50, 100, 200]
    fa = [1 - (1 - p) ** m for m in ms]
    fig3 = go.Figure(go.Bar(x=[str(m) for m in ms], y=fa))
    fig3.update_layout(height=240, xaxis_title="아군 목록 크기", yaxis_title="오수락 확률(≥1건)",
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True, key="listsize")
    st.caption(f"단위 오수락 확률 p = {p:.4f} (n={config.MANEUVER_BITS}, K={K}). "
               "목록이 커질수록 C2 단독 식별은 신뢰도가 떨어진다 → C1 확인 필요.")


with tab5:
    render_attacker_cost_panel(Path(__file__).resolve().parent / "out")
