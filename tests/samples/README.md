# Type3 Clipboard Sample Fixtures

This directory contains reverse-engineering sample fixtures for the `type3_clipboard_codec` project.

These files are raw hex dumps of clipboard payloads copied from the Type3 program.
They are used as reference fixtures for parsing, testing, and documenting currently known binary structures.

## Future Geometry Fixture Plan

다음 geometry 구조 검증용 fixture 확장 계획은 아래 문서를 따른다.

- `docs/geometry_fixture_plan.md`

핵심 목적:
- contour count 다양성 확보
- `selected_shift=8` 관찰의 세션/좌표 조건 재현성 검증
- 현재 `strong observed candidate / provisional` 상태를 유지한 채 근거 확대
- contour tag/role (`0x03` family) 분리 검증용 rotated/reversed/topology-toggle fixture 확보

## Newly Captured Geometry Fixtures (Evidence Update)

아래 fixture는 `tests/samples/`에 실제 추가된 단일 객체 캡처다.
이번 섹션은 **ground truth intent**와 **current parser observation**을 분리해 기록한다.

해석 정책:
- fixture 파일명(`polyline`, `polygon`, `rectangle`)은 사람이 이해하기 위한 intent label이다.
- draw tool 이름과 내부 object/class semantic을 동일시하지 않는다.
- 현재 확실한 UI 관찰 용어는 status bar의 `곡선 객체`다(Observed).
- absolute offset은 계속 diagnostic only다.

### Ground truth intent (geometry)

| fixture | intent | open/closed | vertices (intent) | bbox (mm, intent) |
|---|---|---|---:|---|
| `polyline_2_points.txt` | 열린 폴리선 | open | 2 | x(11.111~88.888), y(22.222~22.222) |
| `polyline_3_points.txt` | 열린 폴리선 | open | 3 | x(11.111~88.888), y(22.222~44.444) |
| `polyline_5_points.txt` | 열린 폴리선 | open | 5 | x(11.111~88.888), y(11.111~44.444) |
| `polygon_5_sides.txt` | 닫힌 5각형 | closed | 5 | x(33.333~77.777), y(44.444~88.888) |
| `polygon_6_sides.txt` | 닫힌 6각형 | closed | 6 | x(33.333~77.777), y(44.444~99.999) |
| `rectangle_small.txt` | 사각형(소형 스케일) | closed | 4 | x(11.111~11.44433), y(22.222~22.66644) |
| `rectangle_large.txt` | 사각형(대형 스케일) | closed | 4 | x(11.111~33344.111), y(22.222~44466.222) |
| `rectangle_negative_offset.txt` | 사각형(음수 오프셋) | closed | 4 | x(-88.888~-55.555), y(-77.777~-33.333) |
| `rectangle_large_positive_offset.txt` | 사각형(대형 양수 오프셋) | closed | 4 | x(11111~11144.333), y(22222~22266.444) |
| `rectangle_recap_session2.txt` | `default_rectangle` 재캡처 | closed | 4 | `default_rectangle`와 동일 intent |

참고:
- scale 관련 fixture는 UI 스케일 문구보다 최종 측정 geometry 값을 우선한다.

### Current parser observation snapshot (provisional)

`tools/report_contour_header_candidates.py` 및 `tools/inspect_clipboard_hex.py` 기준:
- `polyline_2_points`: selected `(shift=8, kind=0, count=2, raw=0000000002000000)`, contour records=2
- `polyline_3_points`: selected `(shift=8, kind=0, count=3, raw=0000000003000000)`, contour records=3
- `polyline_5_points`: raw 후보 `count=5` 관찰, 현재 gate로 미선택, contour records=0
- `polygon_5_sides`: raw 후보 `count=5` 관찰, 현재 gate로 미선택, contour records=0
- `polygon_6_sides`: raw 후보 `count=6` 관찰, 현재 gate로 미선택, contour records=0
- rectangle 변형(`small/large/negative/large_positive/recap_session2`): 모두 selected `shift=8`, `kind=2`, `count=4`

추가 관찰:
- 현재 plausible count gate `{2,3,4,8,12}`는 `count=5/6` 샘플을 선택하지 못하므로 incomplete whitelist 상태다.
- `polyline_2_points`, `polyline_3_points`는 현재 classifier에서 `arc`로 표시되어 count-heavy heuristic 오분류 evidence가 존재한다.

UI/semantic 해석 주의:
- `polyline_3_points`와 `default_circular_arc`는 모두 `count=3`이지만, arc는 `anchor/control=2/1`, polyline_3는 `2/0`(중간 포인트 `unknown`)으로 관찰된다.
- 따라서 같은 count라도 semantic 확정은 아직 provisional로 유지한다.

## File: `default_rectangle.txt`

This file contains the hex dump of a copied rectangle-like object from Type3.

### Known source geometry

The copied object corresponds to a rectangle with the following geometric properties:

