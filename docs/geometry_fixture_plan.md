# Geometry Fixture Expansion Plan

본 문서는 geometry parser 구조 검증 강화를 위한 **신규 fixture 확보 계획**이다.  
주의: 현재 상태 표현은 `strong observed candidate / provisional heuristic`를 유지한다.

## 1) Current Coverage Summary

### 현재 확보 shape/구조
- single geometry: `default_rectangle`, `default_circle`, `default_circular_arc`, `default_rounded_rectangle`
- newly captured single geometry: `polyline_2_points`, `polyline_3_points`, `polyline_5_points`, `polygon_5_sides`, `polygon_6_sides`, `rectangle_small`, `rectangle_large`, `rectangle_negative_offset`, `rectangle_large_positive_offset`, `rectangle_recap_session2`
- multi/group: `two_rectangle`, `two_circle`, `two_rectangle_group`
- color variation: `color_*_rectangle`, `two_rectangle_group_*`, `turquoise_rectangle_and_army_green_rectangle`

### 현재 contour header 관찰
- selected shift 분포: 선택 성공 케이스는 `shift=8`만 관찰됨 (geometry inventory 기준)
- selected raw header는 `u32 kind + u32 count` 형태로 자연스럽게 해석됨
- 단, count candidate 선택은 아직 `{2,3,4,8,12}` whitelist에 의해 제한됨 (known incomplete)

### 현재 관찰된 count
- selected count로 관찰됨: `2`, `3`, `4`, `8`, `12`
- raw header count로 관찰되나 현재 gate에서 미선택: `5`, `6`
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

추가 권장(미캡처):
- `polyline_7_points.txt` (gate 밖 count)
- `polygon_8_sides.txt` (circle/rounded와 count 충돌 여부 확인)

## 3) Fixture-by-Fixture Validation Table (Ground Truth Intent)

| filename | Type3 UI source term | source geometry | expected contour behavior | expected count | validation purpose | why it matters |
|---|---|---|---|---|---|---|
| `polyline_2_points.txt` | status bar: `곡선 객체`; draw tool: not recorded | 열린 2점 폴리선 | open polyline, 최소 구성 | 2 (observed) | `count=2` 실관측 확보 | gate 하한값 실측 확보 |
| `polyline_3_points.txt` | status bar: `곡선 객체`; draw tool: not recorded | 열린 3점 폴리선 | open polyline, 3점 | 3 (observed) | arc와 같은 count의 비교군 | 동일 count의 shape-의존 해석 리스크 점검 |
| `polyline_5_points.txt` | status bar: `곡선 객체`; draw tool: not recorded | 열린 5점 폴리선 | open polyline, 5점 | 5 (raw observed, unselected) | gate 밖 count 유입 시험 | `count_not_plausible` 패턴 직접 확인 |
| `polygon_5_sides.txt` | status bar: `곡선 객체`; draw tool: not recorded | 닫힌 5각형 | closed polygon | 5 (raw observed, unselected) | 다각형 count 매핑 확인 | rectangle/rounded 편향 완화 |
| `polygon_6_sides.txt` | status bar: `곡선 객체`; draw tool: not recorded | 닫힌 6각형 | closed polygon | 6 (raw observed, unselected) | count 6 구조 확인 | gate 확장의 핵심 후보 |
| `rectangle_large.txt` | TBD | 큰 사각형 | rectangle-like 4 records | likely 4 | bbox 스케일 변화 검증 | 좌표 범위/precision 영향 점검 |
| `rectangle_small.txt` | TBD | 매우 작은 사각형 | rectangle-like 4 records | likely 4 | 작은 값 안정성 검증 | epsilon/정밀도 경계 점검 |
| `rectangle_negative_offset.txt` | TBD | 음수 좌표로 이동 | rectangle-like 4 records | likely 4 | 음수 bbox/contour 안정성 | sign 변화에서 header/record 일관성 확인 |
| `rectangle_large_positive_offset.txt` | TBD | 큰 양수 좌표로 이동 | rectangle-like 4 records | likely 4 | 큰 절대값 좌표 안정성 | max reasonable bound 근처 동작 관찰 |
| `rectangle_recap_session2.txt` | TBD | `default_rectangle` 동일 형상 재캡처 | rectangle-like 4 records | likely 4 | 세션 간 재현성 | shift=8이 세션 독립적으로 유지되는지 확인 |

해석 주의:
- fixture filename(`polyline`, `polygon`, `rectangle`)은 **fixture intent label**이다.
- 현재 확실한 UI 용어 관찰은 status bar의 `곡선 객체`이며, draw tool 이름과 내부 class semantic을 동일시하지 않는다.
- `expected count`는 ground truth intent/관찰값 분리로 기록하며, parser confirmed 승격으로 해석하지 않는다.

## 4) Current Parser Observation Snapshot (Diagnostics)

`tools/report_contour_header_candidates.py` 기준 핵심 관찰:
- `polyline_2_points`: selected `(shift=8, kind=0, count=2, raw=0000000002000000)`
- `polyline_3_points`: selected `(shift=8, kind=0, count=3, raw=0000000003000000)`
- `polyline_5_points`: raw candidate `count=5` 관찰, 현재 gate로 미선택
- `polygon_5_sides`: raw candidate `count=5` 관찰, 현재 gate로 미선택
- `polygon_6_sides`: raw candidate `count=6` 관찰, 현재 gate로 미선택
- rectangle scale/offset 변형(`small/large/negative/large_positive/recap_session2`)은 모두 selected `shift=8`, `count=4`
- `polyline_2_points`/`polyline_3_points`는 현재 shape classifier에서 `arc`로 분류됨(현재 분류기가 count-heavy heuristic임을 시사)

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

## 6) Parser Promotion Gates (Updated)

### shift=8 승격 조건 (아직 미충족)
1. 서로 독립적인 신규 fixture에서 반복 재현
2. count gate 밖 샘플에서도 동일 구조/선택 근거 유지
3. 다른 세션/좌표 조건에서 동일 선택 패턴 유지
4. raw header 8B(kind/count) 반복성 확인

### count gate 확정/확장 조건
1. 기존 gate `{2,3,4,8,12}`의 실 fixture 보강 (`2` 포함)
2. gate 밖 count(`5`, `6`, `7` 등)에서 구조적 타당성 검증
3. shape family별 count 분포 확보(polyline/polygon/rounded)
4. rejection reason 패턴이 구조적으로 설명 가능한지 확인
5. whitelist 의존보다 structural validation 기반 후보 선택이 타당한지 비교 리포트 확보

### 어떤 fixture가 어떤 gate를 채우는가
- shift 재현성: `rectangle_recap_session2`, `rectangle_negative_offset`, `rectangle_large_positive_offset`
- count 확장성: `polyline_5_points`, `polygon_5_sides`, `polygon_6_sides`
- gate 보강(기존값): `polyline_2_points`, `polyline_3_points`

## 7) Execution Priority

1. `rectangle_recap_session2.txt`  
2. `polyline_2_points.txt`, `polyline_3_points.txt`  
3. `polyline_5_points.txt`, `polygon_5_sides.txt`, `polygon_6_sides.txt`  
4. `rectangle_small.txt`, `rectangle_large.txt`  
5. `rectangle_negative_offset.txt`, `rectangle_large_positive_offset.txt`

우선순위 기준:
- parser 승격 리스크를 가장 빨리 줄이는 샘플부터
- 제작 난이도 대비 정보량이 높은 샘플부터
