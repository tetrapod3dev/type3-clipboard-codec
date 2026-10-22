# Native Archive 구조 확장 검증 002

**ARCHIVE_STRUCTURE_EXTENDED_VERIFIED — 가변 Contour 기록 폭·경계 및 대상 파생 클래스의 추가 목록 0기여에 한정.** Clipboard Copy의 Archive 생성 문맥은 여전히 미확정이다. 범용 Parser, 전체 class/object map 또는 객체 소유권을 검증했다는 의미가 아니다.

## Stage A — Copy / Archive 초기화: 미확정, 제한 조사 종료

기존 `type3-paste-reuse-final-001`, `type3-native-deserializer-reuse-001`, `_reverse_engineering/reports/phase1_summary.md`를 재사용했다. 기존에 포착한 CommonCmdLaser RVA **0x6F30**은 Grid 문자열 복사로 TypeEditZone 도형 Copy가 아니다. Type3의 COleDataSource/CSharedFile 관련 import 존재는 실제 Copy handler와 Archive 생성자 호출을 연결하는 증거가 아니다. BaseDoc/CommonCmd/TypeEditDLL의 제한된 export 표면에서도 해당 이름의 명시적 Copy 진입점은 찾지 못했다. 이를 제품에서 경로가 없다는 결론으로 해석하지 않는다.

| 질문 | 결과 |
|---|---|
| 실제 TypeEditZone Copy 담당 함수/RVA | NOT_FOUND_IN_SCOPE |
| CArchive 생성자 옵션 및 CFile/CMemFile/CSharedFile 실제 receiver | UNKNOWN |
| 첫 WriteObject 전 MapObject/사전 등록 | UNKNOWN |
| 6바이트 `000000000100` 생성 위치 | UNKNOWN |
| 첫 CZone descriptor byte6의 원인 | 표본에서 재현되나 생성 경로 미확정 |

마지막으로 확정된 **Archive 라이브러리 함수**는 matched MFC80 `CArchive::WriteObject` RVA **0x28562**, `MapObject` **0x2875F**다. 이 주소는 제품 Copy caller의 주소가 아니다. fresh map의 null=0 / next count=1 규칙은 기존 근거대로지만 실제 Copy가 fresh/unseeded인지 증명하지 못했다. 따라서 001의 초기 map 가정은 유지된다. 추가 광범위한 Copy/Paste 호출 그래프 추적은 하지 않았다.

## Stage B — 추가 직접 Serialize 목록: 대상 클래스에서 0기여 확인

Maude SHA `eded4261fe6df1f22ceb098648188a6d789c1b6eed5a713a97e0e0e52a895f91`를 재대조하고 constructor의 vptr 기록과 vtable 실제 슬롯을 연결했다. 파일 bytes만 읽었으며 Native 함수를 실행하지 않았다. 정확한 명령과 표는 `native-evidence.json`에 있다.

| 동적 클래스 | constructor / vtable RVA | +0x12C count target | +0x130 element target |
|---|---|---|---|
| CZone | ctor0x9A730 / 0xB1F04 | **0x9A3B0: xor eax,eax; ret** | 0x9A3C0: xor eax,eax; ret4 |
| CCourbe | ctor0x31690 / 0xAD344 | **0x30910: xor eax,eax; ret** | 0x30920: xor eax,eax; ret4 |

`CObDaoCtn::Serialize`의 **0x5ACBE**는 먼저 `SerializeDeque2`(RVA0x5AB00)를 호출한다. 이 helper는 count와 WriteObject 항목을 기록한다. 이후 **0x5ACD5**에서 virtual+0x12C를 호출하고 결과가1 미만이면 direct loop를 건너뛴다. 반복 시 +0x130 결과에 virtual+8 Serialize를 직접 호출하므로 다른 파생 클래스에서는 추가 bytes를 기록할 수 있다.

