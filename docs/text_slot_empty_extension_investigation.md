# Text slot empty-extension investigation

> **Historical status note**
>
> This document records the shadow investigation at that time; its evidence and
> readiness results are preserved. The statement that no production gate is
> enabled was later superseded: current production requires exact AttrChar v5,
> CPropertyExtend v5 and all six empty-extension guards, failing closed otherwise.
> For current consumer-facing interpretation, use the
> [text-slot typed candidate consumer contract](text_slot_typed_candidate_contract.md).

This batch adds **analyzer-only shadow evidence**. Production F4 recognition,
candidate selection, count/stride/terminal rules, typed widths, ownership, style
archive metadata, Maximum Length and compression extraction are unchanged.

**empty_extension_recognizer_readiness = structurally_supported_but_incomplete**.
The six empty-state words are locally testable in order. A matching local v5
record window is still candidate evidence, not an independently proved runtime
class/serializer identity for every version/corpus. No production gate is enabled.

## Code evidence and boundary

Read-only references:
- [Phase 2C composition](C:/TypeEdit_2009/_reverse_engineering/data/phase2c_slot_composition.csv)
- [Phase 2C current-store operations](C:/TypeEdit_2009/_reverse_engineering/data/phase2c_current_store_ops.csv)
- [Phase 2C layout](C:/TypeEdit_2009/_reverse_engineering/reports/phase2c_current_stream_layout.md)
- [Phase 2A reviewed store sequence](C:/TypeEdit_2009/_reverse_engineering/tools/phase2a_evidence.py)
- [Phase 2D scoped crosswalk](C:/TypeEdit_2009/_reverse_engineering/data/phase2d_crosswalk.csv)
- [Phase 3 review](C:/TypeEdit_2009_reverse_engineering/reports/phase3_codec_promotion_review.md)

The checked-in `tools/text_slot_empty_extension_layout.json` was transcribed from
the ordered Phase 2C CSV operations, including variable emissions and their zero
contribution **only on the empty path**. It is code evidence, not a fixture-byte
template. Neither implementation nor tests require access to vendor installations.

MaudeTxt.dll!CTxtAttrChar::Serialize (0x4D790) emits five 4-byte words and nine
8-byte doubles in its fixed part: **5*4 + 9*8 = 92**. After the last write at
0x4D873, the virtual call at **0x4D882** serializes the embedded extension at
**CTxtAttrChar+0x68**, identified in the reviewed evidence as
**Maude.dll!CPropertyExtend::Serialize 0x60370**. Hence
**record_relative_extension_start = 92**, derived from the preceding store
sequence, not 204 minus 112.

The current AttrChar version word is literal **5**, write RVA 0x4D7B9.
CPropertyExtend's first emitted word is **member+4**, not a proved standalone
extension version discriminator. Its store branch selects archive storing at
0x6039D–0x603A6 and then writes members; no extra stored schema header was inferred.

The extension's fixed contributions are **16*4 + 6*8 = 112**. The six variable
emissions contribute zero only when their preceding counts/lengths/presence words
are zero. The helper computes all cumulative offsets by traversing the operation
list; no padding or target-total fitting is used.

## Ordered extension store sequence

Offsets below are **extension-relative**, half-open. They are valid along the
reviewed empty path, i.e. every earlier variable component contributes zero.
Widths of opaque 8-byte extension blocks are not promoted to semantic doubles.
All entries are CPropertyExtend in Maude.dll, with Phase 2C confirmed_code evidence.
The fixed AttrChar operation sequence is separately retained in the manifest.

