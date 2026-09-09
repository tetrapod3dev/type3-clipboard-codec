"""Maximum-length evidence, oracle independence and unchanged runtime regression."""
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
CLI = ROOT / 'tools/analyze_text_maximum_length.py'
NAMES = ('text_slotstyle_a8_baseline.txt', 'text_maxlength_a8_100mm.txt',
         'text_maxlength_a8_60mm.txt', 'text_maxlength_a8_40mm.txt', 'text_maxlength_a8_m60mm.txt')
HASHES = ('994c115e0dab58c605747420e7ba1e67961835ed4ef17aae0951bf899a406392',
          '1f24a7b2042dca993977690fa295aa7295593572103cb04523cc06ac1bd89046',
          'b8281f358591493b1dadf609c18ab788d8d73c1ae5f222045dbdb3a9033b25b6',
          '44b998a2e69cd08618936da6a5250a11bf223b7d0f89f3aef3deb1bb9ab6d49a',
          'e9bb3439205bab970b73b1b6fc70d2814d77e0d088cb577ed6d37802b4d27d85')
STRUCTURAL_KEYS = ('fixture_inventory', 'runtime_candidate_summary', 'structural_alignment_summary',
                   'node_level_differentials', 'cparagraphe_region_differentials', 'slot_field_audit',
                   'numeric_candidate_summary', 'f4_summary', 'geometry_summary')


