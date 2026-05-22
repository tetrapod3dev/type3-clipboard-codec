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

### Multi-object chain/node ownership audit

Tool:

- `tools/analyze_text_multi_object_ownership.py`
- output modes: text / `--json` / `--markdown`

Current audit result:

| fixture | parser chains | `CParagraphe` nodes | `CParagraphe` direct triple match | other expected anchor triple |
|---|---:|---:|---|---|
| `text_group_same_color_two_objects.txt` | 2 | 1 | chain0 `(111.111, 222.222, 0.0)` | chain1 anchor found in `CPropertyExtend` at class-payload offset `472` |
| `text_group_mixed_color_two_objects.txt` | 2 | 1 | chain0 `(111.111, 222.222, 0.0)` | chain1 anchor found in `CPropertyExtend` at class-payload offset `472` |
| `text_two_objects_mixed_color_not_grouped.txt` | 2 | 1 | chain1 `(211.111, 322.222, 0.0)` | chain0 anchor found in `CPropertyExtend` at class-payload offset `620` |

Updated interpretation:

- single-object direct anchor candidate at `CParagraphe` payload-relative offsets `158/166/174` is a strong observed candidate.
- multi-object fixtures prove that `chain count == CParagraphe count` is false for current samples.
- `CParagraphe` direct triple currently links to one parser chain by exact anchor equality and bbox/anchor proximity.
- the unmatched chain's expected anchor is still present as a contiguous `double64le` triple, but it appears outside `CParagraphe` in `CPropertyExtend`.
- therefore the direct triple must not be generalized as a per-text-chain `CParagraphe` field yet.
- `baseline_midpoint` remains the active parser fallback until chain ownership is structurally resolved.

Clipboard fixture collection note:

```powershell
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py dump-bundle --dir .\dumps\parser_case01
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py inspect --in .\dumps\parser_case01\typeeditzone.bin
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py load-bundle --dir .\dumps\parser_case01
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py verify-bundle --dir .\dumps\parser_case01
```

Parser promotion remains blocked until:

1. chain ownership can be derived without fixture filename assumptions.
2. the relationship between `CParagraphe` and `CPropertyExtend` anchor triples is explained structurally.
3. text-run ownership and anchor ownership are separated for grouped and non-grouped multi-object payloads.

### CPropertyExtend anchor context audit

Tool:

- `tools/analyze_text_cproperty_anchor_context.py`
- output modes: text / `--json` / `--markdown`

Current CPropertyExtend observations:

| fixture | anchor found in `CPropertyExtend` | `CPropertyExtend` payload-relative offset | matched parser chain |
|---|---|---:|---:|
| `text_group_same_color_two_objects.txt` | `(211.111, 322.222, 0.0)` | `472` | chain1 |
| `text_group_mixed_color_two_objects.txt` | `(211.111, 322.222, 0.0)` | `472` | chain1 |
| `text_two_objects_mixed_color_not_grouped.txt` | `(111.111, 222.222, 0.0)` | `620` | chain0 |

Local context status:

- grouped fixtures share the same `CPropertyExtend` anchor payload offset `472`.
- grouped fixtures are not byte-identical around the full local window because volatile/context bytes differ.
- grouped fixtures do share the same local marker signature around the hit; `CObDao` appears at `hit - 34`.
- non-grouped `620` has the same marker signature pattern but is shifted by `148` bytes relative to grouped `472`.
- this `148` byte delta is an offset-shift candidate only; no stable section/record boundary rule is confirmed yet.

`CObDao`-normalized update:

- target anchor triples in the current multi-object fixtures are all at `CObDao + 34` within the anchor-bearing `CPropertyExtend` local section.
- grouped fixtures: anchor-bearing `CObDao` offset `438`, anchor hit offset `472`, `hit_relative_to_cobdao=34`.
- non-grouped fixture: anchor-bearing `CObDao` offset `586`, anchor hit offset `620`, `hit_relative_to_cobdao=34`.
- grouped fixtures currently have 5 `CObDao` sections in `CPropertyExtend`; the non-grouped fixture has 6.
- the non-grouped anchor-bearing `CObDao` section is shifted by `148` bytes relative to the grouped anchor-bearing section.
- observed local class marker spelling is `OBJETINFOS_CLASSNAME`, followed by `CObDao` after 24 bytes in the current target sections.
- this strengthens the local-section hypothesis, but still does not define a complete chain ownership or record boundary rule.

