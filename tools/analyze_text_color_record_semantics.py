"""Color Phase 1C: bounded repeated-record evidence, without ownership."""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_color_field_boundary as boundary  # noqa: E402
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser  # noqa: E402

color = boundary.color
compact = color.compact
TEXT_DIR = color.TEXT_DIR
FIXTURES = tuple(dict.fromkeys(boundary.PRIMARY + (
    "text_ascii_lowercase.txt", "text_ascii_uppercase.txt", "text_digits.txt",
    "text_alphanumeric.txt", "text_spaces.txt", "text_special_characters.txt",
    "text_height_10mm.txt", "text_height_30mm.txt", "text_font_arial.txt",
    "text_font_arial_bold.txt", "text_multiline_basic.txt",
    "text_three_objects_grouped_order_abc_content_variation.txt",
) + boundary.FIXTURES[3:]))
POLICY = {"scope": "text_color_record_semantics_analysis_only",
          "parser_behavior": "not_modified", "color_ownership_assignment": "not_performed",
          "typed_color_field_promotion": "not_performed", "anchor_ownership_used": False,
          "oracle_isolation": True}
LIMITS = {"max_fixtures": 32, "max_payload_bytes": 1048576, "max_nodes": 32,
          "max_chunks_per_paragraph": 24, "max_runs_per_paragraph": 16,
          "window_start": 0x70, "window_end_inclusive": 0xA0,
          "extra_probes": "chunk prefix 0..15; existing text slot header +59..66; fixed markers +53/+77",
          "json_bytes": 180000, "text_bytes": 50000,
          "whole_record_comparison": False}


def mask(raw, start=0x70):
    return bytes(v for i, v in enumerate(raw, start) if not 0x8B <= i <= 0x8D).hex()


