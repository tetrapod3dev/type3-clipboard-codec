# Type3 Text Object Reverse-Engineering Planning

This document defines the current understanding, terminology, and reverse-engineering strategy for Type3 text objects.

The purpose of this document is:

1. preserve original Type3 terminology exactly as observed in the UI
2. avoid losing semantic meaning during translation
3. derive stable parser targets
4. design controlled clipboard fixture samples
5. support future parser/data-model implementation

---

## Important Terminology Policy

### MUST preserve original Korean UI terminology

Type3 UI terminology observed from the Korean UI MUST be preserved exactly.

Even if English translations are introduced later for parser field names or internal APIs:

- the original Korean term MUST remain documented
- the English translation MUST be treated as provisional unless verified
- reverse-engineering notes must remain traceable to original UI wording

Example:

| Korean UI | Proposed English | Notes |
|---|---|---|
| 자유 위치 | free position | provisional translation |
| 인쇄 비례 | print proportional | provisional translation |
| 기본선 위 | above baseline | inferred meaning |

Never discard original Korean wording.

---

## Current Understanding of Type3 Text Objects

Type3 text objects appear to contain:

- general CAM object geometry/state information
- text content
- text layout information
- typography information
- alignment/baseline behavior
- paragraph/line-spacing behavior
- optional rendering modifiers

Text objects should NOT yet be treated as "simple strings".

They likely contain:

- object-level geometry
- insertion/alignment anchors
- typography parameters
- contour/outline geometry
- metadata blocks
- rendering/layout flags

---

## Object-Level Information (Selection Mode)

The following fields are visible while the object is selected in normal selection mode.

These may represent either:

- persisted object fields
- derived UI values
- calculated helper values

Current status is intentionally conservative.

### W / H / D

Observed UI labels:

- W
- H
- D

Current interpretation:

| Field | Interpretation | Confidence |
|---|---|---|
| W | width | medium |
| H | height | medium |
| D | dimension/depth | low |

Notes:

- D appears to remain `0` during normal 2D usage
- W/H may be derived from bbox geometry instead of explicitly stored values

### Cx / Cy / Cz

Observed UI labels:

- Cx
- Cy
- Cz

Current interpretation:

- possible object center coordinates
- may be derived by UI instead of persisted

Status:

- unresolved
- parser should not assume persisted storage yet

### X / Y / Z

Observed UI labels:

- X
- Y
- Z

Possible interpretations:

- insertion point
- alignment anchor
- object origin
- transform origin

Still unresolved.

---

## Text Mode UI Fields

The following fields are visible while editing text objects in "Text mode".

These are highly likely to correspond to actual persisted text-object data.

### 글꼴 / Font

Original Korean UI:

- 글꼴

Observed behavior:

- selectable font family

Likely stored:

- font name
- font identifier
- font metrics reference

High-confidence parser target.

### 정렬 / Alignment

Original Korean UI:

- 왼쪽
- 중앙
- 오른쪽
- 맞춤
- 자유 위치

Current interpretation:

| Korean | Proposed English | Notes |
|---|---|---|
| 왼쪽 | left align | likely enum |
| 중앙 | center align | likely enum |
| 오른쪽 | right align | likely enum |
| 맞춤 | justify | independent toggle-like behavior |
| 자유 위치 | free position | unresolved semantics |

Observed behavior:

- 자유 위치 appears mutually exclusive with left/center/right alignment
- 맞춤 behaves independently

Possible internal structure:

- alignment enum
- justify flag
- free-position flag

Still unresolved.

### 높이 / Height

Original Korean UI:

- 높이

Observed behavior:

- text height
- unit: mm

High-confidence persisted field.

### 폭 / Width

Original Korean UI:

- 폭

Observed behavior:

- character width scale
- unit: %

Likely corresponds to horizontal scaling/stretch.

High-confidence persisted field.

### 기울기 / 이탤릭 / Slant / Italic

Original Korean UI:

- 기울기
- 이탤릭

Observed behavior:

- angle-based slant system
- unit: degrees
- `0°` disables italic state
- non-zero enables italic state
- italic button toggles between:
  - `0°`
  - `15°`

Important observation:

The actual persisted value is likely:

- slant angle

NOT:

- simple italic boolean

Parser should prioritize numeric angle extraction.

### 문자 리스트

Original Korean UI:

