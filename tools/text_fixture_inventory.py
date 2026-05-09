import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser


TEXT_SAMPLES_DIR = REPO_ROOT / "tests" / "samples" / "text"


def _infer_fixture_intent(path: Path) -> dict:
    name = path.name
    intent = {
        "fixture_intent_text": None,
        "fixture_intent_font": None,
        "fixture_intent_anchor": None,
        "fixture_intent_color": None,
        "is_multiline_family": False,
        "is_ungroup_family": False,
        "recapture_required": False,
        "intent_notes": [],
    }
    if name.startswith("text_origin_0_0"):
        intent["fixture_intent_anchor"] = {"x": 0.0, "y": 0.0, "z": 0.0}
    elif name.startswith("text_origin_offset"):
        intent["fixture_intent_anchor"] = {"x": 333.333, "y": 444.444, "z": 0.0}
    else:
        intent["fixture_intent_anchor"] = {"x": 111.111, "y": 222.222, "z": 0.0}

    if "group_same_color_two_objects" in name:
        intent["fixture_intent_color"] = ["Army Green", "Army Green"]
    elif "group_mixed_color_two_objects" in name:
        intent["fixture_intent_color"] = ["Army Green", "Navy Blue"]
    elif "two_objects_mixed_color_not_grouped" in name:
        intent["fixture_intent_color"] = ["Army Green", "Navy Blue"]
    elif "text_color_army_green" in name:
        intent["fixture_intent_color"] = "Army Green"
    elif "text_color_navy_blue" in name:
        intent["fixture_intent_color"] = "Navy Blue"
    elif name == "default_text.txt":
        intent["fixture_intent_color"] = "Black (observed baseline)"
    else:
        intent["fixture_intent_color"] = "Black"

    if "font_hy_gyeongo_dik" in name:
        intent["fixture_intent_font"] = "HY견고딕"
    elif "font_arial_bold" in name:
        intent["fixture_intent_font"] = "Arial Bold"
    elif "font_hy_se_gothic" in name:
        intent["fixture_intent_font"] = "HY세고딕"
    elif "font_hy_tae_gothic" in name:
        intent["fixture_intent_font"] = "HY태고딕"
    elif "font_hy_teuktae_gothic" in name:
        intent["fixture_intent_font"] = "HY특태고딕"
    else:
        intent["fixture_intent_font"] = "Arial"

    if "digits" in name:
        intent["fixture_intent_text"] = "1234567890"
    elif "ascii_uppercase" in name:
        intent["fixture_intent_text"] = "ABCDEFG"
    elif "lowercase_mode" in name:
        intent["fixture_intent_text"] = "ABCDEFG"
    elif "alphanumeric" in name:
        intent["fixture_intent_text"] = "A1B2C3d4"
    elif "spaces" in name:
        intent["fixture_intent_text"] = "ab cd ef"
    elif "special_characters" in name:
        intent["fixture_intent_text"] = "+-*/#@&()"
    elif "korean_basic" in name:
        intent["fixture_intent_text"] = "Korean text (fixture-defined)"
    elif "korean_mixed" in name:
        intent["fixture_intent_text"] = "Mixed Korean/ASCII (fixture-defined)"
    elif "multiline" in name or "spacing_fixed" in name or "spacing_proportional" in name or "spacing_print_proportional" in name:
        intent["fixture_intent_text"] = "abcd\\nefgh"
        intent["is_multiline_family"] = True
    else:
        intent["fixture_intent_text"] = "abcdefg"

    if "font_arial_bold" in name:
        intent["fixture_intent_text"] = "abcdefg"
    return intent


def _ascii_strings(data: bytes, min_len: int = 3) -> list[str]:
    out: list[str] = []
    buf: list[int] = []
    for b in data:
        if 32 <= b <= 126:
            buf.append(b)
            continue
        if len(buf) >= min_len:
            out.append(bytes(buf).decode("ascii", errors="ignore"))
        buf = []
    if len(buf) >= min_len:
        out.append(bytes(buf).decode("ascii", errors="ignore"))
    return out


