from pathlib import Path

import streamlit as st

from .attacker_cost import cost_csv, probability_text, write_attacker_cost


def render_attacker_cost_panel(out_dir: Path) -> None:
    """Render the same source-derived rows exported to attacker_cost.csv."""
    rows = write_attacker_cost(out_dir)
    st.subheader("공격자 비용 모델")
    st.caption("기본 설정과 저장된 sweep 기준입니다. 사이드바의 실험 파라미터와 별도로 표시합니다.")
    st.write("성공 확률은 조건부 수락 또는 해석적 오수락입니다. 유도할 수 없는 숫자는 비워 두고 미측정으로 표시합니다.")
    st.download_button("공격자 비용 CSV 다운로드", cost_csv(rows), "attacker_cost.csv", "text/csv")
    overview = []
    for scenario in ("S2", "S3", "S4", "S5", "S6"):
        first = next(row for row in rows if row.scenario == scenario)
        success = {"S3": "지연별 상세표", "S4": "폐기 전 조건부 1 / 폐기 후 0",
                   "S6": "편대 크기별 상세표"}.get(scenario, probability_text(first))
        overview.append({"공격": f"{scenario} {first.attack}", "성공 확률": success,
                         "필요 역량": first.capability, "유효 시간": first.valid_window})
    st.dataframe(overview, hide_index=True, width="stretch")
    selected = st.selectbox("공격별 유도와 출처", ["S2", "S3", "S4", "S5", "S6"], index=1,
                            key="cost_attack")
    selected_rows = [row for row in rows if row.scenario == selected]
    first = selected_rows[0]
    st.markdown(f"**{first.scenario} · {first.attack}**")
    st.write(first.probability_note)
    st.markdown(f"**필요 역량** · {first.capability}")
    st.markdown(f"**유효 시간** · {first.valid_window}")
    st.write(first.notes)
    st.dataframe([{"조건": row.condition, "성공 확률": probability_text(row),
                   "유효 시간 상한(초)": "미측정" if row.valid_window_upper_s is None
                   else f"{row.valid_window_upper_s:g}"} for row in selected_rows],
                 hide_index=True, width="stretch")
    st.markdown("**출처**")
    for source in first.source.split("; "):
        st.text(source)
    if not (out_dir / "relay_sweep.csv").exists() or not (out_dir / "list_size.csv").exists():
        st.info("sweep 자료가 없습니다. 아래 명령으로 생성하면 지연별·편대별 값을 표시합니다.")
        st.code("python3 scripts/sweep_noise.py", language="bash")
