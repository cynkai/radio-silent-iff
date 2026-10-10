# IFF dashboard UI conventions

## 1. Identity
An operational simulation dashboard, built with the existing Streamlit component system.
The cost panel presents derived values, their conditions, and their provenance together.

## 2. Color
Use Streamlit theme background, secondary background, text, and primary colors.
The cost panel introduces no custom colors; both built-in themes remain supported.

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
No custom animation or interaction library is introduced.

## 7. Surfaces
Use Streamlit's existing theme surfaces and component borders without added shadows or decorative borders.

## 8. Accessibility and scope
Preserve the framework's semantic controls. Verify the cost panel at phone and desktop sizes in both themes.
Existing unrelated dashboard styling is outside this feature's scope.