- lower-left corner: `(11.111, 22.222, 0)` mm
- width: `33.333` mm
- height: `44.444` mm

From this, the rectangle corners are:

- lower-left: `(11.111, 22.222, 0)` mm
- lower-right: `(44.444, 22.222, 0)` mm
- upper-right: `(44.444, 66.666, 0)` mm
- upper-left: `(11.111, 66.666, 0)` mm

### Expected bounding box

Type3 clipboard coordinates are stored as little-endian `double` values in **meters**, not millimeters.

Therefore, the expected bounding box values in the payload are:

- `xmin = 0.011111`
- `ymin = 0.022222`
- `zmin = 0.0`
- `xmax = 0.044444`
- `ymax = 0.066666`
- `zmax = 0.0`

Derived values:

- `width = 0.033333 m` = `33.333 mm`
- `height = 0.044444 m` = `44.444 mm`

### Expected contour geometry

The copied rectangle is represented in the clipboard payload through a `CContour` block.

The currently known contour point order is:

1. top-left     = `(0.011111, 0.066666, 0.0)` m
2. top-right    = `(0.044444, 0.066666, 0.0)` m
3. bottom-right = `(0.044444, 0.022222, 0.0)` m
4. bottom-left  = `(0.011111, 0.022222, 0.0)` m

In millimeters:

1. top-left     = `(11.111, 66.666, 0)` mm
2. top-right    = `(44.444, 66.666, 0)` mm
3. bottom-right = `(44.444, 22.222, 0)` mm
4. bottom-left  = `(11.111, 22.222, 0)` mm

### Known object/class chain

This sample is known to contain the following object/class sequence:

- `CZone`
- `CCourbe`
- `CContour`
- `CPropertyExtend`

### Known reverse-engineered facts from this sample

#### Common object header

Each known block appears to begin with:

- marker: `uint16 little-endian`, expected value `0xFFFF`
- class_id: `uint16 little-endian`
- name_len: `uint16 little-endian`
- class_name: ASCII string of length `name_len`

#### Repeated bbox block

For `CZone`, `CCourbe`, and `CContour`, the class header is followed by six `double` values:

- `xmin`
- `ymin`
- `zmin`
- `xmax`
- `ymax`
- `zmax`

#### Contour point record

Within `CContour`, the rectangle appears as 4 point records.

The currently inferred point structure is:

- `x: double`
- `y: double`
- `z: double`
- `w: double`
- `tag: uint32`

Notes:

- `w` appears to be `1.0` in this sample
- `tag` is not yet semantically decoded and should be treated as raw/provisional

#### Metadata

This sample repeatedly includes metadata indicating:

- key: `OBJECTINFOS_CLASSNAME`
- value: `CObDao`

This is known to exist, but the full metadata format is not yet fully specified.

#### Property extension block

A `CPropertyExtend` block is present after the contour block.

One observed little-endian `double` value within it corresponds to:

- `0.0005`

This may represent a style-related property such as line width, but this is not yet confirmed.

### Fixture usage guidance

Use `default_rectangle.txt` as the primary fixture for the first rectangle parsing milestone.

Tests based on this file should verify at least:

- recognition of `CZone`, `CCourbe`, `CContour`, `CPropertyExtend`
- parsing of bbox values in meters
- conversion from meters to millimeters
- extraction of exactly 4 contour points
- correctness of contour point order and coordinates
- derived width and height
- rectangle-oriented preview/summary output

### Reverse-engineering status

This fixture documents the first reliable rectangle sample.
It should be treated as:

- a confirmed reference for rectangle bbox and contour parsing
- a provisional reference for some internal fields such as `tag` and `CPropertyExtend` semantics

Do not overgeneralize unsupported format rules from this file alone.
Prefer conservative parsing and preserve unknown/raw bytes where possible.

## File: `two_rectangle.txt`

This file contains the hex dump of two independent rectangle-like objects copied together from Type3.

### Known source geometry

The sample contains two rectangles.

The first rectangle is the same geometry as `default_rectangle.txt`:

- lower-left corner: `(11.111, 22.222, 0)` mm
- width: `33.333` mm
- height: `44.444` mm

The second rectangle was created by copying the first rectangle and moving the copy `100.000 mm` to the right:

- lower-left corner: `(111.111, 22.222, 0)` mm
- width: `33.333` mm
- height: `44.444` mm

The two independent rectangles were selected at the same time and then copied to the clipboard.

### Expected combined bounding box

If Type3 stores or reports a combined selection/object bbox for this payload, the expected combined extents are:

- lower-left: `(11.111, 22.222, 0)` mm
- upper-right: `(144.444, 66.666, 0)` mm

In meters:

- `xmin = 0.011111`
- `ymin = 0.022222`
- `zmin = 0.0`
- `xmax = 0.144444`
- `ymax = 0.066666`
- `zmax = 0.0`

