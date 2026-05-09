# Type3 Text Reverse-Engineering Notes (Revised)

This document records the current text-object reverse-engineering status and revises fixture planning based on newly confirmed behavior.

Conservative policy:

- preserve Korean UI terminology exactly as observed
- distinguish confirmed observations from inferred/provisional interpretations
- avoid parser-contract claims that are not yet fixture-backed

---

## Baseline Text Fixture (Revised)

Fixture: `tests/samples/text/default_text.txt`

Confirmed baseline setup:

- visible text: `abcdefg`
- font: `Arial`
- alignment default: `중앙 (center alignment)`
- color default: black `000000`
- `높이 (height)`: `10 mm`
- `폭 (width)`: `100%`
- `회전 (rotation)`: `0`
- `기울기 (slant)`: `0`
- `간격 (spacing)`: `100%`
- `미러 (mirror)`: OFF
- `밑줄 (underline)`: OFF
- multiline: OFF

Notes:

- Korean UI terms are primary. English aliases are helper labels only.
- This fixture remains the baseline comparison anchor for text-object deltas.

---

## Newly Confirmed Multiline Behavior

### Confirmed observations

- Type3 text objects can contain multiple lines using Enter/newline input.
- Multiline text behavior is not identical to single-line text behavior.
- Single-line text objects cannot be `결합 해제`.
- Multiline text objects can be `결합 해제`.
- After `결합 해제`, each line becomes an independent text object.

### Inferred / provisional interpretation

- The observed `결합 해제` behavior suggests multiline text may internally behave like grouped text entities.
- This is a working architectural hypothesis, not yet a finalized internal schema claim.

---

## Text Fixture Strategy Revision

Additional fixtures are now required because text analysis must separate multiple interacting factors:

- color isolation:
  isolate color-only changes to locate text-side `CPropertyExtend` style fields and compare against rectangle color evidence.
- visible text isolation:
  isolate string-only changes to locate string payloads and length/count metadata.
- multiline/group behavior:
  compare grouped multiline vs `결합 해제` output to identify decomposition metadata and object-boundary changes.
- font comparison:
  keep text and layout fixed while changing font to isolate font-name storage and glyph/contour side effects.
- volatile field identification:
  repeat near-identical captures to separate stable semantic fields from session/object-noise ranges.

---

## Planned Fixture Definitions

### Color fixtures

- `text_color_blue.txt`
- `text_color_green.txt`
- `text_color_cyan.txt`
- `text_color_light_cyan.txt`

Fixture intent:

- geometry unchanged
- only color changes
- intended for `CPropertyExtend` analysis
- intended for comparison with rectangle color fixtures

### Visible text fixtures

- `text_value_TEST.txt`
- `text_value_1234567.txt`
- `text_value_A1b2C3.txt`

Fixture intent:

- only visible text changes
- all geometry/style settings fixed
- intended for locating stored string payloads and length fields

### Multiline fixture

- `text_multiline_2lines.txt`

Content:

- line1: `abc`
- line2: `def`

Investigation targets:

- line-separator encoding
- bbox expansion behavior
- line-spacing-related fields
- internal record grouping hints

### Multiline ungroup fixtures

- `text_multiline_2lines_grouped.txt`
- `text_multiline_2lines_ungrouped.txt`

Fixture intent:

- grouped version: original multiline text object
- ungrouped version: state after `결합 해제`
- intended for studying internal group/object decomposition behavior

---

## Recommended Capture Rules

- change exactly one primary variable per fixture
- prefer a new document/session when feasible
- run one logical experiment per clipboard capture
- preserve raw clipboard bytes
- avoid manual normalization beyond whitespace cleanup
- preserve Korean UI terminology exactly in metadata
- avoid hidden-object selection contamination

Operational note:

- if multiline controls force coupled changes, record the effective comparison baseline explicitly.

---

## Current High-Priority Reverse-Engineering Targets

- visible string storage
- font name storage
- bbox encoding
- multiline representation
- group decomposition metadata
- color field storage
- text transform fields
- contour-vs-glyph storage model investigation

---

## Next Recommended Fixture Creation Order

1. `text_color_blue.txt`
2. `text_color_green.txt`
3. `text_color_cyan.txt`
4. `text_color_light_cyan.txt`
5. `text_value_TEST.txt`
6. `text_value_1234567.txt`
7. `text_value_A1b2C3.txt`
8. `text_multiline_2lines.txt`
9. `text_multiline_2lines_grouped.txt`
10. `text_multiline_2lines_ungrouped.txt`