def _font_candidates(data: bytes) -> list[str]:
    deny = {"CZone", "CCourbe", "CContour", "CPropertyExtend", "CParagraphe", "OBJECTINFOS_CLASSNAME", "CObDao"}
    fonts: list[str] = []
    for s in _ascii_strings(data, min_len=3):
        if s in deny:
            continue
        if "Arial" in s or s.startswith("HY"):
            if s not in fonts:
                fonts.append(s)
    return fonts


def _text_candidates_from_paragraphe(data: bytes) -> list[str]:
    parser = Type3ChainParser()
    nodes = parser._extract_nodes(data[6:])
    runs: list[str] = []
    for node in nodes:
        if node.header.class_name != "CParagraphe":
            continue
        for recs in parser._read_paragraphe_slot_record_runs(node.payload):
            run = parser._records_to_text_run(recs)
            if run is None:
                continue
            text = run["text"]
            if text not in runs:
                runs.append(text)
    return runs


def _color_candidates(parsed_obj) -> list[dict]:
    items: list[dict] = []
    for chain in getattr(parsed_obj, "object_chains", []) or []:
        for c in chain.style.color_candidates:
            rec = {
                "offset": c.get("offset"),
                "raw_hex": c.get("raw_hex"),
                "name": c.get("name"),
                "hex_rgb": c.get("hex_rgb"),
                "confidence": c.get("confidence"),
                "source": c.get("source"),
            }
            if rec not in items:
                items.append(rec)
    return items


