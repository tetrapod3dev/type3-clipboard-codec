"""Runtime v2 acceptance: Gate 8, exact identity, later layers and budgets."""

from itertools import product

import pytest

from tests.unit.test_text_slot_candidate import make_run
from type3_clipboard_codec.parsers.text import text_slot_candidate as runtime


def evaluate(*buffers):
    return runtime._evaluate(bytes(b) for b in buffers)


def unsupported(kind, variant=0):
    data = make_run(variant=variant)
    offset, value = {"unknown_plus08": (8, 2), "unknown_structural_constant": (36, 85),
                     "unknown_core": (9, 1)}[kind]
    for p in (40, 244, 448):
        data[p + offset] = value
        assert runtime._family(data, p) == kind
    return data


@pytest.mark.parametrize("kind", ["unknown_plus08", "unknown_structural_constant", "unknown_core"])
@pytest.mark.parametrize("placement", ["same_after", "same_before", "payload_after", "payload_before",
                                      "first", "interior", "last", "next"])
@pytest.mark.parametrize("variant", [0, 2])
def test_global_unknown_veto(kind, placement, variant):
    good = make_run(variant=variant)
    bad = unsupported(kind, variant)
    if placement == "same_after":
        inputs = [good + bad]
    elif placement == "same_before":
        inputs = [bad + good]
    elif placement == "payload_after":
        inputs = [good, bad]
    elif placement == "payload_before":
        inputs = [bad, good]
    else:
        p = {"first": 40, "interior": 244, "last": 448, "next": 652}[placement]
        good[p:p + 64] = bad[40:104]
        inputs = [good]
    candidate, audit = evaluate(*inputs)
    assert candidate is None
    assert audit["failing_layer"] == "identity" and audit["reason"] == kind
    assert audit["unsupported_contexts"] == 1  # Early global failure, no partial result.
    assert not audit["scan_complete"]
    assert runtime.extract_text_slot_candidate(bytes(b) for b in inputs) is None


@pytest.mark.parametrize("a,r,c", list(product([False, True], repeat=3)))
def test_exact_rejection_only_truth_table(a, r, c):
    data = make_run()
    data[48] = 0 if a else 2
    data[49] = 0 if r else 1
    data[76] = 0 if c else 85
    expected = ("F4" if a and r and c else "unknown_plus08" if r and c else
                "unknown_structural_constant" if a and r else "unknown_core" if c else None)
    assert runtime._family(data, 40) == expected


@pytest.mark.parametrize("offset", [0, 1, 2, 3, 8, 9, 10, 11, *range(36, 44), *range(56, 64)])
def test_each_required_f4_byte(offset):
    data = make_run()
    data[40 + offset] ^= 85
    assert runtime._family(data, 40) != "F4"
    assert evaluate(data)[0] is None


@pytest.mark.parametrize("offset", [*range(4, 8), *range(12, 36), *range(44, 56)])
def test_excluded_style_and_code_bytes_are_not_identity(offset):
    data = make_run()
    data[40 + offset] ^= 85
    assert runtime._family(data, 40) == "F4"
    assert evaluate(data)[0] is not None


@pytest.mark.parametrize("variant", [0, 2])
@pytest.mark.parametrize("ordinal", [0, 1, 2])
def test_both_directions_of_plus08_switch(variant, ordinal):
    data = make_run(variant=variant)
    data[40 + ordinal * 204 + 8] ^= 1
    candidate, audit = evaluate(data)
    assert candidate is None and audit["reason"] == "plus08_switch"


@pytest.mark.parametrize("offset", [36, 56])
@pytest.mark.parametrize("indices", [(0,), (3,), (7,), (0, 3, 7)])
@pytest.mark.parametrize("mixed", [False, True])
def test_each_constant_mutation_and_valid_companion(offset, indices, mixed):
    bad = make_run()
    for p in (40, 244, 448):
        for i in indices:
            bad[p + offset + i] ^= 85
    inputs = [make_run(variant=2), bad] if mixed else [bad]
    candidate, audit = evaluate(*inputs)
    assert candidate is None and audit["reason"] == "unknown_structural_constant"


