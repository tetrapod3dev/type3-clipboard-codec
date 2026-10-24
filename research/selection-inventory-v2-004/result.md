# Selection Inventory V2 004

최종 판정: **SELECTION_INVENTORY_V2_VERIFIED_LIMITED**. 보존 표본에서 발생 기록을 조회하는 연구 도구의 검증이며, 실제 최상위 객체 열거 성공이 아니다. 2026-10-24.

| 별도 판정 | 결과 |
|---|---|
| count_candidate_status | COUNT_CANDIDATE_CONDITIONAL |
| exact_top_level_enumeration | false |
| group_membership_verified | false |
| complete_inventory | false |
| production_change_allowed | false |

## 실제 기능

`selection_inventory_v2.py`를 추가했다. 저장된 TypeEditZone binary만 읽으며, 기본은 UTF-8 콘솔 출력이다. JSON과 한국어 표를 제공하고 `--output`을 명시한 경우에만 새 파일을 쓴다. 기존 출력 경로 덮어쓰기는 거부한다.

```powershell
./.venv/Scripts/python.exe -B research/selection-inventory-v2-004/selection_inventory_v2.py --input research/selection-object-inventory-001/samples/F.bin --format table
./.venv/Scripts/python.exe -B research/selection-inventory-v2-004/selection_inventory_v2.py --input saved-typeeditzone.bin --format json --output new-v2.json
```

`analyze_bytes(data, timeout=15)`로 입력 경계를 분리했다. 현재 TypeEdit/Clipboard/GUI 연결은 없다. Version은 해석하지 않는다. PARTIAL exit0은 발생 기록 보고서 생성 성공이며, 완전한 객체 목록을 의미하지 않는다. UNSUPPORTED exit2는 원본 객체 부재가 아니다.

재사용: 001의 `_decode_worker`와 출력 정규화, 002의 원본 `_worker` 및 그 안에서 쓰는 기존 slot/run helpers, 기존 record reader/bbox/classifier, 006/007 경계 대조. 새 Archive Reader나 Production dispatch는 없다. 기존001/002/003 파일도 변경하지 않았다.

002의 CParagraphe 추가 probe는 **검증된 E1/F 전체 SHA 두 건에만** 재사용한다. 다른 입력과 같은 문구 합성 입력에는 적용하지 않는다. 새 CParagraphe 창을 무차별 탐색하도록 일반화하지 않았다. 일반 문자 발생 조회는 002가 이미 사용하는 slot reader·record-to-run·layout validator를 호출한다.

## 001보다 추가되는 정보

| 표본 | 선택 수 후보 | Geometry occurrences | Text occurrences | 의미 |
|---|---:|---:|---:|---|
| E1 |3|4|2|기존 chain4개와 T1A/T2B 기록을 분리 |
| F |4|4|2|기존 chain1개 + 검증된 연구 probe3개, T2B도 별도 노출 |
| G1/H1 |각1|각2|0|기존 bbox·색상·경계 후보 유지 |
| 단독 Text |1|1|1|geometry 보조 contour와 text record는 같은 독립 객체 수가 아님 |
| 그룹3문자 abc |1|3|3|그룹 소유권은 UNKNOWN, 후보 count로 분할하지 않음 |
| 비그룹3문자 |3|3|3|같은3개 발생 수가 선택 count 증명은 아님 |
| 다른폰트2문자 표본 |2|2|2|n2, 계산한 count 위치132/descriptor134 |

F의 T1A record window는[1322,2138), T2B는[4138,4954)다. char DWORD와 record 길이·기존 v5 layout 검사 결과를 표시한다. 기존 chain에 같은 문자열이 노출됐는지도 보여주지만, 같은 내용이라는 사실을 occurrence-to-object 귀속으로 승격하지 않는다. F의 T2B는 legacy chain 노출 없음으로 표시된다.

Geometry에는 원본 byte 범위/SHA, 기록 수·좌표·bbox·형상·색상 후보와 출처를 둔다. 추가 probe의 색상은 새로 추정하지 않는다. 각 발생 ID는 그 캡처의 표시 ID이며 TypeEdit 영속 ID가 아니다. 서로 다른 위치의 동일 raw Contour는 유지한다. 같은 문구가 두 위치에 있으면 별도 text occurrence를 남긴다. 같은 물리 byte window가 helper에서 중복 반환되는 경우에만 관찰 중복을 제거한다.

## 개수 후보 검증

