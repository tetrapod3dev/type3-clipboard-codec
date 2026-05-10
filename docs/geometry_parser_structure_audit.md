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
- 현재 구현 상태(Phase 2): actual selection은 `refined_structural_ranking` 활성화, legacy/structural/refined 비교는 diagnostics로 병행 유지(`structural_policy_status=diagnostic_only`).

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
- gate 밖 count였던 사례의 현재 상태:
  - `polyline_5_points`: actual selected `count=5` (`0000000005000000`)
  - `polygon_5_sides`: actual selected `count=5` (`0200000005000000`)
  - `polygon_6_sides`: actual selected `count=6` (`0200000006000000`)
- count gate `{2,3,4,8,12}`는 historical incomplete whitelist로 남아 있으며, actual selection의 universal rule이 아니라 legacy diagnostics reference로만 관리한다.
- shadow diff gate(`tools/report_contour_selection_shadow_diff.py`)로 fixture 전역 `legacy vs refined` 차이를 정량 추적한다.
  - `fixture-level winner mismatch`와 `marker-level auxiliary observation`을 분리
  - `low-margin(score_margin <= 3)`은 provisional 경계 신호로 별도 보고

### Shape Evidence Delta (New Fixtures)

- `polyline_2_points`: selected `kind=0, count=2`, classifier는 `polyline_candidate`
- `polyline_3_points`: selected `kind=0, count=3`, classifier는 `polyline_candidate`
- `default_circular_arc`도 `count=3`이지만 `anchor/control=2/1`, polyline_3는 `2/0`(중간 role unknown)로 패턴 차이가 관찰됨
- `polyline_5_points`는 actual `kind=0,count=5`, `polygon_5/6`는 actual `kind=2,count=5/6`으로 decode/selection됨
- 위 차이는 `kind`와 record/tag 패턴이 shape semantic 힌트일 수 있음을 시사하지만, 현재 단계에서는 provisional evidence로 유지한다.
- 추가 관찰: 일부 multi-object fixture(`two_rectangle`, `two_circle`, `turquoise_rectangle_and_army_green_rectangle`)의 별도 marker에서 `kind=3,count=1` 후보가 structural-valid로 관찰된다. 현재는 unresolved auxiliary candidate로 분류하고 selection 전환 전 추가 점검이 필요하다.
- 교훈: `structural_valid`와 `selected contour candidate로 적합`은 별개다. 현재는 refined weighted ranking을 shadow-run으로 병행 기록하고 parser selection은 유지한다.

## Shape Classifier Audit (Updated)

### 이전 count-heavy 분기(문제점)

| 분류 | 이전 조건(요약) | 리스크 |
|---|---|---|
| rectangle | `count==4` | 낮음 |
| circle | `count==8` + square-like bbox | 낮음 |
| rounded_rectangle | `count==8`(anchor/control=4/4) 또는 `count==12` | 중간 |
| circular_arc | `count==3` 또는 `count==2` | 높음 (`polyline_2/3` 오분류) |

### 현재 pattern-based 분기(적용됨)

- `circular_arc`: anchor/control 구조 + control 존재 + `w≈0.707` arc-like evidence + distinct start/end
- `polyline_candidate`: control 없음 + open-like evidence + arc-like control pattern 부재
- `polygon_candidate`: control 없음 + closed-like evidence (first/last 또는 role-pattern 기반 폐곡선 후보)
- `rectangle/circle/rounded_rectangle`: 기존 회귀 유지

상태:
- `polyline_2_points`, `polyline_3_points`, `polyline_5_points` → `polyline_candidate`
- `polygon_5_sides`, `polygon_6_sides` → `polygon_candidate`
- `default_circular_arc`는 `circular_arc` 유지
- `polyline_candidate`/`polygon_candidate`는 **provisional semantic**으로 유지 (confirmed 승격 아님)

### Polygon Candidate Audit Note