### Fixture usage guidance

Use `two_rectangle.txt` to investigate how Type3 represents multiple selected independent objects in a single clipboard payload.

Tests based on this file should eventually verify at least:

- detection of two rectangle-like objects
- preservation of each object's independent geometry
- recognition that the second rectangle is translated by `100.000 mm` in X from the first rectangle
- distinction between multi-object clipboard payloads and grouped/combined payloads
- preservation of raw object ordering as stored in the clipboard payload

### Reverse-engineering status

This fixture should be treated as:

- a confirmed source setup for two simultaneously copied independent rectangles
- a provisional reference for multi-object payload boundaries and ordering
- a provisional reference for any selection-level or aggregate bbox data

Do not assume yet that the two objects are stored as a simple concatenation of two `default_rectangle.txt`-like payloads.
Prefer conservative parsing and preserve unknown/raw bytes where possible.

## File: `two_rectangle_group.txt`

This file contains the hex dump of the same two rectangles from `two_rectangle.txt` after applying Type3's `결합` function and copying the result.

The Type3 Korean UI term `결합` must be preserved exactly. In other graphics programs such as Illustrator or PowerPoint, the closest common English concept is often "group", but that translation is provisional for this project.

### Known source geometry

The grouped/combined sample starts from the same two rectangles:

- rectangle 1 lower-left corner: `(11.111, 22.222, 0)` mm
- rectangle 2 lower-left corner: `(111.111, 22.222, 0)` mm
- each rectangle width: `33.333` mm
- each rectangle height: `44.444` mm
- rectangle 2 is translated `100.000 mm` to the right from rectangle 1

After creating these two rectangles, both were combined using Type3's `결합` function and then copied to the clipboard.

### Expected combined bounding box

The expected overall geometric extents are the same as `two_rectangle.txt`:

- lower-left: `(11.111, 22.222, 0)` mm
- upper-right: `(144.444, 66.666, 0)` mm

In meters:

- `xmin = 0.011111`
- `ymin = 0.022222`
- `zmin = 0.0`
- `xmax = 0.144444`
- `ymax = 0.066666`
- `zmax = 0.0`

### Fixture usage guidance

Use `two_rectangle_group.txt` to investigate how Type3's `결합` feature changes clipboard structure relative to two independent selected rectangles.

Tests based on this file should eventually verify at least:

- recognition of the same two rectangle geometries
- detection of any additional container/group/combined-object structure introduced by `결합`
- distinction between independent multi-object selection and `결합` output
- preservation of nested object or contour ordering if the grouped payload introduces hierarchy
- preservation of unknown group-related bytes until the `결합` structure is understood

### Reverse-engineering status

This fixture should be treated as:

- a confirmed source setup for two rectangles combined with Type3 `결합`
- a provisional reference for group-like or combined-object clipboard structure
- a provisional comparison pair with `two_rectangle.txt`

Do not collapse `결합` into an English-only "group" concept in parser or documentation names without keeping the Korean original term.
Prefer conservative parsing and preserve unknown/raw bytes where possible.

## Comparison: `two_rectangle.txt` vs `two_rectangle_group.txt` (`결합`)

Current reverse-engineering observations for this fixture pair:

- Both payloads contain the same visible class marker chain:
  - `CZone -> CCourbe -> CContour -> CPropertyExtend`
- `two_rectangle.txt` declares object count `2`.
- `two_rectangle_group.txt` declares object count `1`.
- Both payloads still expose two rectangle-like contour candidates.
- Contour ownership/bbox hierarchy differs between the two payloads:
  - independent multi-object selection and `결합` do not look identical at the byte-structure level.

Conservative interpretation status:

- `two_rectangle.txt` should currently be interpreted as independent multi-object selection.
- `two_rectangle_group.txt` should currently be interpreted as a provisional Type3 `결합` container/group/combined object candidate.
- Treat "group" / "combined object" as provisional English helper terms only; keep `결합` explicitly in docs, parser notes, and tests.
- Keep unknown group-related ranges as raw bytes until validated with additional fixtures.

Fixture usage guidance for tests/tools:

- Use geometry assertions (bbox, contour count, translation) for both files.
- Also assert structural differences (declared count, hierarchy hints, or parser notes).
- Do not flatten `결합` into a single contour-only object too early.
- Do not assume every multi-object payload is `결합`, and do not assume every `결합` payload is flat multi-selection.
- Use `tools/compare_group_samples.py` to print marker offsets, payload ranges, contour header candidates, and byte-difference ranges for this pair.

## Files: `color_*_rectangle.txt`

These files contain independent rectangle color fixtures. They intentionally use matching names so color tests do not need to infer or remember the color of `default_rectangle.txt`.

Current color fixtures:

- `color_black_rectangle.txt`
- `color_blue_rectangle.txt`
- `color_green_rectangle.txt`
- `color_cyan_rectangle.txt`
- `color_light_cyan_rectangle.txt`

