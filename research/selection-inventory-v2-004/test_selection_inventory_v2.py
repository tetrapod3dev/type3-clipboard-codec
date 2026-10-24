from pathlib import Path
import json,sys,subprocess,copy
import pytest
import selection_inventory_v2 as v2
import reproduce_v2 as replay
HERE=Path(__file__).resolve().parent

@pytest.fixture(scope='module')
def results():return json.loads((HERE/'v2-sample-results.json').read_text(encoding='utf8'))

@pytest.fixture(scope='module')
def counts():return json.loads((HERE/'selection-count-evidence.json').read_text(encoding='utf8'))

@pytest.mark.parametrize('name',['E1','F','G1','H1','default_rectangle','default_circle','polyline_3_points','text/default_text','text_three_objects_grouped_order_abc','text_three_objects_not_grouped'])
def test_unknown_ownership_and_exact_count_are_not_promoted(results,name):
 r=results['samples'][name]['inventory']
 assert r['status']=='PARTIAL'
 assert r['selection_summary']['top_level_selection_count']=='UNKNOWN'
 assert not any(r[k] for k in ['exact_top_level_enumeration','group_membership_verified','complete_inventory','production_change_allowed'])
 assert all(x['owner']=='UNKNOWN' for x in r['geometry_occurrences']+r['text_occurrences'])
 assert not r['execution']['timed_out']

@pytest.mark.parametrize('name',['E1','F'])
def test_text_runs_and_four_contour_occurrences_recovered(results,name):
 r=results['samples'][name]['inventory']
 assert {t['text_candidate'] for t in r['text_occurrences']}=={'T1A','T2B'}
 assert len(r['geometry_occurrences'])==4
 assert r['research_probe_status']=='EXACT_EF_PROFILE_REUSED'


def test_f_t2b_was_not_exposed_by_legacy_chain(results):
 rows=results['samples']['F']['inventory']['text_occurrences']
 a=next(x for x in rows if x['text_candidate']=='T1A');b=next(x for x in rows if x['text_candidate']=='T2B')
 assert a['range']==[1322,2138] and b['range']==[4138,4954]
 assert a['exposed_by_legacy_chain_text'] and not b['exposed_by_legacy_chain_text']
 assert [x['u32'] for x in b['char_dwords']]==[84,50,66,0]
 assert b['layout_validation']==[None]*4 and not b['chain_ownership_verified']


def test_ef_raw_contour_crosswalk_and_inclusion_distinction(results):
 a=results['samples']['E1']['inventory']['geometry_occurrences'];b=results['samples']['F']['inventory']['geometry_occurrences']
 assert sorted(x['raw_sha256'] for x in a)==sorted(x['raw_sha256'] for x in b)
 assert sum(x['decoder_chain_included'] for x in a)==4
 assert sum(x['decoder_chain_included'] for x in b)==1
 assert all(x['source']=='EXACT_EF_RESEARCH_PROBE_002' for x in b if not x['decoder_chain_included'])

@pytest.mark.parametrize('name',['G1','H1'])
def test_g_h_values_and_old_boundaries_preserved(results,name):
 old=json.loads((v2.ROOT/'research/selection-object-inventory-001/inventory-results.json').read_text(encoding='utf8'))['samples'][name]['inventory']
 new=results['samples'][name]['inventory']
 assert new['research_probe_status']=='NOT_APPLIED_OUTSIDE_EXACT_EF_PROFILE'
 assert len(new['geometry_occurrences'])==2
 for row,c in zip(new['geometry_occurrences'],old['candidates']):
  assert row['records']==c['records'] and row['bbox_candidate']==c['bbox'] and row['color_candidate']==c['color']
  assert row['boundary_observation']==c.get('archive_boundary_observation')


def test_old001_fingerprints_remain_equal(results):
 old=json.loads((v2.ROOT/'research/selection-object-inventory-001/inventory-results.json').read_text(encoding='utf8'))
 for name,r in old['samples'].items():assert r['inventory']['decoder_fingerprint']==results['samples'][name]['inventory']['legacy001']['decoder_fingerprint']


def test_same_text_separate_windows_are_separate_occurrences(results):
 r=results['synthetic']['same_text_distinct_windows']['inventory']
 assert [x['text_candidate'] for x in r['text_occurrences']]==['T1A','T1A']
 assert r['text_occurrences'][0]['range']!=r['text_occurrences'][1]['range']
 assert all(x['duplicate_content_observed'] for x in r['text_occurrences'])
 assert r['research_probe_status']=='NOT_APPLIED_OUTSIDE_EXACT_EF_PROFILE'
 assert r['selection_summary']['top_level_selection_count']=='UNKNOWN'


def test_duplicate_contour_data_keeps_distinct_positions(results):
 r=results['synthetic']['duplicate_contour']['inventory'];rows=r['geometry_occurrences']
 assert len(rows)==2 and rows[0]['raw_sha256']==rows[1]['raw_sha256'] and rows[0]['range']!=rows[1]['range']
 assert rows[0]['equal_raw_at_other_ranges']==[rows[1]['range']]

