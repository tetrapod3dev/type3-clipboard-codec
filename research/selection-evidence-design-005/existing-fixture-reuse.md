# 기존 표본 재사용과 A~E 대체 범위

| 후보 | 기존 자료 | 대체 가능한 부분 | 정확히 대체하지 못하는 부분 | 이번 결정 |
|---|---|---|---|---|
| A 사각형R단독 | member-color-003 S1-confirmed/S2-confirmed,기본rectangle | 단독geometry발생과UI단독선택·단위·bbox | E/F의R과같은생성객체/속성의단독Copy는아님 | 일반기준재사용. 같은R새캡처는body/map목적에NON_DISCRIMINATING |
| B T1A단독 | text/default_text와그intent/record,기존단독text표본 | text가자체Contour를동반할수있다는반례,slot/run기준 | E/F T1A와동일문구/폰트/색상/객체인단독캡처는확인되지않음 | 좁은발생연관성은추가가능하지만객체끝증거는아님 |
| C R+T1A독립 | F는R/T1A/L/T2B독립,geometry U0,비그룹다중text | independent-selection과복수발생의차이 | 같은R/T1A두개만선택한완전대조군은없음 | 결손을인정하되새시험필수로확정하지않음 |
| D 같은R+T1A Group1 | E1은Group(R,T1A)+L+T2B, G0/U0및다중textgroup | Group전후최상위/구성원구분과count후보의반례 | R/T1A그룹만의rawCopy는확인되지않음. E1그룹만화면선택과그룹만캡처는구분 | UI선택화면을없는binary로간주하지않음 |
| E 선택순서반전 | text_two_objects_not_grouped_selection_reversed와원래2text,3text abc/cba | attempted selection order와stored order의차이 | R/T1A서로다른종류2개순서대조는아님 | 별도새R/T순서시험권고없음 |

같은 문구·크기·폰트라고 같은 Native객체/영속ID는아니다. 서로다른문서의A-like와B-like를이어붙여C/D와완전대조군이라고주장하지않는다. 원래R/T1A의단독바이너리가없다는것은명시하되,그파일이생기면프레이밍이자동해결된다고가정하지않는다.

## 기존 통제군이 이미 배제하는 해석

- F는UI4개인데legacy1chain이다. chain수는최상위선택수의정답이아니다.
- G1/H는UIgroup1에사각형발생2개가있다. Contour발생수는그룹구성원/선택수와동일하지않다.
- 그룹3text와비그룹3text는CParagraphe descriptor하나만보인다. 새classdescriptor수는object수아니다.
- reversed2text의actual_stored_order는unresolved다. 이표본은기존004에서도사용됐으므로003에없던결정적Producer근거를새로발견한것으로세지않는다.
- text그룹intent의literal selected/copied3과grouped 표시는범위모호성이있다. 이를UI상top-level1로자동수정하지않으며새경계정답으로사용하지않는다.

## 캡처 도구 소스 적합성 검토 — 실행하지 않음

`tools/clipboard_typeeditzone.py`의dump-bundle은두등록이름의bytes를원형대로저장하고registered_id/length manifest를쓴다. 하지만dir를exist_ok로만들고write_bytes하므로**스스로기존파일충돌을거부하지않는다**. manifest자체에SHA256도없다. verify-bundle은저장파일끼리검사하는명령이아니라현재Clipboard를다시읽는다. inspect의main도adapter를생성하므로이번작업에서는어떤명령도호출하지않았다.

`tools/capture_type3_sample.py`는기본overwrite거부와binary/hexwrite검사를제공하지만기존fixture/intents/reports에출력하고기본inspect=true로Decoder를실행한다. git-add옵션도있다. 따라서지금V2기준선보존과raw연구채집의무조건안전한실행진입점으로승인하지않았다. 기존코드의옵션/쓰는경로를읽기만했으며수정하지않았다.

두도구의Adapter는포맷이름을RegisterClipboardFormat으로조회하고각형식을별도Open/Get/Close로읽는다. session별실제ID와과거observed상수는구분해야하며atomic두형식캡처를보장하지않는다. 독립UI상태·시각·수집순서·각파일SHA가필요하고원본길이를Archive유효길이로보지않는다. 임의전체Clipboarddump/사전내용백업/다른형식수집은대안으로제안하지않는다.

