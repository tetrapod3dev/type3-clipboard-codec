# Decoder Contour Progress Guard 008

**DECODER_PROGRESS_GUARD_PARTIAL**

실제 비전진 원인을 입증하고 최소 guard를 구현했다. 수정 후 손상 입력11개 timeout0, 정상8개 및007 진단 결과 완전 동일을 확인했다. 다만 전체 Suite의 소스 고정 정책과 출력 상한 검사4건이 추가 실패하여 전체 회귀 완료 조건은 충족하지 못했다. frozen baseline·lock·fixture를 바꿔 통과시키지 않았다.

## 시작 상태와 변경 범위

- 시작 HEAD: `4b978cd8bdd79ea15c930f376f4771d31d3e738d`, Git status clean.
- 기존 Git tracked 파일과006의 보존 목록을 합쳐 중복 제거한893개를 before.json에 스냅샷했다. 저장소 전체 파일 수라는 의미는 아니다.
- 변경한 기존 파일은 **src/type3_clipboard_codec/parsers/geometry/contour_parser.py 한 개**뿐이다. 나머지892개 SHA는 동일하다. 기존007·fixture·profile·execution-lock·source integrity baseline·Encoder는 변경하지 않았다.
- 추가한 파일은 신규008 폴더의 자식 실행기·검사·증거·보고서다. commit/reset/checkout/clean/push는 하지 않았다.

## Stage A — 재현과 원인

입력은007의 G1 복사본에서 첫 Contour 끝 직전으로 메모리 절단한773바이트 합성 입력이다. 원본 fixture는 변경하지 않았다.

SHA256: `f054b591f09be5a4e806fac69960b1936e3bbc36ef9e64f4eacf85cc7d494856`

[reproduction-before.json](reproduction-before.json)에 실제 재현을 보존했다.

- 별도 Python 자식 PID53156, 부모 PID46192. Windows venv launcher의 별도 worker가 남지 않도록 실제 base Python interpreter를 직접 실행하고, 자식이 출력한 os.getpid와 Popen PID를 대조했다.
- 부모 communicate timeout2초. timeout 후 **해당 Popen handle의 자식만 kill**하고 communicate로 종료를 수거했다. 반환코드1, timeout=true.
- 0.6초 faulthandler stack과 Python line trace를 제한적으로 기록했다. Type3·CLion·부모 프로세스나 전역 프로세스 목록을 검색/종료하지 않았다.

멈춘 함수는 `analyze_contour_header_candidates`다. 원본 line272의 diagnostics.append 직전에 완료된 세 반복에서 다음 상태가 모두 같았다.

| 의미 있는 상태 | 값 |
|---|---|
| idx | 0 |
| marker_pos | 76 |
| 후보 shift | 8 |
| legacy kind / count / payload offset | 1 / 4 / 98 |
| structural_valid | false |
| found_for_this_marker | true |
| actual_selected | None |
| selected_offsets / found_headers | 빈 집합 / 빈 목록 |
| selection_reason | no_structural_recommended_candidate |

원인 흐름:
1. line145: legacy의 count4 판정이 plausible이므로 found_for_this_marker=true로 표시하고 shift 검토를 끝낸다.
2. line152~154의 scan 전진 fallback은 found_for_this_marker=false일 때만 실행되어 건너뛴다.
3. 실제 기록은 절단됐으므로 structural candidate는 invalid이고 recommended/actual_selected=None이다.
4. line238의 winner 기반 idx 갱신도 실행되지 않는다.
5. 같은 marker를 같은 idx에서 다시 찾는다. payload·후보 순서·선택 집합은 동일하며, 누적 diagnostics 자체는 다음 ranking에 사용되지 않는다. 따라서 새 의미 상태로 나아갈 수 없다.

이는 단지 cursor 한 번이 같았던 관찰이 아니다. 후보 검토가 끝난 세 번의 전체 선택 상태가 동일했고,2초 동안 함수가 반환하지 않았다. 같은 장애를 수정 전 반복 재현하지 않았다.

## Stage B — 최소 수정과 종료 계약

