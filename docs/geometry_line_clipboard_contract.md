# Single-line TypeEditZone: actual capture and differential results

Date: 2026-09-16 (Asia/Seoul). Scope: eight human-gated captures, raw preservation, immediate verification, then file-only analysis.

## 1. Decision

**8개 raw bundle을 모두 보존했다. 관측한 좌표·bounds는 수치적으로 일치하지만, 안전한 synthesis 계약은 닫히지 않았다.**

```text
text_slot_milestone_status = stable_pause_point
line_object_structure = partial
line_endpoint_fields = candidate_only
line_derived_fields = partial
line_identity_fields = unresolved
line_clipboard_synthesis_strategy = unresolved
line_clipboard_runtime_readiness = missing_specific_contract
```

주요 차단점:

1. L00_R은 사용자가 검증 구간의 다른 Copy를 보고하여 controlled recopy evidence에서 제외한다.
2. A 삭제 후 변형은 B에 수행했다. 원래 A와 같은 객체라는 identity 비교는 성립하지 않는다.
3. record 0/1이 human P0/P1과 일치하지만, 모든 샘플에서 동시에 componentwise min/max와도 일치한다. 두 순서 가설을 구별하지 못한다.
4. 세 class의 opaque 16-byte metadata window와 record tag의 역할·수명·paste identity/reference 정책이 미해결이다.
5. nonempty property/tail과 전체 Serialize extent는 미해결이다. 세 bounds가 파생 데이터의 전부라는 보장도 없다.

No synthetic candidate emitted. No template patcher or encoder implemented. No paste.

## 2. Artifacts and provenance

- [Actual capture manifest](../research/geometry-line/actual_capture_manifest.json): human statements, unknowns, deviations, actual format IDs, timestamps, sizes, SHA256, verification, final permitted use.
- [Differential results](../research/geometry-line/differential_results.json): per-sample typed observations, raw changed ranges, expected/invariant coordinate profiles, encoding alternatives, bounds checks.
- [File-only analyzer](../research/geometry-line/analyze_capture_files.py): reproducible audit of exactly these eight stored bundles; no clipboard access or payload output.
- [Final integrity](../research/geometry-line/capture_stage_final_integrity.json).
- [Original baseline](../research/geometry-line/capture_stage_baseline_20260916.json): SHA256 of 441 pre-existing tracked files, recorded before capture output writes.
- [Historical capture plan](../research/geometry-line/capture_plan.json): preserved unchanged, not rewritten as actual history.
- [Legacy inventory](../research/geometry-line/evidence.json): preserved historical evidence, not this corpus's current classification.

Each bundle is under `tests/samples/bundles/geometry/geometry_line_<ID>/`:

```text
typeeditzone.bin
typeeditzone_version.bin
manifest.json
capture_metadata.json
```

Matching hex fixtures and human-intent files were created by the existing capture CLI. Final actual-capture metadata is authoritative for corrections and eligibility; the initial generated intent descriptions are not substituted for later disclosures.

## 3. Capture execution

The user alone launched TypeEdit, constructed/edited/selected objects and performed Copy. The agent used only the existing capture CLI with `--no-inspect`, followed immediately by the existing read-only `verify-bundle`.

All samples preserved:

| Format | Runtime registered ID in this session | Exact size for each of 8 samples |
| --- | ---: | ---: |
| TypeEditZone | 49863 | 8192 bytes |
| TypeEditZoneVersion | 49864 | 32 bytes |

IDs are observed session values, not hardcoded format constants. Both format names, per-sample capture UTC/Seoul timestamps and SHA256 values are in actual_capture_manifest.json. Trailing zeros, unused capacity, version bytes and opaque tail were retained.

Each saved bundle passed immediate byte-for-byte verification against clipboard. Each hex fixture round-tripped to its raw TypeEditZone file. These checks establish byte preservation; they do not independently prove intended object provenance. The tools read the two formats separately, without atomic pair capture or continuous clipboard-sequence monitoring.

No semantic analysis occurred between samples. After LZ verification, all analysis used stored files only. No further clipboard reads occurred.

### Environment

The IDE was queried on files in this repository before Python execution. It returned Python 3.14.7 at `C:\work\develop\typeedit-automation\.venv\Scripts\python.exe`. That path was not guessed from a neighboring repository.

The first L00 attempt stopped before clipboard access because pywin32 was missing. Cached pywin32 312 was installed in that configured environment, then L00 was captured. No compiler, TypeEdit process, native shim or vendor API was invoked by the agent.

## 4. Actual corpus and human deviations

All endpoint tuples below are in mm, from human statements. L01's full tuple is reconstructed from the user's explicit baseline restoration and x1-only edit; it was not separately restated or taken from parser output.

