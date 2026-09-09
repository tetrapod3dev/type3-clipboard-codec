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

## Character-spacing differential results (2026-09-10)

This section supersedes the earlier spacing-only "future/unanswered" status;
prior inventory and accepted runtime history remain historical evidence.
Maximum-length fixtures: **captured / analysis pending**. They are excluded
from the new spacing analyzer's exact five-input inventory.

Analyzer: `tools/analyze_text_slot_spacing_fields.py`; regression tests:
`tests/integration/test_text_slot_spacing_fields_cli.py`. Run with `--json`,
`--no-oracle`, or `--details`. Numeric ranges in JSON are half-open.
Phase A observes runtime before independent CParagraphe token recurrence,
count views and zero-terminal boundary validation. It compares every byte in
nine complete 204-byte windows; first prefix is payload-relative 310 (0x136),
run end 2146. A second recurrence at 402 is retained but fails framing.
Ambiguous compatible runs remain unresolved. Filename spelling, target indices,
spacing percentages, RGB expectations and natural length do not select runs.
Frozen structural JSON is hashed before any intent file is read.

| Exact fixture | Runtime candidate | Changed zero-based slots | Exact local delta |
| --- | --- | --- | --- |
| text_slotstyle_a8_baseline.txt | present | none | reference F0 |
| text_slotstyle_a8_char4_spacing50.txt | present | 3 | +0x46: F0 -> E0 |
| text_slotstyle_a8_char4_spacing150.txt | present | 3 | +0x46: F0 -> F8 |
| text_slotstyle_a8_char6_spacing150.txt | present | 5 | +0x46: F0 -> F8 |
| text_slotstyle_a8_all_spacing150.txt | present | 0..8 | +0x46: F0 -> F8 |

All five parse successfully and independently align. Every runtime result has
source `CParagraphe_slot_prefix_family_v2`, prefix_family=F4, first prefix=310,
slot_count=9 and plus08_value=0. No runtime abstention occurs in this cohort.
The only changed byte inside complete slot windows is +0x46 (JSON [70,71)).
After freeze, intent supports `spacing_correlated_field_candidate` and
`strong_style_field_candidate`: char4 low/high isolation is supported,
`ordinal_transfer_supported=true`, and `visible_slot_replication_supported=true`.
The two single-position 150% captures have identical raw F8 at different ordinals.
All eight visible slots repeat F8. Terminal slot 8 ALSO changes F0 -> F8 in
all-spacing150, despite not being an intentionally styled visible character.
Single-character controls leave terminal unchanged. Its slot-code remains zero;
visible code diagnostics remain 65 x 8 and RGB diagnostics remain unchanged.
Terminal setting propagation/ownership semantics remain unresolved.

The exact discovered delta is ONE byte. No exact discovered 4/8-byte range
exists, so normalized-ratio, delta-from-baseline and raw-percentage float/integer
diagnostics are inapplicable under this task's exact-range restriction.
The analyzer does not widen +0x46 to nearby 4/8-byte containers to seek a match.
`diagnostic_spacing_encoding=unresolved`; typed width remains null/unresolved.
No `character_spacing_field_confirmed` promotion is made.

F4 region A (+0x24..+0x2B) remains `00 00 00 00 00 00 00 00` in all 45
aligned slots. Region B (+0x38..+0x3F) independently remains
`9A 99 99 99 99 99 D9 BF`. Targets, non-targets and terminal are all invariant.
Both results are `not_falsified_by_current_spacing_controls`, not confirmation
of structural constants. No F4 style contamination is demonstrated here.
Auxiliary +0x2C..+0x2F is unchanged in every slot: no target-local, all-slot,
direction or magnitude correlation is demonstrated; semantics remain unresolved.

Secondary changes are retained, without speculative field names:

| Capture suffix | Before first slot | After slot windows | Before payload | After payload |
| --- | ---: | ---: | ---: | ---: |
| char4_spacing50 | 48 | 116 | 14 | 95 |
| char4_spacing150 | 47 | 113 | 13 | 92 |
| char6_spacing150 | 47 | 113 | 13 | 93 |
| all_spacing150 | 63 | 126 | 14 | 96 |

Counts are changed bytes within each comparison domain, not disjoint global
summands. CParagraphe node header is unchanged. CZone, CCourbe and CContour bbox
changes provide derived geometry evidence; CCourbe, CContour and CPropertyExtend
payload changes are also reported. Other secondary range semantics are unresolved.
Baseline natural text-box length is 74.584 mm; it is documentation only and
never used as a binary selector or normalization target.

