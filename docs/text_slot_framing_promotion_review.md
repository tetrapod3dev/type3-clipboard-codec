# CParagraphe Text-Slot Framing Promotion Gate Review

Review date: 2026-09-07. This is a documentation-only review of the six gates in
the [candidate framing RFC](text_slot_framing_rfc.md). No parser, decoder, model,
analyzer, fixture or test implementation is included in this change.

## 1. Scope

The decision concerns a **future candidate-only experiment**, limited to adding
`candidate_fields["text_slot_run"]` after existing parsing has completed. It does
not approve production semantic decoding or declare the candidate parser-safe.
The final decision and its conditions appear in section 13.

This review supersedes the RFC's pre-review authorization status only within that
narrow scope. Its descriptive grammar, unresolved typed widths, closed reference
family and non-goals remain in force. Work outside the conditions requires another
review; this turn performs no implementation.

## 2. Current Evidence

The [Phase 1F evidence](text_color_decode_rfc.md) records 24 runs / 207 slots,
204-byte recurrence, count candidate at prefix -4, and agreement with total slots
including terminal in 24/24 runs. The family has 20 invariant bytes and exactly
three observed joint variants. Code is a candidate at +4; RGB bytes are candidates
at +0x50..+0x52. Four multiline and seven multi-object controls are structurally
compatible. Typed count/code/color widths and ownership remain unresolved.

The raw periodic token alone has a competing sequence in each fixture. The
analyzers' count/context experiments are research evidence, not automatically the
future parser's selection policy. Later Phase 1F negative controls already preserve
ambiguity between multiple family-valid runs; this review makes that policy explicit.

Current architecture supports a candidate-only extension without new model fields:

| Inspected source | Relevant finding |
| --- | --- |
| [ParsedObject](../src/type3_clipboard_codec/models/parsed_object.py) | Existing `candidate_fields: Dict[str, Any]` and lossless `raw_data` storage |
| [GeometryObject](../src/type3_clipboard_codec/models/geometry.py) | Inherits the candidate container from `ParsedObject` |
| [Type3ChainParser](../src/type3_clipboard_codec/parsers/type3_chain_parser.py) | Builds a candidate dictionary and preserves `full_data` in `raw_data` |
| [Inspect formatters](../src/type3_clipboard_codec/inspect/formatters.py) | Copies candidate fields through `_json_safe`; bytes/dicts/lists are already handled |
| [Preview](../src/type3_clipboard_codec/codec/preview.py) | Verbose output displays the candidate dictionary; the new entry can intentionally appear there |
| [Existing candidate tests](../tests/integration/test_text_cproperty_anchor_candidates.py) | Demonstrate provisional dictionaries with unresolved ownership and null `matched_chain`, without making them ownership oracles |

These observations establish API feasibility, not proof that an unwritten
implementation preserves behavior. Gate 5's future regression obligations remain
mandatory. The current test baseline is 428 passing tests.

## 3. Competing-Run Policy Decision

**Choose Policy A — validation-only count.** Count never resolves ambiguity.

1. Identify maximal runs using the exact prefix family and independently observed
   recurrence. Do not use count, terminal value, text or color to choose between runs.
2. Deduplicate suffixes of the same periodic run; they are not separate run starts.
3. If more than one family-valid run remains, return unresolved even when exactly
   one count agrees, another count is corrupt, or only one has a plausible terminal.
4. Validate count and terminal only after the run is structurally unique.

For the singular `text_slot_run` key, uniqueness applies across all structurally
identified CParagraphe payloads in the parsed input, not separately per chain or
object. Multiple runs in one payload or across payloads cannot be resolved by node
ordinal, class proximity, final chain index or selection order.

Policy B could exploit a count-consistent candidate among competitors, but it
couples selection to an untyped header view and may hide a real second run. There
is no compelling need for that risk in the first candidate experiment. A weak
periodic token that fails the bounded family predicate is not a competing
family-valid run; its rejection must not depend on count. Unknown family-like
variants must cause safe abstention, not be discarded to manufacture uniqueness.

