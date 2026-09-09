"""Spacing controls: raw discovery must precede and survive adversarial intent."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools/analyze_text_slot_spacing_fields.py'
NAMES = ('text_slotstyle_a8_baseline.txt', 'text_slotstyle_a8_char4_spacing50.txt',
         'text_slotstyle_a8_char4_spacing150.txt', 'text_slotstyle_a8_char6_spacing150.txt',
         'text_slotstyle_a8_all_spacing150.txt')
HASHES = ('994c115e0dab58c605747420e7ba1e67961835ed4ef17aae0951bf899a406392',
          '44e34d07dae0ad07126b9ea0ac1a6ab8c5557e3eb5d2ff0926f4ef2ef43380a3',
          '4aca752c400bded286e7115d15e9cbc4f96572d113c609e97e82782e0fb8fd50',
          '475e09e69b70c612cffae140f389fad7da2962fec8b7741c253aaf4e9b51bf4a',
          '3e46e6b3406d17d2f6a40dbe3b84e9fced14d985772635bbb8f2e61cc263f9e6')


@pytest.fixture(scope='module')
def analyzer():
    spec = importlib.util.spec_from_file_location('spacing_research_test', CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def report(analyzer):
    return analyzer.build_report()


def test_inventory_and_hashes(analyzer, report):
    assert analyzer.FIXTURES == NAMES
    assert len(report['fixture_inventory']) == 5
    assert tuple(r['file_sha256'] for r in report['fixture_inventory']) == HASHES
    for name, expected in zip(NAMES, HASHES, strict=True):
        assert hashlib.sha256((analyzer.TEXT / name).read_bytes()).hexdigest() == expected


def test_freeze_before_intent(analyzer, monkeypatch):
    original = analyzer.oracle_phase
    def evaluate(frozen, *args):
        assert isinstance(frozen, str)
        assert len(json.loads(frozen)['per_fixture_differentials']) == 5
        with monkeypatch.context() as m:
            m.setattr(analyzer, 'structural_phase', lambda *a: pytest.fail('discovery after freeze'))
            return original(frozen, *args)
    monkeypatch.setattr(analyzer, 'oracle_phase', evaluate)
    analyzer.build_report()


def test_structural_never_reads_intent(analyzer, monkeypatch, report):
    monkeypatch.setattr(analyzer, 'load_intent', lambda *a: pytest.fail('oracle access'))
    result = analyzer.build_report(oracle_enabled=False)
    assert result['oracle_summary']['structural_sha256'] == report['oracle_summary']['structural_sha256']
    for key in ('per_fixture_differentials', 'changed_range_summary', 'structural_alignment_summary'):
        assert result[key] == report[key]


@pytest.mark.parametrize('attack', ['index', 'value', 'terminal'])
def test_adversarial_intent(analyzer, monkeypatch, report, attack):
    original = analyzer.load_intent
    def malicious(name):
        meta = copy.deepcopy(original(name))
        if attack == 'value':
            meta['changed_value_percent'] = -987
            meta['baseline_value_percent'] = 432
        elif attack == 'index':
            meta['target_character_index_1based'] = 2
        else:
            meta['target_character_indices_1based'] = list(range(1, 10))
        return meta
    monkeypatch.setattr(analyzer, 'load_intent', malicious)
    result = analyzer.build_report()
    assert result['oracle_summary']['structural_sha256'] == report['oracle_summary']['structural_sha256']
    assert result['per_fixture_differentials'] == report['per_fixture_differentials']
    if attack == 'terminal':
        assert not result['oracle_summary']['per_fixture'][NAMES[4]]['valid_visible_targets']


def test_renaming(analyzer, tmp_path, report):
    paths = []
    for i, name in enumerate(NAMES):
        path = tmp_path / f'opaque_{17-i}.txt'
        path.write_bytes((analyzer.TEXT / name).read_bytes())
        paths.append(path)
    result = analyzer.build_report(paths, paths[0].name, oracle_enabled=False)
    for name, path in zip(NAMES, paths, strict=True):
        assert result['structural_alignment_summary'][path.name] == report['structural_alignment_summary'][name]
        assert result['per_fixture_differentials'][path.name] == report['per_fixture_differentials'][name]


def test_full_period_and_ordinal_transfer(report):
    expected = ([], [3], [3], [5], list(range(9)))
    for name, ordinals in zip(NAMES, expected, strict=True):
        diff = report['per_fixture_differentials'][name]
        assert diff['count'] == 9 and diff['periodic_window_bytes'] == 204
        rows = [s for s in diff['slots'] if s['changed_byte_count']]
        assert [s['slot_ordinal_zero_based'] for s in rows] == ordinals
        assert all(s['ranges'][0]['relative_range'] == [70, 71] for s in rows)
        assert all(s['changed_byte_count'] == 1 for s in rows)
        assert diff['positive_controls']['code_fixture'] == ['41000000'] * 8 + ['00000000']
        assert diff['positive_controls']['rgb_fixture'] == diff['positive_controls']['rgb_baseline']
    assert report['ordinal_transfer_summary']['ordinal_transfer_supported']
    assert report['all_character_replication_summary']['visible_slot_replication_supported']
    terminal = report['answers']['terminal_spacing_behavior']
    assert terminal[NAMES[4]]['changed'] and not terminal[NAMES[4]]['intentionally_targeted']
    assert all(not terminal[n]['changed'] for n in NAMES[1:4])


def test_exact_raw_encoding_limits(analyzer, report):
    assert analyzer.diagnostic_windows([(70, 71)]) == []
    assert analyzer.diagnostic_windows([(36, 44), (80, 84)]) == [(36, 44), (80, 84)]
    assert report['answers']['diagnostic_spacing_encoding'] == 'unresolved'
    for name, raw in zip(NAMES[1:], ['e0', 'f8', 'f8', 'f8'], strict=True):
        rows = report['per_fixture_differentials'][name]['slots']
        assert all(s['ranges'][0]['fixture_hex'] == raw for s in rows if s['changed_byte_count'])


@pytest.mark.parametrize('key,raw', [('f4_region_a_summary', '00'*8),
                                    ('f4_region_b_summary', '9a9999999999d9bf')])
def test_f4_regions_independent(report, key, raw):
    assert len(report[key]['fixtures']) == 5
    for rows in report[key]['fixtures'].values():
        assert len(rows) == 9
        assert all(r['fixture_hex'] == raw and not r['changed'] for r in rows)
    assert report[key]['status'] == 'not_falsified_by_current_spacing_controls'


def test_aux_and_secondary(report):
    assert all(not r['changed'] for rows in report['auxiliary_region_summary']['fixtures'].values() for r in rows)
    for name in NAMES[1:]:
        secondary = report['secondary_change_summary'][name]
        assert secondary['before_first_slot']['changed_byte_count'] > 0
        assert secondary['after_slot_windows']['changed_byte_count'] > 0
        assert any(n['bbox_changed'] for n in secondary['other_nodes'])


def test_runtime_source_and_hashes(report):
    for row in report['runtime_candidate_summary'].values():
        assert row['parse_success'] and row['candidate_present']
        assert row['source'] == 'CParagraphe_slot_prefix_family_v2'
        assert (row['first_prefix'], row['slot_count'], row['prefix_family'], row['plus08_value']) == (310, 9, 'F4', 0)
    for path, expected in (
        ('parsers/text/text_slot_candidate.py', '31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876'),
        ('parsers/type3_chain_parser.py', '9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb'),
    ):
        assert hashlib.sha256((ROOT / 'src/type3_clipboard_codec' / path).read_bytes()).hexdigest() == expected
    assert not report['answers']['parser_safe']
    assert report['answers']['runtime_change_readiness'] == 'not_authorized_in_this_task'
    assert report['answers']['ownership_status'] == 'unresolved'


def test_alignment_without_runtime_acceptance(analyzer, monkeypatch):
    original = analyzer.observe_runtime
    def absent(raw):
        _, digest = original(raw)
        return dict(parse_success=True, candidate_present=False, status='safe_abstention'), digest
    monkeypatch.setattr(analyzer, 'observe_runtime', absent)
    assert analyzer.build_report(oracle_enabled=False)['answers']['fixtures_aligned'] == 5


def test_ambiguous_alignment_and_complete_deltas(analyzer):
    assert analyzer.compare({'selected': None}, {'selected': None})['status'] == 'unresolved'
    a = bytes(204)
    b = bytearray(a)
    b[203] = 1
    assert analyzer.changed_ranges(a, b)['ranges'][0]['relative_range'] == [203, 204]
    assert analyzer.changed_ranges(b'a', b'abc')['changed_byte_count'] == 2


@pytest.mark.parametrize('flags', [[], ['--json'], ['--json', '--no-oracle'], ['--json', '--details']])
def test_cli_bounds(flags):
    result = subprocess.run([sys.executable, str(CLI), *flags], cwd=ROOT, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    assert len(result.stdout) < (100000 if '--json' in flags else 50000)
    if '--json' in flags:
        assert json.loads(result.stdout)['answers']['fixtures_aligned'] == 5

@pytest.fixture(scope='module')
def ratio_report(analyzer):
    return analyzer.build_report(spacing_ratio=True)


def test_ratio_exact_windows(ratio_report):
    evidence = ratio_report['spacing_ratio_raw']
    assert evidence['relative_range'] == [64, 72]
    patterns = ([1.0]*9, [1.0]*3+[0.5]+[1.0]*5, [1.0]*3+[1.5]+[1.0]*5,
                [1.0]*5+[1.5]+[1.0]*3, [1.5]*9)
    raw = {1.0: '000000000000f03f', 0.5: '000000000000e03f', 1.5: '000000000000f83f'}
    for name, values in zip(NAMES, patterns, strict=True):
        rows = evidence['fixtures'][name]
        assert [r['f64le'] for r in rows] == values
        assert [r['raw_hex'] for r in rows] == [raw[v] for v in values]
        assert [r['ordinal'] for r in rows] == list(range(9))
        assert [r['terminal'] for r in rows] == [False]*8+[True]


def test_ratio_fixed_read_only(analyzer, monkeypatch):
    class FixedWindow:
        def __getitem__(self, key):
            assert key == slice(64, 72)
            return bytes.fromhex('0000000000000440')  # 2.5, preserved despite mismatch
    monkeypatch.setattr(analyzer, 'slots', lambda _: [FixedWindow()])
    assert analyzer.read_ratio_windows({'selected': {'count': 1}}) == [
        dict(ordinal=0, terminal=True, raw_hex='0000000000000440', f64le=2.5)]


def test_ratio_freeze_and_no_oracle(analyzer, monkeypatch, ratio_report):
    original = analyzer.load_intent
    frozen = []
    original_oracle = analyzer.oracle_phase
    def oracle(raw, *args):
        frozen.append(json.loads(raw)['spacing_ratio_raw'])
        with monkeypatch.context() as m:
            m.setattr(analyzer, 'read_ratio_windows', lambda *a: pytest.fail('read after freeze'))
            return original_oracle(raw, *args)
    monkeypatch.setattr(analyzer, 'oracle_phase', oracle)
    assert analyzer.build_report(spacing_ratio=True) == ratio_report
    assert frozen == [ratio_report['spacing_ratio_raw']]
    monkeypatch.setattr(analyzer, 'load_intent', lambda *a: pytest.fail('intent read'))
    absent = analyzer.build_report(spacing_ratio=True, oracle_enabled=False)
    assert absent['spacing_ratio_raw'] == ratio_report['spacing_ratio_raw']
    assert absent['oracle_summary']['structural_sha256'] == ratio_report['oracle_summary']['structural_sha256']
    assert absent['spacing_ratio_summary']['confidence'] == 'unresolved'
    monkeypatch.setattr(analyzer, 'load_intent', original)


@pytest.mark.parametrize('attack', ['index', 'value'])
def test_ratio_adversarial_oracle(analyzer, monkeypatch, ratio_report, attack):
    original = analyzer.load_intent
    def altered(name):
        meta = copy.deepcopy(original(name))
        meta['target_character_index_1based' if attack == 'index' else 'changed_value_percent'] = 2
        return meta
    monkeypatch.setattr(analyzer, 'load_intent', altered)
    result = analyzer.build_report(spacing_ratio=True)
    assert result['spacing_ratio_raw'] == ratio_report['spacing_ratio_raw']
    assert result['oracle_summary']['structural_sha256'] == ratio_report['oracle_summary']['structural_sha256']
    assert result['spacing_ratio_summary']['confidence'] == 'unresolved'


def test_ratio_renamed_inputs(analyzer, tmp_path, ratio_report):
    paths = []
    for i, name in enumerate(NAMES):
        path = tmp_path / f'blind_{i}.txt'
        path.write_bytes((analyzer.TEXT / name).read_bytes())
        paths.append(path)
    result = analyzer.build_report(paths, paths[0].name, spacing_ratio=True, oracle_enabled=False)
    for name, path in zip(NAMES, paths, strict=True):
        assert result['spacing_ratio_raw']['fixtures'][path.name] == ratio_report['spacing_ratio_raw']['fixtures'][name]


def test_ratio_support_and_terminal(ratio_report):
    summary = ratio_report['spacing_ratio_summary']
    assert summary['candidate'] == 'spacing_ratio_f64_candidate'
    assert summary['confidence'] == 'strong_style_field_candidate'
    assert summary['ordinal_transfer_supported'] and summary['visible_slot_replication_supported']
    assert summary['diagnostic_storage_candidate'] == 'f64le'
    assert summary['typed_width'] is None and summary['ownership_status'] == 'unresolved'
    assert summary['terminal_status'] == 'terminal_spacing_state_propagation_observed'
    assert summary['prior_plus47_compatible']
    assert summary['f4_required_bytes_unaffected'] and summary['runtime_candidates_present']
    for name in NAMES[1:]:
        assert summary['per_fixture'][name]['roles'][-1] == 'terminal'
        assert summary['per_fixture'][name]['visible_match']
    test_runtime_source_and_hashes(ratio_report)
    assert tuple(r['file_sha256'] for r in ratio_report['fixture_inventory']) == HASHES


@pytest.mark.parametrize('flags', [[], ['--json'], ['--json', '--no-oracle'], ['--json', '--details']])
def test_ratio_cli_bounds(flags):
    result = subprocess.run([sys.executable, str(CLI), '--spacing-ratio', *flags],
                            cwd=ROOT, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    assert len(result.stdout) < (100000 if '--json' in flags else 50000)
    if '--json' in flags:
        assert json.loads(result.stdout)['spacing_ratio_raw']['relative_range'] == [64, 72]
