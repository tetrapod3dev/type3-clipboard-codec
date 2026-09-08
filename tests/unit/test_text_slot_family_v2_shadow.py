"""Frozen F4 shadow contracts; no runtime replacement."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def shadow():
    path = Path(__file__).resolve().parents[2] / "tools/analyze_text_slot_family_shadow.py"
    spec = importlib.util.spec_from_file_location("shadow_unit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("flag", [0, 1])
def test_positive_and_suffix_deduplication(shadow, flag):
    payload = shadow.make_run(flag=flag)
    assert shadow.probe(payload, 32) == "match"
    result = shadow.evaluate_v2([payload])
    assert result["selected"] == dict(payload_index=0, positions=[32, 236, 440], plus08=flag)
    assert result["accounting"]["deduplicated_runs"] == 1
    assert result["accounting"]["suffix_starts_removed"] == 2
    assert result["count_result"]["valid"] and result["terminal_result"]["valid"]


@pytest.mark.parametrize("offset", [0, 1, 2, 3, 8, 9, 10, 11, *range(36, 44), *range(56, 64)])
def test_every_required_identity_byte(shadow, offset):
    payload = bytearray(shadow.make_run())
    for p in (32, 236, 440):
        payload[p + offset] ^= 0x55
        assert shadow.probe(payload, p) != "match"
    result = shadow.evaluate_v2([bytes(payload)])
    assert result["selected"] is None
    assert result["failing_layer"] == "identity"


def test_unconstrained_bytes_do_not_change_identity(shadow):
    payload = bytearray(shadow.make_run())
    required = set(range(4)) | set(range(8, 12)) | set(range(36, 44)) | set(range(56, 64))
    for offset in set(range(64)) - required:
        payload[32 + offset] ^= 0x55
    assert shadow.probe(payload, 32) == "match"


def test_plus08_switch(shadow):
    payload = bytearray(shadow.make_run())
    payload[236 + 8] = 1
    result = shadow.evaluate_v2([bytes(payload)])
    assert result["reason"] == "within_run_plus08_switch"
    assert result["selected"] is None


@pytest.mark.parametrize("flag", [2, 255])
def test_unknown_plus08(shadow, flag):
    result = shadow.evaluate_v2([shadow.make_run(flag=flag)])
    assert result["reason"] == "unknown_plus08"
    assert result["selected"] is None


def test_broken_recurrence_and_competing_runs(shadow):
    payload = shadow.make_run()
    shifted = payload[:236] + b"\xcc" + payload[236:]
    assert shadow.evaluate_v2([shifted])["status"] == "ambiguous"
    assert shadow.evaluate_v2([payload, payload])["status"] == "ambiguous"
    # Two runs within one structural payload also compete.
    assert shadow.evaluate_v2([payload + payload])["status"] == "ambiguous"


@pytest.mark.parametrize("bad_layer", ["count", "terminal"])
def test_identity_clones_and_policy_a_precede_validation(shadow, bad_layer):
    valid = shadow.make_run()
    clone = bytearray(valid)
    if bad_layer == "count":
        clone[28:32] = b"\0" * 4
    else:
        clone[444:448] = b"A\0\0\0"
    result = shadow.evaluate_v2([bytes(clone)])
    assert result["accounting"]["identity_matches"] == 3
    assert result["accounting"]["maximal_recurring_runs"] == 1
    assert result["failing_layer"] == bad_layer
    assert result["selected"] is None
    competing = shadow.evaluate_v2([valid, bytes(clone)])
    assert competing["status"] == "ambiguous"
    assert competing["count_result"] is None
    assert competing["terminal_result"] is None


@pytest.mark.parametrize("offset", [36, 56])
@pytest.mark.parametrize("width", [1, 8])
def test_constant_mutations_fail_closed(shadow, offset, width):
    payload = bytearray(shadow.make_run())
    for p in (32, 236, 440):
        for i in range(width):
            payload[p + offset + i] ^= 0x55
    result = shadow.evaluate_v2([bytes(payload)])
    assert result["accounting"]["identity_matches"] == 0
    assert result["failing_layer"] == "identity"
    assert result["selected"] is None


@pytest.mark.parametrize("remaining", [63, 64, 82, 91, 92])
def test_identity_and_rgb_bounds_separate(shadow, remaining):
    payload = shadow.make_run(count=1)[:32 + remaining]
    assert shadow.probe(payload, 32) == ("incomplete" if remaining == 63 else "match")
    result = shadow.evaluate_v2([payload])
    assert result["status"] == "bounds"
    assert result["selected"] is None
    if 64 <= remaining < 92:
        assert result["reason"] == "incomplete_rgb_or_raw_span"


@pytest.mark.parametrize("remaining", [0, 31, 32, 63, 64])
def test_next_probe_never_treats_incomplete_as_absent(shadow, remaining):
    result = shadow.evaluate_v2([shadow.make_run(next_bytes=remaining)])
    if remaining == 64:
        assert result["status"] == "present"
    else:
        assert result["reason"] == "incomplete_next_prefix"
        assert result["terminal_result"] is None
        assert result["selected"] is None


@pytest.mark.parametrize("tail", [b"\x05", b"\x05\0", b"\x05\0\0", b"\x05\0\0\0"])
def test_truncated_payload_scan(shadow, tail):
    result = shadow.evaluate_v2([shadow.make_run() + tail])
    assert result["status"] == "bounds"
    assert result["selected"] is None


def test_resource_caps_and_probe_budget(shadow, monkeypatch):
    for buffers in ([b""] * 33, [b"\xcc" * 1_048_577],
                    [shadow.TOKEN * 4097 + b"\xcc" * 64], [shadow.make_run(count=257)]):
        result = shadow.evaluate_v2(buffers)
        assert result["status"] == "resource"
        assert result["selected"] is None
    assert shadow.probe_budget(123) == 2 * 123 + 4096
    # Fault injection exercises the guard; it does not introduce a study cap.
    monkeypatch.setattr(shadow, "probe_budget", lambda _: 3)
    assert shadow.evaluate_v2([shadow.make_run()])["reason"] == "probe_cap"
