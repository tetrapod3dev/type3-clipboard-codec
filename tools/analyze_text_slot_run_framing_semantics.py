"""Phase 1F: count/context semantics of bounded slot runs; no parser implementation."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_slot_prefix_framing as framing  # noqa: E402

base = framing.prior.prior
TEXT_DIR, FIXTURES, compact = framing.TEXT_DIR, framing.FIXTURES, framing.compact
STRIDE = 204
# Frozen Phase 1E structural reference hypotheses, not palette/text expectations.
# 0..31 with code bytes 4..7 omitted; exact vectors avoid an untested Cartesian mask.
REFERENCE_SIGNATURES = tuple(bytes.fromhex(s) for s in (
    "05000000000000007b14ae47e17a843f000000000000f03f00000000",
    "0500000000000000b81e85eb51b89e3f000000000000f03f00000000",
    "05000000010000007b14ae47e17a843f000000000000f03f00000000",
))
SIGNATURE_OFFSETS = tuple(i for i in range(32) if not 4 <= i <= 7)
COUNT_VIEWS = tuple((off, width) for off in range(-16, 0) for width in (1, 2, 4) if off+width <= 0)
POLICY = {"scope": "text_slot_run_framing_semantics_analysis_only", "parser_behavior": "not_modified",
          "decoder_behavior": "not_modified", "model_behavior": "not_modified",
          "slot_parser_implementation": "not_performed", "color_ownership_assignment": "not_performed",
          "oracle_isolation": True}
LIMITS = {"max_fixtures": 24, "max_payload_bytes": 1048576, "max_hex_bytes": 8388608,
          "max_nodes": 32, "max_paragraphs": 2, "search_region": [128, 768],
          "max_slots": 24, "max_runs": 8, "count_window": [-16, -1],
          "max_fixture_details": 3, "max_slot_rows": 5, "max_count_view_rows": 8,
          "max_signature_examples": 3, "default_slot_rows": 0,
          "json_bytes": 100000, "text_bytes": 50000, "whole_payload_scan": False}


def family_rule():
    variable_indices = [i for i in range(28) if len({s[i] for s in REFERENCE_SIGNATURES}) > 1]
    return {"source": "frozen_Phase1E_masked_signature_hypotheses",
        "signature_window": [0, 31], "excluded_code_bytes": [4, 7], "color_bytes_outside_window": [80, 82],
        "invariant_core": {str(off): REFERENCE_SIGNATURES[0][i] for i, off in enumerate(SIGNATURE_OFFSETS) if i not in variable_indices},
        "variant_positions": [SIGNATURE_OFFSETS[i] for i in variable_indices],
        "allowed_variant_vectors": [bytes(s[i] for i in variable_indices).hex() for s in REFERENCE_SIGNATURES],
        "variant_policy": "exact observed vectors; no independent wildcard combinations",
        "parser_safe": False}


def family_match(signature):
    return signature in REFERENCE_SIGNATURES


def candidate_evidence(data, raw):
    """Independent A/B probes; raw runs were enumerated without accepting their count."""
    start, count = raw["start"], raw["count"]
    positions = [start+i*STRIDE for i in range(count)]
    complete = start >= 16 and positions[-1]+92 <= len(data)
    signatures = [framing.signature(data, p) for p in positions] if complete else []
    prefix_ok = bool(signatures) and all(family_match(s) for s in signatures)
    value = int.from_bytes(data[start-4:start], "little") if start >= 4 else None
    count_ok = value == count
    return {"prefix_start": start, "slot_count": count, "last_prefix_start": positions[-1],
        "A_prefix_periodicity_and_family": prefix_ok, "B_count_equals_total": count_ok,
        "count_value_minus4_u32le_view": value,
        "count_status": "unavailable_or_zero" if not value else "match" if count_ok else "mismatch",
        "prefix_signature_classes": len(set(signatures)),
        "unknown_signature_count": sum(not family_match(s) for s in signatures),
        "evidence_relation": "both_agree" if prefix_ok and count_ok else "prefix_only" if prefix_ok else "count_only" if count_ok else "neither"}


def agreement(candidates):
    prefix = [r for r in candidates if r["A_prefix_periodicity_and_family"]]
    counted = [r for r in candidates if r["B_count_equals_total"]]
    if len(prefix) > 1:
        return "ambiguous", None
    if len(prefix) == 1:
        p = prefix[0]
        if p["B_count_equals_total"]:
            return "both_agree", p
        return ("prefix_only" if p["count_status"] == "unavailable_or_zero" else "conflict"), None
    return ("count_only" if counted else "ambiguous"), None


def inspect_run(data, candidate, details=False):
    start, count = candidate["prefix_start"], candidate["slot_count"]
    positions = [start+i*STRIDE for i in range(count)]
    signatures = [framing.signature(data, p) for p in positions]
    codes = [int.from_bytes(data[p+4:p+8], "little") for p in positions]
    colors = [data[p+80:p+83].hex() for p in positions]
    terminal = codes[-1] == 0 and not framing.prefix_present(data, positions[-1]+STRIDE)
    total_bytes = count*STRIDE  # provisional full-period extent, not a proven typed byte length
    values = [int.from_bytes(data[start+off:start+off+width], "little") for off, width in COUNT_VIEWS]
    matches = [[v == count-1 if terminal else False, v == count, v == total_bytes, v == count*STRIDE] for v in values]
    value = candidate["count_value_minus4_u32le_view"]
    result = {"prefix_start": start, "total_slot_count": count,
        "nonterminal_count": count-1 if terminal else None, "terminal_index": count-1 if terminal else None,
        "terminal_status": "zero_code_terminal_candidate" if terminal else "unresolved",
        "code_13_count": codes.count(13), "zero_slot_count": codes.count(0),
        "count_window_hex": data[start-16:start].hex(),
        "count_probe": {"relative_offset": -4, "raw_four_bytes": data[start-4:start].hex(),
            "u8": data[start-4], "u16le": int.from_bytes(data[start-4:start-2], "little"), "u32le": value},
        "count_matches": {"C1_nonterminal": value == count-1 if terminal else None,
            "C2_total_including_terminal": value == count,
            "C3_provisional_byte_extent": value == total_bytes, "C4_slots_times_204": value == count*STRIDE},
        "observed_prefix_span_bytes": (count-1)*STRIDE, "provisional_run_byte_extent": total_bytes,
        "variant_ids": sorted({REFERENCE_SIGNATURES.index(s) for s in signatures}),
        "signature_classes": len(set(signatures)),
        "first_prefix_matches_later": signatures[0] == signatures[1],
        "terminal_signature_matches_previous": signatures[-1] == signatures[-2],
        "upstream_first_differs": data[start-16:start] != data[start+STRIDE-16:start+STRIDE],
        "slot_code_offset": 4, "typed_slot_code_width": None,
        "color_offset": 80, "typed_color_width": None,
        "color_context_classes": len({data[p+72:p+80]+data[p+83:p+92] for p in positions}),
        "color_context_example": (data[start+72:start+80]+data[start+83:start+92]).hex(),
        "terminal_color_matches_previous": colors[-1] == colors[-2],
        "stride_204_observed": all(framing.prefix_present(data, p) for p in positions),
        "slot_rows": [], "count_view_rows": []}
    if details:
        for i in sorted({0, 1, count//2, max(0, count-2), count-1})[:LIMITS["max_slot_rows"]]:
            result["slot_rows"].append({"index": i, "prefix_start": positions[i],
                "code_zero": codes[i] == 0, "variant_id": REFERENCE_SIGNATURES.index(signatures[i]), "color_bytes": colors[i]})
        # Select bounded representative views before constructing diagnostic rows.
        ranked = sorted(range(len(COUNT_VIEWS)), key=lambda i: (-sum(matches[i]), COUNT_VIEWS[i]))[:LIMITS["max_count_view_rows"]]
        for i in ranked:
            off, width = COUNT_VIEWS[i]
            result["count_view_rows"].append({"offset": off, "width": width,
                "raw": data[start+off:start+off+width].hex(), "value": values[i], "C1_C2_C3_C4": matches[i]})
    return result, {"codes": codes, "count_values": values, "count_matches": matches}


def analyze_payload(data, details=False):
    # Reuse only Phase 1E's small candidate enumerator, not its combined selection/report.
    inventory = framing.discover_runs(data)
    candidates = [candidate_evidence(data, r) for r in inventory["candidate_runs"]]
    status, selected = agreement(candidates)
    # Preserve prefix-only runs even when their count disagrees: no success-only filtering.
    prefix_candidates = [r for r in candidates if r["A_prefix_periodicity_and_family"]]
    runs, evidence = [], []
    for i, candidate in enumerate(prefix_candidates):
        row, raw = inspect_run(data, candidate, details and i == 0)
        runs.append(row)
        evidence.append(raw)
    return {"detector_status": status, "selected_prefix_start": selected["prefix_start"] if selected else None,
            "candidate_evidence": candidates, "prefix_family_runs": runs,
            "selection_scope": "bounded leading region; ambiguous or mismatched evidence is not accepted"}, evidence


def extract_structure(blob, details=False):
    if len(blob) > LIMITS["max_payload_bytes"]:
        raise ValueError("payload budget exceeded")
    parser = base.Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    nodes = parser._extract_nodes(blob[origin:])
    if len(nodes) > LIMITS["max_nodes"]:
        raise ValueError("node budget exceeded")
    paragraphs, evidence = [], []
    for ni, node in enumerate(nodes):
        if node.header.class_name != "CParagraphe":
            continue
        if len(paragraphs) == LIMITS["max_paragraphs"]:
            raise ValueError("paragraph budget exceeded")
        result, raw = analyze_payload(node.payload, details and not paragraphs)
        desc = origin+node.start_offset
        paragraphs.append({"provenance": {"node_ordinal": ni, "runtime_descriptor_start": desc,
            "class_name": "CParagraphe", "runtime_schema": int.from_bytes(blob[desc+2:desc+4], "little"),
            "class_payload_start": origin+node.payload_offset, "MFC_effect": "provenance_only",
            "absolute_offset_role": "diagnostic_only"}, **result})
        evidence.extend(raw)
    return {"paragraphs": paragraphs}, evidence


def structural_report(prepared, evidence):
    paragraphs = [p for _, s in prepared for p in s["paragraphs"]]
    runs = [r for p in paragraphs for r in p["prefix_family_runs"]]
    raw = [r for _, rows in evidence for r in rows]
    scores = [sum(r["count_matches"][i][1] for r in raw) for i in range(len(COUNT_VIEWS))]
    maximum = max(scores, default=0)
    winners = [i for i, score in enumerate(scores) if score == maximum and maximum > 0]
    offsets = {COUNT_VIEWS[i][0] for i in winners}
    best_offset = next(iter(offsets)) if len(offsets) == 1 else None
    views = [[off, width, *[sum(r["count_matches"][i][h] for r in raw) for h in range(4)]]
             for i, (off, width) in enumerate(COUNT_VIEWS)]
    field_bytes = [bytes.fromhex(r["count_probe"]["raw_four_bytes"]) for r in runs]
    variable = [i-4 for i in range(4) if len({b[i] for b in field_bytes}) > 1]
    statuses = Counter(p["detector_status"] for p in paragraphs)
    variants = []
    for vi, sig in enumerate(REFERENCE_SIGNATURES):
        members = [(name, r) for name, s in prepared for p in s["paragraphs"] for r in p["prefix_family_runs"] if vi in r["variant_ids"]]
        variants.append({"variant_id": vi, "fixture_count": len({name for name, _ in members}),
            "run_count": len(members), "representative_masked_bytes": sig.hex(),
            "variable_positions_across_family": family_rule()["variant_positions"],
            "stable_positions": [int(k) for k in family_rule()["invariant_core"]],
            "code_13_run_count": sum(r["code_13_count"] > 0 for _, r in members),
            "without_code_13_run_count": sum(r["code_13_count"] == 0 for _, r in members),
            "first_slot_difference_count": sum(not r["first_prefix_matches_later"] for _, r in members),
            "grouping_style_content_labels": "oracle_only_after_freeze"})
    agreed = bool(paragraphs) and statuses["both_agree"] == len(paragraphs)
    supported = bool(runs) and all(r["count_matches"]["C2_total_including_terminal"] for r in runs)
    terminal = bool(runs) and all(r["terminal_index"] is not None for r in runs)
    prerequisites = {"all_prefix_count_evidence_agrees": agreed,
        "count_supported_across_multiple_lengths": supported and len({r["total_slot_count"] for r in runs}) >= 3,
        "structural_terminal_present": terminal,
        "three_reference_variants_observed": sum(v["run_count"] > 0 for v in variants) == 3,
        "shifted_and_code13_layouts_exercised": len({r["prefix_start"] for r in runs}) > 1 and any(r["code_13_count"] for r in runs),
        "stride_and_local_context_stable": bool(runs) and all(r["stride_204_observed"] and r["signature_classes"] == 1 for r in runs),
        "normalized_color_context_shared": bool(runs) and len({r["color_context_example"] for r in runs}) == 1}
    ready = all(prerequisites.values()) and best_offset == -4
    return {"fixture_results": [{"fixture": name, "structural": s} for name, s in prepared],
        "count_field_summary": {"best_candidate_offset": best_offset,
            "best_candidate_views": [{"offset": COUNT_VIEWS[i][0], "width": COUNT_VIEWS[i][1],
                "decode_type": f"u{COUNT_VIEWS[i][1]*8}"+("le" if COUNT_VIEWS[i][1] > 1 else "")} for i in winners],
            "view_columns": ["offset", "width", "C1_matches", "C2_matches", "C3_matches", "C4_matches"],
            "bounded_view_scores": views, "selection_population": "all prefix-family runs including count conflicts",
            "observed_changed_byte_positions_in_minus4_view": variable,
            "observed_stable_byte_positions_in_minus4_view": [i-4 for i in range(4) if field_bytes and len({b[i] for b in field_bytes}) == 1],
            "candidate_typed_start": best_offset, "typed_start": None, "typed_width": None,
            "status": "ambiguous_width" if best_offset is not None else "unresolved",
            "independent_boundary_evidence": "none; low-byte counts with zero upper bytes do not prove integer width"},
        "count_hypothesis_summary": {"C1": sum(r["count_matches"]["C1_nonterminal"] is True for r in runs),
            "C2": sum(r["count_matches"]["C2_total_including_terminal"] for r in runs),
            "C3": sum(r["count_matches"]["C3_provisional_byte_extent"] for r in runs),
            "C4": sum(r["count_matches"]["C4_slots_times_204"] for r in runs),
            "tested_runs": len(runs), "C5": "correlated_header_semantics_not_formally_excluded",
            "extent_caveat": "C3 uses total_slots*204 and equals C4 here; not independent evidence of full record width",
            "interpretation": "total_slots_including_zero_terminal_supported" if supported and terminal else "unresolved"},
        "prefix_variant_summary": {"variants": variants, "semantic_explanation": "bounded fixture variants, not first/terminal subtypes; labels only in oracle"},
        "prefix_family_summary": {**family_rule(), "observed_variant_count": sum(v["run_count"] > 0 for v in variants),
            "P_family": "supported_with_exact_three_variant_vectors" if runs else "unresolved",
            "P_multiple": "multiple_semantic_families_not_excluded", "typed_field_offsets_promoted": False,
            "normalized_color_context_classes": len({r["color_context_example"] for r in runs}),
            "rfc_prerequisites": prerequisites},
        "detector_agreement_summary": {"fixture_paragraph_status_counts": dict(statuses),
            "candidate_evidence_relations": dict(Counter(c["evidence_relation"] for p in paragraphs for c in p["candidate_evidence"])),
            "candidate_disagreement_count": sum(c["A_prefix_periodicity_and_family"] != c["B_count_equals_total"] for p in paragraphs for c in p["candidate_evidence"]),
            "disagreement_count": sum(p["detector_status"] != "both_agree" for p in paragraphs),
            "policy": "more than one family-valid prefix remains ambiguous; wrong count never erases prefix evidence"},
        "multiline_summary": {"code_13_runs": [{"fixture": name, "prefix_start": r["prefix_start"],
            "count_offset": -4, "count_value": r["count_probe"]["u32le"], "total_slots": r["total_slot_count"],
            "nonterminal_slots": r["nonterminal_count"], "code_13_count": r["code_13_count"],
            "terminal_included": r["count_matches"]["C2_total_including_terminal"], "typed_count_width": None}
            for name, s in prepared for p in s["paragraphs"] for r in p["prefix_family_runs"] if r["code_13_count"]],
            "selection_basis": "structural code distribution, not filename or shift correction"},
        "multi_object_summary": {"all_fixture_compatibility": [{"fixture": name,
            "statuses": [p["detector_status"] for p in s["paragraphs"]],
            "slot_counts": [r["total_slot_count"] for p in s["paragraphs"] for r in p["prefix_family_runs"]]} for name, s in prepared],
            "scope": "paragraph-run consistency only; grouping labels withheld until oracle; no chain/object mapping"},
        "answers": {"best_count_field_candidate": best_offset, "count_field_type": "unresolved_u8_u16le_u32le" if best_offset is not None else "unresolved",
            "count_field_width": None, "count_semantics": "total_slots_including_zero_terminal_candidate" if supported and terminal else "unresolved",
            "terminal_included_in_count": supported and terminal, "prefix_variant_count": sum(v["run_count"] > 0 for v in variants),
            "prefix_family_status": "bounded_invariant_core_plus_exact_variants" if runs else "unresolved",
            "detector_disagreement_count": sum(p["detector_status"] != "both_agree" for p in paragraphs),
            "slot_code_normalization_status": "prefix_plus4_candidate_typed_width_null",
            "color_normalization_status": "prefix_plus50_to52_candidate_typed_width_null",
            "structural_framing_readiness": "bounded_count_and_family_candidate_supported" if ready else "unresolved",
            "candidate_parser_rfc_readiness": "ready" if ready else "not_ready",
            "rfc_scope": "bounded candidate RFC with abstention rules, not a production parser specification",
            "candidate_parser_model_readiness": "not_ready", "color_ownership_readiness": "not_ready"}}


def load_oracle(name):
    text = framing.load_text_oracle(name)
    capture = base.load_oracle(name)
    # Task-defined reporting cohorts; evaluated only after freeze, never used by detector.
    cohort = next((label for label, names in (
        ("ASCII_content", FIXTURES[:7]), ("color", FIXTURES[7:9]), ("height", FIXTURES[9:11]),
        ("font", FIXTURES[11:13]), ("multi_object", FIXTURES[13:20]), ("multiline_spacing", FIXTURES[20:])) if name in names), "unavailable")
    return {"texts": text["texts"] if text else None, "grouping": capture.get("grouping") if capture else None,
            "cohort": cohort, "source": "diagnostic capture grouping and task control labels only"}


def oracle_phase(frozen, enabled):
    if not enabled:
        return {"enabled": False, "fixtures": [], "variant_labels": []}
    snapshot = json.loads(frozen)
    structures = {r["fixture"]: r["structural"] for r in snapshot["structural"]["fixture_results"]}
    rows, labels = [], []
    for name, evidence in snapshot["evidence"]:
        oracle = load_oracle(name)
        diagnostics = []
        for raw in evidence:
            codes = raw["codes"]
            text = "".join("\n" if c == 13 else chr(c) for c in codes[:-1]) if codes and codes[-1] == 0 and all(c == 13 or 32 <= c <= 126 for c in codes[:-1]) else None
            diagnostics.append({"candidate_text": text, "ordinal_text_match": text in oracle["texts"] if text is not None and oracle["texts"] else None})
        rows.append({"fixture": name, "diagnostics": diagnostics})
        runs = [r for p in structures[name]["paragraphs"] for r in p["prefix_family_runs"]]
        for run, diagnostic in zip(runs, diagnostics):
            for vi in run["variant_ids"]:
                labels.append((vi, oracle["grouping"] or "unavailable", oracle["cohort"], diagnostic["candidate_text"]))
    return {"enabled": True, "structural_freeze_before_oracle": True, "selection_updates": False,
        "fixtures": rows, "variant_labels": [{"variant_id": vi,
            "grouping_distribution": dict(Counter(g for v, g, _, _ in labels if v == vi)),
            "cohort_distribution": dict(Counter(c for v, _, c, _ in labels if v == vi)),
            "diagnostic_text_distribution": dict(Counter(t or "unavailable" for v, _, _, t in labels if v == vi))} for vi in range(3)],
        "interpretation": "labels describe frozen classes; correlations do not establish semantic fields"}


def build_report(fixtures=None, oracle_enabled=True, details=False):
    names = list(dict.fromkeys(FIXTURES if fixtures is None else fixtures))
    if len(names) > LIMITS["max_fixtures"]:
        raise ValueError("fixture budget exceeded")
    prepared, evidence = [], []
    for i, name in enumerate(names):
        path = (TEXT_DIR / name).resolve()
        if not path.is_relative_to(TEXT_DIR.resolve()) or not path.is_file():
            raise ValueError("fixture must exist inside text samples")
        if path.stat().st_size > LIMITS["max_hex_bytes"]:
            raise ValueError("hex budget exceeded")
        blob = base.hex_text_to_bytes(path.read_text(encoding="utf-8-sig"))
        result, raw = extract_structure(blob, details and i < LIMITS["max_fixture_details"])
        prepared.append((name, result))
        evidence.append((name, raw))
    frozen = compact({"structural": structural_report(prepared, evidence), "evidence": evidence})
    oracle = oracle_phase(frozen, oracle_enabled)
    return {"mode": "text_slot_run_framing_semantics_phase1f", "policy": POLICY.copy(),
            "limits": {**LIMITS, "details_enabled": details}, "warnings": [],
            **json.loads(frozen)["structural"], "oracle_summary": oracle}


def render_text(report, markdown=False):
    lines = [("# " if markdown else "")+"Text Slot Run Framing Semantics - Phase 1F"]
    for f in report["fixture_results"]:
        for p in f["structural"]["paragraphs"]:
            lines.append(compact({"fixture": f["fixture"], "detector_status": p["detector_status"],
                "selected_prefix_start": p["selected_prefix_start"], "runs": [{"slots": r["total_slot_count"],
                    "count_value": r["count_probe"]["u32le"], "variants": r["variant_ids"],
                    "terminal": r["terminal_status"], "count_view_rows": r["count_view_rows"], "slot_rows": r["slot_rows"]} for r in p["prefix_family_runs"]]}))
    lines.append(compact(report["answers"]))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    formats = parser.add_mutually_exclusive_group()
    formats.add_argument("--json", action="store_true")
    formats.add_argument("--markdown", action="store_true")
    parser.add_argument("--fixture", action="append")
    parser.add_argument("--no-oracle", action="store_true")
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()
    report = build_report(args.fixture, not args.no_oracle, args.details)
    output = compact(report) if args.json else render_text(report, args.markdown)
    if len(output.replace("\n", "\r\n").encode("utf-8"))+2 >= LIMITS["json_bytes" if args.json else "text_bytes"]:
        parser.error("output budget exceeded")
    print(output)


if __name__ == "__main__":
    main()
