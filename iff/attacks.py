"""Attacker constructions. Each returns a protocol.Response as the attacker
would present it to the interrogator.
"""
import secrets
from . import crypto, config
from .protocol import Response, make_response


def replay(recorded_response: Response, t_recv_ns: int) -> Response:
    """Replay a previously recorded valid response verbatim (old nonce)."""
    r = recorded_response
    return Response(r.unit_id, r.epoch, r.nonce, r.tag, t_recv_ns)


def relay(master_key, epoch, friendly_unit_id, live_nonce, t_recv_ns) -> Response:
    """MITM relay: forward the live challenge to a real distant friendly and
    return its genuine response. Tag is valid; only the timing betrays it."""
    return make_response(master_key, epoch, friendly_unit_id, live_nonce, t_recv_ns)


def captured(master_key, epoch, unit_id, live_nonce, t_recv_ns) -> Response:
    """Captured aircraft: holds a genuine unit key and answers correctly."""
    return make_response(master_key, epoch, unit_id, live_nonce, t_recv_ns)


def forge(unit_id, epoch, live_nonce, t_recv_ns) -> Response:
    """No key: echo the public nonce, guess the tag at random."""
    tag = secrets.token_bytes(config.TAG_BYTES)
    return Response(unit_id, epoch, live_nonce, tag, t_recv_ns)
