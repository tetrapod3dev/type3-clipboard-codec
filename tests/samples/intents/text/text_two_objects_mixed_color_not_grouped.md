# text_two_objects_mixed_color_not_grouped

## User intent / ground truth

- category: text
- fixture: `tests/samples/text/text_two_objects_mixed_color_not_grouped.txt`
- selected/copied object count: 2
- grouped/not grouped: not_grouped
- description: Two independent text objects selected together without grouping, with Army Green and Navy Blue colors.

This intent file documents an existing fixture; it is not a new capture.
Grouping is documented in the multi-object fixture tables in
[Text object reverse engineering](../../../../docs/text_object_reverse_engineering.md).
Color intent is documented in
[Text reverse engineering](../../../../docs/text_reverse_engineering.md#text-color-fixtures-and-ownership).
The existing order tables record attempted selection order as unknown.

## Machine-readable intent metadata

```yaml
intent_metadata:
  schema_version: 1
  object_count: 2
  grouping: not_grouped
  order_control_status: unknown
  attempted_selection_order: []
  actual_stored_order: unresolved
  notes:
    - attempted selection order was not recorded for this fixture
    - actual payload stored order is unresolved
```

## Order / ownership metadata

- attempted selection order: unknown
- order control status: unknown
- actual stored order: unresolved

Unknown explicitly means the attempted selection order was not recorded.
No selection order is inferred from the filename, parser chain order, anchor
coordinate order, or the order in which colors are listed above.
Intent metadata is reporting-only and must not be used by the parser, decoder,
or model to assign ownership or change active anchors.
