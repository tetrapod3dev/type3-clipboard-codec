# Copy1회 관찰 결과 — 예외 정지로 중단

**COPY_PRODUCER_RUNTIME_PARTIAL**. 일부 Archive 연결과 prefix/초기 map을 실제로 관찰했지만 TypeEditZone 발행은 확인하지 못했다. **시험 PID20560은 예상 밖 예외에서 정지한 채 x86 LLDB가 부착되어 있다.** 이번 중단점은 모두 제거했으며 예외를 continue/무시하거나 detach/kill/quit하지 않았다. 해제가 안전한지 불확실하므로 다음 제어 조작은 사용자 판단이 필요하다.

## 실행 범위

사용자의 Stage B 명시적 승인 후 진행했다. 시작 시 Pltf/TypeEdit 실행 인스턴스는 관찰되지 않았다. 이전 PID17188/34968/36460을 현재 대상으로 사용하지 않았다. 최초 Pltf.exe 직접 실행은 PID36940이 종료되어 제품 UI가 만들어지지 않았다. 정상 바로가기/기존 기록의 **TypeEdit.exe**를 확인해 실행했고, 새 실제 Host **20560**, 시작15:16:19, Type31을 확인했다. 엔진 직접 실행의 종료 원인을 추측하지 않는다. `existing-hosts.json`, `launcher.json`, `actual-test-host.json` 참조.

새 문서가 빈 화면임을 `initial.png`로 확인한 후 사각형1개를 만들고 선택했다(`selected-test-rectangle.png`). Copy 명령은 **Ctrl+C 요청1회**뿐이다(`copy-once.json`). H 후보 Paste·추가 Copy·문서 저장/닫기/폐기는 하지 않았다. 예상 밖 정지 때문에 정상 Copy 완료 및 Clipboard 변경 여부는 확인하지 않았다. 현재 Clipboard를 읽거나 덤프하지 않았다.

## 실제 환경·초기 attach

x86 LLDB로 PID20560을 명시해 attach했고 target은 i386-pc-windows-msvc로 인식됐다. 최초 ntdll의 attach breakpoint0x80000003은 예상된 attach 정지로 식별한 후 관찰점을 설정했다. **후속 TypeEditDLL 예외와 구분한다.** 로드된 MFC80 base0x6C320000, Maude base0x03B30000, BaseDoc base0x03C60000의 경로/SHA가 기존 증거와 일치했다. `loaded-modules.json`에 기록했으며 MFC WriteObject/ctor의 진입 bytes도 memory에서 대조했다. relocation된 ctor 절대 상수는 해당 base를 반영해 해석했다.

## 실제 관찰된 연결

1. **Pltf.exe의 반환 주소 RVA0xC3532**에서 store Archive 생성자를 호출했다. A1이 Archive, F1이 입력 file이다. mode0, buffer size0x1000, 입력 buffer0이었다. 생성 후 A1+0x24는 F1, +0x38은null이다. +0x34에는 잔여 값이 보였지만 초기 count로 사용하지 않았다. F1 vptr는 MFC RVA0x7C24였으나 동적 file 클래스는 이번 범위에서 확정하지 않았다.
2. Pltf caller의 제한적 disassembly에서 CSharedFile형 호출 후보 뒤 Archive 생성, `CTxtFonts::BeginSave`, `CTxtFonts::Save(Archive&)`, 대상 virtual Serialize, `CTxtFonts::EndSave` 호출 순서가 보였다. IAT 대상은 MaudeTxt RVA0x247E0/0x25BB0/0x24890으로 LLDB module/symbol lookup에서 식별했다. 이것이 TypeEditZone producer라는 발행 관계는 아직 없다.
3. **첫 WriteObject는 같은 A1**이고 map+0x38이 아직null이었다. buffer base와 cursor 차이는6, 실제 먼저 기록된 bytes는 **000000000100**이었다. 이는 현재 buffer 내 offset이며 전체 stream 문맥은 발행 전이라 별도다.
4. WriteObject의 **직접 반환 주소는 MFC RVA0x4D433**이었다. LLDB backtrace의 상위 프레임은 직접 반환 주소와 달랐으므로 unwind를 완전히 신뢰하지 않았다. 상위 caller의 정확한 연결은 스택8frame만으로 확정하지 않는다.
5. O1의 동적 vptr는 **ShapeDLL RVA0xF7EC**였다. Maude CZone vtable과 같다고 가정하지 않았다. 이후 실제 작성된 `FFFF, schema1, length5, CZone` descriptor가 **buffer offset6**에 보였으므로 **직렬화 클래스 CZone**은 확인했다. O1의 정확한 동적 클래스/계층은 UNKNOWN이다. GetRuntimeClass 등 미확인 getter를 직접 실행하지 않았다.
6. 같은 A1의 `MapObject(null)` 진입을 두 번 관찰했다. 첫 것은 WriteObject 내부 호출, 두 번째는 WriteClass 내부 호출이며 그때 map count는1이었다. 두 번째 WriteObject 직전 count3이 확인되어 첫 class1/object2 등록과 일치했다. 이는 **이번 관찰된 stream**의 기록이다. TypeEditZone 발행과 아직 연결되지 않았으므로 G1/H 전체 가정을 일반 승격하지 않는다.
7. 두 번째 WriteObject의 직접 반환 주소는 **Maude RVA0x5AB54**로 기존 SerializeDeque2 호출부와 대응했다. 원 WriteObject 반환 관찰 후 count9와 buffer 진행이 보였다. 원래 stream bytes 전체를 수집하지 않았고 후속 클래스/객체 등록 전체를 새로 해석하지 않았다.

