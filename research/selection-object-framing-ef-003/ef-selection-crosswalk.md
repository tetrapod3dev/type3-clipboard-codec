# E/F local 구조와 선택 관계 대조

## 현재 구현 수준

| 구분 | 현재 근거 |
|---|---|
| Class descriptor 선언 | FFFF/schema/이름길이/이름이 맞는 scanner 후보. 실제 Archive 문맥은 CONDITIONAL |
| 기존 class reference | MFC80 계약은 확인, E/F의전역map/cursor 해석은 UNKNOWN |
| 새 object 생성 | E/F에서 검증된 WriteObject context 없음. 이벤트로 확정하지 않음 |
| 기존 object reference | 확인된 순차 이벤트 없음. 발견되지 않음을 부재로 판정하지 않음 |
| Serialize body | 조건부 base prefix와 첫문단 pre-slot/속성 일부만 설명 |
| 부모/자식 | 직렬화 포인터필드와UI그룹관계 연결 UNKNOWN |
| 최상위선택열거 | UNKNOWN,3/4정답 주입없음 |

## Local 연속 범위

첫 CZone descriptor 후보는 E/F 모두[70,81). 기존base walk는[81,219), container version[219,223)=3, helper count[223,227)=E2/F1을 재현한다. count가다르다는 사실은 구조변화 단서지만 직접 UI 멤버 수라고 할 수 없다. 기존003/002의계약을 확대하지 않았다.

처음 CParagraphe descriptor 후보는 E[375,392), F[995,1012)다. 이직후를local C origin으로 놓고, 기존code-derived walker가필드길이/버전/배열길이를검증하며 전진한다. 182상수에맞추거나slot을찾은뒤역산하지않았다.

| 항목 | E1 | F |
|---|---|---|
| C origin 가정 |392|1012|
| 기존walker가도출한CTxtPara P |574|1194|
| lines |1|1|
| char attribute count |4|4|
| 첫AttrChar |702|1322|
|4개204바이트v5empty slot 끝 |1518|2138|
| 전체CParagraphe body 끝 |UNKNOWN|UNKNOWN|

이와같이local상대기록을설명할수있어도Archive처음부터도달한cursor가아니다. slot끝후8바이트가0이어도null-object tag/absenceflag/padding중무엇인지판정하지않았다. 뒤쪽Type3객체body를강제로시작하지않는다.

## CParagraphe 뒤쪽에서 끊기는 이유

automation `research/_reverse_engineering/reports/phase2a_cparagraphe_serialize.md`의MaudeTxt RVA BCA0 경로:

- BD5A: this+AC의CTxtPara를직접virtual Serialize.
- BD6C: this+E8의optional CTxtPara, Native non-null 조건. 바이트만으로분기를선택할독립계약미확정.
- BD79/BD89/BD9F: raw DWORD/길이/가변buffer.
- BDB4: embedded CCube3D.
- BDC2: this+148이 가리키는내부객체의virtual Serialize, 실제타입/기록종료미확정.
- BDCD/BDDB: this+B0/B4 curve pointer의WriteObject 후보. 최신MFC80ordinal6303대응근거와합쳐볼수있으나실제E/Fcursor는미확정.
- BE16: 후속DWORD.

부모의실제호출과각필드끝을알기전에는다음CZone/CCourbe/CContour reference가어느byte부터인지정할수없다. CParagraphe load version/schema6과AttrPara4/AttrChar5는서로다른판별값이다. 옛보고서의MFC80미확보·ordinal미확정메모는역사적상태이며현재matched-MFC80근거가해당부분을보완한다. 이것이내부virtual대상/optional분기까지해결하지는않는다.

## 데이터 후보와원본관계

002의T1A/T2B코드와동일Contour raw4개는그대로참조했다. raw가같아도동일영속객체라는뜻은아니다. E1은UI Group(R,T1A)+L+T2B, F는4개독립이라는외부관찰만있다. R의사각형후보와2-record후보들을바로원본객체로명명하지않았다. 특히2-record가L인지문자내부기준선인지전체소유범위가없어UNKNOWN이다.

기존다중문자표본은그룹3개/비그룹3개/abc-cba/혼합색에관계없이scanner의CParagraphe descriptor1개만보인다. 첫CTxtPara문구는abc그룹에서abcdefg, cba그룹/비그룹표본에서XYZ로달라진다. 첫문구나첫descriptor가선택집합전체라는가설을지지하지않는다. 동일색2문자표본은서로다른내용이며동일문구2개대조군으로세지않았다.

따라서SelectionObjectHypothesis는비워뒀다. 새클래스범위를다른객체계열로확장하거나002출력에가짜Group/Member를붙이지않았다.
