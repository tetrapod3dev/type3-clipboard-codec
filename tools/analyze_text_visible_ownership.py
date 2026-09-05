from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject, Point, Type3Node
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
INTENT_DIR = REPO_ROOT / "tests" / "samples" / "intents" / "text"
TOP_LEVEL_HEADER_LEN = 6

FIXTURES = [
    "text_group_same_color_two_objects.txt",
    "text_group_mixed_color_two_objects.txt",
    "text_two_objects_mixed_color_not_grouped.txt",
    "text_two_objects_same_color_not_grouped.txt",
    "text_two_objects_not_grouped_selection_reversed.txt",
    "text_three_objects_grouped_order_abc.txt",
    "text_three_objects_grouped_order_cba.txt",
    "text_three_objects_not_grouped.txt",
    "text_three_objects_grouped_order_abc_mixed_color.txt",
    "text_three_objects_not_grouped_mixed_color.txt",
    "text_three_objects_grouped_order_abc_height_30mm.txt",
    "text_three_objects_grouped_order_abc_font_arial_bold.txt",
    "text_three_objects_grouped_order_abc_content_variation.txt",
]


def _read_fixture(path: Path) -> bytes:
    return hex_text_to_bytes(path.read_text(encoding="utf-8"))


def _read_nodes(blob: bytes) -> list[Type3Node]:
    return Type3ChainParser()._extract_nodes(blob[TOP_LEVEL_HEADER_LEN:])


def _point_mm(point: Point | None) -> dict[str, float] | None:
    if point is None:
        return None
    return {"x": round(point.x, 6), "y": round(point.y, 6), "z": round(point.z, 6)}


def _decode_cparagraphe_direct_anchor(payload: bytes) -> dict[str, float] | None:
    if len(payload) < 182:
        return None
    x_m, y_m, z_m = struct.unpack("<ddd", payload[158:182])
    if not all(math.isfinite(v) for v in (x_m, y_m, z_m)):
        return None
    return {"x": round(x_m * 1000.0, 6), "y": round(y_m * 1000.0, 6), "z": round(z_m * 1000.0, 6)}


def _same_point(a: dict[str, float] | None, b: dict[str, float] | None, tol_mm: float = 1e-6) -> bool:
    if a is None or b is None:
        return False
    return (
        abs(a["x"] - b["x"]) <= tol_mm
        and abs(a["y"] - b["y"]) <= tol_mm
        and abs(a["z"] - b["z"]) <= tol_mm
    )


def _parse_attempted_order(raw: str | None, text_content: list[str] | None = None) -> list[str] | None:
    if raw is None:
        return None
    normalized = re.sub(r"\(.*?\)", "", raw).strip()
    normalized = normalized.replace("`", "")
    if "->" in raw:
        parts = [part.strip() for part in normalized.split("->") if part.strip()]
        mapping = {"A": 0, "B": 1, "C": 2, "D": 3}
        if text_content:
            resolved: list[str] = []
            for part in parts:
                idx = mapping.get(part)
                if idx is not None and idx < len(text_content):
                    resolved.append(text_content[idx])
                else:
                    resolved.append(part)
            return resolved
        return parts
    return [normalized] if normalized else None


