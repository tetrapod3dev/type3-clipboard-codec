# Type3 Text Object Reverse-Engineering Fixture Plan

This document defines the complete first-stage fixture plan for reverse-engineering Type3 clipboard text objects.

The goal is not parser implementation yet. The goal is to capture controlled, diff-friendly fixtures that let later parser milestones separate high-level text information from generated geometry/outline information without overgeneralizing from a small sample set.

## Terminology Policy

Original Korean Type3 UI terminology MUST be preserved exactly. English translations may be used as secondary, provisional labels only.

Rules:

- never discard Korean original wording
- never replace Korean UI terms with English-only names
- treat English translations as provisional until validated
- keep fixture metadata traceable to the exact Type3 UI controls used during capture
- if a Korean term has uncertain semantics, document the uncertainty instead of forcing an English field name

Examples:

| Korean UI term | Provisional English | Status                               |
|----------------|---------------------|--------------------------------------|
| 자유 위치          | free position       | unresolved layout/alignment behavior |
| 인쇄 비례          | print proportional  | provisional spacing mode label       |
| 기본선 위          | above baseline      | inferred from UI wording             |
| 기본선 아래         | below baseline      | inferred from UI wording             |

## Current Text-Object Assumption

Type3 text objects are expected to contain both:

- high-level text information: visible text, font, layout, typography, style flags
- generated geometry/outline information: `CCourbe`, `CContour`, contour records, property blocks

Therefore, text fixtures must support investigation of:

- text extraction
- font extraction
- encoding analysis
- layout analysis
- geometry generation analysis
- transform analysis
- style analysis

The parser must not treat text objects as simple strings. Unknown byte regions must remain raw-preserved until multiple controlled fixtures support a stronger interpretation.

---

## 1. Fixture Naming Convention

Text fixture names use a deterministic lowercase snake-case:

```text
text_<category>_<variant>.txt
```

Rules:

- prefix every first-stage text fixture with `text_`
- keep names stable even if later interpretation changes
- use ASCII-only filenames
- use Korean UI terms in metadata, not filenames
- encode numeric values explicitly: `30deg`, `10mm`, `50_percent`
- keep baseline-like aliases intentional and documented
- avoid abbreviations unless already common, such as `rtl`

Recommended category tokens:

| Category    | Meaning                                                        |
|-------------|----------------------------------------------------------------|
| `ascii`     | ASCII text-content fixtures                                    |
| `korean`    | Korean text-content fixtures                                   |
| `multiline` | newline/paragraph content fixtures                             |
| `font`      | font-family/font-style fixtures                                |
| `origin`    | object/bbox/anchor position fixtures                           |
| `align`     | alignment mode fixtures                                        |
| `height`    | `높이` fixtures                                                  |
| `width`     | `폭` fixtures                                                   |
| `spacing`   | `간격` or paragraph spacing fixtures; metadata must disambiguate |
| `rotation`  | `회전` fixtures                                                  |
| `mirror`    | `미러` fixtures                                                  |
| `slant`     | `기울기` / `이탤릭` fixtures                                         |
| `baseline`  | `기본선 위` / `기본선 아래` fixtures                                    |
| `rtl`       | `오른쪽에서 왼쪽` fixtures                                            |

When two Korean UI controls could map to the same English word, the filename may stay practical but the metadata must preserve the exact Korean control. For example, `text_spacing_150_percent.txt` must say whether it changes `간격` or paragraph spacing mode/value.

---

## 2. Fixture Capture Rules

Primary rule:

> Each fixture should change exactly one variable from `default_text.txt`.

Capture rules:

- start every fixture from the baseline text object when possible
- keep visible text as `abcdefg` unless the fixture targets text content
- keep font as `Arial` unless the fixture targets font behavior
- keep text reference anchor `X 위치` / `Y 위치` near the baseline values unless the fixture targets geometry/position behavior
- keep single-line content unless the fixture targets multiline or paragraph behavior
- keep no rotation, no mirror, no underline, default spacing, and default alignment unless targeted
- default to one text object per clipboard payload
- allow multi-object payloads only for explicit group/color fixtures; mark them as exceptions in metadata
- avoid selecting or copying helper geometry, construction lines, or multiple objects
- avoid editing after capture without recapturing metadata
- record the exact Type3 UI controls and values used
- preserve raw clipboard hex exactly as captured after the repository's normal hex normalization

Diff-friendly precautions:

- use the same Type3 document/session setup for fixture groups when practical
- capture fixtures in a controlled order
- keep the object creation workflow consistent
- avoid manual dragging unless testing free positioning
- prefer numeric entry fields over mouse movement
- avoid snapping changes unless the fixture targets position behavior
- if Type3 writes volatile IDs/timestamps/session data, document candidate byte ranges but do not delete or normalize them from the raw fixture

Conservative reverse-engineering precautions:

