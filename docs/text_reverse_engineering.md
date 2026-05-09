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
- baseline coordinate control uses text reference anchor, not bbox lower-left:
  - `X 위치 (text reference anchor X) = 111.111 mm`
  - `Y 위치 (text reference anchor Y) = 222.222 mm`
  - `Z 위치 (text reference anchor Z) = 0.000 mm`

Anchor vs bbox policy (confirmed capture policy):

- do not expect bbox lower-left to remain fixed across text fixtures
- do not normalize/move text objects merely to force bbox lower-left `(0, 0, 0)`
- keep `X 위치` / `Y 위치` as the controlled coordinate
- treat bbox as observed/derived geometry
- this distinction is important with default `중앙 (center alignment)`

### Confirmed vs provisional (anchor)

Confirmed:

- Type3 Text mode has real UI fields: `X 위치`, `Y 위치`, `Z 위치`.
- Fixtures were created by explicitly setting those anchor values (for example `(111.111, 222.222, 0.000)` mm).
- Text fixture comparison baseline is anchor position, not bbox lower-left.

Provisional:

- exact binary payload offsets for the anchor fields
- parser extraction path for anchor values (`direct_field` vs structural recovery)
- binary-to-UI mapping confidence for each fixture family

Current parser status:

- anchor values are currently recovered via structural method (`baseline_midpoint`) in many fixtures.
- this method is not the same claim as direct binary anchor-field decoding.

Anchor metadata layering (for parser/model/inspector):

- expected/source layer: `text_anchor_expected_source` (example: `confirmed_from_fixture_setup`)
- parser-method layer: `text_anchor_parse_method` (examples: `baseline_midpoint`, `bbox_center_fallback`, `direct_field_candidate`, `unknown`)
- parser-confidence layer: `text_anchor_parse_confidence` (examples: `provisional`, `candidate`, `fallback`, `direct_confirmed`)

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

Order 40/41/42 fixture purpose:

- these fixtures use `abcd\nefgh`
- they are for multiline encoding, line-break representation, object order, and grouped/multiline decomposition checks
- they should test whether `abcd\nefgh` is stored as one paragraph-like object or multiple internal text runs

---

## Case Mode Notes

### `작은 대문자 (small caps mode)` - observed behavior

Source input text used in fixture:

- `abcdefg`

Observed Type3 behavior:

- letters are displayed as uppercase-like forms
- first `A` appears visually larger
- following letters appear smaller

Conservative interpretation:

- this is not equivalent to plain uppercase rendering
- behavior is consistent with a small-caps-like mode, but internal storage semantics remain provisional

### `소문자 (lowercase mode)` - fixture design note

Source input text used in fixture:

- `ABCDEFG`

Then `소문자` option is enabled.

This fixture is intentionally designed to test whether Type3 stores:

- original typed text
- transformed visible text
- mode flag only
- or a combination of these

Current status:

- unresolved; do not assume one model yet

Parser TODO:

- expose `source_text_candidate` vs `display_text_candidate` separately when both are detectable.
- keep case-mode semantics provisional until binary mapping is verified across fixtures.

---

## Two-Text-Object Fixture Policy

Two-text-object fixtures are used to validate per-object extraction and ordering behavior.

Text object #1 baseline:

- reference anchor: `(111.111, 222.222, 0.000)` mm
- visible/source text: `abcdefg`
- default text settings:
  - text height: `10 mm`
  - width scale / `폭`: `100%`
  - other settings default unless fixture name states otherwise
- color: `Army Green`

Text object #2 baseline:

- reference anchor: `(211.111, 322.222, 0.000)` mm
- visible/source text: `1234567890`
- color by fixture:
  - same-color fixture: `Army Green`
  - different-color fixture: `Navy Blue`

Validation goals:

- multi-text-object detection
- per-object anchor extraction
- per-object visible/source text candidate extraction
- per-object color extraction
- object order preservation
- no accidental merge of two text objects into one

Current color-ownership status:

- same-color two-object fixtures are useful for sanity validation.
- mixed-color per-object ownership remains provisional and should not be treated as fully confirmed.

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

## Captured Fixture Inventory (Current)

Current inventory baseline:

