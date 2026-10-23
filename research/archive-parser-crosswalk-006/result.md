# Native Serialize / Codec Parser 교차 검증 006

**ARCHIVE_PARSER_CROSSWALK_VERIFIED — 기존 Codec와 제한된 Native Crosswalk의 대응 및 구체적인 진단 개선점 확인에 한정.** 범용 Parser, 객체 소유권, 쓰기 또는 유효 데이터 전체 종료를 검증한 것은 아니다.

이번의 진전은 001/002의 36바이트 계약 재발견이 아니라, 실제 production 필드와 순차 Archive 경계의 좌표를 정규화해 차이를 재현하고, 중복되지 않는 최소 개선 범위를 특정한 것이다. production 코드·fixture는 수정하지 않았다.

## 비교 방법과 근거

`shadow_reader.py`는 001 `Reader`와 002의 import·fixture 도구를 재사용한다. 객체 파서나 Native 규칙을 다시 만들지 않았다. G1/H 그룹 전용 locator를 호출해야 하는 001 diagnose 대신 같은 Reader.obj를 직접 호출하므로 비교할 색상이나 Decoder 결과로 cursor를 재동기화하지 않는다. Decoder는 결과 대조에만 사용한다.

- Native 폭·저장 순서 근거: [001](../archive-crosswalk-001/result.md), [002](../archive-crosswalk-002/result.md).
- 첫 WriteObject 전 prefix·null map은 [004 원본](../archive-copy-runtime-004/runtime-001/runtime-result.json)의 단일 런타임 관찰이다. 일반적인 생성 문맥으로 확대하지 않는다.
- [005](../archive-producer-crosswalk-005/result.md)의 Pltf 정적 분석 차단 및 발행 UNKNOWN을 유지했다. 그 코드를 다시 분석하지 않았다.
- 입력별 SHA256, 실제 읽은 범위, class/reference 이벤트, Archive 범위 ID, 객체 기록 tree, Property·suffix·색상 구간, 중단 위치와 UNKNOWN tail은 [crosswalk-results.json](crosswalk-results.json)에 보존했다. hex fixture 원본 파일 SHA와 변환 payload SHA를 구분했다.

모든 보고 범위는 원본 payload byte의 반열린 구간이다. production의 node/style/stream offset은 6바이트 envelope를 제외한 상대 좌표이므로 해당 시작값을 더해 비교했다. source_payload_offset은 node-local이므로 그대로 파일 offset으로 사용하지 않았다. 같은 contour raw bytes가 정확히 한 chain에 대응할 때만 필드를 연결했다.

## Stage A — Parser와 Native 계약 대응

| 항목 | 기존 Parser 실제 구현 | Native 기반 진단과 차이 / 신뢰 수준 |
|---|---|---|
| 객체 시작 | `binary/node_scanner.py`에서 FFFF 검색, `header_parser.py`의 인쇄 가능한 C 계열 이름 검사, 다음 descriptor까지 payload 절단 | HEURISTIC. 클래스 재사용 tag와 객체 PID map을 순차 해석하는 기능과 다르다. Shadow의 등록 이벤트는 초기 map 가정 때문에 CONDITIONAL |
| 공통 header | `common.py:5`의 두 번째 WORD가 `ObjectHeader.class_id`로 저장됨 | 해당 새 클래스 descriptor에서 이 WORD는 **schema**다. G1의 CPropertyExtend는 schema5와 Archive class ID8이 다름을 실제 비교했다. 공개 필드명 변경 없이 별도 메타데이터로 구분할 필요가 있음 |
| Contour | `geometry/contour_parser.py`는 CObDao 마커 이후 여러 shift를 검사·평가한다. `contour_candidate_validator.py:12`는 positive count, 상한4096, count×stride 범위, 전체 좌표 finite, decode 수를 이미 검사 | count/36 폭 검증을 새로 복제할 이익은 없음. header의 출처는 HEURISTIC, 지원 CPtCtr4D 36바이트 저장 폭은 VERIFIED, 이번 입력의 정확한 시작·끝은 초기 문맥 포함 CONDITIONAL |
| Property | `node_parser.py`는 다음 그럴듯한 새 클래스 descriptor까지 payload를 잡고 `style/property_extend_parser.py`가 그 안을 탐색 | Property 끝을 Serialize 필드로 계산하지 않는다. Native 규칙으로 순차 count·길이를 계산한 본문은 이번 7개 입력에서112B, 다른 길이는 실표본 미검증. CONDITIONAL |
| 색상 | Type3ChainParser의 0x79/0x85 및 0x20E/0x21A 후보와 palette scan, 반복12바이트·거리·confidence 우선순위 사용 | 기존 선택값은 이번 9개 contour 모두 Native suffix 후보값과 같음. 위치·소유권까지 확정한 것은 아님. production의 confirmed/strong은 연구상 VERIFIED와 다른 내부 confidence임. 색상 선택은 HEURISTIC, 순차 suffix의 Native 저장 필드 대응은 지원 계열에 한정 VERIFIED/파일 위치 CONDITIONAL |
| 그룹 | declared_count==1, 여러 final chain, 비문자 조건으로 is_grouped 후보 설정. chain은 CZone/CContour 마커와 embedded contour로 나뉨 | HEURISTIC. chain 수를 최상위 객체 수로 취급하지 않음. Shadow tree의 helper 목록 관계는 직렬화 포함 관계이며 실제 UI 부모·소유권 전체는 UNKNOWN |
| 미지원 | ObjectDetector가 can_parse를 순서 검사하고 UnknownParser fallback. Type3ChainParser는 첫512B FFFF만으로 후보가 되고 일부 실패를 빈 contour로 남길 수 있음 | 전체 Archive 유효성 검증기가 아님. Shadow는 미지원 prefix/class/schema/null/object/확장 reference/optional child/상한을 넘는 count에서 명시적 UNSUPPORTED. 이 상태는 Codec 전체 기능 미지원 판정이 아님 |
| 데이터 끝 | production은 입력 전체를 raw_data/raw_size로 보존하고 node payload가 끝까지 갈 수 있음 | raw_size는 Archive 유효 길이가 아니다. Shadow의 parsed_end 이후는 UNKNOWN. tail을 padding이나 추가 객체라고 확정하지 않음 |

