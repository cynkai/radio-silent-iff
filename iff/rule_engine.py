from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TypedDict, assert_never

from .rule_config import EventRule, PairRule, Rule, WindowRule


Scalar = str | int | float | None
EventRecord = Mapping[str, Scalar]


class Alert(TypedDict):
    rule: str
    severity: str
    message: str
    evidence: list[Scalar]


class EventNumberError(TypeError):
    def __init__(self, field: str, value: Scalar) -> None:
        self.field = field
        self.value = value
        super().__init__(f"{field} must be numeric, got {value!r}")


def _number(event: EventRecord, field: str) -> int | float:
    value = event[field]
    if isinstance(value, (int, float)):
        return value
    raise EventNumberError(field, value)


def _matches(event: EventRecord, fields: Mapping[str, str]) -> bool:
    return all(event.get(field) == expected for field, expected in fields.items())


def _alert(rule_id: str, severity: str, message: str, evidence: Sequence[EventRecord]) -> Alert:
    return {
        "rule": rule_id,
        "severity": severity,
        "message": message.replace("{unit_id}", str(evidence[0].get("unit_id"))),
        "evidence": [event.get("ts_ns") for event in evidence],
    }


def _event_alerts(rule: EventRule, events: Sequence[EventRecord], budget: float) -> list[Alert]:
    alerts = []
    for event in events:
        for case in rule.cases:
            if not _matches(event, case.match):
                continue
            fraction = case.rtt_above_budget_fraction
            if fraction is not None and (
                event.get("rtt_ns") is None or not _number(event, "rtt_ns") > fraction * budget
            ):
                continue
            alerts.append(_alert(rule.id, case.severity, case.message, [event]))
            break
    return alerts


def _pair_alerts(rule: PairRule, events: Sequence[EventRecord]) -> list[Alert]:
    groups: defaultdict[tuple[Scalar, ...], list[EventRecord]] = defaultdict(list)
    for event in events:
        if _matches(event, rule.match):
            groups[tuple(event.get(field) for field in rule.group_by)].append(event)
    alerts = []
    for group in groups.values():
        for index, first in enumerate(group):
            for second in group[index + 1:]:
                if any(abs(_number(first, field) - _number(second, field)) > limit
                       for field, limit in rule.difference_gt.items()):
                    alerts.append(_alert(rule.id, rule.severity, rule.message, [first, second]))
    return alerts


def _window_alerts(rule: WindowRule, events: Sequence[EventRecord]) -> list[Alert]:
    selected = sorted(
        (event for event in events if _matches(event, rule.match)),
        key=lambda event: _number(event, "ts_ns") if "ts_ns" in event else 0,
    )
    for anchor in selected:
        burst = [anchor]
        for other in selected:
            if other is anchor:
                continue
            if (abs(_number(other, "bearing_deg") - _number(anchor, "bearing_deg"))
                    <= rule.bearing_tolerance_deg
                    and 0 <= _number(other, "ts_ns") - _number(anchor, "ts_ns") <= rule.window_ns):
                burst.append(other)
        if len(burst) >= rule.min_count:
            return [_alert(rule.id, rule.severity, rule.message, burst)]
    return []


def evaluate(rules: Sequence[Rule], events: Sequence[EventRecord], budget: float) -> list[Alert]:
    """Evaluate event, pair, and first-window rules while preserving evidence order."""
    alerts = []
    for rule in rules:
        match rule:
            case EventRule():
                alerts.extend(_event_alerts(rule, events, budget))
            case PairRule():
                alerts.extend(_pair_alerts(rule, events))
            case WindowRule():
                alerts.extend(_window_alerts(rule, events))
            case unreachable:
                assert_never(unreachable)
    return alerts
