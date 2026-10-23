# PID 20560 읽기 전용 장애 진단

**원인 분류: UNKNOWN. 안전한 detach 가능 여부: UNKNOWN.** PID20560의 정지와 LLDB 부착을 유지한다. 프로세스 복구와 Copy 연구 결과는 분리한다.

## 실행 범위와 현재 상태

기존 LLDB 세션1632의 정상 prompt에서 다음 명령을 **한 번씩, 이 순서로만** 실행했다.

1. `process status`
2. `thread list`
3. `thread backtrace`
4. `register read eip esp ebp`
5. `disassemble --pc --count 8`
6. `breakpoint list`

첫 명령에서 PID20560이 stopped인 것을 확인한 뒤 나머지를 실행했다. 모두 같은 대상에서 정상 응답했고 새 예외·세션 이상·예상 밖 상태 변화는 표시되지 않았다. 마지막 명령 후 prompt로 돌아왔고 추가 LLDB 명령을 실행하지 않았다. 이는 프로세스의 정상 재개 가능성을 보증하지 않는다.

실제 출력은 [incident-readonly-evidence.json](incident-readonly-evidence.json)에 보존했다. 기존 `runtime-001` 원본은 읽기 참고만 했고 수정하지 않았다.

| 확인 항목 | 관찰 결과 |
|---|---|
| PID | 20560, stopped |
| LLDB 연결 | 기존 세션의 동일 대상, prompt 정상 응답 |
| 선택 스레드 | #4, TID **0xCFEC** (53228), 표시 이름 `combase.dll thread` |
| stop reason 원문 | `Exception 0x80000003 encountered at address 0x8e46ad0` |
| 예외 코드 | **0x80000003 / EXCEPTION_BREAKPOINT** |
| EIP | **0x08E46AD1** |
| ESP / EBP | 0x0C4DF768 / 0x0C4DF81C, 정지 시점의 관찰값일 뿐 추후 재사용하지 않음 |
| EIP 모듈 | **TypeEditDLL.dll**, LLDB frame 분류 |
| EIP RVA | **UNKNOWN**. 승인된 명령 출력에는 검증 가능한 실제 load base가 없으므로 추측하지 않음 |
| 사용자 breakpoint 목록 | **`No breakpoints currently set.`** |
| 내부/잔여 breakpoint site 전체 | **UNKNOWN**. 빈 사용자 목록만으로 backend 내부 site까지 없다고 증명하지 않음 |
| first-chance / second-chance | **UNKNOWN**. 이번 출력에 구분 정보 없음 |
| 미완료 step/thread plan | **UNKNOWN**. 현재 stop reason은 exception이며, pending plan 전체를 검사한 것은 아님 |
| 안전한 detach | **UNKNOWN**, 시도하지 않음 |

## 예외 원인 분류의 한계

`0x80000003`은 Windows EXCEPTION_BREAKPOINT 코드다. 코드만으로 LLDB의 소프트웨어 중단점 처리인지, 애플리케이션/보호 코드의 실제 INT3인지 구분할 수 없다.

예외 주소는0x08E46AD0이고 EIP는 그 다음 byte인0x08E46AD1이다. 이 차이만으로 원래 INT3를 확정하지 않는다. 이번 disassemble 명령은 **현재 EIP부터** 읽었으므로 예외 주소의 byte 자체를 검사하지 않았다. 디스크 원본·로드 메모리·LLDB 내부 breakpoint site의 일치 여부도 확인하지 않았다.

따라서 `DEBUGGER_BREAKPOINT`, `APPLICATION_INT3` 중 어느 쪽으로도 승격하지 않고 **UNKNOWN**을 유지한다. 기존 중단점 삭제 사실과 이번 빈 목록은 안전한 분리를 의미하지 않는다.

## 현재 EIP의 명령 8개

