# 실제 Copy 생산자 추적 003

**COPY_PRODUCER_STATIC_BLOCKED**. 지정된 제한 범위에서 TypeEditZone의 실제 발행 함수를 특정하지 못했다. 다른 Clipboard 형식의 실제 발행/Archive 경로는 확인했지만 TypeEditZone으로 재분류하지 않았다. 이전 Contour/클래스 대응 및 H 후보 상태는 유지한다.

## 실제 조사 범위와 identity

현재 EXE 디렉터리 최상위의 **244개 PE**에 대해 SHA, 정확한 TypeEditZone/Version ASCII·UTF16LE literal, 관련 named import 및 matched MFC ordinal→RVA→PDB 이름을 조사했다. 하위 디렉터리·동적 구성 문자열·리소스·수동 함수 주소 로딩까지 조사한 것은 아니다. 문자열이 없거나 import를 찾지 못했다는 이유로 기능 부재를 결론내리지 않는다. 전체 목록은 [static-evidence.json](static-evidence.json)에 있다.

MFC80 SHA `8204dbcc054c1e54b6065bacb78c55716681ad91759e25111b4e4797e51d0aa3`, PDB SHA `3de04172355214be3c9f6851ccb2ef785efb3c2c900084036dbe12919ef1202a`, RSDS/age14를 재대조했다. 이름 없는 ordinal import를 PDB public symbol로 연결했다. 동일 RVA에 여러 alias가 있는 함수는 import만으로 의미를 확정하지 않았다. 특히 일반적인 no-op/공통 stub의 COleDataSource 이름 alias를 실제 생산자라고 분류하지 않았다.

| 주요 모듈 | SHA256 |
|---|---|
| impapi.dll | `acb90662e4a5243d717dc60e4138f920a7d59645b4f54c988ee4b15b3e9d3ca0` |
| VnxGest.dll | `d854efc97a65525e76fb02ea60855e2d692698217e5fe94bf466af5292c806fa` |
| SMSTE.dll | `03d474bc8ab6ce54f410130fb64223ae04df92d277985768fcc872a9d62f54f0` |
| Maude3D.dll | `7c72f042983dee7bc2ed4ef8f0f0a8efb77ead7289e8e5ff3959a9bdbcb02304` |
| BaseDoc.dll | `68efd5f43de9d881516d03c1ac440dc29cc95855c8b3cfd7430db9045e41ddcc` |
| CommonCmd.dll | `ec5471da4877a2633bc1956ac216badb9fd986ec7a1dbdb6dbd5d073224da30d` |
| TypeEditDLL.dll | `62f2fc8fcc653746e0844d01882b86251f89de2b14d8202a551a7ed4afaf18a9` |
| Pltf.exe | `f679f2641e60a41f62326e1c68c5e2c64d2415498bb1b92019c5f2d64245e662` |
| CommonCmdLaser.dll | `7fc927dd099ca8ad848fd0e403e33da0cdc854fb06fcbe3a87823dd2fae093d3` |
| DlgMatrixDLL.dll | `f7346923e4d34f1a663b57f47bad7c27dc78ed63256cb147c206635b46c5d18b` |
| DlgVariableDLL.dll | `1c67e535d5080b5a0d19799f45fa2fcd75d6598d2d2f99e63ffbcfce447f8586` |

Clipboard 후보는 import 존재에서 끝내지 않고 실제 IAT call/jmp와 그 직전 인수 명령을 확인했다. JSON의 `code_evidence`/`import_thunks`에 RVA·instruction bytes를 보존했다. 일부 범위는 함수 전체가 아닌 명시된 코드 구간이며, 임의 시작점 디스어셈블리를 함수 경계 증명으로 사용하지 않는다.

## 확인한 발행 경로와 제외 근거

| 모듈 / 경로 | 확인한 코드 | 판정 |
|---|---|---|
| impapi.dll 함수 시작 RVA **0xB410** | **0xB45D** RegisterClipboardFormatA ← 문자열 RVA0x34488, **0xB5C6** SetClipboardData | **TypeEditCalque**, TypeEditZone 아님 |
| impapi.dll 별도 발행 구간 | **0xBF5A** 같은 형식 등록, **0xC0C0** 발행 | **TypeEditCalque**, 제외 |
| VnxGest.dll 초기화 **0x1010** | **0x101E** 등록 ← RVA0x21218, ID를 global+0x2B800에 보관, **0xEE0A** 발행 | **VNXCLP**, 제외 |
| SMSTE.dll 초기화 **0x17520** | **0x1752E** 등록 ← RVA0x4512C | **VNXCLP**, 제외 |
| CommonCmdLaser.dll **0x6F30** | 기존 Grid 문자열 Copy 근거 재사용 | TypeEditZone과 무관, 재분류하지 않음 |

