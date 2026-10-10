"""Attack scenarios S1-S7. Each returns (events, expected) where expected is
the list of (decision, reject_stage) the design predicts, so run_all can
assert actual == expected without anyone editing expectations to pass.
"""
import numpy as np
from . import crypto, channel, attacks, config
from .protocol import Challenge, Interrogator, Responder, Response, make_response
from .events import Event
from .maneuver import (expected_bits, generate_yaw_series, observe,
                       recover_bits, hamming)

MASTER_KEY = bytes.fromhex("00112233445566778899aabbccddeeff"
                           "ffeeddccbbaa99887766554433221100")
EPOCH = 100
IQ = "IQ-01"
FRIEND = bytes.fromhex("0000000a")   # unit id of a legitimate friendly
CAP = bytes.fromhex("0000000c")      # unit id that gets captured


def _event(scn, resp, result, nonce, bearing, rng_m, component="C1", note=""):
    return Event(
        ts_ns=0, interrogator_id=IQ, bearing_deg=bearing, range_m=rng_m,
        component=component, unit_id=resp.unit_id.hex(), epoch=resp.epoch,
        nonce_hex=resp.nonce.hex(), rtt_ns=result.rtt_ns,
        decision=result.decision, reject_stage=result.reject_stage,
        scenario=scn, note=note,
    )


def _iq(rng, **kw):
    return Interrogator(master_key=MASTER_KEY, current_epoch=EPOCH, **kw)


def s1_normal_friend(rng):
    iq = _iq(rng)
    nonce = rng.bytes(config.NONCE_BYTES)
    t0 = 1_000_000
    iq.issue(nonce, t0)
    rtt = channel.round_trip_ns(300.0, rng)
    resp = make_response(MASTER_KEY, EPOCH, FRIEND, nonce, t_recv_ns=int(t0 + rtt))
    res = iq.verify(resp)
    ev = [_event("S1", resp, res, nonce, 45.0, 300.0, note="valid friendly")]
    return ev, [("ACCEPT_FRIEND", None)]


def s2_replay(rng):
    iq = _iq(rng)
    # prior legitimate exchange (nonce_old), consumed
    nonce_old = rng.bytes(config.NONCE_BYTES)
    t0 = 1_000_000
    iq.issue(nonce_old, t0)
    rtt = channel.round_trip_ns(300.0, rng)
    resp_old = make_response(MASTER_KEY, EPOCH, FRIEND, nonce_old, t_recv_ns=int(t0 + rtt))
    res_ok = iq.verify(resp_old)                      # ACCEPT, nonce_old consumed
    ev = [_event("S2", resp_old, res_ok, nonce_old, 45.0, 300.0, note="prior valid exchange")]
    # fresh challenge, attacker replays the recorded response
    nonce_new = rng.bytes(config.NONCE_BYTES)
    t1 = 5_000_000
    iq.issue(nonce_new, t1)
    rep = attacks.replay(resp_old, t_recv_ns=int(t1 + rtt))
    res_rep = iq.verify(rep)                           # NONCE reject (old nonce)
    ev.append(_event("S2", rep, res_rep, rep.nonce, 46.0, 310.0, note="replayed old response"))
    return ev, [("ACCEPT_FRIEND", None), ("REJECT", "NONCE")]


def s3_relay_mitm(rng, relay_overhead_ns=100_000.0):
    iq = _iq(rng)
    nonce = rng.bytes(config.NONCE_BYTES)
    t0 = 1_000_000
    iq.issue(nonce, t0)
    rtt = channel.round_trip_ns(400.0, rng, relay_overhead_ns=relay_overhead_ns)
    resp = attacks.relay(MASTER_KEY, EPOCH, FRIEND, nonce, t_recv_ns=int(t0 + rtt))
    res = iq.verify(resp)                               # valid tag, RTT over budget
    ev = [_event("S3", resp, res, nonce, 120.0, 400.0, note="relayed via distant friendly")]
    return ev, [("REJECT", "RTT")]


