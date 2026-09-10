# Maximum-length boundary findings (2026-09-11)

Fixed-window mode: `tools/analyze_text_maximum_length.py --boundary [--json] [--no-oracle]`.
Default historical output is unchanged. The five default inputs are the existing
baseline plus the four boundary captures. Custom `--fixtures` accepts five paths;
renaming/reordering does not change structural output. Hashes identify frozen
observations; intent association occurs only afterward.

[Machine report](text_maximum_length_boundary_results.json) contains every
round-trip-safe prediction, absolute/relative residual, ULP distance and raw
coordinate provenance. [Inventory/history](text_spacing_maxlength_fixture_plan.md)
remains intact.

## Structural result and fixed raw inventory

All five inputs independently align: one CParagraphe, first prefix 310, nine
slots; runtime candidate present, source CParagraphe_slot_prefix_family_v2,
prefix_family=F4, plus08_value=0. Required +0x24..+0x2B and +0x38..+0x3F
remain unchanged in all nine slots. No runtime/F4 contradiction.
Only the three frozen candidate windows and established CZone X bounds are
numerically inspected; no new field nomination or full-payload differential.

| Fixture | [262,270) raw | f64le meters | [214,222) raw | [286,294) raw | Scalar at both |
| --- | --- | ---: | --- | --- | ---: |
| text_maxlength_a8_74p50mm.txt | df4f8d976e12b33f | 0.0745 | 304623b297eeef3f | 304623b297eeef3f | 0.9978750685933786 |
| text_maxlength_a8_74p58mm.txt | b988efc4ac17b33f | 0.07458 | ba27492361f7ef3f | ba27492361f7ef3f | 0.9989476861166999 |
| text_maxlength_a8_74p60mm.txt | f0164850fc18b33f | 0.0746 | 000000000000f03f | 000000000000f03f | 1.0 |
| text_maxlength_a8_74p66mm.txt | 94c151f2ea1cb33f | 0.07466 | 000000000000f03f | 000000000000f03f | 1.0 |

duplicate_scalar_storage_observed continues: byte and numeric identity in every
boundary capture, extending the five broad controls. Storage ownership remains
unresolved. Requested-setting residuals are all zero/0 ULP against the decimal UI
meter labels converted to binary64. Separately, binary64 74.66/1000 yields
0.07465999999999999, one ULP below the observed 0.07466 (absolute residual
1.3877787807814457e-17 m); the report preserves both conversion paths.
Object-setting evidence is strong_object_setting_candidate_extended_to_boundary_controls;
typed widths remain null/unresolved.

## Exact serialized CZone X bounds

The established parser framing gives xmin raw absolute [81,89) and xmax
[105,113) in each capture. Raw hex, binary64 repr/hex and exact rational coordinate
differences are in the machine report. The method is (xmax_m - xmin_m) * 1000;
no denominator is inferred from UI or boundary fixture geometry.

| L mm | xmin m | xmax m | extent m | extent mm |
| ---: | ---: | ---: | ---: | ---: |
| 74.50 | 0.031165000000000005 | 0.10566500000000001 | 0.07450000000000001 | 74.50000000000001 |
| 74.58 | 0.031125000000000007 | 0.105705 | 0.07457999999999998 | 74.57999999999998 |
| 74.60 | 0.031115000000000004 | 0.105715 | 0.0746 | 74.6 |
| 74.66 | 0.031085 | 0.105745 | 0.07466 | 74.66000000000001 |

Pattern A: bbox tracks requested object length within 0–1 ULP even above N.
It does not clamp to N in these captures. Serialized bbox is not glyph width.

## Four explicit hypotheses

N remains baseline-derived 74.58390177353341 mm; provisional 1.001N is
74.65848567530693 mm. H1=L/N, H2=L/N-0.001, H3=min(1,L/N),
H4=min(1,L/N-0.001). No epsilon search or free-constant fitting.
Relative residual denominator is abs(observed S). The prior numeric closeout's
four-ULP comparison threshold is retained, without changing predictions.

| L | H1 absolute residual | H2 absolute residual | H3 absolute residual | H4 absolute residual |
| ---: | ---: | ---: | ---: | ---: |
| 74.50 | 0.0010000000000000009 | 0.0 | 0.0010000000000000009 | 0.0 |
| 74.58 | 0.001000000000000445 | 4.440892098500626e-16 | 0.001000000000000445 | 4.440892098500626e-16 |
| 74.60 | 0.0002158404975307615 | 0.0007841595024692394 | 0.0 | 0.0007841595024692394 |
| 74.66 | 0.0010203036400220356 | 2.0303640022145686e-05 | 0.0 | 0.0 |

