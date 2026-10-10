from typing import Final

import streamlit as st

BACKGROUND: Final = "#0b1118"
PANEL: Final = "#111c28"
GRID: Final = "#2b3b4e"
TEXT: Final = "#e5edf5"
MUTED: Final = "#9aafc4"
ACCEPT: Final = "#51d69a"
REJECT: Final = "#ff7a86"
ACCENT: Final = "#81b7ee"
WAITING: Final = "#78899c"


def apply_console_style() -> None:
    st.markdown(f"""
    <style>
    :root {{ --console-panel: {PANEL}; --console-text: {TEXT};
             --console-muted: {MUTED}; --console-pass: {ACCEPT};
             --console-fail: {REJECT}; --console-wait: {WAITING}; }}
    .block-container {{ max-width: 1440px; padding-top: 2rem; }}
    h1 {{ font-size: 2rem !important; letter-spacing: -.03em; }}
    h1, h2, h3, p {{ word-break: keep-all; overflow-wrap: anywhere; }}
    [data-testid="stMetricValue"] {{ font-variant-numeric: tabular-nums; }}
    [data-testid="stMetric"] {{ padding: 1rem; border-radius: .5rem;
        background: var(--secondary-background-color); }}
    .console-row {{ padding: .75rem 0; border-bottom: 1px solid {GRID};
        overflow-wrap: anywhere; line-height: 1.6; }}
    .console-badge {{ display: inline-block; padding: .125rem .5rem;
        border-radius: .25rem; font-size: .875rem; font-weight: 600;
        background: var(--console-panel); color: var(--console-text); }}
    .console-badge.accept, .step.pass {{ color: var(--console-pass); }}
    .console-badge.reject, .console-badge.high, .step.fail {{ color: var(--console-fail); }}
    .console-badge.medium {{ color: #edc56b; }}
    .console-badge.low {{ color: {ACCENT}; }}
    .console-badge.neutral {{ color: var(--console-muted); }}
    .brief-unverified {{ color: var(--text-color); opacity: .6; }}
    .brief-finding {{ line-height: 1.6; word-break: keep-all; overflow-wrap: anywhere; }}
    .st-key-experiments [data-testid="stCaptionContainer"] * {{
        word-break: keep-all; overflow-wrap: anywhere; }}
    .st-key-situation_briefing [data-testid="stText"] span,
    .st-key-situation_briefing p {{ word-break: keep-all !important; overflow-wrap: anywhere; white-space: normal; }}
    .step {{ display: flex; justify-content: space-between; gap: .5rem;
        padding: .5rem .75rem; margin-bottom: .25rem; border-radius: .25rem;
        background: var(--console-panel); font-size: .875rem; }}
    .step.wait {{ color: var(--console-wait); }}
    @media (max-width: 640px) {{
        .block-container {{ padding: 4rem 1rem 1rem; }}
        h1 {{ font-size: 1.5rem !important; }}
        .st-key-kpi_strip [data-testid="stHorizontalBlock"] {{
            display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .5rem; }}
        .st-key-kpi_strip [data-testid="stColumn"] {{ width: 100%; min-width: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)