## 4. Gate 1 Review — Prefix Selector and Search Bounds

**Result: pass_with_conditions.**

Use only the RFC's exact three joint variants and invariant core. Do not accept
independent wildcard combinations. Unknown combinations or unsupported within-run
variant changes are unresolved. `05` alone is not a family predicate.

The first experiment may perform a bounded, targeted family search over the
already identified payloads. It must consider the complete eligible payload
range before declaring uniqueness; finding one run inside the historical analyzer
window is insufficient. This is one bounded signature search, not arbitrary
field-width/offset brute force or a new clipboard/MFC scanner.

The following are **experiment resource limits**, not Type3 format constants:

| Resource | Initial condition |
| --- | --- |
| CParagraphe payloads | At most 32 per parsed input |
| Aggregate CParagraphe bytes considered | At most 1,048,576 bytes |
| Raw prefix-token hits considered | At most 4,096 across the input |
| Traversed slots | At most 256 across the experiment |
| Bounded signature/probe evaluations | At most `2 * aggregate_payload_length + 4096` |

For a payload of length `L`, inspect only positions with the required bytes inside
`[0, L)`. The 32-byte family predicate defines the last complete signature origin
as `L - 32`; a short or incomplete family-like probe must not count as absence.
Count context needs 16 bytes before the selected first prefix. The first experiment
uses a 92-byte local inspection span to retain the known prefix/code/color context;
that span is not a record-width claim.

For prefix position `p`, the available traversal budget is bounded by both remaining
global resources and:

```text
min(256, max(0, 1 + floor((L - p - 92) / 204)))
```

This bound comes from available bytes and a safety maximum, never from the count
candidate. Validate each step and the required following-prefix probe separately.
Use visited prefix positions or equivalent accounting to avoid repeatedly walking
the same suffixes. Exhausting a budget means unresolved, not a truncated success.
If aggregate input exceeds a cap, omit the candidate instead of scanning a selected
prefix of the input and claiming uniqueness there.

The analyzer's `[128,768)` and 24-slot cap must not become format assumptions.
Starts 47/310/378 and a +68 multiline correction are prohibited selectors. The new
resource limits allow shifted candidate locations, but do not validate >255 count
encoding: numeric-view agreement may still reject such inputs. Cap changes need
documented review and boundary/resource tests; they must not widen the family.

The wider targeted search is a future implementation obligation, not newly
validated evidence from this documentation review. If it reveals additional runs
in current fixtures, preserve Policy A and investigate; do not retreat to the
historical window or use count to force the old answer.

## 5. Gate 2 Review — Count Without Typed Width

**Result: pass_with_conditions.**

After unique structural traversal, preserve the preceding window and calculate
the existing candidate views at prefix -4: u8, u16le and u32le. A successful
`count_candidate` may expose the validated total only when **all three numeric
views agree with each other and with independently traversed total slots**.

Keep typed width null. The view names describe diagnostic reads, not storage types.
Do not select a matching subset of views, choose a preferred integer width, use
alignment as evidence, or correct a conflicting count. Zero, unavailable or
conflicting views cause unresolved. Count must include the validated final zero
terminal; code 13 and internal zero positions remain traversed slots.

Count must not select a run under Policy A, allocate a slot array before traversal,
set an unbounded loop limit, or supply missing slots. An agreed count without a
structural terminal is insufficient. Unresolved typed width is acceptable for
this raw, provisional candidate experiment because agreement is explicitly checked
and does not alter existing semantic outputs.

## 6. Gate 3 Review — Raw Count Provenance

**Result: pass.** The mandatory output requirements are defined as follows:

| Entry within `count_candidate` | Requirement |
| --- | --- |
| `raw_window` | Exact bytes at prefix -16..-1, without normalization |
| `window_relative_start` | -16 |
| `probe_relative_offset` | -4 |
| `numeric_views` | All u8/u16le/u32le values and their widths/relative offsets |
| `validated_total_slot_count` | Independently traversed total, exposed only after agreement and terminal validation |
| `typed_width` | null |
| `confidence` | `provisional` |
| Source provenance | Runtime descriptor position, payload source span, and discovered prefix position kept distinct |

Retain the complete original CParagraphe bytes through verified, lossless references
into the existing `raw_data`, or an equally lossless bounded representation. Raw
span references must name their buffer and coordinate domain and reconstruct the
exact bytes in tests. They do not require a new model class. Absolute source
positions are diagnostics only and must not influence selection.

Conflicting views mean no successful slot-run candidate, even if raw evidence can
be inspected privately. Never report a guessed numeric count as validated.

## 7. Gate 4 Review — Failure and Fallback Behavior

**Result: pass_with_conditions. API decision: absence on failure.**

For this first experiment, unsuccessful extraction means
`candidate_fields["text_slot_run"]` is **absent**. Do not put an unresolved object,
null placeholder, empty successful run or partially populated candidate under that
key. Do not introduce a second public diagnostics key. The current generic
dictionary permits diagnostics, but does not establish a uniform unresolved-run
API convention, so adding one is unnecessary for this experiment.

An internal bounded diagnostic result may support implementation tests, but must
not mutate existing notes, warnings, text notes, candidate entries or parser
fallbacks. Existing full raw input remains available on failure. Construct the
new dictionary locally and attach it only after all checks succeed.

For the zero-terminal test, require the existing four-byte code candidate view
at prefix +4 to be all zero; a zero low byte with nonzero remaining candidate
bytes is not sufficient. This is a conservative diagnostic predicate, not a
promotion of the slot-code typed width. Prefix recurrence must still end.

| Failure/condition | Required behavior |
| --- | --- |
| Multiple family-valid runs | Absent key under Policy A, irrespective of counts or terminal plausibility |
| Unknown joint variant or family-like unknown prefix | Absent key; preserve raw, never broaden masks |
| Bare periodic `05` token failing the family outside a run | Not a valid run; cannot be accepted using a matching count |
| Unknown/slot-like context at an expected next slot | Absent key; do not treat it as a convenient run end |
| Unsupported within-run variant switch | Absent key |
| Count/run mismatch or conflicting numeric views | Absent key; no width selection or count correction |
| Missing/zero count or missing final terminal | Absent key |
| Valid prefix after the position claimed final by count | Absent key; no trimming, count inflation or partial output |
| Internal zero with another valid prefix | Continue bounded traversal; do not prematurely mark a terminal |
| Missing next-prefix probe bytes or other insufficient bounds | Absent key; untested is not absent |
| Unknown multiline variant | Absent key with original bytes preserved |
| Incomplete scan or resource exhaustion | Absent key; no success based on an unexamined suffix |

Unknown variant here includes a family-core match with an unobserved variant
vector. Unrelated bytes elsewhere are not automatically unknown slots. At expected
run continuation positions, token-like but unsupported context is conservative
failure. Checked bounds must precede every read. Expected malformed/unsupported
input must not throw through to change existing successful parser results; handle
such failures explicitly, without blanket exception suppression hiding bugs.

## 8. Gate 5 Review — Regression Isolation

**Result: pass_with_conditions.** Architecture permits isolation; future regression
proof is a condition, not something the current 428 tests can establish for code
that has not been written.

The candidate helper must be read-only with respect to existing nodes, chains,
styles and raw buffers. Invoke it after the existing semantic pipeline and attach
only the new dictionary entry after success. No current stage may consume it to
change text, anchor, color, geometry, ordering, attachment or fallback.

Compare the future result against the pre-experiment baseline after removing
**only** the new `text_slot_run` entry. All other fields and existing candidate
entries must remain equal, including `raw_data`, source text, visible text, text
anchor, `baseline_midpoint` behavior, `matched_chain`, notes/warnings, ownership,
chain ordering, attachment and geometry. Do not ignore the whole candidate
dictionary or sort away an ordering regression.

