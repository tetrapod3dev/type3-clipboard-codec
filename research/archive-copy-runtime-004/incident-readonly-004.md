# LLDB 내부 상태 및 Async Tasks 확인 004

**INCIDENT_READONLY_DIAGNOSTICS_PARTIAL**. 승인된 LLDB 조회는 완료했지만 Async Tasks UI의 실제 작업 ID/소유 관계와 취소 전파 동작, backend breakpoint site 전체 및 Windows 예외 처리 단계는 확인하지 못했다. 원인 분류 및 안전한 detach 가능 여부는 계속 **UNKNOWN**이다. 복구를 시도하지 않고 정지·부착 상태를 유지한다.

## 관찰 시각과 동일 대상 확인

관찰 구간: **2026-10-23 17:06:31~17:07:30 KST**, 이후 결과 문서 작성. OS CIM 조회와 기존 생성 기록을 먼저 대조했다.

| 항목 | 실제 관찰 |
|---|---|
| Type3 OS PID | **20560** |
| Type3 생성 시각 | **2026-10-23T15:16:19.472414+09:00**, 기존 actual-test-host 기록과 일치 |
| Type3 실행 파일 | C:\TypeEdit_2009\EXE\Pltf.exe |
| Type3 명령행 | `"C:\TypeEdit_2009\EXE\Pltf.exe" -PLUG TypeEditDLL.dll -LOADER TypeEdit.exe` |
| Type3 부모 PID | 39992, 생성 당시 런처. 현재 부모 생존 여부는 별도 조사하지 않음 |
| LLDB OS PID | **31084** |
| LLDB 생성 시각 | **2026-10-23T15:17:12.696770+09:00** |
| LLDB 실행 파일 | C:\Program Files\JetBrains\CLion 2026.2.3\bin\lldb\win\x86\bin\lldb.exe |
| LLDB 명령행 | 위 파일 경로 + **--no-lldbinit** |
| LLDB 부모 | **28572**, pwsh.exe, 생성15:17:12.327837+09:00 |
| 그 부모 PID | 35084. 소유 애플리케이션/종료 전파는 미확인 |
| 도구의 대화형 실행 세션 | **1632**, OS PID가 아님 |

OS 조회에서 LLDB 프로세스는 한 개였고, 세션1632에 보낸 `process status`는 **Process20560 stopped**로 응답했다. 기존 생성 시각·경로·실행 기록과 함께 동일 시험 대상을 확인했으며 PID 재사용 근거는 없었다. 이 대조가 끝난 뒤 나머지 LLDB 조회를 진행했다.

## Async Tasks의 확인 범위

- **확인:** 세션1632는 이 대화에서 실행한 x86 LLDB 명령에 계속 응답하고 있으며 대상은20560이다. OS의 단일 LLDB PID31084와 실행 경로·명령행·생성 시각이 부합한다. shell 부모는28572다. 세션 ID1632를 OS PID로 취급하지 않는다.
- **강한 대응 근거이나 플랫폼 매핑 자체는 미확인:** LLDB31084가 해당 세션의 실행 파일이라는 관계는 생성/명령 응답/OS 단일 후보로 뒷받침된다. 도구는 세션 ID→OS PID 소유 그래프를 직접 반환하지 않았다.
- **UNKNOWN:** 사용자가 보는 **Async Tasks 행의 실제 UI 작업 ID**, 그 행이 세션1632를 가리키는 직접 메타데이터, 취소 버튼의 구현 및 shell/LLDB/Type3에 대한 종료 전파. 현재 제공된 도구에는 해당 UI 목록/소유 그래프/대기 큐를 읽는 전용 기능을 확인하지 못했다. UI 버튼을 누르거나 종료로 시험하지 않았다.
- **확인:** 모든 제출 명령이 응답 후 `(lldb)` prompt로 돌아왔다. 실행 중인 분석 명령은 관찰되지 않았다. 이번 제출분에 미완료 명령이 없다.
- **관찰 한계:** LLDB stdin/PTY의 원시 입력 큐, IDE 전체 예약 작업과 외부 automation을 열람하지 않았다. 따라서 플랫폼 전체에 대기 명령이 절대 없다고 보증하지 않는다.
- **기존 실행 이력:** 이 대화에서 자동 반복·후속 제어 예약·breakpoint command·background continue를 등록하지 않았다. LLDB는 --no-lldbinit로 시작했다. 현재 사용자·내부 breakpoint 목록도 비어 있다. 이는 외부 플랫폼 전체 예약 부재 증명과는 다르다.