- do not assume a changed byte range is semantic after only one pairwise diff
- do not assume unchanged byte ranges are irrelevant
- do not collapse unknown fields into a single guessed structure
- keep generated geometry and high-level text records separately observable
- preserve all unknown bytes for future round-trip work

---

## 3. Fixture Metadata Requirements

Every fixture must have metadata in this document or a future sidecar manifest before it is used as parser evidence.

Required metadata:

| Field                     | Required value                                             |
|---------------------------|------------------------------------------------------------|
| fixture filename          | exact `tests/samples/*.txt` filename                       |
| baseline delta            | one sentence describing the single changed variable        |
| visible text              | exact visible content, including newlines/spaces           |
| font Korean/original      | exact Type3 font label when Korean or localized            |
| font provisional id       | ASCII fixture identifier/transliteration                   |
| bbox lower-left           | observed/derived position in mm (not the primary text control baseline) |
| anchor/reference position | `X 위치` / `Y 위치` if known                                   |
| text mode                 | single-line/multiline/paragraph                            |
| alignment                 | exact Korean UI term: `왼쪽`, `중앙`, `오른쪽`, `맞춤`, `자유 위치`     |
| height                    | `높이` value and unit                                        |
| width scale               | `폭` value and unit                                         |
| character spacing         | `간격` value and unit                                        |
| max length                | `최대 길이` value and unit                                     |
| slant/italic              | `기울기` value and `이탤릭` state                                |
| rotation                  | `회전` value                                                 |
| mirror                    | `미러` state                                                 |
| underline                 | `밑줄` state and value if visible                            |
| offset                    | `옵셋` value                                                 |
| baseline mode             | `기본선 위` / `기본선 아래` / default                               |
| paragraph spacing mode    | `고정`, `비례`, `인쇄 비례`, or default                            |
| directionality            | `오른쪽에서 왼쪽` state                                           |
| case/script mode          | `대문자`, `작은 대문자`, `소문자`, `윗 첨자`, `아래 첨자`, or default        |
| is grouped                | boolean (`true` for `결합` or other grouped candidates)      |
| group term (Korean)       | exact Type3 grouping label such as `결합`, if present        |
| child object count        | number of child objects for grouped payloads               |
| per-child style summary   | per-child color/style selection and bbox summary           |
| color candidates          | candidate list including offset, raw value, name, encoding |
| selected color confidence | selection confidence (`confirmed`/`strong`/`weak`)         |
| selected color source     | selection source (`fixed_offset`/`payload_scan`)           |
| expected changed regions  | conservative candidates only                               |
| volatile regions          | observed session/object ID candidates                      |
| notes                     | capture caveats and unresolved observations                |

Metadata should describe expected binary regions using cautious language:

- "likely font-record region"
- "candidate character-record region"
- "candidate layout flag"
- "generated geometry likely changed because glyph outlines differ"
- "bbox likely changed as a derived consequence"

Do not mark a byte range as confirmed until it survives multiple fixture comparisons.

---

## 4. Baseline Fixture Definition

| Field           | Value                                           |
|-----------------|-------------------------------------------------|
| fixture         | `default_text.txt`                              |
| role            | baseline text object                            |
| visible text    | `abcdefg`                                       |
| font            | `Arial`                                         |
| anchor/reference position | `X 위치 = 111.111 mm`, `Y 위치 = 222.222 mm`, `Z 위치 = 0.000 mm` |
| line mode       | single-line                                     |
| rotation        | none / `회전 = 0°`                                |
| mirror          | off / `미러` disabled                             |
| underline       | off / `밑줄` disabled                             |
| spacing         | default                                         |
| alignment       | default Type3 alignment                         |
| width/height    | default captured values, to be recorded exactly |
| slant/italic    | default, expected `기울기 = 0°`, `이탤릭` disabled    |

Expected reverse-engineering value:

- identifies first reliable text-object structure
- confirms presence of `CParagraphe`
- exposes baseline font record containing `Arial`
- exposes baseline character records for `abcdefg`
- provides generated outline geometry for a simple ASCII text object
- anchors comparisons for all first-stage fixture diffs

Likely changed regions in future deltas:

- text/font records near high-level text data
- object bbox values if visible geometry changes
- generated `CCourbe` / `CContour` outline geometry when glyph shape or layout changes
- `CPropertyExtend` or related style blocks when style controls change

Important:

- `default_text.txt` remains the canonical baseline even if `text_ascii_lowercase.txt` is later captured as an explicit text-content fixture.
- If both files exist and are byte-identical except volatile regions, document that fact instead of removing either fixture.

---

## 5. Text Content Fixtures

Purpose:

- identify encoding strategy
- determine whether text records are per-character, UTF-8, UTF-16, mixed, or glyph-index-based
- identify string length/count fields
- identify newline storage behavior
- identify spacing and word-separation behavior
- compare text content changes against generated geometry changes

All text-content fixtures should keep font `Arial`, baseline position, baseline typography, no rotation, no mirror, and default style.

