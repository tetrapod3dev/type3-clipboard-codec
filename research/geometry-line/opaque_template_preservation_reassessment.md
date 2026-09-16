# Opaque template preservation: static reassessment

**Preserving every non-coordinate byte while changing xyz and three bounds remains unresolved.** Endpoint ordering is resolved; no stale-state mutation acceptance has been tested. No synthetic payload was constructed.

## Evidence and B lineage controls

Sixteen saved bundles were read: L00, L00_N, L01, L02, L04, LY0, LZ, M00, M00_R1, M00_R2, M00_ER, M00_N, D00, replay, R2_first, R2_second. L00_N is the documented B baseline; no geometry-variant causal claim is made against original A/L00. Prior L01 move/Undo, restoration steps and fixed-setting unknowns are retained. Captured copy equality does not undo those limitations.

## Exact B profiles

| Region | L00_N | L01 | L02 | L04 | LY0 | LZ |
| --- | --- | --- | --- | --- | --- | --- |
| CZone | unchanged | unchanged | unchanged | unchanged | unchanged | changed |
| CCourbe | unchanged | changed | changed | changed | changed | changed |
| CContour | unchanged | changed | changed | changed | changed | changed |
| record0.tag.upper | unchanged | unchanged | unchanged | unchanged | unchanged | unchanged |
| record1.tag.upper | unchanged | unchanged | unchanged | unchanged | unchanged | unchanged |

Relative to baseline and between successive stored edits, CCourbe/CContour change at every sampled stage; CZone changes only at the LZ step; both tags remain constant. This is association with the recorded operation/history, not a Z-specific or every-UI-edit law.

### CZone

| Sample | Exact bytes |
| --- | --- |
| L00_N | `fb64a724641e0b4da4414fdae7121a4a` |
| L01 | `fb64a724641e0b4da4414fdae7121a4a` |
| L02 | `fb64a724641e0b4da4414fdae7121a4a` |
| L04 | `fb64a724641e0b4da4414fdae7121a4a` |
| LY0 | `fb64a724641e0b4da4414fdae7121a4a` |
| LZ | `a60abed6cacc1845a81e997f43c976ce` |

### CCourbe

| Sample | Exact bytes |
| --- | --- |
| L00_N | `f8b2b69a9e6f3e4aad4844942e252665` |
| L01 | `4a8c7fdb1bcf0648b8edb1228854db9c` |
| L02 | `f3a77fa4b5a1c64cb954dcf086b993a9` |
| L04 | `34fba6d00605e145ad1002fffb8d90d5` |
| LY0 | `11baa2e3a8834843a6679caab30ff5cd` |
| LZ | `adf5a81bdb2d4d4892f7a27ea72c5df6` |

### CContour

| Sample | Exact bytes |
| --- | --- |
| L00_N | `1e639f2be8030540b3b49992789c2063` |
| L01 | `99c3936fef4f81458ee5aa0131f8aab1` |
| L02 | `90cca2396b3c3048b8272f58bd736ebf` |
| L04 | `9d4c69acfee4124e839d27142f01bd43` |
| LY0 | `b6ce04702ea3e74a8fa45bfdeb805a0b` |
| LZ | `8f2a88de1da5f3499e189bccf94c77a4` |

### record0.tag.upper

| Sample | Exact bytes |
| --- | --- |
| L00_N | `40454e` |
| L01 | `40454e` |
| L02 | `40454e` |
| L04 | `40454e` |
| LY0 | `40454e` |
| LZ | `40454e` |

### record1.tag.upper

| Sample | Exact bytes |
| --- | --- |
| L00_N | `000000` |
| L01 | `000000` |
| L02 | `000000` |
| L04 | `000000` |
| LY0 | `000000` |
| LZ | `000000` |

## Complete B raw differences

Every changed byte was assigned by fixed ranges; adjacent runs split at role boundaries. JSON retains individual offsets and before/after bytes.

### L00_N to L01

| Range [start,end) | Role | Before | After |
| --- | --- | --- | --- |
| [47,48) | derived bounds | `84` | `94` |
| [206,207) | derived bounds | `84` | `94` |
| [252,268) | opaque metadata | `f8b2b69a9e6f3e4aad4844942e252665` | `4a8c7fdb1bcf0648b8edb1228854db9c` |
| [366,367) | derived bounds | `84` | `94` |
| [412,428) | opaque metadata | `1e639f2be8030540b3b49992789c2063` | `99c3936fef4f81458ee5aa0131f8aab1` |
| [524,525) | primary endpoint | `84` | `94` |