def _validate_intent_metadata(meta: Any) -> dict[str, Any]:
    """Validate reporting data only; never pass it to a payload parser."""
    if not isinstance(meta, dict):
        raise ValueError("intent_metadata must be a mapping")
    if type(meta.get("schema_version")) is not int or meta["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if type(meta.get("object_count")) is not int or meta["object_count"] < 1:
        raise ValueError("object_count must be a positive integer")
    if meta.get("grouping") not in ("grouped", "not_grouped", "unknown"):
        raise ValueError("invalid grouping")
    status = meta.get("order_control_status")
    if status not in ("attempted", "unknown", "controlled_observed"):
        raise ValueError("invalid order_control_status")
    if meta.get("actual_stored_order") != "unresolved":
        raise ValueError("actual_stored_order must remain unresolved in schema v1")
    notes = meta.get("notes")
    if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
        raise ValueError("notes must be a list of strings")
    order = meta.get("attempted_selection_order")
    if not isinstance(order, list):
        raise ValueError("attempted_selection_order must be a list")
    if (status == "unknown" and order) or (status != "unknown" and len(order) != meta["object_count"]):
        raise ValueError("attempted_selection_order does not match status/object_count")
    labels = []
    for entry in order:
        if not isinstance(entry, dict) or any(
            not isinstance(entry.get(key), str) or not entry[key] for key in ("label", "text", "color")
        ):
            raise ValueError("each order entry needs string label, text and color")
        anchor = entry.get("anchor_mm")
        if not isinstance(anchor, list) or len(anchor) != 3 or not all(
            type(value) in (int, float) and math.isfinite(value) for value in anchor
        ):
            raise ValueError("anchor_mm must contain three finite numbers")
        labels.append(entry["label"])
    if len(set(labels)) != len(labels):
        raise ValueError("order labels must be unique")
    return {key: meta[key] for key in (
        "schema_version", "object_count", "grouping", "order_control_status",
        "attempted_selection_order", "actual_stored_order", "notes",
    )}


def _intent_metadata(fixture: str) -> dict[str, Any]:
    path = INTENT_DIR / fixture.replace(".txt", ".md")
    meta: dict[str, Any] = {
        "grouping": "unknown",
        "attempted_selection_order": None,
        "actual_stored_order": "unresolved",
        "order_control_status": "unknown",
        "attempted_order_source": "missing",
        "normalized_intent_metadata": None,
        "warnings": [],
    }
    if "_not_grouped" in fixture:
        meta["grouping"] = "not_grouped"
    elif "_group_" in fixture or "_grouped_" in fixture:
        meta["grouping"] = "grouped"
    if not path.exists():
        meta["warnings"].append(f"missing intent file: {path.name}")
        return meta

    text = path.read_text(encoding="utf-8")
    blocks = [block for block in re.findall(
        r"^```(?:yaml|yml)[ \t]*\r?\n(.*?)^```[ \t]*$", text, re.MULTILINE | re.DOTALL
    ) if re.search(r"^intent_metadata\s*:", block, re.MULTILINE)]
    if blocks:
        try:
            if len(blocks) != 1:
                raise ValueError("expected one intent_metadata block")
            normalized = _validate_intent_metadata(yaml.safe_load(blocks[0])["intent_metadata"])
        except (yaml.YAMLError, ValueError, TypeError, KeyError) as exc:
            meta["warnings"].append(f"invalid intent metadata: {path.name}: {exc}")
        else:
            meta.update({key: normalized[key] for key in (
                "grouping", "order_control_status", "actual_stored_order",
            )})
            meta["normalized_intent_metadata"] = normalized
            meta["attempted_order_source"] = "yaml"
            meta["attempted_selection_order"] = [entry["text"] for entry in normalized["attempted_selection_order"]] or None
            return meta
    else:
        meta["warnings"].append(f"missing intent metadata: {path.name}")
    meta["attempted_order_source"] = "filename_or_unknown"
    grouped_match = re.search(r"- grouped/not grouped:[ \t]*(.+)", text)
    if grouped_match:
        grouped = grouped_match.group(1).strip().lower().replace("-", "_")
        meta["grouping"] = grouped if grouped in {"grouped", "not_grouped"} else "unknown"
    content_match = re.search(r"- text content:[ \t]*(.+)", text)
    text_content: list[str] | None = None
    if content_match:
        text_content = [part.strip() for part in content_match.group(1).split("|") if part.strip()]
    attempted_match = re.search(r"- attempted selection order:[ \t]*(.+)", text)
    if attempted_match and attempted_match.group(1).strip().lower() != "unknown":
        meta["attempted_selection_order"] = _parse_attempted_order(attempted_match.group(1).strip(), text_content)
        meta["attempted_order_source"] = "loose_text"
        meta["order_control_status"] = "attempted"
    meta["normalized_intent_metadata"] = {
        "schema_version": 1,
        "object_count": 3 if "three_objects" in fixture else 2,
        "grouping": meta["grouping"],
        "order_control_status": meta["order_control_status"],
        "attempted_selection_order": [
            {"label": None, "text": value, "anchor_mm": None, "color": None}
            for value in meta["attempted_selection_order"] or []
        ],
        "actual_stored_order": "unresolved",
        "notes": ["legacy fallback; unrecorded object attributes remain null"],
    }
    return meta


def _fixture_report(fixture: str) -> dict[str, Any]:
    blob = _read_fixture(TEXT_DIR / fixture)
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(blob)
    if not isinstance(parsed, GeometryObject):
        raise TypeError(f"{fixture} did not parse as GeometryObject")
    nodes = _read_nodes(blob)
    intent = _intent_metadata(fixture)

    chains: list[dict[str, Any]] = []
    text_order: list[str | None] = []
    anchor_order: list[dict[str, float] | None] = []
    for idx, chain in enumerate(parsed.object_chains):
        text_candidate = chain.source_text_candidate or chain.text_candidate
        anchor = _point_mm(chain.text_anchor)
        text_order.append(text_candidate)
        anchor_order.append(anchor)
        chains.append(
            {
                "fixture": fixture,
                "chain_index": idx,
                "text_candidate": text_candidate,
                "text_confidence": "provisional",
                "anchor_candidate": anchor,
                "anchor_confidence": chain.text_anchor_parse_confidence or chain.text_anchor_confidence or "provisional",
                "anchor_parse_method": chain.text_anchor_parse_method or chain.text_anchor_source or "unknown",
                "notes": "text-run ownership and anchor ownership are analyzed separately",
            }
        )

    cpar_direct = None
    cpar_owner_chain_indexes: list[int] = []
    for node in nodes:
        if node.header.class_name != "CParagraphe":
            continue
        cpar_direct = _decode_cparagraphe_direct_anchor(node.payload)
        if cpar_direct is None:
            continue
        for chain in chains:
            if _same_point(cpar_direct, chain["anchor_candidate"]):
                cpar_owner_chain_indexes.append(chain["chain_index"])
        break

    cpar_owner_text = [chains[i]["text_candidate"] for i in cpar_owner_chain_indexes] if cpar_owner_chain_indexes else []
    cproperty_candidates = (parsed.candidate_fields or {}).get("cproperty_anchor_candidates") or []
    parser_order_known = all(item is not None for item in text_order)
    attempted = intent["attempted_selection_order"]
    if attempted is None or not parser_order_known:
        attempted_matches = "unknown"
    else:
        attempted_matches = attempted == text_order

    return {
        "fixture": fixture,
        "parser_name": parser_name,
        "grouping": intent["grouping"],
        "normalized_intent_metadata": intent["normalized_intent_metadata"],
        "attempted_order_source": intent["attempted_order_source"],
        "order_control_status": intent["order_control_status"],
        "intent_warnings": intent["warnings"],
        "attempted_selection_order": intent["attempted_selection_order"],
        "actual_stored_order": "unresolved",
        "parser_chain_count": len(chains),
        "parser_chain_text_order": text_order,
        "parser_chain_anchor_order": anchor_order,
        "cparagraphe_direct_anchor_owner_text": cpar_owner_text,
        "cparagraphe_direct_anchor_owner_chain_indexes": cpar_owner_chain_indexes,
        "cparagraphe_direct_anchor_evidence": cpar_direct,
        "cproperty_anchor_candidate_count": len(cproperty_candidates),
        "cproperty_anchor_ownership_status": "unresolved",
        "attempted_order_matches_parser_chain_order": attempted_matches,
        "chain_details": chains,
    }


def _build_report() -> dict[str, Any]:
    warnings: list[str] = []
    missing: list[str] = []
    fixtures: list[dict[str, Any]] = []
    missing_intents = []
    for fixture in FIXTURES:
        intent_path = INTENT_DIR / Path(fixture).with_suffix(".md").name
        if not intent_path.exists():
            missing_intents.append(intent_path.name)
        path = TEXT_DIR / fixture
        if not path.exists():
            missing.append(fixture)
            warnings.append(f"missing fixture: {fixture}")
            if not intent_path.exists():
                warnings.append(f"missing intent file: {intent_path.name}")
            continue
        fixtures.append(_fixture_report(fixture))
        warnings.extend(fixtures[-1]["intent_warnings"])

    grouped = [f for f in fixtures if f["grouping"] == "grouped"]
    not_grouped = [f for f in fixtures if f["grouping"] == "not_grouped"]
    grouped_orders = {tuple(f["parser_chain_text_order"]) for f in grouped if f["parser_chain_text_order"]}
    not_grouped_orders = {tuple(f["parser_chain_text_order"]) for f in not_grouped if f["parser_chain_text_order"]}
    grouped_effect = "observed" if grouped_orders and not_grouped_orders and grouped_orders != not_grouped_orders else "provisional"

    order_analysis = []
    for f in fixtures:
        order_analysis.append(
            {
                "fixture": f["fixture"],
                "attempted_selection_order": f["attempted_selection_order"],
                "parser_chain_text_order": f["parser_chain_text_order"],
                "parser_chain_anchor_order": f["parser_chain_anchor_order"],
                "cparagraphe_owner_text": f["cparagraphe_direct_anchor_owner_text"],
                "attempted_order_matches_parser_chain_order": f["attempted_order_matches_parser_chain_order"],
                "parser_chain_order_stability": "observed" if f["parser_chain_text_order"] else "unknown",
                "grouped_not_grouped_effect": grouped_effect,
            }
        )

    conclusions = {
        "stable_observations": [
            "parser chain text candidates are consistently emitted per chain across available fixtures",
            "CPropertyExtend anchor candidates are present as provisional evidence and remain ownership-unresolved",
            "active anchor parser behavior is unchanged",
        ],
        "provisional_observations": [
            "parser chain text order appears stable within each fixture family but should remain provisional for parser-rule claims",
            "attempted selection order can differ from parser chain text order",
            "grouped/not-grouped can correlate with ownership/ordering outcomes in current fixtures",
        ],
        "unresolved": [
            "actual stored order",
            "selection/primary object semantics",
            "CPropertyExtend anchor ownership assignment",
            "per-object text-run ownership vs anchor ownership final rule",
        ],
    }

    answers = {
        "parser_behavior": "not_modified",
        "visible_text_ownership_status": "observed_or_provisional",
        "parser_readiness": "analyzer_only",
        "q1_text_candidate_stable_separation": "observed_with_provisional_confidence",
        "q2_parser_chain_order_basis": "unknown_or_payload_order_like",
        "q3_attempted_vs_parser_order_independence": "observed_in_some_fixtures",
        "q4_grouping_effect_on_ownership": grouped_effect,
        "q5_content_variation_order_change": "content variation keeps parser_chain_text_order as observed sequence in current fixture",
        "q6_text_vs_anchor_stability": "text_candidate_ownership_appears_more_stable_than_anchor_ownership",
        "q7_visible_text_ownership_confirmed": "provisional",
    }

    return {
        "policy": {
            "scope": "visible text ownership analysis only",
            "parser_behavior": "not_modified",
            "cproperty_anchor_ownership": "not_assigned",
            "active_anchor_behavior": "unchanged",
        },
        "limits": {
            "text_max_chars": 50000,
            "json_max_chars": 100000,
            "default_execution": "fast",
        },
        "warnings": warnings,
        "missing_fixtures": missing,
        "missing_intent_files": missing_intents,
        "intent_metadata_summary": {
            "total_fixtures": len(fixtures),
            "with_yaml_metadata": sum(f["attempted_order_source"] == "yaml" for f in fixtures),
            "missing_metadata": sum(f["attempted_order_source"] != "yaml" for f in fixtures),
            "unknown_order_count": sum(f["order_control_status"] == "unknown" for f in fixtures),
            "attempted_order_count": sum(f["order_control_status"] == "attempted" for f in fixtures),
            "controlled_observed_count": sum(f["order_control_status"] == "controlled_observed" for f in fixtures),
        },
        "fixture_summaries": [
            {
                "fixture": f["fixture"],
                "grouping": f["grouping"],
                "attempted_order": f["attempted_selection_order"],
                "normalized_intent_metadata": f["normalized_intent_metadata"],
                "attempted_order_source": f["attempted_order_source"],
                "order_control_status": f["order_control_status"],
                "actual_stored_order": f["actual_stored_order"],
                "parser_chain_text_order": f["parser_chain_text_order"],
                "parser_chain_anchor_order": f["parser_chain_anchor_order"],
                "cparagraphe_owner_text": f["cparagraphe_direct_anchor_owner_text"],
                "cproperty_anchor_candidate_count": f["cproperty_anchor_candidate_count"],
                "ownership_status": "unresolved",
            }
            for f in fixtures
        ],
        "chain_details": [d for f in fixtures for d in f["chain_details"]],
        "order_analysis_summary": order_analysis,
        "conclusions": conclusions,
        "answers": answers,
    }


def _render_fixture_table(report: dict[str, Any]) -> str:
    lines = [
        "fixture | grouping | attempted_order | parser_chain_text_order | parser_chain_anchor_order | cparagraphe_owner_text | cproperty_anchor_candidate_count | ownership_status",
        "---|---|---|---|---|---|---:|---",
    ]
    for row in report["fixture_summaries"]:
        lines.append(
            f"{row['fixture']} | {row['grouping']} | {row['attempted_order']} | "
            f"{row['parser_chain_text_order']} | {row['parser_chain_anchor_order']} | "
            f"{row['cparagraphe_owner_text']} | {row['cproperty_anchor_candidate_count']} | unresolved"
        )
    return "\n".join(lines)


def _render_chain_table(report: dict[str, Any]) -> str:
    lines = [
        "fixture | chain_index | text_candidate | anchor | text_confidence | anchor_confidence | anchor_parse_method | notes",
        "---|---:|---|---|---|---|---|---",
    ]
    for row in report["chain_details"]:
        lines.append(
            f"{row['fixture']} | {row['chain_index']} | {row['text_candidate']} | "
            f"{row['anchor_candidate']} | {row['text_confidence']} | {row['anchor_confidence']} | "
            f"{row['anchor_parse_method']} | {row['notes']}"
        )
    return "\n".join(lines)


def _print_text(report: dict[str, Any]) -> None:
    print("Text Visible Ownership Analysis")
    print("Policy: parser not modified, CPropertyExtend ownership not assigned, active anchor unchanged")
    if report["warnings"]:
        print("Warnings:")
        for w in report["warnings"]:
            print(f"- {w}")
    print()
    print("Fixture Summary Table")
    print(_render_fixture_table(report))
    print()
    print("Chain Detail Table")
    print(_render_chain_table(report))
    print()
    print("Order Analysis Summary")
    for row in report["order_analysis_summary"]:
        print(
            f"- {row['fixture']}: attempted={row['attempted_selection_order']} "
            f"parser_text={row['parser_chain_text_order']} match={row['attempted_order_matches_parser_chain_order']} "
            f"grouped_effect={row['grouped_not_grouped_effect']}"
        )
    print()
    print("Conclusions")
    print("Stable observations:")
    for item in report["conclusions"]["stable_observations"]:
        print(f"- {item}")
    print("Provisional observations:")
    for item in report["conclusions"]["provisional_observations"]:
        print(f"- {item}")
    print("Unresolved:")
    for item in report["conclusions"]["unresolved"]:
        print(f"- {item}")


def _print_markdown(report: dict[str, Any]) -> None:
    print("# Text Visible Ownership Analysis")
    print()
    if report["warnings"]:
        print("## Warnings")
        print()
        for w in report["warnings"]:
            print(f"- {w}")
        print()
    print("## Fixture Summary Table")
    print()
    print("| fixture | grouping | attempted_order | parser_chain_text_order | parser_chain_anchor_order | cparagraphe_owner_text | cproperty_anchor_candidate_count | ownership_status |")
    print("|---|---|---|---|---|---|---:|---|")
    for row in report["fixture_summaries"]:
        print(
            f"| {row['fixture']} | {row['grouping']} | {row['attempted_order']} | "
            f"{row['parser_chain_text_order']} | {row['parser_chain_anchor_order']} | "
            f"{row['cparagraphe_owner_text']} | {row['cproperty_anchor_candidate_count']} | unresolved |"
        )
    print()
    print("## Chain Detail Table")
    print()
    print("| fixture | chain_index | text_candidate | anchor | text_confidence | anchor_confidence | anchor_parse_method | notes |")
    print("|---|---:|---|---|---|---|---|---|")
    for row in report["chain_details"]:
        print(
            f"| {row['fixture']} | {row['chain_index']} | {row['text_candidate']} | {row['anchor_candidate']} | "
            f"{row['text_confidence']} | {row['anchor_confidence']} | {row['anchor_parse_method']} | {row['notes']} |"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze visible text ownership across multi-object text fixtures.")
    parser.add_argument("--json", action="store_true", help="output compact JSON")
    parser.add_argument("--markdown", action="store_true", help="output markdown summary tables")
    args = parser.parse_args()

    report = _build_report()
    if args.json:
        raw = json.dumps(report, ensure_ascii=False, separators=(",", ":"))
        print(raw)
    elif args.markdown:
        _print_markdown(report)
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