Current parser decision:

- `CPropertyExtend` anchor location is observed, but structural rules remain unresolved.
- do not add a fixed offset parser rule for `472` or `620`.
- do not add a parser rule for `CObDao + 34` yet.
- do not promote `CPropertyExtend` anchor decode to confirmed.
- keep `baseline_midpoint` as the active fallback.

### CObDao section role audit

Current section counts in target multi-object fixtures:

| fixture | `CObDao` sections in `CPropertyExtend` | anchor-bearing section index | anchor-bearing `CObDao` offset |
|---|---:|---:|---:|
| `text_group_same_color_two_objects.txt` | 5 | 1 | 438 |
| `text_group_mixed_color_two_objects.txt` | 5 | 1 | 438 |
| `text_two_objects_mixed_color_not_grouped.txt` | 6 | 2 | 586 |

Section role observations:

- `CObDao + 34` can be read as a finite double triple in all current `CObDao` sections.
- anchor-bearing sections decode to the expected non-zero text anchor and match the corresponding parsed chain baseline anchor in analyzer evidence.
- some non-anchor sections also decode to coordinate-like triples, commonly `(0.0, 0.0, 0.0)`.
- therefore coordinate-like decode alone is not a safe anchor-bearing section selector.
- section index is also not stable: grouped anchor-bearing section index is `1`, non-grouped is `2`.
- current distinguishing evidence still depends on expected anchor / parsed baseline equality, which is analyzer-only and must not become parser selection logic.

Current role conclusion:

- `CObDao + 34` is a strong observed local pattern candidate.
- anchor-bearing `CObDao` section selection remains unresolved.
- false-positive risk is high if selecting by coordinate-like triple alone.

### CObDao section insertion audit

Current alignment observations:

- grouped same-color and grouped mixed-color fixtures both have 5 `CObDao` sections.
- grouped fixtures align section-by-section; anchor-bearing section index is `1` in both.
- non-grouped fixture has 6 `CObDao` sections.
- non-grouped section index `1` is a 148-byte inserted-section candidate before the anchor-bearing section.
- grouped section `1` anchor-bearing candidate aligns best with non-grouped section `2` anchor-bearing candidate after accounting for the inserted section.
- anchor-bearing `CObDao` offset shifts `438 -> 586`.
- anchor hit offset shifts `472 -> 620`.
- both shifts are `148` bytes.

Inserted section candidate:

- fixture: `text_two_objects_mixed_color_not_grouped.txt`
- section index: `1`
- `CObDao` offset: `438`
- section length candidate: `148`
- role: `non_anchor_candidate`
- `CObDao + 34` triple is finite but not coordinate-like.
- no matched chain in analyzer evidence.

Selector candidate status:

- section index: rejected; grouped uses `1`, non-grouped uses `2`.
- `CObDao + 34` coordinate-like: rejected as unsafe; non-anchor sections can decode coordinate-like triples.
- `OBJETINFOS/CObDao` marker signature: rejected as unsafe; marker signature is not unique to anchor-bearing sections.
- section alignment: useful analyzer evidence, but not parser-safe until inserted-section semantics are known.
- chain/source offset proximity: diagnostic only.

Parser readiness:

- no baseline-independent anchor-bearing section selector is available yet.
- parser promotion remains blocked.

### Three-object not-grouped scaling audit

New fixture:

- `text_three_objects_not_grouped.txt`
- intent: three independent text objects, same Army Green color, not grouped
- attempted selection order: `abcdefg`, `1234567890`, `XYZ`
- intended anchors:
  - `(111.111, 222.222, 0.0)`
  - `(211.111, 322.222, 0.0)`
  - `(311.111, 422.222, 0.0)`