### L00_N to L02

| Range [start,end) | Role | Before | After |
| --- | --- | --- | --- |
| [49,57) | derived bounds | `0000000000000000` | `7b14ae47e17a843f` |
| [208,216) | derived bounds | `0000000000000000` | `7b14ae47e17a843f` |
| [252,268) | opaque metadata | `f8b2b69a9e6f3e4aad4844942e252665` | `f3a77fa4b5a1c64cb954dcf086b993a9` |
| [368,376) | derived bounds | `0000000000000000` | `7b14ae47e17a843f` |
| [412,428) | opaque metadata | `1e639f2be8030540b3b49992789c2063` | `90cca2396b3c3048b8272f58bd736ebf` |
| [526,534) | primary endpoint | `0000000000000000` | `7b14ae47e17a843f` |

### L00_N to L04

| Range [start,end) | Role | Before | After |
| --- | --- | --- | --- |
| [17,25) | derived bounds | `0000000000000000` | `7b14ae47e17a84bf` |
| [176,184) | derived bounds | `0000000000000000` | `7b14ae47e17a84bf` |
| [252,260) | opaque metadata | `f8b2b69a9e6f3e4a` | `34fba6d00605e145` |
| [261,268) | opaque metadata | `4844942e252665` | `1002fffb8d90d5` |
| [336,344) | derived bounds | `0000000000000000` | `7b14ae47e17a84bf` |
| [412,428) | opaque metadata | `1e639f2be8030540b3b49992789c2063` | `9d4c69acfee4124e839d27142f01bd43` |
| [482,490) | primary endpoint | `0000000000000000` | `7b14ae47e17a84bf` |

### L00_N to LY0

| Range [start,end) | Role | Before | After |
| --- | --- | --- | --- |
| [25,33) | derived bounds | `0000000000000000` | `1b2fdd24068175bf` |
| [184,192) | derived bounds | `0000000000000000` | `1b2fdd24068175bf` |
| [252,268) | opaque metadata | `f8b2b69a9e6f3e4aad4844942e252665` | `11baa2e3a8834843a6679caab30ff5cd` |
| [344,352) | derived bounds | `0000000000000000` | `1b2fdd24068175bf` |
| [412,428) | opaque metadata | `1e639f2be8030540b3b49992789c2063` | `b6ce04702ea3e74a8fa45bfdeb805a0b` |
| [490,498) | primary endpoint | `0000000000000000` | `1b2fdd24068175bf` |

### L00_N to LZ

| Range [start,end) | Role | Before | After |
| --- | --- | --- | --- |
| [33,41) | derived bounds | `0000000000000000` | `7b14ae47e17a643f` |
| [57,65) | derived bounds | `0000000000000000` | `7b14ae47e17a643f` |
| [93,109) | opaque metadata | `fb64a724641e0b4da4414fdae7121a4a` | `a60abed6cacc1845a81e997f43c976ce` |
| [192,200) | derived bounds | `0000000000000000` | `7b14ae47e17a643f` |
| [216,224) | derived bounds | `0000000000000000` | `7b14ae47e17a643f` |
| [252,268) | opaque metadata | `f8b2b69a9e6f3e4aad4844942e252665` | `adf5a81bdb2d4d4892f7a27ea72c5df6` |
| [352,360) | derived bounds | `0000000000000000` | `7b14ae47e17a643f` |
| [376,384) | derived bounds | `0000000000000000` | `7b14ae47e17a643f` |
| [412,428) | opaque metadata | `1e639f2be8030540b3b49992789c2063` | `8f2a88de1da5f3499e189bccf94c77a4` |
| [498,506) | primary endpoint | `0000000000000000` | `7b14ae47e17a643f` |
| [534,542) | primary endpoint | `0000000000000000` | `7b14ae47e17a643f` |

## Geometry, event and lineage interpretation

The combined opaque metadata, specifically CCourbe and CContour windows, is NOT a pure function of final geometry: same C and byte-identical endpoints/bounds have different windows after edit/restore. This does not rule out dependence on geometry plus history or on other unobserved state.

The JSON tests repeated start/end/bounds, length, direction and translation-invariant displacement only for equal-feature/different-bytes counterexamples. No checksum search, hash fitting or arbitrary formula was attempted. Equal geometry in C/D also refutes geometry-only explanations for CZone and record1 high bytes. Record0 high bytes are stable in C/D but differ across older contexts; that does not establish lineage tracking. Stable tags under B coordinate edits do not prove arbitrary-mutation safety.

