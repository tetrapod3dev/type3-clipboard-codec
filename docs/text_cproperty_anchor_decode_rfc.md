# CPropertyExtend Direct Anchor Provisional Decode RFC

Status: Draft (provisional)  
Date: 2026-05-24  
Scope: Text parser design discussion only (no implementation in this RFC)

## 1. Problem Statement

Current active text anchor behavior relies on `baseline_midpoint` fallback.
In multi-object text fixtures, direct-anchor evidence is observed as:

- one anchor stored in `CParagraphe` direct triple
- remaining `N-1` anchors observed in `CPropertyExtend` `CObDao`-local sections

`CPropertyExtend` local anchor pattern exists, but parser does not decode it yet.

## 2. Evidence Summary

### 2.1 Anchor storage scaling

For `N` parsed text chains (current controlled fixture groups):

- `1` `CParagraphe` direct anchor
- `N-1` `CPropertyExtend` anchor hits

### 2.2 Signature v1

Name:

- `CPropertyExtend_CObDao_anchor_record_candidate_v1`

Observed conditions:

- node class is `CPropertyExtend`
- `OBJETINFOS_CLASSNAME` exists at `CObDao - 24`
- `CObDao` marker exists
- `u32le@CObDao+12 == 131072`
- `u32le@CObDao+56 == 262144`
- `u32le@CObDao+108 == 65536`
- `u32le@CObDao+112 == 262144`
- `CObDao+34` decodes as finite `double3`
- z near `0`
- x/y coordinate-like

### 2.3 Stability coverage (small analyzer groups)

Source analyzer:

- `tools/analyze_text_cproperty_anchor_record_semantics.py`

Group results:

- Group A (style/content variation): stable on checked offsets
- Group B (grouping variation): stable on checked offsets
- Group C (order variation): stable on checked offsets

Checked offsets:

- `+12`, `+34`, `+56`, `+108`, `+112`

Current observed stable values:

- `+12 = 131072`
- `+56 = 262144`
- `+108 = 65536`
- `+112 = 262144`
- `+34`: coordinate-like, z near zero

## 3. Proposed Parser Scope

Important split: decode and ownership assignment are separate phases.

### Phase 1 (decode only, no ownership assignment)

Possible future parser behavior:

- scan `CPropertyExtend` local `CObDao` sections
- detect signature v1
- decode anchor triple at `CObDao+34`
- expose candidate evidence only

Candidate output shape (example names):

- `cproperty_anchor_candidates`
- `source: CPropertyExtend_CObDao_signature_v1`
- `confidence: provisional`
- `ownership: unresolved`
- `matched_chain: None`

### Phase 2 (ownership assignment, later)

Not implemented in this RFC.
Requires independent chain mapping rule.

Possible future signals:

- anchor equality/proximity vs chain anchor/bbox
- text-run ownership evidence
- parser chain order evidence
- selection/primary-object metadata evidence
- `CParagraphe` ownership evidence

## 4. Explicit Non-Goals

- do not replace `baseline_midpoint` now
- do not assign `CPropertyExtend` anchors to chains now
- do not mark direct anchor as confirmed
- do not use fixture filename as parser rule
- do not use absolute offset as parser rule
- do not use baseline equality as parser selector
- do not decode text color/font/style in this RFC

## 5. Parser Readiness

Current recommendation:

- `ready_for_decode_candidate_experiment`: maybe (limited/provisional only)
- `ready_for_active_anchor_replacement`: no
- `ready_for_ownership_assignment`: no

Rationale:

- signature pattern is stable in current controlled groups, but semantics of `+12/+56/+108/+112` are unresolved
- ownership rule is unresolved and must be independent from analyzer labels
- active anchor behavior regression risk is high without guarded rollout

## 6. Safety Requirements Before Any Implementation

If implementation is attempted later:

- feature flag or provisional output-only mode
- snapshot tests before/after
- no active `text_anchor` change unless explicitly enabled
- candidate fields only in default behavior
- keep `baseline_midpoint` fallback
- expose provisional/warning metadata in parser output

## 7. Future Test Plan (Implementation Stage)

- signature v1 candidate-count tests
- decoded candidate triple tests (`CObDao+34`)
- assert no active anchor change by default
- assert no ownership assignment
- multi-object fixture coverage
- assert no fixture-name branching
- malformed/short payload safety tests

## 8. Open Questions

- what are semantics of `+12/+56/+108/+112`?
- is signature v1 stable across broader Type3 sessions?
- how to map candidates to parsed chains safely?
- relation to selection order / primary-object behavior?
- full record boundary and length?
- other anchor-record variants?

## Current Conclusion

Signature v1 is a strong, currently stable local pattern in controlled fixtures.
Promotion to active parser anchor logic is not recommended yet.
Only provisional decode-candidate experimentation is in scope for future guarded work.
