# text_maxlength_a8_100mm

## Machine-readable intent metadata

```yaml
intent_metadata:
  schema_version: 1
  fixture: text_maxlength_a8_100mm.txt
  baseline_fixture: text_slotstyle_a8_baseline.txt
  intent_source: capture_operator
  analysis_status: inventory_only
  oracle_only: true
  visible_text: AAAAAAAA
  font: Arial
  character_count: 8
  changed_scope: text_object
  property: maximum_length
  baseline_value_mm: 0
  changed_value_mm: 100
  expected_ui_relationship: greater_than_natural_length
  observed_program_behavior: >-
    text box expands; glyphs are not compressed or stretched merely because the requested length exceeds natural length
  all_other_object_settings_held_constant: true
  baseline_natural_length_mm: 74.584
  baseline_maximum_length_mm: 0
  all_other_character_properties_held_constant: true
  one_intended_experimental_variable: true
  capture_reset_from_baseline: true
  capture_reset_between_fixtures: true
  base_character_attributes:
    height_mm: 10
    width_percent: 100
    slant_degrees: 0
    rotation_degrees: 0
    color: Army Green
    character_spacing_percent: 100
  baseline_capture_setup:
    lower_left_mm: [31.123, 72.234, 1.234]
    anchor_mm: [68.415, 72.234]
    alignment: center-bottom
  anchor_capture_setup_inherited_from_baseline: true
  resulting_lower_left_and_bbox: not_asserted
  z_coordinate_note: >-
    Baseline Z=1.234 mm is a diagnostic control against zero-heavy coordinate
    patterns; it adds no semantic Z parser meaning.
  experimental_rationale: >-
    Separate object/text-box setting changes above the natural 74.584 mm length from actual compression effects.
```

[Raw fixture](../../text/text_maxlength_a8_100mm.txt) ·
[Shared baseline and fixture plan](../../../../docs/text_spacing_maxlength_fixture_plan.md)

Capture-operator intent only. One setting is changed after restoring the baseline;
settings are reset before the next capture. Coordinates above identify baseline
capture setup, not measured resulting geometry. Text-box/lower-left/bounding-box
changes can be outcomes, especially for maximum length.

Maximum length applies to the entire text object/text box, not a selected character.
At 0 mm the program uses natural font length (baseline: 74.584 mm). UI compression
or negative-length inversion does not establish a mirror flag, sign bit, Y flip,
scale factor or transform matrix.

Labels, expected values and observed UI behavior may be consulted only after
future structural/differential results freeze. They cannot locate/select binary
structures. No byte localization, F4 validation or runtime interpretation is
performed for this fixture in this inventory step.