| Extension interval | Write RVA | Source member / item | Encoded width | Empty contribution | Repetition / guard | Archive representation |
| --- | --- | --- | --- | --- | --- | --- |
| [0,4) | 0x603b2 | 0x4 | 4 | 4 | 1 | raw bytes; explicit count |
| [4,12) | 0x603bf | 0x10 | 8 | 8 | 1 | raw bytes; explicit count |
| [12,16) | 0x603cc | 0x8 | 4 | 4 | 1 | raw bytes; explicit count |
| [16,20) | 0x603d9 | 0x18 | 4 | 4 | 1 | raw bytes; explicit count |
| [20,24) | 0x603e6 | 0x1c | 4 | 4 | 1 | raw bytes; explicit count |
| [24,28) | 0x603f3 | 0x20 | 4 | 4 | 1 | raw bytes; explicit count |
| [28,32) | 0x60400 | 0x24 | 4 | 4 | 1 | raw bytes; explicit count |
| [32,36) | 0x6040d | 0x28 | 4 | 4 | 1 | raw bytes; explicit count |
| [36,40) | 0x6041a | 0x2c | 4 | 4 | 1 | raw bytes; explicit count |
| [40,44) | 0x60427 | 0x30 | 4 | 4 | array30_count | raw bytes; explicit count |
| [44,44) | 0x6044b | 0x34[i] | 4 | 0 | max(0,member_30) | raw bytes; explicit count |
| [44,48) | 0x60460 | 0x38 | 4 | 4 | 1 | raw bytes; explicit count |
| [48,52) | 0x6046d | 0x3c | 4 | 4 | 1 | raw bytes; explicit count |
| [52,60) | 0x6047a | 0x40 | 8 | 8 | 1 | raw bytes; explicit count |
| [60,64) | 0x60487 | 0x48 | 4 | 4 | array48_count | raw bytes; explicit count |
| [64,64) | 0x604ab | 0x4c[i] | 8 | 0 | max(0,member_48) | raw bytes; explicit count |
| [64,72) | 0x604c0 | 0x60 | 8 | 8 | 1 | raw bytes; explicit count |
| [72,80) | 0x604cd | 0x68 | 8 | 8 | 1 | raw bytes; explicit count |
| [80,88) | 0x604da | 0x70 | 8 | 8 | 1 | raw bytes; explicit count |
| [88,96) | 0x604e7 | 0x78 | 8 | 8 | 1 | raw bytes; explicit count |
| [96,100) | 0x60504 | length(string+0x50) | 4 | 4 | string50_length | raw bytes; explicit count |
| [100,100) | 0x6052d | 0x50[i] | 1 | 0 | string_length_50 | raw bytes; explicit count |
| [100,104) | 0x60550 | bool(pointer+0x54 != null) | 4 | 4 | zone54_present | raw bytes; explicit count |
| [104,104) | 0x60565 | 0x54 | nested_zone_bytes | 0 | optional | virtual Serialize; no WriteObject framing |
| [104,108) | 0x6057f | length(string+0x58) | 4 | 4 | string58_length | raw bytes; explicit count |
| [108,108) | 0x605a8 | 0x58[i] | 1 | 0 | string_length_58 | raw bytes; explicit count |
| [108,112) | 0x605cb | bool(pointer+0x5c != null) | 4 | 4 | zone5c_present | raw bytes; explicit count |
| [112,112) | 0x608f9 | 0x5c | nested_zone_bytes | 0 | optional | virtual Serialize; no WriteObject framing |

## Mandatory conditions and runtime detectability

| Condition | Code provenance | Empty state | Local detectability | Implementation |
| --- | --- | --- | --- | --- |
| Aligned current AttrChar store | version 5 at 0x4D7B9; extension call 0x4D882 | v5 candidate, complete fixed prefix | yes_bounded_candidate | Read word 0; unknown version becomes unresolved |
| array +30 | count write 0x60427; element writes 0x6044B | count=0 | yes_exact on reviewed path | extension+40 / record+132 |
| array +48 | count 0x60487; elements 0x604AB | count=0 | yes_exact after earlier count=0 | extension+60 / record+152 |
| string +50 | length 0x60504; byte loop 0x6052D | length=0 | yes_exact after earlier empty conditions | extension+96 / record+188 |
| zone +54 | 4-byte bool 0x60550; virtual call 0x60565 | presence=0 | yes_exact on empty path | extension+100 / record+192 |
| string +58 | length 0x6057F; byte loop 0x605A8 | length=0 | yes_exact on empty path | extension+104 / record+196 |
| zone +5C | bool 0x605CB; store jump 0x605E0 to call 0x608F9 | presence=0 | yes_exact on empty path | extension+108 / record+200 |
| Actual serializer/class applicability beyond reviewed scope | code/class evidence vs anonymous local bytes | correct serializer and current branch | unresolved from this local window alone | Success stays supported, parser_safe=false |

The six structural conditions are **confirmed_code**; their application to a
candidate window is **supported**. These are the complete variable-emission
conditions in the reviewed store sequence. Other fixed member bytes may be nonzero;
the helper does not demand zero padding, fixture equality, a known style value,
font ID, RGB, UI intent or a terminal-specific template.

Arrays use signed positive-count loops in the reviewed code. Negative count/length
words are outside the reviewed empty state even if some loops would skip them;
they return unresolved rather than being silently accepted as empty.
Presence words produced by the writer are 0 or 1; other nonzero values are unresolved.
A normal positive count/length or presence=1 yields not_empty_extension_layout.

