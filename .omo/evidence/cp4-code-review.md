# CP4 code and functional QA review

codeQualityStatus: WATCH
recommendation: APPROVE
blockers: []

Scope: attacker-cost calculations/panel, S8, run_all integration, sweep metadata, new tests, visual QA G–J. No production or test code edited. No ulw-loop plan exists (status returned ULW_LOOP_PLAN_MISSING); this is the fallback report path.

## Evidence and limitations

Independently ran `python3 -B -m pytest -q -p no:cacheprovider`: **75 passed in final rerun** (74 passed in 3.32s before the added verifier-observation test). Focused cost/S8 run: 11 passed. Read iff/attacker_cost.py, iff/attacker_cost_panel.py, iff/scenarios.py, iff/protocol.py, app.py, scripts/run_all.py, scripts/sweep_noise.py, tests/test_attacker_cost.py, tests/test_attacker_cost_dashboard.py, tests/test_s8_grace.py, tests/test_detect_regression.py. Read out/summary.csv (S1–S8 all True). The suite itself executes AppTest across all five cost choices and S8.

Viewed all eight out/qa/s4-{desktop-1440,iphone-14}-{light,dark}-{top,end}.png captures, both cost-desktop-light-{top,detail}.png captures, and the extra s8-desktop-dark.png. Screenshot freshness cannot be independently established from an immutable build identifier. There is no .git repository, baseline archive, full historical diff, or supplied notepad. Therefore preservation of historical source/spec/test bytes cannot be certified. The frozen regression fixtures and default-versus-extended comparison provide behavioral evidence, not historical provenance.

## Findings by severity

### CRITICAL
None.

### HIGH
None.

### MEDIUM
1. **S8 UI assertions do not establish the advertised outcome** — tests/test_attacker_cost_dashboard.py:26–34 checks only zero exceptions, one success widget, and two JSON widgets. S2 has the same shape and would pass if S8 were accidentally routed to S2. Check the rendered structured decision/reject_stage/unit/epoch values. This is a coverage weakness, not an observed implementation bug.

### LOW
None remaining in this pass.

### Resolved during review
- Added `test_s8_verifies_both_responses_in_next_epoch` observes the real verifier's current epoch, response epoch and revocation membership while delegating to the original verifier. It closes the missing E+1 scenario-wiring coverage without faking decisions or pinning prose.
- Reopened refreshed `s4-iphone-14-light-top.png`: sidebar is closed, matching dark top state.
- Reopened refreshed `s8-desktop-dark.png`: S8 is selected and both ACCEPT_FRIEND and REJECT/REVOKED are visible, with response epoch 100 and verifier epoch 101.

## Correctness conclusions

- S8 constructs a key at E, signs an E response, verifies with current_epoch E+1, then adds the same CAP to the same verifier's revocation set and responds to a fresh nonce. Actual results are ACCEPT_FRIEND then REJECT/REVOKED. No substitute TAG or EPOCH rejection is used.
- Default run_all retains S1–S7, with S8 opt-in and appended after the original RNG sequence. CLI opts in. Existing S4 TAG expectation remains the falsely claimed current-epoch case.
- S2 consumed nonce probability is zero; fresh nonce collision is separately labeled. S5 tag guessing derives from TAG_BITS. S6 derives a Hamming-ball/list probability with stated assumptions. No invented operational cost is introduced.
- S3 uses each CSV reject-rate complement; unknown relay/time values remain blank numerically. Nominal boundary is budget minus base round trip (~30.674 microseconds), independent of jitter; observed rates remain jitter-dependent. UI explains the distinction.
- S4 bound is (1 + grace) * epoch duration = 1200 seconds by default, with no-new-key and regular-rotation assumptions explicitly rendered in cost details and exports. The verifier remains epoch-input-driven and no wall-clock enforcement is claimed there.

## Skill-perspective check

Loaded and applied omo:remove-ai-slops, omo:programming and its Python reference, plus visual-qa G–J. No deletion-only tests, requested-removal pins, prompt-prose tests, untyped escape hatches, unnecessary normalization, or speculative production abstraction found in the scoped new modules. CSV parsing is required by the requested derived-cost boundary. New frozen/slotted AttackCost is appropriate. Probability tests generally use independent math or changed config inputs; UI-to-export comparisons test routing/display consistency and are complemented by numeric unit tests. The remaining MEDIUM gap above violates the skills' behavioral-test perspective by overstating what S8 assertions establish. It does not demonstrate a present product failure and does not block approval. Existing loose typing/large baseline modules were not treated as a mandate for unrelated refactoring.

## Visual QA G–J (scoped functional pass)

PASS below means source/AppTest/static-capture evidence for the new CP4 surface; it does not certify unobserved native framework interaction timing. No browser keyboard trace, animation clip or accessibility-tree dump was supplied.

| Item | Verdict | Evidence / scope |
|---|---|---|
| G1 | N/A | New panel adds no authored animation. |
| G2 | N/A | No authored moving/resizing transition. |
| G3 | N/A | No authored animation/input gate. |
| G4 | N/A | No authored motion requiring a reduced-motion variant. |
| G5 | N/A | Native Streamlit control timing not measured; AppTest confirms selection completes. |
| G6 | PASS | Source renders the actual panel directly, no splash or deferred media; settled desktop/phone captures. Dynamic timing not measured. |
| G7 | PASS | Static content, no authored flashing/looping media in source. |
| H1 | PASS (empty state) | Missing sweeps produce derived fallback/unknown rows plus next-step command at panel lines 39–41; missing-sweep test passes. Framework offline/error states not independently exercised. |
| H2 | N/A | No new custom asynchronous/loading UI; native rerun behavior not timed. |
| H3 | PASS | Selection changes inline rows; S8 displays decision objects and match result. No added toast. |
| H4 | N/A | No new modal alert. |
| H5 | PASS (observed focus) | Cost selector has visible focus outline in desktop light/dark S4 captures; native hover/pressed/disabled behavior not exhaustively exercised. |
| H6 | N/A | No new sheet or modal. |
| H7 | N/A | Cost derivation is synchronous and small; no new long operation. |
| H8 | N/A | No permission request. |
| H9 | N/A | No authentication flow. |
| H10 | N/A | No new search surface. |
| H11 | N/A | No new settings toggle. Caption clearly separates saved/default costs from sidebar experiment parameters. |
| I1 | PASS (observed focus) | Labeled selector shows ring; source introduces no focus manipulation or destructive default. Full tab traversal unverified. |
| I2 | N/A | No custom key overrides or modal; native menu Escape/Enter unverified. |
| I3 | PASS (control labels) | Download and selectbox have explicit text names; new surface has no meaningful images or authored icon-only buttons. Full accessibility tree unverified. |
| I4 | PASS | New functionality uses explicit button/select controls, not gesture-only actions. |
| I5 | N/A | No autoplay media. |
| J1 | N/A | Browser app, not native macOS app. |
| J2 | N/A (native control limitation) | New control is a Streamlit selectbox; compact expanded-control state/inputmode not captured. No new numeric input or collapsing title. |

Functional verdict: PASS with the stated nonblocking test weaknesses. This report does not replace the separate A–F visual/layout verdict or claim universal G–J accessibility certification. The mobile light-top comparability issue was repaired and the refreshed capture was independently viewed.
