# Geometry Fixture Expansion Plan

본 문서는 geometry parser 구조 검증 강화를 위한 **신규 fixture 확보 계획**이다.  
주의: 현재 상태 표현은 `strong observed candidate / provisional heuristic`를 유지한다.
candidate selection 로직 전환 설계는 `docs/contour_candidate_selection_rfc.md`에 정리한다.

## 1) Current Coverage Summary

### 현재 확보 shape/구조
- single geometry: `default_rectangle`, `default_circle`, `default_circular_arc`, `default_rounded_rectangle`
- newly captured single geometry: `polyline_2_points`, `polyline_3_points`, `polyline_5_points`, `polygon_5_sides`, `polygon_6_sides`, `rectangle_small`, `rectangle_large`, `rectangle_negative_offset`, `rectangle_large_positive_offset`, `rectangle_recap_session2`
- multi/group: `two_rectangle`, `two_circle`, `two_rectangle_group`
- color variation: `color_*_rectangle`, `two_rectangle_group_*`, `turquoise_rectangle_and_army_green_rectangle`

### 현재 contour header 관찰
- selected shift 분포: 선택 성공 케이스는 `shift=8`만 관찰됨 (geometry inventory 기준)
- selected raw header는 `u32 kind + u32 count` 형태로 자연스럽게 해석됨
- actual selection mode는 `refined_structural_ranking`이며, legacy whitelist `{2,3,4,8,12}`는 diagnostics 경로로만 유지된다.

### 현재 관찰된 count
- selected count로 관찰됨: `2`, `3`, `4`, `5`, `6`, `8`, `12`
- 미관찰: `7`, `9`, `10`, `11`, `13+`

### 아직 검증하지 못한 영역
- count 다양성 부족(특히 gate 밖)
- 동일 형상 재캡처(세션 간 안정성) 부족
- 좌표 규모/부호 변화(작은 값, 큰 값, 음수 오프셋)에서의 header 안정성
- polyline/polygon 계열의 실제 count 대응

## 2) Captured Fixture Inventory (Current)

이번 단계에서 실제 캡처 완료:
- `polyline_2_points.txt`
- `polyline_3_points.txt`
- `polyline_5_points.txt`
- `polygon_5_sides.txt`
- `polygon_6_sides.txt`
- `rectangle_large.txt`
- `rectangle_small.txt`
- `rectangle_negative_offset.txt`
- `rectangle_large_positive_offset.txt`
- `rectangle_recap_session2.txt`
- `polygon_6_sides_rotated_start.txt`
- `polyline_from_polygon_5_points.txt`
- `polyline_5_points_reversed.txt`
- `closed_from_polyline_5_points.txt`
- `polygon_6_sides_session2.txt`
- `polyline_5_points_session2.txt`

추가 권장(미캡처):
- `polyline_7_points.txt` (gate 밖 count)
- `polygon_8_sides.txt` (circle/rounded와 count 충돌 여부 확인)

### Ground Truth Correction Note (UI Recheck + Recapture)

- 과거 문서의 polygon 좌표 설명 중 일부는 초기 추정치였고, 현재 fixture는 재캡처된 최신 기준으로 정정한다.
- 아래 polygon 점 번호는 **geometric traversal description**이며 payload 저장 순서 확정값이 아니다.
- 문서 표기 원칙:
  - `UI-confirmed start point`
  - `user-described geometric point order`
  - `actual stored contour record order is unresolved`

#### `polygon_6_sides.txt` (recaptured current fixture)
- UI-confirmed start point: `(77.777, 66.666)` mm
- user-described geometric point order:
  1. `(77.777, 66.666)`
  2. `(66.666, 44.444)`
  3. `(33.333, 55.555)`
  4. `(33.333, 88.888)`
  5. `(55.555, 99.999)`
  6. `(66.666, 88.888)`
- actual stored contour record order is unresolved.

#### `polygon_5_sides.txt` (recaptured current fixture)
- UI-confirmed start point: `(77.777, 66.666)` mm
- user-described geometric point order:
  1. `(77.777, 66.666)`
  2. `(66.666, 44.444)`
  3. `(33.333, 55.555)`
  4. `(33.333, 88.888)`
  5. `(55.555, 99.999)`
- actual stored contour record order is unresolved.

