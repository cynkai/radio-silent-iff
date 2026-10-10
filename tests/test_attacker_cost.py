import csv
import io
from math import comb
from pathlib import Path

import pytest

from iff import config
from iff.attacker_cost import build_costs, cost_csv, cost_markdown, write_attacker_cost
from scripts.sweep_noise import list_size_false_accept, relay_sweep


def _write_csv(path: Path, rows: list) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_forgery_probability_tracks_tag_bits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "TAG_BITS", 24)

    row = next(row for row in build_costs(tmp_path) if row.scenario == "S5")

    assert row.success_probability == 1 / 16_777_216
    assert row.valid_window_upper_s is None


def test_consumed_nonce_replay_is_zero_and_collision_bound_tracks_nonce_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "NONCE_BYTES", 2)

    row = next(row for row in build_costs(tmp_path) if row.scenario == "S2")

    assert row.success_probability == 0
    assert row.valid_window_upper_s == 0
    assert f"{1 / 65_536:.6g}" in row.probability_note


def test_relay_success_rates_are_csv_complements(tmp_path: Path) -> None:
    points = relay_sweep(seed=42, trials=200)
    _write_csv(tmp_path / "relay_sweep.csv", points)

    rows = [row for row in build_costs(tmp_path) if row.scenario == "S3"]

    assert [(row.relay_overhead_ns, row.success_probability) for row in rows] == [
        (point["relay_overhead_ns"], 1 - point["reject_rate"]) for point in points
    ]
    assert next(row for row in rows if row.relay_overhead_ns == 30_000).success_probability == 0.595
    assert all(row.valid_window_upper_s is None for row in rows)


def test_nominal_relay_boundary_uses_budget_and_base_round_trip_not_jitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = relay_sweep(trials=1)[0]
    monkeypatch.setattr(config, "ASSUMPTION_PROC_JITTER_NS", 0)

    zero_jitter = relay_sweep(trials=1)[0]

    assert original["budget_ns"] - original["nominal_rtt_ns"] == pytest.approx(30_674, abs=1)
    assert zero_jitter["nominal_rtt_ns"] == original["nominal_rtt_ns"]
    assert zero_jitter["budget_ns"] == original["budget_ns"]


def test_captured_window_tracks_epoch_duration_and_grace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "EPOCH_SECONDS", 90)
    monkeypatch.setattr(config, "EPOCH_GRACE", 2)

    rows = [row for row in build_costs(tmp_path) if row.scenario == "S4"]

    assert [(row.success_probability, row.valid_window_upper_s) for row in rows] == [
        (1.0, 270.0), (0.0, 0.0),
    ]


def test_fleet_false_accept_matches_hamming_ball_and_list_size(tmp_path: Path) -> None:
    _write_csv(tmp_path / "list_size.csv", list_size_false_accept())
    p = (comb(16, 0) + comb(16, 1) + comb(16, 2)) / 65_536

    rows = [row for row in build_costs(tmp_path) if row.scenario == "S6"]

    assert [row.fleet_size for row in rows] == [1, 5, 10, 25, 50, 100, 200]
    for row in rows:
        assert row.fleet_size is not None
        assert row.success_probability == pytest.approx(1 - (1 - p) ** row.fleet_size)
        assert row.valid_window_upper_s == config.MANEUVER_WINDOW_S


def test_missing_sweep_values_are_empty_in_csv_not_zero(tmp_path: Path) -> None:
    rows = build_costs(tmp_path)

    exported = list(csv.DictReader(io.StringIO(cost_csv(rows))))

    relay = next(row for row in exported if row["scenario"] == "S3")
    assert relay["success_probability"] == ""
    assert relay["valid_window_upper_s"] == ""
    assert relay["condition"] == "미측정"
    fleet = next(row for row in rows if row.scenario == "S6")
    assert fleet.fleet_size == 1
    assert fleet.success_probability == 137 / 65_536


def test_csv_and_explanation_export_the_same_rows_and_provenance(tmp_path: Path) -> None:
    _write_csv(tmp_path / "relay_sweep.csv", relay_sweep(trials=1))
    _write_csv(tmp_path / "list_size.csv", list_size_false_accept())

    rows = write_attacker_cost(tmp_path)

    assert (tmp_path / "attacker_cost.csv").read_bytes() == cost_csv(rows).encode("utf-8")
    assert (tmp_path / "attacker_cost.md").read_text(encoding="utf-8") == cost_markdown(rows)
    assert {row.scenario for row in rows} == {"S2", "S3", "S4", "S5", "S6", "S9"}
    assert all(row.source and row.capability for row in rows)
