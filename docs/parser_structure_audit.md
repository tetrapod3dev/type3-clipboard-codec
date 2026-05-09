# Parser Structure Audit (Type3ChainParser 중심)

## 1) 현재 문제 요약
- `src/type3_clipboard_codec/parsers/type3_chain_parser.py`는 현재 약 1256 lines로, 파싱/분류/후보 추출/신뢰도/진단 메모 구성까지 한 파일에 혼재되어 있다.
- CParagraphe field offset 분석 도구(`validate_*`, `report_*`) 간 결과 흔들림은 텍스트 역공학 난이도뿐 아니라, parser와 analyzer의 책임 경계가 느슨한 구조에서도 발생할 수 있다.
- 이번 문서는 **기능 변경이 아니라 감사와 리팩터링 설계**를 목적으로 한다.

---

## 2) `type3_chain_parser.py` Responsibility Map

| Responsibility | 관련 함수 | Rule 성격 | Offset 의존 | 도메인 |
|---|---|---|---|---|
| raw bytes scanning | `can_parse`, `_extract_nodes`, `_find_next_class_header_offset` | parser confirmed(구조 탐지) | class header scan (`0xFFFF`) | geometry+text 공통 |
| class header detection | `_parse_single_node` + `read_object_header` | parser confirmed(구조) | class-relative | 공통 |
| node boundary detection | `_parse_single_node`, `_find_next_class_header_offset` | parser confirmed(heuristic) | next header heuristic | 공통 |
| Type3Node construction | `_parse_single_node` | parser confirmed | class-relative | 공통 |
| bbox parsing | `_parse_single_node` + `read_bbox` | parser confirmed (CZone/CCourbe/CContour) | class-relative (48B bbox) | 공통 |
| contour header parsing | `_read_contour_header` | observed/provisional | payload-relative shift 후보(8/14/12/16/20) | geometry 중심 |
| contour record parsing | `_read_contour_records`, `read_contour_points` | parser confirmed(현재 규칙), 일부 provisional | fixed stride(기본 36) payload-relative | geometry |
| contour validation | `_validate_records` | parser confirmed(보수적 검증) | 좌표 값 범위 기준 | geometry |
| contour role assignment | `_assign_semantic_roles` | observed/provisional | record 값 기반 | geometry |
| shape classification | `_process_object_chain` 내부 role/count/bbox 이용 | observed/provisional | record/bbox 상대 | geometry |
| multi-object chain grouping | `_group_nodes_into_chains`, `_process_object_chain`, `_read_embedded_contour_chains` | observed/provisional | chain sequence + contour 반복 | geometry 중심 |
| CPropertyExtend style/color candidate | `_read_style_properties*`, `_collect_palette_color_candidates`, `_choose_color_candidate`, `_style_for_reference_offset`, `_localize_color_candidates` | geometry는 mostly confirmed, text는 provisional | fixed offsets(0x79/0x85/0x20E/0x21A) + payload scan | 공통(실질은 geometry 기반) |
| text object detection | `_looks_like_text_object` | observed/provisional | class marker + font marker + text record heuristic | text |
| text runs extraction | `_extract_text_runs`, `_read_paragraphe_slot_record_runs`, `_read_slot_record_runs_from_blob`, `_records_to_text_run` | observed/provisional | CParagraphe payload heuristic(47/204 관련 구조 해석) | text |
| text anchor candidate | `_attach_text_anchor_candidates` | observed/provisional | contour midpoint 기반 | text |
| font candidate | `_extract_font_candidates`, `_extract_font_name` | observed/provisional | raw scan | text |
| text color confidence downgrade | `_downgrade_unverified_text_color_selection` | parser safety guard | fixed_offset 결과 격하 | text |
| notes/confidence generation | `parse` 내부 `notes`, `candidate_fields`, text/group notes 구성 | analyzer-like 혼합 | n/a | 공통 |
| inspector 출력 보조 데이터 | `parse`의 `candidate_fields`, style/font/text notes | analyzer-like 혼합 | n/a | 공통 |

요약:
- **구조 파싱(헤더/노드/bbox/contour 추출)**은 비교적 parser 책임으로 적합.
- **text/style semantic 해석과 confidence 산정 일부**는 analyzer 책임과 혼재되어 있다.

---

## 3) Fixed/Magic Offset Audit

### A. OK - binary format structural constant
- `read_bbox`: 6 x f64 (48 bytes) (`common.py`)
- contour record 기본 stride 36 (`DEFAULT_CONTOUR_RECORD_STRIDE`, `read_contour_points`)
- class header 최소 구조 `[u16,u16,u16,name_len]`
- top-level header provisional 6 bytes (`_read_top_level_header`)

