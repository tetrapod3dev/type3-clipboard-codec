# CParagraphe Controlled Per-Slot Style Field Investigation

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