추가 독립 UI 검증은 **10캡처 / 고유 Zone SHA8개**다. S1/S2 단독, U0 두 선택, G0 계열 그룹, G1/H0/H1 그룹의 보존 UI 기록과 후보가 일치했다. E1/F는 이전003에서 이미 검토한 통제군으로 분리했다. UI 없는 기본 도형·문자 fixture는 탐색에는 사용하되 정답 일치 통계에는 넣지 않았다.

추가 문자 intent에는 grouped이면서 `selected/copied object count: 3`인 문서가 있다. 이는 구성원 수/최상위 선택 수의 범위가 불분명하다. 예를 들어 font_arial_bold 그룹 표본의 literal3과 candidate1을 숨기지 않고 evidence에 원문으로 기록했으며, 독립 UI 정답으로 세거나1로 보정하지 않았다. 새 독립 증거가 geometry n0 계열에 집중돼 있어 전체 가설을 CORROBORATED나 VERIFIED로 올리지 않았다.

자세한 적용 범위·비적용·반례 취급은 `selection-count-candidate.md`와 `selection-count-evidence.json` 참조. count는 요약 후보로만 사용하며 object 분할이나 Decoder loop 횟수로 사용하지 않는다. 테스트에서 후보를30000으로 바꿔도 발생 수2개가 유지됐다.

## 검증 및 제한

- 보존 표본 **28개**, 합성 입력 **11개** 재현, timeout0: `v2-sample-results.json`, `replay.log`.
- 신규34검사 + 기존134회귀 = **168 PASS**, `regression.log`.
- F 문자2개 노출, E/F Contour raw 대응, G1/H 값·경계 보존, 다른 위치의 동일 문구/형상 유지, 미지원 구조 거부, 개수 반증 보고 경로, count-loop 독립성, 파일 덮어쓰기 거부 및 한국어 CLI 출력 검증.
- 기존001 fingerprint11개와 같고, 기존134에는001/002 출력 불변 검사가 포함된다. 각 V2 결과에도 legacy fingerprint를 보존했다.
- 전체 Suite는 이번에 실행하지 않았다. 008의17개 역사적 실패 +4개 추가 실패는 별도 유지하며009를 수행하지 않았다. 관련168 PASS가 전체 Suite 정상화를 의미하지 않는다.

모든 Decoder/probe 실행은 직접 소유한 base-Python child 안에서만 수행한다. 기본15초, 입력1MiB, 각 종류 발생 기록256개, 각 종류 기록 총4096개, JSON8MiB 상한이다. 초과/timeout 시 부분 성공을 반환하지 않는다. 강제 timeout 검사에서만 자신의 child handle을 종료했다. 이는 OS 메모리 sandbox나 포맷 정확성의 증명은 아니다.

최초 표 출력에서 cp949가 긴 대시를 인코딩하지 못한 문제를 확인해 CLI를 명시적 UTF-8 출력으로 고쳤다. 실제 CLI subprocess 검사가 통과했다. 기존 Decoder/Encoder/fixture/frozen baseline/008/009/원본 증거는 변경하지 않았다. TypeEdit·Clipboard·Native 접근 없음, 업무 모드 OFF 유지. 세부 SHA는 `preservation.json` 참조.

## 마지막 질문

1. **기존 캡처에서 선택 수 후보를 읽을 수 있는가?** 검토된 preamble 계열에서 읽을 수 있다. 정확한 선택 수는 계속 UNKNOWN이다.
2. **어디에 적용할 수 없는가?** 계산 위치에 검토된 CZone descriptor가 없거나, 잘린/과도한 n/알 수 없는 prefix는 후보 없음이다. 새 문자 intent만으로는 값 검증을 할 수 없다. arbitrary class/version/선행부에는 일반화하지 않는다.
3. **001 대비 추가 정보는?** F에서 누락되던 T2B와3개의 연구 Contour, 모든 발견된 slot record window·char DWORD·layout 검사·중복 발생을 따로 조회한다.
4. **실제 객체별 조회의 차단 조건은?** Archive 초기 map/진입, 전체 object Serialize 종료, 문자·Contour 소유 관계와 그룹 경계, 영속 원본 재대응이다.
5. **현재 자료만으로 더 개선하기 어려운가?** 발생 기록 표시·독립 검증 자료 정리는 더 가능하지만, 정확한 객체별 열거로 나아가는 구조적 근거는 여전히 부족하다. 같은 정적 분석을 반복하지 않고 필요한 독립 증거를 `remaining-blockers.md`에 기록한 뒤 종료한다.
