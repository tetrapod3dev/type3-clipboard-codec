# H 독립 그룹 최소 패치 결과

**H_EXACT_PATCH_OFFLINE_READY**. 기존 H1 한 건에 한정해 고정 프로파일/field locator가 계산한 R2 색상 구간을 수정했다. 실제 Type3·Clipboard는 사용하지 않았다. Runtime Verified가 아니다.

## 기준과 원본 보존

시작 시 Codec `master` HEAD는 `87bc59179f1b9fa518ea333d8f92d0c4bf022cc9`, Git 작업 트리는 clean이었다. 지시문과 달리 이관 자료는 이미 커밋되어 있었다. commit/reset/checkout/clean/push는 하지 않았다. 새 `experiments/h-exact-patch-001/`만 추가했다.

이관 manifest의 원본 증거·코드 99개 SHA, 고정 프로파일, 현재 실행 lock 및 H0/H1 최초 예측·comparison·UI 대응을 검증했다. 실행 lock은 시작 스냅샷 SHA와도 대조했다. H1 입력 SHA는 이관 자료·comparison·고정 허용 SHA가 모두 같아야 한다. H로 프로파일을 학습하지 않았다.

- 프로파일 SHA: `d0f179eaee2c9e625a936f7ce7ad7c3db0d78928df5a782bfd4a18d8130d3197`
- 입력 H1 Zone SHA: `1e2d803df75b56385d97ee8a0021ae94b80cb1da2cd37f96abdf95e4242957af`
- **출력 후보 Zone SHA: `f699289a52535d3d9dc3cf8098ae03d6fb8b2a7017109109f66c5f3833105885`**
- Version SHA: `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f` — 원본 32바이트 그대로
- 입력/출력 Zone: 모두 8192바이트

`preservation.json`: 기존 Codec 파일 **803개** SHA 검사, 변경 0개. G1 원본·코드·성공 후보·재Copy 및 이전 이관 증거·lock은 유지됐다. 원본 automation 저장소도 Git 변경 없음. 캐시/가상환경/Git/IDE는 내용 검사에서 제외했다.

## 패치 범위와 조건

`h_exact_patch.py`의 `patch_h1()`은 고정 H1 SHA/Version, 단일 그룹 후보·사각형 후보 2개, UI bbox와 색상, 이전 예측의 동일성 및 필드 비중첩을 검사한다. R1/R2는 순번 대신 실기 bbox 대응으로 구분한다.

수정 구간은 locator의 `mapping['R2']['color_pair_ranges_candidate']`에서 가져온다. **915/927은 build/test에서 결과를 검사하는 기대값일 뿐 패치 위치 입력이 아니다.** 조건 불일치·모호한 매핑·손상 입력은 후보 생성 전에 실패한다. 기존 locator의 `change_allowed=false`는 그대로다.

| 대상 | 계산된 구간 | 입력 → 출력 |
|---|---|---|
| R2 | `[915,919)`, `[927,931)` | `64 FF CC 00` → `98 CC 98 00` |
| R1 | `[1641,1645)`, `[1653,1657)` | `30 60 CC 00` 유지 |

실제 변경 offset은 **915, 916, 917, 927, 928, 929**의 6개다. 그 외 모든 바이트는 동일하다. 원본 H1은 수정하지 않았고, `candidate/typeeditzone.bin`과 `candidate/typeeditzone_version.bin`을 별도로 만들었다. 기존 출력과 충돌하면 덮어쓰지 않는다.

Decoder의 그룹 후보 1개·사각형 후보 2개, 두 객체 bbox·contour·좌표·크기가 유지됐다. 수정본 R2는 Army Green, R1은 Navy Blue로 확인됐다. 수정 후 field locator 결과도 원본 H0 UI bbox/색상 대응과 일치했다.

H0-A 대비 후보의 차이는 **110바이트**다. 이는 기존 base walker의 GUID raw 후보 범위 안에 있으며 미분류 차이는 0개다. 색상 외 차이를 무해하다고 선언하지 않는다. GUID의 영속 identity·구성원 Serialize 전체 경계·일반적인 소유권은 미확정이다.

## 검증

- H exact 및 G1/H 재현: 10개 PASS. 정상 후보, 잘못된 SHA/길이, 절단·추가·손상, 다른 색상, H0/G1/이미 패치된 입력, 잘못된 Version, 원본 불변을 확인했다.
- 기존 005/006/G1 exact 검사 28개 PASS. 합계 **38/38 PASS**, `tests.txt`.
- 기존 Codec Decoder·혼합 색상·그룹·사각형·형상 불변 관련 검사 **25/25 PASS**, `codec-related-tests.txt`.
- 이번 관련 범위 합계 **63 PASS**, 새 실패 없음. 전체 Codec 테스트는 재실행하지 않았다. 이전 전체 회귀의 17개 실패는 과거 baseline으로 유지하며 이번 성공 수에 포함하지 않는다. 기대값·기존 fixture를 수정하지 않았다.

Codec 루트에서 재현:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe research/group-color/experiments/h-exact-patch-001/h_exact_patch.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider research/group-color/experiments/h-exact-patch-001/test_h_exact_patch.py
```

정확한 입력·출력 SHA, 전체 차분 및 판정은 `verification.json`, 테스트는 `test_h_exact_patch.py`에 있다. 패치 코드는 일반 Codec API가 아닌 이 폴더의 실험에만 존재한다. 생산 Decoder나 Serializer/Encoder를 변경하지 않았다.

## 실기 준비와 다음 결정

이 후보는 별도 승인을 받은 뒤 원본 시험 문서와 분리된 빈 시험 문서에 Paste 1회 → 재Copy하여 확인할 **입력 준비 완료** 상태다. 승인 전 Clipboard 등록·Paste·Copy·Type3 실행/문서 조작은 하지 않는다. 과거 PID의 현재 생존 여부를 조회하거나 그 PID로 조작하지 않았다. 미저장 문서 저장·닫기·폐기, DLL/PLG 변경, Native 호출은 하지 않았다. 업무 모드는 **OFF**다.

승인 후 최소 비교는 그룹 1개, R1 Navy Blue/R2 Army Green, 두 bbox·contour, 후보와 재Copy Zone/Version 전체 바이트다. 일치하지 않는 정규화가 발생하면 별도 기록하며 성공으로 가정하지 않는다. 실기가 성공하면 같은 두 사각형 색상 시험의 반복 확장 대신 가공 대상 분류·업무 자동화 연결 방식을 결정한다. 원본 객체 선택 적용은 여전히 별도 과제다.
