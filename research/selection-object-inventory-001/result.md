# Selection Object Inventory 001

최종 판정: **SELECTION_INVENTORY_PARTIAL**. 2026-10-24. 파일 전용 읽기 도구를 구현했다. 독립 객체 전체 목록을 해독했다고 선언하지 않는다.

## 실제 구현

`selection_inventory.py`는 저장된 TypeEditZone 바이너리를 입력받아 기존 Decoder API와 원본 006/007 Reader/비교 함수를 호출한다. 새로운 Contour/Text/Archive Parser나 ObjectDetector를 만들지 않았다. 기존 public API/Parser 등록/색상 ranking은 변경하지 않았다. JSON과 표 출력, SHA256, chain별 형상 후보·기록·bbox·문자 후보·색상 후보, 원본 Contour 범위 및 조건부 순차 경계 대조를 제공한다.

출력의 `candidates`는 **Decoder chain 후보**다. 실제 최상위 선택 객체가 아니다. `complete_inventory=false`, `top_level_selection_count.value=null`, `group_hierarchy.value=null`, `parent_group.value=null`, `change_allowed=false`를 유지한다. 선택 수를 알 수 없을 때 후보 수로 채우지 않는다. Archive tree는 직렬화 관계이며 UI 그룹 계층으로 반환하지 않는다. index/Archive ID는 영속 Object ID가 아니다.

## 실행

Codec 저장소 루트에서:

```powershell
./.venv/Scripts/python.exe -B research/selection-object-inventory-001/selection_inventory.py --input research/group-color/type3-clipboard-member-color-003/samples/G1/typeeditzone.bin --format table
./.venv/Scripts/python.exe -B research/selection-object-inventory-001/selection_inventory.py --input saved-typeeditzone.bin --format json --output new-inventory.json
```

실제 입력은 binary다. 기존 hex fixture는 재현 코드에서 기존 `hex_to_bytes`로 변환한다. CLI는 Clipboard adapter를 생성하지 않는다. `--output`은 기존 파일을 덮어쓰지 않는다. PARTIAL 보고서 생성 exit0, UNSUPPORTED exit2이며 exit0을 완전한 목록 성공으로 해석하지 않는다. 기본 timeout8초, 입력 상한16MiB는 도구의 자원 정책이지 Archive 형식 제한이 아니다.

향후 별도 캡처 adapter가 저장한 bytes를 `analyze_bytes(data, timeout=...)`로 전달할 수 있다. 현재 실시간 Clipboard 기능은 없다. Version은 해석하지 않는다.

## 보존 표본 결과

| 표본 | 외부 관찰/자료 | Decoder chain | 도구의 정확한 최상위 개수 | 조회 범위 |
|---|---|---:|---|---|
| default_rectangle | 기존 fixture 설명, 독립 UI 개수 재확인 없음 |1|UNKNOWN|rectangle 후보,4기록,bbox,Black 후보 |
| polyline_3/5 | README의 단일 캡처 intent와 좌표 설명; 저장 순서 미확정 |각1|UNKNOWN|3/5기록과 순차36바이트 범위 재현 |
| polygon_5/6 | README의 UI start point 및 geometry intent; stored order 미확정 |각1|UNKNOWN|5/6기록, polygon 후보 |
| default_circle | 기존 fixture 설명, 독립 UI 개수 재확인 없음 |1|UNKNOWN|8기록,circle 후보; 일반 원 판정 보장 아님 |
| default_text | README intent `abcdefg`/Arial, 단독 문자 설명 |1|UNKNOWN|`abcdefg` payload/chain 후보. chain의 polyline 분류를 문자 객체 종류로 해석하지 않음 |
| G1 | UI Group1, 구성원 사각형2 |2|UNKNOWN|두 bbox/색상은 보존 UI 표시와 일치. 그룹 소유 경계 UNKNOWN |
| H1 | 그룹 생성·단일 handle 관찰, 구성원2; 독립 Native count 아님 |2|UNKNOWN|55x35 at(600,200),30x20 at(450,200) 및 색상 대조 |
| E1 | UI 최상위3, 총 구성원4 |4|UNKNOWN|T1A/T2B chain 후보 존재. geometry와 text의 올바른 귀속은 미확정 |
| F | UI 최상위4, 총 구성원4 |1|UNKNOWN|T1A만 노출; T2B 및 전체 객체 목록 누락 |