캡처를채택하지않아실행command/preflight는작성하지않았다. 새비교가채택되는별도단계에서는고유비어있는대상경로와독립SHA/manifest·사용자Copy승인및기존문서보호조건을먼저확정해야한다.

## 이번에 직접 확인한 기준선 SHA256

| 자료 | SHA256 |
|---|---|
| `research/selection-inventory-v2-004/v2-sample-results.json` | `8f374bdd8adbe88338434519e38314884d9edc0cb70cabcf7a3c9c788cd657ba` |
| `research/selection-inventory-v2-004/selection-count-evidence.json` | `2e0d22779b76fa8d8d3282f4203cecccb8acfe6836bec0241b9a95d2fa160fb1` |
| `research/selection-inventory-v2-004/regression.log` | `5b13ae8d0dec2af99ebbc66e74fd8192289cf2536e28d3882e935daed942c7fc` |
| `research/selection-enumeration-ef-002/ef-parser-trace.json` | `36bd51aa8c77203d1ef4e9c875cd65b9134a290148b585db19dc537002ab311e` |
| `research/selection-object-framing-ef-003/object-reference-events.json` | `f4074ef8088411af4c54658bba9b0b3858d7bd517ba122039a8e4c9032d09a80` |
| `research/archive-producer-crosswalk-005/result.md` | `43a99918adc912d8306a862ed0311166a74f0bd389b270e1a8a65985256574e4` |
| `research/selection-object-inventory-001/samples/E1.bin` | `9957013e159914f0df2c4ccc21238c5708c440e7ff4a376c08e03351d69095c2` |
| `research/selection-object-inventory-001/samples/F.bin` | `e481935f07e9986cecd827b95c3e10a2920718f660f9872e6318690c33c4e743` |
| `research/group-color/type3-clipboard-member-color-003/samples/S1-confirmed/typeeditzone.bin` | `ac14d3bf6769b3b7ad283e81287dd301cd29a684cd3be5028903e0c0d874fe8a` |
| `research/group-color/type3-clipboard-member-color-003/samples/S2-confirmed/typeeditzone.bin` | `72f6a1e90d229ea0546237f8c63f2cc7801d3e595b3e7befc12c79c01fae4819` |
| `research/group-color/type3-clipboard-member-color-003/samples/U0/typeeditzone.bin` | `4b224da0536a5abe34c48e299376af3c4f03acd75dab3287c76808ebd3f78887` |
| `research/group-color/type3-clipboard-member-color-003/samples/G1/typeeditzone.bin` | `0b62011ff898b414fce086a6c775d1073bb08fe0b49edacf98e9d5a1d185ad4c` |
| `research/group-color/type3-clipboard-independent-prediction-006/samples/H1/typeeditzone.bin` | `1e2d803df75b56385d97ee8a0021ae94b80cb1da2cd37f96abdf95e4242957af` |
| `tests/samples/text/default_text.txt` | `f3a84603a39f0e8695446bb363797ac3bd7c483e98f908d84d14d656e686d111` |
| `tests/samples/text/text_three_objects_grouped_order_abc.txt` | `aa8a05d891b4e9e620edfb0b06ab8b5bec12922b8b5d566d6369fe423c13291f` |
| `tests/samples/text/text_three_objects_not_grouped.txt` | `e1a12f77519ccc4337f1c4faaa33d6513b6d63b1cffe4705c420bf58389fc79a` |
| `tests/samples/text/text_two_objects_not_grouped_selection_reversed.txt` | `92e3ef810a3c18b1fbc582e36c631b34421c2944a65fecd21bd616f7d4bd878c` |
| `tools/clipboard_typeeditzone.py` | `72e4c8fd38e2c75332acd521aa01485ed95c7def0b1e410c15870fd5933938fe` |
| `tools/capture_type3_sample.py` | `f51c37968c22916602cc1003ac65b9cb1b73a78237aa133e43ad102949fda64f` |
| `src/type3_clipboard_codec/adapters/win32_clipboard.py` | `f084c629cc6d8af5652b5f11c21f64ddd69f1102ebd2d87ba0f8a1fa9f4b668c` |