The full Type3 palette list is kept in `src/type3_clipboard_codec/models/colors.py`.
These fixtures validate a small representative subset against real clipboard payloads.

### Shared source geometry

The source geometry is intentionally unchanged across all color fixtures:

- lower-left corner: `(11.111, 22.222, 0)` mm
- width: `33.333` mm
- height: `44.444` mm
- contour record count: `4`
- known object/class chain: `CZone`, `CCourbe`, `CContour`, `CPropertyExtend`

This makes the set useful for isolating style/color-related fields without changing bbox or contour geometry.

### Observed byte differences

All five color fixtures are currently `8192` bytes after hex normalization.

Comparing the color fixtures shows several changed ranges:

- Three earlier 16-byte-ish ranges near `CZone`, `CCourbe`, and `CContour` metadata differ between captures. These are currently treated as object/session identifier candidates, not color fields.
- The stable color-related candidate differences are inside `CPropertyExtend`.

The current color candidates are measured relative to the start of the `CPropertyExtend` payload:

- payload offset `0x79`: primary line color candidate
- payload offset `0x85`: secondary/mirrored line color candidate

Observed values:

| Sample | Color | HEX color (`RRGGBB`) | primary raw candidate | secondary raw candidate |
| --- | --- | ---: | ---: | ---: |
| `color_black_rectangle.txt` | Black | `000000` | `0x00000000` | `0x00000000` |
| `color_blue_rectangle.txt` | Blue | `000080` | `0x00008000` | `0x00008000` |
| `color_green_rectangle.txt` | Green | `008000` | `0x00000080` | `0x00000080` |
| `color_cyan_rectangle.txt` | Cyan | `008080` | `0x00008080` | `0x00008080` |
| `color_light_cyan_rectangle.txt` | Light Cyan | `00FFFF` | `0x0000FFFF` | `0x0000FFFF` |

These values are represented in the raw byte stream as little-endian `u32` values:

- Black: `00 00 00 00`
- Blue: `00 80 00 00`
- Green: `80 00 00 00`
- Cyan: `80 80 00 00`
- Light Cyan: `FF FF 00 00`

Note that the raw candidate value is not always numerically identical to the display HEX color. For example, the blue fixture is `#000080`, while the observed raw little-endian `u32` candidate is `0x00008000`.

### Reverse-engineering status

These fixtures should be treated as:

- a confirmed reference that changing rectangle color changes two `CPropertyExtend` color candidate fields
- a provisional reference for the exact semantic names of the two fields
- a provisional reference for the broader Type3 palette encoding

Do not assume yet that all object types use the same offsets or that the two candidate values always represent separate stroke/fill colors. More color-only fixture pairs are needed.

## File: `default_circle.txt`

This file contains the hex dump of a copied circle-like object from Type3.

### Known source geometry

The copied object corresponds to a circle with the following geometric properties:

- center: `(11.111, 22.222, 0)` mm
- radius: `33.333` mm

### Expected bounding box (mm)

- `xmin = -22.222`, `ymin = -11.111`, `zmin = 0.0`
- `xmax = 44.444`, `ymax = 55.555`, `zmax = 0.0`

### Contour structure

The circle is represented as an ordered sequence of **8 contour-related records** with an **alternating control/anchor pattern**.

- **Stored Order:** R1 (control), R2 (anchor), R3 (control), R4 (anchor), R5 (control), R6 (anchor), R7 (control), R8 (anchor)
- **Anchors:** R2, R4, R6, R8 (actual shape vertices)
- **Controls:** R1, R3, R5, R7 (curvature control vertices)

Stored order is critical for reverse engineering.

### Known object/class chain

This sample is known to contain the following object/class sequence:

- `CZone`
- `CCourbe`
- `CContour`
- `CPropertyExtend`

### Fixture usage guidance

Use `default_circle.txt` to validate full closed-loop alternating patterns.

Tests based on this file should verify at least:

- recognition of `CZone`, `CCourbe`, `CContour`, `CPropertyExtend`
- parsing of bbox values in meters
- conversion from meters to millimeters
- derived center, radius, and diameter
- detection of exactly 8 contour records/items
- preservation of actual contour record order
- classification of records into `anchor` and `control`
- anchor set = `R2`, `R4`, `R6`, `R8`
- control set = `R1`, `R3`, `R5`, `R7`
- circle-oriented preview/summary output

### Reverse-engineering status

This fixture documents the first reliable circle-like sample.

It should be treated as:

- a confirmed reference for circle bbox parsing
- a confirmed reference for derived center/radius/diameter
- a confirmed reference for the alternating anchor/control contour pattern in this sample
- a provisional reference for the exact mathematical semantics of each contour record
- a provisional reference for deeper `tag` decoding and `CPropertyExtend` semantics