Active runtime remains family v2/F4, `accepted_candidate_only`, Policy A,
exact F4 identity and Gate 8 rejection-only veto. Runtime source, models,
fixtures and prior analyzers are unchanged. `matched_chain=null`;
`runtime_f4_review_readiness=no_spacing_falsification_trigger`;
`runtime_change_readiness=not_authorized_in_this_task`; `parser_safe=false`;
ownership unresolved. These controls do not justify widening or masking F4.

Validation: targeted spacing CLI tests **19 passed**; full
`PYTHONPATH=src pytest -q`: **1088 passed** (historical pre-analysis reference:
1061). Ruff passes the new analyzer, new tests and modified test-only replay
helper. `git diff --check` passes; `git diff -- src/type3_clipboard_codec` is empty.
All five raw-file SHA-256 hashes match the initial observation and are pinned in
the new tests; fixture and previous-analyzer diffs are empty. The configured
PyCharm SDK used for verification is Python 3.13.5.

The initial full-suite attempt exposed historical v1 replay copying later
captures into its frozen corpus (22 failures, 17 errors). The test-only
`tests/text_slot_v1_replay.py` now copies text captures from the stored historical
baseline inventory. No analyzer or capture is edited, and maximum-length inputs
are excluded from those historical replays. The successful full rerun includes
all original assertions; none were removed or skipped.

UTF-8 rendered sizes including final LF: default JSON **79,571 bytes**;
text **27,539 bytes**; details JSON **81,580 bytes**; details text **27,539 bytes**.
Default structural freeze SHA-256:
`57e844610b3b3acf5619e0b952e075b5ed65e112cc1a40f35576da3237bb2c06`.
No full slot dumps are emitted. Oracle-disabled/adversarial target/value tests
preserve this structural evidence, and renamed copies select the same raw run.

## Fixed-window spacing ratio follow-up (2026-09-10)

This numeric interpretation follow-up explicitly authorizes only prefix
+0x40..+0x47, following the independently discovered +0x46 delta. It supersedes
encoding-unresolved status for this diagnostic hypothesis only; the earlier
exact-delta analysis and its restriction remain valid historical results.
Use `tools/analyze_text_slot_spacing_fields.py --spacing-ratio --json`;
`--no-oracle` retains identical `spacing_ratio_raw` and structural freeze hash.
The default CLI and its previous exact-delta tests remain unchanged.

No new field discovery or neighboring-offset search is performed. Existing
independent alignment is reused; every aligned slot is read at the same fixed
[64,72) window. Exact eight-byte windows AND f64le raw reads are frozen before
intent loading. `spacing_ratio_summary` then records target/non-target/terminal
roles and expected-ratio matching, separate from raw evidence. No other numeric
encoding is tested in this follow-up.

Define exact raw windows (little-endian):

| Window | Exact +0x40..+0x47 bytes | f64le |
| --- | --- | ---: |
| B | 00 00 00 00 00 00 F0 3F | 1.0 |
| L | 00 00 00 00 00 00 E0 3F | 0.5 |
| H | 00 00 00 00 00 00 F8 3F | 1.5 |

| Exact fixture | Visible slots (zero-based) | Terminal slot 8 |
| --- | --- | --- |
| text_slotstyle_a8_baseline.txt | 0..7: B | B |
| text_slotstyle_a8_char4_spacing50.txt | target 3: L; non-target 0..2,4..7: B | B |
| text_slotstyle_a8_char4_spacing150.txt | target 3: H; non-target 0..2,4..7: B | B |
| text_slotstyle_a8_char6_spacing150.txt | target 5: H; non-target 0..4,6..7: B | B |
| text_slotstyle_a8_all_spacing150.txt | 0..7: H | H |

All strong-support criteria pass: baseline values are 1.0, low target is 0.5,
high targets are 1.5, char4 and char6 carry identical eight-byte H at different
ordinals, single-character non-targets remain B, and all eight visible slots
replicate H. `spacing_ratio_f64_candidate` has
`diagnostic_storage_candidate=f64le`, `confidence=strong_style_field_candidate`.
`typed_width=null` remains formally unresolved. No production typed decoding,
style output, confirmed-field promotion or ownership assignment is authorized.

Terminal baseline is B/1.0; all single-character captures preserve it;
all-spacing150 terminal is H/1.5, identical to every visible slot. Conclusion:
`terminal_spacing_state_propagation_observed`. Whether this copies final/current
paragraph style remains semantic speculation. No real-character, formatting
ownership or character-8 membership conclusion follows.

