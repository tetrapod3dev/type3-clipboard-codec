# 최소 비교쌍 판단

**현재 채택한 새 수동 비교쌍: 없음. 승인 요청: 없음.** 아래는 A~E의 가설 판별력 평가이며 실행 지시나 승인 대기 상태가 아니다.

| 비교 | 판별할 수 있는 좁은 가설 | 핵심경계에 대한 판정 |
|---|---|---|
| A vs B | 각단독선택에어떤geometry/text발생이동반되는지 | B1/B2에는NON_DISCRIMINATING. B3의operation연관성만부분확인하며기존단독text자료로유사반례확보 |
| B vs C | R을추가선택했을때발생기록/선행count후보가달라지는지 | B1/B2/전체B3에는NON_DISCRIMINATING. byte증분은두번째객체의완전body길이가아님 |
| C vs D | 같은구성원2개에서최상위선택2→group1로변할때count/기록변화 | 가장작은후보2캡처쌍이나,다른map/재생성/메타데이터설명과구분불가. 전체객체경계시험으로채택하지않음 |
| C vs E | attempted순서에따른byte순서/등록변화 | stored순서가반드시selection순서라는가설은반박가능. cursor/map없이class재사용과object생성을구별하지못함 |

## 채택하지 않은 C/D 쌍의 판정 범위

외부UI에서C의top-level2/D의group1과구성원2를독립적으로확인했을경우에만count후보2/1을비교할수있다. 후보가다르면그표본의count가설은CONTRADICTED이며값을보정하지않는다. 후보가같고구성원발생기록이대응돼도count의실제producer의미·Group목록경계·class/objectmap·문자body끝은UNKNOWN이다.

C와D의diff범위가여러가설에서동일하게나올수있으므로“diff최소span=추가container”혹은“3/4객체정답에맞춘분할”을합격기준으로삼을수없다. GUID/동적메타데이터와Group재생성효과를제외할독립계약도없다. 이계획은효율상보류이지TypeEdit에서기능이영구불가능하다는판정이아니다.

## 지금 필요한 최소 독립 증거 묶음

새 binary2개 대신 먼저 **단독 editable Text 한 개의한정된Copy한실행**에대해아래연결을보여주는증거가필요하다. 이는획득해야할내용의명세이며,현재실행가능한관찰수단을설계완료했다는뜻이아니다.

1. 정확한2009 binary identity와대상시험문서·단일text선택의독립UI기록.
2. 동일Archive를구분할run-local증거토큰과stream-origin/단위. 이토큰은원본객체ID나공개Nativepointer가아님.
3. Archive초기화·사전MapObject/SerializeClass상태와선행primitive/font 기록전후cursor.
4. 최초WriteObject인지SerializeClass/직접Serialize인지확정하는caller/callee·class/schema·map변경순서.
5. 동일실행CParagraphe entry/return cursor와secondary CTxtPara분기, this+148타입·nestedcall전후cursor, curve기록·suffix까지의범위.
6. 생성buffer가실제TypeEditZone원본bytes로게시됐다는연결과SHA/길이. 다른Archive호출이나Copy미완료관찰은채택하지않음.

처음에는3~4의B1구간을확보할수있는지부터평가해야한다. 이구간만있으면B1일부만진전이며B2/Group소유권은남는다. 모든항목을한번의관찰에서쉽게얻을수있다고보장하지않는다.

동일빌드의제품source/serializer명세·검증가능한기존기록이제공된다면실행없이대조할수있다. 실행관찰만가능하다면과거LLDB예외UNKNOWN사건의재발위험·도구적합성과안전한시험분리/종료조건을별도검토하고사용자의새명시적승인을받아야한다. 이번에는breakpoint·부착·Probe·Hook·직접호출·실행스크립트를준비하지않았다. 차단된Pltf정적검색을반복하지않는다.
