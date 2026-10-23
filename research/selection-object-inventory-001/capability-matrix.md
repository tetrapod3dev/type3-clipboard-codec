# 현재 객체 판별 계약

| 항목 | 기존 구현 | Inventory 표현·수준 | 한계 |
|---|---|---|---|
| Parser 선택 | ObjectDetector/ParserRegistry, Type3ChainParser 우선 TextParser fallback | parser_name, decoder_object_type | 객체별 종류가 아니라 payload parser 선택 |
| 최상위 선택 집합 | declared_object_count, is_grouped, object_chains | declared_count_candidate HEURISTIC; exact count UNKNOWN | descriptor/chain 수와 UI 수를 동일시하지 않음 |
| Rectangle | shape_classifier:4record면 rectangle, confidence confirmed | kind HEURISTIC 및 original confidence 별도 | 4record 일반 사각형/다른형상 배제 근거 부족 |
| Circle |8record + 거의 square bbox 등 | circle HEURISTIC | 정확한 원 방정식/curve 의미의 일반 판정 아님 |
| Polyline/Polygon | role/control/closed-like/endpoint 경험적 규칙 | *_candidate HEURISTIC, reason 보존 | UI 도구명/저장 시작점/폐곡선 의미와 동일하지 않음 |
| Contour | 기존 count/stride 후보 검사, chain builder | records/범위 HEURISTIC,006/007 일치 경계 CONDITIONAL |36바이트는 검증된 CPtCtr4D 계열에만 VERIFIED 계약; 객체 extent 아님 |
| 좌표/bbox | 기존 model/contour 기록 | m→mm CONDITIONAL, 수치값 HEURISTIC | G/H UI 대조는 해당 표본 범위. 전체 클래스 일반화 없음 |
| Text | text pipeline/CParagraphe 및 기존 global/chain 후보 | payload_text/chain text HEURISTIC | glyph 관련 geometry chain이 독립 text 객체가 아님. E에서T1A/T2B 후보, F에서T2B누락 |
| Font | decoded.font_name | payload_text의 font 후보 HEURISTIC | 폰트 목록과 각 문자 객체별 소유 관계 UNKNOWN |
| 색상 | 기존 Property 후보창과 ranking | color HEURISTIC; suffix field 조건부 대조 별도 | shared window 경고, color_member_association UNKNOWN |
| Group | is_grouped/group_children 및 Archive tree | group flag HEURISTIC, 실제 hierarchy UNKNOWN | false는 Group 부재 증명 아님. tree edges는 Serialize 관계 |
| Archive schema/ID | 원본006/007 | descriptor_events CONDITIONAL | schema와 Archive-local class/object ID 분리; 영속 ID 금지 |
| Layer/CAM | 확정된 읽기 계약 없음 | UNKNOWN | 색상을 가공조건으로 추정하지 않음 |
| 미지원 | 연구Reader 조건부 거부, Decoder UnknownParser 등 | UNSUPPORTED 혹은 후보만 PARTIAL | tail/전체 객체 종료 UNKNOWN. 자동재동기화/후보확정 없음 |

VERIFIED는 기록 폭 등 기존 Native 저장 명령의 확인 범위이며, 기존 Decoder의 `confirmed`/`strong`을 의미하지 않는다. 실제 출력의 shape/색상/bbox 후보는 이 상위 검증으로 승격하지 않았다.

재사용 코드: `src/type3_clipboard_codec/codec/decoder.py`, `parsers/object_detector.py`, `parsers/geometry/{contour_parser,shape_classifier,chain_builder}.py`, `parsers/text_parser.py` 및 text pipeline, `research/archive-parser-crosswalk-006/shadow_reader.py`, `research/archive-boundary-diagnostic-007/boundary_diagnostic.py`. 이들 기존 파일은 수정하지 않았다.

외부 관찰 근거: `tests/samples/README.md`(fixture intent와 parse결과 혼재, 독립 UI로 전부 승격하지 않음), `research/group-color/type3-clipboard-member-color-003/result.md`, `research/group-color/type3-clipboard-independent-prediction-006/result.md`, automation `research/feasibility/type3-mixed-clipboard-ef-001/result.md` 및 대응 캡처. G/H 숫자·색상 대조는 이 문서의 UI 표시/수치 설정을 기준으로 했다. G1/H를 별개의 영구 객체 ID로 재결합한 것은 아니다.