def build_inventory_entry(path: Path) -> dict:
    raw_hex = path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(data)
    intent = _infer_fixture_intent(path)
    markers = list(getattr(parsed, "markers", []) or [])
    text_candidates = _text_candidates_from_paragraphe(data)
    object_chains = list(getattr(parsed, "object_chains", []) or [])
    parsed_chain_candidate_count = len(object_chains)
    chain_summaries: list[dict] = []
    for idx, chain in enumerate(object_chains, start=1):
        bbox = chain.bbox
        chain_summaries.append(
            {
                "index": idx,
                "markers": list(chain.markers),
                "text_candidate": chain.text_candidate,
                "source_text_candidate": chain.source_text_candidate,
                "display_text_candidate": chain.display_text_candidate,
                "font_candidate": getattr(parsed, "font_name", None),
                "line_count": chain.line_count,
                "text_anchor_mm": (
                    {
                        "x": chain.text_anchor.x,
                        "y": chain.text_anchor.y,
                        "z": chain.text_anchor.z,
                    }
                    if chain.text_anchor is not None
                    else None
                ),
                "bbox_mm": (
                    {
                        "xmin": bbox.xmin_mm,
                        "ymin": bbox.ymin_mm,
                        "zmin": bbox.zmin_mm,
                        "xmax": bbox.xmax_mm,
                        "ymax": bbox.ymax_mm,
                        "zmax": bbox.zmax_mm,
                        "width": bbox.width_mm,
                        "height": bbox.height_mm,
                    }
                    if bbox is not None
                    else None
                ),
                "line_color_name": chain.style.line_color_name,
                "line_color_confidence": chain.style.line_color_confidence,
                "line_color_source": chain.style.line_color_source,
                "anchor_expected_source": chain.text_anchor_expected_source,
                "anchor_parse_method": chain.text_anchor_parse_method or chain.text_anchor_source,
                "anchor_parse_confidence": chain.text_anchor_parse_confidence or chain.text_anchor_confidence,
                "provisional_notes": list(chain.text_notes),
            }
        )
    parser_text_candidate = text_candidates[0] if text_candidates else None
    parser_font_candidate = getattr(parsed, "font_name", None)
    parser_anchor_candidate = chain_summaries[0]["text_anchor_mm"] if chain_summaries else None
    parser_color_candidate = (
        [c["line_color_name"] for c in chain_summaries]
        if len(chain_summaries) > 1
        else (chain_summaries[0]["line_color_name"] if chain_summaries else None)
    )
    color_candidate_source = (
        [c["line_color_source"] for c in chain_summaries]
        if len(chain_summaries) > 1
        else (chain_summaries[0]["line_color_source"] if chain_summaries else None)
    )
    color_candidates_raw = _color_candidates(parsed)

    text_confidence = "candidate"
    if intent["fixture_intent_text"] and parser_text_candidate == intent["fixture_intent_text"]:
        text_confidence = "candidate_match"
    elif parser_text_candidate is None:
        text_confidence = "unresolved"

    font_confidence = "candidate"
    font_notes: list[str] = []
    if parser_font_candidate == intent["fixture_intent_font"]:
        font_confidence = "candidate_match"
    elif parser_font_candidate is None:
        font_confidence = "unresolved"
        font_notes.append("font_name_candidate unresolved")
    else:
        font_notes.append(
            f"expected={intent['fixture_intent_font']}, detected={parser_font_candidate}"
        )

    anchor_confidence = chain_summaries[0]["anchor_parse_confidence"] if chain_summaries else "unresolved"
    color_notes: list[str] = []
    if len(chain_summaries) > 1:
        color_confidence = "mixed_object_ownership_unresolved"
        color_notes.append("Per-object color ownership is provisional for multi-object text fixtures.")
    else:
        color_confidence = chain_summaries[0]["line_color_confidence"] if chain_summaries else "unresolved"
    if intent["fixture_intent_color"] and parser_color_candidate:
        if isinstance(intent["fixture_intent_color"], list):
            if not isinstance(parser_color_candidate, list) or len(parser_color_candidate) != len(intent["fixture_intent_color"]):
                color_confidence = "unresolved"
            elif parser_color_candidate != intent["fixture_intent_color"]:
                color_confidence = "mixed_object_ownership_unresolved"
                color_notes.append(
                    f"expected={intent['fixture_intent_color']}, detected={parser_color_candidate}"
                )
        else:
            if isinstance(parser_color_candidate, list):
                color_confidence = "mixed_object_ownership_unresolved"
            elif parser_color_candidate != intent["fixture_intent_color"]:
                color_confidence = "unresolved"
                color_notes.append(
                    f"expected={intent['fixture_intent_color']}, detected={parser_color_candidate}"
                )

    notes: list[str] = []
    notes.extend(intent["intent_notes"])
    recapture_required = bool(intent["recapture_required"])
    if path.name == "text_font_arial_bold.txt":
        if parser_text_candidate is not None and "\n" in parser_text_candidate:
            recapture_required = True
            notes.append(
                "Fixture intent mismatch: text_font_arial_bold.txt currently shows multiline evidence; recapture required."
            )
        else:
            recapture_required = False
    if intent["is_multiline_family"]:
        notes.append(
            "Multiline fixture: parsed_chain_candidate_count is parser chain count, not confirmed Type3 object count."
        )
    if "korean_" in path.name and not text_candidates:
        notes.append("Parser limitation: Korean visible text candidate extraction unresolved.")
    if "text_color_" in path.name and parser_color_candidate != intent["fixture_intent_color"]:
        notes.append("Parser limitation: expected text color and detected color mismatch.")
        color_notes.append("Single text object color candidate does not match fixture intent.")
    if "font_hy_" in path.name and parser_font_candidate != intent["fixture_intent_font"]:
        notes.append("Parser limitation: expected HY font and detected font mismatch.")
        font_notes.append("Korean font name storage unresolved")
    if "font_arial_bold" in path.name and parser_font_candidate != intent["fixture_intent_font"]:
        notes.append("Parser limitation: expected Arial Bold and detected font mismatch.")
        font_notes.append("Arial Bold storage mapping unresolved")

    return {
        "file": path.name,
        "normalized_bytes": len(data),
        "parser": parser_name,
        "declared_object_count": getattr(parsed, "declared_object_count", None),
        "parsed_chain_candidate_count": parsed_chain_candidate_count,
        "is_text_object": getattr(parsed, "is_text_object", False),
        "is_grouped": getattr(parsed, "is_grouped", False),
        "group_term_ko": getattr(parsed, "group_term_ko", None),
        "group_notes": list(getattr(parsed, "group_notes", []) or []),
        "markers": markers,
        "has_CZone": "CZone" in markers,
        "has_CParagraphe": "CParagraphe" in markers,
        "has_CCourbe": "CCourbe" in markers,
        "has_CContour": "CContour" in markers,
        "has_CPropertyExtend": "CPropertyExtend" in markers,
        "font_candidate": getattr(parsed, "font_name", None),
        "font_candidates_ascii": _font_candidates(data),
        "visible_text_candidates": text_candidates,
        "text_object_notes": list(getattr(parsed, "text_notes", []) or []),
        "color_candidates": _color_candidates(parsed),
        "color_candidates_raw": color_candidates_raw,
        "chains": chain_summaries,
        "fixture_intent_text": intent["fixture_intent_text"],
        "parser_text_candidate": parser_text_candidate,
        "fixture_intent_font": intent["fixture_intent_font"],
        "parser_font_candidate": parser_font_candidate,
        "fixture_intent_anchor": intent["fixture_intent_anchor"],
        "parser_anchor_candidate": parser_anchor_candidate,
        "anchor_parse_method": chain_summaries[0]["anchor_parse_method"] if chain_summaries else None,
        "fixture_intent_color": intent["fixture_intent_color"],
        "parser_color_candidate": parser_color_candidate,
        "color_candidate_source": color_candidate_source,
        "text_confidence": text_confidence,
        "font_confidence": font_confidence,
        "font_notes": font_notes,
        "anchor_confidence": anchor_confidence,
        "color_confidence": color_confidence,
        "color_notes": color_notes,
        "recapture_required": recapture_required,
        "notes": notes,
    }