TypeEdit accepts and preserves existing self-consistent opaque state in exact replay and duplicate R2; stale opaque state after coordinate mutation was never tested.

Same length/orientation with differing metadata (including baseline vs Z translation) precludes a simple length/orientation-only explanation where the recorded counterexample applies. Edit history, object context and operation type are not independently randomized. Byte-level functions for event or lineage cannot be derived.

## Decision table

| Region | Role | Geometry dependent? | Edit-history dependent? | Lineage dependent? | Replay-preserved? | Safe to preserve during coordinate mutation? |
| --- | --- | --- | --- | --- | --- | --- |
| record xyz | ordered primary endpoints | yes, resolved mapping | values return on restore | not needed for coordinate mapping | yes | must update; field mapping resolved |
| three bounds | derived min/max blocks | yes, accepted observed formula | return on restore | not needed for formula | yes | must update; complete writable contract candidate_only |
| CZone opaque | unknown, distinct profile | not pure final-geometry function across C/D; B Z association only | not observed in C restore; B Z/history confounded | candidate: C/D differ | yes | unresolved |
| CCourbe opaque | unknown edit/lineage-variable candidate | not pure final geometry (same-C counterexample) | candidate: M00_ER differs | candidate: C/D differ | yes | unresolved |
| CContour opaque | unknown edit/lineage-variable candidate | not pure final geometry (same-C counterexample) | candidate: M00_ER differs | candidate: C/D differ | yes | unresolved |
| record0 tag | low 0D; upper uninterpreted | no B edit variation; cross-context variation not a geometry rule | not observed for B/ER | C/D same; earlier cross-object differences confounded | yes | low candidate_only; upper unresolved |
| record1 tag | low 0D; upper uninterpreted | no B edit variation; same geometry C/D differs | not observed for B/ER | candidate: C/D high bytes differ | yes | low candidate_only; upper unresolved |
| property/tail | opaque stable retained region | variation not observed | variation not observed | variation not observed | yes | candidate_only; extent/semantics unresolved |
| Version | 32-byte uninterpreted format | variation not observed | variation not observed | variation not observed | yes | candidate_only; no regenerated version |
| other unchanged bytes | prefix/descriptors/w/unknown metadata | not established | not established | not established | yes | candidate_only for fixed framing/w; unknown metadata unresolved |

## Hypothetical patch allowlist

Exactly 192 bytes: six 8-byte xyz scalars and eighteen 8-byte bounds scalars. This is a field-location list, not implemented writes or complete mutation authorization. Endpoint mappings remain resolved; bounds ordering/formula observations are accepted, while bounds write authorization and derived completeness remain candidate-only.

| Field | Offset | Length | Status |
| --- | ---: | ---: | --- |
| record0.x | 482 | 8 | resolved |
| record0.y | 490 | 8 | resolved |
| record0.z | 498 | 8 | resolved |
| record1.x | 518 | 8 | resolved |
| record1.y | 526 | 8 | resolved |
| record1.z | 534 | 8 | resolved |
| CZone.min_x | 17 | 8 | candidate_only |
| CZone.min_y | 25 | 8 | candidate_only |
| CZone.min_z | 33 | 8 | candidate_only |
| CZone.max_x | 41 | 8 | candidate_only |
| CZone.max_y | 49 | 8 | candidate_only |
| CZone.max_z | 57 | 8 | candidate_only |
| CCourbe.min_x | 176 | 8 | candidate_only |
| CCourbe.min_y | 184 | 8 | candidate_only |
| CCourbe.min_z | 192 | 8 | candidate_only |
| CCourbe.max_x | 200 | 8 | candidate_only |
| CCourbe.max_y | 208 | 8 | candidate_only |
| CCourbe.max_z | 216 | 8 | candidate_only |
| CContour.min_x | 336 | 8 | candidate_only |
| CContour.min_y | 344 | 8 | candidate_only |
| CContour.min_z | 352 | 8 | candidate_only |
| CContour.max_x | 360 | 8 | candidate_only |
| CContour.max_y | 368 | 8 | candidate_only |
| CContour.max_z | 376 | 8 | candidate_only |

## Complete preserve partition

The following nonoverlapping ranges cover every other TypeEditZone byte (8000 total). The CObDao marker is located inside otherwise unresolved metadata; its string is not a separate serialized descriptor. Trailing zeros are a retained-buffer observation, not an established padding/semantic extent.

