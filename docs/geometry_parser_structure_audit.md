# Geometry Parser Structure Audit

본 문서는 `Type3ChainParser`의 geometry parsing 경로가 구조 기반인지 점검한 감사 결과다.  
신규 fixture 확보 계획은 `docs/geometry_fixture_plan.md`를 참고한다.
contour candidate 선택 로직 전환 설계는 `docs/contour_candidate_selection_rfc.md`를 참고한다.

범위:
- `src/type3_clipboard_codec/parsers/type3_chain_parser.py`
- `src/type3_clipboard_codec/parsers/binary/*`
- `src/type3_clipboard_codec/parsers/geometry/*`
- `src/type3_clipboard_codec/parsers/style/property_extend_parser.py`
- `src/type3_clipboard_codec/parsers/common.py`
- geometry integration tests

분류 기준:
- **Confirmed**: 코드상 구조 규칙이 명시적이고 fixture 범위에서 일관 검증됨
- **Observed**: 관찰 기반으로 동작하나 구조 규칙으로 단정하기 어려움
- **Provisional**: 휴리스틱/추정이며 확정 승격 금지

## A. Geometry Parser Responsibility Map

| 영역 | 주요 함수/모듈 | 판정 | 비고 |
|---|---|---|---|
| top-level header | `Type3ChainParser._read_top_level_header` | Observed | `[4B reserved][u16 count]`, `count<=1000` 휴리스틱 포함 |
| class header scan | `binary/header_parser.py:is_plausible_class_header_at` | Confirmed | marker/name_len/class_name 기반 class-relative 탐지 |
| node scan / boundary | `binary/node_scanner.py:extract_nodes`, `binary/node_parser.py:parse_single_node` | Confirmed + Observed | 다음 plausible header까지 payload 절단(구조적), false positive 가능성은 Observed risk |
| bbox decode | `common.py:read_bbox` + `_BBOX_CLASS_NAMES` | Confirmed | class header 직후 `6*f64(48B)` class-relative |
| contour header 탐지 | `geometry/contour_parser.py:read_contour_header` | Provisional | `CObDao` marker + shift 후보(8/14/12/16/20) |
| contour record decode | `read_contour_records` + `read_contour_points` | Confirmed(현재 스키마) | stride=36 기반 payload-relative 레코드 파싱 |
| contour validate | `validate_records` | Confirmed | finite/range/bbox overlap 보수 검증 |
| role assignment | `assign_semantic_roles` | Observed | tag low-byte 매핑(0x0C/0x0D/0x0F) |
| shape classification | `shape_classifier.py:classify_shape_type` | Observed | bbox+record pattern 기반 의미 분류, parser 구조와 분리됨 |
| chain grouping | `chain_builder.py:group_nodes_into_chains` | Observed | class sequence 기반 분할 규칙 |
| embedded contour chain | `_read_embedded_contour_chains` | Provisional | `CPropertyExtend` 내부 contour 존재 가정 |
| group detection | `is_group_candidate` branch | Provisional | `declared_count==1 && chain>1` 휴리스틱 |
| style/color parse | `style/property_extend_parser.py` | Geometry: Observed strong / Text: Provisional | payload-relative fixed offsets + palette scan 조합 |

## B. Geometry Fixed-Offset / Magic-Number Audit Table

| 상수/규칙 | 위치 | 종류 | 판정 | 설명 |
|---|---|---|---|---|
| `0xFFFF` | class header marker | 구조 시그니처 | Confirmed | absolute file offset 의존 아님, scan 기반 |
| `name_len < 64`, printable ASCII, startswith `"C"` | `is_plausible_class_header_at` | header plausibility | Observed | 오탐 방지 휴리스틱 |
| header 최소 6B | binary/common | 구조 상수 | Confirmed | `[u16,u16,u16]` |
| bbox 48B (`6*f64`) | `read_bbox` | 구조 상수 | Confirmed | class-relative decode |
| `_BBOX_CLASS_NAMES={"CZone","CCourbe","CContour"}` | `node_parser.py` | class rule | Observed | fixture군에서 성립, 클래스 확장 시 재검증 필요 |
| contour marker `b"CObDao"` | `read_contour_header` | marker heuristic | Provisional | payload 내부 탐지 |
| contour header shifts `[8,14,12,16,20]` | `read_contour_header` | heuristic | Provisional | 변형 대응용, 오검출 위험 존재 |
| plausible count `{2,3,4,8,12}` | `is_plausible_contour_count` | heuristic gate | Observed (known incomplete) | 기존 fixture 기준 whitelist였으나 count=5/6 raw evidence 등장 |
| contour stride `36` | parser/common | 레코드 구조 상수 | Confirmed(현재) | `x,y,z,w` + `tag` + trailing skip 전제 |
| 좌표 범위 `MAX_REASONABLE_COORD_M=100.0` | `Type3ChainParser` | safety bound | Observed | 안전장치(형식 규칙 아님) |
| bbox margin `0.05m` | `validate_records` | validate heuristic | Observed | bbox 교차 허용 오차 |
| color offsets `0x79/0x85` | `Type3ChainParser`/style | payload-relative fixed offset | Observed | CPropertyExtend payload 내부 규칙 |
| group color offsets `0x20E/0x21A` | `Type3ChainParser`/style | payload-relative fixed offset | Observed | group fixture 기반 |
| absolute file offset rule | 전체 geometry path | 금지 규칙 점검 | Confirmed(미사용) | stream/file 절대 오프셋 기반 decode 없음 |

