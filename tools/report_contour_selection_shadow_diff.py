from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_ROOT = REPO_ROOT / "tests" / "samples"
TEXT_SAMPLES_ROOT = SAMPLES_ROOT / "text"
LOW_MARGIN_THRESHOLD = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report legacy vs refined contour selection shadow diff.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--markdown", action="store_true", help="Emit markdown output.")
    parser.add_argument("--include-text", action="store_true", help="Include text fixtures as scan candidates.")
    return parser.parse_args()


def _iter_fixture_paths(include_text: bool) -> list[Path]:
    paths = sorted(SAMPLES_ROOT.glob("*.txt"))
    if include_text:
        paths.extend(sorted(TEXT_SAMPLES_ROOT.glob("*.txt")))
    return paths


def _decode_fixture(path: Path) -> GeometryObject | None:
    raw_hex = path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, _ = parse_type3_clipboard_bytes_with_parser(data)
    if not isinstance(parsed, GeometryObject):
        return None
    return parsed


def _candidate_key(candidate: dict[str, Any] | None) -> tuple[int | None, int | None, int | None] | None:
    if candidate is None:
        return None
    return (
        candidate.get("shift"),
        candidate.get("kind"),
        candidate.get("count"),
    )


def _is_auxiliary(candidate: dict[str, Any]) -> bool:
    return (
        candidate.get("node_class_name") == "CPropertyExtend"
        and candidate.get("kind") == 3
        and candidate.get("count") == 1
    )


def _summarize_fixture(path: Path, parsed: GeometryObject) -> dict[str, Any]:
    blocks = parsed.candidate_fields.get("contour_header_diagnostics", [])
    markers: list[dict[str, Any]] = []
    legacy_candidates: list[dict[str, Any]] = []
    refined_candidates: list[dict[str, Any]] = []
    actual_candidates: list[dict[str, Any]] = []
    margins: list[int] = []
    auxiliary_observed = 0
    auxiliary_suppressed = 0
    suppressed_aux_rows: list[dict[str, Any]] = []
    all_markers_expected_outside_gate_add = True
    any_marker_diff = False
    any_marker_with_winner = False

    for block in blocks:
        chain_index = block.get("chain_index")
        for marker_index, diag in enumerate(block.get("diagnostics", [])):
            legacy = diag.get("legacy_selected_candidate")
            refined = diag.get("refined_recommended_candidate")
            actual = diag.get("actual_selected_candidate")
            legacy_candidates.append(legacy) if legacy else None
            refined_candidates.append(refined) if refined else None
            actual_candidates.append(actual) if actual else None
            any_marker_with_winner = any_marker_with_winner or legacy is not None or refined is not None or actual is not None

            candidates = diag.get("candidates", [])
            sorted_candidates = sorted(
                [c for c in candidates if c.get("structural_valid")],
                key=lambda c: int(c.get("refined_score") or -9999),
                reverse=True,
            )
            winner_score = int(actual.get("refined_score") or 0) if actual else None
            runner_up_score = int(sorted_candidates[1].get("refined_score") or 0) if len(sorted_candidates) > 1 else None
            score_margin = (winner_score - runner_up_score) if winner_score is not None and runner_up_score is not None else None
            if score_margin is not None:
                margins.append(score_margin)

            marker_aux = [c for c in candidates if _is_auxiliary(c)]
            auxiliary_observed += len(marker_aux)
            for aux in marker_aux:
                aux_key = _candidate_key(aux)
                if actual is None or _candidate_key(actual) != aux_key:
                    auxiliary_suppressed += 1
                    suppressed_aux_rows.append(
                        {
                            "fixture": path.name,
                            "chain_index": chain_index,
                            "marker_index": marker_index,
                            "shift": aux.get("shift"),
                            "kind": aux.get("kind"),
                            "count": aux.get("count"),
                            "node_class_name": aux.get("node_class_name"),
                            "refined_score": aux.get("refined_score"),
                        }
                    )

            legacy_key = _candidate_key(legacy)
            refined_key = _candidate_key(refined)
            actual_key = _candidate_key(actual)
            if legacy_key != actual_key:
                any_marker_diff = True
                outside_gate = False
                if legacy is None and actual is not None:
                    for candidate in candidates:
                        if _candidate_key(candidate) == actual_key:
                            outside_gate = bool(candidate.get("structural_valid")) and not bool(candidate.get("legacy_plausible"))
                            break
                all_markers_expected_outside_gate_add = all_markers_expected_outside_gate_add and outside_gate

            markers.append(
                {
                    "chain_index": chain_index,
                    "marker_index": marker_index,
                    "legacy_selected_candidate": legacy,
                    "refined_selected_candidate": refined,
                    "actual_selected_candidate": actual,
                    "winner_node_class": actual.get("node_class_name") if actual else (legacy.get("node_class_name") if legacy else None),
                    "winner_kind": actual.get("kind") if actual else (legacy.get("kind") if legacy else None),
                    "winner_count": actual.get("count") if actual else (legacy.get("count") if legacy else None),
                    "winner_refined_score": winner_score,
                    "runner_up_refined_score": runner_up_score,
                    "score_margin": score_margin,
                    "auxiliary_candidates_observed_count": len(marker_aux),
                    "auxiliary_candidates_suppressed_count": len(marker_aux) if refined is None or not _is_auxiliary(refined) else max(len(marker_aux) - 1, 0),
                    "low_margin": bool(score_margin is not None and score_margin <= LOW_MARGIN_THRESHOLD),
                }
            )

    if not any_marker_with_winner:
        status = "no_candidate"
    elif not any_marker_diff:
        status = "same"
    elif all_markers_expected_outside_gate_add:
        status = "refined_adds_outside_gate_candidate"
    else:
        status = "refined_differs_unexpectedly"

    primary = next((m for m in markers if m.get("winner_node_class") is not None), None)
    return {
        "fixture": path.name,
        "declared_object_count": parsed.declared_object_count,
        "parsed_object_count": len(parsed.object_chains),
        "marker_count": len(markers),
        "legacy_selected_candidate_summary": [c for c in legacy_candidates if c is not None],
        "refined_selected_candidate_summary": [c for c in refined_candidates if c is not None],
        "actual_selected_candidate_summary": [c for c in actual_candidates if c is not None],
        "legacy_vs_actual_status": status,
        "winner_node_class": primary.get("winner_node_class") if primary else None,
        "winner_kind": primary.get("winner_kind") if primary else None,
        "winner_count": primary.get("winner_count") if primary else None,
        "winner_refined_score": primary.get("winner_refined_score") if primary else None,
        "runner_up_refined_score": primary.get("runner_up_refined_score") if primary else None,
        "score_margin": primary.get("score_margin") if primary else None,
        "auxiliary_candidates_observed_count": auxiliary_observed,
        "auxiliary_candidates_suppressed_count": auxiliary_suppressed,
        "low_margin_flag": any(m.get("low_margin") for m in markers),
        "notes": "diagnostic comparison; actual selection uses refined structural ranking",
        "markers": markers,
        "suppressed_auxiliary_candidates": suppressed_aux_rows,
    }


