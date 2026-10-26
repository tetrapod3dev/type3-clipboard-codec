# 선택 객체 조회를 위한 독립 증거 설계 005

최종 판정: **NEW_CAPTURE_NON_DISCRIMINATING**.

단일 권고: **A~E를 새로 캡처하도록 사용자에게 요청하지 않는다.** 현재 목적이 정확한 객체 경계·참조·소유권 확인이기 때문이다. 이 시험들은 선택 수 후보나 발생 기록의 작업 연관성을 추가 검증할 수 있지만, B1의 Archive 진입/map과 B2의 전체 Serialize 종료를 판별하지 못한다. 기존 반례를 반복하는 캡처를 정식 후속 과제로 만들지 않는다.

새로운 Producer 호출 근거를 확보할 수 있는 안전한 실행 경로도 이번에 확인한 것은 아니다. 따라서 EVIDENCE_ACQUISITION_PLAN_READY로 판정하지 않았다. 기존에 사용하지 않은 결정적 독립 근거도 발견하지 못해 EXISTING_EVIDENCE_SUFFICIENT_FOR_NEXT_ANALYSIS를 사용하지 않았다. 이후 Native 실험·부착 계획을 준비하거나 실행하지 않는다.

## 현재 기준선

V2 결과에서 F는 선택 수 후보4/HEURISTIC, Geometry occurrence4개, T1A/T2B record occurrence를 보인다. 정확한 최상위 객체 목록, Group/Member, 전체 Archive 길이와 객체 body는 UNKNOWN이다. 기존168 PASS는 당시 결과를 그대로 유지하며 이번 작업에서 테스트나 V2 CLI를 다시 실행하지 않았다. 008 Guard와 미완료009 안정화는 별도다.

보존한 V2 결과 SHA256: `8f374bdd8adbe88338434519e38314884d9edc0cb70cabcf7a3c9c788cd657ba`.

## 무엇이 추가로 필요한가

**B1:** 동일한 Archive에 대해 선행 primitive/font 기록의 실제 종료 cursor, 초기 class/object map 및 사전등록, 첫 호출이 WriteObject/SerializeClass/직접Serialize 중 무엇인지, 실제 TypeEditZone 게시 bytes와의 연결이 필요하다. 첫 descriptor가70/134에 있다는 관찰과 count 가설 일치로는 이를 대신할 수 없다.

**B2:** CParagraphe의 entry/return stream 위치와, 첫 CTxtPara 이후 optional secondary CTxtPara의 실제 분기, this+148 virtual Serialize의 타입·범위, curve reference 및 suffix의 기록 순서/끝이 필요하다. 첫 slot run 종료1518/2138은 paragraph 종료가 아니다.

**B3:** 이미 경계가 확인된 객체의 생성·참조와 owning field/container를 UI의 선택 단위·Group 구성원에 연결할 근거가 필요하다. UI는 정답 검사용이고, 그 숫자로 bytes를 강제 분할해서는 안 된다.

세부 보고서 `missing-evidence-matrix.md`, `existing-fixture-reuse.md`, `minimum-comparison-plan.md`, `decision-gates.md`에 기존 근거·시험 가치·합격/중단 조건을 나눴다. 실질적인 새 캡처를 채택하지 않아 `capture-preflight.md`는 작성하지 않았다.

## 마지막 질문에 대한 답

**“사용자가 선택한 실제 객체의 개별 경계를 알아내기 위해, 지금까지 없는 어떤 증거를 다음에 확보해야 하며, 그 증거를 얻는 최소 방법은 무엇인가?”**

먼저 필요한 것은 **실제 TypeEditZone bytes에 연결된 동일 Archive의 초기화→선행부→첫 object 호출을 설명하는 독립 Producer 근거**다. 다음으로 동일 실행의 CParagraphe 전체 body와 nested Serialize 범위가 필요하다. 가장 작은 증거 단위는 새 A~E binary 묶음이 아니라 **독립 문자 한 개를 Copy한 한 실행의 이 두 구간을 연결하는 기록 계약/검증 가능한 관찰 묶음**이다.

확보 수단은 정확한2009 빌드와 대응하는 제품 측 source/serializer 명세 또는 신뢰 가능한 호출·cursor 관찰 근거여야 한다. source와 설명이 있다면 당시 바이너리 identity 및 실제 캡처에 적용되는지 대조해야 한다. 실행 관찰이 필요하면 도구 적합성·과거예외 재발 위험·문서 보호·별도 명시적 승인이 먼저다. 현재 안전한 관찰 수단이 확보됐다고 주장하지 않는다. 한 문자 실행으로 Group 일반 소유권까지 증명되는 것도 아니다.

이번 작업은 **필요한 증거의 명세와 새 캡처 비권고 결정까지** 수행했다. TypeEdit/Clipboard/캡처 도구/Native/디버거 실행 없음. 원본·V2·생산 코드·Git 사용자 변경과 업무 모드OFF는 `preservation.json`으로 보존 확인했다.
