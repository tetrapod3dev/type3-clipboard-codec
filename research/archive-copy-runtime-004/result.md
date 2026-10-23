# Copy 직렬화 호출 역추적 004 — Stage A

**COPY_RUNTIME_PREPARED**. 오프라인 관찰 준비만 완료했다. 실제 Type3 실행·부착·Copy·메모리 관찰은 **NOT_EXECUTED**이며 Stage B는 별도 승인 대기다. Type3와의 attach/detach 호환성은 아직 실측하지 않았으므로 승인 후 첫 환경 게이트로 남긴다. Runtime Verified 판정이 아니다.

## 1. 환경과 사용 가능한 도구

Codec 시작 HEAD `7180de5e8cfaa8e77e9e64ca28a948bb3911d033`, 기존 작업 트리는 clean이었다. 현재 환경은 `Windows-11-10.0.26200-SP0`다. 기존 PATH/Windows Kits/Visual Studio 경로와 현재 사용자 WinDbg Appx 조회에서 WinDbg/CDB/NTSD를 찾지 못했다. 전 시스템 부재를 주장하지 않는다.

추가로 CLion에 이미 설치된 **x86 LLDB**를 확인했다.

- 실행 파일: `C:\Program Files\JetBrains\CLion 2026.2.3\bin\lldb\win\x86\bin\lldb.exe`
- PE machine: **0x14C (x86)**
- SHA256: `8af1daad95040f92a2045ed92a0cc020a02617edc88467a35e489aad713039d9`
- 실행 버전: `lldb version 9.0.0 (JetBrains IDE bundle; x86; rider-lldb-9; build 593)`
- `--version`, `--no-lldbinit --batch`의 **help만** 대상 없는 상태에서 실행했고 exit0이었다. attach/detach, address breakpoint, delete, register read, memory read, limited backtrace, image list 명령이 제공된다. 자세한 출력은 `lldb-help.txt`, 파일 identity와 실행 명령은 `debugger-inventory.json`.

x64 LLDB/GDB 및 Visual Studio x86 msvsmon/VsDebugConsole도 파일 존재·machine·SHA만 기록했다. msvsmon은 원격 서버이며 단독 프런트엔드로 채택하지 않았다. 새 도구 설치는 하지 않았다. LLDB 자동 init을 비활성화했고 PID/name/target/process 인수를 전달하지 않았다. Type3 인스턴스를 열거하거나 자동 부착하는 스크립트도 만들지 않았다.

**호환성 한계:** x86 실행 파일과 필요한 CLI 제공 및 무대상 실행 성공까지 확인했다. 해당 버전 LLDB의 현재 Windows/Type3/CLR2 프로세스에서의 Native 부착·스택 unwind·PDB 표시·안전 detach 성공은 별도 시험 대상이다. 이 확인이 실패하면 Copy하지 않는다. PDB 자동 다운로드나 네트워크 symbol 설정은 하지 않았다.

## 2. MFC/PDB 및 ABI

`native-evidence.json`에 실제 instruction bytes·matched PDB 심볼을 기록했다.

- MFC80: `C:\Windows\WinSxS\Fusion\x86_microsoft.vc80.mfc_1fc8b3b9a1e18e3b_none_bd39c11e9405d29b\8.0\8.0.50727.6195\mfc80.dll`
- SHA: `8204dbcc054c1e54b6065bacb78c55716681ad91759e25111b4e4797e51d0aa3`
- PDB SHA: `3de04172355214be3c9f6851ccb2ef785efb3c2c900084036dbe12919ef1202a`, RSDS GUID/age14 일치
- PE: x86. 이 identity는 **디스크 파일의 정적 확인**이며 Host에 로드된 모듈을 관찰한 결과가 아니다.

