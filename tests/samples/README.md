# Type3 Clipboard Sample Fixtures

This directory contains reverse-engineering sample fixtures for the `type3_clipboard_codec` project.

These files are raw hex dumps of clipboard payloads copied from the Type3 program.
They are used as reference fixtures for parsing, testing, and documenting currently known binary structures.

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