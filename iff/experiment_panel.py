from dataclasses import asdict
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from .briefing_panel import render_briefing
from .console_charts import radar_figure, rtt_figure
from .console_style import ACCENT, GRID, PANEL, TEXT
from .operator_console import render_alerts
from .rule_engine import Alert
from .sandbox import Attack, PIPELINE, SandboxInput, pipeline_states, run_experiment
from .traffic import (Measurement, Performance, Traffic, TrafficInput, detect_traffic,
                      generate_traffic, measure, sweep)
from .traffic_report import render_traffic_outcomes


def render_sandbox() -> None:
    st.subheader("레드팀 샌드박스")
    st.caption("입력을 구성하고 공격 실행을 누르세요. 기존 프로토콜 엔진의 실제 결과를 표시합니다.")
    with st.form("sandbox_form"):
        attack = st.selectbox("공격 유형", list(Attack), format_func=str, key="sandbox_attack", index=1)
        left, right = st.columns(2)
        relay = left.slider("중계 추가 지연 (µs)", 0, 200, 25, key="sandbox_relay")
        elapsed = right.selectbox("포획 후 경과 epoch", [0, 1, 2], index=1, key="sandbox_epoch")
        revoked = left.checkbox("폐기 여부", key="sandbox_revoked")
        ber = right.number_input("비트오류율 (BER)", 0.0, 1.0, 0.0, 0.001, format="%.3f", key="sandbox_ber")
        seed = left.number_input("시드", min_value=0, value=42, step=1, key="sandbox_seed")
        st.caption("지연은 중계, 경과 epoch는 포획 기체에 적용합니다. BER은 응답 태그에 적용합니다.")
        if st.form_submit_button("공격 실행", type="primary"):
            inputs = SandboxInput(attack=attack, relay_us=relay, elapsed_epochs=elapsed,
                                  revoked=revoked, ber=ber, seed=seed)
            st.session_state.sandbox_run = (inputs, run_experiment(inputs))
    if "sandbox_run" not in st.session_state:
        st.info("아직 실행한 공격이 없습니다.")
        return
    inputs, result = st.session_state.sandbox_run
    event = result.event
    alerts = detect_traffic([event])
    st.caption(f"실행 입력 · {inputs.attack} · seed={inputs.seed} · BER={inputs.ber:g} · "
               f"지연={inputs.relay_us:g}µs · 경과={inputs.elapsed_epochs}epoch · 폐기={inputs.revoked}")
    if inputs.attack != Attack.BENIGN and event.decision == "ACCEPT_FRIEND":
        st.error("방어 실패 — 알려진 한계")
        st.markdown("[README · 가정과 한계](?workspace=experiments&limits=1#experiment-limits)")
    st.write(f"**엔진 판정: {event.decision} · {event.reject_stage or 'ACCEPT'}**")
    pipeline, timing = st.columns(2)
    with pipeline:
        st.markdown("**6단계 검증 파이프라인**")
        for stage, status in zip(PIPELINE, pipeline_states(event)):
            state = {"통과": "pass", "차단": "fail", "미도달": "wait"}[status]
            st.markdown(f'<div class="step {state}"><span>{stage}</span><span>{status}</span></div>',
                        unsafe_allow_html=True)
    with timing:
        if event.rtt_ns is None:
            st.info(f"RTT 미측정 · {event.reject_stage}에서 차단")
            st.caption("응답이 없거나 RTT 단계에 도달하지 않았습니다. 임의 RTT를 표시하지 않습니다.")
        else:
            st.plotly_chart(rtt_figure(event), width="stretch", key="sandbox_rtt", theme=None)
            st.caption(f"검증 RTT {event.rtt_ns / 1000:.3f}µs / 예산 {result.budget_ns / 1000:.3f}µs")
    st.markdown("**탐지 경보**")
    render_alerts(alerts)
    render_briefing([event], alerts, key="sandbox_brief", show_example=False)
    with st.expander("엔진 원본 이벤트"):
        st.json(asdict(event))


@st.cache_data(show_spinner=False, max_entries=16)
def traffic_report(inputs: TrafficInput) -> tuple[Traffic, list[Alert], tuple[Performance, ...],
                                                 tuple[Measurement, ...]]:
    traffic = generate_traffic(inputs)
    alerts = detect_traffic(traffic.events)
    return traffic, alerts, measure(traffic, alerts), sweep(inputs)


