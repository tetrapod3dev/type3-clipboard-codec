from pathlib import Path
import json
import subprocess
import sys
import copy
import pytest
import selection_inventory as inv
import reproduce_inventory as reproduce

@pytest.fixture(scope='module')
def results():
    return reproduce.build_results()

@pytest.mark.parametrize('name',['default_rectangle','polyline_3_points','polyline_5_points','polygon_5_sides','polygon_6_sides','default_circle','text/default_text','G1','H1','E1','F'])
def test_saved_inputs_never_claim_complete_selection(results,name):
    r=results['samples'][name]['inventory']
    assert r['status']=='PARTIAL'
    assert r['top_level_selection_count']['value'] is None
    assert r['group_hierarchy']['value'] is None
    assert not r['complete_inventory'] and not r['change_allowed']
    assert r['decoder_model_unchanged']
    assert not r['execution']['timed_out']
    assert all(c['parent_group']['value'] is None for c in r['candidates'])

@pytest.mark.parametrize('name',['G1','H1'])
def test_two_geometry_candidates_are_not_two_selected_objects(results,name):
    r=results['samples'][name]
    assert r['external_validation_only']['top_level_ui_observation']==1
    assert r['inventory']['candidate_count']==2
    assert all('SHARED_PROPERTY_CANDIDATE_WINDOW; color ownership UNKNOWN' in c['ambiguities'] for c in r['inventory']['candidates'])
    assert all(c['color_member_association']['value'] is None for c in r['inventory']['candidates'])

@pytest.mark.parametrize('name,ui,chains',[('E1',3,4),('F',4,1)])
def test_mixed_counts_report_real_disagreement(results,name,ui,chains):
    r=results['samples'][name]
    assert r['count_comparison']['ui_count']==ui
    assert r['inventory']['decoder_chain_count']==chains
    assert r['inventory']['top_level_selection_count']['value'] is None

@pytest.mark.parametrize('name,count',[('polyline_3_points',3),('polyline_5_points',5),('polygon_5_sides',5),('polygon_6_sides',6),('default_circle',8)])
def test_reuses_contour_boundaries_without_promoting_kind(results,name,count):
    r=results['samples'][name]['inventory'];c=r['candidates'][0]
    assert c['record_count']==count and c['kind']['confidence']=='HEURISTIC'
    obs=c['archive_boundary_observation']
    assert obs['native_record_width']==36
    assert obs['native_contour_range']==c['contour_range']['value']
    assert c['object_byte_range']['value'] is None


def test_payload_text_not_counted_again_per_chain(results):
    r=results['samples']['text/default_text']['inventory']
    assert r['payload_text']['value']['text_content']=='abcdefg'
    assert r['payload_text']['confidence']=='HEURISTIC'
    assert r['archive_structure']['status']=='UNSUPPORTED'

@pytest.mark.parametrize('name',['count_out_of_scope','count_stride_extent_truncated','property_truncated','suffix_truncated','unregistered_class_reference','unsupported_schema'])
def test_malformed_refusal_is_bounded_and_has_no_partial_success(results,name):
    r=results['synthetic'][name]['inventory']
    assert r['status']=='UNSUPPORTED' and r['decoder_status']=='NOT_RUN_UNSUPPORTED_STRUCTURE'
    assert not r['candidates'] and r['stop_cursor']>0
    assert not r['execution']['timed_out']


def test_duplicate_contours_remain_two_occurrences(results):
    r=results['synthetic']['duplicate_contour']['inventory']
    assert r['candidate_count']==2
    assert r['candidates'][0]['display_index']!=r['candidates'][1]['display_index']
    assert all(any('DUPLICATE_CONTOUR' in a for a in c['ambiguities']) for c in r['candidates'])
    assert r['boundary_comparison']['overall_status']=='AMBIGUOUS'


def test_removed_tail_is_not_full_archive_verification(results):
    r=results['synthetic']['unknown_tail_removed']['inventory']
    assert r['status']=='PARTIAL' and r['archive_valid_length']=='UNKNOWN'