## C. Reusable Foundation For Text Parsing

| 재사용 가능 계층 | 이유 | 판정 |
|---|---|---|
| class header/node scan (`binary/*`) | object family 무관한 구조 추출 계층 | Confirmed |
| bbox decode (`read_bbox`) | class-relative 공통 구조 | Confirmed |
| chain grouping 뼈대 (`group_nodes_into_chains`) | 클래스 시퀀스 기반 object chain 구성 | Observed |
| style payload candidate 수집 프레임 | payload-relative scan/후보 보존 구조 자체는 재사용 가능 | Observed |
| raw evidence 보존(`raw_data`, `raw_contour_bytes`, candidate_fields) | 확정 전 단계에서 안정적 근거 축적 가능 | Confirmed |

text 분기 필요 지점:
- `CParagraphe` 기반 text run/anchor/line_count 조립
- text color confidence downgrade 정책
- font marker 관련 판정

즉, **binary/geometry 구조 계층은 공유**, **text 의미 해석 계층은 별도 family**가 맞다.

## D. Remaining Geometry Risks

| 리스크 | 현재 상태 | 영향 | 판정 |
|---|---|---|---|
| contour header shift heuristic 오탐 | shift 후보 다중 시도 | 잘못된 count/offset 채택 가능 | Provisional |
| count gate whitelist 누락 | `5/6` raw count 관찰, 현재 미선택 | 실제 contour decode 누락 가능 | Provisional |
| `_BBOX_CLASS_NAMES` 고정 | 클래스 확장 시 누락 가능 | bbox 미해석/체인 bbox fallback | Observed |
| shape classifier의 count 의존 | `polyline_2/3`가 현재 `arc`로 분류 | object_type labeling 오분류 | Observed |
| group candidate 규칙 | `declared_count==1 && chain>1` | group false positive/negative | Provisional |
| color fixed offset 일반화 범위 | payload 내부 특정 offset 가정 | fixture 외 샘플에서 색상 신뢰도 저하 | Observed |

## Contour Header Traceability Policy (P0)

- `read_contour_header(...)`의 반환 계약(`Optional[List[(kind,count,offset)]]`)은 유지한다.
- 동시에 `analyze_contour_header_candidates(...)`로 marker별 후보/선택 과정을 수집한다.
- 진단 필드(예):
  - `marker_offset`
  - `candidate_shifts`
  - `candidates[]` (`shift`, `header_offset`, `kind`, `count`, `plausible`, `rejection_reason`)
  - `selected_shift`, `selected_header_offset`, `selected_kind`, `selected_count`, `selected_payload_offset`
  - `selected_raw_header_hex` (선택된 kind/count 8B raw evidence)
  - `raw_8b_hex` (각 후보 kind/count 8B raw evidence)
  - `selection_reason`
  - `confidence="provisional"`
- parser는 이 진단을 `candidate_fields.contour_header_diagnostics` 및 chain-level diagnostics로 노출한다.
- 기본 inspector 가독성 보호를 위해 일반 출력은 늘리지 않고, diagnostics는 필요 시에만 확인한다.
- 현재 구현 상태(Phase 1): legacy selection 유지 + structural recommendation 진단 병행(`selection_mode=legacy_count_whitelist`, `structural_policy_status=diagnostic_only`)

### Current Inventory Observation (Geometry Fixtures)

- 현재 `tests/samples/*.txt` geometry fixture inventory 기준, **선택 성공 케이스의** `selected_shift`는 모두 `8`로 관찰되었다.
- 예시 raw 8B(kind/count):
  - `default_rectangle.txt`: `0200000004000000` (kind=2, count=4)
  - `default_circle.txt`: `0200000008000000` (kind=2, count=8)
  - `default_circular_arc.txt`: `0000000003000000` (kind=0, count=3)
  - `default_rounded_rectangle.txt`: `020000000c000000` (kind=2, count=12)
  - `polyline_2_points.txt`: `0000000002000000` (kind=0, count=2)
  - `polyline_3_points.txt`: `0000000003000000` (kind=0, count=3)
