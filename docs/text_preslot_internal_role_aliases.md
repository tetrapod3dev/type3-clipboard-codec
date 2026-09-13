# Two additive pre-slot internal-role aliases

Only two Tier A stored model-side roles from the
[semantic contract review](text_typed_field_semantic_contract_review.md) receive
aliases. **Neutral P-relative keys remain canonical. UI semantic ownership is
unresolved for both aliases.** No vendor reverse engineering was reopened.

The accepted run optionally includes:

```json
"preslot_archive_double_aliases": {
  "stored_minimum_line_layout_scale": "P+0x20",
  "stored_first_line_layout_scale": "P+0x68"
}
```

Each string targets a key in the same run's
`preslot_archive_double_candidates`. The alias map does not copy a field object,
raw bytes or numbers. The canonical entry remains the sole value authority.
Consumers may continue using all existing neutral keys unchanged.

| Alias | Canonical target | Existing source | Narrow internal role |
|---|---|---|---|
| stored_minimum_line_layout_scale | P+0x20 | CTxtAttrPara+0x20 | Stored aggregate/minimum of assigned line-layout scales |
| stored_first_line_layout_scale | P+0x68 | CTxtAttrLine[0]+0x10 | Stored assigned/limited layout scale for the first line |

The first role does not promise fresh recomputation, equality with the first-line
value, positivity, a [0,1] range or UI compression ownership. The second is not
the unmodified return of one helper invocation, a paragraph-wide scale, an
immutable value or Maximum Length ownership. No second-line alias is added.

P+0x50 remains neutral with source `CTxtAttrLine[0]+0x30`; it has no alias.
The five slot-local fields and P+0x50 retain Tier B. P+0x20/P+0x68 retain Tier A
only for the reviewed internal roles. Six Tier B UI interpretations receive no
production aliases. Documentation may still describe P+0x50 as a
maximum-length-correlated signed value.

## Placement and availability

Only `src/type3_clipboard_codec/parsers/text/text_slot_candidate.py` changes in
production: nine lines appended after accepted candidate construction, successful
parent validation and canonical pre-slot extraction. Alias creation cannot affect
alignment, F4, the 204 gate, count, terminal state, chain ordering, ownership or
typed decoding. Existing decisions and extraction code are unchanged.

The map includes each approved alias only if its individual canonical key exists.
An empty result does not add an alias-map key. Current production emits the full
three-field pre-slot group for L>=1; failed parent validation or L=0 emits neither
that group nor aliases. Tests also inject partial groups to prove individual
availability handling without adding partial parsing support.

Alias eligibility reads key presence only. Unequal values, negative numbers,
NaN and infinities do not suppress either reference. All eight canonical fields'
raw bytes, f64le formatting, width8, source identities and dynamic
payload_relative_offset remain unchanged. Existing nonfinite presentation and
authoritative raw bits remain exactly as before.

One-line and two-line inputs use the same alias map. In the four real two-line
paragraphs, stored_first_line_layout_scale still refers only to AttrLine[0].
Observed equality is neither an aliasing rule nor a reason to merge the two
distinct canonical objects.

## Compatibility and tests

Actual parser objects and parser/chain choices for all 116 valid captures were
frozen before implementation. After removing **only**
`preslot_archive_double_aliases`, values, nested field order and selection match
those snapshots exactly. The projection retains all canonical pre-slot fields
and all five slot-local doubles. An AST comparison of the complete production
module confirms that only the appended alias construction block differs.

`tests/text_slot_typed_output.py` adds alias-only projections for this batch.
Older historical projections compose that step with their already approved
earlier field projections; they introduce no new canonical-field exclusion for
comparison against this batch's immediate baseline. Historical goldens are untouched.

The 18 new tests cover canonical references, no P+0x50/Tier B aliases, unchanged
raw/f64 values, unequal values, negative and nonfinite values, strict deterministic
JSON, one/two lines, partial availability, parent failure, record-gate ordering
and broad corpus counts. Partial-group tests use opaque objects to prove that
alias creation does not inspect numbers or duplicate field objects.

| Corpus result | Count |
|---|---:|
| Valid captures with exact pre/post compatibility | 116 |
| Canonical pre-slot groups | 84 |
| stored_minimum_line_layout_scale aliases | 84 |
| stored_first_line_layout_scale aliases | 84 |
| Two-line groups | 4 |

Counts are regression evidence, never parser constants. No captures or synthetic
fixtures were saved. The fixture tree's 204 files remain byte-exact.

## Source-integrity provenance

The production-only change was committed locally first:
`d76ac962777ecb374443a6fb0c42590801409f1c`. No push was performed. Committed source
blob `97891daaae3ee79cf0885c8b702433eaf2653d5c` was hashed with the approved
`tests/source_integrity.py` CRLF-to-LF-only canonical policy:

`f5ec6614cd11d4c89ec77ae569ed5209f3c2615392b02dafef90a5a9ac96e54d`.

Only its current protected record changed out of 49 records. All four previous
provenance generations and legacy raw provenance are preserved; groups/inventory
are unchanged. No dirty-working-tree or blanket rebaseline was used. Companion
changes are the new test, projection helper, single baseline entry and this document.

| Validation | Result |
|---|---|
| New alias tests | 18 passed |
| Existing pre-slot production / shadow / slot doubles | 46 / 39 / 26 passed |
| Production204 / applicability / empty extension / archive metadata | 29 / 36 / 26 / 16 passed |
| Historical replay | 1 assertion passed;104 fixtures, runtime_outputs_equal=true, canonical_source_equal=true, ready_for_review |
| Combined focused run | 237 passed in 22.16s |
| Full actual checkout | 1486 passed in 94.28s; baseline1468 + 18 new tests |
| Ruff / E4,E7,E9,F | No new full-rule diagnostics; one pre-existing C408 remains. E4/E7/E9/F passed |
| Git whitespace / fixture hashes | Passed; all204 fixture files byte-exact, no additions/removals |

No chain parser, analyzer, canonical field, Tier B decision or UI ownership status
changed. The next step is human review of this additive reference contract and
compatibility evidence. No further semantic aliases or parsing starts automatically.
