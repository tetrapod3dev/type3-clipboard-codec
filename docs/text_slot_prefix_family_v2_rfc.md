# CParagraphe Text-Slot Prefix Family v2 Redesign RFC

## Runtime v2 candidate promotion review (2026-09-08)

The [v2 Runtime Promotion Gate Review](text_slot_prefix_family_v2_promotion_review.md)
decides **runtime_v2_candidate_replacement_authorized_with_conditions**:
future Strategy A replacement only within text_slot_run, with neutral run-level
prefix_family=F4 and raw plus08_value metadata replacing legacy run/slot
prefix_variant. Gates 3/4 pass; Gates 1/2/5/6/7/8 pass with concrete conditions.
These include a global veto for recognized unsupported contexts mixed with a
valid run, which the existing shadow helper does not yet enforce, and exact
allowlist-based runtime regression. No implementation occurs in this review.
Current runtime remains v1; parser_safe=false, typed widths and ownership remain
unresolved. No fallback, dual family or semantic promotion is authorized.
This current authorization status supersedes earlier not-authorized status
statements for the narrowly scoped future experiment only; historical evidence,
the Draft redesign RFC text and prior review scopes below are preserved.


## Independent v1/F4 shadow status (2026-09-08)

Promotion Gate 3/4 shadow evidence is now available in the
[standalone analyzer](../tools/analyze_text_slot_family_shadow.py) and
[frozen comparison report](../tests/samples/reports/text/text_slot_family_shadow_comparison.json).
The actual v1 parser produced 62 candidates across 104 real fixtures
(72 text, including all 9 controlled styles, 5 prior unsupported styles,
4 multiline and 7 multi-object captures; 32 geometry controls).
Independent F4 produced 72 shadow candidates: 62 identical raw-provenance runs,
10 v1-absent/v2-present disagreements, 32 both-absent controls, no losses,
different-run disagreements, real ambiguities or resource/bounds differences.

The 10 disagreements are structurally explained by legacy predicate mismatches:
height bytes in controlled height20 (1); width invariant bytes in mirror,
prior width50/150 and controlled width50/150 (5); slant invariant bytes in
prior slant15/30 and controlled slant +/-15 (4). These semantic region labels
are applied only after structural results freeze, and do not select runs.
Raw identity accounting: 1,184 token hits, 592 F4 matches, 72 maximal recurring
and deduplicated runs, 520 suffix starts removed, zero global competitors,
zero count/terminal failures and 72 final successes. All 72 known +92 decoy
runs (592 prefixes) fail identity.

The separate 32-case synthetic harness rejects all six general negatives.
Identity clones still pass identity/recurrence: wrong count fails count,
nonzero terminal fails terminal, and two complete runs abstain under Policy A.
The old synthetic templates receive 64 continuation bytes for this study;
otherwise their 32-byte context would fail bounds before testing later layers.
This is safe abstention evidence, **not a zero false-positive-rate claim**.

Observed +08 is constant within every run (71 runs use 00, one uses 01);
unknown values and mixed 00/01 runs fail closed without semantic inference.
Both wider constants reject one-byte and multi-byte mutations. Exact 64-byte
identity bounds pass; 63-byte identity and incomplete next-prefix probes fail
conservatively. RGB/raw-span bounds are separate. Existing resource caps remain
unchanged; synthetic exhaustion yields no candidate and no real exhaustion
occurs (maximum 23 probe evaluations). Probe-budget exhaustion is guard-tested
by fault injection; the reviewed formula exceeds reachable token probes.

All 104 parser serializations, inspect/preview outputs and runtime source hashes
match the pre-existing frozen baseline. Oracle-disabled output differs only in
oracle_summary; adversarial labels and renamed input preserve structural outcomes.
Default JSON is 90,523 bytes, text 10,090 bytes; bounded details JSON is 92,243 bytes.
Focused tests: 62 passed. Full PYTHONPATH=src pytest: 784 passed (722 baseline
plus 62 new tests). Ruff on all three shadow Python files and git diff --check
pass. Historical evidence below remains unchanged.

