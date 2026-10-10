from collections.abc import Sequence
from math import cos, radians

import plotly.graph_objects as go

from . import config
from .console_style import ACCEPT, ACCENT, GRID, MUTED, PANEL, REJECT, TEXT
from .events import Event


def radar_figure(events: Sequence[Event]) -> go.Figure:
    figure = go.Figure()
    for component, symbol in (("C1", "circle"), ("C2", "diamond"), ("CQ", "circle")):
        for decision, color, label in (("ACCEPT_FRIEND", ACCEPT, "수락"),
                                       ("REJECT", REJECT, "거부"),
                                       ("NO_RESPONSE", MUTED, "무응답")):
            points = [(index, event) for index, event in enumerate(events)
                      if event.component == component and event.decision == decision]
            if not points:
                continue
            figure.add_trace(go.Scatterpolar(
                r=[event.range_m for _, event in points],
                theta=[event.bearing_deg for _, event in points],
                mode="markers", name=f"{component} · {label}",
                marker={"color": color, "symbol": "x" if decision == "NO_RESPONSE" else symbol, "size": 13,
                        "line": {"color": PANEL, "width": 1}},
                customdata=[[index + 1, event.scenario, event.reject_stage or "통과",
                             "해당 없음" if event.rtt_ns is None else f"{event.rtt_ns / 1000:.3f} µs"]
                            for index, event in points],
                hovertemplate="#%{customdata[0]} · %{customdata[1]}<br>"
                              "방위 %{theta}° · 거리 %{r} m<br>"
                              "reject_stage: %{customdata[2]}<br>RTT: %{customdata[3]}<extra>%{fullData.name}</extra>",
            ))
    labels: dict[tuple[float, float], list[str]] = {}
    for event in events:
        names = labels.setdefault((event.range_m, event.bearing_deg), [])
        if event.scenario not in names:
            names.append(event.scenario)
    figure.add_trace(go.Scatterpolar(
        r=[point[0] for point in labels], theta=[point[1] for point in labels],
        mode="text", text=[" / ".join(names) for names in labels.values()],
        textposition=["bottom center" if any(
            radius ** 2 + prior_radius ** 2 - 2 * radius * prior_radius
            * cos(radians(angle - prior_angle)) < 40 ** 2
            for prior_radius, prior_angle in list(labels)[:index]) else "top center"
            for index, (radius, angle) in enumerate(labels)],
        textfont={"size": 12, "color": TEXT},
        showlegend=False, hoverinfo="skip",
    ))
    figure.add_trace(go.Scatterpolar(
        r=[0], theta=[0], mode="markers", name="질의기",
        marker={"symbol": "cross", "size": 12, "color": ACCENT},
        hovertemplate="질의기 · 원점<extra></extra>",
    ))
    radial_max = max((event.range_m for event in events), default=config.DEFAULT_D_MAX_M)
    figure.update_layout(
        height=480, paper_bgcolor=PANEL, font={"color": TEXT},
        margin={"l": 48, "r": 48, "t": 32, "b": 48},
        legend={"orientation": "h", "y": -0.13, "font": {"size": 12}},
        polar={"bgcolor": PANEL,
               "radialaxis": {"range": [0, radial_max * 1.15], "gridcolor": GRID,
                              "linecolor": GRID, "tickfont": {"color": MUTED}},
               "angularaxis": {"rotation": 90, "direction": "clockwise",
                               "gridcolor": GRID, "linecolor": GRID,
                               "ticksuffix": "°", "tickfont": {"color": MUTED}}},
    )
    return figure


def rtt_figure(event: Event) -> go.Figure:
    budget_us = config.rtt_budget_ns(config.DEFAULT_D_MAX_M) / 1000
    rtt_us = event.rtt_ns / 1000 if event.rtt_ns is not None else 0
    figure = go.Figure(go.Indicator(
        mode="number+gauge", value=rtt_us, number={"suffix": " µs", "font": {"size": 24}},
        gauge={"shape": "bullet", "axis": {"range": [0, max(budget_us, rtt_us) * 1.15]},
               "bar": {"color": REJECT if rtt_us > budget_us else ACCEPT},
               "bgcolor": GRID, "threshold": {"value": budget_us,
                                               "line": {"color": TEXT, "width": 2}}},
    ))
    figure.update_layout(height=160, paper_bgcolor=PANEL, font={"color": TEXT},
                         title={"text": f"RTT / 예산 {budget_us:.3f} µs", "x": .06,
                                "font": {"size": 14}},
                         margin={"l": 24, "r": 64, "t": 48, "b": 32})
    return figure


def timeline_figure(events: Sequence[Event]) -> go.Figure:
    epoch = min(event.epoch for event in events)
    expiry = epoch + config.EPOCH_GRACE + 1
    figure = go.Figure()
    figure.add_vrect(x0=epoch + 1, x1=expiry, fillcolor=ACCENT, opacity=.15,
                     line_width=0, annotation_text="EPOCH_GRACE · 유예", annotation_position="top left")
    figure.add_vrect(x0=epoch, x1=epoch + 1, fillcolor=ACCEPT, opacity=.06, line_width=0)
    for scenario in ("S4", "S8"):
        points = [event for event in events if event.scenario == scenario]
        verifier_epochs = [epoch + 1 if scenario == "S8" else event.epoch for event in points]
        labels = [event.reject_stage or "ACCEPT" for event in points]
        figure.add_trace(go.Scatter(
            x=verifier_epochs, y=[f"{scenario} · 응답 {index + 1}" for index in range(len(points))],
            mode="markers+text", text=labels, textposition="middle right", name=scenario,
            marker={"size": 13, "color": [ACCEPT if event.decision == "ACCEPT_FRIEND" else REJECT
                                          for event in points]},
            customdata=[[event.epoch, event.ts_ns, event.decision] for event in points],
            hovertemplate="%{y}<br>검증기 epoch %{x}<br>응답 epoch %{customdata[0]}<br>"
                          "이벤트 ts_ns %{customdata[1]}<br>%{customdata[2]} / %{text}<extra></extra>",
        ))
    figure.add_vline(x=expiry, line_color=MUTED, line_dash="dot")
    figure.add_annotation(x=expiry, y=1.12, yref="paper", text="EPOCH · 유예 종료 경계",
                          showarrow=False, xanchor="right", font={"color": MUTED, "size": 12})
    figure.update_layout(
        height=340, paper_bgcolor=PANEL, plot_bgcolor=PANEL, font={"color": TEXT},
        margin={"l": 24, "r": 24, "t": 64, "b": 48}, showlegend=False,
        xaxis={"range": [epoch - .15, max(epoch + 3, expiry + 1)],
               "tickvals": [epoch, epoch + 1, epoch + 2],
               "ticktext": [f"E · {epoch}", f"E+1 · {epoch + 1}", f"E+2 · {epoch + 2}"],
               "title": "검증기 epoch · 구간 내 실제 경과시간을 뜻하지 않음", "gridcolor": GRID},
        yaxis={"autorange": "reversed", "gridcolor": GRID},
    )
    return figure
