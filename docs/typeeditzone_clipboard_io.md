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
