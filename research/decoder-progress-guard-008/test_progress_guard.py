import json,sys
from pathlib import Path
import pytest
import bounded_child as b
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/archive-boundary-diagnostic-007'))
import reproduce,boundary_diagnostic as d

CASES=['count_stride_extent_truncated','property_truncated','suffix_truncated','count_out_of_scope','count_0','count_4294967295','count_4097','unregistered_class_reference','unsupported_schema','duplicate_contour','unknown_tail_removed']

def test_original_trace_proves_same_complete_selection_state_repeated():
    r=json.loads((Path(__file__).parent/'reproduction-before.json').read_text())
    assert r['timed_out'] and r['child_pid']!=r['parent_pid']
    states=[e for e in r['events'] if e['event']=='loop_completed']
    assert len(states)==3 and states[0]==states[1]==states[2]
    assert states[0]['idx']==0 and states[0]['marker_pos']==76
    assert states[0]['actual_selected'] is None and states[0]['found_for_this_marker']

@pytest.mark.parametrize('name',CASES)
def test_malformed_or_synthetic_input_finishes_in_bounded_child(name):
    r=b.run_case(name)
    assert not r['timed_out'],r
    assert r['returncode']==0,r
    assert r['events'][-1]['event'] in ('decoder_returned','decoder_exception')
    if name=='count_stride_extent_truncated':
        assert r['events'][-1]['event']=='decoder_returned'
        assert all(not c['count'] for c in r['events'][-1]['contours'])

@pytest.mark.parametrize('name',['G1','H1','polyline_3_points','polyline_5_points','polygon_5_sides','polygon_6_sides','default_circle','text/default_text'])
def test_exact_normal_model_and_parser_preserved(name):
    baseline=json.loads((Path(__file__).parent/'normal-before.json').read_text())
    data=d.load_shadow().fixtures()[name][1]
    current=d.fingerprint(d.load_shadow().a.Decoder().decode_bytes_with_parser(data))
    assert current==baseline[name]['before']==baseline[name]['after']

@pytest.mark.parametrize('name',['scan_fallback','scan_no_marker'])
def test_legitimate_scan_fallback_keeps_exact_baseline_result(name):
    before=b.run_case(name,before_scan=True);after=b.run_case(name)
    assert not before['timed_out'] and not after['timed_out']
    assert before['returncode']==after['returncode']==0
    a=before['events'][-1];c=after['events'][-1]
    assert a['headers']==c['headers'] and a['diagnostics']==c['diagnostics']
    if name=='scan_fallback':
        assert len(c['diagnostics'])==2 and len(c['headers'])==1


def test_007_reports_and_write_admission_unchanged():
    before=json.loads((Path(__file__).parent/'diagnostic-before.json').read_text(encoding='utf8'))
    current,_=reproduce.build_reports()
    assert current==before
    assert all(not v['change_allowed'] and v['ownership']=='UNKNOWN' for v in current.values())
    r=d.diagnose_bytes(reproduce.synthetic_inputs()['count_stride_extent_truncated'],research_shadow=True)
    assert r['decoder_observation_status']=='NOT_RUN_UNSUPPORTED_STRUCTURE'
