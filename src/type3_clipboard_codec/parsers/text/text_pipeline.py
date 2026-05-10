from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ...models.geometry import BBox3D, Type3Node, Type3ObjectChain
from ..style.property_extend_parser import downgrade_unverified_text_color_selection
from .cparagraphe_parser import (
    attach_text_anchor_candidates,
    attach_text_runs_to_chains,
    extract_font_candidates,
    extract_font_name,
    extract_text_runs,
)


@dataclass
class TextPipelineResult:
    font_candidates: List[dict[str, Any]] = field(default_factory=list)
    font_name: Optional[str] = None
    font_offset: Optional[int] = None
    font_context: Optional[bytes] = None
    raw_text_records: List[bytes] = field(default_factory=list)
    text_notes: List[str] = field(default_factory=list)
    text_content: Optional[str] = None
    czone_bbox: Optional[BBox3D] = None


def run_text_pipeline(
    *,
    full_data: bytes,
    all_nodes: List[Type3Node],
    chains: List[Type3ObjectChain],
    is_text_object: bool,
    known_font_markers: set[str],
) -> TextPipelineResult:
    font_candidates = extract_font_candidates(full_data)
    font_name, font_offset, font_context = extract_font_name(
        full_data, known_font_markers, font_candidates
    )
    result = TextPipelineResult(
        font_candidates=font_candidates,
        font_name=font_name,
        font_offset=font_offset,
        font_context=font_context,
    )

    if not is_text_object:
        return result

    result.czone_bbox = _first_bbox_for_class(all_nodes, "CZone")
    text_runs, result.raw_text_records, result.text_notes = extract_text_runs(all_nodes)
    attach_text_runs_to_chains(chains, text_runs)
    attach_text_anchor_candidates(chains)
    downgrade_unverified_text_color_selection(chains)
    if chains:
        chains.sort(
            key=lambda c: (
                c.text_anchor.x
                if c.text_anchor is not None
                else (c.bbox.center_mm.x if c.bbox else float("inf")),
                c.text_anchor.y
                if c.text_anchor is not None
                else (c.bbox.center_mm.y if c.bbox else float("inf")),
            )
        )
    result.text_content = text_runs[0]["text"] if text_runs else None
    result.text_notes.append(
        "Text object parsing is provisional; unknown CParagraphe bytes are preserved in raw_data and node payloads."
    )
    if len(chains) > 1:
        result.text_notes.append(
            "Per-object text-run ownership and per-object mixed-color ownership are still provisional for multi-text fixtures."
        )
    if result.font_name is None:
        result.text_notes.append("Korean font name storage unresolved (font_name_candidate not decoded).")
    return result


def _first_bbox_for_class(nodes: List[Type3Node], class_name: str) -> Optional[BBox3D]:
    for node in nodes:
        if node.header.class_name == class_name and node.bbox is not None:
            return node.bbox
    return None
