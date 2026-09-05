"""Color Phase 1B: bounded byte deltas and provisional chunk roles, without ownership."""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_color_record as color  # noqa: E402

TEXT_DIR = color.TEXT_DIR
PRIMARY = ("default_text.txt", "text_color_army_green.txt", "text_color_navy_blue.txt")
FIXTURES = PRIMARY + (
    "text_group_same_color_two_objects.txt", "text_group_mixed_color_two_objects.txt",
    "text_two_objects_same_color_not_grouped.txt", "text_two_objects_mixed_color_not_grouped.txt",
    "text_three_objects_grouped_order_abc.txt", "text_three_objects_grouped_order_abc_mixed_color.txt",
    "text_three_objects_not_grouped.txt", "text_three_objects_not_grouped_mixed_color.txt",
)
START, STRIDE = 47, 204
WINDOW_START, WINDOW_END = 0x80, 0x99  # end exclusive
MAX_RECORDS, MAX_SECTIONS, MAX_NODES = 24, 16, 32
VIEWS = [(off, order) for off in (0x8A, 0x8B, 0x8C) for order in ("little", "big")]
POLICY = {"scope": "text_color_field_boundary_analysis_only", "parser_behavior": "not_modified",
          "ownership_assignment": "not_performed", "anchor_ownership_used": False,
          "mfc_refactor": "not_performed", "oracle_isolation": True}
compact = color.compact


def runs(positions):
    result = []
    for pos in sorted(positions):
        if not result or pos != result[-1][1] + 1:
            result.append([pos, pos])
        else:
            result[-1][1] = pos
    return result