| ID | Human endpoint P0 → P1 | Actual lineage/actions | Controlled-use limitation |
| --- | --- | --- | --- |
| L00 | (0,0,0) → (10,0,0) | A constructed by rectangle creation, breakup into segments, straight-line construction and order adjustment | Direct-line tool unavailable according to user; exact tool/state incomplete |
| L00_R | (0,0,0) → (10,0,0) | Initially reported same A, no edits, recopy | Later user reported setting up B and repeatedly copying B during the L00_R protected interval; `capture_interference=true`, excluded |
| L00_N | (0,0,0) → (10,0,0) | B independently created without clone/paste; A deleted because overlap made selection difficult; B repeatedly copied | A preservation violated, copy ordinal unknown, method only “almost the same”; not clean lineage-only contrast |
| L01 | (0,0,0) → (20,0,0) | B initially translated +10 X and copied mistakenly; undo/restoration; endpoint X 10→20; final Copy once | Undo/history and B substitution retained |
| L02 | (0,0,0) → (10,10,0) | B endpoint only moved left 10 to restore baseline, then up 10; no recreation | User clarified movement applied only to endpoint; original-A continuity absent |
| L04 | (-10,0,0) → (10,0,0) | Baseline restored; B start point only moved; no recreation; Copy once | Original-A continuity absent |
| LY0 | (0,-5.25,0) → (10,0,0) | Baseline restored; B start point only moved; no recreation; Copy once | Original-A continuity absent |
| LZ | (0,0,2.5) → (10,0,2.5) | Baseline restored; whole B translated along Z by 2.5; no recreation; Copy once | Valid reported common-Z operation, not separate endpoint Z editing; exact numeric UI/precision unrecorded |

B variants are explicitly `same_object_variant=false` relative to original L00 A. Human “no deletion/recreation” of B does not prove native identity survived earlier undo/edit actions.

Known L00 settings: mm, 레이어1, black. UI precision, origin/workplane, document/session names, line style and width were not established. Later settings were not independently reconfirmed. Unknown fields remain null/labeled inherited in metadata.

L00_R's interference flag is retained **even though its saved bytes equal L00**. Equality cannot override the user's provenance disclosure. Other capture intervals were not continuously monitored; “Copy once” alone is not a timestamped guarantee about all other writers. No interference was fabricated where none was reported.

Strict controlled differential eligibility is not granted to these pairs. Results below are explicitly **descriptive file comparisons**. They are useful measurements, not a repaired controlled corpus.

## 5. Stable descriptor and structural observations

All eight have the exact descriptor/schema sequence:

```text
CZone: schema 1
CCourbe: schema 1
CContour: schema 2
CPropertyExtend: schema 5
```

Observed descriptor framing is `FFFF : u16 schema : u16 ASCII-name-length : ASCII name`. This is an MFC-compatible fingerprint, not proof of a fully synchronized archive/PID/object graph.

Diagnostic descriptor positions are 6, 163, 322, 554 relative to clipboard byte zero. All lengths, relative descriptor positions, the 6-byte prefix `00 00 00 00 01 00`, kind/count candidate and 72-byte record region are stable. Existing parser output is one chain, two records, `polyline_candidate` with provisional confidence.

**Offsets used below are relative to recovered descriptor/record origins.** Absolute offsets in JSON are diagnostic only.

Let H be CContour descriptor start, R the selected point-region start:

| Relative location | Observation |
| --- | --- |
| H + 14 | six binary64 bounds values |
| H + 62 | start of opaque post-bounds metadata |
| H + 138 | CObDao ASCII name in OBJETINFOS_CLASSNAME context |
| H + 152 | u32 kind candidate = 0 |
| H + 156 | u32 point-count candidate = 2 |
| R = H + 160 | first 36-byte record |
| R + 36 | second 36-byte record |
| R + 72 | CPropertyExtend descriptor |

The analyzer obtains R from existing structural selection and cross-checks the relation, count and next descriptor; it does not search arbitrary float coincidences. Existing parser offsets are relative to the first descriptor, which is clipboard +6 here. The analyzer normalizes that explicitly.

A distinct authoritative contour-count field, complete Serialize extent and parent graph are still unresolved. One extracted contour region is not proof of a universal serialized `contour_count=1` field. CObDao strings are not matching class descriptors and are not treated as separate object headers.

## 6. Endpoint numerical evidence

| Record field | Offset from each 36-byte record | Observed interpretation |
| --- | ---: | --- |
| x | +0 | little-endian binary64 candidate |
| y | +8 | little-endian binary64 candidate |
| z | +16 | little-endian binary64 candidate |
| w | +24 | binary64 1.0 in all records; semantics not promoted |
| tag | +32 | u32 low byte 0x0D in all records; high bytes unexplained |

For all 48 xyz observations, bytes exactly match binary64 encoding of the human mm value divided by 1000. All 8×3 bounds blocks also match the corresponding endpoint min/max values at the byte level.

Examples: 10→0.01, 20→0.02, -10→-0.01, -5.25→-0.00525, 2.5→0.0025. The recorded raw field hex and expected raw hex match, not just displayed rounded values.

This demonstrates the tested conversion fingerprint. It does not prove universal document-unit conversion or vendor rounding rules for arbitrary future inputs. No additional precision measurements were made.

| Field profile | Samples that change versus L00 | All others invariant? |
| --- | --- | --- |
| record[0].x | L04 | Yes, measured bytes |
| record[0].y | LY0 | Yes |
| record[1].x | L01 | Yes |
| record[1].y | L02 | Yes |
| record[0].z and record[1].z | LZ | Yes |

The numeric observations include stored R bytes for completeness; R is excluded from causal recopy/identity inference.

### Alternative encoding check

At these structurally selected xyz positions, little-endian f64 with common multiplier 1000 to mm explains all values. f32, signed int32 and signed int64 interpretations each fail five observations even after fitting one common multiplier from the first nonzero value. This is a bounded alternative test, not a proof against arbitrary encodings or field-specific invented scales elsewhere in the payload.

