"""Event log schema — one JSONL line per identification decision."""
import json
from dataclasses import dataclass, asdict, field
from typing import Optional

DECISIONS = ("ACCEPT_FRIEND", "REJECT", "NO_RESPONSE")
# C1 stages plus C2_HAMMING for component 2 (see README "가정한 것")
STAGES = ("FORMAT", "EPOCH", "REVOKED", "NONCE", "TAG", "RTT", "C2_HAMMING")


@dataclass
class Event:
    ts_ns: int
    interrogator_id: str
    bearing_deg: float
    range_m: float
    component: str                # "C1" | "C2"
    unit_id: str                  # hex
    epoch: int
    nonce_hex: str
    rtt_ns: Optional[float]
    decision: str
    reject_stage: Optional[str]
    scenario: str
    note: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def write_jsonl(events, path):
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(e.to_json() + "\n")


def to_dicts(events):
    return [asdict(e) for e in events]