- directory: `tests/samples/text/`
- total fixtures: `53`
- parser-detected chain count (`parsed_chain_candidate_count`):
  - single-object text fixtures: majority
  - chain-count=2 fixtures (parser candidate count only, not confirmed Type3 object count):  
    `text_group_same_color_two_objects.txt`,  
    `text_group_mixed_color_two_objects.txt`,  
    `text_two_objects_mixed_color_not_grouped.txt`,  
    `text_multiline_basic.txt`,  
    `text_spacing_fixed.txt`,  
    `text_spacing_proportional.txt`,  
    `text_spacing_print_proportional.txt`
- multiline evidence fixtures (`abcd\nefgh` candidate):  
  `text_multiline_basic.txt`, `text_spacing_fixed.txt`, `text_spacing_proportional.txt`, `text_spacing_print_proportional.txt`

### Color fixtures (captured)

- `text_color_army_green.txt`
- `text_color_navy_blue.txt`
- two-object color fixtures:
  - `text_group_same_color_two_objects.txt`
  - `text_group_mixed_color_two_objects.txt`
  - `text_two_objects_mixed_color_not_grouped.txt`

Current status:

- single-object text color parser output still often resolves to `Black` even when fixture name indicates non-black.
- mixed-color per-object ownership remains provisional.

### Visible text fixtures (captured)

- `text_alphanumeric.txt`
- `text_digits.txt`
- `text_ascii_lowercase.txt`
- `text_ascii_uppercase.txt`
- `text_spaces.txt`
- `text_special_characters.txt`
- `text_korean_basic.txt`
- `text_korean_mixed.txt`

Current status:

- ASCII candidates are extracted conservatively in many fixtures.
- Korean text payload extraction is still unresolved in current parser output (`visible_text_candidates` may be empty).

### Case/style/layout fixtures (captured examples)

- alignment: `text_align_left.txt`, `text_align_center.txt`, `text_align_right.txt`, `text_align_justify.txt`, `text_align_free_position.txt`
- transform: `text_rotation_30deg.txt`, `text_rotation_90deg.txt`, `text_slant_15deg.txt`, `text_slant_custom_30deg.txt`, `text_mirror_on.txt`
- spacing/width/height: `text_spacing_80_percent.txt`, `text_spacing_150_percent.txt`, `text_width_50_percent.txt`, `text_width_150_percent.txt`, `text_height_10mm.txt`, `text_height_30mm.txt`
- mode: `text_small_caps_mode.txt`, `text_lowercase_mode.txt`, `text_uppercase_mode.txt`, `text_rtl_on.txt`, `text_subscript.txt`, `text_superscript.txt`, `text_baseline_above.txt`, `text_baseline_below.txt`, `text_underline_on_default.txt`
- position/baseline anchor checks: `text_origin_0_0.txt`, `text_origin_offset.txt`, `text_offset_10_percent.txt`

### Font fixtures (captured)

- `text_font_arial.txt` (expected: `Arial`)
- `text_font_arial_bold.txt` (expected: `Arial Bold`)
- `text_font_hy_gyeongo_dik.txt` (expected: `HY견고딕`)
- `text_font_hy_teuktae_gothic.txt` (expected: `HY특태고딕`)
- `text_font_hy_tae_gothic.txt` (expected: `HY태고딕`)
- `text_font_hy_se_gothic.txt` (expected: `HY세고딕`)

Observed parser status (current):

- `text_font_arial.txt`: parser font candidate `Arial`
- `text_font_arial_bold.txt`: recapture mismatch resolved; now single-line text `abcdefg`, multiline evidence `abcd\nefgh` no longer observed
- HY font fixtures: parser font candidate unresolved (`None`) in current conservative extraction

Provisional:

- exact Korean font-name binary encoding rules
- stable binary offsets for font name storage across all font families

### Missing planned fixtures
- previously planned names do not exist yet in current folder:
  - `text_color_blue.txt`, `text_color_green.txt`, `text_color_cyan.txt`, `text_color_light_cyan.txt`
  - `text_value_TEST.txt`, `text_value_1234567.txt`, `text_value_A1b2C3.txt`
  - `text_multiline_2lines.txt`, `text_multiline_2lines_grouped.txt`, `text_multiline_2lines_ungrouped.txt`

---

## Parser Limitations (Current)