### Archive가 있는 다른 형식과 구분

`impapi.dll`의 실제 TypeEditCalque 경로에서는 다음이 연결된다.

- 0xB475 → thunk0x2B556 → IAT0x32198 → MFC ordinal546 **CSharedFile constructor**. 호출부 인수는 `0x2042`, `0x1000`이다.
- 0xB491 → thunk0x2B550 → IAT0x32194 → MFC ordinal317 **CArchive(CFile*, UINT, int, void*)**. 해당 코드에서 pFile은 위 local shared file, mode=0, buffer size=0x1000, buffer pointer=0으로 전달된다.
- 0xB565 → thunk0x2B538 → IAT0x32184 → **CSharedFile::Detach**. 그 결과 버퍼를 0xB5C6에서 앞서 등록한 TypeEditCalque 형식으로 넘긴다.

이는 실제 Clipboard+Archive 연결이지만 **다른 형식**이다. 이 생성 옵션·map 상태를 G1/H TypeEditZone에 적용하지 않는다. 내부 목록 직렬화까지 Type3 CZone으로 추정하지 않았다.

MFC/PDB 관련 import 조사에서 Maude3D.dll에도 CSharedFile/CArchive 생성자가 있었다. 직접 thunk XREF는 CSharedFile 0x6E518 및 CArchive 0x6E512, 호출 구간은 0x1E707/0x1E73B 등이다. 그러나 TypeEditZone 등록/발행과 연결되지 않았고 독립 메모리 직렬화·복원 용도일 수 있다. 함수 이름·Clipboard 역할은 UNKNOWN으로 두고 호출 그래프를 확장하지 않았다.

## TypeEditZone에 대해 남은 UNKNOWN

| 질문 | 결과 |
|---|---|
| 실제 발행/생산자 함수와 RVA | NOT_IDENTIFIED |
| stream/file 동적 클래스와 receiver | UNKNOWN |
| 해당 경로의 Archive constructor 인수 | UNKNOWN |
| 첫 WriteObject 이전 MapObject·클래스/객체 사전 등록 | UNKNOWN |
| 최초 map count와 첫 CZone class ID1 | 기존 조건부 가정 유지 |
| `000000000100` 생성 명령과 offset6 이유 | UNKNOWN |
| TypeEditZone의 OLE/지연 렌더링 경로 | 확인 못함; 배제하지 않음 |

마지막으로 확정된 **대상 Archive primitive**는 matched MFC80 constructor ordinal317/RVA **0x27C4F**, WriteObject **0x28562**, MapObject **0x2875F**다. 이 주소는 TypeEditZone Copy caller가 아니다. 현재 자료에는 그 primitive를 실제 발행 함수로 연결할 근거가 없으므로 Stage B의 TypeEditZone map/prefix 분석과 Stage 5의 새 map 교차 검증은 수행하지 않았다. 기존 class8/offset6 조건부 상태를 승격하지 않는다.

## 실행하지 않은 최소 동적 관찰 계획

정적 추적을 더 확대하지 않고 다음 **별도 승인 대상** 계획만 남긴다. 이번에 도구 설치·Type3 실행·디버거 부착·중단점 설정·Clipboard 조회는 하지 않았다.

