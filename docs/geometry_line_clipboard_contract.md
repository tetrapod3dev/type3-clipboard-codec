# Single-line TypeEditZone clipboard contract — corpus gate

Date: 2026-09-15  
Repository: C:\work\develop\type3-clipboard-codec  
Scope: existing corpus inventory and read-only structural observations. No new capture, synthesis, clipboard write, paste, or document mutation.

## 1. Decision

**현재 corpus만으로 단일 직선 payload의 안전한 synthesis 계약을 닫을 수 없다.**
기존 2점 geometry 후보는 있지만, 통제된 endpoint 차분 및 identity 대조군과 원본 two-format bundle이 없다. 따라서 구조 후보와 필요한 최소 capture plan을 기록하고 정지한다.

```text
text_slot_milestone_status = stable_pause_point
line_object_structure = partial
line_endpoint_fields = candidate_only
line_derived_fields = partial
line_identity_fields = unresolved
line_clipboard_synthesis_strategy = unresolved
line_clipboard_runtime_readiness = needs_controlled_line_corpus
```

Synthetic candidate는 생성하지 않았다. 쓰기 허용 field 목록은 현재 빈 목록이다.
Template mutation은 향후 선호 방향일 뿐, 현재 사용 가능한 전략으로 승인하지 않는다.

Machine-readable evidence:

- [Corpus and structural evidence](../research/geometry-line/evidence.json)
- [Minimum controlled capture plan](../research/geometry-line/capture_plan.json)
- [Integrity verification](../research/geometry-line/integrity.json)

## 2. Corpus inventory

기존 working tree는 시작 시 clean이었다. 신규 기록의 기준 commit은
`ce3e7f2ce35996810a8316c2cea3162d406cf64a`이다.

| 기존 자료 | 이번 확인 | 이 task에 대한 적격성 |
| --- | --- | --- |
| tests/samples 바로 아래 geometry hex fixture | 32개; 모두 decoded 8192 bytes | 기존 parser/corpus evidence. 통제된 line differential set 아님 |
| polyline_2_points.txt | one chain, 2 records, polyline_candidate / provisional | 유일한 2점 후보. Endpoint mapping 연구 출발점만 가능 |
| polyline_3/5_points 및 polygon/rectangle/arc/circle | 다른 geometry와 반복/세션 자료 있음 | container 대조군 또는 다른 geometry 연구. line 대조군으로 대체 금지 |
| geometry raw bundles/intents/reports | 해당 category directory 없음 | 원본 TypeEditZone + TypeEditZoneVersion pair 없음 |
| text raw bundles | 존재 | text 계약 보존. line version/provenance 대용으로 쓰지 않음 |
| dumps/typeeditzone_a.bin, b.bin | 8192 bytes, 서로 byte-identical; parser상 12-record rounded_rectangle | line 아님. 동일 객체 “다시 Copy” 증거도 아님 |
| dumps/typeeditzone_version_a.bin, b.bin | 각각 32 bytes, 서로 byte-identical | 기존 raw-I/O 자료. legacy line과 짝을 임의로 만들지 않음 |
| controlled empty sample | 이번 inventory에서 적격 자료 미발견 | empty payload를 만들어 대체하지 않음 |

32개 전체 파일의 source SHA256, decoded payload SHA256/size, parser 관측 및 bundle 부재는 evidence.json에 보존했다. 파일명과 parser confidence는 capture ground truth가 아니다. 다른 geometry의 count/shape 분류를 변경하지 않았다.

### Existing two-point candidate provenance

[Fixture README](../tests/samples/README.md)는 `polyline_2_points.txt`를 열린 2점 폴리선으로 기록하고, intent bbox를 x=11.111..88.888 mm, y=22.222..22.222 mm로 명시한다.
[Geometry fixture plan](geometry_fixture_plan.md)은 status bar `곡선 객체`, draw tool not recorded로 기록한다.

- Source hex file SHA256:
  `e537224a9d3799cc580591369dfca021df78d6e31ea5df27b662c27dfa67cead`
- Decoded 8192-byte payload SHA256:
  `ed6ae9039dc40ffae691c6829d58fc3840e17faff472dcaa748174da1eea469e`
- Original raw companion: absent.
- TypeEditZoneVersion companion: absent.
- Actual UI start/end order, exact creation tool, session/document state, z input: not established by this fixture.
- Same-object recopy / independently created identical line pair: absent.

