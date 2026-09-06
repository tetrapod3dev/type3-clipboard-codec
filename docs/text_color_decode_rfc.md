# Text Color Decode RFC: Phase 1 Evidence

Phase 1B update: changed bytes independently support the variable span
**0x8B..0x8D**, but the typed field start/width remain unresolved. A three-byte
RGB value, a trailing-zero u32le view, and a leading-zero big-endian view remain
compatible. See [Phase 1B](#phase-1b-byte-boundary-and-chunk-role-audit).

Status: strong field candidate, analyzer only. Parser color implementation and
color ownership are not ready. Anchor ownership remains closed out and deferred;
this RFC does not reopen it or change active anchors, `matched_chain`, or fallback
behavior. No MFC parser refactor is performed.

## Scope and execution

`tools/analyze_text_color_record.py` separates binary field observations from
record-to-object ownership. It supports default text, `--json`, `--markdown`,
repeatable `--fixture NAME`, and `--no-oracle`.

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe tools/analyze_text_color_record.py --json
.venv/Scripts/python.exe tools/analyze_text_color_record.py --json --no-oracle
```

The default corpus contains the requested three single-object, five two-object,
and four three-object fixtures. Two existing non-color controls,
`text_height_30mm.txt` and `text_width_50_percent.txt`, test unrelated-variable
stability. No fixtures were created. There are 14 fixtures and 140 full-fit chunks.

## Structural inventory and oracle isolation

The analyzer uses only the current scanner and origin logic, not the active
color-selection pipeline. CParagraphe candidate chunks start at payload-relative
47 with stride 204. A "valid record" means only a complete in-bounds chunk, not
a verified uniform semantic record. Header, tail, and nonmatching chunks remain
visible; expected colors and palette success never filter chunk validity.

Candidate start offsets are limited to 0x83..0x95 inclusive. The four-byte probes
can end at 0x98. Each position is decoded as u8, u16le, u32le, and u32be, the last
for comparison only. All 228 offset/type/encoding combinations are reported.

| Encoding | Definition |
| --- | --- |
| TYPE3_RAW_GBR0 | Existing `TYPE3_COLORS_BY_RAW`: G, B, R, 00 bytes |
| RGB0 | Existing `TYPE3_COLORS_BY_RGB0_RAW`: R, G, B, 00; u32le = 00BBGGRR |
| BGR0 | B, G, R, 00; u32le = 00RRGGBB, derived from existing palette `hex_rgb` |

The existing raw table is not BGR0. Older analyzer labels calling that table
00RRGGBB are not an encoding specification. Palette aliases retain first-entry
behavior. Zero maps to Black but may be padding and contributes no selection score.

Oracle-free ranking maximizes nonzero palette observations, distinct nonzero
palette values, then fixture coverage. Primary ties abstain. u32be is excluded
from primary selection by its predeclared comparison-only role. Neither names,
expected colors, intent, anchors, chain indices, source ownership, nor descriptor
absolute positions enter selection.

All raw structures are serialized, and candidate selection and public provenance
tables frozen before the first oracle load. Oracle diagnostics have a separate
result pool and cannot update structural status or rank. Oracle on/off, missing
intent, and changed expected colors preserve structure and best-candidate selection.
Only intent color frequencies survive reporting; labels and attempted order do not.

JSON uses column tables and zero-based pools for compact reporting.
`field_start_summary.rows` contains all structural evaluations;
`oracle_summary.candidate_rows` joins by candidate index to the primary controls,
repeatability, mixed presence and unrelated-control stability. `_ref` entries
resolve to that section's pool. These are report references, not archive PIDs.

## Runtime descriptor and payload provenance

Every chunk reports runtime descriptor start/schema/class name, class payload
start, payload-relative record start, record-relative color offset, and traversal
ordinal. Schema is the class-level candidate 6, not color/style metadata. The
payload follows the six-byte descriptor prefix and eleven-byte CParagraphe name.
Descriptor positions are diagnostic, not proven semantic TYPE3 object boundaries.

The candidate expression is `CParagraphe payload + 47 + ordinal * 204 + 0x8B`,
subject to the provisional chunk model, not an implemented decoder rule.
Prefix-shift tests move descriptor positions without changing relative starts,
decoded windows or ranking. This invariance test does not establish record
semantics. MFC discovery improves provenance terminology only; see the
[compatibility audit](typeeditzone_mfc_archive_investigation.md).

## Strongest field candidate

The strongest primary candidate is **0x8B / u32le / RGB0**. Of 140 chunks, 117
values map to the palette: Army Green 67, Navy Blue 19, Black 31. The 86 nonzero
observations occur in 11 fixtures. All 23 unmapped chunks remain in the inventory.

| Single-object control | Exact raw u32le | Four bytes | Palette observations | Chunks |
| --- | --- | --- | ---: | ---: |
| default_text | 0x00000000 | 00 00 00 00 | Black ×9 | 10 |
| Army Green | 0x0098CC98 | 98 CC 98 00 | Army Green ×8 | 10 |
| Navy Blue | 0x00CC6030 | 30 60 CC 00 | Navy Blue ×8 | 10 |

The three controls separate among decodable observations, not across every
provisional chunk. Both nonblack controls have unmapped chunk 0 and final chunk;
Black has one unmapped final chunk. Full raw distributions retain those values.

At 0x8C/0x8D, Army Green shifts to 0x000098CC/0x00000098 and Navy Blue to
0x0000CC60/0x000000CC. They do not map to the capture colors under the tested
tables. Height and width controls preserve Black ×9 at 0x8B.

The **0x8A / u32be / BGR0** comparison also has 86 nonzero observations and the
same color-separation evidence: a preceding zero allows an alternative four-byte
view. This audit prefers the little-endian candidate but does not independently
prove its boundary or rule out that view. No first-pass status is confirmed.

## Multi-object multisets, not owners

Observation multiplicity is retained. Eight Green observations plus one Navy
are not equal to a one-Green/one-Navy object multiset. Expected-color presence
is reported separately; duplicate copies are never collapsed into object counts.

| Contrast | CParagraphe chunks | Decoded observations at 0x8B | CPropertyExtend sections |
| --- | ---: | --- | ---: |
| Two grouped, Green/Green | 10 | Green ×8 | 5 |
| Two grouped, Green/Navy | 10 | Green ×8 | 5 |
| Two not-grouped, Green/Green | 14 | Green ×11, Black ×1 | 6 |
| Two not-grouped, Green/Navy | 14 | Navy ×11 | 6 |
| Two not-grouped, reversed selection | 10 | Green ×8, Black ×1 | 6 |
| Three grouped, same color | 10 | Green ×8, Black ×1 | 9 |
| Three grouped, mixed color | 10 | Green ×8 | 9 |
| Three not-grouped, same color | 6 | Green ×4, Black ×1 | 11 |
| Three not-grouped, mixed color | 6 | Green ×4 | 11 |

Green/Navy abbreviate Army Green/Navy Blue; Black observations may be padding.

The grouped two-object same/mixed pair changes only raw slot 0 at 0x8B. Both
values are unmapped; eight Green copies remain unchanged. Each side has three
distinct raw values and seven duplicate observations. No slot is assigned to A/B.

Grouped/not-grouped mixed chunk counts differ (10/14), so changed-slot alignment
abstains. Raw duplicate counts are 7/10. Traversal ordinals are provenance, not
semantic stored order. Both three-object same/mixed pairs change slot 0 only,
with grouped/not-grouped counts 10/6. Counts do not map one-to-one to intended
objects or unique colors; grouping-related section counts do not prove ownership.

None of the four mixed fixtures contains both intended colors in CParagraphe
chunk observations alone. Adding bounded CPropertyExtend observations gives both
color names in all four, but strict multiset equality still fails in all four.

## Bounded CPropertyExtend evidence

Sections require a length-prefixed OBJECTINFOS/OBJETINFOS name followed by length
6 and CObDao. This is textual framing, not a runtime descriptor or object boundary.
No anchor signature, coordinates, owner oracle, or anchor-record classification
is reused. The tested local u32le start window is CObDao+24..+30 only.

Detailed rows show +30, all seven probe raw values, three palette interpretations,
and whether the +30 value appears in CParagraphe. Aggregate distributions retain
all seven positions. There is no broad payload palette scan.

Across 73 sections, +30/RGB0 yields Green ×10, Navy ×3, Black ×27, with 33 unmapped
values. Grouped Green/Green has a Green side observation; grouped Green/Navy has
Navy; not-grouped Green/Navy has Green. Each three-object mixed fixture has one
Green and one Navy side observation. Zero and unmapped sections remain visible.

All three primary single-object fixtures give only Black/zero at this probe. It
fails primary isolation, and the section model does not establish a uniform color
field. General-field status remains `no_stable_cpropertyextend_color_field_found`.
The repeated +30 side evidence is not promoted to a universal decoder or owner rule.

## Readiness and verification

| Area | Readiness |
| --- | --- |
| CParagraphe 0x8B/u32le/RGB0 | strong_candidate_analyzer_only |
| Uniform 204-byte color record semantics | Unresolved; header/tail mismatches |
| Unique field boundary versus shifted big-endian view | Unresolved |
| General CPropertyExtend color field | no_stable_cpropertyextend_color_field_found |
| Parser color implementation | Not performed |
| Color ownership | not_ready; not assigned |
| MFC parser refactor | Not performed |

Default outputs: text 2,308 bytes; Markdown 2,398 bytes; JSON 98,110 bytes.
No-oracle JSON: 77,944 bytes. All 228 candidates, 140 chunk rows and 73 section
rows are retained. Limits: 16 fixtures, 32 nodes, 24 chunks per paragraph, 16
sections per CPropertyExtend, 1 MiB input payload. Missing fixtures and bounded
inventories are explicit. No raw payload dumps are emitted.

Tests cover output bounds, exact values, candidate status, oracle isolation,
changed/missing intent, strict multiset multiplicity, grouping/scaling contrasts,
prefix shifts, narrow scan independence, zero-only abstention, and unchanged
parser objects/source.

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m pytest tests/integration/test_text_color_record_analysis_cli.py -q
.venv/Scripts/python.exe -m pytest -q
```

Integration: 11 passed. Full suite: 345 passed (previous baseline 334).
Parser, decoder, model, scanner, anchor closeout conclusions and active color
selection remain unchanged.

## Phase 1B: Byte Boundary and Chunk Role Audit

`tools/analyze_text_color_field_boundary.py` is a separate small analyzer. It
examines the requested 11 existing fixtures: the three primary single-object
controls, four two-object controls and four three-object controls. No new fixture
capture, parser implementation, ownership inference, chain mapping or MFC
refactor is performed. The Phase 1 findings above remain historical evidence;
Phase 1B adds the following narrower boundary and local-role conclusions.

### Method and scope

The provisional model remains payload-relative 47 with stride 204. Exact byte
comparisons are limited to record-relative 0x80..0x98 inclusive. Each chunk reports
bytes 0x89..0x90 and u32le/u32be views at 0x8A/0x8B/0x8C with the existing palette
interpretations. Column tables preserve all chunk rows without raw payload dumps.

The only outside-window chunk reads are fixed, previously observed context
checks: OBJETINFOS_CLASSNAME at +53, its neighboring length 6, and CObDao at +77.
These identify a header-like context; they are not a new search or comparison
across the rest of the chunk. Consequently, whole-record equality except color
bytes is **untested** and reported as null. The analyzer separately reports
equality except the candidate span within the bounded window.

The boundary is selected from the unique most-repeated contiguous changed-byte
pattern shared by all three pairwise control comparisons. Fixed-marker chunks
are excluded from that repeated-context pattern, independently of palette
matches. Chunk roles use that context and terminal positions, not expected color
or palette scores. A synthetic shifted-delta test moves the selected boundary;
disabling all palette mappings does not change the boundary or role labels.

The complete structural report is serialized before oracle/intent loading.
Oracle assessment can report decoding consistency but cannot modify boundaries,
roles or alignment. With `--no-oracle`, the entire JSON except `oracle_summary`
is identical, including answers. Changed expected colors leave structure intact.

### Actual changed-byte boundaries

For each ordinal 1 through 8, all three comparisons (Black/Green, Black/Navy,
Green/Navy) change exactly **0x8B, 0x8C, 0x8D**, one contiguous three-byte run.
That is eight ordinal observations and 24 pairwise comparisons. In all 24
fixture/chunk observations, both neighboring bytes 0x8A and 0x8E are zero.

| Ordinal | Black -> Army Green | Black -> Navy Blue | Army Green -> Navy Blue |
| --- | --- | --- | --- |
| 0 | 0x8D..0x8E | 0x8C..0x8E | 0x8C..0x8E |
| 1..8, each | 0x8B..0x8D | 0x8B..0x8D | 0x8B..0x8D |
| 9 | No changes | No changes | No changes |

The local bytes 0x89..0x90 in repeated ordinal 1 illustrate the distinction:

```text
Offsets:     89 8A 8B 8C 8D 8E 8F 90
Black:       00 00 00 00 00 00 00 00
Army Green:  00 00 98 CC 98 00 00 00
Navy Blue:   00 00 30 60 CC 00 00 00
```

There is strong changed-byte support for the start of the **variable RGB span**
at 0x8B. This is more specific than the Phase 1 palette score, but does not prove
that a typed serialized field starts there: invariant bytes can belong to a
larger field or lie beside it.

| Hypothesis | Repeated-context changed-byte support | Remaining ambiguity |
| --- | ---: | --- |
| H1: +0x8B, four-byte u32le RGB0 | 24 pair comparisons | Fourth zero may instead be padding |
| H2: +0x8B, three RGB bytes plus adjacent zero/padding | 24 | No independent width/type delimiter |
| H3: +0x8A, four-byte big-endian/BGR0-like field | 24 | Leading zero may belong to this view or precede RGB |
| H4: coincidence / typed boundary unresolved | No positive width proof | Remains viable for typed-boundary semantics |

H1/H2/H3 remain compatible and not distinguished. The observable color-bearing
part is three bytes; **storage width is not established**. The report therefore
sets `best_field_start=139` with variable-span scope, `best_field_width=null`, and
`observed_variable_span_width=3`. Integer byte order remains unresolved even
though the three color bytes fit an RGB sequence. The fourth zero's ownership by
the field cannot be inferred from these fixtures.

### Why 8/10 and 9/10 palette matches occur

All three primary fixtures have the same provisional local-role layout:

| Role candidate | Ordinals | Structural basis |
| --- | --- | --- |
| header_like_chunk | 0 | Fixed prior marker context; different delta run |
| repeated_color_record_candidate | 1..8 | Repeated masked local context and the common three-byte delta |
| tail_like_chunk | 9 | Terminal nonmatching context, invariant window across the controls |

| Primary control | u32le/RGB0 matching ordinals | Nonmatching ordinals |
| --- | --- | --- |
| Black | 0..8 | 9 |
| Army Green | 1..8 | 0, 9 |
| Navy Blue | 1..8 | 0, 9 |

Black's ninth palette match is **the zero word in header-like chunk 0**. It does
not turn that chunk into a repeated color record. Header roles stay the same in
all controls even when palette success changes. The terminal chunk's bounded
bytes are identical across controls and remain unmapped. Thus the unmatched
positions and their local structural roles are repeatable; this explains the
match counts without inventing additional owners or discarding failed chunks.

These results support mixed local roles within the fixed 204-byte chopping
model, not a homogeneous array of verified typed color records. Role names are
provisional: no semantic header/footer format or entire-record identity is proven.

### Cross-fixture alignment

| Layout | Header-like | Repeated context | Terminal candidates |
| --- | --- | --- | --- |
| Primary and grouped 10-chunk cases | 0 | 1..8 | 9 |
| Not-grouped two-object 14-chunk cases | 0 | 1..11 | 12..13 |
| Not-grouped three-object 6-chunk cases | 0 | 1..4 | 5 |

The grouped cases share the repeated masked context at matching ordinals with
the primary controls, but their header/tail windows need not be byte-identical.
The 14-chunk layout has three more repeated candidates and one more terminal
candidate than the 10-chunk layout. The 6-chunk layout has four fewer repeated
candidates. Those are count/profile differences, **not localized insertion or
deletion events**: duplicate local signatures prevent a unique edit alignment.
No semantic object count, stored order, or chain correspondence is inferred.

### CPropertyExtend and readiness

Only the already established bounded textual sections and local +30 probe are
reused. No new CPropertyExtend offsets or anchor-record semantics are searched.
Its side observations supply the color name missing from CParagraphe in all four
mixed-intent fixtures. The textual section frame is repeatable, but its +30 value
does not have a demonstrated uniform color role. The status remains
`no_stable_cpropertyextend_color_field_found`.

`field_boundary_readiness=changed_span_supported_typed_boundary_not_ready`.
`candidate_parser_model_ready=false`: variable-byte evidence is stronger, but a
typed field width and independently validated per-record applicability rule are
still missing. `color_ownership_readiness=not_ready`; ownership is out of scope.
MFC framing remains provenance terminology and schema 6 has no color semantics.

### Phase 1B verification

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe tools/analyze_text_color_field_boundary.py --json
.venv/Scripts/python.exe tools/analyze_text_color_field_boundary.py --json --no-oracle
.venv/Scripts/python.exe -m pytest tests/integration/test_text_color_field_boundary_cli.py -q
.venv/Scripts/python.exe -m pytest -q
```

Tests cover exact delta runs, unchanged neighbors, unresolved width, role and
match ordinals, all six integer views, bounded-only comparisons, ambiguous
alignment, +30-only side evidence, oracle isolation, palette-independent boundary
selection, moved synthetic deltas, prefix shifts, truncation abstention and
unchanged parser sources/objects. No fixture files are created.

Results: 14 integration tests passed; full suite **359 passed** (prior baseline
345). Ruff and whitespace checks passed. Default output sizes are text 5,521
bytes, Markdown 5,523 bytes, and JSON 76,423 bytes; no-oracle JSON is 71,931 bytes.
All 110 chunk rows and 65 bounded +30 section observations are retained.
Parser/decoder/model sources, the anchor closeout RFC and the MFC investigation
document have no changes in this phase.

## Color Phase 1C — repeated record semantics

`tools/analyze_text_color_record_semantics.py` inventories 23 existing fixtures
(22 requested controls plus `text_multiline_basic.txt`). Phase A is serialized
before any intent/expected-color load. `--no-oracle` leaves every structural
result and hypothesis unchanged. Roles use the unique corpus-modal masked
Phase 1B context and fixed header marker, never filenames or palette matches.

The strongest explanation is an **existing text slot run including a zero-code
slot**. In 22 context-matched fixtures, repeated count equals extracted ASCII
character count + 1. The bounded eight-byte slot headers at provisional chunk
offset +59 match the existing parser's entire code sequence, including its
final zero. This supports the 204-byte stride; it does not establish that every
204-byte slice of the paragraph payload is a record of that type.

| Extracted text/control | Characters | Chunks | Repeated candidates |
| --- | ---: | ---: | ---: |
| abcdefg / ABCDEFG | 7 | 10 | 8 |
| 1234567890 | 10 | 14 | 11 |
| A1B2C3d4 / ab cd ef | 8 | 12 | 9 |
| +-*/#@&() | 9 | 13 | 10 |
| HELLO (content variation) | 5 | 8 | 6 |
| XYZ (three-chain controls) | 3 | 6 | 4 |
| abcd newline efgh | 9 including newline | 13 | unresolved |

Multiline has an existing ten-slot run, including newline and zero, but fails
the Phase 1B masked-context classifier. Its candidate count and character delta
are null, not zero or a forced N+1 result. Non-ASCII decoding, when unavailable,
is not replaced by codepoint counts or fixture-name text. No new glyph boundary
is introduced. Single-chain controls retain one CContour and two parsed contour
points while repeated count varies 8..11: these geometry counts do not explain
the variation. Glyph/geometry semantics remain unresolved.

All 179 classified candidates have one masked signature class per fixture in
0x70..0xA0 excluding 0x8B..0x8D. `identical_except_color_count` includes the modal
representative; `structurally_similar_count` counts other wide signatures sharing
the narrower Phase 1B context. Both that latter count and divergent count are
zero in the 22 classified fixtures. Multiline has unresolved interior contexts
and `mixed_record_roles_possible=true`. Homogeneity is local, not full-record
identity or a claim that header/tail slices have the same role.

The 28 structurally selected same-text, single-chain pairs retain candidate
count/layout and masked repeated windows across color, height and font controls.
This supports color modifying an existing repeated record. The three primary
color-only pairs also retain the terminal window. Height/font changes can
change terminal geometry; whole-payload color-only equality is not asserted.

Ordinal zero and the final ordinal differ from the candidate context in every
fixture. Ordinal zero retains its fixed prior marker. A bounded prefix +5 u32
probe is always 8 even as slot counts vary, so it is **not** a demonstrated text
count field. The baseline header's zero bytes merely alias Black. Header-like
and terminal-like remain provisional roles; extra tail slices are not uniquely
decoded or aligned as insertion/deletion events.

The observed span remains start 0x8B, changed width 3. Typed width is null and
typed start unresolved: no independent next-field start at 0x8E or typed field
declaration has been found. Field decode and ownership remain not ready.
CPropertyExtend section counts are structural inventory only;
`no_stable_cpropertyextend_color_field_found` remains the prior conclusion.

Validation: eight new integration tests cover bounds, freeze ordering, disabled
and adversarial oracle inputs, filename-independent roles, raw-color mutation,
slot evidence, multiline abstention, and unchanged parser source/results.
Run with `PYTHONPATH=src`: `.venv/Scripts/python.exe -m pytest -q`.
Full suite: **367 passed**; Ruff and whitespace checks passed. Parser/decoder/model
sources and fixtures have no diff.
Default output retains 242 chunks: JSON 178,945 bytes, no-oracle JSON 175,355
bytes, text 11,134 bytes, Markdown 11,136 bytes (including Windows line endings).
Output budgets are 180,000 JSON / 50,000 text bytes; oversized inputs fail closed.

## Color Phase 1D — provisional CParagraphe text-slot record schema

`tools/analyze_text_slot_record_schema.py` validates 21 existing controls without
changing parser, decoder or model code. It does not import the Phase 1C analyzer
or generate its large report. Analysis uses runtime-descriptor-derived CParagraphe
payloads; absolute clipboard positions and MFC schema 6 are provenance only.
No chain, anchor, order or color ownership mapping is performed.

### Boundary versus periodicity

H1 uses the original payload-relative grid `47 + ordinal * 204`. Ordinal zero
remains header-like; the first repeated slot candidate is ordinal one, at 251.
Twenty single-line fixtures retain this grid, totaling 167 aligned candidates.
H2 compares starts 39..55 with the same exact adjacent-boundary repetition score
over bounded -8..+7 windows. **No fixture uniquely selects start 47**. Some have
47..55 ties; others favor 50..55, and multiline favors 50..52. Padding can produce
equal or better repetition at shifted starts. `best_record_start=null` is deliberate.

A stronger independent lead is repeated `05 00 00 00` at payload-relative 310
for all 20 single-line controls, +0x3B inside provisional ordinal one. The immediately
preceding u32le view at 306 equals the independently enumerated prefix count,
varying with content. This is distinct from Phase 1C's invariant header +5 probe.
Enumeration stops at prefix loss or bounds, never because a code is zero or
printable. The next prefix is absent after the final slot in every covered fixture.

The bounded stride comparison 196..212 uniquely supports 204 in all 21 fixtures,
including multiline. Other tested strides retain only the initial prefix. This
supports **204-byte periodicity and a count-prefixed slot run**, while H3 (internal
period, not complete record width) and H4 (mixed family or repetition window)
remain viable. Neither 47 nor 310 is promoted to a confirmed outer record boundary.

### Slot code, terminal and homogeneity

Within 0x30..0x50, the unique longest repetition of the prior prefix lead selects
the following candidate code at **+0x3F**, or prefix-relative +4. Narrow u8/u16le/
u32le summaries retain varying/terminal-zero alternatives; no expected character
or ASCII score selects the offset. Values remain compatible with all three views;
code storage width is also unresolved.

Only after the complete structural report is serialized does the diagnostic
oracle load documented ASCII controls or capture text-content alternatives.
All seven primary ASCII fixtures match ordinally, including both spaces in
`ab cd ef`, all ten digits, and all nine punctuation characters. Slot counts are
8 for seven-letter controls, 11 for digits, 9 for alphanumeric/spaces and 10 for
punctuation: N+1. Overall, 18 fixtures match available text oracles; three multi-object
controls have unavailable text metadata and are not counted as matches. Unordered
text alternatives never identify an object.

All 21 runs have exactly one final zero code, a retained prefix at that slot,
prefix loss at the next stride, and agreement with the preceding count. In the
20 aligned cases the terminal masked signature and color bytes match the preceding
slot, including nonzero Army Green/Navy Blue controls. This supports
`zero_code_terminal_candidate`, without distinguishing terminator from padding/
default slot or proving C-string semantics.

The wider homogeneity test combines 0x30..0x50 and 0x70..0xA0, masking only the
four-byte code *view* and color bytes 0x8B..0x8D. No coordinates are silently
excluded. Every aligned fixture has **two signature classes**: first-slot context
versus remaining slots, including the final zero slot. Color-local signatures
still have one class. `multiple_slot_subtypes` is a bounded observation: a run
prefix crossing the provisional boundary can explain the difference, so semantic
subtypes are not proven. Phase 1C's narrower homogeneity remains valid.

### Multiline and color applicability

Multiline has no single-line prefix lead in the code window. A separate bounded
prefix-window contrast finds its prefix at 378, shifted +68 from 310, with preceding
count 10 and the same 204-byte period. Code 13 occurs at slot five with no prefix
break; the post-freeze oracle reads `abcd\nefgh` followed by the zero slot. This is
`alternate_layout_or_unresolved` / `single_line_schema_not_directly_applicable`.
Single-line homogeneity masks and color positions are not transferred to it.
Additional runs are not exhaustively searched; totals cover enumerated leading runs.

The observed color region stays at +0x8B..+0x8D in all 167 aligned candidates,
equivalently +0x50 from the repeated prefix lead. Terminal values match preceding
slots. This is position consistency in the provisional grid, not a typed boundary.
`observed_changed_width=3`, `typed_color_field_width=null`; no independent next-field
start at 0x8E is demonstrated. Candidate parser modeling and color ownership remain
`not_ready`. Anchor closeout and MFC conclusions are unchanged.

### Compact reporting and validation

Default output has counts, code sequences and compact signature/view statistics,
with **zero per-record rows**. `--details` constructs at most four rows and two
signature examples for the first paragraph of at most three selected fixtures.
Limits apply before row construction. JSON is capped at 100,000 bytes and text
at 50,000 bytes in both modes. The previous Phase 1C analyzer is unchanged.

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe tools/analyze_text_slot_record_schema.py --json
.venv/Scripts/python.exe tools/analyze_text_slot_record_schema.py --json --no-oracle
.venv/Scripts/python.exe tools/analyze_text_slot_record_schema.py --json --details
.venv/Scripts/python.exe -m pytest tests/integration/test_text_slot_record_schema_cli.py -q
.venv/Scripts/python.exe -m pytest -q
```

Fifteen new tests cover compact output, bounded details, freeze ordering,
adversarial expected text, no-oracle equality, filename-independent structure,
shifted descriptor provenance, unchanged parser/model sources and results,
multiline abstention, and synthetic exact/shifted periods, internal zeros and
periodic bytes without a prefix. No fixtures are added.

Validation result: **15 new tests passed; full pytest 382 passed** with
`PYTHONPATH=src`. Ruff and whitespace checks passed. Measured CLI sizes including
Windows line endings: default JSON **85,453 bytes**, no-oracle JSON **78,990 bytes**,
details JSON **90,453 bytes**, text **12,435 bytes**, Markdown **12,437 bytes**,
details text **16,521 bytes**. Parser/decoder/model sources, existing analyzers,
fixture files, anchor closeout and the MFC investigation have no changes.

## Color/Text Slot Phase 1E — dynamic prefix framing candidate

`tools/analyze_text_slot_prefix_framing.py` searches payload-relative [128, 768)
inside structurally identified CParagraphe payloads. This is a bounded leading
search region, not a fixed record-start rule or whole-payload scan. It inventories
the prior `05 00 00 00` lead, skips suffixes with a predecessor at -204, traverses
maximal prefix sequences, and tests their local context. Code values, printable
text, colors, fixture names, anchors and object/chain order never select a run.

### Competing starts and framing rules

All 24 existing fixtures contain **two** maximal periodic `05` sequences in this
search: the proposed slot prefix and another prefix 92 bytes later. Their counts
are equal. Therefore R1 (longest periodic run) alone is ambiguous in 24/24 cases;
the raw token is insufficient to identify a text-slot run. P2, incidental internal
periodicity, is not excluded by token matching alone.

R2 adds a preceding-header transition: the u32le view immediately before a run
must equal the independently traversed prefix count, and masked contexts must
repeat after an optional distinct first context. The count is checked **after**
enumeration; it does not determine traversal length. R2 uniquely selects one run
in 24/24 fixtures. The competing +92 prefix has preceding view 1072693248 rather
than the run count. This is a structural rejection, not proof of that region's
semantic role. Multiple qualifying candidates cause abstention.

| Rule | Support | Conflict | Ambiguity | Structurally rejected candidates proposed |
| --- | ---: | ---: | ---: | ---: |
| R1 longest raw-prefix run | 0 | 0 | 24 | 24 |
| R2 preceding count + repeated context | 24 | 0 | 0 | 0 |
| R3 distinct first positive-prefix signature | 0 | 24 | 0 | 0 |
| R4 historical start 310, diagnostic only | 20 | 4 | 0 | 0 |

These are internal consistency scores against count/context framing, not an
external semantic oracle. The analyzer permits a distinct first prefix context;
P3/P4 are not rejected by definition. A synthetic first-context control exercises
that case. Absolute descriptor/payload positions and MFC schema remain provenance.

### Prefix signature and first-slot context

The tested positive-prefix window is +0..+31 with +4..+7 masked. Color bytes are
outside that window and are never required invariants. Nearby origins -8..+8 are
compared while keeping masks anchored to the nominated prefix, so moving a window
does not accidentally require invariant code bytes. Nearby windows can also
repeat: context repetition alone still does not prove an outer record boundary.

Each selected run has **one** masked positive-prefix signature, including first
and terminal slots. Across fixtures there are **three** classes: the baseline,
height-control variation around +12..+18, and a mixed-group control's +8 variation.
These are fixture-level differences, not established semantic subtypes. Common
invariant positions are reported from structural evidence; no unknown coordinate
fields are silently masked. The 16 bytes before the prefix have two classes:
first-slot upstream context versus later slots. Thus Phase 1D's widened first-slot
difference belongs upstream of the positive prefix in these fixtures, not to a
demonstrated separate first-slot record schema.

### Normalized code, color and terminal

All 24 selected runs, totaling **207 slots**, preserve 204-byte recurrence. In the
bounded comparison 196..212, other tested strides retain only the initial prefix.
The prior code hypothesis is prefix +4. Phase A reports zero/nonzero statistics
and narrow u8/u16le/u32le distributions around +0..+8; expected characters do not
select +4. Only byte +4 varies within the four-byte code view in these fixtures.
`observed_variable_width=1` is not a storage declaration: `typed_code_start` and
`typed_code_width` remain null.

For the 20 single-line controls, discovered prefix equals provisional grid
+0x3B, and +0x50..+0x52 equals the prior grid +0x8B..+0x8D at all **167 slots**.
This comparison occurs only after run discovery and uses coordinate equality,
not coincident zero-byte matches. All 24 fixtures have one shared masked color
context at prefix +72..+91, excluding +80..+82. The shifted multiline cases
therefore support the normalized position by context, although no changed-color
multiline controls independently establish its color semantics.
`observed_color_changed_width=3`, `typed_color_width=null` remain unchanged.

Traversal never stops on a code value. It ends when prefix recurrence ends, then
checks final zero plus absence of the next prefix (T1). All 24 fixture runs meet
T1; the final masked signature and color bytes match the previous slot. T2, zero
alone, has no internal-zero counterexample in these fixtures but fails the synthetic
internal-zero test. T3, prefix loss alone, locates the sequence end without proving
terminal semantics. The role remains `zero_code_terminal_candidate`, not a proven
sentinel versus padding/default slot.

### Multiline, isolation and readiness

`text_multiline_basic.txt` and the fixed/proportional/print-proportional spacing
controls are all found automatically at prefix 378, while single-line controls
are found at 310. There is no +68 correction in discovery. All four have ten slots,
the same positive-prefix signature as the baseline, code 13 inside the same run,
and compatible +0x50 color context. This strengthens the dynamic prefix-local
schema and qualifies Phase 1D's single-line-grid incompatibility; it does not
confirm the entire paragraph or a 204-byte outer record extent.

All seven requested multi-object controls are structurally compatible; counts
cover enumerated paragraph runs only, with no object/chain mapping. The complete
structural report and private diagnostic code ordering are serialized before any
text oracle access. Phase A exposes distributions, not decoded text. Wrong expected
text changes only oracle diagnostics; `--no-oracle` preserves identical structure.

`structural_slot_run_readiness=bounded_framing_candidate_supported`.
`candidate_parser_model_readiness=not_ready`, `parser_safe=false`: bounded corpus
coverage, competing periodic tokens, and the unproven general count/prefix grammar
still limit parser applicability. Typed field widths remain unresolved. Color
ownership stays `not_ready` and is not investigated. Parser/decoder/model, existing
analyzers, fixtures, anchor closeout and MFC conclusions are unchanged.

### Compact CLI and verification

Default reports have no per-slot rows. `--details` constructs at most five rows
for the first paragraph of at most three fixtures, selected before row construction.
Signature examples are bounded to three. Input, candidate, traversal and output
budgets fail closed rather than silently truncating evidence.

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe tools/analyze_text_slot_prefix_framing.py --json
.venv/Scripts/python.exe tools/analyze_text_slot_prefix_framing.py --json --no-oracle
.venv/Scripts/python.exe tools/analyze_text_slot_prefix_framing.py --json --details
.venv/Scripts/python.exe -m pytest tests/integration/test_text_slot_prefix_framing_cli.py -q
.venv/Scripts/python.exe -m pytest -q
```

Measured CLI output including Windows line endings: JSON **91,387 bytes**,
no-oracle JSON **87,672 bytes**, details JSON **94,362 bytes**, text **11,798 bytes**,
Markdown **11,800 bytes**, details text **14,774 bytes**. Both JSON modes stay below
100,000 bytes; text stays below 50,000 bytes.

Validation: **20 new integration cases passed; full pytest 402 passed** with
`PYTHONPATH=src`. Ruff and whitespace checks passed. Tests cover oracle isolation,
wrong expected text, shifted real/synthetic payloads (+37/+68/+113), descriptor
relocation, internal zeros, periodic filler, count disagreement, competing eligible
runs, and a distinct synthetic first context. Code/color mutations do not select
the prefix, and source/result snapshots preserve parser/model behavior. No fixture
files are created or changed.
