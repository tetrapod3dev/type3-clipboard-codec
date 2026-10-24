# 선택 개수 후보와 독립 검증

판정: **COUNT_CANDIDATE_CONDITIONAL**. producer 확인 없음. CLI의 값은 HEURISTIC이며 `top_level_selection_count=UNKNOWN`과 분리된다.

## 읽기 가설

`DWORD n / 64-byte entry × n / WORD count candidate / CZone descriptor candidate`다. V2는 n≤32와 입력 경계를 확인하고, 계산된 위치에서 정확한 기존 `FFFF/schema1/name-length5/CZone` 패턴을 검사한다. 첫 descriptor를 찾기 위해 문자열 검색이나 cursor 재동기화하지 않는다. offset70/134를 하드코딩하지 않는다. 이 검사는 Archive 진입이나 fresh map을 승인하지 않는다.

n>0은 TEXT_FONT64_PREAMBLE_CANDIDATE, n0은 GEOMETRY_N0_PREAMBLE_CANDIDATE로 별도 표시한다. n0도 기존6바이트 헤더를 무조건 승인하지 않고, 실제 descriptor 패턴 및 geometry계열의 독립 UI 대조 범위를 따로 기록했다. 64바이트 entry의 raw/SHA·이름 bytes 후보·NUL수는 출력하지만, 폰트 테이블이라는 의미는 아직 HEURISTIC이다.

## 신규 독립 자료

| 표본 | 독립 관찰 근거 | UI 최상위 수 | 후보 |
|---|---|---:|---:|
| S1-confirmed/S2-confirmed | member-color-003의 단독 선택 캡처·화면·count 재검사 기록 |각1|각1|
| U0 | 두 사각형 함께 선택2개라는 UI 기록 |2|2|
| G0-A/G0-B/G0-R/G1 | Group1개, 재Group 후1개라는 UI 기록 |각1|각1|
| H0-A/H0-B/H1 | 별도 그룹 생성·단일 선택 handle 및 수치 관찰 |각1|각1|

10개 캡처 중 G0-A/B 및 H0-A/B는 각각 같은 Zone SHA여서 고유 byte 입력은8개다. 반복 캡처를 독립된 포맷 법칙8건 이상으로 부풀리지 않았다. H는 독립 Native count가 아니라 UI Group/handle 관찰이라는 한계를 유지한다.

E1=3/F=4는 기존003 검토군이며 새 검증 통계와 분리했다. 단일문자/여러폰트/선택순서/기본polyline/circle 등의 보존 fixture는 출력·범위 점검에 사용했지만, 파일명/Decoder chain/intent만으로 정답 수를 정하지 않았다.

## 메타데이터 충돌과 반례

- 그룹3문자 intent의 `selected/copied object count: 3`과 후보1은 literal 불일치다. 같은 문서가 grouping=grouped, object_count=3으로 구성원도 설명하므로 최상위 UI 선택 수의 독립 증거인지 불명확하다. evidence의 `metadata_only`에 원문을 남기고 NOT_ESTABLISHED로 제외했다. 이를 UI count1로 수정하거나 실제 반증이라고 단정하지 않았다.
- 실제 UI count가 확립된 검토 표본에서는 CONTRADICTED 표본이 없었다. 이것은 모든 형식에서 맞는다는 증명이 아니다.
- count 반증을 누락시키지 않도록 U0의 count만7로 바꾼 메모리 합성 seam에서 CONTRADICTED 상태·값7 보존을 검사했다. 이는 새로운 실제 TypeEdit 반례가 아니다.
- 알 수 없는 preamble, 과도한n, 계산 위치의 CZone 불일치, 절단은 NOT_APPLICABLE/COUNT_CANDIDATE_UNKNOWN이다. 보정 규칙이나 검색 fallback은 없다.

## 다른 count와의 혼동

E/F의 n은 모두1인데 후보는3/4다. G1은 그룹 구성원/Contour2개지만 후보1, U0는 독립선택2개·후보2이며 파일 길이는 둘 다8192다. 그룹3문자는 문자/Contour 발생3개·char attribute가여러개지만 후보1이다. 한 값이 우연히 font/line/helper count와 같을 수 있으므로 이것만으로 의미를 확정하지 않는다. 기존 문자 intent 검토는 이런 혼동을 드러내는 보조 자료이며 선택 수의 독립 정답을 대신하지 않는다.

producer의 실제 기록 계약과 더 넓은 문자 계열 UI top-level 관찰이 없으므로 전체 가설을 COUNT_CANDIDATE_CORROBORATED 또는 VERIFIED로 올리지 않았다. UI값과 후보가 실제로 다르면 row의 CONTRADICTED와 전체 COUNT_CANDIDATE_CONTRADICTED를 그대로 보고하도록 검증했다. 값은 object 분할·그룹 구성원수·loop에 사용되지 않는다.