먼저 기존 source 파일을 읽어 hash를 기록한 뒤 메모리에서 hex decode했다. 원본을 수정하거나 normalization 결과로 덮어쓰지 않았다. Legacy hex를 이번에 새로 캡처한 원본 raw라고 표시하지 않았고, 빠진 version bytes도 발명하지 않았다.

## 3. Primary questions

| 질문 | 현재 답 |
| --- | --- |
| 1. Line을 나타내는 class? | 후보의 실제 ASCII descriptors는 CZone, CCourbe, CContour, CPropertyExtend. “CLine” class를 가정하지 않음. CCourbe/CContour의 2점 표현 후보 |
| 2. 주변 records? | 6-byte outer prefix, 위 descriptors, 세 번의 OBJETINFOS_CLASSNAME/CObDao 문자열, opaque metadata/property 영역 |
| 3. x0/y0/x1/y1/z? | 구조상 선택된 두 36-byte record의 +0/+8/+16 f64 후보. Record 0/1과 UI 시작/끝 대응은 아직 candidate |
| 4. Doubles인가? | 관측된 좌표·bounds 위치에서는 little-endian binary64 해석이 강한 후보. controlled field mapping까지 resolved 아님 |
| 5. Bounds 중복? | CZone/CCourbe/CContour descriptor 직후 각각 6 doubles가 byte-identical. geometry와 일치하는 min/max 후보 |
| 6. GUID/identity serialized? | unresolved. CObjGuid/GUID 문자열 부재가 binary identity 부재를 뜻하지 않음 |
| 7. Layer/parent serialized? | unresolved. CCalque 문자열 부재가 live parent/reference 부재를 뜻하지 않음 |
| 8. Detached clipboard zone? | CZone descriptor 존재는 확인. detachedness·ownership·portable parent semantics는 미확정 |
| 9. Recompute 대상? | endpoint records 및 적어도 세 bounds가 후보. cached length, flags, 기타 중복 값의 완전 목록은 미해결 |
| 10. Undocumented 값을 발명하지 않고 합성 가능한가? | No. identity, record extent, extension, derived-field completeness가 남음 |

## 4. First structural pass

기존 analyzer의 descriptor 관측을 재사용했다:

```text
FFFF : schema_u16_le : ASCII_name_length_u16_le : exact ASCII name
```

이 fingerprint 일치가 전체 MFC archive와 object identity를 닫는 것은 아니다. 기존
[MFC archive investigation](typeeditzone_mfc_archive_investigation.md)의 한계를 유지했다.
Native vendor binaries나 외부 자료는 새로 분석하지 않았다.

| 실제 name | Schema 후보 | Name length | 이번 line candidate에서 확인 |
| --- | ---: | ---: | --- |
| CZone | 1 | 5 | ff ff 01 00 05 00 + CZone |
| CCourbe | 1 | 7 | ff ff 01 00 07 00 + CCourbe |
| CContour | 2 | 8 | ff ff 02 00 08 00 + CContour |
| CPropertyExtend | 5 | 15 | ff ff 05 00 0f 00 + CPropertyExtend |
| CObDao | not established | 문자열 6 bytes | 위 descriptor가 아님; 앞 06 00 00 00와 OBJETINFOS_CLASSNAME 문맥 |
| CCalque / CObjGuid / CVect* | not observed | — | 명시적 해당 이름 hit 없음; 무명 fields의 부재 증명 아님 |

Container-only 대조:

- default_rectangle, default_circle, polyline_3_points: 같은 4개 exact descriptors/schema 관측.
- text/default_text: 공통 descriptors에 CParagraphe schema 6가 추가됨.
- Text 내용·문자 폭·text slot semantics는 조사/승격하지 않았다.
- 공통 descriptor만으로 hierarchy/parent identity/line object subtype을 확정하지 않았다.

Archive analyzer는 전체 stream 시작 가정에서 prefix 뒤 reference 해석에 실패하고, 첫 CZone descriptor부터 시작한 별도 가정에서도 Serialize body extent에서 멈춘다. 동기화된 PID 진행은 unresolved다. Archive-local reference 후보를 object GUID로 이름 붙이지 않는다.

## 5. Boundaries and offset origins

**아래 절대 위치는 fixture 검토용이다. Patcher contract가 아니다.**

현 parser는 clipboard 앞 6 bytes를 제거한 stream을 node/source offset 기준으로 사용한다. 이 fixture의 scan origin은 clipboard +6이다. 따라서 parser의 source_stream_offset=476은 clipboard +482에 해당한다. 이 둘을 혼용하면 다른 bytes를 건드리게 된다.

