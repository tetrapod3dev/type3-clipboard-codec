# CParagraphe Controlled Per-Slot Style Field Investigation

## Independent v1/F4 shadow status (2026-09-08)

[Gate 3/4 shadow evidence and limitations](text_slot_prefix_family_v2_rfc.md#independent-v1f4-shadow-status-2026-09-08)
now cover 104 real fixtures and 32 synthetic controls. Actual runtime v1: 62
candidates; F4 shadow: 72; identical runs: 62; structurally explained disagreements:
10 gains; losses, different-run disagreements and real ambiguities: zero.
All 72 known decoys and six general negatives remain rejected. Clone, +08,
constant, bounds, resource, oracle-isolation and runtime regression checks pass.
Both disagreement closeout and v2 promotion-review readiness are ready_for_review.
This does **not** authorize runtime v2 implementation/replacement. The RFC remains
Draft redesign RFC; runtime v1 is unchanged, no public v2 candidate or fallback
is emitted, parser_safe=false, and ownership/style/typed widths remain unresolved.
Historical evidence and authorization scopes below are preserved.


## Prefix Family v2 RFC status (2026-09-07)

The [Prefix Family v2 Redesign RFC](text_slot_prefix_family_v2_rfc.md) is a
**Draft redesign RFC**, freezing F4 evidence, identity-collision limitations,
Policy A, fail-closed behavior, output compatibility and eight promotion gates.
Current family v1 (source `CParagraphe_slot_prefix_family_v1`, with legacy exact
variants v0/v1/v2) remains the implemented candidate-only runtime. Proposed family
v2/F4 is a research redesign only: **runtime implementation/replacement not authorized**.
The draft recommends a separately reviewed independent v1/v2 shadow study, not
automatic fallback or two public candidates. Both wider F4 regions are termed
`structural_constant_candidate`; no padding or semantic meaning is promoted.

**The v0/v1/v2 runtime family is retained for safety while redesign evidence is reviewed.**
Historical analysis and review conclusions below remain unchanged. This status
update adds no runtime, analyzer, fixture or test behavior.


Date: 2026-09-07. Status: analyzer-only controlled differential research.
The proposed Phase 1G addition of unknown prefix variants v3/v4/v5 is **abandoned**.
No runtime parser, exact v0/v1/v2 family, model, anchor behavior or fixture bytes
were changed. `parser_safe=false`; typed widths and ownership remain unresolved.
This is not production style decoding support.

## Capture matrix and intent

All nine supplied captures exist. Files below are under `tests/samples/text/`;
each has matching machine-readable YAML in `tests/samples/intents/text/`.
Each raw capture is 8,192 bytes. The metadata records user-provided capture intent,
not a claim that every serialized byte outside the intended field is constant.

Shared controls: visible text `AAAAAAAA`, Arial, eight characters, height 10 mm,
width 100%, slant 0°, rotation 0°, Army Green; all other character properties held
constant. Only the fourth A (human index 4, zero-based ordinal 3) was intended to
change. The changed property was reset to its baseline after every capture.
Alignment: center-bottom. Provided lower-left: `[31.123, 72.234, 1.234]` mm;
provided anchor: `[68.415, 72.234]` mm, at the text's horizontal center/bottom.
These are capture controls, not decoded anchor/ownership assertions.

> Z=1.234 mm was intentionally used as a diagnostic control to avoid zero-heavy coordinate byte patterns. No Z semantic decoding change is implied.

| Exact fixture filename | Changed property | Base → capture | Runtime candidate | Changed slot indices (1-based) |
| --- | --- | --- | --- | --- |
| text_slotstyle_a8_baseline.txt | None | Baseline | Present | None |
| text_slotstyle_a8_char4_height20.txt | Height | 10 → 20 mm | Absent: safe abstention | 4 |
| text_slotstyle_a8_char4_width50.txt | Width | 100 → 50% | Absent: safe abstention | 4, 6 |
| text_slotstyle_a8_char4_width150.txt | Width | 100 → 150% | Absent: safe abstention | 4 |
| text_slotstyle_a8_char4_slant_p15.txt | Slant | 0 → +15° | Absent: safe abstention | 2, 4 |
| text_slotstyle_a8_char4_slant_m15.txt | Slant | 0 → −15° | Absent: safe abstention | 4, 8 |
| text_slotstyle_a8_char4_rotation_p15.txt | Rotation | 0 → +15° | Present | 4, 9 (terminal) |
| text_slotstyle_a8_char4_rotation_m15.txt | Rotation | 0 → −15° | Present | 3, 4 |
| text_slotstyle_a8_char4_navy.txt | Color | Army Green → Navy Blue | Present | 4 |

Every capture parses successfully. Existing source-text candidate is `AAAAAAAA`;
the separate display-text candidate remains null (including the chain display
candidate). The analyzer does not fabricate a visible-text value. Every present
runtime slot candidate has nine slots, variant v0 and diagnostic code views
`[65,65,65,65,65,65,65,65,0]`. Absent candidates were not made to appear.

## Structural method and oracle boundary

[Standalone analyzer](../tools/analyze_text_slot_style_fields.py) first scans the
complete structurally identified CParagraphe payload. It enumerates every maximal
204-byte token recurrence, then investigates complete local windows, unanimous
u8/u16/u32 count views, and a zero-code terminal. It requires exactly one eligible
analyzer alignment globally. This is a research count/context alignment method;
it is **not** the runtime exact-family acceptance rule or a proposal to change
runtime Policy A. Count is allowed as analyzer evidence, not runtime disambiguation.

All nine payloads are 2,530 bytes. Each has two raw periodic sequences: observed
origins 310 and 402, both length nine. The first has count views 9 and a zero-code
terminal; the second's u32 view is 1,072,693,248 and its code window is nonzero.
The selected run has nine complete 204-byte inventory windows, ending at 2,146,
with sufficient following probe context. These measured origins are output only;
no constant 310/402, historical search window or fixture-specific shift selects them.
No run relocation or count change is observed. All code/prefix windows align with
the baseline independently of expected text, style, color or intended target index.

The complete 204-byte period is used for a bounded byte inventory, not asserted
as semantic record extent. Exact contiguous byte-delta ranges are discovered over
all 204 bytes, including changes outside +0x00..+0x5F. Integer/f32/f64 diagnostic
windows are limited to 4-byte-grid windows intersecting those discovered ranges;
there is no all-offset/type/value oracle brute force. Eight-byte probes may begin
at either half of eight-byte alignment. Their width is not a confirmed field width.

Phase A freezes its complete result as JSON before Phase B can read any intent.
Phase B receives only this immutable JSON, never the raw buffers or a discovery
callback. It compares generic numeric probes with supplied values and indices.
`--no-oracle`, deliberately wrong style values/properties/target indices, and
renamed input files preserve structural output and field candidate ranking.
Shared capture controls and semantic correlations are oracle output, so they are
unresolved/empty in no-oracle mode. Runtime parse observations do not select runs.

## Provisional field map and numeric hypotheses

Ranges in this table are inclusive. Machine JSON ranges are half-open.
All semantic names below are diagnostic candidates with null typed widths.

| Relative range | Independent structural observation | Diagnostic semantic candidate | Status |
| --- | --- | --- | --- |
| +0x04..+0x07 | Code windows identical in all comparisons; final zero | slot_code_candidate; no production text replacement | unresolved typed width |
| +0x0C..+0x13 | Only +0x12 changes in target for height20 | f64le height in meters | strong_style_field_candidate |
| +0x14..+0x1B | Only +0x1A changes in target for both widths | f64le width ratio | strong_style_field_candidate |
| +0x1C..+0x23 | Eight changed bytes, target slot, paired signs | slant_correlated_field_candidate, f64le radians | strong_style_field_candidate |
| +0x2D..+0x2F | Three changed bytes at different slots across six captures | No semantic assignment; +0x2C four-byte probe is diagnostic only | unresolved |
| +0x48..+0x4F | Eight changed bytes, target slot, paired signs | rotation_correlated_field_candidate, f64le radians | strong_style_field_candidate |
| +0x50..+0x52 | Three changed bytes only in target for Navy | rgb_bytes_candidate | strong_style_field_candidate |

Height: raw `7b14ae47e17a843f` → `7b14ae47e17a943f`, f64le 0.01 → 0.02.
All other seven visible slots retain 0.01. The terminal's height probe is stable,
characterized separately in JSON `field_profiles`. This supports meters as the
height interpretation without confirming a production storage type.

Width: raw `000000000000f03f` (1.0) → `000000000000e03f` (0.5) or
`000000000000f83f` (1.5). The other seven visible slots retain 1.0; the terminal
probe is also stable. Width150 also has the unexplained auxiliary change in its
target slot, which is not silently absorbed into the width field.

Slant and rotation: zero baseline → `65732d3852c1d03f` (+0.2617993877991494) or
`65732d3852c1d0bf` (−0.2617993877991494). These match ±15° in radians, with exact
paired sign behavior. Direct degree, f32 degree/radian and signed-integer probes
at the independently discovered windows do not match the intended values. The
JSON retains nonmatching generic probes as well as matching interpretations.
Four bytes immediately before and after each selected eight-byte candidate remain
stable. The slant and rotation candidates are disjoint and not adjacent; their
order was discovered rather than assumed. Both also have secondary changes.

Color positive control: `98 CC 98` → `30 60 CC` at +0x50..+0x52, exclusively in
slot ordinal 3. Other seven visible slot windows and the terminal window are
unchanged. `color_control_alignment_status=strong_style_field_candidate`.
This validates the alignment as a control after discovery; palette expectations
never select a run or slot and no object-color ownership follows from it.

## Secondary slot changes and capture-quality qualification

At the auxiliary +0x2D..+0x2F range, bytes `00 00 00` become `10 A7 EF`.
The encompassing four-byte diagnostic probe at +0x2C changes from `00000000` to
`0010a7ef`. Locations (human indices) are width50: 6; width150: 4;
slant +15: 2; slant −15: 8; rotation +15: 9 (terminal); rotation −15: 3.
Neither these bytes nor their slot locations have an established semantic meaning.
A capture-state/pointer/derived-data interpretation would be speculation and is
not used to suppress them, rank candidates or claim all non-target slots stable.

At the selected primary style candidate region, all non-target visible slots and
terminal are stable. Across the **entire** 204-byte windows, only height20, Navy,
and width150 have a sole changed target slot. Five controls change a non-target
window too. Rotation +15 changes terminal auxiliary bytes although the terminal
code and primary style probes stay stable. No control changes every slot.
Thus the user-provided one-character experimental design is documented, but
strict byte-level isolation is qualified by unexplained secondary differences.
`fixture_control_quality=documented_controls_with_unexplained_secondary_changes`.
These exceptions must be preserved in future investigations.

## Header, geometry and outside-run differences

Counts below inventory changed bytes, not semantic fields. Upstream/suffix ranges
use independent payload-relative regions; outside-payload ranges are raw input
provenance. The analyzer records the exact contiguous ranges and region lengths.
No coordinate equality is used for alignment or ownership.

| Capture | Payload upstream | Payload suffix after windows | Outside CParagraphe payload |
| --- | ---: | ---: | ---: |
| baseline | 0 | 0 | 0 |
| height20 | 70 | 141 | 117 |
| width50 | 48 | 124 | 109 |
| width150 | 47 | 121 | 104 |
| slant +15 | 31 | 54 | 93 |
| slant −15 | 31 | 54 | 93 |
| rotation +15 | 37 | 72 | 100 |
| rotation −15 | 37 | 72 | 97 |
| Navy | 16 | 0 | 54 |

Payload +76..+91 changes even in Navy; its role is unresolved. CZone/CCourbe/
CContour bbox values change in the geometric style controls but not Navy.
CCourbe, CContour and CPropertyExtend payload bytes also change. These are
secondary/global layout-or-capture-state observations, not proof that each changed
byte is derived geometry. No new anchor location, anchor ownership, baseline_midpoint
rule, fallback rule or Z interpretation is inferred. Anchor closeout, MFC
conclusions and color-ownership readiness remain unchanged.

## Runtime prefix-family implications

The former v0/v1 height-region bytes diagnostically read as 0.01/0.03. The new
controlled 0.02 delta strongly supports the interpretation that this part of the
old variant vector contains a style value rather than only framing identity.
The width 1.0 bytes and low slant bytes were also required prefix invariants.
Their controlled changes explain why the current exact family is over-constrained
for these style captures. Rotation and RGB lie outside that 32-byte predicate;
the corresponding captures retain their candidates.

This does **not** explain v2's +0x08 flag: its meaning remains unresolved. It is
incorrect to claim all v0/v1/v2 differences are decoded. A future review should
consider separating style-field evidence from framing, including whether masking
validated style regions is safe and how uniqueness/unknown-continuation rules
would work. This task neither proposes an approved mask nor adds v3/v4/v5.

- runtime_prefix_family_review_readiness: `ready_for_review`
- candidate_parser_change_readiness: `not_ready`
- slot_style_struct_readiness: `not_ready`
- color_ownership_readiness: `not_ready`
- parser_safe: `false`; all typed widths and ownership: unresolved

## Reproduction, bounds and validation

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe tools/analyze_text_slot_style_fields.py --json
.venv/Scripts/python.exe tools/analyze_text_slot_style_fields.py --json --no-oracle
.venv/Scripts/python.exe tools/analyze_text_slot_style_fields.py --details
.venv/Scripts/python.exe -m pytest tests/integration/test_text_slot_style_fields_cli.py -q
.venv/Scripts/python.exe -m pytest -q
```

`--fixtures` accepts explicitly selected paths and `--baseline` a reference label;
neither supplies semantic interpretation. Missing controls produce warnings and
available captures continue. Unresolved alignment never forces a slot comparison.
Limits: nine fixtures; 8 MiB hex text/file; 1 MiB aggregate CParagraphe bytes/file;
128 nodes, 32 paragraphs, 4,096 prefix hits/payload, 256 slots/run; 256 changed
ranges/comparison; 64 changed-range probe windows/slot. Details retain at most four
representative changed slots per capture and at most 16 bytes per hex fragment.
Output-budget failure emits no partial report. No full payload/slot dumps occur.

Measured UTF-8 output sizes including final newline: default JSON **81,803 bytes**,
details JSON **83,329 bytes**, default text **11,027 bytes**, details text
**12,553 bytes**. Both modes stay below the 100 KB / 50 KB limits.

New tests: **43 passed**. Full suite: **632 passed** (580 prior baseline + nine
new fixture cases automatically included by the existing parser regression test +
43 new analyzer tests). Ruff passes for both new Python files. The nine exact
whole-parser-result snapshots (including every candidate, raw byte, note/warning,
anchor, geometry, style and chain order) match the pre-analysis runtime baseline.
Source hashes cover the candidate extractor, chain parser, text pipeline and
CParagraphe semantic parser; runtime sources and raw captures remain unchanged.
Snapshot evidence: `tests/samples/reports/text/text_slot_style_runtime_baseline.json`.

The report is reproducible without an external service. No new fixture was
captured, no raw fixture was rewritten and no runtime candidate expectation was
relaxed to make unsupported styles pass.

## Prefix family redesign analysis (2026-09-07)

**The v0/v1/v2 runtime family is retained for safety while redesign evidence is reviewed.**

[New standalone analyzer](../tools/analyze_text_slot_prefix_redesign.py) evaluates
F0–F4 without changing this investigation's analyzer, its output, the runtime
extractor, models, ownership, anchors or raw fixtures. No v3/v4/v5 are introduced.
Result: `runtime_prefix_redesign_readiness=ready_for_rfc_review` for F4 on this
bounded corpus. This is analysis readiness only, not runtime authorization or
production support. `parser_safe=false`; typed widths and ownership unresolved.

### Corpus and reference evidence

The full selected corpus has 104 captured inputs: all 72 text fixtures and 32
geometry fixtures. Text includes nine controlled style captures, the previous
24-run / 207-slot Phase 1F corpus, five formerly unsupported mirror/slant/width
controls, and 34 other text captures. Multiline (4) and multi-object (7) are
subsets of the previous 24, not additional independent runs. All 72 text inputs
have one count/terminal-nominated reference run, totaling 592 slots, plus one
same-length raw +92 competitor, also totaling 592 slots. There are 1,184 raw token
hits and 144 raw recurring runs. No captured CParagraphe without a research-supported
reference was found. The 32 geometry negatives have zero eligible CParagraphe
payloads: zero matches is a scope check, not strong in-domain discrimination evidence.

Reference nomination uses complete bounded windows, independent raw token
recurrence, unanimous count views and terminal evidence. These research reference
labels are not ownership or ground truth semantics. **Every hypothesis scans all
eligible payload token positions independently**, before count/terminal validation.
Neither reference nomination nor +92 competitor identification filters hypothesis
hits. Prefix matches, suffix-deduplicated runs and ambiguity remain visible even
when count/terminal fails. No expected style, text, color, target index, numeric
encoding or filename meaning selects a prefix.

Nine synthetic challenges are generated in memory from a seed selected by raw
structural evidence and digest, without fixture labels. Six are general negatives:
zero filler, nonzero filler, known-decoy replay, decoy with +08..+0B repaired,
decoy with both that core and +24..+2B padding repaired, and unknown +08=02.
Two additional negative identity clones retain a matching prefix but corrupt
count or terminal. A ninth challenge contains two complete identity clones in
distinct payloads, explicitly testing global ambiguity.

### Variability map and wider structural candidates

JSON inventories every byte at prefix-relative −0x10..+0x5F: unique raw values,
within-run constancy, cross-fixture constancy, terminal/nonterminal value classes,
and variation within equal raw code classes. Phase B adds controlled-style,
multiline, multi-object and unsupported-style cohort maps. Rows are summarized
per position; full slot rows are not dumped.

The observed height, width and slant regions overlap old identity constraints.
Rotation +48..+4F and RGB +50..+52 are inventoried but remain outside the old
32-byte predicate. In the broader corpus, variability extends to **+2C**, not
only the formerly highlighted +2D..+2F; +30..+37 and +40..+46 also vary. These
observations are preserved without giving the auxiliary bytes semantic names.

| Wider area (inclusive) | Real-slot evidence | Known decoy evidence | Candidate interpretation |
| --- | --- | --- | --- |
| +24..+2B | Eight zero bytes in all 592 slots | +24 is 04; remaining bytes zero | padding_candidate; full range is F4 evidence |
| +2C..+2F | Variable, including +2C | +2C is 04, others zero | Unresolved; not required by F4 |
| +30..+37 | Variable | Zero | Not a framing constant |
| +38..+3F | `9A 99 99 99 99 99 D9 BF` in all 592 slots | Eight zero bytes | unknown_stable_field; no decoded semantics used |
| +40..+46 | Variable | Zero | Not required by F4 |
| +47 | Stable 3F | Zero | Additional constant candidate, not selected for F4 |

No byte is established as *genuinely structural* in all future formats. In
particular, the new +38 constant might still represent an unperturbed field.
Its value is not numerically decoded or treated as a confirmed storage type.
F4 is a declared few-range hypothesis, not an automatically learned mask that
keeps every constant or discards every variable in this corpus.

### Explicit predicate hypotheses

All predicates exclude code candidate +04..+07. Byte ranges below are inclusive;
JSON exclusions and local windows use half-open coordinates. No numeric style
value is tested during prefix matching.

| Hypothesis | Identity rule | Required local bytes |
| --- | --- | ---: |
| F0 | Existing exact v0/v1/v2 joint family | 32 |
| F1 | Project F0 joint vectors excluding +0C..+13 | 32 |
| F2 | Project F0 joint vectors excluding +0C..+1B | 32 |
| F3 | Project F0 excluding +0C..+23; retain token and +08..+0B core | 12 |
| F4 | F3 core plus fixed +24..+2B and +38..+3F ranges | 64 |

F1/F2/F3 retain projections of exact allowed joint vectors, not independently
wildcarded components. F4 explicitly requires:

- +00..+03 = `05 00 00 00`.
- +08 is exactly `00` or `01`; every other value fails. This is a bounded raw
  class policy, not an unrestricted wildcard or assigned semantic flag.
- +09..+0B = `00 00 00`.
- +24..+2B = eight zero bytes.
- +38..+3F = `9A 99 99 99 99 99 D9 BF`.
- Complete bounds through +3F. Code, style region +0C..+23, auxiliary +2C..+37,
  rotation/RGB and other unrequired bytes do not participate.

There are 24 required byte positions over a 64-byte local span. These are
identity bounds only; recurrence, count, terminal and global ambiguity are
separate evidence layers. The analyzer's declaration is not a new runtime mask.

### Recall and known-decoy discrimination

The following numerators are complete reference-run matches before count is
used to reject any hypothesis run. F4 also has a unique maximal run in every
positive fixture; the old-family ambiguities are not resolved using count.

| Corpus | Runs | F0 | F1 | F2 | F3 | F4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All text | 72 | 62 | 63 | 68 | 72 | 72 |
| Controlled style | 9 | 4 | 5 | 7 | 9 | 9 |
| Previous Phase 1F | 24 | 24 | 24 | 24 | 24 | 24 |
| Multiline subset | 4 | 4 | 4 | 4 | 4 | 4 |
| Multi-object subset | 7 | 7 | 7 | 7 | 7 | 7 |
| Previously unsupported styles | 5 | 0 | 0 | 3 | 5 | 5 |

Height exclusion recovers the controlled height20 slot. Width exclusion recovers
the two controlled widths and old mirror/width50/width150 captures. Slant exclusion
recovers both controlled slants and both old slant controls. All nine controlled
captures therefore share F3/F4 framing without their style values entering the
predicate. F4 is preferred over F3 because synthetic discrimination differs.

All five hypotheses reject **all 592 known decoy slots / all 72 decoy runs**:
known-decoy false-positive rate 0/72. Known decoy +08..+0B is `4D 62 40 3F`,
already incompatible with the retained F3 core. F4 has additional independent
mismatches at +24 and +38..+3F. Thus known-decoy rejection alone is insufficient
reason to accept F3: it is easier to satisfy than the wider candidate.

### Synthetic false positives and layer contributions

| Hypothesis | General negative identity matches | Including the two identity-clone negatives | Captured-input ambiguity |
| --- | ---: | ---: | ---: |
| F0 | 0/6 | 2/8 (25%) | 5 |
| F1 | 0/6 | 2/8 (25%) | 4 |
| F2 | 1/6 | 3/8 (37.5%) | 2 |
| F3 | 3/6 | 5/8 (62.5%) | 0 |
| F4 | 0/6 | 2/8 (25%) | 0 |

These are deliberately adversarial test-case rates, not estimates of production
prevalence. Identity-clone failures are not removed from the total denominator.
F4 does not materially increase these measured negatives over F0, but it does
not eliminate collisions with copied identity bytes. The two-full-clone challenge
produces two matches under every hypothesis and remains ambiguous even though
both count and terminal validate.

The zero-filled periodic synthetic is especially diagnostic: F2 and F3 pass
prefix, recurrence, count **and** terminal. Count cannot rescue a weak predicate.
F4 rejects it at identity because it lacks the nonzero wider constant. Repaired
known decoys likewise expose F3's weakness; F4 rejects them before count checks.

| Layer quantity, captured corpus | F0 | F1 | F2 | F3 | F4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prefix slot matches | 547 | 548 | 574 | 592 | 592 |
| Maximal accepted runs (suffixes deduplicated) | 72 | 71 | 72 | 72 | 72 |
| Runs with ≥2 accepted prefixes at stride 204 | 72 | 71 | 72 | 72 | 72 |
| Recurring runs passing count | 62 | 63 | 68 | 72 | 72 |
| Recurring runs passing terminal independently | 67 | 67 | 70 | 72 | 72 |
| Recurring runs passing both count and terminal | 62 | 63 | 68 | 72 | 72 |

The raw token layer initially has 144 recurring sequences. F4 removes the 72
competitors using identity; count and terminal add validation but no further
captured-corpus discrimination. In synthetic identity clones, count rejects the
wrong-count clone, terminal rejects the nonzero-terminal clone, and uniqueness
rejects the two-complete-run challenge. None of these filters erases the reported
prefix matches or competing-run counts. Runtime Policy A itself is unchanged.

### +08 and old variant reinterpretation

All 72 reference runs are homogeneous at +08. Exactly one fixture has 01:
`text_group_mixed_color_two_objects.txt`. The other 71, including all controlled
styles, other mixed-color/grouped/not-grouped captures, multiline and formerly
unsupported styles, have 00. Intent grouping and filename hints are loaded only
after structural freeze and are reported as diagnostics. This distribution does
not establish a group, color, object, style or ownership meaning. +08 remains an
unresolved raw class; F4 retains the explicit 00/01 enumeration and rejects 02,
4D and FF in tests.

The observed v0/v1 byte differences are wholly inside the height-correlated
region. In this corpus they are fully explainable by the previously diagnostic
0.01/0.03 height values and the new controlled 0.02 evidence; excluding that
region merges the identity vectors. The distinction is not needed for observed
framing. This is not proof of a universal typed height field or every possible
meaning of a serialized version. Old invariants also overlap width and slant.
Conclusion: `old_family_overconstrained_by_style_fields`. V2 remains a distinct
raw +08 class with **unresolved interpretation**, not a newly named semantic flag.

### Freeze, readiness, limitations and verification

The complete raw structural report, predicate hits, positional profiles and
synthetic results are serialized before `load_labels` can run. No-oracle output
retains identical structural results, rankings/definitions and layer totals.
Wrong labels/intents and renaming/reordering inputs do not change predicate
results. Label-dependent cohort metrics and readiness are unresolved without
oracle labels; the matcher does not need those labels to reproduce its decisions.
No existing analyzer output was modified.

Readiness is limited to **ready_for_rfc_review**, because F4 supports all controlled,
previous, multiline/multi-object and additional references, rejects known decoys,
retains bounded +08 handling, and does not increase measured negative identity
matches over F0. Geometry controls are scope-only and true unsupported captured
paragraphs are absent, so additional in-domain negatives and independently varied
wider fields would strengthen a future review. Identity-clone collisions and the
possible nonstructural meaning of wider constants must remain explicit RFC risks.
No runtime parser change, typed style promotion, chain mapping, anchor ownership,
Z behavior or MFC work is authorized by this result.

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe tools/analyze_text_slot_prefix_redesign.py --json
.venv/Scripts/python.exe tools/analyze_text_slot_prefix_redesign.py --json --no-oracle
.venv/Scripts/python.exe tools/analyze_text_slot_prefix_redesign.py --json --details
.venv/Scripts/python.exe -m pytest tests/integration/test_text_slot_prefix_redesign_cli.py -q
.venv/Scripts/python.exe -m pytest -q
```

The CLI also accepts explicit `--fixtures` paths. Limits: 128 inputs, 8 MiB hex
text/input, 1 MiB aggregate paragraph bytes/input, 32 paragraphs/input,
4,096 raw token hits/payload, 256 slots/run, 512 maximal runs/payload and 32,768
signature evaluations/input. Bounds/cap failures produce warnings and block
review readiness. Output-cap failure emits no partial report.

Measured UTF-8 sizes including final newline: **96,553 bytes** default JSON,
**97,700 bytes** details JSON; **8,118 bytes** text in either mode. JSON includes
column-described compact tables instead of full slot dumps. Details add at most
four fixture summaries. New targeted tests: **90 passed**. Full suite:
**722 passed** (632 baseline + 90 new). Ruff passes both new Python files.
Tests compare F0 with the actual runtime predicate at every captured token hit,
verify runtime source hashes and exact whole-result controlled snapshots, and
exercise styles, unknown +08, complete bounds, ambiguity, synthetic negatives,
oracle isolation and output caps. No runtime, fixture or previous-analyzer changes
are part of this task.
