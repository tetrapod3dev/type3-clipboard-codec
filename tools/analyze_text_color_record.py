"""Phase 1 text color field evidence; no color or anchor ownership assignment."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes  # noqa: E402
from type3_clipboard_codec.models.colors import TYPE3_COLORS_BY_RAW, TYPE3_COLORS_BY_RGB0_RAW, TYPE3_PALETTE  # noqa: E402
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser  # noqa: E402

TEXT_DIR = ROOT / "tests/samples/text"
INTENT_DIR = ROOT / "tests/samples/intents/text"
FIXTURES = (
    "default_text.txt", "text_color_army_green.txt", "text_color_navy_blue.txt",
    "text_group_same_color_two_objects.txt", "text_group_mixed_color_two_objects.txt",
    "text_two_objects_same_color_not_grouped.txt", "text_two_objects_mixed_color_not_grouped.txt",
    "text_two_objects_not_grouped_selection_reversed.txt", "text_three_objects_grouped_order_abc.txt",
    "text_three_objects_grouped_order_abc_mixed_color.txt", "text_three_objects_not_grouped.txt",
    "text_three_objects_not_grouped_mixed_color.txt", "text_height_30mm.txt", "text_width_50_percent.txt",
)
START, STRIDE = 47, 204
OFFSETS = tuple(range(0x83, 0x96))
FOCUS = (0x8B, 0x8C, 0x8D)
TYPES = (("u8", 1, "little"), ("u16le", 2, "little"), ("u32le", 4, "little"), ("u32be", 4, "big"))
BGR0 = {}
for _color in TYPE3_PALETTE:
    BGR0.setdefault(int(_color.hex_rgb, 16), _color)
PALETTES = {"TYPE3_RAW_GBR0": TYPE3_COLORS_BY_RAW, "RGB0": TYPE3_COLORS_BY_RGB0_RAW, "BGR0": BGR0}
SPECS = [(off, typ, encoding) for off in OFFSETS for typ, _, _ in TYPES for encoding in PALETTES]
CP_OFFSETS = tuple(range(24, 31))
MAX_RECORDS, MAX_SECTIONS, MAX_NODES, MAX_FIXTURES = 24, 16, 32, 16
POLICY = {"scope": "text_color_field_decoding_analysis_only", "parser_behavior": "not_modified",
          "decoder_behavior": "not_modified", "model_behavior": "not_modified",
          "color_ownership_assignment": "not_performed", "anchor_ownership_used": False,
          "mfc_parser_refactor": "not_performed", "oracle_isolation": True}


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def distribution(values):
    return dict(sorted(Counter(str(v) for v in values).items()))


def color_name(raw, encoding):
    color = PALETTES[encoding].get(raw)
    return color.name if color else None


def structural_phase(blob):
    """No fixture name, expected colors, intent, parsed chains, or anchors enter here."""
    if len(blob) > 1024 * 1024:
        raise ValueError("payload input budget exceeded")
    parser = Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    nodes = parser._extract_nodes(blob[origin:])
    records, descriptors, sections = [], [], []
    truncated = len(nodes) > MAX_NODES
    paragraphs = []
    for ni, node in enumerate(nodes[:MAX_NODES]):
        kind = node.header.class_name
        if kind not in ("CParagraphe", "CPropertyExtend"):
            continue
        desc_start, payload_start = origin + node.start_offset, origin + node.payload_offset
        desc = {"node_ordinal": ni, "runtime_descriptor_start": desc_start,
                "runtime_descriptor_schema": int.from_bytes(blob[desc_start+2:desc_start+4], "little"),
                "runtime_class_name": kind, "class_payload_start": payload_start,
                "payload_length": len(node.payload), "absolute_offset_role": "diagnostic_only",
                "semantic_object_boundary": False}
        descriptors.append(desc)
        data = node.payload
        if kind == "CParagraphe":
            available = max(0, (len(data) - START) // STRIDE)
            count = min(available, MAX_RECORDS)
            truncated |= available > MAX_RECORDS
            paragraphs.append({"node_ordinal": ni, "candidate_record_count": available,
                               "reported_record_count": count, "payload_length": len(data),
                               "unmodeled_prefix_bytes": min(START, len(data)),
                               "trailing_bytes_after_full_chunks": max(0, len(data)-START) % STRIDE,
                               "validation": "full 204-byte chunk only; uniform semantic record type not established"})
            for ri in range(count):
                pos = START + ri * STRIDE
                rec = data[pos:pos+STRIDE]
                values = [int.from_bytes(rec[off:off+width], order) for off in OFFSETS for _, width, order in TYPES]
                records.append({"descriptor": desc, "record_ordinal": ri,
                                "class_payload_relative_record_start": pos, "values": values})
        else:
            # A textual section frame, not a TYPE3 object or anchor-record classifier.
            starts, cursor = [], 0
            while len(starts) <= MAX_SECTIONS:
                pos = data.find(b"CObDao", cursor)
                if pos < 0:
                    break
                cursor = pos + 6
                markers = (b"OBJETINFOS_CLASSNAME", b"OBJECTINFOS_CLASSNAME")
                if pos >= 4 and data[pos-4:pos] == b"\x06\0\0\0" and any(
                    pos >= len(m)+8 and data[pos-4-len(m):pos-4] == m
                    and int.from_bytes(data[pos-8-len(m):pos-4-len(m)], "little") == len(m) for m in markers
                ):
                    starts.append(pos)
            truncated |= len(starts) > MAX_SECTIONS
            for si, pos in enumerate(starts[:MAX_SECTIONS]):
                end = starts[si+1] - 28 if si+1 < len(starts) else len(data)
                fields = [int.from_bytes(data[pos+off:pos+off+4], "little") if pos+off+4 <= end else None
                          for off in CP_OFFSETS]
                sections.append({"node_ordinal": ni, "local_section_ordinal": si,
                                 "class_payload_relative_section_start": pos, "values": fields})
    return {"descriptors": descriptors, "records": records, "paragraphs": paragraphs,
            "sections": sections, "truncated": truncated}


def candidate_values(structure, spec):
    off, typ, _ = spec
    index = OFFSETS.index(off) * len(TYPES) + [t[0] for t in TYPES].index(typ)
    return [rec["values"][index] for rec in structure["records"]]


def statistics(values, encoding):
    colors = [color_name(v, encoding) for v in values]
    return {"raw": distribution(f"0x{v:08X}" for v in values),
            "colors": distribution(c for c in colors if c is not None),
            "valid": len(values), "decodable": sum(c is not None for c in colors),
            "nonzero": sum(v != 0 and c is not None for v, c in zip(values, colors)),
            "distinct_nonzero": len({v for v, c in zip(values, colors) if v and c is not None})}


def structural_candidates(structures):
    candidates = []
    for spec in SPECS:
        values = [v for s in structures for v in candidate_values(s, spec)]
        stats = statistics(values, spec[2])
        coverage = sum(any(v != 0 and color_name(v, spec[2]) is not None for v in candidate_values(s, spec)) for s in structures)
        status = ("strong_candidate" if stats["distinct_nonzero"] >= 2 and coverage >= 3 else
                  "cross_fixture_candidate" if stats["nonzero"] and coverage >= 2 else
                  "weak_candidate" if stats["decodable"] else "unresolved")
        candidates.append({"spec": spec, **stats, "fixture_nonzero_coverage": coverage, "status": status})
    eligible = [i for i, c in enumerate(candidates) if c["spec"][1] != "u32be" and c["nonzero"]]
    scores = {i: (candidates[i]["nonzero"], candidates[i]["distinct_nonzero"], candidates[i]["fixture_nonzero_coverage"]) for i in eligible}
    best = [i for i in eligible if scores[i] == max(scores.values())] if scores else []
    return candidates, best


def public_structure(structure, best_spec):
    # Compact, explicit column tables preserve every provenance field per record.
    columns = ["runtime_descriptor_start", "runtime_descriptor_schema", "runtime_class_name", "class_payload_start",
               "class_payload_relative_record_start", "record_relative_color_offset", "record_ordinal",
               "raw_u32le_at_8B_8C_8D", "selected_raw_value", "decoded_palette_candidate"]
    selected = candidate_values(structure, best_spec) if best_spec else [None] * len(structure["records"])
    rows = []
    for rec, raw in zip(structure["records"], selected):
        d = rec["descriptor"]
        rows.append([d["runtime_descriptor_start"], d["runtime_descriptor_schema"], d["runtime_class_name"],
                     d["class_payload_start"], rec["class_payload_relative_record_start"], best_spec[0] if best_spec else None,
                     rec["record_ordinal"], [rec["values"][OFFSETS.index(off)*4+2] for off in FOCUS],
                     raw, color_name(raw, best_spec[2]) if best_spec else None])
    cp_rows = []
    for section in structure["sections"]:
        for off, raw in zip(CP_OFFSETS, section["values"]):
            if off != 30:
                continue  # all seven positions remain in the aggregate field inventory
            cp_rows.append([section["node_ordinal"], section["local_section_ordinal"],
                section["class_payload_relative_section_start"], off, raw,
                [color_name(raw, enc) for enc in PALETTES], raw in selected if raw is not None else False,
                section["values"]])
    return {"runtime_descriptor_provenance": structure["descriptors"], "paragraphs": structure["paragraphs"],
            "records": {"columns": columns, "rows": rows},
            "cpropertyextend": {"columns": ["node_ordinal", "local_section_ordinal", "class_payload_relative_section_start",
                "local_field_relative_candidate_offset", "raw_u32le", "palette_candidates_TYPE3_RAW_RGB0_BGR0",
                "same_raw_value_in_cparagraphe", "bounded_probe_u32le_at_24_to_30"], "rows": cp_rows},
            "truncated": structure["truncated"]}


def load_oracle(fixture):
    """Reporting only. Read capture color multisets, never object/anchor identity."""
    primary = {"default_text.txt": "Black", "text_color_army_green.txt": "Army Green", "text_color_navy_blue.txt": "Navy Blue"}
    if fixture in primary:
        return {"colors": {primary[fixture]: 1}, "object_count": 1, "grouping": "single",
                "source": "task single-object capture controls"}
    path = INTENT_DIR / (Path(fixture).stem + ".md")
    if not path.exists():
        return None
    # Stop before generated parser observations, and load only the reporting header.
    with path.open(encoding="utf-8") as stream:
        header = stream.read(12000).split("## Parser observation", 1)[0].split("## Order / ownership metadata", 1)[0]
    block = re.search(r"```yaml\s*(.*?)```", header, re.S)
    metadata = {}
    if block:
        import yaml
        metadata = (yaml.safe_load(block.group(1)) or {}).get("intent_metadata", {})
    count = metadata.get("object_count")
    colors = [e.get("color") for e in metadata.get("attempted_selection_order", []) if e.get("color")]
    # Only color frequencies survive: discard labels, anchors and attempted order.
    if not colors and count:
        color_line = re.search(r"^- color:\s*(.+)$", header, re.M)
        description = re.search(r"^- description:\s*(.+)$", header, re.M)
        text = color_line.group(1) if color_line else description.group(1) if description else ""
        names = [n for n in sorted({c.name for c in TYPE3_PALETTE}, key=len, reverse=True) if n in text]
        # Avoid the shorter Green/Blue names embedded in Army Green/Navy Blue.
        names = [n for n in names if not any(n != other and n in other for other in names)]
        if len(names) == 1:
            colors = names * count
        elif len(names) == count:
            colors = names
    if not count or len(colors) != count:
        return None
    return {"colors": distribution(colors), "object_count": count,
            "grouping": metadata.get("grouping", "unknown"), "source": "capture intent color multiset only"}


def compare_multiset(observed, expected):
    return {"unordered_color_multiset_match": observed == expected,
            "expected_color_presence": set(expected).issubset(observed),
            "observed_record_color_multiset": observed, "expected_object_color_multiset": expected,
            "ownership_inferred": False}


def finish_report(prepared, oracle_enabled=True, warnings=None):
    names = [p[0] for p in prepared]
    structures = [json.loads(p[1]) for p in prepared]
    candidates, best_ids = structural_candidates(structures)
    best_spec = candidates[best_ids[0]]["spec"] if len(best_ids) == 1 else None
    # Finish all structural reporting and selection before loading any oracle.
    public_frozen = compact([public_structure(s, best_spec) for s in structures])
    candidates_frozen = compact(candidates)
    candidates = json.loads(candidates_frozen)
    oracles = [load_oracle(name) for name in names] if oracle_enabled else [None] * len(names)
    pool, pool_index = [], {}
    oracle_pool, oracle_pool_index = [], {}

    def intern(value):
        key = compact(value)
        if key not in pool_index:
            pool_index[key] = len(pool)
            pool.append(value)
        return pool_index[key]

    def intern_oracle(value):
        key = compact(value)
        if key not in oracle_pool_index:
            oracle_pool_index[key] = len(oracle_pool)
            oracle_pool.append(value)
        return oracle_pool_index[key]

    table, oracle_rows = [], []
    for ci, candidate in enumerate(candidates):
        spec = candidate["spec"]
        table.append([spec[0], spec[1], spec[2], candidate["valid"], candidate["decodable"],
            intern(candidate["raw"]), intern(candidate["colors"]), candidate["nonzero"],
            candidate["distinct_nonzero"], candidate["fixture_nonzero_coverage"], candidate["status"]])
        stats = [statistics(candidate_values(s, spec), spec[2]) for s in structures]
        primary_results = []
        for primary in FIXTURES[:3]:
            if not oracle_enabled or primary not in names:
                primary_results.append(None)
                continue
            i = names.index(primary)
            expected = oracles[i]["colors"] if oracles[i] else {}
            primary_results.append({"raw_values": stats[i]["raw"], "decoded_colors": stats[i]["colors"],
                                    "expected_color_only_among_decodable": set(stats[i]["colors"]) == set(expected),
                                    "unmapped_chunks": stats[i]["valid"] - stats[i]["decodable"]})
        separation = all(r and r["expected_color_only_among_decodable"] for r in primary_results) if oracle_enabled and all(primary_results) else None
        same = [i for i, o in enumerate(oracles) if o and o["object_count"] > 1 and len(o["colors"]) == 1]
        mixed = [i for i, o in enumerate(oracles) if o and len(o["colors"]) > 1]
        repeat = {"eligible": len(same), "repeated_expected_color": sum(any(stats[i]["colors"].get(c, 0) > 1 for c in oracles[i]["colors"]) for i in same)} if oracle_enabled else None
        presence = {"eligible": len(mixed), "all_expected_colors_present": sum(set(oracles[i]["colors"]).issubset(stats[i]["colors"]) for i in mixed)} if oracle_enabled else None
        controls = [n for n in ("text_height_30mm.txt", "text_width_50_percent.txt") if n in names]
        stability = {"controls": len(controls), "same_decoded_distribution": sum(stats[names.index(n)]["colors"] == stats[names.index("default_text.txt")]["colors"] for n in controls)} if oracle_enabled and "default_text.txt" in names else None
        oracle_rows.append([ci, *[intern_oracle([r[k] for k in ("raw_values", "decoded_colors", "expected_color_only_among_decodable", "unmapped_chunks")] if r else None) for r in primary_results], separation,
                            intern_oracle(repeat), intern_oracle(presence), intern_oracle(stability)])
    best_stats = [statistics(candidate_values(s, best_spec), best_spec[2]) if best_spec else None for s in structures]
    fixture_results = []
    for i, (name, s, public) in enumerate(zip(names, structures, json.loads(public_frozen))):
        cp_colors = Counter()
        for section in s["sections"]:
            raw = section["values"][CP_OFFSETS.index(30)]
            if color_name(raw, "RGB0") is not None:
                cp_colors[color_name(raw, "RGB0")] += 1
        observed = best_stats[i]["colors"] if best_stats[i] else {}
        combined = dict(Counter(observed) + cp_colors)
        oracle = oracles[i]
        fixture_results.append({"fixture": name, "structural": public,
            "color_observations": {"CParagraphe": best_stats[i], "CPropertyExtend_local_30_RGB0": dict(cp_colors),
                                   "location_distribution": {"CParagraphe_chunks": len(s["records"]), "CPropertyExtend_sections": len(s["sections"])},
                                   "duplicates_are_record_observations_not_objects": True},
            "oracle": oracle, "comparison": {"CParagraphe": compare_multiset(observed, oracle["colors"]),
                "combined_presence_control": compare_multiset(combined, oracle["colors"])} if oracle else None})
    contrasts = []
    if oracle_enabled:
        pairs = [("text_group_same_color_two_objects.txt", "text_group_mixed_color_two_objects.txt"),
                 ("text_group_mixed_color_two_objects.txt", "text_two_objects_mixed_color_not_grouped.txt"),
                 ("text_three_objects_grouped_order_abc.txt", "text_three_objects_grouped_order_abc_mixed_color.txt"),
                 ("text_three_objects_not_grouped.txt", "text_three_objects_not_grouped_mixed_color.txt")]
        for left, right in pairs:
            if left in names and right in names and best_spec:
                li, ri = names.index(left), names.index(right)
                lv, rv = candidate_values(structures[li], best_spec), candidate_values(structures[ri], best_spec)
                contrasts.append({"fixtures": [left, right], "record_counts": [len(lv), len(rv)],
                    "changed_traversal_slots": [j for j, (a, b) in enumerate(zip(lv, rv)) if a != b] if len(lv) == len(rv) else None,
                    "record_traversal_orders": [list(range(len(lv))), list(range(len(rv)))],
                    "distinct_raw_counts": [len(set(lv)), len(set(rv))],
                    "duplicate_raw_observation_counts": [len(lv)-len(set(lv)), len(rv)-len(set(rv))],
                    "decoded_color_multisets": [best_stats[li]["colors"], best_stats[ri]["colors"]],
                    "alignment_basis": "same ordinal only for equal chunk counts; not semantic object alignment"})
    chosen_oracle = oracle_rows[best_ids[0]] if len(best_ids) == 1 else None
    separation = chosen_oracle[4] if chosen_oracle else None
    field_columns = ["record_relative_offset", "decode_type", "palette_encoding", "valid_record_count", "palette_decodable_count",
                     "raw_value_distribution_ref", "decoded_color_distribution_ref", "nonzero_palette_count",
                     "distinct_nonzero_color_count", "nonzero_fixture_count", "status"]
    report = {
        "mode": "text_color_record_phase1", "policy": POLICY.copy(),
        "limits": {"max_fixtures": MAX_FIXTURES, "max_nodes": MAX_NODES, "max_records_per_paragraph": MAX_RECORDS,
            "max_sections_per_cpropertyextend": MAX_SECTIONS, "scan_start": 0x83, "scan_end_inclusive": 0x95,
            "cpropertyextend_local_offsets": list(CP_OFFSETS), "json_bytes": 100000, "text_bytes": 50000},
        "warnings": list(warnings or []) + [f"bounded structural inventory: {n}" for n, s in zip(names, structures) if s["truncated"]],
        "fixture_results": fixture_results,
        "runtime_descriptor_provenance": {"location": "fixture_results.structural.runtime_descriptor_provenance",
            "schema_values": sorted({d["runtime_descriptor_schema"] for s in structures for d in s["descriptors"] if d["runtime_class_name"] == "CParagraphe"}),
            "schema_color_relationship": "no evidence; class-level version metadata candidate only",
            "descriptor_is_semantic_object_boundary": False},
        "field_start_summary": {"columns": field_columns, "rows": table,
            "distribution_pool": pool, "pool_reference_semantics": "zero-based index in this structural distribution pool",
            "selection": {"best_candidate_indices": best_ids,
                "rule": "maximize nonzero palette count, distinct nonzero colors, nonzero fixture coverage; ties abstain",
                "u32be_role": "comparison_only, excluded from primary selection before oracle",
                "expected_colors_used": False},
            "palette_encoding_definitions": {"TYPE3_RAW_GBR0": "existing raw table: G B R 00 bytes, not BGR0",
                "RGB0": "R G B 00 bytes; u32le 0x00BBGGRR", "BGR0": "B G R 00 bytes; u32le 0x00RRGGBB; derived from existing hex_rgb palette"}},
        "color_record_summary": {"candidate_record_count": sum(len(s["records"]) for s in structures),
            "best_candidate_statistics": {k: v for k, v in candidates[best_ids[0]].items() if k != "spec"} if len(best_ids) == 1 else None,
            "count_interpretation": "palette matches include zero/padding; copies are not object counts"},
        "cparagraphe_summary": {"record_start": START, "stride": STRIDE,
            "record_model": "provisional full-fit chunks; header/tail chunks may not share interior record semantics",
            "validity_does_not_use_color": True},
        "cpropertyextend_summary": {"section_framing": "length-prefixed OBJECTINFOS/OBJETINFOS name followed by length 6 and CObDao; no anchor signature",
            "fields": [{"local_field_relative_candidate_offset": off,
                "raw_value_distribution": distribution(f"0x{raw:08X}" if raw is not None else "unavailable" for s in structures for sec in s["sections"] for k, raw in zip(CP_OFFSETS, sec["values"]) if k == off)} for off in CP_OFFSETS],
            "local_30_role": "bounded side-evidence probe, not a stable field or ownership selector",
            "status": "no_stable_cpropertyextend_color_field_found"},
        "oracle_summary": {"enabled": oracle_enabled, "available_fixtures": sum(o is not None for o in oracles),
            "result_pool": oracle_pool,
            "primary_result_columns": ["raw_values", "decoded_colors", "expected_color_only_among_decodable", "unmapped_chunks"],
            "candidate_columns": ["candidate_index", "single_object_black_result_ref", "single_object_army_green_result_ref",
                "single_object_navy_blue_result_ref", "single_object_separation", "same_color_repeatability_ref", "mixed_color_presence_ref", "unrelated_fixture_stability_ref"],
            "candidate_rows": oracle_rows, "contrasts": contrasts,
            "scaling_columns": ["fixture_index", "object_intent_color_count", "grouping", "candidate_chunk_count",
                "palette_bearing_chunk_count", "unique_decoded_colors", "duplicate_raw_observations", "cpropertyextend_section_count"],
            "scaling_rows": [[i, o["object_count"], o["grouping"], best_stats[i]["valid"], best_stats[i]["decodable"],
                len(best_stats[i]["colors"]), best_stats[i]["valid"]-len(best_stats[i]["raw"]), len(structures[i]["sections"])]
                for i, o in enumerate(oracles) if o and o["object_count"] > 1 and best_stats[i]],
            "note": "multiset cardinality preserved; presence is separate, no deduplication into object counts"},
        "answers": {"best_color_field_start": best_spec[0] if best_spec else None,
            "best_decode_type": best_spec[1] if best_spec else None, "best_palette_encoding": best_spec[2] if best_spec else None,
            "single_object_separation_status": "separated_with_unmapped_chunks" if separation else "unavailable" if separation is None else "not_separated",
            "multi_object_color_presence_status": "see unordered presence and strict multiset comparisons; not ownership" if oracle_enabled else "oracle_disabled",
            "primary_color_evidence_class": "CParagraphe" if best_spec else "unresolved",
            "cpropertyextend_color_status": "no_stable_cpropertyextend_color_field_found",
            "mfc_framing_effect": "provenance improvement only; field stays payload/record relative; schema is not color",
            "field_decode_readiness": "strong_candidate_analyzer_only" if best_spec and candidates[best_ids[0]]["status"] == "strong_candidate" else "unresolved",
            "color_ownership_readiness": "not_ready"},
    }
    return report


def build_report(fixtures=None, oracle_enabled=True):
    names = list(dict.fromkeys(FIXTURES if fixtures is None else fixtures))
    if len(names) > MAX_FIXTURES:
        raise ValueError("fixture count exceeds bounded limit of 16")
    prepared, warnings = [], []
    for name in names:
        path = (TEXT_DIR / name).resolve()
        if not path.is_relative_to(TEXT_DIR.resolve()) or not path.is_file():
            warnings.append(f"missing fixture: {name}")
            continue
        if path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("fixture text exceeds input budget")
        blob = hex_text_to_bytes(path.read_text(encoding="utf-8-sig"))
        prepared.append((name, compact(structural_phase(blob))))
    return finish_report(prepared, oracle_enabled, warnings)


def render_text(report, markdown=False):
    lines = [("# " if markdown else "") + "Text Color Record - Phase 1", "",
             f"Fixtures: {len(report['fixture_results'])}; provisional chunks: {report['color_record_summary']['candidate_record_count']}",
             "Selection: " + compact(report["answers"]), "",
             "| Fixture | chunks | decoded CParagraphe multiset | CPropertyExtend local +30 RGB0 |" if markdown else
             "Fixture | chunks | decoded CParagraphe multiset | CPropertyExtend local +30 RGB0"]
    if markdown:
        lines.append("| --- | ---: | --- | --- |")
    for result in report["fixture_results"]:
        obs = result["color_observations"]
        row = (f"{result['fixture']} | {obs['location_distribution']['CParagraphe_chunks']} | "
               f"{compact(obs['CParagraphe']['colors'] if obs['CParagraphe'] else {})} | {compact(obs['CPropertyExtend_local_30_RGB0'])}")
        lines.append("| " + row + " |" if markdown else row)
    lines += ["", "Primary oracle and contrasts are diagnostics only. No ownership is assigned.",
              "The 0x8A/u32be/BGR0 comparison may share color evidence with 0x8B/u32le/RGB0; byte order role is predefined.",
              "Chunks are full-fit, not verified uniform semantic records. Zero/padding palette matches are retained.",
              "Warnings: " + compact(report["warnings"])]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true")
    mode.add_argument("--markdown", action="store_true")
    parser.add_argument("--fixture", action="append")
    parser.add_argument("--no-oracle", action="store_true")
    args = parser.parse_args()
    report = build_report(args.fixture, not args.no_oracle)
    output = compact(report) if args.json else render_text(report, args.markdown)
    if len(output.encode("utf-8")) + 2 >= (100000 if args.json else 50000):
        parser.error("output budget exceeded")
    print(output)


if __name__ == "__main__":
    main()
