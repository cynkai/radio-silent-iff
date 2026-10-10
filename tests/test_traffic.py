from dataclasses import asdict
from unittest.mock import patch

import pytest

from iff import detect
from iff.traffic import TrafficInput, Truth, detect_traffic, generate_traffic, measure, score, sweep


def test_seed_counts_geometry_and_event_identity():
    inputs = TrafficInput(benign=40, attacks=20, seed=8)
    traffic = generate_traffic(inputs)
    assert traffic == generate_traffic(inputs)
    assert len(traffic.events) == len(traffic.truth) == 60
    assert sum(row.label == "benign" for row in traffic.truth) == 40
    assert len({event.ts_ns for event in traffic.events}) == 60
    assert all(0 <= event.bearing_deg < 360 and 100 <= event.range_m <= 1800 for event in traffic.events)
    assert [event.ts_ns for event in traffic.events] == sorted(event.ts_ns for event in traffic.events)


def test_detector_receives_no_ground_truth_and_labels_do_not_affect_alerts():
    traffic = generate_traffic(TrafficInput(benign=20, attacks=20))
    with patch("iff.traffic.detect.run_rules", wraps=detect.run_rules) as engine:
        alerts = detect_traffic(traffic.events)
    records = engine.call_args.args[0]
    assert records == [asdict(event) for event in traffic.events]
    assert all(record["scenario"] == "traffic" and record["note"] in ("", "responder: query rejected")
               and "label" not in record and "attack" not in record for record in records)
    relabeled = tuple(Truth(row.ts_ns, "benign") for row in traffic.truth)
    assert detect_traffic(traffic.events) == alerts
    assert score(relabeled, alerts, ["R1_REPLAY_ATTEMPT"])[-1].tp == 0


def test_unique_evidence_confusion_matrix_and_union():
    truth = [Truth(1, "benign"), Truth(2, "benign"), Truth(3, "relay"), Truth(4, "forge")]
    alerts = [{"rule": "R1", "severity": "high", "message": "", "evidence": [1, 3, 3]},
              {"rule": "R1", "severity": "high", "message": "", "evidence": [3]},
              {"rule": "R2", "severity": "high", "message": "", "evidence": [4]}]
    rows = score(truth, alerts, ["R1", "R2", "R3"])
    assert [(r.tp, r.fp, r.fn, r.tn) for r in rows] == [(1, 1, 1, 1), (1, 0, 1, 2), (0, 0, 2, 2), (2, 1, 0, 1)]
    assert rows[0].detection_rate == rows[0].false_positive_rate == 0.5
    assert rows[-1].detection_rate == 1


@pytest.mark.parametrize(("benign", "attacks"), [(0, 0), (0, 10), (10, 0)])
def test_empty_class_has_undefined_rate(benign, attacks):
    traffic = generate_traffic(TrafficInput(benign=benign, attacks=attacks))
    rows = measure(traffic, detect_traffic(traffic.events))
    assert all((row.detection_rate is None) == (attacks == 0) for row in rows)
    assert all((row.false_positive_rate is None) == (benign == 0) for row in rows)


def test_ber_paired_trials_preserve_inputs_and_expose_false_positives():
    inputs = TrafficInput()
    clean = generate_traffic(inputs)
    noisy = generate_traffic(TrafficInput(ber=0.3))
    assert clean.truth == noisy.truth
    assert [(e.bearing_deg, e.range_m, e.nonce_hex) for e in clean.events] == [
        (e.bearing_deg, e.range_m, e.nonce_hex) for e in noisy.events]
    measurements = sweep(inputs, [0, 0.3])
    assert measurements[0].metrics[-1].fp == 0
    assert measurements[1].metrics[-1].fp > measurements[0].metrics[-1].fp