| 관측 영역 | Clipboard absolute, diagnostic only | 범위 해석 |
| --- | ---: | --- |
| Outer prefix | [0,6) | 00 00 00 00 01 00; parser는 reserved 4 bytes + count u16=1로 해석. 형식 전체 검증은 provisional |
| CZone descriptor | 6 | descriptor 길이 11; 뒤 bounds 48 bytes 후보 |
| CCourbe descriptor | 163 | descriptor 길이 13; 뒤 bounds 48 bytes 후보 |
| CContour descriptor | 322 | descriptor 길이 14; 뒤 bounds 48 bytes 후보 |
| Candidate kind/count | 474 / 478 | 00000000 / 02000000, structural ranking이 선택 |
| Candidate record region | [482,554) | 36-byte record 2개 |
| CPropertyExtend descriptor | 554 | descriptor 길이 21; 뒤 opaque property/tail |
| Raw payload 끝 | 8192 | backing buffer size 관측; semantic object 종료/길이 규칙 아님 |

Scanner의 “다음 plausible class header까지” slice는 객체 Serialize의 닫힌 종료 경계가 아니다. CZone/CCourbe/CContour의 nested ownership, properties의 유효 길이, trailing bytes의 의미는 별도 미해결이다. 한 descriptor occurrence를 한 객체와 항상 등치하지 않는다.

CContour descriptor 시작을 H, 선택된 record 시작을 R이라고 부르면 이 fixture에서:

```text
H + 14: 6 × f64 bounds candidate
H + 62: opaque metadata starts
H + 138: ASCII CObDao in OBJETINFOS_CLASSNAME context
H + 152: u32 kind candidate = 0
H + 156: u32 point-count candidate = 2
R = H + 160
R + 0: first 36-byte record
R + 36: second 36-byte record
R + 72: next exact CPropertyExtend descriptor
```

이 관계는 단일 fixture의 관측이다. “CObDao를 아무 곳에서 검색하고 +22에 patch” 같은 규칙은 승인하지 않는다. Contour count=1도 parser가 추출한 한 region이라는 관측이며, 별도의 authoritative serialized contour-count field는 아직 닫히지 않았다.

## 6. Endpoint encoding candidates

기존 structural selection은 CContour 안 CObDao 문맥에서 kind/count 후보를 고르고, record count·36-byte stride·bounds 일관성을 확인한다. 임의의 float coincidence만 찾아 endpoint로 승격하지 않았다.

| Record-relative field | Size | Record 0 decode | Record 1 decode | 상태 |
| --- | ---: | ---: | ---: | --- |
| +0 | 8 | 0.011111000000000003 | 0.08888800000000001 | x candidate |
| +8 | 8 | 0.022222000000000006 | 0.022222000000000006 | y candidate |
| +16 | 8 | 0 | 0 | z candidate; zero만으로 의미 증명 불가 |
| +24 | 8 | 1 | 1 | w candidate; 정확한 의미 미해결 |
| +32 | 4 | 0x4146500D | 0x4E45400D | tag candidate; high bytes 및 lifecycle 미해결 |

x/y에 1000을 곱하면 문서의 mm intent와 일치한다. 기존 parser는 이를 meter로 이름 붙인다. 여기서는 이 fixture에 부합하는 scale 후보로 기록하며, 모든 document units/workplane의 보편 변환으로 확정하지 않는다.

같은 record 위치를 f32로 읽으면 x/y가 약 7.38e-12이고, int32로 읽으면 755089612 또는 755089611이다. 이 직접 해석은 기록된 좌표를 설명하지 않는다. 하지만 한 fixture만으로 다른 위치의 float32, 다른 정수 폭/scale, serialization 규칙 전체를 배제할 수는 없다.

**Controlled differential endpoint search는 수행 불가**다. L00/L01 등의 pair가 없다. 다른 count/shape/color 샘플을 L00의 endpoint 변경본으로 취급하지 않았다. UI start/end ordering, y0/y1 독립 변동, nonzero z, integer-scaled 대안 검증은 capture gate 뒤에 남는다.

## 7. Duplicated data, metadata, identity

세 descriptor 직후의 48-byte bounds는 이 fixture에서 서로 byte-identical이며 다음처럼 해석된다:

```text
(min_x, min_y, min_z, max_x, max_y, max_z)
≈ (0.011111, 0.022222, 0, 0.088888, 0.022222, 0)
```