### B. OK - analyzer diagnostic only
- `tools/analyze_text_color_diff.py`: `absolute offset is diagnostic only` 명시
- `tools/compare_text_color_samples.py`: absolute + class_payload_relative 동시 출력
- `tools/analyze_cparagraphe_structure.py`, `tools/analyze_cparagraphe_records.py`, `tools/analyze_cparagraphe_field_candidates.py`, `tools/validate_cparagraphe_field_offsets.py`, `tools/report_cparagraphe_field_validation.py`: fixture pair 기반 비교/점수 산정(진단 도구 용도)

### C. Risk - parser uses unverified offset
- `type3_chain_parser.py`
  - `PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET = 0x79`
  - `PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET = 0x85`
  - `PROPERTY_EXTEND_GROUP_COLOR_PRIMARY_OFFSET = 0x20E`
  - `PROPERTY_EXTEND_GROUP_COLOR_SECONDARY_OFFSET = 0x21A`
- 현재는 text에 대해 `fixed_offset_text_unverified`로 강등 처리하고 있으나, parser 내부에서 fixed offset 기반 색상 선택 로직이 geometry/text 공통 경로에 남아 있어 구조적 분리가 필요.

### D. Risk - mixed responsibility
- `type3_chain_parser.py`의 `parse`에서:
  - text/group notes 생성
  - candidate_fields 조립
  - color confidence/source 재가공
  - text anchor parse method/confidence 셋업
- 위 항목은 parser 결과 모델을 넘어서 analyzer/report 계층과 섞여 있음.

### E. Must remove later
- parser 내 fixture filename 분기: **현재 미발견**.
- absolute file offset 기반 parser rule: **text color 쪽에서 직접 absolute offset rule은 미사용**, 그러나 fixed payload offsets를 text semantics에 직접 재사용하는 경로는 추후 분리 필요.

추가 주의:
- `tools/text_fixture_inventory.py`는 fixture 이름 기반 intent 분기를 다수 사용한다. 이는 **inventory/analyzer 용도라서 허용**되지만 parser로 유입되면 안 된다.

---

## 4) Geometry Parser Structural Soundness Audit

대상 fixture군:
- `default_rectangle`, `default_circle`, `default_circular_arc`, `default_rounded_rectangle`
- `two_rectangle`, `two_rectangle_group`, `two_circle`
- `turquoise_rectangle_and_army_green_rectangle`
- `color_*_rectangle`
- `two_rectangle_group_army_green`, `two_rectangle_group_navy_blue`

| Feature | 관찰 | Status |
|---|---|---|
| CZone/CCourbe/CContour/CPropertyExtend chain detection | class header scan 기반 추출 동작 | `structurally_sound` |
| node payload boundary | next class header 탐지 기반 분할 | `mostly_sound_with_risk` (header-like false positive 가능성) |
| bbox parsing | class-relative bbox decode(48B) | `structurally_sound` |
| contour header parsing | `CObDao` + shift 후보 heuristic | `mostly_sound_with_risk` |
| contour record parsing | payload-relative + stride 기반 | `structurally_sound` (현재 fixture 범위) |
| shape classification | contour count / roles / bbox 조합 | `mostly_sound_with_risk` |
| color parsing(geometry) | CPropertyExtend payload-relative fixed 후보 + palette scan | `mostly_sound_with_risk` |
| multi-object grouping | chain sequence + multi contour 분할 | `mostly_sound_with_risk` |
| absolute offset parser rule | geometry 경로에서 파일 absolute offset 직접 rule은 미사용 | `structurally_sound` |

geometry 요약:
- 기본 도형 파싱은 구조 기반으로 잘 동작한다.
- 취약점은 contour header shift heuristic, group/multi-object 분해 heuristic, color fixed offset 일반화 가능성이다.

---

## 5) Parser vs Analyzer 경계 정책 (권고)

### Parser가 해도 되는 것
- class header detection / node boundary / bbox decode
- CContour record extraction
- CPropertyExtend / CParagraphe payload 보존
- object chain 구성
- candidate 필드 노출(낮은 confidence 명시)

### Analyzer가 해야 하는 것
- fixture pair diff
- expected-value scoring
- absolute offset 출력
- field offset 후보 탐색/랭킹
- byte-order 실험
- confidence 실험/비교 리포트

### Parser가 하면 안 되는 것
- fixture filename 기반 분기
- absolute offset rule
- 미확정 text decode를 confirmed처럼 출력
- analyzer evidence를 semantic field로 승격

---

