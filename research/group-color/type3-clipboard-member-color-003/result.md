# Phase 003 — 구성원별 색상 소유권 검증 결과

**최종 판정: MEMBER_COLOR_OWNERSHIP_PARTIAL.** 사용자 승인 후 7개 유효 표본을 확보했다. 그룹화가 두 색상을 소실시키지는 않았다. R2의 색상 변경에 대응하는 별도 바이트 쌍도 확인했다. 다만 구성원별 Serialize/CPropertyExtend 레코드의 완전한 시작·종료 및 참조 문맥이 미확정이어서 VERIFIED 또는 안전한 패치 API로 승격하지 않는다. **패치 후보·수정 Clipboard 등록·Paste는 수행하지 않았다.**

## 실제 UI와 그룹 보존

시작 시 Pltf/TypeEdit가 없어 정상 TypeEdit.exe를 실행했다. 새 PID **34968**, 빈 `Type31` 문서만 사용했다. 기동 중 창 준비 전 focus 검사는 실패하여 입력을 차단했고, 정상 창이 확인된 뒤 진행했다.

| 객체 | 실제 UI 크기(mm) | 실제 UI 중심(mm) | G0 색상 | G1 색상 |
|---|---|---|---|---|
| R1 | 80.024 × 60.053 | 200.678, 371.058 | Navy Blue | Navy Blue |
| R2 | 176.052 × 104.092 | 488.764, 349.039 | Army Green | Turquoise |

예시 20×15/45×30을 실제 크기로 기록하지 않았다. 서로 다른 크기·좌표로 생성한 뒤 UI 표시값을 사용했다. 단독 캡처 bbox와 U0/G0/G1의 구성원 bbox도 대조했으며 최대 차이는 약 `5.56e-17 m`(부동소수점 1 ULP 수준)이었다. 비교 허용오차는 `1e-12 m`다. Native 객체 identity나 비트 단위 좌표 동일성까지 주장하지 않는다.

U0는 실제 선택 **2개**, Group 후에는 **1개**로 확인했다. 그룹 bounds는 W 416.124, H 104.092mm다. Ungroup 후 2개 → 색상·위치 무변경 재Group 후 1개 → 다시 Ungroup하여 R2만 Turquoise로 변경 → 재Group 후 1개를 확인했다.

화면 근거: [S1 선택](S1-selection.png), [S2 선택](S2-confirmed-selection.png), [U0 두 개 선택](U0-selection.png), [그룹화 후 서로 다른 색상](group-colors-visible.png), [그룹 한 개 선택](group-single-selection.png), [재생성 대조군](G0-R-regrouped.png), [R2만 선택한 색상 변경](G1-R2-after-color.png), [최종 서로 다른 색상](G1-final-visible.png).

## 유효 표본과 SHA

모든 유효 Zone은 **8,192바이트**, Version은 **32바이트**다. Version SHA는 모두 `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f`다. 실제 format ID는 manifest의 registered_id로 기록했으며 observed_id 상수를 실제 ID로 쓰지 않았다.

| 표본 | Zone SHA256 |
|---|---|
| S1 | `ac14d3bf6769b3b7ad283e81287dd301cd29a684cd3be5028903e0c0d874fe8a` |
| S2 | `72f6a1e90d229ea0546237f8c63f2cc7801d3e595b3e7befc12c79c01fae4819` |
| U0 | `4b224da0536a5abe34c48e299376af3c4f03acd75dab3287c76808ebd3f78887` |
| G0-A | `eb9e7f9fb03dd1495b8e5337d0afdbce4e721e75791f2728d1434776a240155f` |
| G0-B | `eb9e7f9fb03dd1495b8e5337d0afdbce4e721e75791f2728d1434776a240155f` |
| G0-R | `ec2bc47e80652422d9973ec4ede4b4a8ba382070a9d6562fe3c5f961339d73bc` |
| G1 | `0b62011ff898b414fce086a6c775d1073bb08fe0b49edacf98e9d5a1d185ad4c` |