| Range | Observed role | Stable in all 16? | Preserve status |
| --- | --- | --- | --- |
| [0,6) | outer prefix | True | candidate_only |
| [6,17) | class descriptors | True | candidate_only |
| [65,93) | other metadata/framing (includes unresolved CObDao context) | True | unresolved |
| [93,109) | CZone opaque | False | unresolved |
| [109,163) | other metadata/framing (includes unresolved CObDao context) | True | unresolved |
| [163,176) | class descriptors | True | candidate_only |
| [224,252) | other metadata/framing (includes unresolved CObDao context) | True | unresolved |
| [252,268) | CCourbe opaque | False | unresolved |
| [268,322) | other metadata/framing (includes unresolved CObDao context) | True | unresolved |
| [322,336) | class descriptors | True | candidate_only |
| [384,412) | other metadata/framing (includes unresolved CObDao context) | True | unresolved |
| [412,428) | CContour opaque | False | unresolved |
| [428,460) | other metadata/framing (includes unresolved CObDao context) | True | unresolved |
| [460,466) | CObDao ASCII marker; enclosing metadata extent unresolved | True | unresolved |
| [466,482) | other metadata/framing (includes unresolved CObDao context) | True | unresolved |
| [506,514) | record w | True | candidate_only |
| [514,515) | record tag low byte | True | candidate_only |
| [515,518) | record0.tag.upper | False | unresolved |
| [542,550) | record w | True | candidate_only |
| [550,551) | record tag low byte | True | candidate_only |
| [551,554) | record1.tag.upper | False | unresolved |
| [554,704) | CPropertyExtend descriptor/property/tail | True | candidate_only |
| [704,8192) | trailing zeros (within retained property/tail) | True | candidate_only |

Version is separate: [0,32), candidate_only preservation. Property/tail [554,8192) equality across all 16: True. Full Version equality: True. Both tag low bytes are 0x0D in every sample; B high-byte profiles are constant. Stability supports a candidate, not an empty-extension or mutation-safety assertion.

## Novel state and decision

No different-geometry sample has the entire non-allowlist complement equal to M00. Thus new coordinates + new bounds + old M00 state is unobserved in the stored vendor evidence (`synthetic_state_novelty = true`). This comparison uses existing byte positions only; it does not construct patched bytes.

### safe_candidate

- Resolved endpoint order/xyz and observed min/max fields identify a narrow proposed edit set.
- Exact replay and R2 preserve the complete existing M00 state; immediate exact-state coexistence observed.
- B tags/w and property/tail/Version remain stable through observed edits.

### unsafe_candidate

- A proposed different-geometry/old-M00-metadata combination is unobserved; replay has not tested stale metadata.
- Vendor edits change CCourbe/CContour even after restoration, so simply carrying them forward differs from observed edit lifecycle.
- CZone change at whole-object Z step cautions against treating every opaque window as a fixed lineage marker.

### unknown

- No demonstrated rejection of stale metadata; cannot label preservation proven unsafe/unsupported.
- No exact field meanings, references or complete Serialize extent.
- No evidence that the three bounds exhaust derived state; unknown bytes may encode dependencies.
- One tested family/session context cannot establish general version/property/tag safety.

```text
opaque_metadata_pure_function_of_geometry = no
opaque_metadata_replay_preservation = observed
synthetic_state_novelty = true
coordinate_patch_allowlist = partial
opaque_fields_preservation_for_template_mutation = unresolved
line_clipboard_synthesis_strategy = unresolved
line_clipboard_runtime_readiness = missing_specific_contract
line_record_order = creation_direction
line_endpoint_fields = resolved
line_derived_fields = partial
line_identity_fields = unresolved
```

No demonstrated rejection warrants unsupported/unsafe as an established fact; replay support is insufficient for supported. Multiple contracts remain open, so this is not a strong candidate with exactly one remaining runtime uncertainty. Full encoding has no evidence advantage while metadata meaning remains unknown.

Next task only:

Perform one bounded vendor-generated edit comparison to determine whether TypeEdit accepts stale opaque metadata after geometry changes before any synthetic mutator is built.

Recommendation only. A vendor-generated comparison alone can reveal state changes, not prove stale-state acceptance without a separately specified and authorized intervention. No such intervention is performed here.

Integrity is recorded separately against the pre-write baseline; all prior bundles/results are required unchanged. No clipboard access, TypeEdit action, new capture, Paste, payload mutation or vendor/native investigation occurred.