[minimal-change.diff](minimal-change.diff)의 변경은 루프 끝4줄뿐이다.

```diff
         diagnostics.append(marker_diag)
+        # Without scan/selection progress, the next pass repeats this marker.
+        # Stop with the existing diagnostics instead of inventing a contour.
+        if idx <= marker_pos:
+            break
```

모든 후보 검사·ranking·confidence·legacy fallback을 마친 뒤에만 검사한다. 정상 winner는 idx를 actual_offset으로 옮기고, legacy 후보 자체가 없으면 기존대로 marker_pos+1로 옮긴다. 두 경로 모두 현재 marker를 지나므로 guard를 통과한다. 같은 marker 안의 여러 shift 및 처리 단계 검토를 조기에 막지 않는다.

루프가 계속되려면 idx > marker_pos가 되어야 하며 marker_pos는 이전 idx 이상이다. 따라서 계속 실행하는 각 반복의 scan 위치는 엄격히 증가한다. 유한 입력의 marker 검색 공간에 근거한 종료 보장이며 임의의 작은 반복 상수나 전체 상한을 추가하지 않았다. selected_offsets나 found_headers가 바뀌는 유일한 winner 경로도 idx를 함께 전진시키므로, 이 guard는 생산적인 선택 상태 변화를 중단시키지 않는다.

반환형과 실패 계약은 기존대로다. 해당 탐색에서 winner가 없으면 headers=None와 실제 진단을 반환하고, 직접 호출자인 Type3ChainParser는 `if not headers: continue` 경로로 진행한다. 이미 성공한 앞선 contour가 있었다면 그 기존 결과를 보존하는 부분 추출 계약도 유지한다. 새 exception·공개 API·성공 contour·bbox·padding·재동기화는 추가하지 않았다.

## Stage C — 수정 후 검증

[child-results-after.json](child-results-after.json)에11개 사례 각각의 실제 자식 PID·입력 SHA·종료코드·timeout·Decoder 반환 요약을 기록했다. 모두 독립 Python 자식에서3초 상한으로 실행했으며 **timeout0 / 반환코드0**이다.

- 007 재현 입력 / 잘린 Contour
- 잘린 Property
- 잘린 CCourbe suffix
- 부적절한 count101 / 0 / FFFFFFFF / 4097
- 미등록 class reference
- 미지원 schema
- 중복 Contour 합성 대조
- UNKNOWN tail 제거 대조

첫 재현 입력의 수정 후 trace는 같은 실패 상태를 한 번만 기록하고 Decoder가 반환했음을 보여준다. 이 입력에서 contour 기록은0개이며 허위 형상을 만들지 않았다.

다른 손상 사례 일부에서는 기존 heuristic Decoder가 남아 있는 contour를 반환했다. 이를 정상 Archive 판정으로 취급하지 않는다. 이 수정은 전체 파일 검증이나 손상 탐지기가 아니라 **반복 종료 보장**이다. 서로 다른 손상이 모두 같은 예외를 내야 한다고 가정하지 않았다.

G1/H1, polyline3/5, polygon5/6, circle, text/default_text **8개**는 수정 전에 새로 저장한 전체 Decoder 반환 모델/Parser 이름의 지문과 수정 후 지문이 동일하다. contour raw bytes·정점·bbox·색상 confidence·텍스트·group/chain 및 공개 반환 모델 전체를 포함한다. 근거: normal-before.json, normal-after.json, equivalence.json.

합법적인 fallback 검사는 독립 자식에서 원본 함수와 수정 함수를 대조했다. 후보가 없는 marker 이후 정상 marker를 찾는 입력과 marker가 없는 입력에서 headers와 diagnostics가 완전히 동일했다. 원본 함수는 보존 텍스트를 격리된 모듈로 읽었으며 실제 checkout을 되돌리지 않았다.

007의8개 진단 JSON도 수정 전후 완전히 동일하다. AMBIGUOUS 검사, 경계 차이, ownership=UNKNOWN, change_allowed=false를 유지하고, `NOT_RUN_UNSUPPORTED_STRUCTURE` 정책을 자동 해제하지 않았다.