#### `polygon_6_sides_rotated_start.txt`
- changed from: `polygon_6_sides.txt`
- changed variable: start point only
- UI-confirmed rotated start point: `(33.333, 88.888)` mm
- user-described geometric traversal (description): `4 -> 5 -> 6 -> 1 -> 2 -> 3`
- actual stored contour record order is unresolved.

#### `polyline_from_polygon_5_points.txt`
- changed from: `polygon_5_sides.txt`
- changed variable: closed contour -> open contour (`5 -> 1` 연결 제거)
- user-described point order:
  1. `(77.777, 66.666)`
  2. `(66.666, 44.444)`
  3. `(33.333, 55.555)`
  4. `(33.333, 88.888)`
  5. `(55.555, 99.999)`
- actual stored contour record order is unresolved.

#### `polyline_5_points_reversed.txt`
- changed from: `polyline_5_points.txt`
- changed variable: input order reversed only
- intended geometry: same 5 points, reversed traversal description
- actual stored contour record order is unresolved.
- hypothesis tested: `0x03` family가 좌표를 따르는지, 순번/방향을 따르는지 분리.

#### `closed_from_polyline_5_points.txt`
- changed from: `polyline_5_points.txt`
- changed variable: open contour -> closed contour only
- intended geometry: same 5 points + 마지막에서 시작점으로 닫힘
- actual stored contour record order is unresolved.
- hypothesis tested: 같은 좌표/순서에서 topology(open/closed)만 바뀔 때 `0x03` family 변화 여부.

#### `polygon_6_sides_session2.txt`
- changed from: `polygon_6_sides.txt`
- changed variable: capture session only
- intended geometry: `polygon_6_sides.txt`와 동일한 6개 점/동일 start point intent
- actual stored contour record order is unresolved.
- hypothesis tested: session 변경 시 `0x03` low-byte 안정성 vs full raw tag(high-byte 포함) 안정성 분리.

#### `polyline_5_points_session2.txt`
- changed from: `polyline_5_points.txt`
- changed variable: capture session only
- intended geometry: `polyline_5_points.txt`와 동일한 열린 5점 폴리선
- user-described point order:
  1. `(11.111, 22.222)`
  2. `(33.333, 11.111)`
  3. `(55.555, 33.333)`
  4. `(88.888, 22.222)`
  5. `(88.888, 44.444)`
- actual stored contour record order is unresolved.
- hypothesis tested: open-path 계열에서 session recapture 시 `0x03` 재현성과 high-byte 변동 분리.

## 3) Fixture-by-Fixture Validation Table (Ground Truth Intent)

| filename | Type3 UI source term | source geometry | expected contour behavior | expected count | validation purpose | why it matters |
|---|---|---|---|---|---|---|
| `polyline_2_points.txt` | status bar: `곡선 객체`; draw tool: not recorded | 열린 2점 폴리선 | open polyline, 최소 구성 | 2 (observed) | `count=2` 실관측 확보 | gate 하한값 실측 확보 |
| `polyline_3_points.txt` | status bar: `곡선 객체`; draw tool: not recorded | 열린 3점 폴리선 | open polyline, 3점 | 3 (observed) | arc와 같은 count의 비교군 | 동일 count의 shape-의존 해석 리스크 점검 |
| `polyline_5_points.txt` | status bar: `곡선 객체`; draw tool: not recorded | 열린 5점 폴리선 | open polyline, 5점 | 5 (actual selected/decoded) | gate 밖 count actual decode 검증 | refined selection 전환 효과 검증 |
| `polygon_5_sides.txt` | status bar: `곡선 객체`; draw tool: not recorded | 닫힌 5각형 | closed polygon | 5 (actual selected/decoded) | 다각형 count 매핑 확인 | rectangle/rounded 편향 완화 |
| `polygon_6_sides.txt` | status bar: `곡선 객체`; draw tool: not recorded | 닫힌 6각형 | closed polygon | 6 (actual selected/decoded) | count 6 구조 확인 | tag/role unresolved 분리 검증 핵심 |
| `rectangle_large.txt` | TBD | 큰 사각형 | rectangle-like 4 records | likely 4 | bbox 스케일 변화 검증 | 좌표 범위/precision 영향 점검 |
| `rectangle_small.txt` | TBD | 매우 작은 사각형 | rectangle-like 4 records | likely 4 | 작은 값 안정성 검증 | epsilon/정밀도 경계 점검 |
| `rectangle_negative_offset.txt` | TBD | 음수 좌표로 이동 | rectangle-like 4 records | likely 4 | 음수 bbox/contour 안정성 | sign 변화에서 header/record 일관성 확인 |
| `rectangle_large_positive_offset.txt` | TBD | 큰 양수 좌표로 이동 | rectangle-like 4 records | likely 4 | 큰 절대값 좌표 안정성 | max reasonable bound 근처 동작 관찰 |
| `rectangle_recap_session2.txt` | TBD | `default_rectangle` 동일 형상 재캡처 | rectangle-like 4 records | likely 4 | 세션 간 재현성 | shift=8이 세션 독립적으로 유지되는지 확인 |