def test_timeout_kills_only_owned_child_and_returns_no_success():
    r=inv.analyze_bytes(b'',timeout=0.000001)
    assert r['status']=='UNSUPPORTED' and r['execution']['timed_out']
    assert r['execution']['child_pid']>0 and r['execution']['kill_scope']=='owned Python child only'
    assert not r['candidates']


def test_input_sha_and_immutability(results):
    for name,(path,data) in reproduce.fixtures().items():
        assert results['samples'][name]['inventory']['source_sha256']==inv.sha(data)
        assert results['samples'][name]['source_file_sha256']==inv.sha(path.read_bytes())


def test_existing_007_decoder_fingerprints_preserved(results):
    baseline=json.loads((inv.ROOT/'research/archive-boundary-diagnostic-007/sample-diagnostics.json').read_text(encoding='utf-8'))
    for name,old in baseline.items():
        assert old['decoder_fingerprint']==results['samples'][name]['inventory']['decoder_fingerprint']


def test_invalid_timeout_and_input_type():
    with pytest.raises(ValueError):inv.analyze_bytes(b'',timeout=float('nan'))
    with pytest.raises(TypeError):inv.analyze_bytes('not bytes')


def test_file_cli_and_no_overwrite(tmp_path):
    data=reproduce.fixtures()['G1'][1];source=tmp_path/'input.bin';source.write_bytes(data)
    output=tmp_path/'table.txt'
    assert inv.main(['--input',str(source),'--format','table','--output',str(output)])==0
    assert 'UNKNOWN' in output.read_text(encoding='utf-8')
    assert 'not a complete object list' in output.read_text(encoding='utf-8')
    with pytest.raises(SystemExit):inv.main(['--input',str(source),'--output',str(source)])
    assert source.read_bytes()==data


def test_h_bbox_and_color_match_independent_ui_parameter_records(results):
    rows=results['samples']['H1']['inventory']['candidates']
    for row,x,y,w,h,color in [(rows[0],600,200,55,35,'Turquoise'),(rows[1],450,200,30,20,'Navy Blue')]:
        b=row['bbox']['value']
        assert b['xmin_m']*1000 == pytest.approx(x,abs=1e-6)
        assert b['ymin_m']*1000 == pytest.approx(y,abs=1e-6)
        assert (b['xmax_m']-b['xmin_m'])*1000 == pytest.approx(w,abs=1e-6)
        assert (b['ymax_m']-b['ymin_m'])*1000 == pytest.approx(h,abs=1e-6)
        assert row['color']['value']['name']==color
        assert row['color_member_association']['confidence']=='UNKNOWN'


def test_g_bbox_and_colors_match_rounded_ui_display(results):
    rows=results['samples']['G1']['inventory']['candidates']
    for row,w,h,x,y,color in [(rows[0],80.024,60.053,200.678,371.058,'Navy Blue'),(rows[1],176.052,104.092,488.764,349.039,'Turquoise')]:
        b=row['bbox']['value']
        assert (b['xmax_m']-b['xmin_m'])*1000==pytest.approx(w,abs=0.001)
        assert (b['ymax_m']-b['ymin_m'])*1000==pytest.approx(h,abs=0.001)
        assert (b['xmax_m']+b['xmin_m'])*500==pytest.approx(x,abs=0.001)
        assert (b['ymax_m']+b['ymin_m'])*500==pytest.approx(y,abs=0.001)
        assert row['color']['value']['name']==color


def test_mixed_text_candidates_do_not_become_proven_text_objects(results):
    e=results['samples']['E1']['inventory'];f=results['samples']['F']['inventory']
    assert {'T1A','T2B'} <= {row['text']['value'] for row in e['candidates']}
    assert 'T2B' not in {row['text']['value'] for row in f['candidates']}
    assert all(row['top_level_selection']['value'] is None for row in e['candidates'])
