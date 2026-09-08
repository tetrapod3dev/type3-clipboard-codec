# CParagraphe Text-Slot Prefix Family v2 Runtime Promotion Gate Review

## Candidate-only runtime v2 acceptance (2026-09-09)

runtime_v2_replacement_acceptance = **accepted_candidate_only**.

The authorized Strategy A implementation and acceptance conditions now pass.
The active public source is **CParagraphe_slot_prefix_family_v2** within the
existing candidate_fields["text_slot_run"] key. This acceptance supersedes the
earlier current-runtime-v1 and pending-implementation status statements below;
their dated review decisions and historical evidence remain unchanged.

Only the [candidate extractor](../src/type3_clipboard_codec/parsers/text/text_slot_candidate.py)
changed in runtime source. It uses exact bounded F4 identity, the reviewed
rejection-only possible-context recognizer and global unsupported-context veto,
204-periodic roots with suffix deduplication, Policy A before independent
count/terminal validation, and candidate construction only after every check.
Private accounting separates token hits, identity positions, roots, suffixes,
unsupported contexts and competitors. Early failure marks the scan incomplete;
diagnostics never enter the public candidate or select a run.

The positive predicate requires complete 64-byte context, token 05000000,
+08 in {00,01}, +09..+0B zeros, +24..+2B eight zeros, and +38..+3F
9A9999999999D9BF. All prefixes in a successful run have the same raw +08.
Both wider regions remain structural_constant_candidate with unresolved meaning.
Gate 8 now globally rejects unknown_plus08, unknown_structural_constant and
unknown_core under the exact reviewed conditions, including valid plus
unsupported contexts in either order within/across payloads and at
first/interior/last/next positions. Ordinary mismatches do not become vetoes.
No fallback, dual family, mask widening, learned values or oracle selection exists.

| Acceptance obligation | Verified result |
| --- | --- |
| Real corpus | 104: 72 text, 32 geometry scope controls |
| Overlaps | All 62 same payload/run/provenance; exact metadata allowlist only |
| Reviewed gains | Exactly the ten fixtures listed in section 4; full new candidate independently matches frozen positions/raw provenance |
| Other presence transitions / losses / different runs | 0 / 0 / 0 |
| Remaining controls | All 32 retain candidate absence |
| Runtime identity accounting | 1,184 tokens; 592 identity positions; 72 maximal runs; 520 suffixes removed; zero unsupported contexts or competitors in real corpus |
| Known +92 decoys | 72 runs / 592 positions: ordinary identity mismatch, no global veto |
| Prior general negatives | 0/6 accepted |
| Identity clones | Wrong count fails count; nonzero terminal fails terminal; two runs fail Policy A |
| Competing invalid-count/terminal runs | Neither later validation can choose a winner |
| +08 and wider constants | Both allowed uniform values pass; unknown/switch and single/multiple-byte constant mutations fail closed, including mixed inputs |
| Bounds | Exact 64-byte identity and next probes; 63-byte/incomplete probes fail; count/RGB/92-byte raw context separately bounded |
| Caps | Existing five caps unchanged; limit/over-limit and injected probe guard checked; exhaustion never returns partial success |
| Semantic regression | All 104 exact outside the reviewed candidate delta, including raw_data, notes/warnings, unrelated candidates and ordering |
| Inspect/preview | Exact candidate-only display delta; non-verbose output unchanged |

Metadata changes are exactly source v1 -> v2, removal of run/slot prefix_variant,
and addition of run-level prefix_family="F4" and raw integer plus08_value.
There is no per-slot replacement field. All count/code/RGB values, spans,
terminal flags, provisional confidence and unresolved/null metadata remain
equal for overlaps. The 256-slot safety boundary does not waive count agreement:
u8 cannot represent 256, so that synthetic case fails count after traversal;
257 fails the slot cap. This retains the existing contract without typed promotion.

[Runtime unit acceptance](../tests/unit/test_text_slot_candidate_v2.py) and
[104-real migration regression](../tests/integration/test_text_slot_candidate_v2_migration.py)
validate current v2 directly. The byte-exact
[frozen v1 extractor](../tests/frozen_text_slot_candidate_v1.py) is test-only and
its hash matches the pre-migration baseline. Historical Phase 1F/1G/shadow tests
use an isolated temporary v1 replay through
[test support](../tests/text_slot_v1_replay.py), preserving their assertions,
analyzers, reports and captures. Those historical analyzer entry points target
v1 and are replayed in that historical environment, not used as current-v2
acceptance tools. No production import or retry path uses the frozen extractor.
The historical shadow helper's mixed-context limitation remains historical;
the runtime implementation closes it without rewriting shadow evidence.

