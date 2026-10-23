# E/F Archive 진입 계약

## 기존 MFC80 근거

`research/archive-crosswalk-001/result.md` 및 native-evidence.json: 정확한 MFC80 SHA `8204dbcc054c1e54b6065bacb78c55716681ad91759e25111b4e4797e51d0aa3`, MapObject2875F, WriteObject28562, WriteClass28882, RuntimeClass::Store27C14, ReadObject285F3, ReadClass28927. 클래스와 객체가 같은 Archive-local 등록 counter를 공유하고 서로 다른 등록 단계를 가진다. null/object reference/class reference/새class/확장tag 분기를 구분한다. 이 계약 자체를 다시 역공학하거나 DLL을 로드하지 않았다.

WriteObject이면 WriteClass→object map 등록→virtual Serialize 순서다. SerializeClass 또는 직접 Serialize가 혼합되면 보이는 descriptor가 같아도 counter 진행과 객체 의미는 달라진다. null MapObject 초기화/선행 non-null 매핑을 모르면 class ID1/object ID2를 보장할 수 없다. Archive ID는 원본 문서 영속 ID가 아니다.

## 실제 선행부 관찰

E/F는 `010000004859`, G1/H는 `000000000100`로 시작한다. 기존006/007의geometry prefix 조건을 넓히지 않았다. 아래 값은 이미 알려진 descriptor 후보 앞부분에서 관찰한 값이며, 해당 식으로 동적으로 다음 cursor를 생성하지 않았다.

| 입력 | 첫 DWORD n | 첫 descriptor 후보 | 앞부분 마지막 WORD | 외부 intent |
|---|---:|---:|---:|---|
| E1 |1|70|3|Group(R,T1A),L,T2B |
| F |1|70|4|R,T1A,L,T2B |
| text_three_objects_grouped_order_abc |1|70|1|그룹3문자 |
| text_three_objects_not_grouped |1|70|3|독립3문자 |
| text_three_objects_grouped_order_cba |1|70|1|그룹3문자, 선택순서반전 |
| text_two_objects_same_color_not_grouped |1|70|2|독립2문자, 같은색 |
| text_two_objects_mixed_color_not_grouped |2|134|2|독립2문자, 다른색 |
| text_three_objects_grouped_order_abc_mixed_color |1|70|1|그룹3문자, 혼합색 |

`4 + 64*n + 2`는 이8개에서 맞는 관찰식이다. n을 폰트 수,64바이트를 font entry,마지막WORD를 선택 수로 해석하는 것은 HEURISTIC이다. source producer의 실제 count/문자열 기록 폭·초기화/종료·map 변경 여부가 미확정이다. raw prefix와 표본 SHA는 object-reference-events.json에 있다. userUI3/4와 일치해도 이를 분할 입력으로 사용하지 않았다.

## 생산자 근거의 한계

`research/archive-producer-crosswalk-005/result.md`: 과거 Pltf runtime에서 Archive 생성→CTxtFonts::BeginSave/Save→대상 virtual Serialize→EndSave 후보 관계가 관찰됐지만 디스크 명령이 runtime과 달라 직접 정적 연결이 BLOCKED다. Copy 완료/TypeEditZone publication도 UNKNOWN. geometry 시험에서 첫 WriteObject 전6바이트/null map 관찰은 해당1건에 한정되며 E/F의font 선행부/map 상태를 증명하지 않는다.

따라서 byte70은 “처음 관찰한 CZone descriptor 후보”일 뿐, 최초 Archive object 시작으로 승인되지 않았다. 후보 선언 종료byte81에서 local base 필드를 확인할 수 있어도 전역map과WriteObject 문맥을 소급 증명하지 못한다. 기존 scanner는 class name이 재사용되는 추가 객체의 reference를 해석하지 못한다. 새descriptor가 없다는 이유로 새객체가 없다고 보지 않는다.

## 명시적인 거부

A의순차 event stream은 byte0에서 UNSUPPORTED_RECORD로 끝난다. 초기WORD1을object reference1로 해석하지 않고,0x8001같은후속값도 검증된cursor/map 없이 CLASS_REFERENCE로 승격하지 않는다. 문자열 검색·header 건너뛰기·offset 고정·임의 map reset·resynchronization은 하지 않았다. next_cursor0과halted=true는 실패종료 기록이며 같은상태에서 반복하지 않는다.