@pytest.mark.parametrize("failure", ["count", "terminal", "none"])
def test_clones_and_count_terminal_cannot_rank(failure):
    clone = make_run()
    if failure == "count":
        clone[36:40] = b"\0" * 4
    elif failure == "terminal":
        clone[452:456] = b"A\0\0\0"
    candidate, audit = evaluate(clone)
    assert audit["identity_positions"] == 3 and audit["maximal_runs"] == 1
    assert audit["failing_layer"] == (None if failure == "none" else failure)
    assert (candidate is not None) == (failure == "none")
    for inputs in ([make_run(), clone], [clone, make_run()], [make_run() + clone]):
        candidate, audit = evaluate(*inputs)
        assert candidate is None and audit["reason"] == "multiple_runs"
        assert audit["globally_competing_runs"] == 2 and audit["traversed_slots"] == 0


def test_suffix_accounting_and_recurrence():
    candidate, audit = evaluate(make_run())
    assert candidate is not None
    assert {k: audit[k] for k in ("raw_token_hits", "identity_positions", "maximal_runs",
                                  "suffix_positions_removed", "unsupported_contexts")} == {
        "raw_token_hits": 3, "identity_positions": 3, "maximal_runs": 1,
        "suffix_positions_removed": 2, "unsupported_contexts": 0,
    }
    data = make_run()
    assert evaluate(data[:244] + b"\xcc" + data[244:])[1]["reason"] == "multiple_runs"


@pytest.mark.parametrize("remaining", [63, 64, 79, 80, 81, 82, 83, 91, 92])
def test_identity_rgb_and_raw_span_bounds(remaining):
    data = make_run(codes=(0,))[:40 + remaining]
    assert runtime._family(data, 40) == ("incomplete" if remaining < 64 else "F4")
    candidate, audit = evaluate(data)
    assert candidate is None and audit["failing_layer"] == "bounds"
    expected = ("incomplete_identity" if remaining < 64 else
                "incomplete_raw_rgb_span" if remaining < 92 else "incomplete_next_prefix")
    assert audit["reason"] == expected
    assert len(data[120:123]) == min(3, max(0, remaining - 80))
    assert runtime._family(data, -1) == "incomplete"


@pytest.mark.parametrize("remaining", [0, 1, 3, 4, 31, 32, 63, 64])
def test_next_prefix_bounds(remaining):
    data = make_run()[:652 + remaining]
    candidate, audit = evaluate(data)
    assert (candidate is not None) == (remaining == 64)
    assert audit["reason"] == (None if remaining == 64 else "incomplete_next_prefix")


@pytest.mark.parametrize("start", [4, 8, 15, 16])
def test_count_window_boundary(start):
    candidate, audit = evaluate(make_run(start=start))
    assert (candidate is not None) == (start == 16)
    if start < 16:
        assert audit["reason"] == "incomplete_count_window"


def test_real_cap_boundaries_and_explicit_probe_guard(monkeypatch):
    good = bytes(make_run())
    assert evaluate(*([b""] * 31 + [good]))[0] is not None
    assert evaluate(*([b""] * 32 + [good]))[1]["reason"] == "payload_cap"
    exact_bytes = good + b"\xcc" * (1_048_576 - len(good))
    assert evaluate(exact_bytes)[0] is not None
    assert evaluate(exact_bytes + b"\xcc")[1]["reason"] == "payload_cap"
    exact_hits = good + (runtime.TOKEN + b"\xcc" * 60) * 4093
    assert evaluate(exact_hits)[0] is not None
    assert evaluate(exact_hits + runtime.TOKEN + b"\xcc" * 60)[1]["reason"] == "token_cap"
    candidate, audit = evaluate(make_run(codes=(65,) * 255 + (0,)))
    # u8 cannot represent 256: reaching the slot cap does not waive count agreement.
    assert candidate is None and audit["traversed_slots"] == 256
    assert audit["failing_layer"] == "count"
    assert evaluate(make_run(codes=(65,) * 256 + (0,)))[1]["reason"] == "slot_cap"
    assert (runtime.MAX_PAYLOADS, runtime.MAX_PAYLOAD_BYTES, runtime.MAX_PREFIX_HITS, runtime.MAX_SLOTS,
            runtime.PROBE_FACTOR, runtime.PROBE_ALLOWANCE) == (32, 1_048_576, 4096, 256, 2, 4096)
    monkeypatch.setattr(runtime, "PROBE_FACTOR", 0)
    monkeypatch.setattr(runtime, "PROBE_ALLOWANCE", 4)
    assert evaluate(good)[0] is not None
    monkeypatch.setattr(runtime, "PROBE_ALLOWANCE", 3)
    assert evaluate(good)[1]["reason"] == "probe_cap"
    monkeypatch.setattr(runtime, "PROBE_ALLOWANCE", 2)
    assert evaluate(good)[1]["reason"] == "probe_cap"
