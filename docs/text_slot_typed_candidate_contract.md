# Text-slot typed candidate consumer contract

Review of checkout `89dc8551951cdc0c00fb469017477e90d2be1b8d`. This document
consolidates current output and recommends compatibility rules; it changes no
parser, schema, alias, source-integrity baseline or evidence capture. Current
behavior below is verified against the production implementation. SHOULD/MAY
statements are consumer and future-maintenance recommendations, not new runtime
enforcement or an already versioned external API guarantee.

## What each layer establishes

| Layer | Safe conclusion | Limit |
|---|---|---|
| Candidate existence | The existing alignment, uniqueness, count, continuation and terminal rules accepted a text-slot run. | Not general Type3 coverage or visible-glyph ownership. |
| Layout applicability | Every accepted record passed the reviewed current/empty 204-byte layout gate. | Not UI semantic ownership; parent applicability is separate. |
| Canonical archive coordinate | A key identifies a field within its record or independently derived P context. | Not an absolute file address or UI name. |
| Typed archive representation | Eight preserved bytes decode as little-endian IEEE-754 binary64. | Not numeric range, units or semantic validation. |
| Internal-role alias | A reference supplies one approved, narrow stored model-side role. | Not a second value authority or UI control identity. |
| Correlated semantic label | Existing controlled evidence supports a provisional diagnostic interpretation. | A-E do not establish UI-to-model ownership. |

The run lives at `candidate_fields.text_slot_run`. Its existing
`confidence="provisional"`, `parser_safe=false` and unresolved ownership remain
unchanged. They must not be silently upgraded by a typed field's presence. The
bounded decoding described here does not claim a complete semantic parser.

## Canonical identities and scope

Canonical identity includes the container namespace and the particular run/record
instance. The exact key spelling is significant; offsets below are not globally
unique identifiers. Consumers SHOULD persist/reference canonical structural keys
when archive identity matters. Semantic aliases are never primary identity.

| Container within run | Canonical key | Archive source | Safe descriptive label / tier |
|---|---|---|---|
| `slots[i].archive_double_candidates` | `0xc` | CTxtAttrChar+0x10, serialized record+0x0C | Height-correlated; B |
| same | `0x14` | CTxtAttrChar+0x18, serialized record+0x14 | Width-correlated ratio; B |
| same | `0x1c` | CTxtAttrChar+0x20, serialized record+0x1C | Slant-correlated value; B |
| same | `0x40` | CTxtAttrChar+0x30, serialized record+0x40 | Character-spacing-correlated ratio; B |
| same | `0x48` | CTxtAttrChar+0x38, serialized record+0x48 | Rotation-correlated value; B |
| `preslot_archive_double_candidates` | `P+0x20` | `CTxtAttrPara+0x20` | Stored minimum line-layout scale; A, internal role only |
| same | `P+0x50` | `CTxtAttrLine[0]+0x30` | Maximum-length-correlated signed value; B |
| same | `P+0x68` | `CTxtAttrLine[0]+0x10` | Stored first-line layout scale; A, internal role only |

Member coordinates and serialized coordinates are distinct: for example,
record+0x40 is serialized from Char+0x30. The per-slot field objects do not gain a
`source` property through this documentation.

Each slot field contains `raw_bytes`, `f64le`, `typed_width=8`. Each pre-slot field
additionally contains `payload_relative_offset` and the exact `source` string
shown above. `typed_width` means serialized archive width in bytes, not semantic
confidence, display precision, ownership confidence or UI unit width. Unresolved
widths on code/count/RGB candidates are separate field-specific states.

Slot keys are record-relative: combine the parsed slot's
`prefix_relative_offset` with the key's offset to obtain a CParagraphe
payload-relative position. No absolute raw-file coordinate is a stable identity.
The inspection `raw_span` is not a promise to contain all 204 record bytes.

P is the first embedded AttrPara version emission, derived by walking from the
recognized CParagraphe payload origin C. Pre-slot positions are P plus the
canonical key's offset. `payload_relative_offset` records the dynamically derived
C-relative position. **Do not assume 214, 262 or 286.** Those were observed because
P-C was 182 in all 84 reviewed paragraphs; supported synthetic prefixes produced
181, 183 and 213 too. At shift 181 the three positions become 213, 261 and 285.
Identity is the P-relative key and structural source in its run context, not a
historical C-relative number.

**P+0x50 and P+0x68 belong to AttrLine[0].** They are not generic paragraph-wide
fields and say nothing about later lines. Four reviewed paragraphs have two
lines; the same first-line meaning applies. P+0x20 is aggregate storage, with no
promise of fresh recomputation or equality to the first-line value.

## Applicability and absence