| Fixture                       | Visible text              | Delta from baseline                                    | Expected reverse-engineering value                                                    | Likely changed regions                                                              |
|-------------------------------|---------------------------|--------------------------------------------------------|---------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| `text_ascii_lowercase.txt`    | `abcdefg`                 | explicit lowercase content fixture; may match baseline | confirms baseline repeatability and volatile regions                                  | ideally only volatile/session regions if recaptured                                 |
| `text_ascii_uppercase.txt`    | `ABCDEFG`                 | visible text only                                      | distinguishes character values from same-length ASCII records; glyph geometry changes | character records, possible glyph IDs, generated outlines, bbox                     |
| `text_digits.txt`             | `1234567890`              | visible text only; length changes                      | tests digit encoding and length/count fields                                          | character records, length/count candidates, outlines, bbox                          |
| `text_alphanumeric.txt`       | `A1B2C3d4`                | visible text only                                      | tests mixed case/digit records and per-character ordering                             | character records, glyph IDs, outlines                                              |
| `text_spaces.txt`             | `ab cd ef`                | visible text only; includes spaces                     | identifies space storage, advance width, word separation                              | character records, spacing/advance records, outlines may omit space glyph           |
| `text_special_characters.txt` | `+-*/#@&()`               | visible text only                                      | tests punctuation encoding and glyph mapping                                          | character records, glyph IDs, outlines, bbox                                        |
| `text_korean_basic.txt`       | `가나다라마`                   | visible text only; Korean                              | tests Hangul encoding and non-ASCII font fallback behavior                            | encoding records, possible UTF-16/glyph indices, font fallback candidates, outlines |
| `text_korean_mixed.txt`       | `ABC가나다123`               | visible text only; mixed scripts                       | tests script transitions and mixed encoding strategy                                  | character records, run records, glyph IDs, outlines                                 |
| `text_multiline_basic.txt`    | `abcd` + newline + `efgh` | content changes to two lines                           | identifies newline representation and paragraph/line record structure                 | character records, newline/line break marker, layout records, bbox, outlines        |

Rationale:

- Same-length ASCII swaps (`abcdefg` -> `ABCDEFG`) help isolate per-character storage.
- Length-changing ASCII fixtures expose count and offset fields.
- Korean fixtures are required before choosing an internal parser text-encoding model.
- Multiline content is included here as a content fixture, while paragraph spacing modes are handled separately.

Capture notes:

- Spaces must be ordinary spaces, not non-breaking spaces.
- Newline must be produced by the normal Type3 text entry workflow.
- For Korean text, record the active input method only if it affects Type3 behavior; the fixture metadata should still focus on visible text and Type3 UI settings.

---

## 6. Font Fixtures

Purpose:

- identify font family storage
- distinguish font name strings from font IDs or style flags
- observe whether generated outlines change when only the font changes
- validate Korean font names used in real Type3 workflows

All font fixtures must keep visible text `abcdefg` and all other settings baseline/default.

| Fixture                           | Original font name                          | Provisional identifier | Delta from baseline                                | Expected reverse-engineering observations                   | Likely changed regions                                        |
|-----------------------------------|---------------------------------------------|------------------------|----------------------------------------------------|-------------------------------------------------------------|---------------------------------------------------------------|
| `text_font_arial.txt`             | `Arial`                                     | `arial`                | explicit Arial control fixture; may match baseline | validates recapture stability and font-record baseline      | ideally only volatile/session regions if recaptured           |
| `text_font_arial_bold.txt`        | `Arial Bold` or Type3's exact bold UI label | `arial_bold`           | font/style only                                    | separates family/style storage from generated bold outlines | font record, style/weight candidate, outlines, bbox           |
| `text_font_hy_gyeongo_dik.txt`    | `HY견고딕`                                     | `hy_gyeongo_dik`       | font only                                          | tests Korean font name storage and glyph outline generation | font record, possible localized name encoding, outlines, bbox |
| `text_font_hy_teuktae_gothic.txt` | `HY특태고딕`                                    | `hy_teuktae_gothic`    | font only                                          | tests wide/heavy Korean Gothic family storage               | font record, localized name bytes, outlines, bbox             |
| `text_font_hy_tae_gothic.txt`     | `HY태고딕`                                     | `hy_tae_gothic`        | font only                                          | compares related HY Gothic family identifiers               | font record, localized name bytes, outlines, bbox             |
| `text_font_hy_se_gothic.txt`      | `HY세고딕`                                     | `hy_se_gothic`         | font only                                          | compares related HY Gothic family identifiers               | font record, localized name bytes, outlines, bbox             |

Important:

- Preserve original Korean font names exactly: `HY견고딕`, `HY특태고딕`, `HY태고딕`, `HY세고딕`.
- The ASCII identifiers are filename/transliteration conveniences only.
- Do not infer that Type3 stores the Korean visible name directly until bytes confirm it.

Current status update (after `text_font_arial_bold.txt` recapture):