S1/S2의 유효 저장 경로는 `samples/S1-confirmed`, `samples/S2-confirmed`다. 나머지는 표본명과 같은 디렉터리다. 정확한 대응·파일 시각·UI 값은 [capture-metadata.json](capture-metadata.json)에 기록했다. 파일 시각을 Copy 이벤트 발생 시각으로 해석하지 않는다.

## 바이트 대조와 소유권의 경계

| 대조 | 실측 결과 |
|---|---|
| G0-A ↔ G0-B | 완전 일치, 차이 0 |
| G0-A ↔ G0-R | 110바이트 차이. 기존 제한적 base walker로 읽은 GUID raw 구간 안에 포함됨 |
| G0-R ↔ G1 | 117바이트 차이. 111바이트는 같은 GUID 기록 구간, 나머지 6바이트는 아래 R2 색상 후보 |

색상 후보(파일 byte 0 기준):
- R1 Navy Blue: **[915,919), [927,931)**. G0-A/G0-R/G1에서 같은 값 `30 60 CC 00` 유지.
- R2 Army Green → Turquoise: **[1641,1645), [1653,1657)**. `98 CC 98 00` → `64 FF CC 00`. 실제 변경은 각 필드의 앞 3바이트, 합계 6바이트다.
- S1/S2 단독 표본에서는 각각 **[767,771), [779,783)**에 해당 색상 값이 있다. 독립 사각형의 이전 offset 769를 이식한 결과가 아니다.

기존 `walk_base.py`를 수정 없이 재사용하여, 확인된 cube·version·GUID·property 길이 순서로 읽을 수 있는 base 부분을 대조했다. 재그룹 차분을 무조건 마스킹한 것이 아니다. 그러나 처음의 Archive 문맥이나 각 구성원 전체의 Serialize 종료 위치까지 증명하지는 않는다. GUID 기록을 영속 ID나 원본 객체 동일성의 증거로 사용하지 않는다.

UI에서 R2만 색상 변경, 재생성 대조군, R1 값 유지, 서로 다른 bbox라는 독립 근거를 확보했다. 따라서 **두 색상이 서로 다른 위치에 기록된다는 관찰은 강화됐다**. 하지만 두 위치가 R2 소유 Serialize 레코드 내부임을 확정할 경계는 미해결이다. 거리나 바이트 검색만으로 소유권을 확정하지 않았다. 길이·parser 선언 수는 같지만 전체 참조표의 불변성은 미검증이다.

상세 근거: [comparison.json](comparison.json), [ownership-evidence.json](ownership-evidence.json), [제한적 파일 비교 코드](compare_members.py). 비교 코드의 검사 및 기존 그룹·혼합 색상 회귀 **6/6 PASS** (`regression.log`).

## 기존 파서의 공유 색상 문제

`_process_object_chain`은 공통 CPropertyExtend payload에서 base style을 만들고 embedded contour에 적용한다. `choose_color_candidate`는 일치한 fixed pair를 거리보다 먼저 선택하므로 과거의 같은 색 그룹 표본에서는 두 chain이 같은 pair를 가리켰다. 두 개의 독립적인 Native style을 읽었다는 뜻은 아니었다.

이번 서로 다른 색 그룹에서는 같은 넓은 property payload 안에서 다른 scan 후보를 선택하지만, 여전히 후보·거리에 의존한다. 현재 codec 출력을 안전한 구성원 쓰기 API로 바로 전용하지 않는다. 기존 codec은 변경하지 않았다.

## 다음 개발 판단과 환경

**Patch/Paste로 발전시킬 가치가 있는 차분 입력은 확보했지만 실행 후보는 아직 만들 수 없다.** 다음에 필요한 것은 이 보존 데이터의 R2 property 레코드 경계와 참조 문맥에 대한 제한적 확인 한 건이다. 추가 표본을 무제한 생성하거나 Native Paste를 재조사하지 않는다. 조건이 충족되기 전에는 텍스트·선·혼합 그룹 쓰기로 확장하지 않는다.

최종 Clipboard는 제품이 Copy한 G1이다. 수정 데이터 등록과 Paste는 실행하지 않았다. PID 34968의 미저장 시험 문서는 열린 상태다. 원본 DLL·PLG·Workbench·PracticalClient·codec 등 보호 대상 **915개 파일 변경 0개**, 업무 모드 OFF다. 저장·폐기·종료하지 않았다.

