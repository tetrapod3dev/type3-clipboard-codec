# Contour Candidate Selection RFC

상태: Draft (actual selection switched to refined structural ranking; legacy path retained for diagnostics)  
범위: contour candidate selection 설계 및 단계별 구현 상태 기록

## 1) 현재 로직 요약

현재 `geometry/contour_parser.py`의 candidate 선택 흐름:

1. `CObDao` marker를 payload에서 탐색
2. marker 뒤 `candidate_shifts=[8,14,12,16,20]` 순서로 후보 검사
3. 각 shift에서 `u32 kind + u32 count`를 little-endian으로 해석
4. `count`가 현재 gate `{2,3,4,8,12}`에 들어오면 plausible
5. 첫 plausible 후보(중복 offset 제외)를 selected로 채택
6. diagnostics에는 후보군/선택값/raw 8B evidence를 남김

selection reason:
- `first_plausible_shift_with_unique_offset`
- 실패 시 `no_plausible_candidate`

왜 지금까지 동작했는가:
- 기존 fixture 대부분이 `count ∈ {2,3,4,8,12}`에 포함
- selected shift가 사실상 8로 안정적으로 반복

왜 한계가 드러났는가:
- 새 fixture에서 raw valid 후보가 `count=5/6`으로 관찰되지만 gate에서 탈락
- 결과적으로 structural decode 가능성 있는 contour가 누락됨

## 2) 문제 정의

### 2.1 count whitelist 누락
- 현재 gate `{2,3,4,8,12}`는 universal rule이 아니라 관찰 목록
- `polyline_5_points(kind=0,count=5)`, `polygon_5/6(kind=2,count=5/6)`를 누락

### 2.2 구조 decode와 semantic 추론의 결합
- 현재 gate가 shape 경험칙에 묶여 structural decode 단계에 개입
- decode 이전에 semantic-like 제약이 걸려 data loss 발생

### 2.3 count-heavy classifier 오분류
- `count==2/3` 중심 분류로 `polyline_2/3`가 `arc`로 라벨링
- `default_circular_arc`와 `polyline_3`는 동일 count라도 record pattern이 다름

### 2.4 fixture intent와 internal semantic 구분 필요
- 파일명 `polyline/polygon/rectangle`은 fixture intent 라벨
- status bar 관찰 `곡선 객체`는 generic 내부 모델 가능성을 시사
- draw tool 이름과 internal class semantic 동일시 금지

## 3) 목표 설계: Structural Validation 우선

핵심 원칙:
- count는 semantic whitelist가 아니라 structural validation 입력값
- decode 성공 여부를 먼저 판정하고 semantic은 후속 계층에서 처리

제안 validation 조건(후보 1건 기준):

1. `header_offset` bounds 유효
2. `kind`, `count`를 u32 LE로 decode 가능
3. `count > 0`
4. safety upper bound 이내 (`count <= MAX_SAFE_CONTOUR_COUNT`, 예: 4096)
5. `record_start_offset + count * stride <= payload_length`
6. record decode가 예외 없이 수행됨
7. 좌표 finite
8. bbox consistency는 초기 단계에서 soft signal로 기록 (hard reject 아님)

주의:
- upper bound는 malformed/DoS 방지용 safety limit
- semantic whitelist 대체물이 아니어야 함

### tie-break 제안
동일 marker에서 복수 candidate가 structural-valid일 때:

1. structural-valid 후보만 필터
2. structural score 높은 후보 우선
3. 동점이면 legacy shift priority 우선
4. 그래도 동점이면 가장 작은 `header_offset` 우선
   - finite pass
   - bbox consistency soft signal
   - decode completeness

## 4) 계층 분리 설계

### A. Structural contour decode 계층
입력:
- payload

출력:
- candidate header 목록
- 각 후보의 records decode 결과
- structural validity (pass/fail + reason)
- diagnostics (raw 8B, bounds, decode status)

성격:
- semantic 중립
- 가능한 한 raw evidence 보존

### B. Derived shape classification 계층
입력:
- decoded records
- `kind`
- bbox
- tags/roles/w

출력:
- `rectangle/circle/circular_arc/polyline_candidate/polygon_candidate/...`
- confidence (`provisional` 가능)

원칙:
- decode 성공 != shape 분류 성공
- 분류 실패해도 contour records는 결과 모델에 유지

## 5) 최소 구현 전략 (향후)

1. RFC 승인 전 parser 변경 없음
2. structural validation helper 추가
3. diagnostics에 `structural_validity`/`failure_reason` 필드 추가
4. 기존 count whitelist는 legacy fallback 비교용으로 축소 또는 제거 후보화
5. 새 fixture들을 evidence/snapshot 테스트에 포함
6. shape classifier 개선은 다음 단계로 분리

