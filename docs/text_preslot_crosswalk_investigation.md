# CParagraphe current pre-slot internal crosswalk

> **Historical status note**
>
> This document records the shadow crosswalk investigation. Its proposed next
> step was subsequently completed by parent-gated pre-slot production output.
> The 84-paragraph evidence and historical readiness conclusions below are
> preserved. For current consumer-facing interpretation, use the
> [text-slot typed candidate consumer contract](text_slot_typed_candidate_contract.md).

`pre_slot_crosswalk_readiness = broad_current_corpus_supported`.

All 84 analyzer-recognized current text paragraphs independently produce
`P_origin - C_origin = 182`, and their derived first AttrChar positions and
character counts agree with production alignment. The three object-level
crosswalks are supported across those 84 paragraphs. **First record P+128 / C+310
is limited to the 80 single-line paragraphs**: four two-line paragraphs instead
start at P+196 / C+378. No production source, output, semantics or fixtures changed.

## Scope progression and origins

The historical `exact_internal_stream_crosswalk` finding covered five controlled
maximum-length fixtures. This investigation adds independent broader corpus
evidence; it does not replace or rewrite that historical scope. Recommended new
wording is: **supported across all reviewed structurally current CParagraphe text
paragraphs recognized by the existing analyzer**. This is not a universal Type3
layout or proof of global MFC object/class-reference framing.

C remains the byte immediately following the analyzer-recognized CParagraphe
runtime-class descriptor. Its absolute position is `base + node.payload_offset`.
P remains the first current CTxtPara emission through CParagraphe+0xAC, namely
the first embedded AttrPara version word. The production record position is
not an input to `derive_preslot(payload)`. The separate `compare_alignment`
function receives its completed result and checks the production start and count.

## Code-derived cursor model frozen before corpus comparison

Primary provenance is the previously audited
[Phase 2D prefix](C:/TypeEdit_2009/_reverse_engineering/reports/phase2d_182_prefix.md),
[ordered emissions](C:/TypeEdit_2009/_reverse_engineering/data/phase2d_prefix_ops.csv),
[C-origin resolution](C:/TypeEdit_2009_reverse_engineering/reports/phase2d_c_origin_resolution.md),
and [promotion review](C:/TypeEdit_2009_reverse_engineering/reports/phase3_codec_promotion_review.md).
The existing [version evidence](../tools/text_slot_layout_version_evidence.json)
supplies the current AttrPara/AttrLine sizes and legacy branches. These external
evidence files were read only; no callback or anti-debug investigation was run.

| Ordered bounded segment from C | Width / condition | Serializer provenance |
|---|---|---|
| Cube: two vectors | 2 x 3 x 8 | CObDao 58462; LGeom 110F0, CVect3D 117A8/117E9/1182A |
| Stored flags, base version, four members | 6 x 4 | CObDao 58482/58498/584A5/584B2/584BF/584CC |
| GUID version and GUID | 4 + 16 | CObjGuid 5D9AA/5D9B7 |
| GUID-property count | 4 | 5D324 |
| Each key and value | DWORD length then exactly length bytes | string helper 5CDA0, writes 5CDF8/5CE09 |
| Additional map count | 8; only zero supported in this walker | 5817D |
| CObDaoFin optional word | Only proven-absent state supported | 5B303; original flag preimage analysis |
| Paragraph +A8,+D8,+E4,+EC | 4+8+4+4 | BD07/BD17/BD27/BD37 |
| Paragraph vector +B8 | 3 x 8 | BD4C -> CVect3D |
| P: embedded AttrPara | version first; then total 52 for exactly v4 | CTxtPara 4E954 -> AttrPara 4E212..4E26D |
| Line count | 4, at P+52 | CTxtPara 4E920 current list sequence |
| AttrLine list | each version first; total 68 only for exactly v4 | CTxtAttrLine 4DDF0, version write 4DE17 |
| Char count | 4 after all L lines | CTxtPara current list sequence |
| First AttrChar | next cursor byte | CTxtPara 4E9F9 nested serialization |

