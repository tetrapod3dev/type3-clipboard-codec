# Multi-object Text Anchor Ownership Mapping RFC

Status: research proposal; Phase 2 ownership assignment **not ready**.
Scope: documentation only. No parser, analyzer, model, active anchor, or fixture changes.

Related documents: [candidate decode contract](text_cproperty_anchor_decode_rfc.md),
[text research notes](text_reverse_engineering.md), and
[text object research](text_object_reverse_engineering.md).

## 1. Problem Statement

A CPropertyExtend anchor candidate can be decoded independently of knowing which
parsed text chain owns it. Candidate recognition and candidate-to-chain mapping are
separate decisions. The latter remains unresolved. Active anchors already have
chain-specific structural recovery through `baseline_midpoint`; Phase 2 would need to
connect a direct candidate to a chain without using that existing result as its selector.

This RFC takes the supplied Phase 1 state as its design premise:

```text
candidate_fields["cproperty_anchor_candidates"]
source="CPropertyExtend_CObDao_signature_v1"
confidence="provisional"
ownership="unresolved"
matched_chain=None
```

Checkout verification note: when this RFC was written, the named Phase 1 candidate
fields were not found in local parser source, and the linked decode RFC did not exist.
The decode document was added as a contract summary. This RFC records the supplied
Phase 1 contract, not a claim that its implementation was verified in this checkout.
No implementation is added to reconcile that difference.

## 2. Current Observed Model

Across the 13 multi-object fixtures, the observed model is `N` parsed text chains,
one CParagraphe direct anchor, and `N-1` CPropertyExtend anchor candidates.

| Parsed chains | CParagraphe direct anchors | CPropertyExtend candidates | Coverage |
|---:|---:|---:|---|
| 2 | 1 | 1 | grouped and not-grouped |
| 3 | 1 | 2 | grouped and not-grouped |

This cardinality pattern constrains a possible mapping but does not identify owners.
Even the single remaining candidate in a two-object case cannot be assigned by
elimination unless the primary owner and completeness are independently established.

Visible `text_candidate` separation is stable in the current fixture range but remains
provisional. Parser chain text order and attempted selection order can vary independently.
In the content variation fixture, attempted A-B-C text is HELLO / 9876543210 / Type3,
while parser chain text order is Type3 / 9876543210 / HELLO.

Intent metadata coverage is 13 targets, 10 YAML metadata files, 3 missing metadata
files, 4 unknown orders, 9 attempted orders, and 0 controlled-observed orders.
Every `actual_stored_order` is `unresolved`. Intent is reporting-only and never parser input.
An absent intent file must not block payload parsing.

## 3. Candidate Ownership Signals

### A. Anchor equality / proximity to current baseline anchor

Equality with the current chain baseline anchors produces useful analyzer matches.
It is the strongest current observational evidence for proposed owners, rather than
a structural link. Using the active baseline result to select its direct replacement
creates circular validation: a wrong baseline could select a wrong direct candidate
and then appear to corroborate itself. Proximity also needs a tolerance and cannot
distinguish coincident or nearby objects reliably.

Classification: **validation/evaluation only**. Neither equality nor nearest-neighbor
proximity may be the parser's primary selector or a tie-breaker. A future structural
mapping can be evaluated against these observations after selection.

### B. Parser chain order

Every parsed chain has an index, so this is available without external metadata.
However, chain order is not a proven payload ownership relation. Attempted selection
order can change while chain text order remains stable, and the CParagraphe owner is
not always chain0. Never zip candidate order to chain order or assign leftover chains
solely by index.

Classification: **insufficient alone**. Indexes may identify the output target after
an independent link has been established; they cannot establish the link.

### C. Attempted selection order

This is fixture capture intent, not a decoded payload field. Some captures lack it;
even recorded attempts are not proof of actual stored order. Filenames are subject
to the same restriction.

Classification: **analyzer/reporting only**; prohibited as parser input.

### D. CParagraphe ownership / primary-object evidence

For same-content grouped fixtures, baseline-based analyzer observations associate
grouped ABC with owner A and grouped CBA with owner C. In the not-grouped ABC fixture,
the corresponding observation identifies C, showing that the grouped pattern is not
universal. These labels denote capture objects, not permanently assigned chain indexes.

This is useful evidence that grouping/selection may affect primary-object storage.
It does not establish the exact payload rule, and the observed owner must not be
reused as an independently decoded fact. A proven primary-object link could later
constrain other links, provided completeness and uniqueness are also established.

Classification: **useful evidence; exact structural rule unresolved**.

### E. Visible text identity

Chain-level text candidates provide useful identities for comparing observations.
No text identifier linking a CPropertyExtend anchor record to a text run has been
confirmed. A stable visible value does not establish that such a reference exists,
and equal text can legitimately appear in multiple objects.

Classification: **insufficient alone**. Research should look for a record reference
or link identifier, rather than equating visible text values or assuming uniqueness.

### F. CObDao local metadata

The local signature identifies an anchor candidate, not its owner. Fields beyond
the signature may encode ownership, order, or a reference, but none is confirmed.
Constant signature fields that discriminate anchor-bearing records cannot themselves
distinguish multiple owners with the same signature.

Classification: **future structural-link research candidate**, not a current mapping rule.

## 4. Parser-safe vs Analyzer-only Matrix

Here, “parser-safe” means sufficient evidence to participate in an ownership selector,
not merely that a value is accessible in the parser. No listed signal currently provides
a validated ownership mapping rule. Payload-derived signals may be researched in the
analyzer without becoming parser rules.

