# Visual upgrade verification

## Phase A — protocol replay

- PASS: Engine event JSON supplies decision, reject stage, RTT and configured budget. No engine, scenario, rule, expectation, alert message or existing test changed; no dependency added.
- PASS: Challenge, responder authentication, response and interrogator validation replay; S2 NONCE, S3 RTT and S9 silence variants inspected.
- PASS: 1440×900 and 390×844 start/middle/end captures in `docs/img/visual-a-*`; mobile uses vertical geometry. No horizontal overflow or clipped labels after splitting the mobile challenge label.
- PASS: Replay button, reduced-motion final state, simulation disclaimer and non-sensor explanation.
- PASS: Browser page/console errors: zero at both widths.
- PASS: First-render median over three visits: baseline 1586 ms; Phase A 1607 ms (+21 ms). This small local sample shows no noticeable regression.
- PASS: `python3 -m pytest -q`: 160 passed (including existing AppTest); `python3 scripts/run_all.py --seed 42`: all S1–S9 match.

Screenshots are engine-derived live captures, not input data or stored simulation results.