Record acceptance requires existing structural alignment, exact AttrChar version
5, exact CPropertyExtend version 5 and all six reviewed empty-extension guards
zero, within a complete 204-byte window. The two array counts, two string lengths
and two optional-zone presences are checked; other fixed extension bytes need
not be zero. Every record, including terminal, passes the same gate. F4 remains
a separate structural condition. Unknown higher versions are not accepted as
current merely because they are numerically greater.

Pre-slot output additionally requires an independent bounded parent walk:
exact CObDao v8, CObjGuid v2, AttrPara v4 and every encountered AttrLine v4;
bounded DWORD-length property strings; the supported empty additional map;
unambiguous absence of the optional Fin word; and supported flags/counts/bounds.
First AttrChar is independently derived as `P + 60 + 68*L`, not by subtracting
128 from a slot start. Derived alignment and char count must agree with the
accepted run. The complete three-field group currently requires L>=1.

| Missing output | Consumer interpretation |
|---|---|
| `text_slot_run` | This candidate path did not structurally accept a run. Not proof of no text or a corrupt capture; other parsing may still exist. |
| A slot's `archive_double_candidates` | The typed set was not produced/available in that output generation. Current accepted records emit all five; do not synthesize missing values. |
| `preslot_archive_double_candidates` | The supported parent context was not established, failed alignment/count consistency, or had no first line under the complete-group contract. The accepted slot run can remain present. |
| `preslot_archive_double_aliases` | Approved references are unavailable, including with older producers. Inspect canonical availability independently. |

Absence never means numeric zero. The public dictionary does not expose a complete
failure-reason taxonomy. Legacy/future record versions, non-empty extension or
truncation cause candidate abstention. Unsupported parent versions/map/optional
state, parent truncation, or parent alignment/count mismatch suppress only the
new pre-slot group and its aliases; they do not reject an otherwise accepted run.
No guessed offsets or numeric fallback values are authorized.

A terminal record carries the same structurally validated field representation.
Consumers must inspect `terminal_candidate` before visible-character analysis;
terminal values must not automatically become visible glyph properties. A
nonterminal flag alone also does not resolve the existing glyph ownership gap.

## Value authority and JSON

All eight typed fields preserve exactly their original eight archive bytes.
Production slices those bytes and decodes with `struct.unpack("<d", raw)` only
after the relevant structural gates. **`raw_bytes` is authoritative** for NaN
payloads, signed zero, nonfinite encodings and bit-exact roundtrip investigations.
Never reconstruct authoritative raw bits from `f64le`.

| Representation | Python candidate object | Existing inspection JSON |
|---|---|---|
| `raw_bytes` on these eight fields | Eight-byte `bytes` object | Lowercase hexadecimal string, 16 hex digits |
| Finite `f64le` | Python float, no intentional rounding | JSON number |
| NaN `f64le` | `"nan"` | `"nan"` |
| Positive infinity | `"inf"` | `"inf"` |
| Negative infinity | `"-inf"` | `"-inf"` |

The candidate formatter replaces nonfinite floats with strings; the inspection
formatter recursively converts bytes to hex. Directly serializing an unconverted
Python candidate is not the same transport contract. Consumers SHOULD preserve
the raw representation alongside decoded presentation, including when another
language's JSON number handling loses information. Recommended compatibility
policy: retain these intentional number/string and bytes/hex representations as
part of the typed candidate contract; do not silently switch NaN to null or zero.
JSON object member order is not field identity. Named lookup and preservation of
unknown additive data are preferable to positional assumptions.

Typed extraction and aliasing impose no finite, positive, normalized, 0..1,
unit-specific or equality condition. NaN, infinity, negative and arbitrary finite
values do not alone invalidate an otherwise supported structure. Equality of
P+0x20 and P+0x68 in 84/84 reviewed paragraphs is diagnostic observation of
distinct stored members, not an aliasing rule or a duplicate-copy contract.

RGB remains outside this contract: its existing three-byte projection and
unresolved typed width do not expose RGBA or an enclosing word32 field.

## Internal-role aliases and provisional labels

`preslot_archive_double_aliases` contains only these references into the same
run's canonical pre-slot dictionary:

| Alias | Target | Interpretation limit |
|---|---|---|
| `stored_minimum_line_layout_scale` | `P+0x20` | Stored aggregate/minimum role; not a freshness, range or UI compression guarantee. |
| `stored_first_line_layout_scale` | `P+0x68` | Assigned/limited AttrLine[0] storage role; not paragraph-wide or the untouched output of one helper call. |

One canonical field object holds each value. An alias contains no copied number
or bytes and appears only when its target exists. Unequal or nonfinite values do
not suppress either alias. Aliases are created after candidate acceptance, parent
validation and extraction; they may not control parsing, alignment, counts,
terminal state, ownership or typed decoding.