- declared object count from text fixtures is often unavailable (`declared_object_count = None`).
- text anchor is currently recovered by structural methods (mostly `baseline_midpoint`), not confirmed direct binary field decode.
- single-text color ownership is provisional; non-black fixtures may still resolve to `Black` in selected fields.
- mixed-color two-object ownership is provisional and should not be asserted as stable per-object mapping.
- Korean visible text decoding is incomplete in current conservative extraction path.
- multiline internal storage model (single paragraph-like record vs multiple text runs) is still provisional.
- per-object text-run ownership in multi-object text fixtures remains provisional in heuristic mapping paths.
- text color ownership for mixed two-object fixtures remains provisional.

---

## Text color fixtures and ownership

Confirmed fixture intent:

- `text_color_army_green.txt`: `Army Green`
- `text_color_navy_blue.txt`: `Navy Blue`
- `text_group_same_color_two_objects.txt`: object #1 `Army Green`, object #2 `Army Green`
- `text_group_mixed_color_two_objects.txt`: object #1 `Army Green`, object #2 `Navy Blue`
- `text_two_objects_mixed_color_not_grouped.txt`: object #1 `Army Green`, object #2 `Navy Blue`

Observed parser output (current):

- single text color fixtures (`text_color_army_green.txt`, `text_color_navy_blue.txt`) still often yield `Black` in selected color fields.
- grouped same-color fixture yields `Army Green` candidates on both parsed chains.
- mixed-color fixtures can yield one dominant candidate (`Navy Blue` or `Army Green`) across both chains depending on payload candidate selection.

Provisional:

- exact per-object mixed-color ownership mapping
- stable text-specific `CPropertyExtend` offset rules equivalent to rectangle fixtures
- whether candidate order in payload scan is semantic or volatile

## Offset policy for text reverse engineering

Confirmed:

- Type3 text-object payload is dynamic by text length, font, line count, object count, and style options.
- Therefore, absolute byte offsets (example: `offset=634`) are evidence locations from a specific fixture, not parser rules.

Observed:

- color diff tools can repeatedly show palette-like values at absolute offsets in specific fixtures.
- those repeated offsets are useful diagnostics, but they shift when structure/length changes.

Provisional:

- parser rules should be built from class boundary / payload boundary / record boundary.
- absolute offsets remain `diagnostic only` until class-relative or record-relative mapping is validated.

## Target model: class-relative and record-relative parsing

- primary target: `CParagraphe` internal record boundary detection
- secondary target: style/run record candidate extraction
- validation target: color/font/height/slant/spacing as record-relative fields
- current color diff output is evidence, not confirmed parser mapping

## CParagraphe structure investigation

Current goal:

- this phase is record-boundary discovery, not final value decoding.

Policy:

- absolute offset is diagnostic only.
- prioritize `class_payload_relative_offset` and `record_relative_offset`.

Observed:

- color/font/height/slant/spacing signals appear as candidate evidence inside `CParagraphe` payload scans.
- candidate offsets can move when text length/font/line count/object count changes.

Provisional:

- no confirmed field mapping for color/font/height/slant/spacing yet.
- current candidates remain structural hypotheses until cross-fixture record-relative stability is shown.

Next confirmation criteria:

1. same record-relative offset repeats across multiple fixtures.
2. single-option-change fixtures modify only the corresponding candidate field.
3. record-relative position remains stable even when text length/font/line count/object count changes.

---

## Fixture Issues (Current)

- color-only fixtures:
  - `text_color_army_green.txt`, `text_color_navy_blue.txt` expected color vs detected color mismatch is currently treated as parser limitation, not fixture corruption.
- font fixtures:
  - `text_font_arial_bold.txt` recapture mismatch is resolved, but bold font candidate extraction is still unresolved in parser output.
- HY font fixtures:
  - expected HY font vs detected font mismatch is currently treated as parser limitation, not fixture corruption.

---

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

## Next Recommended Fixture Creation / Recapture Order

1. Capture missing explicit color-isolation set:  
   `text_color_blue.txt`, `text_color_green.txt`, `text_color_cyan.txt`, `text_color_light_cyan.txt`.
2. Capture missing explicit visible-text isolation set:  
   `text_value_TEST.txt`, `text_value_1234567.txt`, `text_value_A1b2C3.txt`.
3. Capture explicit multiline grouped/ungrouped pair:  
   `text_multiline_2lines_grouped.txt`, `text_multiline_2lines_ungrouped.txt`.
4. Re-run inventory and update parser ownership expectations for mixed-color two-object fixtures.