## Stage D — 회귀 결과와 미완료 조건

| 실행 | 결과 |
|---|---|
| 신규008 + 기존007/006 + 관련 production Contour | **100 PASS** |
| 위 검사와001/002까지 함께 실행 | **113 PASS / 2 FAIL** |
| 기존 전체 Suite 기준(007 after-suite 원본) | **1469 PASS / 17 FAIL** |
| 수정 후 기존 전체 Suite | **1465 PASS / 21 FAIL** |

001/002의2개 실패는 H/G1 예측 경로가 immutable execution-lock에 고정된 contour_parser.py의 과거 SHA와 달라졌기 때문이다. Native Reader 자체나007 진단의 실패가 아니다. 하지만 이 두 검사를 통과했다고 기록하지 않는다. 원본 lock을 수정하거나 검사 우회를 넣지 않았다.

전체 Suite의 기존17개 실패 ID는 모두 남았고, 다음4개가 추가됐다.

1. `test_source_integrity_policy.py::test_every_committed_source_baseline_matches_checkout[historical:src/type3_clipboard_codec/parsers/geometry/contour_parser.py]`
2. `test_source_integrity_policy.py::test_adapter_text_mutation_fails_integrity`
3. `test_text_slot_candidate_v2_migration.py::test_exact_corpus_and_unchanged_other_sources`
4. `test_text_slot_family_shadow_cli.py::test_cli_bounded_output[args1]`

앞의3개는 canonical source SHA 고정과 새 guard의 소스 변경이 충돌한다. 기존17개 중 `test_all_runtime_outputs_and_source_bytes_unchanged`도 과거 runtime_outputs_equal 실패보다 앞선 source SHA 검사에서 먼저 실패하도록 원인이 바뀌었다. 이를 기존 실패와 같은 원인이라고 숨기지 않았다.

추가 CLI 출력 실패는 임시 historical replay 복사본과 **별도 Python 실행**으로 인과를 분리했다. source integrity 보고가 guard 변경을 감지하면서 JSON이 **99,846 → 100,014바이트**로168바이트 늘어,100,000바이트 상한을14바이트 초과한다. 임시 대조만 과거 source 파일로 바꾸었으며 실제 checkout·baseline·fixture·상한 값은 수정하지 않았다. 근거: output-cap-cause.json.

상세 실패 ID·원인 비교는 [suite-comparison.json](suite-comparison.json), 실제 로그는 targeted-tests.txt / guard-and-diagnostic-tests.txt / after-suite.txt다. 기대값·fixture 수·frozen baseline을 변경해 통과시키지 않았다. 따라서 “신규 실패0” 또는 전체 회귀 완료를 선언하지 않는다.

## 보존·남은 문제·다음 결정

[before.json](before.json)과 [preservation-final.json](preservation-final.json)에 허용된 소스1개 외 무변경 및 SHA를 기록했다. diff check도 통과했다. Type3/Clipboard/Native/DLL/PLG/Ghidra·업무 문서를 조작하지 않았고 업무 모드 OFF를 유지했다.

아직 남은 문제:
- 승인된 production 변경과 historical 소스 고정 잠금·보고서 출력 정책을 함께 유지할 버전 관리 계약이 필요하다. 기존 frozen 기록을 덮어쓰는 방식으로 해결하지 않는다.
- 일반 Decoder는 여전히 부분 추출 기반이며 schema/reference/Archive 유효 길이를 전부 검증하지 않는다. 다른 루프·임의 손상 입력 전체의 종료나 메모리 상한을 보장하지 않는다.
-007은 계속 손상 구조에서 Decoder 미실행 정책을 유지한다. 이번 guard만으로 그 정책을 바꾸지 않는다.

최소 guard와 그 검증 근거는 준비됐지만 전체 회귀 게이트가 미충족이므로 최종 상태는 PARTIAL이다. 추가 baseline/lock 정책 변경이나 별도 기능 개발은 이번 작업에서 실행하지 않는다.