Do not overgeneralize unsupported format rules from this file alone.
Prefer conservative parsing and preserve unknown/raw bytes where possible.

## File: `default_circular_arc.txt`

This file contains the hex dump of a copied circular-arc-like object from Type3.

### Known source geometry

This sample corresponds to a **90-degree circular arc**.

It is understood using the same circle model documented in `default_circle.txt`.

- circle center: `(11.111, 22.222, 0)` mm
- circle radius: `33.333` mm
- arc start: `(11.111, -11.111, 0)` mm
- arc end: `(-22.222, 22.222, 0)` mm

Based on the currently known ordered circle contour records, this arc corresponds to the segment:

- from `R8`
- to `R2`

That is, it represents the quarter-arc segment between the bottom anchor and the left anchor of the known circle model.

### Known object/class chain

This sample is known to contain the following object/class sequence:

- `CZone`
- `CCourbe`
- `CContour`
- `CPropertyExtend`

### Known reverse-engineered facts from this sample

#### Common object header

Each known block appears to begin with:

- marker: `uint16 little-endian`, expected value `0xFFFF`
- class_id: `uint16 little-endian`
- name_len: `uint16 little-endian`
- class_name: ASCII string of length `name_len`

#### Repeated bbox block

For `CZone`, `CCourbe`, and `CContour`, the class header is followed by six `double` values:

- `xmin`
- `ymin`
- `zmin`
- `xmax`
- `ymax`
- `zmax`

#### Contour structure

Unlike the full circle sample, this fixture represents only a partial circular segment.

The circular arc is represented by **3 contour records**:

1. start anchor
2. control vertex
3. end anchor

At the current reverse-engineering stage, the important facts are:

- this is **not** a full circle
- it consists of exactly 3 records (2 anchors + 1 control)
- stored record order must be preserved
- anchor/control role classification is determined by tags (`0x0C = control`, `0x0F/0x0D = anchor`)
- the arc segment from `R8` to `R2` in the full circle model corresponds to these 3 records

The exact low-level mathematical semantics of each arc-related contour record should still be treated conservatively unless supported by additional evidence.

#### Metadata

This sample repeatedly includes metadata indicating:

- key: `OBJECTINFOS_CLASSNAME`
- value: `CObDao`

This is known to exist, but the full metadata format is not yet fully specified.

#### Property extension block

A `CPropertyExtend` block is present after the contour block.

As with the other samples, this may contain style-related data, but its full semantics are not yet confirmed.

### Fixture usage guidance

Use `default_circular_arc.txt` as the primary fixture for the first circular-arc parsing milestone.

Tests based on this file should verify at least:

- recognition of `CZone`, `CCourbe`, `CContour`, `CPropertyExtend`
- identification as a circular arc
- extraction of exactly 3 contour records
- recognition of 2 anchors and 1 control vertex
- preservation of actual contour record order
- exposure of distinct arc start and end points
- arc-oriented preview/summary output

### Reverse-engineering status

This fixture documents the first reliable circular-arc-like sample.

It should be treated as:

- a confirmed reference for partial-circle object detection
- a confirmed reference that stored order matters for arc interpretation
- a provisional reference for exact arc contour mathematics
- a provisional reference for deeper `tag` decoding and `CPropertyExtend` semantics

Do not overgeneralize unsupported format rules from this file alone.
Prefer conservative parsing and preserve unknown/raw bytes where possible.

## File: `default_rounded_rectangle.txt`

This file contains the hex dump of a copied rounded-rectangle-like object from Type3.

### Known source geometry

The copied object corresponds to a rounded rectangle with the following geometric properties:

- bbox lower-left corner: `(11.111, 22.222, 0)` mm
- width: `75.000` mm
- height: `25.000` mm
- corner radius: `2.000` mm

From this, the expected outer bounding box is:

- lower-left: `(11.111, 22.222, 0)` mm
- lower-right: `(86.111, 22.222, 0)` mm
- upper-right: `(86.111, 47.222, 0)` mm
- upper-left: `(11.111, 47.222, 0)` mm

### Expected bounding box

Type3 clipboard coordinates are stored as little-endian `double` values in **meters**, not millimeters.

Therefore, the expected bounding box values in the payload are:

- `xmin = 0.011111`
- `ymin = 0.022222`
- `zmin = 0.0`
- `xmax = 0.086111`
- `ymax = 0.047222`
- `zmax = 0.0`

Derived values:

- `width = 0.075000 m` = `75.000 mm`
- `height = 0.025000 m` = `25.000 mm`

### Expected contour characteristics

This rounded rectangle is expected to be represented as a mixed contour consisting of:

- straight segments
- rounded corner arc segments

At the current reverse-engineering stage, the working expectation for this sample is:

- `contour_kind = 2`
- `point_count = 12`
- record stride = 36 bytes
- records consist of 8 anchors and 4 controls
- topology: 4 corners (arc: anchor-control-anchor) and 4 edges (line: anchor-anchor) shared between corners.

