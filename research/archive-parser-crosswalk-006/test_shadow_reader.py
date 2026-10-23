"""Saved-file boundary comparisons and synthetic rejection; never invokes Type3."""
import struct
import pytest
import shadow_reader as s
from type3_clipboard_codec.parsers.common import read_contour_points, read_object_header
from type3_clipboard_codec.parsers.geometry.contour_parser import read_contour_records
from type3_clipboard_codec.parsers.geometry.contour_candidate_validator import validate_contour_header_candidate

@pytest.fixture(scope='module')
def inputs():return s.fixtures()

@pytest.mark.parametrize('name',['G1','H1','polyline_3_points','polyline_5_points','polygon_5_sides','polygon_6_sides','default_circle'])
def test_unique_contour_and_color_comparison(inputs,name):
 data=inputs[name][1];r=s.compare(name,data)
 assert r['shadow']['status']=='CONDITIONAL_MATCH'
 assert len(r['comparisons'])==len(r['codec']['chains'])
 for m in r['comparisons']:
  assert m['byte_equal'] and m['unique_codec_chain'] is not None
  assert m['contour_span']==m['codec_absolute_contour_span']
  assert m['count']*36==m['contour_span'][1]-m['contour_span'][0]
  assert m['selected_color_equal'] and m['suffix_follows_contour_end']
 assert not r['shadow']['change_allowed']

@pytest.mark.parametrize('name',['G1','H1'])
def test_shared_codec_candidate_window_is_not_member_ownership(inputs,name):
 r=s.compare(name,inputs[name][1]);m=r['comparisons']
 assert m[0]['property_payload_span_codec']==m[1]['property_payload_span_codec']
 assert m[0]['native_property_body_span']!=m[1]['native_property_body_span']
 assert m[0]['property_payload_span_codec'][1]==len(inputs[name][1])

@pytest.mark.parametrize('case',range(10))
def test_synthetic_corrupt_input_rejects_without_success_tree(inputs,case):
 original=inputs['G1'][1];before=s.sha(original);r=s.synthetic(original)[case]['result']
 assert r['status']=='UNSUPPORTED' and 'tree' not in r
 assert not r['change_allowed'] and not r.get('partial_result_usable',True)
 assert s.sha(original)==before

def test_tail_removal_does_not_certify_valid_length(inputs):
 data=inputs['G1'][1];original=s.shadow(data);trim=s.shadow(data[:original['stop_cursor']])
 assert trim['status']=='CONDITIONAL_MATCH'
 assert trim['full_valid_length']=='UNKNOWN' and trim['unknown_ranges']==[]
 assert original['tree']==trim['tree']

def test_text_rejection_is_only_shadow_scope(inputs):
 r=s.compare('text/default_text',inputs['text/default_text'][1])
 assert r['shadow']['status']=='UNSUPPORTED' and r['shadow']['stop_cursor']==0
 assert r['codec']['parser']=='Type3ChainParser'
 assert r['codec']['object_type']=='text' and r['codec']['text_content']=='abcdefg'
 assert r['codec']['direct_TextParser']['text_content']!='abcdefg'

def test_existing_validator_already_checks_count_stride_and_extent(inputs):
 data=inputs['polyline_5_points'][1];r=s.shadow(data)
 node=next(n for n in s.a.nodes(r['tree']) if n['class']=='CContour');a,b=node['point_records']['span']
 good=validate_contour_header_candidate(payload=data,header_offset=a-8,stride=36,bbox=None,max_safe_contour_count=4096)
 assert good['structural_valid'] and good['record_region_end_offset']==b and good['decoded_record_count']==5
 bad=validate_contour_header_candidate(payload=data[:b-1],header_offset=a-8,stride=36,bbox=None,max_safe_contour_count=4096)
 assert not bad['structural_valid'] and 'record_region_out_of_bounds' in bad['structural_failure_reasons']

def test_schema_word_is_not_archive_class_id(inputs):
 data=inputs['G1'][1];r=s.shadow(data)
 for e in r['events']:
  if e['kind']!='new_class':continue
  header=read_object_header(s.BytesReader(data[e['span'][0]:]))
  assert header.class_id==e['schema']
 # CPropertyExtend schema5 versus conditional Archive class ID8.
 p=next(e for e in r['events'] if e.get('class')=='CPropertyExtend' and e['kind']=='new_class')
 assert p['schema']==5 and p['class_id']==8

def test_low_level_missing_tag_fallback_is_not_a_strict_reader():
 # Synthetic 32B vector lacks the final 4B tag; high-level extent guards reject it.
 data=struct.pack('<4d',1.,2.,0.,1.);reader=s.BytesReader(data)
 assert read_contour_points(reader,1)[0].tag==0 and reader.tell()==36
 assert read_contour_records(data,0,1,36)==[]
