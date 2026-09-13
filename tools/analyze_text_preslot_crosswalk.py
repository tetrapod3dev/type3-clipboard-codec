"""Independent current pre-slot cursor walk; analyzer only, never a production gate."""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter
from pathlib import Path

from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text.text_slot_candidate import extract_text_slot_candidate
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

ROOT = Path(__file__).resolve().parents[1]
# Frozen archive emissions, not corpus-derived offsets. See investigation provenance table.
PARA_WIDTH = 4 + 4 + 5 * 8 + 4
LINE_WIDTH = 4 + 4 + 6 * 8 + 4 + 8
PARAGRAPH_WIDTHS = (4, 8, 4, 4, 8, 8, 8)
STATES = ("exact_match", "mismatch", "insufficient_context", "unsupported_parent_version",
          "truncated", "unresolved")
FIELDS = (("A", 32, "CTxtAttrPara+0x20", "0x4e253"),
          ("length", 56 + 24, "CTxtAttrLine[0]+0x30", "0x4de4b"),
          ("B", 56 + 48, "CTxtAttrLine[0]+0x10", "0x4de72"))


class WalkStopped(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


class Cursor:
    def __init__(self, data):
        self.data, self.position, self.trace = data, 0, []

    def take(self, width, label):
        start = self.position
        if width > len(self.data) - start:
            raise WalkStopped("truncated", label)
        self.position += width
        self.trace.append({"segment": label, "start": start, "width": width})
        return self.data[start:self.position]

    def word(self, label, width=4):
        return int.from_bytes(self.take(width, label), "little")

    def version(self, label, expected):
        value = self.word(label)
        self.trace[-1]["value"] = value
        if value != expected:
            raise WalkStopped("unsupported_parent_version", label)


def derive_preslot(payload: bytes) -> dict:
    """Input begins at the recognized descriptor's end (C), with no alignment input.

    P is published as established only after the complete current parent walk.
    A tentative cursor is retained separately on failures for audit, never eligibility.
    """
    cursor = Cursor(payload)
    result = {"status": "unresolved", "parser_safe": False, "p_origin": None,
              "first_attrchar": None, "trace": cursor.trace}
    try:
        cursor.take(2 * 3 * 8, "CObDao/cube/two CVect3D")
        flags = cursor.word("CObDao stored flags")
        cursor.version("CObDao version", 8)
        cursor.take(4 * 4, "CObDao members +58,+5c,+60,+64")
        cursor.version("CObjGuid version", 2)
        cursor.take(16, "CObjGuid GUID")
        count = cursor.word("GUID property count")
        # At least two DWORD lengths per pair; bound work by the available bytes.
        if count > (len(payload) - cursor.position) // 8:
            raise WalkStopped("truncated", "property count exceeds available pair framing")
        for i in range(count):
            for part in ("key", "value"):
                size = cursor.word(f"property {i} {part} length")
                cursor.take(size, f"property {i} {part} bytes")
        extra = cursor.word("additional map count", 8)
        if extra:
            raise WalkStopped("unresolved", "nonempty additional map outside reviewed walk")
        # Base ORs these bits before writing, then restores original flags.
        if flags & 0x01001000 != 0x01001000:
            raise WalkStopped("unresolved", "stored flags incompatible with current base store")
        possible_extra = {kind | low | 0x01001000
                          for kind in (0x01000010, 0x01000100) for low in (0, 1)}
        if flags in possible_extra:
            raise WalkStopped("unresolved", "CObDaoFin optional word preimage ambiguous")
        result.update(base_length=cursor.position, property_count=count, extra_map_count=extra)
        for member, width in zip(("+a8", "+d8", "+e4", "+ec", "+b8.x", "+b8.y", "+b8.z"),
                                 PARAGRAPH_WIDTHS, strict=True):
            cursor.take(width, "CParagraphe " + member)
        p = cursor.position
        result["tentative_p_origin"] = p
        cursor.version("AttrPara version", 4)
        cursor.take(PARA_WIDTH - 4, "current AttrPara remainder")
        lines = cursor.word("line count")
        result["line_count"] = lines
        # Even an unsupported line needs a DWORD version. Never multiply by 68 to skip.
        if lines > (len(payload) - cursor.position) // 4:
            raise WalkStopped("truncated", "line count exceeds available versions")
        line_starts = []
        for i in range(lines):
            line_starts.append(cursor.position)
            cursor.version(f"AttrLine {i} version", 4)
            cursor.take(LINE_WIDTH - 4, f"current AttrLine {i} remainder")
        chars = cursor.word("char count")
        result.update(status="current_preslot_supported", p_origin=p,
                      first_attrchar=cursor.position, char_count=chars,
                      line_starts=line_starts)
    except WalkStopped as stopped:
        result.update(status=stopped.status, reason=stopped.reason)
    return result


def compare_alignment(derived, candidate):
    """Compare only after independent derivation; candidate cannot influence its cursor."""
    if derived["status"] != "current_preslot_supported":
        return derived["status"]
    if candidate is None:
        return "insufficient_context"
    if (derived["first_attrchar"] != candidate["first_prefix_relative_offset"]
            or derived["char_count"] != len(candidate["slots"])):
        return "mismatch"
    return "exact_match"


def field_evidence(payload, derived):
    """Values are diagnostics after the entire parent structure has been established."""
    if derived["status"] != "current_preslot_supported":
        return {}
    fields = {}
    for name, relative, member, rva in FIELDS:
        if name != "A" and not derived["line_count"]:
            continue
        position = derived["p_origin"] + relative
        raw = bytes(payload[position:position + 8])
        value = struct.unpack("<d", raw)[0]
        fields[name] = {"p_relative": relative, "c_relative": position, "member": member,
                        "operation_rva": rva, "archive_type": "binary64", "raw_hex": raw.hex(),
                        "value": value if math.isfinite(value) else repr(value)}
    return fields


def build_report(paths=None):
    paths = sorted((ROOT / "tests/samples").rglob("*.txt")) if paths is None else list(paths)
    rows, issues = [], []
    valid = text_captures = 0
    for supplied in paths:
        path = Path(supplied)
        try:
            raw = hex_text_to_bytes(path.read_bytes().decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError) as error:
            issues.append({"path": str(path), "reason": type(error).__name__})
            continue
        valid += 1
        parser = Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        paragraphs = [node for node in parser._extract_nodes(raw[base:])
                      if node.header.class_name == "CParagraphe"]
        text_captures += bool(paragraphs)
        for node in paragraphs:
            derived = derive_preslot(node.payload)
            candidate = extract_text_slot_candidate([node.payload])
            c = base + node.payload_offset
            rows.append({"capture": str(path), "c_absolute": c,
                         "p_absolute": None if derived["p_origin"] is None else c + derived["p_origin"],
                         "production_candidate": candidate is not None,
                         "production_first": None if candidate is None else candidate["first_prefix_relative_offset"],
                         "comparison": compare_alignment(derived, candidate),
                         "structure": derived, "fields": field_evidence(node.payload, derived)})
    states = Counter(row["comparison"] for row in rows)
    established = [row for row in rows if row["structure"]["p_origin"] is not None]
    supported = [row for row in rows if row["comparison"] == "exact_match"]
    shifts = Counter(row["p_absolute"] - row["c_absolute"] for row in established)
    pairs = [row["fields"] for row in supported if "B" in row["fields"]]
    versions = {}
    for row in rows:
        for segment in row["structure"]["trace"]:
            if "value" in segment:
                label = segment["segment"]
                if label.startswith("AttrLine"):
                    label = "AttrLine version"
                versions.setdefault(label, Counter())[segment["value"]] += 1
    if states["mismatch"]:
        readiness = "contradicted"
    elif rows and len(supported) == len(rows) and set(shifts) == {182}:
        readiness = "broad_current_corpus_supported"
    elif supported:
        readiness = "partially_supported"
    elif states["unsupported_parent_version"]:
        readiness = "blocked_by_parent_versions"
    else:
        readiness = "unresolved"
    return {"policy": "shadow_only", "parser_safe": False,
            "pre_slot_crosswalk_readiness": readiness, "files_examined": len(paths),
            "typed_promotion_readiness": {
                name: "ready_for_typed_representation_review"
                if readiness == "broad_current_corpus_supported" and all(name in row["fields"] for row in supported)
                else "structurally_supported_but_incomplete" if any(name in row["fields"] for row in supported)
                else "unresolved" for name, *_ in FIELDS},
            "valid_captures": valid, "text_captures": text_captures, "paragraphs_examined": len(rows),
            "production_candidates": sum(row["production_candidate"] for row in rows),
            "independently_derived_p": len(established), "shift_histogram": dict(shifts),
            "exact_182": shifts[182], "other_shifts": {k: v for k, v in shifts.items() if k != 182},
            "comparison_counts": {state: states[state] for state in STATES},
            "line_count_histogram": dict(Counter(row["structure"]["line_count"] for row in established)),
            "paragraphs_per_text_capture": dict(Counter(Counter(row["capture"] for row in rows).values())),
            "base_length_histogram": dict(Counter(row["structure"]["base_length"] for row in established)),
            "first_record_c_relative_histogram": dict(Counter(row["structure"]["first_attrchar"] for row in established)),
            "first_record_p_relative_histogram": dict(Counter(
                row["structure"]["first_attrchar"] - row["structure"]["p_origin"] for row in established)),
            "field_c_relative_histograms": {name: dict(Counter(row["fields"][name]["c_relative"]
                for row in supported if name in row["fields"])) for name, *_ in FIELDS},
            "observed_versions": versions,
            "ab_diagnostic": {"pairs": len(pairs), "equal_raw": sum(p["A"]["raw_hex"] == p["B"]["raw_hex"] for p in pairs),
                              "equal_numeric": sum(p["A"]["value"] == p["B"]["value"] for p in pairs)},
            "value_histograms": {name: dict(Counter(str(row["fields"][name]["value"])
                for row in supported if name in row["fields"])) for name, *_ in FIELDS},
            "input_issues": issues, "paragraphs": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="include per-paragraph traces")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report if args.json else {k: v for k, v in report.items() if k != "paragraphs"},
                     indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
