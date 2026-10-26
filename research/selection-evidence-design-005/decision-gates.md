# 후속 증거 채택 Gate

이번 단계는설계검토만완료했다. 아래조건은향후증거를평가하는기준이며,통과했다고기록한항목은없다.

| Gate | 합격 기준 | 실패·UNKNOWN 처리 |
|---|---|---|
| G0 출처/무결성 | 정확한빌드·독립UI상태·원본두포맷·시각·파일SHA·충돌없는출력경로;같은실행의buffer연결 | 캡처시각·UI대응불명/파일충돌/다른Archive면채택중단 |
| G1 선택수 | top-level수와구성원수를독립UI로별도기록;count후보는검증대상 | intent의object_count/Decoder chain을정답으로대체하지않음;불일치반증보존 |
| G2 object시작/map | 기록순서와동일Archive의실제class/object등록·참조,검증된cursor로시작과다음cursor재현 | FFFF/800x패턴·문자열검색·고정offset만으로통과불가 |
| G3 text body종료 | first/optionalCTxtPara·내부virtual대상·curve/suffix를빠짐없이따라가반환cursor재현 | 미확정영역을0바이트/padding으로건너뛰지않음;secondary분기가관찰되지않으면그범위UNKNOWN |
| G4 소유권 | owningfield/container경로로독립도형과문자보조Contour구분 | 동일raw/내용/색상으로identity나부모관계부여하지않음 |
| G5 Group/최상위 | G2~G4의구조에서UI개수를주입하지않고구성원·Group·top-level을재구성하고외부관찰과대조 | 2개구성원이보인다는이유로그룹1개성공이라고하지않음 |
| G6 회귀/적용 | 기존V2기준선·지원범위·중복/미지원·시간상한및008보존,해당새기능만검증 | 168개과거PASS를새framing성공으로계산하지않음;009와혼합금지 |

## 반증과 성공의 한계

- count후보실패는count가설을기각한다. 곧바로캡처손실·전체Parser오류·TypeEdit객체부재의증명은아니다.
- 순서반전후bytes가같아도선택순서무관저장·정규화·cache등을구분할추가근거가없으면UNKNOWN이다. 다르더라도각object의범위는확정되지않는다.
- Group전후원본속성이같아보여도Nativeidentity·소유권·CAM참조의불변을보증하지않는다.
- 단독문자에서Contour발견은동반데이터의증거다. 그Contour의정확한역할과다른문자에서의동일구조는별도다.
- B1만통과하면B2/B3는그대로남으며,모든경계조건이연결되지않으면exact_top_level_enumeration은UNKNOWN/false로유지한다.

## 현재 승인·실행 상태

새캡처선정없음,수동시험실행안없음,capture-preflight없음. TypeEdit실행·창/프로세스확인·Copy·Clipboard읽기·그룹변경·도구실행·디버거·Native·문서저장/종료모두미실행이다. 이문서로어떤추가동작도승인되지않는다. 추가승인을요청하지않고결과보고후종료한다.
