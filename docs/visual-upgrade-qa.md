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

## Phase B — shared verification pipeline

- PASS: The console detail, sandbox and guide tour use the same six-gate component. Engine-projected stage states drive green passes, the red blocking gate, unreached gates and the final ACCEPT stamp.
- PASS: RTT gauge inside the last gate uses measured RTT and configured budget. C2/CQ explicitly do not traverse C1 gates; missing RTT stays missing.
- PASS: Desktop horizontal gates and mobile vertical gates; replay and reduced-motion static final state. Captures: `visual-b-{desktop,mobile}-{start,middle,end,sandbox,rtt,tour}.png`.
- PASS: No horizontal overflow or browser console/page errors. Console readiness observed at 1218 ms desktop and 1224 ms mobile (warm local server); no perceived regression.
- Existing sandbox's duplicate Plotly RTT gauge was removed after mobile inspection showed its numeric label clipping; the complete value remains in the shared component.
- Existing tests, selectors, engine and original alert messages are unchanged.
- PASS: Final full pytest/AppTest suite: 160 passed in 19.98 s; run_all S1–S9 all match.

## Phase C — SVG contact geometry

- PASS: Live SVG replaces rendered Plotly radar in console/replay, tour and traffic scrubber. Engine range/bearing remain unchanged; labels use leader lines and contacts fade in by event timestamp.
- PASS: Severity rings, selected-event ring, hover/focus details, distance rings, bearing ticks and explicitly decorative sweep. Reduced motion renders the complete static scene; replay restarts it.
- PASS: Desktop/mobile start-middle-end captures in `visual-c-*`; no text overlaps or horizontal scroll. Browser errors zero. Warm readiness: desktop 1248 ms, mobile 1583 ms.
- PASS: pytest/AppTest 160 passed in 18.62 s; run_all S1–S9 all match.
- Selector-only AppTest migration: five dashboard test files now select the SVG iframe JSON instead of the removed Plotly chart. Coordinate, shape, no-response, scenario-label and chart-count expectations remain equivalent. No decision tests or expected simulation outcomes changed.
- PASS: Browser checks verified every SVG contact transform against its injected engine bearing/range; keyboard tooltip, one selected ring and reduced-motion final state. Traffic slider changed 300 contacts to the two-event prefix at both widths, with matching prefix alerts.
- Final selection synchronization uses the detail widget's returned index. Revalidation: 160 tests passed in 19.74 s and all scenarios matched; fresh captures show unchanged layout, zero browser errors and widths 1440/390.