- 해석 상태는 `strong observed candidate`이며, **confirmed 승격 아님**. confidence는 계속 `provisional`.
- gate 밖 count raw 관찰:
  - `polyline_5_points`: raw `count=5` (`0000000005000000`)
  - `polygon_5_sides`: raw `count=5` (`0200000005000000`)
  - `polygon_6_sides`: raw `count=6` (`0200000006000000`)
  - 현재 gate `{2,3,4,8,12}` 때문에 `selection_reason=no_plausible_candidate`로 유지됨.
- 따라서 count gate는 현재 `known incomplete whitelist` 상태로 관리한다.

### Shape Evidence Delta (New Fixtures)

- `polyline_2_points`: selected `kind=0, count=2`, classifier는 count 기반으로 `arc` 분류
- `polyline_3_points`: selected `kind=0, count=3`, classifier는 count 기반으로 `arc` 분류
- `default_circular_arc`도 `count=3`이지만 `anchor/control=2/1`, polyline_3는 `2/0`(중간 role unknown)로 패턴 차이가 관찰됨
- `polyline_5_points`는 raw `kind=0,count=5`, `polygon_5/6`는 raw `kind=2,count=5/6`이 관찰됨
- 위 차이는 `kind`와 record/tag 패턴이 shape semantic 힌트일 수 있음을 시사하지만, 현재 단계에서는 provisional evidence로 유지한다.

### Type3 UI Observation (Observed/Provisional)

- 사용자 관찰 기준, 여러 draw tool(`사각형 도구`, `원형 도구`, `타원 도구`, `다각형 도구`)로 생성해도 선택 시 status bar 표시는 `곡선 객체`로 나타난다.
- 현재 단계 해석:
  - `곡선 객체` 표시는 **observed UI evidence**
  - draw tool 이름을 내부 object/class semantic과 직접 동일시하는 것은 **provisional 해석 금지**
  - fixture 파일명(`polyline`, `polygon`, `rectangle`)은 사람 가독성을 위한 intent label로 취급

### Shift=8 Promotion Gate (Not Yet Satisfied)

`shift=8`을 confirmed rule로 승격하려면 최소 아래 조건이 필요하다.
1. 더 다양한 독립 fixture 집합(도형/속성 조합 확장)
2. 현재 contour count gate `{2,3,4,8,12}` 밖 사례 검증
3. 다른 생성 세션/다른 객체 조건에서 반복 재현
4. raw 구조 반복성(kind/count 인접 구조) 추가 확인

## E. Recommended Next Actions (Priority)

| Priority | 액션 | 목적 |
|---|---|---|
| P0 | geometry 구조 불변성 테스트 유지/확장 (`test_geometry_parser_structure_invariants.py`) | 구조 계층 회귀 조기 감지 |
| Done | contour header raw evidence logging + inventory report CLI 추가 | `selected_raw_header_hex`, `raw_8b_hex`, `report_contour_header_candidates.py`로 추적성 확보 |
| Done | 1차 신규 geometry fixture 확보 (`polyline/polygon/rectangle scale+offset`) | count/좌표 조건 관찰 근거 확보 |
| P1 | gate 밖 count 샘플에 대한 evidence-only 축적 (`5/6` 포함) | heuristic 확정/확장 판단용 데이터셋 강화 |
| P1 | `tools/compare_contour_shape_evidence.py` 기반 count 동형/이형 비교 리포트 누적 | semantic 변경 전 evidence 축적 |
| P1 | polyline vs arc (`count=3`) tag/role 패턴 비교 리포트 | 동형 count의 semantic 혼동 리스크 분리 |
| P2 | `_BBOX_CLASS_NAMES` 규칙 검증 테스트 추가(새 fixture 생길 때) | bbox decode 안정성 유지 |
| P2 | group candidate를 evidence model로 분리(confirmed 승격 금지) | 의미 해석과 구조 파싱 경계 강화 |

## 항목별 결론

1. **header parsing**: marker/name_len/class_name 기반 구조 파싱이며 absolute file offset 의존 없음.  
2. **node scanning/boundary**: 다음 class header 기반 분할이며 absolute offset rule 없음.  
3. **bbox parsing**: class header 직후 6 doubles를 class-relative로 해석.  
4. **contour parsing**: payload marker + shift heuristic로 탐지하며 여기는 Provisional risk 핵심. stride=36은 현재 fixture군에서 구조 상수로 동작.  
5. **shape classification**: parser 구조 계층과 분리되어 있으며 의미 분류는 Observed heuristic.  
6. **multi/group**: class sequence 및 contour 반복 기반 분할은 Observed, group 판정은 Provisional.  
7. **style/color**: `0x79/0x85/0x20E/0x21A`는 absolute가 아니라 `CPropertyExtend payload-relative`다. geometry에서는 동작하지만 일반화 확정은 아님. text에는 downgrade 정책 유지가 맞다.  
8. **text 재사용성**: binary/node/bbox/evidence 보존 계층은 재사용 가능, text semantics는 별도 pipeline 유지가 정합적.