- confirmed: `text_font_arial_bold.txt` no longer shows multiline `abcd\nefgh` evidence; current visible/source text candidate is `abcdefg`.
- observed: parser still resolves `font_name` as unresolved for `text_font_arial_bold.txt` and HY fixtures in current conservative path.
- provisional: exact binary mapping for `Arial Bold` and Korean font-name storage.

Expected parser milestone value:

- high priority for font extraction
- medium priority for glyph-outline relationship analysis
- low priority for exact font metrics until multiple fonts and heights are captured

---

## 7. Geometry/Layout Fixtures

Purpose:

- separate bbox, anchor/reference position, and alignment behavior
- determine whether `X 위치` / `Y 위치` are persisted independently of bbox
- identify alignment flags/enums
- detect derived geometry changes caused by layout

Preserve original Korean alignment terms:

- `왼쪽`

---

## 8. Text color fixtures and ownership

Target fixtures:

- `text_color_army_green.txt`
- `text_color_navy_blue.txt`
- `text_group_same_color_two_objects.txt`
- `text_group_mixed_color_two_objects.txt`
- `text_two_objects_mixed_color_not_grouped.txt`
- `default_text.txt`

Confirmed:

- fixture intent colors are controlled during capture.
- anchor control remains `X 위치`, `Y 위치`, `Z 위치`; bbox is observed/derived.

Observed:

- single-object text color fixtures can still parse as `Black` in current conservative parser output.
- same-color two-object fixture provides `Army Green` evidence on both chains.
- mixed-color two-object fixtures do not yet provide stable per-object ownership decoding.

Provisional:

- per-object ownership mapping for mixed-color fixtures

## Offset policy for text reverse engineering

Confirmed:

- absolute file offset is not a stable parser key for text objects.
- class chain and payload structure are stable parsing anchors; style/color raw values at absolute offsets are fixture-level evidence only.

Observed:

- `text_color_army_green.txt` vs `text_color_navy_blue.txt` comparisons produce repeated palette-like candidates at several absolute offsets.
- those offsets are useful for diagnostics and clustering, not for direct parser decoding rules.

Provisional:

- text color/font/style should be decoded from class-payload-relative or record-relative fields inside `CParagraphe`/related records.
- direct binary field mapping for text color remains unresolved.
- exact text-specific color field offsets in `CPropertyExtend`
- distinction between semantic color bytes and volatile/session-local byte regions
- `중앙`
- `오른쪽`
- `맞춤`
- `자유 위치`

| Fixture                        | Target control/value                                            | Delta from baseline                         | Expected reverse-engineering value                           | Likely changed regions                                             |
|--------------------------------|-----------------------------------------------------------------|---------------------------------------------|--------------------------------------------------------------|--------------------------------------------------------------------|
| `text_origin_0_0.txt`          | anchor `X 위치` / `Y 위치` near baseline values                 | explicit origin control; may match baseline | validates coordinate repeatability and volatile regions      | bbox/anchor candidates only if recapture differs                   |
| `text_origin_offset.txt`       | move object to a documented offset, e.g. `(11.111,22.222,0)` mm | position only                               | separates position fields from text/style records            | bbox doubles, anchor `X 위치`/`Y 위치`, generated geometry coordinates |
| `text_align_left.txt`          | `왼쪽`                                                            | alignment only                              | identifies left alignment enum/flag                          | alignment candidate, possible anchor/bbox derived change           |
| `text_align_center.txt`        | `중앙`                                                            | alignment only                              | identifies center alignment enum/flag                        | alignment candidate, possible anchor/bbox derived change           |
| `text_align_right.txt`         | `오른쪽`                                                           | alignment only                              | identifies right alignment enum/flag                         | alignment candidate, possible anchor/bbox derived change           |
| `text_align_justify.txt`       | `맞춤`                                                            | justify/alignment behavior only             | tests whether `맞춤` is enum or independent flag               | alignment/justify candidate, spacing/layout records, outlines      |
| `text_align_free_position.txt` | `자유 위치`                                                         | free-position mode only                     | tests whether free positioning is enum, flag, or anchor mode | alignment/free-position candidate, anchor records                  |

Capture precautions:

- alignment fixtures should be captured with identical visible text and no manual repositioning after mode change unless Type3 requires it.
- If changing alignment moves the visual bbox, record both `bbox lower-left` and `X 위치` / `Y 위치`.
- Do not combine `맞춤` and `자유 위치` with other alignment changes unless Type3's UI forces a state transition; document forced state transitions explicitly.

---

## 8. Typography Fixtures

Purpose:

- identify numeric typography fields
- separate high-level parameters from regenerated outline geometry
- validate unit handling for mm and percent controls

Preserve original Korean typography terms:

- `높이`
- `폭`
- `간격`
- `최대 길이`
- `밑줄`
- `옵셋`