기존의 'Async Tasks 하나는 LLDB 대기 세션으로 보인다'는 설명은 위 실제 세션과 OS 정보에 부합한다. 다만 **UI 행의 직접 식별까지 확인한 확정 문장으로 바꾸지 않는다**.

## 실행한 LLDB 명령

정상 prompt와 동일 대상 확인 후 다음 읽기만 수행했다. help로 실제 설치본 옵션을 확인하고 나서 내부 표시 옵션을 사용했다.

```text
process status
thread list
breakpoint list
watchpoint list
help thread plan list
help breakpoint list
thread plan list
thread plan list --internal --verbose
breakpoint list --internal --verbose
help settings show
settings show target.process.detach-keeps-stopped
```

전부 정상 응답 후 prompt로 복귀했고 새 예외·프로세스 상태 변화는 표시되지 않았다. 임의의 breakpoint site 내부 명령, Python/script/expression, thread plan discard/prune는 사용하지 않았다. 실제 출력은 [incident-readonly-004-evidence.json](incident-readonly-004-evidence.json)에 보존했다.

## 현재 process/thread/중단점/plan

| 항목 | 결과 |
|---|---|
| Process | **20560 stopped**, 기존 상태 동일 |
| 선택 thread | **#4, TID0xCFEC**, `combase.dll thread` |
| stop reason | **Exception0x80000003 encountered at address0x08E46AD0**, 이전과 동일 |
| 현재 EIP 표시 | **0x08E46AD1 TypeEditDLL.dll**, 이전과 동일 |
| 현재 thread 수 | thread list에24개 표시 |
| 사용자 breakpoint | **No breakpoints currently set.** |
| 내부 포함 verbose breakpoint 목록 | **No breakpoints currently set.** |
| watchpoint | **No watchpoints currently set.**, supported hardware watchpoints4로 표시 |
| 선택 thread의 기본 plan | **No active thread plans** |
| 선택 thread의 내부 포함 verbose plan | **No active thread plans** |
| 다른 thread의 plan 전체 | 이번에 별도 열람하지 않음, UNKNOWN |
| backend의 모든 orphan site / 저장 원본 byte 이력 | CLI의 breakpoint 목록과 별개로 **UNKNOWN** |

활성 step plan은 **선택 thread의 CLI 목록에서 관찰되지 않았다**. 이를 모든 backend/internal pending 상태가 없다는 보증으로 바꾸지 않는다. 내부 breakpoint 옵션의 빈 목록도 모든 메모리 CC의 생성 주체를 설명하지 않는다.

## 예외 설정·원인 분류

`target.process.detach-keeps-stopped (boolean) = false`를 **읽기만** 했다. 설정을 바꾸지 않았다. 이는 detach 시 정지를 유지하지 않도록 요청하는 설정값으로 보아야 하며, backend가 현재 예외를 어떻게 처리하는지 또는 Type3가 안전하게 동작할지 보증하지 않는다. '이 값이 false라서 detach해도 안전하다'는 결론은 내리지 않는다.

현재 출력에는 Windows 예외의 **first-chance/second-chance**, DBG_CONTINUE/DBG_EXCEPTION_NOT_HANDLED 같은 다음 처리 선택, 미결 예외 전달 상태를 직접 설명하는 정보가 없다. 특정 Windows 예외 정책의 현재 값은 **UNKNOWN**이다. 관련되지 않은 Unix signal 정책을 Windows INT3 정책으로 대신 해석하거나 정책 명령을 추측해 실행하지 않았다.

기존001~003 근거는 유지한다.