### 구현 상태 (현재)
- 완료: structural validation helper 도입 및 diagnostics 필드 추가
- 완료: legacy selected vs structural recommended 동시 노출
- 완료: 실제 parser selection을 refined structural ranking winner로 전환
- 유지: structural 결과는 `diagnostic_only` 정책
- 관찰: expected mismatch(`polyline_5`, `polygon_5`, `polygon_6`) 외에 multi-object fixture에서 `kind=3,count=1` structural-valid 보조 후보가 추가 관찰됨 (`unresolved auxiliary candidate`)
- 완료(Shadow): refined ranking score를 diagnostics에 추가하고 `legacy/structural/refined`를 병렬 노출 (`recommendation_mode=shadow_run_only`)
- 완료(Shadow Gate): fixture inventory 전역 `legacy vs refined` diff 리포트 추가 (`tools/report_contour_selection_shadow_diff.py`)
  - fixture-level mismatch와 marker-level auxiliary 관찰을 분리해 보고
  - low-margin(`score_margin <= 3`, provisional threshold) fixture를 별도 경계 목록으로 유지
  - actual parser selection 전환 전 CI gate 근거로 사용
- 완료: actual selection 전환 후에도 legacy/actual/refined 비교를 diagnostics와 shadow diff 리포트에서 유지

### refined ranking score components (shadow-run)
- `base_structural_score`
- `node_context_score`
- `record_richness_score`
- `degeneracy_penalty`
- `bbox_relation_score`
- `competition_score`
- `final_refined_score`

원칙:
- hard reject 대신 weighted ranking
- parser selection 전환 전까지 diagnostics/evidence 용도로만 사용

## 6) 테스트 전략 (향후)

필수:
- 기존 geometry fixture 회귀 유지
- `polyline_5_points`, `polygon_5_sides`, `polygon_6_sides` structural decode 검증
- `polyline_3_points` vs `default_circular_arc`:
  - 둘 다 decode 성공
  - classifier 분기 개선은 별도 단계에서 검증
- malformed payload reject 케이스
  - out-of-bounds count
  - decode 불가 record
  - NaN/inf 좌표

금지:
- absolute offset assert
- fixture filename 분기

## 7) 비목표 (이번 단계)

- parser 코드 변경
- count gate 즉시 확장
- shape classifier 즉시 수정
- `polyline/polygon` confirmed type 승격
- `kind=0==open`, `kind=2==closed` 단정

## 10) 활성 모드 요약

- active selection mode: `refined_structural_ranking`
- legacy whitelist `{2,3,4,8,12}`: historical/diagnostic 경로로 유지 (`legacy_selected_candidate`)
- diagnostics 핵심 필드:
  - `legacy_selected_candidate`
  - `structural_recommended_candidate`
  - `refined_recommended_candidate`
  - `actual_selected_candidate`
  - `legacy_vs_actual_summary`
- shape classifier는 이번 전환과 분리되어 기존 동작 유지

## 8) 현재 evidence 요약

- `selected_shift=8`은 성공 케이스에서 강하게 반복 (`strong observed candidate`)
- raw header `u32 kind + u32 count` 해석은 자연스러움
- count gate는 `known incomplete whitelist`
- shape semantic은 provisional 유지 필요

outside-gate raw evidence (diagnostic):

| fixture | kind | count | raw_8b_hex | legacy result |
|---|---:|---:|---|---|
| `polyline_5_points.txt` | 0 | 5 | `0000000005000000` | `no_plausible_candidate` |
| `polygon_5_sides.txt` | 2 | 5 | `0200000005000000` | `no_plausible_candidate` |
| `polygon_6_sides.txt` | 2 | 6 | `0200000006000000` | `no_plausible_candidate` |

## 9) 오픈 질문

1. `kind` 값의 안정적 의미(특히 0 vs 2)는 무엇인가?
2. open/closed 판정에서 `first==last`를 충분조건 후보로만 쓸지, 추가 신호(tag/segment topology)를 어떻게 결합할지?
3. bbox consistency 실패를 hard reject로 둘지 soft signal로 둘지?
4. malformed payload에서 어디까지 복구 시도하고 어디서 fail-fast 할지?
5. multi-object/group payload에서 marker 간 후보 충돌을 어떻게 정규화할지?
6. `kind=3,count=1` 보조 후보를 하드 배제 없이 낮은 우선순위로 내리는 구조적 신호는 무엇인지?
7. shadow diff 리포트에서 `unexpected refined difference`가 0이 아닐 때 전환을 보류할 기준을 어디까지 자동화할지?
8. low-margin fixture가 발견될 때 score component 재조정 vs fixture 보강의 우선순위를 어떻게 둘지?
