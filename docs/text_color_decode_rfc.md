# Text Color Decode RFC: Phase 1 Evidence

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