| signal | parser-safe | analyzer-only | reason |
|---|---|---|---|
| baseline anchor equality / proximity | No | Validation/evaluation only | Depends on the active result; ambiguous for coincident anchors; no selector or tie-breaker use |
| fixture intent order | No, prohibited | Reporting only | External capture metadata, not payload structure; attempted is not stored order |
| parser chain index | No, alone | Compare order hypotheses | Available as an output identifier, but no proven candidate-to-index correspondence |
| visible text value | No, alone | Compare visible identities | Duplicate text is possible; no candidate text reference confirmed |
| CParagraphe owner | Not yet | Primary-object evidence | Current owner labels are evaluation-derived; structural primary-owner rule unresolved |
| CObDao local metadata | Not yet; possible future link | Inspect link/id hypotheses | Signature recognizes candidate type, not owner; no confirmed link field |
| relative section ordering | No, alone | Compare structural sequences | Grouping changes section layout; no proven ordering-to-chain relation |
| absolute offset | No, prohibited | Locate/report evidence only | Fixture/layout-specific addresses do not identify an owner across payloads |

Bounds-checked offsets relative to a structurally decoded record may be used to read
future link fields; this is distinct from a hard-coded absolute payload offset or a
section ordinal used to guess ownership. A proposed structural relation must pass all
promotion requirements below before it becomes parser-safe.

## 5. Phase 2 Minimum Promotion Requirements

Ownership assignment must not be implemented until a documented, independently
supported structural rule meets every requirement:

1. Works without fixture filenames, fixture identities, or intent metadata.
2. Works without baseline equality or proximity, including tie-breakers.
3. Works without hard-coded absolute offsets.
4. Reproduces across grouped and not-grouped payloads.
5. Reproduces across two-object and three-object payloads.
6. Reproduces across ABC and CBA order attempts without consuming those labels.
7. Preserves `unresolved` when a candidate or mapping is ambiguous.
8. Prefers no assignment over a wrong assignment.

The promotion evidence should specify link field boundaries, reference scope, target
identity, completeness checks, and uniqueness rules. Evaluate a proposed rule against
all 13 current fixtures and the existing content/style variants; passing these fixtures
alone does not prove the format semantics. Baseline/intent comparisons remain separate
evaluation evidence and must never feed the selector.

Before implementation, define negative cases for duplicate visible text, coincident
anchors, multiple possible links, missing/truncated chains, and malformed sections.
Do not claim current fixture coverage for these cases. This RFC creates neither new
fixtures nor tests for an unimplemented selector. Phase 2 approval concerns ownership
mapping only; replacing the active anchor would require a separate decision.

## 6. Proposed Future Ownership API

A future Phase 2 may extend the Phase 1 candidate with the following mapping fields:

| Field | Meaning |
|---|---|
| `ownership` | Mapping outcome: `resolved` or `unresolved` |
| `matched_chain` | Parsed chain index after a unique link is established, otherwise `None` |
| `ownership_source` | Versioned structural mapping rule, separate from candidate decode source |
| `ownership_confidence` | Confidence in that mapping, separate from decode confidence |
| `ownership_notes` | Evidence and reasons for assignment or abstention |

Illustrative future result only; this is not an implemented or approved rule:

```text
ownership="resolved"
matched_chain=1
ownership_source="future_structural_link_v1"
ownership_confidence="provisional"
ownership_notes=["Unique structural reference to parsed chain 1"]
```

Here `resolved` means a unique mapping under the stated rule, not confirmed format
semantics. The source name is a placeholder, not evidence that the link exists.
Current Phase 1 contract remains:

```text
ownership="unresolved"
matched_chain=None
```

Do not add or populate the proposed ownership fields in this documentation stage.
Keep `source="CPropertyExtend_CObDao_signature_v1"` and decode confidence separate
from any future ownership decision. Ownership assignment would not itself switch
the active anchor away from `baseline_midpoint`.

## 7. Failure Policy

- No unique structural mapping: do not assign; keep ownership unresolved.
- Multiple matches or conflicting candidate-to-chain links: unresolved; no index,
  proximity, section-order, or leftover-chain tie-breaker.
- Incomplete chain count or unproven completeness: unresolved; matching the observed
  `1 + (N-1)` count is necessary context, not sufficient ownership proof.
- Malformed section: ignore that section as an assignable candidate and emit a warning;
  retain raw evidence under existing preservation policy and do not infer a missing owner.
- Valid candidate with no established link: preserve the decoded candidate with
  `matched_chain=None` rather than inventing a match.
- In all failure cases, preserve the active `baseline_midpoint` fallback.

## 8. Explicit Non-goals

- Implementing Phase 2 ownership assignment.
- Replacing `baseline_midpoint` or changing active anchors.
- Forcing candidate ownership, including assignment by elimination without proven links.
- Using fixture intent, filenames, or attempted order as parser rules.
- Expanding into color, font, or style ownership.
- Expanding analyzer processing or generating new fixtures during this RFC stage.

## 9. Open Questions

- Does the payload contain a chain/object link id, and what is its scope and lifetime?
- Is there a structural relation between the CParagraphe primary object and
  CPropertyExtend section order?
- Is there an identifier linking a visible text run to a CPropertyExtend section?
- Does group structure change ownership metadata, reference scope, or only layout?
- What does the ordering of multiple CPropertyExtend candidates mean, if anything?
- How can reference uniqueness and complete chain recovery be established independently
  of the current anchor coordinates and fixture intent?

## 10. Current Recommendation

- Phase 1 candidate decode: retain the supplied provisional candidate contract.
- Active anchor: retain `baseline_midpoint`.
- Phase 2 ownership assignment: **not ready**; no parser-safe mapping rule confirmed.
- Next research target: a structural link/id between a chain or text record and a
  CPropertyExtend section, with independently established target identity and bounds.

Use existing observations to evaluate that research, not to supply missing links.
Actual stored order and visible text ownership remain unresolved/provisional respectively.