Validation: focused runtime units **228 passed**; migration integration
**107 passed**; candidate/anchor/text/color/geometry regressions **957 passed,
104 deselected**; full PYTHONPATH=src pytest **1061 passed in 53.23s**
(pre-migration baseline 784). Ruff passes all ten changed/added Python files.
git diff --check passes; runtime diff is limited to the candidate extractor.
No parser integration, analyzer, fixture, model, semantic consumer, formatter,
decoder interface, geometry/anchor/style/color parser or MFC change was needed.

parser_safe remains **false**; typed widths remain **null/unresolved**;
ownership remains **unresolved**, matched_chain remains **null**. Semantic
promotion is not authorized. No new real-corpus contradiction was found.
Unsupported real CParagraphe-without-slot-run negatives, broader layouts,
encoding, full record extent, constant/+08 meanings and ownership remain evidence
gaps. Geometry is scope-only evidence; tested safe clone rejection is not a
global uniqueness or zero false-positive-rate claim.


Date: 2026-09-08. Documentation review only; runtime remains family v1.

## 1. Scope

Decision: **runtime_v2_candidate_replacement_authorized_with_conditions**.
Authorize a future Strategy A candidate-only replacement, subject to the
implementation acceptance conditions below. This document does not implement,
validate or deploy that replacement. Until the conditions pass, retain current
runtime source `CParagraphe_slot_prefix_family_v1`.

The sole authorized destination is `candidate_fields["text_slot_run"]`.
Keep `parser_safe=false`, `confidence=provisional`, `ownership=unresolved`,
`matched_chain=null` and null typed widths. The semantic parser must not consume
this candidate. No semantic text, color/style, visible text, attachment, anchor,
geometry, ownership, model/dataclass, decoder interface or MFC refactor is
authorized. No fallback or dual public families are authorized.

## 2. Evidence Reviewed

- [Family v2 RFC](text_slot_prefix_family_v2_rfc.md), including all eight gates
  and its unresolved possible-family-context obligation.
- [Frozen shadow report](../tests/samples/reports/text/text_slot_family_shadow_comparison.json)
  and [runtime baseline](../tests/samples/reports/text/text_slot_family_shadow_baseline.json).
- [Standalone shadow analyzer](../tools/analyze_text_slot_family_shadow.py),
  [focused tests](../tests/unit/test_text_slot_family_v2_shadow.py) and
  [CLI/regression tests](../tests/integration/test_text_slot_family_shadow_cli.py).
- [Actual v1 extractor](../src/type3_clipboard_codec/parsers/text/text_slot_candidate.py)
  and [parser integration](../src/type3_clipboard_codec/parsers/type3_chain_parser.py).

The 104 real inputs contain 72 text captures and 32 geometry scope controls.
Text coverage includes controlled style 9, prior unsupported styles 5, prior
Phase 1F 24, multiline 4 and multi-object 7; these cohorts overlap and must not
be summed as independent captures. There are 32 separate synthetic challenges,
including six general negatives and three identity-collision/ambiguity controls.
The clone templates have complete 64-byte continuation context in this study;
legacy 32-byte templates would stop at bounds rather than test later layers.

Actual v1 output, structural F4 results and provenance were frozen before intent
labels. No-oracle output differs only in oracle_summary. Adversarial labels and
renamed inputs preserve structural outcomes. Runtime source and all 104 parser,
inspect and preview outputs matched the frozen baseline during shadow work.
That proves shadow isolation, not equality of a future runtime v2 implementation.

Review inspection also found an unclosed mixed-context case (Gate 8). The frozen
report is preserved, including its historical ready_for_review designation;
this review does not reinterpret that designation as completed implementation.

## 3. Shadow Comparison Summary

| Measurement / primary outcome | Count |
| --- | ---: |
| Actual v1 candidates | 62 |
| Independent F4 shadow candidates | 72 |
| Both absent | 32 |
| Both present, same payload/run provenance | 62 |
| v1 absent / v2 present | 10 |
| v1 present / v2 absent | 0 |
| Both present, different run | 0 |
| Real v2 ambiguity | 0 |
| Bounds/resource difference | 0 |
| Other structural disagreement | 0 |

