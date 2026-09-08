"""Actual runtime v1 versus independent F4 shadow; no public v2 or fallback."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser  # noqa: E402
from type3_clipboard_codec.codec.preview import PreviewRenderer  # noqa: E402
from type3_clipboard_codec.inspect.formatters import _json_safe, to_inspection_dict  # noqa: E402
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes  # noqa: E402
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser  # noqa: E402
from type3_clipboard_codec.parsers.text import text_slot_candidate as runtime  # noqa: E402
import analyze_text_slot_prefix_redesign as research  # noqa: E402

SAMPLES = ROOT / "tests/samples"
BASELINE = SAMPLES / "reports/text/text_slot_family_shadow_baseline.json"
TOKEN = b"\x05\0\0\0"
STRIDE = 204
SPAN = 92
F4_CONSTANTS = ((36, b"\0" * 8), (56, bytes.fromhex("9a9999999999d9bf")))
CAPS = dict(max_payloads=32, max_payload_bytes=1_048_576, max_prefix_hits=4096, max_slots=256)
LIMITS = dict(
    candidate_caps=CAPS,
    signature_probe_budget="2 * aggregate_payload_length + 4096",
    max_fixture_files=128,
    max_hex_file_bytes=8_388_608,
    json_bytes=100000,
    text_bytes=50000,
    detail_fixtures=4,
    run_examples=4,
)
POLICY = dict(
    scope="text_slot_family_v1_v2_shadow_comparison_only",
    runtime_parser_behavior="not_modified",
    runtime_family="v1_unchanged",
    v2_public_candidate="not_emitted",
    fallback="not_performed",
    ownership_assignment="not_performed",
    oracle_isolation=True,
)
ACCOUNTING = (
    "raw_prefix_hits",
    "identity_matches",
    "maximal_recurring_runs",
    "deduplicated_runs",
    "globally_competing_runs",
    "suffix_starts_removed",
    "traversed_slots",
    "probe_evaluations",
    "count_failures",
    "terminal_failures",
    "final_successes",
)
OUTCOMES = (
    "both_absent",
    "both_present_same_run",
    "v1_absent_v2_present",
    "v1_present_v2_absent",
    "both_present_different_run",
    "v2_ambiguous",
    "resource_or_bounds_difference",
    "other_structural_disagreement",
)


def compact(value):
    return json.dumps(_json_safe(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


def probe(payload, p):
    """Frozen exact F4; mismatch diagnostics do not create additional selectors."""
    if p < 0 or p + 64 > len(payload):
        return "incomplete"
    if payload[p : p + 4] != TOKEN:
        return "mismatch"
    flag = payload[p + 8] in (0, 1)
    reserved = payload[p + 9 : p + 12] == b"\0" * 3
    constants = all(payload[p + off : p + off + len(raw)] == raw for off, raw in F4_CONSTANTS)
    if flag and reserved and constants:
        return "match"
    if reserved and constants and not flag:
        return "unknown_plus08"
    if flag and reserved:
        return "unknown_structural_constant"
    if constants:
        return "unknown_core"
    return "mismatch"


def probe_budget(length):
    return 2 * length + 4096


def evaluate_v2(payloads):
    """Standalone shadow evidence; never a public candidate or semantic model."""
    buffers = []
    aggregate = 0
    stats = dict.fromkeys(ACCOUNTING, 0)
    result = dict(
        status="absent",
        failing_layer=None,
        reason=None,
        accounting=stats,
        selected=None,
        scan_complete=False,
        run_examples=[],
        unsupported_contexts=[],
        count_result=None,
        terminal_result=None,
    )

    def fail(layer, reason, status="absent"):
        result.update(failing_layer=layer, reason=reason, status=status)
        return result

    for payload in payloads:
        aggregate += len(payload)
        if len(buffers) >= CAPS["max_payloads"] or aggregate > CAPS["max_payload_bytes"]:
            return fail("resource", "payload_cap", "resource")
        buffers.append(payload)
    budget = probe_budget(aggregate)
    result["aggregate_bytes"] = aggregate
    result["probe_budget"] = budget
    prefixes = {}
    unsupported = []
    for index, payload in enumerate(buffers):
        start = 0
        while (p := payload.find(TOKEN, start)) >= 0:
            stats["raw_prefix_hits"] += 1
            if stats["raw_prefix_hits"] > CAPS["max_prefix_hits"]:
                return fail("resource", "prefix_hit_cap", "resource")
            if p + 64 > len(payload):
                return fail("bounds", "incomplete_identity", "bounds")
            stats["probe_evaluations"] += 1
            if stats["probe_evaluations"] > budget:
                return fail("resource", "probe_cap", "resource")
            state = probe(payload, p)
            if state == "match":
                prefixes[index, p] = payload[p + 8]
                stats["identity_matches"] += 1
            elif state.startswith("unknown_"):
                unsupported.append((index, p, state))
            start = p + 1
        if any(payload.endswith(TOKEN[:n]) for n in (1, 2, 3)):
            return fail("bounds", "partial_token_at_end", "bounds")
    result["scan_complete"] = True
    roots = [(i, p) for i, p in prefixes if (i, p - STRIDE) not in prefixes]
    stats["deduplicated_runs"] = len(roots)
    stats["maximal_recurring_runs"] = sum((i, p + STRIDE) in prefixes for i, p in roots)
    stats["suffix_starts_removed"] = len(prefixes) - len(roots)
    stats["globally_competing_runs"] = len(roots) if len(roots) > 1 else 0
    result["run_examples"] = [dict(payload_index=i, first_prefix=p) for i, p in roots[: LIMITS["run_examples"]]]
    result["unsupported_contexts"] = [dict(payload_index=i, prefix=p, reason=s) for i, p, s in unsupported[:4]]
    result["unsupported_context_count"] = len(unsupported)
    # Policy A precedes independent count and terminal validation.
    if len(roots) > 1:
        return fail("uniqueness", "multiple_identity_valid_runs", "ambiguous")
    if not roots:
        return fail("identity", unsupported[0][2] if unsupported else "no_identity_valid_run")
    index, first = roots[0]
    payload = buffers[index]
    positions = []
    p = first
    while (index, p) in prefixes:
        if stats["traversed_slots"] >= CAPS["max_slots"]:
            return fail("resource", "slot_cap", "resource")
        if p + SPAN > len(payload):
            return fail("bounds", "incomplete_rgb_or_raw_span", "bounds")
        positions.append(p)
        stats["traversed_slots"] += 1
        p += STRIDE
    flags = {prefixes[index, p] for p in positions}
    result["plus08_values"] = sorted(flags)
    if len(flags) != 1:
        return fail("plus08_consistency", "within_run_plus08_switch", "unsupported")
    if first < 16:
        return fail("bounds", "incomplete_count_window", "bounds")
    values = [int.from_bytes(payload[first - 4 : first - 4 + w], "little") for w in (1, 2, 4)]
    count_ok = values == [len(positions)] * 3
    result["count_result"] = dict(values=values, total=len(positions), valid=count_ok)
    stats["count_failures"] = int(not count_ok)
    following = positions[-1] + STRIDE
    if following + 64 > len(payload):
        return fail("bounds", "incomplete_next_prefix", "bounds")
    stats["probe_evaluations"] += 1
    if stats["probe_evaluations"] > budget:
        return fail("resource", "probe_cap", "resource")
    next_state = probe(payload, following)
    zero = payload[positions[-1] + 4 : positions[-1] + 8] == b"\0" * 4
    next_absent = next_state == "mismatch" and payload[following] != 5
    terminal_ok = zero and next_absent
    result["terminal_result"] = dict(
        prefix=positions[-1],
        zero=zero,
        next_probe=following,
        next_probe_bytes=64,
        next_absent=next_absent,
        valid=terminal_ok,
    )
    stats["terminal_failures"] = int(not terminal_ok)
    if not count_ok:
        return fail("count", "count_views_disagree_with_traversal")
    if not terminal_ok:
        return fail("terminal", "missing_zero_terminal" if not zero else "unsupported_continuation")
    result.update(status="present", selected=dict(payload_index=index, positions=positions, plus08=next(iter(flags))))
    stats["final_successes"] = 1
    return result


def nodes_from_raw(raw):
    parser = Type3ChainParser()
    _, _, base = parser._read_top_level_header(raw)
    return [
        (base + n.payload_offset, base + n.start_offset, n.payload)
        for n in parser._extract_nodes(raw[base:])
        if n.header.class_name == "CParagraphe"
    ]


def run_view(
    payload, source_start, descriptor, positions, raw_codes, raw_rgbs, spans, count_window, count_values, terminal
):
    """Canonical exact comparison, independent of family metadata and semantic objects."""
    first = positions[0]
    identity = dict(
        payload_source=[source_start, len(payload), hashlib.sha256(payload).hexdigest()],
        descriptor=descriptor,
        coordinate_domain="cparagraphe_payload_relative",
        first_prefix=first,
        positions=positions,
        count=len(positions),
        terminal_prefix=terminal,
        count_window=[first - 16, 16, count_window.hex()],
        count_probe=[first - 4, [1, 2, 4], count_values],
        raw_spans=spans,
        code_spans=[[p + 4, 4] for p in positions],
        rgb_spans=[[p + 80, 3] for p in positions],
        raw_codes=[v.hex() for v in raw_codes],
        raw_rgbs=[bytes(v).hex() for v in raw_rgbs],
    )
    view = dict(
        payload_source=[source_start, len(payload)],
        descriptor=descriptor,
        first_prefix=first,
        prefix_positions=positions,
        slot_count=len(positions),
        terminal_prefix=terminal,
        count_window=[first - 16, 16],
        count_probe=first - 4,
        count_views=count_values,
        count_valid=count_values == [len(positions)] * 3,
        terminal_valid=raw_codes[-1] == b"\0" * 4,
        span_length=SPAN,
        code_relative_span=[4, 4],
        rgb_relative_span=[80, 3],
        provenance_sha256=digest(identity),
    )
    return identity, view


def actual_v1_view(candidate, raw):
    if candidate is None:
        return None, None
    span = candidate["payload_span"]
    payload = raw[span["start"] : span["start"] + span["length"]]
    positions = [s["prefix_relative_offset"] for s in candidate["slots"]]
    terminals = [s["prefix_relative_offset"] for s in candidate["slots"] if s["terminal_candidate"]]
    if len(terminals) != 1:
        raise ValueError("actual runtime terminal provenance unsupported")
    return run_view(
        payload,
        span["start"],
        candidate["descriptor_relative_offset"],
        positions,
        [s["slot_code_candidate"]["raw_bytes"] for s in candidate["slots"]],
        [s["rgb_bytes_candidate"]["raw_bytes"] for s in candidate["slots"]],
        [[s["raw_span"]["start"], s["raw_span"]["length"]] for s in candidate["slots"]],
        candidate["count_candidate"]["raw_window"],
        [candidate["count_candidate"]["numeric_views"][n]["value"] for n in ("u8", "u16le", "u32le")],
        terminals[0],
    )


def shadow_view(result, nodes):
    if result["selected"] is None:
        return None, None
    selected = result["selected"]
    start, descriptor, payload = nodes[selected["payload_index"]]
    positions = selected["positions"]
    return run_view(
        payload,
        start,
        descriptor,
        positions,
        [payload[p + 4 : p + 8] for p in positions],
        [payload[p + 80 : p + 83] for p in positions],
        [[p, SPAN] for p in positions],
        payload[positions[0] - 16 : positions[0]],
        result["count_result"]["values"],
        positions[-1],
    )


def outcome(v1, v2, state):
    if state["status"] == "ambiguous":
        return "v2_ambiguous"
    if state["status"] in ("bounds", "resource"):
        return "resource_or_bounds_difference"
    if v1 is not None and v2 is not None:
        return "both_present_same_run" if v1 == v2 else "both_present_different_run"
    if v1 is not None:
        return "v1_present_v2_absent"
    if v2 is not None:
        return "v1_absent_v2_present"
    return "both_absent"


def legacy_audit(payload, positions):
    """Actual runtime predicate diagnostics, never a simulated v1 selection result."""
    patterns = Counter()
    accepted = []
    for p in positions:
        tag = runtime._family(payload, p)
        if tag in ("v0", "v1", "v2"):
            accepted.append(p)
            continue
        mismatches = tuple(
            tuple(i for i in range(32) if not 4 <= i < 8 and payload[p + i] != v[i]) for v in research.VECTORS
        )
        patterns[(str(tag), mismatches)] += 1
    return dict(
        actual_family_valid_prefixes=len(accepted),
        actual_family_roots=sum(p - STRIDE not in accepted for p in accepted),
        rejected_patterns=[
            dict(actual_family_result=tag, legacy_variant_mismatch_offsets=[list(x) for x in offsets], prefix_count=n)
            for (tag, offsets), n in patterns.items()
        ],
    )


def decoy_audit(nodes):
    """Discover all raw runs first, then label a +92 relation; not a v2 selector."""
    candidates = []
    for index, (_, _, payload) in enumerate(nodes):
        hits = research.raw_hits(payload)
        runs = research.maximal_runs(hits)
        for run in runs:
            if len(run) < 2 or not research.count_valid(payload, run) or not research.terminal_valid(payload, run):
                continue
            paired = [p + 92 for p in run]
            if paired in runs:
                candidates.append(
                    dict(
                        payload_index=index,
                        reference_first=run[0],
                        decoy_first=paired[0],
                        slots=len(paired),
                        identity_matches=sum(probe(payload, p) == "match" for p in paired),
                        raw_recurrence=True,
                        rejection_layer="identity",
                    )
                )
    return candidates


def presentation_digest(obj, parser):
    return digest(
        [
            PreviewRenderer().render(obj),
            PreviewRenderer().render(obj, verbose=True),
            to_inspection_dict(obj, parser, "shadow_regression"),
        ]
    )


def compare_fixture(path, baseline):
    if path.stat().st_size > LIMITS["max_hex_file_bytes"]:
        raise ValueError("analysis hex-file cap")
    raw = hex_text_to_bytes(path.read_text(encoding="utf-8"))
    before, parser = parse_type3_clipboard_bytes_with_parser(raw)
    before_hash = digest(asdict(before))
    before_preview = presentation_digest(before, parser)
    actual = before.candidate_fields.get("text_slot_run")
    v1, view1 = actual_v1_view(actual, raw)
    nodes = nodes_from_raw(raw)
    shadow = evaluate_v2(n[2] for n in nodes)
    v2, view2 = shadow_view(shadow, nodes)
    category = outcome(v1, v2, shadow)
    after, parser_after = parse_type3_clipboard_bytes_with_parser(raw)
    raw_hash = hashlib.sha256(raw).hexdigest()
    prior = baseline.get(raw_hash)
    regression = (
        before_hash == digest(asdict(after))
        and before_preview == presentation_digest(after, parser_after)
        and prior is not None
        and before_hash == prior["parser_sha256"]
        and before_preview == prior["presentation_sha256"]
    )
    row = dict(
        fixture=path.name,
        outcome=category,
        v1=dict(present=actual is not None),
        v2=dict(
            present=v2 is not None,
            status=shadow["status"],
            layer=shadow["failing_layer"],
            reason=shadow["reason"],
            accounting=[shadow["accounting"][k] for k in ACCOUNTING],
        ),
        runtime_regression_equal=regression,
        paragraph_count=len(nodes),
    )
    if actual:
        row["v1"].update(run=view1, prefix_variant=actual["prefix_variant"])
    if view2:
        row["v2"]["run_ref"] = "v1.run" if v1 == v2 else None
        if v1 != v2:
            row["v2"]["run"] = view2
    if category == "v1_absent_v2_present":
        row["v1"]["identity_audit"] = legacy_audit(
            nodes[shadow["selected"]["payload_index"]][2], shadow["selected"]["positions"]
        )
    if category in (
        "v1_present_v2_absent",
        "both_present_different_run",
        "v2_ambiguous",
        "resource_or_bounds_difference",
    ):
        row["v2"]["failure_evidence"] = {
            k: shadow[k] for k in ("run_examples", "unsupported_contexts", "count_result", "terminal_result")
        }
    row["decoys"] = decoy_audit(nodes)
    return row, shadow, nodes


def make_run(count=3, start=32, flag=0, next_bytes=64):
    """Synthetic harness template, never a captured fixture or selection oracle."""
    payload = bytearray(b"\xcc" * (start + count * STRIDE + next_bytes))
    payload[start - 4 : start] = count.to_bytes(4, "little")
    for i in range(count):
        p = start + i * STRIDE
        payload[p : p + 32] = research.VECTORS[0]
        payload[p + 4 : p + 8] = (65 if i < count - 1 else 0).to_bytes(4, "little")
        payload[p + 8] = flag
        for off, data in F4_CONSTANTS:
            payload[p + off : p + off + len(data)] = data
        payload[p + 80 : p + 83] = bytes.fromhex("98cc98")
    return bytes(payload)


def harness_case(payloads):
    actual = runtime.extract_text_slot_candidate(payloads)
    result = evaluate_v2(payloads)
    return dict(
        v1_present=actual is not None,
        v2_present=result["selected"] is not None,
        status=result["status"],
        layer=result["failing_layer"],
        reason=result["reason"],
        accounting=[result["accounting"][k] for k in ACCOUNTING],
        count_result=result["count_result"],
        terminal_result=result["terminal_result"],
    )


def challenge_study(seed):
    cases = {}
    if seed:
        payload, positions = seed
        for name, (kind, buffers) in research.synthetic_cases(payload, positions).items():
            # Phase 1G templates have 32 continuation bytes. Give this study the
            # full 64-byte F4 context so later-layer clone tests are meaningful.
            cases[name] = dict(kind=kind, **harness_case([b + b"\xcc" * 32 for b in buffers]))
    valid = make_run()
    switch = bytearray(valid)
    switch[32 + STRIDE + 8] = 1
    cases["plus08_switch"] = dict(kind="plus08", **harness_case([bytes(switch)]))
    for value in (0, 1, 2, 255):
        cases[f"plus08_{value:02x}"] = dict(kind="plus08", **harness_case([make_run(flag=value)]))
    for off in (36, 56):
        for width in (1, 8):
            changed = bytearray(valid)
            for p in (32, 32 + STRIDE, 32 + 2 * STRIDE):
                for i in range(width):
                    changed[p + off + i] ^= 0x55
            cases[f"constant_{off:02x}_{width}"] = dict(kind="constant", **harness_case([bytes(changed)]))
    for remaining in (0, 31, 32, 63, 64):
        cases[f"next_context_{remaining}"] = dict(kind="bounds", **harness_case([make_run(next_bytes=remaining)]))
    for remaining in (63, 64, 82, 91, 92):
        short = make_run(count=1)[: 32 + remaining]
        cases[f"prefix_context_{remaining}"] = dict(
            kind="bounds", identity_probe=probe(short, 32), **harness_case([short])
        )
    cases["payload_count_cap"] = dict(kind="resource", **harness_case([b""] * 33))
    cases["payload_byte_cap"] = dict(kind="resource", **harness_case([b"\xcc" * 1_048_577]))
    cases["prefix_hit_cap"] = dict(kind="resource", **harness_case([TOKEN * 4097 + b"\xcc" * 64]))
    cases["slot_cap"] = dict(kind="resource", **harness_case([make_run(count=257)]))
    return cases


def structural_phase(paths):
    if len(paths) > LIMITS["max_fixture_files"]:
        raise ValueError("analysis fixture-file cap")
    frozen_baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    by_raw = {v["raw_sha256"]: v for v in frozen_baseline["fixtures"].values()}
    source_equal = all(
        hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in frozen_baseline["source_sha256"].items()
    )
    rows = []
    seeds = []
    flags = Counter()
    evaluations = []
    warnings = []
    for path in sorted(paths):
        row, shadow, nodes = compare_fixture(path, by_raw)
        rows.append(row)
        if not row["runtime_regression_equal"]:
            warnings.append(path.name + ": runtime baseline/presentation disagreement or missing baseline")
        if shadow["selected"]:
            selected = shadow["selected"]
            flags[selected["plus08"]] += 1
            if row["decoys"] and row["v1"]["present"]:
                seeds.append((nodes[selected["payload_index"]][2], selected["positions"]))
        evaluations.append(shadow["accounting"]["probe_evaluations"])
    if not source_equal:
        warnings.append("Runtime source hash disagreement")
    seed = min(seeds, key=lambda x: (len(x[1]), hashlib.sha256(x[0]).hexdigest())) if seeds else None
    challenges = challenge_study(seed)
    if seed is None:
        warnings.append("No complete seed for known-decoy synthetic challenges")
    counts = {name: sum(r["outcome"] == name for r in rows) for name in OUTCOMES}
    totals = {k: sum(r["v2"]["accounting"][i] for r in rows) for i, k in enumerate(ACCOUNTING)}
    gains = [
        dict(fixture=r["fixture"], identity_audit=r["v1"]["identity_audit"])
        for r in rows
        if r["outcome"] == "v1_absent_v2_present"
    ]
    losses = [r["fixture"] for r in rows if r["outcome"] == "v1_present_v2_absent"]
    different = [r["fixture"] for r in rows if r["outcome"] == "both_present_different_run"]
    decoys = [d for r in rows for d in r["decoys"]]
    general = [v for v in challenges.values() if v["kind"] == "negative"]
    collisions = {k: v for k, v in challenges.items() if v["kind"] in ("identity_collision", "ambiguity_control")}
    collision_ok = (
        len(collisions) == 3
        and collisions["identity_clone_wrong_count"]["layer"] == "count"
        and collisions["identity_clone_missing_terminal"]["layer"] == "terminal"
        and collisions["two_full_identity_clones"]["status"] == "ambiguous"
        and all(not v["v2_present"] for v in collisions.values())
    )
    plus_ok = (
        challenges["plus08_switch"]["reason"] == "within_run_plus08_switch"
        and challenges["plus08_00"]["v2_present"]
        and challenges["plus08_01"]["v2_present"]
        and not challenges["plus08_02"]["v2_present"]
        and not challenges["plus08_ff"]["v2_present"]
    )
    constant_ok = all(not v["v2_present"] for v in challenges.values() if v["kind"] == "constant")
    bounds_ok = (
        challenges["prefix_context_64"]["identity_probe"] == "match"
        and challenges["prefix_context_63"]["identity_probe"] == "incomplete"
        and challenges["next_context_64"]["v2_present"]
        and all(not challenges[f"next_context_{n}"]["v2_present"] for n in (0, 31, 32, 63))
        and all(not challenges[f"prefix_context_{n}"]["v2_present"] for n in (63, 64, 82, 91, 92))
    )
    # Explainability is byte-based here; semantic cause names belong only to oracle_summary.
    explainable = all(
        g["identity_audit"]["rejected_patterns"]
        and all(p["actual_family_result"] not in ("v0", "v1", "v2") for p in g["identity_audit"]["rejected_patterns"])
        for g in gains
    )
    corpus_complete = len(rows) == len(frozen_baseline["fixtures"]) and all(r["runtime_regression_equal"] for r in rows)
    ready = (
        corpus_complete
        and source_equal
        and not warnings
        and not losses
        and not different
        and counts["v2_ambiguous"]
        == counts["resource_or_bounds_difference"]
        == counts["other_structural_disagreement"]
        == 0
        and explainable
        and len(decoys) == 72
        and all(d["identity_matches"] == 0 for d in decoys)
        and len(general) == 6
        and all(not c["v2_present"] for c in general)
        and collision_ok
        and plus_ok
        and constant_ok
        and bounds_ok
    )
    answers = dict(
        real_fixture_count=len(rows),
        v1_present_count=sum(r["v1"]["present"] for r in rows),
        v2_shadow_present_count=sum(r["v2"]["present"] for r in rows),
        **{k + "_count": counts[k] for k in OUTCOMES[:5]},
        v2_ambiguity_count=counts["v2_ambiguous"],
        resource_difference_count=counts["resource_or_bounds_difference"],
        known_decoy_accept_count=sum(d["identity_matches"] > 0 for d in decoys),
        synthetic_general_negative_accept_count=sum(v["v2_present"] for v in general),
        collision_safe_abstention_status="passed" if collision_ok else "unresolved",
        plus08_consistency_status="passed" if plus_ok else "unresolved",
        structural_constant_fail_closed_status="passed" if constant_ok else "unresolved",
        bounds_migration_status="passed" if bounds_ok else "unresolved",
        disagreement_closeout_readiness="ready_for_review" if ready else "not_ready",
        runtime_v2_promotion_review_readiness="ready_for_review" if ready else "not_ready",
        runtime_prefix_v2_migration_readiness="not_authorized" if ready else "not_ready",
        parser_safe=False,
        ownership_readiness="unresolved",
    )
    return dict(
        mode="summary",
        policy=POLICY,
        limits=LIMITS,
        warnings=warnings,
        corpus_summary=dict(
            real_fixtures=len(rows),
            text_paragraph_inputs=sum(r["paragraph_count"] > 0 for r in rows),
            geometry_scope_inputs=sum(r["paragraph_count"] == 0 for r in rows),
            synthetic_cases=len(challenges),
            runtime_source_equal=source_equal,
            runtime_outputs_equal=corpus_complete,
        ),
        fixture_results=rows,
        outcome_summary=counts,
        v1_summary=dict(
            actual_parser=True,
            present=answers["v1_present_count"],
            absent=len(rows) - answers["v1_present_count"],
            failure_telemetry="not exposed; actual predicate diagnostics on disagreements only",
        ),
        v2_identity_summary=dict(accounting_columns=list(ACCOUNTING), **{k: totals[k] for k in ACCOUNTING[:2]}),
        v2_run_summary={k: totals[k] for k in ACCOUNTING[2:]},
        coverage_gain_summary=gains,
        coverage_loss_summary=losses,
        different_run_summary=different,
        decoy_summary=dict(
            runs=len(decoys),
            slots=sum(d["slots"] for d in decoys),
            identity_matches=sum(d["identity_matches"] for d in decoys),
            rejection_layer="identity",
        ),
        collision_summary=collisions,
        plus08_summary=dict(
            real_run_values=dict(sorted(flags.items())),
            cases={k: v for k, v in challenges.items() if v["kind"] == "plus08"},
        ),
        structural_constant_summary={k: v for k, v in challenges.items() if v["kind"] == "constant"},
        bounds_summary={k: v for k, v in challenges.items() if v["kind"] == "bounds"},
        resource_summary=dict(
            real_exhaustions=sum(r["v2"]["layer"] == "resource" for r in rows),
            real_probe_evaluation_max=max(evaluations, default=0),
            v1_probe_counts="not exposed by runtime",
            wider_probe_effect="No real exhaustion difference; 32/63-byte continuation controls now fail bounds",
            probe_cap_reachability="With these caps, one probe per token plus continuation cannot exhaust the formula; "
            "guard is tested with fault injection only",
            cases={k: v for k, v in challenges.items() if v["kind"] == "resource"},
        ),
        _general_negatives={k: v for k, v in challenges.items() if v["kind"] == "negative"},
        answers=answers,
    )


def oracle_phase(frozen, enabled):
    evidence = json.loads(frozen)
    if not enabled:
        return dict(enabled=False)
    labels = {r["fixture"]: research.load_labels(r["fixture"]) for r in evidence["fixture_results"]}
    groups = Counter(g for v in labels.values() for g in v["groups"])
    causes = []
    for gain in evidence["coverage_gain_summary"]:
        regions = set()
        for pattern in gain["identity_audit"]["rejected_patterns"]:
            for offsets in pattern["legacy_variant_mismatch_offsets"]:
                if offsets and all(12 <= p < 20 for p in offsets):
                    regions.add("old_height_dependent_prefix_mismatch")
                if offsets and all(20 <= p < 28 for p in offsets):
                    regions.add("old_width_dependent_invariant_mismatch")
                if offsets and all(28 <= p < 36 for p in offsets):
                    regions.add("old_slant_dependent_invariant_mismatch")
        causes.append(
            dict(
                fixture=gain["fixture"],
                causes=sorted(regions) or ["other"],
                corpus_groups=labels[gain["fixture"]]["groups"],
            )
        )
    return dict(
        enabled=True,
        cohort_counts=dict(groups),
        coverage_gain_causes=causes,
        note="Semantic cause labels applied only to frozen raw mismatches; no run selected by intent",
    )


def build_report(paths=None, oracle_enabled=True, details=False):
    paths = sorted(SAMPLES.glob("*.txt")) + sorted((SAMPLES / "text").glob("*.txt")) if paths is None else paths
    report = structural_phase(paths)
    report["collision_summary"]["general_negatives"] = report.pop("_general_negatives")
    if details:
        report["mode"] = "details"
        report["bounds_summary"]["detail_run_examples"] = [
            r["v2"].get("run", r["v1"].get("run")) for r in report["fixture_results"] if r["v2"]["present"]
        ][: LIMITS["detail_fixtures"]]
    frozen = compact(report)
    # Everything except this sole oracle_summary key is frozen before labels can load.
    report = json.loads(frozen)
    report["oracle_summary"] = oracle_phase(frozen, oracle_enabled)
    return report


def render_text(report):
    lines = [
        "Actual v1 vs proposed F4 shadow; runtime unchanged",
        compact(report["answers"]),
        "F4 accounting: " + compact({**report["v2_identity_summary"], **report["v2_run_summary"]}),
    ]
    for row in report["fixture_results"]:
        lines.append(
            row["fixture"] + ": " + row["outcome"] + "; v2 " + str(row["v2"]["layer"]) + "/" + str(row["v2"]["reason"])
        )
    lines.append("Oracle: " + compact(report["oracle_summary"]))
    lines.extend(report["warnings"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-oracle", action="store_true")
    parser.add_argument("--details", action="store_true")
    parser.add_argument("--fixtures", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        report = build_report(args.fixtures, not args.no_oracle, args.details)
        output = compact(report) + "\n" if args.json else render_text(report)
        if len(output.encode()) >= LIMITS["json_bytes" if args.json else "text_bytes"]:
            raise ValueError("output cap exceeded; no partial report emitted")
    except ValueError as exc:
        parser.error(str(exc))
    print(output, end="")


if __name__ == "__main__":
    main()
