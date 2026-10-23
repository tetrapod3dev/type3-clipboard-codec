# Pltf Copy 호출 지점 정적 교차 분석 005

판정: **PLTF_ARCHIVE_CROSSWALK_BLOCKED**

TypeEditZone publication: **UNKNOWN — PRODUCER_NOT_FULLY_LINKED**

## 파일 identity와 비교 한계

`C:\TypeEdit_2009\EXE\Pltf.exe` SHA256:
`f679f2641e60a41f62326e1c68c5e2c64d2415498bb1b92019c5f2d64245e662`

기존 003의 SHA와 일치한다. PE x86, preferred ImageBase 0x00400000. 역사적 반환 주소 0x004C3532를 이 기준으로 환산하면 RVA 0xC3532다. 기존 loaded-modules.json에는 Pltf 항목이 없으므로 그 파일만으로 런타임 Pltf 해시를 확인했다고 주장하지 않는다. 동일 디스크 SHA는 당시 메모리 내용과의 일치 증명이 아니다.

원본 debugger-observations.json은 명령 텍스트를 보존하지만 해당 Pltf 구간의 원시 메모리 instruction bytes는 보존하지 않았다. runtime-instruction-excerpt.json은 원본 행을 별도 발췌한 것이다. static-evidence.json의 runtime_encoding_inferred_not_captured는 텍스트로부터 재구성한 비교용 인코딩이며 런타임 캡처 바이트가 아니다.

## Runtime vs disk

모든 아래 RVA는 디스크 .text에 실제 raw-backed 바이트가 있다. 임의 시작점 디코딩은 함수 경계 증명이 아니다.

| RVA | 기존 런타임 명령 | 대응 디스크 바이트 | 결과 |
|---|---|---|---|
| C350E | call 0x64C516 | A7 C1 1F 5F F0 | 불일치 |
| C352D | call 0x64BD7E | CB 3A 53 32 72 | 불일치 |
| C3532 | movb $1,-4(ebp) | B8 6E D9 BC | 불일치 |
| C3536 | call *0x70B868 | 0B 49 9B 85 DB 9E | 불일치 |
| C354C | call *0x70B86C | AE 86 F4 5B 4C F2 | 불일치 |
| C3564 | call *eax | F5 20 | 불일치 |
| C3566 | call *0x70B870 | 47 F6 EF F2 CA 74 | 불일치 |

RVA [C34E0,C35B0) 안에 PE relocation 항목은 없다. 특히 상대 call opcode E8와 디스크 CB의 차이, 간접 call FF와 다른 opcode의 차이는 일반적인 이미지 base relocation만으로 설명되지 않는다. 실행 시 변환·보호·다른 코드 매핑 등의 구체 원인은 UNKNOWN이다. 임의 해독이나 코드 복원을 시도하지 않았다. 이전 TypeEditDLL 예외의 .protect 문제와 같은 원인이라고 결론내리지 않는다.

## 기존 런타임에서만 입증된 순서

다음은 새로운 정적 확인이 아니라 원본 런타임 근거의 범위다.

1. C350E 호출 전에 0x1000, 0x2042를 push하고 ECX에 EBP-0x98을 전달한다. CSharedFile 계열 후보이나 디스크 thunk와 대조 불가로 정확한 생성자 확정은 보류한다.
2. C352D 호출에 파일 후보 EBP-0x98, mode 0, buffer 4096, buffer pointer 0을 전달한다. 실제 MFC CArchive 생성자 중단 관찰과 반환 주소가 연결되어 Archive 지역 변수는 EBP-0x64로 대응한다.
3. C3536의 간접 호출은 과거 IAT 메모리 및 image lookup으로 CTxtFonts::BeginSave와 대응했다.
4. C3540에서 함수 0x4975E0에 [EBP+8]을 전달한다. 역할 UNKNOWN이며 지금 디스크로 의미를 채우지 않는다.
5. C354C는 Archive 주소를 인자로 CTxtFonts::Save를 호출한다는 기존 관찰이 있다.
6. C3564는 [EBP+8] 객체의 vtable+8에 같은 Archive를 전달한다. 그 객체의 정확한 동적 타입과 전체 함수 ABI는 UNKNOWN이다.
7. C3566은 기존 관찰상 CTxtFonts::EndSave다.