준비 과정의 다음 제외 사항은 정식 대조 데이터와 구분한다.
- 최초 S1은 팔레트에 focus가 남아 Copy가 성립하지 않았고 시험 데이터와 일치하지 않았다. **분석·소유권 근거·버전 관리에서 제외**하고 유효 S1을 별도 폴더에 다시 확보했다. 오캡처 파일 3개 삭제는 처음 자동 승인 검토에서 “증거 삭제 위험”으로 거부됐으나, 이후 사용자의 명시적 승인에 따라 해당 파일 3개만 삭제하고 부재를 확인했다. 내용의 추가 분석은 하지 않았다. 정리 기록은 `invalid-capture-cleanup.json`에 있다.
- 그리기 모드를 전환하기 전에 준비용 검정 사각형 한 개가 추가됐다. 삭제하지 않고 완전 포함 선택 범위에서 제외했다. 최초 S2는 이 준비물이어서 제외했으며, 선택 모드에서 R2 크기·색상을 대조한 S2-confirmed를 사용했다. 대상 그룹에는 포함되지 않았다.
- 최종 문서에는 대상 그룹 1개(R1/R2)와 범위 밖 준비 사각형 1개가 있다. 모두 이번 새 시험 문서의 객체이며 업무 파일이 아니다.

---

## Stage A 사전 계획 — 아래는 실행 전 이력

2026-10-22. **Stage A 완료 / 실기 캡처 승인 대기.**

현재 소유권은 NOT_VERIFIED다. S1/S2/U0/G0-A/G0-B/G0-R/G1은 아직 만들지 않았다. 최종 실험 판정은 캡처 후 내린다. 기존 Phase 002의 GROUP_MEMBER_PATCH_BLOCKED가 해소됐다고 표시하지 않는다.

## 재사용 도구와 기존 근거

- 캡처는 기존 codec `tools/clipboard_typeeditzone.py dump-bundle --dir <샘플 경로>`를 사용한다. **실제 Copy 직후 TypeEditZone/TypeEditZoneVersion 두 형식만** 저장한다. manifest의 `registered_id`가 실제 ID이며 `observed_id` 상수를 현재 ID로 쓰지 않는다. 현재 Clipboard는 읽지 않았다.
- 같은 도구의 main은 file inspect 명령에서도 Clipboard adapter를 생성하므로 Stage A 분석에서는 호출하지 않았다. 기존 Decoder를 직접 import하는 파일 전용 분석기를 준비했다.
- [Phase 002 진단](../type3-clipboard-group-member-patch-002/member-evidence.json)에서 그룹 두 chain은 같은 property payload 시작 647과 같은 색상 범위 [1173,1177), [1185,1189)를 가리킨다. 같은 색상 그룹 테스트는 구성원별 독립성을 보장하지 않는다.
- 비그룹 혼합 색상은 구분되지만 후보 검색·거리 기반 배정이다. 이를 그룹 child 소유 레코드로 간주하지 않는다. 독립 사각형의 offset 769도 이식하지 않는다.

## 승인 후 캡처 절차

실행 직전에 PID·창 제목·열린 문서 상태를 다시 확인한다. 다른 업무 창에는 조작을 보내지 않는다. 기존 인스턴스의 미저장 문서를 바꾸지 않으며, 안전한 별도 시험 문서를 준비할 수 없거나 저장 확인이 나오면 취소하고 중단한다. 자동 저장·폐기·종료하지 않는다. 프로세스 출력은 반드시 JSON 등 명시적 형식으로 확인하여 이전의 표 출력 혼선을 반복하지 않는다.

