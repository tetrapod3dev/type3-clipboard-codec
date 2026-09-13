# Optional parent-gated pre-slot archive doubles

Three pre-slot binary64 fields are now exposed as an approved additive production
candidate output. **The parent gate only controls the new dictionary; existing
slot candidate acceptance is unchanged.** UI/model semantic ownership is unchanged.

## Contract and placement

The existing run-level candidate dictionary is the narrowest suitable owner.
The fields are not repeated in every slot. The only production file changed is
`src/type3_clipboard_codec/parsers/text/text_slot_candidate.py`, containing two
small private helpers: `_derive_current_preslot_layout` and
`_preslot_archive_double_candidates`. The bounded walk fits in that module without
a separate framework or new protected module. No tools/evidence import is used.

The new helper is called only after the entire existing slot candidate has been
accepted and its old output dictionary constructed. Its failure returns no new
key, not a failed candidate. Existing F4, current/empty204 validation, count,
terminal, ordering, uniqueness and five per-record doubles code remain intact.
`type3_chain_parser.py` is unchanged.

Accepted parent evidence adds this run-level dictionary:

```python
"preslot_archive_double_candidates": {
    "P+0x20": {
        "raw_bytes": eight_original_bytes,
        "f64le": decoded_value,
        "typed_width": 8,
        "payload_relative_offset": independently_derived_p + 0x20,
        "source": "CTxtAttrPara+0x20",
    },
    # P+0x50: CTxtAttrLine[0]+0x30
    # P+0x68: CTxtAttrLine[0]+0x10
}
```

There are exactly three entries. No semantic aliases such as maximum_length or
compression are introduced. The source identities explicitly retain first-line
ownership for the two AttrLine entries. No second-line values are exposed, even
when the paragraph contains multiple lines. Existing per-slot
`archive_double_candidates` is unchanged and separate.

Finite doubles use the existing raw-preserving contract: `<d`, eight bytes,
Python float without rounding or unit conversion. Nonfinite presentation uses
`"nan"`, `"inf"`, `"-inf"`, matching the existing per-record implementation.
Raw bytes remain authoritative for negative zero and NaN sign/payload bits.
No equality, finite/range condition, expected UI number or fixture identity
controls eligibility. Strict JSON output remains supported.

## Independent current parent gate

The production walk translates the already reviewed
[pre-slot shadow evidence](text_preslot_crosswalk_investigation.md). Its input
is the existing CParagraphe payload beginning immediately after the recognized
descriptor (C). It never discovers P from a slot position, an absolute raw
offset, a numeric value, or a fixed C+182/C+310 rule.

Ordered operations are: two vector emissions (48); CObDao flags/version/four
members (24); CObjGuid version/GUID (20); GUID property count (4); every actual
key and value DWORD byte length followed by those bytes; empty additional map
count (8); proven-absent optional CObDaoFin word; paragraph members/vector
(4+8+4+4+24). The resulting cursor is P.

Required versions are exact CObDao=8, CObjGuid=2, AttrPara=4 and **every** AttrLine=4.
Current widths are used only after the relevant version check. Higher versions
are not assumed compatible. Property/string/line work is bounded by available
payload bytes, itself bounded by existing candidate resource limits. There is
no hard-coded property count or G=34 string total.

Only empty additional maps are supported. Stored flags must contain the current
0x01001000 mask. Values 0x01001010/11 and 0x01001100/01 retain ambiguous original
flag preimages for the optional Fin word and cause abstention; the walker does
not guess four bytes or treat stored flags as the original enum.

From P the walk reads AttrPara v4 (52 bytes), line count DWORD, then individually
validated AttrLine v4 records (68 bytes each), then char count DWORD. The next
cursor is `P + 60 + 68*L`. Only afterwards does the optional output helper compare
this cursor and count with the existing candidate's first position and slot
count. Alignment/count mismatch omits only the new group.

For simplicity the complete group requires **L>=1**. For L=0, A may exist in the
archive but the entire new group is omitted; no AttrLine[0] is invented. Truncated
input, unsupported versions/maps/flags and missing first line fail closed for
this output. Parent failures do not become new candidate-selection failures.

The old scanner can independently react to a parent mutation containing its
version5 token. Tests isolate parent-only failures with opaque parent bytes;
the old scanner rules are not relaxed to make synthetic inputs pass.

## Field status and dynamic positions