The tested window is disjoint from F4-required +00..03, +08, +09..0B,
+24..2B and +38..3F. All required bytes remain unchanged and all five runtime
candidates remain present with active source CParagraphe_slot_prefix_family_v2.
Spacing can vary without abstention in this cohort, supporting separation of
framing identity from the spacing style candidate. F4 is unchanged.

Earlier +40..46 variability with +47 stable 3F is compatible with a multi-byte
numeric field whose high byte remains stable across these ratios. The current
controls vary only +46; they do not independently demonstrate variability of
every earlier byte. This is interpretation of frozen evidence, never a selector.
Baseline natural length 74.584 mm is not a binary selector.
Runtime unchanged; parser_safe=false; ownership unresolved; typed width
unresolved; runtime_change_readiness=not_authorized_in_this_task.
Maximum-length fixtures remain **captured / analysis pending**.

Follow-up validation: targeted spacing suite **30 passed** (previous 19 retained,
11 follow-up cases added); full `PYTHONPATH=src pytest -q`: **1099 passed**.
Ruff and `git diff --check` pass. Runtime source hashes and all five fixture
hashes remain unchanged; runtime/fixture/F4 RFC diffs are empty.
Opt-in output: JSON **85,104 bytes**, text **33,098 bytes** (UTF-8 with final LF).
Raw windows and f64 reads have structural freeze SHA-256
`cc40310b2cece13a168cc37f494f684bb92e210c02203201cf8fd253850572e2`.
Tests cover exact window-only access, preserved raw mismatching numeric reads,
pre-oracle freeze, oracle-disabled equality, adversarial targets/percentages,
renamed inputs, terminal separation, unchanged runtime/hashes and CLI bounds.

## Maximum-length differential results (2026-09-10)

Maximum-length status: **analysis complete / provisional findings**. This section
supersedes only the earlier maximum-length "captured / analysis pending" status.
Character-spacing findings, including the fixed +40..47 f64 ratio follow-up,
remain unchanged historical evidence. No runtime or semantic-model changes are
authorized.

New standalone analyzer: `tools/analyze_text_maximum_length.py`;
new integration suite: `tests/integration/test_text_maximum_length_cli.py`.
Run with `--json`, `--no-oracle`, or `--details`. `--fixtures` accepts exactly
five paths in reference-first order; neutral f0..f4 identifiers are input-order
labels only. All ten unordered pairs are structurally compared, covering all
seven required comparisons without using length labels to choose comparisons.
Every node payload and header is compared before paragraph region breakdown.
All ranges below are half-open and node-payload-relative unless specified.

| ID | Exact fixture | Runtime result | Independent alignment |
| --- | --- | --- | --- |
| f0 | text_slotstyle_a8_baseline.txt | candidate present | 9 slots, first prefix 310 |
| f1 | text_maxlength_a8_100mm.txt | candidate present | 9 slots, first prefix 310 |
| f2 | text_maxlength_a8_60mm.txt | candidate present | 9 slots, first prefix 310 |
| f3 | text_maxlength_a8_40mm.txt | candidate present | 9 slots, first prefix 310 |
| f4 | text_maxlength_a8_m60mm.txt | candidate present | 9 slots, first prefix 310 |

All five parse successfully. Source=CParagraphe_slot_prefix_family_v2,
prefix_family=F4, plus08_value=0, slot_count=9, first_prefix=310. Runtime is
observed before independent research alignment; current F4 positivity is not a
prerequisite. Node sequence is CZone, CParagraphe, CCourbe, CContour,
CPropertyExtend with payload sizes 98, 2530, 98, 170, 5006 respectively.
Complete periodic windows occupy CParagraphe [310,2146), with suffix
[2146,2530). No slot byte changes in any pair, including terminal slot 8.

### Requested-setting candidate

A cohort-wide exact eight-byte changed range independently nominates
CParagraphe **[262,270), +0x106..+0x10D**. It is upstream of the slot run,
not a prefix-relative field. Post-freeze diagnostic values are:

| Capture | Exact bytes at [262,270) | f64le |
| --- | --- | ---: |
| baseline | 00 00 00 00 00 00 00 00 | 0.0 |
| +100 | 9A 99 99 99 99 99 B9 3F | 0.100 |
| +60 | B8 1E 85 EB 51 B8 AE 3F | 0.060 |
| +40 | 7B 14 AE 47 E1 7A A4 3F | 0.040 |
| -60 | B8 1E 85 EB 51 B8 AE BF | -0.060 |