| Fixture                         | Target Korean control | Target value                         | Delta from baseline    | Expected reverse-engineering value                       | Likely changed regions                                                      |
|---------------------------------|-----------------------|--------------------------------------|------------------------|----------------------------------------------------------|-----------------------------------------------------------------------------|
| `text_height_10mm.txt`          | `높이`                  | `10 mm`                              | height only            | identifies text-height field and scale                   | height candidate, bbox, outlines                                            |
| `text_height_30mm.txt`          | `높이`                  | `30 mm`                              | height only            | validates numeric field and proportional outline scaling | height candidate, bbox, outlines                                            |
| `text_width_50_percent.txt`     | `폭`                   | `50%`                                | width scale only       | identifies horizontal scale field                        | width-scale candidate, bbox, outlines                                       |
| `text_width_150_percent.txt`    | `폭`                   | `150%`                               | width scale only       | validates percent scaling and bbox relationship          | width-scale candidate, bbox, outlines                                       |
| `text_spacing_80_percent.txt`   | `간격`                  | `80%`                                | character spacing only | identifies tracking/character spacing field              | spacing candidate, advances, bbox, outlines                                 |
| `text_spacing_150_percent.txt`  | `간격`                  | `150%`                               | character spacing only | validates tracking direction and percent encoding        | spacing candidate, advances, bbox, outlines                                 |
| `text_max_length_50mm.txt`      | `최대 길이`               | `50 mm`                              | max length only        | tests forced fit/stretch behavior                        | max-length candidate, layout records, possibly width/spacing derived values |
| `text_underline_on_default.txt` | `밑줄`                  | enabled with default underline value | underline only         | separates underline flag/value from outline geometry     | underline flag/value, added underline geometry or style records             |
| `text_offset_10_percent.txt`    | `옵셋`                  | `10%`                                | offset only            | identifies baseline-relative offset field                | offset candidate, bbox/anchor/layout records                                |

Notes:

- `밑줄` may have both an enable flag and a percentage value. The default observed value should be recorded exactly during capture.
- `최대 길이` may cause derived width or spacing changes. Treat those as layout side effects, not separate user-controlled variables.
- `간격` here means character spacing/tracking, not paragraph line spacing. Paragraph spacing fixtures are listed separately.

---

## 9. Paragraph/Multiline Fixtures

Purpose:

- identify multiline text structure
- distinguish paragraph spacing modes from character spacing
- identify baseline-relative mode storage
- determine whether line layout is high-level or geometry-only

Preserve original Korean terms:

- `기본선 위`
- `기본선 아래`
- `고정`
- `비례`
- `인쇄 비례`

| Fixture                               | Target Korean control/value | Delta from baseline         | Expected reverse-engineering value                                 | Likely changed regions                                |
|---------------------------------------|-----------------------------|-----------------------------|--------------------------------------------------------------------|-------------------------------------------------------|
| `text_baseline_above.txt`             | `기본선 위`                     | baseline mode only          | identifies baseline mode enum/flag                                 | baseline flag, anchor/layout records, bbox            |
| `text_baseline_below.txt`             | `기본선 아래`                    | baseline mode only          | validates alternate baseline mode                                  | baseline flag, anchor/layout records, bbox            |
| `text_spacing_fixed.txt`              | `고정`                        | paragraph spacing mode only | identifies fixed spacing enum and mm value field                   | spacing mode enum, spacing value/unit, layout records |
| `text_spacing_proportional.txt`       | `비례`                        | paragraph spacing mode only | identifies proportional spacing enum and percent value field       | spacing mode enum, spacing value/unit, layout records |
| `text_spacing_print_proportional.txt` | `인쇄 비례`                     | paragraph spacing mode only | identifies print-proportional spacing enum and percent value field | spacing mode enum, spacing value/unit, layout records |

Recommended capture setup:

- If the UI only exposes paragraph spacing behavior for multiline text, use the same visible multiline text for all paragraph spacing fixtures, preferably:

```text
abcd
efgh
```

- If multiline is required, document that these fixtures differ from the baseline by both multiline content and the target paragraph mode. In that case, compare them primarily against `text_multiline_basic.txt`, not directly against `default_text.txt`.

Conservative note:

- Paragraph spacing fixtures are the main exception to the strict one-variable rule if Type3 requires multiline content to expose the control. The metadata must state the effective comparison baseline.

---

## 10. Directionality Fixtures

Purpose:

- identify text direction flags
- determine whether case/script modes transform stored text or only display/output
- test mutually exclusive text mode controls

Preserve original Korean terms:

- `오른쪽에서 왼쪽`
- `대문자`
- `작은 대문자`
- `소문자`
- `윗 첨자`
- `아래 첨자`