def s4_captured_unit(rng):
    ev = []
    # --- pre-revocation: captured unit answers correctly, ACCEPTS (danger window) ---
    iq = _iq(rng)
    n1 = rng.bytes(config.NONCE_BYTES); t0 = 1_000_000
    iq.issue(n1, t0)
    rtt = channel.round_trip_ns(300.0, rng)
    r1 = attacks.captured(MASTER_KEY, EPOCH, CAP, n1, t_recv_ns=int(t0 + rtt))
    res1 = iq.verify(r1)
    ev.append(_event("S4", r1, res1, n1, 200.0, 300.0, note="captured unit, pre-revocation"))
    # --- operator revokes CAP; it answers again -> REVOKED ---
    iq.revoked.add(CAP)
    n2 = rng.bytes(config.NONCE_BYTES); t1 = 5_000_000
    iq.issue(n2, t1)
    r2 = attacks.captured(MASTER_KEY, EPOCH, CAP, n2, t_recv_ns=int(t1 + rtt))
    res2 = iq.verify(r2)
    ev.append(_event("S4", r2, res2, n2, 200.0, 300.0, note="after revocation"))
    # --- epoch rotates; captured unit has no key for the new epoch -> TAG ---
    iq2 = _iq(rng); iq2.current_epoch = EPOCH + 1
    n3 = rng.bytes(config.NONCE_BYTES); t2 = 9_000_000
    iq2.issue(n3, t2)
    # attacker still holds only the OLD epoch key -> builds stale-epoch response,
    # but presents current epoch id; tag derived from old key fails
    uk_old = crypto.unit_key(MASTER_KEY, EPOCH, CAP)
    stale_tag = crypto.response_tag(uk_old, n3, CAP, EPOCH + 1)
    from .protocol import Response
    r3 = Response(CAP, EPOCH + 1, n3, stale_tag, t_recv_ns=int(t2 + rtt))
    res3 = iq2.verify(r3)
    ev.append(_event("S4", r3, res3, n3, 200.0, 300.0, note="next epoch, no new key"))
    return ev, [("ACCEPT_FRIEND", None), ("REJECT", "REVOKED"), ("REJECT", "TAG")]


def s5_random_forgery(rng):
    iq = _iq(rng)
    nonce = rng.bytes(config.NONCE_BYTES); t0 = 1_000_000
    iq.issue(nonce, t0)
    rtt = channel.round_trip_ns(300.0, rng)
    resp = attacks.forge(bytes.fromhex("000000ff"), EPOCH, nonce, t_recv_ns=int(t0 + rtt))
    res = iq.verify(resp)
    ev = [_event("S5", resp, res, nonce, 80.0, 300.0, note="no key, random tag")]
    return ev, [("REJECT", "TAG")]


def s6_maneuver_replay(rng, sigma=0.5):
    """Component 2: genuine friendly accepted; replay of a past window rejected."""
    from .events import Event as Ev
    window = 500
    exp = expected_bits(MASTER_KEY, EPOCH, FRIEND, window)
    # genuine: fly this window's pattern, observe with light noise
    genuine_series = generate_yaw_series(exp)
    obs = observe(genuine_series, sigma, rng)
    rec = recover_bits(obs, len(exp))
    d_ok = hamming(exp, rec)
    ok = d_ok <= config.MANEUVER_HAMMING_K
    ev = [Ev(ts_ns=0, interrogator_id=IQ, bearing_deg=60.0, range_m=500.0,
             component="C2", unit_id=FRIEND.hex(), epoch=EPOCH, nonce_hex="",
             rtt_ns=None, decision="ACCEPT_FRIEND" if ok else "REJECT",
             reject_stage=None if ok else "C2_HAMMING", scenario="S6",
             note=f"genuine, hamming={d_ok}")]
    # replay: attacker flies the PREVIOUS window's pattern this window
    old = expected_bits(MASTER_KEY, EPOCH, FRIEND, window - 1)
    old_series = generate_yaw_series(old)
    obs2 = observe(old_series, sigma, rng)
    rec2 = recover_bits(obs2, len(exp))
    d_bad = hamming(exp, rec2)      # compared against THIS window's expected
    bad_ok = d_bad <= config.MANEUVER_HAMMING_K
    ev.append(Ev(ts_ns=0, interrogator_id=IQ, bearing_deg=61.0, range_m=510.0,
                 component="C2", unit_id=FRIEND.hex(), epoch=EPOCH, nonce_hex="",
                 rtt_ns=None, decision="ACCEPT_FRIEND" if bad_ok else "REJECT",
                 reject_stage=None if bad_ok else "C2_HAMMING", scenario="S6",
                 note=f"replayed prev window, hamming={d_bad}"))
    return ev, [("ACCEPT_FRIEND", None), ("REJECT", "C2_HAMMING")]


