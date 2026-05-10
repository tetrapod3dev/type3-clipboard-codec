# Reverse Engineering Log

이 문서는 TYPE3 clipboard format 역공학의 상태 로그다.  
목표는 “현재 사실”과 “과거 가설”을 분리해서 유지하는 것이다.

---

## Confirmed / Strongly Observed Facts (Current)

### Geometry/Binary structure
- class header scan은 marker/name_len/class_name 기반 구조 파싱을 사용한다.
- bbox는 class-relative로 `6 * little-endian double` decode를 사용한다.
- 좌표는 현재 fixture 범위에서 **little-endian double + meter 단위**로 일관 관찰된다.
- contour record decode는 stride 36 기반 구조로 동작한다.
- contour actual selection은 `refined_structural_ranking`이 active mode다.

### Shape/contour observations
- rectangle/circle/circular_arc/rounded_rectangle fixture는 구조 파싱 회귀 없이 유지된다.
- circular arc는 3-record 패턴(`anchor-control-anchor`)과 control `w≈0.707` 근거가 강하게 관찰된다.
- tag low-byte stable observed mapping:
  - `0x0C -> control`
  - `0x0D`, `0x0F -> anchor`

### Text baseline observations
- text 계열에서 `CParagraphe` 중심 구조가 반복 관찰된다.
- ASCII visible text/font 후보(예: `Arial`, `abcdefg`)는 일부 fixture에서 추출 가능하다.
- text anchor 검증 기준은 bbox lower-left가 아니라 `X 위치/Y 위치/Z 위치`(fixture policy)다.

### Style observations
- `CPropertyExtend` block 존재는 geometry/text 모두에서 반복 관찰된다.
- geometry color는 payload-relative candidate evidence가 축적되어 있다.
- text color ownership/semantic은 아직 provisional이다.

---

## Provisional Interpretations (Current)

- `kind` 값의 semantic 의미
- contour tag high-byte 의미
- `polyline_candidate` / `polygon_candidate` semantic 승격
- text exact encoding model(특히 Korean/multiline ownership)
- text style field의 direct semantic mapping

---

## 0x03 Family Investigation Closeout (2026-05-10)

### Timeline summary
1. 초기엔 middle marker 가능성
2. rotated_start 비교로 pure record-position 가설 약화
3. reversed 비교로 traversal-direction 가설 약화
4. open↔closed 비교로 topology-only 가설 약화
5. polygon session2 비교로 coordinate-local 강가설 약화
6. polyline session2 비교로 partial reproduction + full-tag volatility 확인

### Current policy
- `0x03` status: `volatile_unresolved_family`
- `0x03 == anchor` 승격 금지
- parser role assignment에서 `unknown` 유지
- 신규 재현 근거 없이는 mapping 변경 금지

### Reopen criteria
- 동일 geometry의 session-independent 반복 재현
- shape family를 넘는 일관 분포
- low-byte와 role 관계의 안정적 반복
- parser behavior에 실질적 오류 유발 사례

---

## Resolved Questions (Moved From Old Open Questions)

1. 좌표값 형식은 무엇인가?  
   - resolved(현재 범위): little-endian double, meter 단위 관찰.
2. Arc는 어떤 구조를 가지는가?  
   - resolved(부분): 3-record arc pattern(2 anchor + 1 control)과 control `w≈0.707` evidence 확보.
3. 스타일/지오메트리 블록이 완전히 무관한가?  
   - resolved(부분): `CPropertyExtend` block 존재와 geometry color evidence는 확보됨.

---

## Active Open Questions (Updated)

### Geometry
- 좌표 double/meter 규칙이 **모든 객체 family/필드**에서 동일하게 적용되는가?
- `kind` semantic은 무엇인가?
- tag high-byte는 어떤 상태(세션/객체/역할)를 반영하는가?

### Text
- Korean text 저장 표현과 exact encoding 규칙은 무엇인가?
- multiline text에서 run ownership/object ownership 경계는 어떻게 구성되는가?
- text color/style field의 class-relative/record-relative 안정 mapping은 어디인가?

### Cross-domain
- geometry에서의 style candidate 규칙과 text style candidate 규칙 중 공유 가능한 최소 공통 계층은 어디까지인가?

---

## Geometry Parser Milestone Summary

- 완료:
  - refined structural contour selection actual 전환
  - count-heavy shape misclassification 개선(pattern-based)
  - geometry structure audit + diagnostics closeout
- 경계:
  - Confirmed: 구조 파싱 계층
  - Provisional: semantic 계층(kind/tag high-byte/shape candidate meaning)

---

## Historical Notes / Superseded Hypotheses

아래는 과거 기록이지만 현재는 대체되었거나 범위가 좁혀진 가설이다.

- “좌표값은 정수/고정소수점/부동소수점 중 무엇인가”  
  -> 현재는 little-endian double(meter)로 strongly observed.
- “Arc는 어떤 수학적 표현으로 저장되는가”  
  -> 구조 패턴(3-record)은 확보, exact mathematical semantics만 미확정.
- “Text 인코딩은 무엇인가”  
  -> ASCII 일부는 추출 가능, Korean/exact encoding은 active open.
- “스타일 정보와 지오메트리 정보의 배치 순서”  
  -> `CPropertyExtend` 존재와 일부 mapping evidence는 확보, text style semantics는 미확정.

---

## Next Focus (Operational)

- `0x03` 트랙은 closeout 상태 유지(재오픈 조건 충족 전까지 동결)
- 다음 우선순위는 text object 분석 심화:
  - Korean/multiline ownership
  - text style field mapping stability
  - parser confidence layering 정교화
