import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

import streamlit.components.v1 as components
import streamlit as st

from . import config
from .events import Event
from .sandbox import pipeline_states
from .rule_engine import Alert


def event_payload(event: Event) -> dict[str, object]:
    return {**asdict(event), "budget_ns": config.rtt_budget_ns(config.DEFAULT_D_MAX_M),
            "states": list(pipeline_states(event))}


def render_motion(kind: str, data: object, *, height: int = 340) -> None:
    assets = Path(__file__).with_name("visuals")
    encoded = json.dumps({"kind": kind, "data": data}, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    document = (assets / "frame.html").read_text(encoding="utf-8")
    document = document.replace("__STYLE__", (assets / "motion.css").read_text(encoding="utf-8"))
    document = document.replace("__DATA__", encoded)
    document = document.replace("__SCRIPT__", (assets / "motion.js").read_text(encoding="utf-8"))
    with st.container(key=f"motion_{kind}"):
        components.html(document, height=height, scrolling=False)


def render_protocol(event: Event) -> None:
    render_motion("protocol", event_payload(event), height=340)


def render_pipeline_motion(event: Event) -> None:
    render_motion("pipeline", event_payload(event), height=330)


def render_radar_motion(events: Sequence[Event], alerts: Sequence[Alert], selected: int | None = None) -> None:
    contacts = []
    labels: dict[tuple[float, float], list[str]] = {}
    severity_rank = {"low": 1, "medium": 2, "high": 3}
    for index, event in enumerate(events):
        severity = max((alert["severity"] for alert in alerts if event.ts_ns in alert["evidence"]),
                       key=lambda value: severity_rank[value], default="")
        contacts.append({**asdict(event), "id": index + 1, "severity": severity,
                         "symbol": "x" if event.decision == "NO_RESPONSE" else "diamond" if event.component == "C2" else "circle",
                         "decision_label": {"ACCEPT_FRIEND": "수락", "REJECT": "거부", "NO_RESPONSE": "무응답"}[event.decision]})
        names = labels.setdefault((event.range_m, event.bearing_deg), [])
        if event.scenario not in names:
            names.append(event.scenario)
    render_motion("radar", {"events": contacts, "selected": selected,
                  "labels": [{"r": radius, "theta": angle, "text": " / ".join(names)}
                             for (radius, angle), names in labels.items()],
                  "radialaxis": {"max": max((event.range_m for event in events), default=config.DEFAULT_D_MAX_M)}}, height=530)