해석 주의:
- fixture filename(`polyline`, `polygon`, `rectangle`)은 **fixture intent label**이다.
- 현재 확실한 UI 용어 관찰은 status bar의 `곡선 객체`이며, draw tool 이름과 내부 class semantic을 동일시하지 않는다.
- `expected count`는 ground truth intent/관찰값 분리로 기록하며, parser confirmed 승격으로 해석하지 않는다.
- the numbered order in polygon/polyline descriptions is a geometric description, not a confirmed payload order.

## 4) Current Parser Observation Snapshot (Diagnostics)

`tools/report_contour_header_candidates.py` / `tools/report_contour_selection_shadow_diff.py` 기준 핵심 관찰:
- `polyline_2_points`: selected `(shift=8, kind=0, count=2, raw=0000000002000000)`
- `polyline_3_points`: selected `(shift=8, kind=0, count=3, raw=0000000003000000)`
- `polyline_5_points`: actual selected `(shift=8, kind=0, count=5)`, contour records=5
- `polygon_5_sides`: actual selected `(shift=8, kind=2, count=5)`, contour records=5
- `polygon_6_sides`: actual selected `(shift=8, kind=2, count=6)`, contour records=6
- `polygon_6_sides_rotated_start`: actual selected `(shift=8, kind=2, count=6)`, contour records=6
- `polyline_from_polygon_5_points`: actual selected `(shift=8, kind=2, count=5)`, contour records=5
- `polyline_5_points_reversed`: actual selected `(shift=8, kind=0, count=5)`, contour records=5
- `closed_from_polyline_5_points`: actual selected `(shift=8, kind=2, count=5)`, contour records=5
- rectangle scale/offset 변형(`small/large/negative/large_positive/recap_session2`)은 모두 selected `shift=8`, `count=4`
- `polyline_2_points`/`polyline_3_points`는 현재 `polyline_candidate`
- `polygon_5_sides`/`polygon_6_sides`는 현재 `polygon_candidate`
- `polygon_6_sides_rotated_start`는 현재 `polygon_candidate`
- `polyline_from_polygon_5_points`는 현재 parser 출력상 `polygon_candidate`이며 open/closed 의존성은 추가 evidence 수집 대상
- `polyline_5_points` vs `polyline_5_points_reversed`: `0x03` 좌표 집합이 동일하게 유지됨 (record index는 변동)
- `polyline_5_points` vs `closed_from_polyline_5_points`: `0x03` 좌표 집합이 유지됨
- `polygon_6_sides` vs `polygon_6_sides_session2`: `0x03` 좌표가 유지되며 low-byte 안정성은 높게 관찰됨(세부 full-tag/high-byte 변화는 evidence로 추적)
  - 최신 관찰: base의 `(55.555,99.999)` `0x...03`가 session2에서는 `0x...0D`로 관찰되어 `0x03` 좌표 보존은 확인되지 않음
  - 다만 동일 좌표군 전반에서 high-byte는 변동이 크고 low-byte 패턴(`0x0D` 계열)은 상대적으로 반복되어, low-byte와 full-tag를 분리 추적해야 함
