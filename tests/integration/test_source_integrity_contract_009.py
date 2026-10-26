"""Historical replay and current production are distinct, closed source contracts."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest
from tests.source_integrity import BASELINES, source_baseline, source_integrity, canonical_source_sha256
from tests.text_slot_v1_replay import historical_root

ROOT = Path(__file__).resolve().parents[2]
CONTOUR = "src/type3_clipboard_codec/parsers/geometry/contour_parser.py"
TEXT = "src/type3_clipboard_codec/parsers/text/text_slot_candidate.py"


def populate(root, group):
    for path, record in source_baseline(group).items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / record.get("frozen_snapshot_path", path), target)


def test_current_contract_covers_historical_surface_with_only_reviewed_overrides():
    historical = source_baseline("family")
    current = source_baseline("current_production")
    assert set(historical) == set(current)
    assert {p for p in current if current[p] != historical[p]} == {CONTOUR, TEXT}
    assert source_integrity(ROOT, "current_production")["canonical_source_equal"]
    assert historical[CONTOUR]["canonical_source_sha256"] == "1882f894b333f6f3a005b4d0713d29bd0215ec5c9316e4b64f61d68ea61b65a4"
    assert current[CONTOUR]["canonical_source_sha256"] == "a09b0e44f9a1e1066602e6fd451a5458e04c8c33c71570c0803cfe5b24061054"
    assert hashlib.sha256((ROOT / CONTOUR).read_bytes()).hexdigest() == "94643e5c509ca469b453f2918ec4e31517bfa68157ac3646147f3e4bca492c87"


@pytest.mark.parametrize("group", ["family", "current_production"])
@pytest.mark.parametrize("path", [CONTOUR, "src/type3_clipboard_codec/adapters/win32_clipboard.py"])
def test_mutation_detected_in_each_explicit_contract(tmp_path, group, path):
    populate(tmp_path, group)
    assert source_integrity(tmp_path, group)["canonical_source_equal"]
    source = tmp_path / path
    source.write_bytes(source.read_bytes() + b"\n# unauthorized text change\n")
    result = source_integrity(tmp_path, group)
    assert not result["canonical_source_equal"]
    assert result["canonical_source_mismatches"] == [path]


@pytest.mark.parametrize("group,other", [("family", "current_production"), ("current_production", "family")])
def test_contract_does_not_accept_other_contour_version(tmp_path, group, other):
    populate(tmp_path, group)
    record = source_baseline(other)[CONTOUR]
    shutil.copyfile(ROOT / record.get("frozen_snapshot_path", CONTOUR), tmp_path / CONTOUR)
    result = source_integrity(tmp_path, group)
    assert not result["canonical_source_equal"]
    assert result["canonical_source_mismatches"] == [CONTOUR]


def test_historical_replay_restores_frozen_contour_without_touching_production():
    before = (ROOT / CONTOUR).read_bytes()
    replay = historical_root()
    assert replay != ROOT
    assert source_integrity(replay, "family")["canonical_source_equal"]
    assert canonical_source_sha256(replay / CONTOUR) == source_baseline("family")[CONTOUR]["canonical_source_sha256"]
    assert (ROOT / CONTOUR).read_bytes() == before


def test_existing_historical_record_values_are_preserved():
    before = json.loads((ROOT / "research/source-integrity-contract-009/historical-records-before.json").read_text(encoding="utf-8"))
    after = json.loads(BASELINES.read_text(encoding="utf-8"))
    for key, record in before["records"].items():
        assert {k: after["records"][key][k] for k in record} == record
    for key, group in before["groups"].items():
        assert after["groups"][key] == group