- `polygon_6_sides` 관찰:
  - `record_count=6`, `anchor_record_count=5`, `control_record_count=0`, `unknown_record_count=1`
  - 즉, 1개 레코드의 tag가 현재 role mapping에서 `unknown`으로 남아 anchor 집계가 5로 계산됨
- `closed_like_evidence=True` 근거:
  - `first_equals_last`가 아니라
  - `role_pattern_closed_like`(control 없음, anchor/unknown 중심, count>=5) 신호
- 결론:
  - polygon 판정은 현재 `kind` 확정 의미에 의존하지 않고 role/control/open-closed 패턴을 우선 사용
  - role/tag 의미 확정 전까지 `polygon_candidate` confidence는 provisional 유지가 타당

### Updated Interpretation of `0x03` Family

- weakened hypotheses:
  - always-middle marker
  - pure record-position marker
  - purely open/closed-topology-dependent marker
- session-recapture evidence also weakens strong coordinate-local interpretation:
  - `polygon_6_sides`의 `(55.555, 99.999)`는 `0x48454C03`
  - `polygon_6_sides_session2`의 동일 좌표는 `0x56454C0D`
- current safest interpretation:
  - `0x03`은 geometry/session/internal-state가 섞인 unresolved volatile family 후보
  - full raw tag는 session-sensitive
  - low byte는 full tag보다 상대적으로 안정적일 수 있으나 `0x03` 자체는 semantic role로 승격할 재현성이 아직 부족

## Contour Tag/Role Evidence Status

- 현재 confirmed role mapping 범위(관찰 기반, 보수 적용):
  - low-byte `0x0C` -> `control`
  - low-byte `0x0D`, `0x0F` -> `anchor`
- unknown tag family:
  - low-byte `0x03` 계열이 polyline/polygon fixture에서 반복 관찰됨
  - 예: `polygon_6_sides`의 `0x48454C03`는 현재 `unknown`
  - 예: `polygon_6_sides_rotated_start`에서도 `0x...03`가 관찰됨 (start-point 변경 후 비교용)
  - 예: `polyline_from_polygon_5_points`에서도 `0x...03`가 관찰됨 (closed->open topology 비교용)
  - 예: `polyline_5_points_reversed`에서도 `0x...03`가 동일 좌표 집합에 유지됨 (reversal 비교용)
  - 예: `closed_from_polyline_5_points`에서도 `0x...03`가 유지됨 (open->closed 비교용)
- pairwise evidence update (`tools/analyze_contour_tag_role_evidence.py`):
  - `polyline_5_points` vs `polyline_5_points_reversed`: `0x03` 좌표 집합 보존, index만 이동
  - `polyline_5_points` vs `closed_from_polyline_5_points`: `0x03` 좌표 집합 보존
  - `polygon_6_sides` vs `polygon_6_sides_session2`: `0x03` 좌표 집합은 보존되지 않았고(base의 `0x...03`가 session2에서 `0x...0D`로 관찰), high-byte 변동은 크게 관찰됨
  - `polyline_5_points` vs `polyline_5_points_session2`: open-path 계열에서도 `0x03` 좌표 재현성/low-byte 재현성/full-tag 재현성을 분리 관찰
  - 해석: `always middle`/pure record-position 가설 약화
  - 최신 해석: session 재캡처 증거로 strong coordinate-local 가설도 약화됨
  - 단, semantic 의미는 unresolved/provisional 유지 (`0x03==anchor` 승격 금지)
- 주의:
  - `...03`를 anchor로 확정 승격할 근거는 아직 부족
  - tag 의미와 shape semantic을 직접 동일시하지 않는다
  - shape classifier에서 `polyline_candidate/polygon_candidate`를 provisional로 유지하는 핵심 이유가 role/tag 미확정 상태다
  - 다음 단계 fixture 캡처 계획은 `docs/geometry_fixture_plan.md`의 `Tag/Role Evidence Expansion Plan`을 따른다.
  - polygon fixture의 numbered point order는 geometric description이며 payload 저장 순서 확정값이 아니다.

## 0x03 Family Investigation Closeout

