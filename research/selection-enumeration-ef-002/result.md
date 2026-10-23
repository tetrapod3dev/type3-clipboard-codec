# E/F 선택 객체 열거 누락 원인 002

**SELECTION_EF_ENUMERATION_CAUSE_VERIFIED** — 누락이 발생하는 기존 코드 경로와 실제 바이트를 재현했다. 원인 분류는 **MULTIPLE_CAUSES**이며, 정확한 최상위 객체 열거 성공은 **false**다. 원인 검증을 Inventory 완성으로 승격하지 않는다.

2026-10-24, 저장 파일만 사용. TypeEdit/Clipboard/Native/디버거 접근 없음. Production Decoder와 기존001을 수정하지 않았다.

## 확인된 원인

1. **OBJECT_ENUMERATION_GAP**: 기존 node scanner는 새 class descriptor 후보를 기준으로 payload를 나눈다. E1과 F 모두 초기 chain은1개다. 이후 `_process_object_chain()`은 CContour 및 CPropertyExtend payload에서만 Contour를 찾는다. E1의 긴 마지막 payload는 CPropertyExtend여서 추가3후보가 발견되지만, F의 긴 마지막 payload는 CParagraphe여서 이 분기를 받지 않는다. 따라서 E1은1+3=4chain, F는1+0=1chain이다. 첫 관련 데이터배치 차이는 offset227 이후 descriptor 순서/후보창이며, 실제 후보 누락을 만드는 실행 분기는 `type3_chain_parser.py:520,541`이다.
2. **TEXT_OWNERSHIP_GAP / 반환 축소**: F에서도 `extract_text_runs()`는 이미 T1A/T2B 두 run을 반환한다. 하지만 `attach_text_runs_to_chains()`의 `len(chains)==1` 분기(`cparagraphe_parser.py:185~192`)가 첫 run만 붙이고 반환한다. `text_pipeline.py:67`의 payload `text_content`도 첫 run 하나뿐이다. 그래서 T2B는 실제 추출 이후 공개 결과에서 사라진다. 문자열 자체를 읽지 못한 TEXT_EXTRACTION_GAP은 이 E/F의 직접 원인이 아니다.
3. 소유권 자체도 미확정이다. E1은4chain이라 두 run을 폭/문자열 길이 heuristic으로 배정하는데, 사각형 chain에T1A가 붙는다. chain 수가 늘어난다고 문자와 원본 객체의 귀속이 정확해지는 것은 아니다.

## F 원본에서 확인한 데이터

- T1A slot windows: **[1322,2138)**.
- T2B slot windows: **[4138,4954)**.
- 각 run은204바이트 record4개, char DWORD는 T2B의 경우 **84,50,66,0**이다. 기존 AttrChar v5/empty-extension validator도4개 모두 통과한다. ASCII 연속 문자열 검색만으로 얻은 결과가 아니다.
- F의 기존 Contour [546,690) 및 연구용 추가 후보 [2638,2710), [3468,3540), [5454,5526)는 E1의4개 Contour 후보와 각각 전체 raw bytes/SHA가 일치한다.

이것은 관련 문자·Contour 바이트가 원본 안에 존재한다는 근거다. **독립 객체 전체 Serialize 범위·class reference 문맥·Group/Member 소유권·전체 유효 Archive 길이는 여전히 UNKNOWN**이다. 사용자 선택4개와 후보4개를 동일시하지 않는다.

## 구현

`enumeration-diagnostic.py`: 기존 Decoder를 수정하지 않고 Python trace로 Parser 선택·node/chain·Contour 분기·text run/attachment를 기록한다. 원본001의 import seam과 기존006/007 Reader를 재사용했다. E/F의 prefix는 `010000004859`이며 Shadow는 계속 `unreviewed prefix`로 거부한다.

추가 읽기 출력:

- `all_extracted_text_runs`: 이미 기존 extractor가 얻은 모든 내용 후보를 attachment와 분리해 표시.
- `slot_record_findings`: 기존 slot reader 결과의 원본 byte window와 char field/204바이트/v5 layout 검사. 전체 text 객체 extent로 취급하지 않음.
- `diagnostic_contour_probe`: 기존 embedded scanner를 CParagraphe 후보창에 별도로 적용한 반사실적 진단. 후보를 원래 Decoder/001에 합치지 않고 HEURISTIC/ownership UNKNOWN을 유지.
- `trace`: 함수/분기/offset/검증 결과. node/chain은 envelope 상대, slot window는 입력 절대 byte 좌표. E/F는 envelope0이다.