## 6) 제안 모듈 구조 (계획)

```text
src/type3_clipboard_codec/parsers/
  type3_chain_parser.py            # thin orchestrator
  binary/header_parser.py
  binary/node_scanner.py
  binary/node_parser.py
  binary/bbox_parser.py
  geometry/contour_parser.py
  geometry/shape_classifier.py
  geometry/geometry_chain_builder.py
  style/property_extend_parser.py
  style/color_candidate_parser.py
  text/cparagraphe_parser.py
  text/text_candidate_parser.py
  text/text_anchor_parser.py
  diagnostics/evidence.py
  diagnostics/confidence.py
```

이번 단계에서는 **파일 이동/대규모 리팩터링 미수행**.

---

## 7) 안전한 리팩터링 순서 (Roadmap)

### Step 1. Behavior snapshot 테스트 추가
- 목적: 리팩터링 전후 외부 동작 고정
- 변경: `tests/integration/*snapshot*` 신규
- 위험도: 낮음
- 테스트: fixture별 public output 비교
- 성공 기준: 기존 + snapshot 모두 pass

### Step 2. 공통 binary parser 분리
- 목적: header/bbox read 중복 제거
- 변경: `binary/header_parser.py`, `binary/bbox_parser.py`
- 위험도: 중간
- 테스트: geometry/text 기본 fixture smoke
- 성공 기준: marker/bbox/chain 동일

### Step 3. node scanning/boundary 분리
- 목적: `_extract_nodes`, `_find_next_class_header_offset` 분리
- 위험도: 중간
- 테스트: multi-object/group fixture
- 성공 기준: node offsets/count 동일

### Step 4. contour parser 분리
- 목적: contour header/record/validate 모듈화
- 위험도: 중간~높음
- 테스트: rectangle/circle/arc/rounded/group
- 성공 기준: contour count/shape 유지

### Step 5. geometry classifier 분리
- 목적: type inference/role assignment 분리
- 위험도: 중간
- 테스트: 도형 분류 테스트
- 성공 기준: type 결과 유지

### Step 6. CPropertyExtend/color candidate 분리
- 목적: geometry용/diagnostic용 경계 명확화
- 위험도: 중간
- 테스트: rectangle color fixtures
- 성공 기준: rectangle color 회귀 없음

### Step 7. text/CParagraphe analyzer-level 로직 분리
- 목적: parser는 후보 추출/보존만, scoring은 tool로 이동
- 위험도: 높음
- 테스트: text parsing + analyzer CLI 테스트
- 성공 기준: parser confirmed 증가 없음, 후보/notes 보존

### Step 8. Type3ChainParser orchestrator 축소
- 목적: 1000+ 라인 파일 슬림화
- 위험도: 중간
- 테스트: 전체 회귀
- 성공 기준: parse output shape 동일

### Step 9. inspector/formatter model-only 정리
- 목적: formatter에서 파싱 로직 재실행 금지
- 위험도: 낮음
- 테스트: inspect CLI golden output
- 성공 기준: 출력 semantics 유지

### Step 10. 전체 회귀
- 목적: behavior stability 확인
- 테스트: `pytest -q`, 주요 inspect CLI
- 성공 기준: 전 통과

---

## 8) 리팩터링 전 Snapshot Test 제안

public output 기준으로만 검증(내부 함수/구현 세부 미검증):

- Geometry
  - `default_rectangle`
  - `default_circle`
  - `default_circular_arc`
  - `default_rounded_rectangle`
  - `two_rectangle`
  - `two_rectangle_group`
  - `color_*_rectangle`
- Text
  - `text/default_text`
  - `text/text_group_same_color_two_objects`
  - `text/text_multiline_basic`

검증 항목:
- object count / chain count
- class chain(marker order)
- bbox
- contour record count
- object type
- color candidate confidence/source
- text candidate
- text anchor + parse method/confidence
- provisional note 존재 여부

---

## 9) Do-Not-Do Rules
- parser에 fixture 파일명 기반 분기 금지
- parser에 absolute file offset rule 금지
- text color/font/style confirmed 승격 금지(현 단계)
- analyzer score를 parser truth로 승격 금지
- geometry 회귀를 유발하는 무검증 리팩터링 금지

---

## 10) 이번 감사 결론
- geometry core parsing은 대체로 구조 기반이며 `mostly sound`.
- 가장 큰 구조 위험은 `type3_chain_parser.py`의 **책임 과밀 + parser/analyzer 혼재**.
- text field decode는 아직 evidence 단계이며, parser 승격 전에 모듈 경계 정리와 snapshot 고정이 선행되어야 한다.
