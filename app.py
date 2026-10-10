"""Radio-silent IFF — simulation dashboard (D4D x EDTH, Track 1 / Problem 04).

Run:  streamlit run app.py
"""
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iff import scenarios, detect, config, channel  # noqa: E402
from iff.events import to_dicts  # noqa: E402
from iff.maneuver import (expected_bits, generate_yaw_series, observe,  # noqa: E402
                          recover_bits, hamming, random_match_prob)
from iff.protocol import Interrogator, make_response  # noqa: E402
from iff.attacker_cost import captured_window_text
from iff.attacker_cost_panel import render_attacker_cost_panel

st.set_page_config(page_title="Radio-silent IFF — simulation", layout="wide")

st.warning("⚠️ 시뮬레이션 — 실기체·실채널 측정값이 아닙니다. "
           "모든 암호는 표준 공개 기법(HKDF/HMAC, RFC 5869)이며 하드웨어는 없습니다.")
st.title("전파 최소화 피아식별(IFF) — 2-컴포넌트 시뮬레이션")

# ---- sidebar ----
sb = st.sidebar
sb.header("파라미터")
seed = sb.number_input("시드", value=42, step=1)
d_max = sb.slider("d_max (m)", 500, 5000, int(config.DEFAULT_D_MAX_M), 100)
sigma = sb.slider("관측 노이즈 σ (deg)", 0.0, 80.0, 5.0, 1.0)
K = sb.slider("해밍 허용치 K", 0, 6, config.MANEUVER_HAMMING_K)
budget = config.rtt_budget_ns(d_max)
sb.caption(f"RTT 예산 ≈ {budget/1000:.1f} µs  (= 2·d_max/c + 처리 {config.ASSUMPTION_PROC_MAX_NS/1000:.0f} µs)")

STAGES = ["FORMAT", "EPOCH", "REVOKED", "NONCE", "TAG", "RTT"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(["① 시나리오 실행", "② 이벤트 로그",
                                  "③ 포획 기체", "④ 한계 분석", "⑤ 공격자 비용"])


def pipeline_figure(reject_stage, component="C1"):
    stages = STAGES if component == "C1" else ["관측", "비트복원", "해밍≤K"]
    colors = []
    hit = False
    for s in stages:
        if reject_stage is None:
            colors.append("#2e7d32")
        elif s == reject_stage or (component == "C2" and s == "해밍≤K" and reject_stage == "C2_HAMMING"):
            colors.append("#c62828"); hit = True
        elif hit:
            colors.append("#424242")
        else:
            colors.append("#2e7d32")
    fig = go.Figure(go.Bar(x=stages, y=[1] * len(stages), marker_color=colors,
                           text=stages, textposition="inside"))
    fig.update_layout(height=160, showlegend=False, yaxis=dict(visible=False),
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


# ---------------- Tab 1 ----------------
with tab1:
    scenario_functions = {**scenarios.ALL, "S8": scenarios.s8_captured_key_grace}
    scn = st.selectbox("시나리오", list(scenario_functions),
                       format_func=lambda s: {
                           "S1": "S1 — 정상 아군", "S2": "S2 — 재전송",
                           "S3": "S3 — 중계 MITM", "S4": "S4 — 포획 기체",
                           "S5": "S5 — 무작위 위조", "S6": "S6 — 기동 재현(C2)",
                           "S7": "S7 — 복제 기체", "S8": "S8 — 포획 키 유예와 폐기"}[s])
    rng = np.random.default_rng(seed)
    events, expected = scenario_functions[scn](rng)
    for i, e in enumerate(events):
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown(f"**이벤트 {i+1}** · {e.note}")
            st.write({"decision": e.decision, "reject_stage": e.reject_stage,
                      "unit_id": e.unit_id, "epoch": e.epoch,
                      "nonce": e.nonce_hex or "(C2 — nonce 없음)",
                      "rtt_µs": round(e.rtt_ns / 1000, 2) if e.rtt_ns else None})
        with c2:
            st.plotly_chart(pipeline_figure(e.reject_stage, e.component),
                            use_container_width=True, key=f"pipe_{scn}_{i}")
    ok = [(e.decision, e.reject_stage) for e in events] == expected
    if ok:
        st.success(f"기대 결과와 일치: {ok}")
    else:
        st.error("기대 결과 불일치")


# ---------------- Tab 2 ----------------
with tab2:
    results = scenarios.run_all(seed=seed, include_grace=True)
    all_events = [e for r in results.values() for e in r["events"]]
    df = pd.DataFrame(to_dicts(all_events))[
        ["scenario", "component", "decision", "reject_stage",
         "unit_id", "epoch", "bearing_deg", "range_m", "rtt_ns", "note"]]
    st.dataframe(df, use_container_width=True, height=320)
    st.subheader("탐지 경보")
    alerts = detect.run_rules(to_dicts(all_events), revoked_hex=[scenarios.CAP.hex()], d_max_m=d_max)
    sev_color = {"high": "🔴", "medium": "🟠", "low": "🟡"}
    for a in alerts:
        st.markdown(f"{sev_color.get(a['severity'],'⚪')} **{a['rule']}** "
                    f"({a['severity']}) — {a['message']}")


# ---------------- Tab 3 ----------------
with tab3:
    st.subheader("포획된 아군 기체 대응 타임라인")
    rng = np.random.default_rng(seed)
    events, _ = scenarios.s4_captured_unit(rng)
    steps = ["정상 운용 (키 보유)", "포획 → 아군 응답 ACCEPT (위험 구간)",
             "운영자 폐기 등록", "폐기된 unit 재응답 → REVOKED + R3 경보",
             "epoch 회전 → 신규 키 없음 → TAG 실패"]
    labels = ["ACCEPT_FRIEND", "REVOKED", "TAG"]
    st.markdown("1. **" + steps[0] + "**")
    st.markdown("2. **" + steps[1] + f"** — `{events[0].decision}`")
    st.markdown("3. **" + steps[2] + "**")
    st.markdown("4. **" + steps[3] + f"** — `{events[1].decision}/{events[1].reject_stage}`")
    st.markdown("5. **" + steps[4] + f"** — `{events[2].decision}/{events[2].reject_stage}`")
    alerts = detect.run_rules(to_dicts(events), revoked_hex=[scenarios.CAP.hex()], d_max_m=d_max)
    for a in alerts:
        if a["rule"] == "R3_REVOKED_UNIT_ACTIVE":
            st.error(f"🔴 {a['rule']} — {a['message']}")
    st.info(captured_window_text())
    st.caption("S4의 TAG 거부는 새 epoch를 주장하면서 이전 키로 서명한 경우입니다. "
               "이전 epoch를 그대로 제시하는 유예 수락과 즉시 폐기는 S8에서 확인합니다.")


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