P+0x50 has no alias. The six Tier B descriptions in the field table MAY be used
as correlated diagnostic labels. They SHOULD NOT be presented as definitively
owned UI properties unless an application deliberately accepts and identifies
provisional semantics. Neither approved Tier A role confirms UI ownership.
Names such as compression_ratio, paragraph_scale, natural glyph width or an
unqualified maximum_length would overclaim the current contract.

The [semantic review](text_typed_field_semantic_contract_review.md) preserves
the field-specific evidence boundaries. Callback-dependent UI-to-model paths
remain unresolved. Phase 2E static-registration exhaustion and Phase 2F's
`Debugger detected (E0030)` stop before DlgRapido loading remain historical
limits; no bypass occurred. Further reverse engineering is not a prerequisite
for safe use of the bounded structural/raw API.

## Public surface and compatibility recommendations

These classifications define the recommended scoped candidate contract, not a
retroactive guarantee that every historical producer emitted the new keys.

| Key | Recommended classification | Stability rule |
|---|---|---|
| `archive_double_candidates` | Public typed candidate surface | Preserve canonical keys, eight-byte raw authority and decoded presentation. |
| `preslot_archive_double_candidates` | Optional public typed candidate surface | Preserve canonical identities, complete-group presence semantics and dynamic coordinates. |
| `preslot_archive_double_aliases` | Optional public reference metadata | Preserve approved mapping meanings; canonical entries remain authoritative. |
| `archive_type_evidence` | Diagnostic/research provenance | Existing analyzer metadata, not a required member of each production typed object or a runtime gate. `confirmed_archive_double` remains complementary evidence. |
| Pre-slot field `source` | Documented structural metadata, recommended part of compatibility contract | The three strings precisely distinguish serializer member and first-line ownership. Preserve their identities/spelling; consumers should not parse them as an executable schema. |
| `payload_relative_offset` | Public derived coordinate metadata | Stable meaning, variable numeric value; never a constant or primary field identity. |

The run-level `source="CParagraphe_slot_prefix_family_v2"` is a separate framing
provenance tag; it is not a typed-output schema version. Diagnostic confidence,
research RVAs and hypothesis annotations do not independently authorize new
semantic fields. Consumers SHOULD tolerate documented optional/additive keys
without treating diagnostic metadata as required selection criteria.

Practical compatibility hierarchy:

1. **Level 1:** candidate selection and existing canonical fields/coordinates.
2. **Level 2:** additive raw-preserving typed archive fields.
3. **Level 3:** additive internal-role/semantic reference metadata.

Level 3 evolution should not require rewriting Level 1/2 consumers. New aliases
MAY be added after separate evidence and compatibility approval. An existing
alias SHOULD NOT silently retarget. Removal or retargeting needs an explicit
compatibility decision and migration/deprecation or schema policy. One alias
resolves to exactly one available canonical key; multiple aliases for one key
require separate approval. No alias may become sole value storage authority.

Historical replay projections are explicitly approved, generation-specific test
comparisons, not consumer schema negotiation or permission to ignore arbitrary
changes. For the alias batch only the new alias map was removed when comparing
against its immediate baseline; canonical pre-slot and slot fields stayed in
that comparison. Older projections retain their separately approved scopes.
Historical runtime goldens were not rewritten wholesale.

**Schema decision: `recommended_before_external_stability_promise`.** No new
version is required merely to document today's additive candidate surface.
Before promising a stable external API, define output version negotiation and
deprecation rules for breaking changes. Vendor versions 5/4/8/2 and the run's
source suffix are not substitutes. This review adds no version number.

## Safe consumer lookup (pseudocode only)

```text
run = candidate_fields.get("text_slot_run")
if run is absent: return unavailable
fields = run.get("preslot_archive_double_candidates", {})
field = fields.get("P+0x20")                 # canonical identity
if field is absent: return unavailable      # never default to zero
aliases = run.get("preslot_archive_double_aliases", {})
target = aliases.get("stored_minimum_line_layout_scale")
if target is present:
    require target == "P+0x20" and target in fields
    require fields[target] is the canonical entry
raw = field["raw_bytes"]                    # bytes in Python; hex in inspection JSON
presentation = field["f64le"]               # finite number or documented string
preserve(raw, presentation, canonical_key="P+0x20")
# No inference about a UI compression control; no float-to-raw reconstruction.
```

## Earlier-document wording audit

Earlier reports are historical evidence, not replacements for this consolidated
consumer contract. No prior report is rewritten here.