@pytest.fixture(scope='module')
def analyzer():
    spec = importlib.util.spec_from_file_location('maximum_length_research_test', CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def report(analyzer):
    return analyzer.build_report()


def structural(report):
    return {k: report[k] for k in STRUCTURAL_KEYS}


def test_inventory_hashes_and_runtime(analyzer, report):
    assert analyzer.FIXTURES == NAMES
    assert [r['fixture'] for r in report['fixture_inventory']] == list(NAMES)
    assert tuple(r['file_sha256'] for r in report['fixture_inventory']) == HASHES
    for name, expected in zip(NAMES, HASHES, strict=True):
        assert hashlib.sha256((analyzer.research.TEXT / name).read_bytes()).hexdigest() == expected
    for row in report['runtime_candidate_summary'].values():
        assert row['parse_success'] and row['candidate_present']
        assert row['source'] == 'CParagraphe_slot_prefix_family_v2'
        assert (row['prefix_family'], row['plus08_value'], row['first_prefix'], row['slot_count']) == ('F4', 0, 310, 9)
    assert report['answers']['fixtures_aligned'] == 5
    assert not report['warnings']


def test_complete_object_scope_and_matrix(report):
    required = {'f0:f1', 'f0:f2', 'f0:f3', 'f0:f4', 'f1:f2', 'f2:f3', 'f2:f4'}
    assert required <= report['node_level_differentials'].keys()
    assert len(report['node_level_differentials']) == 10
    for key, pair in report['node_level_differentials'].items():
        assert [n['class_name'] for n in pair['nodes']] == [
            'CZone', 'CParagraphe', 'CCourbe', 'CContour', 'CPropertyExtend']
        assert [n['payload']['lengths'][0] for n in pair['nodes']] == [98, 2530, 98, 170, 5006]
        assert pair['outside_nodes']
        para = report['cparagraphe_region_differentials'][key]
        assert para['starts'] == [310, 310] and para['stride'] == 204
        assert para['suffix_starts'] == [2146, 2146]
        assert para['suffix']['changed_bytes'] > 0
        assert len(para['slots']) == 9
        assert all(s['lengths'] == [204, 204] and s['changed_bytes'] == 0 for s in para['slots'])


def test_freeze_before_oracle(analyzer, monkeypatch):
    original = analyzer.oracle_phase
    def evaluate(frozen, enabled):
        assert isinstance(frozen, str)
        assert len(json.loads(frozen)['node_level_differentials']) == 10
        with monkeypatch.context() as m:
            m.setattr(analyzer.research, 'read_capture', lambda *a: pytest.fail('binary read after freeze'))
            m.setattr(analyzer, 'numeric_windows', lambda *a: pytest.fail('nomination after freeze'))
            return original(frozen, enabled)
    monkeypatch.setattr(analyzer, 'oracle_phase', evaluate)
    assert analyzer.build_report()['answers']['fixtures_aligned'] == 5


def test_no_oracle_equality(analyzer, monkeypatch, report):
    monkeypatch.setattr(analyzer, 'load_intent', lambda *a: pytest.fail('intent access'))
    result = analyzer.build_report(oracle_enabled=False)
    assert structural(result) == structural(report)
    assert result['oracle_summary']['structural_sha256'] == report['oracle_summary']['structural_sha256']
    assert result['answers']['object_setting_candidate_range'] is None


@pytest.mark.parametrize('field,value', [('baseline_natural_length_mm', 999), ('changed_value_mm', 314),
    ('expected_ui_relationship', 'fabricated'), ('observed_program_behavior', 'no reflection'),
    ('observed_program_behavior', ''), ('target_character_index_1based', 999)])
def test_wrong_oracle_does_not_select(analyzer, monkeypatch, report, field, value):
    original = analyzer.load_intent
    def altered(name):
        meta = copy.deepcopy(original(name))
        meta[field] = value
        return meta
    monkeypatch.setattr(analyzer, 'load_intent', altered)
    result = analyzer.build_report()
    assert structural(result) == structural(report)
    assert result['oracle_summary']['structural_sha256'] == report['oracle_summary']['structural_sha256']
    if field == 'changed_value_mm':
        assert result['answers']['object_setting_candidate_range'] is None


def test_renamed_labels(analyzer, tmp_path, report):
    paths = []
    for i, name in enumerate(NAMES):
        path = tmp_path / f'opaque_{92-i}.txt'
        path.write_bytes((analyzer.research.TEXT / name).read_bytes())
        paths.append(path)
    result = analyzer.build_report(paths, oracle_enabled=False)
    for key in STRUCTURAL_KEYS[1:]:
        assert result[key] == report[key]


def test_numeric_nomination_is_bounded_not_value_driven(analyzer):
    assert analyzer.numeric_windows([bytes(20), b'\xff'*16+bytes(4)]) == []  # never split a wide blob
    assert analyzer.numeric_windows([bytes(12), b'\xff'*7+bytes(5)])[0]['relative_range'] == [0, 8]
    assert analyzer.numeric_windows([bytes(7), b'\xff'*7]) == []  # no out-of-bounds high byte
    assert analyzer.numeric_windows([bytes(20), b'\xff'*8+bytes(12)])[0]['nomination'] == 'exact_eight_byte_union'
    assert analyzer.numeric_windows([bytes(8), bytes(9)]) == []
    assert analyzer.delta(b'abc', b'abcdef')['ranges'] == [[3, 6]]
    assert analyzer.delta(bytes(204), bytes(203)+b'\xff')['ranges'] == [[203, 204]]


def test_requested_storage(report):
    setting = report['answers']['object_setting_candidate_range']
    assert setting['node'] == 1 and setting['relative_range'] == [262, 270]
    assert setting['encoding'] == ['f64le_meters']
    candidate = report['numeric_candidate_summary']['candidates'][setting['candidate']]
    assert candidate['discovered_delta'] == [262, 270]
    assert candidate['nomination'] == 'exact_eight_byte_union'
    assert [struct.unpack('<d', bytes.fromhex(h))[0] for h in candidate['raw']] == [0, .1, .06, .04, -.06]
    assert candidate['typed_width'] is None
    assert all(not row['hypotheses']['f64le_millimeters'] for row in report['oracle_summary']['numeric_tests'])


def test_compression_candidates_and_model_gap(report):
    candidates = report['answers']['compression_activation_candidate_ranges']
    assert [c['relative_range'] for c in candidates] == [[214, 222], [286, 294]]
    tests = report['oracle_summary']['numeric_tests']
    first, second = [tests[c['candidate']] for c in candidates]
    assert first['values'] == second['values']
    assert first['values'] == [0.9989999999999998, 1.0, 0.8034631424913115, 0.5353087616608744, 0.8034631424913115]
    assert all(not r['matches'] for r in first['ratio_diagnostics'])
    assert all(-.00101 < r['residual'] < -.00099 for r in first['ratio_diagnostics'])
    assert report['compression_activation_summary']['additional_vs_baseline_100']
    assert report['answers']['compression_model_readiness'] == 'provisional_correlated_candidates_model_unresolved'


@pytest.mark.parametrize('field', ['height', 'width', 'slant', 'auxiliary', 'spacing', 'rotation', 'rgb'])
def test_every_slot_field(report, field):
    region = report['slot_field_audit']['regions'][field]
    assert len(region['fixtures']) == 5
    for rows in region['fixtures'].values():
        assert len(rows) == 9
        assert [r[0] for r in rows] == list(range(9))
        assert [r[1] for r in rows] == [False]*8+[True]
        assert all(r[3] is False for r in rows)
        if field in ('width', 'spacing'):
            assert all(struct.unpack('<d', bytes.fromhex(r[2]))[0] == 1 for r in rows)


@pytest.mark.parametrize('key,raw', [('plus00', '05000000'), ('plus08', '00'), ('plus09', '000000'),
                                    ('plus24', '00'*8), ('plus38', '9a9999999999d9bf')])
def test_independent_f4_regions(report, key, raw):
    for rows in report['f4_summary']['regions'][key]['fixtures'].values():
        assert len(rows) == 9
        assert all(r[2] == raw and r[3] is False for r in rows)
    assert report['answers']['runtime_f4_review_readiness'] == 'no_maxlength_falsification_trigger'


def test_positive_negative_symmetry(report):
    symmetry = report['positive_negative_symmetry_summary']
    assert symmetry['shared_baseline_changed_ranges'] and symmetry['identical_baseline_range_boundaries']
    assert [8, 15] in symmetry['negative_only_vs_all_positive']['1']
    assert [32, 39] in symmetry['negative_only_vs_all_positive']['1']
    signs = [r for r in symmetry['numeric_symmetry'] if r['sign_only']]
    assert len(signs) == 1 and signs[0]['magnitude_identical']
    assert report['numeric_candidate_summary']['candidates'][signs[0]['candidate']]['relative_range'] == [262, 270]
    upstream = report['cparagraphe_region_differentials']['f2:f4']['upstream']['ranges']
    assert [269, 270] in upstream
    assert report['answers']['terminal_behavior'] == 'complete_204_bytes_unchanged'


def test_geometry_is_separate(report):
    zones = [report['geometry_summary'][f'f{i}'][0]['geometry'] for i in range(5)]
    assert [g['x_extent_mm'] for g in zones] == pytest.approx([74.5839017735334, 100, 60, 40, 60])
    assert zones[2]['bbox']['xmin_m'] == zones[4]['bbox']['xmin_m']
    assert zones[4]['bbox']['ymin_m'] == pytest.approx(zones[2]['bbox']['ymin_m']-.01)
    assert all(g['y_extent_mm'] == pytest.approx(10) for g in zones)
    assert zones[0]['role'] == 'parsed_geometry_not_rendered_glyph_measurement'


def test_sources_and_policies_unchanged(report):
    hashes = {'src/type3_clipboard_codec/parsers/text/text_slot_candidate.py':
              '31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876',
              'src/type3_clipboard_codec/parsers/type3_chain_parser.py':
              '9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb',
              'tools/analyze_text_slot_spacing_fields.py':
              '3b2d7545189da35b9682c61575e946ea48b1cc2f4dc6fd3938ce49b9f39094b3',
              'tools/analyze_text_slot_style_fields.py':
              'd19a4a2345209c023c763860eba8f9c0191582616c9490aca23c8695079b30f2'}
    for path, expected in hashes.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    assert report['policy']['runtime_parser_behavior'] == 'not_modified'
    assert not report['answers']['parser_safe']
    assert report['answers']['ownership_status'] == 'unresolved'
    assert report['answers']['runtime_change_readiness'] == 'not_authorized_in_this_task'


@pytest.mark.parametrize('flags', [[], ['--json'], ['--json', '--no-oracle'], ['--details'], ['--json', '--details']])
def test_cli_bounds(flags):
    result = subprocess.run([sys.executable, str(CLI), *flags], cwd=ROOT, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    assert len(result.stdout) < (100000 if '--json' in flags else 50000)


def test_inventory_limit(analyzer):
    with pytest.raises(ValueError, match='exactly five'):
        analyzer.build_report([])