`inventory-results.json`의 `external_validation_only`는 과거 UI 관찰을 별도 첨부한 것이다. 그 값을 analyzer가 추론한 결과처럼 주입하지 않는다. `count_comparison`에서 UI 수·chain 수·후보 수·정확한 최상위 개수를 분리했다. Archive descriptor 개수는 객체 수로 사용하지 않았다.

G1은 사각형 UI 폭/높이/중심 표시값과0.001mm 범위에서 대조했다(기존 UI 표시의 반올림 대조 허용오차이지 CNC 정밀도 계약 아님). H1은 보존된 수치 입력·관찰의 bbox와1e-6mm 범위 대조했다. 각 색상 후보도 기록과 일치한다. 그러나 shared Property 후보 창과 일반 ownership UNKNOWN은 계속 표시한다. 상관관계 관찰을 범용 소유권 증명으로 올리지 않는다.

## 검증

- 신규 Inventory + 원본 007 검사: 최초64 PASS.
- 독립 G/H UI 대조 검사 추가 후 신규 Inventory, 원본006/007, 기존 원/사각형색상/그룹/혼합색상/구조 검사: **114 PASS**, `regression.log`.
- 11개 보존 입력,10개 합성 입력을 재현. 모든 재현 입력 timeout0. 강제 timeout 분기 테스트는 별도이며 자신이 생성한 Python child 하나만 종료하고 성공 후보를 반환하지 않았다.
- 007의8개 Decoder fingerprint와 일치하고, 모델 정규화 전후 fingerprint도 동일하다.
- 손상 count/stride·잘린 Property/suffix·미등록 reference/schema는 007의 known-prefix 정책을 유지하여 Decoder 진입 전 UNSUPPORTED. 임의 비지원 prefix도 Decoder가 필요하면 격리 child에서만 실행한다.
- 중복 Contour2개는 합치지 않고 AMBIGUOUS, tail제거 입력도 유효 Archive 종료 UNKNOWN.
- 전체 Suite는 이번에 재실행하지 않았다. 기존008의1465 PASS/21 FAIL(종전17+신규4), 소스 고정 lock 문제는 해결/변경했다고 주장하지 않는다. 009 수행 없음. 관련114 PASS가 전체 Suite 정상화를 의미하지 않는다.

모든 Decoder 실행은 실제 base Python interpreter의 독립 child로 제한했다. timeout 시 해당 Popen handle의 child만 kill한다. TypeEdit·프로세스 검색·Clipboard·GUI·Native 호출은 없다. isolation은 의미 정확성/모든 손상 입력 안전성 증명이 아니라 시간 제한이다.

원본 E1/F는 automation 프로젝트에서 읽어 신규 `samples/E1.bin`, `samples/F.bin`에 동일 SHA로 복사했다. 일반 CLI는 automation 저장소에 의존하지 않는다. 원본/기존fixture/Decoder/Encoder/frozen baseline/G1/H/008·009는 변경하지 않았다. 세부 SHA와 Git 상태는 `preservation.json` 참조.

## 마지막 질문

**현재 TypeEdit에서 사용자가 Copy한 선택 집합을 어떤 객체들로 구성되어 있다고 정확히 설명할 수 있는가?**

지원 표본의 Contour 후보·기록·좌표·bbox와 일부 문자/색상 후보를 근거와 함께 설명할 수 있다. G1/H의 두 사각형은 보존 UI 값과 대조됐다. 그러나 임의 Copy의 정확한 최상위 객체 수, 독립 문자 객체별 귀속, 혼합 그룹 부모/자식, layer/CAM, 전체 유효 Archive 범위는 설명하지 못한다. 특히 F의4객체를 현재 Decoder가1chain으로 읽으므로 **완전한 선택 객체 목록 기능은 아직 아니다**.

다음 최소 증거는 새 실기보다 이미 보존된 E/F에서 독립 문자2개와 형상·최상위 단위의 연결을 설명할 수 있는 읽기 계약이다. 추가 캡처나 TypeEdit 시험을 자동 시작하지 않는다. 회전·이동·Group 생성·Nesting·Paste·쓰기 API는 없다.
