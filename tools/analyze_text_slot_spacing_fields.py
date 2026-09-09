"""Spacing-only differential evidence; no runtime or F4 modification."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_slot_style_fields as prior  # noqa: E402
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser  # noqa: E402
from type3_clipboard_codec.inspect.formatters import _json_safe  # noqa: E402
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser  # noqa: E402

TEXT = ROOT / "tests/samples/text"
INTENTS = ROOT / "tests/samples/intents/text"
BASELINE = "text_slotstyle_a8_baseline.txt"
# Inventory only. No member's spelling participates in structural selection.
FIXTURES = (BASELINE, "text_slotstyle_a8_char4_spacing50.txt", "text_slotstyle_a8_char4_spacing150.txt",
            "text_slotstyle_a8_char6_spacing150.txt", "text_slotstyle_a8_all_spacing150.txt")
POLICY = dict(scope="character_spacing_per_slot_differential_and_f4_falsification_only",
              runtime_parser_behavior="not_modified", f4_runtime_change="not_performed",
              semantic_spacing_promotion="not_performed", ownership_assignment="not_performed",
              oracle_isolation=True)
LIMITS = dict(max_fixtures=5, max_hex_bytes=8_388_608, max_paragraph_bytes=1_048_576,
              max_nodes=128, max_paragraphs=32, max_prefix_hits=4096, max_slots=256,
              max_ranges=256, fragment_bytes=16, max_diagnostic_windows=16,
              detail_slots=4, json_bytes=100000, text_bytes=50000)
REGIONS = {"f4_region_a_summary": (36, 44), "f4_region_b_summary": (56, 64),
           "auxiliary_region_summary": (44, 48)}
EXPECTED_F4 = {"f4_region_a_summary": "00" * 8, "f4_region_b_summary": "9a9999999999d9bf"}


def compact(value):
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


def changed_ranges(a, b, raw=True):
    """Full comparison; retain unequal-length tails and bound only raw fragments."""
    spans = prior.ranges(a, b)
    rows = []
    for lo, hi in spans:
        row = dict(relative_range=[lo, hi], changed_byte_count=hi - lo)
        if raw:
            end = min(hi, lo + LIMITS["fragment_bytes"])
            row.update(baseline_hex=a[lo:end].hex(), fixture_hex=b[lo:end].hex(),
                       raw_fragment_truncated=end < hi)
        rows.append(row)
    return dict(baseline_length=len(a), fixture_length=len(b), changed_byte_count=sum(hi-lo for lo, hi in spans),
                ranges=rows)


def observe_runtime(raw):
    obj, parser = parse_type3_clipboard_bytes_with_parser(raw)
    candidate = obj.candidate_fields.get("text_slot_run")
    observation = dict(parse_success=True, parser=parser, candidate_present=candidate is not None,
                       status="candidate_present" if candidate else "safe_abstention")
    if candidate:
        observation.update(source=candidate["source"], first_prefix=candidate["first_prefix_relative_offset"],
                           slot_count=len(candidate["slots"]), prefix_family=candidate["prefix_family"],
                           plus08_value=candidate["plus08_value"])
    return observation, digest(asdict(obj))


def read_capture(path):
    file_bytes = path.read_bytes() if path.stat().st_size <= LIMITS["max_hex_bytes"] else None
    if file_bytes is None:
        raise ValueError("hex input budget exceeded")
    raw = prior.hex_text_to_bytes(file_bytes.decode("utf-8"))
    # Actual runtime is observed BEFORE independent discovery; its result never selects a run.
    runtime, parser_digest = observe_runtime(raw)
    parser = Type3ChainParser()
    _, _, base = parser._read_top_level_header(raw)
    nodes = parser._extract_nodes(raw[base:])
    paragraphs = [n for n in nodes if n.header.class_name == "CParagraphe"]
    if len(nodes) > LIMITS["max_nodes"] or len(paragraphs) > LIMITS["max_paragraphs"]:
        raise ValueError("node/paragraph budget exceeded")
    if sum(len(n.payload) for n in paragraphs) > LIMITS["max_paragraph_bytes"]:
        raise ValueError("paragraph byte budget exceeded")
    if sum(n.payload.count(prior.TOKEN) for n in paragraphs) > LIMITS["max_prefix_hits"]:
        raise ValueError("token budget exceeded")
    runs = [dict(paragraph_index=i, **r) for i, node in enumerate(paragraphs) for r in prior.discover(node.payload)]
    eligible = [r for r in runs if r["eligible"]]
    selected = eligible[0] if len(eligible) == 1 else None
    if selected and selected["count"] > LIMITS["max_slots"]:
        raise ValueError("slot budget exceeded")
    return dict(raw=raw, runtime=runtime, parser_digest=parser_digest, file_sha256=hashlib.sha256(file_bytes).hexdigest(),
                base=base, nodes=nodes, paragraphs=paragraphs, runs=runs, selected=selected)


def slots(data):
    run = data["selected"]
    payload = data["paragraphs"][run["paragraph_index"]].payload
    return [payload[p:p+204] for p in range(run["start"], run["end"], 204)]


def diagnostic_windows(spans):
    """Only exact discovered ranges; never enlarge a delta to obtain a type."""
    windows = sorted({(lo, hi) for lo, hi in spans if hi - lo in (4, 8)})
    if len(windows) > LIMITS["max_diagnostic_windows"]:
        raise ValueError("diagnostic-window budget exceeded")
    return windows


def compare(base, capture, details=False):
    a, b = base["selected"], capture["selected"]
    if not a or not b or a["count"] != b["count"]:
        return dict(status="unresolved", reason="no unique compatible independently framed run")
    left, right = slots(base), slots(capture)
    if [x[:8] for x in left] != [x[:8] for x in right]:
        return dict(status="unresolved", reason="cross-capture raw prefix/code alignment disagrees")
    rows = []
    for i, (x, y) in enumerate(zip(left, right, strict=True)):
        diff = changed_ranges(x, y)
        rows.append(dict(slot_ordinal_zero_based=i, visible_index_1based=i+1 if i < len(left)-1 else None,
                         terminal=i == len(left)-1, **diff))
    p = base["paragraphs"][a["paragraph_index"]]
    q = capture["paragraphs"][b["paragraph_index"]]
    start_a, start_b = base["base"] + p.payload_offset, capture["base"] + q.payload_offset
    secondary = dict(
        before_first_slot=changed_ranges(p.payload[:a["start"]], q.payload[:b["start"]], False),
        after_slot_windows=changed_ranges(p.payload[a["end"]:], q.payload[b["end"]:], False),
        before_selected_payload=changed_ranges(base["raw"][:start_a], capture["raw"][:start_b], False),
        after_selected_payload=changed_ranges(base["raw"][start_a+len(p.payload):],
                                             capture["raw"][start_b+len(q.payload):], False),
        paragraph_header=changed_ranges(base["raw"][base["base"]+p.start_offset:start_a],
                                        capture["raw"][capture["base"]+q.start_offset:start_b], False),
        selected_paragraph_bbox_changed=p.bbox != q.bbox,
        other_nodes=[],
        node_alignment="aligned" if [n.header.class_name for n in base["nodes"]] == [
            n.header.class_name for n in capture["nodes"]] else "unresolved",
    )
    if secondary["node_alignment"] == "aligned":
        for i, (x, y) in enumerate(zip(base["nodes"], capture["nodes"], strict=True)):
            if x is p and y is q:
                continue
            secondary["other_nodes"].append(dict(node_index=i, class_name=x.header.class_name,
                                                payload=changed_ranges(x.payload, y.payload, False),
                                                header=changed_ranges(
                                                    base["raw"][base["base"]+x.start_offset:base["base"]+x.payload_offset],
                                                    capture["raw"][capture["base"]+y.start_offset:
                                                                   capture["base"]+y.payload_offset], False),
                                                bbox_changed=x.bbox != y.bbox))
    result = dict(status="aligned", count=len(left), baseline_start=a["start"], fixture_start=b["start"],
                  payload_sources=[[start_a, len(p.payload)], [start_b, len(q.payload)]],
                  coordinate_domain="cparagraphe_payload_relative", periodic_window_bytes=204,
                  slots=rows, terminal_changed=left[-1] != right[-1], secondary=secondary,
                  positive_controls=dict(code_baseline=[x[4:8].hex() for x in left],
                                         code_fixture=[x[4:8].hex() for x in right],
                                         rgb_baseline=[x[80:83].hex() for x in left],
                                         rgb_fixture=[x[80:83].hex() for x in right]))
    if details:
        result["representative_slots"] = [r for r in rows if r["changed_byte_count"]][:LIMITS["detail_slots"]]
    return result


def structural_phase(paths, baseline, details=False):
    if len(paths) > LIMITS["max_fixtures"] or len({p.name for p in paths}) != len(paths):
        raise ValueError("fixture budget or duplicate labels")
    loaded, inventory, warnings = {}, [], []
    for path in paths:
        try:
            data = read_capture(path)
            loaded[path.name] = data
            inventory.append(dict(fixture=path.name, file_sha256=data["file_sha256"],
                                  raw_sha256=hashlib.sha256(data["raw"]).hexdigest(), raw_size=len(data["raw"])))
        except (OSError, ValueError, EOFError) as exc:
            warnings.append(f"{path.name}: unresolved: {exc}")
    reference = loaded.get(baseline)
    diffs = {}
    for name, data in loaded.items():
        try:
            diffs[name] = compare(reference, data, details) if reference else dict(status="unresolved")
        except ValueError as exc:
            diffs[name] = dict(status="unresolved", reason=str(exc))
        if diffs[name]["status"] != "aligned":
            warnings.append(name + ": structural alignment unresolved")
    spans = Counter(tuple(r["relative_range"]) for d in diffs.values() for s in d.get("slots", []) for r in s["ranges"])
    windows = diagnostic_windows(spans)
    regions = {key: dict(relative_range=[lo, hi], fixtures={}) for key, (lo, hi) in REGIONS.items()}
    profiles = {f"{lo}:{hi}": dict(relative_range=[lo, hi], typed_width=None, fixtures={}) for lo, hi in spans}
    if reference and reference["selected"]:
        left = slots(reference)
        for name, data in loaded.items():
            if diffs[name]["status"] != "aligned":
                continue
            right = slots(data)
            for key, (lo, hi) in REGIONS.items():
                regions[key]["fixtures"][name] = [dict(
                    ordinal=i, terminal=i == len(left)-1, baseline_hex=x[lo:hi].hex(), fixture_hex=y[lo:hi].hex(),
                    changed=x[lo:hi] != y[lo:hi]) for i, (x, y) in enumerate(zip(left, right, strict=True))]
            for profile in profiles.values():
                lo, hi = profile["relative_range"]
                profile["fixtures"][name] = dict(baseline=[x[lo:hi].hex() for x in left],
                                               fixture=[x[lo:hi].hex() for x in right])
    for name, data in loaded.items():
        _, after = observe_runtime(data["raw"])
        if after != data["parser_digest"]:
            raise ValueError("runtime parser output changed during independent analysis")
    return dict(
        mode="details" if details else "summary", policy=POLICY, limits=LIMITS, warnings=warnings,
        fixture_inventory=inventory, runtime_candidate_summary={n: d["runtime"] for n, d in loaded.items()},
        structural_alignment_summary={n: dict(status=diffs[n]["status"], raw_runs=d["runs"],
                                              selected=d["selected"], runtime_output_unchanged=True)
                                      for n, d in loaded.items()},
        per_fixture_differentials=diffs,
        changed_range_summary=dict(ranges=[dict(relative_range=list(r), slot_occurrences=count)
                                          for r, count in sorted(spans.items())],
                                   diagnostic_containers=list(profiles.values()),
                                   diagnostic_ranges=[list(w) for w in windows],
                                   note="Half-open exact deltas; numeric diagnostics only for exact 4/8-byte deltas"),
        **regions,
        secondary_change_summary={n: d.pop("secondary") for n, d in diffs.items() if d["status"] == "aligned"},
    )


def load_intent(name):
    import yaml
    text = (INTENTS / (Path(name).stem + ".md")).read_text(encoding="utf-8")
    return yaml.safe_load(text.split("```yaml\n", 1)[1].split("```", 1)[0])["intent_metadata"]


def oracle_phase(frozen, enabled, baseline):
    """Only frozen JSON crosses into interpretation; no payloads or discovery calls."""
    evidence = json.loads(frozen)
    if not enabled:
        return dict(enabled=False, status="unresolved")
    labels, warnings, targets = {}, [], {}
    for row in evidence["fixture_inventory"]:
        name = row["fixture"]
        if name == baseline:
            continue
        try:
            meta = load_intent(name)
            if meta.get("property") != "character_spacing":
                raise ValueError("not a spacing intent")
            labels[name] = meta
            targets[name] = ([meta["target_character_index_1based"] - 1] if meta["changed_scope"] == "character"
                             else [v-1 for v in meta["target_character_indices_1based"]])
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            warnings.append(name + ": intent unresolved: " + str(exc))
    evaluated = []
    for container in evidence["changed_range_summary"]["diagnostic_containers"]:
        lo, hi = container["relative_range"]
        width = hi-lo
        if width not in (4, 8):
            continue
        fmt = "<d" if width == 8 else "<f"
        observations = []
        for name, meta in labels.items():
            profile = container["fixtures"].get(name)
            if profile is None:
                continue
            for i in targets[name]:
                if not 0 <= i < len(profile["fixture"]) - 1:
                    continue  # Terminal is never silently accepted as an intended visible target.
                a, b = profile["baseline"][i], profile["fixture"][i]
                av, bv = struct.unpack(fmt, bytes.fromhex(a))[0], struct.unpack(fmt, bytes.fromhex(b))[0]
                observations.append(dict(fixture=name, ordinal=i, baseline_raw=a, fixture_raw=b,
                                         baseline_value=av if math.isfinite(av) else None,
                                         fixture_value=bv if math.isfinite(bv) else None,
                                         baseline_percent=meta["baseline_value_percent"],
                                         fixture_percent=meta["changed_value_percent"]))
        hypotheses = {}
        for label, scale, shift in (("normalized_ratio", 100, 0), ("delta_from_baseline", 100, -1),
                                    ("raw_percentage", 1, 0)):
            hypotheses[label] = bool(observations) and all(
                o["baseline_value"] == o["baseline_percent"] / scale + shift and
                o["fixture_value"] == o["fixture_percent"] / scale + shift for o in observations)
        evaluated.append(dict(relative_range=[lo, hi], diagnostic_type="f64le" if width == 8 else "f32le",
                              hypotheses=hypotheses, observations=observations, typed_width=None))
    matches = [r for r in evaluated if any(r["hypotheses"].values())]
    chosen = matches[0] if len(matches) == 1 else None
    per_fixture = {}
    region_labels = {key: {} for key in REGIONS}
    for name, meta in labels.items():
        diff = evidence["per_fixture_differentials"].get(name, {})
        if diff.get("status") != "aligned":
            continue
        intended = targets[name]
        valid_targets = bool(intended) and len(set(intended)) == len(intended) and all(
            0 <= i < diff["count"]-1 for i in intended)
        changed = [s["slot_ordinal_zero_based"] for s in diff["slots"] if s["changed_byte_count"]]
        per_fixture[name] = dict(intended_visible_ordinals=intended, valid_visible_targets=valid_targets,
                                 actual_changed_ordinals=changed, visible_isolation=valid_targets and
                                 [i for i in changed if i < diff["count"]-1] == intended,
                                 terminal_changed=diff["terminal_changed"], percent=meta["changed_value_percent"])
        for key in REGIONS:
            region_labels[key][name] = [dict(ordinal=r["ordinal"], changed=r["changed"],
                                            role="terminal" if r["terminal"] else
                                            "visible_target" if r["ordinal"] in intended else "visible_non_target")
                                       for r in evidence[key]["fixtures"].get(name, [])]
    # Correlation and ordinal transfer are raw evidence, independent of numeric decoding.
    raw_candidates = []
    for profile in evidence["changed_range_summary"]["diagnostic_containers"]:
        observations = []
        isolated = bool(labels)
        for name, meta in labels.items():
            values = profile["fixtures"].get(name)
            if values is None or not per_fixture.get(name, {}).get("valid_visible_targets"):
                isolated = False
                continue
            changed = [i for i, (a, b) in enumerate(zip(values["baseline"][:-1], values["fixture"][:-1])) if a != b]
            isolated &= changed == targets[name]
            observations.extend(dict(fixture=name, ordinal=i, fixture_percent=meta["changed_value_percent"],
                                     fixture_raw=values["fixture"][i]) for i in targets[name])
        if isolated:
            raw_candidates.append(dict(relative_range=profile["relative_range"], observations=observations))
    primary = raw_candidates[0] if len(raw_candidates) == 1 else None
    transfer = []
    if primary:
        obs = primary["observations"]
        for j, a in enumerate(obs):
            for b in obs[j+1:]:
                if (a["fixture"] != b["fixture"] and len(targets[a["fixture"]]) == len(targets[b["fixture"]]) == 1
                        and a["ordinal"] != b["ordinal"] and a["fixture_percent"] == b["fixture_percent"]):
                    transfer.append(dict(fixtures=[a["fixture"], b["fixture"]],
                                         ordinals=[a["ordinal"], b["ordinal"]], relative_range=primary["relative_range"],
                                         same_raw=a["fixture_raw"] == b["fixture_raw"],
                                         isolated=all(per_fixture[n]["visible_isolation"]
                                                      for n in (a["fixture"], b["fixture"]))))
    all_runs = [n for n, meta in labels.items() if meta["changed_scope"] == "all_visible_characters"]
    replication, terminal = {}, {}
    if primary:
        profile = next(p for p in evidence["changed_range_summary"]["diagnostic_containers"]
                       if p["relative_range"] == primary["relative_range"])
        for name, values in profile["fixtures"].items():
            if name == baseline:
                continue
            terminal[name] = dict(baseline_raw=values["baseline"][-1], fixture_raw=values["fixture"][-1],
                                  changed=values["baseline"][-1] != values["fixture"][-1],
                                  matches_first_visible=values["fixture"][-1] == values["fixture"][0],
                                  intentionally_targeted=False)
            if name in all_runs and name in per_fixture:
                raw = values["fixture"][:-1]
                replication[name] = bool(raw) and len(set(raw)) == 1 and per_fixture[name]["visible_isolation"]
    return dict(enabled=True, warnings=warnings, labels=labels, per_fixture=per_fixture, primary=primary,
                region_roles=region_labels, encoding_tests=evaluated, selected_encoding=chosen,
                ordinal_transfer_pairs=transfer, ordinal_transfer_supported=bool(transfer) and
                all(p["same_raw"] and p["isolated"] for p in transfer),
                visible_slot_replication_supported=bool(replication) and all(replication.values()),
                replication=replication, terminal=terminal,
                natural_baseline_length_mm=74.584,
                integer_probe_status="not_attempted: changed high bytes alone do not justify integer storage",
                note="Exact delta is one byte in current controls: f64/f32/integer encoding unresolved; no widened probes")


def finish_report(evidence, oracle):
    enabled = oracle.get("enabled", False)
    chosen = oracle.get("selected_encoding")
    region_status = {}
    for key in ("f4_region_a_summary", "f4_region_b_summary"):
        rows = [r for values in evidence[key]["fixtures"].values() for r in values]
        if not rows:
            state = "unresolved"
        elif all(not r["changed"] and r["fixture_hex"] == EXPECTED_F4[key] for r in rows):
            state = "not_falsified_by_current_spacing_controls"
        else:
            state = "changed_interpretation_unresolved"
        region_status[key] = state
        evidence[key]["status"] = state
        evidence[key]["oracle_roles"] = oracle.get("region_roles", {}).get(key, {})
    stable = all(v == "not_falsified_by_current_spacing_controls" for v in region_status.values())
    isolation = oracle.get("per_fixture", {})
    aux = [r for rows in evidence["auxiliary_region_summary"]["fixtures"].values() for r in rows]
    evidence["auxiliary_region_summary"]["status"] = (
        "unchanged_in_current_controls_semantics_unresolved" if aux and all(not r["changed"] for r in aux)
        else "unresolved")
    evidence.update(
        ordinal_transfer_summary=dict(ordinal_transfer_supported=oracle.get("ordinal_transfer_supported", False),
                                      pairs=oracle.get("ordinal_transfer_pairs", [])),
        all_character_replication_summary=dict(visible_slot_replication_supported=oracle.get(
            "visible_slot_replication_supported", False), terminal=oracle.get("terminal", {})),
        spacing_encoding_summary=dict(status="diagnostic_encoding_candidate" if chosen else "unresolved",
                                      selected=chosen, tests=oracle.get("encoding_tests", []), typed_width=None),
        oracle_summary=oracle,
        answers=dict(
            fixtures_aligned=sum(d["status"] == "aligned" for d in evidence["per_fixture_differentials"].values()),
            runtime_candidate_presence={n: v["candidate_present"] for n, v in evidence["runtime_candidate_summary"].items()},
            primary_spacing_relative_range=oracle.get("primary", {}).get("relative_range") if oracle.get("primary") else None,
            char4_low_high_isolation_status="supported" if enabled and isolation and all(
                r["visible_isolation"] for r in isolation.values()) else "unresolved",
            char4_to_char6_ordinal_transfer_status="supported" if oracle.get("ordinal_transfer_supported") else "unresolved",
            all_visible_slot_replication_status="visible_slot_replication_supported" if oracle.get(
                "visible_slot_replication_supported") else "unresolved",
            terminal_spacing_behavior=oracle.get("terminal", {}),
            diagnostic_spacing_encoding=(dict(relative_range=chosen["relative_range"], type=chosen["diagnostic_type"],
                                               matched_hypotheses=[k for k, v in chosen["hypotheses"].items() if v])
                                         if chosen else "unresolved"),
            f4_plus24_constant_status=region_status["f4_region_a_summary"],
            f4_plus38_constant_status=region_status["f4_region_b_summary"],
            f4_style_contamination_status="not_demonstrated_by_current_spacing_controls" if stable else "unresolved",
            auxiliary_plus2c_2f_status=evidence["auxiliary_region_summary"]["status"],
            spacing_field_readiness="strong_style_field_candidate" if oracle.get("primary") and oracle.get(
                "ordinal_transfer_supported") and oracle.get("visible_slot_replication_supported") else "unresolved",
            runtime_f4_review_readiness="no_spacing_falsification_trigger" if stable else "unresolved",
            runtime_change_readiness="not_authorized_in_this_task", parser_safe=False, ownership_status="unresolved"))
    return evidence


def build_report(paths=None, baseline=BASELINE, oracle_enabled=True, details=False):
    paths = [TEXT / name for name in FIXTURES] if paths is None else list(paths)
    frozen = compact(structural_phase(paths, baseline, details))
    oracle = oracle_phase(frozen, oracle_enabled, baseline)
    oracle["structural_sha256"] = hashlib.sha256(frozen.encode()).hexdigest()
    return finish_report(json.loads(frozen), oracle)


def render(report, json_output=False):
    if json_output:
        output = compact(report) + "\n"
    else:
        output = "Spacing-only differential / F4 review evidence\n" + compact(report["answers"]) + "\n"
        for name, diff in report["per_fixture_differentials"].items():
            output += name + ": " + diff["status"] + "\n"
            for slot in diff.get("slots", []):
                if slot["changed_byte_count"]:
                    output += compact(slot) + "\n"
        output += "Secondary changes (raw ranges, not semantic assignments):\n" + compact(report["secondary_change_summary"]) + "\n"
    if len(output.encode()) >= LIMITS["json_bytes" if json_output else "text_bytes"]:
        raise ValueError("output budget exceeded; no partial report")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-oracle", action="store_true")
    parser.add_argument("--details", action="store_true")
    parser.add_argument("--fixtures", type=Path, nargs="+")
    parser.add_argument("--baseline", default=BASELINE, help="comparison reference label only")
    args = parser.parse_args()
    try:
        print(render(build_report(args.fixtures, args.baseline, not args.no_oracle, args.details), args.json), end="")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
