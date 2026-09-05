# Text Anchor Ownership Mapping RFC

Status: Draft; Phase 2 ownership implementation is not ready.
Date: 2026-09-06
Scope: Phase 2A analyzer-only shadow experiment implemented; no parser ownership assignment.

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
| CParagraphe ownership | Unresolved/provisional; analyzer matches only |
| CPropertyExtend ownership | Unresolved; `matched_chain = None` |
| Active ownership implementation | Not ready |
| Analyzer-only shadow mapping | Phase 2A implemented; blocked/unresolved hypotheses and diagnostic comparisons reported |

This RFC does not authorize parser promotion. Active anchors and the
`baseline_midpoint` fallback remain unchanged.