def render_text(entries: list[dict]) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("Type3 Text Fixture Inventory")
    lines.append("=" * 72)
    for item in entries:
        lines.append(f"[{item['file']}]")
        lines.append(f"  bytes: {item['normalized_bytes']}")
        lines.append(f"  parser: {item['parser']}")
        lines.append(f"  declared_object_count: {item['declared_object_count']}")
        lines.append(f"  parsed_chain_candidate_count: {item['parsed_chain_candidate_count']}")
        lines.append(f"  is_text_object: {item['is_text_object']}")
        lines.append(f"  is_grouped: {item['is_grouped']}")
        lines.append(f"  markers: {', '.join(item['markers']) if item['markers'] else 'none'}")
        lines.append(
            "  has: "
            f"CZone={item['has_CZone']} "
            f"CParagraphe={item['has_CParagraphe']} "
            f"CCourbe={item['has_CCourbe']} "
            f"CContour={item['has_CContour']} "
            f"CPropertyExtend={item['has_CPropertyExtend']}"
        )
        lines.append(f"  font_candidates: {item['font_candidates_ascii'] or []}")
        lines.append(f"  fixture_intent_text: {item['fixture_intent_text']}")
        lines.append(f"  parser_text_candidate: {item['parser_text_candidate']}")
        lines.append(f"  fixture_intent_font: {item['fixture_intent_font']}")
        lines.append(f"  parser_font_candidate: {item['parser_font_candidate']}")
        lines.append(f"  fixture_intent_anchor: {item['fixture_intent_anchor']}")
        lines.append(f"  parser_anchor_candidate: {item['parser_anchor_candidate']}")
        lines.append(f"  anchor_parse_method: {item['anchor_parse_method']}")
        lines.append(f"  fixture_intent_color: {item['fixture_intent_color']}")
        lines.append(f"  parser_color_candidate: {item['parser_color_candidate']}")
        lines.append(f"  color_candidate_source: {item['color_candidate_source']}")
        lines.append(f"  color_candidates_raw: {item['color_candidates_raw']}")
        lines.append(f"  text_confidence: {item['text_confidence']}")
        lines.append(f"  font_confidence: {item['font_confidence']}")
        lines.append(f"  font_notes: {item['font_notes']}")
        lines.append(f"  anchor_confidence: {item['anchor_confidence']}")
        lines.append(f"  color_confidence: {item['color_confidence']}")
        lines.append(f"  color_notes: {item['color_notes']}")
        lines.append(f"  color_candidates: {len(item['color_candidates'])}")
        if item.get("recapture_required"):
            lines.append("  recapture_required: True")
        for note in item.get("notes", []):
            lines.append(f"  note: {note}")
        for chain in item["chains"]:
            lines.append(f"    [Chain #{chain['index']}]")
            lines.append(f"      text_candidate: {chain['text_candidate']}")
            lines.append(f"      source_text_candidate: {chain['source_text_candidate']}")
            lines.append(f"      display_text_candidate: {chain['display_text_candidate']}")
            lines.append(f"      line_count: {chain['line_count']}")
            lines.append(f"      line_color_name: {chain['line_color_name']}")
            lines.append(f"      line_color_confidence: {chain['line_color_confidence']}")
            lines.append(f"      anchor_expected_source: {chain['anchor_expected_source']}")
            lines.append(f"      anchor_parse_method: {chain['anchor_parse_method']}")
            lines.append(f"      anchor_parse_confidence: {chain['anchor_parse_confidence']}")
            lines.append(f"      text_anchor_mm: {chain['text_anchor_mm']}")
            lines.append(f"      bbox_mm: {chain['bbox_mm']}")
            if chain["provisional_notes"]:
                lines.append("      provisional_notes:")
                for note in chain["provisional_notes"]:
                    lines.append(f"        - {note}")
    return "\n".join(lines)


