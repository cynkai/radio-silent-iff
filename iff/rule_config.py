from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import assert_never

import yaml


class RuleKind(Enum):
    EVENT = "event"
    PAIR = "pair"
    WINDOW = "window"


class RuleConfigError(ValueError):
    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}")


@dataclass(frozen=True, slots=True)
class EventCase:
    match: Mapping[str, str]
    severity: str
    message: str
    rtt_above_budget_fraction: float | None = None


@dataclass(frozen=True, slots=True)
class EventRule:
    id: str
    cases: tuple[EventCase, ...]


@dataclass(frozen=True, slots=True)
class PairRule:
    id: str
    match: Mapping[str, str]
    group_by: tuple[str, ...]
    difference_gt: Mapping[str, float]
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class WindowRule:
    id: str
    match: Mapping[str, str]
    bearing_tolerance_deg: float
    window_ns: int
    min_count: int
    severity: str
    message: str


Rule = EventRule | PairRule | WindowRule


def _valid_match(fields: Mapping[str, str]) -> bool:
    return isinstance(fields, dict) and bool(fields) and all(
        isinstance(key, str) and isinstance(value, str) for key, value in fields.items()
    )


def _valid_number(value: float) -> bool:
    return type(value) in (int, float) and isfinite(value) and value >= 0


def _validate(rule: Rule, path: Path) -> None:
    if not isinstance(rule.id, str) or not rule.id:
        raise RuleConfigError(path, "id must be a nonempty string")
    outputs: tuple[EventCase | PairRule | WindowRule, ...]
    match rule:
        case EventRule():
            valid = bool(rule.cases) and all(
                _valid_match(case.match)
                and (case.rtt_above_budget_fraction is None
                     or _valid_number(case.rtt_above_budget_fraction))
                for case in rule.cases
            )
            outputs = rule.cases
        case PairRule():
            valid = (
                _valid_match(rule.match) and bool(rule.group_by)
                and all(isinstance(field, str) for field in rule.group_by)
                and isinstance(rule.difference_gt, dict) and bool(rule.difference_gt)
                and all(isinstance(field, str) and _valid_number(limit)
                        for field, limit in rule.difference_gt.items())
            )
            outputs = (rule,)
        case WindowRule():
            valid = (
                _valid_match(rule.match) and _valid_number(rule.bearing_tolerance_deg)
                and type(rule.window_ns) is int and rule.window_ns >= 0
                and type(rule.min_count) is int and rule.min_count >= 1
            )
            outputs = (rule,)
        case unreachable:
            assert_never(unreachable)
    if not valid:
        raise RuleConfigError(path, "invalid match or correlation parameters")
    if any(output.severity not in ("low", "medium", "high")
           or not isinstance(output.message, str) for output in outputs):
        raise RuleConfigError(path, "invalid severity or message")


def load_rules(directory: Path) -> tuple[Rule, ...]:
    """Load one rule per YAML file in filename order; reject invalid definitions."""
    paths = sorted(directory.glob("*.yaml"))
    if not paths:
        raise RuleConfigError(directory, "no YAML rules found")
    rules: list[Rule] = []
    ids: set[str] = set()
    for path in paths:
        try:
            with path.open(encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
            if not isinstance(data, dict):
                raise RuleConfigError(path, "expected a rule mapping")
            kind = RuleKind(data.pop("kind"))
            match kind:
                case RuleKind.EVENT:
                    cases = data.pop("cases")
                    if not isinstance(cases, list):
                        raise RuleConfigError(path, "cases must be a list")
                    rule: Rule = EventRule(cases=tuple(EventCase(**case) for case in cases), **data)
                case RuleKind.PAIR:
                    fields = data.pop("group_by")
                    if not isinstance(fields, list):
                        raise RuleConfigError(path, "group_by must be a list")
                    rule = PairRule(group_by=tuple(fields), **data)
                case RuleKind.WINDOW:
                    rule = WindowRule(**data)
                case unreachable:
                    assert_never(unreachable)
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            if isinstance(exc, RuleConfigError):
                raise
            raise RuleConfigError(path, str(exc)) from exc
        _validate(rule, path)
        if rule.id in ids:
            raise RuleConfigError(path, f"duplicate rule id: {rule.id}")
        ids.add(rule.id)
        rules.append(rule)
    return tuple(rules)