- 따라서 `0x03`에 대해:
  - `always middle` 가설은 약화
  - pure record-position 가설은 약화
  - open-only/closed-only 가설도 약화
  - session recapture에서 `0x03` coordinate 재현 실패 사례가 관찰되어 strong coordinate-local 가설도 약화
  - 현재 safest interpretation: `0x03`은 geometry/session/internal-state가 섞인 unresolved volatile family 후보
  - full raw tag는 session-sensitive 경향, low-byte는 상대적으로 더 안정적일 수 있으나 `0x03` 자체 승격 근거는 부족
  - semantic meaning은 여전히 unresolved (승격 금지)

## 5) Fixture 제작 지침 (Type3 작업자용)

### 공통 지침
- 좌표는 해석이 쉬운 수치 사용: `11.111`, `22.222`, `33.333` mm 계열 권장
- bbox와 기준점이 명확하도록 폭/높이/이동량을 단순 정수/반복소수로 고정
- fixture pair는 한 변수만 변경:
  - 예: `rectangle_large` vs `rectangle_small` (크기만 변경)
  - 예: `rectangle_small` vs `rectangle_negative_offset` (위치만 변경)

### 명명 규칙
- 파일명 패턴: `<shape>_<condition>.txt`
- 조건 토큰 예: `large`, `small`, `negative_offset`, `recap_session2`
- 텍스트 fixture와 충돌 방지 위해 geometry는 `tests/samples/` 루트에 저장

### 세션 재캡처
- `rectangle_recap_session2.txt`는 `default_rectangle`와 동일 좌표/크기/스타일로 새 세션에서 다시 캡처
- 목표: 형상 동일, 세션 메타 차이만 존재하는 상태 확보

### 난이도/대체안
- Type3에서 polyline/polygon 직접 생성이 어렵다면:
  - 대체안 1: 동일 계열 도구(다각형/폴리선)의 기본 도형 사용
  - 대체안 2: anchor 편집으로 점 수를 목표값에 맞춰 수동 조정
- count가 의도와 다르면 fixture명을 `*_observed_<count>.txt`로 임시 저장 후 재명명

## 6) Parser Status And Promotion Gates (Updated)

### Completed (Historical)
- actual contour candidate selection 전환 완료: `refined_structural_ranking`
- legacy whitelist `{2,3,4,8,12}`는 diagnostics path로 강등
- outside-gate count(`5`,`6`) actual decode 성공(`polyline_5`, `polygon_5`, `polygon_6`)

### Active Provisional Gates
- `shift=8`의 포맷 의미 confirmed 승격 여부
- `kind` 값 semantic 의미
- contour tag/role semantic (`...03` family 포함)
- `polyline_candidate`/`polygon_candidate` semantic confidence 승격 여부

### shift=8 승격 조건 (아직 미충족)
1. 서로 독립적인 신규 fixture에서 반복 재현
2. count gate 밖 샘플에서도 동일 구조/선택 근거 유지
3. 다른 세션/좌표 조건에서 동일 선택 패턴 유지
4. raw header 8B(kind/count) 반복성 확인

### role/tag 확정 조건 (현재 활성)
1. `0x03` family의 topology/order/session 민감도 분리
2. 동일 좌표 open↔closed 전환 fixture에서 role 변화 확인
3. rotated/reversed fixture에서 tag가 좌표 기반인지 순번 기반인지 확인
4. arc/circle/rounded 대비 `0x03`의 역할 분포 안정성 확보

### 어떤 fixture가 어떤 gate를 채우는가 (현재)
- shift 재현성: `rectangle_recap_session2`, `rectangle_negative_offset`, `rectangle_large_positive_offset`
- role/tag 분리: `polygon_6_sides_rotated_start`, `polyline_5_points_reversed`, `closed_from_polyline_5_points`, `polyline_from_polygon_5_points`

## 7) Execution Priority

### Historical (Completed)
1. `rectangle_recap_session2.txt`  
2. `polyline_2_points.txt`, `polyline_3_points.txt`  
3. `polyline_5_points.txt`, `polygon_5_sides.txt`, `polygon_6_sides.txt`  
4. `rectangle_small.txt`, `rectangle_large.txt`  
5. `rectangle_negative_offset.txt`, `rectangle_large_positive_offset.txt`

### Active (Tag/Role Track)
1. `polygon_6_sides_rotated_start.txt`
2. `polyline_5_points_reversed.txt`
3. `closed_from_polyline_5_points.txt`
4. `polyline_from_polygon_5_points.txt`
5. `polygon_6_sides_session2.txt`

