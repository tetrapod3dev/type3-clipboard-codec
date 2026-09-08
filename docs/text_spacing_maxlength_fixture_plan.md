# Controlled Character Spacing and Maximum-Length Fixture Plan

Date: 2026-09-09. Status: **inventory and capture intent only**.

## 1. Scope

This inventory identifies eight newly supplied fixtures and their single intended
experimental variables. It prepares labels for a later differential study; it
contains no byte comparison, field localization, F4 constant validation, runtime
interpretation, ownership analysis or geometry reverse engineering. Raw captures,
runtime, analyzers and semantic models are unchanged by this documentation work.
Actual repository filenames below are authoritative inventory identifiers, never
runtime selectors. Program behavior is supplied by the capture operator, not
inferred from serialized bytes or external TYPE3 CAA documentation.

## 2. Baseline

All eight experiments use the existing
[text_slotstyle_a8_baseline.txt](../tests/samples/text/text_slotstyle_a8_baseline.txt)
and its [controlled-style intent](../tests/samples/intents/text/text_slotstyle_a8_baseline.md).
“Baseline” means the common default sample for every comparison, not a new capture.

| Baseline setting | Operator-supplied value |
| --- | --- |
| Text / visible character count | AAAAAAAA / 8 |
| Font | Arial |
| Height | 10 mm |
| Width | 100% |
| Slant / rotation | 0 / 0 |
| Color | Army Green |
| Character spacing / 자간 | 100% |
| Maximum length | 0 mm |
| Actual natural text-box length | 74.584 mm |
| Alignment | center-bottom |
| Known baseline lower-left | [31.123, 72.234, 1.234] mm |
| Known baseline anchor | [68.415, 72.234] mm |

The operator confirms that maximum length 0 mm uses the font's natural text
length. These values are capture labels, not claims about stored field widths,
units or positions. Baseline Z=1.234 mm was a diagnostic control to avoid
zero-heavy coordinate patterns; it adds no semantic Z parser interpretation.

## 3. Actual Fixture Inventory

Each filename links to the unchanged raw capture; the intent column links to
schema_version 1 metadata in the repository's Markdown/YAML convention.

| Actual fixture filename | Intended scope/change | Intent |
| --- | --- | --- |
| [text_slotstyle_a8_char4_spacing50.txt](../tests/samples/text/text_slotstyle_a8_char4_spacing50.txt) | Character 4 only: spacing 50% | [metadata](../tests/samples/intents/text/text_slotstyle_a8_char4_spacing50.md) |
| [text_slotstyle_a8_char4_spacing150.txt](../tests/samples/text/text_slotstyle_a8_char4_spacing150.txt) | Character 4 only: spacing 150% | [metadata](../tests/samples/intents/text/text_slotstyle_a8_char4_spacing150.md) |
| [text_slotstyle_a8_char6_spacing150.txt](../tests/samples/text/text_slotstyle_a8_char6_spacing150.txt) | Character 6 only: spacing 150% | [metadata](../tests/samples/intents/text/text_slotstyle_a8_char6_spacing150.md) |
| [text_slotstyle_a8_all_spacing150.txt](../tests/samples/text/text_slotstyle_a8_all_spacing150.txt) | Visible characters 1–8: spacing 150% | [metadata](../tests/samples/intents/text/text_slotstyle_a8_all_spacing150.md) |
| [text_maxlength_a8_100mm.txt](../tests/samples/text/text_maxlength_a8_100mm.txt) | Whole text object: maximum length +100 mm | [metadata](../tests/samples/intents/text/text_maxlength_a8_100mm.md) |
| [text_maxlength_a8_60mm.txt](../tests/samples/text/text_maxlength_a8_60mm.txt) | Whole text object: maximum length +60 mm | [metadata](../tests/samples/intents/text/text_maxlength_a8_60mm.md) |
| [text_maxlength_a8_40mm.txt](../tests/samples/text/text_maxlength_a8_40mm.txt) | Whole text object: maximum length +40 mm | [metadata](../tests/samples/intents/text/text_maxlength_a8_40mm.md) |
| [text_maxlength_a8_m60mm.txt](../tests/samples/text/text_maxlength_a8_m60mm.txt) | Whole text object: maximum length -60 mm | [metadata](../tests/samples/intents/text/text_maxlength_a8_m60mm.md) |

This cohort is four spacing plus four maximum-length captures. Existing older
text_spacing_* fixtures and the nine prior controlled style captures are not
new members of these eight. The shared baseline is an additional existing input.

## 4. Shared Capture Controls

Unless an individual intent says otherwise, text, font, height, width, slant,
rotation, color and alignment have the baseline values above. Spacing starts at
100% and maximum length at 0 mm. Each capture changes one intended setting at
the specified scope; settings are restored from baseline before applying that
change and reset again before the next capture. Target selection defines the
scope of the experiment, not another inferred serialized field.

Anchor/capture setup is inherited from the controlled baseline. The metadata
stores coordinates under baseline_capture_setup and explicitly marks resulting
lower-left/bounding-box geometry as not asserted. In particular, maximum length
can legitimately change text-box geometry as an outcome. Fixed input settings
and inherited anchor intent do not prove identical resulting coordinates or
dimensions. No resulting bounding box is measured or inferred here.

## 5. Character-Spacing Fixtures

Use the operator's terminology **character spacing / 자간**. Default is 100%.
The program allows single-character application and multiple selected characters.
Do not rename this setting “Extra Space” or assume equivalence to a feature in
external TYPE3 CAA documentation.

