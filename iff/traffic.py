"""Generate labeled exchanges and evaluate labels only after detection."""
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from . import detect
from .events import Event, to_dicts
from .rule_config import load_rules
from .rule_engine import Alert
from .sandbox import Attack, SandboxInput, run_experiment


class TrafficInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    benign: int = Field(default=200, ge=0, le=5000)
    attacks: int = Field(default=100, ge=0, le=5000)
    seed: int = Field(default=42, ge=0)
    ber: float = Field(default=0, ge=0, le=1)


@dataclass(frozen=True, slots=True)
class Truth:
    ts_ns: int
    label: str


@dataclass(frozen=True, slots=True)
class Traffic:
    events: tuple[Event, ...]
    truth: tuple[Truth, ...]


@dataclass(frozen=True, slots=True)
class Performance:
    rule: str
    tp: int
    fp: int
    fn: int
    tn: int
    detection_rate: float | None
    false_positive_rate: float | None


@dataclass(frozen=True, slots=True)
class Measurement:
    ber: float
    metrics: tuple[Performance, ...]


BER_LEVELS: Final = (0.0, 0.001, 0.005, 0.01, 0.03, 0.1, 0.3)


def generate_traffic(inputs: TrafficInput) -> Traffic:
    """Labels stay in a sidecar; every transmitted trial has a unique unit ID."""
    rng = np.random.default_rng(inputs.seed)
    attack_types = tuple(attack for attack in Attack if attack != Attack.BENIGN)
    kinds = [Attack.BENIGN] * inputs.benign + [
        attack_types[int(rng.integers(len(attack_types)))] for _ in range(inputs.attacks)]
    rng.shuffle(kinds)
    events, truth = [], []
    for index, kind in enumerate(kinds):
        params = SandboxInput(attack=kind, seed=int(rng.integers(2**32)),
                              relay_us=float(rng.uniform(0, 200)),
                              elapsed_epochs=int(rng.integers(3)),
                              revoked=kind == Attack.CAPTURED and bool(rng.integers(2)),
                              ber=inputs.ber)
        event = run_experiment(
            params, bearing_deg=float(rng.uniform(0, 360)), range_m=float(rng.uniform(100, 1800)),
            ts_ns=index * 1_000_000_000 + int(rng.integers(900_000_000)),
            unit_id=(index + 1).to_bytes(4, "big"), scenario="traffic",
        ).event
        events.append(event)
        truth.append(Truth(event.ts_ns, "benign" if kind == Attack.BENIGN else kind.name.lower()))
    return Traffic(tuple(events), tuple(truth))


def detect_traffic(events: Sequence[Event]) -> list[Alert]:
    """The detection boundary accepts engine records only, never truth labels."""
    return detect.run_rules(to_dicts(events))


def score(truth: Sequence[Truth], alerts: Sequence[Alert],
          rule_ids: Sequence[str]) -> tuple[Performance, ...]:
    """Count unique evidence events, not alerts; every attack is positive for each rule."""
    positive = {item.ts_ns for item in truth if item.label != "benign"}
    negative = {item.ts_ns for item in truth if item.label == "benign"}
    rows = []
    for rule in (*rule_ids, "ANY_RULE"):
        predicted = {stamp for alert in alerts if rule == "ANY_RULE" or alert["rule"] == rule
                     for stamp in alert["evidence"]}
        tp, fp = len(positive & predicted), len(negative & predicted)
        rows.append(Performance(rule, tp, fp, len(positive) - tp, len(negative) - fp,
                                tp / len(positive) if positive else None,
                                fp / len(negative) if negative else None))
    return tuple(rows)


def measure(traffic: Traffic, alerts: Sequence[Alert]) -> tuple[Performance, ...]:
    return score(traffic.truth, alerts, [rule.id for rule in load_rules(detect.RULES_DIR)])


def sweep(inputs: TrafficInput, levels: Sequence[float] = BER_LEVELS) -> tuple[Measurement, ...]:
    """Paired trials: same geometry, attack mix, nonce, jitter and seed at every BER."""
    rows = []
    for ber in levels:
        traffic = generate_traffic(TrafficInput(**{**inputs.model_dump(), "ber": ber}))
        rows.append(Measurement(ber, measure(traffic, detect_traffic(traffic.events))))
    return tuple(rows)
