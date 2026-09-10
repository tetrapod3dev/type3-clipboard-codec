"""Inventory-only checks: never decode captures or import binary analyzers."""
from decimal import Decimal
import hashlib
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CASES = [["50","74.50","below","below","Sample clearly below the exact natural-length boundary but very near it.","d1a2a1989f91439964f92d70c3f2660ae825ca154000e1f0f1a2c515fe4e2c71"],["58","74.58","below","below","Sample immediately below the exact natural-length boundary.","0ed160771700001d8541fd928aaae2ddcdfcbac0093546bb680e9d2e43fb3046"],["60","74.60","above","below","Critical discriminator between a possible natural-length transition and a possible scalar/clamp transition; future hypotheses only.","9611d0940a6597383fea97cf610d0bfd1132df55df152ab9d2c4ebdabd23f57c"],["66","74.66","above","above","Probe immediately beyond the provisional scalar crossover without predicting a binary outcome.","4a757614a844b13be6725fefa83c27c6beded576d68896b25549deaac875d6de"]]
N = Decimal("74.58390177353341")
CROSSOVER = Decimal("74.65848567530693")


@pytest.mark.parametrize("suffix,value,natural,crossover,purpose,digest", CASES)
def test_boundary_inventory(suffix, value, natural, crossover, purpose, digest):
    stem = f"text_maxlength_a8_74p{suffix}mm"
    raw = ROOT / "tests/samples/text" / (stem + ".txt")
    intent = ROOT / "tests/samples/intents/text" / (stem + ".md")
    assert raw.is_file()
    # Hashing only: no hex decoding, window reads or binary interpretation.
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == digest
    text = intent.read_text(encoding="utf-8")
    block = re.search(r"```yaml\n(.*?)```", text, re.S).group(1)
    metadata = yaml.safe_load(block)["intent_metadata"]
    assert metadata["fixture"] == raw.name
    assert metadata["baseline_fixture"] == "text_slotstyle_a8_baseline.txt"
    assert metadata["property"] == "maximum_length"
    assert metadata["changed_scope"] == "text_object"
    assert f"changed_value_mm: {value}\n" in block
    assert Decimal(str(metadata["changed_value_mm"])) == Decimal(value)
    assert metadata["baseline_value_mm"] == 0
    assert metadata["baseline_natural_length_mm"] == 74.584
    assert metadata["exact_previous_serialized_natural_extent_mm"] == float(N)
    assert metadata["provisional_crossover_mm"] == float(CROSSOVER)
    assert metadata["relationship_to_exact_natural_extent"] == natural
    assert natural == ("below" if Decimal(value) < N else "above")
    assert metadata["relationship_to_provisional_crossover"] == crossover
    assert crossover == ("below" if Decimal(value) < CROSSOVER else "above")
    assert metadata["observed_ui_compression"] == "not_recorded"
    assert metadata["oracle_only"] is True
    assert metadata["analysis_status"] == "inventory_only"
    assert metadata["crossover_status"] == "post_discovery_hypothesis_only"
    assert "expected_value" not in block and "expected_scalar" not in block
    assert "expected_raw" not in block
    assert "Oracle isolation" in text and "must freeze before" in text
    assert metadata["visible_text"] == "AAAAAAAA" and metadata["font"] == "Arial"
    assert metadata["base_character_attributes"] == {
        "height_mm": 10, "width_percent": 100, "slant_degrees": 0,
        "rotation_degrees": 0, "color": "Army Green", "character_spacing_percent": 100,
    }
    assert metadata["one_intended_experimental_variable"] is True
    assert metadata["anchor_capture_setup_inherited_from_baseline"] is True
    for target in re.findall(r"\]\(([^)]+)\)", text):
        assert (intent.parent / target.split("#")[0]).resolve().is_file()


def test_boundary_documentation_links_and_hypotheses():
    plan = ROOT / "docs/text_spacing_maxlength_fixture_plan.md"
    section = plan.read_text(encoding="utf-8").split(
        "## Maximum-length boundary fixture inventory — analysis pending", 1
    )[1]
    for hypothesis in ("H-natural", "H-scalar", "H-other"):
        assert hypothesis in section
    assert "Oracle isolation" in section and "not_recorded" in section
    for target in re.findall(r"\]\(([^)]+)\)", section):
        assert (plan.parent / target.split("#")[0]).resolve().is_file()
    for name in ("text_reverse_engineering.md", "text_object_reverse_engineering.md"):
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        assert "text_spacing_maxlength_fixture_plan.md#maximum-length-boundary-fixture-inventory--analysis-pending" in text

