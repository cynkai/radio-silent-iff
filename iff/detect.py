"""Log-based detection rules — alerts generated from the event log,
independent of the per-response accept/reject decision.
"""
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Final

from . import config
from .rule_config import load_rules
from .rule_engine import Alert, EventRecord, evaluate


RULES_DIR: Final = Path(__file__).resolve().parent.parent / "rules"


def run_rules(
    events: Sequence[EventRecord],
    revoked_hex: Iterable[str] | None = None,
    d_max_m: float = config.DEFAULT_D_MAX_M,
    *,
    rules_dir: Path | None = None,
) -> list[Alert]:
    rules = load_rules(RULES_DIR if rules_dir is None else rules_dir)
    return evaluate(rules, events, config.rtt_budget_ns(d_max_m))