현재 G1/H 및 추가 표본 경로의 CZone/CCourbe는 count override가 명령상 항상0이므로 **해당 추가 직접 loop는 실행되지 않는다**. 이는 SerializeDeque2가 비었다는 뜻이 아니다. root/curve의 helper 목록은 실제로 객체를 기록한다. CObDaoCtn 일반형과 다른 동적 클래스에는 이 결론을 확장하지 않는다. 001의 기존 코드를 수정하거나 그 보고서의 과거 가정을 재작성하지 않고 새 근거로 분리했다.

## Stage C — 가변 Contour와 Native 36바이트 근거

이번에 LGeom의 실제 `CVect4D::Serialize` RVA **0x11CD0** 저장 경로를 확인했다. `native-evidence.json`에 LGeom 파일 SHA와 export, 명령 bytes를 기록했다.

- 객체 메모리 **+8/+0x10/+0x18/+0x20**의 값을 각각 Archive cursor에 qword로 기록하고 cursor를8씩 증가시킨다. 실제 qword 저장 명령은 **0x11D0D, 0x11D4D, 0x11D8D, 0x11DCD**다. 저장 경로의 총 기록은 **32바이트**다.
- Maude `CPtCtr4D::Serialize` **0x61460**는 위 LGeom import를 호출한 뒤 메모리 member **+0x28**을 DWORD로 추가한다(Write4 호출0x61480). 따라서 해당 타입의 기록은 **32+4=36바이트**다.
- `CPtCtr4DArray::Serialize` **0x1F940**의 count Write4(0x1F986)와 typed 요소 virtual Serialize 루프(0x1F9C3)는 001 근거를 재사용했다. null/타입 불일치 항목이 있으면 기록이 생략될 수 있으므로 모든 임의 배열에서 count×36이라고 가정하지 않는다. 현재 표본은 연속 기록과 count가 일치하고 기존 Decoder의 contour raw bytes와도 대조했다.

아래 범위는 **각 fixture에서 순차 cursor로 계산한 파일 byte offset**이며 Native member offset과 다르다. 새 클래스 검색으로 cursor를 재동기화하거나 불명 구간을 padding으로 넘기지 않았다.

| 저장 표본 | Native 기록 클래스 경로 | 점 count / contour 기록 범위 | Property 본문 | CCourbe suffix / 색상 쌍 |
|---|---|---|---|---|
| polyline_3_points | CZone→CCourbe→CContour→CPropertyExtend | 3 / [482,590), 108B | [611,723) | [723,747), 731/743 |
| polyline_5_points | 동일 | 5 / [482,662), 180B | [683,795) | [795,819), 803/815 |
| polygon_5_sides | 동일 | 5 / [482,662), 180B | [683,795) | [795,819), 803/815 |
| polygon_6_sides | 동일 | 6 / [482,698), 216B | [719,831) | [831,855), 839/851 |
| default_circle | 동일 | 8 / [482,770), 288B | [791,903) | [903,927), 911/923 |
| text/default_text | 미해석 | **prefix 단계에서 거부, cursor0** | 미조사 | 미조사 |

원 표본의 UI 명칭상 폴리라인·폐다각형·원이라는 서로 다른 형상도 이 입력에서는 같은 Native 직렬화 클래스 계열로 관찰됐다. 원을 별도 Native CCircle 클래스라고 꾸미지 않는다. 서로 다른 점 수에 따라 contour 종료/새 Property 기록/색상 위치가 **36바이트 단위로 이동**한다. 단순 화면 유사성·곡선 정확성·원 반지름 보존을 새로 검증한 것은 아니다. 요소 마지막 DWORD의 원문은 의미를 새로 단정하지 않는다.

문자 fixture는 첫6바이트가 검토된 prefix와 달라 즉시 거부했다. 문자열 검색으로 CParagraphe를 찾아 강제 파싱하지 않았다. 이 입력에서 실제 Native 클래스 경로를 확인했다고 주장하지 않는다. 문자/다른 prefix·클래스, null/타입 불일치 요소, 비어 있지 않은 optional Property child, 확장 참조 등은 계속 미지원이다.

