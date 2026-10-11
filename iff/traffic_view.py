from collections.abc import Sequence

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .console_style import ACCENT, GRID, MONO_FONT, PANEL, REJECT, TEXT
from .traffic import Measurement, Performance, Traffic


def traffic_until(traffic: Traffic, timestamp: int) -> Traffic:
    return Traffic(tuple(event for event in traffic.events if event.ts_ns <= timestamp),
                   tuple(item for item in traffic.truth if item.ts_ns <= timestamp))


def performance_figure(metrics: Sequence[Performance], measurements: Sequence[Measurement], rule: str) -> go.Figure:
    figure = make_subplots(rows=2, cols=1, vertical_spacing=.27,
                           subplot_titles=("룰별 탐지율 · 오탐률", f"BER 대비 오탐 · {rule.split('_')[0]}"))
    names = [item.rule.split("_")[0] if item.rule != "ANY_RULE" else "ALL" for item in metrics]
    figure.add_trace(go.Bar(x=names, y=[item.detection_rate for item in metrics],
                           name="탐지율", marker_color=ACCENT), row=1, col=1)
    figure.add_trace(go.Bar(x=names, y=[item.false_positive_rate for item in metrics],
                           name="오탐률", marker_color=REJECT), row=1, col=1)
    index = next(index for index, item in enumerate(metrics) if item.rule == rule)
    rates = [row.metrics[index].false_positive_rate for row in measurements]
    figure.add_trace(go.Scatter(x=[row.ber for row in measurements], y=rates,
                               mode="lines+markers", line_color=ACCENT, showlegend=False,
                               hovertemplate="BER %{x}<br>오탐률 %{y:.2%}<extra></extra>"), row=2, col=1)
    figure.update_layout(height=560, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                         font={"family": MONO_FONT, "color": TEXT}, barmode="group",
                         margin={"l": 52, "r": 16, "t": 45, "b": 50},
                         legend={"orientation": "h", "y": 1.1, "x": 0},
                         annotations=[dict(annotation, font={"size": 13}) for annotation in figure.to_dict()["layout"]["annotations"]])
    figure.update_xaxes(gridcolor=GRID, tickfont={"size": 11})
    figure.update_xaxes(title="비트오류율 (BER)", row=2, col=1)
    figure.update_yaxes(gridcolor=GRID, tickformat=".0%", range=[0, 1.05], row=1, col=1)
    figure.update_yaxes(gridcolor=GRID, tickformat=".1%", range=[0, max(max((rate or 0 for rate in rates), default=0) * 1.2, .01)], row=2, col=1)
    return figure