- 예외 주소0x08E46AD0, base0x08910000, RVA0x536AD0는 이전 읽기 근거다. 이번에는 모듈 base나 원시 bytes를 다시 읽지 않았다.
- 메모리 **CC C0 E2 20 89 1D C0 74**와 디스크 **26 B2 09 12 2C B9 66 82**가 달랐다. 현재 메모리 INT3의 생성 주체는 미확정이다.
- `.protect` 이름 및 디스크/메모리 차이만으로 코드 변환·소프트웨어 breakpoint 삽입·애플리케이션 자체 INT3 중 하나를 확정하지 않는다.
- 원인 분류: **UNKNOWN**. DEBUGGER_BREAKPOINT/APPLICATION_INT3 확정 근거 없음.
- 안전한 continue 및 detach: **UNKNOWN**.

## 복구 선택지의 전제조건 — 실행/권고 아님

| 선택지 | 현재 증거만으로의 판단 | 문서·Host 영향 | Async Tasks/LLDB 영향 | 추가 최소 조건 |
|---|---|---|---|---|
| 정지·부착 유지 | 현재 승인된 유지 조치이며 실행 중인 상태. 영구 해결은 아님 | 시험 문서가 메모리에 남지만 Host가 정지해 사용 불가. 외부 종료/장애 위험까지 보장 못함 | 세션/LLDB가 계속 남음. UI 행 직접 매핑은 UNKNOWN | 유지 상태를 바꿀 명시적 결정. 장기 안전성을 임의 보증하지 않음 |
| LLDB 정상 detach | **안전성 UNKNOWN, 이번 승인 없음** | false 설정 때문에 재개될 수 있으며 예외 전달/Host 충돌·문서 손실 가능성 미확정 | 정상 성공하면 target 연결은 풀릴 수 있으나 LLDB CLI 자체는 남을 수 있음. UI 행 동작은 플랫폼 의존 | Windows backend의 현재 예외 처리 단계와 detach 동작 확인, 대상 식별 재확인 및 별도 승인 |
| 예외 처리 후 continue | **안전성 UNKNOWN, 이번 승인 없음** | 앱 handler/보호 로직의 동작이 미확정. 비정상 종료·내부 충돌·미저장 상태 영향 배제 못함 | 디버거 연결 상태로 실행 또는 재정지 가능. 자동 후속 명령은 설정하지 않음 | first/second-chance와 전달/처리 계약, 재개 의도에 대한 명시적 별도 결정. EIP 이동으로 우회하지 않음 |
| 독립 시험 프로세스 종료 | **이번 승인 없음**, 단순 복구라고 하지 않음 | 미저장 시험 문서와 메모리 상태 소실 가능. 정상 종료는 저장 확인/정리 동작이 필요할 수 있음 | target exit 사건 뒤 LLDB/Async Tasks가 자동 종료되는지 UNKNOWN | 현재 독립 시험 대상 확인, 보존 필요 상태·문서 처리에 대한 사용자 결정과 별도 종료 절차 |

**Async Tasks 취소는 위 어느 절차와도 동등하다고 보장하지 않는다.** shell/LLDB가 종료되면 debugger-exit 정책에 따라 Type3에도 영향을 줄 수 있지만, 이 세션의 kill-on-debugger-exit/취소 전파 정책은 확인하지 못했다. Type3는 무영향이고 LLDB만 사라진다고 단정하지 않는다. 버튼을 누르지 않았다.

## 보호·종료 상태

기존 runtime-001 및 incident001~003은 수정하지 않았다. 새004 문서와 명령 응답 증거만 추가했다. 재개/detach/kill/step, thread plan discard/prune, breakpoint 추가/삭제, register/memory write, exception 정책 변경, Native expression, 다른 debugger 부착, Async Tasks 종료, LLDB/CLion 종료, Type3 UI·Clipboard·문서 조작, 업무 모드 변경은 **모두 미실행**이다.

판정이 PARTIAL인 이유는 조회 실패가 아니라 **플랫폼 UI 소유 관계·backend site 전체·예외 전달 단계·안전한 복구가 여전히 UNKNOWN**이기 때문이다. 기존 COPY_PRODUCER_RUNTIME_PARTIAL과 Archive 증거는 그대로 보존한다.

**읽기 전용 진단을 여기서 종료한다. PID20560의 정지·LLDB 부착을 유지하며 복구를 시도하지 않는다. 추가 승인 질문도 하지 않는다.**