## 기존 G1/H와 비교·범위

추가 표본의 조건부 map은 CZone class1/object2 → CCourbe class3/object4 → CContour class5/object6 → CPropertyExtend class7/object8이다. G1/H의 CZone 중간 wrapper 및 객체 등록 단계가 달라 class8이었던 것과 구분해야 한다. ID는 Archive 범위의 조건부 등록 순서이며 문서의 영속 객체 ID가 아니다.

5개 표본의 Property 본문은 가변 count/문자열이 비어 있어 각각112바이트였고, 그 뒤 **CCourbe의 24바이트 suffix**가 존재한다. +0xB8/+0xC4는 Native 메모리 멤버이고 파일 위치는 위 표처럼 변한다. 120/132는 이 **112바이트 Property 경우에만** 대응하는 경험적 상대 위치다. 생산 파서나 일반 패치 규칙으로 적용하지 않았다. 색상값이 모두 검정인 이번 표본만으로 다양한 색상 소유권을 다시 검증했다고 주장하지 않는다.

G1/H의 001 결과는 새 코드에서 재계산 후 보존 JSON 전체와 일치함을 검사했다. 001 코드·표본·profile/lock·H 후보는 수정하지 않았다.

## 실행 코드·테스트·보호

`analyse_fixtures.py`는 001의 bounded Reader를 그대로 사용하되 사각형 그룹 전용 locator 단계와 분리하여 기존 fixture의 Native 기록 범위를 대조한다. 기존 Decoder는 비교에만 사용한다. 원 Decoder/Encoder API, 색상 패치 로직, class ownership 정책은 변경하지 않았다. 전체 tail은 계속 UNKNOWN이며 추가 객체나 padding이라고 판정하지 않았다.

**15/15 PASS**: 새 검사7 + 기존001 검사8, `tests.txt`.

초기 새 검사 하나는 문자 fixture가 prefix 검사보다 뒤의 CParagraphe 분기에서 거부될 것이라고 잘못 기대해 실패했다. 실제로는 cursor0에서 더 일찍 거부됐다. 새 검사만 그 거부 지점으로 바로잡았고, 파싱 규칙·기존 테스트 기대값·fixture는 변경하지 않았다. `tests-initial.txt`에 최초 실패를 보존했다.

Codec 루트에서:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe research/archive-crosswalk-002/analyse_fixtures.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider research/archive-crosswalk-002/test_extension.py research/archive-crosswalk-001/test_crosswalk.py
```

`fixture-crosswalk.json`에 원본 fixture/payload SHA, 순차 event/tree, contour/Property/suffix 범위, 거부 사유를 보존했다. `preservation.json`은 작업 전 존재하던 Codec 파일의 SHA 변경0개와 업무 모드 **OFF**를 확인한다. Type3·Clipboard·기존 미저장 문서에 접근하지 않았고 H Paste도 수행하지 않았다. DLL/PLG/Ghidra DB 수정·Native 호출/Hook·새 패치 생성은 없었다. 기존 전체 Codec 회귀의 17개 실패를 재판정하거나 테스트를 수정하지 않았다.

## 다음 구현에 필요한 최소 증거

가변 Contour 기록 폭은 현재 자료로 검증했으므로 같은 사각형·정점 샘플을 더 만들 필요는 없다. 다음 단일 장애물은 **실제 TypeEditZone Copy 함수의 CArchive 생성과 첫 WriteObject 전 문맥**이다. 그 caller/RVA와 생성 옵션·선행 MapObject·6바이트 prefix 기록이 연결되는 기존 함수 증거가 필요하다. 현재 범위에서 이를 찾지 못했으므로 자동 추적을 확대하지 않는다. 실제 관찰이 필요해지면 별도 승인된 시험 계획부터 수립한다. 객체 소유권과 원본 선택 적용은 별도 미해결 과제다.
