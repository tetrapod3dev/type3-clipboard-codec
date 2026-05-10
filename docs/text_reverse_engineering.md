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

## CParagraphe 204-byte record candidate

Observed:

- in many single-line fixtures, a repeated candidate appears as:
  - `candidate_start_offset=47`
  - `candidate_stride=204`
  - `candidate_record_count=10`
- in multiline fixture (`text_multiline_basic.txt`), alternate start candidates appear and require additional validation.

Current objective:

- build a provisional record-relative field map from `record_index` + `record_relative_offset`.
- this phase is not final semantic decoding.

Policy:

- absolute offset is diagnostic only.
- parser keeps text style/color/font as candidate-level evidence, not confirmed fields.

Provisional verification criteria for future promotion:

1. same option-change fixtures repeatedly change the same `record_relative_offset`.
2. the same record-relative candidates remain stable when bbox/payload length/text length changes.
3. multi-object and multiline cases are explainable with the same model.
4. parser regression tests keep existing geometry/text extraction stable.

## CParagraphe record-relative field candidate map

Record model status:

- baseline candidate remains `start_offset=47`, `stride=204`.
- this is still an observed/provisional model, not confirmed decoding.

Paired comparison strategy (summary-first analyzer output):

- analyzer compares option pairs first, then ranks `record_relative_offset` candidates.
- primary pair sets:
  - height: `text_height_10mm` vs `text_height_30mm`
  - width: `text_width_50_percent` vs `text_width_150_percent`
  - slant: `text_slant_15deg` vs `text_slant_custom_30deg` + baseline comparisons
  - spacing: `text_spacing_80_percent` vs `text_spacing_150_percent` + baseline comparisons
  - rotation: `text_rotation_30deg` vs `text_rotation_90deg` + baseline comparisons
  - color: `text_color_army_green` vs `text_color_navy_blue` + baseline comparisons
  - font: Arial/HY comparison pairs
  - text value: lowercase/uppercase/digits/alphanumeric pairs
  - multiline: `default_text` vs `text_multiline_basic`

Evidence labels:

- `strong_candidate`: high signal in target tag with good stability in unrelated tags
- `cross_fixture_candidate`: repeated but weaker or mixed signal
- `weak_candidate`: observed but low confidence
- `provisional`: early signal only, not ready for interpretation

Strong-candidate policy:

- repeated change in the same `record_relative_offset` for the same option tag
- repeated across multiple records when applicable
- stable in unrelated option tags
- numeric/value pattern matches expected fixture direction

Low-signal filter policy:

- all-zero blocks
- `0.0` / `1.0` doubles
- repeated padding-like bytes
- volatile identifier-like regions
- metadata marker strings (`OBJETINFOS_CLASSNAME`, `CObDao`, class labels)

Current candidate status:

- strong/cross-fixture/provisional candidates are reported from analyzer output only.
- parser fields are intentionally not promoted yet.

Top-ranked offsets from the current analyzer run:

| candidate_name | top record_relative_offset | evidence | notes |
|---|---:|---|---|
| candidate_text_height | `0x47` (71) | strong_candidate | numeric match `0.01` ↔ `0.03` observed in height pair |
| candidate_width_percent | `0x55` (85) | cross_fixture_candidate | width-only pair sensitivity observed, stability still moderate |
| candidate_slant_angle | `0x57` (87) | strong_candidate | numeric match `0.261799` / `0.523599` seen in slant comparisons |
| candidate_spacing_percent | `0x7B` (123) | strong_candidate | numeric match `0.8` observed in spacing comparisons |
| candidate_rotation_angle | `0x83` (131) | strong_candidate | numeric match `0.523599` / `1.570796` seen in rotation comparisons |
| candidate_text_color | `0x8D` (141) | strong_candidate (analyzer-only) | palette-like behavior observed, parser mapping still provisional |
| candidate_font_or_style_flag | `0x69` (105) | strong_candidate (analyzer-only) | font pairs show repeated changes, semantic meaning unresolved |
| candidate_visible_character_or_run_code | `0x3F` (63) | strong_candidate | text-value pair sensitivity high |
| candidate_linebreak_or_multiline_marker | `0x87` (135) | strong_candidate | multiline pair shows strong separation from single-line baseline |

