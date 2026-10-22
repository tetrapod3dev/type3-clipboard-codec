# 특정 G1 그룹 색상 패치 — 실제 Paste 검증

**최종 판정: GROUP_PATCH_RUNTIME_VERIFIED.** 사용자의 Stage B 승인 후 별도 빈 시험 문서에 수정본을 **한 번만** 붙여넣었다. 그룹 1개, R1 Navy Blue 유지, R2 Army Green 복원, 두 사각형 형상·좌표·크기 유지와 재Copy를 확인했다.

이번 후보는 사용자가 지정한 G1 SHA 하나와 네 필드의 원본값에만 적용된다. 범용 그룹 구성원 API나 Serialize 레코드 소유권 해석을 확보한 결과가 아니다.

## Stage B 실제 실행 결과

기존 PID **34968**의 미저장 원본 시험 문서는 그대로 유지했다. 새 TypeEdit 인스턴스 PID **17188**의 빈 `Type31` 문서에서만 Paste했다. 첫 준비 검사 시 새 창의 handle이 아직 없어 입력을 차단했고, 창이 정상적으로 준비된 뒤 이어갔다. 두 번째 인스턴스를 반복 실행하거나 Paste를 재시도하지 않았다.

| 확인 항목 | 실제 결과 |
|---|---|
| G1·후보·Version SHA 재확인 | PASS |
| 후보 Zone + G1 원본 Version 등록·검증 | PASS |
| 정상 Ctrl+V | **1회**, 추가 설정·확인창 0개 |
| UI의 최상위 그룹 선택 수 | **1개** |
| 표시 형상 | 서로 떨어진 사각형 2개, 불필요한 객체 관찰 없음 |
| R1 | 작은 사각형, Navy Blue 유지 |
| R2 | 큰 사각형, Army Green 복원 |
| 재Copy의 형상·bbox·점·contour | G1 및 후보와 동일 |
| 후보 ↔ 재Copy Zone | **8,192바이트 전체 동일** |
| 후보 ↔ 재Copy Version | **32바이트 전체 동일** |
| 경고·오류·부분 삽입 | 관찰하지 않음 |

재Copy Zone SHA256:
`d70bc09ac7b8f4bfff4d131acecda4d831f99b249d4fc6f1996c2d65ae605fb8`.
Version SHA256:
`33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f`.

G1 원본과 실제 재Copy 사이의 차이도 지정한 **6바이트뿐**이다. 이번에는 GUID 등 추가 바이트 정규화가 관찰되지 않았지만, 다른 입력·문서에서도 같다는 보장은 아니다. G0-R과의 111바이트 차이를 일반적으로 무해하다고 판정하지 않는다.

선택 UI의 그룹 크기는 **416.124×104.092mm**, 중심 **(368.728,349.039)mm**였다. 개별 사각형의 재Copy bbox·점·contour는 G1/후보와 정확히 일치한다. 기존 기준은 R1 **80.024×60.053mm**, R2 **176.052×104.092mm**(반올림)이며 새 문서에서 원래 위치에 나타났다. 화면상 두 색상과 배치도 대조했다. 붙여넣은 그룹을 해제·재그룹하거나 구성원을 이동·삭제하지 않았다.

화면 및 데이터:
- [빈 시험 문서](runtime-001/test-empty.png)
- [한 번 Paste 후 그룹 1개 선택](runtime-001/after-single-paste.png)
- [R1 파랑·R2 녹색 표시](runtime-001/restored-colors-visible.png)
- [그대로 유지한 원본 문서](runtime-001/original-after.png)
- [실제 재Copy 입력 쌍](runtime-001/recopy/manifest.json), [실기 비교 결과](runtime-001/runtime-result.json), [파일 전용 검증 코드](verify_runtime.py)

원본 PID34968에는 창 상태 확인과 읽기용 화면 기록만 했으며 문서·선택·색상 변경 명령을 보내지 않았다. 최종적으로 두 인스턴스와 두 미저장 시험 문서는 열린 상태다. Clipboard는 복원한 그룹의 재Copy 데이터로, 후보와 같다. 저장·닫기·폐기·프로세스 종료는 하지 않았다. 업무 모드 **OFF**, 보호 파일 **941개 변경 0개** (`runtime-001/preservation.json`).

**검증 범위는 이 특정 G1의 두 필드 패치 한 건**이다. 구성원 Serialize 경계는 여전히 Unknown이며, 일반 그룹의 소유권·참조 해석·원본 선택·삭제·교체·중첩 그룹·텍스트/선 지원 또는 장기 안정성을 검증한 결과는 아니다. 이 시험으로 작업을 마치며 추가 Paste는 하지 않는다.

## 실제 생성물

| 항목 | 결과 |
|---|---|
| 입력 G1 | `../type3-clipboard-member-color-003/samples/G1/typeeditzone.bin` |
| 입력 SHA256 | `0b62011ff898b414fce086a6c775d1073bb08fe0b49edacf98e9d5a1d185ad4c` |
| [수정본](candidate/typeeditzone.bin) SHA256 | `d70bc09ac7b8f4bfff4d131acecda4d831f99b249d4fc6f1996c2d65ae605fb8` — 지정 예상값 일치 |
| 원본·수정본 크기 | 모두 8,192바이트 |
| Version | G1 원본 32바이트를 [그대로 복사](candidate/typeeditzone_version.bin) |
| Version SHA256 | `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f` |

