"""Phase 2A: bounded structural hypotheses followed by isolated oracle comparison."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import analyze_text_visible_ownership as visible  # noqa: E402

FIXTURES = tuple(visible.FIXTURES)
TEXT_DIR = visible.TEXT_DIR
TOLERANCE_MM = 1e-6
MAX_CHAINS = 8
MAX_CANDIDATES = 16
MAX_SECTIONS = 256
MAX_LOCAL_ROWS = 4
MAX_TEXT_CHARS = 128
JSON_MAX_CHARS = 100000
STATUSES = ("supported", "contradicted", "blocked", "unresolved", "no_link_found")
OUTCOMES = ("agreement", "contradiction", "abstention", "oracle_unavailable", "oracle_ambiguous")
STRATEGIES = ("chain_order_pairing", "payload_order", "structural_linkage")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _chain_rows(parsed: Any) -> list[dict[str, Any]]:
    return [{
        "parser_chain_index": i,
        "text_candidate": (chain.source_text_candidate or chain.text_candidate or "")[:MAX_TEXT_CHARS],
        "text_truncated": len(chain.source_text_candidate or chain.text_candidate or "") > MAX_TEXT_CHARS,
        "current_active_anchor": visible._point_mm(chain.text_anchor),
        "anchor_parse_method": chain.text_anchor_parse_method or chain.text_anchor_source or "unknown",
        "provenance": {
            "source_node_class": chain.source_node_class,
            "source_payload_relative_offset": chain.source_payload_offset,
        },
    } for i, chain in enumerate(parsed.object_chains[:MAX_CHAINS])]


def _provenance(parsed: Any, nodes: list[Any]) -> tuple[list[dict], list[tuple], bool]:
    """Reproduce local signature traversal and reconcile with parser candidates.

    Offsets locate evidence only; their numeric values never select chains.
    Node ordinal counts only CPropertyExtend nodes; section/match ordinals reset per node.
    """
    parser = visible.Type3ChainParser()
    candidates = (parsed.candidate_fields or {}).get("cproperty_anchor_candidates") or []
    rows, locations = [], []
    visited = 0
    truncated = False
    for node_ordinal, node in enumerate(n for n in nodes if n.header.class_name == "CPropertyExtend"):
        start, section_ordinal, match_ordinal = 0, 0, 0
        while True:
            offset = node.payload.find(parser.COBDAO_MARKER, start)
            if offset < 0:
                break
            if visited >= MAX_SECTIONS or len(rows) >= MAX_CANDIDATES:
                truncated = True
                break
            visited += 1
            start = offset + 1
            matched, signature = parser._match_cproperty_anchor_signature_v1(node.payload, offset)
            if matched:
                index = len(rows)
                anchor = parser._decode_double3_mm(node.payload, offset + 34)
                if index >= len(candidates) or anchor is None:
                    raise ValueError("candidate provenance could not be reconciled")
                candidate = candidates[index]
                if (candidate["cobdao_relative_offset"] != offset or
                        tuple(candidate[k] for k in ("x_mm", "y_mm", "z_mm")) != tuple(anchor)):
                    raise ValueError("candidate traversal differs from parser extraction")
                rows.append({
                    "candidate_index": index,
                    "cproperty_node_ordinal": node_ordinal,
                    "cobdao_section_ordinal": section_ordinal,
                    "signature_match_ordinal": match_ordinal,
                    "cobdao_payload_relative_offset": offset,
                    "anchor_relative_to_cobdao": 34,
                    "candidate_anchor_mm": list(anchor),
                    "signature_values": {f"+{k}": signature[f"u32le_cobdao_plus_{k}"] for k in (12, 56, 108, 112)},
                })
                locations.append((node.payload, offset))
                match_ordinal += 1
            section_ordinal += 1
        if truncated:
            break
    if not truncated and len(rows) != len(candidates):
        raise ValueError("not all parser candidates have local provenance")
    return rows, locations, truncated


def _local_linkage(parsed: Any, locations: list[tuple]) -> dict:
    """Check small-index coincidences in bounded local words, never anchor bytes.

    The chain source preamble is only an untyped reference region. Matching a word
    does not establish that it is an object ID, count, or link.
    """
    reference_words: dict[int, set[int]] = {}
    for i, chain in enumerate(parsed.object_chains[:MAX_CHAINS]):
        # Stream position is used internally to locate the parser's source node,
        # never emitted or used numerically as an ownership hypothesis.
        if chain.source_payload_offset is None or chain.source_stream_offset is None:
            continue
        node = next((n for n in chain.nodes if n.header.class_name == chain.source_node_class
                     and n.payload_offset + chain.source_payload_offset == chain.source_stream_offset), None)
        if node is None:
            continue
        end = chain.source_payload_offset
        if not 16 <= end <= len(node.payload):
            continue
        reference_words[i] = set(struct.unpack("<4I", node.payload[end - 16:end]))
    rows, hits, words_scanned = [], 0, 0
    for candidate_index, (payload, offset) in enumerate(locations):
        # Fixed 120-byte local window. Exclude the whole coordinate triple and
        # all signature-word spans, including overlapping windows.
        excluded = ((12, 16), (34, 58), (56, 60), (108, 116))
        for relative in range(8, 125, 4):
            if any(relative < end and relative + 4 > start for start, end in excluded):
                continue
            if offset + relative + 4 > len(payload):
                continue
            words_scanned += 1
            value = struct.unpack_from("<I", payload, offset + relative)[0]
            if not 1 <= value <= len(parsed.object_chains):
                continue
            matches = [i for i, words in reference_words.items() if value in words]
            if matches:
                hits += 1
                if len(rows) < MAX_LOCAL_ROWS:
                    rows.append({"candidate_index": candidate_index, "relative_to_cobdao": relative,
                                 "untyped_integer": value, "reference_chain_indices": matches})
    return {
        "search": "u32le at +8..+124 step 4; excludes anchor/signature spans; chain source preamble 16 bytes",
        "candidate_words_scanned": words_scanned,
        "chain_reference_regions": len(reference_words),
        "untyped_coincidence_count": hits,
        "verbose_rows": rows,
        "verbose_rows_omitted": hits - len(rows),
        "interpretation": "integer coincidences are not typed object identifiers or ownership links",
    }


def _conditional_pairings(candidate_order: list[int], chain_count: int) -> list[dict]:
    if chain_count > MAX_CHAINS or len(candidate_order) != chain_count - 1:
        return []
    # At most MAX_CHAINS alternatives, never permutations. Each is conditional,
    # and every chain can be the excluded owner; no one alternative is selected.
    return [{"if_cpar_owner_chain": owner,
             "candidate_order": list(candidate_order),
             "remaining_chain_order": [i for i in range(chain_count) if i != owner]}
            for owner in range(chain_count)]


def structural_phase(parsed: Any, nodes: list[Any]) -> dict:
    """Phase A API: no filename, intent, oracle, or expected ownership inputs."""
    provenance, locations, truncated = _provenance(parsed, nodes)
    chain_count = len(parsed.object_chains)
    truncated = truncated or chain_count > MAX_CHAINS
    emission_order = [p["candidate_index"] for p in provenance]
    traversal_order = [p["candidate_index"] for p in sorted(provenance, key=lambda p: (
        p["cproperty_node_ordinal"], p["cobdao_section_ordinal"], p["signature_match_ordinal"]))]
    pairing = [] if truncated else _conditional_pairings(emission_order, chain_count)
    payload_pairing = [] if truncated else _conditional_pairings(traversal_order, chain_count)
    linkage = _local_linkage(parsed, locations)
    hypotheses = [
        {"strategy": "chain_order_pairing", "status": "blocked", "parser_safe": False,
         "reason": "no_structural_cparagraphe_owner", "mapping_hypotheses": pairing,
         "evidence": {"candidate_emission_order": emission_order, "parser_chain_count": chain_count},
         "unmet_dependencies": ["no_structural_cparagraphe_owner", "candidate_order_to_chain_order_unproven"]},
        {"strategy": "payload_order", "status": "unresolved", "parser_safe": False,
         "mapping_hypotheses": payload_pairing,
         "evidence": {"candidate_traversal_order": traversal_order,
                      "traversal_definition": ["cproperty_node_ordinal", "cobdao_section_ordinal", "signature_match_ordinal"],
                      "unsupported_assumptions": ["ascending_remaining_chain_order", "one_candidate_per_remaining_chain"]},
         "unmet_dependencies": ["no_structural_cparagraphe_owner", "payload_order_semantics_unproven"]},
        {"strategy": "structural_linkage", "status": "no_link_found", "parser_safe": False,
         "mapping_hypotheses": [], "evidence": linkage,
         "unmet_dependencies": ["no_typed_object_identifier_or_linkage_validated"]},
    ]
    for hypothesis in hypotheses:
        if len(provenance) != chain_count - 1:
            hypothesis["unmet_dependencies"].append("candidate_count_not_n_minus_one")
        if truncated:
            hypothesis["unmet_dependencies"].append("bounded_analysis_incomplete")
    return {"parser_chains": _chain_rows(parsed), "candidate_provenance": provenance,
            "structural_hypotheses": hypotheses, "truncated": truncated,
            "provenance_counts": {"parser_chains": chain_count,
                                  "parser_candidates": len((parsed.candidate_fields or {}).get("cproperty_anchor_candidates") or []),
                                  "reported_candidates": len(provenance)}}


def anchor_oracle(anchor: dict | None, chains: list[dict], *, enabled: bool = True) -> dict:
    available = enabled and anchor is not None and bool(chains) and all(
        c["current_active_anchor"] is not None for c in chains)
    matches = [c["parser_chain_index"] for c in chains
               if available and visible._same_point(anchor, c["current_active_anchor"], TOLERANCE_MM)]
    status = "unavailable" if not available else "unique" if len(matches) == 1 else "ambiguous" if matches else "none"
    return {"source": "current_parser_active_anchor_equality_diagnostic_only", "tolerance_mm": TOLERANCE_MM,
            "matching_chain_indices": matches, "status": status}


def oracle_phase(phase_a: dict, nodes: list[Any], *, enabled: bool) -> dict:
    """Phase B oracle construction; baseline equality is not independent truth."""
    direct = next((visible._decode_cparagraphe_direct_anchor(n.payload) for n in nodes
                   if n.header.class_name == "CParagraphe"), None)
    chains = phase_a["parser_chains"]
    candidates = []
    for p in phase_a["candidate_provenance"]:
        anchor = dict(zip(("x", "y", "z"), p["candidate_anchor_mm"]))
        candidates.append({"candidate_index": p["candidate_index"],
                           **anchor_oracle(anchor, chains, enabled=enabled and not phase_a["truncated"])})
    return {"anchor_equality": candidates,
            "cparagraphe_anchor_equality": anchor_oracle(direct, chains, enabled=enabled and not phase_a["truncated"]),
            "limitation": "active-anchor consistency only; not independent text identity or stored-order truth"}


def _mapping_comparison(mapping: dict, oracles: dict) -> str:
    rows = {r["candidate_index"]: r for r in oracles["anchor_equality"]}
    selected = [rows.get(i) for i in mapping["candidate_order"]]
    if not selected or any(r is None or r["status"] == "unavailable" for r in selected):
        return "oracle_unavailable"
    if any(r["status"] == "ambiguous" for r in selected):
        return "oracle_ambiguous"
    return "agreement" if all(r["matching_chain_indices"] == [chain] for r, chain in
                               zip(selected, mapping["remaining_chain_order"])) else "contradiction"


def compare_frozen(frozen_hypotheses: str, oracles: dict) -> list[dict]:
    """Deserialize a private copy; never revise Phase A statuses or hypotheses."""
    comparisons = []
    for strategy in json.loads(frozen_hypotheses):
        statuses = [r["status"] for r in oracles["anchor_equality"]]
        outcome = "abstention"
        if not statuses or "unavailable" in statuses:
            outcome = "oracle_unavailable"
        elif "ambiguous" in statuses:
            outcome = "oracle_ambiguous"
        conditional_results = []
        for mapping in strategy["mapping_hypotheses"]:
            cpar = oracles["cparagraphe_anchor_equality"]
            condition = ("oracle_unavailable" if cpar["status"] in ("unavailable", "none") else
                         "oracle_ambiguous" if cpar["status"] == "ambiguous" else
                         "agreement" if cpar["matching_chain_indices"] == [mapping["if_cpar_owner_chain"]] else
                         "contradiction")
            conditional_results.append({"if_cpar_owner_chain": mapping["if_cpar_owner_chain"],
                                        "condition_comparison": condition,
                                        "mapping_comparison": _mapping_comparison(mapping, oracles)})
        comparisons.append({"strategy": strategy["strategy"], "outcome": outcome,
                            "reason": "no_unconditional_structural_assignment",
                            "conditional_results": conditional_results})
    return comparisons


def analyze_parsed(parsed: Any, nodes: list[Any], fixture: str, *, oracle_enabled: bool = True) -> dict:
    phase_a = structural_phase(parsed, nodes)
    frozen = _json(phase_a["structural_hypotheses"])
    # This is the first point at which a fixture name/intent can affect reporting.
    intent = visible._intent_metadata(fixture) if oracle_enabled else None
    oracles = oracle_phase(phase_a, nodes, enabled=oracle_enabled)
    comparisons = compare_frozen(frozen, oracles)
    normalized = intent["normalized_intent_metadata"] if intent else None
    intent_reporting = None if intent is None else {
        "attempted_order_source": intent["attempted_order_source"],
        "attempted_selection_order": [
            {"label": entry["label"], "text": entry["text"][:MAX_TEXT_CHARS]}
            for entry in (normalized or {}).get("attempted_selection_order", [])[:MAX_CHAINS]
        ],
    }
    return {"fixture": fixture, **phase_a, "structural_hypotheses": json.loads(frozen),
            "grouping": intent["grouping"] if intent else "unknown",
            "order_control_status": intent["order_control_status"] if intent else "unknown",
            "actual_stored_order": "unresolved",
            "intent_reporting": intent_reporting,
            "warnings": intent["warnings"] if intent else [],
            "oracle_results": oracles, "comparisons": comparisons}


def _summaries(fixtures: list[dict]) -> tuple[dict, dict]:
    strategies = {name: {**dict.fromkeys(("evaluated", *STATUSES), 0),
                         **dict.fromkeys(("oracle_agreement", "oracle_contradiction", "abstention",
                                          "oracle_unavailable", "oracle_ambiguous"), 0),
                         "conditional_applicable_agreement": 0, "conditional_applicable_contradiction": 0}
                  for name in STRATEGIES}
    oracle_counts = Counter({status: 0 for status in ("unique", "ambiguous", "none", "unavailable")})
    direct_counts = Counter(oracle_counts)
    for fixture in fixtures:
        oracle_counts.update(r["status"] for r in fixture["oracle_results"]["anchor_equality"])
        direct_counts.update([fixture["oracle_results"]["cparagraphe_anchor_equality"]["status"]])
        for hypothesis, comparison in zip(fixture["structural_hypotheses"], fixture["comparisons"]):
            counts = strategies[hypothesis["strategy"]]
            counts["evaluated"] += 1
            counts[hypothesis["status"]] += 1
            outcome = comparison["outcome"]
            counts["oracle_" + outcome if outcome in ("agreement", "contradiction") else outcome] += 1
            for conditional in comparison["conditional_results"]:
                if conditional["condition_comparison"] == "agreement":
                    match = conditional["mapping_comparison"]
                    if match in ("agreement", "contradiction"):
                        counts["conditional_applicable_" + match] += 1
    return strategies, {"candidate_anchor_equality": dict(oracle_counts),
                        "cparagraphe_anchor_equality": dict(direct_counts),
                        "counting_unit": "candidate; strategy counts use fixture; conditional counts are diagnostic only"}


def _bound_report(report: dict, limit: int = JSON_MAX_CHARS) -> dict:
    """Rows are bounded at generation; shed optional evidence if total budget is exceeded."""
    if len(_json(report)) < limit:
        return report
    report["truncated"] = True
    report["warnings"].append("output budget: verbose evidence rows omitted")
    for fixture in report["fixture_results"]:
        for strategy in fixture["structural_hypotheses"]:
            strategy["evidence"].pop("verbose_rows", None)
        fixture["intent_reporting"] = None
    if len(_json(report)) >= limit:
        report["warnings"].append("output budget: fixture details omitted; summaries and provenance counts retained")
        report["fixture_results"] = [{k: row[k] for k in (
            "fixture", "grouping", "order_control_status", "actual_stored_order", "provenance_counts")}
            for row in report["fixture_results"]]
    return report


def build_report(*, oracle_enabled: bool = True) -> dict:
    results, warnings = [], []
    for fixture in FIXTURES:
        path = TEXT_DIR / fixture
        if not path.exists():
            warnings.append(f"missing fixture: {fixture}")
            continue
        blob = visible._read_fixture(path)
        parsed, _ = visible.parse_type3_clipboard_bytes_with_parser(blob)
        result = analyze_parsed(parsed, visible._read_nodes(blob), fixture, oracle_enabled=oracle_enabled)
        results.append(result)
        warnings.extend(result["warnings"])
        if result["truncated"]:
            warnings.append(f"bounded analysis incomplete: {fixture}")
    strategies, oracles = _summaries(results)
    return _bound_report({
        "mode": "phase_2a_shadow_mapping", "oracle_enabled": oracle_enabled,
        "policy": {"scope": "phase_2a_shadow_mapping_analyzer_only", "parser_behavior": "not_modified",
                   "ownership_assignment": "not_performed", "matched_chain_behavior": "unchanged_none",
                   "active_anchor_behavior": "unchanged", "oracle_isolation": True},
        "limits": {"text_max_chars": 50000, "json_max_chars": JSON_MAX_CHARS,
                   "max_chains_per_fixture": MAX_CHAINS, "max_candidates_per_fixture": MAX_CANDIDATES,
                   "max_sections_per_fixture": MAX_SECTIONS, "max_local_evidence_rows": MAX_LOCAL_ROWS,
                   "local_search_bytes": 120, "local_hex": False, "factorial_permutations": False},
        "warnings": warnings, "truncated": any(r["truncated"] for r in results),
        "fixture_results": results, "strategy_summary": strategies, "oracle_summary": oracles,
        "answers": {"parser_ownership_ready": False, "parser_safe": False,
                    "cparagraphe_owner": "no_structural_rule", "actual_stored_order": "unresolved",
                    "next_step": "investigate typed local linkage and independently validate CParagraphe ownership"},
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="compact JSON")
    parser.add_argument("--no-oracle", action="store_true", help="skip intent loading and disable equality oracles")
    args = parser.parse_args()
    report = build_report(oracle_enabled=not args.no_oracle)
    if args.json:
        print(_json(report))
    else:
        print("Text Anchor Shadow Mapping (Phase 2A, analyzer only)")
        print("Parser unchanged; ownership not performed; all strategies parser_safe=false")
        for row in report["fixture_results"]:
            statuses = ", ".join(f"{s['strategy']}={s['status']}" for s in row.get("structural_hypotheses", []))
            print(f"{row['fixture']}: {row['grouping']}, order={row['order_control_status']}; {statuses}")
        print("Strategy summary:", _json(report["strategy_summary"]))
        print("Oracle summary:", _json(report["oracle_summary"]))
        for warning in report["warnings"]:
            print("Warning:", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