| Fixture                    | Target Korean control | Delta from baseline | Expected reverse-engineering value                   | Likely changed regions                                     |
|----------------------------|-----------------------|---------------------|------------------------------------------------------|------------------------------------------------------------|
| `text_rtl_on.txt`          | `오른쪽에서 왼쪽` enabled    | directionality only | identifies RTL flag and visual ordering behavior     | direction flag, layout records, possible outline order     |
| `text_uppercase_mode.txt`  | `대문자`                 | case mode only      | tests whether original or transformed text is stored | case-mode flag, character records if transformed, outlines |
| `text_small_caps_mode.txt` | `작은 대문자`              | case mode only      | tests small-caps behavior and glyph substitution     | case-mode flag, glyph/style records, outlines              |
| `text_lowercase_mode.txt`  | `소문자`                 | case mode only      | tests lowercase transformation storage               | case-mode flag, character records if transformed, outlines |
| `text_superscript.txt`     | `윗 첨자`                | script mode only    | identifies superscript enum/flag and baseline shift  | script-mode flag, scale/offset/layout records, bbox        |
| `text_subscript.txt`       | `아래 첨자`               | script mode only    | identifies subscript enum/flag and baseline shift    | script-mode flag, scale/offset/layout records, bbox        |

Capture notes:

- Case-mode fixtures should keep source entry text `abcdefg` unless the UI requires a different trigger.
- Record both entered source text and visible text after Type3 applies the mode.
- If `대문자`, `작은 대문자`, or `소문자` mutates the actual text in the editor, note that separately from binary interpretation.

---

## 11. Transform Fixtures

Purpose:

- identify object transform fields
- distinguish high-level transform parameters from transformed generated contour coordinates
- validate whether Type3 stores original outlines plus transform, transformed outlines only, or both

Preserve original Korean terms:

- `회전`
- `미러`
- `기울기`
- `이탤릭`

| Fixture                       | Target Korean control/value         | Delta from baseline | Expected reverse-engineering value                          | Likely changed regions                                    |
|-------------------------------|-------------------------------------|---------------------|-------------------------------------------------------------|-----------------------------------------------------------|
| `text_rotation_30deg.txt`     | `회전 = 30°`                          | rotation only       | identifies rotation numeric field and geometry side effects | rotation candidate, bbox, transformed outlines            |
| `text_rotation_90deg.txt`     | `회전 = 90°`                          | rotation only       | validates angle encoding and axis behavior                  | rotation candidate, bbox, transformed outlines            |
| `text_mirror_on.txt`          | `미러` enabled                        | mirror only         | identifies mirror flag or transform matrix behavior         | mirror flag/matrix, layout direction, bbox/outlines       |
| `text_slant_15deg.txt`        | `기울기 = 15°`, `이탤릭` expected enabled | slant only          | validates default italic-button slant angle                 | slant numeric candidate, italic state indicator, outlines |
| `text_slant_custom_30deg.txt` | `기울기 = 30°`                         | slant only          | proves slant is numeric rather than boolean-only            | slant numeric candidate, outlines, bbox                   |

Important:

- `이탤릭` should not be modeled as only a boolean until `기울기` fixtures prove the relationship.
- Rotation may change bbox even if text content and font are stable. Treat bbox changes as derived transform evidence.
- Mirror may alter a cursor direction or visual alignment; capture `X 위치` / `Y 위치` and alignment state after enabling it.

---

## 12. Style Fixtures

First-stage style coverage starts narrow but now includes text color fixtures to align with current grouped/color analysis work.

Required first-stage style fixture:

| Fixture                         | Target Korean control/value               | Delta from baseline | Expected reverse-engineering value                                                        | Likely changed regions                                                            |
|---------------------------------|-------------------------------------------|---------------------|-------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `text_underline_on_default.txt` | `밑줄` enabled with default underline value | underline only      | identifies text-specific underline flag/value and whether underline is generated geometry | underline flag/value, possible extra contour/line geometry, `CPropertyExtend`     |
| `text_color_navy_blue.txt`      | text color set to navy-blue sample value  | text color only     | validates text color candidate extraction and confidence/source fields                    | text style/property block, candidate color offsets, possible generated style data |
| `text_color_army_green.txt`     | text color set to army-green sample value | text color only     | validates non-default text color mapping and repeated fixed-offset candidates             | text style/property block, candidate color offsets                                |

Group/color exception fixtures (multi-object payloads allowed):

| Fixture                                        | Target Korean control/value            | Delta from baseline               | Expected reverse-engineering value                                      | Likely changed regions                                                |
|------------------------------------------------|----------------------------------------|-----------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------|
| `text_group_same_color_two_objects.txt`        | `결합` + same text color                 | group structure + color           | validates grouped payload detection plus shared child color attribution | group wrapper records, child style/property blocks, marker order      |
| `text_group_mixed_color_two_objects.txt`       | `결합` + child text colors differ        | group structure + per-child color | validates per-child color disambiguation in grouped payload             | group wrapper records, child style/property blocks, candidate offsets |
| `text_two_objects_mixed_color_not_grouped.txt` | non-grouped multi-select + mixed color | multi-object non-grouped + color  | separates grouped-vs-independent color attribution behavior             | per-object property blocks, object boundary markers                   |

