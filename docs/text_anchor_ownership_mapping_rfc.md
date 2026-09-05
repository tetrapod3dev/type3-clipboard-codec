# Text Anchor Ownership Mapping RFC

Status: Phase 2A investigation complete. Parser ownership implementation deferred.
Date: 2026-09-06
Scope: Anchor ownership investigation closeout, including shadow mapping and source-linkage analysis; ownership is not solved.

Phase 2 active ownership implementation is deferred until independent structural
or semantic evidence establishes a parser-safe link. The next text
reverse-engineering track is color ownership; that handoff does not promote any
anchor ownership hypothesis. Earlier investigation plans below are retained as
evidence history, not active implementation work.

Related: [candidate decode RFC](text_cproperty_anchor_decode_rfc.md),
[text reverse engineering](text_reverse_engineering.md),
[text object evidence](text_object_reverse_engineering.md), and
[fixture metadata schema](../tests/samples/README.md#multi-object-intent-order-metadata-schema-v1).

## 1. Problem Statement

For N multi-text parser chains in the current fixture set, visible text candidates
appear separable per chain, one direct anchor is observed in `CParagraphe`, and
N-1 anchor candidates are observed in `CPropertyExtend`. The latter candidates
have no assigned chain ownership. Candidate extraction does not establish which
text object owns an anchor.

The goal is to determine whether a parser-safe chain mapping rule exists.
Three ownership layers must be assessed independently:

| Layer | Relationship under investigation | Current evidence limit |
|---|---|---|
| Text identity ownership | Visible text candidate/run to parser chain | Stable observations in this set; provisional, not a confirmed object identity rule |
| CParagraphe direct-anchor ownership | Direct triple to a chain/object | Analyzer anchor matches; no general structural owner rule |
| CPropertyExtend candidate ownership | Each decoded candidate to a chain/object | Candidate-only evidence; unresolved |

Neither text identity nor an anchor match proves the other layer. Repeated text
can identify multiple objects; equal coordinates can match multiple chains.
Even a unique match in a fixture is not proof of structural ownership.

## 2. Terminology

| Term | Definition |
|---|---|
| `parser_chain_order` | Sequence of chains emitted by the current parser; an observed output order |
| `parser_chain_index` | Zero-based position in that sequence, not a persistent object identifier |
| `visible_text_identity` | Candidate text/run associated with a chain, with provenance and provisional confidence; string equality alone is not unique object identity |
| `attempted_selection_order` | User-attempted or user-observed selection sequence recorded in fixture intent; may be explicitly unknown |
| `actual_stored_order` | Semantic ordering of objects in the payload, which remains unresolved |
| `CParagraphe_direct_anchor` | Direct coordinate triple decoded from the CParagraphe payload, distinct from identifying its owner |
| `CPropertyExtend_anchor_candidate` | Provisional coordinate triple extracted from a local CObDao signature, without an assigned chain |
| `ownership` | Supported relationship between an anchor/text record and a particular chain/object |
| `analyzer_match` | Diagnostic correspondence, possibly using fixture expectations or anchor equality; not a parser rule |
| `parser_safe_match` | Match derived independently from payload structure/parser evidence, satisfying Section 5 and failing to unresolved when ambiguous |

Treat `attempted_selection_order != parser_chain_order != actual_stored_order`
as a separation of concepts: some sequences may coincide, but no equivalence is
assumed unless independently proven. Local byte/section order is observable;
calling it semantic stored object order requires additional evidence.

## 3. Current Evidence

### Fixture and metadata coverage

The fixture set is the 13 targets of
[`analyze_text_visible_ownership.py`](../tools/analyze_text_visible_ownership.py).
The current analyzer was rerun for this RFC:

| Metric | Result |
|---|---:|
| Total fixtures / schema v1 YAML metadata | 13 / 13 |
| Missing metadata | 0 |
| Attempted order | 9 |
| Unknown order | 4 |
| Controlled-observed order | 0 |

`warnings`, `missing_fixtures`, and `missing_intent_files` are empty.
All actual stored orders are `unresolved`. Controlled content/style/color
variations must not be confused with a controlled-observed selection order:
none of the 13 fixtures has that order status.

### Visible text and CParagraphe direct anchor

The following table summarizes analyzer observations. A/B/C refer to intent
labels in the ordinary three-object fixtures (`abcdefg`, `1234567890`, `XYZ`).
“Direct-anchor match” means equality against current parser chain anchors,
not a structurally established owner. No expected coordinates are parser selectors.

| Fixture family | Attempted order | Parser text order | Direct-anchor analyzer match |
|---|---|---|---|
| Two grouped, same/mixed color | Unknown | `abcdefg`, `1234567890` | chain0 / `abcdefg` |
| Two not grouped, same/mixed color | Unknown | `abcdefg`, `1234567890` | chain1 / `1234567890` |
| Two not grouped, reversed selection | B-A attempted | `abcdefg`, `1234567890` | chain0 / `abcdefg` |
| Three grouped ABC | A-B-C attempted | A, B, C | chain0 / A |
| Three grouped CBA | C-B-A attempted | A, B, C | chain2 / C |
| Three not grouped, same/mixed color | A-B-C attempted | A, B, C | chain2 / C |
| Three grouped ABC, mixed color / height 30mm / Arial Bold | A-B-C attempted | A, B, C | chain0 / A |
| Three grouped ABC, content variation | `HELLO`, `9876543210`, `Type3` | `Type3`, `9876543210`, `HELLO` | chain0 / `Type3` |

Chain-level text candidates appear consistently separable across these fixtures;
confidence remains provisional. The base grouped ABC/CBA pair matches the text
corresponding to the attempted first object while the parser text order remains
unchanged. This is an observation, not a first-selected-object rule. Not-grouped
samples show different matches, so grouping effects remain provisional.

The content-variation fixture is especially important: the direct anchor matches
chain0, whose visible text is `Type3`, while attempted first text is `HELLO`.
Its direct coordinate also corresponds to the recorded A position. Those facts
must remain separate; coordinate ownership labels cannot be used to silently
relabel chain0's visible text or to claim text/anchor ownership is solved.

### CPropertyExtend anchors

Phase 1 exposes `candidate_fields["cproperty_anchor_candidates"]` with
`source = CPropertyExtend_CObDao_signature_v1`, `confidence = provisional`,
`ownership = unresolved`, and `matched_chain = None`.

All five two-object fixtures have one candidate; all eight three-object fixtures
have two. The N-1 count and signature v1 are stable in current controlled
content/style/color and grouping/order comparisons. Neither is a generic proof
for arbitrary N, additional sessions, or alternate record formats.

Earlier section audits report grouped/not-grouped CObDao section counts of 5/6
for two objects and 9/11 for three. Reported anchor-match sequences include
chain1,chain2 for grouped ABC and chain1,chain0 for grouped CBA/not-grouped ABC.
These are analyzer labels from earlier audits; the visible analyzer does not
independently establish candidate record traversal order. The future experiment
must record node/section provenance before treating such lists as payload order.

## 4. Candidate Ownership Strategies

| Strategy | Evidence for / benefit | Evidence against / unresolved dependency | Status |
|---|---|---|---|
| A. Baseline/anchor equality | Can identify expected correspondences in current fixtures | Circular if existing/expected anchors select the chain; overlapping anchors can be ambiguous; text and anchor identities can diverge | Validation oracle only; prohibited parser selector |
| B. Parser chain order pairing | N-1 candidates suggest pairing with remaining chains after excluding a CParagraphe owner; grouped ABC is compatible with ascending pairing | CParagraphe owner itself lacks a structural rule; CBA and not-grouped audit sequences challenge unconditional ascending pairing; two-object cases cannot discriminate permutations | Provisional hypothesis only |
| C. Attempted selection order | Base grouped ABC/CBA owner movement correlates with attempted first object | Four orders are unknown; not-grouped/content variation do not support a universal rule; parser cannot access capture intent | Analyzer evidence only |
| D. CPropertyExtend section/payload order | Node and section traversal are payload-local and could supply a generic ordering | Grouping changes section counts; list order needs explicit provenance; semantic order and inter-session stability are unknown | Important future investigation target; potentially parser-safe if independently proven |
| E. Structural linkage | Direct local links could identify owners without coordinate expectations | No established object identifier/index/linkage semantics yet; coincidental adjacency or constant fields are insufficient | Preferred if evidence emerges |

Evaluate each strategy independently, including unsupported and contradictory
cases. Strategy B must not borrow an oracle-derived CParagraphe owner and then
claim the whole mapping is parser-safe. If a structural owner is unavailable,
report the strategy as blocked or enumerate conditional owner hypotheses; any
oracle-conditioned result belongs only in the oracle comparison.

For D, define traversal explicitly as node traversal plus section ordinal within
that node, and distinguish all sections from signature-matching sections. Never
sort candidates by expected coordinates or expected chain indices before testing.
For E, investigate record adjacency, object identifiers, repeated indices, section
linkage, node-relative ordinals, and shared local metadata. A relative offset may
locate a field inside a validated record; an unexplained offset or ordinal alone
does not prove a chain link. Conflicting strategies must not be resolved by voting
or by selecting whichever agrees with fixture truth.

## 5. Parser-Safe Requirements

Any future ownership rule must:

- Use structural payload information and parser output with explicit provenance.
- Never use fixture filenames, intent YAML, expected UI anchor values, or baseline
  equality as selectors. Parser-produced baseline coordinates are not a loophole.
- Never use absolute file offsets or assume attempted selection order is stored order.
- Handle N-object text generically, including ambiguous CParagraphe ownership,
  repeated text, coincident anchors, and missing/extra candidate records.
- Validate local boundaries/linkage before consuming a record or ordinal.
- Fail safely to unresolved when evidence is missing, non-unique, or conflicting;
  N-1 candidate count alone cannot force a one-to-one assignment.
- Preserve every candidate and raw/provenance evidence without rewriting active
  anchors or hiding unmatched candidates.

A strategy accepting only payload inputs is eligible for evaluation, not
automatically parser-safe. It needs independent validation and review before any
parser promotion. Both the CParagraphe-owner dependency and CPropertyExtend mapping
must meet these requirements end to end.

## 6. Phase 2A Design and Implementation

The analyzer implements shadow mapping without assigning ownership, with two
isolated stages:

1. Compute structural hypotheses from immutable parser/payload evidence. Inputs
   exclude filenames, intent, expected coordinates, and oracle owner indices.
   Retain possible chain sets, local provenance, unmet dependencies, and reasons.
2. Independently construct diagnostic oracles and compare frozen hypotheses with
   them. Intent expectations and baseline equality are separate oracle sources;
   baseline agreement is consistency checking, not independent truth. Record the
   source, tolerance, availability, ambiguity, and contradictions for each oracle.

Fixture names may label report rows and select the fixed input inventory, but
must not branch strategy logic. Intent can stratify reporting by grouping/order
only after structural results exist. Unknown attempted-order fixtures still run
all payload-only strategies; missing oracle information yields `unavailable`,
never an inferred attempted order or a successful match.

Original illustrative report shape (not an actual fixture result; the implemented
tool separates fixture-level `structural_hypotheses` and `oracle_results`):

```json
{
  "shadow_anchor_mapping_candidates": [
    {
      "cproperty_candidate_index": 0,
      "candidate_anchor": [211.111, 322.222, 0.0],
      "possible_chain_indices": [0, 1, 2],
      "strategy_results": {
        "chain_order_excluding_cpar": {
          "status": "blocked",
          "reason": "no structural CParagraphe owner"
        },
        "payload_order": {"status": "unresolved"},
        "structural_linkage": {"status": "no_link_found"}
      },
      "expected_match_from_fixture_oracle": {
        "status": "unavailable",
        "chain_indices": [],
        "source": null
      },
      "parser_safe": false
    }
  ]
}
```

These are separate analyzer records, not additions to or mutations of parser
candidates. `possible_chain_indices` is a hypothesis set, not an assignment.
Include candidate node/section provenance in the output; do not
represent absent strategy evidence as an empty, successfully matched chain set.
Keep `parser_safe: false` throughout Phase 2A, even when an oracle agrees.

### Implemented experiment

Run `python tools/analyze_text_anchor_shadow_mapping.py` for a small text report,
add `--json` for compact JSON, or use `--json --no-oracle` to skip intent loading
and disable anchor equality. The tool reuses the 13-fixture inventory and small
metadata reader from the visible ownership analyzer; heavy analyzers are unchanged.

`structural_phase(parsed, nodes)` accepts no fixture name, intent, or oracle.
The caller serializes the complete hypotheses to canonical JSON before loading
intent or constructing oracles. Comparison receives this frozen string and works
on a private deserialized copy. Final structural output is reconstructed from the
same frozen string; oracle agreement never updates a structural status.

Candidate provenance includes zero-based candidate, CPropertyExtend-node,
CObDao-section, and signature-match ordinals, a payload-relative CObDao offset,
anchor-relative offset 34, candidate coordinates, and signature words at
`+12/+56/+108/+112`. Node ordinal counts CPropertyExtend nodes only; section and
signature-match ordinals reset for each node. Candidates are reconciled against
parser extraction order. Absolute file offsets are not emitted. Chain provenance
reports source node class and source payload-relative offset only.

B enumerates at most one conditional ascending pairing per possible CParagraphe
owner, in candidate emission order. Its status stays `blocked` with reason
`no_structural_cparagraphe_owner`. D independently uses node/section/match traversal
order and reports the same conditional remaining-chain hypothesis as `unresolved`.
Neither chooses an owner, and candidate-count mismatch suppresses pairing rather
than forcing an assignment. Candidate coordinate values never sort the records.

E probes u32 words at CObDao-relative `+8..+124` with stride 4, excluding anchor
bytes and signature-word spans. It compares only small positive integers (1..N)
against four words in each chain source's 16-byte preamble. Those words are untyped:
neither constants nor integer coincidences establish identifier semantics. The
current 13 fixtures yield no such shared-index evidence and `no_link_found`.
This limited probe does not rule out other alignments, larger identifiers,
adjacency encodings, or links outside the window. No whole-payload pairwise search
or hex dump is performed.

The equality oracle compares candidate/direct coordinates with current active
parser anchors at per-axis tolerance `1e-6` mm. Its source explicitly says
`current_parser_active_anchor_equality_diagnostic_only`; it is a consistency
oracle, not independent expected-UI or text-identity truth. The tool does not
manufacture fixture expected coordinates or use intent anchors for mapping.
Unavailable or non-unique oracle matches remain unavailable/ambiguous. Intent
reports grouping, attempted order, and order status only after Phase A.

### Current results and comparison accounting

| Strategy | Evaluated fixtures | Structural status | Unconditional comparison | Applicable conditional agreement / contradiction |
|---|---:|---|---|---|
| B: chain_order_pairing | 13 | blocked: 13 | abstention: 13 | 10 / 3 |
| D: payload_order | 13 | unresolved: 13 | abstention: 13 | 10 / 3 |
| E: structural_linkage | 13 | no_link_found: 13 | abstention: 13 | 0 / 0 (no hypotheses) |

All other structural status counts and unconditional `oracle_agreement`,
`oracle_contradiction`, `oracle_unavailable`, and `oracle_ambiguous` counts are zero.
All 21 candidate equality oracles and 13 CParagraphe equality oracles are unique.
This does not turn abstentions into successful mappings. Summary counting units
are fixtures per strategy, candidates for candidate oracles, and fixtures for
direct-anchor oracles. Every conditional branch is compared and retained; the
`conditional_applicable_*` counters describe only branches whose CParagraphe
condition agrees with that separate diagnostic oracle. They are not parser results.

The three conditional contradictions, for both B and D, are grouped CBA,
not-grouped ABC, and not-grouped ABC mixed-color fixtures. With oracle-observed
CParagraphe chain2, ascending remaining-chain pairing predicts `[0,1]`, whereas
candidate traversal matches `[1,0]`. The other ten agree conditionally, including
the content-variation fixture; that agreement concerns anchor coordinates only
and does not resolve its visible-text identity disagreement.

Default limits are eight chain references/conditional owners, sixteen reported
candidates, 256 scanned sections per fixture, four local evidence rows, and 128
characters per reported text. Exceeding bounds suppresses complete mapping claims
and emits `truncated=true` with a warning; full evidence remains in parser output
and fixtures. There is no factorial enumeration. Optional evidence is shed if the
bounded report exceeds the JSON budget; a further fallback retains summary and
provenance counts with explicit warnings. Current output needs no truncation.

Integration checks cover all 13 fixtures, byte-identical serialized structural
hypotheses with oracles enabled/disabled, missing intent, changed active anchors,
Phase A-before-oracle call order, and full parser result equality before/after
analysis. `parser_safe` remains false everywhere; Phase 2 parser ownership is
still not authorized.

### CParagraphe owner structural investigation

The primary structural blocker exposed by Phase 2A is the absence of an
independently established CParagraphe direct-anchor owner. B remains blocked in
13 fixtures, D unresolved in 13, and E has no typed linkage; the earlier B/D
conditional comparisons remain 10 agreements / 3 contradictions.

[`analyze_text_cparagraphe_owner_structure.py`](../tools/analyze_text_cparagraphe_owner_structure.py)
now investigates this blocker separately. Run it with no arguments for a small
text report, `--json` for compact JSON, or `--json --no-oracle` for structural
inventory without intent loading or equality diagnostics. All 13 structural
inventories, hypotheses, and cross-fixture field/adjacency summaries are computed
and frozen before the first intent read or oracle calculation. Only Phase B
stratifies these frozen layouts using intent grouping labels.

The structural signal is the nearest following node that produces a parser
chain: in all current fixtures this is `CContour`. The source-chain hypothesis
agrees with the direct-anchor diagnostic oracle in 13/13 cases. This uses the
parser's source node class and node-relative contour provenance, not expected
coordinates, attempted order, or an oracle owner index. Shared source-node ties
remain ambiguous; no chain is chosen by tie-breaking on coordinates or index.

All fixtures have one CParagraphe at traversal ordinal 1 (zero-based), following
`CZone` and preceding `CCourbe`; the next chain-producing node is `CContour` at
ordinal 3. The complete class sequence is unchanged:
`CZone -> CParagraphe -> CCourbe -> CContour -> CPropertyExtend`.
The direct triple is recorded at CParagraphe payload-relative offset 158, and the
CContour source record currently starts at its payload-relative offset 98.
These offsets locate evidence; neither numeric offset is an ownership selector.

| Comparison case | CParagraphe payload bytes | CPropertyExtend CObDao sections | Source classes in parser chain order | Following CContour source-chain hypothesis / diagnostic owner |
|---|---:|---:|---|---|
| Grouped ABC | 2290 | 9 | CContour, CPropertyExtend, CPropertyExtend | 0 / 0 |
| Grouped CBA | 1330 | 9 | CPropertyExtend, CPropertyExtend, CContour | 2 / 2 |
| Not-grouped ABC, same or mixed color | 1330 | 11 | CPropertyExtend, CPropertyExtend, CContour | 2 / 2 |
| Grouped ABC, content variation | 1810 | 9 | CContour, CPropertyExtend, CPropertyExtend | 0 / 0 |
| Two grouped, same or mixed color | 2290 | 5 | CContour, CPropertyExtend | 0 / 0 |
| Two not grouped, same or mixed color | 3010 | 6 | CPropertyExtend, CContour | 1 / 1 |
| Two not grouped, reversed selection | 2290 | 6 | CContour, CPropertyExtend | 0 / 0 |

These are payload/source-provenance differences that correlate with the reported
owner movement. The class sequence alone cannot explain it: ABC and CBA have the
same adjacency and section count but different chains sourced from CContour.
Grouping changes section counts (5/6 for two objects and 9/11 for three), yet
not-grouped reversed selection demonstrates that those counts do not determine
an owner. No added/removed top-level class in this set provides an explicit link.

The existing [text pipeline](../src/type3_clipboard_codec/parsers/text/text_pipeline.py)
sorts emitted chains by active anchor coordinates, falling back to bbox center;
that implementation is unchanged. Thus the source node can remain the same
structural role while its output chain index changes. This analyzer never sorts
coordinates and does not interpret parser chain index as stored object order.
It follows source provenance into the already-emitted chain list. This dependency
on current parser construction, plus the absence of an explicit anchor-to-contour
link, prevents promotion of the correlation to parser-safe ownership.

Content variation retains the CContour-to-chain0 source relationship while its
parser text is `Type3` and attempted first text is `HELLO`. Payload length changes
to 1810 without breaking that source-role correlation. This supports limited
content independence of the structural signal, not text identity ownership;
neither payload length nor the visible string is used to select the chain.

Local mining is restricted to sixteen u32 words: payload-relative offsets
126..154 and 182..210, stride 4, excluding the entire anchor triple [158,182).
Reference regions are each chain source's 16-byte preamble and bounded non-anchor,
non-signature words in candidate CObDao sections. Zero padding is excluded from
shared-value evidence; there is no full-payload pairwise mining or local hex dump.
The only shared nonzero field is `u32@138 = 2`, which occurs in every chain's
reference preamble and therefore cannot distinguish an owner. No shared nonzero
field identifies a CPropertyExtend candidate section in this probe. Fourteen of
the sixteen local words are invariant; `+154` has two values and `+186` eight.
Their semantics are untyped and no identifier claim is made from these variations.
Larger windows, alternate alignments, and other identifier encodings remain untested.

| Frozen structural hypothesis | Diagnostic support | Conflict | Abstention | Interpretation |
|---|---:|---:|---:|---|
| Nearest following chain source | 13 | 0 | 0 | Supported correlation only; structural status remains unresolved |
| First parser chain (control) | 8 | 5 | 0 | Contradicted as a general owner hypothesis |
| Exclusive CParagraphe node membership | 0 | 0 | 13 | Blocked: current chains share CParagraphe node membership |
| Local shared identifier | 0 | 0 | 13 | No typed owner-discriminating signal |
| Layout-only owner | 0 | 0 | 13 | Blocked: class/section counts have no ownership semantics |

The five control conflicts are the two ordinary not-grouped two-object fixtures,
grouped CBA, and not-grouped ABC same/mixed color. Counts in `hypothesis_summary`
are explicitly post-oracle diagnostic counts; per-fixture frozen hypotheses are
not rewritten, and `supported` in the summary does not mean parser-safe. All 13
direct-anchor oracles are unique with per-axis tolerance `1e-6` mm. Disabled or
unavailable oracles are null and comparisons abstain, distinct from a computed
`none` match. All hypotheses retain `parser_safe=false`.

Integration tests verify all 13 inventories are frozen before oracle loading,
structural equality with/without oracles and missing intent, full parser result
immutability, coordinate-window exclusion, source-chain reordering and ambiguous
ties. Output is bounded by 32 nodes, four CParagraphe nodes, eight chain references,
and eight shared-field rows per CParagraphe; existing candidate-reference bounds
also apply. Overflow is marked truncated rather than used for complete claims.

The conclusion remains `no_parser_safe_cparagraphe_owner_rule_found`. A promising
source-node correlation was found, but an independent ownership link was not.
Phase 2 ownership implementation is still not authorized; active anchors,
baseline_midpoint, CPropertyExtend ownership, and matched_chain are unchanged.

## 7. Phase 2A Success Criteria

Before considering parser ownership implementation, require at least:

- All 13 current fixtures analyzed with no fixture-name branch in mapping logic.
- Structural strategies evaluated independently of fixture/baseline oracles,
  including independently justified CParagraphe ownership or an unresolved result.
- Zero mismatches, or every mismatch explicitly documented by strategy, provenance,
  competing hypotheses, and oracle reliability. Unexplained mismatches block promotion.
- Grouped/not-grouped, ABC/CBA, two-/three-object, and content/style/color coverage.
- All four unknown-order fixtures remain analyzable without selection-order inference.
- Ambiguous cases may remain unresolved; no forced assignments or discarded evidence.
- Compare full parser output before/after shadow analysis to demonstrate no mutation;
  changing/removing intent oracles must not change structural hypotheses.
- Report evaluated, supported, contradicted, unresolved, and oracle-unavailable counts
  separately. Agreement percentages must not hide abstentions or missing oracles.

Completing the current matrix is necessary, not sufficient for promotion. Broader
N, duplicate/coincident cases, cross-session captures, and alternate signatures
remain evidence gaps. Planning those checks does not authorize new fixtures in
this analyzer stage. A separate review must establish a generic structural
rule and its failure behavior before parser work begins.

## 8. Non-Goals

- No active anchor changes, `matched_chain` assignments, or parser ownership changes.
- No replacement of `baseline_midpoint`.
- No promotion of signature v1 to confirmed.
- No color/font/style decoding or changes to text identity extraction.
- No inference of actual stored order or intent YAML use inside the parser.
- No parser/decoder/model edits, production ownership implementation, or new fixtures
  in this analyzer stage.

## 9. Implemented Small Analyzer

[`tools/analyze_text_anchor_shadow_mapping.py`](../tools/analyze_text_anchor_shadow_mapping.py)
is a separate small tool; existing heavy section-audit tools are unchanged.
Its purpose is to compare mapping strategies while
leaving parser candidates, ownership, and active anchors unchanged.

Default to all 13 fixtures, a short per-fixture/strategy summary, and compact
`--json`. Target the existing visible analyzer's limits: text below 50,000
characters and JSON below 100,000. Emit counts, provenance, reasons, and bounded
hypothesis sets; avoid raw payload dumps and factorial permutation enumeration.
Preserve raw evidence in the original parser results/fixtures and reference it
from the report. Missing inputs and unavailable oracles should be explicit warnings.

## 10. Open Questions

- What determines the CParagraphe owner, independently of expected anchor equality?
- Does CPropertyExtend candidate record order map to parser chain order or a
  different structural sequence?
- Is there a local object index/identifier near candidate records?
- Does grouping insert/remove records that reveal linkage rather than merely counts?
- Is candidate ordering stable across capture sessions, creation orders, and Type3 versions?
- Can ownership be solved structurally without expected anchor or baseline equality?
- Are there alternate signature variants or valid candidates that v1 misses?
- How should content-variation text/anchor disagreement be interpreted without
  presuming either provisional layer already defines object identity?
- What happens with repeated text, coincident anchors, or more than three objects?

## 11. Readiness

| Area | Current judgment |
|---|---|
| Intent metadata | Complete for 13/13; 9 attempted, 4 explicitly unknown |
| Visible text identity | Provisional but relatively stable in current observations |
| CPropertyExtend candidate decode | Provisional implemented |
| Raw source relationship | Structurally supported; semantic linkage not established |
| Semantic CParagraphe ownership | Unresolved; 13/13 source correlation is not ownership proof |
| CPropertyExtend ownership | Unresolved; `matched_chain = None` |
| Phase 2 active ownership implementation | Deferred / not ready; awaits independent evidence |
| Analyzer-only shadow mapping and source-linkage investigation | Phase 2A investigation complete |

This RFC does not authorize parser promotion. Active anchors and the
`baseline_midpoint` fallback remain unchanged.

### CParagraphe source-linkage audit (2026-09-06)

Run `python tools/analyze_text_cparagraphe_source_linkage.py --json` (or
`--no-oracle`). This separate bounded analyzer changes no parser, decoder, model,
active anchor, or `matched_chain` assignment.

The previous next-chain-producing-CContour correlation survives before coordinate
sorting: 13 support / 0 conflict / 0 abstention. The analyzer executes the existing
node grouping and chain construction methods on copied nodes, records their actual
return order, and reconciles sources with final chains using node provenance and
payload-relative record positions. It does not reconstruct source order by sorting
final coordinates. Addresses are used internally only to reconcile parser/body
origins, never as an ownership rule or emitted file offset.

All 13 fixtures have the scanned sequence CZone (0), CParagraphe (1), CCourbe (2),
CContour (3), then CPropertyExtend. Raw chain 0 comes from CContour; subsequent
chains come from embedded records in CPropertyExtend. CCourbe is context, not a
chain-producing source in these fixtures. The paragraph direct anchor at
payload-local +158 is decoded only in the diagnostic oracle phase.

The scanner cuts each payload at the next plausible class header. This establishes
flat scanner node spans, not verified object lengths, nesting, or parent-child
links. The chain builder starts a group at CZone or a repeated CContour. These are
parser construction heuristics. In this corpus, the paragraph and all produced
chains share the same parser group; embedded chains inherit its node list.
CPropertyExtend is a scanner node boundary but does not terminate that parser
group. Additional producing records occur before the group ends. No independently
validated enclosing object block or explicit paragraph-to-contour reference was
identified. The common range therefore cannot uniquely establish ownership.

The text pipeline subsequently sorts chains by active anchor (x, y), falling back
to bbox center (x, y), then infinity. Of 34 chains, 10 change index in five fixtures.
The following lists final indices in raw construction order:

| Contrast | Raw-to-final indices |
| --- | --- |
| Grouped ABC, including mixed color, height, font and content variations | [0, 1, 2] |
| Grouped CBA | [2, 1, 0] |
| Not-grouped ABC, same color and mixed color | [2, 1, 0] |
| Two-object grouped, same color and mixed color | [0, 1] |
| Two-object not-grouped, same color and mixed color | [1, 0] |
| Two-object reversed selection | [0, 1] |

These contrast labels are reporting context only. No fixture name, attempted
order, expected coordinate, baseline equality, or intent selects a source.

| Hypothesis | Support | Conflict | Abstention |
| --- | ---: | ---: | ---: |
| H1 immediate next producing CContour | 13 | 0 | 0 |
| H2 independently delimited same local block | 0 | 0 | 13 |
| H3 first raw chain constructed from paragraph parser group | 13 | 0 | 0 |
| H4 contiguous CParagraphe / CCourbe / producing CContour | 13 | 0 | 0 |
| H5 adjacency-only null hypothesis | 0 | 0 | 13 |

Counts measure post-freeze diagnostic owner agreement, not independent semantic
validation. H3 can be stated without next-CContour wording, but remains dependent
on parser grouping and construction order. H4 is a repeatable class sequence;
its semantic distinction from later embedded contours is unproven. H2 has no
validated block selector. H5 remains viable: oracle agreement cannot distinguish
accidental layout adjacency from semantic linkage. No current fixture contradicts
H1/H3/H4, and this corpus does not discriminate between them.

The entire structural corpus is serialized before any oracle or intent load.
`--no-oracle` preserves fixture structural results and structural summaries;
intent removal also preserves them. Tests reverse final chain order and remove
sort coordinates without changing source hypotheses, compare active parser
objects before/after, and verify source files are unchanged by analysis.

Conclusion: `raw_source_chain_relationship_supported`, with
`independent_linkage_found=false`. This does not prove adjacency is accidental,
nor that adjacency means ownership. Every hypothesis retains
`semantic_linkage_proven=false` and `parser_safe=false`; parser-safe CParagraphe
ownership is still not ready. Further evidence needs an independently decoded
object delimiter/reference or a discriminating layout, not more identical
adjacency examples. Output is bounded to <100 KB JSON / <50 KB text with no raw
payload dumps.

## 12. Final Ownership Investigation Closeout

Phase 2A investigation is complete. Phase 2 parser ownership implementation is
explicitly deferred until new evidence establishes an independently validated
link. The final structural conclusion is
`raw_source_chain_relationship_supported`, not ownership solved.

### Confirmed / strongly observed in the current corpus

- The CParagraphe-related source relationship survives before coordinate sorting
  in all 13 fixtures. The candidate is raw chain 0 produced from CContour;
  later chains are produced from CPropertyExtend embedded contours.
- Of 34 total chains, 10 across five fixtures change final index after coordinate
  sorting. Final parser index is not a stable structural ownership identifier.
- Raw/source provenance precedes final index assignment and is more fundamental
  for tracing construction. This does not establish semantic object identity.

### Provisional correlations and unresolved semantics

The CParagraphe-to-raw-source-chain and CCourbe/CContour sequence relationships
remain correlations. Adjacency-only remains a viable explanation. There is no
independently verified object-block boundary, unique local object identifier, or
semantic ownership linkage. CParagraphe ownership, CPropertyExtend
candidate-to-chain mapping, and actual stored object order remain unresolved.
Neither CParagraphe nor CPropertyExtend has a parser-safe ownership rule.

### Rejected as parser ownership rules

Baseline equality, expected-anchor selection, attempted selection order, final
sorted chain index, fixture filename, absolute offsets, and unconditional
chain-order pairing must not select owners. Diagnostic agreement and raw chain 0
in this corpus do not make unconditional order pairing safe. All ownership
hypotheses remain `parser_safe=false`.

### Deferred implementation and next track

`matched_chain = None`, the active text anchor, and the `baseline_midpoint`
fallback remain unchanged. Candidate decoding is provisional implemented;
semantic ownership is unresolved, and Phase 2 active ownership implementation is
deferred / not ready as recorded in the readiness table above.

Reopening anchor ownership requires independent evidence such as a validated
object boundary/reference or a semantic identifier that uniquely links records
to source chains and distinguishes that link from adjacency. Additional agreement
with expected coordinates or attempted order alone is insufficient.

The next text reverse-engineering track is **color ownership**. Its initial
question is how color candidate records relate to source objects, using the
existing single-object and grouped/not-grouped mixed-color evidence. Keep color
field decoding separate from color ownership and do not assume anchor ownership
is available as an object identity oracle. This closeout adds no analyzer,
parser feature, heuristic, or fixture.

Verification baseline: `PYTHONPATH=src pytest -q` — **311 passed**.