1. 기존 미저장 문서는 열거나 닫지 않는다. 사용자와 식별한 별도 시험 인스턴스 및 폐기 가능한 테스트 도형만 준비하고, 실제 PID·시작 시각·창·활성 시험 문서를 새로 확인한다. 과거 PID를 재사용하지 않는다. 시험 준비와 Clipboard 덮어쓰기를 명시적으로 승인받는다.
2. 사용 가능한 x86 native debugger를 확인하고 **관찰 전 실제 로드된 모듈 경로/SHA가 이번 identity와 일치하는지** 대조한다. 새 디버거 설치가 필요하면 따로 승인받는다. 기능이 필요한 최소 소프트웨어 중단점도 실행 코드를 일시 변경·정지시킬 수 있음을 고지한다. 주입/Hook/직접 Native 함수 호출은 하지 않는다.
3. **발행 관찰 1개:** 직접 Win32 경로면 시험 인스턴스의 `user32!SetClipboardData`, OLE 경로면 `ole32!OleSetClipboard` 중 실제 사용되는 진입을 관찰한다. 처음부터 두 경로가 같다고 가정하지 않는다. Copy1회에서 호출 스레드·앱 caller 모듈/RVA·형식 식별 인수와 동일 시험 작업의 대응을 기록한다. 등록 형식 이름 확인은 해당 시험 Copy의 형식에 한정하며 다른 Clipboard 내용을 덤프하지 않는다. 지연 렌더링이면 IDataObject 게시만으로 버퍼 생성이 확인됐다고 판단하지 않는다. Paste로 렌더링을 강제하지 않고 NOT_OBSERVED로 중단할 수 있다.
4. **Archive 관찰 1개:** matched MFC constructor **0x27C4F**. x86 함수 진입의 ECX=this, stack arguments의 pFile/uMode/buffer size/buffer pointer를 그때의 ABI와 함께 확인한다. 돌아온 뒤 archive+0x18 모드, +0x34 map count, +0x38 map 유무를 관찰한다. 같은 UI Copy 스레드·콜스택으로 생산자와 연결되지 않는 생성자는 제외한다. 모든 파일 작업을 TypeEditZone으로 분류하지 않는다.
5. 필요할 때만 같은 callback 범위의 **WriteObject 0x28562**를 관찰해 첫 object의 runtime class와 cursor, map count 전후를 확인한다. MapObject **0x2875F**는 생성→첫 WriteObject 사이의 사전 매핑 여부를 확인할 때만 추가한다. raw pointer를 영구 객체 ID로 보관하지 않고, 보고에는 모듈/RVA와 값·분류 결과를 사용한다. 수명 확인 없이 getter를 직접 호출하지 않는다.
6. prefix 생성은 위에서 발견한 **실제 caller**의 Write 호출/버퍼 cursor로만 역추적한다. 현재 모르는 prefix 함수에 임의 breakpoint를 지어내지 않는다. Copy1회로 필요한 연결이 안 나오면 추가 Copy·Paste·문서 조작으로 자동 확대하지 않는다.
7. 예상치 못한 예외·내부 충돌 경고·멈춤·잘못된 문서 활성화·저장 확인이 나오면 중단한다. 예외를 무시하거나 강제 종료하지 않는다. 정상적으로 계속/분리할 수 있는지 확인하고, 불확실하면 정지 상태와 필요한 사용자 조작만 보고한다. 미저장 시험 문서도 자동 저장·폐기·닫지 않는다. 디버거 부착이 완전한 무영향 관찰이라고 주장하지 않는다.

최소 승인 범위는 **별도 시험 인스턴스·시험 문서/도형 준비, x86 디버거 부착/정지/해제, Copy1회 및 그로 인한 Clipboard 덮어쓰기, 위 호출의 제한된 관찰**이다. 기존 업무 문서와 기존 미저장 문서, H Paste는 포함하지 않는다.

## 회귀와 보호

기존 001/002 구조 검사 **15/15 PASS**, `regression.txt`. Crosswalk·Decoder/Encoder·G1/H·profile/lock·H 후보를 변경하지 않았다. 기존 전체 Codec 17개 실패를 새 실패로 재분류하거나 테스트 기대값을 바꾸지 않았다.

`preservation.json`: 기존 Codec 파일 **830개** SHA 변경0, 조사한 설치 PE **244개** SHA 변경0. 업무 모드 **OFF**. 원본 automation 저장소 Git 변경 없음. Native DLL/PLG/Ghidra DB 수정, 실제 Type3·Clipboard 접근, 문서 저장/닫기/폐기, H Paste는 모두 미실행이다.

**결론:** 현재 정적 근거로 생산자 식별을 완료하지 못했으므로 BLOCKED로 종료한다. 다른 형식의 생성자를 재사용하거나 class map 초기 상태를 추측해 구현하지 않는다. 추가 정적 함수 연쇄 분석으로 자동 진행하지 않는다.
