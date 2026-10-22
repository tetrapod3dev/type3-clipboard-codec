# Archive / Native Serialize 교차 검증

**ARCHIVE_CROSSWALK_PARTIAL**. 실제 G1/H의 기록 순서와 Native 저장 명령을 연결하는 제한적 읽기 진단을 작성했다. 클래스 참조 전체 해석·범용 Parser·쓰기 허가로 승격하지 않는다. **H 실기는 별도 승인 전이므로 NOT_EXECUTED**이며 Runtime 판정을 내리지 않는다.

## 1. 확정된 Native 기록 규칙

정확한 MFC80 SHA `8204dbcc054c1e54b6065bacb78c55716681ad91759e25111b4e4797e51d0aa3`, matched PDB SHA `3de04172355214be3c9f6851ccb2ef785efb3c2c900084036dbe12919ef1202a`, RSDS/age14를 재확인했다. Maude SHA는 `eded4261fe6df1f22ceb098648188a6d789c1b6eed5a713a97e0e0e52a895f91`다. 파일 읽기·명령 디코딩만 했으며 DLL을 로드/실행하지 않았다. [native-evidence.json](native-evidence.json)에 해당 범위의 실제 bytes·명령을 저장했다. 기존 Ghidra 출력과 CFG를 재사용하고 CPropertyExtend의 기존 reachable 명령 **507개**를 현재 바이너리 bytes와 재대조했다. 기존 Ghidra DB는 변경하지 않았다.

- `CArchive::MapObject` RVA **0x2875F**: 새 저장 map에서 null을 0으로 등록하고 archive+0x34 카운터를 1로 설정한다. non-null 사전 매핑은 카운터를 증가시킬 수 있다.
- `WriteClass` **0x28882**: 새 클래스는 WORD FFFF → RuntimeClass Store → 현재 map count를 클래스에 배정하고 증가. 재사용 클래스는 작은 ID에 0x8000을 OR한다. 큰 ID는 확장 경로가 따로 있다.
- `CRuntimeClass::Store` **0x27C14..0x27C4D**: 이름 길이 취득 → schema의 WORD → 이름 길이 WORD → 이름 bytes를 기록한다. 이전 004에서 미분석이었던 직접 위임 구간을 이번에 확인했다. 새 `CPropertyExtend` 기록은 FFFF + schema5 + 길이15 + 이름 = 21바이트다.
- `WriteObject` **0x28562**: WriteClass 뒤 객체도 같은 count에서 별도 등록·증가한 뒤 virtual+8 Serialize 호출. 클래스 번호와 객체 번호는 별개 증가 단계를 공유한다.
- `ReadClass` **0x28927**, `ReadObject` **0x285F3**: 작은/확장 tag 분기, 클래스/객체 구분, map 범위 및 분류 확인과 class/object 등록을 대응시킨다. 정적 확인이며 실제 복원 호출은 하지 않았다.

## 2. G1/H의 제한적 클래스·객체 등록 대조

기존 E/F의 첫 descriptor 후보 offset70을 G1/H에 적용하지 않았다. G1/H의 `000000000100` 프리픽스 뒤 첫 `CZone` descriptor는 **[6,17)**이다. 기존 base walker로 다음 시작을 상대 cursor로 따라가며 문자열 검색으로 재동기화하지 않았다.

다음 표의 ID는 **새 unseeded Archive를 byte6에서 시작하고, 검토 구간에 추가 MapObject/가상 직접 목록 데이터가 없다는 조건** 아래 도출한 값이다. Native 영속 객체 ID가 아니다.

| 기록 위치 | 기록/이벤트 | 조건부 등록 |
|---|---|---|
| [6,17) | 새 CZone | class1, object2 |
| [163,165) | 0x8001 | CZone 재사용, object3 |
| [311,324) | 새 CCourbe | class4, object5 |
| [470,484) | 새 CContour | class6, object7 |
| [774,795) | 새 CPropertyExtend | class8, object9 |
| [931,933) | 0x8001 | CZone, object10 |
| [1079,1081) | 0x8004 | CCourbe, object11 |
| [1227,1229) | 0x8006 | CContour, object12 |
| [1519,1521) | **0x8008** | **CPropertyExtend**, object13 |

