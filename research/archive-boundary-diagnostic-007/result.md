# Archive Boundary Diagnostic 007

판정: **ARCHIVE_BOUNDARY_DIAGNOSTIC_VERIFIED** — 읽기 전용 진단 기능에 한정. 범용 Archive 복원, 객체 소유권, 쓰기 허가는 검증하지 않았다.

## 제공 도구와 실행

기존 tools의 argparse/JSON 진입 구조를 확인하고, production 패키지에 등록하지 않는 **연구용 CLI**로 제공했다. 파일은 이 신규 연구 폴더에만 추가했다. 기존 Decoder API·색상/형상/그룹 결과·ObjectHeader.class_id 및 Encoder는 수정하지 않았다.

Codec 저장소 루트 PowerShell에서:

```powershell
.venv\Scripts\python.exe research\archive-boundary-diagnostic-007\boundary_diagnostic.py `
  --input research\group-color\type3-clipboard-member-color-003\samples\G1\typeeditzone.bin `
  --research-shadow
```

선택적으로 `--output 새경로.json`을 지정한다. 기존 파일은 덮어쓰지 않으며 기본 출력은 stdout JSON이다. 입력은 저장된 바이너리만 받는다. hex-text fixture의 자동 추측 변환이나 Clipboard 입력은 없다. 8개 보존 fixture의 재현용 `reproduce.py`만 기존 006 fixture 로더를 통해 hex-text를 변환한다.

`--research-shadow` 또는 함수 호출의 `research_shadow=True`를 명시해야 한다. 정상 진단 수행의 CLI 종료값은0이며 UNSUPPORTED도 결과 JSON으로 표현한다. 파일·인수 오류는2다. 기본 Decoder를 import/실행하는 경로는 연구 Reader를 import하지 않는다.

## 구현과 지원 범위

- `boundary_diagnostic.py`는 **006 원본 shadow_reader.py를 선택 실행으로 import**한다. Reader를 복사·재구현하지 않았다. 001/002의 지원 집합을 확대하지 않았다.
- 지원 입력에서는 기존 Decoder와 Native Shadow가 동일한 원본 전체 bytes를 각기 읽는다. Decoder에 Native가 선택한 slice·cursor·색상값을 전달하지 않는다. 비교 시 Codec의 envelope-relative 좌표만 원본 절대 byte 좌표로 정규화한다.
- 결과는 전체 상태와 개별 관찰 이벤트를 분리한다. BOUNDARY_MATCH와 CANDIDATE_WINDOW_WIDER_THAN_NATIVE_BODY, 전역 SHARED_PROPERTY_CANDIDATE_WINDOW가 동시에 성립할 수 있다.
- raw Contour가 복수 chain에 대응하면 AMBIGUOUS로 표시하고 구성원 연결을 생략한다. 비교 가능한 단일 chain에서 위치/길이/count가 다르면 색상 일치 여부와 관계없이 BOUNDARY_MISMATCH다.
- shadow가 지원 prefix의 손상 구조를 거부하면 Decoder를 강제로 실행하지 않고 `decoder_observation_status=NOT_RUN_UNSUPPORTED_STRUCTURE`, `codec=null`을 반환한다. 이 상태는 Decoder의 실패 결과를 대신 만들어낸 것이 아니라 **관찰 미실행**이다. 기본 Decoder 자체의 응답은 변경하지 않았다.
- prefix가 다른 문자 표본에서는 Shadow가 UNSUPPORTED이지만 기존 Decoder는 정상 실행하여 결과를 별도로 보존한다.

## G1 / H1 실제 예시

두 그룹 모두 전체 상태는 CONDITIONAL_COMPARISON_COMPLETE이며 다음 관찰을 동시에 반환한다.

| Contour | Native / Codec 절대 범위 | Codec Property 후보 | Native Property 본문 | CCourbe suffix | 색상 DWORD 시작 |
|---|---|---|---|---|---|
| 첫째 | [630,774) | [795,8192) | [795,907) | [907,931) | 915/927 |
| 둘째 | [1375,1519) | [795,8192) | [1521,1633) | [1633,1657) | 1641/1653 |

