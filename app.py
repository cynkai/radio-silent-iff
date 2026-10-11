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
from iff.console_style import ACCENT, GRID, MONO_FONT, PANEL, TEXT, apply_console_style
from iff.console_charts import timeline_figure
from iff.briefing_panel import render_briefing
from iff.operator_console import render_radar_detail, render_feed, render_alerts, advance_replay, reset_replay
from iff.experiment_panel import render_experiments
from iff.guide_tour import render_tour, start_tour
from iff.operator_query_panel import render_operator_query
from iff.motion_components import render_protocol, render_kpis

st.set_page_config(page_title="IFF · 운용자 콘솔", layout="wide", initial_sidebar_state="collapsed")


@st.cache_resource
def _ensure_sweeps():
    """Cloud deploys start without out/ (gitignored); regenerate the sweep CSVs once."""
    root = Path(__file__).resolve().parent
    needed = ["relay_sweep.csv", "list_size.csv", "roc.csv"]
    if not all((root / "out" / name).exists() for name in needed):
        import subprocess
        subprocess.run([sys.executable, str(root / "scripts" / "sweep_noise.py")],
                       check=True, cwd=root, capture_output=True)
    return True


_ensure_sweeps()
apply_console_style()
st.markdown('<div class="masthead"><div class="disclosure">시뮬레이션 — 실기체·실채널 측정값이 아닙니다. '
            '표준 공개 암호 기법(HKDF/HMAC)을 사용하며 하드웨어는 없습니다.</div>'
            '<h1>IFF / 운용자 콘솔</h1>'
            '<p class="value-proposition">무선 송신 없이 아군을 식별하고, 공격이 차단되는 지점과 한계를 확인하세요.</p></div>',
            unsafe_allow_html=True)


def navigate_console(workspace: str, tab: str, mode: str) -> None:
    st.session_state.tour_active = False
    st.session_state.workspace = workspace
    st.session_state.console_tab = tab
    st.session_state.view_mode = mode


with st.container(key="quick_guide"):
    guide = st.columns([.7, 2, 2, 2], vertical_alignment="center")
    guide[0].caption("이렇게 보세요")
    guide[1].button("① 3분 가이드 투어", width="stretch", on_click=start_tour)
    guide[2].button("② 공격 실험에서 직접 공격", width="stretch", on_click=navigate_console,
                    args=("공격 실험", "① 운용자 콘솔", "전체 기록"))
    guide[3].button("③ 한계 분석 확인", width="stretch", on_click=navigate_console,
                    args=("기존 시나리오", "④ 한계 분석", "전체 기록"))
workspace = st.radio("작업 공간", ["기존 시나리오", "공격 실험"], horizontal=True,
                     index=1 if st.query_params.get("workspace") == "experiments" else 0,
                     key="workspace", label_visibility="collapsed")
if workspace == "공격 실험":
    with st.container(key="experiments"):
        render_experiments()
    st.stop()
if st.session_state.get("tour_active", False):
    render_tour()
    st.stop()
signature = st.container(key="signature_scene")
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

results = scenarios.run_all(seed=seed, include_grace=True, include_rogue=True)
with signature:
    signature_scenario = st.selectbox("프로토콜 장면", list(results), key="signature_scenario")
    scene_events = results[signature_scenario]["events"]
    scene_index = next((i for i, event in enumerate(scene_events) if event.decision != "ACCEPT_FRIEND"), 0)
    render_protocol(scene_events[scene_index])
all_events = [event for result in results.values() for event in result["events"]]
if st.session_state.get("replay_seed") != seed:
    st.session_state.replay_seed = seed
    st.session_state.replay_index = 0

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["① 운용자 콘솔", "② 이벤트 로그", "③ 포획 기체", "④ 한계 분석", "⑤ 공격자 비용"],
    key="console_tab", on_change="rerun")

with tab1:
    mode = st.radio("표시 범위", ["전체 기록", "공격 재생", "선택 시나리오"], horizontal=True,
                    key="view_mode", label_visibility="collapsed")
    scn = st.selectbox("시나리오", list(results), key="scenario") if mode == "선택 시나리오" else None
    if mode == "공격 재생":
        next_column, reset_column, progress_column = st.columns([1, 1, 4])
        next_column.button("다음", key="replay_next", disabled=st.session_state.replay_index >= len(all_events),
                           on_click=advance_replay, args=(len(all_events),))
        reset_column.button("초기화", key="replay_reset", on_click=reset_replay)
        progress_column.caption(f"S1 → S9 · {st.session_state.replay_index} / {len(all_events)} 이벤트")
        visible_events = all_events[:st.session_state.replay_index]
    elif mode == "선택 시나리오":
        visible_events = results[scn]["events"]
    else:
        visible_events = all_events
    alerts = detect.run_rules(to_dicts(visible_events), revoked_hex=[scenarios.CAP.hex()])
    with kpi_strip:
        render_kpis(visible_events, alerts)
    render_radar_detail(visible_events)
    render_feed(visible_events, alerts)
    render_briefing(visible_events, alerts)
    render_operator_query(visible_events, alerts)
    with st.expander("표시 중인 원본 기록", expanded=False):
        events = visible_events
        for event in events:
            st.json(to_dicts([event])[0])
        if all(result["match"] for result in results.values()):
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
    fig = go.Figure(go.Scatter(x=[o/1000 for o in ovhs], y=rates, mode="lines+markers",
                              line={"color": ACCENT}))
    fig.update_layout(height=260, xaxis_title="중계 추가 지연 (µs)", yaxis_title="RTT 거부율",
                      paper_bgcolor=PANEL, plot_bgcolor=PANEL, font={"family": MONO_FONT, "color": TEXT},
                      xaxis={"gridcolor": GRID}, yaxis={"gridcolor": GRID},
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
    fig2.add_trace(go.Scatter(x=sigmas, y=gacc, mode="lines+markers", name="정상 아군",
                             line={"color": ACCENT}))
    fig2.add_trace(go.Scatter(x=sigmas, y=racc, mode="lines+markers", name="이전 window 재현",
                             line={"color": ACCENT, "dash": "dot"}, marker={"symbol": "diamond"}))
    fig2.update_layout(height=260, xaxis_title="관측 노이즈 σ (deg)", yaxis_title="수락률",
                       paper_bgcolor=PANEL, plot_bgcolor=PANEL, font={"family": MONO_FONT, "color": TEXT},
                       xaxis={"gridcolor": GRID}, yaxis={"gridcolor": GRID},
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True, key="maneuver")

    st.subheader("(c) 아군 목록 크기 대 C2 오수락률 (해석적)")
    p = random_match_prob(k=K)
    ms = [1, 5, 10, 25, 50, 100, 200]
    fa = [1 - (1 - p) ** m for m in ms]
    fig3 = go.Figure(go.Bar(x=[str(m) for m in ms], y=fa, marker={"color": ACCENT}))
    fig3.update_layout(height=240, xaxis_title="아군 목록 크기", yaxis_title="오수락 확률(≥1건)",
                       paper_bgcolor=PANEL, plot_bgcolor=PANEL, font={"family": MONO_FONT, "color": TEXT},
                       xaxis={"gridcolor": GRID}, yaxis={"gridcolor": GRID},
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True, key="listsize")
    st.caption(f"단위 오수락 확률 p = {p:.4f} (n={config.MANEUVER_BITS}, K={K}). "
               "목록이 커질수록 C2 단독 식별은 신뢰도가 떨어진다 → C1 확인 필요.")


with tab5:
    render_attacker_cost_panel(Path(__file__).resolve().parent / "out")
