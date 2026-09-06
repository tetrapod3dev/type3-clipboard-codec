"""Phase 1E: bounded dynamic text-slot prefix framing; analysis only."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_slot_record_schema as prior  # noqa: E402

TEXT_DIR = prior.TEXT_DIR
compact = prior.compact
FIXTURES = prior.FIXTURES + (
    "text_spacing_fixed.txt", "text_spacing_proportional.txt", "text_spacing_print_proportional.txt",
)
PREFIX, STRIDE = b"\x05\0\0\0", 204
POLICY = {"scope": "text_slot_prefix_framing_analysis_only", "parser_behavior": "not_modified",
          "decoder_behavior": "not_modified", "model_behavior": "not_modified",
          "slot_parser_implementation": "not_performed", "color_ownership_assignment": "not_performed",
          "anchor_ownership_used": False, "oracle_isolation": True}
LIMITS = {"search_region_payload_relative": [128, 768], "search_end_exclusive": True,
          "max_payload_bytes": 1048576, "max_hex_bytes": 8388608, "max_fixtures": 24,
          "max_nodes": 32, "max_paragraphs": 2, "max_prefix_hits": 32, "max_runs": 8,
          "max_slots": 24, "max_fixture_details": 3, "max_slot_rows_per_fixture": 5,
          "max_signature_examples": 3, "signature_window": [0, 31],
          "signature_exclusions": [[4, 7]], "color_window": [72, 91],
          "color_exclusions": [[80, 82]], "nearby_origin_shifts": [-8, 8],
          "nearby_stride_range": [196, 212], "default_slot_rows": 0,
          "code_view_columns": ["offset", "width", "zero_count", "distinct_count"],
          "json_bytes": 100000, "text_bytes": 50000,
          "scope": "bounded leading-region discovery; no full-record or full-payload scan"}


def profile(values):
    counts = Counter(values)
    return {"count": len(values), "classes": len(counts), "modal_count": max(counts.values(), default=0)}


def signature(data, pos, shift=0):
    # Masks stay anchored to the nominated prefix even when the window moves.
    # Code/color bytes never become required invariants at a nearby origin.
    return bytes(data[pos+i] for i in range(shift, shift+32)
                 if not 4 <= i <= 7 and not 80 <= i <= 82)


def prefix_present(data, pos):
    return pos >= 0 and data[pos:pos+4] == PREFIX


def walk_prefix(data, pos, stride=STRIDE):
    count = 0
    while prefix_present(data, pos+count*stride):
        if count == LIMITS["max_slots"]:
            raise ValueError("slot traversal budget exceeded")
        count += 1
    return count


def discover_runs(data):
    """No grid origin, code values, colors, names, or text enter run selection."""
    if len(data) > LIMITS["max_payload_bytes"]:
        raise ValueError("payload budget exceeded")
    low, high = LIMITS["search_region_payload_relative"]
    hits, runs = 0, []
    for pos in range(low, min(high, max(low, len(data)-3))):
        if not prefix_present(data, pos):
            continue
        hits += 1
        if hits > LIMITS["max_prefix_hits"]:
            raise ValueError("prefix hit budget exceeded")
        # Skip periodic suffixes, even when the preceding prefix is outside search.
        if prefix_present(data, pos-STRIDE):
            continue
        count = walk_prefix(data, pos)
        if count < 2:
            continue
        if len(runs) == LIMITS["max_runs"]:
            raise ValueError("run candidate budget exceeded")
        positions = [pos+i*STRIDE for i in range(count)]
        complete = positions[-1]+92 <= len(data)
        signatures = [signature(data, p) for p in positions] if complete else []
        preceding = int.from_bytes(data[pos-4:pos], "little")
        upstream = [data[p-16:p] for p in positions]
        runs.append({"start": pos, "last_prefix_start": positions[-1], "count": count,
            "prefix_window_end_exclusive": positions[-1]+32, "complete_bounded_windows": complete,
            "signature_profile": profile(signatures), "preceding_u32le": preceding,
            "preceding_count_matches": preceding == count,
            "preceding_prefix_present": prefix_present(data, pos-STRIDE),
            "next_prefix_present": prefix_present(data, pos+count*STRIDE),
            "upstream_first_differs": upstream[0] != upstream[1],
            "prefix_first_differs": bool(signatures) and signatures[0] != signatures[1],
            # Permit a distinct first context so P3/P4 are not rejected by definition.
            "framing_eligible": complete and preceding == count and
                (len(set(signatures)) == 1 or count >= 3 and len(set(signatures[1:])) == 1)})
    eligible = [r for r in runs if r["framing_eligible"]]
    selected = eligible[0] if len(eligible) == 1 else None
    return {"prefix_hit_count_in_search": hits, "candidate_runs": runs, "selected": selected,
            "status": "unique_count_framed_periodic_candidate" if selected else
                      "ambiguous_count_framed_candidates" if eligible else "no_eligible_candidate"}


def rule_results(inventory):
    runs, selected = inventory["candidate_runs"], inventory["selected"]
    maximum = max((r["count"] for r in runs), default=0)
    proposed = {
        "R1": [r["start"] for r in runs if r["count"] == maximum],
        "R2": [r["start"] for r in runs if r["framing_eligible"]],
        "R3": [r["start"] for r in runs if r["prefix_first_differs"]],
        # Historical offset is diagnostic control only, never passed into discovery.
        "R4": [r["start"] for r in runs if r["start"] == 310],
    }
    result = {}
    for rule, starts in proposed.items():
        status = ("ambiguity" if len(starts) > 1 else "abstention" if not selected else
                  "support" if starts == [selected["start"]] else "conflict")
        result[rule] = {"status": status, "candidate_count": len(starts),
            "false_candidate_count": sum(not r["framing_eligible"] for r in runs if r["start"] in starts)}
    return result


def analyze_payload(data, details=False):
    inventory = discover_runs(data)
    selected = inventory["selected"]
    result = {k: v for k, v in inventory.items() if k != "selected"}
    result.update({"rules": rule_results(inventory), "slot_rows": [], "selected_run": None})
    if not selected:
        return result, None
    start, count = selected["start"], selected["count"]
    positions = [start+i*STRIDE for i in range(count)]
    codes = [int.from_bytes(data[p+4:p+8], "little") for p in positions]
    signatures = [signature(data, p) for p in positions]
    color_contexts = [data[p+72:p+80]+data[p+83:p+92] for p in positions]
    colors = [data[p+80:p+83].hex() for p in positions]
    zero_indices = [i for i, code in enumerate(codes) if code == 0]
    nearby = [profile([signature(data, p, shift) for p in positions])["classes"] for shift in range(-8, 9)]
    # Narrow overlapping code views are diagnostics, never discovery constraints.
    code_views = []
    for off in range(9):
        for width in (1, 2, 4):
            values = [int.from_bytes(data[p+off:p+off+width], "little") for p in positions]
            code_views.append([off, width, sum(v == 0 for v in values), len(set(values))])
    variable = [off for off in range(4, 8) if len({data[p+off] for p in positions}) > 1]
    # Compare to the prior grid only after discovery. Coincident zeros cannot prove alignment.
    historical_grid_delta = start-(47+204)
    prior_geometry_matches = historical_grid_delta == 0x3B
    prior_match_count = sum(data[p+80:p+83] == data[47+(i+1)*204+0x8B:47+(i+1)*204+0x8E]
                            for i, p in enumerate(positions)) if prior_geometry_matches else None
    last = count-1
    next_present = prefix_present(data, start+count*STRIDE)
    terminal = {"terminal_candidate_index": last if codes[-1] == 0 and not next_present else None,
        "zero_code": codes[-1] == 0, "next_prefix_present": next_present,
        "terminal_detection_status": "zero_plus_prefix_end_candidate" if codes[-1] == 0 and not next_present else "prefix_end_without_zero_confirmation",
        "T1": "support" if codes[-1] == 0 and not next_present else "conflict",
        "T2_zero_only_stop_indices": zero_indices,
        "T2_premature_stop_count": sum(i < last for i in zero_indices),
        "T3_prefix_end_index": last, "T3_does_not_prove_terminal_semantics": True,
        "terminal_signature_matches_previous": signatures[-1] == signatures[-2],
        "terminal_color_matches_previous": colors[-1] == colors[-2]}
    result["selected_run"] = {"prefix_start": start, "last_prefix_start": positions[-1],
        "slot_count": count, "stride": STRIDE, "parser_safe": False,
        "nearby_origin_class_counts_minus8_to_plus8": nearby,
        "nearby_stride_prefix_counts_196_to_212": [walk_prefix(data, start, stride) for stride in range(196, 213)],
        "signature_classes": len(set(signatures)), "signature_example": signatures[0].hex(),
        "other_signature_examples": [s.hex() for s in dict.fromkeys(signatures) if s != signatures[0]][:2],
        "upstream_context_classes": profile([data[p-16:p] for p in positions])["classes"],
        "first_vs_later": "first_slot_signature_candidate" if signatures[0] != signatures[1] else
            "upstream_difference_only" if selected["upstream_first_differs"] else "mixed_or_unresolved",
        "terminal_signature_label": "terminal_signature_candidate_matches_repeated" if signatures[-1] == signatures[-2] else "mixed_or_unresolved",
        "code": {"offset_relative_to_prefix": 4, "distribution_u32le_view": dict(sorted(Counter(str(v) for v in codes).items())),
            "zero_count": len(zero_indices), "nonzero_count": count-len(zero_indices),
            "narrow_views": code_views, "observed_code_byte_start": min(variable) if variable else None,
            "observed_variable_width": len(variable), "variable_byte_positions_in_code_view": variable,
            "typed_code_start": None, "typed_code_width": None},
        "color": {"observed_color_offset_relative_to_prefix": 0x50, "observed_color_changed_width": 3,
            "typed_color_width": None, "byte_distribution": dict(Counter(colors)),
            "color_context_signature_classes": len(set(color_contexts)), "color_context_example": color_contexts[0].hex(),
            "prior_grid_origin_delta": historical_grid_delta, "prior_grid_coordinate_match": prior_geometry_matches,
            "prior_grid_byte_match_count": prior_match_count},
        "terminal": terminal, "internal_code_13_count": codes.count(13),
        "prefix_break_at_code_13": False if 13 in codes else None}
    if details:
        # Bound indices before constructing optional rows.
        for i in sorted({0, 1, count//2, max(0, count-2), count-1})[:5]:
            result["slot_rows"].append({"index": i, "prefix_payload_start": positions[i],
                "code_zero": codes[i] == 0, "masked_prefix_signature": signatures[i].hex(),
                "color_bytes_50_52": colors[i], "next_prefix_present": prefix_present(data, positions[i]+STRIDE)})
    # Raw ordering is private frozen evidence for Phase B, not public Phase A text.
    return result, {"codes": codes}


def extract_structure(blob, details=False):
    if len(blob) > LIMITS["max_payload_bytes"]:
        raise ValueError("payload budget exceeded")
    parser = prior.prior.Type3ChainParser()
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
        report, raw = analyze_payload(node.payload, details and not paragraphs)
        desc = origin+node.start_offset
        paragraphs.append({"provenance": {"node_ordinal": ni, "runtime_descriptor_start": desc,
            "runtime_class_name": "CParagraphe", "runtime_schema": int.from_bytes(blob[desc+2:desc+4], "little"),
            "class_payload_start": origin+node.payload_offset, "payload_length": len(node.payload),
            "MFC_effect": "provenance_only", "absolute_offsets": "diagnostic_only"}, **report})
        evidence.append(raw)
    return {"paragraphs": paragraphs}, evidence


def structural_report(prepared):
    rows = [{"fixture": name, "structural": s} for name, s in prepared]
    paragraphs = [p for _, s in prepared for p in s["paragraphs"]]
    selected = [p["selected_run"] for p in paragraphs if p["selected_run"]]
    signatures = Counter(s for r in selected for s in [r["signature_example"], *r["other_signature_examples"]])
    color_contexts = Counter(r["color"]["color_context_example"] for r in selected)
    examples = list(signatures)[:LIMITS["max_signature_examples"]]
    # Derive a cross-fixture invariant mask only after count-framed structural selection.
    offsets = [i for i in range(32) if not 4 <= i <= 7]
    raw_signatures = [bytes.fromhex(s) for s in signatures]
    invariant = {str(off): raw_signatures[0][i] for i, off in enumerate(offsets)
                 if raw_signatures and len({s[i] for s in raw_signatures}) == 1}
    rules = {}
    for rule in ("R1", "R2", "R3", "R4"):
        statuses = Counter(p["rules"][rule]["status"] for p in paragraphs)
        rules[rule] = {f"{status}_count": statuses[status] for status in ("support", "conflict", "ambiguity", "abstention")}
        rules[rule]["false_candidate_count"] = sum(p["rules"][rule]["false_candidate_count"] for p in paragraphs)
    compatible = bool(selected) and len(selected) == len(paragraphs)
    all_terminal = bool(selected) and all(r["terminal"]["T1"] == "support" for r in selected)
    shifted = [r for r in selected if not r["color"]["prior_grid_coordinate_match"]]
    return {"fixture_results": rows,
        "prefix_signature_summary": {
            "P1": {"support": len(selected), "conflict": 0, "abstention": len(paragraphs)-len(selected)},
            "P2": {"status": "viable_prefix_token_alone_is_ambiguous",
                "support": rules["R1"]["ambiguity_count"], "conflict": 0,
                "abstention": len(paragraphs)-rules["R1"]["ambiguity_count"],
                "competing_run_count": sum(len(p["candidate_runs"])-bool(p["selected_run"]) for p in paragraphs)},
            "P3": {"status": "cross_fixture_variation_not_semantic_subtypes", "signature_classes": len(signatures),
                "support": sum(r["signature_classes"] > 1 for r in selected),
                "conflict": sum(r["signature_classes"] == 1 for r in selected), "abstention": len(paragraphs)-len(selected)},
            "P4": {"status": "upstream_transition_not_distinct_positive_prefix",
                "support": sum(r["signature_classes"] != 1 for r in selected),
                "conflict": sum(r["signature_classes"] == 1 for r in selected), "abstention": len(paragraphs)-len(selected)},
            "signature_examples": examples, "cross_fixture_invariant_bytes": invariant,
            "code_and_color_required_invariant_bytes": False, "parser_safe": False},
        "periodic_run_summary": {"selected_runs": len(selected), "selected_slots": sum(r["slot_count"] for r in selected),
            "stride": STRIDE, "maximality_scope": "prefix recurrence, not zero or text count; leading bounded search only",
            "all_selected_contexts_homogeneous": bool(selected) and all(r["signature_classes"] == 1 for r in selected),
            "nearby_strides": "see fixture count vectors for 196..212"},
        "run_start_rule_summary": {"rules": rules,
            "R1": "longest raw-prefix recurrence; ties retained",
            "R2": "preceding count matches independent recurrence; masked contexts stable after optional first-context difference",
            "R3": "distinct first positive-prefix signature; upstream differences alone do not qualify",
            "R4": "historical payload position 310 as diagnostic control only",
            "false_candidate_definition": "fails count/context framing, not externally proven non-slot semantics",
            "rule_validation_scope": "internal structural consistency, not independent semantic ground truth"},
        "slot_code_summary": {"slot_code_offset_relative_to_prefix": 4,
            "observed_code_byte_start": 4 if selected and all(r["code"]["observed_code_byte_start"] == 4 for r in selected) else None,
            "observed_variable_width": 1 if selected and all(r["code"]["observed_variable_width"] == 1 for r in selected) else None,
            "typed_code_start": None, "typed_code_width": None,
            "independent_neighbor_boundary_evidence": "none; zero upper bytes do not distinguish widths",
            "offset_basis": "existing prefix+4 hypothesis; never used for run selection"},
        "color_normalization_summary": {"observed_color_offset_relative_to_prefix": 0x50,
            "observed_color_changed_width": 3, "typed_color_width": None,
            "prior_grid_coordinate_matches": sum(r["color"]["prior_grid_coordinate_match"] for r in selected),
            "cross_fixture_masked_context_classes": len(color_contexts),
            "shifted_run_count": len(shifted), "shifted_scope": "same local context supports normalized position, not independent typed color decoding"},
        "terminal_detection_summary": {"T1_support_count": sum(r["terminal"]["T1"] == "support" for r in selected),
            "T2_internal_zero_count": sum(r["terminal"]["T2_premature_stop_count"] for r in selected),
            "T3_prefix_end_count": len(selected), "status": "zero_plus_prefix_end_candidate" if all_terminal else "unresolved",
            "T2_limit": "zero alone cannot justify stopping; synthetic internal-zero control required",
            "semantic_role": "zero_code_terminal_candidate; sentinel versus padding unresolved"},
        "multiline_summary": {"selection_basis": "code-13 or shifted structural runs; no filename branching",
            "fixtures": [{"fixture": name, "prefix_start": p["selected_run"]["prefix_start"],
                "slot_count": p["selected_run"]["slot_count"], "code_13_count": p["selected_run"]["internal_code_13_count"],
                "same_positive_prefix_example": p["selected_run"]["signature_example"] in {r["signature_example"] for r in selected if r["color"]["prior_grid_coordinate_match"]}}
                for name, s in prepared for p in s["paragraphs"] if p["selected_run"] and
                (p["selected_run"]["internal_code_13_count"] or not p["selected_run"]["color"]["prior_grid_coordinate_match"])],
            "interpretation": "bounded shared prefix-local schema; no hard-coded shift correction"},
        "answers": {"repeated_prefix_supported": compatible, "best_prefix_signature": {"token": PREFIX.hex(), "invariant_bytes": invariant},
            "prefix_signature_classes": len(signatures), "periodic_stride": STRIDE if selected else None,
            "run_start_detection_status": "unique_count_framed_candidate_in_bounded_search" if compatible else "unresolved",
            "slot_code_offset_relative_to_prefix": 4, "typed_slot_code_width": None,
            "color_offset_relative_to_prefix": 0x50, "typed_color_width": None,
            "terminal_detection_status": "zero_plus_prefix_end_candidate" if all_terminal else "unresolved",
            "multiline_same_slot_schema": "shared_prefix_local_candidate_only" if shifted else "not_tested_in_selected_inputs",
            "structural_slot_run_readiness": "bounded_framing_candidate_supported" if compatible and all_terminal else "unresolved",
            "candidate_parser_model_readiness": "not_ready", "color_ownership_readiness": "not_ready",
            "remaining_blockers": "bounded corpus/search coverage, competing periodic token, unproven count/prefix grammar and typed field widths"}}


def load_text_oracle(name):
    # This is diagnostic only and runs after complete structural/evidence freeze.
    if name in ("text_spacing_fixed.txt", "text_spacing_proportional.txt", "text_spacing_print_proportional.txt"):
        return {"texts": ["abcd\nefgh"], "source": "documented multiline paragraph-spacing controls"}
    return prior.load_text_oracle(name)


def oracle_phase(frozen, enabled):
    if not enabled:
        return {"enabled": False, "fixtures": []}
    evidence = json.loads(frozen)["evidence"]
    rows = []
    for name, paragraphs in evidence:
        oracle = load_text_oracle(name)
        diagnostics = []
        for raw in paragraphs:
            codes = raw["codes"] if raw else []
            text = "".join("\n" if v == 13 else chr(v) for v in codes[:-1]) if codes and codes[-1] == 0 and all(v == 13 or 32 <= v <= 126 for v in codes[:-1]) else None
            match = text in oracle["texts"] if oracle and text is not None else None
            diagnostics.append({"candidate_text": text, "ordinal_match": match,
                "n_plus_one": len(codes) == len(text)+1 if match else None})
        rows.append({"fixture": name, "diagnostics": diagnostics, "oracle_available": oracle is not None})
    return {"enabled": True, "structural_freeze_before_oracle": True, "selection_updates": False, "fixtures": rows}


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
        blob = prior.prior.hex_text_to_bytes(path.read_text(encoding="utf-8-sig"))
        structure, raw = extract_structure(blob, details and i < LIMITS["max_fixture_details"])
        prepared.append((name, structure))
        evidence.append((name, raw))
    frozen = compact({"structural": structural_report(prepared), "evidence": evidence})
    oracle = oracle_phase(frozen, oracle_enabled)
    return {"mode": "text_slot_prefix_framing_phase1e", "policy": POLICY.copy(),
            "limits": {**LIMITS, "details_enabled": details}, "warnings": [],
            **json.loads(frozen)["structural"], "oracle_summary": oracle}


def render_text(report, markdown=False):
    lines = [("# " if markdown else "")+"Text Slot Prefix Framing - Phase 1E"]
    for row in report["fixture_results"]:
        for p in row["structural"]["paragraphs"]:
            run = p["selected_run"]
            lines.append(compact({"fixture": row["fixture"], "status": p["status"],
                "start": run["prefix_start"] if run else None, "slots": run["slot_count"] if run else None,
                "candidate_runs": len(p["candidate_runs"]), "rules": p["rules"], "slot_rows": p["slot_rows"]}))
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