This should be treated as a structurally important sample because it mixes line-like and arc-like contour behavior in a single object.
Specifically, the 12 records represent a closed loop where arcs and lines alternate.
Previous 8-record interpretations were incomplete due to misalignment.

### Known object/class chain

This sample is known to contain the following object/class sequence:

- `CZone`
- `CCourbe`
- `CContour`
- `CPropertyExtend`

### Known reverse-engineered facts from this sample

#### Common object header

Each known block appears to begin with:

- marker: `uint16 little-endian`, expected value `0xFFFF`
- class_id: `uint16 little-endian`
- name_len: `uint16 little-endian`
- class_name: ASCII string of length `name_len`

#### Repeated bbox block

For `CZone`, `CCourbe`, and `CContour`, the class header is followed by six `double` values:

- `xmin`
- `ymin`
- `zmin`
- `xmax`
- `ymax`
- `zmax`

#### Contour point record

The currently inferred contour point structure remains:

- `x: double`
- `y: double`
- `z: double`
- `w: double`
- `tag: uint32`

However, the precise semantic interpretation of each of the 12 records in this rounded rectangle sample is not yet fully confirmed.

In particular:

- some records are expected to correspond to straight-segment anchors
- some records are expected to correspond to arc-related anchors or controls
- stored order is expected to matter

#### Metadata

This sample repeatedly includes metadata indicating:

- key: `OBJECTINFOS_CLASSNAME`
- value: `CObDao`

This is known to exist, but the full metadata format is not yet fully specified.

#### Property extension block

A `CPropertyExtend` block is present after the contour block.

As with the other samples, this may contain style-related data, but its full semantics are not yet confirmed.

### Fixture usage guidance

Use `default_rounded_rectangle.txt` as the primary fixture for the first mixed-geometry parsing milestone.

Tests based on this file should verify at least:

- recognition of `CZone`, `CCourbe`, `CContour`, `CPropertyExtend`
- parsing of bbox values in meters
- conversion from meters to millimeters
- derived width = `75.000 mm`
- derived height = `25.000 mm`
- preservation of the rounded-rectangle contour record order
- extraction of the expected contour header values
- rounded-rectangle-oriented preview/summary output

### Reverse-engineering status

This fixture documents the first reliable rounded-rectangle-like sample.

It should be treated as:

- a confirmed reference for rounded-rectangle bbox parsing
- a confirmed reference for mixed line/arc contour investigation
- a provisional reference for exact 12-record contour semantics
- a provisional reference for deeper `tag` decoding and `CPropertyExtend` semantics

Do not overgeneralize unsupported format rules from this file alone.
Prefer conservative parsing and preserve unknown/raw bytes where possible.

## File: `default_text.txt`

This file contains the hex dump of a copied text object from Type3.

### Text fixture coordinate policy update (confirmed)

For text fixtures, the controlled position is the text reference anchor, not the bbox lower-left corner.

Controlled anchor for baseline text fixture:

- `X 위치 = 111.111 mm`
- `Y 위치 = 222.222 mm`
- `Z 위치 = 0.000 mm`

Important capture rule:

- do not force bbox lower-left to `(0, 0, 0)` after changing text/style
- keep the reference anchor controlled
- treat bbox as observed/derived (it changes with text/font/size/spacing/glyph geometry)

This distinction is especially important with default alignment `중앙`.

Confirmed:

- `X 위치`, `Y 위치`, `Z 위치` are real Type3 Text mode UI fields used during fixture setup.
- fixture coordinate control is anchor-based; bbox is derived.

Provisional:

- exact binary offsets for anchor fields
- parser method used to recover anchor from payload (`direct_field` vs structural recovery)

Inspector/model layering for anchor fields:

- `text_anchor_expected_source`: fixture-ground-truth source (example: `confirmed_from_fixture_setup`)
- `text_anchor_parse_method`: parser path (example: `baseline_midpoint`, `bbox_center_fallback`)
- `text_anchor_parse_confidence`: parser confidence for that method (example: `provisional`, `fallback`)

### Text fixture inventory summary (actual files)

Inventory source:

- `tools/text_fixture_inventory.py --markdown`
- target directory: `tests/samples/text/*.txt`

아래 표는 `tools/text_fixture_inventory.py --markdown`의 최신 출력에서
정책/회귀에 중요한 행만 발췌한 것이다.