def _build_report(include_text: bool) -> dict[str, Any]:
    fixture_rows: list[dict[str, Any]] = []
    for path in _iter_fixture_paths(include_text):
        parsed = _decode_fixture(path)
        if parsed is None:
            continue
        fixture_rows.append(_summarize_fixture(path, parsed))

    status_counter = Counter(row["legacy_vs_actual_status"] for row in fixture_rows)
    winner_node_class_dist = Counter()
    winner_kind_count_dist = Counter()
    outside_gate_winner_dist = Counter()
    low_margin_fixtures = []
    fixture_mismatch = []
    auxiliary_observations = []
    suppressed_auxiliary = []
    margin_values = []
    node_context_dominant = []

    for row in fixture_rows:
        if row.get("winner_node_class") is not None:
            winner_node_class_dist[row["winner_node_class"]] += 1
        if row.get("winner_kind") is not None and row.get("winner_count") is not None:
            winner_kind_count_dist[f"kind={row['winner_kind']},count={row['winner_count']}"] += 1
        if row["legacy_vs_actual_status"] == "refined_adds_outside_gate_candidate":
            outside_gate_winner_dist[f"{row['winner_node_class']} kind={row['winner_kind']} count={row['winner_count']}"] += 1
        if row.get("low_margin_flag"):
            low_margin_fixtures.append(row["fixture"])
        if row["legacy_vs_actual_status"] != "same":
            fixture_mismatch.append(
                {
                    "fixture": row["fixture"],
                    "status": row["legacy_vs_actual_status"],
                    "winner_node_class": row["winner_node_class"],
                    "winner_kind": row["winner_kind"],
                    "winner_count": row["winner_count"],
                    "score_margin": row["score_margin"],
                }
            )
        for marker in row["markers"]:
            if marker["auxiliary_candidates_observed_count"] > 0:
                auxiliary_observations.append(
                    {
                        "fixture": row["fixture"],
                        "chain_index": marker["chain_index"],
                        "marker_index": marker["marker_index"],
                        "observed_count": marker["auxiliary_candidates_observed_count"],
                    }
                )
            if marker["score_margin"] is not None:
                margin_values.append(marker["score_margin"])
        for s in row["suppressed_auxiliary_candidates"]:
            suppressed_auxiliary.append(s)

        for marker in row["markers"]:
            winner = marker.get("actual_selected_candidate")
            if winner is None:
                continue
            # node_context 영향 점검: CContour winner지만 score margin 작으면 dominant 가능성 후보로 추적
            if marker["score_margin"] is not None and marker["score_margin"] <= LOW_MARGIN_THRESHOLD:
                node_context_dominant.append(
                    {
                        "fixture": row["fixture"],
                        "chain_index": marker["chain_index"],
                        "marker_index": marker["marker_index"],
                        "score_margin": marker["score_margin"],
                    }
                )

    aggregate = {
        "total_fixtures_scanned": len(fixture_rows),
        "fixtures_with_same_legacy_refined_winner": status_counter.get("same", 0),
        "fixtures_where_refined_adds_outside_gate_valid_contour": status_counter.get("refined_adds_outside_gate_candidate", 0),
        "fixtures_with_unexpected_refined_difference": status_counter.get("refined_differs_unexpectedly", 0),
        "fixtures_with_no_candidate": status_counter.get("no_candidate", 0),
        "total_auxiliary_candidates_observed": sum(row["auxiliary_candidates_observed_count"] for row in fixture_rows),
        "total_auxiliary_candidates_suppressed": sum(row["auxiliary_candidates_suppressed_count"] for row in fixture_rows),
        "low_margin_fixture_count": len(low_margin_fixtures),
        "winner_node_class_distribution": dict(winner_node_class_dist),
        "winner_kind_count_distribution": dict(winner_kind_count_dist),
        "outside_gate_refined_winner_distribution": dict(outside_gate_winner_dist),
        "score_margin_stats": {
            "min": min(margin_values) if margin_values else None,
            "median": median(margin_values) if margin_values else None,
            "max": max(margin_values) if margin_values else None,
            "threshold": LOW_MARGIN_THRESHOLD,
            "threshold_status": "provisional",
        },
    }

    return {
        "policy": "diagnostic comparison; actual selection is refined structural ranking; absolute offset is diagnostic only",
        "selection_mode": "refined_structural_ranking",
        "recommendation_mode": "shadow_run_only",
        "fixtures": fixture_rows,
        "fixture_level_winner_mismatch": fixture_mismatch,
        "refined_vs_actual_mismatch_fixtures": sorted(
            [
                row["fixture"]
                for row in fixture_rows
                if any(
                    _candidate_key(marker.get("refined_selected_candidate"))
                    != _candidate_key(marker.get("actual_selected_candidate"))
                    for marker in row["markers"]
                )
            ]
        ),
        "marker_level_auxiliary_observations": auxiliary_observations,
        "suppressed_auxiliary_candidates": suppressed_auxiliary,
        "low_margin_fixtures": low_margin_fixtures,
        "node_context_score_dominance_watchlist": node_context_dominant,
        "aggregate_summary": aggregate,
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Contour Selection Shadow Diff Report")
    print(f"policy: {report['policy']}")
    print()
    print("[Fixture Summary]")
    for row in report["fixtures"]:
        print(
            f"{row['fixture']}: status={row['legacy_vs_actual_status']} declared={row['declared_object_count']} parsed={row['parsed_object_count']} "
            f"markers={row['marker_count']} winner={row['winner_node_class']} kind={row['winner_kind']} count={row['winner_count']} "
            f"winner_score={row['winner_refined_score']} runner_up={row['runner_up_refined_score']} margin={row['score_margin']} "
            f"aux={row['auxiliary_candidates_observed_count']}/{row['auxiliary_candidates_suppressed_count']} low_margin={row['low_margin_flag']}"
        )
    print()
    print("[A. Fixture-level Winner Mismatch]")
    for row in report["fixture_level_winner_mismatch"]:
        print(
            f"{row['fixture']}: status={row['status']} winner={row['winner_node_class']} "
            f"kind={row['winner_kind']} count={row['winner_count']} margin={row['score_margin']}"
        )
    print()
    print("[Refined vs Actual Mismatch Fixtures]")
    for fixture in report["refined_vs_actual_mismatch_fixtures"]:
        print(fixture)
    print()
    print("[B. Marker-level Auxiliary Observations]")
    for row in report["marker_level_auxiliary_observations"]:
        print(
            f"{row['fixture']}: chain={row['chain_index']} marker={row['marker_index']} observed={row['observed_count']}"
        )
    print()
    print("[C. Suppressed Auxiliary Candidates]")
    for row in report["suppressed_auxiliary_candidates"]:
        print(
            f"{row['fixture']}: chain={row['chain_index']} marker={row['marker_index']} "
            f"class={row['node_class_name']} kind={row['kind']} count={row['count']} score={row['refined_score']}"
        )
    print()
    print("[Low-margin Fixtures]")
    for name in report["low_margin_fixtures"]:
        print(name)
    print()
    print("[Aggregate Summary]")
    for k, v in report["aggregate_summary"].items():
        print(f"{k}: {v}")


def _print_markdown(report: dict[str, Any]) -> None:
    print("# Contour Selection Shadow Diff")
    print()
    print(f"- policy: {report['policy']}")
    print(f"- selection_mode: `{report['selection_mode']}`")
    print(f"- recommendation_mode: `{report['recommendation_mode']}`")
    print()
    print("| fixture | status | winner class | winner kind/count | margin | aux observed/suppressed | low margin |")
    print("|---|---|---|---|---:|---:|---|")
    for row in report["fixtures"]:
        print(
            f"| {row['fixture']} | {row['legacy_vs_actual_status']} | {row['winner_node_class']} | "
            f"{row['winner_kind']}/{row['winner_count']} | {row['score_margin']} | "
            f"{row['auxiliary_candidates_observed_count']}/{row['auxiliary_candidates_suppressed_count']} | {row['low_margin_flag']} |"
        )


def main() -> int:
    args = parse_args()
    report = _build_report(include_text=args.include_text)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.markdown:
        _print_markdown(report)
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