우선순위 기준:
- parser 승격 리스크를 가장 빨리 줄이는 샘플부터
- 제작 난이도 대비 정보량이 높은 샘플부터

## 8) Tag/Role Evidence Expansion Plan (`0x03` Family)

목적:
- role mapping을 확정 변경하지 않고, `0x03` family가 어떤 구조 조건과 함께 나타나는지 분리 관찰
- fixture intent와 internal semantic 동일시 금지
- 한 fixture당 한 변수만 변경

### 검증 가설
1. `0x03`은 단순 middle-position marker인가?
2. open contour에서만 나타나는가?
3. closed contour에서도 특정 조건에서 나타나는가?
4. vertex count 증가와 연관되는가?
5. 좌표값 자체보다 record 순번/연결 순서에 연동되는가?
6. 시작점/종점/순서 변경에 반응하는가?

### Proposed Capture Matrix

| filename | source geometry intent | reused base fixture | changed variable | fixed variables | hypothesis tested | why it matters | expected observation |
|---|---|---|---|---|---|---|---|
| `polyline_4_points.txt` | open polyline | `polyline_3_points` | vertex count +1 | style, scale, capture flow | count 증가 시 `0x03` 분포 변화 | count 효과 분리 | unknown/provisional |
| `polyline_6_points.txt` | open polyline | `polyline_5_points` | vertex count +1 | style, scale, ordering 규칙 | count 6에서 middle tag 반복성 | high-count open 경향 확인 | unknown/provisional |
| `polygon_5_sides_rotated_start.txt` | closed polygon | `polygon_5_sides` | start vertex rotation | 좌표 집합, edge 연결, style | tag가 좌표 vs 순번 중 무엇을 따르는지 | 순서 민감도 분리 | unknown/provisional |
| `polygon_6_sides_rotated_start.txt` | closed polygon | `polygon_6_sides` | start vertex rotation | 좌표 집합, edge 연결, style | `0x48454C03`류가 index 이동하는지 | `polygon_6` unknown 원인 분리 | unknown/provisional |
| `polyline_from_polygon_5_points.txt` | open path from polygon coords | `polygon_5_sides` | closed→open topology | 좌표 집합, vertex order | open/closed 영향 분리 | topology 신호 검증 | unknown/provisional |
| `closed_from_polyline_5_points.txt` | closed path from polyline coords | `polyline_5_points` | open→closed topology | 좌표 집합, vertex order | same coords에서 closure 영향 | topology 독립성 확인 | unknown/provisional |
| `polyline_5_points_reversed.txt` | open polyline reversed | `polyline_5_points` | record order reverse | 좌표 집합, style | `0x03`가 middle-relative인지 | 순번 기반 여부 확인 | unknown/provisional |
| `polygon_6_sides_reversed.txt` | closed polygon reversed | `polygon_6_sides` | record order reverse | 좌표 집합, style | `0x03` tag 위치 반전 여부 | 방향성 영향 확인 | unknown/provisional |
| `polyline_3_points_middle_changed.txt` | open polyline | `polyline_3_points` | middle vertex coordinate | endpoints, style | 좌표 변화에 따른 tag 변동 | position vs coordinate 분리 | unknown/provisional |
| `polygon_6_sides_session2.txt` | closed polygon recapture | `polygon_6_sides` | capture session | geometry, style | session 독립 재현성 | 우연/세션 artifact 배제 | unknown/provisional |

### Capture Guidance
- 가능한 한 기존 좌표 재사용 (`11.111/22.222/33.333` 계열).
- start rotation/reverse는 geometry set 유지, record order만 변경.
- `polyline_from_polygon_*` / `closed_from_polyline_*`는 좌표 집합 고정 + topology만 변경.
- 결과 해석은 `confirmed` 금지, `observed/provisional`만 사용.

### Priority (Tag/Role Track)
1. `polygon_6_sides_rotated_start.txt`
2. `polyline_5_points_reversed.txt`
3. `closed_from_polyline_5_points.txt`
4. `polyline_from_polygon_5_points.txt`
5. `polygon_6_sides_session2.txt`
6. 나머지 count 확장 fixture (`polyline_4`, `polyline_6`, `polyline_3_middle_changed`, `polygon_5_rotated`, `polygon_6_reversed`)