The generic reviewed expression is `148 + G + M + F`; the implemented walker
supports arbitrary bounded GUID-property string pairs, an empty extra map and
unambiguously absent optional Fin word. It does not insert padding or use 182
as a stopping condition. In all 84 real paragraphs the variable string emission
contributes G=34, M=0 and F=0, giving base=138 and paragraph=44. String contents,
known numeric values and fixture names are never structural selectors.

The local parent sequence is AttrPara52 + count4 + L x AttrLine68 + count4:
`first AttrChar = P + 60 + 68*L`. AttrLine i starts at P+56 plus the lengths of
previously validated lines. No assumed L=1 or backwards subtraction from the
production start is used. Counts and lengths are bounded by available bytes.

## Required versions and fail-closed states

* **CObDao exactly 8** at its code-derived version field: the current base layout
  includes the map serialization. Load checks versions 1..8 at 58549..5856C and
  gates the map at 586D8. This is a relevant base-layout discriminator.
* **CObjGuid exactly 2** before using its property-list layout. Store 5D9AA writes
  the DWORD at RVA AEB9C; read-only PE inspection confirms the value 2. The load
  comparison at 5D9E8 gates properties at version >=2. Higher versions are not
  assumed compatible.
* **AttrPara exactly 4**, before using its current 52-byte size.
* **Each AttrLine exactly 4**, before advancing its current 68-byte size.

AttrChar5 and CPropertyExtend5 are prerequisites already enforced by the
production candidate used for the final comparison. They are not needed to
calculate the preceding parent cursor and are not rescanned by this analyzer.
CTxtPara has no own version emission. No CParagraphe descriptor schema=6 rule or
unserialized static version state was invented; the claim remains structural
support for the reviewed current-store path, with global MFC schema unresolved.

Stored CObDao flags must contain the current store OR-mask 0x01001000. Original
Fin kinds 0x01000010/0x01000100 can map to stored values 0x01001010/11 or
0x01001100/01. Those values have ambiguous original preimages, so the walker
returns unresolved rather than guessing whether a four-byte optional word exists.
Other compatible stored flags exclude those optional-write preimages.

Unsupported versions stop immediately at the version word. Nonempty extra maps,
ambiguous flags and incompatible flags remain unresolved. Truncation never reads
past the payload. `p_origin` and `first_attrchar` remain null on failed walks;
`tentative_p_origin`, when present, is diagnostic only and never counted as
established evidence. A completed walk without production alignment is reported
as insufficient_context; start/count disagreements are mismatch.

## Broad corpus results

Every existing sample `*.txt` was considered. Content validation found 116 valid
captures out of 126 files; ten existing inspect reports are explicitly listed as
invalid hex inputs, not silently discarded paragraphs. The 32 valid captures
without recognized CParagraphe remain included in the input inventory.

| Metric | Count |
|---|---:|
| Valid captures examined | 116 |
| Captures with recognized CParagraphe | 84 |
| CParagraphe nodes examined | 84 |
| Paragraphs with production candidate | 84 |
| Independently established P origins | 84 |
| Exact +182 | 84 |
| Other shifts | 0; histogram {} |
| First-record and count exact agreement | 84 |
| Unsupported parent / truncated / mismatch / unresolved / insufficient context | 0 / 0 / 0 / 0 / 0 |
| Base-length histogram | 138: 84 |
| AttrPara versions | 4: 84 |
| AttrLine versions | 4: 88 |
| CObDao / CObjGuid versions | 8: 84 / 2: 84 |
| Line-count histogram | 1: 80; 2: 4 |
| First-record P-relative histogram | 128: 80; 196: 4 |
| First-record C-relative histogram | 310: 80; 378: 4 |

The scan includes basic/legacy-named, style, color, spacing, maximum-length,
boundary and multiobject captures without family filters. Names are reporting
metadata only. Existing multiobject captures yield one recognized CParagraphe
descriptor each under the current scanner, not multiple independently recognized
paragraph nodes. Real multiple-node coverage therefore cannot be claimed.
In-memory two-node and three-node tests verify independent node boundaries,
reversed order, mixed supported/unsupported states and enclosing-offset changes.
No pairing uses text, expected values, chain order or visible ownership.

