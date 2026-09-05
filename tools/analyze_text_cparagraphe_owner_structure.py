"""Bounded CParagraphe owner-structure investigation; no ownership assignment."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct
import sys
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import analyze_text_anchor_shadow_mapping as shadow  # noqa: E402

visible = shadow.visible
FIXTURES = tuple(shadow.FIXTURES)
TEXT_DIR = visible.TEXT_DIR
MAX_NODES = 32
MAX_CPAR = 4
MAX_CHAINS = 8
MAX_FIELD_MATCH_ROWS = 8
FIELD_OFFSETS = (*range(126, 158, 4), *range(182, 214, 4))
JSON_LIMIT = 100000


def compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _source_inventory(parsed: Any, nodes: list[Any]) -> tuple[list[dict], list[tuple]]:
    rows, references = [], []
    for index, chain in enumerate(parsed.object_chains[:MAX_CHAINS]):
        # Locate the source using existing parser provenance, not coordinate equality.
        # Absolute addresses are used only for internal node lookup, never emitted.
        source = next((n for n in chain.nodes if n.header.class_name == chain.source_node_class
                       and chain.source_payload_offset is not None
                       and n.payload_offset + chain.source_payload_offset == chain.source_stream_offset), None)
        ordinal = None
        if source is not None:
            # visible._read_nodes uses the body origin; parser chain nodes use the
            # full stream origin. Normalize the origin solely to locate that node.
            ordinal = next((i for i, n in enumerate(nodes) if n.header.class_name == source.header.class_name
                            and n.payload_offset + visible.TOP_LEVEL_HEADER_LEN == source.payload_offset), None)
            offset = chain.source_payload_offset
            if offset is not None and 16 <= offset <= len(source.payload):
                references.append((index, source.payload[offset - 16:offset]))
        rows.append({"parser_chain_index": index,
                     "text_candidate": (chain.source_text_candidate or chain.text_candidate or "")[:128],
                     "source_node_class": chain.source_node_class,
                     "source_node_traversal_ordinal": ordinal,
                     "source_payload_relative_offset": chain.source_payload_offset,
                     "cpar_node_membership_count": sum(n.header.class_name == "CParagraphe" for n in chain.nodes)})
    return rows, references


def _local_fields(payload: bytes) -> list[dict]:
    # Two fixed 32-byte windows around, but never overlapping, direct double3.
    # Values remain untyped; color/style/float semantics are deliberately not decoded.
    return [{"payload_relative_offset": offset, "u32le": struct.unpack_from("<I", payload, offset)[0]}
            for offset in FIELD_OFFSETS if offset + 4 <= len(payload)]


def _identifier_probe(fields: list[dict], references: list[tuple], candidate_locations: list[tuple], n: int) -> dict:
    # Indexed lookup of bounded u32 words, not full payload pairwise comparison.
    chains: dict[int, set[int]] = defaultdict(set)
    sections: dict[int, set[int]] = defaultdict(set)
    for index, preamble in references:
        for value in struct.unpack("<4I", preamble):
            chains[value].add(index)
    for index, (payload, offset) in enumerate(candidate_locations):
        for relative in range(8, 125, 4):
            if any(relative < end and relative + 4 > start
                   for start, end in ((12, 16), (34, 60), (108, 116))):
                continue
            if offset + relative + 4 <= len(payload):
                sections[struct.unpack_from("<I", payload, offset + relative)[0]].add(index)
    rows, hit_count = [], 0
    for field in fields:
        value = field["u32le"]
        if value == 0:
            continue  # zero padding is not identifier evidence
        if value in chains or value in sections:
            hit_count += 1
            if len(rows) < MAX_FIELD_MATCH_ROWS:
                rows.append({**field, "small_ordinal_range": 1 <= value <= n,
                             "chain_reference_indices": sorted(chains.get(value, [])),
                             "candidate_section_indices": sorted(sections.get(value, []))})
    return {"chain_reference_count": len(references), "candidate_section_reference_count": len(candidate_locations),
            "shared_nonzero_field_count": hit_count, "field_matches": rows,
            "field_matches_omitted": hit_count - len(rows),
            "typed_identifier_found": False,
            "limitation": "untyped word equality including constants is not an object identifier"}


def _hypothesis(name: str, inputs: list[str], status: str, proposed: list[int], evidence: dict) -> dict:
    return {"name": name, "structural_inputs": inputs, "status": status,
            "possible_chain_indices": proposed,
            "fixture_support_count": 0, "fixture_conflict_count": 0, "fixture_abstention_count": 1,
            "count_basis": "pre_oracle_no_owner_claim", "evidence": evidence, "parser_safe": False}


def structural_phase(parsed: Any, nodes: list[Any]) -> dict:
    """Phase A: no fixture name, intent, active-anchor oracle, or known owner input."""
    truncated = len(nodes) > MAX_NODES or len(parsed.object_chains) > MAX_CHAINS
    bounded_nodes = nodes[:MAX_NODES]
    sources, references = _source_inventory(parsed, bounded_nodes)
    candidates, locations, candidate_truncated = shadow._provenance(parsed, nodes)
    truncated |= candidate_truncated
    candidate_rows = [{k: p[k] for k in (
        "candidate_index", "cproperty_node_ordinal", "cobdao_section_ordinal",
        "signature_match_ordinal", "cobdao_payload_relative_offset")}
        for p in candidates]
    layouts = []
    parser = visible.Type3ChainParser()
    for ordinal, node in enumerate(bounded_nodes):
        if node.header.class_name == "CPropertyExtend":
            count, start = 0, 0
            while count < shadow.MAX_SECTIONS:
                found = node.payload.find(parser.COBDAO_MARKER, start)
                if found < 0:
                    break
                count += 1
                start = found + 1
            limited = count == shadow.MAX_SECTIONS and node.payload.find(parser.COBDAO_MARKER, start) >= 0
            truncated |= limited
            layouts.append({"node_traversal_ordinal": ordinal, "cobdao_section_count": count,
                            "count_truncated": limited})
    cpars = []
    for ordinal, node in enumerate(bounded_nodes):
        if node.header.class_name != "CParagraphe":
            continue
        if len(cpars) == MAX_CPAR:
            truncated = True
            break
        fields = _local_fields(node.payload)
        nearby = [{"node_traversal_ordinal": i, "class": bounded_nodes[i].header.class_name}
                  for i in range(max(0, ordinal - 2), min(len(bounded_nodes), ordinal + 3)) if i != ordinal]
        cpars.append({"cparagraphe_node_ordinal": len(cpars), "node_traversal_ordinal": ordinal,
                      "payload_length": len(node.payload),
                      "preceding_node_class": bounded_nodes[ordinal - 1].header.class_name if ordinal else None,
                      "following_node_class": bounded_nodes[ordinal + 1].header.class_name if ordinal + 1 < len(bounded_nodes) else None,
                      "nearest_structural_classes": nearby,
                      "direct_anchor_local_offset": 158,
                      "direct_anchor_mm": visible._decode_cparagraphe_direct_anchor(node.payload),
                      "bounded_structural_fields": fields,
                      "identifier_probe": _identifier_probe(fields, references, locations, len(parsed.object_chains))})
    nearest = []
    if len(cpars) == 1 and not truncated:
        following = [s for s in sources if s["source_node_traversal_ordinal"] is not None
                     and s["source_node_traversal_ordinal"] > cpars[0]["node_traversal_ordinal"]]
        if following:
            first = min(s["source_node_traversal_ordinal"] for s in following)
            # Do not break ties using coordinates, names, or chain index.
            nearest = [s["parser_chain_index"] for s in following if s["source_node_traversal_ordinal"] == first]
    membership = [s["parser_chain_index"] for s in sources if s["cpar_node_membership_count"]]
    hypotheses = [
        _hypothesis("nearest_following_chain_source", ["node_traversal", "chain_source_node"],
                    "unresolved" if nearest else "blocked", nearest,
                    {"relationship": "closest following node that structurally produces a parser chain",
                     "limitation": "adjacency is correlation only; no explicit anchor-to-chain link"}),
        _hypothesis("first_parser_chain_control", ["parser_chain_index"],
                    "unresolved" if sources and not truncated else "blocked",
                    [0] if sources and not truncated else [],
                    {"relationship": "control hypothesis: chain zero regardless of source-node position"}),
        _hypothesis("exclusive_cpar_node_membership", ["chain_node_membership"],
                    "unresolved" if len(membership) == 1 else "blocked",
                    membership if len(membership) == 1 and not truncated else [],
                    {"member_chain_indices": membership, "limitation": "shared node membership does not identify an owner"}),
        _hypothesis("local_shared_identifier", ["bounded_cpar_u32_fields", "source_preamble_words", "candidate_section_words"],
                    "no_signal", [], {"typed_identifier_found": False, "limitation": "untyped coincidences cannot select owners"}),
        _hypothesis("layout_only_owner", ["node_class_order", "cobdao_section_counts"], "blocked", [],
                    {"limitation": "counts/class order have no established chain linkage semantics"}),
    ]
    return {"cparagraphe_provenance": cpars, "parser_chain_provenance": sources,
            "node_class_order": [n.header.class_name for n in bounded_nodes],
            "cproperty_section_layout": layouts, "cproperty_candidate_traversal": candidate_rows,
            "hypotheses": hypotheses, "truncated": truncated,
            "inventory_counts": {"nodes": len(nodes), "parser_chains": len(parsed.object_chains),
                                 "cparagraphe_nodes": sum(n.header.class_name == "CParagraphe" for n in nodes)}}


def oracle_phase(parsed: Any, frozen: str, *, enabled: bool) -> dict | None:
    """Phase B only. Disabled or unavailable diagnostics are null, never 'none'."""
    structure = json.loads(frozen)
    cpars = structure["cparagraphe_provenance"]
    if not enabled or len(cpars) != 1 or structure["truncated"]:
        return None
    result = shadow.anchor_oracle(cpars[0]["direct_anchor_mm"], shadow._chain_rows(parsed))
    if result["status"] == "unavailable":
        return None
    return {"matching_chain_indices": result["matching_chain_indices"], "status": result["status"],
            "tolerance": result["tolerance_mm"], "source": result["source"]}


def compare_frozen(frozen: str, oracle: dict | None) -> list[dict]:
    comparisons = []
    for h in json.loads(frozen)["hypotheses"]:
        proposed = h["possible_chain_indices"]
        if oracle is None:
            outcome = "oracle_unavailable"
        elif oracle["status"] == "ambiguous":
            outcome = "oracle_ambiguous"
        elif len(proposed) != 1:
            outcome = "abstention"
        else:
            outcome = "support" if proposed == oracle["matching_chain_indices"] else "conflict"
        comparisons.append({"name": h["name"], "outcome": outcome})
    return comparisons


def finish_fixture(parsed: Any, frozen: str, fixture: str, *, oracle_enabled: bool = True) -> dict:
    # The string is immutable, and neither oracle nor intent has access to Phase A objects.
    intent = visible._intent_metadata(fixture) if oracle_enabled else None
    oracle = oracle_phase(parsed, frozen, enabled=oracle_enabled)
    warnings = list(intent["warnings"]) if intent else []
    if oracle_enabled and oracle is None:
        warnings.append("direct-anchor oracle unavailable")
    metadata = (intent or {}).get("normalized_intent_metadata") or {}
    return {"fixture": fixture, "structural": json.loads(frozen),
            "grouping": intent["grouping"] if intent else "unknown",
            "order_control_status": intent["order_control_status"] if intent else "unknown",
            "attempted_selection_order": [{"label": e["label"], "text": e["text"][:128]}
                                          for e in metadata.get("attempted_selection_order", [])[:MAX_CHAINS]],
            "actual_stored_order": "unresolved", "oracle": oracle,
            "comparisons": compare_frozen(frozen, oracle), "warnings": warnings}


def analyze_parsed(parsed: Any, nodes: list[Any], fixture: str, *, oracle_enabled: bool = True) -> dict:
    return finish_fixture(parsed, compact(structural_phase(parsed, nodes)), fixture, oracle_enabled=oracle_enabled)


def structural_summaries(structures: list[dict]) -> tuple[list, list]:
    fields: dict[int, Counter] = defaultdict(Counter)
    adjacency = Counter()
    for structure in structures:
        for cpar in structure["cparagraphe_provenance"]:
            adjacency[(cpar["node_traversal_ordinal"], cpar["preceding_node_class"], cpar["following_node_class"])] += 1
            for field in cpar["bounded_structural_fields"]:
                fields[field["payload_relative_offset"]][field["u32le"]] += 1
    return ([{"payload_relative_offset": offset, "observations": sum(values.values()),
              "distinct_value_count": len(values), "values": dict(values),
              "interpretation": "untyped; invariance or variation alone is not an owner identifier"}
             for offset, values in sorted(fields.items())],
            [{"node_traversal_ordinal": key[0], "preceding_class": key[1], "following_class": key[2], "count": count}
             for key, count in adjacency.items()])


def _post_oracle_summaries(results: list[dict]) -> tuple[list, dict, dict]:
    hypotheses: dict[str, dict] = {}
    groups: dict[str, list] = defaultdict(list)
    oracle_counts = Counter({s: 0 for s in ("unique", "ambiguous", "none", "unavailable")})
    for result in results:
        oracle_counts[result["oracle"]["status"] if result["oracle"] else "unavailable"] += 1
        structure = result["structural"]
        groups[result["grouping"]].append({
            "fixture": result["fixture"], "chain_count": structure["inventory_counts"]["parser_chains"],
            "cpar_payload_lengths": [p["payload_length"] for p in structure["cparagraphe_provenance"]],
            "cobdao_section_counts": [p["cobdao_section_count"] for p in structure["cproperty_section_layout"]],
            "chain_source_classes": [p["source_node_class"] for p in structure["parser_chain_provenance"]],
            "nearest_following_source_chain_indices": structure["hypotheses"][0]["possible_chain_indices"],
            "diagnostic_owner": result["oracle"]["matching_chain_indices"] if result["oracle"] else None,
        })
        for h, comparison in zip(structure["hypotheses"], result["comparisons"]):
            if h["name"] not in hypotheses:
                hypotheses[h["name"]] = {"name": h["name"], "structural_inputs": h["structural_inputs"],
                    "status": h["status"], "fixture_support_count": 0, "fixture_conflict_count": 0,
                    "fixture_abstention_count": 0, "oracle_unavailable_count": 0, "oracle_ambiguous_count": 0,
                    "evidence": {"conflicting_fixtures": [], "structural_status_counts": {}},
                    "count_basis": "post_oracle_diagnostic_comparison_only", "parser_safe": False}
            row = hypotheses[h["name"]]
            statuses = row["evidence"]["structural_status_counts"]
            statuses[h["status"]] = statuses.get(h["status"], 0) + 1
            outcome = comparison["outcome"]
            if outcome in ("support", "conflict", "abstention"):
                row[f"fixture_{outcome}_count"] += 1
            else:
                row["fixture_abstention_count"] += 1
                row[outcome + "_count"] += 1
            if outcome == "conflict":
                row["evidence"]["conflicting_fixtures"].append(result["fixture"])
    for row in hypotheses.values():
        if row["fixture_conflict_count"]:
            row["status"] = "contradicted"
        elif row["fixture_support_count"]:
            row["status"] = "supported"
    return list(hypotheses.values()), dict(groups), dict(oracle_counts)


def bound_report(report: dict, limit: int = JSON_LIMIT) -> dict:
    if len(compact(report).encode("utf-8")) < limit:
        return report
    report["truncated"] = True
    report["warnings"].append("output budget: local field details omitted; aggregate field summary retained")
    for result in report["fixture_results"]:
        for cpar in result["structural"]["cparagraphe_provenance"]:
            cpar.pop("bounded_structural_fields", None)
            cpar["identifier_probe"].pop("field_matches", None)
    if len(compact(report).encode("utf-8")) >= limit:
        report["warnings"].append("output budget: fixture details omitted; inventory counts and summaries retained")
        report["fixture_results"] = [{"fixture": r["fixture"], "inventory_counts": r["structural"]["inventory_counts"]}
                                     for r in report["fixture_results"]]
    return report


def build_report(*, oracle_enabled: bool = True) -> dict:
    prepared, warnings = [], []
    # Finish and freeze the entire structural corpus before loading any oracle/intent.
    for fixture in FIXTURES:
        path = TEXT_DIR / fixture
        if not path.exists():
            warnings.append(f"missing fixture: {fixture}")
            continue
        blob = visible._read_fixture(path)
        parsed, _ = visible.parse_type3_clipboard_bytes_with_parser(blob)
        structural = structural_phase(parsed, visible._read_nodes(blob))
        if structural["truncated"]:
            warnings.append(f"bounded structural inventory incomplete: {fixture}")
        prepared.append((fixture, parsed, compact(structural)))
    field_summary, adjacency = structural_summaries([json.loads(frozen) for _, _, frozen in prepared])
    results = [finish_fixture(parsed, frozen, fixture, oracle_enabled=oracle_enabled)
               for fixture, parsed, frozen in prepared]
    for result in results:
        warnings.extend(f"{result['fixture']}: {w}" for w in result["warnings"])
    hypotheses, grouping, oracles = _post_oracle_summaries(results)
    return bound_report({
        "mode": "cparagraphe_owner_structure", "oracle_enabled": oracle_enabled,
        "policy": {"scope": "cparagraphe_owner_structural_analysis_only", "parser_behavior": "not_modified",
                   "ownership_assignment": "not_performed", "oracle_isolation": True, "active_anchor_behavior": "unchanged"},
        "limits": {"text_max_bytes": 50000, "json_max_bytes": JSON_LIMIT, "local_hex": False,
                   "max_nodes": MAX_NODES, "max_cpar_nodes": MAX_CPAR, "max_chains": MAX_CHAINS,
                   "cpar_u32_offsets": list(FIELD_OFFSETS), "max_field_match_rows": MAX_FIELD_MATCH_ROWS,
                   "chain_reference_bytes": 16, "candidate_reference_bytes": 120,
                   "max_candidate_references": shadow.MAX_CANDIDATES, "max_sections_per_node": shadow.MAX_SECTIONS,
                   "unrestricted_pairwise_mining": False},
        "warnings": warnings, "truncated": any(r["structural"]["truncated"] for r in results),
        "fixture_results": results, "structural_field_summary": field_summary, "adjacency_summary": adjacency,
        "grouping_comparison": {"phase": "post_freeze_reporting_only", "groups": grouping,
                                "limitation": "intent grouping labels stratify observed layouts; no owner selector"},
        "hypothesis_summary": hypotheses, "oracle_summary": oracles,
        "answers": {"conclusion": "no_parser_safe_cparagraphe_owner_rule_found", "parser_safe": False,
                    "phase_2_ownership_ready": False, "actual_stored_order": "unresolved",
                    "structural_signal": "nearest following chain-producing node; correlation requires independent linkage proof",
                    "parser_index_caveat": "existing text parser sorts chains by anchor/bbox coordinates; analyzer does not sort coordinates",
                    "content_independence": "inspect chain source provenance rather than text labels; payload length can vary",
                    "scope_limit": "bounded local words and existing parser chain construction only; not exhaustive"},
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-oracle", action="store_true")
    args = parser.parse_args()
    report = build_report(oracle_enabled=not args.no_oracle)
    if args.json:
        print(compact(report))
    else:
        print("CParagraphe Owner Structure (analyzer only)")
        for row in report["fixture_results"]:
            structural = row.get("structural")
            if structural:
                print(f"{row['fixture']}: source-chain hypothesis={structural['hypotheses'][0]['possible_chain_indices']} "
                      f"oracle={row['oracle']}")
        print("Hypotheses:", compact(report["hypothesis_summary"]))
        print("Adjacency:", compact(report["adjacency_summary"]))
        print("Oracle:", compact(report["oracle_summary"]))
        print(report["answers"]["conclusion"])
        for warning in report["warnings"]:
            print("Warning:", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