| Document / wording | Current interpretation |
|---|---|
| [Empty-extension investigation](text_slot_empty_extension_investigation.md), opening “No production gate is enabled” and future-gate table | Historically correct shadow-stage boundary; misleading if read as current production status. Current exact-version/empty gate is implemented. |
| [Archive-type evidence](slot_style_archive_type_evidence.md), “current recognizer does not validate that full condition” | Stale current-tense production statement after gate implementation. |
| Same document, widths “all remain None” / width8 “evidence-only” | Correct for that analyzer-metadata batch and its hypothesis objects; must not be generalized to today's eight runtime typed objects. RGB/count/code exclusions remain valid. |
| Same document, crosswalk limited to five fixtures | Historical evidence scope subsequently expanded by the 84-paragraph structural investigation; not universal layout proof. |
| [Layout applicability](text_slot_layout_applicability.md), historical shadow/future-gate sections | Already explicitly superseded by its production-status introduction. Preserve history; no active contradiction requiring rewrite. |
| [Slot double promotion](text_slot_archive_double_promotion.md), batch exclusions of pre-slot promotion | Describes the five-field batch; not a current ban on the subsequently implemented pre-slot group. |
| [Pre-slot crosswalk](text_preslot_crosswalk_investigation.md), next step proposing object-level typed-output work | Completed later by parent-gated pre-slot production output; historical next-step text is no longer current guidance. |
| [Pre-slot promotion](text_preslot_archive_double_promotion.md), no semantic aliases in that batch and subsequent review recommendation | Three canonical entries remain correct. The later separate alias map adds only two internal roles, not UI aliases. |
| [Semantic review](text_typed_field_semantic_contract_review.md), future additive aliases / none implemented “here” | Correct review-only history; its recommended two-role batch was subsequently implemented. Tier decisions remain unchanged. |
| [Internal-role aliases](text_preslot_internal_role_aliases.md) | Current mapping, reference authority and UI limitations agree with implementation. |

Exactly one recommended next maintenance batch: **documentation-only historical
status banners and links to this contract in the superseded stage reports**.
Preserve their original evidence/results and avoid presenting old next steps as
current work. No further aliases, semantic promotion, parser change or dynamic
investigation is recommended by this review.

## Acceptance answers

| # | Question | Decision |
|---|---|---|
| 1 | Five slot identities? | `archive_double_candidates`: `0xc`, `0x14`, `0x1c`, `0x40`, `0x48`, each relative to its own record. |
| 2 | Three pre-slot identities? | `preslot_archive_double_candidates`: `P+0x20`, `P+0x50`, `P+0x68`, within the independently derived parent context. |
| 3 | Are aliases canonical? | No; canonical structural entries remain authoritative. |
| 4 | Which aliases exist? | Only stored_minimum_line_layout_scale -> P+0x20 and stored_first_line_layout_scale -> P+0x68. |
| 5 | Raw or float authority? | `raw_bytes`; float/string is decoded presentation. |
| 6 | Width8 meaning? | Eight serialized archive bytes, not semantic confidence or precision. |
| 7 | Absent pre-slot output? | Supported parent/first-line/alignment/count evidence was not established; not zero and not necessarily slot rejection. |
| 8 | Is P+0x50 always C+262? | No; use its derived payload_relative_offset. |
| 9 | Are P+0x50/P+0x68 paragraph-wide? | No; both are AttrLine[0] fields. |
| 10 | Terminal values are visible glyph properties? | No; terminal and glyph ownership must remain distinct. |
| 11 | Nonfinite values structurally valid? | Yes, numerical nonfiniteness alone does not invalidate supported structure. |
| 12 | Provisional UI labels? | Height, width, slant, character spacing, rotation and maximum length remain correlated Tier B descriptions. |
| 13 | Safe internal names? | Only the two stored model-side roles in the alias map, with their narrow limits. |
| 14 | May aliases control parsing? | No; aliases follow accepted canonical extraction. |
| 15 | Future alias compatibility? | Additive approval, no silent retarget, explicit removal/migration decision; retain canonical value authority. |
| 16 | Public versus diagnostic? | Typed dictionaries/alias references are recommended public candidate surface; source/derived offsets are documented public structural metadata; archive_type_evidence is analyzer provenance. |
| 17 | Schema version now? | Recommended before external stability promise; not implemented or required for this documentation batch. |
| 18 | Stale wording? | Old no-gate, evidence-only-width, five-fixture scope and now-completed future-step statements; see audit for historical versus current distinctions. |
| 19 | Single next maintenance step? | Historical-status banners and links in superseded reports, documentation only. |
| 20 | More reverse engineering needed for structural API use? | No. It would address separate semantic questions, not this raw-preserving structural contract. |

## Review validation scope

Implementation references: [candidate construction and gates](../src/type3_clipboard_codec/parsers/text/text_slot_candidate.py)
and [inspection JSON conversion](../src/type3_clipboard_codec/inspect/formatters.py).
Raw-byte retention, nonfinite presentation, alias references and downstream parent
gating were reviewed in code. Prior recorded baseline is 1486 tests and a
104-fixture historical replay with runtime/source equality and ready_for_review;
these are prior results, not tests rerun for this document. Only this new document
is delivered. Production, fixtures and source-integrity metadata remain untouched.
