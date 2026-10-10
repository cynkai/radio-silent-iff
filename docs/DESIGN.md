# IFF operator console design

The existing Streamlit dashboard supplies tabs, controls, data tables, and Plotly charts.
The redesign prioritizes an event-backed radar and inspection pane over repeated pipeline charts.
No additional dependencies, contact synthesis, or automatic animation are permitted.

## Console tokens

- Background #0b1118; panel #111c28; raised surface #182637; grid #2b3b4e.
- Text #e5edf5; secondary text #9aafc4; accept #51d69a; reject/high #ff7a86.
- Medium #edc56b; low/accent #81b7ee; unreached #78899c.
- System sans-serif with Korean fallbacks; tabular numbers; body 16px, labels 14px,
  title 32px; spacing 4/8/12/16/24/32px; corners 8px.
- Chart heights: radar 480px, gauge 160px, epoch timeline 340px.

## Console layout and states

The supporting-pane pattern keeps detail next to the radar, with no nested scroll owner:
https://github.com/changeroa/StyleGallery/blob/main/patterns/split-sidebar/supporting-pane.md
The Streamlit document owns page scrolling. Desktop uses a 2:1 radar/detail split,
with a 3:2 event/alert split below; Streamlit columns stack at compact widths.
At phone widths KPI values use a 2x2 grid and the document has 64px top clearance.
Navigation stays in five tabs. Analysis controls live in the collapsible sidebar.
KPI values and radar contacts use the visible event prefix during replay; scenario
inspection uses the selected scenario. No fake offsets resolve overlapping contacts.
The event selector and feed provide access to contacts at identical coordinates.

Replay states are empty, partially played, and complete. Next adds one event;
reset returns to empty. A changed seed restarts replay. Event selection never advances it.
C2 shows the C1 pipeline as not applicable, plus its actual C2 verdict, with no RTT gauge.
The timeline has separate S4/S8 lanes; x is verifier epoch, not fabricated elapsed time.
E+2 is a policy boundary annotation, never a synthetic EPOCH event.

## Accessibility and review constraints

Decisions use text plus color, components use shape plus text, pipeline states use
explicit symbols and labels. Controls retain Streamlit keyboard/focus behavior.
HTML interpolations are escaped. Charts have adjacent textual event information.
Korean uses word-break: keep-all; long technical identifiers may wrap.
No motion is needed. Empty feeds and missing RTT have explicit explanations.
Dark is the default console theme; user-selected light mode keeps readable controls.
Native Plotly/Streamlit rendering and their built-in accessibility remain framework constraints.

## 1. Identity
An operational simulation dashboard, built with the existing Streamlit component system.
The cost panel presents derived values, their conditions, and their provenance together.

## 2. Color
The console uses the tokens above; analysis and cost controls use Streamlit theme colors.

## 3. Typography
Use Streamlit subheader, body, caption, table, and code primitives and their default font scale.
Scientific probabilities retain significant digits rather than rounding to zero percent.

## 4. Layout
Use the existing wide layout and tabs. The cost panel is a single vertical stack.
The comparison table may scroll horizontally; selected attack details also appear as wrapping text.

## 5. Components
Reuse st.tabs, st.dataframe, st.selectbox, st.markdown, st.caption, st.info, and st.download_button.
Keep labels visible. Empty source files have an explanation and a generation command.
The selected attack exposes capability, time window, assumptions, and source beneath the overview.

## 6. Interaction
Use built-in keyboard/focus/selection states. CSV download exports the same rows shown in the panel.
No custom animation or interaction library is introduced. Next and reset use native buttons.

## 7. Surfaces
Use Streamlit's existing theme surfaces and component borders without added shadows or decorative borders.

## 8. Accessibility and scope
Preserve the framework's semantic controls. Verify the cost panel at phone and desktop sizes in both themes.
Existing unrelated dashboard styling is outside this feature's scope.

## Situation briefing
The console starts with a native bordered Streamlit container for interpretation only.
Use existing badge tokens, wrapping body text, and tertiary buttons as evidence links.
Unverified findings use the secondary text token plus strikethrough and an explicit label.
Evidence selection updates the existing detail selector without advancing replay.
Cached examples are explicitly labeled; verification always uses the visible logs.
Summary and recommendations are labeled as interpretation outside the finding count.
