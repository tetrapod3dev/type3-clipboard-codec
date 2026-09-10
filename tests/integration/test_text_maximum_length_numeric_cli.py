"""Fixed-window numeric closeout, exact binary64 evidence and oracle isolation."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools/analyze_text_maximum_length_numeric.py'
HASHES = ('994c115e0dab58c605747420e7ba1e67961835ed4ef17aae0951bf899a406392',
          '1f24a7b2042dca993977690fa295aa7295593572103cb04523cc06ac1bd89046',
          'b8281f358591493b1dadf609c18ab788d8d73c1ae5f222045dbdb3a9033b25b6',
          '44b998a2e69cd08618936da6a5250a11bf223b7d0f89f3aef3deb1bb9ab6d49a',
          'e9bb3439205bab970b73b1b6fc70d2814d77e0d088cb577ed6d37802b4d27d85')


@pytest.fixture(scope='module')
def analyzer():
    spec = importlib.util.spec_from_file_location('maximum_length_numeric_test', CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def report(analyzer):
    return analyzer.build_report()


def test_fixed_raw_duplicate_inventory(analyzer, report):
    assert analyzer.WINDOWS == {'object_setting': (262, 270), 'scalar_a': (214, 222), 'scalar_b': (286, 294)}
    raws = ('298716d9cef7ef3f', '000000000000f03f', '8c541156f8b5e93f',
            '171013d73f21e13f', '8c541156f8b5e93f')
    values = (0.9989999999999998, 1.0, 0.8034631424913115, 0.5353087616608744, 0.8034631424913115)
    for i, (raw, value) in enumerate(zip(raws, values, strict=True)):
        windows = report['structural']['windows'][f'f{i}']
        for key in ('scalar_a', 'scalar_b'):
            assert windows[key]['raw_hex'] == raw
            assert windows[key]['f64le']['value'] == value
    assert report['structural']['duplicated_scalars'] == dict(byte_identical=True, numeric_identical=True)
    assert report['answers']['duplicate_scalar_status'] == 'duplicate_scalar_storage_observed'
    object_raws = ('0000000000000000', '9a9999999999b93f', 'b81e85eb51b8ae3f',
                   '7b14ae47e17aa43f', 'b81e85eb51b8aebf')
    for i, (raw, value) in enumerate(zip(object_raws, (0.0, 0.1, 0.06, 0.04, -0.06), strict=True)):
        setting = report['structural']['windows'][f'f{i}']['object_setting']
        assert setting['raw_hex'] == raw
        assert setting['f64le']['value'] == value


def test_json_round_trip_full_precision(analyzer, report):
    decoded = json.loads(analyzer.render(report, True))
    for windows in decoded['structural']['windows'].values():
        for row in windows.values():
            f = row['f64le']
            assert float(f['repr']) == float.fromhex(f['hex']) == f['value']
            assert struct.pack('<d', f['value']).hex() == row['raw_hex']
    assert '0.8034631424913115' in analyzer.render(report, True)


def test_exact_natural_extent_and_provenance(report):
    n = report['structural']['natural_extent']
    assert n['xmin_m']['raw_hex'] == 'fe169d2cb5de9f3f'
    assert n['xmax_m']['raw_hex'] == 'ec2c14869b0fbb3f'
    xmin = struct.unpack('<d', bytes.fromhex(n['xmin_m']['raw_hex']))[0]
    xmax = struct.unpack('<d', bytes.fromhex(n['xmax_m']['raw_hex']))[0]
    assert xmin == 0.031123000000000005 and xmax == 0.10570690177353342
    assert n['extent_m']['value'] == xmax-xmin == 0.07458390177353341
    assert n['extent_mm']['value'] == (xmax-xmin)*1000 == 74.58390177353341
    assert n['provenance']['xmin_absolute_range'] == [81, 89]
    assert n['provenance']['xmax_absolute_range'] == [105, 113]


def test_no_new_discovery_and_freeze(analyzer, monkeypatch, report):
    monkeypatch.setattr(analyzer.previous, 'numeric_windows', lambda *a: pytest.fail('new nomination'))
    monkeypatch.setattr(analyzer.previous, 'structural_phase', lambda *a: pytest.fail('new differential discovery'))
    original = analyzer.oracle_phase
    def after_freeze(frozen, enabled):
        assert json.loads(frozen) == report['structural']
        with monkeypatch.context() as m:
            m.setattr(analyzer, 'czone_extent', lambda *a: pytest.fail('geometry after freeze'))
            m.setattr(analyzer, 'raw_numeric', lambda *a: pytest.fail('numeric read after freeze'))
            m.setattr(analyzer.previous.research, 'read_capture', lambda *a: pytest.fail('binary after freeze'))
            return original(frozen, enabled)
    monkeypatch.setattr(analyzer, 'oracle_phase', after_freeze)
    assert analyzer.build_report() == report


def test_no_oracle_structural_equality(analyzer, monkeypatch, report):
    monkeypatch.setattr(analyzer.previous, 'load_intent', lambda *a: pytest.fail('intent access'))
    absent = analyzer.build_report(oracle_enabled=False)
    assert absent['structural'] == report['structural']
    assert absent['structural_sha256'] == report['structural_sha256']
    assert absent['answers']['h1_residuals'] == {}


@pytest.mark.parametrize('field,value', [('changed_value_mm', 20), ('baseline_natural_length_mm', 900),
    ('expected_ui_relationship', 'unknown'), ('observed_program_behavior', 'no negative description')])
def test_adversarial_labels(analyzer, monkeypatch, report, field, value):
    original = analyzer.previous.load_intent
    def altered(name):
        meta = copy.deepcopy(original(name))
        meta[field] = value
        return meta
    monkeypatch.setattr(analyzer.previous, 'load_intent', altered)
    result = analyzer.build_report()
    assert result['structural'] == report['structural']
    assert result['structural_sha256'] == report['structural_sha256']
    if field != 'changed_value_mm':
        assert result['oracle_summary']['below_natural'] == report['oracle_summary']['below_natural']


def test_only_fixed_hypotheses_and_residuals(analyzer):
    assert analyzer.hypotheses(50, 100) == {'H1': .5, 'H2': .499, 'H3': .499}
    assert analyzer.hypotheses(-50, 100) == analyzer.hypotheses(50, 100)
    assert analyzer.hypotheses(0, 100) == {'H1': 0.0, 'H2': -.001, 'H3': -.001}
    result = analyzer.residual(0.25, 0.5)
    assert result['absolute_residual'] == .25 and result['relative_residual'] == .5
    assert analyzer.ulp_distance(1.0, math.nextafter(1.0, math.inf)) == 1
    assert analyzer.ulp_distance(-1.0, math.nextafter(-1.0, -math.inf)) == 1
    assert analyzer.ulp_distance(-0.0, 0.0) == 0


def test_hypothesis_results(report):
    below = report['oracle_summary']['below_natural']
    for key in ('f2', 'f4'):
        assert below[key]['H1']['absolute_residual'] == 0.001000000000000223
        assert below[key]['H2']['absolute_residual'] == 2.220446049250313e-16
        assert below[key]['H3']['absolute_residual'] == 1.1102230246251565e-16
        assert [below[key][h]['ulp_distance'] for h in ('H2', 'H3')] == [2, 1]
    assert below['f3']['H1']['absolute_residual'] == 0.0010000000000000009
    assert below['f3']['H2']['absolute_residual'] == below['f3']['H3']['absolute_residual'] == 0
    assert 'f0' not in below and 'f1' not in below


def test_clamp_contradictions_and_baseline(report):
    oracle = report['oracle_summary']
    assert oracle['above_natural_clamp_status'] == 'no_compression_clamp_candidate'
    assert oracle['zero_default_mode_status'] == 'default_natural_mode_scalar_candidate'
    assert all(not v['exact_matches_all'] for v in oracle['clamp_whole_set'].values())
    for row in oracle['clamps']['f1'].values():
        assert row['absolute_residual'] == 0
    assert oracle['clamps']['f0']['min_1_L_over_N']['predicted']['value'] == 0
    assert oracle['clamps']['f0']['min_1_L_over_N_minus_001']['predicted']['value'] == -.001
    assert report['answers']['semantic_formula_readiness'] == 'provisional_not_ready'


def test_positive_negative_and_previous_evidence(report):
    raw = report['structural']
    pos, neg = raw['windows']['f2'], raw['windows']['f4']
    assert pos['object_setting']['raw_hex'] == 'b81e85eb51b8ae3f'
    assert neg['object_setting']['raw_hex'] == 'b81e85eb51b8aebf'
    for key in ('scalar_a', 'scalar_b'):
        assert pos[key]['raw_hex'] == neg[key]['raw_hex']
    assert report['answers']['positive_negative_magnitude_status'] == 'compression_magnitude_uses_absolute_length_candidate'
    assert raw['geometry']['f2'][0]['bbox'] != raw['geometry']['f4'][0]['bbox']
    assert raw['geometry']['f2'][2]['bbox'] == raw['geometry']['f4'][2]['bbox']
    assert len(raw['previous_negative_ranges']['rows']) == 44
    for row in raw['previous_negative_ranges']['rows']:
        assert len(set(row['raw'][:4])) == 1 and row['raw'][4] != row['raw'][0]
    for rows in raw['slot_invariance'].values():
        assert rows['all_204_bytes_unchanged'] and rows['terminal_204_bytes_unchanged']
        assert all(v['f64le']['value'] == 1 for k in ('width_values', 'spacing_values') for v in rows[k])
    for field in ('plus24', 'plus38'):
        assert all(not row[3] for rows in raw['f4_invariance']['regions'][field]['fixtures'].values() for row in rows)


def test_source_fixture_preservation(analyzer, report):
    assert tuple(r['file_sha256'] for r in report['structural']['fixture_inventory']) == HASHES
    for filename, expected in zip(analyzer.FIXTURES, HASHES, strict=True):
        assert hashlib.sha256((analyzer.previous.research.TEXT/filename).read_bytes()).hexdigest() == expected
    for path, expected in (
        ('src/type3_clipboard_codec/parsers/text/text_slot_candidate.py',
         '31ff8567fe65c08ff9085d5433b1b533efc6978f540b6ed0d17dd735dba00876'),
        ('src/type3_clipboard_codec/parsers/type3_chain_parser.py',
         '9eed3128222722ca9300e3a3845600026c6562aec951c04772f86d22d03f9dbb')):
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected
    assert all(r['source'] == 'CParagraphe_slot_prefix_family_v2' and r['candidate_present']
               for r in report['structural']['runtime_candidate_summary'].values())
    assert report['answers']['typed_width'] is None
    assert not report['answers']['parser_safe'] and report['answers']['ownership_status'] == 'unresolved'


@pytest.mark.parametrize('flags', [[], ['--json'], ['--json', '--no-oracle']])
def test_cli(flags):
    result = subprocess.run([sys.executable, str(CLI), *flags], cwd=ROOT, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    assert len(result.stdout) < (100000 if '--json' in flags else 50000)