CZone는 descriptor+11, CCourbe는 +13, CContour는 +14가 관측된 시작이다. Endpoint 후보의 min/max와 일치하지만, 변화에 따른 쓰기 책임·rounding·recompute 규칙·더 많은 cache의 부재는 증명되지 않았다.

| Region/field | 현재 evidence category | 미해결 |
| --- | --- | --- |
| 2×xyz record | primary geometry candidate | controlled endpoint mapping, scale, direction |
| 세 min/max blocks | derived geometry candidate | 모든 변형에서의 값/rounding 및 전체 중복 목록 |
| kind/count | unknown semantics / structural count candidate | kind=0의 일반 의미, contour-count field |
| record w/tag | unknown | w invariant, low/high tag 의미와 안정성 |
| outer prefix 및 OBJETINFOS metadata | unknown | counts, IDs, references, flags, lengths 구분 |
| CPropertyExtend/tail | unknown | nonempty extension boundary, property/cache/identity 포함 여부 |
| GUID/timestamp/random/object ID | 위치 자체 unresolved | identity/random으로 확정한 bytes 없음 |
| cached length/volume flags | unresolved | 위치·존재·recompute 요구 여부 |

이 표는 변경된 fields의 차분 분류 결과가 아니다. 적격 pair가 없어 차분 결과는 비어 있다. 기존 polygon/polyline 세션 자료의 tag 변화는 line identity 증거로 전용하지 않는다.

### Same-object recopy and paste identity

- 동일한 line A를 편집 없이 다시 Copy한 pair: 없음.
- 동일 geometry의 별도 line B를 새로 만든 pair: 없음.
- Anonymous dumps a/b는 rounded-rectangle parser 관측이며 같은 raw-I/O 상태일 수 있다. A의 재복사 또는 A/B identity 실험으로 주장하지 않는다.
- CObjGuid 이름이 없어도 raw GUID, object-local ID, archive reference 또는 pointer-like data가 있을 수 있다.
- **Copy된 GUID 유지 또는 paste 시 새 GUID 발급 여부는 unresolved.**

미해결 identity bytes를 보존하기만 하면 안전하다고 보지 않는다. 같은 identity를 담은 template을 재사용해도 되는지가 바로 미해결이기 때문이다. Copy-only 대조군은 bytes의 변동을 분리할 뿐 paste identity 정책을 증명하지 못한다. 이번에는 paste 검증을 권고하거나 수행하지 않는다.

## 8. Container / parent semantics

CZone descriptor는 실제 payload evidence다. 그러나 그것이 detached clipboard zone인지, generic wrapper인지, 살아 있는 layer/parent를 가리키는 reference를 포함하는지는 확인되지 않았다.

현 parser의 declared_object_count=1, structure_kind=single, is_grouped=false는 기존 휴리스틱 출력이다. 원본 UI 선택 개수와 완전한 object graph 검증을 대신하지 않는다.

CCalque 이름을 찾지 못했다는 사실은 portable detached geometry의 증명이 아니다. Native model ownership과 무관하게 clipboard 자체의 구조/identity/reference 증거로 닫아야 한다.

## 9. Synthesis strategy and fail-closed gate

### A. Template mutation

모든 필수 계약이 닫힌 뒤에는 known-good two-format bundle을 복제하여 proven primary/derived geometry fields만 바꾸는 전략을 우선 평가한다. 현재 legacy fixture는 version pair, identity, opaque extension 및 derived-field completeness가 부족하므로 승인된 template이 아니다.

### B. Full encoding

Object Serialize 전체 extent, reference/PID state, metadata, version와 identity 생성 규칙이 미해결이다. From-scratch encoder는 정당화되지 않는다.

### Required gate specification — not an implemented mutator

| Gate | 반드시 요구할 조건 | 현재 verdict |
| --- | --- | --- |
| Capture provenance | 인간이 확인한 정확히 한 simple line, 실제 units/좌표/방향/상태 | reject: legacy provenance 부족 |
| Two-format raw pair | 같은 controlled Copy에서 보존한 두 원본 bytes, size/SHA256 일치 | reject: line version/raw pair 없음 |
| Class/schema | 닫힌 family의 descriptor/name/schema 및 nesting; 불일치 즉시 reject | partial, complete extent 미해결 |
| Counts | serialized object count=1, contour count=1, point count=2를 authoritative 구조에서 검증 | reject: contour count/전체 graph 미해결 |
| Geometry | 검증된 typed positions, 유한 값, 방향/단위/z/degenerate 정책 | reject: differential mapping 미해결 |
| Derived data | 필요한 모든 bounds/cache 위치와 계산/rounding 규칙 | reject: completeness 미해결 |
| Extension | length-delimited known empty 또는 해석이 닫힌 extension만 허용 | reject: unknown nonempty/tail |
| Identity/references | copy/paste identity·parent 정책이 닫혀야 함 | reject: unresolved identity |
| Length | serialized extent와 buffer length 관계, offsets/ranges/consumption 일치 | reject: 8192만 맞아서는 부족 |
| Byte preservation | TypeEditZoneVersion 그대로; 승인된 변경 field 외 모든 bytes 동일 | 실행 전제 자체 미충족 |

