# PID 20560 추가 읽기 전용 진단 002

**원인 분류 UNKNOWN / 안전한 detach UNKNOWN.** 사용자 승인 범위인 예외 주소의 제한된 메모리 bytes와 모듈 기준주소만 추가 확인했다. PID20560의 정지와 LLDB 부착을 유지한다.

## 명령과 관찰

기존 세션1632에서 `process status`로 PID20560이 같은 예외에서 정지한 것을 확인했다. 이후 아래 읽기만 수행했고 모두 정상 prompt로 돌아왔다. 새 예외나 재개는 표시되지 않았다.

```text
process status
image list -o -f TypeEditDLL.dll
image lookup --address 0x08e46ad0
memory read --format x --size 1 --count 8 0x08e46ad0
image list --header -f TypeEditDLL.dll
```

`image list -o`는 load base가 아닌 slide를 표시한다. 실제 base는 설치본의 기존 help에서 `--header` 의미를 확인한 후 명시적으로 조회했다. slide를 base로 오해하여 RVA를 계산하지 않았다.

| 항목 | 확인 결과 |
|---|---|
| PID / 상태 | 20560 / stopped, 기존 LLDB 부착 유지 |
| 선택 스레드 | #4, 이전 진단의 TID0xCFEC와 같은 선택 스레드; 이번에 새 thread list는 실행하지 않음 |
| stop reason | Exception0x80000003 encountered at address0x08E46AD0 |
| 현재 EIP 표시 | 0x08E46AD1, TypeEditDLL.dll |
| 모듈 경로 | C:\TypeEdit_2009\EXE\TypeEditDLL.dll |
| **실제 load base** | **0x08910000**, `image list --header` |
| 예외 주소 / RVA | **0x08E46AD0 / 0x536AD0** |
| EIP / RVA | **0x08E46AD1 / 0x536AD1** |
| lookup section | TypeEditDLL의 `.protect`, section 상대2308816으로 표시 |
| 현재 메모리 8바이트 | **CC C0 E2 20 89 1D C0 74** |
| 원인 분류 | **UNKNOWN** |
| first/second-chance | UNKNOWN, 추가 정보 없음 |
| 안전한 detach | **UNKNOWN**, 미시도 |

[incident-readonly-002-evidence.json](incident-readonly-002-evidence.json)에 실제 명령/응답을 보존했다. 이전 incident 및 runtime-001 증거는 수정하지 않았다.

## 확인한 사실과 확인하지 못한 사실

예외 주소의 **현재 메모리**에 CC가 존재한다. x86의 단일 바이트 INT3 opcode이고, 보고된 예외 주소 다음 byte가 EIP인 것과 부합한다.

하지만 이 사실은 **APPLICATION_INT3 확정이 아니다**. 디스크 원본의 같은 RVA bytes, 로더/보호 코드가 변경한 메모리, LLDB 내부/잔여 breakpoint site 및 이전 삽입 이력을 대조하지 않았다. CC가 원래 제품 명령인지 debugger patch인지 여전히 구분하지 못한다. `.protect`라는 section 이름만으로 원인·보호 기능·정상성도 판단하지 않는다.

이전 명령의 `No breakpoints currently set`는 사용자 목록에 관한 결과다. 이번에는 breakpoint 관련 명령을 더 실행하지 않았고, 내부 site 전체의 부재를 새로 증명한 것이 아니다. 미완료 step/exception 처리 상태도 UNKNOWN이다.

## 실행하지 않은 조치와 대기

continue/detach/kill/step, EIP 이동, register/memory write, exception 정책 변경, Native expression 실행, breakpoint 추가/삭제는 하지 않았다. Type3 UI, Copy/Paste, 문서 저장·닫기·폐기와 LLDB/CLion 종료도 하지 않았다. 업무 모드 설정을 변경하지 않았다.

**여기서 다시 중단한다.** 다음에 디스크 원본과 같은 RVA의 소량 bytes를 비교하려면 별도 읽기 전용 범위를 승인받는다. 그 비교도 로더/보호 코드의 동적 변경과 debugger patch를 단독으로 구분하지 못할 수 있다. 이번 승인과 다음 읽기 승인은 프로세스 재개·디버거 해제를 포함하지 않는다.
