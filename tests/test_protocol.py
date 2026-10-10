import numpy as np
from iff import config, channel, crypto
from iff.protocol import Interrogator, Response, make_response

MK = b"\x07" * 32
EP = 100
UID = bytes.fromhex("0000000a")


def _iq(**kw):
    return Interrogator(master_key=MK, current_epoch=EP, **kw)


def test_s1_accept():
    rng = np.random.default_rng(1)
    iq = _iq()
    nonce = b"\x01" * config.NONCE_BYTES
    iq.issue(nonce, 0)
    rtt = channel.round_trip_ns(300.0, rng)
    r = make_response(MK, EP, UID, nonce, t_recv_ns=int(rtt))
    assert iq.verify(r).decision == "ACCEPT_FRIEND"


def test_nonce_replay_rejected():
    iq = _iq()
    nonce = b"\x02" * config.NONCE_BYTES
    iq.issue(nonce, 0)
    r = make_response(MK, EP, UID, nonce, t_recv_ns=50_000)
    assert iq.verify(r).decision == "ACCEPT_FRIEND"   # consumes nonce
    assert iq.verify(r).reject_stage == "NONCE"        # second time: replay


def test_bad_tag_rejected():
    iq = _iq()
    nonce = b"\x03" * config.NONCE_BYTES
    iq.issue(nonce, 0)
    r = make_response(MK, EP, UID, nonce, t_recv_ns=50_000)
    r.tag = bytes([r.tag[0] ^ 0xFF]) + r.tag[1:]
    assert iq.verify(r).reject_stage == "TAG"


def test_revoked_rejected():
    iq = _iq(revoked={UID})
    nonce = b"\x04" * config.NONCE_BYTES
    iq.issue(nonce, 0)
    r = make_response(MK, EP, UID, nonce, t_recv_ns=50_000)
    assert iq.verify(r).reject_stage == "REVOKED"


def test_epoch_out_of_window_rejected():
    iq = _iq()
    nonce = b"\x05" * config.NONCE_BYTES
    iq.issue(nonce, 0)
    r = make_response(MK, EP - 5, UID, nonce, t_recv_ns=50_000)
    assert iq.verify(r).reject_stage == "EPOCH"


def test_rtt_over_budget_rejected():
    iq = _iq()
    nonce = b"\x06" * config.NONCE_BYTES
    iq.issue(nonce, 0)
    over = int(config.rtt_budget_ns(config.DEFAULT_D_MAX_M) + 1_000_000)
    r = make_response(MK, EP, UID, nonce, t_recv_ns=over)
    assert iq.verify(r).reject_stage == "RTT"


def test_stage_order_revoked_before_tag():
    # revoked unit AND wrong tag -> REVOKED must win (earlier stage)
    iq = _iq(revoked={UID})
    nonce = b"\x07" * config.NONCE_BYTES
    iq.issue(nonce, 0)
    r = make_response(MK, EP, UID, nonce, t_recv_ns=50_000)
    r.tag = b"\x00" * config.TAG_BYTES
    assert iq.verify(r).reject_stage == "REVOKED"