The current [behavior snapshots](../tests/integration/test_parser_behavior_snapshot.py)
are useful but not sufficient by themselves. Retain their assertions and add
candidate-specific checks. Any normalized snapshot comparison must remove only
the intentional new entry, and any golden update must explicitly account for that
addition rather than regenerate unrelated baselines.

Because inspect JSON and verbose preview already render the dictionary, their
candidate-only display addition is expected on success. This is the sole allowed
presentation delta; ordinary text/color/geometry sections and non-verbose behavior
must stay unchanged. No formatter or preview redesign is needed or authorized.

## 9. Gate 6 Review — candidate_fields-only API

**Result: pass_with_conditions.** Existing parser-local dictionaries are sufficient.
No production model/dataclass/schema additions are allowed in the first experiment.

Use `candidate_fields["text_slot_run"]` only on success, with these constraints:

| Property | Required value/meaning |
| --- | --- |
| `source` | `CParagraphe_slot_prefix_family_v1` |
| `confidence` | `provisional` |
| `parser_safe` | false |
| `count_candidate` | Raw/provenance-bearing structure defined by Gate 3 |
| `stride` | 204, a candidate prefix period |
| `prefix_variant` | Exact observed variant identifier, not a semantic type |
| `slots` | Actual validated traversal only, with local ordinals |
| `slot_code_candidate` | Provisional numeric view with raw bytes and null typed width |
| `rgb_bytes_candidate` | Three raw bytes at +0x50..+0x52, with null typed width |
| `terminal_candidate` | Structural final-zero-plus-prefix-end result |
| Ownership, at run and slot scope where represented | `unresolved` |
| `matched_chain` | null; no chain index or inferred match |
| Count/code/color typed widths | null |
| Raw evidence | Exact count/code bytes and bounded slot/payload span provenance |

Use plain dictionaries/lists and existing JSON-safe scalar/byte conventions.
Retain raw spans without duplicating the full payload per slot. Do not create new
model classes, semantic properties, decoder dispatch, public parsing modes or
serialization adapters. If the implementation discovers it cannot fit the existing
container and serializer without such changes, stop and seek a revised review.

This review refines the RFC's illustrative numeric `count` into `count_candidate`
with a provisional validated total. Use `count_candidate`, `slot_code_candidate`,
`rgb_bytes_candidate` and `terminal_candidate`; do not introduce `character`,
`char_code`, `text_color` or `record_count` as confirmed semantic names. Existing
unrelated fields with those kinds of names must remain unchanged, not be renamed.

## 10. Required Implementation Constraints

- Policy A, closed exact variants, independent traversal and unanimous count-view
  agreement are non-negotiable for the first experiment.
- Resource bounds derive from payload length and the documented safety maxima;
  historical analyzer windows and starts are never format rules.
- Failure is candidate-key absence, with existing raw input and parser output
  preserved. Success is one provisional dictionary addition only.
- No expected text/color, fixture-name semantics, intent metadata, anchor equality,
  final chain index or absolute clipboard offset may guide candidate decisions.
- No production visible-text replacement, color promotion, semantic model change,
  object/chain mapping, ownership assignment, anchor change or order inference.
- No import of repository `tools` analyzers into runtime parsing; a future small
  internal helper may reuse reviewed evidence as constants/predicates, not an
  analyzer report pipeline or oracle loader.
- MFC remains `mfc_runtimeclass_framing_supported_but_writeobject_unclear`. Use the
  current structurally identified CParagraphe payload. No archive decoder, PID
  reinterpretation or MFC refactor is required or authorized. The
  [MFC conclusion](typeeditzone_mfc_archive_investigation.md) and anchor closeout stand.

## 11. Required Tests

These are obligations for a future implementation change; no tests are added in
this documentation review.

