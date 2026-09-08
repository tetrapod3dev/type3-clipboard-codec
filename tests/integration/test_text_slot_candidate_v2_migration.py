"""Exact historical-v1 baseline comparison with the reviewed v2 delta only."""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

from tests.text_slot_v1_replay import SOURCE, legacy, replay_parser
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.codec.preview import PreviewRenderer
from type3_clipboard_codec.inspect.formatters import _json_safe, to_inspection_dict
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text import text_slot_candidate as runtime

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "tests/samples/reports/text"
BASELINE = json.loads((REPORTS / "text_slot_family_shadow_baseline.json").read_text())
SHADOW = json.loads((REPORTS / "text_slot_family_shadow_comparison.json").read_text())
ROWS = {r["fixture"]: r for r in SHADOW["fixture_results"]}
GAINS = {
    "text_slotstyle_a8_char4_height20.txt", "text_mirror_on.txt", "text_width_50_percent.txt",
    "text_width_150_percent.txt", "text_slotstyle_a8_char4_width50.txt", "text_slotstyle_a8_char4_width150.txt",
    "text_slant_15deg.txt", "text_slant_custom_30deg.txt", "text_slotstyle_a8_char4_slant_p15.txt",
    "text_slotstyle_a8_char4_slant_m15.txt",
}


def digest(value):
    encoded = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def presentation(obj, parser):
    return [PreviewRenderer().render(obj), PreviewRenderer().render(obj, verbose=True),
            to_inspection_dict(obj, parser, "shadow_regression")]


def ordered(value):
    if isinstance(value, dict):
        return [(k, ordered(v)) for k, v in value.items()]
    if isinstance(value, (list, tuple)):
        return [ordered(v) for v in value]
    return value


def expected_candidate(raw, view, payload_index):
    """Construct the entire expected dict from frozen positions and independent raw reads."""
    start, length = view["payload_source"]
    payload = raw[start:start + length]
    first = view["first_prefix"]
    positions = view["prefix_positions"]
    assert view["slot_count"] == len(positions)
    assert view["count_probe"] == first - 4
    assert view["terminal_prefix"] == positions[-1]
    slots = []
    for i, p in enumerate(positions):
        code = payload[p + 4:p + 8]
        slots.append(dict(
            ordinal=i, prefix_relative_offset=p,
            slot_code_candidate=dict(raw_bytes=code, numeric_view=int.from_bytes(code, "little"),
                                     typed_width=None, confidence="provisional"),
            rgb_bytes_candidate=dict(raw_bytes=list(payload[p + 80:p + 83]), typed_width=None,
                                     confidence="provisional"),
            terminal_candidate=i == len(positions) - 1, ownership="unresolved", matched_chain=None,
            raw_span=dict(coordinate_domain="cparagraphe_payload_relative", start=p, length=92),
        ))
    return dict(
        source="CParagraphe_slot_prefix_family_v2", confidence="provisional", parser_safe=False,
        ownership="unresolved", matched_chain=None, payload_index=payload_index,
        first_prefix_relative_offset=first,
        count_candidate=dict(raw_window=payload[first - 16:first], window_relative_start=-16,
                             probe_relative_offset=-4, numeric_views={
                                 name: dict(value=int.from_bytes(payload[first - 4:first - 4 + width], "little"),
                                            width=width, relative_offset=-4)
                                 for name, width in (("u8", 1), ("u16le", 2), ("u32le", 4))},
                             validated_total_slot_count=len(positions), typed_width=None, confidence="provisional"),
        stride=204, prefix_family="F4", plus08_value=payload[first + 8], slots=slots,
        payload_span=dict(buffer="raw_data", coordinate_domain="raw_data_relative", start=start, length=length),
        descriptor_relative_offset=view["descriptor"],
    )


