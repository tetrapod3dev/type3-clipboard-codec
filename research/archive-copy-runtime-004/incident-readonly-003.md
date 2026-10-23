# PID20560 — 디스크 동일 RVA 비교 003

**원인 UNKNOWN / 안전한 재개·detach UNKNOWN.** 사용자 승인 범위인 디스크 원본의 같은 RVA에서8바이트 읽기와 이전 메모리 관찰값 비교만 수행했다. LLDB에는 명령을 보내지 않았고 PID20560에 접근·재개·해제하지 않았다.

## 파일 identity와 위치

- 파일: `C:\TypeEdit_2009\EXE\TypeEditDLL.dll`
- SHA256: `62f2fc8fcc653746e0844d01882b86251f89de2b14d8202a551a7ed4afaf18a9` — 기존003 모듈 inventory와 일치
- 크기: 4976640바이트
- 대상 RVA: **0x536AD0**
- section: `.protect`, 시작 RVA0x303000, virtual size0x236A32
- section raw 시작0x288000, raw size0x237000
- section 내 상대0x233AD0 → **파일 offset0x4BBAD0**
- 이 위치의8바이트가 실제 raw 범위에 포함됨을 확인했다. 가상 zero-fill이나 인접 파일 bytes로 대체하지 않았다.

## 비교

| 입력 | 8바이트 |
|---|---|
| 현재 디스크 동일 RVA | **26 B2 09 12 2C B9 66 82** |
| 이전 승인 진단002의 메모리0x08E46AD0 | **CC C0 E2 20 89 1D C0 74** |

8바이트 모두 다르다. 메모리는 이번에 다시 읽지 않았으며 두 값은 동시 snapshot이 아니다. 과거 확인한 load base0x08910000 + RVA0x536AD0의 계산을 사용했다.

따라서 메모리의 CC를 **디스크 원본 동일 RVA에 존재하는 INT3**라고 결론낼 수 없다. 그러나 이것으로 DEBUGGER_BREAKPOINT가 확정되는 것도 아니다. 로더/보호 계층/실행 중 코드 변환 후의 정상 메모리에 디버거가 CC를 썼을 가능성과 애플리케이션이 스스로 CC를 만든 가능성 등을 이번 비교로 구분하지 못한다. `.protect`라는 이름만으로 특정 보호 기법이나 예외 원인을 단정하지 않는다. 여러 byte가 다르다는 사실도 단일 원인의 증거가 아니다.

**APPLICATION_INT3 / DEBUGGER_BREAKPOINT 분류는 UNKNOWN 유지**다. 해당 주소가 메모리에서 CC였다는 이전 사실은 유지하되, 그 byte의 생성 주체는 미확정이다. first/second-chance, 내부 breakpoint site/미완료 thread plan도 추가 확인하지 않았다.

## 상태와 실행하지 않은 조치

이번 작업에서 대상 상태를 새로 조회하지 않았다. 마지막 승인 진단에서 PID20560은 정지·LLDB 부착 상태였으며, 그 상태를 변경하는 명령은 보내지 않았다. 기존 유지 지시를 그대로 따른다.

continue/detach/kill/step, register/memory write, EIP 이동, exception 정책 변경, 새 breakpoint, Native expression, LLDB/CLion 종료, Type3 UI·Copy/Paste·문서 저장/닫기/폐기는 모두 미실행이다. DLL/PLG/기존 runtime-001 및 이전 incident 파일은 수정하지 않았다. 새 산출물 두 개만 추가했다.

[incident-readonly-003-evidence.json](incident-readonly-003-evidence.json)에 파일 매핑·해시·원문 비교를 보존했다. **여기서 중단하며 추가 진단·복구는 별도 승인을 기다린다.** 이 비교만으로 재개나 debugger 해제를 권고하지 않는다.
