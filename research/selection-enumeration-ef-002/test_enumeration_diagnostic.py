from pathlib import Path
import importlib.util,json,sys
import pytest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('ef002_test_module',HERE/'enumeration-diagnostic.py');diag=importlib.util.module_from_spec(spec);spec.loader.exec_module(diag)

@pytest.fixture(scope='module')
def saved():return json.loads((HERE/'ef-parser-trace.json').read_text(encoding='utf-8'))

@pytest.fixture(scope='module')
def fresh():
 return {n:diag.diagnose_bytes((ROOT/'research/selection-object-inventory-001/samples'/f'{n}.bin').read_bytes()) for n in ['E1','F']}

@pytest.mark.parametrize('name',['E1','F'])
def test_original_capture_and_inventory_copy_have_identical_sha(saved,name):
 r=saved['capture_integrity'][name]
 assert r['equal'] and r['original_zone_sha256']==r['inventory_copy_sha256']
 assert r['zone_length']==12288 and r['whole_archive_valid_length']=='UNKNOWN'

@pytest.mark.parametrize('name',['E1','F'])
def test_fresh_trace_reproduces_saved_pipeline(saved,fresh,name):
 a=saved['samples'][name]['diagnostic'];b=fresh[name]
 assert b['status']=='DIAGNOSTIC_COMPLETE' and not b['trace_truncated']
 for k in ['source_sha256','header','node_candidates','decoder_chains','all_extracted_text_runs','slot_record_findings','diagnostic_contour_probe','decoder_fingerprint']:
  assert a[k]==b[k]
 assert b['decoder_model_unchanged_after_diagnostic'] and not b['execution']['timed_out']


def test_f_missing_t2b_is_already_decoded_before_attachment(fresh):
 r=fresh['F'];assert [x['text'] for x in r['all_extracted_text_runs']]==['T1A','T2B']
 assert len(r['decoder_chains'])==1 and r['decoder_chains'][0]['text_candidate']=='T1A'
 event=next(x for x in r['trace'] if x['function']=='attach_text_runs_to_chains' and x['event']=='return')
 assert len(event['locals']['runs'])==2 and len(event['locals']['chains'])==1 and event['line']==192


def test_f_t2b_is_structured_slot_data_not_an_ascii_search(fresh):
 finding=next(x for x in fresh['F']['slot_record_findings'] if x['decoded_run_candidate']['text']=='T2B')
 assert finding['source_record_windows']==[[4138,4954]]
 assert finding['record_lengths']==[204]*4
 assert finding['reviewed_v5_empty_layout_rejections']==[None]*4
 assert [x['u32'] for x in finding['char_fields']]==[84,50,66,0]
 assert finding['owner']=='UNKNOWN' and finding['object_extent']=='UNKNOWN'


def test_same_extractor_scans_property_tail_only_in_e(fresh):
 for name,count,payload in [('E1',3,[2134,12288]),('F',0,[711,995])]:
  r=fresh[name]
  prop=next(n for n in r['node_candidates'] if n['class']=='CPropertyExtend')
  assert prop['scanner_payload_span']==payload
  e=next(x for x in r['trace'] if x['function']=='_read_embedded_contour_chains' and x['event']=='return')
  assert len(e['return'])==count
  calls=[x for x in r['trace'] if x['event']=='branch' and x['function']=='_process_object_chain']
  assert any(x['node']['class']=='CParagraphe' for x in calls)


def test_diagnostic_probe_recovers_identical_contour_bytes_not_object_ownership(fresh):
 e=fresh['E1'];f=fresh['F'];extra=f['diagnostic_contour_probe'][0]
 assert extra['scanner_payload_span']==[1012,12288]
 assert len(extra['candidate_contours'])==3 and not extra['merged_into_decoder']
 combined=f['decoder_chains']+extra['candidate_contours']
 assert sorted(x['contour_sha256'] for x in combined)==sorted(x['contour_sha256'] for x in e['decoder_chains'])
 assert f['exact_top_level_enumeration'] is False and f['top_level_selection_count']=='UNKNOWN'

@pytest.mark.parametrize('name',['E1','F'])
def test_unreviewed_prefix_does_not_become_supported_shadow(fresh,name):
 r=fresh[name]
 assert r['input_prefix_hex']=='010000004859'
 assert r['header']['declared_count_candidate'] is None and r['header']['envelope_offset']==0
 assert r['shadow']['status']=='UNSUPPORTED' and r['shadow']['reason']=='unreviewed prefix'
 assert not r['complete_inventory'] and r['group_hierarchy']=='UNKNOWN' and not r['change_allowed']


def test_previous_inventory_reports_exactly_unchanged(saved):
 inv=diag.load_inventory()
 sys.path.insert(0,str(ROOT/'research/selection-object-inventory-001'))
 import reproduce_inventory
 old=json.loads((ROOT/'research/selection-object-inventory-001/inventory-results.json').read_text(encoding='utf-8'))
 for name,(_path,data) in reproduce_inventory.fixtures().items():
  new=inv.analyze_bytes(data);baseline=old['samples'][name]['inventory']
  assert {k:v for k,v in new.items() if k!='execution'}=={k:v for k,v in baseline.items() if k!='execution'}
  assert saved['samples'][name]['diagnostic']['decoder_fingerprint']==new['decoder_fingerprint']


def test_same_text_is_not_used_as_object_identity(fresh):
 data=bytearray((ROOT/'research/selection-object-inventory-001/samples/F.bin').read_bytes())
 second=next(x for x in fresh['F']['slot_record_findings'] if x['decoded_run_candidate']['text']=='T2B')['source_record_windows'][0][0]
 data[second+204+4:second+204+8]=(49).to_bytes(4,'little')
 data[second+408+4:second+408+8]=(65).to_bytes(4,'little')
 r=diag.diagnose_bytes(bytes(data))
 assert [x['decoded_run_candidate']['text'] for x in r['slot_record_findings']]==['T1A','T1A']
 assert len(r['all_extracted_text_runs'])==1 # existing content dedup, not a real object count
 assert r['top_level_selection_count']=='UNKNOWN'


def test_existing_duplicate_contours_are_not_merged(saved):
 r=saved['synthetic']['duplicate_contour']['diagnostic']
 assert len(r['decoder_chains'])==2
 assert r['decoder_chains'][0]['contour_sha256']==r['decoder_chains'][1]['contour_sha256']
 assert r['decoder_chains'][0]['contour_range']!=r['decoder_chains'][1]['contour_range']

@pytest.mark.parametrize('name',['count_out_of_scope','count_stride_extent_truncated','property_truncated','suffix_truncated','unregistered_class_reference','unsupported_schema'])
def test_malformed_known_prefix_has_no_successful_graph(saved,name):
 r=saved['synthetic'][name]['diagnostic']
 assert r['status']=='UNSUPPORTED' and 'decoder_chains' not in r
 assert not r['execution']['timed_out'] and not r['exact_top_level_enumeration']


def test_deadline_discards_worker_result():
 r=diag.diagnose_bytes(b'',timeout=0.000001)
 assert r['status']=='UNSUPPORTED' and r['execution']['timed_out']
 assert r['execution']['kill_scope']=='owned Python child only' and not r['exact_top_level_enumeration']
