from typing import Final

import streamlit as st

from .sandbox import Attack, SandboxInput, run_experiment


PRESETS: Final = (
    ("중계 25µs — 통과(알려진 한계)", SandboxInput(relay_us=25)),
    ("중계 40µs — RTT 차단", SandboxInput(relay_us=40)),
    ("포획 기체 미폐기 — 통과(알려진 한계)", SandboxInput(attack=Attack.CAPTURED)),
    ("가짜 질의기 — 무응답", SandboxInput(attack=Attack.ROGUE)),
)


def select_preset(index: int) -> None:
    inputs = PRESETS[index][1]
    for key, value in (("attack", inputs.attack), ("relay", int(inputs.relay_us)),
                       ("epoch", inputs.elapsed_epochs), ("revoked", inputs.revoked),
                       ("ber", inputs.ber), ("seed", inputs.seed)):
        st.session_state[f"sandbox_{key}"] = value
    st.session_state.sandbox_run = (inputs, run_experiment(inputs))


def render_presets() -> None:
    if "sandbox_run" not in st.session_state:
        select_preset(0)
    st.caption("원클릭 프리셋 · 입력을 채우고 기존 엔진으로 즉시 실행합니다.")
    columns = st.columns(2)
    for index, (label, _) in enumerate(PRESETS):
        columns[index % 2].button(label, key=f"preset_{index}", width="stretch",
                                   on_click=select_preset, args=(index,))
