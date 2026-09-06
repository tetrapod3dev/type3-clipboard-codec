"""Color Phase 1D: bounded CParagraphe slot-schema validation, not a parser."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_color_record as prior  # noqa: E402

TEXT_DIR = prior.TEXT_DIR
compact = prior.compact
FIXTURES = (
    "default_text.txt", "text_ascii_lowercase.txt", "text_ascii_uppercase.txt",
    "text_digits.txt", "text_alphanumeric.txt", "text_spaces.txt", "text_special_characters.txt",
    "text_color_army_green.txt", "text_color_navy_blue.txt", "text_height_10mm.txt",
    "text_height_30mm.txt", "text_font_arial.txt", "text_font_arial_bold.txt",
    "text_group_same_color_two_objects.txt", "text_group_mixed_color_two_objects.txt",
    "text_two_objects_same_color_not_grouped.txt", "text_two_objects_mixed_color_not_grouped.txt",
    "text_three_objects_grouped_order_abc.txt",
    "text_three_objects_grouped_order_abc_content_variation.txt",
    "text_three_objects_not_grouped.txt", "text_multiline_basic.txt",
)
START, STRIDE, MAX_RECORDS = 47, 204, 24
POLICY = {"scope": "text_slot_record_schema_analysis_only", "parser_behavior": "not_modified",
          "model_behavior": "not_modified", "color_ownership_assignment": "not_performed",
          "slot_parser_implementation": "not_performed", "oracle_isolation": True}
LIMITS = {"max_fixtures": 24, "max_nodes": 32, "max_paragraphs_per_fixture": 2,
          "max_payload_bytes": 1048576, "max_hex_bytes": 8388608,
          "max_records_examined": MAX_RECORDS, "max_record_rows": 4,
          "max_fixture_details": 3, "max_signature_examples": 2,
          "detail_scope": "first paragraph of each eligible fixture only",
          "default_record_rows": 0, "json_bytes": 100000, "text_bytes": 50000,
          "boundary_shifts": [-8, 8], "boundary_window": [-8, 7],
          "code_window": [0x30, 0x50], "homogeneity_windows": [[0x30, 0x50], [0x70, 0xA0]],
          "alternate_prefix_window": [0x50, 0x90],
          "nearby_stride_range": [196, 212], "whole_record_comparison": False}
PREFIX = b"\x05\0\0\0"  # prior slot-header lead; not a decoded record type


def classes(values):
    counts = Counter(values)
    return {"class_count": len(counts), "modal_count": max(counts.values(), default=0),
            "count": len(values)}


def boundary_score(data, start, stride=STRIDE):
    """Repetition only: no code, text, palette, expected count, or header selection."""
    count = max(0, (len(data)-start)//stride)
    if count > MAX_RECORDS:
        raise ValueError("record examination budget exceeded")
    windows = [data[start+i*stride-8:start+i*stride+8] for i in range(count)]
    equal = sum(a == b for a, b in zip(windows, windows[1:]))
    return {"count": count, "equal_adjacent_boundaries": equal,
            "adjacent_comparisons": max(0, count-1), "signature_classes": len(set(windows))}


def prefix_run(data, pos, stride=STRIDE):
    """Stop on prefix loss/bounds, never on zero or printable-character tests."""
    count = 0
    while count < MAX_RECORDS and pos+count*stride+8 <= len(data):
        if data[pos+count*stride:pos+count*stride+4] != PREFIX:
            return count, "prefix_mismatch"
        count += 1
    if count == MAX_RECORDS and data[pos+count*stride:pos+count*stride+4] == PREFIX:
        raise ValueError("prefix run budget exceeded")
    return count, "payload_end" if pos+count*stride+8 > len(data) else "prefix_mismatch"


def locate_lead(data, code_offsets):
    # First repeated provisional chunk only. No scan of full payload or ASCII ranking.
    candidates = []
    for off in code_offsets:
        pos = START+STRIDE+off-4
        count, stop = prefix_run(data, pos)
        if count >= 2:
            candidates.append({"code_offset": off, "prefix_start": pos, "count": count, "stop": stop})
    maximum = max((c["count"] for c in candidates), default=0)
    winners = [c for c in candidates if c["count"] == maximum]
    return winners[0] if len(winners) == 1 else None, len(candidates)


def masked_signature(data, pos, code_offset):
    # No coordinate fields are silently masked: first-slot prefix differences survive.
    return bytes(data[pos+i] for lo, hi in ((0x30, 0x50), (0x70, 0xA0))
                 for i in range(lo, hi+1)
                 if not code_offset <= i < code_offset+4 and not 0x8B <= i <= 0x8D)


def analyze_payload(data, details=False):
    """All schema choices are functions of payload bytes alone."""
    if len(data) > LIMITS["max_payload_bytes"]:
        raise ValueError("payload budget exceeded")
    shifts = [boundary_score(data, START+s) for s in range(-8, 9)]
    # Integer score avoids ratios favoring a shorter sampled grid.
    maximum = max(s["equal_adjacent_boundaries"] for s in shifts)
    winners = [START+i-8 for i, s in enumerate(shifts) if s["equal_adjacent_boundaries"] == maximum]
    lead, candidate_count = locate_lead(data, range(0x30, 0x51))
    alternate, alternate_candidates = (None, 0) if lead else locate_lead(data, range(0x54, 0x95))
    active = lead or alternate
    result = {"candidate_start": START, "candidate_stride": STRIDE,
        "provisional_full_chunk_count": shifts[8]["count"],
        "H1_boundary_score": shifts[8],
        "H2_shift_scores": [s["equal_adjacent_boundaries"] for s in shifts],
        "best_repetition_start_candidates": winners,
        "boundary_confirmed": False, "candidate_code_positions_count": candidate_count,
        "aligned_record_count": lead["count"] if lead else None,
        "status": "provisional_single_line_grid" if lead else "alternate_layout_or_unresolved",
        "alternate_prefix_candidates_count": alternate_candidates,
        "record_rows": [], "signature_examples": []}
    if not active:
        result.update({"stop_reason": "no_unique_repeated_prefix_in_bounded_windows",
                       "boundary_signature_consistency": None, "pre_boundary_consistency": None,
                       "post_boundary_consistency": None, "slot_codes": None,
                       "homogeneity": {"status": "unresolved"}, "terminal": None})
        return result
    count, prefix = active["count"], active["prefix_start"]
    positions = [prefix+i*STRIDE for i in range(count)]
    codes = [int.from_bytes(data[p+4:p+8], "little") for p in positions]
    preceding_count = int.from_bytes(data[prefix-4:prefix], "little")
    relative = active["code_offset"]
    grid = [START+(i+1)*STRIDE for i in range(count)]
    if lead and any(p+STRIDE > len(data) for p in grid):
        result.update({"aligned_record_count": None, "status": "alternate_layout_or_unresolved",
            "stop_reason": "prefix_run_exceeds_complete_provisional_records",
            "boundary_signature_consistency": None, "pre_boundary_consistency": None,
            "post_boundary_consistency": None, "slot_codes": None,
            "homogeneity": {"status": "unresolved"}, "terminal": None})
        return result
    pre = [data[p-8:p] for p in grid]
    post = [data[p:p+8] for p in grid]
    result.update({"stop_reason": active["stop"], "first_repeated_ordinal": 1 if lead else None,
        "last_repeated_ordinal": count if lead else None,
        "boundary_signature_consistency": classes([a+b for a, b in zip(pre, post)]),
        "all_enumerated_prefixes_on_stride": True,
        "complete_provisional_extent_fits": all(p+STRIDE <= len(data) for p in grid),
        "pre_boundary_consistency": classes(pre), "post_boundary_consistency": classes(post),
        "prefix_evidence": {"payload_relative_start": prefix, "value_hex": PREFIX.hex(),
            "record_relative_offset": relative-4 if lead else None,
            "preceding_u32le": preceding_count, "equals_enumerated_count": preceding_count == count,
            "prefix_count": count, "enumeration_ignores_code_value": True,
            "nearby_stride_prefix_counts": [prefix_run(data, prefix, stride)[0] for stride in range(196, 213)],
            "next_prefix_hex": data[prefix+count*STRIDE:prefix+count*STRIDE+4].hex()},
        "slot_codes": {"candidate_record_relative_offset": relative if lead else None,
            "alternate_grid_relative_offset": relative if not lead else None,
            "u32le_values": codes, "u8_u16le_u32le_equal": all(v <= 255 for v in codes),
            "typed_code_width": None, "zero_ordinals": [i+1 for i, v in enumerate(codes) if v == 0],
            "nonzero_count": sum(v != 0 for v in codes),
            "adjacent_equal_count": sum(a == b for a, b in zip(codes, codes[1:])),
            "selection_basis": "unique longest repeated prior prefix in bounded lead window; no code-value scoring"},
        "alternate_layout": None if lead else {"prefix_payload_start": prefix,
            "shift_from_single_line_prefix_lead": prefix-(START+STRIDE+59),
            "slot_count": count, "code_13_ordinals": [i+1 for i, v in enumerate(codes) if v == 13],
            "single_line_schema_applied": False}})
    if lead:
        views = {}
        for label, width in (("u8", 1), ("u16le", 2), ("u32le", 4)):
            varying, varying_final_zero = [], []
            for offset in range(0x30, 0x51-width+1):
                values = [int.from_bytes(data[p+offset:p+offset+width], "little") for p in grid]
                if len(set(values)) > 1:
                    varying.append(offset)
                    if values[-1] == 0:
                        varying_final_zero.append(offset)
            views[label] = {"varying_offsets": varying, "varying_final_zero_offsets": varying_final_zero}
        result["slot_codes"]["bounded_window_view_summary"] = views
        signatures = [masked_signature(data, p, relative) for p in grid]
        local = [data[p+0x70:p+0x8B]+data[p+0x8E:p+0xA1] for p in grid]
        color_bytes = [data[p+0x8B:p+0x8E].hex() for p in grid]
        result["homogeneity"] = {"status": "homogeneous_slot_record_candidate" if len(set(signatures)) == 1 else "multiple_slot_subtypes",
            "masked_signature_classes": len(set(signatures)), "modal_class_size": Counter(signatures).most_common(1)[0][1],
            "color_local_masked_classes": len(set(local)),
            "first_differs_from_second": signatures[0] != signatures[1],
            "first_vs_second_changed_offsets": [i for lo, hi in ((0x30, 0x50), (0x70, 0xA0))
                for i in range(lo, hi+1) if not relative <= i < relative+4 and not 0x8B <= i <= 0x8D
                and data[grid[0]+i] != data[grid[1]+i]],
            "terminal_matches_previous": signatures[-1] == signatures[-2],
            "interpretation": "bounded subtypes or prefix crossing provisional boundary; not proven semantic subtypes"}
        result["color"] = {"observed_color_byte_start": 0x8B, "observed_changed_width": 3,
            "typed_color_field_width": None, "inside_all_aligned_records": all(p+STRIDE <= len(data) for p in grid),
            "relative_to_prefix_lead": 0x8B-(relative-4), "byte_value_counts": dict(Counter(color_bytes)),
            "terminal_equals_previous": color_bytes[-1] == color_bytes[-2],
            "terminal_bytes": color_bytes[-1], "typed_boundary_evidence": "none"}
        if details:
            # Select row indices BEFORE constructing diagnostic records or examples.
            indices = sorted({0, 1, max(0, count-2), count-1})[:LIMITS["max_record_rows"]]
            for i in indices:
                p = grid[i]
                raw = data[p+relative:p+relative+4]
                result["record_rows"].append({"ordinal": i+1, "payload_relative_start": p,
                    "before_boundary_hex": pre[i].hex(), "after_boundary_hex": post[i].hex(),
                    "code_window_hex": data[p+0x30:p+0x51].hex(), "candidate_code_raw": raw.hex(),
                    "u8": raw[0], "u16le": int.from_bytes(raw[:2], "little"), "u32le": codes[i],
                    "is_zero": codes[i] == 0, "equals_previous_code": codes[i] == codes[i-1] if i else None,
                    "color_bytes": color_bytes[i]})
            for signature in dict.fromkeys(signatures):
                if len(result["signature_examples"]) == LIMITS["max_signature_examples"]:
                    break
                result["signature_examples"].append(signature.hex())
    else:
        result["homogeneity"] = {"status": "unresolved", "reason": "single_line_masks_not_applied_to_alternate_layout"}
        result["color"] = {"observed_color_byte_start": 0x8B, "observed_changed_width": 3,
                           "typed_color_field_width": None, "inside_all_aligned_records": None,
                           "status": "single_line_position_not_transferred"}
    result["terminal"] = {"interpretation": "zero_code_terminal_candidate" if codes[-1] == 0 else "unresolved",
        "last_code_zero": codes[-1] == 0, "only_last_zero": codes[-1] == 0 and 0 not in codes[:-1],
        "prefix_present_at_final": True, "next_prefix_absent": active["stop"] == "prefix_mismatch",
        "count_equals_nonzero_plus_one": count == sum(v != 0 for v in codes)+1,
        "local_signature_matches_previous": result["homogeneity"].get("terminal_matches_previous"),
        "color_matches_previous": result["color"].get("terminal_equals_previous"),
        "T1": "supported_candidate_not_c_string_proof" if codes[-1] == 0 else "unresolved",
        "T2": "padding_or_default_slot_not_excluded", "T3": "semantic_role_unresolved"}
    return result


def extract_structure(blob, details=False):
    if len(blob) > LIMITS["max_payload_bytes"]:
        raise ValueError("payload budget exceeded")
    parser = prior.Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    nodes = parser._extract_nodes(blob[origin:])
    if len(nodes) > LIMITS["max_nodes"]:
        raise ValueError("node budget exceeded")
    paragraphs = []
    for ni, node in enumerate(nodes):
        if node.header.class_name != "CParagraphe":
            continue
        if len(paragraphs) == LIMITS["max_paragraphs_per_fixture"]:
            raise ValueError("paragraph budget exceeded")
        desc = origin+node.start_offset
        paragraphs.append({"provenance": {"node_ordinal": ni, "runtime_descriptor_start": desc,
            "runtime_class_name": "CParagraphe", "runtime_schema": int.from_bytes(blob[desc+2:desc+4], "little"),
            "class_payload_start": origin+node.payload_offset, "payload_length": len(node.payload),
            "MFC_effect": "provenance_only", "absolute_offsets": "diagnostic_only"},
            **analyze_payload(node.payload, details and not paragraphs)})
    return {"paragraphs": paragraphs, "total_paragraph_slot_count": sum(p.get("prefix_evidence", {}).get("prefix_count", 0) for p in paragraphs) or None,
            "total_aligned_repeated_record_count": sum(p["aligned_record_count"] or 0 for p in paragraphs) if paragraphs and all(p["aligned_record_count"] is not None for p in paragraphs) else None,
            "multiple_run_breaks": "not_exhaustively_enumerated_bounded_leading_run_only",
            "total_count_scope": "enumerated_leading_runs_only; additional_runs_unresolved",
            "chain_mapping": "not_performed"}


def structural_report(prepared):
    rows = [{"fixture": name, "structural": s} for name, s in prepared]
    paragraphs = [p for _, s in prepared for p in s["paragraphs"]]
    aligned = [p for p in paragraphs if p["aligned_record_count"] is not None]
    counts = Counter(p["homogeneity"]["status"] for p in paragraphs)
    code_positions = Counter(p["slot_codes"]["candidate_record_relative_offset"] for p in aligned)
    code_candidate = next(iter(code_positions)) if len(code_positions) == 1 else None
    enumerated = [p for p in paragraphs if p.get("prefix_evidence")]
    one_zero = bool(enumerated) and all(p["terminal"]["only_last_zero"] for p in enumerated)
    return {"fixture_results": rows,
        "boundary_hypothesis_summary": {
            "H1": {"start": START, "stride": STRIDE, "aligned_paragraphs": len(aligned),
                   "conflicting_or_alternate_paragraphs": len(paragraphs)-len(aligned), "status": "grid_candidate_not_confirmed"},
            "H2": {"starts": list(range(39, 56)), "score": "adjacent equal -8..+7 windows on full provisional grid",
                   "unique_47_winner_count": sum(p["best_repetition_start_candidates"] == [47] for p in paragraphs),
                   "status": "nearby_equal_or_better_repetition_does_not_delimit_records"},
            "H3": {"status": "viable", "evidence": "204 prefix periodicity and preceding count support run framing, not outer record extent"},
            "H4": {"status": "viable", "evidence": "header/tail plus first-slot context differences; periodic layout need not be uniform full records"},
            "prefix_count_agreement": sum(p.get("prefix_evidence", {}).get("equals_enumerated_count", False) for p in paragraphs),
            "unique_204_prefix_period_in_196_212_count": sum(
                all(n < p["prefix_evidence"]["prefix_count"] for i, n in enumerate(p["prefix_evidence"]["nearby_stride_prefix_counts"]) if i != 8)
                for p in enumerated),
            "stride_scope": "bounded nearby alternatives only; internal periodicity is not full record width"},
        "slot_code_candidate_summary": {"record_relative_candidate": code_candidate,
            "relative_to_repeated_prefix": 4, "candidate_prefix_relative_offset": code_candidate-4 if code_candidate is not None else None,
            "supported_paragraphs": len(aligned), "typed_code_width": None,
            "u8_u16le_u32le": "all tested narrowly; equal values do not prove storage width",
            "selection": "prior 05 prefix repetition only; printable ASCII is oracle-only"},
        "terminal_slot_summary": {"zero_terminal_paragraphs": sum(bool(p.get("terminal", {}).get("only_last_zero")) for p in paragraphs if p.get("terminal")),
            "interpretation": "zero_code_terminal_candidate" if one_zero else "unresolved", "not_proven": "C-string terminator versus padding/default slot"},
        "record_homogeneity_summary": {"statuses": dict(counts),
            "mask": "code candidate four-byte view and 8B..8D only; no coordinate exclusions",
            "scope": "30..50 plus 70..A0; no whole-record equality"},
        "multi_object_summary": {"fixture_totals": [{"fixture": n, "paragraph_slots": s["total_paragraph_slot_count"],
            "aligned_records": s["total_aligned_repeated_record_count"]} for n, s in prepared],
            "cohort_selection": "all fixtures reported without object-count or grouping inference",
            "multiple_runs": "only bounded leading prefix run tested; no chain/anchor/order mapping"},
        "multiline_summary": {"status": "single_line_schema_not_directly_applicable" if any(p["status"] != "provisional_single_line_grid" for p in paragraphs) else "no_alternate_in_selected_inputs",
            "alternate_layouts": [{"fixture": n, "alternate": p.get("alternate_layout")} for n, s in prepared for p in s["paragraphs"] if p["status"] != "provisional_single_line_grid"],
            "selection_basis": "structural incompatibility, not fixture name"},
        "answers": {"best_record_start": None, "best_record_stride": STRIDE if enumerated else None,
            "record_boundary_readiness": "periodicity_supported_outer_boundary_unresolved" if enumerated else "unresolved",
            "best_slot_code_candidate": code_candidate,
            "slot_code_readiness": "structural_candidate_relative_to_provisional_grid" if code_candidate is not None else "unresolved",
            "n_plus_one_relationship": "one_final_zero_beyond_nonzero_slots; visible_text_validation_oracle_only" if one_zero else "unresolved",
            "terminal_slot_interpretation": "zero_code_terminal_candidate" if one_zero else "unresolved",
            "record_schema_interpretation": "provisional_text_slot_periodic_layout; see bounded homogeneity classes" if enumerated else "unresolved",
            "color_relative_position_status": "0x8B_in_aligned_single_line_grid_only; typed_width_null",
            "multiline_compatibility": "alternate_layout_or_unresolved",
            "candidate_parser_model_readiness": "not_ready", "color_ownership_readiness": "not_ready"}}


def load_text_oracle(name):
    """Diagnostic ground truth from documented fixture controls; invoked only after freeze."""
    controls = dict.fromkeys(FIXTURES[:13], "abcdefg")
    controls.update({"text_ascii_uppercase.txt": "ABCDEFG", "text_digits.txt": "1234567890",
        "text_alphanumeric.txt": "A1B2C3d4", "text_spaces.txt": "ab cd ef",
        "text_special_characters.txt": "+-*/#@&()", "text_multiline_basic.txt": "abcd\nefgh"})
    if name in controls:
        return {"texts": [controls[name]], "source": "documented content/style controls in docs/text_object_reverse_engineering.md"}
    path = prior.INTENT_DIR / (Path(name).stem+".md")
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as stream:
        header = stream.read(12000).split("## Order / ownership metadata", 1)[0].split("## Parser observation", 1)[0]
    match = re.search(r"^- text content:\s*(.+)$", header, re.M)
    return {"texts": sorted(set(match.group(1).strip().split("|"))),
            "source": "capture text content only; unordered alternatives, no labels"} if match else None


def oracle_phase(frozen, enabled):
    if not enabled:
        return {"enabled": False, "fixtures": []}
    rows = []
    for row in json.loads(frozen)["fixture_results"]:
        oracle = load_text_oracle(row["fixture"])
        diagnostics = []
        for p in row["structural"]["paragraphs"]:
            codes = (p.get("slot_codes") or {}).get("u32le_values", [])
            text = "".join("\n" if v == 13 else chr(v) for v in codes[:-1]) if codes and codes[-1] == 0 and all(v == 13 or 32 <= v <= 126 for v in codes[:-1]) else None
            matches = [t for t in oracle["texts"] if t == text] if oracle and text is not None else []
            diagnostics.append({"candidate_text": text, "ordinal_code_match": bool(matches) if oracle else None,
                "n_plus_one": len(codes) == len(matches[0])+1 if matches else None,
                "space_slot_count": codes.count(32), "linebreak_code_13_count": codes.count(13),
                "final_zero": bool(codes) and codes[-1] == 0})
        rows.append({"fixture": row["fixture"], "oracle": oracle, "diagnostics": diagnostics})
    return {"enabled": True, "structural_freeze_before_oracle": True,
            "boundary_or_code_updates": False, "fixtures": rows}


def build_report(fixtures=None, oracle_enabled=True, details=False):
    names = list(dict.fromkeys(FIXTURES if fixtures is None else fixtures))
    if len(names) > LIMITS["max_fixtures"]:
        raise ValueError("fixture budget exceeded")
    prepared = []
    for i, name in enumerate(names):
        path = (TEXT_DIR / name).resolve()
        if not path.is_relative_to(TEXT_DIR.resolve()) or not path.is_file():
            raise ValueError("fixture must exist inside text samples")
        if path.stat().st_size > LIMITS["max_hex_bytes"]:
            raise ValueError("hex input budget exceeded")
        blob = prior.hex_text_to_bytes(path.read_text(encoding="utf-8-sig"))
        prepared.append((name, extract_structure(blob, details and i < LIMITS["max_fixture_details"])))
    frozen = compact(structural_report(prepared))
    oracle = oracle_phase(frozen, oracle_enabled)
    return {"mode": "text_slot_record_schema_phase1d", "policy": POLICY.copy(),
            "limits": {**LIMITS, "details_enabled": details}, "warnings": [],
            **json.loads(frozen), "oracle_summary": oracle}


def render_text(report, markdown=False):
    lines = [("# " if markdown else "")+"Text Slot Record Schema - Phase 1D"]
    for row in report["fixture_results"]:
        for p in row["structural"]["paragraphs"]:
            lines.append(compact({"fixture": row["fixture"], "slots": p.get("prefix_evidence", {}).get("prefix_count"),
                "aligned": p["aligned_record_count"], "status": p["status"],
                "best_start_candidates": p["best_repetition_start_candidates"], "stop": p["stop_reason"],
                "code_offset": (p.get("slot_codes") or {}).get("candidate_record_relative_offset"),
                "homogeneity": p["homogeneity"], "record_rows": p["record_rows"]}))
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