G1/H0-A/H1 모두 같은 상대 호출·바이트 순서가 byte1657까지 재현된다. `crosswalk.json`의 event/tree는 **위 조건이 붙은 진단 모델**이다. 나머지 6535바이트는 해석하지 않았고 padding이라고 단정하지 않는다.

**확인 범위:** 단순히 8이라는 값이나 클래스명 거리로 연결하지 않고, WriteClass/WriteObject의 공용 등록 순서와 실제 필드 크기에서 위 순서를 도출했다. **미확정 범위:** 제품의 Archive 생성/선행 MapObject와 byte6 진입 문맥 자체는 확인하지 않았다. CObDaoCtn의 별도 virtual+0x12C/+0x130 직접 Serialize 목록이 이 경로에서 0기여라는 독립 증명도 없다. 따라서 class8 연결은 강한 조건부 대응이며 일반 class reference 해석을 확정했다고 표시하지 않는다. 기존 locator의 UNKNOWN/change_allowed=false는 수정하지 않았다.

## 3. 색상 120/132의 실제 기록 위치

핵심 발견은 **이 값들을 CPropertyExtend 자체의 색상 멤버로 볼 근거가 없다는 것**이다. 검토 표본에서는 CPropertyExtend 본문이 끝난 뒤 CCourbe의 여섯 DWORD가 이어진다.

- `CContour::Serialize` **0x1E610**: base → member+0x130의 DWORD → embedded `CPtCtr4DArray` virtual Serialize → this+0xB0을 MFC WriteObject로 기록. **0x1E686**의 thunk0x9B1E2는 MFC ordinal6303 WriteObject다.
- CContour constructor **0x25AA0**에서 this+0xB0은 `CPropertyExtend` ctor0x5FF50, this+0x134는 `CPtCtr4DArray` ctor0x18240으로 연결된다. 배열 vtable의 Serialize slot+8은 **0x1F940**이다.
- `CPropertyExtend::Serialize` **0x60370**는 40바이트 → int count 및 count×4 → 16바이트 → double count 및 count×8 → 32바이트 → 첫 문자열 길이/bytes 및 optional child flag → 두 번째 문자열 길이/bytes 및 optional child flag 순서다. 비어 있는 가변 항목의 현재 기록은 **112바이트**다. 의미 불명 필드에 임의 이름을 붙이지 않았다. optional child가 있으면 이번 진단은 명시적으로 중단한다.
- `CCourbe::Serialize` **0x30940**, base 호출0x3094A 뒤: **0x30963, 0x30973, 0x30983, 0x30993, 0x309A3, 0x309B3**에서 this+**B0/B4/B8/BC/C0/C4**를 각각 DWORD로 기록한다.
- `CCourbe::SetColor` **0x2F7F0**는 같은 입력을 **this+B8 및 this+C4 양쪽**에 저장한다. `CCourbe::GetColor(CPtrList&)` **0x2F810**은 **C4** 값을 색상 목록에 추가한다. B8/C4 두 저장 위치가 색상 API와 연결됨은 확인했지만 B8의 별도 의미, 선색/채움색 같은 역할 구분은 UNKNOWN이다.

| G1/H 기록 | Property 본문 | Property 끝 / CCourbe suffix | B8 색상 | C4 색상 |
|---|---|---|---|---|
| 첫 curve | [795,907) | [907,931) | [915,919) | [927,931) |
| 둘째 curve | [1521,1633) | [1633,1657) | [1641,1645) | [1653,1657) |

즉 **112+8=120, 112+20=132**다. G1에서는 둘째 curve가 R2이고, 생성 순서를 바꾼 H에서는 첫 curve가 R2다. 진단이 계산한 suffix 범위는 보존된 field locator 결과와 세 표본 모두 일치했다. 각 멤버의 전체 소유권이나 UI 그룹 일반 모델을 확정한 것은 아니다.

## 4. 정점 수와 가변 구조