def extract_structure(blob):
    """No filename, palette lookup, intent, or ownership enters extraction."""
    if len(blob) > LIMITS["max_payload_bytes"]:
        raise ValueError("payload budget exceeded")
    parser = color.Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    nodes = parser._extract_nodes(blob[origin:])
    if len(nodes) > LIMITS["max_nodes"]:
        raise ValueError("node budget exceeded")
    parsed, _ = parse_type3_clipboard_bytes_with_parser(blob)
    paragraphs = []
    sections = 0
    for ni, node in enumerate(nodes):
        data = node.payload
        if node.header.class_name == "CPropertyExtend":
            # Reuse the established textual framing condition, without +30 or palette reads.
            for marker in (b"OBJETINFOS_CLASSNAME", b"OBJECTINFOS_CLASSNAME"):
                frame = len(marker).to_bytes(4, "little") + marker + b"\x06\0\0\0CObDao"
                sections += data.count(frame)
        if node.header.class_name != "CParagraphe":
            continue
        count = max(0, (len(data)-47)//204)
        if count > 24:
            raise ValueError("chunk budget exceeded")
        runs = parser._read_paragraphe_slot_record_runs(data)
        if len(runs) > 16 or any(len(r) > 24 for r in runs):
            raise ValueError("text run budget exceeded")
        texts = []
        for records in runs:
            run = parser._records_to_text_run(records)
            if run:
                texts.append({"text": run["text"], "character_count": len(run["text"]),
                              "printable_character_count": len(run["text"].replace("\n", "")),
                              "line_count": run["line_count"], "slot_count": len(records),
                              "codes": run["codes"], "zero_slot_count": run["codes"].count(0)})
        chunks = []
        for i in range(count):
            pos = 47 + i*204
            window = data[pos+0x70:pos+0xA1]
            chunks.append({"ordinal": i, "payload_relative_start": pos,
                           "color_bytes": data[pos+0x8B:pos+0x8E].hex(),
                           "local_signature": window.hex(), "masked_signature": mask(window),
                           "phase1b_signature": mask(data[pos+0x80:pos+0x99], 0x80),
                           "prefix_0_15": data[pos:pos+16].hex(),
                           "slot_header_at_59": data[pos+59:pos+67].hex(),
                           "fixed_header_marker": data[pos+53:pos+73] == b"OBJETINFOS_CLASSNAME"
                           and data[pos+73:pos+83] == b"\x06\0\0\0CObDao"})
        desc = origin + node.start_offset
        paragraphs.append({"descriptor_provenance": {"node_ordinal": ni,
            "runtime_descriptor_start": desc, "schema": int.from_bytes(blob[desc+2:desc+4], "little"),
            "class_name": "CParagraphe", "class_payload_start": origin+node.payload_offset,
            "payload_length": len(data)}, "provisional_chunk_count": count,
            "trailing_bytes": max(0, len(data)-47) % 204, "chunks": chunks, "text_runs": texts})
    return {"paragraphs": paragraphs, "parser_chain_count": len(parsed.object_chains),
            "CContour_count": sum(n.header.class_name == "CContour" for n in nodes),
            "contour_records_per_chain": [len(c.contour_records) for c in parsed.object_chains],
            "contour_record_count": sum(len(c.contour_records) for c in parsed.object_chains),
            "CPropertyExtend_CObDao_section_count": sections,
            "grouping": None, "grouping_status": "not_independently_decoded",
            "glyph_count": None, "glyph_status": "existing_parser_has_no_glyph_boundaries"}


def structural_report(prepared):
    # Corpus modal Phase 1B context: no fixture-name or palette classification.
    signatures = Counter(c["phase1b_signature"] for _, s in prepared for p in s["paragraphs"]
                         for c in p["chunks"] if not c["fixed_header_marker"])
    common = signatures.most_common()
    template = common[0][0] if common and (len(common) == 1 or common[0][1] > common[1][1]) else None
    results, counts, similarities, ends = [], [], [], []
    for name, s in prepared:
        for p in s["paragraphs"]:
            chunks = p["chunks"]
            body = [c for c in chunks if not c["fixed_header_marker"] and c["phase1b_signature"] == template]
            ordinals = [c["ordinal"] for c in body]
            p["repeated_candidate_ordinals"] = ordinals
            for c in chunks:
                c["role"] = ("header_like" if c["fixed_header_marker"] else
                             "repeated_color_record_candidate" if c in body else
                             "terminal_like" if body and c["ordinal"] > max(ordinals) else "unresolved")
                del c["phase1b_signature"]
            classes = Counter(c["masked_signature"] for c in body)
            modal = max(classes.values(), default=0)
            similarity = {"local_signature_class_count": len(classes),
                "identical_except_color_count": modal, "structurally_similar_count": len(body)-modal,
                "divergent_count": sum(c["role"] == "unresolved" for c in chunks),
                "mixed_record_roles_possible": len(classes) > 1 or not body,
                "scope": "70..A0 excluding 8B..8D; identical count includes modal representative; similar means equal narrower 80..98 context"}
            p["structure_similarity"] = similarity
            texts = p["text_runs"]
            chars = sum(t["character_count"] for t in texts) if texts else None
            slots = sum(t["slot_count"] for t in texts) if texts else None
            # Existing slot-run header, checked on the provisional grid; no new glyph decoding.
            grid_codes = [int.from_bytes(bytes.fromhex(c["slot_header_at_59"])[4:], "little") for c in body]
            slot_match = bool(body and texts and all(c["slot_header_at_59"].startswith("05000000") for c in body)
                              and grid_codes == [code for t in texts for code in t["codes"]])
            p["existing_slot_run_grid_match"] = slot_match
            row = {"fixture": name, "paragraph_node": p["descriptor_provenance"]["node_ordinal"],
                   "visible_text": [t["text"] for t in texts], "visible_character_count": chars,
                   "text_status": "existing_ASCII_run_candidate" if texts else "unavailable_decoding_unresolved",
                   "provisional_chunk_count": len(chunks), "repeated_candidate_count": len(body) if body else None,
                   "candidate_status": "context_matched" if body else "unresolved_context_mismatch",
                   "delta": len(body)-chars if chars is not None and body else None,
                   "text_run_count": len(texts), "slot_count": slots, "slot_grid_match": slot_match,
                   **{k: s[k] for k in ("parser_chain_count", "CContour_count", "contour_record_count",
                                        "CPropertyExtend_CObDao_section_count", "grouping")}}
            counts.append(row)
            similarities.append({"fixture": name, **similarity})
            ends.append({"fixture": name, "header_ordinal": 0 if chunks else None,
                "header_distinct": bool(chunks and chunks[0]["masked_signature"] not in classes),
                "header_fixed_marker": bool(chunks and chunks[0]["fixed_header_marker"]),
                "header_count_probe_at_5": int.from_bytes(bytes.fromhex(chunks[0]["prefix_0_15"])[5:9], "little") if chunks else None,
                "header_count_probe_equals_slot_count": bool(chunks and slots is not None and int.from_bytes(bytes.fromhex(chunks[0]["prefix_0_15"])[5:9], "little") == slots),
                "header_raw_8B_8E": chunks[0]["local_signature"][(0x8B-0x70)*2:(0x8F-0x70)*2] if chunks else None,
                "final_ordinal": len(chunks)-1 if chunks else None,
                "terminal_distinct": bool(chunks and chunks[-1]["masked_signature"] not in classes)})
        results.append({"fixture": name, "structural": s})
    # All same-text, single-chain contrasts are selected structurally, not by name.
    pairs = []
    single = [r for r in results if r["structural"]["parser_chain_count"] == 1 and len(r["structural"]["paragraphs"]) == 1]
    for a, b in combinations(single, 2):
        pa, pb = a["structural"]["paragraphs"][0], b["structural"]["paragraphs"][0]
        if not pa["text_runs"] or pa["text_runs"] != pb["text_runs"]:
            continue
        ca, cb = pa["chunks"], pb["chunks"]
        aligned = len(ca) == len(cb) and pa["repeated_candidate_ordinals"] == pb["repeated_candidate_ordinals"]
        body = pa["repeated_candidate_ordinals"]
        pairs.append({"fixtures": [a["fixture"], b["fixture"]], "count_layout_equal": aligned,
            "repeated_windows_equal_excluding_color": aligned and all(ca[i]["masked_signature"] == cb[i]["masked_signature"] for i in body),
            "color_bytes_changed": aligned and any(ca[i]["color_bytes"] != cb[i]["color_bytes"] for i in body),
            "terminal_window_invariant": aligned and ca[-1]["local_signature"] == cb[-1]["local_signature"]})
    usable = [r for r in counts if r["delta"] is not None]
    n_plus_one = bool(usable) and all(r["delta"] == 1 for r in usable)
    slot_support = bool(usable) and all(r["slot_grid_match"] for r in usable)
    homogeneous = bool(usable) and all(r["local_signature_class_count"] == 1 for r in similarities if r["local_signature_class_count"])
    style = bool(pairs) and all(r["count_layout_equal"] and r["repeated_windows_equal_excluding_color"] for r in pairs)
    return {"fixture_results": results,
        "character_count_hypothesis": {"status": "N+1_in_context_matched_ASCII_runs" if n_plus_one else "unresolved", "fixtures": counts,
            "supported_fixture_count": len(usable), "unresolved_fixtures": [r["fixture"] for r in counts if r["delta"] is None],
            "count_convention": "spaces count; newline counts as one control character; unresolved Unicode unavailable; extracted paragraph text is not total document text"},
        "geometry_count_hypothesis": {"status": "unresolved", "evidence": "see per-fixture counts; parser contour points are not glyphs",
            "single_chain_repeated_counts": sorted({r["repeated_candidate_count"] for r in usable if r["parser_chain_count"] == 1}),
            "glyph_boundaries_available": False},
        "text_run_hypothesis": {"status": "existing_text_slot_run_supported" if slot_support else "unresolved",
            "slot_grid_match_count": sum(r["slot_grid_match"] for r in counts),
            "interpretation": "context-matched candidate count matches existing 204-byte slot run including zero-code slot; not one chunk per run/style entry; unmatched contexts unresolved",
            "slot_header_chunk_relative_start": 59, "scope": "bounded 8-byte header equality on grid; no whole-record comparison"},
        "style_independence_summary": {"supported_in_bounded_windows": style, "pairs": pairs,
            "scope": "same structurally extracted content and one parser chain; full payload color-only equality not asserted"},
        "multi_object_scaling_summary": {"fixtures": [r for r in counts if r["parser_chain_count"] > 1],
            "grouping": "unavailable structurally; filenames are identifiers only",
            "total_characters_across_objects": None, "selected_object_relationship": "unresolved_no_ownership",
            "interpretation": "counts track extracted paragraph slots; chain counts and grouping cannot establish object correspondence"},
        "repeated_record_structure_summary": {"fixtures": similarities, "homogeneous_in_bounded_window": homogeneous,
            "homogeneity_scope": "classified candidates only; unmatched contexts unresolved; full chunks have mixed roles",
            "classification_basis": "unique modal masked Phase 1B context, independent of filename/palette/intent",
            "record_model_status": "204_byte_stride_supported_by_existing_slot_grid_not_uniform_full_payload_records" if slot_support else "unresolved"},
        "header_terminal_summary": {"fixtures": ends,
            "black_alias": "zero header bytes can alias Black; never used as record-role evidence",
            "count_probe_status": "bounded observation only, not decoded header field",
            "color_change_pair_terminal_invariance": [p for p in pairs if p["color_bytes_changed"]]},
        "answers": {"repeated_record_best_interpretation": "text_slot_run_including_zero_code_slot" if slot_support else "unresolved",
            "character_count_relationship": "N+1_for_context_matched_ASCII_text" if n_plus_one else "unresolved",
            "geometry_count_relationship": "unresolved_no_glyph_boundaries", "style_independence": style,
            "repeated_records_homogeneous": homogeneous,
            "header_like_status": "structurally_distinct" if ends and all(e["header_distinct"] and e["header_fixed_marker"] for e in ends) else "unresolved",
            "terminal_like_status": "structurally_distinct" if ends and all(e["terminal_distinct"] for e in ends) else "unresolved",
            "observed_color_byte_start": 0x8B, "observed_changed_width": 3,
            "typed_field_width": None, "typed_field_start": "unresolved",
            "typed_width_blocker": "no independent next-field boundary or typed storage declaration; stable adjacent zeros insufficient",
            "field_decode_readiness": "not_ready", "color_ownership_readiness": "not_ready"}}


def oracle_phase(frozen, enabled):
    if not enabled:
        return {"enabled": False, "fixtures": []}
    rows = []
    for result in json.loads(frozen)["fixture_results"]:
        expected = color.load_oracle(result["fixture"])
        observed = Counter(color.color_name(int.from_bytes(bytes.fromhex(c["color_bytes"])+b"\0", "little"), "RGB0")
                           for p in result["structural"]["paragraphs"] for c in p["chunks"]
                           if c["role"] == "repeated_color_record_candidate")
        rows.append({"fixture": result["fixture"], "expected_colors": expected["colors"] if expected else None,
                     "candidate_palette_counts": {str(k): v for k, v in observed.items()},
                     "missing_expected_colors": sorted(set(expected["colors"])-set(observed)) if expected else None})
    return {"enabled": True, "fixtures": rows, "structural_freeze_before_oracle": True,
            "role_updates": False, "scope": "RGB byte consistency only; integer padding here is palette lookup, not storage width"}


def build_report(fixtures=None, oracle_enabled=True):
    names = list(dict.fromkeys(FIXTURES if fixtures is None else fixtures))
    if len(names) > 32:
        raise ValueError("fixture budget exceeded")
    prepared, warnings = [], []
    for name in names:
        path = (TEXT_DIR / name).resolve()
        if not path.is_relative_to(TEXT_DIR.resolve()) or not path.is_file():
            raise ValueError("fixture must be an existing file inside text samples")
        if path.stat().st_size > 8*1048576:
            raise ValueError("hex input budget exceeded")
        prepared.append((name, extract_structure(color.hex_text_to_bytes(path.read_text(encoding="utf-8-sig")))))
    frozen = compact(structural_report(prepared))
    oracle = oracle_phase(frozen, oracle_enabled)
    return {"mode": "text_color_record_semantics_phase1c", "policy": POLICY.copy(),
            "limits": LIMITS.copy(), "warnings": warnings, **json.loads(frozen), "oracle_summary": oracle}


def render_text(report, markdown=False):
    lines = [("# " if markdown else "") + "Text Color Record Semantics - Phase 1C"]
    lines.extend(compact(r) for r in report["character_count_hypothesis"]["fixtures"])
    lines.append(compact(report["answers"]))
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
    if len(output.encode("utf-8"))+2 >= LIMITS["json_bytes" if args.json else "text_bytes"]:
        parser.error("output budget exceeded")
    print(output)


if __name__ == "__main__":
    main()