def render_traffic() -> None:
    st.subheader("교전 트래픽")
    st.caption("시드 기반 혼합 트래픽 · 정답 라벨은 탐지 후 채점에만 사용합니다.")
    with st.form("traffic_form"):
        left, right = st.columns(2)
        benign = left.number_input("정상 아군 N", min_value=0, max_value=5000, value=200, key="traffic_n")
        attacks = right.number_input("공격 M", min_value=0, max_value=5000, value=100, key="traffic_m")
        seed = left.number_input("트래픽 시드", min_value=0, value=42, step=1, key="traffic_seed")
        ber = right.number_input("트래픽 BER", 0.0, 1.0, 0.0, 0.001, format="%.3f", key="traffic_ber")
        if st.form_submit_button("트래픽 생성", type="primary"):
            st.session_state.traffic_input = TrafficInput(benign=benign, attacks=attacks, seed=seed, ber=ber)
    if "traffic_input" not in st.session_state:
        st.info("트래픽 생성을 누르면 레이더와 성능 측정 결과를 표시합니다.")
        return
    inputs = st.session_state.traffic_input
    with st.spinner("엔진으로 교전과 BER 스윕 실행 중…"):
        traffic, alerts, metrics, measurements = traffic_report(inputs)
    st.caption(f"실행 입력 · N={inputs.benign} · M={inputs.attacks} · seed={inputs.seed} · BER={inputs.ber:g}")
    st.write(f"엔진 이벤트 {len(traffic.events)}건 · 수락 "
             f"{sum(event.decision == 'ACCEPT_FRIEND' for event in traffic.events)}건 · 경보 {len(alerts)}건")
    figure = radar_figure(traffic.events)
    figure.data = tuple(trace for trace in figure.data if trace.mode != "text")
    st.plotly_chart(figure, width="stretch", key="traffic_radar", theme=None)
    render_traffic_outcomes(traffic, alerts)
    st.markdown("**룰별 경보 성능**")
    st.caption("경보 근거의 고유 이벤트 단위. TP·FN 분모는 모든 공격 M건, FP·TN 분모는 정상 N건입니다. "
               "ANY_RULE은 중복 제거한 합집합입니다. detection_rate는 경보율이며 차단율이 아닙니다. "
               "해당 표본이 없으면 비율은 비어 있습니다.")
    st.dataframe([asdict(row) for row in metrics], hide_index=True, width="stretch")
    st.markdown("**BER 대비 오탐 곡선**")
    chart = go.Figure()
    for index, metric in enumerate(metrics):
        chart.add_trace(go.Scatter(x=[row.ber for row in measurements],
                                  y=[row.metrics[index].false_positive_rate for row in measurements],
                                  mode="lines+markers", name=metric.rule.split("_")[0],
                                  visible=True if metric.rule == "ANY_RULE" else "legendonly"))
    peak = max((metric.false_positive_rate or 0 for row in measurements for metric in row.metrics), default=0)
    chart.update_layout(height=360, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                        font={"color": TEXT}, colorway=[ACCENT],
                        legend={"orientation": "h", "y": -0.35},
                        xaxis={"title": "비트오류율 (BER)", "gridcolor": GRID},
                        yaxis={"title": "오탐률", "range": [0, max(peak * 1.2, 0.01)],
                               "tickformat": ".1%", "gridcolor": GRID},
                        margin={"l": 64, "r": 16, "t": 16, "b": 88})
    st.plotly_chart(chart, width="stretch", key="traffic_ber_curve", theme=None)
    st.caption("동일 시드·기하·공격 구성을 유지한 paired sweep입니다. 유한 표본과 창 기반 룰 특성상 "
               "곡선은 단조 증가를 보장하지 않습니다. 범례를 누르면 룰별 곡선을 볼 수 있습니다.")
    with st.expander("스윕 측정값 / 이벤트 / 정답 sidecar"):
        st.dataframe([{**asdict(metric), "ber": row.ber} for row in measurements
                      for metric in row.metrics], hide_index=True)
        st.dataframe([asdict(event) for event in traffic.events], hide_index=True)
        st.dataframe([asdict(item) for item in traffic.truth], hide_index=True)
    with st.expander("탐지 경보 원문"):
        render_alerts(alerts)


def render_experiments() -> None:
    sandbox, traffic = st.tabs(["레드팀 샌드박스", "교전 트래픽"])
    with sandbox:
        render_sandbox()
    with traffic:
        render_traffic()
    if st.query_params.get("limits") == "1":
        st.header("README · 가정과 한계", anchor="experiment-limits")
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
        st.markdown(readme.split("<!-- experiment-limits -->")[1])
