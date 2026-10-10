# Cost panel visual review

recommendation: APPROVE (scoped native-Streamlit contract)
verdict: PASS for scoped readability; not an unqualified visual-qa checklist PASS
confidence: HIGH for the visible findings; limited for unrecorded interactions

Scope: new `iff/attacker_cost_panel.py` and S4 cost copy only. This is an extension of native Streamlit, not a reference clone. `DESIGN.md` is the design contract. Existing title/sidebar/tab styling is outside scope. No implementation files were changed.

## Findings by severity

### CRITICAL
None.

### HIGH
None remaining. The original obstructed mobile light top capture was replaced at 02:43:34; I reopened the replacement and verified that its sidebar is closed, the panel is unobstructed, and it matches the dark capture state.

### MEDIUM
None under the clarified native-Streamlit scope.

### LOW
- [product, polish] Korean words break mid-word in the new panel at 390 CSS px. Both `s4-iphone-14-{light,dark}-end.png` show `포획 시점 / 에 따라` and `입력받 / 으며` in S4 notes. `s4-iphone-14-dark-top.png` also shows `파라미터 / 와` in the introduction and `유도 / 할 수 없는` in the probability explanation. Locations: `iff/attacker_cost_panel.py:12`, `:13`, `:31`; S4 source copy `iff/attacker_cost.py:79`. The full copy remains readable: no missing glyphs, overlap or prose truncation is visible. Natural word wrapping would improve linguistic polish, but the parent clarified that native wrapping is accepted for this functional feature and bespoke style changes are outside scope. This is therefore nonblocking under that contract. Strict skill item C5 remains unmet; this is not an unqualified pass of every skill rule.

Native dataframe clipping/horizontal scrolling is permitted by DESIGN.md and is compensated by wrapping selected detail text; it is not raised as a defect.

## Design-system integrity

The panel is a real Streamlit component tree: subheader/caption/body, download button, dataframe, selectbox, selected details and sources (`iff/attacker_cost_panel.py:11-38`). All five scenario summaries and selected rows derive from `write_attacker_cost`; there is no raster screenshot, CSS background-image, hardcoded color, spacing or font override in this component. Framework primitives provide the shared theme and spacing system. The one-column sequence matches DESIGN.md. Desktop S3 and S4 render coherently, and both S4 themes retain readable hierarchy and sources.

## A–F checklist disposition

PASS means visible evidence or direct source confirms the item only within this feature. N/A includes baseline-only items and checks outside the provided static evidence; limitations are explicit rather than inferred passing results.

| Item | Result | Evidence / limitation |
|---|---|---|
| A1 | PASS | Desktop top captures: aligned content stack |
| A2 | PASS | Desktop and mobile end: complete theme backgrounds |
| A3 | PASS | Symmetric panel margins; wide analytical layout follows DESIGN.md |
| A4 | N/A | Browser screenshots do not establish real-device safe areas |
| A5 | PASS | Mobile end scrollbar overlays right edge |
| A6 | PASS | Native comparison tables scroll horizontally within vertical page |
| A7 | PASS | Shared edges in all unobstructed captures; native primitives |
| A8 | PASS | Label, selector, details and sources separated consistently |
| A9 | PASS | Replacement mobile light top is unobstructed; primary text reflows without horizontal clipping |
| A10 | PASS | Tables/rows visibly continue at viewport/table edges |
| A11 | N/A | Existing app/sidebar window behavior outside scope |
| B1 | PASS | Single export action in new panel |
| B2 | N/A | No destructive actions |
| B3 | PASS | New panel title clearly names its content |
| B4 | PASS | Summary followed by selectable details and provenance |
| B5 | PASS | Existing Streamlit primary accent only |
| B6 | PASS | Native heading/body/caption hierarchy in both themes |
| C1 | N/A | Uses contract-mandated native font scale; exact computed font sizes not recorded |
| C2 | PASS | Technical values/identifiers belong to this analytical tool and provenance |
| C3 | PASS | CSV download has clear outcome label |
| C4 | PASS | New heading fits; selected detail wraps; dataframe overflow intentionally permitted. 200% zoom not tested |
| C5 | FAIL product | New Korean copy breaks words/particles, documented above |
| C6 | N/A | Missing-file info/code source path inspected at panel lines 39-41, but no rendered empty capture |
| C7 | PASS | Selectbox label visible in desktop captures/source |
| C8 | N/A | Static captures cannot establish text selection; native text primitives used |
| D1 | N/A | Uses contract-mandated native controls; target geometry not independently measured |
| D2 | N/A | Existing tabs are outside scope |
| D3 | N/A | No new toolbar |
| D4 | N/A | No new bar buttons |
| E1 | PASS | All light/dark pairs now unobstructed and readable |
| E2 | N/A | Both themes visually readable; no quantitative AA contrast measurement provided |
| E3 | PASS | Scenario/conditions/probabilities have textual labels; no color-only encoding |
| E4 | PASS | Consistent framework theme across captures |
| E5 | N/A | No new translucent surfaces |
| E6 | N/A | Existing Streamlit theme system; setting interaction not captured |
| F1 | PASS | Native components only; no new icon set |
| F2 | PASS | Framework-managed spacing/borders/radii; source contains no overrides |
| F3 | PASS | Repeated native dataframe/text primitives visually consistent in S3/S4 |
| F4 | N/A | No branding changes in scoped panel |
| F5 | N/A | Native selected/focus states; complete state matrix not captured |
| F6 | PASS | Native selector arrow and dataframe toolbar glyphs |
| F7 | N/A | No new sheets or modal surfaces |

## Evidence inspected

- `DESIGN.md`
- Full `iff/attacker_cost_panel.py` (41 lines)
- `iff/attacker_cost.py` derivation/copy/export portions, including S4 lines 76-92
- `app.py` panel integration references
- `out/qa/s4-desktop-1440-light-top.png`
- `out/qa/s4-desktop-1440-light-end.png`
- `out/qa/s4-desktop-1440-dark-top.png`
- `out/qa/s4-desktop-1440-dark-end.png`
- `out/qa/s4-iphone-14-light-top.png`
- `out/qa/s4-iphone-14-light-end.png`
- `out/qa/s4-iphone-14-dark-top.png`
- `out/qa/s4-iphone-14-dark-end.png`
- `out/qa/cost-desktop-light-top.png`
- `out/qa/cost-desktop-light-detail.png`

All ten images opened directly. File signatures are PNG RGB, with desktop 1440×900 and mobile 1170×2532 (consistent with 390×844 at DPR3). All ten file mtimes postdate both reviewed Python sources. No black or uncomposited regions seen. No pixel target exists, so no reference image diff applies.

## Limitations

The folder is not a Git repository; no full before/after diff was available. No notepad path or objective browser metadata was supplied. Screenshot timestamps establish ordering, not a cryptographic build identity. The reported 74 tests and all-five-selection checks were not rerun by this visual reviewer. Captures cover S3 desktop and S4 desktop/mobile; they do not visually establish S2/S5/S6, the mobile selector region between top/end, empty states, 1920px, 200% zoom, quantitative contrast or interaction/focus/motion states. These limits must not be described as independently verified.

## Blockers

None under the clarified feature scope and native-Streamlit design contract. Strict checklist C5 remains a documented deviation; do not report this scoped review as an all-items visual-qa PASS. The initial capture defect is resolved in inspected replacement evidence.
