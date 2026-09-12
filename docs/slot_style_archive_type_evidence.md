# Slot-style archive-type evidence metadata

This batch records vendor **archive representation** on the diagnostic analyzer side.
A confirmed archive type does **not** mean that runtime layout is universally
confirmed or that UI semantic ownership is confirmed. Production parser output
and all recognition decisions are unchanged.

## Representation and scope

The existing height, width, slant and rotation candidate summaries in
`tools/analyze_text_slot_style_fields.py` receive two additive keys:

- `archive_type_evidence: "confirmed_archive_double"`
- `archive_type_provenance`: binary, serializer/write RVAs, source/Style member
  offsets, the **code-model** record-relative range, binary64 representation and
  archive width, plus explicit applicability/ownership limits.

The spacing analyzer adds the same keys to `spacing_encoding_summary` and,
when requested, `spacing_ratio_summary`. The latter remains a
`spacing_ratio_f64_candidate`; existing candidate confidence is unchanged.

These are annotations of the reviewed field hypotheses, not new decoded values.
They are appended only after discovery, frozen structural evidence, oracle
evaluation, ranking and readiness decisions finish. They remain available with
the oracle disabled, while the existing semantic status remains unresolved.
The provider receives only a field key, never a filename, byte buffer, fixture
identity or expected value. It does not establish applicability for arbitrary
F4 hits. Existing `typed_width` values all remain `None` (JSON null).

| Reviewed hypothesis | Code record interval (half-open, hex) | CTxtAttrChar member | CTxtAttrStyle member | MaudeTxt write RVA | Evidence |
| --- | --- | --- | --- | --- | --- |
| height | [0C,14) | +10 | +18 | 4D7F1 | confirmed_archive_double |
| width ratio | [14,1C) | +18 | +20 | 4D7FE | confirmed_archive_double |
| slant | [1C,24) | +20 | +28 | 4D80B | confirmed_archive_double |
| character spacing | [40,48) | +30 | +38 | 4D84C | confirmed_archive_double |
| rotation | [48,50) | +38 | +40 | 4D859 | confirmed_archive_double |

The serializer is MaudeTxt.dll!CTxtAttrChar::Serialize RVA 4D790, also reached
for the embedded Char portion of CTxtAttrStyle::Serialize RVA 4E480.
Ranges here are code-relative provenance, not new extraction offsets.
Archive width 8 is evidence-only; it does not set active `typed_width=8`.

The historical style analyzer's v1 replay contract is retained; existing tests
run it against the project's historical v1 replay. This batch does not migrate
that analyzer to the current v2 runtime or repair unrelated compatibility issues.
Existing text rendering is retained; JSON/build_report exposes the new evidence.

## RGB, maximum length and compression are not promoted

The production RGB candidate still exposes exactly three bytes at slot
[50,53), with `typed_width=None`. Vendor code establishes an enclosing
four-byte archive word at [50,54), Char+54 / Style+5C, write RVA 4D866:
`confirmed_archive_word32` describes that **container**, not the existing
three-byte candidate projection. This batch emits no RGB container metadata,
does not extract another byte and does not add an alpha channel or claim RGBA.

Maximum Length C+262 is deliberately excluded. Its archive evidence and strong
signed-input correlation do not resolve the UI-to-model callback edge.
Its values, names, semantic status and analyzer output remain unchanged.

C+214 (CTxtAttrPara+20, write 4E253) and C+286 (CTxtAttrLine+10, write 4DE72)
are two distinct compression-correlated scalar storage fields, whose raw/numeric
values were equal in the reviewed controlled fixtures. They are not described
here as the same field written twice. No production key, diagnostic extraction
or historical report is renamed or regenerated.

## Conditions and deferred claims

The exact internal C/P crosswalk is limited to five reviewed current-version
controlled fixtures: the A8 baseline and maximum-length +100/+60/+40/-60 mm
captures. Baseline C=244 and P=426, with code-derived 138+44=182, are provenance
facts, not absolute-offset parser rules. Separate style/spacing captures retain
their supported correlations; this metadata does not broaden exact scope.

The 92+112=204 record length is code-confirmed only under the reviewed
empty-extension condition: empty arrays/strings and absent optional zones.
The current recognizer does not validate that full condition. No stride,
extension validator, count logic, terminal checks, F4 constants or fail-closed
policy changes are made; `parser_safe=false` remains appropriate.

A terminal record can carry style state. It is not promoted to a C-string
terminator; neither terminal parsing nor state/ownership mapping changes here.

Phase 2F registration observation was blocked before DlgRapido loading by
`Debugger detected (E0030)`; no bypass occurred. SendAtribToCompo, GetValDist
and GetValPourcent targets remain unresolved. Character Spacing does not become
a fully confirmed UI-to-model path because its archive type is now documented.

## Evidence references

The metadata is transcribed from these reviewed artifacts, not loaded from
external paths at runtime or in tests:

- [Phase 3 promotion review](C:/TypeEdit_2009_reverse_engineering/reports/phase3_codec_promotion_review.md),
  sections 4–8 and 13.