def extract_structure(blob):
    """Only window bytes and preexisting fixed marker checks; no fixture/intent input."""
    if len(blob) > 1024 * 1024:
        raise ValueError("input payload budget exceeded")
    parser = color.Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    nodes = parser._extract_nodes(blob[origin:])
    paragraphs, side = [], []
    truncated = len(nodes) > MAX_NODES
    for ni, node in enumerate(nodes[:MAX_NODES]):
        data = node.payload
        if node.header.class_name == "CParagraphe":
            count = max(0, (len(data) - START) // STRIDE)
            truncated |= count > MAX_RECORDS
            records = []
            for ri in range(min(count, MAX_RECORDS)):
                pos = START + STRIDE * ri
                # Context already observed in Phase 1's first chunk. No marker search
                # or byte-delta/palette scan outside 80..98 is performed.
                marker = (data[pos+53:pos+73] == b"OBJETINFOS_CLASSNAME"
                          and data[pos+73:pos+77] == b"\x06\0\0\0"
                          and data[pos+77:pos+83] == b"CObDao")
                records.append({"record_ordinal": ri, "payload_relative_start": pos,
                                "window": list(data[pos+WINDOW_START:pos+WINDOW_END]),
                                "prior_fixed_marker_context": marker})
            desc = origin + node.start_offset
            paragraphs.append({"node_ordinal": ni, "runtime_descriptor_start": desc,
                "runtime_descriptor_schema": int.from_bytes(blob[desc+2:desc+4], "little"),
                "runtime_class_name": "CParagraphe", "class_payload_start": origin + node.payload_offset,
                "payload_length": len(data), "candidate_chunk_count": count,
                "trailing_bytes": max(0, len(data)-START) % STRIDE, "records": records})
        elif node.header.class_name == "CPropertyExtend":
            cursor, section = 0, 0
            while section <= MAX_SECTIONS:
                pos = data.find(b"CObDao", cursor)
                if pos < 0:
                    break
                cursor = pos + 6
                marker = next((m for m in (b"OBJETINFOS_CLASSNAME", b"OBJECTINFOS_CLASSNAME")
                    if pos >= len(m)+8 and data[pos-4:pos] == b"\x06\0\0\0"
                    and data[pos-4-len(m):pos-4] == m
                    and int.from_bytes(data[pos-8-len(m):pos-4-len(m)], "little") == len(m)), None)
                if marker is None:
                    continue
                if section == MAX_SECTIONS:
                    truncated = True
                    break
                raw = int.from_bytes(data[pos+30:pos+34], "little") if pos+34 <= len(data) else None
                side.append({"node_ordinal": ni, "section_ordinal": section,
                    "payload_relative_section_start": pos, "field_relative_offset": 30, "raw_u32le": raw,
                    "RGB0_palette_candidate": color.color_name(raw, "RGB0"),
                    "structural_role": "textual_marker_section_only"})
                section += 1
    return {"paragraphs": paragraphs, "cproperty_side": side, "truncated": truncated}


def only_records(structure):
    # Do not concatenate or align multiple paragraphs as though one record array.
    return structure["paragraphs"][0]["records"] if len(structure["paragraphs"]) == 1 else []


def delta_analysis(primaries):
    arrays = [only_records(s) for s in primaries]
    aligned = len(arrays) == 3 and bool(arrays[0]) and len({len(a) for a in arrays}) == 1
    if not aligned or any(s["truncated"] for s in primaries):
        return {"aligned": False, "ordinals": [], "dominant_changed_span": None, "reason": "requires three complete equal-length single-paragraph inventories"}
    ordinals, signatures = [], Counter()
    for ri, triple in enumerate(zip(*arrays)):
        comparisons = []
        for a, b in combinations(range(3), 2):
            changed = [WINDOW_START+i for i, (left, right) in enumerate(zip(triple[a]["window"], triple[b]["window"])) if left != right]
            comparisons.append({"control_pair": [a, b], "changed_byte_positions": changed, "changed_contiguous_runs": runs(changed)})
        patterns = [tuple(c["changed_byte_positions"]) for c in comparisons]
        eligible = (bool(patterns[0]) and len(set(patterns)) == 1 and len(runs(patterns[0])) == 1
                    and not any(r["prior_fixed_marker_context"] for r in triple))
        if eligible:
            signatures[patterns[0]] += 1
        ordinals.append({"record_ordinal": ri, "comparisons": comparisons,
                         "same_ordinal_window_stable_across_three": not any(patterns),
                         "consistent_contiguous_delta": eligible})
    maximum = max(signatures.values(), default=0)
    winners = [sig for sig, n in signatures.items() if n == maximum and n >= 2]
    span = [winners[0][0], winners[0][-1]] if len(winners) == 1 else None
    return {"aligned": True, "ordinals": ordinals, "dominant_changed_span": span,
            "selection_rule": "unique most repeated contiguous changed-byte pattern across all three pairwise comparisons; fixed-marker chunks excluded; no palette input"}


def masked(window, span):
    return tuple(v for i, v in enumerate(window, WINDOW_START) if span is None or not span[0] <= i <= span[1])


def structural_report(prepared):
    names = [p[0] for p in prepared]
    inventories = [json.loads(p[1]) for p in prepared]
    primaries = [inventories[names.index(n)] for n in PRIMARY if n in names]
    delta = delta_analysis(primaries)
    delta["control_fixtures"] = [n for n in PRIMARY if n in names]
    span = delta["dominant_changed_span"]
    supported = [r["record_ordinal"] for r in delta["ordinals"] if span and all(
        c["changed_byte_positions"] == list(range(span[0], span[1]+1)) for c in r["comparisons"])]
    template = masked(only_records(primaries[0])[supported[0]]["window"], span) if supported else None
    delta_by_ordinal = {r["record_ordinal"]: r for r in delta["ordinals"]}
    neighbor = {}
    if span and supported:
        for pos in (span[0]-1, span[1]+1):
            if not WINDOW_START <= pos < WINDOW_END:
                neighbor[f"0x{pos:02X}"] = {"values": {}, "stable": None, "reason": "outside tested window"}
                continue
            values = [only_records(s)[ri]["window"][pos-WINDOW_START] for s in primaries for ri in supported]
            neighbor[f"0x{pos:02X}"] = {"values": dict(Counter(str(v) for v in values)), "stable": len(set(values)) == 1}
    boundary = {"start": span[0] if span else None, "width": None,
        "observed_changed_width": span[1]-span[0]+1 if span else None,
        "changed_byte_support": {"primary_record_ordinals": supported, "pair_comparisons": len(supported)*3},
        "neighbor_stability": neighbor, "scope": "variable byte span in repeated local-context chunks, not proven typed field extent",
        "status": "changed_byte_span_supported_storage_width_unresolved" if span else "unresolved"}
    hypotheses = []
    for name, start, width, definition in (
        ("H1", 0x8B, 4, "u32le RGB0, including trailing zero"),
        ("H2", 0x8B, 3, "RGB bytes with adjacent trailing zero/padding"),
        ("H3", 0x8A, 4, "big-endian/BGR0-like field including leading zero"),
        ("H4", None, None, "window coincidence or typed field boundary unresolved"),
    ):
        compatible = bool(span and start is not None and start <= span[0] and span[1] < start+width)
        hypotheses.append({"name": name, "start": start, "width": width, "definition": definition,
            "changed_byte_support": len(supported)*3 if compatible else 0,
            "status": "compatible_not_distinguished" if compatible else "viable_typed_boundary_null" if name == "H4" else "unresolved",
            "analyzer_only": True, "typed_boundary_established": False})
    results, role_summaries, alignment, side_reports = [], [], [], []
    for name, structure in zip(names, inventories):
        records = only_records(structure)
        body = [r["record_ordinal"] for r in records if template is not None and not r["prior_fixed_marker_context"] and masked(r["window"], span) == template]
        rows = []
        for rec in records:
            ri, window = rec["record_ordinal"], rec["window"]
            primary_delta = delta_by_ordinal.get(ri) if name in PRIMARY else None
            if rec["prior_fixed_marker_context"]:
                role = "header_like_chunk"
            elif ri in body:
                role = "repeated_color_record_candidate"
            elif body and ri > max(body):
                role = "tail_like_chunk"
            elif primary_delta and primary_delta["same_ordinal_window_stable_across_three"]:
                role = "invariant_chunk"
            else:
                role = "unresolved"
            values = [int.from_bytes(bytes(window[off-WINDOW_START:off-WINDOW_START+4]), order) for off, order in VIEWS]
            palettes = [[color.color_name(v, enc) for enc in color.PALETTES] for v in values]
            rgb = bytes(window[0x8B-WINDOW_START:0x8E-WINDOW_START])
            rgb_name = color.color_name(int.from_bytes(rgb + b"\0", "little"), "RGB0")
            le = values[VIEWS.index((0x8B, "little"))]
            changes = sorted({p for c in primary_delta["comparisons"] for p in c["changed_byte_positions"]}) if primary_delta else None
            rows.append({"record_ordinal": ri, "payload_relative_record_start": rec["payload_relative_start"],
                "bytes_89_to_90": bytes(window[0x89-WINDOW_START:0x91-WINDOW_START]).hex(),
                "candidate_RGB_bytes": rgb.hex(), "RGB_palette_candidate": rgb_name,
                "u32_values": values, "palette_views": palettes,
                "role": role, "prior_marker_context": {"OBJETINFOS_CLASSNAME": 53, "CObDao": 77} if rec["prior_fixed_marker_context"] else {},
                "participates_in_control_delta": bool(changes) if changes is not None else None,
                "same_ordinal_window_stable_across_primary": primary_delta["same_ordinal_window_stable_across_three"] if primary_delta else None,
                "bounded_window_identical_except_changed_span": set(changes).issubset(range(span[0], span[1]+1)) if changes is not None and span else None,
                "record_identical_except_color_bytes": None,
                "u32le_8B_palette_candidate": color.color_name(le, "RGB0")})
        descriptors = [{k: v for k, v in p.items() if k != "records"} for p in structure["paragraphs"]]
        results.append({"fixture": name, "structural": {"provenance": descriptors,
            "chunks": {"columns": list(rows[0]) if rows else [], "rows": [list(r.values()) for r in rows]},
            "truncated": structure["truncated"], "multiple_paragraph_alignment_abstained": len(structure["paragraphs"]) > 1}})
        roles = {role: [r["record_ordinal"] for r in rows if r["role"] == role] for role in sorted({r["role"] for r in rows})}
        role_summaries.append({"fixture": name, "roles": roles,
            "u32le_8B_palette_nonmatching_ordinals": [r["record_ordinal"] for r in rows if r["u32le_8B_palette_candidate"] is None],
            "RGB_three_byte_nonmatching_ordinals": [r["record_ordinal"] for r in rows if r["RGB_palette_candidate"] is None],
            "all_roles_provisional": True})
        same_count = bool(delta["aligned"] and len(records) == len(only_records(primaries[0])))
        reference = only_records(primaries[0]) if delta["aligned"] else []
        signatures_equal = [r["record_ordinal"] for r, ref in zip(records, reference)
            if masked(r["window"], span) == masked(ref["window"], span)] if same_count and span else []
        alignment.append({"fixture": name, "chunk_count": len(records), "repeated_subranges": runs(body),
            "count_delta_vs_primary": len(records)-len(reference) if reference else None,
            "same_count_as_primary": same_count, "same_ordinal_masked_window_matches": signatures_equal,
            "repeated_signature_multiplicity": len(body), "unique_insert_delete_alignment": False,
            "interpretation": "repeated signatures prevent unique insertion/deletion placement; count delta alone is not an edit map"})
        cp_names = Counter(s["RGB0_palette_candidate"] for s in structure["cproperty_side"] if s["RGB0_palette_candidate"] is not None)
        paragraph_names = {r["u32le_8B_palette_candidate"] for r in rows if r["u32le_8B_palette_candidate"] is not None}
        side_reports.append({"fixture": name, "sections": structure["cproperty_side"],
            "palette_observations": dict(cp_names), "palette_names_not_in_cparagraphe": sorted(set(cp_names)-paragraph_names),
            "stable_color_semantic_role": False})
    return {"fixture_results": results, "byte_delta_summary": delta,
        "boundary_hypothesis_summary": {"candidate_field_boundary": boundary, "hypotheses": hypotheses},
        "chunk_role_summary": {"fixtures": role_summaries,
            "classification_basis": "fixed prior marker checks, then equality to dominant-delta masked context, then terminal position; no expected color or palette scoring",
            "whole_record_equality": "not tested; only 80..98 byte comparisons; record_identical_except_color_bytes is null"},
        "cross_fixture_alignment_summary": {"fixtures": alignment, "semantic_stored_order": "unresolved"},
        "cproperty_side_evidence": {"fixtures": side_reports, "only_field_offset": 30,
            "status": "no_stable_cpropertyextend_color_field_found"},
        "answers": {"best_field_start": span[0] if span else None, "best_field_width": None,
            "observed_variable_span_width": span[1]-span[0]+1 if span else None,
            "best_byte_order": "RGB byte sequence; integer storage byte order unresolved" if span else "unresolved",
            "best_palette_encoding": "RGB; RGB0 remains a storage candidate" if span else "unresolved",
            "neighboring_byte_stability": neighbor,
            "nonmatching_chunk_roles": "see exact ordinal distributions; header and terminal candidates, not semantic record types",
            "record_model_status": "mixed_local_chunk_roles_provisional" if supported else "unresolved",
            "field_boundary_readiness": "changed_span_supported_typed_boundary_not_ready" if supported else "unresolved",
            "candidate_parser_model_ready": False, "color_ownership_readiness": "not_ready"}}


def oracle_phase(frozen, enabled):
    """The immutable full structural report is the only analysis input here."""
    if not enabled:
        return {"enabled": False, "fixtures": []}
    structure = json.loads(frozen)
    side = {f["fixture"]: f for f in structure["cproperty_side_evidence"]["fixtures"]}
    rows = []
    for result in structure["fixture_results"]:
        fixture = result["fixture"]
        oracle = color.load_oracle(fixture)
        if oracle is None:
            rows.append({"fixture": fixture, "expected_colors": None})
            continue
        chunk_table = result["structural"]["chunks"]
        chunks = [dict(zip(chunk_table["columns"], row)) for row in chunk_table["rows"]]
        h1 = Counter(c["u32le_8B_palette_candidate"] for c in chunks if c["u32le_8B_palette_candidate"] is not None)
        h2 = Counter(c["RGB_palette_candidate"] for c in chunks if c["RGB_palette_candidate"] is not None)
        h3 = Counter(c["palette_views"][VIEWS.index((0x8A, "big"))][list(color.PALETTES).index("BGR0")]
                     for c in chunks if c["palette_views"][VIEWS.index((0x8A, "big"))][list(color.PALETTES).index("BGR0")] is not None)
        missing = set(oracle["colors"]) - set(h1)
        rows.append({"fixture": fixture, "expected_colors": oracle["colors"],
            "hypothesis_observations": {"H1": dict(h1), "H2": dict(h2), "H3": dict(h3)},
            "expected_only_among_decodable": {h: set(counts) == set(oracle["colors"]) for h, counts in (("H1", h1), ("H2", h2), ("H3", h3))},
            "mixed_intent": len(oracle["colors"]) > 1, "cproperty_covers_missing_color_names": bool(missing) and missing.issubset(side[fixture]["palette_observations"]),
            "missing_color_names_in_cparagraphe": sorted(missing),
            "no_boundary_or_role_update": True})
    return {"enabled": True, "fixtures": rows, "interpretation": "decoding consistency only; no ownership or field-width promotion"}


def build_report(fixtures=None, oracle_enabled=True):
    names = list(dict.fromkeys(FIXTURES if fixtures is None else fixtures))
    if len(names) > 16:
        raise ValueError("maximum 16 fixtures")
    prepared, warnings = [], []
    for name in names:
        path = (TEXT_DIR / name).resolve()
        if not path.is_relative_to(TEXT_DIR.resolve()) or not path.is_file():
            warnings.append(f"missing fixture: {name}")
            continue
        if path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("hex text input budget exceeded")
        blob = color.hex_text_to_bytes(path.read_text(encoding="utf-8-sig"))
        inventory = extract_structure(blob)
        if inventory["truncated"]:
            warnings.append(f"bounded inventory: {name}")
        prepared.append((name, compact(inventory)))
    frozen = compact(structural_report(prepared))
    oracle = oracle_phase(frozen, oracle_enabled)
    return {"mode": "text_color_field_boundary_phase1b", "policy": POLICY.copy(),
        "limits": {"window_start": WINDOW_START, "window_end_inclusive": WINDOW_END-1,
            "max_fixtures": 16, "max_payload_bytes": 1024 * 1024,
            "max_chunks_per_paragraph": MAX_RECORDS, "max_sections_per_node": MAX_SECTIONS, "max_nodes": MAX_NODES,
            "comparison_scope": "local window only; fixed marker checks 53/77 are context only",
            "u32_view_columns": [[off, "u32le" if order == "little" else "u32be"] for off, order in VIEWS],
            "palette_view_columns": list(color.PALETTES), "absolute_offset_role": "diagnostic_only",
            "json_bytes": 100000, "text_bytes": 50000},
        "warnings": warnings, **json.loads(frozen), "oracle_summary": oracle}


def render_text(report, markdown=False):
    boundary = report["boundary_hypothesis_summary"]["candidate_field_boundary"]
    lines = [("# " if markdown else "") + "Text Color Field Boundary - Phase 1B", "",
        f"Fixtures: {len(report['fixture_results'])}", "Boundary candidate: " + compact(boundary),
        "Hypotheses: " + compact(report["boundary_hypothesis_summary"]["hypotheses"]), "",
        "Chunk role and nonmatching ordinal inventory:"]
    lines += [compact(row) for row in report["chunk_role_summary"]["fixtures"]]
    lines += ["", "Whole-record equality outside 0x80..0x98 was not tested.",
        "Invariant leading/trailing zeros do not distinguish a 3-byte payload from either 4-byte view.",
        "Counts and repeated local signatures do not uniquely locate insertions/deletions.",
        "CPropertyExtend: no_stable_cpropertyextend_color_field_found; +30 reporting only.",
        "Readiness: " + compact(report["answers"]), "Warnings: " + compact(report["warnings"])]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    formats = parser.add_mutually_exclusive_group()
    formats.add_argument("--json", action="store_true")
    formats.add_argument("--markdown", action="store_true")
    parser.add_argument("--no-oracle", action="store_true")
    parser.add_argument("--fixture", action="append")
    args = parser.parse_args()
    report = build_report(args.fixture, not args.no_oracle)
    output = compact(report) if args.json else render_text(report, args.markdown)
    if len(output.encode("utf-8")) + 2 >= (100000 if args.json else 50000):
        parser.error("output budget exceeded")
    print(output)


if __name__ == "__main__":
    main()
