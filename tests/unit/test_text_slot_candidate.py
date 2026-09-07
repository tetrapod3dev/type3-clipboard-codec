import pytest

from type3_clipboard_codec.parsers.text import text_slot_candidate as module


def make_run(start=40, codes=(65, 66, 0), variant=0):
    data = bytearray(b'\xcc' * (start + len(codes) * 204 + 32))
    data[start - 4:start] = len(codes).to_bytes(4, 'little')
    vectors = [(0, '7B14AE47E17A84'), (0, 'B81E85EB51B89E'), (1, '7B14AE47E17A84')]
    flag, vector = vectors[variant]
    for i, code in enumerate(codes):
        p = start + i * 204
        data[p:p + 32] = (module.TOKEN + code.to_bytes(4, 'little') + bytes([flag])
                          + b'\0' * 3 + bytes.fromhex(vector) + b'\x3f' + module.TAIL)
        data[p + 80:p + 83] = b'\x10\x20\x30'
    return data


def extract(data):
    return module.extract_text_slot_candidate([bytes(data)])


@pytest.mark.parametrize('start', [16, 40, 177, 1100])
@pytest.mark.parametrize('variant', [0, 1, 2])
def test_valid_shifted_exact_variants(start, variant):
    candidate = extract(make_run(start, variant=variant))
    assert candidate['first_prefix_relative_offset'] == start
    assert candidate['prefix_variant'] == f'v{variant}'
    assert candidate['count_candidate']['validated_total_slot_count'] == 3
    assert candidate['parser_safe'] is False


@pytest.mark.parametrize('mutation', ['none', 'count', 'code', 'rgb'])
def test_competing_runs_never_resolved(mutation):
    data = make_run()
    other = make_run(1100)
    other[:len(data)] = data
    if mutation == 'count':
        other[1096:1100] = b'\0' * 4
    if mutation == 'code':
        other[1104:1108] = b'\xff' * 4
    if mutation == 'rgb':
        other[1180:1183] = b'\xff' * 3
    assert extract(other) is None


def test_global_uniqueness():
    assert module.extract_text_slot_candidate([bytes(make_run()), bytes(make_run())]) is None


@pytest.mark.parametrize('offset', [8, 12, 204 + 8])
def test_unknown_joint_or_mixed_unknown(offset):
    data = make_run()
    data[40 + offset] = 2
    assert extract(data) is None


def test_unobserved_combination():
    data = make_run(variant=1)
    data[48] = 1
    assert extract(data) is None


def test_weak_periodic_filler():
    data = make_run()
    for p in (40, 244, 448):
        data[p + 19] = 0
    assert extract(data) is None


@pytest.mark.parametrize('count', [0, 2, 4, 259, 65539])
def test_wrong_zero_conflicting_count(count):
    data = make_run()
    data[36:40] = count.to_bytes(4, 'little')
    assert extract(data) is None


def test_missing_count_bounds():
    assert extract(make_run(8)) is None


def test_internal_zero_continues():
    candidate = extract(make_run(codes=(65, 0, 0)))
    assert [s['terminal_candidate'] for s in candidate['slots']] == [False, False, True]


@pytest.mark.parametrize('code', [65, 256, 65536, 16777216])
def test_missing_four_byte_terminal(code):
    assert extract(make_run(codes=(65, code))) is None


@pytest.mark.parametrize('remaining', [0, 1, 31])
def test_incomplete_next_probe(remaining):
    data = make_run()
    assert extract(data[:40 + 3 * 204 + remaining]) is None


def test_unsupported_next_context():
    data = make_run()
    data[652:656] = module.TOKEN
    assert extract(data) is None


@pytest.mark.parametrize('limit,value', [('MAX_PAYLOADS', 0), ('MAX_PAYLOAD_BYTES', 100),
                                       ('MAX_PREFIX_HITS', 2), ('MAX_SLOTS', 2),
                                       ('PROBE_FACTOR', 0)])
def test_resource_exhaustion(monkeypatch, limit, value):
    monkeypatch.setattr(module, limit, value)
    if limit == 'PROBE_FACTOR':
        monkeypatch.setattr(module, 'PROBE_ALLOWANCE', 3)
    assert extract(make_run()) is None


def test_actual_resource_limits():
    assert module.extract_text_slot_candidate([b''] * 33) is None
    assert extract(b'x' * 1_048_577) is None
    assert extract(module.TOKEN * 4097 + b'x' * 32) is None
    assert extract(make_run(codes=(65,) * 256 + (0,))) is None


def test_raw_reconstruction_and_read_only():
    data = make_run()
    original = bytes(data)
    candidate = extract(data)
    assert bytes(data) == original
    assert candidate['count_candidate']['raw_window'] == original[24:40]
    for slot in candidate['slots']:
        span = slot['raw_span']
        raw = original[span['start']:span['start'] + span['length']]
        assert len(raw) == 92
        assert raw[4:8] == slot['slot_code_candidate']['raw_bytes']
        assert list(raw[80:83]) == slot['rgb_bytes_candidate']['raw_bytes']
        assert slot['ownership'] == 'unresolved' and slot['matched_chain'] is None
        assert slot['slot_code_candidate']['typed_width'] is None
        assert slot['rgb_bytes_candidate']['typed_width'] is None


@pytest.mark.parametrize('tail', [module.TOKEN, b'\x05', b'\x05\0', b'\x05\0\0'])
def test_partial_search_evidence(tail):
    assert extract(make_run() + tail) is None


def test_empty():
    assert module.extract_text_slot_candidate([]) is None

@pytest.mark.parametrize('limit,value', [('MAX_PAYLOADS', 1), ('MAX_PAYLOAD_BYTES', 684),
                                       ('MAX_PREFIX_HITS', 3), ('MAX_SLOTS', 3)])
def test_resource_limit_exact_boundary(monkeypatch, limit, value):
    monkeypatch.setattr(module, limit, value)
    assert extract(make_run()) is not None


def test_unknown_outside_selected_run():
    data = make_run()
    other = make_run(1100, variant=1)
    other[:len(data)] = data
    other[1108] = 1
    assert extract(other) is None


def test_known_variants_independently_checked():
    data = make_run()
    other = make_run(variant=2)
    data[244:276] = other[244:276]
    candidate = extract(data)
    assert [s['prefix_variant'] for s in candidate['slots']] == ['v0', 'v2', 'v0']


def test_truncated_local_color_context():
    assert extract(make_run()[:448 + 82]) is None


def test_weak_filler_elsewhere_does_not_compete():
    assert extract(make_run() + module.TOKEN + b'\xcc' * 40) is not None


def test_damaged_token_at_expected_continuation():
    data = make_run()
    data[652:656] = b'\x05\xff\0\0'
    assert extract(data) is None
