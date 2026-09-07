from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.formatters import _json_safe
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text.text_slot_candidate import VARIANTS

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools/analyze_text_slot_style_fields.py'
GOLDEN = json.loads((ROOT / 'tests/samples/reports/text/text_slot_style_runtime_baseline.json').read_text())
NAMES = sorted(GOLDEN['fixtures'])


@pytest.fixture(scope='module')
def analyzer():
    spec = importlib.util.spec_from_file_location('slot_style_analysis_test', CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def report(analyzer):
    return analyzer.build_report()


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


def structural(report, analyzer):
    return {k:report[k] for k in analyzer.STRUCTURAL_KEYS}


def test_inventory_deterministic(report, analyzer):
    assert [f['fixture'] for f in report['fixture_inventory']] == NAMES
    assert analyzer.build_report() == report
    assert len(NAMES) == 9
    assert not report['warnings']


def test_shared_controls(report):
    c = report['shared_capture_controls']
    assert c['visible_text'] == 'AAAAAAAA' and c['font'] == 'Arial'
    assert c['character_count'] == 8 and c['target_character_index_1based'] == 4
    assert c['lower_left_mm'] == [31.123,72.234,1.234]
    assert c['anchor_mm'] == [68.415,72.234] and c['alignment'] == 'center-bottom'
    assert c['capture_reset_between_fixtures'] and c['all_other_character_properties_held_constant']
    assert 'No Z semantic decoding change is implied.' in c['z_coordinate_note']


def test_freeze_before_oracle(analyzer, monkeypatch, report):
    original = analyzer.oracle_phase
    seen = []
    def phase(frozen, enabled):
        assert isinstance(frozen, str)
        evidence = json.loads(frozen)
        assert len(evidence['per_fixture_differentials']) == 9
        assert all(d['status']=='aligned' for d in evidence['per_fixture_differentials'].values())
        seen.append(evidence)
        with monkeypatch.context() as patch:
            patch.setattr(analyzer, 'structural_phase', lambda *a, **k: pytest.fail('discovery after freeze'))
            return original(frozen, enabled)
    monkeypatch.setattr(analyzer, 'oracle_phase', phase)
    assert analyzer.build_report() == report
    assert seen


def test_no_oracle_equality(analyzer, report, monkeypatch):
    monkeypatch.setattr(analyzer, 'load_oracle', lambda _: pytest.fail('oracle access'))
    absent = analyzer.build_report(oracle_enabled=False)
    assert structural(absent, analyzer) == structural(report, analyzer)
    assert absent['answers']['candidate_parser_change_readiness'] == 'not_ready'
    cli = json.loads(run_cli('--json','--no-oracle'))
    assert structural(cli, analyzer) == structural(report, analyzer)


@pytest.mark.parametrize('field,value', [('changed_value',999999),('target_character_index_1based',8),
                                        ('changed_property','fabricated'),('font','incorrect')])
def test_wrong_oracle_cannot_change_discovery(analyzer, report, monkeypatch, field, value):
    original = analyzer.load_oracle
    monkeypatch.setattr(analyzer, 'load_oracle', lambda n: {**original(n),field:value})
    changed = analyzer.build_report()
    assert structural(changed, analyzer) == structural(report, analyzer)


@pytest.mark.parametrize('name', NAMES)
def test_runtime_exact_snapshot_and_capture_unchanged(name):
    path = ROOT / 'tests/samples/text' / name
    old = GOLDEN['fixtures'][name]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == old['fixture_file_sha256']
    obj, _ = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(path.read_text(encoding='utf-8')))
    encoded = json.dumps(_json_safe(asdict(obj)),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    # Exact whole parser result: no normalization or removal of candidate keys.
    assert hashlib.sha256(encoded).hexdigest() == old['parser_result_sha256']
    assert ('text_slot_run' in obj.candidate_fields) == old['candidate_present']
    assert obj.source_text_candidate == 'AAAAAAAA' and obj.display_text_candidate is None


@pytest.mark.parametrize('path,digest', GOLDEN['source_sha256'].items())
def test_runtime_source_and_anchor_pipeline_unchanged(path,digest):
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest


def test_family_has_no_new_variant_or_mask():
    assert VARIANTS == {(0,bytes.fromhex('7B14AE47E17A84')):'v0',
                        (0,bytes.fromhex('B81E85EB51B89E')):'v1',
                        (1,bytes.fromhex('7B14AE47E17A84')):'v2'}


def test_all_alignment_and_runtime_abstentions(report):
    for name, diff in report['per_fixture_differentials'].items():
        assert diff['status']=='aligned' and diff['total_aligned_slots']==9
        assert diff['relocation_bytes']==0 and not diff['count_changed']
        runtime=report['runtime_candidate_behavior'][name]
        assert runtime['candidate_present'] == GOLDEN['fixtures'][name]['candidate_present']
        if runtime['candidate_present']:
            assert runtime['prefix_variant']=='v0'
            assert runtime['slot_code_sequence']==[65]*8+[0]
        else:
            assert runtime['status']=='safe_abstention'


@pytest.mark.parametrize('kind,offset,values', [('height',12,[0.02]),('width',20,[0.5,1.5]),
                                            ('slant',28,[-0.2617993877991494,0.2617993877991494]),
                                            ('rotation',72,[-0.2617993877991494,0.2617993877991494])])
def test_local_numeric_candidates(report,kind,offset,values):
    summary=report[kind+'_candidate_summary']
    assert summary['status']=='strong_style_field_candidate'
    assert {r['offset'] for r in summary['target_encoding_matches']} == {offset}
    assert all(r['other_visible_slots_stable'] and r['terminal_field_stable'] for r in summary['field_profiles'])
    assert sorted(r['capture'][3] for r in summary['field_profiles']) == pytest.approx(values)
    if kind in ('slant','rotation'):
        assert summary['positive_negative_symmetry']
    assert summary['typed_width'] is None and summary['ownership']=='unresolved'


def test_color_control_and_secondary_changes(report):
    diffs=report['per_fixture_differentials']
    color=diffs['text_slotstyle_a8_char4_navy.txt']
    assert color['changed_slot_ordinals_zero_based']==[3]
    assert color['changed_slots'][0]['changed_ranges']==[[80,83]]
    assert report['color_control_summary']['color_control_alignment_status']=='strong_style_field_candidate'
    assert diffs['text_slotstyle_a8_char4_slant_p15.txt']['changed_slot_ordinals_zero_based']==[1,3]
    assert diffs['text_slotstyle_a8_char4_rotation_p15.txt']['terminal_changed']
    assert report['answers']['target_slot_isolation_status']=='primary_changes_at_target_with_secondary_slot_changes'


def test_no_ownership_or_promotion(report):
    assert report['policy']['anchor_ownership_used'] is False
    assert report['policy']['prefix_family_runtime_change']=='not_performed'
    for key in ('candidate_parser_change_readiness','color_ownership_readiness','slot_style_struct_readiness'):
        assert report['answers'][key]=='not_ready'
    assert report['runtime_prefix_family_implication']['v2_plus08_explanation']=='unresolved'
    assert report['answers']['runtime_prefix_family_review_readiness']=='ready_for_review'


@pytest.mark.parametrize('args,limit', [(('--json',),100000),(('--json','--details'),100000),
                                      ((),50000),(('--details',),50000)])
def test_output_bounds(args,limit):
    assert len(run_cli(*args))<limit


def test_details_do_not_change_ranking(analyzer,report):
    detailed=analyzer.build_report(details=True)
    for name,d in detailed['per_fixture_differentials'].items():
        assert d['field_candidate_ranking']==report['per_fixture_differentials'][name]['field_candidate_ranking']
        assert sum('fragments' in r for r in d.get('changed_slots',[]))<=4
        for row in d.get('changed_slots',[]):
            for fragment in row.get('fragments',[]):
                assert len(fragment['baseline_hex'])<=32
                assert len(fragment['capture_hex'])<=32


def test_missing_capture_warns_and_continues(analyzer):
    paths=sorted(analyzer.TEXT_DIR.glob('text_slotstyle_a8_*.txt'))[:-1]
    report=analyzer.build_report(paths)
    assert len(report['fixture_inventory'])==8 and report['warnings']
    assert all(d['status']=='aligned' for d in report['per_fixture_differentials'].values())


def test_filename_labels_do_not_select_fields(analyzer,tmp_path,report):
    paths=[]
    mapping={}
    for i,name in enumerate(NAMES):
        dest=tmp_path/f'capture_{i}.txt'
        dest.write_bytes((analyzer.TEXT_DIR/name).read_bytes())
        paths.append(dest)
        mapping[name]=dest.name
    renamed=analyzer.build_report(paths,baseline=mapping[analyzer.BASELINE],oracle_enabled=False)
    for name,d in report['per_fixture_differentials'].items():
        assert renamed['per_fixture_differentials'][mapping[name]]==d


def test_changed_slot_discovered_without_target_index(analyzer):
    raw=analyzer.load_raw(analyzer.TEXT_DIR/analyzer.BASELINE)
    capture={**raw,'selected':dict(raw['selected'])}
    payload=bytearray(capture['selected']['payload'])
    payload[capture['selected']['start']+6*204+120]^=1
    capture['selected']['payload']=bytes(payload)
    diff=analyzer.compare(raw,capture,False)
    assert diff['changed_slot_ordinals_zero_based']==[6]
    assert diff['changed_slots'][0]['changed_ranges']==[[120,121]]


@pytest.mark.parametrize('a,b,expected', [(b'abc',b'abc',[]),(b'abc',b'axz',[[1,3]]),
                                        (b'ab',b'abc',[[2,3]]),(b'abc',b'a',[[1,3]])])
def test_changed_ranges_bounds(analyzer,a,b,expected):
    assert analyzer.ranges(a,b)==expected


def test_ambiguous_or_incomplete_alignment_is_unresolved(analyzer):
    raw=analyzer.load_raw(analyzer.TEXT_DIR/analyzer.BASELINE)
    payload=raw['selected']['payload']
    assert len([r for r in analyzer.discover(payload) if r['eligible']])==1
    assert len([r for r in analyzer.discover(payload+payload) if r['eligible']])==2
    truncated=payload[:raw['selected']['end']+31]
    assert not any(r['eligible'] for r in analyzer.discover(truncated))


def test_budget_failure(analyzer,monkeypatch):
    monkeypatch.setitem(analyzer.LIMITS,'max_prefix_hits',1)
    report=analyzer.build_report(oracle_enabled=False)
    assert report['warnings']
    assert all(f['status']=='unresolved' for f in report['fixture_inventory'])