- 문자 리스트

Observed behavior:

- UI popup helper for selecting special characters

Current interpretation:

- UI-only helper
- likely NOT persisted

Low reverse-engineering priority.

### 미러 / Mirror

Original Korean UI:

- 미러

Observed behavior:

- horizontal mirroring
- alignment direction changes visually
- cursor movement reverses

Likely persisted:

- mirror flag
- possibly transform matrix modification

High-confidence parser target.

### X 위치 / Y 위치

Original Korean UI:

- X 위치
- Y 위치

Observed behavior:

- position of alignment anchor/reference point
- unit: mm

Important:

These values may differ from bbox origin.

Likely persisted.

### 최대 길이 / Maximum Length

Original Korean UI:

- 최대 길이

Observed behavior:

- unit: mm
- text is forced to fit within specified length
- if text exceeds:
  - width scale shrinks
- if text is shorter:
  - spacing expands

Likely persisted:

- max_length field
- possibly additional justification/stretch behavior

High reverse-engineering priority.

### 고정 / 비례 / 인쇄 비례

Original Korean UI:

- 고정
- 비례
- 인쇄 비례

Observed behavior:

- mutually exclusive radio-button behavior
- related to multiline spacing

Descriptions observed:

| Korean | Original Description |
|---|---|
| 고정 | 고정 선을 기준으로 단의 간격을 조절합니다. |
| 비례 | 비례 선에 맞추어 단의 간격을 조절합니다. |
| 인쇄 비례 | 인쇄 비례 선에 맞추어 단의 간격을 조절합니다. |

Observed units:

| Mode | Unit |
|---|---|
| 고정 | mm |
| 비례 | % |
| 인쇄 비례 | % |

Possible internal structure:

- spacing mode enum
- spacing value
- spacing unit

High parser relevance.

### 선 압축 / 단락 압축

Original Korean UI:

- 선 압축
- 단락 압축

Descriptions observed:

| Korean | Description |
|---|---|
| 선 압축 | 선에 의해 압축합니다 |
| 단락 압축 | 단락에 의해 압축합니다 |

Observed behavior:

- mutually exclusive
- no immediately visible effect found yet

Status:

- unresolved
- lower parser priority for now

### 회전 / Rotation

Original Korean UI:

- 회전

Observed behavior:

- text object rotation
- unit: degrees

High-confidence persisted field.

### 간격 / Tracking / Character Spacing

Original Korean UI:

- 간격

Observed behavior:

- character spacing/tracking
- unit: %
- `100%` appears default

Likely persisted:

- tracking percentage value

The toggle indicator itself may only reflect:

- value != `100%`

Parser should prioritize numeric value.

### 밑줄 / Underline

Original Korean UI:

- 밑줄

Observed behavior:

- toggle + percentage value
- default appears `-40%`
- relative to baseline

Likely persisted:

- underline enabled flag
- underline offset percentage

### 오른쪽에서 왼쪽 / RTL

Original Korean UI:

- 오른쪽에서 왼쪽

Observed behavior:

- text input direction reverses
- cursor behavior changes accordingly

Likely persisted:

- RTL flag

### 윗 첨자 / 아래 첨자 / Superscript / Subscript

Original Korean UI:

- 윗 첨자
- 아래 첨자

Observed behavior:

- mutually exclusive radio behavior

Likely persisted:

- script mode enum

### 대문자 / 작은 대문자 / 소문자

Original Korean UI:

- 대문자
- 작은 대문자
- 소문자

Observed behavior:

| Korean | Observed behavior |
|---|---|
| 대문자 | converts all letters to uppercase |
| 작은 대문자 | capitalizes first letter of words |
| 소문자 | converts all letters to lowercase |

Unresolved:

- whether original text or transformed text is persisted

Important parser target.

### 기본선 위 / 기본선 아래

Original Korean UI:

- 기본선 위
- 기본선 아래

Observed behavior:

- baseline-relative positioning mode

Likely persisted:

- baseline alignment mode enum

### 옵셋 / Offset

Original Korean UI:

- 옵셋

Observed behavior:

- percentage offset relative to text height
- affects position relative to baseline

Likely persisted.

### 자동간격

Original Korean UI:

- 자동간격

Observed behavior:

- cyclic button with 5 visual states
- no textual explanation found yet

Status:

- unresolved
- likely enum/flag field

Lower priority for initial parser implementation.

---

## Reverse-Engineering Strategy

The parser implementation MUST proceed conservatively.

Do NOT overgeneralize format rules from a single fixture.

Unknown fields should remain:

- preserved
- raw-accessible
- minimally interpreted

---

## Fixture Design Philosophy

The most important rule:

### Only change ONE variable per fixture

Bad:

- changing font + height + rotation simultaneously

Good:

- only changing rotation
- only changing alignment
- only changing width scale

This is critical for reliable binary diffing.

---

## Required Text Fixture Categories

Fixture ID gaps are intentional and reserved for future controlled fixtures.

### 1. Base Structure Fixtures

Purpose:

- identify repeated text-record structures
- identify text-object block boundaries

Required fixtures:

| Fixture ID | Description |
|---|---|
| T001 | base text object |
| T002 | single character |
| T003 | two characters |
| T004 | text with spaces |
| T005 | multiline text |

### 2. Encoding Fixtures

Purpose:

- identify character encoding strategy

Required fixtures:

| Fixture ID | Description |
|---|---|
| T010 | lowercase ASCII |
| T011 | uppercase ASCII |
| T012 | digits |
| T013 | mixed ASCII |
| T014 | Korean text |
| T015 | special characters |

### 3. Font Fixtures

Purpose:

- identify font-related storage

Required fixtures:

| Fixture ID | Description |
|---|---|
| T020 | Arial |
| T021 | alternative sans-serif |
| T022 | serif font |
| T023 | decorative/script font |

### 4. Position / Alignment Fixtures

Purpose:

- identify anchor/alignment fields

Required fixtures:

| Fixture ID | Description |
|---|---|
| T030 | origin position |
| T031 | offset position |
| T033 | left align |
| T034 | center align |
| T035 | right align |
| T036 | justify |
| T037 | free position |

### 5. Transform Fixtures

Purpose:

- identify geometry-transform fields

Required fixtures:

| Fixture ID | Description |
|---|---|
| T040 | base height |
| T041 | changed height |
| T042 | width 100% |
| T043 | width 120% |
| T045 | slant 0 |
| T046 | slant 15 |
| T048 | rotation 0 |
| T049 | rotation 45 |
| T051 | mirror off |
| T052 | mirror on |

### 6. Typography Fixtures

Purpose:

- identify spacing/layout fields

Required fixtures:

| Fixture ID | Description |
|---|---|
| T060 | tracking 100% |
| T061 | tracking 80% |
| T063 | max length 0 |
| T064 | max length short |
| T066 | underline off |
| T067 | underline on |
| T069 | baseline above |
| T070 | baseline below |
| T073 | fixed spacing |
| T074 | proportional spacing |
| T075 | print proportional spacing |

### 7. Advanced Mode Fixtures

Purpose:

- identify advanced text-mode flags

Required fixtures:

| Fixture ID | Description |
|---|---|
| T080 | RTL off |
| T081 | RTL on |
| T082 | superscript |
| T083 | subscript |
| T084 | uppercase mode |
| T085 | small-caps mode |
| T086 | lowercase mode |
| T087 | line compression |
| T088 | paragraph compression |
| T089-T093 | automatic spacing states |

---

## Fixture Metadata Requirements

Every fixture MUST include metadata documentation.

Required metadata:

```text
- fixture_id
- source text
- font
- bbox origin
- anchor position
- alignment
- height
- width scale
- slant angle
- rotation
- mirror state
- max length
- tracking
- underline state
- rtl state
- superscript/subscript state
- case transform state
- baseline mode
- spacing mode/value
- notes
```

Without this metadata, binary comparisons become unreliable.

---

## Parser Design Guidance

Parser implementation should initially prioritize extraction of:

- text content
- font
- bbox
- anchor position
- height
- width scale
- slant angle
- rotation
- mirror flag
- alignment mode
- tracking
- max length

Secondary priority:

- RTL
- underline
- baseline modes
- superscript/subscript
- case transforms
- line spacing modes

Unknown fields should remain raw-preserved.

---

## Current Reverse-Engineering Status

The current understanding should be treated as:

- partially confirmed
- highly provisional
- evidence-driven

No field semantics should be considered fully authoritative until validated across multiple controlled fixtures.

Conservative parsing is strongly preferred.