1. Pre-experiment parser results equal candidate-enabled results after excluding
   only the new key. Cover all existing fields/candidate keys and exact raw bytes.
2. Successful output adds only the candidate dictionary with required provisional
   metadata, null typed widths, unresolved ownership and null `matched_chain`.
3. Existing fixture snapshots remain unchanged or explicitly exclude only the new
   candidate entry; inspect/verbose-preview differences are limited to that entry.
4. Unknown core-like variants, an unobserved combination of variant bytes, weak
   periodic filler and within-run unknown variants omit the candidate safely.
5. Two family-valid runs obey Policy A even when only one count agrees. Include
   competing runs beyond [128,768) and across distinct CParagraphe payloads.
6. Wrong count, zero/missing count and conflicting u8/u16le/u32le views fail without
   count-driven allocation. A matching narrow view cannot override a wider conflict.
7. Missing terminal, extra prefix after declared final slot, internal zero followed
   by a valid prefix, and incomplete next-prefix probes follow Gate 4 exactly.
8. Current four multiline fixtures produce candidate-only output, with code 13
   counted, without fixed shifts or visible-text changes.
9. Current seven multi-object controls produce candidate-only output without
   ownership, chain mapping, order changes or modified anchor attachment.
10. Shifted payload/descriptor positions, including starts outside the research
    window, are handled structurally. Test uniqueness across the full bounded scan.
11. Test each safety cap, truncated count/signature/color context and bounded
    traversal complexity. Cap exhaustion must not produce partial success.
12. Reconstruct count/payload/slot raw spans exactly from their provenance. Verify
    code/color mutations cannot select a competing run through an oracle-like score.
13. Run the full pytest suite and all prior anchor/color/geometry regression tests.
    The baseline is 428 passing tests; new candidate tests must add coverage rather
    than weaken those assertions.

Unexpected new candidates or contradictions found by the larger bounded search
must be investigated under Policy A. Do not silently relax the policy, family,
counts or fixture expectations to make these tests pass.

## 12. Remaining Blockers

Typed count/code/color widths, general prefix-variant semantics, non-ASCII encoding,
broader layout/version coverage, full slot extent and ownership remain unresolved.
They block semantic promotion and a production parser, but not a raw provisional
experiment obeying this review.

Future implementation still owes regression, bounds and API-isolation proof.
The targeted whole-payload search within resource limits must be validated against
current and synthetic inputs; the legacy-window evidence alone is insufficient.
These are conditions of the limited approval, not claims that tests already exist.

If isolation requires model/schema changes, a broader family, count-driven
disambiguation, or altered current behavior, this approval no longer covers the
proposal. Return for review instead of treating those changes as implementation
details. No unresolved public diagnostics API is authorized for the first version.

## 13. Final Authorization Decision

**candidate_implementation_authorized_with_conditions**

The six gate results are: Gate 1 `pass_with_conditions`; Gate 2
`pass_with_conditions`; Gate 3 `pass`; Gate 4 `pass_with_conditions`; Gate 5
`pass_with_conditions`; Gate 6 `pass_with_conditions`.

Authorization applies only to a **future candidate_fields-only experiment** under
Policy A, absence-on-failure, closed variants, raw/untyped count agreement, bounded
structural traversal, existing-model compatibility and the required tests above.
The implementation change may be undertaken under these conditions, but is not
considered validated until those tests pass. `parser_safe=false` remains mandatory.

This does not authorize semantic model promotion, visible-text replacement, typed
color decoding promotion, ownership, anchor changes, MFC refactoring or a new
model/dataclass. This review turn remains documentation-only.

Review validation command:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m pytest -q
```

Documentation-review validation: **428 passed** with `PYTHONPATH=src`, preserving
the current baseline. The 13 sections, local links, single authorization decision
and whitespace checks passed. No new tests or implementation files are part of
this review. These results do not discharge the future Gate 5 regression conditions.
