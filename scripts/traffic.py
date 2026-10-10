# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pydantic", "PyYAML", "plotly", "typer"]
# ///
# How to run: python3 scripts/traffic.py --benign 200 --attacks 100 --seed 42
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

import plotly.graph_objects as go
import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iff.events import write_jsonl
from iff.sandbox import Attack, SandboxInput, run_experiment
from iff.traffic import TrafficInput, detect_traffic, generate_traffic, measure, sweep


def main(benign: int = 200, attacks: int = 100, seed: int = 42, ber: float = 0,
         out: Path = Path("out/traffic")) -> None:
    inputs = TrafficInput(benign=benign, attacks=attacks, seed=seed, ber=ber)
    traffic = generate_traffic(inputs)
    alerts = detect_traffic(traffic.events)
    metrics = measure(traffic, alerts)
    measurements = sweep(inputs)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(traffic.events, out / "events.jsonl")
    with (out / "truth.jsonl").open("w", encoding="utf-8") as handle:
        for item in traffic.truth:
            handle.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
    rows = [asdict(row) for row in metrics]
    sweep_rows = [{"ber": row.ber, **asdict(metric)} for row in measurements for metric in row.metrics]
    cases = [SandboxInput(attack=kind, seed=seed) for kind in Attack]
    cases += [SandboxInput(attack=Attack.RELAY, relay_us=40, seed=seed),
              SandboxInput(attack=Attack.CAPTURED, revoked=True, seed=seed),
              SandboxInput(attack=Attack.CAPTURED, elapsed_epochs=2, seed=seed)]
    sandbox_rows = []
    for case in cases:
        event = run_experiment(case).event
        sandbox_rows.append({**case.model_dump(mode="json"), "decision": event.decision,
                             "reject_stage": event.reject_stage, "rtt_ns": event.rtt_ns})
    for name, records in (("metrics.csv", rows), ("ber_sweep.csv", sweep_rows),
                          ("sandbox.csv", sandbox_rows)):
        with (out / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    with (out / "run.json").open("w", encoding="utf-8") as handle:
        json.dump({"inputs": inputs.model_dump(), "alerts": alerts,
                   "engine": "iff.protocol.Interrogator / Responder",
                   "unit": "unique evidence events; all attacks positive for each rule"},
                  handle, ensure_ascii=False, indent=2)
    figure = go.Figure()
    for index, metric in enumerate(metrics):
        figure.add_trace(go.Scatter(x=[row.ber for row in measurements],
                                   y=[row.metrics[index].false_positive_rate for row in measurements],
                                   name=metric.rule, mode="lines+markers"))
    figure.update_layout(xaxis_title="BER", yaxis_title="FP / benign events",
                         title=f"Seed {seed} · N={benign}, M={attacks}")
    figure.write_html(out / "ber_curve.html", include_plotlyjs=True)
    print(json.dumps({"output": str(out), "overall": asdict(metrics[-1])}, ensure_ascii=False))


if __name__ == "__main__":
    typer.run(main)
