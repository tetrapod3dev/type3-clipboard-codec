# TypeEditZone Clipboard I/O

## 1. 목적

이 문서는 Type3 CAM 전용 clipboard raw I/O의 현재 검증 상태를 기록한다.

목표는 Type3 clipboard의 raw payload를 손실 없이 dump/load하고, Type3 paste round-trip에 필요한 최소 포맷 묶음을 명확히 하는 것이다.

## 2. 검증된 포맷

현재 확인된 Type3 CAM clipboard 전용 포맷은 다음과 같다.

- `TypeEditZone`: observed id `50107`
- `TypeEditZoneVersion`: observed id `50108`

`TypeEditZone`은 main raw payload이며, `TypeEditZoneVersion`은 version/helper payload로 관찰되었다.

현재 관찰된 `TypeEditZoneVersion` bytes는 다음과 같다.

```text
01 00 00 00 51 02 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

## 3. 현재 Clipboard Format 목록 예시

probe에서 관찰된 clipboard format 목록 예시는 다음과 같다.

```text
[50107, 50108, 14, 3, 2, 8, 17]
```

이 중 현재 Type3 paste round-trip 검증 대상은 `50107`과 `50108`이다. 표준 그래픽 포맷으로 보이는 `14`, `3`, `2`, `8`, `17`은 현재 dump/load 대상이 아니다.

## 4. 수동 검증 결과

다음 수동 검증이 완료되었다.

- `probe` 성공
- `TypeEditZone` dump 성공: `dumped_bytes=8192`
- `TypeEditZoneVersion` dump 성공: `dumped_version_bytes=32`
- `TypeEditZone + TypeEditZoneVersion` bundle load 성공
- load 이후 re-dump 결과 `fc /b` 기준 동일
- Type3 paste 정상 동작

## 5. 실제 수동 검증 명령

실제 clipboard round-trip 검증은 다음 흐름으로 수행한다.

```powershell
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py probe

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py dump --out typeeditzone.bin

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py dump-version --out typeeditzone_version.bin

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py load --in typeeditzone.bin --version-in typeeditzone_version.bin

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py dump --out typeeditzone_redump.bin

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py dump-version --out typeeditzone_version_redump.bin

cmd /c fc /b typeeditzone.bin typeeditzone_redump.bin

cmd /c fc /b typeeditzone_version.bin typeeditzone_version_redump.bin
```

parser 개발/테스트 루프에서는 동일한 검증을 bundle 단위로 수행할 수 있다.

```powershell
.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py dump-bundle --dir clipboard_bundle

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py load-bundle --dir clipboard_bundle

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py verify-bundle --dir clipboard_bundle

.\.venv\Scripts\python.exe tools\clipboard_typeeditzone.py inspect-clipboard
```

## 6. 성공 기준

수동 검증 성공 기준은 다음과 같다.

- `has_typeeditzone=true`
- `has_typeeditzone_version=true`
- `TypeEditZone` byte-for-byte 동일
- `TypeEditZoneVersion` byte-for-byte 동일
- Type3 paste 정상 동작

## 7. 결론

현재 확인 기준으로 Type3 paste round-trip에는 `TypeEditZone + TypeEditZoneVersion` 2-format bundle이면 충분하다.

전체 clipboard snapshot/restore는 현재 필요하지 않다.

## 8. 보류 항목

다음 항목은 아직 구현 또는 검증 대상에서 제외한다.

- 표준 그래픽 포맷 `14`, `3`, `2`, `8`, `17` 복원
- ctypes fallback
- raw patch/edit 기능

## 9. 이후 개발 기준

이후 clipboard I/O 구현은 다음 기준을 따른다.

- clipboard I/O는 2-format bundle을 기본 경로로 사용한다.
- `TypeEditZoneVersion` bytes는 해석하지 말고 그대로 보존한다.
- `TypeEditZone` raw bytes는 strip/decode/normalize/trailing zero 제거 없이 보존한다.

## 10. Sample Capture Workflow

parser 개발용 sample fixture는 수동 hex 복사/붙여넣기 대신 capture CLI로 생성한다.

권장 흐름:

```powershell
.\.venv\Scripts\python.exe tools\capture_type3_sample.py `
  --name text_two_objects_same_color_not_grouped `
  --category text `
  --description "Two independent text objects, same color, not grouped" `
  --object-count 2 `
  --grouping not_grouped `
  --text "abcdefg|1234567890" `
  --anchors "111.111,222.222,0;211.111,322.222,0" `
  --color "Army Green" `
  --print-readme-snippet
```

CLI는 clipboard에서 `TypeEditZone`과 `TypeEditZoneVersion`을 모두 확인한 뒤 다음 산출물을 함께 남긴다.

- 기존 parser fixture와 호환되는 hex `.txt`
- raw bundle: `typeeditzone.bin`, `typeeditzone_version.bin`, `manifest.json`
- intent markdown template
- inspect text/json report
- README에 붙일 markdown snippet 출력

기본 저장 위치:

- geometry fixture: `tests/samples/<name>.txt`
- text fixture: `tests/samples/text/<name>.txt`
- geometry bundle: `tests/samples/bundles/geometry/<name>/`
- text bundle: `tests/samples/bundles/text/<name>/`
- intent: `tests/samples/intents/<category>/<name>.md`
- reports: `tests/samples/reports/<category>/<name>.inspect.*`

capture 직후 내부 검증을 수행한다.

- `typeeditzone.bin`이 clipboard dump와 byte-for-byte 동일해야 한다.
- `.txt` fixture를 hex decode한 bytes가 원본 `TypeEditZone` bytes와 동일해야 한다.
- `typeeditzone_version.bin`이 clipboard dump와 byte-for-byte 동일해야 한다.

기존 수동 workflow 중 hex 값을 별도 프로그램에서 복사해 fixture 파일에 붙여넣는 방식은 deprecated다. 새 fixture는 `.txt`와 raw bundle을 함께 남겨야 하며, README 자동 수정은 기본 동작이 아니라 `--print-readme-snippet` 출력물을 검토해 수동 반영하는 방식을 우선한다.
