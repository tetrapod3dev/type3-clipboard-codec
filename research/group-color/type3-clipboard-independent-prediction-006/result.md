# 독립 그룹 교차 검증 결과

**INDEPENDENT_FIELD_PREDICTION_VERIFIED** — 새 통제 그룹 한 건에서 기존 고정 프로파일의 경험적 예측을 검증했다. 범용 그룹 파서·쓰기 허가·원본 선택 적용 성공을 뜻하지 않는다.

## 실행과 예측 순서

사용자의 명시적 승인 후 별도 Type3 인스턴스 PID 36460에서 진행했다. 기존 PID 17188/34968의 미저장 문서를 조작하거나 저장·닫기·폐기하지 않았다.

고정 프로파일 SHA256: `d0f179eaee2c9e625a936f7ce7ad7c3db0d78928df5a782bfd4a18d8130d3197`. 기존 S1/S2로 만들어진 프로파일을 그대로 사용했으며 H 표본으로 재학습하거나 기존 locator/codec 규칙을 바꾸지 않았다. `profile-lock.json`과 `frozen-profile.json` 참조.

1. H-R2를 먼저 생성한 뒤 H-R1을 생성했다. 제품 사각형 수치 대화상자의 좌하단 기준 좌표와 폭·높이를 지정했다.
2. 두 객체만 범위 선택하고 기존 Ctrl+결합(Group) 명령으로 묶었다. 단일 그룹 선택 핸들과 Decoder의 최상위 선언 1/사각형 후보 2를 함께 확인했다. 선택 수의 독립적인 Native 조회는 하지 않았다.
3. H0-A Copy·캡처 후 **2026-10-22T08:18:48.690942+00:00**에 예측을 고정했다. 이어 상태 변경 없는 H0-B를 캡처했다.
4. 기존 Ctrl+분리(Ungroup) 후 H-R2만 Turquoise로 변경하고 재그룹화했다. H1 Copy·캡처 후 **2026-10-22T08:19:31.150619+00:00**에 예측을 고정했다.
5. 두 예측 JSON이 존재한 뒤에만 `compare`로 실제 차분과 비교했다. 예측 파일은 최초 작성 후 덮어쓰지 않는다.

| 객체 | 실제 크기 | 좌하단 좌표 | H0 | H1 |
|---|---|---|---|---|
| H-R2, 먼저 생성 | 55×35mm | (600,200)mm | Army Green | Turquoise |
| H-R1, 나중 생성 | 30×20mm | (450,200)mm | Navy Blue | Navy Blue |

수치 입력과 실제 색상 화면은 `runtime-001/H-R2-parameters-corrected.png`, `R1-parameters.png`, `R2-army-selected.png`, `R1-navy-selected.png`, `R2-turquoise-selected.png`, `H1-colors.png`에 보존했다. UI 수치에서 도출한 bbox와 Decoder bbox가 일치했다. `ui-observations.json`에 근거와 대응을 기록했다.

### 준비 과정의 제한·실수

별도 인스턴스의 최초 화면(`runtime-001/empty.png`)에도 파랑·초록 윤곽이 관찰되어 **완전히 빈 문서였다고 주장하지 않는다**. 그 출처는 확인하지 않았다. 준비 중 사용자 정의 수치 입력창에서 Ctrl+A가 전체 선택으로 동작하지 않아 기존 숫자에 입력이 붙었고, 검정 준비 사각형 한 개가 만들어졌다. 화면으로 확인한 뒤 Home/Shift+End 방식으로 수정해 목표 두 객체를 별도로 생성했다. 준비 객체를 삭제·대체하지 않았다. 새 H 객체는 기존 윤곽과 떨어진 하단 영역에 배치해 두 객체만 선택했으며, 캡처에서 정확한 두 bbox·색상 및 단일 그룹 후보가 확인됐다. 이전 문서에 대한 변경이나 Clipboard 오캡처를 성공 근거로 사용하지 않았다.

## 실제 예측과 차분