함수 진입·종료 경계, 반환값, Archive Close/Destructor, 파일 버퍼 Detach와 소비자, 직접 caller는 디스크 불일치 때문에 확정하지 않았다. 과거 unwind의 Pltf C45B6과 직접 반환 주소의 차이도 해소됐다고 주장하지 않는다.

## Prefix와 직렬화 범위

과거 첫 WriteObject 진입에 동일 Archive의 buffer cursor는 +6이었고 buffer는 `00 00 00 00 01 00`이었다. 후속 관찰에 CZone descriptor가 byte 6에서 시작했다. 처음 map pointer는 NULL, 이후 MapObject(null) 및 클래스/객체 등록 결과는 기존 관찰 그대로 유지한다.

그러나 이번 분석으로 4바이트와 2바이트를 기록한 정확한 Write 명령이나 함수는 특정하지 못했다. CTxtFonts::Save가 일부에 기여할 가능성을 확인된 사실로 바꾸지 않는다. CTxtFonts 하위 함수를 연쇄 추적하거나 다른 후보를 더 찾지 않고 Stage A의 차단 조건에서 종료한다.

G1/H 및 기존 형상 표본의 prefix·Contour·36바이트 요소 대응은 기존 조건부 계약을 유지한다. 이번 결과는 그 파서를 무효화하거나 생산자 초기 문맥을 확정하지 않는다. 문자 등 다른 객체 계열을 추가 지원하지 않았다.

## Clipboard 발행과 중단 위치

CZone 직렬화 관찰은 TypeEditZone 발행 증명이 아니다. 기존 시험은 Copy 완료 및 SetClipboardData 발행이 확인되기 전에 예외로 중단됐다. 이번에도 생성 버퍼의 직접 소비자·OLE 게시·지연 렌더링·형식 ID와 연결하지 못했다.

중단 위치는 Pltf RVA C352D/C3532의 런타임-디스크 명령 불일치다. Stage B의 함수 전체 분석과 Stage D의 caller/consumer 추적을 강행하지 않았다. 새 244개 PE 검색, 전체 XREF 또는 Native 함수 호출은 하지 않았다.

## 회귀와 보존

- 기존 crosswalk-001 및 crosswalk-002 테스트: **15/15 PASS** (pytest -q -p no:cacheprovider, PYTHONDONTWRITEBYTECODE=1).
- 첫 시도는 automation .venv에 pytest가 없어 미실행 오류가 났고, 설치 없이 기존 Codec .venv로 실행했다.
- incident-closeout-evidence.json의 보호 원본 19개 SHA를 재검증: 변경 0개.
- INCIDENT_CLOSED, COPY_PRODUCER_RUNTIME_PARTIAL 및 예외 원인 UNKNOWN 유지. PID나 세션을 재사용하지 않았다.
- Type3/LLDB 실행·부착, Clipboard 접근, 문서·DLL·PLG·Ghidra DB 및 Decoder/Encoder 수정 없음. 업무 모드 OFF 파일 유지.
- 전체 Codec 테스트를 실행했다고 주장하지 않는다. Git commit/reset/checkout/clean/push 없음. 시작 Git HEAD: 93e4cd5bccb3ef2f9dad0ae92adaf524a3a9e317; 시작 status는 clean이었다.

## 다음 결정

이번 정적 경로는 여기서 중단한다. prefix 생산자와 발행 연결은 UNKNOWN으로 남긴다. 추가 동적 실험 계획은 작성하거나 시작하지 않았다. LLDB의 예상 밖 breakpoint 예외 원인과 안전한 분리 계약이 미확정이었던 사고 이력이 있으므로, 동일 조건의 디버깅 반복은 프로세스 정지·미저장 시험 문서 소실 위험을 다시 만든다. 다시 관찰을 고려하기 전에 이 재발 위험과 도구 적합성을 별도 검토해야 한다. 새 실기를 자동 제안하거나 준비하지 않는다.
