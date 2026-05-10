from __future__ import annotations

from typing import Any, Optional


def rank_contour_header_candidate(
    *,
    candidate: dict[str, Any],
    node_class_name: Optional[str],
) -> dict[str, Any]:
    base_structural_score = int(candidate.get("structural_score") or 0)

    node_context_score = 0
    if node_class_name == "CContour":
        node_context_score = 3
    elif node_class_name == "CPropertyExtend":
        node_context_score = -2

    decoded_record_count = int(candidate.get("decoded_record_count") or 0)
    role_richness = int(candidate.get("role_richness_score") or 0)
    record_richness_score = 0
    if decoded_record_count >= 2:
        record_richness_score += 2
    if decoded_record_count >= 3:
        record_richness_score += 1
    record_richness_score += role_richness

    degeneracy_penalty = 0
    if decoded_record_count <= 1:
        degeneracy_penalty -= 4
    if candidate.get("near_zero_extent"):
        degeneracy_penalty -= 3

    bbox_consistency = candidate.get("bbox_consistency_status")
    bbox_relation_score = 0
    if bbox_consistency == "consistent":
        bbox_relation_score = 2
    elif bbox_consistency == "mismatch_soft":
        bbox_relation_score = -1

    # Filled later after peer comparison.
    competition_score = 0

    refined_score = (
        base_structural_score
        + node_context_score
        + record_richness_score
        + degeneracy_penalty
        + bbox_relation_score
        + competition_score
    )
    return {
        "base_structural_score": base_structural_score,
        "node_context_score": node_context_score,
        "record_richness_score": record_richness_score,
        "degeneracy_penalty": degeneracy_penalty,
        "bbox_relation_score": bbox_relation_score,
        "competition_score": competition_score,
        "final_refined_score": refined_score,
    }


def choose_refined_recommended_candidate(
    *,
    scored_candidates: list[dict[str, Any]],
    legacy_shift_priority: list[int],
    min_quality_score: int = 1,
) -> Optional[dict[str, Any]]:
    if not scored_candidates:
        return None
    shift_order = {v: i for i, v in enumerate(legacy_shift_priority)}
    # competition score: favor richer candidate among structural-valid peers.
    max_count = max(int(c.get("count") or 0) for c in scored_candidates)
    for c in scored_candidates:
        comp = 1 if int(c.get("count") or 0) == max_count and max_count >= 2 else 0
        c["competition_score"] = comp
        c["final_refined_score"] = (
            int(c.get("base_structural_score") or 0)
            + int(c.get("node_context_score") or 0)
            + int(c.get("record_richness_score") or 0)
            + int(c.get("degeneracy_penalty") or 0)
            + int(c.get("bbox_relation_score") or 0)
            + comp
        )

    ranked = sorted(
        scored_candidates,
        key=lambda c: (
            -(int(c.get("final_refined_score") or -9999)),
            shift_order.get(int(c.get("shift") or -1), 9999),
            int(c.get("header_offset") or 10**9),
        ),
    )
    for idx, candidate in enumerate(ranked, start=1):
        candidate["refined_rank"] = idx
    winner = ranked[0]
    if int(winner.get("final_refined_score") or -9999) < min_quality_score:
        return None
    return winner