```text
0x08E46AD1: shlb $0x20, %dl
0x08E46AD4: movl %ebx, 0x08E474C0
0x08E46ADA: shrb $0x40, %dl
0x08E46ADD: movl %ecx, 0x08E474B0
0x08E46AE3: movb %dh, %dh
0x08E46AE5: jne 0x08E4700F
0x08E46AEB: movw %bx, %bx
0x08E46AEE: je 0x08E46AF2
```

이는 표시된 명령일 뿐 해당 경로의 의도·정상성·안전성·원래 instruction 경계를 검증한 결과가 아니다.

## 선택 스레드의 호출 스택

지정된 `thread backtrace`가 다음32개 frame을 출력했다. 함수 심볼과 각 frame의 정확한 호출 경계를 이번에 검증하지 않았으므로 unwind 결과를 원인 증명으로 사용하지 않는다. `combase.dll thread`라는 이름도 작업 의미를 보증하지 않는다.

```text
#0  0x08E46AD1 TypeEditDLL.dll
#1  0x08C2C89B TypeEditDLL.dll
#2  0x08C45913 TypeEditDLL.dll
#3  0x08E4461E TypeEditDLL.dll
#4  0x08E48973 TypeEditDLL.dll
#5  0x08C2C027 TypeEditDLL.dll
#6  0x08C2EADB TypeEditDLL.dll
#7  0x08C33991 TypeEditDLL.dll
#8  0x08C1D943 TypeEditDLL.dll
#9  0x08C36563 TypeEditDLL.dll
#10 0x08C19156 TypeEditDLL.dll
#11 0x08C23A1E TypeEditDLL.dll
#12 0x08C36C8C TypeEditDLL.dll
#13 0x08C3E302 TypeEditDLL.dll
#14 0x08C1C561 TypeEditDLL.dll
#15 0x08C25880 TypeEditDLL.dll
#16 0x08C4027E TypeEditDLL.dll
#17 0x08C32261 TypeEditDLL.dll
#18 0x08C1AE43 TypeEditDLL.dll
#19 0x08C37D5B TypeEditDLL.dll
#20 0x08C19C7E TypeEditDLL.dll
#21 0x08C132B4 TypeEditDLL.dll
#22 0x77208206 ntdll.dll
#23 0x77242984 ntdll.dll
#24 0x771C93E3 ntdll.dll
#25 0x771C7AE2 ntdll.dll
#26 0x7720073C ntdll.dll
#27 0x7619CF95 KernelBase.dll
#28 0x75C93D07 combase.dll
#29 0x75835D49 kernel32.dll
#30 0x771FC75B ntdll.dll
#31 0x771FC6E1 ntdll.dll
```

Main Thread #1은 win32u.dll 안으로 표시됐다. 이번에는 그 thread를 선택하거나 Copy 미완료 상태를 추가 조사하지 않았다.

## 실행하지 않은 조치와 다음 승인

- continue / detach / kill / step / EIP 이동 미실행
- register write / memory write / expression Native 실행 미실행
- exception pass/ignore/handle 정책 변경 미실행
- 새 breakpoint 추가·기존 site 조작 미실행
- LLDB/CLion 종료, Type3 UI·Copy/Paste·문서 저장/닫기/폐기 미실행
- 이번 명령 외의 memory read, 모듈 lookup, 내부 thread plan 조회 미실행

연구 판정 `COPY_PRODUCER_RUNTIME_PARTIAL`과 기존 Archive 관찰 증거는 유지한다. 이번 진단은 복구 성공이나 원인 확정 판정이 아니다.

**여기서 다시 중단하고 사용자 승인을 기다린다.** 다음에 예외 byte와 RVA를 좁히려면 실제 모듈 기준주소 조회와 예외 주소0x08E46AD0의 제한된 원시 byte 읽기 같은 추가 읽기 전용 범위를 별도 승인받아야 한다. 그 승인도 debugger 해제나 프로세스 재개를 포함하지 않는다.
