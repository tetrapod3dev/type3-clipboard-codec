import copy
import json
import os
import subprocess
import sys
import pytest
import boundary_diagnostic as d
import reproduce

@pytest.fixture(scope='module')
def reports():return reproduce.build_reports()[0]

@pytest.mark.parametrize('name',['G1','H1'])
def test_group_has_simultaneous_boundary_and_shared_window_diagnostics(reports,name):
    r=reports[name]
    assert r['overall_status']=='CONDITIONAL_COMPARISON_COMPLETE'
    assert 'SHARED_PROPERTY_CANDIDATE_WINDOW' in [e['code'] for e in r['observations']]
    assert len(r['contours'])==2
    for i,c in enumerate(r['contours']):
        assert c['codec_property_candidate_range']==[795,8192]
        assert c['native_property_body_range']==[[795,907],[1521,1633]][i]
        assert c['ccourbe_suffix_range']==[[907,931],[1633,1657]][i]
        assert c['class_descriptor_schema']==2
        assert {'BOUNDARY_MATCH','CANDIDATE_WINDOW_WIDER_THAN_NATIVE_BODY'} <= {e['code'] for e in c['observations']}
        assert all(f['outside_native_property_body'] and f['equals_codec_selected_color'] for f in c['color_fields'])
        assert c['codec_color_confidence']=='HEURISTIC' and c['ownership']=='UNKNOWN'
    assert r['ownership']=='UNKNOWN' and not r['change_allowed']

@pytest.mark.parametrize('name,count,end',[('polyline_3_points',3,590),('polyline_5_points',5,662),('polygon_5_sides',5,662),('polygon_6_sides',6,698),('default_circle',8,770)])
def test_variable_contours_keep_existing_codec_values(reports,name,count,end):
    r=reports[name];c=r['contours'][0]
    assert c['native_count']==count and c['native_record_width']==36
    assert c['native_contour_range']==c['codec_contour_range']==[482,end]
    assert c['native_property_body_range'][0]==end+21
    assert all(f['equals_codec_selected_color'] for f in c['color_fields'])

@pytest.mark.parametrize('name',['G1','H1','polyline_3_points','polyline_5_points','polygon_5_sides','polygon_6_sides','default_circle','text/default_text'])
def test_complete_decoder_before_after_equal(name):
    s=d.load_shadow();data=s.fixtures()[name][1]
    before=s.a.Decoder().decode_bytes_with_parser(data)
    result=d.diagnose_bytes(data,research_shadow=True)
    after=s.a.Decoder().decode_bytes_with_parser(data)
    assert d.fingerprint(before)==d.fingerprint(after)
    assert result['decoder_object_unchanged']

def test_text_is_unsupported_only_by_research_reader(reports):
    r=reports['text/default_text']
    assert r['overall_status']=='UNSUPPORTED' and r['shadow_stop_cursor']==0
    assert r['codec']['parser_name']=='Type3ChainParser' and r['codec']['text_content']=='abcdefg'
    assert not r['contours']

def test_schema_is_separate_from_archive_class_id(reports):
    p=next(e for e in reports['G1']['descriptor_and_reference_events'] if e['kind']=='new_class' and e['class']=='CPropertyExtend')
    assert p['schema']==5 and p['class_id']==8
    assert any(e['kind']=='class_reference' for e in reports['G1']['descriptor_and_reference_events'])

@pytest.mark.parametrize('name',['count_out_of_scope','count_stride_extent_truncated','property_truncated','suffix_truncated','unregistered_class_reference','unsupported_schema'])
def test_corruption_stops_without_resynchronization(name):
    r=d.diagnose_bytes(reproduce.synthetic_inputs()[name],research_shadow=True)
    assert r['overall_status']=='UNSUPPORTED' and r['shadow_stop_reason']
    assert r['shadow_stop_cursor']>0 and not r['contours']
    assert r['decoder_observation_status']=='NOT_RUN_UNSUPPORTED_STRUCTURE' and r['codec'] is None
    assert not r['change_allowed']

def test_duplicate_payload_is_ambiguous_not_member_assignment():
    r=d.diagnose_bytes(reproduce.synthetic_inputs()['duplicate_contour'],research_shadow=True)
    assert r['overall_status']=='AMBIGUOUS'
    assert all(c['matching_chain_indices']==[0,1] for c in r['contours'])
    assert all('codec_chain_index' not in c for c in r['contours'])

def test_same_colors_do_not_hide_boundary_mismatch():
    # Synthetic observation fault, not bytes produced by Type3.
    s=d.load_shadow();data=s.fixtures()['G1'][1];obj,parser=s.a.Decoder().decode_bytes_with_parser(data)
    codec=d.normalize_codec(obj,parser,data,s)
    codec['chains'][0]['contour_range'][0]+=1
    r=d.compare_views(data,codec,s.shadow(data))
    assert r['overall_status']=='BOUNDARY_MISMATCH'
    assert all(f['equals_codec_selected_color'] for f in r['contours'][0]['color_fields'])

def test_unknown_tail_removal_is_not_archive_validation():
    r=d.diagnose_bytes(reproduce.synthetic_inputs()['unknown_tail_removed'],research_shadow=True)
    assert r['overall_status']=='CONDITIONAL_COMPARISON_COMPLETE'
    assert r['unknown_ranges']==[] and r['archive_valid_length']=='UNKNOWN'
    assert r['uninterpreted_tail_start']==1657

def test_diagnostic_failure_does_not_replace_decoder(monkeypatch):
    s=d.load_shadow();data=s.fixtures()['G1'][1]
    expected=d.fingerprint(s.a.Decoder().decode_bytes(data))
    def fail(_):raise RuntimeError('synthetic research failure')
    monkeypatch.setattr(s,'shadow',fail)
    r=d.diagnose_bytes(data,research_shadow=True)
    assert r['overall_status']=='DIAGNOSTIC_ERROR'
    assert r['decoder_fingerprint']==expected and r['decoder_object_unchanged']

def test_opt_in_required():
    with pytest.raises(ValueError,match='Explicit'):d.diagnose_bytes(b'')

def test_normal_decoder_does_not_import_research():
    code="from type3_clipboard_codec import Decoder; import sys; assert not any('boundary007' in k or 'prior006' in k for k in sys.modules)"
    env={**os.environ,'PYTHONPATH':str(d.ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
    assert subprocess.run([sys.executable,'-c',code],env=env,capture_output=True).returncode==0

def test_cli_requires_opt_in_and_never_overwrites(tmp_path):
    path=d.load_shadow().fixtures()['G1'][0]
    tool=str(d.ROOT/'research/archive-boundary-diagnostic-007/boundary_diagnostic.py')
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    missing=subprocess.run([sys.executable,tool,'--input',str(path)],capture_output=True,env=env)
    assert missing.returncode==2
    output=tmp_path/'result.json'
    args=[sys.executable,tool,'--input',str(path),'--research-shadow','--output',str(output)]
    run=subprocess.run(args,capture_output=True,env=env)
    assert run.returncode==0,run.stderr
    data=output.read_bytes();assert json.loads(data)['source_sha256']==d.sha(path.read_bytes())
    assert subprocess.run(args,capture_output=True,env=env).returncode==2
    assert output.read_bytes()==data