Overlap equality includes structural CParagraphe source, first prefix, ordered
prefix positions, slot count, terminal, count location/window and comparable
code/RGB/raw spans. Equal slot count alone is insufficient. Text, anchor, chain
index and object order are not equivalence selectors.

Raw accounting is 1,184 token hits, 592 full identity **positions**, 72 maximal
recurring/deduplicated **runs**, and 520 suffix positions removed. There are zero
global competitors, real count failures or real terminal failures, and 72 final
successes. Implementation review must preserve these distinct units and separate
identity, recurrence, uniqueness, count and terminal obligations; no score or
success-only accounting may replace them.

## 4. Gain/Loss Closeout

All ten gains support the established finding
**old_family_overconstrained_by_style_fields**. The table records structural
mismatches against compatible legacy identity bytes, followed by post-freeze
style labels; it does not derive a selector from fixture names.

| Exact reviewed fixture | Legacy structural mismatch / later explanation |
| --- | --- |
| text_slotstyle_a8_char4_height20.txt | +0x12 in old height-dependent prefix; one unknown legacy variant |
| text_mirror_on.txt | +0x1B in old width-dependent invariant |
| text_width_50_percent.txt | +0x1A in old width-dependent invariant |
| text_width_150_percent.txt | +0x1A in old width-dependent invariant |
| text_slotstyle_a8_char4_width50.txt | +0x1A in old width-dependent invariant |
| text_slotstyle_a8_char4_width150.txt | +0x1A in old width-dependent invariant |
| text_slant_15deg.txt | +0x1C..+0x1F in old slant-dependent invariant |
| text_slant_custom_30deg.txt | +0x1C..+0x1F in old slant-dependent invariant |
| text_slotstyle_a8_char4_slant_p15.txt | +0x1C..+0x1F in old slant-dependent invariant |
| text_slotstyle_a8_char4_slant_m15.txt | +0x1C..+0x1F in old slant-dependent invariant |

The five controlled changes interrupt the old identity at one prefix; eight
other legacy-valid positions remain in two fragments. Height20 triggers the
old unknown-variant failure; controlled width/slant fragments cannot be ranked
into a winner. The five prior unsupported captures have no old family-valid
positions in the selected F4 run. Thus identity overconstraint explains both
complete rejection and fragmented recurrence, not just a superficial style label.
No gain needs expected text/style/color, chain index, anchor or fallback.

Losses, different-run disagreements, real ambiguities and resource/bounds/other
disagreements are zero; there is no real-corpus loss to rescue. The closeout is
sufficient for this corpus, not a claim about arbitrary future paragraphs.

## 5. Gate 1 — Exact Identity

Result: **pass_with_conditions**.

Accept exactly the following predicate within complete `[p,p+64)` local bounds:

| Prefix-relative range | Required bytes |
| --- | --- |
| +0x00..+0x03 | 05 00 00 00 |
| +0x08 | 00 or 01 only |
| +0x09..+0x0B | 00 00 00 |
| +0x24..+0x2B | 00 00 00 00 00 00 00 00 |
| +0x38..+0x3F | 9A 99 99 99 99 99 D9 BF |

Require one constant raw +08 value throughout the entire run. The 71 observed
00 runs and one 01 run support this conservative enumeration, not a semantic
meaning. Unknown values and within-run switches must abstain, including the
mixed-context obligation in Gate 8. Do not widen or learn values or constrain
additional positive-identity bytes. Both wider regions remain
`structural_constant_candidate`, not confirmed format constants. Exact matching
is acceptable for this provisional experiment despite unresolved semantics.

## 6. Gate 2 — Collision Safety

Result: **pass_with_conditions**.

Known +92 competitors are rejected at identity: 72 runs / 592 positions, zero
accepted. This in-paragraph evidence is stronger than geometry-only controls;
count does not suppress these decoys and +92 is diagnostic only. General
synthetic negatives are 0/6 accepted. Wrong-count clones reach count rejection,
nonzero-terminal clones reach terminal rejection, and two complete clones cause
Policy A ambiguity and key absence. Tested identity collisions fail safely under
the complete candidate contract. F4 is not globally unique and no zero population
false-positive rate is claimed.

Condition: transfer these checks to the actual runtime extractor, preserving
global Policy A before count/terminal approval. Also test valid plus invalid-count
or invalid-terminal competing runs; later validation must not choose the winner.
Mixed unknown contexts require the additional Gate 8 conditions.

## 7. Gate 3 — Shadow Comparison

Result: **pass**.