The first three spacing intents use changed_scope=character with 1-based targets
4, 4 and 6 respectively. The fourth uses changed_scope=all_visible_characters
with target_character_indices_1based=[1,2,3,4,5,6,7,8]. Every intent has
property=character_spacing, baseline_value_percent=100, its changed_value_percent,
all_other_character_properties_held_constant=true and
capture_reset_from_baseline=true. No terminal slot is intentionally styled.
The presence, position or serialization of a terminal remains a future question.

## 6. Maximum-Length Fixtures

Maximum length is a **text object/text-box setting**, not a character-level
setting. All four intents use changed_scope=text_object, property=maximum_length,
baseline_value_mm=0 and baseline_natural_length_mm=74.584. They contain no target
character index. Other character settings, including width and spacing, start
at baseline even when rendered text changes as an outcome.

| Requested length | expected_ui_relationship | Operator-observed program behavior |
| --- | --- | --- |
| +100 mm | greater_than_natural_length | Text box expands to the requested range; glyphs are not compressed or stretched merely because the requested length exceeds natural length |
| +60 mm | less_than_natural_length | Text is compressed horizontally to fit the specified maximum length |
| +40 mm | well_below_natural_length | Text is compressed more strongly than at 60 mm |
| -60 mm | negative | Text appears in the program's negative-length inverted/reflected form, observed downward |

“More strongly” is descriptive capture intent, not a numeric/binary oracle.
Negative-length UI behavior does not establish a mirror flag, sign bit, Y flip,
negative scale, scale factor or transform matrix. These are at most future
binary-analysis hypotheses. This inventory assigns none of those encodings.

## 7. Natural Baseline Length: 74.584 mm

74.584 mm is the operator-confirmed actual natural text-box length for this
specific AAAAAAAA/Arial baseline. Maximum length 0 mm means use natural font
length in the observed program behavior; it does not mean a zero-length text box.
The value is neither a universal Arial metric nor a format constant. It must not
be searched for or used to nominate binary structures in a future analyzer.

## 8. Per-Character versus Object-Level Experiments

| Experimental group | UI properties |
| --- | --- |
| Per-character property experiments | height, width, slant, rotation, color, character spacing |
| Object/text-box property experiments | maximum length |

Applying spacing to all visible characters remains a character-property
experiment. Conversely, a maximum-length operation that changes rendered glyph
width does not promote that setting into per-slot style serialization. This
grouping describes operator intent only, not confirmed binary storage locations.

## 9. Experimental Rationale

| Control | Purpose of a later study |
| --- | --- |
| char4 spacing 50 / 150 | Compare low/high changes around 100%; find correlated byte ranges later and evaluate numeric representation without assuming one now |
| char6 spacing 150 | Ask whether a discovered field follows the selected ordinal instead of a character-4-specific artifact |
| all spacing 150 | Compare one-character and all-character application; ask whether the same field repeats across all eight visible slots |
| maximum length 100 | Isolate above-natural object/text-box setting changes from compression effects |
| maximum length 60 / 40 | Compare two below-natural levels; distinguish a stored requested value from derived compression/layout changes |
| maximum length -60 | Compare positive/negative behavior and later localize sign/reflection-related changes without assigning their encoding |

## 10. Oracle Isolation

Intent metadata is available only after future structural/differential results
are frozen. Filenames, target indices, expected spacing, requested maximum
length, natural baseline length, expected compression and expected reflection
must not locate, select, rank or validate binary structures. The capture labels
in this document are reporting oracles only. No runtime fixture-name branching,
expected-value-driven selection or semantic promotion follows from this inventory.

## 11. Future Analysis Questions — Unanswered

Character spacing:

1. Is spacing represented inside the 204-byte repeated slot?
2. Does char4 versus char6 move the same slot-relative field with the selected ordinal?
3. Does all-character spacing alter that field in all eight visible slots?
4. Does the terminal behave differently?
5. Does F4 +0x24..+0x2B change?
6. Does F4 +0x38..+0x3F change?

Maximum length:

1. Where is the requested maximum-length value serialized?
2. Is it outside the repeated slot run?
3. Does +100 mm change only text-box/object metadata?
4. What additional changes appear when compression activates at 60/40 mm?
5. Does -60 mm introduce a separate transform/reflection representation?
6. Are any F4 structural constants affected indirectly?

None of these questions is evaluated or answered in this step.

## 12. Current Runtime Status and Inventory Validation

Context from [v2 acceptance](text_slot_prefix_family_v2_promotion_review.md#candidate-only-runtime-v2-acceptance-2026-09-09):
active source=CParagraphe_slot_prefix_family_v2;
runtime_v2_replacement_acceptance=accepted_candidate_only; parser_safe=false;
typed widths=null/unresolved; ownership=unresolved; matched_chain=null.
These are existing statuses, not results from interpreting the eight new captures.
No F4 change or new constant validation is performed here.

Previous full-suite baseline: **1061 passed**, before adding this new cohort.
Inventory validation is limited to file existence, YAML intent consistency,
local links and raw-file hash preservation. Existing capture-workflow unit tests
use mocked clipboard/parser services and temporary data. The full suite includes
automatic differential-analyzer corpus discovery, so it is not run in this
inventory-only step: doing so would execute analysis of the new captures.
No new tests or analyzer are added. Capture-workflow pytest: **9 passed**
(existing mocked tests, not a new full-suite total). All eight intent YAML records,
fixture/baseline references, local links and twelve plan sections pass the
inventory checks. All eight raw-file SHA-256 hashes match their values at task
start, preserving the operator's existing staged/unstaged capture edits.
git diff --check passes. No new fixture is parsed or interpreted by these checks.