def render_markdown(entries: list[dict]) -> str:
    lines: list[str] = []
    lines.append("| file | declared_object_count | parsed_chain_candidate_count | fixture_intent_text | parser_text_candidate | fixture_intent_font | parser_font_candidate | font_notes | fixture_intent_anchor | parser_anchor_candidate | anchor_parse_method | fixture_intent_color | parser_color_candidate | color_candidate_source | color_confidence | color_notes | text_confidence | font_confidence | anchor_confidence | notes |")
    lines.append("|---|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for item in entries:
        intent_anchor = item.get("fixture_intent_anchor")
        parser_anchor = item.get("parser_anchor_candidate")
        intent_anchor_s = (
            f"({intent_anchor['x']:.3f},{intent_anchor['y']:.3f},{intent_anchor['z']:.3f})"
            if intent_anchor else "-"
        )
        parser_anchor_s = (
            f"({parser_anchor['x']:.3f},{parser_anchor['y']:.3f},{parser_anchor['z']:.3f})"
            if parser_anchor else "-"
        )
        notes = "; ".join(item.get("notes", [])) if item.get("notes") else "-"
        lines.append(
            "| "
            f"{item['file']} | {item['declared_object_count']} | {item['parsed_chain_candidate_count']} | "
            f"{str(item.get('fixture_intent_text') or '-').replace('|', '\\|').replace(chr(10), '<br>')} | "
            f"{str(item.get('parser_text_candidate') or '-').replace('|', '\\|').replace(chr(10), '<br>')} | "
            f"{item.get('fixture_intent_font') or '-'} | {item.get('parser_font_candidate') or '-'} | "
            f"{('; '.join(item.get('font_notes') or ['-'])).replace('|', '\\|')} | "
            f"{intent_anchor_s} | {parser_anchor_s} | {item.get('anchor_parse_method') or '-'} | "
            f"{item.get('fixture_intent_color') or '-'} | {item.get('parser_color_candidate') or '-'} | "
            f"{str(item.get('color_candidate_source') or '-').replace('|', '\\|')} | "
            f"{item.get('color_confidence') or '-'} | "
            f"{('; '.join(item.get('color_notes') or ['-'])).replace('|', '\\|')} | "
            f"{item.get('text_confidence') or '-'} | {item.get('font_confidence') or '-'} | "
            f"{item.get('anchor_confidence') or '-'} | "
            f"{notes.replace('|', '\\|')} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan tests/samples/text fixtures and print quick inventory.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--markdown", action="store_true", dest="as_markdown")
    args = parser.parse_args(argv)

    entries = [build_inventory_entry(path) for path in sorted(TEXT_SAMPLES_DIR.glob("*.txt"))]
    if args.as_json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    elif args.as_markdown:
        print(render_markdown(entries))
    else:
        print(render_text(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