아래 인수는 **함수의 첫 명령을 실행하기 전**, x86 thiscall 진입에서만 해석한다. prologue 이후에는 ESP 위치가 달라지므로 같은 offset을 재사용하지 않는다. 반환 주소는 그때의 `[ESP]`, caller 기록은 반환 주소 소속 모듈 및 RVA다.

| 함수 | RVA / 입력 | 실제 명령 근거 |
|---|---|---|
| CArchive::WriteObject(const CObject*) | **0x28562**, ECX=Archive, `[ESP+4]`=object | push ESI → mov ESI,ECX; 추가 push 이후0x28580에서 `[ESP+0xC]`를 object로 취득. 0x2857B는 MapObject(null) 호출 |
| CArchive(CFile*,UINT,int,void*) | **0x27C4F**, ECX=new Archive; `[ESP+4/+8/+0xC/+0x10]`=pFile/mode/buffer size/buffer ptr | PDB exact signature, frame 구성 후 `[EBP+8]` pFile, +0xC mode, +0x10 size, +0x14 buffer. ret0x10 확인 |
| CArchive::MapObject(const CObject*) | **0x2875F**, ECX=Archive, `[ESP+4]`=object | frame 구성 후 `[EBP+8]` 사용. null 초기화와 non-null 사전 등록 분기 구분 |

### 관찰할 Archive 필드와 오독 방지

| Native member offset | 이번 정적 근거 / 관찰 의미 |
|---|---|
| **+0x24** | pFile. ctor0x27CC0에서 입력 receiver 저장. **+0x14를 file pointer로 해석하지 않는다** |
| +0x18 | mode, ctor0x27CAB 저장. bit0 clear=store, set=load로 WriteObject/Serialize 분기와 대조 |
| +0x38 | map pointer, ctor0x27CD4에서0으로 초기화 |
| +0x34 | map count. **ctor의 검토된 본문은 초기값을 기록하지 않는다. map+0x38이 null이면 값이 읽혀도 유효 초기 count로 사용하지 않는다** |
| +0x30 / +0x28 / +0x2C | buffer base / 현재 cursor / buffer end. ctor0x27CE0,0x27D46,0x27D4D. cursor-base는 현재 buffer 구간 값일 뿐 전체 파일 offset이 아닐 수 있음 |

MapObject가 새 map을 만들 때 null 등록0·count1이 성립한다. 이 라이브러리 규칙을 실제 Copy가 미리 어떤 등록도 하지 않았다는 주장과 혼동하지 않는다. 첫 WriteObject 진입의 map이 null인 경우와 이미 생성된 경우를 구분해 기록한다.

## 3. 승인 후 관찰 절차 — 실행하지 않은 계획

### B1: 대상 확인과 중단점 준비

1. 기존 업무/미저장 인스턴스는 제외한다. 새 시험 인스턴스, 업무 데이터 없는 시험 문서와 간단한 도형을 별도 승인 범위에서 준비한다. 준비·선택을 끝낸 뒤 attach하여 그 이후 **Ctrl+C 정확히1회**만 수행한다. 과거 PID는 사용하지 않고 PID/시작 시각/창/활성 문서를 새로 확인한다.
2. LLDB는 위 x86 파일을 `--no-lldbinit`로 빈 상태에서 시작한다. 이름 기반 자동 attach/대기 attach/현재 모든 프로세스 검색은 사용하지 않는다. 사용자가 식별한 **새 시험 PID 하나**만 명시한다.
3. attach가 성공해도 실제 modules 목록의 경로·base·file SHA와 명령 bytes를 먼저 대조한다. MFC80 identity가 다르거나 아키텍처/문서가 불분명하면 Copy 없이 중단한다. 바인딩을 추측해 다른 MFC를 강제로 로드하지 않는다.
4. 주소는 **실제 MFC module base + RVA**로 계산한다. 최초 두 관찰점은 ctor0x27C4F와 WriteObject0x28562다. CPU hardware breakpoint가 해당 backend에서 실제 지원되는지는 미확인이다. 지원되면 사용할 수 있지만 x86 슬롯 제한을 고려한다. 소프트웨어 breakpoint는 일시적 instruction byte 변경/Host 정지를 유발함을 승인 범위에 포함한다. 디스크 DLL을 패치하지 않는다.
5. MapObject는 같은 Archive의 ctor/첫 WriteObject 관계가 관찰된 뒤에만 필요 시 추가한다. publication은 그 뒤 실제 증거에 따라 user32!SetClipboardData **또는** ole32!OleSetClipboard 중 하나를 선택한다. 처음부터 모든 중단점을 무차별 설치하지 않는다. backend에서 안전하게 필요한 관찰점을 추가할 수 없으면 부분 결과로 종료한다.