The independent actual-v1 comparison across 104 real and 32 synthetic inputs
is sufficient for this candidate-only migration step. It includes every required
cohort, comparable raw provenance, full identity accounting and oracle isolation.
Neither the smaller historical positive corpus nor the shadow result alone is
sufficient for semantic promotion or future runtime regression acceptance.

## 8. Gate 4 — Disagreement Closeout

Result: **pass**.

All ten real gains have byte-level explanations under old-family style
overconstraint; all 62 overlaps are the same run. There are no unexplained real
losses, different runs, ambiguities or bounds/resource differences. Strategy A
is selected under the remaining implementation conditions. Any new transition
or different-run result during implementation reopens this gate; do not normalize
it away or rescue it with v1.

## 9. Gate 5 — Regression Equality

Result: **pass_with_conditions**.

Use a pre-migration v1 serialization baseline for all 104 inputs, retaining raw
values, byte representations and ordering. Section 14 defines the only allowed
candidate deltas. For 62 overlaps, assert each allowed delta first, then compare
every other field exactly. For the ten named gains, independently validate the
entire new entry against frozen shadow run/provenance plus the output contract;
only then exclude that one entry from equality against its absent baseline.
The other 32 fixtures must still have no text_slot_run. No unreviewed presence
transition is allowed. Never remove all candidate_fields during normalization.

Across all 104 inputs require unchanged raw_data, source text, visible text,
attachment, active anchor, baseline_midpoint/fallback, candidate anchor fields,
semantic style/color, geometry, ordering, notes, warnings, ownership, matched_chain
and every unrelated candidate_fields entry. No sorting or broad omission of
notes/warnings is allowed. Inspect/preview comparisons may permit only the same
validated text_slot_run metadata/presence delta in candidate displays; semantic
and non-verbose output must be identical. Do not grant whole-output exemptions.

Historical v1 and frozen shadow evidence must remain available. Future tests
whose contract explicitly asserts current v1 metadata may need reviewed updates,
but blanket regeneration of goldens is not an equality proof. Implementation
cannot be declared accepted until the exact comparisons and full suite pass.

## 10. Gate 6 — Bounds/Resources

Result: **pass_with_conditions**.

Accept the complete 64-byte identity and next-prefix requirements. A 64-byte
identity match alone does not establish a complete candidate: the 92-byte raw
inspection span and RGB +0x50..+0x52 require separate bounds. Count requires the
existing first-prefix -16..-1 window, -4 probe, all u8/u16le/u32le diagnostic
views agreeing with independently traversed total, including terminal. Do not
use count as a traversal limit. Keep 204 recurrence and the four-byte zero-code
terminal with a completely bounded next-prefix check. An incomplete probe is
failure, never evidence of prefix absence; preserve partial-token EOF failure.

| Existing experiment cap | Accepted value |
| --- | ---: |
| Eligible CParagraphe payloads | 32 |
| Aggregate payload bytes | 1,048,576 |
| Raw token hits | 4,096 |
| Traversed slots | 256 |
| Signature/probe evaluations | 2 * aggregate_payload_length + 4096 |

These are safety caps, not format constants. Search all eligible structural
payloads without a preferred offset/window; budgets are global and exhaustion
returns no candidate or partial result. No real exhaustion occurred (maximum
23 shadow probes); synthetic exhaustion abstains. Wider bounds intentionally
reject synthetic 32/63-byte continuation contexts that v1 could probe. No real
bounds difference was observed. The formula exceeds naturally reachable probes
under the current scan; test its guard by explicit fault injection rather than
claiming a naturally observed exhaustion. Runtime boundary/cap tests are required.

## 11. Gate 7 — API/Semantic Isolation

Result: **pass_with_conditions**.

The existing dictionary entry can hold the reviewed neutral metadata without
changing models or semantic consumers. Keep provisional confidence, false
parser_safe, null typed widths, unresolved ownership and null matched_chain at
their existing locations. Preserve payload/source offsets, count, stride,
ordinals, terminal flags, raw/numeric code views, RGB bytes and all span domains.
No semantic code path may start reading this candidate. Section 14 is an exact
allowlist; any extra schema/content change requires separate review.

## 12. Gate 8 — Future Unknowns

Result: **pass_with_conditions**; mixed-context behavior is an outstanding
implementation acceptance blocker, not established by the 32-case report.