## Stage B/C — 실제 입력별 범위

모두 8192바이트 입력이다. prefix [0,6)은 조건 검사만 하며 읽은 객체 범위와 구분한다. 7개 geometry 입력의 Codec contour raw bytes와 순차 범위는 9/9 일치했고, source_stream_offset을 정규화한 실제 위치도 일치했다. 다음 표의 범위는 기존 계약 재현이며 새 Native 발견이 아니다.

| 입력 | Contour count / 구간 | Property 본문 | CCourbe suffix | 색상 필드 시작 | 순차 중단 / UNKNOWN tail |
|---|---|---|---|---|---|
| G1 | 4/[630,774), 4/[1375,1519) | [795,907), [1521,1633) | [907,931), [1633,1657) | 915/927, 1641/1653 | 1657 / [1657,8192) |
| H1 | 4/[630,774), 4/[1375,1519) | 동일 | 동일 | 동일, R1/R2 순서는 G1과 다름 | 1657 / [1657,8192) |
| polyline_3_points | 3/[482,590) | [611,723) | [723,747) | 731/743 | 747 / [747,8192) |
| polyline_5_points | 5/[482,662) | [683,795) | [795,819) | 803/815 | 819 / [819,8192) |
| polygon_5_sides | 5/[482,662) | [683,795) | [795,819) | 803/815 | 819 / [819,8192) |
| polygon_6_sides | 6/[482,698) | [719,831) | [831,855) | 839/851 | 855 / [855,8192) |
| default_circle | 8/[482,770) | [791,903) | [903,927) | 911/923 | 927 / [927,8192) |
| text/default_text | prefix 불일치, cursor0, UNSUPPORTED | UNKNOWN | UNKNOWN | UNKNOWN | [0,8192) |

## 이번에 구체화한 차이

G1/H1의 production style은 두 chain 모두 정규화한 Property 후보 구간 **[795,8192)** 를 공유한다. Shadow는 **[795,907)** 과 **[1521,1633)** 을 따로 계산한다. production의 첫 CPropertyExtend payload에 후속 class-reference 객체와 tail이 포함되어, 두 chain이 같은 넓은 후보 집합에서 색상을 선택한다. 따라서 색상값 일치가 Property 소유 범위 일치를 의미하지 않는다.

G1은 Navy Blue/Turquoise, H1은 Turquoise/Navy Blue를 production이 선택했으며 순차 suffix의 값과 일치했다. 과거 공유 후보 문제를 이번 입력에서 색상 오판정으로 재현했다고 주장하지 않는다. 이번에 확인한 것은 **값 일치와 범위 불일치의 공존**이다.

독립 형상에서도 production Property 후보는 본문 시작부터8192까지 이어져, 112B 본문이나 부모 CCourbe의 24B suffix와 범위가 다르다. 이는 다음 literal descriptor를 찾는 설계의 결과이며, 값 추출 자체의 실패를 뜻하지 않는다.

문자 입력에서 실제 Decoder는 **Type3ChainParser** 를 선택하고 object_type=text, text_content=`abcdefg`를 반환했다. 별도로 기존 **TextParser** 를 직접 호출하면 최장 ASCII 후보인 `OBJETINFOS_CLASSNAME`을 반환한다. 두 실행 경로를 혼동하지 않는다. Shadow의 prefix 거부는 Native Crosswalk의 대상 밖이라는 뜻이며, 기존 Codec의 문자 미지원 판정이 아니다.

## 합성 입력과 거부

