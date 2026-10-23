# 장애 시험 종료 준비

状態: `PREPARED_AWAITING_EXPLICIT_TERMINATION_APPROVAL`

## 승인과 동일성

현재 지시는 종료 준비만 승인한다. 미저장 시험 문서 소실 및 PID 20560 강제 종료에 대한 명시적 승인은 아직 받지 않았다.

- Type3 PID 20560: 시작 시각 2026-10-23 15:16:19.472414 KST, `C:\TypeEdit_2009\EXE\Pltf.exe` 일치.
- LLDB OS PID 31084: 시작 시각 2026-10-23 15:17:12.696770 KST, CLion x86 LLDB 경로 일치.
- 도구 세션 1632에서 `process status`만 실행: PID 20560 stopped, thread #4, 예외 0x80000003 / 주소 0x08E46AD0, EIP 0x08E46AD1. 정상 LLDB 프롬프트 반환.
- LLDB 부착과 시험 Type3 정지 상태 유지. Async Tasks UI 항목의 직접 완료 상태는 UNKNOWN이며, 세션 1632는 계속 실행 중이다.

## 보존

runtime-001 전체 파일과 incident-readonly 원본 보고서·JSON의 SHA256 및 크기를 incident-closeout-evidence.json에 기록하고 재검사했다. 기존 파일은 변경하지 않았다. 다른 Type3 인스턴스, 문서, Clipboard, DLL, PLG 및 Codec 코드는 조작하지 않았다. 업무 모드 파일은 OFF다.

Copy 실기 판정은 COPY_PRODUCER_RUNTIME_PARTIAL을 유지한다. Copy 완료 및 예외 원인은 UNKNOWN이다. 안전한 detach 여부도 UNKNOWN이다.

## 승인 후에만 실행할 절차

1. 대상의 PID·생성 시각·실행 경로와 LLDB 대상을 다시 대조한다.
2. 정상 프롬프트에서 정확히 대상 PID 20560임을 확인한 뒤 process kill을 1회 실행한다.
3. OS에서 Type3 종료를 별도 확인한다. 실패하거나 상태가 다르면 즉시 중단하며 OS 강제 종료·detach·continue로 우회하지 않는다.
4. 대상 종료가 확인된 경우에만 LLDB process status 조회 후 정상 quit을 실행한다.
5. LLDB OS PID와 세션 1632 종료를 확인하고 이 기록에 실제 결과를 추가한다.

현재 process kill, quit, detach, continue, step, 예외 정책 변경 및 Async Tasks 취소는 실행하지 않았다. INCIDENT_CLOSED 판정은 아직 내리지 않는다.

## 승인 후 실제 종료 결과

최종 판정: `INCIDENT_CLOSED`

사용자가 다음과 같이 명시적으로 승인했다.
> PID 20560 시험 Type3 프로세스의 미저장 시험 문서 소실을 승인하며, 해당 PID의 통제된 강제 종료를 승인한다.

종료 직전 OS 생성 시각·실행 경로와 LLDB PID 20560 stopped 상태 및 정상 프롬프트를 다시 확인했다. 동일성은 준비 당시와 일치했다.

실제 실행 순서:
1. `process status`: PID 20560 stopped 확인.
2. `process kill`: 정확히 1회. LLDB 출력 `Process 20560 exited with status = 0 (0x00000000)`.
3. OS 조회: 2026-10-23 17:48:58 KST에 PID 20560 부재 확인.
4. `process status`: 대상 exited 상태 재확인.
5. `quit`: LLDB 정상 종료, 도구 세션 1632 exit_code 0.
6. OS 조회: 2026-10-23 17:49:10 KST에 PID 20560과 LLDB PID 31084 모두 부재 확인.

이는 승인된 강제 종료이며 시험 문서의 정상 저장·종료를 의미하지 않는다. 미저장 시험 문서 소실은 승인 범위다. Async Tasks 취소 버튼은 사용하지 않았다. 세션 1632의 완료는 확인했으나 UI 목록 표시 자체는 UNKNOWN이다.

보호 원본 19개 SHA를 다시 검사했고 변경은 0개다. 다른 Type3 인스턴스에 제어 명령이나 UI 조작을 하지 않았다. 해당 인스턴스의 내부 상태까지 검사한 것은 아니다. Clipboard, DLL, PLG, Codec, Ghidra DB 및 업무 문서 조작은 없었다. 업무 모드 OFF를 재확인했다.

Copy 실기 성과는 `COPY_PRODUCER_RUNTIME_PARTIAL`로 보존한다. 예외 원인과 Copy 완료·Clipboard 발행 여부는 여전히 UNKNOWN이다. detach, continue, step, EIP·메모리 수정 및 예외 정책 변경은 실행하지 않았다. 새로운 디버깅은 시작하지 않는다.

기계 판독 종료 결과: `incident-closeout-final.json`.
