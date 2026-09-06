# Type3 Text Object Reverse-Engineering Fixture Plan

This document defines the complete first-stage fixture plan for reverse-engineering Type3 clipboard text objects.

Color Phase 1B [boundary/role results](text_color_decode_rfc.md#phase-1b-byte-boundary-and-chunk-role-audit)
support a variable RGB span at record-relative 0x8B..0x8D from actual byte deltas.
The typed field may still include an invariant leading or trailing zero. Primary
chunk roles align as header-like 0, repeated context 1..8, and terminal 9;
not-grouped layouts instead show repeated ranges 1..11 or 1..4. Repeated local
signatures cannot uniquely locate insertions/deletions or identify semantic
objects. CPropertyExtend stays +30 side evidence only. No new captures, parser
changes, ownership work, or anchor closeout changes accompany this analyzer.

Color Phase 1 field decoding is documented in the [color decode RFC](text_color_decode_rfc.md).
The separate analyzer finds +0x8B/u32le/RGB0 as the strongest primary candidate
without expected-color selection. The provisional 204-byte chunk model includes
unmapped header/tail values and repeated color copies, not one record per object.
Grouped/not-grouped mixed and three-object contrasts use multisets and retain
multiplicity. CPropertyExtend +30 contributes bounded side evidence but fails
the single-object controls as a general color field. Ownership remains not ready;
anchor closeout and scanner/parser behavior are unchanged. Runtime descriptor
positions are provenance only and schema 6 is not interpreted as color metadata.

Independent format audit: see the [MFC CArchive compatibility investigation](typeeditzone_mfc_archive_investigation.md).
The observed FFFF/schema/WORD-length/ASCII-name pattern matches 35 descriptors
across text and geometry; the five descriptor classes have stable schema
candidates. CObDao's 48 ASCII occurrences do not match this layout. Current
scanner starts correspond to descriptor starts, without proving object blocks.
The assessment is `mfc_runtimeclass_framing_supported_but_writeobject_unclear`;
PID/reference/context interpretation and parser refactor remain unready. This
changes no anchor closeout conclusions or fixture plan. Color candidate work may
continue under existing restrictions; archive-based changes need a framing RFC.

Current track status: Phase 2A anchor ownership investigation complete; Phase 2
parser ownership implementation deferred / not ready pending independent evidence.
Ownership is not solved. Color ownership is the next investigation track.
Earlier fixture plans remain a backlog; this closeout creates no new fixtures.
See the [final closeout](text_anchor_ownership_mapping_rfc.md#12-final-ownership-investigation-closeout).

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

---

## Anchor Field Candidate Track (Provisional)

Current separation:

- confirmed: anchor concept in Type3 text UI (`X 위치`, `Y 위치`, `Z 위치`)
- active parser behavior: structural anchor recovery (`baseline_midpoint`)
- unresolved: direct payload field mapping for anchor values

Analyzer for this track:

- `tools/analyze_text_anchor_field_candidates.py`
- output modes: text / `--json` / `--markdown`
- evidence basis:
  - class payload relative offsets
  - record-relative offsets
  - pairwise diffs for origin-shift fixture pairs
  - multi-object anchor separability checks

Required caution:

- absolute offsets are diagnostic only
- text-run ownership and anchor ownership must remain separated concerns
- direct-field candidates remain provisional until cross-fixture repeatability is strong enough

Ownership validation note (multi-object fixtures):

- do not assume one `CParagraphe` node per parser chain.
- in current two-object fixtures, parser emits two chains while only one `CParagraphe` node is observed.
- chain-level direct-anchor validation must therefore:
  - enumerate all `CParagraphe` nodes,
  - enumerate all chains,
  - report unmatched chains explicitly instead of inferring missing direct fields.

Current ownership audit update:

- `tools/analyze_text_multi_object_ownership.py` is the current structure/evidence audit tool.
- current multi-object samples all have `parser chains=2` and `CParagraphe nodes=1`.
- grouped samples:
  - `CParagraphe` direct triple at payload-relative `158/166/174` matches chain0.
  - chain1 anchor triple is found in `CPropertyExtend`, not in a second `CParagraphe`.
- non-grouped sample:
  - `CParagraphe` direct triple at payload-relative `158/166/174` matches chain1.
  - chain0 anchor triple is found in `CPropertyExtend`.
- direct anchor decode is not ready for parser promotion as a per-chain field.
- active parser behavior remains structural `baseline_midpoint` recovery.
- text-run ownership and anchor ownership must remain separate concerns.

Future fixtures can be collected with the verified 2-format clipboard bundle workflow:

```powershell
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py dump-bundle --dir .\dumps\parser_case01
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py verify-bundle --dir .\dumps\parser_case01
```

CPropertyExtend anchor context audit:

- `tools/analyze_text_cproperty_anchor_context.py` inspects whole-payload anchor hits and focuses on `CPropertyExtend` local context.
- The analyzer has safety guards for runtime, marker scanning, CObDao section count, comparison count, decoded local
  values, and output rows. JSON output carries `limits`, `warnings`, and `truncated`; a truncated result is partial
  evidence only and does not change parser behavior.
- grouped two-object fixtures place the unmatched chain anchor at `CPropertyExtend` payload-relative offset `472`.
- the non-grouped two-object fixture places the unmatched chain anchor at `CPropertyExtend` payload-relative offset `620`.
- `620 - 472 = 148`, currently treated as a shift candidate, not a decoded section length.
- local marker evidence is similar: `CObDao` appears at `hit - 34` around the `CPropertyExtend` anchor hit.
- full local windows are not byte-identical, so this remains structure/evidence audit only.
- parser must not use a fixed `CPropertyExtend` offset rule until the local record/section boundary and chain ownership rule are known.
- Heavy record semantics comparisons must remain bounded and analyzer-only.

`CObDao` section normalization:

- anchor-bearing sections normalize to `CObDao + 34` in all current target multi-object fixtures.
- grouped fixtures have the anchor-bearing `CObDao` at payload-relative offset `438`.
- the non-grouped fixture has the anchor-bearing `CObDao` at payload-relative offset `586`.
- grouped `CPropertyExtend` nodes currently contain 5 `CObDao` sections; the non-grouped sample contains 6.
- the non-grouped anchor-bearing `CObDao` offset is `148` bytes after the grouped anchor-bearing `CObDao` offset.
- observed local marker spelling is `OBJETINFOS_CLASSNAME`; it appears 24 bytes before `CObDao` in the current anchor-bearing sections.
- `CObDao + 34` is therefore a strong local pattern candidate, not a confirmed parser rule.

Anchor-bearing section selection audit:

- current multi-object target fixtures contain 16 total `CObDao` sections in `CPropertyExtend`.
- 3 are known anchor-bearing by analyzer evidence; 13 are non-anchor sections.
- all known anchor-bearing sections have coordinate-like `CObDao + 34` triples with `z≈0`.
- non-anchor sections can also have coordinate-like `CObDao + 34` triples, including `(0.0, 0.0, 0.0)`.
- grouped fixtures use section index `1`; the non-grouped fixture uses section index `2`.
- section index/order, coordinate-like decode, and `OBJETINFOS_CLASSNAME -> CObDao` distance do not independently select the anchor-bearing section.
- selection by parsed baseline anchor equality remains analyzer-only and is not a parser rule.

Section insertion audit:

- grouped same-color and grouped mixed-color fixtures align with 5 `CObDao` sections each.
- non-grouped mixed-color fixture has 6 `CObDao` sections.
- non-grouped section index `1` is a 148-byte inserted-section candidate:
  - `CObDao` offset `438`
  - section length candidate `148`
  - non-anchor role
  - no matched chain in analyzer evidence
  - `CObDao + 34` triple is not coordinate-like
- after this inserted section, grouped section `1` corresponds to non-grouped section `2`; both are anchor-bearing candidates.
- anchor-bearing `CObDao` offset and anchor hit offset both shift by `148` bytes.
- this supports an insertion/shift hypothesis, but the inserted section's semantic meaning remains unresolved.

Three-object not-grouped scaling update:

- `text_three_objects_not_grouped.txt` adds a same-color, three-independent-text-object not-grouped fixture.
- parser chain count: `3`
- `CParagraphe` count: `1`
- `CPropertyExtend` `CObDao` section count: `11`
- `CPropertyExtend` anchor hit count: `2`
- `CParagraphe` direct anchor matches chain2 `(311.111, 422.222, 0.0)`.
- `CPropertyExtend` anchor-bearing section index `2` matches chain1 `(211.111, 322.222, 0.0)`.
- `CPropertyExtend` anchor-bearing section index `7` matches chain0 `(111.111, 222.222, 0.0)`.

Current scaling interpretation:

- current evidence supports one `CParagraphe` direct anchor plus `N-1` `CPropertyExtend` anchor hits for `N` parsed text chains.
- two-object not-grouped fixtures have 6 `CObDao` sections, but the three-object not-grouped fixture has 11 sections.
- therefore `section_count = 4 + object_count` is not a valid general rule.
- 148-byte non-anchor `CObDao` section candidates appear multiple times in the three-object fixture, so the earlier single-inserted-section model is incomplete.
- anchor-bearing section selection remains unresolved; parser promotion is still blocked.

Order-aware fixture design update:

- new Type3/CAM observation suggests grouped objects may preserve object order.
- selection order / creation order / internal order may affect:
  - parser chain order
  - `CParagraphe` direct anchor ownership
  - `CPropertyExtend` anchor ownership
  - anchor-bearing `CObDao` section order
- therefore future multi-object text fixtures must record order metadata explicitly.

Current order metadata summary:

| fixture | grouping | attempted selection order | actual stored order | parser chain order | `CParagraphe` owner | `CPropertyExtend` owners |
|---|---|---|---|---|---|---|
| `text_group_same_color_two_objects.txt` | grouped | unknown | unresolved | chain0 `abcdefg`, chain1 `1234567890` | chain0 | chain1 |
| `text_group_mixed_color_two_objects.txt` | grouped | unknown | unresolved | chain0 `abcdefg`, chain1 `1234567890` | chain0 | chain1 |
| `text_two_objects_mixed_color_not_grouped.txt` | not_grouped | unknown | unresolved | chain0 `abcdefg`, chain1 `1234567890` | chain1 | chain0 |
| `text_two_objects_same_color_not_grouped.txt` | not_grouped | unknown | unresolved | chain0 `abcdefg`, chain1 `1234567890` | chain1 | chain0 |
| `text_two_objects_not_grouped_selection_reversed.txt` | not_grouped | B -> A attempted | unresolved | chain0 `abcdefg`, chain1 `1234567890` | chain0 | chain1 |
| `text_three_objects_not_grouped.txt` | not_grouped | A -> B -> C attempted | unresolved | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | chain2 | chain1, chain0 |

Planned grouped order fixtures:

- `text_three_objects_grouped_order_abc`
  - object count: 3
  - grouping: grouped
  - attempted selection order: A -> B -> C
  - A: `abcdefg`, `(111.111, 222.222, 0.0)`, Army Green
  - B: `1234567890`, `(211.111, 322.222, 0.0)`, Army Green
  - C: `XYZ`, `(311.111, 422.222, 0.0)`, Army Green
- `text_three_objects_grouped_order_cba`
  - object count: 3
  - grouping: grouped
  - attempted selection order: C -> B -> A
  - C: `XYZ`, `(311.111, 422.222, 0.0)`, Army Green
  - B: `1234567890`, `(211.111, 322.222, 0.0)`, Army Green
  - A: `abcdefg`, `(111.111, 222.222, 0.0)`, Army Green

Policy:

- selection order and actual stored order must remain separate fields.
- grouped order observations must not be promoted to parser behavior until analyzer evidence exists.
- no fixed offset, filename, or baseline-match parser rule should be added from these planned fixtures alone.

Grouped order fixture analyzer results:

| fixture | attempted order | parser chain order | `CObDao` section count | `CParagraphe` owner | `CPropertyExtend` owners |
|---|---|---|---:|---|---|
| `text_three_objects_grouped_order_abc.txt` | A -> B -> C | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | 9 | chain0 | chain1, chain2 |
| `text_three_objects_grouped_order_abc_content_variation.txt` | A -> B -> C | chain0 `Type3`, chain1 `9876543210`, chain2 `HELLO` | 9 | chain0 | chain1, chain2 |
| `text_three_objects_grouped_order_abc_height_30mm.txt` | A -> B -> C | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | 9 | chain0 | chain1, chain2 |
| `text_three_objects_grouped_order_abc_font_arial_bold.txt` | A -> B -> C | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | 9 | chain0 | chain1, chain2 |
| `text_three_objects_grouped_order_abc_mixed_color.txt` | A -> B -> C | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | 9 | chain0 | chain1, chain2 |
| `text_three_objects_grouped_order_cba.txt` | C -> B -> A | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | 9 | chain2 | chain1, chain0 |
| `text_three_objects_not_grouped.txt` | A -> B -> C | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | 11 | chain2 | chain1, chain0 |
| `text_three_objects_not_grouped_mixed_color.txt` | A -> B -> C | chain0 `abcdefg`, chain1 `1234567890`, chain2 `XYZ` | 11 | chain2 | chain1, chain0 |

Updated interpretation:

- grouped 3-object samples show fewer `CObDao` sections than the 3-object not-grouped sample (`9` vs `11`).
- parser chain order currently remains stable across grouped A-B-C and grouped C-B-A attempts.
- `CParagraphe` and `CPropertyExtend` anchor ownership do vary with attempted grouped order.
- the `N chains -> 1 CParagraphe anchor + N-1 CPropertyExtend anchors` pattern still holds for current grouped 3-object samples.
- this improves order-effect evidence but does not yet provide a baseline-independent anchor-bearing section selector.

Current text anchor storage model:

- confirmed parser behavior: active text anchor remains the parser-derived `baseline_midpoint` fallback.
- strong observed candidate: single-object `CParagraphe` direct triple at offsets 158/166/174.
- observed multi-object model: for `N` parsed text chains, one anchor is in `CParagraphe` and `N-1` anchors are in `CPropertyExtend` `CObDao + 34` sections.
- provisional selection model: attempted selection/group creation order appears to influence which chain is the `CParagraphe` owner, but actual stored order is unresolved.

Section scaling model:

| object count | grouped sections | not-grouped sections | observed delta |
|---:|---:|---:|---:|
| 2 | 5 | 6 | 1 |
| 3 | 9 | 11 | 2 |

The current candidate is `not_grouped_delta = object_count - 1`. This is only provisional; it describes the current fixture set but is not a parser rule.

Parser promotion blocker:

- `CObDao + 34` is a strong local position candidate for CPropertyExtend anchors.
- coordinate-like values also occur in non-anchor sections.
- section index/order alone is insufficient across grouped/not-grouped and selection-order variants.
- parser promotion needs a stable anchor-bearing section selector and a chain ownership rule that does not use baseline equality as the selector.

CObDao local field selector audit:

- analyzer labels remain evidence-only and are derived from current known anchor matches.
- current multi-object set contains 11 anchor-bearing and 46 non-anchor `CObDao` sections.
- after adding 3-object mixed-color, style/font, and content fixtures, the set contains 21 anchor-bearing and 83 non-anchor `CObDao` sections.
- current strongest field leads are:
  - `u32le@CObDao+12 == 131072`
  - `u32le@CObDao+56 == 262144`
  - `u32le@CObDao+108 == 65536`
  - `u32le@CObDao+112 == 262144`
- each separates the current labeled set with zero false positives, but none is parser-safe yet because the semantic meaning of those local fields is unresolved.
- coordinate-like `CObDao + 34` remains rejected as a selector due to non-anchor false positives.
- 3-object mixed-color validation did not change section counts, ownership pattern, or selector lead values relative to same-color fixtures.
- 3-object height 30mm and Arial Bold validation did not change section counts, ownership pattern, or selector lead values relative to same-color fixtures.
- 3-object content variation did not change section counts, ownership pattern, or selector lead values; parser chain text order changed, so stored order remains unresolved.

Local record signature candidate:

- candidate name: `CPropertyExtend_CObDao_anchor_record_candidate_v1`
- required context: `CPropertyExtend`, `OBJETINFOS_CLASSNAME` at `CObDao - 24`, and a `CObDao` marker
- required fields: `u32(+12)=131072`, `u32(+56)=262144`, `u32(+108)=65536`, `u32(+112)=262144`
- required coordinate candidate: finite coordinate-like `double64le` triple at `CObDao+34`, z near 0
- current evaluation: 21/21 anchor-bearing sections matched, 0/83 non-anchor sections matched
- parser-safe status: provisional false

Rejected single-field rules:

- coordinate-like `CObDao+34` alone has non-anchor false positives.
- each individual u32 field is only a lead and lacks confirmed record semantics.
- section index, payload offset, and baseline equality remain invalid parser selectors.

## Anchor-context analyzer runtime policy

- default (`tools/analyze_text_cproperty_anchor_context.py`, `--json`, `--markdown`) is safe summary mode.
- deep local/record semantics output is available only with `--deep`.
- for IDE stability (PyCharm console), deep output should be redirected to a file instead of direct console streaming.

```powershell
.\.venv\Scripts\python.exe tools\analyze_text_cproperty_anchor_context.py --json --deep --max-sections 20 --max-output-rows 50 > out.json
```

Small dedicated semantics analyzer:

- `tools/analyze_text_cproperty_anchor_record_semantics.py`
- purpose: limited local semantics observation for `CPropertyExtend_CObDao_anchor_record_candidate_v1`
- default behavior is bounded and small-output; heavy pairwise/near-miss dumps are intentionally excluded.
- interpretation remains provisional and analyzer-only.

CPropertyExtend direct-anchor decode RFC:

- `docs/text_cproperty_anchor_decode_rfc.md`

Current note:

- signature v1 checked offsets are stable in current controlled fixture groups.
- this does not change parser readiness; status remains `not_ready_analyzer_only`.
- decode and ownership are explicitly separated; implementation is deferred.
- Phase 1 is now implemented as candidate-only output (`candidate_fields["cproperty_anchor_candidates"]`).
- ownership remains `unresolved`, confidence remains `provisional`, and active anchor behavior is unchanged.

## Visible text ownership analysis status

See the [Text Anchor Ownership Mapping RFC](text_anchor_ownership_mapping_rfc.md)
for separate ownership layers, candidate strategy comparisons, and parser-safe
requirements. Phase 2A is implemented in `tools/analyze_text_anchor_shadow_mapping.py`
as shadow mapping only. Structural B/D/E hypotheses are frozen before isolated
oracles run; `--no-oracle` skips intent and preserves the hypotheses. All 13 fixtures
remain analyzable, including four unknown-order fixtures. B is blocked, D unresolved,
and E finds no typed linkage; conditional pairing contradicts three fixtures.
Parser output, `matched_chain=None`, and active anchors are unchanged;
`parser_safe=false` remains mandatory and Phase 2 parser ownership is not authorized.

CParagraphe ownership is now the primary structural blocker. The dedicated
`tools/analyze_text_cparagraphe_owner_structure.py` freezes all 13 structural
inventories before oracle/intent access and supports `--no-oracle`. It finds a
nearest-following CContour source-chain correlation with 13 diagnostic agreements,
while the chain0 control has 8 agreements and 5 conflicts. CParagraphe adjacency
is constant (CZone before, CCourbe after), but the output chain sourced from
CContour differs between ABC, CBA, and not-grouped layouts. Existing parser
coordinate sorting explains why source role and output index are distinct;
the analyzer adds no sorting or anchor-equality selector. Grouping changes
CObDao section counts, not the top-level class sequence, and local shared
integer 2 matches every chain preamble rather than a unique owner. The
content-variation source relationship survives changed text labels.
These remain correlations: `no_parser_safe_cparagraphe_owner_rule_found`.
All hypotheses stay `parser_safe=false`; parser/active anchors/matched_chain
are unchanged and ownership implementation remains unauthorized. Detailed
case evidence is in the [ownership RFC](text_anchor_ownership_mapping_rfc.md#cparagraphe-owner-structural-investigation).

- This stage adds analyzer-only visibility for multi-object text ownership:
  - parser chain order
  - chain text candidate vs chain anchor candidate
  - attempted selection order vs parser chain order
  - grouped/not-grouped variation impact
- Tool: `tools/analyze_text_visible_ownership.py`
- Output contracts:
  - text summary
  - compact JSON
  - markdown summary tables
- Interpretation policy:
  - text candidate ownership can be observed per chain
  - anchor ownership remains unresolved for CPropertyExtend candidates
  - do not treat analyzer observations as parser-confirmed ownership rules yet

## Multi-object intent order metadata (schema v1)

The visible ownership analyzer reads a fenced `yaml` block under `intent_metadata`.
Existing human-readable capture notes are preserved. Example for a known attempted order:

```yaml
intent_metadata:
  schema_version: 1
  object_count: 2
  grouping: not_grouped
  order_control_status: attempted
  attempted_selection_order:
    - label: B
      text: "1234567890"
      anchor_mm: [211.111, 322.222, 0.0]
      color: Army Green
    - label: A
      text: abcdefg
      anchor_mm: [111.111, 222.222, 0.0]
      color: Army Green
  actual_stored_order: unresolved
  notes:
    - attempted selection order is user-observed or user-attempted
    - actual payload stored order is not assumed
```

`grouping` is `grouped`, `not_grouped`, or `unknown`. `order_control_status` is
`attempted`, `unknown`, or `controlled_observed`; the last value requires explicit
capture evidence and is not inferred from a filename or parser output. Unknown older
captures use `attempted_selection_order: []` and a note that selection order was not
recorded. Labels identify objects, and list position records attempted selection order.
Quote numeric text strings; anchors contain three finite coordinates in mm.

Attempted selection order and parser chain text order are separate observations.
Neither proves actual payload stored order; `actual_stored_order` stays `unresolved`
in this schema. Intent anchors/colors describe capture intent, not assigned ownership.
The analyzer uses intent metadata only for reporting. Parser, decoder and model logic
must never use fixture intent metadata or change active anchors based on it.
CPropertyExtend ownership remains unassigned.

Install the development dependencies (including PyYAML) to run
`tools/analyze_text_visible_ownership.py --json`. Valid YAML takes precedence over
loose notes. Missing/invalid YAML produces warnings and falls back to loose text,
then filename grouping/unknown order. Missing intent files do not fail analysis and
appear in `missing_intent_files` and `warnings`.

Each fixture summary includes `normalized_intent_metadata`, `attempted_order_source`
(`yaml`, `loose_text`, `filename_or_unknown`, `missing`), `order_control_status`, and
`actual_stored_order`. Missing files have null normalized metadata; legacy fallback
entries use null for unrecorded label/anchor/color rather than inventing evidence.
`intent_metadata_summary` counts processed fixtures (`total_fixtures`), validated YAML
(`with_yaml_metadata`), fixtures without valid YAML (`missing_metadata`, including
invalid or absent metadata), and unknown/attempted/controlled-observed order states.
Missing payload fixtures are excluded from these counts and listed in `missing_fixtures`.

Current inventory: all 13 current visible-ownership fixtures have schema v1 intent
metadata (9 attempted, 4 unknown), with no missing intent files and 0
controlled-observed orders. Unknown means explicitly not recorded, not inferred;
actual payload stored order remains unresolved for all fixtures.

### CParagraphe source provenance versus object ownership (2026-09-06)

The separate `analyze_text_cparagraphe_source_linkage.py` analyzer confirms the
13/13 next-producing-CContour diagnostic correlation before sorting. CContour
produces raw chain 0; CPropertyExtend produces the remaining embedded chains.
The CParagraphe / CCourbe / CContour sequence repeats in all fixtures, but CCourbe
has no independently decoded reference linking the paragraph to that source.

Scanner boundaries are plausible class headers, not verified object containment.
All produced chains share the paragraph parser group; inherited node membership
is a construction artifact and does not distinguish ownership. No independent
object boundary/link was found. Coordinate sorting changes 10 of 34 indices;
source hypotheses survive reordered final chains and removed sort coordinates.

H1/H3/H4: 13 support / 0 conflict / 0 abstention each. H2/H5: 0/0/13 each.
The adjacency-only null remains unresolved; agreement cannot prove semantic linkage.
All hypotheses remain `semantic_linkage_proven=false`, `parser_safe=false`.
Conclusion: `raw_source_chain_relationship_supported`; ownership is not ready.
Structural data are frozen before oracle/intent, unchanged with `--no-oracle`
or missing intent, with bounded output and no parser/model changes. See the
[ownership RFC](text_anchor_ownership_mapping_rfc.md#cparagraphe-source-linkage-audit-2026-09-06)
for grouped ABC/CBA, ungrouped color, content, two-object and reversed-selection
contrasts and exact sort mappings.

## Anchor Ownership Closeout and Color Ownership Handoff

Phase 2A shadow mapping and source-linkage investigation are complete. Phase 2
active parser ownership implementation is explicitly deferred until independent
evidence establishes a valid link. Final structural conclusion:
`raw_source_chain_relationship_supported`.

Strong observations: all 13 fixtures preserve the same relationship before
coordinate sorting, with candidate raw chain 0 from CContour and later chains
from CPropertyExtend embedded contours. Ten of 34 chains across five fixtures
change final index after sorting. Raw/source provenance is therefore more
fundamental for construction tracing than final parser index; neither establishes
semantic ownership by itself.

Provisional: CParagraphe-to-raw-source and CCourbe/CContour sequence correlations.
Unresolved: semantic CParagraphe ownership, independently verified object-block
linkage, unique local object identifiers, CPropertyExtend candidate-to-chain
mapping, and actual stored object order. Adjacency-only remains viable.

Rejected as parser ownership rules: baseline equality, expected-anchor selection,
attempted selection order, final sorted chain index, fixture filename, absolute
offsets, and unconditional chain-order pairing. All ownership hypotheses remain
`parser_safe=false`; no parser-safe CParagraphe or CPropertyExtend ownership rule
has been established.

| Area | Readiness |
| --- | --- |
| CPropertyExtend candidate decode | Provisional implemented |
| Raw source relationship | Structurally supported |
| Semantic CParagraphe ownership | Unresolved |
| CPropertyExtend ownership | Unresolved |
| Phase 2 active ownership implementation | Deferred / not ready |

`matched_chain = None`, active text anchors, and the `baseline_midpoint` fallback
remain unchanged. Reopen anchor ownership only with independent boundary,
reference, or semantic identifier evidence that distinguishes linkage from
adjacency; more coordinate agreement alone is insufficient.

Next track: **color ownership**, starting from existing color candidate and
single-object/grouped/not-grouped mixed-color evidence. Distinguish field decoding
from candidate-to-object ownership and trace raw sources separately from sorted
indices. Do not use unresolved anchor ownership as a color ownership oracle.
This handoff adds no analyzer, parser/decoder/model change, ownership heuristic,
or fixture. See the [ownership RFC closeout](text_anchor_ownership_mapping_rfc.md#12-final-ownership-investigation-closeout)
for the authoritative status and reopening requirements.

Verification baseline: `PYTHONPATH=src pytest -q` — **311 passed**.
## Color Phase 1C: multi-chain scaling without ownership

`tools/analyze_text_color_record_semantics.py` reports chain counts separately
from paragraph chunks and CPropertyExtend textual CObDao sections. The table
uses fixture labels to identify the requested controls; grouping itself is not
independently decoded and remains null in the structural output.

| Fixture cohort | Parser chains | Chunks | Repeated | Sections | Extracted paragraph text |
| --- | ---: | ---: | ---: | ---: | --- |
| grouped two, same/mixed color | 2 | 10 | 8 | 5 | abcdefg |
| not-grouped two, same/mixed color | 2 | 14 | 11 | 6 | 1234567890 |
| grouped three, baseline/mixed color | 3 | 10 | 8 | 9 | abcdefg |
| grouped three, content variation | 3 | 8 | 6 | 9 | HELLO |
| not-grouped three, baseline/mixed color | 3 | 6 | 4 | 11 | XYZ |

Every row has one CContour node; existing parsed contour record totals are
twice the chain count. Repeated count instead matches the extracted paragraph's
slot count, including a zero-code slot. In particular, changing content at
three chains/nine sections changes repeated count from eight to six. Neither
chain count nor section count explains that change. One chunk per object or
per text run is not supported. The 204-byte slot stride remains credible, while
the entire paragraph's fixed slicing is only a provisional inventory.

These are paragraph text candidates, not complete text inventories across all
objects. Total character count across objects, selected-object correspondence,
and a grouping-specific serialization rule remain unresolved. No anchor mapping
or color ownership is used. A structurally usable multiline control also has
two chains, but its local color context is unmatched and candidate count is
left null. Field decoding and ownership remain not ready; typed color width
is null. See [Color Phase 1C](text_color_decode_rfc.md) for oracle isolation and
bounded-window evidence. Existing anchor and MFC conclusions are unchanged.

## Color Phase 1D: paragraph schema compatibility without object mapping

The new bounded schema analyzer reports the following leading paragraph runs.
The cohort names identify fixtures only; no object, chain, anchor or attempted-order
mapping enters extraction or scoring.

| Existing fixture cohort | Enumerated slots | Single-line grid compatible |
| --- | ---: | --- |
| grouped two, same/mixed color | 8 | yes, provisional |
| not-grouped two, same/mixed color | 11 | yes, provisional |
| grouped three, baseline | 8 | yes, provisional |
| grouped three, content variation | 6 | yes, provisional |
| not-grouped three | 4 | yes, provisional |
| multiline contrast | 10 | no; alternate prefix +68 |

All these runs retain a 204-byte prefix period and a preceding count equal to
enumeration. There are no interior prefix breaks in the enumerated run, including
at multiline's code 13. Additional runs outside the bounded leading region remain
unresolved; these counts are not document-wide or per-object text totals.
Diagnostic capture text alternatives are unordered and used only after structural
freeze. They cannot select a boundary, code position or object correspondence.

Start 47 is not uniquely favored over nearby starts by structural repetition.
The supported prefix is 310 for single-line controls and 378 for multiline.
Code +0x3F is relative to the provisional single-line grid. Wider windows reveal
first-slot context versus remaining-slot classes, so the result is a
**provisional CParagraphe text-slot record schema**, not a confirmed record model.
The final zero remains a terminal candidate; typed color width is null. Both
candidate parser model and color ownership readiness are `not_ready`. The
[Phase 1D RFC](text_color_decode_rfc.md) records compact-output bounds and tests.
Parser, decoder, model, anchor closeout and MFC conclusions are unchanged.

## Color/Text Slot Phase 1E: prefix compatibility without ownership

Dynamic count-framed prefix discovery succeeds for all seven multi-object controls:
grouped two have eight slots; not-grouped two have eleven; grouped three baseline
has eight, grouped content variation six, and not-grouped three four. Each retains
204 recurrence, prefix-relative code +4, candidate color +0x50..+0x52 and final
zero plus prefix loss. No slots are mapped to objects, chains, anchors or order.

The raw `05` prefix alone yields two equal-length periodic candidates, separated
by 92 bytes. The leading count/context condition distinguishes the proposed slot
run structurally. These counts describe bounded paragraph runs, not object totals.
Fixture names and capture expectations do not enter discovery. The historical
payload location 310 is retained only as a control hypothesis, which conflicts
with the four multiline/spacing controls automatically found at 378.

Those four shifted runs share the baseline positive-prefix signature and retain
code 13 inside the same 204-byte recurrence. Color normalization there is supported
by matching masked local context; no changed-color multiline capture proves typed
color semantics. First-slot differences observed previously are upstream of the
prefix; no semantic subtype is assigned. Typed code and color widths stay null.

The [Phase 1E RFC](text_color_decode_rfc.md) documents a supported bounded framing
candidate with `parser_safe=false`. Candidate parser-model and color-ownership
readiness remain `not_ready`. Existing parser/decoder/model behavior, anchor
closeout and MFC conclusions are unchanged.

## Text Slot Phase 1F: paragraph-run count, not object count

For every requested multi-object control, the candidate at prefix -4 counts the
enumerated paragraph slots including the final zero. It is not an object count,
chain count or text-to-object mapping. Grouped two controls have eight slots,
not-grouped two eleven, grouped three baseline eight, grouped content variation
six, and not-grouped three four. These remain bounded leading-run inventories.

All seven controls fit the invariant-core/exact-variant family. The baseline
signature occurs in both grouped and not-grouped fixtures; a second signature
occurs in the grouped mixed-color two-object control. This does not establish a
general grouping or mixed-color flag. Grouping and style/content labels are
applied only after structural freeze. Four shifted multiline controls use the
baseline prefix family and the same count offset, including code 13 and final zero.

Count evidence and family evidence are reported independently. A valid family
with wrong count remains visible as conflict, while a matching count cannot
validate false periodic context. Multiple family-valid runs are left ambiguous;
the analyzer does not resolve them through object labels, anchors or order.
Typed count, slot-code and color widths remain unresolved, with normalized code
+4 and color +0x50..+0x52 retained as candidates.

The [Phase 1F evidence](text_color_decode_rfc.md) supports readiness for a bounded
candidate parser RFC, with explicit coverage/abstention rules. Candidate parser
model and ownership readiness remain `not_ready`; no parser/model implementation
or ownership assignment is performed. Anchor closeout and MFC conclusions are
unchanged.
