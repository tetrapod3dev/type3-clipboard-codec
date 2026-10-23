# E/F 객체 경계·Archive 참조 조사 003

최종 판정: **SELECTION_OBJECT_FRAMING_EF_BLOCKED**.

| 별도 필드 | 결과 |
|---|---|
| exact_top_level_enumeration | false |
| group_membership_verified | false |
| text_object_ownership_verified | false |
| complete_archive_extent_verified | false |
| production_change_allowed | false |

2026-10-24, 보존 파일과 기존 직렬화 근거만 조사했다. 새 Reader·Production 수정·Native 조사/실행·TypeEdit/Clipboard 접근은 없다. Archive 진입 문맥과 객체 끝을 확인하지 못한 중단 조건을 적용했다. `object-framing-reader.py`, `test_object_framing.py`는 **작성하지 않았다**. 002 후보 출력을 새 객체 목록으로 포장하지 않았다.

## 어디까지 확인됐는가

1. E/F의 class descriptor 후보 위치와 schema는 기존 scanner·정확한 MFC80 기록 계약에 부합한다. 그러나 descriptor 선언만으로 WriteObject 호출인지 SerializeClass인지, 어떤 객체가 생성됐는지 결정할 수 없다. 새 class와 새 object를 같은 이벤트로 세지 않는다.
2. 첫 CZone descriptor 후보의 끝 byte81에서 기존 base walker는 E/F 모두 byte219까지 138바이트 필드를 읽는다. 뒤의 container version3, helper count2/1도 기존 근거와 맞는다. **byte81이라는 local body 가정 아래의 base prefix**이며 객체 전체 body 종료가 아니다. helper count를 UI 자식 수로 승격하지 않았다.
3. 처음 발견된 CParagraphe descriptor 후보에서 기존 독립 pre-slot walker로 E1은 P574/첫AttrChar702, F는 P1194/첫AttrChar1322를 도출한다. 각각 count4의204바이트 v5 empty-layout record가 확인돼 첫 CTxtPara의 해당 속성 기록은 E1 byte1518/F byte2138까지 설명된다. 이는002의 slot 검색 결과와 독립적으로 맞지만 **CParagraphe의 끝이 아니다**.
4. 이후 optional CTxtPara, raw length/buffer, embedded cube, 타입이 미확정인 this+0x148 virtual Serialize, 두 curve WriteObject 및 suffix가 남는다. 이 경계 없이 다음 class/object tag cursor를 정할 수 없다. 폰트 선행부 및 map 초기화 계약도 미확정이다.

## 선행부·반례

제한된8개 입력(E1/F와 기존 다중 문자6개)에서 처음 descriptor까지의 길이는 `4 + 64*n + 2`와 맞는다. 첫 DWORD n은1 또는2이고, 마지막 WORD는 E1=3/F=4 및 그룹/비그룹 fixture의 기록된 선택 intent와 맞는다. 원문에서 폰트 이름으로 보이는 bytes도 존재한다. **폰트 테이블 + 선택 수라는 HEURISTIC 가설**일 뿐 producer 기록 순서로 증명하지 못했다.

특히 `text_two_objects_mixed_color_not_grouped`는 n2/descriptor134로, 다른 검토 표본의70과 다르다. offset70 고정 또는 geometry의6바이트 헤더 제거는 안전하지 않다. `CArchive`가 byte0에서 application primitive를 기록했는지와 최초 WriteObject가 어디서 시작하는지도 구분해야 한다. 첫 descriptor 위치는 Archive 생성 시작 위치가 아니다.

선택 순서가 바뀐 기존3문자 abc/cba 표본에서는 첫 문자 속성 run이 달라진다. Group/비Group 표본 모두 scanner상 CParagraphe descriptor는1개뿐이다. descriptor1개=문자객체1개 가설은 성립하지 않는다. 이번 범위에서 실제 동일 문구2객체/정확한2객체선택순서반전의 독립 캡처는 확립하지 못했으며,002의 동일문구 합성 입력을 실제 캡처로 사용하지 않았다.

## Archive Object / Data / Selection 분리

`object-reference-events.json`은 다음을 분리한다.

- **A Archive Object Evidence**: 확인된 생성/객체참조 이벤트 없음. byte0에서 UNSUPPORTED_RECORD로 중단, class/object 초기map UNKNOWN. 무진행 후 재시도하지 않는다.
- **B Data Occurrence Evidence**: 기존 descriptor 후보, 상대 base/pre-slot 필드의 새 대조, 선행부 관찰, 다중 문자 반례. local 후보를 전역 body 범위나 객체 ID로 승격하지 않는다. Contour/Text 기존 발생 근거는002 trace를 SHA와 함께 참조한다.
- **C Selection Object Hypothesis**: 빈 목록. UI의3/4를 주입하거나 문구·색상·형상 동일성으로 부모 관계를 만들지 않는다.

002에서 확인한4개 Contour raw 동일성과 T1A/T2B 존재는 유지된다. 하지만2-record Contour가 독립 L인지 문자 내부 보조 곡선인지 결정하는 전체 object/field 경계가 없으므로 일반 소유 관계는 UNKNOWN이다.

## 검증·보존

요청한 기존001/002/006/007 및 형상 관련 회귀 **134 PASS** 재확인(`regression.log`). 신규 Reader/Parser가 없어 새 Reader 테스트는 없다. 단순 회귀 통과를 framing 성공으로 세지 않았다. 003의8입력 대조는 기존 node scanner·base walker·pre-slot walker를 소유한 Python child에서15초 timeout으로 실행했고 정상 종료했다. 손상 입력은 기존134 회귀의 child 격리 검사를 재사용했다.

기존 Decoder/001출력·G1/H 경계/색상·중복문구/중복Contour·미지원거부·008 Guard가 유지된다. 전체 Suite는 실행하지 않았다. 008의17개 역사적+4개 신규 실패는 별도 유지하며009를 수행하지 않았다. 기존 파일 SHA와 양쪽 Git 상태/업무 모드OFF 보존은 `preservation.json`에 기록했다. Git commit/reset/checkout/clean/push 없음.

## 마지막 질문

**“E/F에 기록된 문자와 Contour가 실제 TypeEdit 객체로 조직되는 경계를 어디까지 확인할 수 있으며, 사용자가 선택한 객체의 수와 Group 관계를 데이터만으로 재구성할 수 있는가?”**

일부 local base/문자 속성 기록의 상대 범위까지 확인할 수 있다. **최상위3/4개와 Group(R,T1A) 관계를 데이터만으로 재구성할 근거는 현재 없다.** 필요한 독립 증거는 두 가지다: (1) font/application 선행부의 실제 기록·종료 계약과 첫 object 호출 전 map 상태 및 WriteObject/SerializeClass 구분, (2) CParagraphe의 optional secondary CTxtPara 및 this+0x148 호출을 포함한 후속 Serialize가 끝나는 조건과 필드별 기록 순서. 이 둘 중 하나만 확인돼도 전체 경로가 완성되지는 않는다.

이를 얻기 위한 TypeEdit 시험이나 새 역공학을 시작하지 않고 여기서 종료한다.