| file | declared_object_count | parsed_chain_candidate_count | fixture_intent_text | parser_text_candidate | fixture_intent_font | parser_font_candidate | font_notes | fixture_intent_anchor | parser_anchor_candidate | anchor_parse_method | fixture_intent_color | parser_color_candidate | color_candidate_source | color_confidence | color_notes | text_confidence | font_confidence | anchor_confidence | notes |
|---|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| default_text.txt | None | 1 | abcdefg | abcdefg | Arial | Arial | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | Black (observed baseline) | Black | fixed_offset_text_unverified | unresolved | expected=Black (observed baseline), detected=Black | candidate_match | candidate_match | provisional | - |
| text_font_arial_bold.txt | None | 1 | abcdefg | abcdefg | Arial Bold | Arial Bold | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | Black | Black | fixed_offset_text_unverified | provisional | - | candidate_match | candidate_match | provisional | - |
| text_color_army_green.txt | None | 1 | abcdefg | abcdefg | Arial | Arial | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | Army Green | Black | fixed_offset_text_unverified | unresolved | expected=Army Green, detected=Black; Single text object color candidate does not match fixture intent. | candidate_match | candidate_match | provisional | Parser limitation: expected text color and detected color mismatch. |
| text_color_navy_blue.txt | None | 1 | abcdefg | abcdefg | Arial | Arial | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | Navy Blue | Black | fixed_offset_text_unverified | unresolved | expected=Navy Blue, detected=Black; Single text object color candidate does not match fixture intent. | candidate_match | candidate_match | provisional | Parser limitation: expected text color and detected color mismatch. |
| text_group_same_color_two_objects.txt | None | 2 | abcdefg | abcdefg | Arial | Arial | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | ['Army Green', 'Army Green'] | ['Army Green', 'Army Green'] | ['text_candidate_unverified', 'text_candidate_unverified'] | mixed_object_ownership_unresolved | Per-object color ownership is provisional for multi-object text fixtures. | candidate_match | candidate_match | provisional | - |
| text_group_mixed_color_two_objects.txt | None | 2 | abcdefg | abcdefg | Arial | Arial | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | ['Army Green', 'Navy Blue'] | ['Navy Blue', 'Navy Blue'] | ['text_candidate_unverified', 'text_candidate_unverified'] | mixed_object_ownership_unresolved | Per-object color ownership is provisional for multi-object text fixtures.; expected=['Army Green', 'Navy Blue'], detected=['Navy Blue', 'Navy Blue'] | candidate_match | candidate_match | provisional | - |
| text_korean_basic.txt | None | 1 | Korean text (fixture-defined) | - | Arial | Arial | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | Black | Black | fixed_offset_text_unverified | provisional | - | unresolved | candidate_match | provisional | Parser limitation: Korean visible text candidate extraction unresolved. |
| text_multiline_basic.txt | None | 2 | abcd\nefgh | abcd<br>efgh | Arial | Arial | - | (111.111,222.222,0.000) | (111.111,222.222,0.000) | baseline_midpoint | Black | ['Black', 'Black'] | ['fixed_offset_text_unverified', 'fixed_offset_text_unverified'] | mixed_object_ownership_unresolved | Per-object color ownership is provisional for multi-object text fixtures. | candidate | candidate_match | provisional | Multiline fixture: parsed_chain_candidate_count is parser chain count, not confirmed Type3 object count. |

For full fixture list, regenerate from CLI output:

- `.\.venv\Scripts\python.exe tools\text_fixture_inventory.py --markdown`
- `.\.venv\Scripts\python.exe tools\text_fixture_inventory.py --json`

Font fixture status note:

- `text_font_arial_bold.txt` recapture mismatch is resolved (single-line `abcdefg`).
- `parser_font_candidate` for `Arial Bold` and HY font fixtures is still provisional/unresolved in current parser.

Text color fixtures and ownership note:

- single-object fixtures: `text_color_army_green.txt`, `text_color_navy_blue.txt`
- two-object fixtures: `text_group_same_color_two_objects.txt`, `text_group_mixed_color_two_objects.txt`, `text_two_objects_mixed_color_not_grouped.txt`
- parser color candidates are currently evidence-level; mixed-color per-object ownership is still provisional.

### Known source text

The copied object corresponds to a text object with the following source content:

- text: `abcdefg`

### Known source setup

The observed font name near the beginning of the payload is:

- `Arial`

At the current stage, this fixture should be treated as the first baseline text-object sample.

### Case mode fixture notes

#### `작은 대문자`

Test input text:

- `abcdefg`

Observed behavior:

- letters are displayed as uppercase-like forms
- first `A` appears larger
- subsequent letters appear smaller

Conservative interpretation:

- this is not equivalent to plain uppercase mode
- semantics are treated as small-caps-like behavior until confirmed by additional fixtures

#### `소문자`

Fixture design:

- source input text intentionally set to `ABCDEFG`
- then `소문자` option enabled

Purpose:

- determine whether Type3 stores original source text, transformed display text, mode flags, or a combination
- no single storage model is assumed yet

Parser implementation note:

- keep `source_text_candidate` and `display_text_candidate` conceptually distinct.
- do not force display transformation in parser until mapping is confirmed.

### Two-text-object fixture policy

