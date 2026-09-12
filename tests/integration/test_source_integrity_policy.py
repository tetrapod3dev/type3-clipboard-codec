"""Source-only canonical integrity; fixtures and runtime replay stay byte-exact."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from tests.source_integrity import (
    BASELINES,
    canonical_source_bytes,
    canonical_source_sha256,
    source_baseline,
    source_integrity,
)
from tests.text_slot_v1_replay import historical_root, replay_parser

ROOT = Path(__file__).resolve().parents[2]
DATA = json.loads(BASELINES.read_text(encoding="utf-8"))
APPROVED = "333d59bd32ee0aed8418edf806be9c9604e0e785"
ADAPTER = "src/type3_clipboard_codec/adapters/win32_clipboard.py"


@pytest.mark.parametrize("raw", [b"a\nb\nc\n", b"a\r\nb\r\nc\r\n", b"a\r\nb\nc\r\n"])
def test_lf_crlf_mixed_source_equivalence(tmp_path, raw):
    source = tmp_path / "source.py"
    source.write_bytes(raw)
    assert canonical_source_bytes(raw) == b"a\nb\nc\n"
    assert canonical_source_sha256(source) == hashlib.sha256(b"a\nb\nc\n").hexdigest()


@pytest.mark.parametrize("raw", [
    b"a \n", b"a\t\n", b"a", b"a\r", b"a\r\r\n",
    b"\xef\xbb\xbfa\n", b"a\n\n", "a\u0301\n".encode(), b"\xff\n",
])
def test_no_other_byte_normalization(raw):
    # Each expected distinction survives; only CRLF pairs may be replaced.
    assert canonical_source_bytes(raw) != b"a\n"
    assert canonical_source_bytes(raw) == raw.replace(b"\r\n", b"\n")


@pytest.mark.parametrize("suffix", [".txt", ".bin", ".dll", ".json"])
def test_fixture_and_binary_paths_rejected(tmp_path, suffix):
    artifact = tmp_path / ("artifact" + suffix)
    artifact.write_bytes(b"a\r\n")
    with pytest.raises(ValueError, match="only Python"):
        canonical_source_sha256(artifact)
    assert artifact.read_bytes() == b"a\r\n"


@pytest.mark.parametrize("key", list(DATA["records"]))
def test_every_committed_source_baseline_matches_checkout(key):
    record = DATA["records"][key]
    path = ROOT / record.get("frozen_snapshot_path", record["path"])
    assert canonical_source_sha256(path) == record["canonical_source_sha256"]
    assert len(record["baseline_commit_or_snapshot"]) == 40
    assert len(record["legacy_raw_sha256"]) == 64


def test_historical_raw_provenance_is_retained():
    old = json.loads((ROOT / "tests/samples/reports/text/text_slot_family_shadow_baseline.json").read_text())
    historical = source_baseline("family")
    assert {p: r["legacy_raw_sha256"] for p, r in historical.items()} == old["source_sha256"]
    assert historical[ADAPTER]["legacy_raw_status"] == "raw_preimage_unresolved"
    for path in ("src/type3_clipboard_codec/parsers/type3_chain_parser.py",
                 "src/type3_clipboard_codec/models/__init__.py"):
        assert historical[path]["legacy_raw_status"] == "mixed_line_endings_reconstructed"
    approved = source_baseline("approved_analyzers")
    assert len(approved) == 2
    for record in approved.values():
        assert record["baseline_commit_or_snapshot"] == APPROVED
        assert record["legacy_raw_status"] == "superseded_by_approved_source_change"


def test_adapter_text_mutation_fails_integrity(tmp_path):
    # No real source is edited. Populate source-only diagnostic copies.
    for path, record in source_baseline("family").items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / record.get("frozen_snapshot_path", path)).read_bytes())
    assert source_integrity(tmp_path, "family")["canonical_source_equal"]
    adapter = tmp_path / ADAPTER
    adapter.write_bytes(adapter.read_bytes() + b"\n# changed source text\n")
    result = source_integrity(tmp_path, "family")
    assert not result["canonical_source_equal"]
    assert result["canonical_source_mismatches"] == [ADAPTER]


def test_fixture_raw_hash_is_still_byte_exact(tmp_path):
    name = "text_slotstyle_a8_baseline.txt"
    golden = json.loads((ROOT / "tests/samples/reports/text/text_slot_style_runtime_baseline.json").read_text())
    expected = golden["fixtures"][name]["fixture_file_sha256"]
    raw = (ROOT / "tests/samples/text" / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    # Even a newline-only artifact mutation remains a raw integrity failure.
    changed = raw + b"\r\n"
    assert hashlib.sha256(changed).hexdigest() != expected
    copy = tmp_path / name
    copy.write_bytes(changed)
    with pytest.raises(ValueError):
        canonical_source_sha256(copy)


@pytest.fixture(scope="module")
def shadow():
    path = historical_root() / "tools/analyze_text_slot_family_shadow.py"
    spec = importlib.util.spec_from_file_location("canonical_policy_shadow", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_historical_replay_and_legacy_information(shadow):
    with replay_parser():
        report = shadow.build_report()
    corpus = report["corpus_summary"]
    assert corpus["real_fixtures"] == 104 and corpus["runtime_outputs_equal"]
    assert corpus["canonical_source_equal"] and corpus["runtime_source_equal"]
    assert corpus["legacy_raw_source_equal"] is False
    assert corpus["source_provenance_information"] == ["Legacy raw snapshot byte representation differs"]
    assert report["warnings"] == []
    assert report["answers"]["runtime_v2_promotion_review_readiness"] == "ready_for_review"


def test_canonical_mismatch_still_blocks_readiness(shadow, monkeypatch):
    original = shadow.source_integrity

    def mismatching(root, group):
        result = original(root, group)
        result["canonical_source_equal"] = False
        result["canonical_source_mismatches"] = [ADAPTER]
        return result

    monkeypatch.setattr(shadow, "source_integrity", mismatching)
    with replay_parser():
        report = shadow.build_report()
    assert not report["corpus_summary"]["canonical_source_equal"]
    assert "Canonical runtime source disagreement" in report["warnings"]
    assert report["answers"]["runtime_v2_promotion_review_readiness"] == "not_ready"