disagreement_closeout_readiness and runtime_v2_promotion_review_readiness:
**ready_for_review**. This is independent evidence for a separate Promotion Review,
not runtime adoption approval. RFC remains **Draft redesign RFC**.
Runtime v1, public candidate fields, source string, models and parser behavior
remain unchanged; no v2 public candidate or fallback exists. Runtime v2
implementation/replacement remains **not authorized**. parser_safe=false;
ownership, style semantics and typed widths remain unresolved.


Status: **Draft redesign RFC.** F4 evidence supports a style-independent bounded
identity candidate in the observed corpus. **Runtime implementation/replacement
not authorized.** Date: 2026-09-07. Current full pytest baseline: 722 passed.

**The v0/v1/v2 runtime family is retained for safety while redesign evidence is reviewed.**

This RFC freezes evidence, failure policy and migration constraints for a separate
Promotion Review. It does not implement F4, a shadow evaluator or a fallback.
Increased candidate coverage does not authorize a runtime change.

## 1. Version terminology and current contract

| Name | Meaning and status |
| --- | --- |
| Current family v1 | Implemented candidate-only runtime; source `CParagraphe_slot_prefix_family_v1` |
| Legacy variants v0/v1/v2 | The three exact joint byte variants **inside current family v1** |
| Proposed family v2 / F4 | Research redesign candidate described here; not implemented or authorized |

The legacy variant named `v2` is not the proposed family version 2. In particular,
its +0x08=01 observation does not confer a semantic meaning on the new family.

Current [extractor](../src/type3_clipboard_codec/parsers/text/text_slot_candidate.py)
and [integration](../src/type3_clipboard_codec/parsers/type3_chain_parser.py) remain
unchanged: candidate-only, `parser_safe=false`, Policy A, exact legacy variants,
unresolved typed widths, and failure by omitting `candidate_fields["text_slot_run"]`.
Source/visible text, text attachment, style/color, ownership, geometry, anchors,
chain order, notes/warnings and fallback behavior remain unchanged.

The [existing Promotion Review](text_slot_framing_promotion_review.md) authorized
only the current experiment under its conditions. That authorization does not
transfer to this family redesign. The [original framing RFC](text_slot_framing_rfc.md)
remains historical context; this draft does not rewrite its prior decisions.

## 2. Frozen Phase 1G evidence and its limits

