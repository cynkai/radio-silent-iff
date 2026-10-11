# IFF operator console design

## Guided experiment extension
Reuse the existing dark surfaces, cyan actions and decision colors. Presets use a
two-column button cluster that stacks on mobile. Results always come from the
engine at runtime. Conditional input groups retain visible labels. Radial tick
labels stay horizontal on the left, without a zero label at the origin.
The tour uses a bordered explanation card, native previous/next/exit controls,
and a progress bar. Each of nine scenes selects existing engine scenarios and
reuses radar/detail; the captured-aircraft scene also highlights the timeline.

The existing Streamlit dashboard supplies tabs, controls, data tables, and Plotly charts.
The redesign prioritizes an event-backed radar and inspection pane over repeated pipeline charts.
No additional dependencies or contact synthesis are permitted. The animation extension below
supersedes the original static presentation rules at the user's explicit request.

## Event replay visual system · A–E

The signature is a luminous optical exchange on an instrument panel: directional cyan
light, machined SVG endpoints, dark inset tracks, and an unambiguous verdict. Existing
IBM Plex typography and semantic colors remain. Primary surfaces use #162534 with a
subtle top light; secondary #111c28; informational #0e1721. A 32px grid at 3% opacity
adds context without resembling a sensor measurement. Titles 32/24px, numbers 36px,
body 14–16px and supporting labels 12px establish hierarchy.

Reusable vanilla SVG/JS primitives live in a components.v1.html document with escaped
engine JSON. The protocol exchange, six gates, SVG radar and count-up each expose a
keyboard-accessible replay button. Motion is a single illustrative replay, never a
physical time scale or a decision engine. prefers-reduced-motion renders the complete
static state, including after replay; offscreen documents pause. Transform and opacity
carry packets/fades. The maximum illustrative exchange duration is 7 seconds.

Mobile uses vertical endpoint/gate layouts and wrapping text, with no horizontal scroll.
Native Streamlit selectors remain accessible outside frames. Frame contents never read
parent DOM or modify engine/session state. Alert stripes are an explicit user requirement.
Simulation and decorative-sweep disclosures are visible within visualizations.

Reference mechanisms: beui.dev motion primitives (reduced-motion state), react-bits
CountUp (elapsed-time interpolation to an input target), existing supporting-pane layout.
No source files or dependencies are vendored. Baseline and per-phase rendered timings,
console errors, motion frames and reduced-motion evidence are recorded in visual QA.

## Console tokens

- Background #0b1118; panel #111c28; grid #2b3b4e. Two dark surface levels.
- Text #e5edf5; secondary text #9aafc4; accept #51d69a; reject/high #ff7a86.
- Accent #5ad4e6; medium/low use accent; no response/unreached #9aafc4.
- Google Fonts IBM Plex Sans KR for body, IBM Plex Mono for numbers, IDs and hex;
  tabular numbers; body 16px, labels 14px, title 28px; spacing 4/8/12/16/24/32px;
  corners 8px. Chart labels use IBM Plex Mono with the Korean body fallback.
- Streamlit's theme base font is Mono for canvas dataframe cells; body, labels,
  headings and captions explicitly use Sans KR. Code uses Mono. Mobile captions
  are 12px and stacked panel gaps are 16px.
- Chart heights: radar 400px, gauge 160px, epoch timeline 340px.
- Compact gray disclosure strip (12px), unchanged disclosure copy; 16px desktop
  top inset. Value proposition and three native navigation buttons precede KPIs.
- KPI cards have one caption under the number; only high alerts have a red border.
- Radar labels can move along leader lines; contact coordinates never move.
- Alert titles are prominent Korean labels; original English messages appear below
  in muted 13px monospace, with every original message retained.

## Console layout and states

The supporting-pane pattern keeps detail next to the radar, with no nested scroll owner:
https://github.com/changeroa/StyleGallery/blob/main/patterns/split-sidebar/supporting-pane.md
The Streamlit document owns page scrolling. Desktop uses a 2:1 radar/detail split,
with a 3:2 event/alert split below; Streamlit columns stack at compact widths.
At phone widths KPI values use a 2x2 grid and the document has 16px top clearance.
Navigation wraps, radar and detail stack, and long identifiers wrap without page overflow.
The default workspace keeps five tabs. Three guide buttons directly select replay,
experiments or limits; initial detail selects the existing S4 REVOKED event.
A visible native workspace radio opens the experiment
workspace with red-team sandbox and engagement traffic tabs. Analysis controls live in the collapsible sidebar.
KPI values and radar contacts use the visible event prefix during replay; scenario
inspection uses the selected scenario. No fake offsets resolve overlapping contacts.
The event selector and feed provide access to contacts at identical coordinates.

