# 캡처 무결성과 최초 처리 차이

## 원본과 UI

원본 automation `research/feasibility/type3-mixed-clipboard-ef-001/result.md`와 E1/F manifest, 대응 선택/그룹/해제 화면 및001복사본을 대조했다. 원본은 변경하지 않았다.

| 표본 | UI 기록 | 캡처 시각(기존보고서,KST) | Zone SHA256 |
|---|---|---|---|
| E1 | Group(R,T1A), 독립L,T2B. 최상위3, 총4구성원 |2026-10-21 15:44:54|9957013e159914f0df2c4ccc21238c5708c440e7ff4a376c08e03351d69095c2|
| F | Ungroup후 R,T1A,L,T2B. 최상위4 |2026-10-21 15:45:28|e481935f07e9986cecd827b95c3e10a2920718f660f9872e6318690c33c4e743|

당시 객체 기록은 R=사각형/Blue, T1A=문자/Red, L=두 점으로 만든 수평 곡선·선/Green, T2B=문자/Magenta다. 문자 생성 시 HY견고딕, 높이116.936mm, 폭100%, 회전0° 표시를 확인했다는 기록이며 T2 설정창을 독립적으로 재측정한 것은 아니다. 이 색상·폰트 기록을 새로 관찰하거나 수정하지 않았다.

두 Zone은 각각12288바이트이며001복사본과 전체동일. Version각32바이트/SHA `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f`. 당시 실제registered ID는 Zone49866/Version49867이며 manifest의observed_id50107/50108은 당시조회값이 아니다. E2는E1과같다는 기존기록이 있으나 이번새진단을 위해 다시Copy하지 않았다.

당시 빈 시험문서에 R/T1A/L/T2B를 준비하고 E1/E2후 그룹해제 및4선택→F를 캡처한 기록과 데이터의 내용이 일치한다. 개별두형식은 순차읽기이므로 atomic쌍/다른업무데이터혼입의 일반불가능을 증명하지 않는다. 그럼에도 이번F의T2B누락 원인을 캡처손실로 돌릴 필요가 없을 만큼 해당slot바이트와Contour바이트가 직접확인됐다. 기록길이는 GlobalData의보존길이일뿐Archive유효길이가아니다. 끝의0바이트를 padding으로 잘라내지 않았다.

## 공통 앞단

ObjectDetector는 첫512바이트 내FFFF로 Type3ChainParser를 선택한다. E/F 모두 첫descriptor가70에 있어 같은경로며 별도TextParser fallback은 사용하지 않는다. `_read_top_level_header`는 [4,6) 값을count후보로 읽지만0x5948=22856>1000으로 count=None,envelope0을 반환한다. 따라서 텍스트fontprefix를 선택개수로 오독하거나6바이트잘라내는것이 이번 E/F 차이 원인은 아니다. Shadow의지원prefix `000000000100`와도달라서 순차ArchiveReader는 계속거부한다.

## Descriptor scanner의 실제 후보창

아래는 실제객체범위가 아니라 기존scanner의새class기록기반창이다. CZone/CCourbe/CContour는48바이트bbox를읽어payload시작이뒤에온다.

| E1 class | descriptor start | payload [start,end) | F class | descriptor start | payload [start,end) |
|---|---:|---|---|---:|---|
| CZone |70|[129,375)|CZone|70|[129,227)|
| CParagraphe |375|[392,1722)|CCourbe|227|[288,386)|
| CCourbe |1722|[1783,1881)|CContour|386|[448,690)|
| CContour |1881|[1943,2113)|CPropertyExtend|690|[711,995)|
| CPropertyExtend |2113|[2134,12288)|CParagraphe|995|[1012,12288)|

`binary/node_parser.py:28`는다음plausibleclassheader까지payload를잘라낸다. `node_scanner.py:31`는그창끝까지idx를전진한다. class/object reference전체문맥을읽는구현이아니며새descriptor가더없으면끝까지한창이다. reference-only각객체시작위치는이번범위에서UNKNOWN이다. “CParagraphepayload”란진짜paragraph소유extent라는뜻이아니다.

`group_nodes_into_chains`는CZone이나반복CContour에서chain을나누며, 두입력모두이5node에서초기1chain이다. 초기chain수차이는없다. group해제후직렬화배치가바뀐사실을scanner실패로직접동일시하지않는다.

## 최초 누락 분기

`type3_chain_parser.py:520`의CPropertyExtend분기만embeddedContour검색을부른다. `:541`는CContour아닌다른node에서바로continue한다. E1은기본Contour1개+[2134,12288)창추가3개, F는기본1개+[711,995)창추가0개다. F의[1012,12288)창에는검색이실행되지않는다.

| Contour raw 범위 E1 | F 범위(기존/연구probe) | 기록수 | 전체raw동일 |
|---|---|---:|---|
|[2890,3034)|[546,690) 기존|4|YES|
|[2041,2113)|[2638,2710) 연구|2|YES|
|[3616,3688)|[3468,3540) 연구|2|YES|
|[5602,5674)|[5454,5526) 연구|2|YES|

이비교는동일Contour기록의보존을보여주며,2기록후보가독립선인지문자내부기준선인지소유관계를결정하지않는다. F에4후보가보여도최상위4객체의구조적해독은아니다. 추측class tag재동기화,임의offset정렬또는새Archive참조해석을추가하지않았다.

E1기존embeddedheader의로컬record시작756/1482/3468과절대2890/3616/5602, F기존Contour의로컬98/절대546은trace에있다. 기존후보ranking/검증/008guard를그대로사용했다. 실패marker별거부조건도trace의`markers/rejections`로남겼다. 후보루프가일찍무한반복을끊어서나머지를잃었다는근거는없으며, 이번직접원인은dispatch범위와출력축소다.