실제 표본을 변경하지 않고 메모리에서 만든10개 사례(count 0/101/FFFFFFFF/원count+1, descriptor/contour/property/suffix 절단, 미등록 class reference, null reference)를 Shadow가 거부했다. 중간 이벤트는 진단 전용이며 성공 tree를 반환하지 않는다. 결과는 [synthetic-results.json](synthetic-results.json)에 있다. count 상한100은 연구 Reader의 범위 제한이며 제품 규격의 상한이 아니다.

UNKNOWN tail만 제거한 합성 입력은 같은 tree로 읽혔지만 full_valid_length=UNKNOWN을 유지했다. 이 대조는 parsed_end를 정식 데이터 종료로 간주할 수 없다는 한계를 보여준다.

저수준 `common.read_contour_points`는 32B 합성 vector만 있어도 부족한 tag를0으로 보충하고 cursor를36으로 옮긴다. 반면 기존 `read_contour_records`와 candidate validator는 count×36 범위를 먼저 검사하여 거부한다. 정상 호출 경로의 검사를 누락한 전체 Parser 결함으로 취급하지 않는다. 향후 primitive를 직접 재사용할 때 이 전제조건을 명시하는 실익이 있다.

## 미확정 사항과 적용 조건

- 001 Reader에 남아 있는 additional-list 가정 문구는 기존 구현을 보존한 것이다. 002에서는 **정확한 CZone/CCourbe 동적 vtable**의 추가 직접 Serialize 목록0기여를 확인했지만, 같은 Archive 이름을 쓰는 모든 파생 타입에 일반화하지 않는다.
- Property의 integer/double/string count는 순서대로 읽지만, 이번 실제 표본은 모두112B다. 임의 Property 길이나 optional child 지원 성공으로 확대하지 않는다.
- class ID는 새 class와 object가 공유하는 Archive 등록 순번이며 영속ID나 원본 문서 identity가 아니다. 초기map/prefix 일반성, 전체 종료 위치, 전체 소유 관계는 UNKNOWN이다.
- raw geometry 일치는 곡선 의미·가공 적합성·원본 선택 적용의 증명이 아니다. change_allowed=false를 유지한다.

## Stage D — 다음 production 개선의 최소 범위

**단일 권고: 기존 Contour/색상 추출을 교체하지 않고, 대응을 확인한 클래스 계열에 한정하여 Archive 경계의 shadow 비교 결과를 진단 메타데이터로 추가한다.** 이번에는 production에 적용하지 않았다.

우선순위:
1. 절대 payload 좌표·schema·조건부 Archive class ID를 구분하고, 기존 후보 Property 구간과 순차 본문/suffix의 범위 차이를 표시한다. 기존 공개 필드와 반환값은 유지한다. G1/H1의 공유 후보와 참조 객체에 걸친 구간을 진단하는 것을 최소 수용 조건으로 삼는다.
2. 이미 있는 count/stride/finite 검사를 재구현하지 않는다. 기존 Contour 후보 시작·종료가 순차 Archive cursor와 일치하는지 비교하고, 불일치하면 기존 결과를 VERIFIED로 취급하지 않는다. 미지원 schema·미등록 reference는 UNKNOWN/UNSUPPORTED로 중단한다.
3. Property scan의 완전한 교체는 보류한다. 다른 Property 길이·optional 자식·별도 prefix/class map 문맥을 검증하지 않았으므로112B/120·132를 고정 규칙으로 만들지 않는다. 그룹 구성원 속성의 본격 쓰기나 UI 부모 관계로의 승격도 보류한다.

연구 코드와 production에는 Contour 폭·후보 위치·속성 해석의 중복이 있다. 다만 연구의 제한된 지원 집합과 production의 넓은 heuristic 용도가 다르다. Reader 사본을 production에 더 만들기보다 이번 비교 인터페이스와 회귀 입력을 다음 진단 통합 단위로 사용한다. 완전 통합이나 기존 heuristic 삭제를 선행하지 않는다.

## 검증과 환경 보호

- 신규 교차 검증24건, 기존 관련 회귀38건, 합계 **62/62 PASS**. 기존001/002의15건을 포함한다. 전체 Codec suite 실행은 아니다.
- [tests.txt](tests.txt)에 실제 검사 결과, diagnostic-run.txt에8개 표본과 합성 대조 실행 결과를 보존했다.
- [preservation.json](preservation.json): production src·tests·관련 기존 연구·group-color **712개 파일**을 전후 SHA 비교하여 변경0개. 신규 연구 폴더만 추가했다. bytecode 쓰기와 pytest cache를 비활성화했다.
- Type3/LLDB/Clipboard 접근, Pltf 재분석, Native 호출, Patch/Paste, DLL/PLG/API/기존 증거 변경 없음. INCIDENT_CLOSED, COPY_PRODUCER_RUNTIME_PARTIAL과 예외 원인 UNKNOWN을 유지했다.
- 업무 모드 OFF를 확인했다. 새로운 동적 디버깅 제안이나 실험 계획은 작성하지 않았다.