Unexpected class version/object count/contour count, unknown nonempty extension, unknown derived layout, unresolved identity, payload length mismatch는 항상 abstain/reject다. “알 수 없는 bytes는 놔두고 endpoints만 patch”하는 best-effort 예외를 두지 않는다.

현재 gate의 결론은 **no candidate emitted**다. Positive minimal LineObjectRecord schema는 아직 제시하지 않는다. 위 relative layout은 관측 표이며 public encoding contract가 아니다.

## 10. Smallest required controlled capture set

**다음 작업은 아래 8개 two-format bundle의 human-gated capture뿐이다.** 지금 캡처를 실행하지 않았다.

좌표는 conceptual labels이다. 실제 document/UI unit에 맞게 사람이 입력한 정확한 값과 표시 정밀도를 따로 기록해야 한다. 0/10/20을 payload value라고 가정하지 않는다.

| ID | P0 | P1 | 기준선 대비 변화 / object lineage |
| --- | --- | --- | --- |
| L00 | (0,0,0) | (10,0,0) | 새 simple line A, baseline |
| L00_R | (0,0,0) | (10,0,0) | **같은 A**를 편집·undo·save·paste 없이 다시 Copy |
| L00_N | (0,0,0) | (10,0,0) | 동일 tool로 **별도 새 line B** 생성; clone/paste 금지; A 보존, B만 선택 |
| L01 | (0,0,0) | (20,0,0) | A의 x1만 변경 |
| L02 | (0,0,0) | (10,10,0) | A의 y1만 변경 |
| L04 | (-10,0,0) | (10,0,0) | A의 x0만 변경; negative test |
| LY0 | (0,-5.25,0) | (10,0,0) | A의 y0만 변경; fractional test |
| LZ | (0,0,2.5) | (10,0,2.5) | A의 공통 z만 변경 |

Baseline + 다섯 독립 coordinate 변수 + 두 identity 대조가 최소 8 captures다. Preferred L03은 x0/x1을 같이 평행이동하므로 이 초기 독립변수 set에서는 중복되어 제외했다.

각 변형은 직전 변형이 아니라 **L00의 실제 값**을 기준으로 해야 한다. 기존 A를 supported UI로 baseline으로 복원한 후 named variable만 바꾸고 복원 과정도 기록한다. A를 delete/redraw/clone하면 same-object geometry diff가 아니므로 해당 사실을 표시하고 적격성 판정을 보류한다.

동일 document/session/workplane/layer/color/style/width/tool을 유지하고, 매 Copy에는 정확히 한 geometry object만 선택한다. 텍스트나 group/다른 선택물을 섞지 않는다. 별도 생성 B와 A의 선택 구분을 명시한다. 실제 UI가 공통 nonzero z를 안전하게 설정/확인하지 못하면 LZ를 만들어낸 것처럼 표시하지 말고 unavailable로 기록한다. 그 경우 arbitrary-z 계약은 unresolved로 남는다.

### Human-gated capture procedure