def s7_cloned_unit(rng: np.random.Generator) -> tuple[list[Event], list[tuple[str, str | None]]]:
    """Authenticate one unit at two incompatible positions in the same epoch."""
    iq = _iq(rng)
    unit_id = bytes.fromhex("0000000d")
    events = []
    for t0, bearing, range_m in ((1_000_000, 30.0, 300.0),
                               (5_000_000, 150.0, 900.0)):
        nonce = rng.bytes(config.NONCE_BYTES)
        iq.issue(nonce, t0)
        rtt = channel.round_trip_ns(range_m, rng)
        resp = make_response(MASTER_KEY, EPOCH, unit_id, nonce,
                             t_recv_ns=int(t0 + rtt))
        result = iq.verify(resp)
        events.append(_event("S7", resp, result, nonce, bearing, range_m,
                             note="same unit key at incompatible positions"))
    return events, [("ACCEPT_FRIEND", None), ("ACCEPT_FRIEND", None)]


def s8_captured_key_grace(rng: np.random.Generator) -> tuple[list[Event], list[tuple[str, str | None]]]:
    """Demonstrate old-key acceptance during grace, then immediate revocation."""
    iq = _iq(rng)
    iq.current_epoch = EPOCH + 1
    captured_key = crypto.unit_key(MASTER_KEY, EPOCH, CAP)
    events = []
    for index, t0 in enumerate((1_000_000, 5_000_000)):
        if index == 1:
            iq.revoked.add(CAP)
        nonce = rng.bytes(config.NONCE_BYTES)
        iq.issue(nonce, t0)
        rtt = channel.round_trip_ns(300.0, rng)
        response = Response(CAP, EPOCH, nonce,
                            crypto.response_tag(captured_key, nonce, CAP, EPOCH),
                            t_recv_ns=int(t0 + rtt))
        result = iq.verify(response)
        event = _event("S8", response, result, nonce, 200.0, 300.0,
                       note=f"key epoch={EPOCH}, verifier epoch={iq.current_epoch}, revoked={index == 1}")
        event.ts_ns = t0
        events.append(event)
    return events, [("ACCEPT_FRIEND", None), ("REJECT", "REVOKED")]


ALL = {
    "S1": s1_normal_friend,
    "S2": s2_replay,
    "S3": s3_relay_mitm,
    "S4": s4_captured_unit,
    "S5": s5_random_forgery,
    "S6": s6_maneuver_replay,
    "S7": s7_cloned_unit,
}


def s9_rogue_interrogator(rng: np.random.Generator) -> tuple[list[Event], list[tuple[str, str | None]]]:
    drone = Responder(FRIEND, EPOCH, {EPOCH: crypto.iq_key(MASTER_KEY, EPOCH)},
                      {EPOCH: crypto.unit_key(MASTER_KEY, EPOCH, FRIEND)})
    fake = Challenge(rng.bytes(config.NONCE_BYTES), 1_000_000, "ROGUE", EPOCH)
    drone.respond(fake, t_recv_ns=1_000_000, scenario="S9a", bearing_deg=280, range_m=600)
    recorded = _iq(rng).issue(rng.bytes(config.NONCE_BYTES), 2_000_000)
    drone.respond(recorded, t_recv_ns=2_000_000, scenario="S9", bearing_deg=310, range_m=700)
    drone.respond(recorded, t_recv_ns=3_000_000, scenario="S9b", bearing_deg=310, range_m=700)
    return drone.events, [("NO_RESPONSE", "IQ_TAG"), ("NO_RESPONSE", "IQ_NONCE")]


def run_all(seed=42, *, include_grace=False, include_rogue=False):
    rng = np.random.default_rng(seed)
    results = {}
    selected = {**ALL, "S8": s8_captured_key_grace} if include_grace else ALL
    if include_rogue:
        selected = {**selected, "S9": s9_rogue_interrogator}
    for name, fn in selected.items():
        events, expected = fn(rng)
        actual = [(e.decision, e.reject_stage) for e in events]
        results[name] = {"events": events, "expected": expected,
                         "actual": actual, "match": actual == expected}
    return results