@pytest.mark.parametrize("name", sorted(ROWS))
def test_exact_migration_and_semantic_presentation_allowlist(name):
    path = ROOT / "tests/samples" / name
    if not path.exists():
        path = ROOT / "tests/samples/text" / name
    raw = hex_text_to_bytes(path.read_text(encoding="utf-8"))
    frozen = BASELINE["fixtures"][name]
    assert hashlib.sha256(raw).hexdigest() == frozen["raw_sha256"]
    with replay_parser():
        before, old_parser = parse_type3_clipboard_bytes_with_parser(raw)
    assert digest(asdict(before)) == frozen["parser_sha256"]
    assert digest(presentation(before, old_parser)) == frozen["presentation_sha256"]
    after, parser = parse_type3_clipboard_bytes_with_parser(raw)
    old = before.candidate_fields.get("text_slot_run")
    new = after.candidate_fields.get("text_slot_run")
    row = ROWS[name]
    assert (old is not None) == row["v1"]["present"]
    assert (new is not None) == row["v2"]["present"]
    normalized = deepcopy(after)
    if new is not None:
        view = row["v1"]["run"] if old is not None else row["v2"]["run"]
        # Independently identify eligible paragraph index from the structural node inventory.
        from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser
        probe = Type3ChainParser()
        _, _, base = probe._read_top_level_header(raw)
        nodes = [n for n in probe._extract_nodes(raw[base:]) if n.header.class_name == "CParagraphe"]
        index = next(i for i, n in enumerate(nodes) if base + n.payload_offset == view["payload_source"][0])
        assert new == expected_candidate(raw, view, index)
        span = new["payload_span"]
        payload = raw[span["start"]:span["start"] + span["length"]]
        assert new["plus08_value"] in (0, 1)
        assert "prefix_variant" not in new
        for slot in new["slots"]:
            assert "prefix_variant" not in slot
            assert payload[slot["prefix_relative_offset"] + 8] == new["plus08_value"]
        if old is not None:
            adjusted = deepcopy(new)
            assert adjusted.pop("prefix_family") == "F4"
            adjusted.pop("plus08_value")
            assert adjusted["source"] == "CParagraphe_slot_prefix_family_v2"
            assert old["source"] == "CParagraphe_slot_prefix_family_v1"
            adjusted["source"] = old["source"]
            assert old["prefix_variant"] in ("v0", "v1", "v2")
            adjusted["prefix_variant"] = old["prefix_variant"]
            for current, previous in zip(adjusted["slots"], old["slots"], strict=True):
                assert previous["prefix_variant"] in ("v0", "v1", "v2")
                current["prefix_variant"] = previous["prefix_variant"]
            assert adjusted == old
            assert [k for k in new if k not in {"prefix_family", "plus08_value"}] == [
                k for k in old if k != "prefix_variant"]
            for current, previous in zip(new["slots"], old["slots"], strict=True):
                assert list(current) == [k for k in previous if k != "prefix_variant"]
            # Restore only removed metadata at its original insertion locations.
            adjusted = {k: adjusted[k] for k in old}
            adjusted["slots"] = [{k: slot[k] for k in previous}
                                 for slot, previous in zip(adjusted["slots"], old["slots"], strict=True)]
            normalized.candidate_fields["text_slot_run"] = adjusted
        else:
            assert name in GAINS
            del normalized.candidate_fields["text_slot_run"]
    else:
        assert old is None and name not in GAINS
    # Only the separately validated entry delta is reversed; every other field remains.
    assert asdict(normalized) == asdict(before)
    assert ordered(asdict(normalized)) == ordered(asdict(before))
    assert parser == old_parser
    assert presentation(normalized, parser) == presentation(before, old_parser)
    assert PreviewRenderer().render(after) == PreviewRenderer().render(before)
    inspected = to_inspection_dict(after, parser, "shadow_regression")
    prior_inspected = to_inspection_dict(before, old_parser, "shadow_regression")
    assert inspected["candidate_fields"].get("text_slot_run") == _json_safe(new)
    if old is None:
        inspected["candidate_fields"].pop("text_slot_run", None)
    else:
        inspected["candidate_fields"]["text_slot_run"] = prior_inspected["candidate_fields"]["text_slot_run"]
    assert inspected == prior_inspected
    before_verbose = PreviewRenderer().render(before, verbose=True)
    if old is not None:
        assert before_verbose.count(repr(old)) == 1
        expected_verbose = before_verbose.replace(repr(old), repr(new), 1)
    elif new is not None:
        old_fields = repr(before.candidate_fields)
        new_fields = old_fields[:-1] + ", 'text_slot_run': " + repr(new) + "}"
        assert new_fields == repr(after.candidate_fields)
        assert before_verbose.count(old_fields) == 1
        expected_verbose = before_verbose.replace(old_fields, new_fields, 1)
    else:
        expected_verbose = before_verbose
    assert PreviewRenderer().render(after, verbose=True) == expected_verbose