Future style fixture candidates:

| Candidate                        | Reason                                                           |
|----------------------------------|------------------------------------------------------------------|
| additional text color variants   | broaden palette coverage after initial navy/green/group fixtures |
| fill/outline style variants      | determine whether text outlines share curve property storage     |
| line width variants              | test whether generated text geometry has stroke-like properties  |
| layer/material/toolpath variants | defer until base text extraction is stable                       |

Conservative guidance:

- Do not assume rectangle color offsets apply to text objects.
- Do not assume underline is stored as a simple style only; it may generate extra geometry.
- Keep text style parser fields raw until text-specific fixtures support them.

---

## 13. Future Unknown/Experimental Fixtures

These are not required for the first capture batch, but filename space should remain compatible.

| Fixture candidate                                                       | Target Korean term/control           | Reason to defer                                   |
|-------------------------------------------------------------------------|--------------------------------------|---------------------------------------------------|
| `text_auto_spacing_state_1.txt` through `text_auto_spacing_state_5.txt` | `자동간격`                               | cyclic states are not yet semantically understood |
| `text_line_compression.txt`                                             | `선 압축`                               | observed behavior unresolved                      |
| `text_paragraph_compression.txt`                                        | `단락 압축`                              | observed behavior unresolved                      |
| `text_unicode_symbols.txt`                                              | symbol content                       | wait until basic encoding fixtures are understood |
| `text_long_ascii.txt`                                                   | long content                         | wait until short length fields are located        |
| `text_empty_or_single_char.txt`                                         | empty/single-character edge cases    | useful after object boundary parsing is stable    |
| `text_font_missing_fallback.txt`                                        | missing font fallback                | environment-dependent                             |
| `text_vertical_or_curve_text.txt`                                       | advanced text path modes, if present | likely changes too many variables                 |

Experimental fixture rule:

- If the control is not semantically understood, capture it only after there is a stable comparison baseline.
- Mark the fixture as experimental and avoid using it as a parser contract until reviewed.

---

## 14. Recommended Parsing Priority

Milestone 1: object detection and raw preservation

- detect text-like object structure
- detect `CParagraphe`
- preserve all raw bytes and nested generated geometry
- expose class chain without aggressive field interpretation

Milestone 2: baseline extraction

- extract visible ASCII text from `default_text.txt` / `text_ascii_lowercase.txt` if safely recoverable
- extract font candidate `Arial`
- extract bbox in meters and convert to mm
- expose raw character/font records

Milestone 3: encoding and font validation

- compare ASCII, digits, spaces, special characters, Korean, and mixed-script fixtures
- determine whether storage is per-character, UTF-8, UTF-16, mixed, or glyph-index-based
- extract font family conservatively across `Arial` and HY Korean font fixtures

Milestone 4: layout and typography

- extract `높이`, `폭`, `간격`, `최대 길이`
- extract `X 위치` / `Y 위치` only after position fixtures prove semantics
- identify alignment candidates for `왼쪽`, `중앙`, `오른쪽`, `맞춤`, `자유 위치`

Milestone 5: transforms

- extract `회전`, `미러`, `기울기`
- decide whether transforms are stored as high-level fields, transformed geometry, or both
- preserve original generated geometry ordering

Milestone 6: advanced modes and style

- extract `밑줄`, `옵셋`, baseline modes, directionality, case/script modes
- extract text color candidates with `candidate_*` fields and explicit confidence/source
- validate grouped-vs.-non-grouped per-child color attribution behavior
- leave unresolved modes as raw enums/flags

Parser implementation rules:

- unknown fields must remain raw-accessible
- candidate fields should use names like `candidate_slant_degrees` until validated
- do not erase byte ranges after successful high-level extraction
- round-trip preservation should be prioritized over premature semantic modeling

---

## 15. Fixture Generation Order

The recommended order is designed to maximize diff value while minimizing ambiguous side effects.

1. Baseline repeatability

    | Order | Fixture                    |
    |------:|----------------------------|
    |     1 | `default_text.txt`         |
    |     2 | `text_ascii_lowercase.txt` |
    |     3 | `text_font_arial.txt`      |
    |     4 | `text_origin_0_0.txt`      |

2. Encoding fixtures

    | Order | Fixture                       |
    |------:|-------------------------------|
    |     5 | `text_ascii_uppercase.txt`    |
    |     6 | `text_digits.txt`             |
    |     7 | `text_alphanumeric.txt`       |
    |     8 | `text_spaces.txt`             |
    |     9 | `text_special_characters.txt` |
    |    10 | `text_korean_basic.txt`       |
    |    11 | `text_korean_mixed.txt`       |
    |    12 | `text_multiline_basic.txt`    |