| 대상 | 고정 프로파일의 예측 필드 | 실제 결과 |
|---|---|---|
| H-R2 | `[915,919)`, `[927,931)` | `98 CC 98 00` → `64 FF CC 00` |
| H-R1 | `[1641,1645)`, `[1653,1657)` | `30 60 CC 00` 유지 |

**변경된 6바이트: 915, 916, 917, 927, 928, 929.** 기존 G1의 R2 위치 1641/1653을 재사용하지 않고, 생성 순서가 바뀐 H에서는 bbox로 구분한 R2의 915/927을 예측했다. 절대 offset 하드코딩이나 색상 검색으로 정답을 찾지 않았다.

H0-A/H0-B는 Zone·Version 모두 완전 동일했다. H0/H1의 길이, Version, bbox 및 예측 필드 위치는 유지됐다. 총 116바이트 차이 중 6바이트가 목표 색상 필드였고, 나머지 110바이트는 기존 제한적 base walker의 GUID raw **후보** 구간 안에 있었다. 미분류 변경은 0개지만 GUID 차이를 무해하거나 동일 객체의 영구 identity로 해석하지 않는다. 재그룹화로 인한 객체 재생성 여부는 미확정이다.

| 표본 | Zone 크기 | Zone SHA256 |
|---|---:|---|
| H0-A | 8192 | `244020e74b9ff014a5e80ea43755c11a2d36cfa20601c10cab2f16de7f308bbf` |
| H0-B | 8192 | `244020e74b9ff014a5e80ea43755c11a2d36cfa20601c10cab2f16de7f308bbf` |
| H1 | 8192 | `1e2d803df75b56385d97ee8a0021ae94b80cb1da2cd37f96abdf95e4242957af` |

Version은 모두 32바이트, SHA256 `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f`. 각 `samples/*/manifest.json`에 실제 등록 포맷 ID와 수집 정보가 있다. 현재 업무 Clipboard를 사전 덤프하지 않고 직접 Copy한 시험 데이터의 TypeEditZone/TypeEditZoneVersion만 캡처했다.

## 코드·검사와 지원 한계

`prediction_check.py`는 고정 프로파일 검증·불변 예측 기록·예측 후 비교만 수행한다. **18/18 PASS**(준비 검사 6 + 기존 locator 12), `verification-final.txt` 참조. 기존 거부 사례를 포함한 검사이며 신규 Native 안전성 증명은 아니다. 상세 예측·전체 변경 offset은 `predictions/`와 `comparison.json`에 있다.

통제된 두 사각형 그룹 계열에서 구성원 순서가 달라도 예측 가능한 경험적 근거를 추가했다. 완전한 MFC class/reference ledger와 구성원 Serialize 끝 경계는 여전히 UNKNOWN이다. locator의 CANDIDATE_ONLY/change_allowed=false를 유지하고 범용 쓰기 허가로 승격하지 않았다. 문자·선·복합 그룹 등 다른 형식을 지원한다고 주장하지 않는다.

## 보존·최종 상태

`preservation-final.json`: 보호 파일 **982개 SHA 검사, 변경 0개**. 기존 locator·codec·성공 증거·제품 DLL/PLG/API 설치본을 보존했다. 업무 모드 **OFF**. Native 호출·Hook·패치 바이너리 생성·Clipboard 수정본 등록·Paste는 하지 않았다.

기존 두 Host와 새 시험 Host(36460)는 모두 미저장 문서가 열린 상태로 남겨 두었다. 자동 저장·닫기·폐기는 하지 않았다. Clipboard는 마지막 정상 Copy한 H1 시험 그룹 상태다. 관찰 중 내부 충돌 경고는 나타나지 않았다.

**다음 최소 작업:** 이 독립 H 표본의 예측 필드를 이용한 제한적 오프라인 패치 후보를 검토하고, 필요할 경우 별도 승인 후 한 번의 Patch/Paste 시험을 진행한다. 이번 작업에서는 실행하지 않는다. 범용 Serializer나 추가 Native 역공학으로 자동 확대하지 않는다.