Most importantly, the first nonzero condition stops inspection. Subsequent offsets
are no longer justified because variable data could have shifted them. No strings,
arrays or zone bodies are parsed in this batch. Null zones add no nested framing;
no global MFC framing recipe is needed to validate these absent components.

## Shadow helper contract and evidence strength

`tools/analyze_text_slot_empty_extension.py::inspect_empty_extension(record)`
receives only one already-aligned record window. It accepts no path, filename,
expected text, raw absolute offset, chain index or oracle argument. At most 204
bytes and six condition words are examined. It never scans for another record,
modifies its input, or mutates a production candidate.

- Complete v5 candidate + all six zero conditions:
  `supported_empty_extension_layout`, `extension_length_candidate=112`,
  conditional `record_length_evidence.code_derived_candidate=204`.
- Positive nonempty condition: `not_empty_extension_layout`.
- Short window: `truncated`; no length evidence is emitted.
- Unknown version, invalid condition word or oversized window: `unresolved`.
- Oversized inputs retain a bounded raw_window with explicit truncation and input
  length; valid-sized inputs retain exact raw bytes. The original input is untouched.

The helper does not currently emit confirmed_empty_extension_layout. Matching all
local empty guards establishes a conditional byte-layout candidate, not arbitrary
version/class membership. The five-fixture Phase 2D exact crosswalk is not widened
to every analyzed fixture by this success label.

Corpus discovery calls the **existing** bounded F4 recognizer per paragraph to
supply alignment; this allows separate observation of paragraphs in multiobject
captures without overriding global production abstention or assigning ownership.
No new payload search or fallback record alignment is introduced. Unaligned
paragraphs are explicitly unexamined, not falsely counted as empty records.

Run with project Python 3.14.7 and `PYTHONPATH=src`:
`python -B tools/analyze_text_slot_empty_extension.py --json`.
The JSON report is diagnostic only and is not attached to production candidate output.

## Corpus observations

Every .txt under tests/samples was considered. Input validity is checked as hex,
not selected by filename. Non-hex inspection reports remain named in input_issues.
Family labels below are assigned **after** record inspection and affect reporting
only. All actual hex captures, including geometry/no-paragraph cases, are retained.

Files considered: **126**; valid hex captures: **116**; non-hex inspection reports: **10**.

Captures with CParagraphe: **84**. Unaligned paragraphs: **0**. Examined records: **700**.

| State | All records | Visible | Terminal |
| --- | ---: | ---: | ---: |
| confirmed_empty_extension_layout | 0 | 0 | 0 |
| supported_empty_extension_layout | 700 | 616 | 84 |
| not_empty_extension_layout | 0 | 0 | 0 |
| truncated | 0 | 0 | 0 |
| unresolved | 0 | 0 | 0 |

| Display family | Captures | Records | Supported | Not empty | Truncated | Unresolved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| legacy_text_or_other | 66 | 343 | 343 | 0 | 0 | 0 |
| color | 8 | 25 | 25 | 0 | 0 | 0 |
| multiobject | 17 | 106 | 106 | 0 | 0 | 0 |
| maximum_length | 4 | 36 | 36 | 0 | 0 | 0 |
| maximum_length_boundary | 4 | 36 | 36 | 0 | 0 | 0 |
| spacing | 9 | 82 | 82 | 0 | 0 | 0 |
| style | 8 | 72 | 72 | 0 | 0 | 0 |

Unaligned fixture paragraphs (no empty-record inference):

None.

Non-hex inputs, rejected by content validation rather than name filtering:

- text_three_objects_grouped_order_abc.inspect.txt
- text_three_objects_grouped_order_abc_content_variation.inspect.txt
- text_three_objects_grouped_order_abc_font_arial_bold.inspect.txt
- text_three_objects_grouped_order_abc_height_30mm.inspect.txt
- text_three_objects_grouped_order_abc_mixed_color.inspect.txt
- text_three_objects_grouped_order_cba.inspect.txt
- text_three_objects_not_grouped.inspect.txt
- text_three_objects_not_grouped_mixed_color.inspect.txt
- text_two_objects_not_grouped_selection_reversed.inspect.txt
- text_two_objects_same_color_not_grouped.inspect.txt

Contradictions among examined records: **none**. Exact per-fixture/record status is reproducible with the CLI --json option; no baseline-equality selector is used.

## F4 independence, terminal evidence and synthetic negatives

All **examined** F4-aligned records matched the six empty guards. This is not a
claim about every F4 occurrence or unaligned paragraph in arbitrary data.

