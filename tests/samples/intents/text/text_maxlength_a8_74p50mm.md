# text_maxlength_a8_74p50mm

## Machine-readable intent metadata

```yaml
intent_metadata:
  schema_version: 1
  fixture: text_maxlength_a8_74p50mm.txt
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
  changed_value_mm: 74.50
  baseline_natural_length_mm: 74.584
  exact_previous_serialized_natural_extent_mm: 74.58390177353341
  provisional_crossover_mm: 74.65848567530693
  crossover_status: post_discovery_hypothesis_only
  relationship_to_exact_natural_extent: below
  relationship_to_provisional_crossover: below
  observed_ui_compression: not_recorded
  baseline_maximum_length_mm: 0
  all_other_object_settings_held_constant: true
  all_other_character_properties_held_constant: true
  one_intended_experimental_variable: true
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
  experimental_rationale: >-
    Sample clearly below the exact natural-length boundary but very near it.
```

[Raw fixture](../../text/text_maxlength_a8_74p50mm.txt) ·
[Shared baseline and boundary fixture plan](../../../../docs/text_spacing_maxlength_fixture_plan.md#maximum-length-boundary-fixture-inventory--analysis-pending)

This is an object/text-box-level control with maximum length as the only intended
variable. Baseline setup is inherited; resulting geometry is not asserted.
UI compression is not recorded and must not be inferred from length, geometry,
serialized bytes or the provisional formula.

Oracle isolation: all metadata, N and the provisional crossover are experiment
design labels only. Future raw/structural results must freeze before consulting
these labels. They cannot locate bytes, select a CParagraphe, choose a scalar
field, nominate a run or validate a structural candidate. Filenames are inventory
identifiers only, never runtime/parser selectors. No expected raw bytes or
authoritative scalar is specified. Boundary analysis is pending.