This is the unique nominated window matching all five requested lengths in
meters, an **object_setting_candidate** / **strong_object_setting_candidate**.
The millimeter hypothesis does not match. Typed width and ownership remain
unresolved, and no production maximum-length field is added.

Numeric nomination uses only isolated 7/8-byte cohort-union payload deltas.
An exact 8-byte range is tested directly; a 7-byte range may include exactly
one following cohort-stable byte as an explicit untyped f64 hypothesis.
No alternative offsets, overlapping alignments, arbitrary blob subdivision or
value-based nomination is allowed. Fifteen raw windows are frozen; f64 reads
and UI matching occur afterward. No f32/integer hypotheses are promoted.
The raw range and nominated-window lists remain identical without oracle.

### Seven complementary comparisons

| Pair | Upstream changed bytes | Suffix changed bytes | Complete slot changed bytes | Main evidence |
| --- | ---: | ---: | ---: | --- |
| baseline vs +100 | 63 | 82 | 0 | requested setting, layout/bbox changes; no operator-observed compression |
| baseline vs +60 | 57 | 118 | 0 | setting and decreasing duplicated scalar candidates |
| baseline vs +40 | 57 | 120 | 0 | further decrease of the same scalar candidates |
| baseline vs -60 | 71 | 244 | 0 | signed setting plus additional geometry/suffix changes |
| +100 vs +60 | 58 | 118 | 0 | duplicated scalar decreases, +298 layout candidate returns to baseline |
| +60 vs +40 | 50 | 116 | 0 | scalar decreases further; simple natural-length ratio does not match |
| +60 vs -60 | 30 | 232 | 0 | requested-setting sign change; duplicated scalar remains identical |

The JSON retains every contiguous changed range in every complete node payload,
node header and outside-node gap. CZone payload stays unchanged; its header/bbox
changes. CCourbe/CContour payloads and headers, CPropertyExtend payload, and
CParagraphe upstream/suffix all have secondary changes. CParagraphe node header
remains unchanged. Opaque 16-byte changes (for example paragraph [76,92),
CCourbe/CContour [28,44), CPropertyExtend [214,230)) are not assigned semantics.
Range-category defaults are unresolved; bounded candidate/negative-only maps
assign categories only within their supported boundaries.

### Compression and layout candidates, with a model gap

The discovered 7-byte deltas [214,221) and [286,293), each followed by a stable
high byte, nominate **[214,222)** and **[286,294)** as diagnostic f64 containers.
They have identical full raw profiles across all five inputs:

| Capture | f64 diagnostic at both windows |
| --- | ---: |
| baseline | 0.9989999999999998 |
| +100 | 1.0 |
| +60 | 0.8034631424913115 |
| +40 | 0.5353087616608744 |
| -60 | 0.8034631424913115 |

These are **compression_correlated_candidate** windows, not confirmed scale
fields. +60 and +40 move in the expected direction, but requested/74.584 gives
0.8044620830204869 and 0.5363080553469913. Residuals are
-0.000998940529175485 and -0.0009992936861169532. Neither matches the narrow
simple-ratio hypothesis; baseline also differs from 1.0. No exact compression
formula is established. The rounded UI natural length is never searched in raw
bytes or used to choose a window. The report also retains inverse-ratio values.

Another nominated upstream window **[298,306)** is
0.000037291950886766956 in baseline/+60/+40/-60, but 0.01270804911323329 in
+100. It is a +100-only layout-correlated observation; semantics remain
unresolved. Compression-related metadata already changes in baseline vs +100
(0.999 -> 1.0), so those regions are not described as exclusively activated
only for compressed captures.

Every visible and terminal slot retains the height, width, slant, auxiliary,
spacing, rotation and RGB candidates. In particular prefix +14..1B stays f64
1.0 and +40..47 stays f64 1.0 across all 45 slots. Operator-observed compression
therefore does not reuse/change the existing character Width candidate in this
cohort; its serialized state is separate from the changing object/layout
metadata. This does not establish an ownership or complete compression model.

### +60 / -60 symmetry and geometry

The dedicated symmetry report separates common baseline-changed positions,
identical range boundaries, negative-only positions, direct +60/-60 changes,
and magnitude-identical / sign-only nominated numeric windows.
At [262,270), only byte **269 (+0x10D)** changes **3F -> BF** between +60/-60;
f64 magnitude stays 0.060. This is a **sign_correlated_candidate**, not an
independent mirror flag. The two compression candidates and [298,306) remain
byte-identical. Upstream direct differences are [8,15), [32,39), [76,83),
[84,92), [269,270). Additional negative-only positions occur in the suffix,
including [2162,2169), [2186,2193), and many later short ranges. These are
negative_length_correlated_candidate / meaning_unresolved observations.
No transform matrix, Y-flip implementation or terminal formatting ownership is
inferred.