3. Font fixtures

    | Order | Fixture                           |
    |------:|-----------------------------------|
    |    13 | `text_font_arial_bold.txt`        |
    |    14 | `text_font_hy_gyeongo_dik.txt`    |
    |    15 | `text_font_hy_teuktae_gothic.txt` |
    |    16 | `text_font_hy_tae_gothic.txt`     |
    |    17 | `text_font_hy_se_gothic.txt`      |

4. Geometry/layout fixtures

    | Order | Fixture                        |
    |------:|--------------------------------|
    |    18 | `text_origin_offset.txt`       |
    |    19 | `text_align_left.txt`          |
    |    20 | `text_align_center.txt`        |
    |    21 | `text_align_right.txt`         |
    |    22 | `text_align_justify.txt`       |
    |    23 | `text_align_free_position.txt` |

5. Typography fixtures

    | Order | Fixture                         |
    |------:|---------------------------------|
    |    24 | `text_height_10mm.txt`          |
    |    25 | `text_height_30mm.txt`          |
    |    26 | `text_width_50_percent.txt`     |
    |    27 | `text_width_150_percent.txt`    |
    |    28 | `text_spacing_80_percent.txt`   |
    |    29 | `text_spacing_150_percent.txt`  |
    |    30 | `text_max_length_50mm.txt`      |
    |    31 | `text_underline_on_default.txt` |
    |    32 | `text_offset_10_percent.txt`    |

6. Transform fixtures

    | Order | Fixture                       |
    |------:|-------------------------------|
    |    33 | `text_rotation_30deg.txt`     |
    |    34 | `text_rotation_90deg.txt`     |
    |    35 | `text_mirror_on.txt`          |
    |    36 | `text_slant_15deg.txt`        |
    |    37 | `text_slant_custom_30deg.txt` |

7. Paragraph/directionality fixtures

    | Order | Fixture                               |
    |------:|---------------------------------------|
    |    38 | `text_baseline_above.txt`             |
    |    39 | `text_baseline_below.txt`             |
    |    40 | `text_spacing_fixed.txt`              |
    |    41 | `text_spacing_proportional.txt`       |
    |    42 | `text_spacing_print_proportional.txt` |
    |    43 | `text_rtl_on.txt`                     |
    |    44 | `text_uppercase_mode.txt`             |
    |    45 | `text_small_caps_mode.txt`            |
    |    46 | `text_lowercase_mode.txt`             |
    |    47 | `text_superscript.txt`                |
    |    48 | `text_subscript.txt`                  |

8. Text color/group fixtures

    | Order | Fixture                                        |
    |------:|------------------------------------------------|
    |    49 | `text_color_navy_blue.txt`                     |
    |    50 | `text_color_army_green.txt`                    |
    |    51 | `text_group_same_color_two_objects.txt`        |
    |    52 | `text_group_mixed_color_two_objects.txt`       |
    |    53 | `text_two_objects_mixed_color_not_grouped.txt` |

Generation-order rationale:

- repeatability fixtures first reveal volatile byte ranges
- encoding fixtures precede font fixtures so text storage is not confused with font behavior
- font fixtures precede typography because glyph outline changes are expected
- layout fixtures precede transform fixtures because transforms can obscure anchor behavior
- paragraph and directionality fixtures come later because they may alter both content and layout records
- grouped/multi-object color fixtures come last because they intentionally break the single-object default rule

---

## 16. Risk Warnings / Common Mistakes

Do not overgeneralize:

- one fixture pair is not enough to confirm a field
- ASCII text behavior may not apply to Korean text
- `Arial` behavior may not apply to HY Korean fonts
- shape `CPropertyExtend` offsets may not apply to text
- unchanged bytes in a small sample set may still be semantic for other modes

Do not lose Korean terminology:

- parser field names may be English, but documentation must retain Korean UI terms
- unresolved Korean terms should remain visible in metadata and issue notes
- translations such as "justify", "free position", and "print proportional" are provisional

Do not damage diff quality:

- do not change the font while testing text content
- do not move the object while testing typography
- do not manually resize text while testing font
- do not mix multiline, paragraph spacing, and alignment unless Type3 requires it
- do not compare paragraph spacing fixtures directly to the single-line baseline if multiline content was required

Do not confuse high-level text with generated geometry:

- glyph changes can alter `CCourbe` / `CContour` data even when the high-level control change is small
- bbox changes may be derived from generated outlines
- underline may be a style flag, generated geometry, or both
- mirror/rotation/slant may be stored as fields, transformed coordinates, or both

Do not normalize away unknown bytes:

- volatile/session-looking regions should be documented, not removed from raw fixtures
- unknown byte ranges should remain available to future parsers
- fixture files must remain faithful clipboard captures
- lossy fixture cleanup makes later round-trip encoding harder

Do not implement parser contracts too early:

- expose raw/candidate fields before stable semantic names
- prefer `unknown_*`, `reserved_*`, or `candidate_*` names for weak evidence
- require multiple fixture categories before promoting a candidate to confirm
- keep binary preservation and evidence traceability ahead of convenience APIs
