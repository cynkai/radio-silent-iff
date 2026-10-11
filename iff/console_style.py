from typing import Final

import streamlit as st

BACKGROUND: Final = "#0b1118"
PANEL: Final = "#111c28"
GRID: Final = "#2b3b4e"
TEXT: Final = "#e5edf5"
MUTED: Final = "#9aafc4"
ACCEPT: Final = "#51d69a"
REJECT: Final = "#ff7a86"
ACCENT: Final = "#5ad4e6"
WAITING: Final = MUTED
BODY_FONT: Final = "IBM Plex Sans KR, sans-serif"
MONO_FONT: Final = "IBM Plex Mono, IBM Plex Sans KR, monospace"


def apply_console_style() -> None:
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap');
    :root {{ --console-panel: {PANEL}; --console-text: {TEXT};
             --console-muted: {MUTED}; --console-pass: {ACCEPT};
             --console-fail: {REJECT}; --console-wait: {WAITING}; }}
    .stApp {{ background: {BACKGROUND}; color: {TEXT}; }}
    .stApp, .stApp p, .stApp label, .stApp button, .stApp input,
    [data-testid="stText"],
    .stApp h1, .stApp h2, .stApp h3, .disclosure, .alert-title, .console-row {{ font-family: {BODY_FONT}; }}
    [data-testid="stHeader"], [data-testid="stToolbar"], [id="MainMenu"], footer {{ display: none; }}
    .block-container {{ max-width: 1440px; padding: 1rem 2.5rem 2rem; }}
    [data-testid="stVerticalBlock"] {{ gap: .5rem; }}
    [data-testid="stMarkdownContainer"] {{ margin-bottom: 0; }}
    [data-testid="stMarkdownContainer"] p {{ margin-bottom: 0; }}
    h1 {{ font-size: 1.75rem !important; letter-spacing: -.03em; padding: 0 !important; }}
    h2, h3 {{ font-size: 1.2rem !important; padding: .25rem 0 !important; }}
    h1, h2, h3, p {{ word-break: keep-all; overflow-wrap: anywhere; }}
    [data-testid="stHeading"] [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"]:has(> .masthead),
    [data-testid="stMarkdownContainer"]:has(> .console-row),
    [data-testid="stMarkdownContainer"]:has(> .step),
    [data-testid="stMarkdownContainer"]:has(> .mono) {{ margin-bottom: 0; }}
    .masthead .disclosure {{ margin-bottom: .5rem; }}
    .masthead h1 {{ margin-bottom: .25rem; }}
    .disclosure {{ color: {MUTED}; background: {GRID}; padding: .25rem .75rem;
        font-size: .75rem; line-height: 1.5; border-radius: .25rem; }}
    .value-proposition {{ color: {TEXT}; font-size: 1rem; margin: 0; }}
    .st-key-quick_guide [data-testid="stVerticalBlock"] {{ gap: .25rem; }}
    .st-key-quick_guide button {{ border-color: {GRID}; min-height: 2.5rem; }}
    .st-key-quick_guide button:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
    .st-key-kpi_strip [data-testid="stColumn"] {{ background: {PANEL};
        border: 1px solid transparent; border-radius: .5rem; padding: .5rem 1rem; }}
    .st-key-kpi_strip [data-testid="stColumn"]:last-child {{ border-color: {REJECT}; }}
    .st-key-kpi_strip [data-testid="stVerticalBlock"] {{ gap: .125rem; }}
    [data-testid="stMetric"] {{ padding: 0; }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] p, code, pre, .mono,
    [data-testid="stNumberInput"] input, .step span:first-child, .alert-original {{
        font-family: {MONO_FONT} !important; font-variant-numeric: tabular-nums; }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] p {{ font-size: 1.75rem; line-height: 1.2; }}
    .st-key-kpi_strip [data-testid="stColumn"]:nth-child(2) [data-testid="stMetricValue"] {{ color: {ACCEPT}; }}
    .st-key-kpi_strip [data-testid="stColumn"]:nth-child(3) [data-testid="stMetricValue"],
    .st-key-kpi_strip [data-testid="stColumn"]:nth-child(4) [data-testid="stMetricValue"] {{ color: {REJECT}; }}
    [data-testid="stCaptionContainer"] {{ color: {MUTED}; }}
    [data-testid="stAlertContainer"] {{ background: {PANEL}; }}
    [data-testid="stAlertContentInfo"] {{ color: {ACCENT}; }}
    [data-testid="stAlertContentError"] {{ color: {REJECT}; }}
    [data-testid="stAlertContentSuccess"] {{ color: {ACCEPT}; }}
    .st-key-kpi_strip [data-testid="stCaptionContainer"] p {{ font-size: .75rem; }}
    [role="tablist"] {{ gap: 1.5rem; }}
    [role="tab"] {{ height: 2.5rem; }}
    [role="tabpanel"] {{ padding-top: .5rem; }}
    [data-testid="stRadio"] > label {{ margin-bottom: .125rem; }}
    .alert-title {{ font-size: 1.1rem; font-weight: 600; margin: .25rem 0 .5rem; }}
    .alert-original {{ color: {MUTED}; font-size: .8rem; line-height: 1.6;
        overflow-wrap: anywhere; margin-top: .25rem; }}
    .console-row {{ padding: .75rem 0; border-bottom: 1px solid {GRID};
        overflow-wrap: anywhere; line-height: 1.6; }}
    .console-badge {{ display: inline-block; padding: .125rem .5rem;
        border-radius: .25rem; font-size: .875rem; font-weight: 600;
        background: var(--console-panel); color: var(--console-text); }}
    .console-badge.accept, .step.pass {{ color: var(--console-pass); }}
    .console-badge.reject, .console-badge.high, .step.fail {{ color: var(--console-fail); }}
    .console-badge.medium {{ color: {ACCENT}; }}
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
    [data-testid="stSelectbox"] input {{ font-family: {MONO_FONT}; font-variant-numeric: tabular-nums; }}
    .js-plotly-plot {{ border-radius: .5rem; overflow: hidden; }}
    .st-key-motion_protocol iframe {{ height: 360px; }}
    .st-key-motion_pipeline iframe {{ height: 330px; }}
    .st-key-motion_radar iframe {{ height: 560px; }}
    .st-key-motion_radar [data-testid="stElementContainer"] {{ height: 560px !important; }}
    .st-key-motion_protocol [data-testid="stElementContainer"] {{ height: 360px !important; }}
    button:focus-visible {{ outline: 2px solid {ACCENT}; outline-offset: 2px; }}
    @media (max-width: 640px) {{
        .st-key-motion_radar iframe {{ height: 530px; }}
        .st-key-motion_radar [data-testid="stElementContainer"] {{ height: 530px !important; }}
        .st-key-motion_pipeline iframe {{ height: 510px; }}
        .st-key-motion_pipeline [data-testid="stElementContainer"] {{ height: 510px !important; }}
        .st-key-motion_protocol iframe {{ height: 510px; }}
        .st-key-motion_protocol [data-testid="stElementContainer"] {{ height: 510px !important; }}
        .block-container {{ padding: 1rem 1rem 1rem; }}
        h1 {{ font-size: 1.5rem !important; }}
        [data-testid="stHorizontalBlock"] {{ flex-direction: column; gap: 1rem; }}
        [data-testid="stCaptionContainer"] p {{ font-size: .75rem; }}
        [data-testid="stColumn"] {{ min-width: 0; width: 100% !important; flex: 1 1 auto !important; }}
        [role="tablist"] {{ flex-wrap: wrap; gap: .25rem .75rem; overflow: visible; }}
        [role="tab"] {{ height: 2.25rem; white-space: normal; }}
        .react-aria-SelectionIndicator {{ display: none; }}
        [role="tab"][aria-selected="true"] {{ border-bottom: 2px solid {ACCENT}; }}
        .st-key-quick_guide [data-testid="stHorizontalBlock"] {{ gap: .25rem; }}
        .st-key-kpi_strip [data-testid="stHorizontalBlock"] {{
            display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .5rem; }}
        .st-key-kpi_strip [data-testid="stColumn"] {{ width: 100%; min-width: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)