0 기준 offset, 끝 제외 구간:

| 기록 구간 | 원본 | 수정본 |
|---|---|---|
| [1641,1645) | `64 FF CC 00` | `98 CC 98 00` |
| [1653,1657) | `64 FF CC 00` | `98 CC 98 00` |
| R1 [915,919) | `30 60 CC 00` | 그대로 |
| R1 [927,931) | `30 60 CC 00` | 그대로 |

실제 변경 offset은 **{1641,1642,1643,1653,1654,1655}**뿐이다. 나머지 모든 바이트가 동일하다. 입력 길이·SHA·네 필드 중 하나라도 다르면 `ValueError`로 거부한다. 출력 SHA도 확인한 뒤 별도 파일에 기록한다. 기존 출력이 다른 데이터이면 덮어쓰지 않는다.

## 오프라인 검증 결과

- 기존 Decoder에서 그룹 후보 유지, 선언 수 1, 두 사각형 chain 유지.
- 색상 후보: R1 Navy Blue → Navy Blue, R2 Turquoise → Army Green.
- 그룹 bbox·aggregate bbox·각 chain bbox·점·contour 기록·raw contour SHA가 입력과 동일.
- G0-R과 남은 차이 **111바이트** 재현. 기존 `ownership-evidence.json`의 제한적 base walker에서 구분한 GUID raw 후보 범위 안에 포함됨. **무해성·참조표 유효성·원본 identity 보존의 증거로 사용하지 않는다.**
- 구성원 Serialize 경계는 계속 **UNKNOWN**. 길이와 모든 비대상 바이트를 보존했으나 전체 참조표를 해석한 것은 아니다.
- 새 패치 테스트 **10/10 PASS**, 기존 관련 회귀 **6/6 PASS**. 검사 로그: `patch-tests.log`, `codec-regression.log`.

실제 코드: [prepare_patch.py](prepare_patch.py). 상세 차분·형상·색상 결과: [offline-result.json](offline-result.json). 원본 G1/G0-R/G0-A, 기존 codec API와 설치본은 수정하지 않았다.

## Stage B 실행 전 계획 — 승인 후 위 결과로 완료

현재 실행 중인 Type3와 미저장 문서는 이번 Stage A에서 조사하거나 조작하지 않았다. 승인 후 PID·창 제목·현재 문서 상태를 새로 확인한다. 기존 미저장 문서를 바꾸지 않는 **별도 빈 시험 문서**가 필요하다. 새 문서 명령이 저장 확인을 유발하면 저장·폐기를 선택하지 않는다. 필요 시 승인 범위 안에서 별도의 정상 Type3 인스턴스를 사용하고 시험 PID만 허용한다.

1. 원본 G1·후보·Version의 SHA를 다시 검증하고 대상 빈 문서를 확인한다.
2. 후보 Zone과 **G1 원본에서 복사한 Version**만 기존 codec 도구로 Clipboard에 등록한다. 이때 기존 Windows Clipboard 내용이 덮어써진다. 기존 업무 Clipboard를 덤프하거나 보관하지 않는다.
3. 시험 PID의 빈 문서에서 정상 **Ctrl+V 한 번만** 실행한다.
4. 그룹 선택 수 1, 작은 R1 Navy Blue, 큰 R2 Army Green, 두 형상·크기·좌표·그룹 유지 여부를 확인하고 화면을 보존한다. 원래 좌표에 배치됐는지도 구분한다.
5. 붙인 그룹만 Copy하여 TypeEditZone/Version을 캡처한다. 입력과 전체 SHA가 같을 것이라고 가정하지 않고, 차분·정규화 가능성·확인된 색상과 형상·그룹 상태를 별도로 기록한다.

기준 UI 크기: R1 80.024×60.053mm, R2 176.052×104.092mm. 그룹 416.124×104.092mm. 보다 정확한 bbox 값은 `offline-result.json`에 있다. palette 이름을 임의의 가공 의미로 해석하지 않는다.

Paste 오류·예상 밖 객체·색상 불일치·내부 경고가 나타나면 반복 Paste하지 않고 중단한다. 저장·문서 닫기·폐기·강제 종료·원본 시험 문서 편집은 승인 범위에서 제외한다. 실제 소유권을 일반화하거나 원본 선택·삭제·교체 기능을 추가하지 않는다.

## 오프라인 완료 당시 상태 — 실기 이전 이력

오프라인 완료 당시에는 실기 승인과 실제 색상 표시·그룹 선택 수·재Copy 검증이 대기 상태였다. `offline-result.json`과 루트 `preservation.json`은 그 시점의 기록이다. 최신 승인·실기·보존 결과는 위 Stage B 절 및 `runtime-001/runtime-result.json`, `runtime-001/preservation.json`을 따른다.
