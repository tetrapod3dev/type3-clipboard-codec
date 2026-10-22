# Codec 프로젝트 이관 결과

**CODEC_MIGRATION_VERIFIED** — 저장 증거를 그대로 이관하고 Codec 안에서 G1/H 결과를 재현했다. 기존 Codec 전체 테스트에는 이관 전부터 있던 17개 실패가 그대로 남는다. 전체 테스트가 모두 통과했다고 주장하지 않는다.

## 저장소와 보존

| 저장소 | 브랜치 / 이관 전 HEAD | 이관 전 상태 |
|---|---|---|
| typeedit-automation | master / `b42abe9cd9a72a9d0116080a57097c06959c9671` | clean |
| type3-clipboard-codec | master / `27d98ad08fd0d46e6d79a8efeba466a9b5620334` | clean |

기존 파일을 덮어쓰거나 reset하지 않았다. 원본 프로젝트는 변경하지 않았으며 Codec에는 새 `research/group-color/`만 추가했다. 커밋은 수행하지 않았다.

Codec의 `core.autocrlf=true`를 확인해 이관 폴더의 `.gitattributes`에 `* -text`를 추가했다. 향후 Git checkout의 줄바꿈 변환으로 증거·원본 코드·실행 lock의 raw SHA가 달라지지 않도록 이 폴더만 제한한다. 기존 저장소 설정은 변경하지 않았다.

원본 표본·예측·결과·화면·코드 **99개**의 경로·크기·SHA와 중복 검사는 [migration-manifest.json](migration-manifest.json)에 있다. 복사 후 원본과 대상의 SHA가 모두 일치한다. [preservation-after.json](preservation-after.json): 기존 원본 파일 5920개, 기존 Codec 파일 673개를 비교해 변경 0개다. Git/가상환경/캐시/IDE 디렉터리는 내용 검사에서 제외했다.

003의 유효 S1/S2/U0/G0-A/G0-B/G0-R/G1, 004의 후보·실기 재Copy·결과·필요 화면, 005의 locator 및 검사, 006의 원본 H 표본·최초 예측·comparison·UI 관찰·화면을 이관했다. 동일한 H0 반복 캡처와 후보/재Copy는 서로 다른 관찰 증거이므로 각각의 bundle을 유지했다. 32바이트 Version은 기존 Codec과 동일 SHA지만 bundle별 독립 증거를 위해 보존했다. Codec의 기존 Decoder·geometry fixture·src는 복사하지 않고 재사용한다.

001/002의 별도 실패 연구·전체 Ghidra DB·제품 Native DLL·API 소스는 가져오지 않았다. 기존 함수 계약의 출처는 원본 프로젝트 `research/feasibility/type3-clipboard-base-serialize-003`, `type3-clipboard-serialize-helper-002`, `type3-clipboard-writeclass-004`, `type3-clipboard-color-patch-001`, `type3-clipboard-group-member-patch-002`다. 이 경로는 참고 문헌이며 실행 의존성이 아니다.

## 원본 코드와 실행 코드

| 실행 사본 | 변경 범위 |
|---|---|
| 005/field_locator.py, test_locator.py | Codec 루트 자동 해석, 기존 표본 상대 경로 유지, 재계산 출력 이름 분리 |
| 006/prediction_check.py | 새 실행 lock의 Codec 루트 상대 경로 검증, 비교 출력 `recomputed-comparison.json` 분리 |
| 006/test_preparation.py | lock 파일명을 새 실행 lock으로 연결 |
| base-003/walk_base.py | bounded walker/diagnose 유지, 이관 범위 밖 E/F 전용 실행 진입부 제외 |
| 004/prepare_patch.py, test_patch.py, verify_runtime.py | Codec 루트 해석, 재계산 보고서 이름 분리; exact-G1 패치 조건 유지 |

위 8개 원본은 `provenance/original-code/`에 바이트 그대로 보관했다. 원본·실행 코드 SHA와 대응 관계는 manifest, 정확한 변경은 `provenance/code-diffs/`에 있다. `conftest.py`는 원본 코드 스냅샷의 중복 pytest 수집만 제외한다. 실제 파싱·소유권·지원 범위는 변경하지 않았다.

`profile-lock.json`은 과거 절대 경로를 포함한 원본 증거 그대로다. 실행 시 읽는 **별도 `execution-lock.json`**은 이관 코드 및 현재 Codec src의 SHA를 Codec 루트 상대 경로로 검증한다. 두 lock을 동일한 증거로 취급하지 않는다.

고정 프로파일 SHA:
`d0f179eaee2c9e625a936f7ce7ad7c3db0d78928df5a782bfd4a18d8130d3197`

