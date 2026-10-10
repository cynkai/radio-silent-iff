import plotly.graph_objects as go
import streamlit as st

from .console_style import ACCEPT, ACCENT, GRID, MONO_FONT, PANEL, REJECT, TEXT
from .experiment_presets import PRESETS
from .sandbox import Attack, PIPELINE, Experiment, SandboxInput, pipeline_states, run_experiment


@st.cache_data(show_spinner=False)
def relay_sweep(seed: int, ber: float) -> tuple[list[Experiment], float]:
    baseline = run_experiment(SandboxInput(relay_us=0, seed=seed))
    assert baseline.event.rtt_ns is not None
    boundary = (baseline.budget_ns - baseline.event.rtt_ns) / 1000
    return [run_experiment(SandboxInput(relay_us=delay, seed=seed, ber=ber))
            for delay in range(201)], boundary


def capture_sweep(revocation: int | None, seed: int, ber: float) -> list[Experiment]:
    return [run_experiment(SandboxInput(attack=Attack.CAPTURED, elapsed_epochs=epoch,
                                       revoked=revocation is not None and epoch >= revocation,
                                       seed=seed, ber=ber)) for epoch in range(3)]


def style_chart(figure: go.Figure, *, height: int = 320) -> go.Figure:
    figure.update_layout(height=height, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                         font={"color": TEXT, "family": MONO_FONT},
                         margin={"l": 48, "r": 20, "t": 30, "b": 64},
                         legend={"orientation": "h", "y": -0.3},
                         xaxis={"gridcolor": GRID}, yaxis={"gridcolor": GRID})
    return figure


def render_deep_sandbox() -> None:
    st.subheader("경계 찾기")
    st.caption("같은 시드로 기존 엔진을 반복 실행합니다. 슬라이더를 움직이면 즉시 다시 계산합니다.")
    seed = st.number_input("심화 시드", min_value=0, value=42, key="deep_seed")
    ber = st.number_input("심화 BER", 0.0, 1.0, 0.0, 0.001, key="deep_ber")
    delay = st.slider("경계 탐색 지연 (µs)", 0, 200, 25, key="deep_delay")
    results, boundary = relay_sweep(seed, ber)
    current = results[delay]
    figure = go.Figure(go.Scatter(x=list(range(201)),
        y=[int(item.event.decision == "ACCEPT_FRIEND") for item in results],
        mode="lines", line={"color": ACCENT}, name="엔진 sweep"))
    figure.add_trace(go.Scatter(x=[delay], y=[int(current.event.decision == "ACCEPT_FRIEND")],
        mode="markers", marker={"size": 17, "color": ACCEPT if current.event.decision == "ACCEPT_FRIEND" else REJECT},
        name="현재 입력"))
    figure.add_vline(x=boundary, line_dash="dash", line_color=TEXT)
    style_chart(figure)
    figure.update_xaxes(title="중계 추가 지연 (µs)")
    figure.update_yaxes(tickvals=[0, 1], ticktext=["차단", "통과"], range=[-.15, 1.15])
    st.plotly_chart(figure, key="deep_relay", width="stretch", theme=None)
    st.write(f"현재 판정 · {current.event.decision} / {current.event.reject_stage or 'ACCEPT'}")
    st.caption(f"점선: RTT 예산 − 기본 왕복 = {boundary:.3f}µs. BER로 인한 앞 단계 차단은 RTT 경계와 별개입니다.")

    st.subheader("포획 기체 타임라인")
    elapsed = st.slider("관찰할 경과 epoch", 0, 2, 1, key="deep_epoch")
    revoked = st.selectbox("폐기 시점", [None, 0, 1, 2],
                           format_func=lambda value: "폐기하지 않음" if value is None else f"E+{value}",
                           key="deep_revocation")
    captures = capture_sweep(revoked, seed, ber)
    timeline = go.Figure()
    for epoch, item in enumerate(captures):
        event = item.event
        color = ACCEPT if event.decision == "ACCEPT_FRIEND" else REJECT
        timeline.add_trace(go.Scatter(x=[epoch, epoch + .95], y=[1, 1], mode="lines",
            line={"color": color, "width": 20}, showlegend=False,
            text=[event.reject_stage or "ACCEPT"] * 2, hovertemplate="%{text}<extra></extra>"))
        timeline.add_annotation(x=epoch + .45, y=1.3, text=event.reject_stage or "ACCEPT", showarrow=False)
    timeline.add_vline(x=elapsed + .45, line_color=ACCENT, line_dash="dot")
    style_chart(timeline, height=240)
    timeline.update_xaxes(tickvals=[.45, 1.45, 2.45], ticktext=["E", "E+1", "E+2"], title="검증기 epoch")
    timeline.update_yaxes(visible=False, range=[.7, 1.6])
    st.plotly_chart(timeline, key="deep_capture", width="stretch", theme=None)
    selected = captures[elapsed].event
    st.write(f"선택 시점 E+{elapsed} · {selected.decision} / {selected.reject_stage or 'ACCEPT'}")

    st.subheader("두 공격 설정 비교")
    st.caption("각 설정을 변경하면 엔진을 실행하고 6단계 결과를 나란히 표시합니다.")
    for index, column in enumerate(st.columns(2)):
        with column:
            preset = st.selectbox(f"설정 {'AB'[index]} 프리셋", range(len(PRESETS)),
                                  index=index, format_func=lambda value: PRESETS[value][0],
                                  key=f"compare_{index}")
            inputs = PRESETS[preset][1]
            relay = st.slider("추가 지연 (µs)", 0, 200, int(inputs.relay_us), key=f"compare_delay_{index}_{preset}") if inputs.attack == Attack.RELAY else inputs.relay_us
            epoch = st.selectbox("경과 epoch", [0, 1, 2], index=inputs.elapsed_epochs, key=f"compare_epoch_{index}_{preset}") if inputs.attack == Attack.CAPTURED else inputs.elapsed_epochs
            revoked = st.checkbox("폐기", key=f"compare_revoked_{index}_{preset}") if inputs.attack == Attack.CAPTURED else False
            compare_ber = st.number_input("BER", 0.0, 1.0, 0.0, .001, key=f"compare_ber_{index}")
            compare_seed = st.number_input("시드", min_value=0, value=42, key=f"compare_seed_{index}")
            result = run_experiment(SandboxInput(attack=inputs.attack, relay_us=relay,
                elapsed_epochs=epoch, revoked=revoked, ber=compare_ber, seed=compare_seed))
            st.write(f"**{result.event.decision} / {result.event.reject_stage or 'ACCEPT'}**")
            for stage, status in zip(PIPELINE, pipeline_states(result.event)):
                state = {"통과": "pass", "차단": "fail", "미도달": "wait"}[status]
                st.markdown(f'<div class="step {state}"><span>{stage}</span><span>{status}</span></div>', unsafe_allow_html=True)
