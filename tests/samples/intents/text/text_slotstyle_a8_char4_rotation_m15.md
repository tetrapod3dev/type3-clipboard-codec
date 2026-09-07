# text_slotstyle_a8_char4_rotation_m15

## Machine-readable intent metadata

```yaml
intent_metadata:
  schema_version: 1
  visible_text: AAAAAAAA
  font: Arial
  character_count: 8
  lower_left_mm:
  - 31.123
  - 72.234
  - 1.234
  anchor_mm:
  - 68.415
  - 72.234
  alignment: center-bottom
  target_character_index_1based: 4
  all_other_character_properties_held_constant: true
  capture_reset_between_fixtures: true
  base_character_attributes:
    height_mm: 10
    width_percent: 100
    slant_degrees: 0
    rotation_degrees: 0
    color: Army Green
  z_coordinate_note: Z=1.234 mm was intentionally used as a diagnostic control to
    avoid zero-heavy coordinate byte patterns. No Z semantic decoding change is implied.
  changed_property: rotation_degrees
  base_value: 0
  changed_value: -15
```

User-provided controlled capture intent; oracle/reporting only. Not a structural selector.
Each capture changes only one property of the fourth A, then resets to baseline.
Byte-level differences may include derived layout or unexplained capture state.
