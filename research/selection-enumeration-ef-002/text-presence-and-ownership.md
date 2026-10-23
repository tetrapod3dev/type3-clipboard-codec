# 문자 데이터 존재와 소유권

## 구조화된 문자 근거

기존 `read_slot_record_runs_from_blob()`의204바이트run추출과 `records_to_text_run()`을 그대로 재사용했다. 새ASCII/UTF문자열검색으로동기화하지않았다. 반환된record전체bytes를원본에서대조해window를표시한다. 여러동일rawwindow가있으면모두표시하고assignment는AMBIGUOUS로남긴다. window는문자객체의전체Serializeextent가아니다.

| 내용 | E1 record window | F record window | char DWORDs |204바이트record수|
|---|---|---|---|---:|
|T1A|[702,1518)|[1322,2138)|84,49,65,0|4|
|T2B|[4286,5102)|[4138,4954)|84,50,66,0|4|

각record의+4 DWORD가문자코드후보다. 예를들어F T2B의코드필드는[4142,4146),[4346,4350),[4550,4554),[4754,4758)이다. 연속ASCII T2B문자열을찾은것이아니다. 기존 `text_slot_candidate._validate_current_empty_slot_layout`로각204바이트window의v5/emptyextension조건을검사했고각run의4record모두rejection=None이다. 레코드패턴·코드·UI문구의교차근거가있지만Archive선행cursor/전체paragraph경계/ownership은미확정이므로출력신뢰는HEURISTIC으로보수적으로유지했다.

## 어디서 누락되는가

`extract_text_runs()`가E1과F모두T1A,T2B를반환한다. E1은첫CParagraphe창에서T1A,이후payloadconcatfallback으로T2B까지얻는다. F는마지막CParagraphe후보창자체에두run이있어서모두얻는다. 이차이는추출실패가아니다.

F의chain1개에대해 `attach_text_runs_to_chains`는 `len(runs)==1 or len(chains)==1`을참으로판정한다. 첫runT1A만chain0에대입하고,여러run이면provisionalnote만더한후line192에서반환한다. 두번째run은누락된다. `TextPipelineResult.text_content`도항상text_runs[0]이라T2B를구제하지않는다.

E1의chain4개는폭/중심좌표와문자길이정렬후zip으로run을배정한다. trace에서사각형Contour[2890,3034)에T1A,다른2recordContour[3616,3688)에T2B가배정된다. 이배정은UI의독립문자객체범위를증명하지않으며,문구존재와소유권을분리해야한다.

## 중복과 경계

기존extract_text_runs는내용이같으면run을중복제거한다. 같은T1A를두곳에둔메모리합성입력에서추출run목록1개와원본slotwindow발견2개가동시에성립함을검사했다. 이를실제객체1개나2개로확정하지않는다. 이문제는같은문구를다루는일반열거의추가제약이며,내용이다른E/F T2B누락의직접원인은아니다.

연구도구의slotfindings는기존reader가반환한발견을표시하는것이지새독립text객체목록이아니다. 표시인덱스·ArchiveID·offset은영속원본객체ID가아니다. 문자열로형상chain을맞추거나그룹멤버를만들지않는다.

## 좁은 개선의 경계

현재002에서는정상Decoder의chain/text_content를유지한채추출run/slot근거를별도출력한다. 따라서T2B데이터의조회는가능해졌지만그것을어떤독립객체에붙일지는여전히UNKNOWN이다. Production최소개선후보는“미귀속payload text runs”를별도노출하는추가진단이며,기존field를바꾸거나run별로가짜chain을만드는방식이아니다.