Analyzer:

- `tools/analyze_text_cproperty_anchor_context.py`

Observed parser/analyzer result:

| fixture | parser chains | `CParagraphe` count | `CPropertyExtend` `CObDao` sections | `CPropertyExtend` anchor hits |
|---|---:|---:|---:|---:|
| `text_group_same_color_two_objects.txt` | 2 | 1 | 5 | 1 |
| `text_two_objects_same_color_not_grouped.txt` | 2 | 1 | 6 | 1 |
| `text_two_objects_not_grouped_selection_reversed.txt` | 2 | 1 | 6 | 1 |
| `text_three_objects_not_grouped.txt` | 3 | 1 | 11 | 2 |

`text_three_objects_not_grouped.txt` ownership observations:

- `CParagraphe` direct anchor at payload-relative `158/166/174` decodes to `(311.111, 422.222, 0.0)` and matches chain2.
- `CPropertyExtend` anchor hit at `CObDao + 34` in section index `2` decodes to `(211.111, 322.222, 0.0)` and matches chain1.
- `CPropertyExtend` anchor hit at `CObDao + 34` in section index `7` decodes to `(111.111, 222.222, 0.0)` and matches chain0.
- all CProperty anchor hits still normalize to `CObDao + 34`.

Scaling interpretation:

- The current fixtures support one `CParagraphe` direct anchor plus `N-1` `CPropertyExtend` anchor hits for `N` parsed text chains.
- The simple section count rule `section_count = 4 + object_count` fits the current two-object not-grouped fixtures (`6 = 4 + 2`) but fails for the three-object not-grouped fixture (`11 != 4 + 3`).
- Several non-anchor 148-byte `CObDao` sections are observed in the three-object not-grouped fixture, so “a single inserted section” is no longer sufficient as the whole scaling model.
- This strengthens the evidence that the extra sections are related to independent not-grouped multi-object structure, not mixed color, but the section selector remains unresolved.

Parser status:

- `CObDao + 34` remains a strong observed local anchor candidate.
- anchor-bearing section selection is still analyzer-only.
- do not add a parser rule based on section index, absolute offset, or parsed baseline equality.
- keep `baseline_midpoint` as the active parser fallback.

### Order-aware multi-object fixture policy

New user observation:

- Type3/CAM appears to preserve object order even after grouping.
- CAM generation also appeared to preserve the order in which objects were selected.

Implication:

- `grouped` vs `not_grouped` is not enough as the only controlled variable.
- future text multi-object fixtures must record attempted selection order separately from payload stored order.
- parser chain order, `CParagraphe` direct anchor ownership, and `CPropertyExtend` anchor ownership must be documented together.

Required metadata for text multi-object fixtures:

- attempted selection order
- grouping state
- actual stored order: `unresolved` unless explicitly verified
- observed parser chain order
- observed `CParagraphe` direct anchor owner
- observed `CPropertyExtend` anchor owner(s)
- order control status: `controlled`, `attempted`, or `unknown`

Current order-aware fixture inventory:

| fixture | grouping | attempted selection order | order status | parser chain order | `CParagraphe` direct owner | `CPropertyExtend` anchor owners |
|---|---|---|---|---|---|---|
| `text_group_same_color_two_objects.txt` | grouped | unknown | unknown | chain0=`abcdefg`, chain1=`1234567890` | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)` |
| `text_group_mixed_color_two_objects.txt` | grouped | unknown | unknown | chain0=`abcdefg`, chain1=`1234567890` | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)` |
| `text_two_objects_mixed_color_not_grouped.txt` | not_grouped | unknown | unknown | chain0=`abcdefg`, chain1=`1234567890` | chain1 `(211.111,322.222,0)` | chain0 `(111.111,222.222,0)` |
| `text_two_objects_same_color_not_grouped.txt` | not_grouped | unknown | unknown | chain0=`abcdefg`, chain1=`1234567890` | chain1 `(211.111,322.222,0)` | chain0 `(111.111,222.222,0)` |
| `text_two_objects_not_grouped_selection_reversed.txt` | not_grouped | B -> A attempted | attempted | chain0=`abcdefg`, chain1=`1234567890` | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)` |
| `text_three_objects_not_grouped.txt` | not_grouped | A -> B -> C attempted | attempted | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | chain2 `(311.111,422.222,0)` | chain1 `(211.111,322.222,0)`, chain0 `(111.111,222.222,0)` |

All rows above keep actual stored order unresolved. Parser chain order is analyzer output, not a confirmed Type3 payload storage order.

### Planned grouped three-object order fixtures

These fixtures are intended to isolate grouped selection-order effects.

#### `text_three_objects_grouped_order_abc`

Purpose:

- observe ownership/order for three grouped text objects with attempted selection order A -> B -> C.

Objects:

- A: `abcdefg`, anchor `(111.111, 222.222, 0.0)`, color `Army Green`
- B: `1234567890`, anchor `(211.111, 322.222, 0.0)`, color `Army Green`
- C: `XYZ`, anchor `(311.111, 422.222, 0.0)`, color `Army Green`

Capture command:

```powershell
.\.venv\Scripts\python.exe tools\capture_type3_sample.py `
  --name text_three_objects_grouped_order_abc `
  --category text `
  --description "Three text objects, same color, grouped, attempted selection order A-B-C" `
  --object-count 3 `
  --grouping grouped `
  --text "abcdefg|1234567890|XYZ" `
  --anchors "111.111,222.222,0;211.111,322.222,0;311.111,422.222,0" `
  --color "Army Green" `
  --print-readme-snippet
```

#### `text_three_objects_grouped_order_cba`

Purpose:

- observe ownership/order for three grouped text objects with attempted selection order C -> B -> A.

Objects:

- C: `XYZ`, anchor `(311.111, 422.222, 0.0)`, color `Army Green`
- B: `1234567890`, anchor `(211.111, 322.222, 0.0)`, color `Army Green`
- A: `abcdefg`, anchor `(111.111, 222.222, 0.0)`, color `Army Green`

Capture command:

```powershell
.\.venv\Scripts\python.exe tools\capture_type3_sample.py `
  --name text_three_objects_grouped_order_cba `
  --category text `
  --description "Three text objects, same color, grouped, attempted selection order C-B-A" `
  --object-count 3 `
  --grouping grouped `
  --text "XYZ|1234567890|abcdefg" `
  --anchors "311.111,422.222,0;211.111,322.222,0;111.111,222.222,0" `
  --color "Army Green" `
  --print-readme-snippet