### Why endpoint status remains candidate_only

| Required criterion | Result |
| --- | --- |
| Same structural typed location | Observed across this family |
| Changes when expected | Matches stored corpus |
| Remains invariant when expected | Matches stored corpus |
| One consistent conversion rule | Exact tested binary64(mm/1000) match |
| No equally explanatory candidate | **Not met** |
| Controlled provenance sufficient for promotion | **Not met** |

Each coordinate's profile also occurs in the corresponding bounds fields. More significantly, all P0 components are <= P1 components in this capture set. Record 0=P0 / record 1=P1 and record 0=min / record 1=max both fit perfectly. Negative x0 and negative y0 still leave that ordering intact. Common z changes both records together and cannot distinguish independent endpoint z semantics.

Thus creation-direction ordering is not resolved. We report measured xyz slots without upgrading a general P0/P1 encoding contract.

## 7. Bounds and additional changed data

The three blocks hold:

```text
min_x, min_y, min_z, max_x, max_y, max_z
```

Their observed starts relative to each descriptor:

| Descriptor | Bounds start |
| --- | ---: |
| CZone | +11 |
| CCourbe | +13 |
| CContour | +14 |

All six fields in all three blocks match endpoint min/max for every sample, including negative/fractional XY and common nonzero Z. Each block is 48 bytes. No observed rounding mismatch occurred.

However, coordinate changes also accompany unexplained changes in opaque metadata. Define M as the byte immediately after each 48-byte bounds block. A 16-byte **observational window at M+28** covers the following differences:

| Class-relative window | Observed changes |
| --- | --- |
| CZone descriptor +87, length 16 | A→B baseline changes; B's XY variants retain B baseline window; LZ whole-object Z movement changes it |
| CCourbe descriptor +89, length 16 | A→B baseline and every B coordinate variant |
| CContour descriptor +90, length 16 | A→B baseline and every B coordinate variant |

These are diff-aligned opaque windows, not proven serialized field boundaries. They are classified **unknown**. A length of 16 and apparent variability do not establish GUID semantics. They may not be regenerated, zeroed, copied into new identities, or treated as derived values.

Tags: A's records have 0x3A726C0D / 0x67696C0D; B baseline and all B variants have 0x4E45400D / 0x0000000D. Only the low byte is common. High-byte meaning is unresolved.

All observed changed bytes in the analyzed pairs are covered by xyz, three bounds, these opaque windows, or tag high bytes. That coverage is not evidence that the remaining stable bytes are irrelevant, nor that three bounds are the entire derived-data set. Cached length, flags and unseen dependent fields remain unresolved.

## 8. Required pair differences

Counts below are differing **bytes**, not field count. Unknown includes opaque windows and tag bytes.

| Pair | Total changed bytes | Unknown changed bytes | Use |
| --- | ---: | ---: | --- |
| L00 ↔ L00_R | 0 | 0 | Raw equality only; recopy provenance invalid |
| L00 ↔ L00_N | 53 | 53 | Confounded A/B contrast, no identity conclusion |
| L00 ↔ L01 | 58 | 54 | Descriptive x1 profile + unknown changes |
| L00 ↔ L02 | 85 | 53 | Descriptive y1 profile + unknown changes |
| L00 ↔ L04 | 85 | 53 | Descriptive x0 profile + unknown changes |
| L00 ↔ LY0 | 85 | 53 | Descriptive y0 profile + unknown changes |
| L00 ↔ LZ | 118 | 54 | Descriptive common-Z profile + unknown changes |

Because A was deleted, supplementary **file-only** contrasts also compare B baseline L00_N to the five B variants. These do not replace the requested L00 comparisons or retroactively repair provenance:

| B baseline ↔ variant | Changed bytes | Unknown |
| --- | ---: | ---: |
| L00_N ↔ L01 | 36 | 32 |
| L00_N ↔ L02 | 64 | 32 |
| L00_N ↔ L04 | 63 | 31 |
| L00_N ↔ LY0 | 64 | 32 |
| L00_N ↔ LZ | 112 | 48 |

The 31-versus-32 count reflects coincidentally equal bytes within changed windows, not different window lengths.

Changed-range categories used in evidence are `geometry-variable`, `derived-geometry-variable` for the measured slots and `unknown` for the rest. We assign no proven `same-copy-variable` or `object-lineage-variable` ranges: R was interfered and N's construction/deletion/repeated-copy history confounds that attribution. No range is labeled GUID.

## 9. TypeEditZoneVersion and opaque property/tail

All eight version payloads are byte-identical, 32 bytes:

```text
01 00 00 00 51 02 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

SHA256: `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f`.

No geometry/copy/object dependence is observed within the saved corpus. The compromised recopy contrast and single session prevent a universal independence claim. Byte meaning remains uninterpreted.

The CPropertyExtend descriptor is stable. The region from descriptor+21 to buffer end is 7617 bytes, contains 14 nonzero bytes, and is byte-identical in all eight samples.

SHA256: `5b249eba26725e118ec261bd613ca27423e86d15e4e9687e83ad1f4731099a3e`.

This is an opaque region-to-buffer-end, not a decoded extension length. It cannot pass a “known empty extension” gate merely because most bytes are zero. No bytes were trimmed.

## 10. Identity, layer and parent

CZone exists explicitly; no new native model inference was used. Whether it is a detached clipboard zone with portable parent semantics remains unresolved. The absence of CCalque/CObjGuid labels does not exclude unnamed references/identity data.

Changing opaque windows in the same user-held B are evidence that “same visible object” does not guarantee invariant serialized metadata. They do not prove new GUID generation, object replacement, timestamps or invalid data.

Even an unconfounded copy/recopy comparison would not prove paste-time identity regeneration. No paste occurred, so GUID retention/regeneration and reference safety remain unresolved. Preserving unknown identity bytes in a reused template is not accepted as safe.

## 11. Synthesis and fail-closed gate

Template mutation remains the preferable future approach if mandatory contracts are later proven. Neither template mutation nor full encoding is currently authorized by evidence, so strategy remains `unresolved`.

| Gate | Current state |
| --- | --- |
| Exactly one intended selection / stored raw pair | Human declarations and complete raw pairs exist; deviations retained |
| Known descriptor/schema family | Stable in this corpus |
| Full object/contour counts and Serialize extent | Partial; authoritative contour-count/reference framing unresolved |
| Endpoint direction and unique semantic mapping | Candidate only |
| Complete derived geometry and rounding | Tested three blocks agree; completeness/global rounding unresolved |
| Identity/reference lifecycle | Unresolved |
| Unknown nonempty extension | Present opaque region; reject |
| Semantic length vs backing capacity | Unresolved; 8192 is observed storage size |
| Protected capture provenance | R invalid; A→B changes and history prevent strict promotion |

Unexpected schema, unexpected counts, unresolved identity, unknown derived layout, unknown nonempty extension or length mismatch must reject. “Only change endpoints and keep everything else” is not a supported fallback.

## 12. Integrity, scope and completion

All eight raw pairs and hex roundtrips were rechecked from files before analysis. Raw SHA256 values were verified again after analysis. Final integrity checks compare the 441-file pre-capture baseline, exempting only this explicitly requested updated document.

The historical capture_plan.json, text authoritative contract, parser/model code, existing tools and all other pre-existing tracked files are required unchanged; the final ledger records the actual result. New files are capture outputs and geometry-line research artifacts.

No vendor files were accessed. No TypeEdit automation, key injection, paste, synthetic payload, native bridge/shim or text character-width work occurred. The only environment change was the required pywin32 dependency install in the IDE-configured environment.

**This capture task is complete.** No extra captures are added to repair the compromised protocol. The plan stops at `missing_specific_contract`; unresolved identity/reference windows, full framing and record direction must be established before any mutator design is justified. No further operation is performed here.


## 13. Controlled metadata micro-corpus (2026-09-16)

This section adds a separate five-sample experiment. Sections 1–12 and the eight prior capture bundles/results remain historical evidence; their compromised controls are not retroactively repaired. The accepted structure, endpoint, derived-field, identity, synthesis and runtime-readiness classifications remain unchanged.

Artifacts:

- [Micro-corpus manifest](../research/geometry-line/metadata_microcorpus_manifest.json): capture order, human statements, fixed settings, unknowns, deviations and per-bundle metadata.
- [Metadata variability results](../research/geometry-line/metadata_variability_results.json): exact changed offsets, pairwise ranges, every window/tag byte profile and retained-buffer comparisons.
- [File-only analyzer](../research/geometry-line/analyze_metadata_microcorpus.py): audits exactly these five stored bundles; never reads or writes the clipboard.
- [Repository baseline](../research/geometry-line/metadata_microcorpus_baseline.json): HEAD `ef199a2ff583c7ebcdd6fa0af39f7cefe263440e`, clean initial status and SHA256 of 495 tracked files before output writes.
- [Completion integrity](../research/geometry-line/metadata_microcorpus_integrity.json).

### Capture controls and provenance

Exactly M00, M00_R1, M00_R2, M00_ER and M00_N were captured with the existing CLI using `--category geometry --object-count 1 --grouping not_grouped --no-inspect`. Each capture preserved TypeEditZone (8192 bytes, runtime ID 49863) and TypeEditZoneVersion (32 bytes, runtime ID 49864), then recorded SHA256 and immediately passed `clipboard_typeeditzone.py verify-bundle` for both formats. Format IDs are observations, not portable constants. Timestamps and hashes are retained per bundle.

C was freshly constructed just after starting Type3 by creating a rectangle, splitting it into segments and retaining only the straight line. User-confirmed actual geometry is (0,0,0) -> (10,0,0) mm, layer `레이어 1`, black, no custom line settings. The two clean recopies were made without changes. ER used vertex edit mode to move only the endpoint right 10 mm and then left 10 mm, returning to default mode before Copy; no Undo was used. The same visible C was retained. This does not establish internal identity replacement or retention.

D was independently constructed by the same rectangle/split/retain procedure, with the same session, document and settings explicitly confirmed. Only D was selected, count 1, not grouped. Whether C was moved aside after ER was not reported; overlap avoidance was optional and no movement is invented. All final coordinates and units were human-confirmed. Exact document/session identifiers, origin/workplane, default line style/width and UI precision remain unknown. These are disclosed limits rather than inferred values.

Human gates confirmed object/geometry, single selection and Copy before clipboard reads. No other Copy was reported. ER's narrower no-other-Copy wording is preserved; it was not rewritten as an explicit broader clipboard-operation attestation. Immediate equality confirms raw preservation, not absence of interference independently of human reports. There was no reported or suspected interference. The tool reads the two formats separately and does not continuously monitor the protected interval.

No semantic comparison occurred until all five captures and verifications were complete. Clipboard access then ended. All analysis below used saved files only.

### Complete differential result

Offsets below are zero-based absolute offsets, with exclusive range ends. The 16-byte windows are observational extents, not established serialized field boundaries.

| Comparison | Changed TypeEditZone bytes | Changed ranges |
| --- | ---: | --- |
| M00 ↔ M00_R1 | 0 | None |
| M00 ↔ M00_R2 | 0 | None |
| M00_R1 ↔ M00_R2 | 0 | None |
| M00 ↔ M00_ER | 32 | [252,268), [412,428) |
| M00 ↔ M00_N | 51 | [93,109), [252,268), [412,428), [551,554) |

The full 8192-byte search found no other varying offsets. Both coordinate blocks and all three bounds blocks are byte-identical in all five samples and match the baseline geometry under the already accepted encoding observations. This is a consistency check, not a new coordinate-encoding or record-direction claim.

| Region | Absolute offsets | Clean recopies | After edit/restore | Independent D | Classification within this corpus |
| --- | --- | --- | --- | --- | --- |
| CZone descriptor +87, length 16 | [93,109) | Stable | Unchanged | Changed | object-lineage-variable candidate |
| CCourbe descriptor +89, length 16 | [252,268) | Stable | Changed | Changed | edit-history-variable candidate; separately object-lineage-variable candidate |
| CContour descriptor +90, length 16 | [412,428) | Stable | Changed | Changed | edit-history-variable candidate; separately object-lineage-variable candidate |
| record 0 tag low byte | [514,515) | Stable | Unchanged | Unchanged | stable: 0x0D |
| record 0 tag upper bytes | [515,518) | Stable | Unchanged | Unchanged | stable within these five captures |
| record 1 tag low byte | [550,551) | Stable | Unchanged | Unchanged | stable: 0x0D |
| record 1 tag upper bytes | [551,554) | Stable | Unchanged | Changed | object-lineage-variable candidate |

Every byte within each listed changed window changes in the indicated contrast; exact byte values and offsets remain in machine-readable evidence. Record 0 tag is `0x4346440D` in all five samples. Record 1 tag is `0x6F422C0D` in all C samples and `0x5F4E480D` in D. These are little-endian u32 representations, not semantic names.

No copy volatility was observed: `copy_variability_not_observed`. Three identical serializations strengthen the unchanged-C observation, but do not establish invariance across all copies or sessions. The ER and D facts remain separate even where they affect the same window. No GUID, timestamp, checksum or object ID meaning is assigned. Variation with identical final geometry rules out final coordinates alone as a sufficient explanation for these changes; their underlying field semantics remain unknown.

All five complete 32-byte Version payloads are exactly equal. All five complete regions from the CPropertyExtend descriptor at offset 554 through the retained buffer end at 8192 (7638 bytes, including the descriptor) are exactly equal. This does not establish an empty extension or its semantic length. Both record +24 values remain binary64 1.0.

```text
line_copy_variability = not_observed
line_edit_history_variability = observed
line_object_lineage_variability = observed
line_opaque_metadata_role = mixed
opaque_fields_preservation_for_template_mutation = unresolved
```

The mixed role reflects distinct observed profiles: CZone and record 1 high bytes vary only for D, while CCourbe and CContour also vary after editing and restoring C. Candidate labels do not prove a causal identity mechanism. One edit cycle and one independent D cannot settle all construction/history/session effects.

### Synthesis consequence and stopping point

Opaque fields cannot currently be justified as safe to preserve unchanged during coordinate mutation. The edit/restore cycle changed two windows despite byte-identical final coordinates and bounds. This does not prove that preserving them would fail, so the preservation classification is `unresolved`, not a demonstrated incompatibility. Even unchanged windows provide no paste-time identity/reference evidence.

Existing `line_object_structure = partial`, `line_endpoint_fields = candidate_only`, `line_derived_fields = partial`, `line_identity_fields = unresolved`, `line_clipboard_synthesis_strategy = unresolved`, and `line_clipboard_runtime_readiness = missing_specific_contract` remain accepted. Direction versus min/max ordering remains a separate unresolved contract.

Recommended next task (recommendation only; not executed):

Perform one bounded exact-replay geometry paste experiment using an unmodified vendor-captured bundle to determine TypeEdit's paste-time identity/reference behavior; do not synthesize coordinates yet.

This task stops at metadata variability classification. No synthesis, clipboard rewrite/load, paste, TypeEdit automation, additional exploratory captures, vendor inspection, native API work or text character-width work occurred.
## 14. Bounded exact M00 replay into a blank document (2026-09-16)

One unmodified M00 bundle was restored to the clipboard, pasted once by the user, and the resulting single object was copied once. **The complete post-paste TypeEditZone and TypeEditZoneVersion are byte-for-byte identical to source M00.** No opaque rewrite was observed in this replay.

Artifacts:

- [Replay manifest](../research/geometry-line/exact_replay_paste_manifest.json): source validation, overwrite approval, blank-document preparation, exact load/readback, runtime observations and post-paste capture provenance.
- [Replay results](../research/geometry-line/exact_replay_paste_results.json): structure, geometry, complete raw differential, all specified windows/tags, property/tail and version comparisons.
- [File-only analyzer](../research/geometry-line/analyze_exact_replay_paste.py).
- [Baseline](../research/geometry-line/exact_replay_paste_baseline.json) and [completion integrity](../research/geometry-line/exact_replay_paste_integrity.json).
- Post-paste bundle: `tests/samples/bundles/geometry/geometry_line_replay_M00_postpaste/`.
- Loaded clipboard readback evidence: `research/geometry-line/exact_replay_M00_loaded_readback/`.

### Source, load and human runtime observations

The sole source was `tests/samples/bundles/geometry/geometry_line_meta_M00/`. Before the write, both raw files matched the SHA256 and sizes recorded in the micro-corpus manifest. Source manifest/capture metadata also matched their recorded pre-write baseline hashes. The micro-corpus manifest records raw hashes; it does not contain hashes of its metadata JSON files, so those checks are explicitly distinguished.

The existing `clipboard_typeeditzone.py load-bundle --dir tests/samples/bundles/geometry/geometry_line_meta_M00` path was inspected and used without modification. It reads stored bytes, registers formats by name, empties the clipboard and writes both formats. No registered ID was hardcoded for the operation. No payload bytes, padding, tags, opaque metadata, coordinates, bounds or Version were changed or regenerated.

The user confirmed a new empty unsaved document, writable `레이어 1`, and authorized replacement of the current Windows clipboard after the warning. Document units were not confirmed before loading and were recorded as unknown. The user subsequently reported exactly 10 mm length and endpoints (0,0,0) -> (10,0,0).

Immediate `verify-bundle` passed after the single load. Existing `dump-bundle` preserved a readback and its runtime IDs; byte equality and SHA256 were independently checked from those saved readback files before the Paste instruction.

| Format | Runtime ID | Source / loaded / post-paste size | SHA256 shared by all three |
| --- | ---: | ---: | --- |
| TypeEditZone | 49863 | 8192 | `8a958920b28afef446818c558d17c6906ee96180ad58967126e87e727e1241cb` |
| TypeEditZoneVersion | 49864 | 32 | `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f` |

Timestamps, raw-equality results and source/readback hashes are in the manifest. IDs are observations in this runtime, not portable constants.

The user performed exactly one Paste and reported no errors, exactly one object, source-equivalent position/length/orientation, and automatic selection. Before Copy, the user deselected the object, selected vertices and viewed its length. The user explicitly confirmed no editing, save, Undo or Redo. This inspection/selection history is retained; the observation covers the entire paste/selection/viewing/Copy lifecycle rather than isolating Paste alone.

The user then selected only that ungrouped pasted object, copied exactly once, and confirmed no other clipboard-producing operation after Copy. Existing capture CLI flags were `--category geometry --object-count 1 --grouping not_grouped --no-inspect`. Raw preservation and SHA256 recording were followed immediately by `verify-bundle`, which passed for both formats. Clipboard access then stopped; all subsequent comparisons were file-only. The user was told that runtime work was complete and that the disposable document could be manually closed/discarded. No automatic Save/Don't Save or shutdown action was taken, and the actual cleanup action is not asserted.

### Structure and complete comparison

Structure was checked before semantic interpretation. Both payloads retain CZone schema 1 at offset 6, CCourbe schema 1 at 163, CContour schema 2 at 322, and CPropertyExtend schema 5 at 554. Kind candidate is 0, point-count candidate is 2, and two 36-byte records begin at 482. No structural change was observed.

Offsets below are zero-based absolute offsets with exclusive ends.

| Comparison region | Result |
| --- | --- |
| Complete TypeEditZone [0,8192) | Exactly equal; 0 changed bytes |
| Both observed record xyz fields | Byte-identical and numerically equal |
| All three observed bounds blocks | Byte-identical and numerically equal |
| CZone window [93,109) | Exactly equal |
| CCourbe window [252,268) | Exactly equal |
| CContour window [412,428) | Exactly equal |
| record 0 tag [514,518) | Exactly equal: `0x4346440D` |
| record 1 tag [550,554) | Exactly equal: `0x6F422C0D` |
| All bytes outside those windows/tags | Exactly equal |
| CPropertyExtend descriptor through retained buffer end [554,8192) | Exactly equal; 7638 bytes |
| Complete Version [0,32) | Exactly equal |

Both tag low bytes remain `0x0D`; their upper three bytes are unchanged. The observational window lengths are not asserted serialized field boundaries. The retained property/tail is not called empty or identity-free. The raw payloads were not normalized or trimmed.

```text
exact_replay_paste = accepted
paste_geometry_fidelity = byte_identical
post_paste_reserialization = byte_identical
paste_opaque_metadata_rewrite = not_observed
paste_serialized_identity_behavior = preservation_candidate
line_clipboard_document_portability = observed_in_one_replay
opaque_fields_preservation_for_template_mutation = unresolved
line_clipboard_runtime_readiness = missing_specific_contract
```

### Interpretation, integrity and next task

The captured payload was portable across this one tested blank-document context. No opaque rewrite was observed in the saved post-paste serialization. This does not identify an actual identity field, establish GUID/object-ID preservation, rule out unobserved internal changes, or generalize to other sessions, versions or document types.

A blank-document replay does not test collision with the original object. No duplicate-identity safety claim or template-mutation promotion follows from one exact replay. The accepted metadata micro-corpus classifications remain unchanged. Direction versus min/max ordering also remains unresolved.

Before new output writes, a clean tracked-file baseline was recorded at HEAD `337cc4b2f0aa37a699cbd32f036073229809cc4c` for 540 files. Completion checks preserve all 539 other pre-existing tracked files and the exact historical prefix of this contract, including all five micro-corpus bundles, the older eight bundles, prior differential/metadata results and the text authoritative contract.

Recommended next task only:

Perform exactly one bounded duplicate-identity replay experiment before coordinate synthesis.

This experiment is complete. No second paste, coordinate synthesis, metadata or Version mutation, new clipboard writer, loader modification, TypeEdit automation, vendor-file inspection, native/mixed-mode work or text character-width investigation occurred.
## 15. Accepted duplicate exact-M00 replay: R2

**TypeEdit accepted two coexisting objects produced from the same exact serialized clipboard payload in this bounded test.** After both captures were complete, the user performed full selection and reported `2 영역에서의 다중 선택`, confirming two objects. The earlier trial and its derived anomaly diagnosis were explicitly withdrawn by the user and removed from the working tree to prevent reuse. R2 is the authoritative duplicate-replay result. A suspected earlier accidental Paste is unconfirmed and is not a causal finding.

Artifacts:

- [R2 manifest](../research/geometry-line/duplicate_identity_replay_R2_manifest.json).
- [R2 results](../research/geometry-line/duplicate_identity_replay_R2_results.json).
- [File-only analyzer](../research/geometry-line/analyze_duplicate_identity_replay_R2.py).
- [R2 baseline](../research/geometry-line/duplicate_identity_replay_R2_baseline.json) and [final integrity](../research/geometry-line/duplicate_identity_replay_R2_integrity.json).
- [Minimal withdrawal ledger](../research/geometry-line/duplicate_replay_retirement.json): removed paths/hashes and authorization only; not experimental evidence.
- Raw captures: `tests/samples/bundles/geometry/geometry_line_duplicate_R2_preexisting_M00/` and `geometry_line_duplicate_R2_second_M00/`.

### Bounded sequence and provenance

The user confirmed a new blank unsaved document with no objects or valuable work, writable `레이어 1`, and approved original M00 clipboard load/reload. Units were not separately confirmed; first-paste endpoints visually matched (0,0,0) -> (10,0,0). Original source hashes were checked before each of exactly two loads using the existing unmodified `load-bundle`; both immediate `verify-bundle` checks passed. No payload bytes were modified.

After the first user Paste, the automatic selection displayed `1 곡선 개체`. The user copied once, reported no error or other action, and the existing capture CLI preserved both raw formats using `--category geometry --object-count 1 --grouping not_grouped --no-inspect`. Immediate verification and a complete file comparison established exact M00 equality before the second load. Original stored M00 was reloaded, never the first capture.

After the second user Paste, automatic selection again displayed `1 곡선 개체`. The user preserved that selection and copied once without other action. Both raw formats were captured and immediately verified; clipboard access then stopped. No error was reported for the second Paste; explicit no-error wording was not separately repeated. Grouping metadata follows the single-line replay context and selected curve-object report.

The user initially declined extra drag checks; neither capture was preceded by a full-selection count action. After capture completion, the user voluntarily performed full selection and reported **`2 영역에서의 다중 선택`**, stating that two objects were correct. This later count is separate from each automatic selected count of one. Its exact event timestamp is unavailable; the manifest records report-ingestion time separately. UI semantics are based on human report, not independently verified documentation. Together with the blank-document confirmation, two reported pastes, no intervening edits and the two exact selected-payload captures, this supports the bounded coexistence conclusion.

The first object was not independently copied after the second Paste. The result does not prove preservation of its internal state. No object movement, third Paste, coordinate synthesis, TypeEdit automation, native/vendor inspection or text-width work was performed.

### Complete file comparison

Source M00, first-object capture and second-object capture are byte-identical in both formats. All three pairwise comparisons have zero changed bytes.

| Format | Bytes | SHA256 shared by all three |
| --- | ---: | --- |
| TypeEditZone | 8192 | `8a958920b28afef446818c558d17c6906ee96180ad58967126e87e727e1241cb` |
| TypeEditZoneVersion | 32 | `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f` |

Descriptor schemas and layout, both xyz records, all three bounds, opaque windows `[93,109)`, `[252,268)`, `[412,428)`, tags `[514,518)` and `[550,554)`, all bytes outside those regions, and property/tail `[554,8192)` are unchanged. Offsets are zero-based and ends exclusive. No normalization or trimming was used. No empty-extension or identity-field semantics are asserted.

```text
duplicate_identity_replay = accepted_two_objects
preexisting_object_exact_M00 = true
duplicate_second_object_reserialization = byte_identical_to_M00
duplicate_paste_opaque_rewrite = not_observed
duplicate_exact_payload_coexistence = observed_in_one_document
line_identity_fields = unresolved
opaque_fields_preservation_for_template_mutation = unresolved
line_clipboard_runtime_readiness = missing_specific_contract
```

This lowers concern that retaining the exact opaque state necessarily causes an immediate collision in this tested document. It does not identify GUID/object ID fields, generalize across sessions/versions/documents, or establish safety under coordinate mutation. The record-direction versus componentwise min/max contract remains unresolved.

### Completion and integrity

R2 raw files, M00 micro-corpus, initial exact-replay evidence and earlier geometry corpus are preserved. Explicitly withdrawn duplicate-trial artifacts and their derived diagnosis were deleted; the minimal retirement ledger makes those authorized removals distinct from corruption in the original R2 baseline. That baseline remains a historical hash inventory, not an endorsement of retired paths. The contract's earlier sections are preserved; superseded duplicate/anomaly sections were replaced by this final R2 account. No further runtime action is requested. The user may manually close/discard the disposable document.

Recommended next task only:

Capture one direction-disambiguating line whose user-defined start point is componentwise greater than its end point; do not synthesize coordinates yet.

## 16. D00: directed endpoint order resolved (2026-09-16)

**Current endpoint status: `line_record_order = creation_direction`, `line_endpoint_fields = resolved` for the observed single-line family and tested ordering hypotheses.** This supersedes earlier sections' historical direction/minmax ambiguity; previous capture/result artifacts remain unchanged.

Artifacts: [direction manifest](../research/geometry-line/direction_disambiguation_manifest.json), [direction results](../research/geometry-line/direction_disambiguation_results.json), [file-only analyzer](../research/geometry-line/analyze_direction_disambiguation.py), [baseline](../research/geometry-line/direction_disambiguation_baseline.json), [integrity](../research/geometry-line/direction_disambiguation_integrity.json). The only new capture is `tests/samples/bundles/geometry/geometry_line_direction_D00/`.

The user reported that vertex order determines line direction and that the UI allows setting a start point, then explicitly stated construction/orientation as START (10,10,0) -> END (0,0,0) mm. Ground truth is this human vertex/start-point statement, not an inference from screen position. The user confirmed `레이어 1`, black, not grouped, Copy once and no other action. Copy followed the instruction to select only that line; the final user reply did not independently repeat the numeric selected count. `--object-count 1` remains intent metadata, not selection validation. Exact construction command sequence, start-setting command name, line style/width, origin/workplane, document/session identifiers and UI precision are not supplied. Same construction family as M00 is not silently assumed.

Exactly one capture used the existing CLI with `--category geometry --object-count 1 --grouping not_grouped --no-inspect`. Both raw formats and hashes were preserved before interpretation. Immediate `verify-bundle` passed exactly; clipboard access then stopped. Runtime format IDs were 49863 (TypeEditZone, 8192 bytes) and 49864 (Version, 32 bytes). Per-format SHA256 and timestamps are in the bundle/manifest. No clipboard interference was reported, and no adaptive recapture occurred.

Before coordinate decoding, the file-only audit confirmed CZone schema 1 at 6, CCourbe schema 1 at 163, CContour schema 2 at 322 and CPropertyExtend schema 5 at 554; kind candidate 0, point-count candidate 2 and two 36-byte records beginning at 482. Coordinates were read only at the established record +0/+8/+16 little-endian binary64 locations. No other float candidates were searched.

| Observed region | Stored values | UI mm using accepted ×1000 |
| --- | --- | --- |
| record 0 xyz, offset 482 | (0.01,0.01,0) | (10,10,0) = human START |
| record 1 xyz, offset 518 | (0,0,0) | (0,0,0) = human END |
| CZone bounds, descriptor +11 | (0,0,0,0.01,0.01,0) | min (0,0,0), max (10,10,0) |
| CCourbe bounds, descriptor +13 | Same | Same |
| CContour bounds, descriptor +14 | Same | Same |

Both endpoint sequences were checked against exact expected binary64 bytes, not a loose tolerance. Creation-direction prediction matches; componentwise-minmax prediction does not. START exceeds END in X/Y and ties in Z, which still produces mutually exclusive order predictions. Three bounds match exact expected min/max bytes independently of endpoint order. This separates ordered primary endpoint observations from the three derived unordered bounds; it does not prove derived-field completeness.

The result resolves endpoint xyz/order for this observed single-line family using the accepted prior coordinate mapping plus this new discriminator. It is not a universal claim about all geometry types, arbitrary sorting rules or native object internals. There is no competing mapping among the two specified order hypotheses. Opaque uncertainty does not block this narrower endpoint resolution.

Raw windows `[93,109)`, `[252,268)`, `[412,428)`, `[514,518)` and `[550,554)` are recorded only as uninterpreted provenance in the results; no normalization or semantic naming was applied. The full 32-byte Version is byte-identical to M00, SHA256 `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f`.

```text
line_record_order = creation_direction
line_endpoint_fields = resolved
line_derived_fields = partial
line_identity_fields = unresolved
opaque_fields_preservation_for_template_mutation = unresolved
line_clipboard_runtime_readiness = missing_specific_contract
```

Full Serialize extent, property/tail semantics, opaque-field preservation and complete derived-field behavior remain separate unresolved contracts. No readiness for synthetic paste is inferred. All pre-existing bundles/results, R2 evidence, micro-corpus and text contract are preserved; this section is appended to the prior contract. No Paste, payload mutation, TypeEdit automation, duplicate replay, native/vendor analysis or text-width work occurred.

Recommended next task only:

Reassess whether the observed opaque metadata can be safely carried through a minimal coordinate-template mutation now that endpoint ordering is resolved; do not generate or paste a synthetic payload yet.