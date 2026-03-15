# Architecture: TYPE3 Clipboard Codec

본 문서는 `type3_clipboard_codec` 라이브러리의 설계 의도와 구조를 설명한다.

## 계층 구조 및 패키지 책임

### 1. Adapters (`src/type3_clipboard_codec/adapters`)
- **역할**: 다양한 외부 입력 소스로부터 원시 바이트 데이터를 수집하는 인터페이스와 구현체를 제공한다.
- **주요 컴포넌트**:
  - `InputAdapter`: 입력 소스 추상 인터페이스.
  - `ManualHexInput`: 사용자가 직접 붙여넣은 16진수 문자열로부터 바이트를 생성한다.
  - `Win32ClipboardAdapter`: (향후) Windows 클립보드 API와 연동하여 실제 클립보드 데이터를 획득한다.

### 2. Codec (`src/type3_clipboard_codec/codec`)
- **역할**: 전체 프로세스의 오케스트레이션을 담당하며, 디코딩과 인코딩의 진입점을 제공한다.
- **주요 컴포넌트**:
  - `Decoder`: 바이트 데이터를 정형화된 모델 객체로 변환한다.
  - `Encoder`: (향후) 수정된 모델 객체를 다시 바이트 데이터로 변환한다.
  - `PreviewRenderer`: 디코딩된 결과를 CLI에서 보기 좋게 렌더링한다.

### 3. Parsers (`src/type3_clipboard_codec/parsers`)
- **역할**: 이진 데이터의 실제 분석 및 객체 타입 식별을 수행한다.
- **주요 컴포넌트**:
  - `ObjectDetector`: 이진 데이터 내의 마커나 패턴을 분석하여 어떤 객체(Text, Contour 등)인지 판별한다.
  - `ParserRegistry`: 등록된 객체별 파서를 관리하여, 확장성을 보장한다.
  - `SpecificParsers`: 각 객체 타입별로 정밀한 필드 분석을 수행한다.

### 4. Models (`src/type3_clipboard_codec/models`)
- **역할**: 데이터가 분석된 이후의 상태를 유지하는 데이터 클래스들이다.
- **설계 특징**:
  - **Editable**: 향후 속성 변경 및 재인코딩을 위해 모든 필드는 변경 가능하도록 설계한다.
  - **Preservative**: 분석되지 않은 원시 데이터나 후보 값들을 필드에 남겨두어 역공학 과정에서의 정보 손실을 최소화한다.

### 5. Utils (`src/type3_clipboard_codec/utils`)
- **역할**: 이진 데이터 읽기, Hex 문자열 처리, ASCII 스캔 등 공통 유틸리티를 제공한다.

## 확장 방향 및 미확정 사항
- 현재는 이진 포맷이 완전히 분석되지 않았으므로, **Heuristic(경험적)** 분석에 의존한다.
- `ObjectDetector`는 알려진 마커(ASCII 문자열)를 기준으로 객체 경계를 추정한다.
- 향후 새로운 객체 타입이 발견되면 `parsers/registry.py`를 통해 쉽게 새 파서를 추가할 수 있다.
- **Encoding** 기능은 초기 단계에서는 인터페이스만 정의하고, 각 객체의 필드 의미가 명확해질 때 구현한다.
