"""Test-only historical v1 replay; never imported by production code.

The old extractor is checked against the canonical pre-migration source hash.
Legacy raw hashes remain provenance; runtime replay still checks historical behavior.
Historical analyzer CLI tests run in a temporary copy with explicitly frozen source files
restored. No baseline, analyzer, capture or current runtime file is overwritten.
"""

from contextlib import contextmanager
from functools import cache
import json
from pathlib import Path
import shutil
import tempfile

import pytest

from tests import frozen_text_slot_candidate_v1 as legacy
from tests.source_integrity import canonical_source_sha256, source_baseline
from type3_clipboard_codec.parsers import type3_chain_parser
from type3_clipboard_codec.parsers import text as text_package

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("src/type3_clipboard_codec/parsers/text/text_slot_candidate.py")
_TEMP = None


@cache
def historical_root():
    global _TEMP
    old = Path(legacy.__file__)
    baseline = json.loads((ROOT / "tests/samples/reports/text/text_slot_family_shadow_baseline.json").read_text())
    assert canonical_source_sha256(old) == source_baseline("family")[SOURCE.as_posix()]["canonical_source_sha256"]
    _TEMP = tempfile.TemporaryDirectory(prefix="text-slot-v1-replay-")
    root = Path(_TEMP.name)
    # Replay the recorded corpus, not captures added after v1 evidence froze.
    # In particular, new spacing/maximum-length controls belong to later studies.
    recorded = set(baseline["fixtures"])

    def historical_inputs(directory, names):
        ignored = {name for name in names if name == "__pycache__"}
        if Path(directory) == ROOT / "tests/samples/text":
            ignored.update(name for name in names if name.endswith(".txt") and name not in recorded)
        return ignored

    for folder in ("src", "tools", "tests/samples"):
        shutil.copytree(ROOT / folder, root / folder, ignore=historical_inputs)
    for name in ("__init__.py", "source_integrity.py", "source_integrity_baselines.json"):
        shutil.copyfile(ROOT / "tests" / name, root / "tests" / name)
    # Restore every explicitly frozen historical source in the isolated copy.
    # The production checkout (including the progress guard) is never replaced.
    for path, record in source_baseline("family").items():
        snapshot = record.get("frozen_snapshot_path")
        if snapshot:
            source = ROOT / snapshot
            assert canonical_source_sha256(source) == record["canonical_source_sha256"]
            shutil.copyfile(source, root / path)
    return root


@contextmanager
def replay_parser():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(type3_chain_parser, "extract_text_slot_candidate", legacy.extract_text_slot_candidate)
        patch.setattr(text_package, "text_slot_candidate", legacy)
        yield