74.50 H2 predicts 0.9978750685933786 exactly. 74.58 H2 predicts
0.9989476861167004 (4 ULP; relative residual 4.445570233776815e-16).
Compared with previous 60/40 results at 0–2 ULP, this supports
below_boundary_formula_continuity_supported; exact ULP count need not match.

At 74.60, N < L < 1.001N, yet S is exactly 1.0. H1 predicts
1.0002158404975308; H2/H4 predict 0.9992158404975308; H3 predicts 1.0.
Their ULP distances are respectively 972059184251, 7063080886239, 0,
7063080886239. This supports a transition at/near N over continuation to the
provisional scalar crossover. It does not establish the exact threshold.

At 74.66, S is also exactly 1.0. H1 predicts 1.001020303640022;
H2 predicts 1.0000203036400221; H3/H4 predict 1.0. ULP distances are
4595039093008, 91439465638, 0, 0. This point alone cannot distinguish the
two transition models. For both above-natural points S=1, relative residuals
equal absolute residuals.

Neither simple clamp fits the entire boundary set: H3 contradicts the two
below-N controls; H4 contradicts 74.60. The proposed continuation through
74.60 then clamp at 74.66 was not observed.

boundary_model_status=natural_threshold_supported;
compression_formula_status=formula_breaks_near_boundary.
These labels describe scalar evidence only, not rendered behavior or a universal
piecewise algorithm. A change is bracketed by samples 74.58 and 74.60;
H-other and thresholds inside that interval remain possible.

## Ordered positive corpus

| L mm | Observed S | Scalar raw | CZone extent mm | vs N | vs 1.001N |
| ---: | ---: | --- | ---: | --- | --- |
| 40 | 0.5353087616608744 | 171013d73f21e13f | 40.00000000000001 | below | below |
| 60 | 0.8034631424913115 | 8c541156f8b5e93f | 60.0 | below | below |
| 74.50 | 0.9978750685933786 | 304623b297eeef3f | 74.50000000000001 | below | below |
| 74.58 | 0.9989476861166999 | ba27492361f7ef3f | 74.57999999999998 | below | below |
| 74.60 | 1.0 | 000000000000f03f | 74.6 | above | below |
| 74.66 | 1.0 | 000000000000f03f | 74.66000000000001 | above | above |
| 100 | 1.0 | 000000000000f03f | 100.0 | above | above |

Broad controls come from the frozen numeric closeout report, without rerunning
their differential analysis. Baseline is separate: L=0, S=0.9989999999999998,
raw 298716d9cef7ef3f, extent 74.58390177353341 mm,
default_natural_mode_scalar_candidate. Prior -60 sign control remains separate:
S=0.8034631424913115 with scalar raw identical to +60.

## Isolation, limitations and unchanged status

Raw windows/f64, CZone X bounds/extents and structural/runtime/F4 observations
freeze before intent, N/crossover labels or hypothesis evaluation.
Wrong boundary labels, wrong N/crossover metadata, renamed copies and reordered
inputs preserve structural data and its digest. --no-oracle preserves numeric
output. Unknown alignment or F4 changes suppress interpretation for that capture.

All four UI observations remain not_recorded. Below-N samples have a
below_boundary_scalar_state; above-N samples have an above_natural_scalar_state
with exact-one clamp_like_scalar_state. No definite glyph compression state
is inferred. Duplicate ownership, the 0.001 adjustment, internal N source,
rendering semantics, exact threshold and cross-font/text generalization remain
unresolved. No universal min(1,L/N-.001) formula is supported.

Runtime stays CParagraphe_slot_prefix_family_v2, accepted_candidate_only,
matched_chain=null; no runtime/parser/F4 edits. Existing spacing conclusions
remain separate and unchanged; no new per-slot style fields are inspected.
compression_scalar_readiness=strong_correlated_numeric_candidate;
semantic_formula_readiness=provisional_not_ready; parser_safe=false;
typed_width=null/unresolved; ownership_status=unresolved;
runtime_change_readiness=not_authorized_in_this_task.

## Verification

Targeted boundary/broad/numeric/inventory tests: 77 passed, including 24 new
boundary tests. Full `PYTHONPATH=src pytest -q`: 1180 passed (historical 1151 +
5 inventory tests + 24 boundary tests). Scoped Ruff passes; `git diff --check`
passes; `git diff -- src/type3_clipboard_codec` is empty. All four raw hashes
match inventory-time SHA-256 values; no fixture or intent edits in this step.
Serialized JSON/text is 33,643 UTF-8 bytes, no-oracle 13,674 bytes, below both
output caps. CLI platform newline conversion can add one byte on Windows.
