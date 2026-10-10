"""Presentation-only accounting of pipeline decisions and rule evidence."""
from collections.abc import Sequence
from typing import Final

import streamlit as st

from .rule_engine import Alert
from .sandbox import Attack
from .traffic import Traffic


BLOCKED: Final = frozenset(("REJECT", "NO_RESPONSE"))
KNOWN_LIMITS: Final = frozenset(("relay", "captured"))


def render_traffic_outcomes(traffic: Traffic, alerts: Sequence[Alert]) -> None:
    """Join truth only for reporting; count each attack once per metric."""
    evidence = {stamp for alert in alerts for stamp in alert["evidence"]}
    events = {event.ts_ns: event for event in traffic.events}
    attacks = [item for item in traffic.truth if item.label != "benign"]
    total = len(attacks)
    blocked = sum(events[item.ts_ns].decision in BLOCKED for item in attacks)
    alerted = sum(item.ts_ns in evidence for item in attacks)
    for label, count in (("차단율", blocked), ("경보율", alerted)):
        rate = f"{count / total:.1%}" if total else "미정 (공격 표본 없음)"
        st.write(f"**{label}: {rate}** · {count}/{total}건")
    st.caption("차단율 = 공격 중 REJECT/NO_RESPONSE 비율. 경보율 = 공격 중 룰 경보 근거가 "
               "하나라도 붙은 비율(중복 제거). 두 지표는 겹치며 합산하지 않습니다.")
    rate = f"{(total - alerted) / total:.1%}" if total else "미정"
    st.markdown(f"**무경보 공격 유형별 분해 · {total - alerted}/{total}건 ({rate})**")
    records = []
    for kind in Attack:
        if kind == Attack.BENIGN:
            continue
        items = [item for item in attacks if item.label == kind.name.lower()
                 and item.ts_ns not in evidence]
        rejected = sum(events[item.ts_ns].decision in BLOCKED for item in items)
        passed = sum(events[item.ts_ns].decision == "ACCEPT_FRIEND"
                     and item.label in KNOWN_LIMITS for item in items)
        records.append({"공격 유형": str(kind), "차단됐지만 룰 없음": rejected,
                        "알려진 한계로 통과": passed, "기타": len(items) - rejected - passed,
                        "무경보 합계": len(items)})
    st.table(records)
    st.caption("알려진 한계: RTT 예산 내 중계 또는 유효 키를 가진 미폐기 포획 기체의 수락. "
               "기타는 앞 두 범주에 해당하지 않는 무경보 공격입니다. 무경보는 통과와 다릅니다.")
