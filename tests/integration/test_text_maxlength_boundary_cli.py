"""Frozen-window boundary checks; no differential analyzer invocation."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools/analyze_text_maximum_length.py"
CASES = [
    ("50", "d1a2a1989f91439964f92d70c3f2660ae825ca154000e1f0f1a2c515fe4e2c71",
     "df4f8d976e12b33f", "304623b297eeef3f", .0745, .9978750685933786,
     .031165000000000005, .10566500000000001, .07450000000000001, 74.50000000000001),
    ("58", "0ed160771700001d8541fd928aaae2ddcdfcbac0093546bb680e9d2e43fb3046",
     "b988efc4ac17b33f", "ba27492361f7ef3f", .07458, .9989476861166999,
     .031125000000000007, .105705, .07457999999999998, 74.57999999999998),
    ("60", "9611d0940a6597383fea97cf610d0bfd1132df55df152ab9d2c4ebdabd23f57c",
     "f0164850fc18b33f", "000000000000f03f", .0746, 1.,
     .031115000000000004, .105715, .0746, 74.6),
    ("66", "4a757614a844b13be6725fefa83c27c6beded576d68896b25549deaac875d6de",
     "94c151f2ea1cb33f", "000000000000f03f", .07466, 1.,
     .031085, .105745, .07466, 74.66000000000001),
]


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("boundary_test_analyzer", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(analyzer):
    return analyzer.build_boundary_report()


@pytest.mark.parametrize("case", CASES)
def test_exact_inventory_alignment_and_extent(case, analyzer, report):
    suffix, digest, setting, scalar, meters, value, xmin, xmax, extent_m, extent_mm = case
    path = analyzer.research.TEXT / f"text_maxlength_a8_74p{suffix}mm.txt"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    row = report["structural"]["rows"][digest]
    assert row["alignment"] == "aligned"
    assert row["run"]["start"] == 310 and row["run"]["count"] == 9
    assert row["runtime"]["candidate_present"]
    assert row["runtime"]["source"] == "CParagraphe_slot_prefix_family_v2"
    assert row["runtime"]["prefix_family"] == "F4" and row["runtime"]["plus08_value"] == 0
    assert row["f4_unchanged"]
    assert row["f4"]["plus24"] == ["0000000000000000"] * 9
    assert row["f4"]["plus38"] == ["9a9999999999d9bf"] * 9
    assert row["duplicate_byte_identity"] and row["duplicate_numeric_identity"]
    for name, expected_raw, expected_value in (
        ("object_setting", setting, meters), ("scalar_a", scalar, value), ("scalar_b", scalar, value)
    ):
        window = row["windows"][name]
        assert window["raw_hex"] == expected_raw
        f = window["f64le"]
        assert f["value"] == float(f["repr"]) == float.fromhex(f["hex"]) == expected_value
        assert struct.pack("<d", f["value"]).hex() == expected_raw
    extent = row["extent"]
    assert extent["xmin_m"]["f64le"]["value"] == xmin
    assert extent["xmax_m"]["f64le"]["value"] == xmax
    assert extent["extent_m"]["value"] == xmax-xmin == extent_m
    assert extent["extent_mm"]["value"] == extent_m*1000 == extent_mm
    for name, coordinate in (("xmin_m", xmin), ("xmax_m", xmax)):
        assert struct.unpack("<d", bytes.fromhex(extent[name]["raw_hex"]))[0] == coordinate
    assert extent["provenance"]["xmin_absolute_range"] == [81, 89]
    assert extent["provenance"]["xmax_absolute_range"] == [105, 113]
    oracle = report["oracle_summary"]["cases"][path.name]
    assert oracle["requested_setting"]["absolute_residual"] == 0
    assert oracle["requested_setting"]["ulp_distance"] == 0


def test_hypotheses_residuals_and_discriminators(analyzer, report):
    assert analyzer.boundary_hypotheses(50, 100) == dict(H1=.5, H2=.499, H3=.5, H4=.499)
    assert analyzer.boundary_hypotheses(200, 100) == dict(H1=2., H2=1.999, H3=1., H4=1.)
    oracle = report["oracle_summary"]
    expected = {
        "50": [0.0010000000000000009, 0., 0.0010000000000000009, 0.],
        "58": [0.001000000000000445, 4.440892098500626e-16,
               0.001000000000000445, 4.440892098500626e-16],
        "60": [0.0002158404975307615, 0.0007841595024692394, 0., 0.0007841595024692394],
        "66": [0.0010203036400220356, 2.0303640022145686e-05, 0., 0.],
    }
    for suffix, residuals in expected.items():
        case = oracle["cases"][f"text_maxlength_a8_74p{suffix}mm.txt"]
        for i, h in enumerate(("H1", "H2", "H3", "H4")):
            r = case["hypotheses"][h]
            assert r["absolute_residual"] == residuals[i]
            assert r["relative_residual"] == residuals[i]/abs(case["observed_scalar"])
    assert oracle["cases"]["text_maxlength_a8_74p58mm.txt"]["hypotheses"]["H2"]["ulp_distance"] == 4
    assert oracle["discriminator_74p60"] == oracle["discriminator_74p66"] == "exactly_one"
    assert oracle["below_boundary_continuity"] == "below_boundary_formula_continuity_supported"
    assert oracle["boundary_model_status"] == "natural_threshold_supported"
    assert oracle["compression_formula_status"] == "formula_breaks_near_boundary"
    assert all(not r["within_4_ulp_all"] for r in oracle["whole_boundary_clamp_comparison"].values())
    assert [r["requested_mm"] for r in oracle["ordered_positive_scalars"]] == [40, 60, 74.5, 74.58, 74.6, 74.66, 100]
    assert oracle["baseline_separate"]["mode"] == "default_natural_mode_scalar_candidate"


def test_no_oracle_or_new_discovery(analyzer, monkeypatch, report):
    for name in ("numeric_windows", "structural_phase", "delta", "merged_ranges"):
        monkeypatch.setattr(analyzer, name, lambda *a, **k: pytest.fail("new differential/discovery"))
    monkeypatch.setattr(analyzer, "load_intent", lambda *a: pytest.fail("intent before freeze"))
    absent = analyzer.build_boundary_report(oracle_enabled=False)
    assert absent["structural"] == report["structural"]
    assert absent["structural_sha256"] == report["structural_sha256"]


@pytest.mark.parametrize("field,value", [
    ("changed_value_mm", 1),
    ("relationship_to_exact_natural_extent", "wrong"),
    ("relationship_to_provisional_crossover", "wrong"),
    ("exact_previous_serialized_natural_extent_mm", 999),
    ("baseline_natural_length_mm", 999),
    ("provisional_crossover_mm", 999),
])
def test_adversarial_labels(analyzer, monkeypatch, report, field, value):
    original = analyzer.load_intent
    def altered(name):
        meta = copy.deepcopy(original(name))
        meta[field] = value
        return meta
    monkeypatch.setattr(analyzer, "load_intent", altered)
    modified = analyzer.build_boundary_report()
    assert modified["structural"] == report["structural"]
    assert modified["structural_sha256"] == report["structural_sha256"]
    if field != "changed_value_mm":
        assert modified["oracle_summary"]["natural_mm"] == report["oracle_summary"]["natural_mm"]
        for name, case in modified["oracle_summary"]["cases"].items():
            assert case["hypotheses"] == report["oracle_summary"]["cases"][name]["hypotheses"]


def test_renamed_and_reordered(analyzer, tmp_path, report):
    paths = []
    for index, name in enumerate((analyzer.FIXTURES[0], *analyzer.BOUNDARY_FIXTURES)):
        path = tmp_path / f"opaque_{index}.txt"
        path.write_bytes((analyzer.research.TEXT / name).read_bytes())
        paths.append(path)
    assert analyzer.build_boundary_report(paths[::-1]) == report


def test_freeze_precedes_labels(analyzer, monkeypatch, report):
    original = analyzer.boundary_oracle
    def check(frozen, enabled):
        assert json.loads(frozen) == report["structural"]
        with monkeypatch.context() as m:
            m.setattr(analyzer.research, "read_capture", lambda *a: pytest.fail("decode after freeze"))
            return original(frozen, enabled)
    monkeypatch.setattr(analyzer, "boundary_oracle", check)
    assert analyzer.build_boundary_report() == report


@pytest.mark.parametrize("failure", ["alignment", "f4"])
def test_unresolved_stops_interpretation(analyzer, monkeypatch, report, failure):
    original = analyzer.research.read_capture
    def broken(path):
        data = original(path)
        if path.name == analyzer.BOUNDARY_FIXTURES[0]:
            if failure == "alignment":
                data["selected"] = None
            else:
                node = data["paragraphs"][data["selected"]["paragraph_index"]]
                payload = bytearray(node.payload)
                payload[data["selected"]["start"]+36] ^= 1
                node.payload = bytes(payload)
        return data
    monkeypatch.setattr(analyzer.research, "read_capture", broken)
    result = analyzer.build_boundary_report()
    assert analyzer.BOUNDARY_FIXTURES[0] not in result["oracle_summary"]["cases"]
    assert result["oracle_summary"]["boundary_model_status"] == "unresolved"


@pytest.mark.parametrize("flags", [[], ["--json"], ["--json", "--no-oracle"]])
def test_cli_bounds(flags):
    proc = subprocess.run([sys.executable, str(CLI), "--boundary", *flags],
                          cwd=ROOT, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()
    assert len(proc.stdout) < (100000 if "--json" in flags else 50000)
    assert json.loads(proc.stdout)["mode"] == "boundary"


def test_runtime_preserved_and_policy(report):
    for path, expected in (
        ("src/type3_clipboard_codec/parsers/text/text_slot_candidate.py",
         "31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876"),
        ("src/type3_clipboard_codec/parsers/type3_chain_parser.py",
         "9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb"),
    ):
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected
    assert report["policy"]["semantic_formula_readiness"] == "provisional_not_ready"
    assert report["policy"]["typed_width"] is None
    assert report["policy"]["parser_safe"] is False