Review-time read-only helper checks found that `[valid_run, unknown08_run]` and
`[valid_run, changed_constant_run]` each return `status=present` with three
unsupported contexts recorded. The second run uses +08=02, or changes +0x24
to 55 at every prefix, respectively. The current helper records unknown_* probes
but does not globally veto success when one exact F4 root remains. Existing
single-negative tests therefore do not prove fail-closed mixed-input behavior.
No analyzer, report or tests are changed by this review.

For the future runtime, freeze the following **rejection-only** possible-context
recognizer, using the current shadow probe diagnostics. With complete 64-byte
bounds and exact token, define R as the required +09..+0B zeros, A as allowed
+08, and C as both exact wider constants. After excluding a full F4 match:

| Possible unsupported context | Exact condition | Required action |
| --- | --- | --- |
| unknown_plus08 | R and C and not A | Global candidate absence |
| unknown_structural_constant | A and R and not C | Global candidate absence |
| unknown_core | C, with remaining nonmatching core | Global candidate absence |

These conditions add no accepted F4 values or positive signature. Do not label
every arbitrary raw-token mismatch a possible run: complete tokens outside these
conditions remain ordinary identity mismatches, preserving independently rejected
known decoys. Incomplete token/context probes remain global failure. At a required
next-prefix location, incomplete context, any identity/unknown match, or a leading
05 byte must fail conservatively; only a complete mismatch with non-05 leading
byte can establish continuation absence. A 00/01 switch inside a family-valid
run must fail. Do not drop an unsupported context, short competitor or mixed-value
run to manufacture global uniqueness; no new minimum run length is authorized.

Required additional runtime tests combine one valid run with each recognized
unknown context, in the same and separate eligible payloads, in both orders;
also mutate first/interior/last prefixes and the required next-prefix context.
All must abstain where the above rules apply. Verify all 104 real outcomes and
all decoys again under this rejection policy. If any reviewed real success is
lost, reopen Gate 4 instead of broadening F4. Acceptance is conditional on these
tests, not on a claim that the existing helper can be copied unchanged.

## 13. Migration Strategy

Choose **Strategy A**, conditional future replacement within the singular
text_slot_run key. Future source becomes `CParagraphe_slot_prefix_family_v2`.
Strategy B describes the current runtime until implementation acceptance, not
the selected long-term experiment. Strategy C is rejected: no v2-to-v1 or
v1-to-v2 fallback, no dual emission, no hidden family retry.

Global Policy A is unchanged: zero structural runs means absence; one proceeds
to independent validation; more than one means absence before count/terminal
ranking. Deduplicate only suffixes of the same 204-periodic run. Count-based
ranking, nearest/first run, chain index, expected text, anchor, style/color oracle
and v1 fallback are explicitly rejected. Unknown-context abstention is an
additional failure obligation, not a competing-run scoring scheme.

## 14. Candidate Metadata Compatibility

Choose **option A: neutral F4 metadata**. Remove legacy prefix_variant at both
run and slot levels. Do not reinterpret v0/v1/v2 or retain them as structural
variants. Add run-level `prefix_family="F4"` and `plus08_value`, a Python/JSON
integer 0 or 1 representing the directly observed raw byte. It has no semantic
flag name and does not resolve any candidate typed width. Do not add per-slot
replacement metadata; each slot's raw provenance retains its byte and tests must
assert it equals the run-level value.

Let R denote candidate_fields["text_slot_run"]. This is the exhaustive overlap
allowlist; wildcard i means every existing slot ordinal, without reordering:

| Exact path | Required intentional difference |
| --- | --- |
| R.source | CParagraphe_slot_prefix_family_v1 -> CParagraphe_slot_prefix_family_v2 |
| R.prefix_variant | Remove; baseline value must be a legacy v0/v1/v2 observation |
| R.slots[i].prefix_variant | Remove; baseline value must be a legacy v0/v1/v2 observation |
| R.prefix_family | Add exactly the string F4 |
| R.plus08_value | Add exactly raw prefix +08 as integer 0 or 1, constant over all slots |

For the ten named gains only, add the entire validated R with these v2 metadata
rules. For the 62 overlaps, everything else remains exactly equal, including
raw code/RGB spans and count provenance. No other candidate presence/content
difference is allowed. The remaining 32 inputs keep R absent. The public key
does not change; no legacy-diagnostic companion candidate is authorized.

## 15. Required Implementation Tests

Documented requirements only; none is implemented in this review:

1. All 62 overlaps reproduce the same selected payload/run, positions, terminal,
   count provenance and code/RGB/raw spans under the exact metadata allowlist.