1. 별도 승인된 capture stage에서 사람이 geometry, 실제 입력 endpoints/units, source tool, selected object count=1을 확인하고 수동 Copy한다. Agent가 TypeEdit을 시작하거나 geometry를 만들지 않는다.
2. 사람이 “sample ID의 Copy 준비 완료”를 확인한 뒤, 기존 capture CLI의 **읽기/capture 경로만** 실행한다. 다른 clipboard writer/새 Copy는 capture+검증 종료까지 중단한다.
3. `--category geometry --object-count 1 --grouping not_grouped --no-inspect`를 사용한다. 기존 capture CLI는 기본값에서 inspect를 파일 저장보다 먼저 수행하므로, **raw 보존 이전 decoding을 피하려면 --no-inspect가 필수**다.
4. 결과 `typeeditzone.bin`, `typeeditzone_version.bin`, manifest, hex fixture, intent를 새 고유 sample name으로 저장한다. overwrite/git-add/load/paste 옵션은 사용하지 않는다.
5. 두 raw 파일의 size와 SHA256을 먼저 companion metadata에 기록한다. 현 capture manifest는 size/format ID를 담지만 SHA256은 자동 포함하지 않는다. 원본 bytes의 trailing zeros/version bytes를 그대로 보존한다.
6. Existing `clipboard_typeeditzone.py verify-bundle --dir <bundle>`는 읽기 비교다. 동일한 clipboard 상태에서 두 bytes의 exact equality를 확인한다. Capture/verify는 각 format을 별도로 읽으므로 atomic pair snapshot 보장은 없다. 중간 writer/Copy 또는 비교 mismatch가 있으면 해당 bundle을 분석 corpus에서 제외한다.
7. 저장·hash·검증 이후에만 파일 기반 parser/diff를 실행한다. Inspector 출력은 human ground truth와 분리한다.
8. clipboard format ID는 시스템별 관측값이다. 고정 numeric ID가 아니라 format names와 실제 등록 ID를 기록한다.

도구 예시는 미래 capture stage 설명이며 이번에는 실행하지 않았다:

```text
<PyCharm configured Python> tools/capture_type3_sample.py
  --name geometry_line_L00
  --category geometry
  --object-count 1
  --grouping not_grouped
  --description "<human-confirmed geometry, units and object A>"
  --anchors "<actual P0>;<actual P1>"
  --no-inspect

<PyCharm configured Python> tools/clipboard_typeeditzone.py
  verify-bundle --dir tests/samples/bundles/geometry/geometry_line_L00
```

줄바꿈은 인자 설명용이며 shell script가 아니다. 각 실행 전에 Python environment를 다시 확인한다. 이번 read-only 분석에 IDE가 반환한 Python은 typeedit-automation/.venv의 3.14.7이었으며, repository 이름으로 interpreter를 추정하거나 새로 설치하지 않았다.

### Required per-sample metadata

- sample ID, capture timestamp, session/document 식별, 인간 확인 geometry 및 실제 start/end 방향;
- 실제 entered coordinates, UI display precision, unit, origin/workplane, common z;
- object lineage A/B, Copy 순번, 이전 편집/복원, selected/copied object count=1;
- layer/color/line-style/width/tool 등 fixed state, not_grouped 여부;
- 두 format name/실제 ID/size/SHA256, raw preservation 및 verify result;
- 원본 raw/hex/intent 경로, clipboard interference 여부;
- unknown 항목은 unknown으로 기록. Parser가 추정한 값을 UI actual로 옮겨 적지 않음.

### Analysis after capture — still no paste

구조를 먼저 정렬한 후 각 field가 변해야 할 pair와 고정되어야 할 pair를 모두 검증한다. Endpoint별 binary64/binary32/scaled integer 후보를 같은 typed region에서 비교하고, 세 bounds와 추가 changes를 primary/derived/identity-or-random/unknown으로 분리한다. 동일 A 재복사와 별도 B 비교에서 변한 bytes도 바로 GUID라고 부르지 않는다.

이 8개 set은 다음 static differential에 필요한 최소 입력이다. Unknown fields나 paste identity 계약까지 자동으로 닫힌다는 보장은 아니다. Identity가 남으면 runtime readiness는 계속 blocked이며 이번 capture plan에 paste를 추가하지 않는다.

## 11. Validation and stop

기존 코드·text contract·fixtures를 변경하지 않았다. 기존 parser와 analyzer를 read-only로 재사용했고, geometry inventory 32개와 container-only control 4개를 확인했다. 별도 code test를 추가하지 않았다. Parser outputs의 provisional semantics를 그대로 보존했다.

새 파일을 쓰기 전후 tracked files 437개의 SHA256을 비교하고 결과를 integrity.json에 기록한다. 기존 geometry fixture들의 source hash와 raw dumps hash는 evidence.json에도 있다. 원본 vendor tree는 읽지도 수정하지도 않았다.

No clipboard API invocation; no TypeEdit launch; no Ctrl+V/paste command; no synthetic bytes emitted; no document mutation; no vendor analysis; no managed/native bridge/shim work; no text character-width investigation.

## 12. Exactly one next task

**Capture exactly eight human-gated two-format bundles: L00, same-object L00_R, independently created L00_N, L01 (x1 only), L02 (y1 only), L04 (x0 only), LY0 (y0 only), and LZ (common z only); preserve both raw formats and metadata; do not paste.**