Replay states are empty, partially played, and complete. Next adds one event;
reset returns to empty. A changed seed restarts replay. Event selection never advances it.
C2 shows the C1 pipeline as not applicable, plus its actual C2 verdict, with no RTT gauge.
The timeline has separate S4/S8 lanes; x is verifier epoch, not fabricated elapsed time.
E+2 is a policy boundary annotation, never a synthetic EPOCH event.

## Accessibility and review constraints

The experiment workspace reuses existing tokens, native form controls, radar and RTT
charts. Forms submit explicitly; the last submitted configuration remains visible.
Six pipeline rows distinguish passed, blocked and unreached stages, including all
unreached stages for suppressed queries. An accepted attack has an explicit failure
message and a README limits link. Traffic tables use evidence-event metrics, with a
separate paired BER chart. No new color, motion or layout primitives are required.
Briefings use an explicit generation button and a shared five-request session ledger.

Decisions use text plus color, components use shape plus text, pipeline states use
explicit symbols and labels. Controls retain Streamlit keyboard/focus behavior.
HTML interpolations are escaped. Charts have adjacent textual event information.
Korean uses word-break: keep-all; long technical identifiers may wrap.
No motion is needed. Empty feeds and missing RTT have explicit explanations.
Dark is the requested console theme. Streamlit chrome is hidden; the sidebar starts collapsed.
Native Plotly/Streamlit rendering and their built-in accessibility remain framework constraints.

## 1. Identity
An operational simulation dashboard, built with the existing Streamlit component system.
The cost panel presents derived values, their conditions, and their provenance together.

## 2. Color
The console uses the tokens above; analysis and cost controls use Streamlit theme colors.

## 3. Typography
Use Streamlit subheader, body, caption, table, and code primitives with the console font tokens.
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
The briefing follows the radar and event/alert feed in a native bordered container for interpretation only.
Use existing badge tokens, wrapping body text, and tertiary buttons as evidence links.
Unverified findings use the secondary text token plus strikethrough and an explicit label.
Evidence selection updates the existing detail selector without advancing replay.
Cached examples are explicitly labeled; verification always uses the visible logs.
Summary and recommendations are labeled as interpretation outside the finding count.

## 심화 실험

기존 실험 탭에 심화 탭을 추가한다. 경계 sweep은 시안 선과 현재 판정색 점,
포획 구간은 수락 초록·거부 빨강을 사용한다. 모바일 비교 열은 세로로 쌓는다.

## 운용자 질문

브리핑 아래 질문 카드와 검증 배지를 배치한다. 모든 답변 문장 아래에 이벤트 ID를
표시하고, 조회 범위나 원문 사실 대조에 실패한 문장은 기존 회색 취소선 스타일을 쓴다.
JSON 필터는 접힌 상세 영역에 표시한다. 예시도 현재 엔진 로그로 생성한다.

## 교전 시간과 성능

시간 스크러버 아래 레이더·시점 경보를 나란히 배치하고 모바일에서 세로로 쌓는다.
탐지율/오탐률 막대와 BER 곡선은 하나의 2행 그림으로 함께 읽게 한다.
경보 패널은 고정 높이의 세로 스크롤을 사용한다. 성능 집계는 전체 표본임을 명시한다.

## 시각 위계와 재생

주 카드는 프로토콜·검증 파이프라인의 밝은 표면과 은은한 상단광을 사용한다.
레이더·KPI는 중간 밝기, 경보·근거 정보는 가장 어두운 카드로 구분한다.
배경 격자는 40px 간격, 시안의 약 1% 불투명도로 제한한다.
제목 36px, 섹션 24px, KPI 숫자 36px, 보조 정보 11–13px로 대비를 만든다.
KPI는 엔진 집계까지 1.6초 동안 카운트업하며 접근성 이름은 최종 집계를 제공한다.
390px에서는 KPI 2열, 프로토콜·파이프라인 세로 배치다.
판정과 R1–R7 아이콘은 `iff/visual_icons.py`의 같은 인라인 SVG 세트를 사용한다.
포커스는 시안 외곽선, hover는 표면 밝기 변화로 표시한다. 모션 감소 설정은 모든
재생을 최종 정지 화면으로 대체하고 CSS 애니메이션·전환도 비활성화한다.