- [Phase 3 matrix](C:/TypeEdit_2009_reverse_engineering/data/phase3_codec_promotion_matrix.csv):
  height, width, slant, character_spacing, rotation and RGB_container rows.
- [Phase 2C current-store operations](C:/TypeEdit_2009/_reverse_engineering/data/phase2c_current_store_ops.csv):
  CTxtAttrChar write rows listed above.
- [Phase 2C serializer layout](C:/TypeEdit_2009/_reverse_engineering/reports/phase2c_current_stream_layout.md):
  current field order/types and conditional extension composition.
- [Phase 2D exact prefix scope](C:/TypeEdit_2009/_reverse_engineering/reports/phase2d_182_prefix.md),
  [latest model/scale distinction](C:/TypeEdit_2009/_reverse_engineering/reports/phase2d_negative_path.md).
- [Spacing callback limitation](C:/TypeEdit_2009/_reverse_engineering/reports/phase2c_character_spacing_closure.md)
  and [Phase 2F outcome](C:/TypeEdit_2009/_reverse_engineering/reports/phase2f_summary.md).

Historical fixture investigation documents are preserved. Production raw bytes,
unknown bytes, legacy chains, candidate ordering, semantics and fixture files
are unchanged. Empty-extension recognition and typed parser promotion require
a separate future task.

## Initial validation (historical, before codec environment setup)

The 16 new focused tests pass in the working checkout. They cover additive report
keys and ordering, retained null typed widths, all five archive annotations,
raw/unknown bytes and parser identity, RGB's three-byte projection, unchanged F4
and 204 recognition, maximum-length/scalar reports, and renamed input captures.

Full-suite validation is **not green** in the available environment:

- The IDE returned Python 3.12.10; this project's declared Python >=3.14 environment
  was unavailable. Python 3.14 validation remains outstanding.
- The working checkout stops at three collection errors because the historical
  replay checks a frozen source SHA against LF bytes but that file has CRLF bytes.
- A disposable copy, with the frozen/current slot-source LF representation and
  isolated test dependencies available to CLI subprocesses, completed with
  **1186 passed, 10 failed** (1196 tests). Remaining failures are unchanged-source
  SHA checks for the chain parser / clipboard adapter and a dependent readiness
  assertion. Original sources, fixture baselines and expected hashes were not
  rewritten. Existing preservation checks also freeze the old analyzer source
  hashes; this intentional metadata addition does not preserve those source hashes.
- Ruff's default rules report 98 diagnostics already present in the two analyzer
  files, with no new diagnostics; the new test file is clean. The E4/E7/E9/F check
  passes for all three changed Python files. No unrelated lint cleanup was made.
- `git diff --check` passes. Production `src`, fixture files and maximum-length
  analyzers have no changes. Focused tests additionally verify capture hashes.

These results establish the narrow tested metadata invariants, not a claim that
the full supported-environment regression suite passes. Test infrastructure/hash
baseline reconciliation and Python 3.14 validation remain separate follow-up work.
## Validation after codec environment setup (2026-09-13)

The user configured `C:\work\develop\type3-clipboard-codec\.venv` with
Python 3.14.7. The outstanding supported-Python validation was rerun using that
interpreter directly; the IDE environment query still reported the unrelated
TypeEdit Python 3.12 SDK. No temporary dependency injection was needed this time.

| Check | Current result |
| --- | --- |
| Focused evidence-metadata tests, actual checkout | 16 passed |
| Full pytest, actual checkout | 3 collection errors in frozen-source SHA verification |
| Full pytest, disposable copy with the frozen/current slot-source files normalized to LF | 1186 passed, 10 failed in 79.57 seconds |
| Ruff, three changed Python files | 98 existing analyzer diagnostics; new test file has zero diagnostics |
| Ruff E4/E7/E9/F | Passed |
| git diff --check | Passed |

The full command used `PYTHONPATH=src` and the codec venv's Python with
`-B -m pytest -q -p no:cacheprovider --tb=short`. The disposable run changed
only two source files' line endings in the copy, not production checkout bytes,
expected hashes or fixture data. It is supplemental validation, not a passing
full-suite result for the actual checkout.

The ten failures reproduce the earlier source-preservation problems: seven
chain-parser SHA assertions (expected `9eed3128...`, actual `ec192403...`), two
clipboard-adapter SHA assertions (expected `8b3b5ebf...`, actual `f084c629...`),
and one dependent readiness assertion. Environment setup did not resolve these
separate baseline issues. The earlier analyzer-source-hash caveat also remains;
expected hashes were not updated to conceal authorized metadata changes.

Python 3.14 validation is now performed, so an unavailable interpreter is no
longer a blocker. Full regression approval remains blocked by the source/hash
baseline checks. No parser, fixture, existing test, analyzer implementation or
vendor evidence was edited during this verification continuation; only this
validation record was updated. The five archive annotations, null typed widths,
three-byte RGB projection and all deferred layout/ownership limits remain as
specified above.