실행 예(Codec 루트):

```powershell
./.venv/Scripts/python.exe -B research/selection-enumeration-ef-002/enumeration-diagnostic.py --input research/selection-object-inventory-001/samples/F.bin --output new-F-diagnostic.json
```

기존 output 덮어쓰기 거부. bytes 입력은 `diagnose_bytes(data)`로 분리. Decoder와 연구용 probe는 모두 실제 base Python child에서 실행하며 기본10초 timeout,16MiB 입력 상한이다. timeout 시 생성한 child handle만 종료하고 결과를 성공으로 사용하지 않는다. trace는1000event 상한/누락 여부를 기록하며 이번 E/F는26event씩, 잘림 없음. timeout/trace 상한은 형식의 정당성 증명이 아니다.

`ef-parser-trace.json`은11개 보존 입력과10개 합성 입력의 결과 및 원본 캡처 SHA를 기록한다. `F-first-diagnostic.json`은 앞서 생성한 초기 연구 진단을 그대로 보존한 보조 기록이며 최종 비교는 ef-parser-trace를 사용한다.

## 검증

**134 PASS** = 기존114 관련 회귀 + 신규20검사. `tests.log` 참조.

신규검사 목적: 원본 캡처 동일성, E/F fresh trace 재현, 추출후 T2B 소실 분기, 구조화된 문자record 존재, Property/Paragraphe dispatch 차이, Contour raw동일성, 미지원prefix 유지,001의11개 기존 보고서 동등성(실행PID/시간 제외), 동일문구 중복과 객체수 분리, 중복Contour 보존, 손상knownprefix 거부, 강제timeout 결과폐기.

G1/H 및 단독문자/사각형/3·5점 폴리라인/5·6각형/원도 기존 Decoder fingerprint와001 출력이 같다. 11개 실제/10개 합성 재현의 timeout0이며, 종료 처리 시험에서만 의도한 짧은timeout을 사용했다. 008 Guard와009계약은 수정하지 않았다.

전체 Suite는 이번에 실행하지 않았다. 기존008의17개 역사적 실패+4개 신규실패(합21)를 해결했다고 주장하지 않는다. fixture/frozen baseline/001/006/007 및 양쪽 기존 사용자 파일의 SHA 보존은 `preservation.json`에 기록했다. 업무 모드OFF 유지.

## 제한적 개선안

지금 확인된 최소 읽기 개선은 **소유권 없는 text-run 목록을 attachment 결과와 별도로 노출하는 것**이다. 기존text_content/chain배정을 덮어쓰지 않고 UNKNOWN owner와 원본slot window를 함께 제공하는 방향이다. 이번에는002연구도구에만 구현했다. Production 또는001출력 변경안은 별도 호환성 검토 전까지 적용하지 않는다.

F의CParagraphe 전체창을 일반 Contour 검색 대상으로 확대하는 변경은 권고하지 않는다. 해당창은 descriptor-scanner가 잘라낸 범위로, paragraph 객체의 실제 extent가 아니다. 다른 객체/참조가 섞인 데이터에 대한 구조계약이 없다. 이번3개추가후보를 일반 열거API나 부모관계로 승격하지 않는다. 새 Native 분석·새 캡처·후속실행을 시작하지 않고 종료한다.

## 마지막 질문

**“F에서 누락된 T2B와 다른 객체들은 원본 데이터 자체에 없는 것인가, 아니면 우리가 작성한 Decoder가 읽지 못하는 것인가?”**

**T2B는 F 원본에 있으며 기존 extractor도 읽고 있었다. 한 chain에 첫 run만 연결하는 반환 경로 때문에 출력에서 누락됐다.** 다른 세 Contour 후보도 원본에 존재하고 E1과 raw bytes가 동일하지만, CParagraphe 후보창을 추가 Contour 검색에서 제외하는 경로 때문에 chain으로 나오지 않았다. 따라서 이번 누락을 원본 데이터 부재로 설명할 근거는 없고, 구체적인 Decoder 열거/반환 제약이 확인됐다. 다만 네 독립 원본 객체의 전체 데이터와 귀속이 모두 보존됐는지는 **UNKNOWN**이다.