각 행에 BOUNDARY_MATCH와 CANDIDATE_WINDOW_WIDER_THAN_NATIVE_BODY를, 전체에는 SHARED_PROPERTY_CANDIDATE_WINDOW를 기록한다. 이는 Parser 오류나 파일 손상 경고가 아니다. 후보 범위가 두 chain 사이에 공유되어 **구성원별 소유권이 아직 입증되지 않았다**는 진단이다.

색상 필드는 각각의 Property 본문 **밖**, 부모 CCourbe suffix의 순차 기록 범위 안에 있다. G1의 Navy Blue/Turquoise, H1의 Turquoise/Navy Blue 선택값은 그대로 유지된다. 같은 위치 순번을 R1/R2의 영구 식별자로 쓰지 않는다.

## 가변 형상과 문자

| 입력 | Contour count / 절대 범위 | Property 본문 | suffix | 진단 |
|---|---|---|---|---|
| polyline_3_points | 3 / [482,590) | [611,723) | [723,747) | 경계 일치, 넓은 Property 후보 |
| polyline_5_points | 5 / [482,662) | [683,795) | [795,819) | 동일 |
| polygon_5_sides | 5 / [482,662) | [683,795) | [795,819) | 동일 |
| polygon_6_sides | 6 / [482,698) | [719,831) | [831,855) | 동일 |
| default_circle | 8 / [482,770) | [791,903) | [903,927) | 동일 |
| text/default_text | Shadow cursor0에서 거부 | 미해석 | 미해석 | UNSUPPORTED; 기존 Decoder의 abcdefg 유지 |

이 범위와 CPtCtr4D의36바이트 계약은 001/002/006의 기존 근거를 재사용했다. 새 Native 발견으로 재분류하지 않는다. 다른 객체 계열에36바이트를 강제 적용하지 않는다.

## Schema·신뢰 수준·종료 위치

새 클래스 descriptor의 schema와 조건부 Archive class ID를 별도 출력한다. G1 CPropertyExtend는 schema5 / Archive class ID8이다. CContour는 schema2다. 기존 공개 ObjectHeader.class_id 필드명이나 값은 바꾸지 않았다. class reference는 원래 이벤트와 Archive 범위 등록 번호로 출력하며 영속 객체ID가 아니다.

- VERIFIED: 직접 검증된 Native CPtCtr4D 저장 폭 등 제한된 계약.
- CONDITIONAL: prefix·초기map·지원 동적 구조 아래 계산한 파일 경계 및 class 등록/참조.
- HEURISTIC: Codec의 후보 구간·선택 색상. 기존 strong/confirmed 원문도 따로 보존하며 VERIFIED로 치환하지 않는다.
- UNKNOWN: 실제 객체 소유권, 전체 Archive 유효 길이, 미해석 tail.
- UNSUPPORTED: 명시적으로 거부한 연구 Reader의 지원 범위.

G1/H1의 순차 중단 위치1657 뒤 [1657,8192)는 UNKNOWN이다. tail을 제거해도 archive_valid_length=UNKNOWN이다. change_allowed=false는 모든 결과에 유지한다.

## 모호성·손상 검증과 개발 중 관찰

[synthetic-diagnostics.json](synthetic-diagnostics.json)의 합성 입력은 Type3 실제 캡처가 아니다.

| 합성 대조 | 결과 / 실제 Reader 중단 위치 |
|---|---|
| 둘째 contour bytes를 첫째와 같게 복사 | AMBIGUOUS, 각 contour에 chain0/1 복수 대응, 구성원 배정 없음 |
| count101 | UNSUPPORTED, cursor630 |
| count×36 구간 끝 직전 절단 | UNSUPPORTED, cursor630 |
| Property 절단 | UNSUPPORTED, cursor903 |
| suffix 절단 | UNSUPPORTED, cursor907 |
| 미등록 class reference | UNSUPPORTED, cursor165 |
| 미지원 schema99 | UNSUPPORTED, cursor17 |
| UNKNOWN tail 제거 | 조건부 비교 완료, 유효 길이는 계속 UNKNOWN |

