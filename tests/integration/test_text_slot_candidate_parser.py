from dataclasses import asdict
from pathlib import Path

import pytest

from tests.sample_utils import resolve_sample_path
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.codec.preview import PreviewRenderer
from type3_clipboard_codec.inspect.formatters import to_inspection_dict
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers import type3_chain_parser

# Independent fixture expectations, never imported into runtime selection.
EXPECTED = {
    'default_text': 8, 'text_ascii_lowercase': 8, 'text_ascii_uppercase': 8,
    'text_digits': 11, 'text_alphanumeric': 9, 'text_spaces': 9, 'text_special_characters': 10,
    'text_color_army_green': 8, 'text_color_navy_blue': 8, 'text_height_10mm': 8,
    'text_height_30mm': 8, 'text_font_arial': 8, 'text_font_arial_bold': 8,
    'text_group_same_color_two_objects': 8, 'text_group_mixed_color_two_objects': 8,
    'text_two_objects_same_color_not_grouped': 11, 'text_two_objects_mixed_color_not_grouped': 11,
    'text_three_objects_grouped_order_abc': 8,
    'text_three_objects_grouped_order_abc_content_variation': 6,
    'text_three_objects_not_grouped': 4, 'text_multiline_basic': 10,
    'text_spacing_fixed': 10, 'text_spacing_proportional': 10, 'text_spacing_print_proportional': 10,
}


def parse(name):
    data = hex_text_to_bytes(resolve_sample_path(name + '.txt').read_text(encoding='utf-8'))
    return parse_type3_clipboard_bytes_with_parser(data)


@pytest.mark.parametrize('name,count', EXPECTED.items())
def test_reviewed_fixture_candidates(name, count):
    obj, _ = parse(name)
    candidate = obj.candidate_fields['text_slot_run']
    assert len(candidate['slots']) == candidate['count_candidate']['validated_total_slot_count'] == count
    assert candidate['source'] == 'CParagraphe_slot_prefix_family_v1'
    assert candidate['confidence'] == 'provisional' and candidate['parser_safe'] is False
    assert candidate['ownership'] == 'unresolved' and candidate['matched_chain'] is None
    expected_variant = {'text_height_30mm': 'v1', 'text_group_mixed_color_two_objects': 'v2'}.get(name, 'v0')
    assert candidate['prefix_variant'] == expected_variant
    span = candidate['payload_span']
    payload = obj.raw_data[span['start']:span['start'] + span['length']]
    assert span['buffer'] == 'raw_data'
    descriptor = candidate['descriptor_relative_offset']
    assert obj.raw_data[descriptor + 6:descriptor + 17] == b'CParagraphe'
    first = candidate['first_prefix_relative_offset']
    assert candidate['count_candidate']['raw_window'] == payload[first - 16:first]
    assert candidate['count_candidate']['typed_width'] is None
    assert all(v['value'] == count for v in candidate['count_candidate']['numeric_views'].values())
    for slot in candidate['slots']:
        p = slot['raw_span']['start']
        assert slot['slot_code_candidate']['raw_bytes'] == payload[p + 4:p + 8]
        assert slot['rgb_bytes_candidate']['raw_bytes'] == list(payload[p + 80:p + 83])
        assert slot['raw_span']['length'] == 92
        assert len(payload[p:p + 92]) == 92
        assert slot['matched_chain'] is None and slot['ownership'] == 'unresolved'
    assert sum(s['terminal_candidate'] for s in candidate['slots']) == 1
    if name in {'text_multiline_basic', 'text_spacing_fixed', 'text_spacing_proportional',
                'text_spacing_print_proportional'}:
        assert 13 in [s['slot_code_candidate']['numeric_view'] for s in candidate['slots']]


ALL_TEXT = sorted(p.stem for p in (Path(__file__).parents[1] / 'samples/text').glob('*.txt'))


@pytest.mark.parametrize('name', ALL_TEXT + ['default_rectangle', 'two_rectangle_group'])
def test_exact_parser_and_presentation_equality(name, monkeypatch):
    after, parser_name = parse(name)
    if name in {'default_rectangle', 'two_rectangle_group'}:
        assert 'text_slot_run' not in after.candidate_fields
    preview = PreviewRenderer().render(after)
    inspected = to_inspection_dict(after, parser_name, 'regression')
    with monkeypatch.context() as patch:
        patch.setattr(type3_chain_parser, 'extract_text_slot_candidate', lambda _: None)
        before, old_parser = parse(name)
    assert parser_name == old_parser
    assert preview == PreviewRenderer().render(before)
    inspected['candidate_fields'].pop('text_slot_run', None)
    assert inspected == to_inspection_dict(before, old_parser, 'regression')
    after.candidate_fields.pop('text_slot_run', None)
    # No sorting, byte normalization, candidate filtering, or notes/warnings removal.
    assert asdict(after) == asdict(before)
    assert PreviewRenderer().render(after, verbose=True) == PreviewRenderer().render(before, verbose=True)
    if name in {'default_rectangle', 'two_rectangle_group'}:
        assert 'text_slot_run' not in before.candidate_fields


@pytest.mark.parametrize('name', ['text_mirror_on', 'text_slant_15deg', 'text_slant_custom_30deg',
                                  'text_width_150_percent', 'text_width_50_percent'])
def test_unsupported_fixture_omits_key(name):
    obj, _ = parse(name)
    assert 'text_slot_run' not in obj.candidate_fields