Multiline pre-record window (47~187):

- observed as a provisional header-like window candidate in multiline fixture.
- CR/LF and selector-like evidence are inspected, but no confirmed mapping yet.

Parser non-application reason:

- record-relative stability is not fully proven across multiline/object-count/font-length variability.
- additional cross-fixture validation is required before safe parser promotion.

## CParagraphe field offset validation

Why ranked offset alone is insufficient:

- ranked `record_relative_offset` can point inside a field payload, not guaranteed field start.
- dynamic text payload layout (text/font/line/object changes) can shift local byte neighborhoods.
- parser rules require repeatable field-start evidence, not only one ranked byte.

Sliding-window validation strategy:

- for each ranked candidate, scan `offset-16 .. offset+16`.
- decode each offset as `u8/i8/u16/i16/u32/i32/float32/double64/ascii/utf16`.
- for color candidates, also test palette candidates (`TYPE3_COLORS_BY_RAW`, `TYPE3_COLORS_BY_RGB0_RAW`).
- score offsets by expected pair matches (height/width/slant/spacing/rotation/color/font).
- keep all outputs as analyzer evidence (`strong_candidate`, `cross_fixture_candidate`, `weak_candidate`, `provisional`).

Current best field-start candidates (analyzer evidence only):

| candidate_name | ranked offset | best field-start candidate | status |
|---|---:|---:|---|
| candidate_text_height | `0x47` | analyzer-derived (window score max) | provisional/strong depending on pair score |
| candidate_width_percent | `0x55` | analyzer-derived (window score max) | provisional/cross |
| candidate_slant_angle | `0x57` | analyzer-derived (window score max) | provisional/strong |
| candidate_spacing_percent | `0x7B` | analyzer-derived (window score max) | provisional/strong |
| candidate_rotation_angle | `0x83` | analyzer-derived (window score max) | provisional/strong |
| candidate_text_color | `0x8D` (`0x8B`,`0x8C` aux) | analyzer-derived (window score max) | provisional (ownership unresolved) |
| candidate_font_or_style_flag | `0x69` (`0x23`,`0xA7` aux) | analyzer-derived (window score max) | provisional (Korean font decode unresolved) |

Cross-record consistency observations:

- candidate offset is applied across full 204-byte record arrays per pair.
- analyzer reports changed/stable record counts per candidate.
- this helps separate run-level repeated fields from header/selective fields.

Parser non-application reason:

- best-start candidates are still evidence-level; record semantics not confirmed.
- mixed constraints (font/HY/multiline/color ownership) still unresolved.
- parser promotion remains blocked until cross-fixture repeatability is stronger.

Next confirmation conditions:

1. same field-start candidate remains stable across independent fixture families.
2. decoded type/value pattern stays consistent under payload-length/line-count changes.
3. multiline pre-record window behavior is explained without contradictory offsets.

Expected-value scoring update:

- changed-only scoring is insufficient because many offsets change together in dynamic payloads.
- validation now prioritizes expected-value match levels:
  - `exact` (`<=1e-9`)
  - `near` (`<=1e-6`)
  - `loose` (`<=1e-3`)
  - `changed_only`
- best field-start selection priority: `exact > near > loose > changed_only`.

Re-evaluated best field-start candidates (current analyzer evidence):

| candidate | ranked offset | re-evaluated best offset | status |
|---|---:|---:|---|
| candidate_text_height | `0x47` | `0x47` | weak/cross evidence |
| candidate_width_percent | `0x55` | `0x4F` | weak evidence |
| candidate_slant_angle | `0x57` | `0x57` | weak/cross evidence |
| candidate_spacing_percent | `0x7B` | `0x7B` | weak/cross evidence |
| candidate_rotation_angle | `0x83` | `0x83` | weak/cross evidence |
| candidate_text_color | `0x8D` | `0x8B` | cross/provisional evidence |
| candidate_font_or_style_flag | `0x69` | `0x5E` | provisional/cross evidence |