### Investigation Timeline
1. 초기 관찰: `0x03`가 middle 위치에만 보이는 사례가 많아 middle-marker 가설 형성
2. `polygon_6_sides` vs `polygon_6_sides_rotated_start`: index 이동에도 동일 좌표 유지 관찰
3. `polyline_5_points` vs `polyline_5_points_reversed`: reversed 후에도 기존 `0x03` 좌표 집합 유지
4. `polyline_5_points` vs `closed_from_polyline_5_points`: open/closed 변경 후에도 기존 `0x03` 좌표 집합 유지
5. `polygon_6_sides` vs `polygon_6_sides_session2`: base의 `0x03` 좌표가 session2에서 `0x0D`로 변경
6. `polyline_5_points` vs `polyline_5_points_session2`: 기존 `0x03` 3개 유지 + 신규 `0x03` 1개 추가, full raw tag는 전 좌표 변경

### Evidence Table (Summary)
| 비교 | `0x03` 좌표 재현 | low-byte 안정성 | full-tag 안정성 | 결론 |
|---|---|---|---|---|
| `polygon_6` vs `rotated_start` | 부분 유지(동일 좌표 사례) | N/A | N/A | pure record-position 약화 |
| `polyline_5` vs `reversed` | 유지 | 높음 | 높음 | traversal-direction 약화 |
| `polyline_5` vs `closed_from_polyline_5` | 유지 | 높음 | 부분 변경 | topology-only 약화 |
| `polygon_6` vs `session2` | 미재현 | 일부 유지 | 낮음 | coordinate-local 약화 + session 민감 |
| `polyline_5` vs `session2` | 부분 재현 + 신규 추가 | 부분 유지 | 매우 낮음 | open-path에서도 session 민감 재현 |

### Weakened Hypotheses
- always middle marker
- pure record-position marker
- topology-only marker
- traversal-direction marker
- stable coordinate-local marker

### Current Policy (Fixed)
- `0x03` 상태: `volatile_unresolved_family`
- role assignment: `unknown` 유지
- `0x03 == anchor` 승격 금지
- shape classifier/semantic layer에서 `0x03` 의미 확정 금지
- 재현 가능한 신규 근거가 나오기 전 parser 정책 변경 금지

### Reopen Criteria
- 동일 geometry를 session-independent recapture해도 반복 재현
- shape family(polyline/polygon/others)를 넘어 일관된 분포 확보
- low-byte와 role 간의 일관 관계가 추가 fixture에서 안정적으로 검증
- parser 동작/정확도에 실제 문제를 유발하는 사례가 재현

## Geometry Parser Milestone Summary

- 완료:
  - actual contour selection을 `refined_structural_ranking`으로 전환
  - legacy whitelist는 diagnostics 경로로 강등
  - count-heavy 오분류(`polyline_2/3 -> arc`)를 pattern-based classifier로 개선
- Confirmed vs Provisional 경계:
  - Confirmed(운영): 구조 파싱 계층(class header/node scan/bbox/contour decode)
  - Provisional(의미): `kind` semantic, tag high-byte 의미, `polyline_candidate/polygon_candidate` semantic
- Remaining open issues:
  - `kind` semantic 확정
  - tag high-byte 의미
  - text object parsing 심화(`CParagraphe`/text color ownership/anchor decode confidence)

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
| P1 | `kind=3,count=1` 보조 후보 competition 분석 (`analyze_contour_candidate_competition.py`) | structural-valid false-positive 분리 신호 정의 |
| P1 | shadow diff CI gate 유지 (`report_contour_selection_shadow_diff.py`) | actual selection 전환 전 unexpected diff/low-margin 조기 감지 |
| P1 | polyline vs arc (`count=3`) tag/role 패턴 비교 리포트 | 동형 count의 semantic 혼동 리스크 분리 |
| P1 | `0x03` family 분리용 fixture 캡처 (rotated start / reversed / topology toggle / session2) | role mapping 승격 전 구조 신호 분리 |
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
