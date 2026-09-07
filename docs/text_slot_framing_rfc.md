# CParagraphe Text-Slot Framing Candidate RFC

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


## Prefix redesign analysis update (2026-09-07)

**The v0/v1/v2 runtime family is retained for safety while redesign evidence is reviewed.**

The [prefix redesign analysis](text_slot_style_field_investigation.md#prefix-family-redesign-analysis-2026-09-07)
evaluates F0–F4 across 72 text fixtures / 592 reference slots, 72 known +92
competitor runs, 32 geometry scope controls and nine synthetic challenges.
Style exclusions increase recall from F0 62/72 to F3 72/72, but F3 admits three
of six general synthetic negatives. Its zero filler also passes count/terminal;
those layers cannot conceal weak prefix discrimination.

The proposed **F4 research predicate** adds zero bytes at +0x24..+0x2B and the
raw constant `9A 99 99 99 99 99 D9 BF` at +0x38..+0x3F to the retained token/
+0x08..+0x0B core. It supports all 72 references (including controlled 9,
previous 24, multiline 4, multi-object 7 and unsupported-style 5), rejects all
known decoys and all six general synthetic negatives. Exact identity clones
still match F0/F4: including those two negative cases gives 2/8 prefix false
positives for both. Competing complete clones remain ambiguous independently
of count. Geometry captures contain no eligible paragraphs and therefore test
scope, not in-domain discrimination.

The wider constants are candidates with no assigned semantics. Variability also
extends to +0x2C; it is not used as an invariant. Old v0/v1 differ only inside
the height-correlated region, while v2 +0x08 remains unresolved; F4 explicitly
allows only 00/01 and rejects other values. The result is
`runtime_prefix_redesign_readiness=ready_for_rfc_review`, **not runtime approval**.
Full details retain corpus limitations, identity collisions, separate evidence
layers and oracle-isolation tests. New tests: 90 passed; full suite: 722 passed;
Ruff passes both new Python files.

No runtime family/mask, candidate output, semantic model, typed widths, ownership,
chain mapping, anchors, Z behavior, MFC conclusion or previous analyzer output
changes are made or authorized. `parser_safe=false` and ownership unresolved.
Any future implementation requires its own RFC/promotion review; no v3/v4/v5
addition is proposed.


## Controlled per-slot style investigation (2026-09-07)

The [controlled style investigation](text_slot_style_field_investigation.md)
documents nine `text_slotstyle_a8_*` captures: Arial `AAAAAAAA`, fourth-character
single-property changes with reset between captures, center-bottom alignment,
lower-left `[31.123,72.234,1.234]` mm and anchor `[68.415,72.234]` mm.
Z=1.234 is only a diagnostic control against zero-heavy byte patterns.

Analyzer-only results support provisional f64le candidates at prefix +0x0C
(height in meters), +0x14 (width ratio), +0x1C (slant radians), and +0x48
(rotation radians). Navy isolates RGB at +0x50..+0x52 in the intended slot.
Several captures also change unexplained +0x2D..+0x2F bytes in other slots,
including a terminal window, plus upstream/layout bytes. Full-slot isolation is
therefore qualified; these exceptions are retained rather than normalized away.

The proposed Phase 1G v3/v4/v5 variant expansion is abandoned. Controlled style
changes show that parts of the current exact prefix family contain style values;
v2's +0x08 remains unexplained. `runtime_prefix_family_review_readiness` is
`ready_for_review`, but `candidate_parser_change_readiness` remains `not_ready`.
Runtime v0/v1/v2, Policy A and safe abstention are unchanged. No semantic model,
anchor/baseline_midpoint/Z behavior, MFC conclusion or color-ownership readiness
changes are authorized or implemented. Typed widths and ownership remain unresolved;
`parser_safe=false`. See the dedicated document for raw evidence, exact fixture
matrix, oracle isolation, regression snapshots and verification results.


## Candidate-only implementation update (2026-09-07)

**candidate-only experiment implemented under Promotion Review conditions**.
This implementation update supersedes historical statements below that the
candidate experiment is future work; the review and research history remain intact.
Semantic promotion is not authorized. `parser_safe=false`, typed widths unresolved,
and ownership unresolved remain mandatory; this is not production parser support.

The internal `parsers/text/text_slot_candidate.py` helper reads structurally
identified CParagraphe payloads. `Type3ChainParser.parse` calls it after all existing
semantic work, immediately before returning, and adds only
`candidate_fields["text_slot_run"]` on complete success. No model, serializer,
semantic text/color, anchor, chain mapping, ownership or MFC changes are involved.

The complete eligible payloads are searched under global limits: 32 payloads,
1,048,576 aggregate bytes, 4,096 raw token hits, 256 traversed slots and
`2 * aggregate_payload_length + 4096` signature/probe evaluations. Limits are
safety budgets, not format constants. Incomplete scans/probes or exceeded budgets
omit the key. Exact invariant bytes and the three joint variants alone identify
prefixes. Core-like unknown variants anywhere cause abstention; token-like
unsupported continuation cannot establish a terminal. Suffixes are deduplicated
by their predecessor at stride 204. Policy A requires exactly one maximal run
across the entire input, before any count/code/RGB validation.

Traversal follows independently validated prefixes, including internal zero
windows. The final four-byte code candidate window must be zero with a complete
next-prefix mismatch probe. Only then must all three count views (u8/u16le/u32le)
agree with the actual slot total. Their diagnostic widths do not confirm storage
widths. Known joint variants are checked independently at each traversed prefix.

Output retains the preceding 16-byte count window, four raw code candidate bytes,
three raw RGB candidate bytes, per-slot variant and terminal evidence. A 92-byte
local span is inspection provenance, not a semantic record extent; 204 is prefix
periodicity. Payload and descriptor provenance locate the exact existing lossless
`raw_data`; per-slot spans are payload-relative and do not duplicate full payloads.
Payload index is provenance only, never a chain or ownership assignment.

Whole-payload results for the reviewed corpus: 24 candidates / 207 slots, including
four multiline controls (10 slots each, including code-view 13 and terminal) and
seven multi-object controls. No competing-run contradiction was found in this
corpus. Additional text controls also yield provisional candidates; mirror-on,
slant-15/custom-30 and width-50/150 controls have no exact family-valid prefixes
and omit the key. This does not establish support for their layouts or non-ASCII
encoding. Multi-object candidates do not establish which object owns the run.

Regression coverage compares all 63 text fixtures and two geometry controls,
removing ONLY `candidate_fields["text_slot_run"]`. Dataclass values, raw bytes,
all other candidates, notes/warnings, order, attachment, anchors (including
baseline-midpoint/fallback), style and geometry remain equal. A separate comparison
against the actual pre-change HEAD parser source also passed all 65 fixtures.
Non-verbose preview and normalized inspect JSON are equal; verbose preview is
equal after removing only the new candidate. Generic rendering requires no change.

Validation: **152 focused candidate tests passed** (58 unit + 94 integration);
**580 full-suite tests passed** (428 baseline + 152 new). Ruff passes for
all three new Python files. Repository-wide Ruff reports 102 pre-existing
diagnostics; the modified existing parser retains its one unchanged F401
(unused Point import), verified against HEAD. No unrelated lint cleanup
was included. `git diff --check` passes.


Status: **Draft candidate framing RFC.** Phase 1A–1F analyzer evidence supports a
bounded candidate grammar. Parser/decoder/model implementation is **not authorized**.
No candidate fields or new parser behavior are implemented by this document.

Subsequent decision: the [promotion gate review](text_slot_framing_promotion_review.md)
governs the narrowly conditioned future candidate-only experiment. It supersedes
this draft's pre-review authorization status within that scope only; the grammar
remains descriptive, and neither document implements parser behavior.

Evidence closeout: [text/color investigation through Phase 1F](text_color_decode_rfc.md),
[text reverse engineering](text_reverse_engineering.md), and
[multi-object investigation](text_object_reverse_engineering.md).

## 1. Problem Statement

The historical payload-relative grid `47 + ordinal * 204` helped align local byte
observations, but neighboring starts repeat equally well or better. Start 47 is
not a uniquely established semantic record boundary and must not select a parser
record. A structurally discovered repeated prefix is the preferred candidate origin.

Keep four coordinate domains distinct:

| Domain | Meaning | Permitted use |
| --- | --- | --- |
| Runtime descriptor | `FF FF 06 00 0B 00` followed by ASCII `CParagraphe` | Framing provenance |
| Serialized CParagraphe payload | Bytes associated with that structurally identified class node | Bounded analysis input; preserve losslessly |
| Slot-run prefix start | First structurally accepted periodic prefix inside the payload | Provisional local origin |
| Slot-relative fields | Offsets from each repeated prefix, not from the descriptor or clipboard | Candidate byte relationships |

The [MFC compatibility audit](typeeditzone_mfc_archive_investigation.md) remains
`mfc_runtimeclass_framing_supported_but_writeobject_unclear`. Descriptor framing
is strongly observed, including schema 6 and name length 11. Complete WriteObject,
PID/reference context and the meaning of schema 6 beyond a runtime-class version
candidate remain unresolved. This RFC treats MFC framing as provenance only and
does not propose a parser or archive redesign.

The goal is a bounded structural candidate grammar with explicit abstention, not
a declaration of the complete slot payload, object boundaries or ownership.

## 2. Evidence Summary

The final corpus contains 24 usable runs and 207 slots. Earlier phase counts refer
to their respective fixture sets; they are not additional independent samples.

| Evidence level | Finding |
| --- | --- |
| Strongly observed | Prefix recurrence at stride 204 in 24 runs / 207 slots; nearby tested strides 196..212 do not retain the same runs |
| Strongly observed | Longest periodic sequence alone is ambiguous in 24/24 fixtures |
| Strongly observed | Preceding count-like view plus bounded prefix context identifies a unique candidate in 24/24 fixtures |
| Strongly observed | Prefix -4 count view equals total slots, including final zero, in 24/24 runs |
| Strongly observed | Three masked prefix variants occur in 22/1/1 runs; positive-prefix context is homogeneous within each current run |
| Strongly observed | Primary ASCII codes correspond ordinally at prefix +4, including spaces, digits and punctuation |
| Strongly observed | Four multiline/spacing fixtures are found at shifted locations using the same structural rule; code 13 and terminal are included in count |
| Strongly observed | Seven multi-object controls retain the framing relationships without object mapping |
| Strongly observed | Primary color-only changes occupy three bytes, normalized to prefix +0x50..+0x52 |
| Provisional | Count semantics are total slots including terminal; prefix family and final zero define a bounded framing candidate |
| Provisional | Prefix +4 is `slot_code_candidate`; +0x50..+0x52 is `rgb_bytes_candidate` |
| Unresolved | Typed count/code/color widths, general variant meanings, complete record extent, non-ASCII encoding, higher-level layout and ownership |

The 24 fixtures include seven ASCII content controls, six color/height/font
controls, seven multi-object controls, and four multiline/spacing controls. The
exact corpus and bounded evidence are retained by the existing
[Phase 1D](../tools/analyze_text_slot_record_schema.py),
[Phase 1E](../tools/analyze_text_slot_prefix_framing.py), and
[Phase 1F](../tools/analyze_text_slot_run_framing_semantics.py) analyzers.
They freeze structure before diagnostic text/intent access; wrong oracle input
and `--no-oracle` leave structural decisions unchanged.

## 3. Candidate Grammar

The following is descriptive notation, **not a production parser contract**:

```text
CParagraphePayload := UnknownPrefix SlotRunCandidate UnknownSuffix

SlotRunCandidate := CountCandidate Slot[validated_total_slot_count]
Slot             := PrefixVariant SlotPayload

CountCandidate:
    candidate value at first_prefix - 4
    typed width unresolved
    agrees with independently traversed total slot count

SlotPayload relationships, relative to each accepted prefix:
    +0x04          -> slot_code_candidate
    +0x50..+0x52   -> rgb_bytes_candidate
    +204           -> next candidate slot prefix

TerminalCandidate:
    final independently traversed slot
    slot_code_candidate == 0
    included in validated_total_slot_count
    no valid following slot prefix
```

`CountCandidate` and `PrefixVariant` describe views and predicates, not fixed-width
tokens to consume. The count observation does not prove that four bytes belong to
one field. The masked prefix window overlaps the code candidate; it is not a
28-byte serialized header followed by a separate payload. Unknown surrounding
bytes, including possible padding, remain unassigned.

For an accepted run with first prefix `p`, candidate prefix positions are
`p + i * 204`. Discover and traverse prefix evidence independently before comparing
its length to the count view. `Slot[count]` must not mean trusting a header to
allocate, fabricate or read that many records. Neither the beginning nor the end
of an entire 204-byte semantic record is established solely by this periodicity.
The end of `UnknownSuffix` and any complete-slot extent are likewise not decoded.

## 4. Prefix Family

The current family predicate inspects prefix +0..+31 with +4..+7 excluded.
Color bytes +0x50..+0x52 are outside this window and cannot be required invariants.
The rule consists of **20 invariant bytes and exactly three observed joint variant
vectors**. It is closed to the observed corpus for this draft.

All offsets and byte values below are hexadecimal and prefix-relative.

| Invariant offsets | Required bytes in offset order |
| --- | --- |
| +00..+03 | `05 00 00 00` |
| +09..+0B | `00 00 00` |
| +13 | `3F` |
| +14..+1F | `00 00 00 00 00 00 F0 3F 00 00 00 00` |

Variant positions are +08 and +0C..+12. Treat each row below as one indivisible
allowed combination; do not mix its components with another row.

| Variant | +08 | +0C..+12 | Observed runs |
| --- | --- | --- | ---: |
| v0 | `00` | `7B 14 AE 47 E1 7A 84` | 22 |
| v1 | `00` | `B8 1E 85 EB 51 B8 9E` | 1 |
| v2 | `01` | `7B 14 AE 47 E1 7A 84` | 1 |

The corresponding 28-byte **masked comparison strings**, with +4..+7 removed,
are reproduced for review; they must not be mistaken for contiguous payload bytes:

```text
v0  05000000000000007b14ae47e17a843f000000000000f03f00000000
v1  0500000000000000b81e85eb51b89e3f000000000000f03f00000000
v2  05000000010000007b14ae47e17a843f000000000000f03f00000000
```

Post-freeze labels associate v1 with the height-30mm control and v2 with one
mixed-group control. This does not establish height, grouping or mixed-color
field semantics. All three can carry the same diagnostic text; multiline uses v0.
First/terminal positive prefixes match later prefixes within each observed run;
the earlier first-slot difference is upstream of this window.

`05` alone is insufficient: a second periodic prefix 92 bytes later has equal run
length in the current fixtures. Future experiments must preserve unknown variant
bytes and return unresolved rather than broadening masks, accepting unobserved
combinations, or silently merging distinct contexts. Cross-variant switching
within a run is not established by these homogeneous-run observations and also
requires abstention or separately reviewed evidence.

## 5. Count Semantics

The candidate begins provisionally at prefix -4. Across 24 independently traversed
runs it equals **total slot count including the final zero-code terminal**. It does
not equal the nonterminal slot count, provisional run byte extent or `slots * 204`.
The byte-extent test currently uses `slots * 204`, so these latter comparisons
are not independent votes. Counts include the multiline code-13 position.

At -4, u8/u16le/u32le views all give the same values because the higher bytes are
zero. Only the low byte varies in this corpus. Structural count semantics are
stronger than typed encoding semantics:

```text
count_semantics       = total_slot_count_including_terminal
count_field_start     = provisional prefix-relative -4
count_typed_width     = unresolved / null
```

Alignment or the availability of four bytes must not promote u32le. The analyzers'
conservative four-byte comparison is a validation view, not a field declaration.
A future experiment needs explicit review of how to expose the raw count window
and reconcile views. If a narrower view matches but a wider view conflicts, it
must not select the convenient view to rescue acceptance. Preserve the raw -16..-1
context and return unresolved until the discrepancy is understood.

A merely correlated header value remains a formal possibility. Generalization
beyond the observed lengths and captures is an evidence gap.

## 6. Slot Code Candidate

Prefix +4 is the current `slot_code_candidate`. Primary ASCII controls match in
order, including spaces, digits and punctuation. Multiline contains code 13 within
the same recurring sequence; the final slot has code candidate zero.

Only one byte of the existing code view varies in these observations. This does
not establish `char`, u8 storage, Unicode, a character encoding, or a four-byte
integer field. Typed width and encoding remain unresolved; numeric diagnostic
views must retain their raw bytes and provisional provenance. Unknown/non-ASCII
codes must not be replaced with fixture-derived text or fabricated characters.

## 7. Color Candidate

The localized region is prefix +0x50..+0x52, normalized from the historical grid
+0x8B..+0x8D using the observed +0x3B prefix relationship in compatible single-line
layouts. The subtraction is evidence normalization, not a parser selector.

| Palette example | Observed candidate bytes |
| --- | --- |
| Black | `00 00 00` |
| Army Green | `98 CC 98` |
| Navy Blue | `30 60 CC` |

Primary color-only comparisons change exactly these three bytes. The candidate
is an RGB byte sequence, but three-byte RGB, u32le RGB0-like storage and alternate
aligned views remain unresolved. `color_typed_width=null` is mandatory in the
illustrative candidate output. Zero neighbors and palette matches do not establish
the next typed field boundary. A zero byte sequence elsewhere does not establish
a semantic Black color record.

Localization is separate from ownership. No slot RGB candidate can update an
object/chain color, select a semantic color record, or imply a slot-to-object map.
Color ownership remains `not_ready`. Multiline shares the masked normalized color
context, but changed-color multiline controls do not independently prove typed
color semantics there.

## 8. Multiline Compatibility

Four controls—multiline basic and fixed/proportional/print-proportional paragraph
spacing—are found structurally despite their shifted payload locations. No fixed
offset adjustment or hard-coded +68 correction participates in discovery.

They retain the same prefix family, 204 stride, count at -4 and code at +4.
Each has ten slots, including code 13 and the final zero. Code 13 does not break
prefix recurrence. This supports the same bounded framing family; it does not
decode line/run grouping, paragraph spacing semantics or higher-level multiline
layout. Unknown multiline variants must remain raw/unresolved.

## 9. Multi-object Compatibility

The seven current multi-object controls retain structural framing and count
relationships across grouped/not-grouped and content variations. These are
paragraph-run observations, not complete object text inventories.

Slots are not assigned to parser chains or semantic text objects. Actual stored
order, grouping ownership and selected-object correspondence remain unresolved.
Anchor equality, anchor ownership results and final chain indices are unavailable
as selectors or ownership oracles. Diagnostic capture labels may annotate already
frozen evidence only; they cannot influence parsing or object assignments.

## 10. Parser-Safe Requirements

These requirements constrain a possible future, separately authorized experiment;
they do not declare this candidate grammar parser-safe today.

1. Start from a structurally identified CParagraphe payload and preserve its full
   original bytes, including unknown regions and trailing bytes.
2. Locate runs structurally within explicitly reviewed search/resource bounds.
   Current analyzers search only [128, 768) for leading candidates, cap traversal
   at 24 slots and candidates at eight. These are research limits, not format
   constants or permission to scan arbitrary remaining payload regions.
3. Require the bounded prefix family before using +204 as a traversal step. A
   recurring token or padding pattern alone cannot establish slot validity.
4. Retain prefix and count evidence independently. Traverse observed prefixes
   within bounds; compare the actual count afterward. Do not allocate or read
   unbounded records based on a count-like value.
5. Validate final zero together with the end of prefix recurrence. Never stop on
   an internal zero when another valid prefix follows.
6. Preserve unknown prefix variants and raw context. Do not accept partial success
   by silently omitting an unknown, incomplete or contradictory slot.
7. Return unresolved on ambiguity, count disagreement, missing terminal, unknown
   variants, unsupported context changes or insufficient payload/probe bounds.
8. Retain lossless raw CParagraphe data and diagnostic candidate spans even when
   candidate extraction is unresolved. Do not fabricate slots or byte extents.
9. Never map slots to objects/chains without independent ownership evidence and
   a separately reviewed ownership design.

Forbidden selectors are fixture filename, expected text, expected color, intent
metadata, anchor equality, final chain index, absolute clipboard offset, and
historical payload start 47 (or a substituted fixed start such as 310/378).
Neither MFC schema 6 nor descriptor proximity supplies slot or ownership semantics.

## 11. Candidate-Only Parser Experiment Proposal

**Proposal only; do not implement.** If subsequently authorized, output could be
confined to a provisional candidate container. The following is illustrative
pseudocode, not a model definition, executable assignment or partial extracted run:

```text
candidate_fields["text_slot_run"] = {
  "source": "CParagraphe_slot_prefix_family_v1",
  "confidence": "provisional",
  "parser_safe": false,
  "count": <validated total slots including terminal>,
  "count_raw_bytes": <lossless preceding candidate window>,
  "count_typed_width": null,
  "stride": 204,
  "prefix_variant": <v0 | v1 | v2>,
  "prefix_payload_offset": <structurally discovered offset>,
  "raw_cparagraphe": <original bytes or lossless reference>,
  "slots": [
    {
      "ordinal": <0 through count-1>,
      "slot_code_candidate": <provisional numeric view>,
      "slot_code_raw_bytes": <raw candidate window>,
      "slot_code_typed_width": null,
      "rgb_bytes_candidate": [<byte>, <byte>, <byte>],
      "color_typed_width": null,
      "terminal_candidate": <structurally validated boolean>,
      "ownership": "unresolved",
      "matched_chain": null,
      "raw_record_or_span": <bounded bytes with payload-relative provenance>
    }
    <one actual entry per independently validated slot>
  ]
}
```

The numeric count/code view must be labeled and accompanied by raw evidence, with
no implied typed promotion. `raw_record_or_span` is a diagnostic span, not proof
of a complete 204-byte record. A later review must define exact bounds and ownership
of raw storage. On failure, preserve raw bytes and a separate unresolved reason;
do not emit an apparently complete success container with missing/synthesized slots.

No existing visible-text extraction, text attachment, geometry, color selection,
fallback or ownership behavior may be replaced by this proposed candidate output.

## 12. Failure Behavior

| Condition | Required candidate outcome |
| --- | --- |
| Multiple family-valid runs | Unresolved; preserve candidates, even when only one count agrees |
| Unknown prefix variant or unobserved variant combination | Unresolved; preserve bytes, do not widen the family |
| Count versus independently traversed run mismatch | Unresolved; retain both evidence streams |
| Missing, zero/corrupt-looking or conflicting count views | Unresolved; do not guess a value or preferred width |
| Missing final zero terminal | Unresolved, even if the count matches |
| Valid prefix after the slot claimed final by the count | Unresolved; do not trim the run or silently increase count |
| Internal zero with a following valid prefix | Continue bounded traversal; it is not yet a terminal candidate |
| Insufficient payload bounds, required next-prefix probe bounds, or resource budget | Unresolved; never read outside bounds or treat an untested region as absence |
| Slot-like unknown context at the next periodic position | Unresolved; do not use an unknown variant as a convenient end marker |
| Unsupported within-run variant switch | Unresolved pending independent evidence |
| Unknown multiline variant | Preserve full raw payload and return unresolved |

The next-prefix check must have sufficient bytes to determine the relevant family
predicate or an unambiguous mismatch. An inaccessible probe is not a proven absence.
Failure must not erase existing parser results or change their fallback behavior.

## 13. Non-Goals

This RFC does not implement parser, decoder, model or candidate fields; decode the
full slot payload; resolve typed field widths; solve color/anchor ownership; map
slots to chains; infer actual object order; reinterpret MFC PID/reference semantics;
or broaden prefix masks for convenience. It adds no analyzer, tests or fixtures.
The anchor ownership closeout and MFC investigation conclusions remain unchanged.

## 14. Evidence Gaps

- Typed count start/width, including the role of higher zero bytes and adjacent padding.
- Typed slot-code width and encoding; confirmed character storage is not established.
- Typed color width, alignment and independent neighboring field boundaries.
- General meanings of the three prefix variants and whether other families exist.
- Korean/non-ASCII slot representation and any relationship between slots, characters and glyphs.
- Broader multiline/paragraph-layout variants and multiple runs inside one payload.
- Longer text with **more than 255 total slots** as a future discriminating fixture
  idea for count width. This task creates no fixture; such work requires separately
  reviewed capture and resource bounds beyond the current 24-slot analyzer limit.
- Alternate Type3 versions and possible serialization changes.
- Slot-to-object/chain ownership and actual stored order.
- Full slot payload schema, complete record boundaries and unknown prefix/suffix regions.

Future discriminating observations must not be replaced by palette fits, expected
text, arbitrary padding assumptions or MFC provenance terminology.

## 15. Readiness

| Area | Readiness |
| --- | --- |
| Slot-run structural framing | Bounded candidate supported |
| Count semantics | Total slots including terminal strongly observed |
| Count typed width | Unresolved |
| Stride | 204 strongly observed as prefix periodicity |
| Prefix family | Three observed variants, bounded |
| Slot-code location | Strong candidate at prefix +4 |
| Slot-code typed semantics | Unresolved |
| RGB byte location | Strong candidate at prefix +0x50..+0x52 |
| Color typed field | Unresolved |
| Multiline compatibility | Observed in current four fixtures |
| Multi-object framing | Structurally compatible in current seven controls |
| Slot/object ownership | Unresolved; color ownership not ready |
| Candidate parser RFC | Ready as this draft candidate proposal |
| Candidate parser implementation | Not ready; not authorized |
| Candidate parser model | Not ready; `parser_safe=false` |

Readiness to specify a bounded candidate experiment is not approval to implement
or a statement that the Type3 format has been decoded.

## 16. Promotion Gates

Before any candidate parser implementation, require explicit review of:

1. Whether the closed bounded prefix family and reviewed search/resource limits
   are acceptable parser selectors, including treatment of competing runs.
2. Whether count validation is safe without a known typed width, and which raw
   views may be exposed without pretending to settle that width.
3. Whether raw count bytes and their provenance must accompany every candidate
   numeric count, including conflicting-view diagnostics.
4. Whether unknown variants, incomplete probes, missing terminals and ambiguous
   counts reliably preserve raw data and fall back unresolved.
5. Whether tests can guarantee current parser outputs and behavior remain unchanged,
   including visible text, color, geometry, ordering, attachment and fallback.
6. Whether provisional slot output belongs exclusively in `candidate_fields`, with
   `parser_safe=false`, unresolved ownership and no model/semantic promotion.

Any later implementation must remain candidate-only and must not replace existing
visible-text extraction or color behavior. Review of this draft and a separate
implementation authorization are still required. This documentation task does not
pass those gates on behalf of a future implementation.

Documentation-only validation command:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m pytest -q
```

Documentation-only validation: **428 passed** with `PYTHONPATH=src`, preserving
the 428-test baseline. The 16 sections, local links, invariant-byte table and exact
variant strings were checked against existing evidence; whitespace checks passed.
No parser, decoder, model, analyzer, fixture or test files changed.
