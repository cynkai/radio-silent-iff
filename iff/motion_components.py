import json
from dataclasses import asdict
from pathlib import Path

import streamlit.components.v1 as components
import streamlit as st

from . import config
from .events import Event
from .sandbox import pipeline_states


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