```

Analyzer preparation note:

- after capture, add both fixtures to `tools/analyze_text_cproperty_anchor_context.py`.
- also add both to `tools/analyze_text_multi_object_ownership.py`.
- compare them against `text_three_objects_not_grouped.txt` and existing two-object grouped/not-grouped fixtures.

Captured analyzer update:

| fixture | attempted order | parser chain order | `CObDao` sections | `CParagraphe` owner | `CPropertyExtend` owners |
|---|---|---|---:|---|---|
| `text_three_objects_grouped_order_abc.txt` | A -> B -> C | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | 9 | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)`, chain2 `(311.111,422.222,0)` |
| `text_three_objects_grouped_order_abc_content_variation.txt` | A -> B -> C | chain0=`Type3`, chain1=`9876543210`, chain2=`HELLO` | 9 | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)`, chain2 `(311.111,422.222,0)` |
| `text_three_objects_grouped_order_abc_height_30mm.txt` | A -> B -> C | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | 9 | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)`, chain2 `(311.111,422.222,0)` |
| `text_three_objects_grouped_order_abc_font_arial_bold.txt` | A -> B -> C | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | 9 | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)`, chain2 `(311.111,422.222,0)` |
| `text_three_objects_grouped_order_abc_mixed_color.txt` | A -> B -> C | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | 9 | chain0 `(111.111,222.222,0)` | chain1 `(211.111,322.222,0)`, chain2 `(311.111,422.222,0)` |
| `text_three_objects_grouped_order_cba.txt` | C -> B -> A | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | 9 | chain2 `(311.111,422.222,0)` | chain1 `(211.111,322.222,0)`, chain0 `(111.111,222.222,0)` |
| `text_three_objects_not_grouped.txt` | A -> B -> C | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | 11 | chain2 `(311.111,422.222,0)` | chain1 `(211.111,322.222,0)`, chain0 `(111.111,222.222,0)` |
| `text_three_objects_not_grouped_mixed_color.txt` | A -> B -> C | chain0=`abcdefg`, chain1=`1234567890`, chain2=`XYZ` | 11 | chain2 `(311.111,422.222,0)` | chain1 `(211.111,322.222,0)`, chain0 `(111.111,222.222,0)` |

Current grouped-order interpretation:

- grouped 3-object fixtures currently have 9 `CObDao` sections, compared with 11 in the 3-object not-grouped fixture.
- parser chain order did not change between grouped order A-B-C and grouped order C-B-A in current analyzer output.
- `CParagraphe` ownership did change with attempted grouped order: A-B-C maps to chain0, C-B-A maps to chain2.
- `CPropertyExtend` ownership changed accordingly for the remaining two anchors.
- grouped fixtures still fit the one `CParagraphe` direct anchor plus `N-1` `CPropertyExtend` anchors pattern.
- mixed-color 3-object fixtures match the same section counts and ownership pattern as the corresponding same-color fixtures.
- height 30mm and Arial Bold grouped 3-object fixtures also match the same 9-section ownership pattern.
- content variation also matches the same 9-section ownership pattern, while parser chain text order changes to `Type3`, `9876543210`, `HELLO`.
- actual stored order remains unresolved; this is analyzer evidence only.

### Multi-object anchor storage model

Current status terms:

- confirmed: parser behavior remains unchanged and uses `baseline_midpoint` as the active anchor fallback.
- observed: direct anchor storage patterns repeatedly appear in current fixtures.
- provisional: ownership/order/section-selection models are not parser rules.

Anchor storage scaling summary:

| fixture class | parsed chains | `CParagraphe` anchors | `CPropertyExtend` anchor hits | observed model |
|---|---:|---:|---:|---|
| 2-object grouped | 2 | 1 | 1 | `1 + (N-1)` holds |
| 2-object not-grouped | 2 | 1 | 1 | `1 + (N-1)` holds |
| 3-object grouped | 3 | 1 | 2 | `1 + (N-1)` holds |
| 3-object not-grouped | 3 | 1 | 2 | `1 + (N-1)` holds |

Grouped vs not-grouped section scaling:

| object count | grouped `CObDao` sections | not-grouped `CObDao` sections | delta | candidate |
|---:|---:|---:|---:|---|
| 2 | 5 | 6 | 1 | `object_count - 1` |
| 3 | 9 | 11 | 2 | `object_count - 1` |

Selection-order / primary-owner evidence:

- grouped A-B-C: parser chain order is A, B, C; `CParagraphe` owner is A.
- grouped C-B-A: parser chain order is still A, B, C; `CParagraphe` owner is C.
- not-grouped A-B-C: parser chain order is A, B, C; `CParagraphe` owner is C.
- attempted selection order appears to influence the primary `CParagraphe` owner.
- parser chain order and `CParagraphe` owner can move independently in current evidence.
- actual stored order is unresolved and must not be treated as equal to attempted UI selection order.

Parser promotion remains blocked by one core unresolved selector: there is no baseline-independent rule that identifies the anchor-bearing `CObDao` sections and maps them to text chains without relying on parser `baseline_midpoint` equality. Until that selector exists, `CParagraphe` direct anchor and `CPropertyExtend` anchor decoding remain analyzer-only.

### CObDao local field selector audit

The field comparison analyzer now compares every current multi-object `CObDao` section with an evidence-only label:

- `anchor_bearing_candidate`: `CObDao + 34` matches a known chain baseline anchor in analyzer evidence.
- `non_anchor_candidate`: all other `CObDao` sections.

Current section counts after 3-object mixed-color, style/font, and content validation:

- anchor-bearing sections: 21
- non-anchor sections: 83
- total multi-object `CObDao` sections: 104

Current useful field candidates:

| local field | anchor-bearing value | current false positives | status |
|---|---|---:|---|
| `u32le@CObDao+12` | `131072` (`00 00 02 00`) | 0 | observed separator, not parser-safe |
| `u32le@CObDao+56` | `262144` (`00 00 04 00`) | 0 | observed separator, not parser-safe |
| `u32le@CObDao+108` | `65536` (`00 00 01 00`) | 0 | observed separator, not parser-safe |
| `u32le@CObDao+112` | `262144` (`00 00 04 00`) | 0 | observed separator, not parser-safe |

3-object mixed-color validation:

- grouped A-B-C mixed color: 9 `CObDao` sections, 2 CPropertyExtend anchor hits, selector leads unchanged.
- not-grouped mixed color: 11 `CObDao` sections, 2 CPropertyExtend anchor hits, selector leads unchanged.
- color variation did not change the current local selector lead values.

3-object style/font validation:

- grouped A-B-C height 30mm: 9 `CObDao` sections, 2 CPropertyExtend anchor hits, selector leads unchanged.
- grouped A-B-C Arial Bold: 9 `CObDao` sections, 2 CPropertyExtend anchor hits, selector leads unchanged.
- height/font variation did not change the current local selector lead values.

3-object content/glyph validation:

- grouped A-B-C content variation (`HELLO`, `9876543210`, `Type3`): 9 `CObDao` sections, 2 CPropertyExtend anchor hits, selector leads unchanged.
- visible content/glyph variation did not change the current local selector lead values.

Local record signature candidate:

`CPropertyExtend_CObDao_anchor_record_candidate_v1` combines the current field leads with local record context:

- node class is `CPropertyExtend`
- `OBJETINFOS_CLASSNAME` appears at `CObDao - 24`
- `CObDao` marker exists
- `u32le@CObDao+12 == 131072`
- `u32le@CObDao+56 == 262144`
- `u32le@CObDao+108 == 65536`
- `u32le@CObDao+112 == 262144`
- `CObDao+34` decodes as a finite coordinate-like `double64le` triple with z near 0

Current signature evaluation:

- matched sections: 21
- anchor-bearing matched sections: 21
- non-anchor matched sections: 0
- false positives: 0
- false negatives: 0
- failed fixtures: none
- parser-safe status: `provisional_false`

Component interpretation:

- strongest separating components: the four u32 fields at `+12`, `+56`, `+108`, and `+112`
- supporting context: `CPropertyExtend`, `OBJETINFOS_CLASSNAME -> CObDao`, finite/coordinate-like `CObDao+34`
- coordinate-like `CObDao+34` alone remains insufficient because non-anchor sections also pass it.

Draft parser rule, not implemented:

```text
for each CPropertyExtend CObDao local section:
    require OBJETINFOS_CLASSNAME at CObDao - 24
    require u32(+12)=131072, u32(+56)=262144, u32(+108)=65536, u32(+112)=262144
    decode double3 at CObDao + 34
    require finite, coordinate-like, z near 0
    yield analyzer-only CPropertyExtend anchor candidate
```

This remains blocked from parser promotion because local field semantics are still unknown, the signature was discovered with analyzer labels, and chain ownership mapping still needs a parser-safe rule.

Important rejection:

- `coordinate-like at CObDao + 34` remains rejected as a selector because non-anchor sections still produce coordinate-like false positives.
- section index, absolute/payload offset, fixture filename, baseline equality, and attempted selection order alone remain rejected selectors.

Interpretation:

- The local fields around `CObDao + 12`, `+56`, `+108`, and `+112` are the strongest current selector leads.
- They are not yet parser-safe because their semantic role is unknown and they were found using analyzer labels derived from current fixtures.
- The next useful work is to design fixtures that vary object count/grouping/order while keeping these fields under observation, or to reverse the local record format around these offsets.
