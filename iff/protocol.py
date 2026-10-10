"""Component 1: optical challenge-response and the fixed verification pipeline.

The response references the nonce it answers (the challenge nonce is public,
sent in the clear). The interrogator demultiplexes by that nonce and records
the first failing stage as `reject_stage`.
"""
import hmac
from dataclasses import dataclass, field
from typing import Optional
from . import crypto, config


@dataclass
class Challenge:
    nonce: bytes
    t_send_ns: int


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

    def issue(self, nonce: bytes, t_send_ns: int) -> Challenge:
        self.pending[nonce] = t_send_ns
        return Challenge(nonce, t_send_ns)

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


def make_response(master_key: bytes, epoch: int, unit_id: bytes, nonce: bytes,
                  t_recv_ns: int = 0) -> Response:
    """Build a correct friendly response (holds a valid unit key)."""
    uk = crypto.unit_key(master_key, epoch, unit_id)
    tag = crypto.response_tag(uk, nonce, unit_id, epoch)
    return Response(unit_id, epoch, nonce, tag, t_recv_ns)