| Output key | Structural source | Runtime archive representation | Structural-source status | Semantic status |
|---|---|---|---|---|
| P+0x20 | CTxtAttrPara+0x20 | f64le / width8 | reviewed source, current parent walk and alignment validated | unchanged |
| P+0x50 | CTxtAttrLine[0]+0x30 | f64le / width8 | reviewed first-line source, current parent walk and alignment validated | unchanged; maximum-length correlation is not an end-to-end callback proof |
| P+0x68 | CTxtAttrLine[0]+0x10 | f64le / width8 | reviewed first-line source, current parent walk and alignment validated | unchanged |

These source/type facts come from vendor serializer operations 4E253, 4DE4B and
4DE72 respectively. The first and third remain distinct serialized members,
regardless of their observed numeric equality. No deduplication is performed.

| Independently derived P-C | Emitted payload-relative field positions |
|---:|---|
| 181 | 213, 261, 285 |
| 182 | 214, 262, 286 |
| 183 | 215, 263, 287 |
| 213 | 245, 293, 317 |

All four shifts are tested in memory with both one and two lines. Production
uses P-relative offsets only; displayed C-relative values are results.

## Corpus and compatibility

Actual pre-change parser objects and chain choices were frozen for 116 valid
captures before production edits. Removing **only** the new run-level key from
post-change objects yields exact equality for all 116. No projection removes the
existing per-record typed fields in this batch's before/after check. An AST
comparison also verifies the old selection body, F4, 204 validator, slot-local
double extraction and old candidate dictionary are unchanged.

All 84 recognized paragraphs emit the group: 80 one-line and four two-line.
There are zero parent gate failures or decode failures in this corpus. The
positions happen to be 214/262/286 in all 84; they are derived, not selectors.
The four multi-line paragraphs have first AttrChar P+196/C+378, and correctly
retain AttrLine[0] values. All outputs agree with the unchanged shadow extraction.

Real captures expose at most one recognized CParagraphe per capture under the
existing scanner; no real multiple-node coverage is claimed. Synthetic three-node
tests mix supported and unsupported parents, reverse node order, and shift the
enclosing raw offset while validating each node independently. A renamed unchanged
capture also produces identical output. No synthetic captures were saved.

Historical migration uses the existing explicit approved typed-output projection.
`prior_candidate` additionally removes the new run-level key, and one historical
key-order assertion now uses that same projection. A separate projection removes
only this batch's key for comparison against the immediate pre-change output.
Historical runtime goldens and all fixture bytes remain untouched.

## Source integrity and validation

The single production file was committed locally first as
`83bdde4a6b66dc011aa5990ad18ea03be04d0c18`; no push was performed. Its committed blob
`f939e32789dddb0348f8270a81e8b36bb0765e8a` was hashed using
`tests/source_integrity.py` with the approved CRLF-to-LF-only policy. Canonical SHA:
`d401abfb88619c4fda03319d8c74d1703ffc679029e37687be861758e2e0d407`.

Only the current entry for that production file changed out of 49 protected
source records. The previous five-field baseline joins the retained original
and 204-gate provenance; legacy raw provenance is preserved. Groups/inventory
are unchanged. The reason records approved additive three-field output after
independent parent validation, with slot acceptance and semantics unchanged.

| Validation | Result |
|---|---|
| New production pre-slot tests | 46 passed |
| Shadow pre-slot / five slot doubles | 39 / 26 passed |
| Production204 / applicability / empty extension / archive metadata | 29 / 36 / 26 / 16 passed |
| Historical replay assertion | 1 passed; 104 fixtures, runtime_outputs_equal=true, canonical_source_equal=true, readiness=ready_for_review |
| Combined focused run | 219 passed in 20.52s |
| Full actual checkout | 1468 passed in 92.95s; baseline 1422 + 46 new tests |
| Ruff full rules / E4,E7,E9,F | Zero new full-rule diagnostics (13 pre-existing: 11 C408, 2 I001); E4/E7/E9/F passed |
| Git whitespace / fixture raw hashes | Passed; all 204 fixture files byte-exact, no additions/removals |

Tests cover all four parent versions with legacy/future/high-bit variants, every
parent truncation byte, impossible lengths/counts, unsupported map/optional state,
alignment/count contradictions, zero lines, dynamic shifts, arbitrary unequal
finite values, negative values, infinities and payload/signaling NaNs. Existing
candidate equality is checked when the new parent group abstains.

Changed companions are the new production test file, test-only projection helper,
one historical migration assertion, the single source baseline record and this
document. No Maximum Length/compression analyzer, RGB field, F4, terminal semantics,
non-empty support, callback ownership or chain parser was changed.

The next smallest step is review of this additive archive contract and its scoped
parent gate. Semantic ownership and UI callback evidence remain separate blockers;
no second-line promotion, non-empty parsing or further reverse engineering begins
automatically.
