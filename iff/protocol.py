"""Component 1: optical challenge-response and the fixed verification pipeline.

The response references the nonce it answers (the challenge nonce is public,
sent in the clear). The interrogator demultiplexes by that nonce and records
the first failing stage as `reject_stage`.
"""
import hmac
from dataclasses import dataclass, field
from typing import Optional
from . import crypto, config
from .events import Event


@dataclass
class Challenge:
    nonce: bytes
    t_send_ns: int
    interrogator_id: str = "IQ-01"
    epoch: int = 0
    iq_tag: bytes = b""


@dataclass
class Response:
    unit_id: bytes
    epoch: int
    nonce: bytes          # which challenge this answers
    tag: bytes
    t_recv_ns: int = 0    # transport-observed, not authenticated


@dataclass
class VerifyResult:
    decision: str                       # ACCEPT_FRIEND | REJECT
    reject_stage: Optional[str] = None
    rtt_ns: Optional[float] = None


@dataclass
class Interrogator:
    master_key: bytes
    current_epoch: int
    d_max_m: float = config.DEFAULT_D_MAX_M
    revoked: set = field(default_factory=set)
    pending: dict = field(default_factory=dict)   # nonce -> t_send_ns
    interrogator_id: str = "IQ-01"

    def issue(self, nonce: bytes, t_send_ns: int) -> Challenge:
        self.pending[nonce] = t_send_ns
        tag = crypto.challenge_tag(crypto.iq_key(self.master_key, self.current_epoch),
                                   nonce, self.interrogator_id, self.current_epoch)
        return Challenge(nonce, t_send_ns, self.interrogator_id, self.current_epoch, tag)

    def verify(self, resp: Response) -> VerifyResult:
        # 1. FORMAT
        if (not isinstance(resp.unit_id, (bytes, bytearray))
                or len(resp.unit_id) != config.UNIT_ID_BYTES
                or len(resp.tag) != config.TAG_BYTES
                or not isinstance(resp.nonce, (bytes, bytearray))
                or len(resp.nonce) != config.NONCE_BYTES):
            return VerifyResult("REJECT", "FORMAT")

        # 2. EPOCH (current or within grace window)
        if not (self.current_epoch - config.EPOCH_GRACE <= resp.epoch <= self.current_epoch):
            return VerifyResult("REJECT", "EPOCH")

        # 3. REVOKED
        if bytes(resp.unit_id) in self.revoked:
            return VerifyResult("REJECT", "REVOKED")

        # 4. NONCE (must be currently pending; consumed on use)
        if bytes(resp.nonce) not in self.pending:
            return VerifyResult("REJECT", "NONCE")
        t_send = self.pending.pop(bytes(resp.nonce))

        # 5. TAG
        uk = crypto.unit_key(self.master_key, resp.epoch, bytes(resp.unit_id))
        expect = crypto.response_tag(uk, bytes(resp.nonce), bytes(resp.unit_id), resp.epoch)
        if not hmac.compare_digest(expect, bytes(resp.tag)):
            return VerifyResult("REJECT", "TAG")

        # 6. RTT
        rtt = resp.t_recv_ns - t_send
        if rtt > config.rtt_budget_ns(self.d_max_m):
            return VerifyResult("REJECT", "RTT", rtt_ns=rtt)

        return VerifyResult("ACCEPT_FRIEND", None, rtt_ns=rtt)


@dataclass(slots=True)
class Responder:
    """Provisioned drone; retain consumed nonces and local decisions across queries."""

    unit_id: bytes
    current_epoch: int
    iq_keys: dict[int, bytes]
    unit_keys: dict[int, bytes]
    seen: set[tuple[int, bytes]] = field(default_factory=set)
    events: list[Event] = field(default_factory=list)

    def respond(self, challenge: Challenge, *, t_recv_ns: int = 0,
                scenario: str = "", bearing_deg: float = 0, range_m: float = 0) -> Response | None:
        """Authenticate before transmitting; query epochs have no grace window."""
        stage = None
        if challenge.epoch != self.current_epoch:
            stage = "IQ_EPOCH"
        elif (challenge.epoch not in self.iq_keys
              or not hmac.compare_digest(challenge.iq_tag, crypto.challenge_tag(
                  self.iq_keys[challenge.epoch], challenge.nonce,
                  challenge.interrogator_id, challenge.epoch))):
            stage = "IQ_TAG"
        elif (challenge.epoch, challenge.nonce) in self.seen:
            stage = "IQ_NONCE"
        if stage:
            self.events.append(Event(
                t_recv_ns, challenge.interrogator_id, bearing_deg, range_m, "CQ",
                self.unit_id.hex(), challenge.epoch, challenge.nonce.hex(), None,
                "NO_RESPONSE", stage, scenario, "responder: query rejected",
            ))
            return None
        self.seen.add((challenge.epoch, challenge.nonce))
        tag = crypto.response_tag(self.unit_keys[challenge.epoch], challenge.nonce,
                                  self.unit_id, challenge.epoch)
        return Response(self.unit_id, challenge.epoch, challenge.nonce, tag, t_recv_ns)


def make_response(master_key: bytes, epoch: int, unit_id: bytes, nonce: bytes,
                  t_recv_ns: int = 0) -> Response:
    """Build a correct friendly response (holds a valid unit key)."""
    uk = crypto.unit_key(master_key, epoch, unit_id)
    tag = crypto.response_tag(uk, nonce, unit_id, epoch)
    return Response(unit_id, epoch, nonce, tag, t_recv_ns)