F4 proves none of the six extension conditions: a baseline F4 payload can have
each count/length/presence word changed to 1 in memory while its existing production
candidate dictionary remains identical and the shadow changes to not-empty.
Conversely, breaking the F4 +08 rule leaves the extension predicate supported.
A synthetic v5 record lacking F4's fixed constants can also have the empty layout.
F4 semantics and recognition are therefore independent of this shadow predicate.

Terminal records use the same helper and conditions as visible records; no alternate
terminal extension is assumed. The observed agreement supports the existing
terminal AttrChar interpretation, without newly proving all class identity or
propagation semantics. No C-string terminator claim is introduced.

Focused tests cover all 204 proper-prefix truncations, all six nonempty guard
mutations, all six invalid/negative-word cases, unsupported version tags,
oversized-window bounds, arbitrary nonzero opaque extension fields, record
reordering, shifted enclosing-buffer offsets, renamed fixture inputs and the
empty-corpus readiness case. Mutations exist only in memory (or pytest temporary
renamed unmodified captures), never in tests/samples.

Full corpus before/after snapshots compare the complete production dataclass,
chain identity and original file bytes. This covers presence, F4 family, count,
stride, terminal result, all raw/unknown candidate bytes and existing typed values.
For shortened record-window tests the original production payload remains intact;
we do not claim truncating a whole serialized payload could never affect production.

## Parser-safe / promotion review

| Requirement for a future gate | Result |
| --- | --- |
| All reviewed empty counts/lengths/presence locally detectable | Pass, under preceding-empty / aligned-current-path condition |
| No fixture/oracle or absolute-offset selection | Pass |
| Truncation and unsupported variants fail closed | Pass |
| All version/schema/class applicability independently proved | **Incomplete**: local v5 tag plus existing alignment is candidate evidence only |
| No unexplained contradictions among examined aligned records | Pass for this corpus; unaligned paragraphs remain outside coverage |
| Production acceptance/stride unchanged | Pass; shadow only |

Final readiness is **structurally_supported_but_incomplete**. There is no
variable-framing blocker on the successfully empty branch itself; a nonempty
branch is deliberately not parsed. Before production-gate review, establish the
runtime serializer/variant applicability and explicitly decide the treatment of
currently unaligned/unsupported paragraphs. Do not use the 700 positive matches
as a universal 204-byte rule.

No production gate, typed parser promotion, Maximum Length ownership change,
compression reinterpretation, F4 change, terminal change, archive-type change or
source-integrity policy change is part of this batch.


## Validation and preserved boundaries

Actual checkout, project-local `.venv` Python **3.14.7**:

| Check | Result |
| --- | --- |
| New shadow tests | 26 passed |
| Existing archive metadata tests | 16 passed |
| Existing historical replay assertion | 1 passed; 104 fixtures, runtime_outputs_equal=true, canonical_source_equal=true, readiness=ready_for_review |
| Combined focused run | 43 passed |
| Full PYTHONPATH=src python -B -m pytest -q -p no:cacheprovider | **1292 passed**, 81.64 seconds |
| Ruff default on both new Python files | Passed |
| Ruff E4/E7/E9/F on both new Python files | Passed |
| git diff --check | Passed |
| src/type3_clipboard_codec diff | Empty |
| tests/samples diff | Empty |
| Existing style/spacing/max-length analyzers and source-integrity policy diff | Empty |

The final full run includes the final import arrangement and all new tests.
No LF-normalized acceptance copy was used.

Raw before/after preservation aggregates hash sorted
`relative_path:raw_file_sha256` rows (no source canonicalization):
- 46 production files:
  `8956966a68e447c0402b72e20f49ed95fffe03a2dc6d3964c3f35f94dba95422`.
- 204 tests/samples files:
  `b71e8ac36824d7876d7e0d39e8a8fc15d99dcdfe35805d37a473cbf83d6b9b30`.

Both aggregates are identical before and after. Python snapshot assertions use
the existing tests/source_integrity.py helper; no raw Python snapshot gate was added.

Only four new files comprise this batch:
- tools/analyze_text_slot_empty_extension.py — pure bounded predicate and corpus CLI
- tools/text_slot_empty_extension_layout.json — serializer-operation evidence
- tests/integration/test_text_slot_empty_extension.py — shadow-only regression tests
- docs/text_slot_empty_extension_investigation.md — this report

All existing files remain unchanged. No vendor binary was executed or loaded;
reference reports/CSV/previous CFG evidence were read only. There are no failing
tests. The remaining limitation is promotion applicability/identity evidence,
not an observed empty-condition mismatch or test failure.