별도의 **합성 관찰값** 검사에서 색상은 그대로 두고 Codec 범위 시작만1바이트 옮겨 BOUNDARY_MISMATCH를 확인했다. 이 검사는 Type3 파일이나 실제 Decoder 출력을 변경한 것이 아니다.

초기 검사에서 전체 모델 지문 계산의 과도한 복제를 줄이기 위해, 공유 참조를 보존하는 메모리 내 pickle 직렬화의 SHA로 바꿨다. 외부 입력을 unpickle하지 않는다. 이후 절단 입력을 기존 Decoder에 직접 주었을 때 contour_parser.py의 후보 루프가 전진하지 않는 경로도 확인했다. 해당 시점 제가 실행한 pytest worker만 식별 후 중단했고, 두 번째 확인은 별도 Python에서2초 faulthandler 상한으로 종료했다. Type3/LLDB 프로세스는 조작하지 않았다.

이 문제를 이번 범위에서 production 수정하지 않았다. 대신 알려진 prefix의 손상 구조는 연구 Reader의 명시적 거부 이후 Decoder 미실행으로 기록한다. 지원 prefix 밖의 모든 임의 손상 데이터까지 안전하다고 보장하지 않는다. 진단은 보존된 검토 표본과 현재 지원 구조용이다.

## 결과 불변과 회귀

[decoder-equivalence.json](decoder-equivalence.json)에 형상·그룹·문자8개 입력의 Decoder 전체 반환 모델/Parser 이름을 진단 전후 비교한 지문을 보존했다. 모두 동일하다. 진단 중 생성된 Decoder 객체도 변경되지 않았다. 연구 Reader 예외를 합성한 검사에서도 기존 Decoder 결과를 재작성하지 않음을 확인했다.

신규 진단 검사30건과 기존006/001/002 검사39건: **69/69 PASS**. 로그는 targeted-tests.txt다. CLI 명시적 선택, 기존 출력 파일 덮어쓰기 거부, 일반 Decoder의 연구 import 부재도 검사했다.

전체 기존 Suite의 전후 결과와 원본 SHA 최종 검사는 preservation-final.json 및 suite-comparison.json에 기록한다. 기존 실패를 기대값 수정으로 숨기지 않는다.

## 보호 및 다음 통합 조건

시작 HEAD는 before.json에 기록했다. 006의712개 목록을 저장소 전체라고 해석하지 않고 재검증했으며, 별도로 Git tracked 파일과 해당 목록의 합집합1584개를 보호 대상으로 스냅샷했다. 사용자 미커밋 변경은 없었다. 기존 파일·연구 원본을 덮어쓰지 않았다.

Production 통합을 고려할 최소 조건은 다음과 같다.
1. 지원 prefix/schema/reference/Property 분기와 절대 좌표의 명시적 계약 유지.
2. 기존 후보와 순차 경계의 차이를 부가 진단으로만 제공하고 실패/거부 시 기존 Decoder를 교체하지 않음.
3. malformed 후보 루프의 전진성 문제는 별도 최소 수정·회귀 범위를 정하기 전 기본 경로에 연결하지 않음.
4. 임의 class 소유권·유효 데이터 끝·일반 Property 길이가 미확정인 동안 패치/쓰기 허가로 연결하지 않음.

이번에는 기본 Codec에 연결하지 않았다. Type3 실행·접근, 디버거 부착, Clipboard 접근, Pltf 분석, DLL/PLG/API/Ghidra 변경, Native 호출, Patch/Paste, 업무 모드 변경 및 새로운 실기 계획은 없다. 업무 모드 OFF와 기존 INCIDENT_CLOSED/COPY_PRODUCER_RUNTIME_PARTIAL/예외 원인UNKNOWN을 유지한다.

## 최종 확인

기존 전체 Suite는 변경 전후 모두 **1,469 PASS / 17 FAIL**이며 실패한 test ID17개가 동일하다. 신규 실패0개이며 기존 실패 기대값은 수정하지 않았다. 006 목록712개와 시작 스냅샷1584개 파일의 SHA를 재확인하여 기존 파일 변경0개다. Git 변경은 신규007 연구 폴더뿐이며 업무 모드는 OFF다.
