import sys,json,hashlib,struct,importlib.util,dataclasses
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('prior006',ROOT/'research/archive-crosswalk-002/analyse_fixtures.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser
from type3_clipboard_codec.parsers.text_parser import TextParser
from type3_clipboard_codec.utils.bytes_reader import BytesReader

def sha(data):return hashlib.sha256(data).hexdigest()
def fixtures():
 group=a.prior.GROUP
 paths={'G1':group/'type3-clipboard-member-color-003/samples/G1/typeeditzone.bin','H1':group/'type3-clipboard-independent-prediction-006/samples/H1/typeeditzone.bin'}
 for n in a.FIXTURES:paths[n]=ROOT/'tests/samples'/f'{n}.txt'
 return {n:(p,a.hex_to_bytes(p.read_text(encoding='utf-8-sig')) if p.suffix=='.txt' else p.read_bytes()) for n,p in paths.items()}

def shadow(data):
 r=a.prior.Reader(data)
 result={'input_sha256':sha(data),'input_length':len(data),'prefix_hex':data[:6].hex(),'prefix_condition':'000000000100','initial_map':'CONDITIONAL: fresh unseeded at byte6; IDs are archive-local only','ownership':'UNKNOWN; tree edges are serialization helper/field edges, not proven UI ownership','change_allowed':False}
 if data[:6]!=bytes.fromhex('000000000100'):return {**result,'status':'UNSUPPORTED','stop_cursor':0,'reason':'unreviewed prefix','unknown_ranges':[[0,len(data)]]}
 try:
  tree=r.obj()
  return {**result,'status':'CONDITIONAL_MATCH','consumed_range':[6,r.pos],'prefix_observed_range':[0,6],'stop_cursor':r.pos,'tree':tree,'events':r.events,'properties':r.properties,'colors':r.colors,'unknown_ranges':[[r.pos,len(data)]] if r.pos<len(data) else [],'full_valid_length':'UNKNOWN'}
 except (ValueError,UnicodeDecodeError,IndexError,struct.error) as e:
  return {**result,'status':'UNSUPPORTED','stop_cursor':r.pos,'reason':str(e),'partial_events_diagnostic_only':r.events,'unknown_ranges':[[6,len(data)]],'partial_result_usable':False}

def compare(name,data):
 s=shadow(data);decoded,parser=a.Decoder().decode_bytes_with_parser(data)
 chains=getattr(decoded,'object_chains',[])
 envelope_offset=Type3ChainParser()._read_top_level_header(data)[2]
 d={'parser':parser,'object_type':decoded.object_type,'is_text_object':getattr(decoded,'is_text_object',None),'text_content':getattr(decoded,'text_content',None),'declared_object_count_candidate':getattr(decoded,'declared_object_count',None),'is_grouped_candidate':getattr(decoded,'is_grouped',None),'chain_count':len(chains),'envelope_payload_offset':envelope_offset,'offset_coordinate_note':'Codec stream/style offsets are relative to envelope payload; source_payload_offset is node-local','nodes':getattr(decoded,'candidate_fields',{}).get('node_markers_with_offsets',[]),'chains':[]}
 for i,c in enumerate(chains):
  d['chains'].append({'index':i,'contour_sha256':sha(c.raw_contour_bytes),'contour_length':len(c.raw_contour_bytes),'record_count':len(c.contour_records),'source_stream_offset':c.source_stream_offset,'source_payload_offset':c.source_payload_offset,'shape_type':c.shape_type,'bbox':dataclasses.asdict(c.bbox) if c.bbox else None,'style':dataclasses.asdict(c.style),'header_diagnostics':c.contour_header_diagnostics})
 matches=[]
 if s['status']=='CONDITIONAL_MATCH':
  for node in a.nodes(s['tree']):
   if node['class']!='CContour':continue
   span=node['point_records']['span'];raw=data[span[0]:span[1]]
   ids=[i for i,c in enumerate(chains) if c.raw_contour_bytes==raw]
   suffix=next((x for x in s['colors'] if x['suffix_span'][0]==node['body_end']),None)
   idsafe=ids[0] if len(ids)==1 else None
   style=chains[idsafe].style if idsafe is not None else None
   expected=int.from_bytes(data[suffix['b8_range'][0]:suffix['b8_range'][1]],'little') if suffix else None
   matches.append({'contour_span':span,'count':node['point_records']['count'],'width':36,'codec_absolute_contour_span':[envelope_offset+chains[idsafe].source_stream_offset,envelope_offset+chains[idsafe].source_stream_offset+len(raw)] if idsafe is not None else None,'unique_codec_chain':idsafe,'matching_chain_indices':ids,'byte_equal':bool(ids),'suffix_follows_contour_end':suffix is not None,'native_color_raw':expected,'codec_selected_color_raw':style.line_color_selected_raw if style else None,'selected_color_equal':style.line_color_selected_raw==expected if style else None,'property_payload_span_codec':[envelope_offset+style.property_extend_payload_offset,envelope_offset+style.property_extend_payload_offset+style.property_extend_payload_length] if style and style.property_extend_payload_offset is not None else None,'native_property_body_span':node['children'][-1].get('body_start') and [node['children'][-1]['body_start'],node['children'][-1]['body_end']]})
 if name=='text/default_text':
  tr=TextParser().parse(BytesReader(data));d['direct_TextParser']={'object_type':tr.object_type,'text_content':tr.text_content,'notes':tr.notes}
 return {'name':name,'shadow':s,'codec':d,'comparisons':matches}

def synthetic(data):
 baseline=shadow(data);contour=next(n for n in a.nodes(baseline['tree']) if n['class']=='CContour');start,end=contour['point_records']['span'];cases=[]
 def run(name,b):
  r=shadow(b);cases.append({'name':name,'source':'SYNTHETIC_MEMORY_INPUT_NOT_TYPE3_SAMPLE','length':len(b),'result':r});return r
 for val in (0,101,0xffffffff,contour['point_records']['count']+1):
  b=bytearray(data);struct.pack_into('<I',b,start-4,val);run('count_'+str(val),bytes(b))
 for label,pos in [('descriptor',10),('contour',end-1),('property',baseline['properties'][0]['body'][1]-1),('suffix',baseline['colors'][0]['suffix_span'][1]-1)]:run('truncated_'+label,data[:pos])
 refs=[e for e in baseline['events'] if e['kind']=='class_reference']
 if refs:
  b=bytearray(data);struct.pack_into('<H',b,refs[0]['span'][0],0x8ffe);run('unknown_class_reference',bytes(b))
 b=bytearray(data);struct.pack_into('<H',b,6,0);run('null_object_reference',bytes(b))
 run('tail_removed',data[:baseline['stop_cursor']])
 return cases

def snapshot():
 paths=[]
 for root in ['src','tests','research/archive-crosswalk-001','research/archive-crosswalk-002','research/archive-copy-runtime-004','research/archive-producer-crosswalk-005','research/group-color']:
  paths.extend(p for p in (ROOT/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
 return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(set(paths))}
def run(out):
 before=snapshot();items=fixtures();report={n:{**compare(n,data),'source_file':str(p.relative_to(ROOT)),'source_file_sha256':sha(p.read_bytes())} for n,(p,data) in items.items()}
 tests=synthetic(items['G1'][1]);after=snapshot();assert before==after
 out.mkdir(exist_ok=True)
 (out/'crosswalk-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'synthetic-results.json').write_text(json.dumps(tests,ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'preservation.json').write_text(json.dumps({'file_count':len(before),'changed':[],'hashes':before},indent=2),encoding='utf-8')
 for n,r in report.items():print(n,r['shadow']['status'],r['shadow']['stop_cursor'],r['codec']['chain_count'],[(m['byte_equal'],m['selected_color_equal']) for m in r['comparisons']])
 for t in tests:print(t['name'],t['result']['status'],t['result'].get('reason','tail UNKNOWN'))
 return report,tests
if __name__=='__main__':run(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent)