prefix가 실제 WriteObject 전에 있다는 점은 좁혔지만, 4바이트와2바이트 각각을 어느 함수가 쓰는지는 입증하지 않았다. Pltf callback을 발견했다고 prefix 구현 전체가 확인됐다고 주장하지 않는다.

## 중단 이유와 현재 상태

자체 one-shot 반환 관찰 뒤 continue하자 **thread#4, combase.dll thread**에서 **Exception0x80000003 at0x08E46AD0 / TypeEditDLL.dll**로 멈췄다. 현재 PC는 그 다음 byte로 표시됐고, 이번 중단점1/2/4/6 및 사용 후 소멸한3/5의 위치와 다르다. 원인은 UNKNOWN이다. 단순한 attach breakpoint, 정상 Copy 동작 또는 안전한 anti-debug 경로라고 해석하지 않았다.

지시문의 중단 정책에 따라 추가 관찰·Copy를 멈췄다. 이번 breakpoint **1,2,4,6을 삭제**했고3/5는one-shot으로 이미 소멸했다. 정상 수동 debugger prompt로 돌아온 상태이지만 **예외를 처리한 것은 아니다**. process continue/detach/kill/quit은 하지 않았다. LLDB 세션1632와 PID20560은 정지 상태로 남아 있다. 사용자 판단 전 프로그램을 계속하거나 닫지 않는다.

SetClipboardData 중단점은 설정됐지만 호출은 관찰되지 않았다. OLE 게시·TypeEditZone format ID도 확인하지 못했다. 따라서 COPY_PRODUCER_RUNTIME_VERIFIED가 아니다. 정상 Copy 완료·Clipboard 최종 내용은 UNKNOWN이다.

## 증거·보호

`debugger-observations.json`에 실제 명령/응답을 보존했고 Native 객체·Archive·버퍼의 일시 주소는 A1/F1/O1/O2/MAP1/BUF1 및STACK alias로 치환했다. code 주소와 모듈/RVA는 재현 근거로 남겼다. `runtime-result.json`은 요약이다. stop은 Copy 요청 후8건으로 상한32 이내였다. 관찰한 stack은8frame 이하, Archive memory는0x48B 이하, 버퍼는 prefix/descriptor32B 이내였다.

기존 Codec 파일과 이전 G1/H·profile·lock·H 후보 SHA는 작업 전 기준에서 변경0개다. 관찰한 설치 DLL은 디스크 SHA 그대로다. debugger의 소프트웨어 breakpoint는 일시적인 프로세스 메모리 변경이었고 디스크 DLL을 수정하지 않았다. 업무 모드는 **OFF**다. 이전 Stage A의 기존 구조 회귀15/15 PASS를 유지하며, 이번 예외를 시험 성공이나 회귀 PASS로 취급하지 않는다.

**다음 필요한 결정 하나:** 예외 정지 상태의 시험 인스턴스를 어떻게 처리할지 사용자 지시를 받는다. 안전 detach를 보장할 근거가 없어 현재는 정지 상태를 보존한다. 추가 Copy나 구조 역공학으로 넘어가지 않는다.
