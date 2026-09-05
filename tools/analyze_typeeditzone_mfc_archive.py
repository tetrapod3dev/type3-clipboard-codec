"""Bounded MFC framing fingerprint audit; does not decode TYPE3 object ownership."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes  # noqa: E402
from type3_clipboard_codec.exceptions import InvalidHexError  # noqa: E402

SAMPLES = ROOT / "tests" / "samples"
KNOWN_NAMES = ("CZone", "CParagraphe", "CCourbe", "CContour", "CPropertyExtend", "CObDao")
NAME_RE = re.compile(b"|".join(re.escape(n.encode("ascii")) for n in KNOWN_NAMES))
DEFAULT_FIXTURES = (
    "text/default_text.txt", "text/text_group_same_color_two_objects.txt",
    "text/text_three_objects_grouped_order_abc.txt", "default_rectangle.txt",
    "default_circle.txt", "polyline_5_points.txt", "two_rectangle.txt", "two_circle.txt",
)
MAX_INPUT_BYTES = 1024 * 1024
MAX_TEXT_BYTES = 8 * MAX_INPUT_BYTES
JSON_LIMIT = 100000
MAX_TAG_ROWS = 100
TN002 = "https://learn.microsoft.com/en-us/cpp/mfc/tn002-persistent-object-data-format?view=msvc-170"
POLICY = {
    "scope": "mfc_carchive_compatibility_audit_only", "parser_behavior": "not_modified",
    "decoder_behavior": "not_modified", "model_behavior": "not_modified",
    "architecture_change": "not_performed",
}


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0] if 0 <= offset <= len(data) - 2 else None


def descriptor_hit(data, name, pos, fixture="synthetic", context_bytes=16):
    """Exact byte checks only. A plausible schema is weak, never a class identity test."""
    encoded = name.encode("ascii")
    length, schema, tag = u16(data, pos - 2), u16(data, pos - 4), u16(data, pos - 6)
    length_match = length == len(encoded) and data[pos:pos + len(encoded)] == encoded
    # Broad WORD-compatible candidate, excluding the non-serializable sentinel.
    # This is explicitly a heuristic; stable schemas are evaluated separately.
    plausible = schema is not None and schema != 0xFFFF
    exact = length_match and tag == 0xFFFF and schema is not None
    store = length_match and plausible and tag != 0xFFFF
    return {
        "fixture": fixture, "class_name": name, "class_name_length": len(encoded),
        "ascii_hit_payload_offset": pos,
        **{f"previous_{n}_bytes": data[pos-n:pos].hex() if pos >= n else None for n in (2, 4, 6, 8)},
        "candidate_name_length_word": length, "candidate_schema_word": schema,
        "candidate_new_class_tag": tag, "exact_length_match": length_match,
        "plausible_schema": plausible, "new_class_tag_match": tag == 0xFFFF,
        "descriptor_pattern_match": exact,
        "runtimeclass_store_pattern_without_newclass_tag": store,
        "length_prefixed_ascii_class_candidate": length_match,
        "descriptor_start": pos - 6 if exact else None,
        "context_before_hex": data[max(0, pos-context_bytes):pos].hex(),
        "context_after_hex": data[pos+len(encoded):pos+len(encoded)+context_bytes].hex(),
    }


def audit_ascii(data, fixture="synthetic", max_class_hits=100, context_bytes=16):
    """Phase A does not import or consult the class scanner, parser, or intent."""
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("payload exceeds bounded input budget")
    rows, truncated = [], False
    for match in NAME_RE.finditer(data):
        if len(rows) == max_class_hits:
            truncated = True
            break
        rows.append(descriptor_hit(data, match.group().decode("ascii"), match.start(), fixture, context_bytes))
    return {"class_hits": rows, "truncated": truncated,
            "count_basis": "bounded known-name hits only"}


def tag_candidate(data, offset, known_classes=None, known_objects=None, synchronized=False):
    """Classify one supplied position, never scan for a value that fits a PID."""
    classes, objects = known_classes or {}, known_objects or set()
    word = u16(data, offset)
    role, pid, supported = "unresolved_word", None, False
    if word == 0:
        role, supported = "null_tag_candidate", synchronized
    elif word == 0xFFFF:
        role = "new_class_tag_requires_descriptor"
    elif word == 0x7FFF:
        role = "extended_tag_candidate"
        if offset + 6 <= len(data):
            extended = struct.unpack_from("<I", data, offset + 2)[0]
            pid = extended & 0x7FFFFFFF
            supported = synchronized and (pid in classes if extended & 0x80000000 else pid in objects)
    elif word is not None and word & 0x8000:
        role, pid = "old_class_tag_candidate", word & 0x7FFF
        supported = synchronized and pid in classes
    elif word:
        role, pid = "object_reference_candidate", word
        supported = synchronized and pid in objects
    return {"tag_value": word, "payload_relative_offset": offset, "candidate_role": role,
            "pid_candidate": pid, "reference_state_match": bool(supported),
            "confidence": "conditional_state_match" if supported else "unresolved",
            "reason": "unverified cursor or conditional PID state"}


def shadow_context(data, hits, start):
    """One conditional WriteObject path. Stop at opaque Serialize data; no resync."""
    exact = {h["descriptor_start"]: h for h in hits if h["descriptor_pattern_match"]}
    cursor, next_pid = start, 1
    classes, objects, events = {}, set(), []
    reason = "step_budget"
    for _ in range(16):
        if cursor >= len(data):
            reason = "end_of_input_under_start_assumption"
            break
        if cursor in exact:
            hit = exact[cursor]
            classes[next_pid] = hit["class_name"]
            objects.add(next_pid + 1)
            events.append({"role": "new_class_and_object_candidates", "offset": cursor,
                           "class": hit["class_name"], "class_descriptor_pid_candidate": next_pid,
                           "object_pid_candidate": next_pid + 1})
            next_pid += 2
            cursor = hit["ascii_hit_payload_offset"] + hit["class_name_length"]
            # Even EOF does not establish that an unknown Serialize body is empty.
            reason = "unknown_class_Serialize_extent"
            break
        word = u16(data, cursor)
        if word == 0:
            events.append({"role": "conditional_null", "offset": cursor})
            cursor += 2
            continue
        probe = tag_candidate(data, cursor, classes, objects, synchronized=True)
        events.append({"role": probe["candidate_role"], "offset": cursor, "tag_value": word,
                       "pid_candidate": probe["pid_candidate"], "reference_state_match": probe["reference_state_match"]})
        reason = "unresolved_tag_or_application_prefix"
        break
    return {"start": start, "status": "desynchronized" if reason != "end_of_input_under_start_assumption" else "conditional_end",
            "stop_offset": cursor, "stop_reason": reason, "next_pid": next_pid,
            "known_class_descriptors": classes, "object_pid_candidates": sorted(objects), "events": events,
            "class_only_alternative_next_pid": 2 if classes else None,
            "coherent_pid_progression_established": False, "resynchronization_attempted": False}


def scanner_relationship(data, hits, max_nodes):
    """Phase E only; same scanner and top-level origin as the active parser."""
    from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

    parser = Type3ChainParser()
    _, _, origin = parser._read_top_level_header(data)
    nodes = parser._extract_nodes(data[origin:])
    by_pos = {h["ascii_hit_payload_offset"]: h for h in hits}
    rows = []
    for node in nodes[:max_nodes]:
        boundary = origin + node.start_offset
        pos = boundary + 6
        hit = by_pos.get(pos)
        exact = bool(hit and hit["descriptor_pattern_match"])
        rows.append({"node_class": node.header.class_name, "scanner_header_location": boundary,
                     "corresponding_ascii_class_hit": pos if hit else None,
                     "mfc_descriptor_match": exact, "descriptor_start": hit["descriptor_start"] if exact else None,
                     "class_name_start": pos,
                     "scanner_boundary_equals_descriptor_start": exact and boundary == hit["descriptor_start"],
                     "scanner_boundary_equals_class_name_start": boundary == pos,
                     "relation": "A_descriptor_start" if exact else "D_unmatched_or_bounded"})
    return {"nodes": rows, "node_count": len(nodes), "truncated": len(nodes) > max_nodes,
            "parser_scan_origin": origin}


def fixture_assessment(hits, truncated=False):
    exact = [h for h in hits if h["descriptor_pattern_match"] and h["plausible_schema"]]
    if len({h["class_name"] for h in exact}) >= 2:
        return "partial_mfc_runtimeclass_framing_match"
    if exact or any(h["runtimeclass_store_pattern_without_newclass_tag"] or h["exact_length_match"] for h in hits):
        return "mfc_inspired_or_custom_serialization_possible"
    # A missing pattern is not a rejection of direct Serialize or other MFC use.
    return "insufficient_evidence"


def analyze_bytes(data, fixture="synthetic", category="unknown", max_class_hits=100, context_bytes=16):
    phase_a = audit_ascii(data, fixture, max_class_hits, context_bytes)
    # Freeze byte evidence before running the existing scanner; Phase A is independent.
    phase_a = json.loads(compact(phase_a))
    hits = phase_a["class_hits"]
    exact = [h for h in hits if h["descriptor_pattern_match"]]
    tag_rows = []
    for hit in exact:
        tag_rows.append({"tag_value": 65535, "payload_relative_offset": hit["descriptor_start"],
                         "candidate_role": "new_class_descriptor_candidate", "neighboring_descriptor": hit["class_name"],
                         "confidence": "exact_layout", "reason": "exact descriptor layout"})
    # These are explicit probe positions, not proven archive cursors. Keep all
    # their tag-like words unresolved, including zeros at a Serialize body start.
    positions = {0: "payload_start_archive_assumption"}
    if exact:
        hit = exact[0]
        positions[hit["ascii_hit_payload_offset"] + hit["class_name_length"]] = "first_descriptor_opaque_Serialize_body_start"
    for pos, basis in sorted(positions.items()):
        if pos in {h["descriptor_start"] for h in exact}:
            continue
        probe = tag_candidate(data, pos)
        probe["neighboring_descriptor_or_reference"] = basis
        tag_rows.append(probe)
    starts = [0]
    if exact and exact[0]["descriptor_start"] != 0:
        starts.append(exact[0]["descriptor_start"])
    paths = [shadow_context(data, hits, start) for start in starts]
    counts = Counter(h["class_name"] for h in exact)
    repeats = {name: count for name, count in counts.items() if count > 1}
    scanner = scanner_relationship(data, hits, max_class_hits)
    return {
        "fixture": fixture, "category": category, "payload_bytes": len(data),
        "absolute_offset_role": "diagnostic_only", "offset_origin": "decoded clipboard payload byte zero",
        **phase_a,
        "summary": {"class_hits": len(hits), "exact_mfc_newclass_descriptor_matches": len(exact),
            "runtimeclass_store_matches_without_tag": sum(h["runtimeclass_store_pattern_without_newclass_tag"] for h in hits),
            "length_only_matches": sum(h["exact_length_match"] and not h["descriptor_pattern_match"] and not h["runtimeclass_store_pattern_without_newclass_tag"] for h in hits),
            "unmatched_class_names": dict(Counter(h["class_name"] for h in hits if not h["exact_length_match"])),
            "exact_length_matches": sum(h["exact_length_match"] for h in hits)},
        "tags": tag_rows, "tags_report_omitted": 0,
        "pid_context": {"paths": paths, "single_context": "unresolved", "multiple_contexts": "unresolved",
            "restart_evidence": "none independently identified; repeated names alone do not prove restart",
            "repeated_exact_descriptors": repeats,
            "repeated_ascii_names": {n: c for n, c in Counter(h["class_name"] for h in hits).items() if c > 1},
            "repeated_class_reference_substitution": "unresolved without Serialize boundaries and PID synchronization",
            "conditional_conflict": "repeated descriptors need explanation IF one context and same runtime class" if repeats else None,
            "first_descriptor_seed_is_not_resynchronization": True},
        "scanner_relationship": scanner,
        "classification": fixture_assessment(hits, phase_a["truncated"]),
    }


def resolve_fixture(name):
    # Names are file selection only, never classification or byte interpretation.
    candidate = Path(name)
    paths = [SAMPLES / candidate, SAMPLES / "text" / candidate]
    for path in paths:
        resolved = path.resolve()
        if resolved.is_relative_to(SAMPLES.resolve()) and resolved.is_file():
            return resolved
    return None


def class_summaries(fixtures):
    hits = [h for f in fixtures for h in f["class_hits"]]
    result = []
    for name in KNOWN_NAMES:
        rows = [h for h in hits if h["class_name"] == name]
        matched = [h for h in rows if h["descriptor_pattern_match"]]
        schemas = sorted({h["candidate_schema_word"] for h in matched})
        repeated = len(matched) > 1 and len({h["fixture"] for h in matched}) > 1
        result.append({"class_name": name, "occurrences": len(rows), "descriptor_match_count": len(matched),
            "candidate_schema_values_all_hits": sorted({h["candidate_schema_word"] for h in rows if h["candidate_schema_word"] is not None}),
            "observed_schema_values": schemas,
            "schema_stability": "stable_across_fixtures" if repeated and len(schemas) == 1 else "variable" if len(schemas) > 1 else "insufficient_observations",
            "observed_length_values": sorted({h["candidate_name_length_word"] for h in rows if h["candidate_name_length_word"] is not None}),
            "length_match_rate": sum(h["exact_length_match"] for h in rows) / len(rows) if rows else None})
    return result


def bound_report(report, budget=JSON_LIMIT):
    """Keep counts/assessments; explicitly omit only diagnostic detail if needed."""
    remaining = MAX_TAG_ROWS
    for fixture in report["fixtures"]:
        keep = min(remaining, len(fixture["tags"]))
        fixture["tags_report_omitted"] = len(fixture["tags"]) - keep
        fixture["tags"] = fixture["tags"][:keep]
        remaining -= keep
    if any(f["tags_report_omitted"] for f in report["fixtures"]):
        report["warnings"].append("tag detail capped at 100 rows globally; aggregate counts retained")
    if len(compact(report).encode("utf-8")) + 2 < budget:
        return report
    report["warnings"].append("output budget: optional context hex omitted")
    for fixture in report["fixtures"]:
        for row in fixture["class_hits"]:
            row.pop("context_before_hex", None)
            row.pop("context_after_hex", None)
    # Fairly reduce the largest fixture detail inventory; never disguise truncation.
    while len(compact(report).encode("utf-8")) + 256 >= budget:
        largest = max(report["fixtures"], key=lambda f: len(f["class_hits"]), default=None)
        if not largest or not largest["class_hits"]:
            raise ValueError("report metadata exceeds output budget")
        largest["class_hits"].pop()
        largest["class_hit_details_omitted"] = largest.get("class_hit_details_omitted", 0) + 1
    if any(f.get("class_hit_details_omitted") for f in report["fixtures"]):
        report["warnings"].append("output budget: some hit details omitted; bounded analysis counts retained")
    return report


def build_report(fixture_names=None, max_fixtures=8, max_class_hits=100, context_bytes=16):
    if not (1 <= max_fixtures <= 8 and 1 <= max_class_hits <= 100 and 0 <= context_bytes <= 64):
        raise ValueError("limits: fixtures 1..8, class hits 1..100, context bytes 0..64")
    names = list(dict.fromkeys(DEFAULT_FIXTURES if fixture_names is None else fixture_names))
    warnings, fixtures = [], []
    if len(names) > max_fixtures:
        warnings.append("fixture selection capped by --max-fixtures")
    for name in names[:max_fixtures]:
        path = resolve_fixture(name)
        if path is None:
            warnings.append(f"missing or unsupported fixture: {name}")
            continue
        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                raise ValueError("hex fixture exceeds input text budget")
            data = hex_text_to_bytes(path.read_text(encoding="utf-8-sig"))
            relative = path.relative_to(SAMPLES).as_posix()
            category = "text" if relative.startswith("text/") else "geometry"
            result = analyze_bytes(data, relative, category, max_class_hits, context_bytes)
        except (ValueError, OSError, InvalidHexError) as exc:
            warnings.append(f"fixture not analyzed: {name}: {exc}")
            continue
        if result["truncated"] or result["scanner_relationship"]["truncated"]:
            warnings.append(f"bounded inventory: {relative}; counts are observed lower bounds")
        fixtures.append(result)
    classes = class_summaries(fixtures)
    stable = [c["class_name"] for c in classes if c["schema_stability"] == "stable_across_fixtures"]
    matched = [c["class_name"] for c in classes if c["descriptor_match_count"]]
    tags = [r for f in fixtures for r in f["tags"]]
    scanner_rows = [r for f in fixtures for r in f["scanner_relationship"]["nodes"]]
    categories = sorted({f["category"] for f in fixtures if f["summary"]["exact_mfc_newclass_descriptor_matches"]})
    assessment = ("mfc_runtimeclass_framing_supported_but_writeobject_unclear" if len(matched) >= 2 and stable else
                  "mfc_like_custom_serialization_possible" if any(f["classification"] != "insufficient_evidence" for f in fixtures) else
                  "evidence_insufficient")
    report = {
        "mode": "typeeditzone_mfc_archive_compatibility_audit", "policy": POLICY.copy(),
        "limits": {"max_fixtures": max_fixtures, "max_class_hits_per_fixture": max_class_hits,
            "context_bytes": context_bytes, "max_reported_tag_rows": MAX_TAG_ROWS,
            "max_payload_bytes": MAX_INPUT_BYTES, "json_bytes": JSON_LIMIT, "text_bytes": 50000},
        "warnings": warnings, "fixtures": fixtures, "class_descriptor_summary": classes,
        "schema_summary": {"stable_schema_classes": stable,
            "basis": "only exact descriptors; repeated across fixtures; schema WORD is a candidate, not decoded semantics",
            "plausible_schema_rule": "any WORD other than FFFF; weak heuristic, not a proven version range",
            "schemas_unique_to_each_class": len({tuple(c["observed_schema_values"]) for c in classes if c["descriptor_match_count"]}) == len(matched) if matched else None},
        "tag_summary": {"tested_positions": "all exact descriptor starts, first descriptor end, payload zero; no whole-payload tag histogram",
            "candidate_role_counts": dict(Counter(r["candidate_role"] for r in tags)),
            "structurally_supported_newclass_candidates": sum(c["descriptor_match_count"] for c in classes),
            "confirmed_old_class_references": 0, "confirmed_object_references": 0,
            "confirmed_null_tags": 0, "confirmed_extended_tags": 0,
            "negative_evidence_scope": "only tested positions; tag-like words in opaque data remain unresolved"},
        "pid_context_summary": {"coherent_full_contexts": 0, "verified_restarts": 0,
            "path_assumptions": "fresh archive at each preselected seed; no MapObject; WriteObject rather than class-only framing",
            "desynchronized_paths": sum(p["status"] == "desynchronized" for f in fixtures for p in f["pid_context"]["paths"]),
            "limitation": "cannot advance through unknown Serialize bodies; no PID assignments beyond the first descriptor; no resync",
            "PID_is_TYPE3_object_ID": False},
        "scanner_relationship_summary": {"reported_nodes": len(scanner_rows),
            "descriptor_start_matches": sum(r["scanner_boundary_equals_descriptor_start"] for r in scanner_rows),
            "ascii_start_matches": sum(r["scanner_boundary_equals_class_name_start"] for r in scanner_rows),
            "independent_fingerprint": False,
            "limitation": "scanner already tests FFFF and name length; agreement is architectural correspondence, not independent MFC proof"},
        "global_assessment": {"classification": assessment, "source_code_certainty": False,
            "fingerprints": {"exact_descriptor_classes": len(matched), "stable_schema_classes": len(stable),
                "fixture_categories": categories, "coherent_reference_tags": False,
                "coherent_PID_progression": False, "archive_context_consistency": "unresolved"},
            "reference": TN002, "exact_WORD_layout_basis": "user-specified CRuntimeClass::Store implementation fingerprint tested as a hypothesis",
            "limitation": "Direct Serialize, selective SerializeClass, custom framing and CArchive primitives remain possible; incomplete WriteObject evidence does not reject MFC."},
        "answers": {"exact_descriptor_pattern_found": bool(matched), "matched_classes": matched,
            "stable_schema_classes": stable, "old_class_tag_evidence": "no confirmed reference at tested positions",
            "pid_progression_evidence": "conditional first class=1/object=2 only; progression desynchronizes at opaque Serialize body",
            "archive_context_evidence": "one versus multiple contexts unresolved; no verified restart",
            "scanner_interpretation": "A: descriptor start" if scanner_rows and all(r["mfc_descriptor_match"] for r in scanner_rows) else "bounded/mixed evidence",
            "mfc_compatibility_assessment": assessment, "parser_refactor_readiness": "not_ready",
            "architecture_implication": "Consider archive framing -> runtime-class tags -> application Serialize data as a hypothesis, not an implemented object model.",
            "next_track": "color investigation may proceed unchanged as candidate evidence; framing RFC before any archive-based parser refactor or ownership inference"},
    }
    return bound_report(report)


def render_text(report, markdown=False):
    classes = report["class_descriptor_summary"]
    title = "TypeEditZone MFC CArchive Compatibility Audit"
    lines = [("# " if markdown else "") + title, "",
        f"Fixtures: {len(report['fixtures'])}",
        f"Class-name hits: {sum(c['occurrences'] for c in classes)}",
        f"Exact new-class descriptors: {sum(c['descriptor_match_count'] for c in classes)}",
        f"RuntimeClass Store-like descriptors without tag: {sum(f['summary']['runtimeclass_store_matches_without_tag'] for f in report['fixtures'])}",
        f"Stable schemas: {len(report['schema_summary']['stable_schema_classes'])}", ""]
    if markdown:
        lines.extend(["| Class | Hits | Exact | Schema(s) | Length match rate |", "| --- | ---: | ---: | --- | ---: |"])
    else:
        lines.append("Class             Hits Exact Schema(s) Length match rate")
    for row in classes:
        values = [row["class_name"], str(row["occurrences"]), str(row["descriptor_match_count"]),
                  str(row["observed_schema_values"]), str(row["length_match_rate"])]
        lines.append("| " + " | ".join(values) + " |" if markdown else "  ".join(values))
    lines += ["", "Old-class/reference evidence: " + report["answers"]["old_class_tag_evidence"],
        "PID/context evidence: " + report["answers"]["pid_progression_evidence"],
        "Archive contexts: " + report["answers"]["archive_context_evidence"],
        "Scanner relationship: " + report["answers"]["scanner_interpretation"], "",
        "Assessment: " + report["global_assessment"]["classification"],
        "Parser refactor readiness: not_ready", report["global_assessment"]["limitation"],
        "", "Fixtures (classification):"]
    lines += [f"- {f['fixture']}: {f['classification']}" for f in report["fixtures"]]
    lines += ["", "Warnings: " + ("; ".join(report["warnings"]) or "none"),
              "Offsets: diagnostic_only; no ownership inference or active parser changes.",
              "Reference: " + TN002]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    formats = parser.add_mutually_exclusive_group()
    formats.add_argument("--json", action="store_true")
    formats.add_argument("--markdown", action="store_true")
    parser.add_argument("--fixture", action="append", metavar="NAME")
    parser.add_argument("--max-fixtures", type=int, default=8)
    parser.add_argument("--max-class-hits", type=int, default=100)
    parser.add_argument("--context-bytes", type=int, default=16)
    args = parser.parse_args()
    try:
        report = build_report(args.fixture, args.max_fixtures, args.max_class_hits, args.context_bytes)
    except ValueError as exc:
        parser.error(str(exc))
    output = compact(report) if args.json else render_text(report, args.markdown)
    if len(output.encode("utf-8")) + 2 >= (JSON_LIMIT if args.json else 50000):
        parser.error("output budget exceeded")
    print(output)


if __name__ == "__main__":
    main()