| Capture | Parsed CZone X extent mm | CZone xmin / xmax mm | CZone ymin / ymax mm |
| --- | ---: | --- | --- |
| baseline | 74.5839017735334 | 31.123 / 105.7069017735334 | 72.234 / 82.234 |
| +100 | 100 | 18.415 / 118.415 | 72.234 / 82.234 |
| +60 | 60 | 38.415 / 98.415 | 72.234 / 82.234 |
| +40 | 40 | 48.415 / 88.415 | 72.234 / 82.234 |
| -60 | 60 | 38.415 / 98.415 | 62.234 / 72.234 |

Requested values are oracle inputs; extents above are independently parsed
serialized bboxes, not rendered glyph measurements. CCourbe/CContour X extents
follow the same values and their Y bounds remain at 72.234 mm, including -60.
CZone's negative capture has a changed Y interval with the same 10 mm extent.
CParagraphe/CPropertyExtend have no parsed bbox in the existing node model.
The report does not equate CZone width with glyph width or claim the parser
measures the rendered compression/reflection. Baseline parsed X extent differs
slightly from rounded UI 74.584 mm; that difference is preserved.

All required F4 regions (+00..03, +08, +09..0B, +24..2B, +38..3F) remain
unchanged in all 45 slots. +24 and +38 independently receive
**not_falsified_by_current_maxlength_controls**, never confirmed constants.
No F4 style contamination or abstention is observed.
Runtime remains family v2/F4, accepted_candidate_only, exact identity, Policy A,
Gate 8 rejection-only veto; matched_chain=null; parser_safe=false;
ownership and typed widths unresolved. runtime_f4_review_readiness=
no_maxlength_falsification_trigger; runtime_change_readiness=
not_authorized_in_this_task. Compression-model readiness and negative-length
reflection-model readiness remain unresolved beyond the provisional candidates.

### Validation and preserved inputs

Targeted maximum-length suite: **35 passed**. Full
`PYTHONPATH=src pytest -q`: **1134 passed** (1099 baseline + 35 new).
Ruff passes both new Python files. `git diff --check` passes;
`git diff -- src/type3_clipboard_codec` is empty. Existing spacing/style analyzer
hashes are pinned in tests and unchanged. No fixture, model or runtime file is
modified. Oracle tests include wrong natural length, wrong requested values,
wrong relationship classification, changed/removed reflection wording, injected
target-character metadata, renamed filenames and disabled oracle. All retain
identical raw structural results and numeric nominations. Structural SHA-256:
`3f9b87b91dd58688de8a73ef461d279c1ac21f4b058e817238c719a13408437b`.

Raw fixture file SHA-256 values, preserved from the initial observation:

| ID | SHA-256 |
| --- | --- |
| f0 | 994c115e0dab58c605747420e7ba1e67961835ed4ef17aae0951bf899a406392 |
| f1 | 1f24a7b2042dca993977690fa295aa7295593572103cb04523cc06ac1bd89046 |
| f2 | b8281f358591493b1dadf609c18ab788d8d73c1ae5f222045dbdb3a9033b25b6 |
| f3 | 44b998a2e69cd08618936da6a5250a11bf223b7d0f89f3aef3deb1bb9ab6d49a |
| f4 | e9bb3439205bab970b73b1b6fc70d2814d77e0d088cb577ed6d37802b4d27d85 |

Measured UTF-8 output including final LF: default JSON **95,721 bytes**,
text **46,452 bytes**; details JSON **97,523 bytes**, details text **47,658 bytes**.
Details add at most four eight-byte changed fragments per region for the first
comparison only. No full payload dumps. Parsed geometry is not normalized away.

In the dedicated +60/-60 comparison, CZone has 14 header-changed bytes and a
changed bbox but zero payload changes; CCourbe/CContour bboxes and headers are
unchanged despite payload changes (16/33 bytes), and CPropertyExtend has 16
payload-changed bytes. CParagraphe has 30 upstream + 232 suffix changed bytes,
zero slot/header changes. This explicitly separates geometry-only node evidence
from opaque metadata and signed-setting evidence; a rendering transform model
remains unresolved.