### B2~B4: Copy1회에서 얻을 최소 증거

- 각 정지: 현재 thread ID, 제한된 stack **최대8 frame**, return address의 모듈/RVA. 내부 UI 명령·호출 시각 구간이 다른 Archive 작업이면 제외한다.
- ctor entry: Archive/pFile을 세션 내부 임시 alias A1/F1로 대응하고 mode/size/buffer ptr을 기록한다. ctor 반환 지점은 **그 호출에서 읽은 실제 반환 주소**로만 정하며 임의 caller RVA를 지어내지 않는다. 성공 반환 후 map null 여부를 확인한다. `+0x34`의 유효성 조건은 위와 같다.
- WriteObject entry: 같은 A1인지, mode가 store인지, object alias 및 **메모리에 저장된 vptr의 모듈/RVA**를 읽는다. 미확인 GetRuntimeClass/virtual getter를 호출하지 않는다. 정적으로 확인한 Maude CZone vtable RVA0xB1F04 등과 실제 identity가 일치할 때만 클래스 근거로 채택한다. 불일치면 UNKNOWN이다. vptr 숫자가 읽혔다는 이유만으로 생존/동적 타입을 보증하지 않는다.
- 같은 Archive 내 MapObject 선행 호출 여부와 object null/non-null을 구분한다. 객체 주소는 callback 안의 동일성 비교에만 사용하고 영구 ID로 내보내지 않는다. 보존 보고서는 A1/F1/O1 alias와 모듈/RVA·값·상태를 사용한다.
- 메모리는 검증된 해당 Archive **최대0x48바이트**와 필요한 object vptr 4바이트, 승인된 buffer의 짧은 prefix 등 최소 범위만 읽는다. 주소가 유효하지 않거나 lifetime이 불명확하면 읽지 않고 중단한다. getter 실행으로 유효성을 시험하지 않는다.

**관찰 상한:** Copy1회, 총 stop **최대32건**, ctor 최대8·WriteObject 최대16·추가 MapObject 최대8을 각각 넘지 않는다(발행 stop도 총32에 포함). stack은 매번8 frame 이하. 제어가 멈춘 채 분석을 무기한 하지 않는다. 같은 Copy와 무관한 호출이 연속되거나 전체 관찰10분을 넘으면 추가 Copy 없이 중단·안전 해제 절차로 간다. 이 상한에서 생성자/생산자 관계를 놓치면 NOT_OBSERVED 또는 PARTIAL이지 재Copy 허가가 아니다.

### B5~B6: 발행 및 prefix

WriteObject/CZone 관찰만으로 TypeEditZone producer라고 하지 않는다. 발행이 필요하면 실제 시험 Copy와 연결된 등록 형식 ID의 이름이 **TypeEditZone**인지 확인한다. `TypeEditCalque`, `VNXCLP`, CF_TEXT/WMF 등은 제외한다. ID는 고정 숫자를 쓰지 않는다. OLE IDataObject 게시와 실제 buffer 생성은 별개이며, 지연 렌더링 때문에 직렬화가 안 보이면 NOT_OBSERVED로 남긴다. IDataObject::GetData를 직접 호출하거나 Paste로 렌더링을 강제하지 않는다.