Dominant decode types (provisional):

- geometry-like numeric candidates: `double64le` / `float32le` / `u32le`
- color candidates: `u32le` + palette mapping variants (`00BBGGRR`, `00RRGGBB` family checks)
- font/style candidates: mixed numeric flag-like values with partial ASCII/UTF-16 fragments

Text color byte-order validation (single-object fixtures):

- checked candidate offsets `0x8B`, `0x8C`, `0x8D` and nearby `±8`.
- compared `text_color_army_green` vs `text_color_navy_blue`.
- current best offset candidate is observed via exact palette-name separation at record-relative level.
- mixed multi-object ownership is still unresolved and intentionally not promoted.

Parser promotion remains blocked:

- expected-value matches are still not uniformly strong across all records/fixture families.
- font/HY decoding and multiline interactions remain unresolved.
- parser update status remains `not_applied`.

Final validation report layer:

- a dedicated report step now validates field starts with:
  - raw decode tables at selected best offsets
  - neighbor offset competition tables (`best ±4`)
  - field confidence (`high_candidate` / `medium_candidate` / `weak_candidate` / `unresolved`)
  - parser candidate readiness (`ready_for_candidate_model` / `needs_more_validation` / `unresolved`)
- this layer is still analyzer evidence and does not modify parser decode behavior.

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

---

## Text Anchor Direct Field Investigation (Current Stage)

Scope of this stage:

- focus only on direct payload-field candidates for text anchor (`X 위치`, `Y 위치`, `Z 위치`)
- do not promote parser decode rules yet
- keep absolute file offsets as diagnostic-only

Current policy split:

- confirmed concept: text anchor is a real UI-controlled concept (`X 위치`, `Y 위치`, `Z 위치`)
- current parser extraction: mostly `baseline_midpoint` structural recovery
- unresolved: direct binary field offsets/structure for anchor in `CParagraphe` payload

Primary evidence fixtures used:

- `default_text.txt`
- `text_origin_0_0.txt`
- `text_origin_offset.txt`
- `text_group_same_color_two_objects.txt`
- `text_group_mixed_color_two_objects.txt`

Analyzer status:

- `tools/analyze_text_anchor_field_candidates.py` provides:
  - pairwise payload diffs (class-relative + record-relative)
  - expected-value scoring for candidate `double64` and contiguous `x/y/z` triple windows
  - multi-object separability checks
  - side-by-side reporting with current parser `baseline_midpoint` output

Interpretation status:

- direct anchor field candidates are still `provisional`
- baseline-midpoint recovery is still the active parser path
- anchor must not be conflated with bbox center

### Multi-object ownership recheck (updated)

Earlier limitation:

- prior manual checks inspected only the first `CParagraphe` payload in a fixture.
- this was insufficient for chain-level ownership validation in multi-object fixtures.

Current analyzer correction:

- the analyzer now reports every parser chain and every available `CParagraphe` node together.
- per chain, it reports:
  - associated `CParagraphe` node index (if matchable)
  - direct triple decode at payload-relative `158/166/174`
  - baseline midpoint anchor
  - expected fixture anchor
  - direct-vs-baseline / direct-vs-expected match status

Observed status for current multi-object fixtures:

- `text_group_same_color_two_objects.txt`: parser chains=2, `CParagraphe` nodes=1
- `text_group_mixed_color_two_objects.txt`: parser chains=2, `CParagraphe` nodes=1
- `text_two_objects_mixed_color_not_grouped.txt`: parser chains=2, `CParagraphe` nodes=1

Interpretation:

- chain count and `CParagraphe` node count are not currently 1:1 in these fixtures.
- direct triple evidence at `158/166/174` remains strong for single-object and for one chain in each multi-object fixture.
- full per-chain direct ownership still remains provisional.