def test_exact_corpus_and_unchanged_other_sources():
    assert len(ROWS) == 104
    assert {n for n, r in ROWS.items() if r["outcome"] == "v1_absent_v2_present"} == GAINS
    assert sum(r["v1"]["present"] for r in ROWS.values()) == 62
    assert sum(r["v2"]["present"] for r in ROWS.values()) == 72
    for path, expected in BASELINE["source_sha256"].items():
        actual = Path(legacy.__file__) if path == SOURCE.as_posix() else ROOT / path
        assert hashlib.sha256(actual.read_bytes()).hexdigest() == expected
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    assert "CParagraphe_slot_prefix_family_v1" not in source
    assert "prefix_variant" not in source
    assert "tools" not in source and "tests" not in source


def test_runtime_full_identity_accounting_decoys_and_prior_challenges():
    from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser
    from tools import analyze_text_slot_prefix_redesign as research

    totals = dict(raw_token_hits=0, identity_positions=0, maximal_runs=0, suffix_positions_removed=0,
                  unsupported_contexts=0, globally_competing_runs=0)
    decoy_runs = decoy_positions = successes = 0
    seed = None
    for name, row in ROWS.items():
        path = ROOT / "tests/samples" / name
        if not path.exists():
            path = ROOT / "tests/samples/text" / name
        raw = hex_text_to_bytes(path.read_text(encoding="utf-8"))
        parser = Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        payloads = [n.payload for n in parser._extract_nodes(raw[base:]) if n.header.class_name == "CParagraphe"]
        candidate, audit = runtime._evaluate(payloads)
        for key in totals:
            totals[key] += audit[key]
        successes += candidate is not None
        assert audit["scan_complete"]
        for decoy in row["decoys"]:
            decoy_runs += 1
            payload = payloads[decoy["payload_index"]]
            for i in range(decoy["slots"]):
                p = decoy["decoy_first"] + i * 204
                assert payload[p:p + 4] == runtime.TOKEN
                assert runtime._family(payload, p) is None  # Ordinary mismatch, no global veto.
                decoy_positions += 1
        if candidate is not None and seed is None:
            seed = (payloads[candidate["payload_index"]],
                    [s["prefix_relative_offset"] for s in candidate["slots"]])
    assert totals == dict(raw_token_hits=1184, identity_positions=592, maximal_runs=72,
                          suffix_positions_removed=520, unsupported_contexts=0, globally_competing_runs=0)
    assert (decoy_runs, decoy_positions, successes) == (72, 592, 72)
    cases = research.synthetic_cases(*seed)
    assert len(cases) == 9
    assert sum(kind == "negative" for kind, _ in cases.values()) == 6
    for name, (kind, payloads) in cases.items():
        # Retain historical windows; extend only the synthetic next-probe context to 64.
        candidate, audit = runtime._evaluate([p + b"\xcc" * 32 for p in payloads])
        assert candidate is None
        if kind == "identity_collision":
            assert audit["identity_positions"] > 0 and audit["maximal_runs"] == 1
            assert audit["failing_layer"] == ("count" if name.endswith("wrong_count") else "terminal")
        elif kind == "ambiguity_control":
            assert audit["reason"] == "multiple_runs"


def test_runtime_selection_ignores_filename_and_oracles(tmp_path, monkeypatch):
    from tools import analyze_text_slot_prefix_redesign as research

    path = ROOT / "tests/samples/text/text_slotstyle_a8_char4_navy.txt"
    renamed = tmp_path / "geometry_wrong_count_wrong_text.txt"
    renamed.write_bytes(path.read_bytes())
    raw = hex_text_to_bytes(path.read_text(encoding="utf-8"))
    before, _ = parse_type3_clipboard_bytes_with_parser(raw)
    monkeypatch.setattr(research, "load_labels", lambda *_: pytest.fail("runtime oracle access"))
    after, _ = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(renamed.read_text(encoding="utf-8")))
    assert ordered(asdict(before)) == ordered(asdict(after))