실제 producer caller가 확보될 때만 그 명령·buffer cursor에서6바이트 기록과 첫 descriptor 경계를 좁힌다. 무제한 메모리 검색이나 다른 문서 데이터를 읽지 않는다. 현재 cursor/base 차이를 전체 파일 위치라고 가정하지 않는다. 그 연결이 없으면 기존 G1/H map·prefix 가정을 유지한다.

### 종료·실패 정책

예외·내부 충돌 경고·예상 밖 정지·활성 문서 불일치·모듈 불일치·쓰기 변화·저장 확인이 나오면 추가 Copy를 하지 않는다. 예외를 자동 무시하거나 강제 종료하지 않는다. debugger가 멈춘 프로세스를 무조건 continue/kill/quit하지 않는다. 정상 정지인지 확인한 다음 **이번에 만든 breakpoint만 제거**하고 안전 detach가 가능한 조건에서 해제한다. detach 여부/Host 실행 상태가 불확실하면 그 상태를 보고하고 사용자 판단을 기다린다. 문서를 저장·닫기·폐기하지 않는다.

## 4. LLDB 수동 명령 템플릿

아래는 **승인 후에만 사람이 실제 값으로 채워 실행하는 설명용 템플릿**이다. 자동 attach 파일이나 실행 스크립트가 아니다. Stage A에서 실행한 것은 `help`뿐이다. 주소/레지스터 인수 문법은 설치본 help에서 확인했지만 실제 Type3 target에서의 성공은 미실측이다.

```text
process attach --pid <NEW_VERIFIED_TEST_PID>
image list -o -f
breakpoint set --address <ACTUAL_MFC_BASE_PLUS_0x27C4F>
breakpoint set --address <ACTUAL_MFC_BASE_PLUS_0x28562>
register read eip esp ecx
memory read --format x --size 4 --count 5 <VERIFIED_ENTRY_ESP>
thread backtrace --count 8
# 필요 시 검증된 Archive A1의 0x48B만 읽고 필드를 위 표로 해석
# 확인한 정상 정지에서만 continue; 예외 정지에는 자동 적용하지 않음
breakpoint delete <ONLY_OUR_BREAKPOINT_IDS>
process detach --keep-stopped false
```

attach/detach/continue는 이번에 실행하지 않았다. 다른 PID를 대입하거나 help 세션의 quit를 부착 세션에 무조건 재사용하지 않는다.

## 5. 승인 범위·미확정 조건·회귀

Stage B에 필요한 별도 승인: **분리된 시험 인스턴스·시험 문서/도형 준비, x86 LLDB 부착·중단점·제한된 메모리/stack 관찰, 시험 도형 선택과 Copy1회, Clipboard 덮어쓰기, 안전 조건 충족 시 해제**. 기존 업무/미저장 문서 조작·H Paste·문서 저장/폐기·Native 직접 호출·Hook·DLL injection은 포함하지 않는다.

아직 미확정: 실제 producer, 새 Archive의 mode와 file 클래스, 선행 MapObject, 실제 첫 map count, prefix 생성 함수, delayed rendering 여부, 기존1개 descriptor/class ID 가정과의 연결. LLDB 실제 Host 호환성도 승인 후 첫 게이트다.

기존 구조 회귀 **15/15 PASS**, `regression.txt`. `preservation.json`: 기존 Codec 파일 **835개** SHA 변경0. 기존 003/001/002·G1/H·H 후보·profile·실행 lock·Decoder/Encoder는 보존했다. 원본 automation 저장소 Git 변경 없음. 업무 모드 **OFF**다. Type3 실행/조작·Clipboard 접근·DLL/PLG·Ghidra DB 변경을 하지 않았다. 현재 과거 시험 PID를 조회하거나 문서 상태를 추정하지 않았다.

**Stage A를 여기서 종료한다. Stage B는 별도 승인 전까지 실행하지 않는다.**