Fixtures include a two-text-object setup for per-object extraction checks.

Text object #1 baseline:

- anchor: `(111.111, 222.222, 0.000)` mm
- text: `abcdefg`
- text height: `10 mm`
- width scale (`폭`): `100%`
- color: `Army Green`

Text object #2 baseline:

- anchor: `(211.111, 322.222, 0.000)` mm
- text: `1234567890`
- color by fixture:
  - same-color: `Army Green`
  - different-color: `Navy Blue`

Fixture validation targets:

- detect two independent text objects
- preserve per-object order
- extract per-object anchor/text/color candidates
- avoid accidental merge into one object

### Multi-line text fixture notes (order 40/41/42)

Text content:

- `abcd\nefgh`

Observed Type3 behavior:

- single-line text object: cannot apply `결합 해제`
- multi-line text object: can apply `결합 해제`
- after `결합 해제`, each line becomes an independent text object

Usage:

- investigate multiline encoding and line-break representation
- compare grouped/multiline decomposition behavior (`결합`, `결합 해제`)
- verify object ordering after decomposition
- determine whether content is represented as one paragraph-like object or multiple internal text runs

### Expected object characteristics

Unlike pure geometric objects such as rectangles, circles, and arcs, this sample appears to contain both:

- text-object data
- generated contour/outline geometry
- object metadata
- style/property-extension data

This means the parser must not treat text objects as simple strings only.

The fixture is expected to include text-related object/class blocks, including:

- `CZone`
- `CParagraphe`
- `CCourbe`
- `CContour`
- `CPropertyExtend`

The presence of `CParagraphe` is especially important because it appears to distinguish text-like objects from ordinary curve-only geometry.

### Known reverse-engineered facts from this sample

#### Font marker

The raw payload begins with a visible ASCII font name:

- `Arial`

This is currently a high-confidence text-object indicator.

However, the full surrounding font-record structure is not yet decoded.

#### Text content

The intended text content is:

- `abcdefg`

The ASCII characters appear in the payload as character-related records.

At the current stage, the parser should try to recover the visible text content conservatively.

Important:

- do not assume yet that all text is stored as a single contiguous string
- do not assume yet that all characters use the same encoding
- preserve raw character records where possible
- future fixtures must validate Korean text, digits, spaces, multiline text, and special characters

#### Text object bbox

텍스트 fixture에서 통제하는 기준값은 bbox lower-left가 아니라 text reference anchor다.

- controlled anchor: `X 위치`, `Y 위치`, `Z 위치`
- bbox는 glyph/정렬/폭/기울임/회전 등에 따라 달라지는 observed/derived geometry다.

따라서 text fixture 검증 시 우선 기준은 anchor 일치성이고, bbox는 부가 관찰값으로 취급한다.

#### Text outline geometry

This sample may contain generated curve/contour data corresponding to text outlines or baseline-related geometry.

The parser should not confuse text-outline `CCourbe` / `CContour` blocks with the primary text content itself.

Text parsing should therefore support both:

- high-level text object extraction
- preservation of any nested or generated geometry blocks

#### Metadata

This sample repeatedly includes metadata indicating:

- key: `OBJECTINFOS_CLASSNAME`
- value: `CObDao`

This is known to exist, but the full metadata format is not yet fully specified.

#### Property extension block

A `CPropertyExtend` block is present.

As with geometric samples, this may contain style-related data such as line width, color, or other rendering parameters, but the full semantics are not yet confirmed.

### Fixture usage guidance

Use `default_text.txt` as the primary fixture for the first text-object parsing milestone.

Tests based on this file should verify at least:

- recognition of text-like object structure
- detection of `CParagraphe`
- detection of font name `Arial`
- extraction of source text `abcdefg` if safely recoverable
- parsing of bbox values in meters
- conversion from meters to millimeters
- preservation of raw text-related records
- preservation of generated curve/contour geometry
- text-oriented preview/summary output

### Reverse-engineering status

This fixture documents the first reliable text-object sample.

It should be treated as:

- a confirmed reference for baseline text-object detection
- a confirmed reference that text objects contain more than simple geometry
- a confirmed reference for the presence of `CParagraphe`
- a provisional reference for font-record structure
- a provisional reference for character-record structure
- a provisional reference for text-outline geometry semantics

Known limitations from current inventory/parsing:

- many text fixtures report `declared_object_count = None`
- text anchor extraction is mostly structural (`baseline_midpoint`) and not direct binary-offset decode yet
- single-text color parsing may still resolve to `Black` for non-black fixture intents
- mixed-color two-object color ownership remains provisional
- Korean visible text extraction is incomplete for `text_korean_basic.txt` / `text_korean_mixed.txt`
- multiline internal representation and per-object run ownership remain provisional

Do not overgeneralize unsupported format rules from this file alone.
Prefer conservative parsing and preserve unknown/raw bytes where possible.
