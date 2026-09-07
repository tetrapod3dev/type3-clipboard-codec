"""Prefix redesign research; runtime v0/v1/v2 remains unchanged."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes  # noqa: E402
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser  # noqa: E402

SAMPLES = ROOT / "tests/samples"
TOKEN = b"\x05\0\0\0"
STRIDE = 204
WINDOW = (-16, 96)
NAMES = ("F0", "F1", "F2", "F3", "F4")
POLICY = dict(
    scope="cparagraphe_text_slot_prefix_redesign_analysis_only",
    runtime_parser_behavior="not_modified",
    runtime_family="exact_v0_v1_v2_retained",
    oracle_isolation=True,
    count_selects_prefix=False,
    semantic_model_change="not_performed",
    ownership="unresolved",
    anchor_ownership_used=False,
    parser_safe=False,
    typed_widths=None,
)
LIMITS = dict(
    max_fixtures=128,
    max_hex_bytes=8_388_608,
    max_payload_bytes=1_048_576,
    max_paragraphs=32,
    max_prefix_hits=4096,
    max_slots=256,
    max_runs=512,
    max_signature_evaluations=32768,
    json_bytes=100000,
    text_bytes=50000,
    details_fixtures=4,
)
# Explicit frozen hypotheses from prior evidence. No decoded style values in matching.
# F1/F2/F3 are projections of the existing EXACT joint vectors, not a Cartesian wildcard rule.
VECTORS = tuple(
    bytes.fromhex(s)
    for s in (
        "05000000 00000000 00000000 7b14ae47e17a843f 000000000000f03f 00000000",
        "05000000 00000000 00000000 b81e85eb51b89e3f 000000000000f03f 00000000",
        "05000000 00000000 01000000 7b14ae47e17a843f 000000000000f03f 00000000",
    )
)
EXCLUDED = {
    "F0": [(4, 8)],
    "F1": [(4, 8), (12, 20)],
    "F2": [(4, 8), (12, 28)],
    "F3": [(4, 8), (12, 36)],
    "F4": [(4, 8), (12, 36), (44, 56), (64, 96)],
}
POSITIONS = {
    name: tuple(p for p in range(32) if not any(lo <= p < hi for lo, hi in EXCLUDED[name])) for name in NAMES[:4]
}
PROJECTED = {name: {bytes(v[p] for p in positions) for v in VECTORS} for name, positions in POSITIONS.items()}
# Wider-area hypotheses are literal, few-range candidates, never learned masks at runtime.
F4_RANGES = ((0, TOKEN), (9, b"\0" * 3), (36, b"\0" * 8), (56, bytes.fromhex("9a9999999999d9bf")))
BOUNDS = {"F0": 32, "F1": 32, "F2": 32, "F3": 12, "F4": 64}


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def predicate(payload, p, hypothesis):
    if p < 0 or p + BOUNDS[hypothesis] > len(payload):
        return False
    if hypothesis == "F4":
        return payload[p + 8] in (0, 1) and all(payload[p + off : p + off + len(raw)] == raw for off, raw in F4_RANGES)
    return bytes(payload[p + i] for i in POSITIONS[hypothesis]) in PROJECTED[hypothesis]


def hypothesis_definitions():
    output = {}
    for name in NAMES:
        if name == "F4":
            constants = {str(off + i): value for off, raw in F4_RANGES for i, value in enumerate(raw)}
            vectors = [{"8": 0}, {"8": 1}]
        else:
            positions = POSITIONS[name]
            constants = {str(p): VECTORS[0][p] for p in positions if len({v[p] for v in VECTORS}) == 1}
            variable = [p for p in positions if str(p) not in constants]
            vectors = [
                dict(zip(map(str, variable), v)) for v in sorted({tuple(v[p] for p in variable) for v in VECTORS})
            ]
        output[name] = dict(
            required_invariant_positions=constants,
            exact_joint_variants=vectors,
            excluded_ranges_half_open=[list(span) for span in EXCLUDED[name]],
            required_bytes=BOUNDS[name],
            byte08_policy="exact allowed raw values 00 or 01; any other value rejected",
            semantics="none; exclusion/probe widths are not typed field promotion",
        )
    return output


def raw_hits(payload):
    hits = set()
    start = 0
    while (p := payload.find(TOKEN, start)) >= 0:
        hits.add(p)
        if len(hits) > LIMITS["max_prefix_hits"]:
            raise ValueError("prefix hit budget exceeded")
        start = p + 1
    return hits


def maximal_runs(hits):
    output = []
    for p in sorted(hits):
        if p - STRIDE in hits:
            continue
        positions = [p]
        while positions[-1] + STRIDE in hits:
            if len(positions) >= LIMITS["max_slots"]:
                raise ValueError("slot budget exceeded")
            positions.append(positions[-1] + STRIDE)
        output.append(positions)
        if len(output) > LIMITS["max_runs"]:
            raise ValueError("run budget exceeded")
    return output


def count_valid(payload, run):
    p = run[0]
    return p >= 16 and all(int.from_bytes(payload[p - 4 : p - 4 + w], "little") == len(run) for w in (1, 2, 4))


def terminal_valid(payload, run):
    end = run[-1] + STRIDE
    return end + 32 <= len(payload) and payload[run[-1] + 4 : run[-1] + 8] == b"\0" * 4 and payload[end] != 5


def inspect_payloads(payloads):
    """Identity/recurrence are evaluated first; count/terminal never filter L1/L2.

    Reference nominations use independent token+count+terminal research evidence.
    They are comparison denominators only, never selectors for hypothesis hits.
    """
    if len(payloads) > LIMITS["max_paragraphs"] or sum(map(len, payloads)) > LIMITS["max_payload_bytes"]:
        raise ValueError("paragraph budget exceeded")
    references = []
    all_tokens = []
    raw_runs = []
    layers = {
        name: dict(
            prefix_hits=0,
            maximal_runs=0,
            recurring_runs=0,
            count_valid_runs=0,
            terminal_valid_runs=0,
            all_four_layers=0,
        )
        for name in NAMES
    }
    matched_runs = {name: [] for name in NAMES}
    matched_hits = {name: set() for name in NAMES}
    evaluations = 0
    for index, payload in enumerate(payloads):
        hits = raw_hits(payload)
        all_tokens.append(hits)
        runs = maximal_runs(hits)
        raw_runs.append(runs)
        for name in NAMES:
            evaluations += len(hits)
            if evaluations > LIMITS["max_signature_evaluations"]:
                raise ValueError("signature budget exceeded")
            accepted = {p for p in hits if predicate(payload, p, name)}
            matched_hits[name].update((index, p) for p in accepted)
            accepted_runs = maximal_runs(accepted)
            matched_runs[name].extend((index, run) for run in accepted_runs)
            row = layers[name]
            row["prefix_hits"] += len(accepted)
            row["maximal_runs"] += len(accepted_runs)
            recurring = [run for run in accepted_runs if len(run) >= 2]
            row["recurring_runs"] += len(recurring)
    # All identity and recurrence results are now fixed, including every competitor.
    for index, runs in enumerate(raw_runs):
        payload = payloads[index]
        for run in runs:
            if len(run) >= 2 and count_valid(payload, run) and terminal_valid(payload, run):
                if run[0] >= 16 and run[-1] + 96 <= len(payload):
                    references.append((index, run))
    for name, matches in matched_runs.items():
        for index, run in matches:
            if len(run) < 2:
                continue
            count_ok = count_valid(payloads[index], run)
            terminal_ok = terminal_valid(payloads[index], run)
            layers[name]["count_valid_runs"] += count_ok
            layers[name]["terminal_valid_runs"] += terminal_ok
            layers[name]["all_four_layers"] += count_ok and terminal_ok
    ref = references[0] if len(references) == 1 else None
    rows = []
    decoy = None
    if ref:
        index, run = ref
        rows = [payloads[index][p - 16 : p + 96] for p in run]
        shifted = [p + 92 for p in run]
        if shifted in raw_runs[index]:
            decoy = (index, shifted)
    metrics = {}
    for name in NAMES:
        matches = matched_runs[name]
        real_hits = sum((ref[0], p) in matched_hits[name] for p in ref[1]) if ref else 0
        decoy_hits = sum((decoy[0], p) in matched_hits[name] for p in decoy[1]) if decoy else 0
        full = bool(ref) and real_hits == len(ref[1])
        competing = len(matches) > 1
        metrics[name] = dict(
            **layers[name],
            reference_slot_hits=real_hits,
            reference_full_match=full,
            known_decoy_slot_hits=decoy_hits,
            known_decoy_full_match=bool(decoy) and decoy_hits == len(decoy[1]),
            ambiguous=competing,
            unique_reference=full and len(matches) == 1,
            nonreference_maximal_runs=sum(
                not ref or index != ref[0] or not set(run).issubset(ref[1]) for index, run in matches
            ),
        )
    return dict(
        reference_count=len(references),
        reference=ref,
        decoy=decoy,
        rows=rows,
        raw_token_count=sum(map(len, all_tokens)),
        raw_recurring_runs=sum(len(r) >= 2 for rs in raw_runs for r in rs),
        metrics=metrics,
        payloads=payloads,
    )


def read_capture(path):
    if path.stat().st_size > LIMITS["max_hex_bytes"]:
        raise ValueError("hex input budget exceeded")
    raw = hex_text_to_bytes(path.read_text(encoding="utf-8"))
    parser = Type3ChainParser()
    _, _, offset = parser._read_top_level_header(raw)
    nodes = parser._extract_nodes(raw[offset:])
    payloads = [n.payload for n in nodes if n.header.class_name == "CParagraphe"]
    result = inspect_payloads(payloads)
    result.update(raw_size=len(raw), sha256=hashlib.sha256(raw).hexdigest(), paragraph_count=len(payloads))
    return result


def synthetic_cases(reference_payload, run):
    """Predeclared challenges include unavoidable identity collisions, not just easy negatives."""
    start = 32
    original = [reference_payload[p : p + 96] for p in run]
    decoy = [reference_payload[p + 92 : p + 188] for p in run]

    def build(windows, count=None, terminal=True):
        data = bytearray(b"\xcc" * (start + len(windows) * STRIDE + 32))
        data[start - 4 : start] = (len(windows) if count is None else count).to_bytes(4, "little")
        for i, window in enumerate(windows):
            p = start + i * STRIDE
            data[p : p + len(window)] = window
        if terminal:
            data[start + (len(windows) - 1) * STRIDE + 4 : start + (len(windows) - 1) * STRIDE + 8] = b"\0" * 4
        return bytes(data)

    zeros = [TOKEN + b"\0" * 92 for _ in original]
    noise = [TOKEN + b"\xcc" * 92 for _ in original]
    patched = []
    for w in decoy:
        w = bytearray(w)
        w[8:12] = b"\0" * 4
        patched.append(bytes(w))
    padded = []
    for w in patched:
        w = bytearray(w)
        w[36:44] = b"\0" * 8
        padded.append(bytes(w))
    unknown = []
    for w in original:
        w = bytearray(w)
        w[8] = 2
        unknown.append(bytes(w))
    missing = []
    for w in original:
        w = bytearray(w)
        w[4:8] = b"\x41\0\0\0"
        missing.append(bytes(w))
    valid = build(original)
    return {
        "periodic_zero_filler": ("negative", [build(zeros)]),
        "periodic_nonzero_filler": ("negative", [build(noise)]),
        "known_decoy_replay": ("negative", [build(decoy, terminal=False)]),
        "decoy_core08_11_repaired": ("negative", [build(patched)]),
        "decoy_core_and_padding_repaired": ("negative", [build(padded)]),
        "unknown_08_value": ("negative", [build(unknown)]),
        "identity_clone_wrong_count": ("identity_collision", [build(original, count=0)]),
        "identity_clone_missing_terminal": ("identity_collision", [build(missing, terminal=False)]),
        "two_full_identity_clones": ("ambiguity_control", [valid, valid]),
    }


METRIC_COLUMNS = [
    "reference_slot_hits",
    "reference_full_match",
    "known_decoy_slot_hits",
    "known_decoy_full_match",
    "prefix_hits",
    "maximal_runs",
    "recurring_runs",
    "count_valid_runs",
    "terminal_valid_runs",
    "all_four_layers",
    "ambiguous",
    "unique_reference",
    "nonreference_maximal_runs",
]


def compact_metrics(metrics):
    return {name: [row[k] for k in METRIC_COLUMNS] for name, row in metrics.items()}


def variability(records):
    runs = [r["rows"] for r in records.values() if r["rows"]]
    output = []
    for relative in range(*WINDOW):
        i = relative + 16
        vals = sorted({row[i] for run in runs for row in run})
        nonterminal = sorted({row[i] for run in runs for row in run[:-1]})
        terminal = sorted({run[-1][i] for run in runs})
        by_code = defaultdict(set)
        for run in runs:
            for row in run:
                by_code[row[20:24]].add(row[i])
        output.append(
            [
                relative,
                vals,
                sum(len({row[i] for row in run}) == 1 for run in runs),
                len(runs),
                len(vals) == 1,
                nonterminal,
                terminal,
                sum(len(v) > 1 for v in by_code.values()),
            ]
        )
    return dict(
        columns=[
            "relative_offset",
            "unique_raw_values",
            "stable_runs",
            "total_runs",
            "cross_fixture_constant",
            "nonterminal_raw_values",
            "terminal_raw_values",
            "varying_same_raw_code_classes",
        ],
        rows=output,
    )


def structural_phase(paths):
    if len(paths) > LIMITS["max_fixtures"]:
        raise ValueError("fixture budget exceeded")
    records = {}
    warnings = []
    inventory = []
    for path in sorted(paths):
        key = path.name
        if key in records:
            raise ValueError("duplicate fixture labels")
        try:
            result = read_capture(path)
            records[key] = result
            inventory.append(
                dict(
                    fixture=key,
                    sha256=result["sha256"],
                    raw_size=result["raw_size"],
                    paragraph_count=result["paragraph_count"],
                    reference_count=result["reference_count"],
                    reference_start=result["reference"][1][0] if result["reference"] else None,
                    reference_slots=len(result["rows"]),
                    decoy_present=result["decoy"] is not None,
                )
            )
        except (OSError, ValueError, EOFError) as exc:
            warnings.append(f"{key}: unresolved: {exc}")
    var = variability(records)
    wider = []
    # This is an inventory, not an automatic mask learner or predicate modifier.
    for offset, values, stable, total, constant, *_ in var["rows"]:
        if not 36 <= offset < 72 or not constant:
            continue
        decvals = sorted(
            {r["payloads"][r["decoy"][0]][p + offset] for r in records.values() if r["decoy"] for p in r["decoy"][1]}
        )
        wider.append(
            dict(
                offset=offset,
                real_values=values,
                decoy_values=decvals,
                discriminates_decoy=not set(values) & set(decvals),
                label="padding_candidate" if values == [0] else "unknown_stable_field",
            )
        )
    synthetic = {}
    # Choose a seed using raw structural content, never filename/intent semantics.
    seeds = [
        r for r in records.values() if r["reference"] and r["decoy"] and r["metrics"]["F0"]["reference_full_match"]
    ]
    if seeds:
        seed = min(seeds, key=lambda r: (len(r["rows"]), r["sha256"]))
        index, run = seed["reference"]
        for name, (kind, payloads) in synthetic_cases(seed["payloads"][index], run).items():
            analysis = inspect_payloads(payloads)
            synthetic[name] = dict(kind=kind, metrics=compact_metrics(analysis["metrics"]))
    else:
        warnings.append("No structural seed for synthetic challenge suite")
    profiles = {
        name: [[sorted({row[i] for row in r["rows"]}), len({row[i] for row in r["rows"]}) == 1] for i in range(112)]
        for name, r in records.items()
        if r["rows"]
    }
    return dict(
        warnings=warnings,
        fixture_inventory=inventory,
        metric_columns=METRIC_COLUMNS,
        fixture_metrics={name: compact_metrics(r["metrics"]) for name, r in records.items()},
        raw_layer_summary=dict(
            token_hits=sum(r["raw_token_count"] for r in records.values()),
            recurring_runs=sum(r["raw_recurring_runs"] for r in records.values()),
        ),
        positional_variability_map=var,
        wider_structural_inventory=wider,
        synthetic_controls=synthetic,
        _frozen_profiles=profiles,
    )


# Corpus labels are explicitly Phase B only. They never enter predicate evaluation.
PREVIOUS = (
    "default_text",
    "text_ascii_lowercase",
    "text_ascii_uppercase",
    "text_digits",
    "text_alphanumeric",
    "text_spaces",
    "text_special_characters",
    "text_color_army_green",
    "text_color_navy_blue",
    "text_height_10mm",
    "text_height_30mm",
    "text_font_arial",
    "text_font_arial_bold",
    "text_group_same_color_two_objects",
    "text_group_mixed_color_two_objects",
    "text_two_objects_same_color_not_grouped",
    "text_two_objects_mixed_color_not_grouped",
    "text_three_objects_grouped_order_abc",
    "text_three_objects_grouped_order_abc_content_variation",
    "text_three_objects_not_grouped",
    "text_multiline_basic",
    "text_spacing_fixed",
    "text_spacing_proportional",
    "text_spacing_print_proportional",
)
MULTILINE = PREVIOUS[-4:]
MULTI = PREVIOUS[13:20]
UNSUPPORTED = (
    "text_mirror_on",
    "text_slant_15deg",
    "text_slant_custom_30deg",
    "text_width_50_percent",
    "text_width_150_percent",
)
CONTROLLED = tuple(
    "text_slotstyle_a8_" + v
    for v in (
        "baseline",
        "char4_height20",
        "char4_width50",
        "char4_width150",
        "char4_slant_p15",
        "char4_slant_m15",
        "char4_rotation_p15",
        "char4_rotation_m15",
        "char4_navy",
    )
)


def load_labels(name):
    stem = Path(name).stem
    groups = []
    for group, names in [
        ("controlled", CONTROLLED),
        ("previous24", PREVIOUS),
        ("multiline", MULTILINE),
        ("multi_object", MULTI),
        ("unsupported_styles", UNSUPPORTED),
    ]:
        if stem in names:
            groups.append(group)
    # Intent is diagnostic, never passed back to discovery. Missing legacy intent is allowed.
    intent_path = SAMPLES / "intents/text" / (stem + ".md")
    intent = {}
    if intent_path.exists():
        text = intent_path.read_text(encoding="utf-8")
        if "```yaml\n" in text:
            import yaml

            intent = yaml.safe_load(text.split("```yaml\n", 1)[1].split("```", 1)[0]).get("intent_metadata", {})
    return dict(groups=groups, intent=intent)


def aggregate_metrics(evidence, names, hypothesis):
    rows = [dict(zip(METRIC_COLUMNS, evidence["fixture_metrics"][name][hypothesis])) for name in names]
    references = {r["fixture"]: r["reference_slots"] for r in evidence["fixture_inventory"]}
    decoy_n = sum(r["decoy_present"] for r in evidence["fixture_inventory"] if r["fixture"] in names)
    return dict(
        fixtures=len(rows),
        reference_runs=sum(references[n] > 0 for n in names),
        full_reference_matches=sum(r["reference_full_match"] for r in rows),
        unique_reference_matches=sum(r["unique_reference"] for r in rows),
        reference_slot_matches=sum(r["reference_slot_hits"] for r in rows),
        reference_slots=sum(references[n] for n in names),
        known_decoy_runs=decoy_n,
        known_decoy_matches=sum(r["known_decoy_full_match"] for r in rows),
        known_decoy_slot_hits=sum(r["known_decoy_slot_hits"] for r in rows),
        ambiguity_count=sum(r["ambiguous"] for r in rows),
        nonreference_maximal_runs=sum(r["nonreference_maximal_runs"] for r in rows),
        prefix_hits=sum(r["prefix_hits"] for r in rows),
        maximal_runs=sum(r["maximal_runs"] for r in rows),
        recurring_runs=sum(r["recurring_runs"] for r in rows),
        count_valid_runs=sum(r["count_valid_runs"] for r in rows),
        terminal_valid_runs=sum(r["terminal_valid_runs"] for r in rows),
        all_four_layers=sum(r["all_four_layers"] for r in rows),
    )


def oracle_phase(frozen, enabled):
    evidence = json.loads(frozen)
    if not enabled:
        return dict(enabled=False)
    groups = defaultdict(list)
    labels = {}
    warnings = []
    for item in evidence["fixture_inventory"]:
        name = item["fixture"]
        labels[name] = load_labels(name)
        if item["reference_slots"]:
            groups["all_reference_text"].append(name)
        elif item["paragraph_count"] == 0:
            groups["geometry_scope_negative"].append(name)
        else:
            groups["unresolved_paragraph"].append(name)
        for group in labels[name]["groups"]:
            groups[group].append(name)
    for group, size in [
        ("controlled", 9),
        ("previous24", 24),
        ("multiline", 4),
        ("multi_object", 7),
        ("unsupported_styles", 5),
    ]:
        if len(groups[group]) != size:
            warnings.append(f"{group}: expected {size} labels, found {len(groups[group])}")
    metrics = {
        group: {h: aggregate_metrics(evidence, names, h) for h in NAMES} for group, names in sorted(groups.items())
    }
    cohort_var = {}
    for group in ("controlled", "multiline", "multi_object", "unsupported_styles"):
        profiles = [evidence["_frozen_profiles"][n] for n in groups[group] if n in evidence["_frozen_profiles"]]
        cohort_var[group] = [
            [i - 16, sorted({v for p in profiles for v in p[i][0]}), sum(p[i][1] for p in profiles)] for i in range(112)
        ]
    byte08 = []
    for name, p in evidence["_frozen_profiles"].items():
        hints = [
            hint
            for hint in ("mixed_color", "same_color", "not_grouped", "multiline", "mirror", "slant", "width")
            if hint in name
        ]
        if ("group_" in name or "grouped_" in name) and "not_grouped" not in name:
            hints.append("grouped")
        byte08.append(
            [
                name,
                p[24][0],
                p[24][1],
                labels[name]["groups"],
                labels[name]["intent"].get("grouping", "unresolved"),
                hints,
            ]
        )
    return dict(
        enabled=True,
        group_metrics=metrics,
        cohort_variability_columns=["relative_offset", "unique_raw_values", "stable_runs"],
        cohort_variability=cohort_var,
        byte08_inventory=byte08,
        byte08_columns=[
            "fixture",
            "raw_values",
            "within_run_stable",
            "corpus_groups",
            "intent_grouping",
            "filename_hints_only",
        ],
        warnings=warnings,
        byte08_interpretation="unresolved; exact 00/01 raw classes only; not a wildcard or ownership flag",
    )


def build_report(paths=None, oracle_enabled=True, details=False):
    paths = sorted(SAMPLES.glob("*.txt")) + sorted((SAMPLES / "text").glob("*.txt")) if paths is None else paths
    frozen = compact(structural_phase(paths))
    oracle = oracle_phase(frozen, oracle_enabled)
    report = json.loads(frozen)
    report.pop("_frozen_profiles")
    report.update(
        mode="details" if details else "summary",
        policy=POLICY,
        limits=LIMITS,
        predicate_hypotheses=hypothesis_definitions(),
        oracle_summary=oracle,
    )
    report["warnings"].extend(oracle.get("warnings", []))
    corpus_names = list(report["fixture_metrics"])
    # Unlabelled totals stay identical with oracle on/off.
    report["identity_and_layer_totals"] = {h: aggregate_metrics(report, corpus_names, h) for h in NAMES}
    negative_rows = [r for r in report["synthetic_controls"].values() if r["kind"] == "negative"]
    report["synthetic_false_positive_summary"] = {
        h: dict(
            negative_cases=len(negative_rows),
            identity_false_positive_cases=sum(r["metrics"][h][4] > 0 for r in negative_rows),
            recurrence_false_positive_cases=sum(r["metrics"][h][6] > 0 for r in negative_rows),
            identity_collision_cases=sum(
                r["metrics"][h][4] > 0
                for r in report["synthetic_controls"].values()
                if r["kind"] == "identity_collision"
            ),
        )
        for h in NAMES
    }
    g = oracle.get("group_metrics", {})
    ready = all(
        g.get(k, {}).get("F4", {}).get("unique_reference_matches") == n
        for k, n in [
            ("controlled", 9),
            ("previous24", 24),
            ("multiline", 4),
            ("multi_object", 7),
            ("unsupported_styles", 5),
        ]
    )
    ready = ready and report["identity_and_layer_totals"]["F4"]["known_decoy_slot_hits"] == 0
    ready = ready and report["synthetic_false_positive_summary"]["F4"]["identity_false_positive_cases"] == 0
    ready = (
        ready and g.get("geometry_scope_negative", {}).get("F4", {}).get("prefix_hits") == 0 and not report["warnings"]
    )
    f4_totals = report["identity_and_layer_totals"]["F4"]
    ready = ready and f4_totals["unique_reference_matches"] == f4_totals["reference_runs"]
    ready = ready and f4_totals["nonreference_maximal_runs"] == 0
    collision_cases = sum(r["kind"] == "identity_collision" for r in report["synthetic_controls"].values())
    for h, summary in report["synthetic_false_positive_summary"].items():
        denominator = len(negative_rows) + collision_cases
        summary["all_negative_cases_including_identity_collisions"] = denominator
        summary["all_identity_false_positive_cases"] = (
            summary["identity_false_positive_cases"] + summary["identity_collision_cases"]
        )
        summary["all_identity_false_positive_rate"] = (
            summary["all_identity_false_positive_cases"] / denominator if denominator else None
        )
    ready = ready and (
        report["synthetic_false_positive_summary"]["F4"]["all_identity_false_positive_cases"]
        <= report["synthetic_false_positive_summary"]["F0"]["all_identity_false_positive_cases"]
    )
    controls = g.get("controlled", {})
    style_effect = (
        controls.get("F3", {}).get("full_reference_matches") == 9
        and controls.get("F0", {}).get("full_reference_matches", 9) < 9
    )
    report["answers"] = dict(
        old_family_interpretation="old_family_overconstrained_by_style_fields" if style_effect else "unresolved",
        old_v1="observed vector difference confined to height-correlated region; not a general semantic proof"
        if oracle_enabled
        else "unresolved",
        old_v2="unresolved; only one nonzero fixture, exact 00/01 policy retained",
        proposed_predicate="F4; additional constant has no assigned semantics",
        runtime_prefix_redesign_readiness="ready_for_rfc_review" if ready else "not_ready",
        parser_safe=False,
        ownership="unresolved",
        typed_widths=None,
        limitations=[
            "Reference runs are count/terminal research nominations, not ownership ground truth",
            "Geometry controls have no eligible paragraph if scope count is zero",
            "Identity-clone negatives remain prefix matches; count/terminal/ambiguity are separate layers",
            "F4 wider constants are corpus evidence, not confirmed structural semantics",
            "The v0/v1/v2 runtime family is retained for safety while redesign evidence is reviewed.",
        ],
    )
    if details:
        report["details"] = [
            dict(fixture=item["fixture"], metrics=report["fixture_metrics"][item["fixture"]])
            for item in report["fixture_inventory"]
            if item["reference_slots"]
        ][: LIMITS["details_fixtures"]]
    return report


def render_text(report):
    lines = [
        "CParagraphe prefix redesign: analysis only",
        compact(report["answers"]),
        "Layers remain independent; counts never remove prefix matches or ambiguity.",
    ]
    for h, row in report["identity_and_layer_totals"].items():
        lines.append(h + ": " + compact(row))
    lines.append("Synthetic negatives: " + compact(report["synthetic_false_positive_summary"]))
    for group, metrics in report["oracle_summary"].get("group_metrics", {}).items():
        lines.append(
            group
            + ": "
            + compact(
                {
                    h: dict(
                        full=r["full_reference_matches"],
                        unique=r["unique_reference_matches"],
                        total=r["reference_runs"],
                        ambiguity=r["ambiguity_count"],
                    )
                    for h, r in metrics.items()
                }
            )
        )
    lines.append("Additional stable positions: " + compact(report["wider_structural_inventory"]))
    lines.extend(report["warnings"])
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-oracle", action="store_true")
    p.add_argument("--details", action="store_true")
    p.add_argument("--fixtures", type=Path, nargs="+")
    args = p.parse_args()
    try:
        report = build_report(args.fixtures, not args.no_oracle, args.details)
        output = compact(report) + "\n" if args.json else render_text(report)
        if len(output.encode()) >= LIMITS["json_bytes" if args.json else "text_bytes"]:
            raise ValueError("output budget exceeded; no partial output emitted")
    except ValueError as exc:
        p.error(str(exc))
    print(output, end="")


if __name__ == "__main__":
    main()