`CPtCtr4DArray::Serialize` **0x1F940**: count를 DWORD로 기록(0x1F986), 각 요소의 정확한 타입 검사를 거쳐 virtual+8 Serialize를 호출(0x1F9C3)한다. count가 달라지면 반복 횟수가 달라지며, 일부 null/타입 불일치 요소는 기록을 생략할 수 있으므로 count×고정크기를 모든 입력에 적용할 수 없다.

`CPtCtr4D::Serialize` **0x61460**: LGeom `CVect4D::Serialize`를 호출한 뒤 this+0x28 DWORD 4바이트를 추가한다. 현재 실제 사각형의 4×36바이트는 기존 contour 파서 및 바이트 대조와 맞는다. 이번에는 LGeom의 부모 serializer 본문을 추가 추적하지 않았으므로 **36바이트 전체를 새롭게 Native 코드만으로 증명했다고 주장하지 않는다**. 현재 crosswalk는 이 검토된 사각형 기록 폭에만 제한한다. 다른 객체/정점 타입은 별도 근거가 필요하다.

Property의 int/double 배열·문자열·optional child가 달라지면 **112가 고정이 아니다**. 이미 식별된 contour 시작과 검증된 요소 타입·기록 폭, count 및 실제 property body 길이에서 다음 색상 필드를 계산할 제한적 근거는 생겼다. 그러나 형상과 무관하게 property 시작을 항상 찾는 범용 경로는 확보하지 못했다. 경험적120/132를 모든 객체에 적용하면 안 된다.

## 5. 작동 코드·검증과 보호

`crosswalk.py`: 고정 프리픽스/지원 클래스·schema에 한정해 cursor, count, property 길이, 조건부 등록 이벤트, CCourbe 색상 suffix를 출력한다. object/null/확장 reference, 미등록 class reference, 큰 길이/count, optional property child, 미지원 타입은 거부한다. 절대 색상 offset 하드코딩이나 색상 검색·최근접 매칭을 하지 않는다. 알려지지 않은 구간을 건너뛰거나 재동기화하지 않는다. 일반 Decoder/Encoder를 수정하지 않았다.

**8/8 PASS**, `tests.txt`: G1/H 재현, 절단, 미등록 참조, 미지원 optional branch 거부. 이 검사 수는 Native 안전성·실기 성공 증거가 아니다. Codec 루트에서:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe research/archive-crosswalk-001/crosswalk.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider research/archive-crosswalk-001/test_crosswalk.py
```

기존 함수 근거 출처는 automation 프로젝트의 `type3-clipboard-writeclass-004`, `type3-clipboard-serialize-helper-002`, `type3-clipboard-base-serialize-003`, `type3-native-deserializer-reuse-001` 및 `_reverse_engineering/data/phase2a_cfg_Maude.dll_60370.json`, `phase2c_nested_maude.txt`다. 상위 Paste 재사용 연구나 Native 수명 조사로 되돌아가지 않았다.

기존 Codec 파일 SHA 변경 0개(`preservation.json`), G1/H·profile/lock·H 후보 보존. H 후보 Zone SHA `f699289a52535d3d9dc3cf8098ae03d6fb8b2a7017109109f66c5f3833105885`, Version SHA `33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f`를 파일로만 재확인했다. 업무 모드 **OFF**. Type3·Clipboard 접근·문서 저장/닫기/폐기·DLL/PLG 수정·Native 실행/Hook은 하지 않았다.

## 다음 최소 결정

H 후보는 기존 OFFLINE_READY 그대로이며, **별도 승인 후에만** 실제 빈 별도 시험 문서에서 Clipboard 덮어쓰기 → Paste 정확히1회 → Copy1회/재Copy 비교를 진행할 수 있다. 빈 문서·기존 문서와의 분리가 불확실하면 Paste하지 않는다. 이번에는 준비 파일 확인까지만 수행했다.

구조 분석은 이번 대응을 토대로 한 제한적 근거이며, Archive 초기 map 문맥과 추가 직접 목록의 기여가 해결되기 전 일반 Parser나 범용 쓰기 허가로 통합하지 않는다. 추가 사각형 생성·무제한 Native 추적을 자동으로 진행하지 않는다.
