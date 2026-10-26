# B1/B2/B3 증거 부족 분류

| 차단 조건 | 이미 확보 | 아직 없는 증거 | 새 수동 캡처로 판별 가능 | 캡처만으로 판별 불가 | 필요한 Producer/실제 호출 근거 |
|---|---|---|---|---|---|
| B1 선행부/진입 | `4+64*n+2` 관찰,70/134 descriptor 후보, MFC80 저장계약, 과거 geometry Archive+6/nullmap 한 건 | E/F font/application 종료의 실제 기록 계약, 초기/선행 map, 첫 호출형태, 게시bytes 연결 | font/선택/그룹 조건 변경과 선행 bytes의 상관관계·반례 | 같은 class descriptor를 만든 WriteObject/SerializeClass/직접호출의 구분, 내부 map 상태 | 동일 Archive instance의 초기화/사전등록 및 선행부 write 구간→첫object호출; 결과 buffer가 TypeEditZone임의 연결 |
| B2 CParagraphe 종료 | base와pre-slot 상대walk, AttrChar v5/빈 extension, optional/내부호출의 기존 명령순서표 | secondary CTxtPara 분기·내용, this+148 동적serializer 타입/길이, 후속curve/suffix 도달·반환cursor | text내용/줄수/폰트 변경과 local record의 변화·귀속 가설 반박 | 어느 변화가body끝인지,변하지 않은메타데이터/optional영역의 의미,내부virtual호출 종료 | CParagraphe entry/return cursor와 각 nested call의 before/after, 실제분기 및타입·callee근거 |
| B3 선택/Group 소유 | E/F UI3/4·구성원4, G1/H UIgroup1·사각형2, V2발생기록,다중text intent | 실제 Archive객체와UI단위연결,문자보조Contour vs독립도형,owningfield/container | 명시적으로 선택한 집합에 어떤 occurrence가 함께 나타나는지,최상위와구성원 수 기록 | 실제부모·중복참조·영속identity·전체객체경계; 같은내용/같은raw로는불가 | B1/B2에서검증한object event와field/container소유관계를독립UI관찰에대조 |

## 판별력의 경계

- 실제 수동 선택/Group 기록은 외부 ground truth를 강화한다. 단독 Text에서 Contour가 관찰되면 “Contour 하나=독립 도형 하나”를 반박할 수 있다. 이 반례는 기존 단독문자/혼합 표본에도 있어 새로 요구할 필요가 없다.
- 같은 bytes에 대해 class 정의 기록과 object 생성은 다른 사건이다. WriteClass 기록은 WriteObject 안에서도 별도 SerializeClass 경로에서도 가능하다. map 등록·object body 경계 없이 descriptor와diff만으로 두 경로를 선택할 수 없다.
- 선택/Group 작업은 GUID·참조등록·정렬순서·캐시·메타데이터를 함께 바꿀 수 있다. diff 시작/종료가곧해당객체의body라는규칙은사용하지않는다. 변화가없어도알지못하는공통영역이정당화되지는않는다.
- 같은 상태의 반복 Copy가 같으면 그 표본의 재현성을 지지할 뿐 모든 volatile 영역·padding·전체 Archive 종료를 증명하지 않는다. 변한다면 “차이 전부 GUID라 무해”라고 마스킹하지 않는다.

## 재사용 근거

004 remaining-blockers/result/count-evidence,003 archive-entry-contract/ef-selection-crosswalk,002 ef-parser-trace, 기존 archive-producer-crosswalk-005 result를 출발점으로 사용했다. 이 문서는 해당serializer나보호코드를재분석한결과가아니다. source 위치와SHA는existing-fixture-reuse 및preservation에있다.