1. 폐기 가능한 문서에서 R1/R2를 겹치지 않게 생성. 목표 크기는 20×15 / 45×30 mm이며 실제 UI 확인값을 사용한다. 크기 입력을 검증할 수 없으면 목표값을 실제값으로 기록하지 않는다. bbox·위치·색상명·선택 수·PID·문서 제목·시각·화면을 함께 남긴다.
2. 제품 색상 UI에서 R1 Navy Blue / R2 Army Green을 확인. S1은 R1 단독, S2는 R2 단독, U0는 두 객체 선택 상태로 각각 Copy·두 형식 캡처.
3. 기존 Group 명령 실행 후 서로 다른 색상이 화면에서 유지되는지 확인한다. 여기서 색상이 같아지거나 소실되면 GROUP_COLOR_COLLAPSES로 중단하고 패치로 우회하지 않는다.
4. 그룹 하나 선택 → G0-A Copy/캡처 → 상태를 바꾸지 않고 G0-B Copy/캡처. 첫 Copy와 두 번째 Copy의 시각도 기록한다.
5. Ungroup → 크기·위치·색상 무변경 확인 → 다시 Group → G0-R 캡처.
6. Ungroup → **R2만** Army Green에서 Turquoise로 변경 → R1과 두 형상의 보존 확인 → 다시 Group → G1 캡처. 객체 재생성이나 색상 자동 정규화가 관찰되면 기록하고 중단한다.

각 표본은 `samples/<이름>/typeeditzone.bin`, `typeeditzone_version.bin`, `manifest.json`으로 저장한다. UI 관찰과 화면은 동일 샘플명으로 별도 기록한다. 이번 승인 범위에 **수정 Clipboard 등록·Paste는 포함하지 않는다**.

## 대조 및 Fail Closed 조건

- G0-A↔G0-B: 같은 상태에서 달라지는 구간과 정확한 재현성 확인. 차이가 있으면 바로 색상으로 해석하지 않는다.
- G0-A↔G0-R: 해제/재그룹에 따른 변화 구분. 객체 순서·identity가 유지됐다고 가정하지 않는다.
- G0-R↔G1: R2의 색상만 바뀌었다는 UI 근거와 대조한다. 재생성 영향 구간을 무조건 마스킹하여 색상 근거로 만들지 않는다.
- S1/S2/U0: 크기·bbox·색상으로 실제 구성원을 구분한다. UI 이름 R1/R2와 archive 순서가 같다고 가정하지 않는다.
- 색상 후보가 달라도 **구성원 Serialize 레코드 안의 필드라는 경계 근거**가 없으면 PARTIAL 이하로 유지한다. 문자열·팔레트 바이트 검색, 가까운 contour, Decoder confidence만으로 VERIFIED를 만들지 않는다.
- R2 필드가 R1과 겹치거나, 길이·개수·참조가 함께 바뀌거나, 입력이 미지원 형식이면 패치 후보를 만들지 않는다. 모든 근거가 확보될 때만 특정 입력 SHA에 한정하여 오프라인 후보를 작성한다. 새 Encoder·Serializer 및 기존 API 수정은 하지 않는다.

[analyze_captures.py](analyze_captures.py)는 보존 파일만 읽어 SHA·길이·Decoder 후보·동일 offset 차분을 출력한다. 절대 offset 차분은 의미별 record alignment가 아니다. 아직 캡처가 없으면 `comparison.json`에 NOT_CAPTURED를 기록하며 가짜 객체·부모 관계를 채우지 않는다.

## 현재 결과와 승인 범위

실제 객체 크기·색상·선택·표본 SHA·그룹화 전후 색상 유지·소유권 대응: **NOT_TESTED / NOT_CAPTURED**. 실제 패치 후보 없음. 텍스트·선·혼합 그룹 확장 또는 Patch/Paste 시험의 가치는 위 통제 표본의 결과가 나온 뒤 판단한다.

요청할 승인은 **Type3 정상 실행(필요 시), 별도 시험 문서와 두 사각형 생성, 지정한 색상 설정, 선택·Group/Ungroup·재Group·R2 색상 변경 및 총 7회 Copy/두 형식 캡처**다. 이 과정에서 기존 Windows Clipboard 내용이 덮어써진다. 기존 업무 Clipboard를 덤프하거나 백업하지 않는다. 문서 저장·폐기·닫기·강제 종료·수정 데이터 등록·Paste는 승인 요청에서 제외한다.

기존 DLL·PLG·Workbench·PracticalClient·codec은 보존하고 업무 모드 OFF를 유지한다. Stage A 보호 파일 전후 결과는 `preservation.json`에 기록한다. 실기 전 환경은 다시 확인한다.