H 재학습은 하지 않았다. 이관 검증에서는 `learn_profile`을 호출하면 즉시 실패하도록 막았다. 원래 예측 JSON·comparison·profile·UI 관찰은 덮어쓰지 않고 재계산값과 대조했다. H0 선예측/H1 선예측 및 SHA 충돌 차단 검사를 유지했다. `verify_migration.py`의 파일 읽기 감사에서 원본 프로젝트 접근을 금지했고 접근 0건으로 실행됐다.

## 동등성 결과

| 항목 | 결과 |
|---|---|
| G1 | 작은 R1 Navy Blue / 큰 R2 Turquoise, R2 1641/1653 재현 |
| G1 exact 패치 | 메모리에서 Army Green 후보 재현; 보존 후보·실기 재Copy와 Zone/Version 동일 |
| G1 후보 SHA | `d70bc09ac7b8f4bfff4d131acecda4d831f99b249d4fc6f1996c2d65ae605fb8` |
| H0-A/H0-B | Zone/Version 동일 |
| H 예측 | R2 915/927, R1 1641/1653; 최초 예측 결과와 동일 |
| H 실제 차분 | 915/916/917/927/928/929, R1 색상·bbox 유지 |
| H 추가 차분 | 110바이트 GUID raw 후보, 미분류 0; 무해성 보장 안 함 |
| H 최종 판정 | `INDEPENDENT_FIELD_PREDICTION_VERIFIED`, 보존 comparison 전체와 동일 |
| 원본 증거 | 99개 SHA 일치, 최초 예측·프로파일·comparison 무변경 |
| 관련 검사 | 005 12 + 006 6 + exact-G1 10 = **28/28 PASS** |
| 기존 Codec 전체 tests | 이관 전/후 모두 **1469 PASS / 17 FAIL**, 실패 ID 집합 동일·신규 실패 0 |

[ migration-verification.json ](migration-verification.json), [migration-tests.txt](migration-tests.txt), [regression-comparison.json](regression-comparison.json), [codec-regression.txt](codec-regression.txt), [codec-regression.xml](codec-regression.xml) 참조. 이관 전 전체 로그는 도구 출력으로 관찰했고 별도 파일로 저장하지 않았으며, 관찰한 17개 실패 ID와 이관 후 JUnit 결과를 대조했다. 기존 실패는 표본 수 기대값(116/104 대비 현재139/127)과 확대된 출력 크기 제한 등을 포함한다. 범위 밖 실패를 통과시키기 위해 기존 테스트나 fixture를 수정하지 않았다.

## 실행 방법

Codec 루트에서 오프라인 검증:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe research/group-color/verify_migration.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider research/group-color/type3-clipboard-group-field-locator-005/test_locator.py research/group-color/type3-clipboard-independent-prediction-006/test_preparation.py research/group-color/type3-clipboard-group-patch-runtime-004/test_patch.py
```

검증기는 보존 입력만 사용하고 새 H 캡처·프로파일 학습·수정 Clipboard·Paste를 하지 않는다. 기존 증거 대신 별도 재계산 JSON만 기록한다. 과거 실기 성공을 다시 실행한 것으로 표시하지 않는다.

## 제약과 개발 책임

`GROUP_PATCH_RUNTIME_VERIFIED`는 특정 G1 한 건, `FIELD_LOCATOR_PARTIAL`은 쓰기 불허 후보, H 검증은 통제된 두 사각형 그룹 계열의 경험적 독립 예측이다. MFC class/reference ledger·구성원 전체 Serialize 경계·일반 소유권·원본 객체 선택 적용은 여전히 미확정이다. `change_allowed=false`, `write_permission=false`를 유지하며 범용 Encoder나 쓰기 API를 추가하지 않았다.

향후 Clipboard Decoder/속성 탐색/부분 수정/샘플 검증은 Codec 프로젝트가 소유한다. Managed·Native API, 현업 UI, 분류 흐름, 원본 선택 적용 및 Codec 연결은 typeedit-automation이 소유한다. 파서를 양쪽에 추가 구현하지 않는다.

Codec에서 저장 표본 기반 후속 개발을 시작할 상태는 확보했다. 새 지원 형식이나 Patch/Paste 실기는 별도 과제다. 이번에는 Type3·Clipboard·현재 PID를 조사하거나 조작하지 않았고, 문서 저장·닫기·폐기 및 DLL/PLG 변경을 하지 않았다. 업무 모드는 **OFF**를 읽기 확인했다. 추가 샘플·Native 분석으로 진행하지 않는다.