2. All ten named gains appear, independently matching frozen shadow provenance.
3. No unreviewed presence transitions; all 32 other real inputs remain absent.
4. Zero losses or different-run disagreements; preserve every unexpected result.
5. Global Policy A within/across payloads, suffix deduplication, and valid plus
   wrong-count/bad-terminal competitors before later validation can rank them.
6. +08=00 and 01 positives, unknown-value failures and within-run switches.
7. Single/multiple-byte mutations in both structural-constant regions, including
   mixed valid/unsupported payloads and first/interior/last prefix mutations.
8. All 72 known +92 decoy runs remain rejected at identity, independently of count.
9. All six general synthetic negatives remain candidate-absent.
10. Wrong-count identity clone passes identity/recurrence then fails count.
11. Nonzero-terminal identity clone fails terminal with complete context.
12. Two complete valid cloned runs produce ambiguity/key absence.
13. Exact 64-byte identity boundary passes identity without implying RGB/run success.
14. Incomplete 63-byte identity and token fragments fail conservatively.
15. Incomplete next-prefix probes never become absence; complete supported and
    unsupported next-context probes and separate RGB/raw-span bounds are tested.
16. All five reviewed caps, aggregate scope, boundary behavior, exhaustion without
    partial success, and probe-budget guard fault injection without changing caps.
17. All 104 real semantic serializations match outside the exact R allowlist;
    retain unrelated candidates, raw_data, notes/warnings and ordering.
18. Inspect/preview change only in validated candidate displays under that allowlist.
19. No fallback or dual family emission, including every failure/ambiguity path.
20. No model/dataclass or semantic consumer changes; verify null typed widths,
    unresolved ownership, null matched_chain and parser_safe=false.
21. Full PYTHONPATH=src pytest, targeted runtime tests and git diff --check pass;
    preserve historical evidence while explicitly reviewing version-specific tests.
22. Gate 8 mixed-context veto for every unknown diagnostic category, same/separate
    payloads and reversed order; no manufactured uniqueness or mask widening.
23. Oracle-disabled, renamed-input and adversarial-intent selection invariance.

## 16. Remaining Evidence Gaps

Geometry fixtures have no eligible CParagraphe payload and test scope only. A
real unsupported CParagraphe-without-slot-run corpus remains missing. Decision:
this gap **blocks semantic production promotion**, but does **not independently
block this conservative candidate-only experiment**, given in-domain decoys,
clone checks, fail-closed conditions and mandatory false parser_safe.

+08 meaning, wider-constant meaning, typed count/code/color widths, full record
extent, non-ASCII encoding, ownership, chain/object mapping and broader versions
remain unresolved. They block semantic promotion, not this bounded candidate
replacement. Exact constants may be defaults or layout/version-dependent fields;
their semantic correctness is not established by mutation rejection.

Outstanding implementation blockers are the Gate 8 mixed-context veto/tests,
actual runtime transfer of bounds/collision policies, and exact allowlist-based
104-real/API/inspect/preview regression. A complete single cloned run may satisfy
the candidate contract: this review does not establish authenticity or ownership.
Any unexpected loss or new output delta must return for review, not be waived.

## 17. Final Authorization Decision

**runtime_v2_candidate_replacement_authorized_with_conditions**

| Gate | Result |
| --- | --- |
| 1. Exact identity | pass_with_conditions |
| 2. Collision safety | pass_with_conditions |
| 3. Shadow comparison | pass |
| 4. Disagreement closeout | pass |
| 5. Regression equality | pass_with_conditions |
| 6. Bounds/resources | pass_with_conditions |
| 7. API/semantic isolation | pass_with_conditions |
| 8. Future unknowns | pass_with_conditions |

Authorization is limited to implementing and validating the reviewed candidate-only
Strategy A replacement. Conditions are concrete acceptance obligations, not claims
that runtime v2 already passes. No unconditional replacement acceptance or semantic
promotion follows from this decision. This turn changes only this review and four
linked status documents; runtime, extractor, analyzer, fixtures, models and tests
remain unchanged. Historical v1/shadow results below linked status notices retain
their original dates and authorization scopes.

Documentation-only validation: `PYTHONPATH=src pytest -q` via the project venv
completed with **784 passed in 49.78s**, preserving the baseline. `git diff --check`
passes. `git diff --exit-code -- src tools tests` confirms no runtime, analyzer,
fixture or test changes. This validates review isolation; it does not discharge
future implementation conditions.
