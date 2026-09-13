# Five current/empty text-slot archive doubles

> **Historical status note**
>
> This document records the five-slot-field implementation batch. Its exclusion
> of pre-slot promotion applies to that batch only: three parent-gated pre-slot
> fields and two additive internal-role aliases were implemented later. The
> five-field history and semantic limits below are preserved. For current
> consumer-facing interpretation, use the
> [text-slot typed candidate consumer contract](text_slot_typed_candidate_contract.md).

The production candidate now adds five raw-preserving `f64le` fields after the
complete current/empty run has passed every structural check. This is an approved
additive typed-output change. Candidate selection and semantic ownership remain
unchanged. Scope is current AttrChar v5 / CPropertyExtend v5 / empty extension only.

## Contract review and implementation

`src/type3_clipboard_codec/parsers/text/text_slot_candidate.py` previously exposed
slot-code, RGB, and count candidate objects with unresolved `typed_width`. None
represented these five doubles, so changing those existing widths would have
changed the wrong fields. `ParsedObject.candidate_fields` already accepts nested
candidate dictionaries; the chain parser only attaches the returned slot run.
It needs no modification.

The style and spacing analyzers expose aggregate hypotheses, raw probes and
numeric profiles, with `archive_type_evidence=confirmed_archive_double`. Their
unresolved `typed_width` describes those diagnostic hypotheses, not a gated
runtime record. Those outputs, evidence and semantic statuses are unchanged.

Each accepted slot gains one small offset-keyed dictionary:

```python
"archive_double_candidates": {
    "0xc": {"raw_bytes": eight_bytes, "f64le": 0.01, "typed_width": 8},
    # Also "0x14", "0x1c", "0x40", "0x48".
}
```

Keys carry record-relative archive positions, without new UI ownership labels.
`typed_width=8` describes the serialized field width. Raw bytes remain exposed,
including unknown bits, negative zero and NaN payload/sign bits. Finite values
are Python floats decoded by `struct.unpack("<d", raw)` without rounding or unit
conversion. Nonfinite values use `"nan"`, `"inf"`, or `"-inf"`, following the
existing spacing diagnostic convention and allowing strict JSON output. Raw
bytes are authoritative for exact nonfinite bit patterns; these strings are
presentation values, not numeric validity constraints.

## Structural and semantic status

Offsets were frozen from serializer order before this task's corpus comparison.
Every listed field has runtime representation `f64le`, width 8. No additional
status enum was introduced into the production schema.

| Existing field label | Record offset | Typed archive representation | Semantic status retained | Existing controlled correlation |
|---|---:|---|---|---|
| Height | +0x0C | f64le, 8 bytes | strong_style_field_candidate; ownership unresolved | 10 / 20 mm -> 0.01 / 0.02 |
| Width ratio | +0x14 | f64le, 8 bytes | strong_style_field_candidate; ownership unresolved | 50 / 100 / 150% -> 0.5 / 1.0 / 1.5 |
| Slant | +0x1C | f64le, 8 bytes | strong_style_field_candidate; ownership unresolved | +/-15 degrees -> +/-0.2617993877991494 |
| Spacing-correlated field | +0x40 | f64le, 8 bytes | existing correlated candidate; UI-to-model callback unresolved | 50 / 100 / 150% -> 0.5 / 1.0 / 1.5 |
| Rotation | +0x48 | f64le, 8 bytes | strong_style_field_candidate; ownership unresolved | +/-15 degrees -> +/-0.2617993877991494 |

Control names are used only as test oracles after structural extraction. They
never select record ownership. Terminal records receive the same archive decode
and retain `terminal_candidate`, unresolved ownership and no matched chain;
their values are not promoted to visible-glyph properties. Existing candidate
`parser_safe=false` remains unchanged: archive decoding does not resolve semantic
ownership.

## Gate prerequisite and independence

Decoding occurs only in the final slot-output loop, after the first record gate,
all subsequent record gates, count agreement and terminal checks have succeeded.
The gate remains exact AttrChar=5, extension=5, full 204-byte window and the six
ordered zero guards at +132, +152, +188, +192, +196 and +200. A failed record
rejects the entire candidate before any double decode. Unsupported versions,
non-empty extension and truncation produce no typed output through this path.

Negative, zero, huge and nonfinite numbers do not affect acceptance. F4, root
selection, prefix families, counts, record alignment, terminal handling, chain
ordering and ownership are unchanged. RGB remains the existing three-byte
projection with unresolved typed width. Maximum Length, its formula/status,
compression scalars, and all their analyzers are unchanged.

## Compatibility and source provenance

Before implementation, actual parser outputs for all 116 valid hex captures and
exact hashes of all 204 fixture-tree files were saved outside the repository.
After implementation, removing only each slot's new `archive_double_candidates`
key reproduces every saved object and parser/chain choice exactly. Raw records,
all previous candidate fields and candidate presence are unchanged. A test-only
projection in `tests/text_slot_typed_output.py` also checks the frozen historical
candidate output without rewriting any runtime goldens. Historical equality is
therefore equality under this explicitly approved additive-output projection,
not a claim that the new public dictionaries are byte-for-byte identical.

Only one production file changed, committed locally as
`67679348ad7775cab02705cea118b1b2e624a08e` (no push). Its committed blob was hashed
through `tests/source_integrity.py`, using the approved CRLF-to-LF canonical
policy. The canonical SHA is
`c72d2b7d232d22201f84a25268ced8da78beb45e233e6f41e33762517c2fc3f7`.
Only its `current` baseline entry changed out of 49 entries. Previous original
and production-gate baselines and legacy raw provenance are retained. The new
reason explicitly records the approved additive five-field f64le archive output
after the current/empty gate, with semantic ownership unchanged. No baseline
was derived from an arbitrary dirty working tree.

## Validation

| Check | Result |
|---|---|
| Accepted records decoded | 700; 616 visible, 84 terminal |
| Binary64 fields decoded | 3,500; zero decode failures |
| Actual pre/post capture comparison | 116 equal after only the approved additive projection |
| New typed-field tests | 26 passed |
| Existing current/empty production gate | 29 passed, including production/shadow agreement |
| Applicability / empty extension / archive metadata | 36 / 26 / 16 passed |
| Historical replay assertion | 1 passed; 104 fixtures, runtime_outputs_equal=true, canonical_source_equal=true, readiness=ready_for_review |
| Combined focused run | 134 passed |
| Candidate v2 migration plus new typed tests | 130 passed |
| Full actual checkout | 1383 passed in 89.88s; baseline 1357 |
| Ruff E4/E7/E9/F on changed/new Python | Passed |
| Ruff full configured rules | Zero new diagnostics; 13 pre-existing diagnostics (11 C408, 2 I001) |
| Fixture SHA preservation | All 204 files unchanged, no additions/removals |
| Production scope | Only text_slot_candidate.py; chain parser and tools unchanged |
| Git whitespace check | Passed |

Synthetic tests cover exact finite values and raw bits at all five offsets,
negative zero, large magnitudes, infinities, signed/payload/signaling NaNs,
unsupported versions, every non-empty guard, truncation, all run positions,
terminal distinction, offset/input-order/name independence, and strict JSON.
Monkeypatched decode failures prove rejected runs never reach typed extraction.

The corpus still contains zero real non-empty extensions. Legacy and non-empty
parsing remain unsupported; UI callback ownership remains unresolved. This task
ends with five runtime archive doubles implemented and semantic status unchanged.
It does not authorize RGB promotion, other scalar promotion or a general typed
style parser.