## Object-level crosswalks and archive types

The P-relative fields are derived only after the complete parent walk. P+80 and
P+104 refer specifically to **AttrLine[0]**, not one paragraph-wide line field
shared by every line. They are absent when L=0; synthetic zero-line tests retain
that distinction. All 84 real paragraphs have at least one current line.

| Coordinate result in all 84 | Code-confirmed member | Archive representation | Future typed-output eligibility |
|---|---|---|---|
| P+32 -> C+214 | CTxtAttrPara+0x20, write 4E253 | binary64, 8 bytes, reviewed little-endian stream | ready_for_typed_representation_review |
| P+80 -> C+262 | CTxtAttrLine[0]+0x30, write 4DE4B | binary64, 8 bytes, reviewed little-endian stream | ready_for_typed_representation_review |
| P+104 -> C+286 | CTxtAttrLine[0]+0x10, write 4DE72 | binary64, 8 bytes, reviewed little-endian stream | ready_for_typed_representation_review |

All three meet independent position derivation, confirmed archive type, no value
selector and fail-closed unsupported parent handling for this scoped path.
Readiness is for review, not active production permission or universal framing.
C+262 remains maximum-length-correlated with unresolved UI-to-model callback
ownership. A and B remain **distinct serialized fields** with different member
provenance; their equality does not make them duplicate copies. No semantic
status, Maximum Length formula or compression conclusion was promoted.

Post-structure diagnostic equality: A/B are numerically equal and raw-bit equal
in 84/84 first-line pairs. Both equal 1.0 in 50 paragraphs, with seven other
observed numeric states across the remaining 34. Requested-length values are
0.0 in 75 paragraphs and each of 0.05, 0.1, 0.04, 0.06, 0.0745, 0.07458,
0.0746, 0.07466 and -0.06 in one paragraph. Full histograms are available from
the CLI. None of these values influences recognition. Synthetic NaN/Inf and
unequal A/B values preserve the identical structural result.

## Validation and preservation

New tests cover legacy/future AttrPara and AttrLine, base versions, every prefix
truncation byte including line-count/line-record/char-count boundaries, impossible
counts/string lengths, unsupported maps and ambiguous flags. Property-length
mutations produce shifts 181, 183 and 213; report-level tests retain 181/183 in
the histogram alongside an unsupported paragraph. No synthetic captures are saved.

The corpus test freezes complete production objects and parser-chain choices for
116 captures before analyzer execution and compares them exactly afterwards,
including `archive_double_candidates`; no additive projection is used here.
Input order and renamed-file tests also pass. Existing maximum-length and
compression analyzer files and outputs remain covered by the unchanged full suite.

| Check | Result |
|---|---|
| New pre-slot tests | 39 passed |
| Typed archive doubles | 26 passed |
| Current/empty production gate | 29 passed |
| Applicability / empty extension / archive metadata | 36 / 26 / 16 passed |
| Historical replay assertion | 1 passed; 104 fixtures, runtime_outputs_equal=true, canonical_source_equal=true, readiness=ready_for_review |
| Combined focused run | 173 passed in 19.07s |
| Full actual checkout | 1422 passed; baseline 1383 + 39 new tests |
| Ruff / E4,E7,E9,F | Both passed after replacing one test-only assigned lambda with a named function |
| Git whitespace and raw preservation | Passed; 204 fixture files and 96 source-tree files byte-exact, no additions/removals |

Only this document, `tools/analyze_text_preslot_crosswalk.py` and
`tests/integration/test_text_preslot_crosswalk.py` are added. No production source
or protected source-baseline update is needed; new files are outside existing
protected source sets. No raw Python source hash was introduced into tests or
evidence policy. Raw source/fixture preservation was audited separately.

The next smallest safe step is review of a minimal object-level typed-output
contract using this independently walked parent structure, retaining raw bytes
and explicit first-line ownership for the two AttrLine members. That would need
a production parent gate and bounded compatibility review. This task implements
none of those production fields and stops before semantic/callback work.