@pytest.mark.parametrize('name',['count_out_of_scope','count_stride_extent_truncated','property_truncated','suffix_truncated','unregistered_class_reference','unsupported_schema','unknown_bytes','empty'])
def test_unsupported_input_does_not_claim_empty_selection(results,name):
 r=results['synthetic'][name]['inventory']
 assert r['status']=='UNSUPPORTED' and not r['geometry_occurrences'] and not r['text_occurrences']
 assert r['empty_lists_do_not_prove_absence'] and r['selection_summary']['top_level_selection_count']=='UNKNOWN'
 assert not r['execution']['timed_out']


def test_count_font2_does_not_assume_offset70(results):
 r=results['samples']['text_two_objects_mixed_color_not_grouped']['inventory']['selection_summary']['count_evidence']
 assert r['font_count_candidate']==2 and r['count_range']==[132,134] and r['first_descriptor_candidate']==[134,145]
 assert len(r['entries'])==2 and r['confidence']=='HEURISTIC'


def test_independent_count_evidence_is_not_derived_from_chains(counts):
 assert counts['count_candidate_status']=='COUNT_CANDIDATE_CONDITIONAL'
 qualified=[r for r in counts['rows'].values() if r['new_independent_validation']]
 assert len(qualified)>=6 and all(r['value_validation']=='MATCH' for r in qualified)
 assert not counts['producer_contract_verified']
 # Literal grouped3 metadata is not accepted as top-level3 and not silently corrected to1.
 r=counts['rows']['text_three_objects_grouped_order_abc_font_arial_bold']
 assert r['ui_top_level_count'] is None and r['value_validation']=='NOT_ESTABLISHED'
 assert r['candidate']['value']==1 and r['metadata_only']


def test_real_count_contradiction_would_be_recorded_without_correction():
 items=replay.corpus();p,data=items['U0'];changed=bytearray(data);rng=v2.count_candidate(data)['count_range']
 changed[rng[0]:rng[1]]=(7).to_bytes(2,'little')
 r=replay.count_evidence({'U0':(p,bytes(changed))}) # Synthetic reporting seam, never written to real corpus.
 assert r['count_candidate_status']=='COUNT_CANDIDATE_CONTRADICTED'
 assert r['rows']['U0']['value_validation']=='CONTRADICTED'
 assert r['rows']['U0']['candidate']['value']==7


def test_count_not_used_as_geometry_loop_bound():
 p,data=replay.corpus()['U0'];changed=bytearray(data);rng=v2.count_candidate(data)['count_range']
 changed[rng[0]:rng[1]]=(30000).to_bytes(2,'little')
 r=v2.analyze_bytes(bytes(changed))
 assert r['selection_summary']['top_level_selection_count_candidate']==30000
 assert len(r['geometry_occurrences'])==2 and r['selection_summary']['top_level_selection_count']=='UNKNOWN'


def test_admission_and_timeout():
 assert v2.analyze_bytes(b'x'*(v2.MAX_INPUT+1))['status']=='UNSUPPORTED'
 with pytest.raises(ValueError):v2.analyze_bytes(b'',timeout=float('inf'))
 r=v2.analyze_bytes(b'',timeout=0.000001)
 assert r['status']=='UNSUPPORTED' and r['execution']['timed_out'] and r['execution']['kill_scope']=='owned Python child only'


def test_output_candidate_bound_refuses_partial_success():
 p,data=replay.corpus()['G1']
 old=json.loads((v2.ROOT/'research/selection-object-inventory-001/inventory-results.json').read_text(encoding='utf8'))['samples']['G1']['inventory']
 fake=copy.deepcopy(old);fake['candidates'][0]['record_count']=v2.MAX_RECORDS+1
 r=v2.normalize(data,fake,None,[],[],[])
 assert r['status']=='UNSUPPORTED' and not r['geometry_occurrences']


def test_cli_default_stdout_and_explicit_output_no_overwrite(tmp_path):
 p,data=replay.corpus()['F'];source=tmp_path/'f.bin';source.write_bytes(data)
 command=[sys._base_executable,'-B',str(HERE/'selection_inventory_v2.py'),'--input',str(source),'--format','table']
 result=subprocess.run(command,capture_output=True,timeout=20)
 assert result.returncode==0
 text=result.stdout.decode('utf8');assert 'T2B' in text and '선택 수 후보: 4' in text
 assert list(tmp_path.iterdir())==[source]
 dest=tmp_path/'out.json'
 assert v2.main(['--input',str(source),'--output',str(dest)])==0
 assert json.loads(dest.read_text(encoding='utf8'))['schema_version']==2
 with pytest.raises(SystemExit):v2.main(['--input',str(source),'--output',str(source)])
 assert source.read_bytes()==data