Evidence comes from the [prefix redesign analysis](text_slot_style_field_investigation.md#prefix-family-redesign-analysis-2026-09-07)
and [standalone analyzer](../tools/analyze_text_slot_prefix_redesign.py), building
on the [controlled style analysis](text_slot_style_field_investigation.md).
These existing artifacts are not changed by this documentation task.

| Corpus | Observed coverage |
| --- | --- |
| Text captures | 72 reference runs / 592 slots |
| Geometry scope controls | 32 captures |
| Known +92 periodic competitors | 72 runs / 592 slots |
| Synthetic/challenge cases | 9: six general negatives, two identity-clone negatives, one two-complete-run ambiguity challenge |

The text corpus includes controlled style 9, previous Phase 1F 24, previously
unsupported mirror/slant/width 5, and 34 other text captures. Multiline 4 and
multi-object 7 are subsets of the previous 24, not additional independent runs.
Reference nomination used bounded raw recurrence/count/terminal research evidence;
it is not semantic ground truth or object ownership. Hypothesis identity matches
were evaluated independently and were not filtered by reference count validation.

Controlled captures use Arial `AAAAAAAA`, changing one attribute of character 4
(zero-based ordinal 3), resetting to baseline between captures. Lower-left is
`[31.123,72.234,1.234]` mm and anchor `[68.415,72.234]` mm, center-bottom.
Z=1.234 is a diagnostic control against zero-heavy byte patterns, not evidence
for a new Z parser rule. These labels and expected values are oracle-only.
Structural results were frozen before labels; no-oracle and adversarial intent
checks preserve predicate results. No future selector may consume capture intent,
expected style/text/color, intended target index or filename semantics.

### Diagnostic slot-local candidates

All ranges in this RFC are inclusive unless explicitly stated otherwise.
These are analyzer/research correlations, **not production-confirmed types**.

| Relative region | Diagnostic candidate / evidence |
| --- | --- |
| +0x04..+0x07 | `slot_code_candidate`; numeric/raw window only |
| +0x0C..+0x13 | Height-correlated candidate: f64le 0.01 / 0.02 / 0.03, consistent with 10/20/30 mm expressed in meters |
| +0x14..+0x1B | Width-correlated candidate: f64le 1.0 / 0.5 / 1.5 |
| +0x1C..+0x23 | Slant-correlated candidate: f64le ±0.2617993877991494, consistent with ±15° in radians |
| +0x2C..+0x2F | Auxiliary variable region; semantics unresolved |
| +0x48..+0x4F | Rotation-correlated candidate: f64le ±0.2617993877991494 |
| +0x50..+0x52 | RGB-byte candidate |

Typed widths remain unresolved, including where an eight-byte diagnostic read
matches an expected number. The primary style regions isolate the controlled
character, but some captures have additional auxiliary/non-target/terminal and
global changes. Those exceptions remain evidence, not bytes to normalize away.

### Old-family result

| Hypothesis | Full text runs | Controlled style | Captured ambiguities |
| --- | ---: | ---: | ---: |
| F0: existing exact family | 62/72 | 4/9 | 5 |
| F1: exclude height-correlated region | 63/72 | 5/9 | 4 |
| F2: exclude height + width | 68/72 | 7/9 | 2 |
| F3: exclude height + width + slant | 72/72 | 9/9 | 0 |

F3 nevertheless accepts 3/6 general synthetic negatives. Its zero filler passes
identity, recurrence, count and terminal, showing that count cannot repair weak
identity evidence.

Conclusion: **old_family_overconstrained_by_style_fields**. Observed legacy v0/v1
differences are fully explained in the current corpus by height-correlated bytes;
width and slant regions also overlap old identity requirements. The old v0/v1
distinction is not needed as framing identity in this corpus. This does not prove
general format semantics, confirm typed height storage or explain the +0x08 class.

## 3. Exact F4 identity candidate

At a payload-relative prefix origin `p`, require the complete local interval
`[p,p+64)` within the structurally identified CParagraphe payload. No partial
predicate match is sufficient. F4 requires exactly the following evidence:

| Relative position/range | Required raw bytes | Interpretation |
| --- | --- | --- |
| +0x00..+0x03 | `05 00 00 00` | Token/core candidate |
| +0x08 | Exactly `00` or `01` | Observed raw set; meaning unresolved |
| +0x09..+0x0B | `00 00 00` | Core candidate |
| +0x24..+0x2B | `00 00 00 00 00 00 00 00` | **structural_constant_candidate** |
| +0x38..+0x3F | `9A 99 99 99 99 99 D9 BF` | **structural_constant_candidate** |

There are 24 required byte positions distributed across a 64-byte local span.
The span is a bounds requirement, not a semantic record size. Neither wider
region is called a confirmed format constant, padding field or semantic field
in this RFC. Earlier exploratory labels remain historical, not promotions.

All unlisted positions are outside the proposed identity evidence. In particular:

- +0x04..+0x07 varies with the slot-code candidate and must not select framing.
- +0x0C..+0x13, +0x14..+0x1B and +0x1C..+0x23 are excluded because controlled
  height/width/slant differences break their old identity constraints.
- +0x2C..+0x2F is independently variable and unresolved, so it is not an invariant.
- +0x30..+0x37 is also unrequired by F4; its variable observations do not establish
  a semantic field or authorize an automatically learned mask.
- Rotation +0x48..+0x4F and RGB +0x50..+0x52 are outside the 64-byte F4 identity
  bounds and need no special masking. Their diagnostic values do not enter F4.

This is a declared few-range predicate, not a rule to mask every varying byte or
retain every constant in a training corpus. No numeric style plausibility test
may replace or supplement these raw requirements as an unreviewed selector.

### +0x08 policy

Observed +0x08 is 00 in 71 runs and 01 in
`text_group_mixed_color_two_objects.txt`; it is constant within each observed run.
Other grouped/mixed-color controls do not establish a unique association.
The possible v2 experiment's allowed set is **{00,01}**, never a wildcard.
Do not name the byte a group flag, mixed-color flag, object flag or style flag.
Its semantics remain unresolved.

Every unobserved value must trigger safe abstention when encountered as possible
family/continuation evidence unless separately reviewed. It cannot be discarded
to manufacture uniqueness for another run. A within-run switch between 00 and 01
has no supporting observation here; this RFC does not authorize accepting such
switches. The subsequent review must settle a fail-closed consistency rule rather
than infer support from the per-prefix allowed set alone.

## 4. F4 performance and specificity

| Positive cohort | Full reference-run recall |
| --- | ---: |
| Controlled style | 9/9 |
| Previous Phase 1F | 24/24 |
| Multiline subset | 4/4 |
| Multi-object subset | 7/7 |
| Previously unsupported mirror/slant/width | 5/5 |
| Total text corpus | 72/72 |

Known +92 decoys: **0 accepted / 72**, with all 72 rejected at identity before
count filtering; all 592 decoy prefix positions are rejected. The decoy is not
rejected by an expected +92 offset selector: independent predicate evaluation
finds the mismatches, and +92 is diagnostic provenance afterward.

General synthetic negatives: **F4 0/6 accepted**. F0 also rejects these six.
Including the two negative identity clones gives **2/8 identity collisions** for
both F0 and F4. The ninth challenge contains two complete cloned runs and stays
ambiguous. The 2/8 denominator includes six general negatives plus two clones;
it is neither two out of nine nor a population false-positive estimate.

**F4 is not a globally unique object signature. F4 alone must NEVER produce a
successful text_slot_run candidate.** Literal identity bytes can be reproduced.
The tested wrong-count clone fails count; the nonzero-terminal clone fails
terminal; two complete clones fail global uniqueness. These results show safe
abstention for the tested collisions, not a proof that every possible synthetic
single run is distinguishable from genuine serialized data.

### Geometry-negative limitation

The 32 geometry fixtures are negative **scope controls**, with no eligible
CParagraphe payloads. Thus “0 false positives in geometry” is not equivalent to
strong specificity inside text payloads. Stronger current negatives are the
+92 competitors inside text structures, synthetic/challenge payloads and competing
complete-run clones. A captured CParagraphe-without-slot-run negative corpus was
not found and remains an evidence gap. Future review must retain that limitation.

## 5. Separate evidence layers and mandatory Policy A

| Layer | Obligation |
| --- | --- |
| 1. Identity | Complete bounded F4 raw predicate, including exact +08 policy |
| 2. Recurrence | Independently establish maximal 204-periodic runs; deduplicate suffixes |
| 3. Global uniqueness | Require exactly one structural run under Policy A across all eligible payloads |
| 4. Count | Validate independent traversal total against all diagnostic count views |
| 5. Terminal | Final four-byte zero-code window and sufficiently bounded next-prefix absence/mismatch |

These layers must not collapse into a score. Their numbering identifies separate
obligations, not permission to use count as a traversal bound. Count comparison
may remain deferred until after terminal establishment, as in the current
conservative implementation; no successful result exists until both validate.

Policy A remains mandatory: zero family-valid runs gives no candidate; exactly
one proceeds to validation; multiple independent family-valid runs give
unresolved / key absent. This applies globally, including distinct CParagraphe
payloads. Suffixes of one periodic run are not competing starts.

“Complete run” here concerns sufficient structural/bounds evidence, **not prior
count or terminal approval**. A competing family-valid run may not be removed
because its count disagrees or its terminal looks less plausible. No new minimum
run length is authorized to discard competitors. Uncertain or incomplete possible
continuations are not evidence of absence and must not manufacture uniqueness.

Even if only one run has matching count, plausible terminal, proximity to the
payload start, matching visible text or expected style/color, the candidate is
absent. No count selection, ranking, nearest-node preference, chain mapping,
anchor matching or oracle-based disambiguation is allowed. Two independently
valid complete runs surviving all other checks still require absence.

Identity collisions are tolerable only within this fail-closed candidate-only
contract, because later structural checks and Policy A can abstain. The observed
collision rate cannot be described as zero by removing failures from reporting.

## 6. Descriptive candidate v2 grammar and failure API

This grammar describes a possible future experiment, not implemented behavior:

```text
StructurallyIdentifiedCParagraphePayloads
  -> complete bounded F4 identity search over all eligible payloads
  -> identify maximal 204-periodic runs
  -> deduplicate suffixes of each run
  -> require exactly one structurally complete run globally (Policy A)
  -> traverse independently of count, text, style, color and ownership
  -> determine actual total slots and validate all count views
  -> validate zero terminal and sufficiently bounded next-prefix absence
  -> only after every obligation succeeds, attach candidate_fields-only output
```

This descriptive listing does not reorder the existing conservative count/terminal
schedule into a new authorization. Actual total must derive from independent
bounded traversal, include the terminal, and be finalized only with terminal
validation. Internal zero windows do not end traversal while another valid prefix
follows. The final four-byte +4 window must be entirely zero; this is a structural
predicate, not a promotion of a four-byte storage type.

Unchanged candidate relationships:

| Relationship | Required continuity |
| --- | --- |
| Count provenance | Complete first-prefix −16..−1 raw window; probe at −4 |
| Count diagnostic views | u8/u16le/u32le values, diagnostic widths and relative offset −4; all must agree with independently traversed total |
| Count typed width | null; never prefer a matching narrow view over a conflicting wider view |
| Stride | 204, prefix periodicity rather than semantic record extent |
| Code candidate | +4 raw/numeric candidate only; no production text replacement |
| RGB candidate | Three raw bytes at +0x50..+0x52; no semantic object color assignment |
| Terminal | Final four-byte zero plus complete next-prefix absence/mismatch evidence |
| Ownership / matched chain | unresolved / null |
| Typed widths | null |
| Provenance | Existing lossless raw_data, bounded slot spans and explicit coordinate domains |

F4's 64-byte identity bounds do not supply the additional RGB/local provenance
bounds. Those must be verified separately. Likewise a future next-prefix absence
probe must cover F4's complete required context; a legacy 32-byte check cannot
silently establish absence of a 64-byte predicate. The Promotion Review must
explicitly validate this bounds migration. A 92-byte local provenance span remains
inspection context, not a record-size claim.

| Failure or unsupported condition | Required result |
| --- | --- |
| No run, multiple family-valid runs, or any ambiguity | Key absent |
| Count missing/zero/mismatched or conflicting views | Key absent; no repair or width selection |
| Missing terminal, extra prefix after count-implied end, incomplete next probe | Key absent; no trimming or fabricated slots |
| Unknown +08 / changed structural constant in possible family context | Safe abstention; never ignore evidence to keep another run unique |
| Unsupported possible continuation | Key absent; never convert it into a convenient terminal |
| Partial local context or exhausted scan/traversal budget | Key absent; no success from the scanned prefix of input |

Failure means **omit `candidate_fields["text_slot_run"]` itself**. Do not emit null,
an empty dictionary, partial slots, an unresolved public placeholder or a secondary
diagnostics key. Existing raw_data and all unrelated results must be unchanged.
A future review must fix the exact conservative recognizer for “possible family
context” before implementation; this RFC does not invent a broader runtime mask.

## 7. Search, resource and structural-constant risk

Search only already structurally identified CParagraphe payloads. Examine the
complete eligible bounded payload range before claiming uniqueness, with bounds
derived from payload length and complete F4/context requirements. Never use start
47, 310, 378, multiline shifts, absolute clipboard offsets or the historical
[128,768) research window as format selectors. No MFC refactor or new archive
scanner follows from this proposal.

Current reviewed runtime caps, recorded for continuity only, are 32 payloads,
1,048,576 aggregate bytes, 4,096 raw token hits, 256 traversed slots and
`2 * aggregate_payload_length + 4096` signature/probe evaluations. They are safety
limits, not format constants. **No different caps are authorized here**. Their
exact application to possible v2 evaluation/bounds must be accepted by the
subsequent Promotion Review. Analyzer-specific budgets do not replace runtime
budgets. Exhaustion must omit the candidate, never return partial success.

The principal remaining structural risk is the meaning of the two wider
`structural_constant_candidate` regions. They are stable over the current corpus
and distinguish known negatives, but may ultimately prove to be:

- true structural constants;
- default-valued fields;
- layout/style fields not yet varied;
- version-specific values.

Therefore any later v2 implementation must remain candidate-only,
`parser_safe=false` and fail-closed when they change. Never silently broaden their
values, turn them into wildcards or discard unknown core-like runs. More captures
varying these regions and genuine unsupported CParagraphe negatives would improve
the evidence. Stable bytes and increased positive recall alone cannot pass a gate.

## 8. Candidate output compatibility and regression constraints

Prefer the existing public dictionary shape and singular key
`candidate_fields["text_slot_run"]`. A possible source string is
`CParagraphe_slot_prefix_family_v2`, **only after explicit Promotion Review**.
The runtime source remains `CParagraphe_slot_prefix_family_v1` in this task.

Required run/slot metadata remains `confidence=provisional`, `parser_safe=false`,
`ownership=unresolved`, `matched_chain=null`, null typed widths and exact raw
provenance. Keep count window/views/validated total, code/RGB candidates, terminal
evidence and bounded span references. Do not duplicate full payloads per slot.
Version-specific `prefix_variant` identifiers or source/content differences need
an explicit compatibility decision; do not silently reinterpret legacy variant
names as F4 meanings or introduce model/dataclass changes to fit a new schema.

No semantic result may depend on the candidate. Source/visible text, attachment,
active anchor and baseline_midpoint/fallback, candidate anchors, matched_chain,
style/color, geometry, ordering, ownership, notes/warnings and lossless raw_data
must remain byte/value identical. Inspect/preview differences must be restricted
to the reviewed candidate entry; non-verbose semantic output stays unchanged.

A future regression comparison may exclude **only explicitly reviewed intentional
candidate source/content differences**. Prefer an exact allowlist and independent
assertions for each changed candidate field/presence transition. Never remove all
candidate_fields, ignore raw_data/notes/warnings or normalize ordering. If an
entire text_slot_run entry needs exclusion for a reviewed presence transition,
validate that entry separately and retain every unrelated candidate in equality.
This RFC itself excludes nothing from current parser output: it changes no code.

## 9. Migration policy and required pre-implementation shadow study

There is no authorized automatic fallback: neither “try v2 then v1” nor “try v1
then v2.” Fallback can hide disagreement and ambiguity. No second simultaneous
public v1/v2 candidate is proposed.

Before runtime replacement, the recommended first study is an independently
reviewed **shadow comparison**: evaluate the current v1 experiment and a proposed
v2 experiment independently over the full current fixture corpus, compare raw run
provenance and candidate presence/structure, and investigate every disagreement.
Do not expose both publicly. This recommendation does not authorize or implement
a shadow evaluator in this documentation task.

The study should report, with byte/provenance evidence:

| Outcome | Required accounting |
| --- | --- |
| v1 success / v2 success | Report both totals and overlap |
| Both succeed identically | Same selected payload/run, ordinals, count/terminal and raw spans; anticipated source labels distinguished explicitly |
| v1 fails / v2 succeeds | Explain each coverage gain without using expected style as a selector |
| v1 succeeds / v2 fails | Investigate every loss; no fallback conceals it |
| Both succeed but different run/content | Preserve disagreement; no winner by count, text, color, anchor or rank |
| v2 ambiguity | Include all family-valid competitors before count/terminal filtering |
| Identity collision | Retain identity-layer matches even if later validation abstains |
| Resource-bound difference | Attribute bounds/cap/probe differences; do not compare only successful scans |

Include all 72 text captures, 32 geometry scope controls, known decoys, synthetic
collisions/competing runs and any newly available unsupported paragraphs. Report
bounds/constant/+08 mutations and incomplete context as required review evidence,
not as permission to create fixtures or tests here. The study must keep structural
results independent of oracle labels. Only a subsequent migration/Promotion Review
may decide the selected family, accepted differences and runtime source transition.

## 10. Promotion gates before any runtime change

The following are **required gates**, not passed gates. Existing analysis supplies
evidence for review, not an implementation decision. No gate passes merely because
v2 increases coverage. Each gate requires an explicit review decision and evidence.

| Gate | Required acceptance/evidence |
| --- | --- |
| 1. Exact identity | Accept F4's raw positions/values, 64-byte bounds, +08 enumeration and fail-closed within-run/unknown-context policy |
| 2. Collision safety | Show tested identity collisions abstain safely under recurrence, global Policy A, count and terminal; keep identity failures visible and do not claim global uniqueness |
| 3. Shadow comparison | Complete independent v1/v2 comparison across the full current fixture corpus and challenge set |
| 4. Disagreement closeout | Enumerate and understand every gain, loss, different run/content, ambiguity and resource-bound difference; explicitly decide migration policy |
| 5. Regression equality | Prove exact equality outside only reviewed candidate source/content/presence differences, which receive separate assertions |
| 6. Bounds/resources | Accept exact runtime caps, full payload search, 64-byte identity/next-prefix probes, separate RGB/provenance context and no partial success on exhaustion |
| 7. API/semantic isolation | No model/dataclass, serializer, decoder interface, semantic text/color, ownership, chain/anchor or ordering changes |
| 8. Future unknowns | Prove changed wider constants, unknown +08 and unsupported possible continuations fail closed without mask broadening, fallback or manufactured uniqueness |

After the review, any candidate-only implementation remains provisional until its
required runtime regression/bounds checks pass. Implementing the proposal, deploying
it and replacing the current family are distinct decisions; this draft authorizes
none of them.

## 11. Readiness table

| Area | Readiness |
| --- | --- |
| F4 positive recall | 72/72 current text runs |
| Controlled style recall | 9/9 |
| Previous Phase 1F recall | 24/24 |
| Multiline | 4/4 |
| Multi-object | 7/7 |
| Prior unsupported styles | 5/5 |
| Known +92 decoy rejection | 72/72 |
| General synthetic negatives | 0/6 accepted |
| Identity-clone resistance | Incomplete; 2/8 collide at identity layer |
| +0x08 semantics | Unresolved; observed set {00,01} |
| +0x24/+0x38 structural constant semantics | Unresolved |
| Geometry specificity | Scope-only negative evidence |
| Unsupported real CParagraphe negatives | Evidence gap |
| Ownership | Unresolved |
| Typed widths | Unresolved |
| Parser-safe | false |
| v2 RFC | Ready as a draft for separate review |
| Runtime v2 implementation | **Not authorized** |
| Runtime replacement | **Not authorized** |

## 12. Non-goals and documentation validation

This task changes no runtime extractor, chain parser, constants, models, decoder
interfaces, fallback, style semantics, typed widths, ownership, chains, anchors,
Z behavior or MFC conclusions. It adds no v3/v4/v5 variants, fixtures, analyzer,
shadow evaluator or tests. Current family v1 is the implemented candidate-only
runtime; proposed family v2/F4 is research redesign only.

Documentation validation command:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m pytest -q
git diff --check
```

Documentation-only validation: **722 passed** (unchanged from baseline).
`git diff --check` passes. New RFC links and all eight gate entries were checked;
the five existing document bodies are preserved, with status links added only.
Passing the current suite cannot pass future implementation gates for runtime
code that does not exist.
