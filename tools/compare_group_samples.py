import argparse
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser
from type3_clipboard_codec.utils.hex_text import hex_to_bytes


@dataclass
class MarkerInfo:
    class_name: str
    start_offset: int
    payload_offset: int
    end_offset: int
    payload_size: int
    bbox_mm: tuple[float, float, float, float, float, float] | None


def contiguous_diff_ranges(data_a: bytes, data_b: bytes) -> List[Tuple[int, int]]:
    limit = min(len(data_a), len(data_b))
    ranges: List[Tuple[int, int]] = []
    start = -1
    for idx in range(limit):
        if data_a[idx] != data_b[idx]:
            if start < 0:
                start = idx
            continue
        if start >= 0:
            ranges.append((start, idx))
            start = -1
    if start >= 0:
        ranges.append((start, limit))
    if len(data_a) != len(data_b):
        ranges.append((limit, max(len(data_a), len(data_b))))
    return ranges


def decode_fixture(path: Path) -> bytes:
    return hex_to_bytes(path.read_text(encoding="utf-8"))


def fmt_bbox_mm(bbox: tuple[float, float, float, float, float, float] | None) -> str:
    if bbox is None:
        return "n/a"
    return (
        f"x({bbox[0]:.3f}~{bbox[3]:.3f}) "
        f"y({bbox[1]:.3f}~{bbox[4]:.3f}) "
        f"z({bbox[2]:.3f}~{bbox[5]:.3f})"
    )


def extract_markers(parser: Type3ChainParser, payload: bytes) -> List[MarkerInfo]:
    nodes = parser._extract_nodes(payload)  # reverse-engineering tool
    infos: List[MarkerInfo] = []
    for node in nodes:
        bbox_mm = None
        if node.bbox is not None:
            bbox_mm = (
                node.bbox.xmin_mm,
                node.bbox.ymin_mm,
                node.bbox.zmin_mm,
                node.bbox.xmax_mm,
                node.bbox.ymax_mm,
                node.bbox.zmax_mm,
            )
        infos.append(
            MarkerInfo(
                class_name=node.header.class_name,
                start_offset=node.start_offset,
                payload_offset=node.payload_offset,
                end_offset=node.end_offset,
                payload_size=len(node.payload),
                bbox_mm=bbox_mm,
            )
        )
    return infos


def contour_header_candidates(parser: Type3ChainParser, payload: bytes) -> List[dict]:
    rows: List[dict] = []
    for node in parser._extract_nodes(payload):
        if node.header.class_name not in {"CContour", "CPropertyExtend"}:
            continue
        headers = parser._read_contour_header(node.payload) or []
        for kind, count, offset in headers:
            rows.append(
                {
                    "class_name": node.header.class_name,
                    "kind": kind,
                    "count": count,
                    "payload_offset": offset,
                    "stream_offset": node.payload_offset + offset,
                }
            )
    return rows


def file_report(path: Path, data: bytes, parser: Type3ChainParser) -> List[str]:
    lines: List[str] = []
    declared = struct.unpack("<H", data[4:6])[0] if len(data) >= 6 else None
    payload_offset = 6 if len(data) >= 6 else 0
    payload = data[payload_offset:]
    markers = extract_markers(parser, payload)
    contour_candidates = contour_header_candidates(parser, payload)

    lines.append(f"== {path.name} ==")
    lines.append(f"- file size: {len(data)} bytes")
    lines.append(f"- declared object count: {declared}")
    lines.append(f"- marker order: {' -> '.join(m.class_name for m in markers)}")
    lines.append("- markers with offsets/payload ranges:")
    for m in markers:
        lines.append(
            "  "
            f"* {m.class_name}: marker@{m.start_offset}, payload[{m.payload_offset}:{m.end_offset}] "
            f"({m.payload_size} bytes), bbox={fmt_bbox_mm(m.bbox_mm)}"
        )
    lines.append("- contour count candidates:")
    for c in contour_candidates:
        lines.append(
            "  "
            f"* {c['class_name']}: kind={c['kind']}, count={c['count']}, "
            f"payload_offset={c['payload_offset']}, stream_offset={c['stream_offset']}"
        )
    if not contour_candidates:
        lines.append("  * none")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Type3 fixtures for 결합/group structure analysis.")
    parser.add_argument(
        "left",
        nargs="?",
        default="tests/samples/two_rectangle.txt",
        help="left fixture path",
    )
    parser.add_argument(
        "right",
        nargs="?",
        default="tests/samples/two_rectangle_group.txt",
        help="right fixture path",
    )
    args = parser.parse_args()

    left_path = Path(args.left)
    right_path = Path(args.right)
    left_data = decode_fixture(left_path)
    right_data = decode_fixture(right_path)
    type3_parser = Type3ChainParser()

    print("\n".join(file_report(left_path, left_data, type3_parser)))
    print()
    print("\n".join(file_report(right_path, right_data, type3_parser)))
    print()

    left_markers = [m.class_name for m in extract_markers(type3_parser, left_data[6:])]
    right_markers = [m.class_name for m in extract_markers(type3_parser, right_data[6:])]
    print("== Structural comparison ==")
    print(f"- additional markers in right: {sorted(set(right_markers) - set(left_markers)) or 'none'}")
    print(f"- additional markers in left: {sorted(set(left_markers) - set(right_markers)) or 'none'}")

    diffs = contiguous_diff_ranges(left_data, right_data)
    print(f"- byte ranges that differ: {len(diffs)}")
    for start, end in diffs[:40]:
        print(f"  * [{start}:{end}] ({end - start} bytes)")
    if len(diffs) > 40:
        print(f"  * ... {len(diffs) - 40} additional ranges omitted")

    left_declared = struct.unpack("<H", left_data[4:6])[0] if len(left_data) >= 6 else None
    right_declared = struct.unpack("<H", right_data[4:6])[0] if len(right_data) >= 6 else None
    print("- inferred structural impact:")
    if left_declared != right_declared:
        print(
            f"  * declared object count changed ({left_declared} -> {right_declared}); possible wrapper/container from 결합."
        )
    else:
        print("  * declared object count unchanged.")

    left_contours = contour_header_candidates(type3_parser, left_data[6:])
    right_contours = contour_header_candidates(type3_parser, right_data[6:])
    if left_contours != right_contours:
        print("  * contour ownership/header layout changed (CContour/CPropertyExtend candidates differ).")
    else:
        print("  * contour ownership/header layout unchanged.")

    print("  * conservative note: unknown bytes are not interpreted here; keep them preserved in parser models.")


if __name__ == "__main__":
    main()
