"""Seeded experiment inputs; protocol objects own every decision."""
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Final, assert_never

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from . import attacks, channel, config, crypto, scenarios
from .events import Event
from .protocol import Interrogator, Responder, Response


class Attack(StrEnum):
    REPLAY = "재전송"
    RELAY = "중계"
    FORGE = "무작위 위조"
    CAPTURED = "포획 기체"
    ROGUE = "가짜 질의기"
    QUERY_REPLAY = "질의 재방송"
    BENIGN = "정상 아군(대조군)"


class SandboxInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    attack: Attack = Attack.RELAY
    relay_us: float = Field(default=25, ge=0, le=200)
    elapsed_epochs: int = Field(default=1, ge=0, le=2)
    revoked: bool = False
    ber: float = Field(default=0, ge=0, le=1)
    seed: int = Field(default=42, ge=0)


@dataclass(frozen=True, slots=True)
class Experiment:
    event: Event
    budget_ns: float


PIPELINE: Final = ("FORMAT", "EPOCH", "REVOKED", "NONCE", "TAG", "RTT")


def run_experiment(inputs: SandboxInput, *, bearing_deg: float = 120,
                   range_m: float = 400, ts_ns: int = 1_000_000,
                   unit_id: bytes | None = None, scenario: str = "sandbox") -> Experiment:
    """Construct a wire exchange, then project the unmodified engine result."""
    rng = np.random.default_rng(inputs.seed)
    unit = unit_id if unit_id is not None else (
        scenarios.CAP if inputs.attack == Attack.CAPTURED else scenarios.FRIEND)
    epoch = scenarios.EPOCH
    verifier_epoch = epoch + (inputs.elapsed_epochs if inputs.attack == Attack.CAPTURED else 0)
    iq = Interrogator(scenarios.MASTER_KEY, verifier_epoch,
                      revoked={unit} if inputs.revoked else set())
    drone = Responder(unit, epoch, {epoch: crypto.iq_key(scenarios.MASTER_KEY, epoch)},
                      {epoch: crypto.unit_key(scenarios.MASTER_KEY, epoch, unit)})
    nonce = rng.bytes(config.NONCE_BYTES)
    challenge = iq.issue(nonce, ts_ns)
    overhead = inputs.relay_us * 1000 if inputs.attack == Attack.RELAY else 0
    recv = ts_ns + int(channel.round_trip_ns(range_m, rng, overhead))
    match inputs.attack:
        case Attack.BENIGN | Attack.RELAY:
            response = drone.respond(challenge, t_recv_ns=recv)
        case Attack.CAPTURED:
            response = attacks.captured(scenarios.MASTER_KEY, epoch, unit, nonce, recv)
        case Attack.FORGE:
            response = Response(unit, epoch, nonce, rng.bytes(config.TAG_BYTES), recv)
        case Attack.REPLAY:
            recorded = drone.respond(challenge, t_recv_ns=recv)
            assert recorded is not None
            iq.verify(recorded)
            iq.issue(rng.bytes(config.NONCE_BYTES), ts_ns)
            response = attacks.replay(recorded, recv)
        case Attack.ROGUE | Attack.QUERY_REPLAY:
            if inputs.attack == Attack.QUERY_REPLAY:
                drone.respond(challenge, t_recv_ns=ts_ns)
            else:
                challenge = replace(challenge, iq_tag=b"")
            response = drone.respond(challenge, t_recv_ns=recv, scenario=scenario,
                                     bearing_deg=bearing_deg, range_m=range_m)
        case unreachable:
            assert_never(unreachable)
    budget = config.rtt_budget_ns(iq.d_max_m)
    if response is None:
        return Experiment(drone.events[-1], budget)
    damaged = replace(response, tag=channel.apply_ber(response.tag, inputs.ber, rng))
    result = iq.verify(damaged)
    return Experiment(Event(
        recv, iq.interrogator_id, bearing_deg, range_m, "C1", damaged.unit_id.hex(),
        damaged.epoch, damaged.nonce.hex(), result.rtt_ns, result.decision,
        result.reject_stage, scenario,
    ), budget)


def pipeline_states(event: Event) -> tuple[str, ...]:
    """Do not infer success for steps an engine never reached."""
    if event.component != "C1":
        return ("미도달",) * len(PIPELINE)
    failure = PIPELINE.index(event.reject_stage) if event.reject_stage in PIPELINE else len(PIPELINE)
    return tuple("통과" if i < failure else "차단" if i == failure else "미도달"
                 for i in range(len(PIPELINE)))
