"""Saved-file Selection Inventory V2: occurrences, never a complete object list."""
from __future__ import annotations
import argparse
import importlib.util
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
MAX_INPUT=1024*1024
MAX_OCCURRENCES=256
MAX_RECORDS=4096
MAX_FONTS=32
MAX_JSON=8*1024*1024
EF_PROBE_HASHES=frozenset(['9957013e159914f0df2c4ccc21238c5708c440e7ff4a376c08e03351d69095c2','e481935f07e9986cecd827b95c3e10a2920718f660f9872e6318690c33c4e743'])


def sha(data):return hashlib.sha256(data).hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def dependencies():
    one=load('inventory_v2_original001',ROOT/'research/selection-object-inventory-001/selection_inventory.py')
    two=load('inventory_v2_original002',ROOT/'research/selection-enumeration-ef-002/enumeration-diagnostic.py')
    return one,two


def count_candidate(data):
    """Bounded hypothesis check only. Never used to split objects or drive decoding."""
    result={'value':None,'confidence':'UNKNOWN','status':'COUNT_CANDIDATE_UNKNOWN','applicability':'NOT_APPLICABLE',
            'reason':'Unrecognized or truncated preamble hypothesis','producer_contract_verified':False,
            'font_count_candidate':None,'entries':[],'count_range':None,'first_descriptor_candidate':None,
            'not_an_object_loop_bound':True}
    if len(data)<6:return result
    n=int.from_bytes(data[:4],'little')
    if n>MAX_FONTS:
        result['reason']='Font-entry hypothesis exceeds admission bound';return result
    offset=4+64*n
    if offset+13>len(data):return result
    # Require exactly the already reviewed CZone descriptor pattern at the calculated position.
    # This does not authorize a fresh MFC map or identify an object start.
    if data[offset+2:offset+13]!=bytes.fromhex('ffff01000500')+b'CZone':
        result['reason']='Calculated position is not the reviewed CZone descriptor';return result
    family='TEXT_FONT64_PREAMBLE_CANDIDATE' if n else 'GEOMETRY_N0_PREAMBLE_CANDIDATE'
    result.update(value=int.from_bytes(data[offset:offset+2],'little'),confidence='HEURISTIC',
                  status='COUNT_CANDIDATE_CONDITIONAL',applicability=family,
                  reason='Observed DWORD/64-byte entries/WORD relation; no producer contract or exact selected-object validation',
                  font_count_candidate=n,count_range=[offset,offset+2],first_descriptor_candidate=[offset+2,offset+13])
    for index in range(n):
        start=4+64*index;raw=data[start:start+64];name=raw.split(b'\0',1)[0]
        result['entries'].append({'range':[start,start+64],'raw_sha256':sha(raw),'raw_hex':raw.hex(),
                                  'font_name_bytes_candidate':name.hex(),'ascii_name_candidate':name.decode('ascii') if name.isascii() else None,
                                  'nul_byte_count':raw.count(0),'role_confidence':'HEURISTIC'})
    return result


def empty(data,status,reason):
    return {'schema_version':2,'status':status,'source_sha256':sha(data),'input_format':'SAVED_TYPEEDITZONE_BINARY','input_length':len(data),
        'selection_summary':{'top_level_selection_count':'UNKNOWN','top_level_selection_count_candidate':None,'count_candidate_status':'COUNT_CANDIDATE_UNKNOWN',
                             'exact_selection_count_verified':False,'complete_inventory':False},
        'geometry_occurrences':[],'text_occurrences':[],
        'geometry_search_status':'UNKNOWN','text_search_status':'UNKNOWN','empty_lists_do_not_prove_absence':True,
        'unknowns':{'archive_valid_length':'UNKNOWN','object_serialize_body_ranges':'UNKNOWN','archive_class_object_map':'UNKNOWN',
                    'group_member_ownership':'UNKNOWN','top_level_object_list':'UNKNOWN'},
        'exact_top_level_enumeration':False,'group_membership_verified':False,'complete_inventory':False,'production_change_allowed':False,
        'change_allowed':False,'reason':reason,'occurrence_id_scope':'Display evidence ID within this capture only, not TypeEdit persistent object identity'}


def normalize(data,legacy,ef,slot_findings,text_runs,extra_enriched):
    report=empty(data,'PARTIAL','Supported occurrences only; full objects and ownership UNKNOWN')
    count=count_candidate(data)
    report['selection_summary'].update(top_level_selection_count_candidate=count['value'],count_candidate_status=count['status'],
        count_candidate_confidence=count['confidence'],count_candidate_family=count['applicability'],count_evidence=count)
    report['legacy001']={'status':legacy['status'],'parser_name':legacy.get('parser_name'),'decoder_fingerprint':legacy.get('decoder_fingerprint'),
        'payload_text':legacy.get('payload_text'),'decoder_model_unchanged':legacy.get('decoder_model_unchanged')}
    if legacy.get('decoder_status')!='COMPLETED':
        report.update(status='UNSUPPORTED',reason=legacy.get('stop_reason',legacy.get('reason','Existing001 refused input')))
        return report
    geometries=[]
    for c in legacy['candidates']:
        span=c.get('contour_range',{}).get('value')
        if not span:continue
        geometries.append({'occurrence_id':f'geometry-{len(geometries)}','range':span,'raw_sha256':c['contour_sha256'],
            'record_count':c['record_count'],'records':c['records'],'bbox_candidate':c['bbox'],'shape_candidate':c['kind'],
            'color_candidate':c['color'],'color_ownership':'UNKNOWN','owner':'UNKNOWN','source':'DECODER_CHAIN',
            'decoder_chain_included':True,'decoder_chain_index':c['display_index'],
            'boundary_observation':c.get('archive_boundary_observation'),'confidence':'HEURISTIC'})
    for extra in extra_enriched:
        geometries.append({'occurrence_id':f'geometry-{len(geometries)}',**extra,'source':'EXACT_EF_RESEARCH_PROBE_002',
                           'decoder_chain_included':False,'owner':'UNKNOWN','confidence':'HEURISTIC','color_candidate':None})
    if len(geometries)>MAX_OCCURRENCES or sum(g['record_count'] for g in geometries)>MAX_RECORDS:
        return empty(data,'UNSUPPORTED','Output geometry/record admission bound exceeded; no truncated success')
    for g in geometries:
        g['equal_raw_at_other_ranges']=[x['range'] for x in geometries if x['raw_sha256']==g['raw_sha256'] and x['range']!=g['range']]
        g['same_range_observation_ids']=[x['occurrence_id'] for x in geometries if x['range']==g['range'] and x is not g]
    texts=[]
    for finding in slot_findings:
        for span in finding['source_record_windows']:
            # Same physical record window may be returned repeatedly by the old search.
            # Coalesce duplicate observations of that exact byte range, never equal text at different ranges.
            if any(t['range']==span for t in texts):continue
            record_raw=data[span[0]:span[1]]
            text=finding['decoded_run_candidate']['text']
            indices=[c['display_index'] for c in legacy['candidates'] if c.get('text',{}).get('value')==text]
            texts.append({'occurrence_id':f'text-{len(texts)}','range':span,'raw_sha256':sha(record_raw),'text_candidate':text,
                'record_count':len(finding['record_lengths']),'record_lengths':finding['record_lengths'],
                'char_dwords':finding['char_fields'],'layout_validation':finding['reviewed_v5_empty_layout_rejections'],
                'source':'EXISTING_002_SLOT_RECORD_READER','confidence':'HEURISTIC','owner':'UNKNOWN',
                'legacy_chain_equal_text_indices':indices,'exposed_by_legacy_chain_text':bool(indices),
                'chain_ownership_verified':False,'chain_link_basis':'Equal text in existing output only; not occurrence-to-object identity',
                'object_body_range':'UNKNOWN'})
    if len(texts)>MAX_OCCURRENCES or sum(t['record_count'] for t in texts)>MAX_RECORDS:
        return empty(data,'UNSUPPORTED','Output text/record admission bound exceeded; no truncated success')
    for t in texts:
        t['equal_text_other_occurrence_ids']=[x['occurrence_id'] for x in texts if x is not t and x['text_candidate']==t['text_candidate']]
        t['duplicate_content_observed']=bool(t['equal_text_other_occurrence_ids'])
    report.update(geometry_occurrences=geometries,text_occurrences=texts,legacy_all_extracted_text_runs=text_runs,
                  geometry_search_status='SUPPORTED_CANDIDATES_FOUND' if geometries else 'UNKNOWN_NO_CANDIDATES',
                  text_search_status='SUPPORTED_SLOT_CANDIDATES_FOUND' if texts else 'UNKNOWN_NO_CANDIDATES',
                  research_probe_status='EXACT_EF_PROFILE_REUSED' if ef else 'NOT_APPLIED_OUTSIDE_EXACT_EF_PROFILE')
    if not geometries and not texts:report.update(status='UNSUPPORTED',reason='No supported occurrences; object absence not established')
    return report


def _worker(data):
    one,two=dependencies()
    legacy=one._decode_worker(data)  # Already inside the single owned V2 child.
    if legacy.get('decoder_status')!='COMPLETED':return normalize(data,legacy,None,[],[],[])
    ef=two._worker(data) if sha(data) in EF_PROBE_HASHES else None
    if ef and (ef['status']!='DIAGNOSTIC_COMPLETE' or ef['decoder_fingerprint']!=legacy['decoder_fingerprint']):
        return empty(data,'UNSUPPORTED','Existing002 did not agree with001; discard partial result')
    sys.path.insert(0,str(ROOT/'src'))
    from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser
    from type3_clipboard_codec.parsers.text.cparagraphe_parser import read_slot_record_runs_from_blob,records_to_text_run,extract_text_runs
    from type3_clipboard_codec.parsers.text.text_slot_candidate import _validate_current_empty_slot_layout
    from type3_clipboard_codec.parsers.geometry.shape_classifier import bbox_from_contour_records,classify_shape_with_evidence
    parser=Type3ChainParser();envelope=parser._read_top_level_header(data)[2]
    if ef:
        slots=ef['slot_record_findings'];runs=ef['all_extracted_text_runs']
    else:
        # Same underlying read-only helpers as002, without invoking its CParagraphe probe.
        nodes=parser._extract_nodes(data[envelope:]);runs,_,_=extract_text_runs(nodes);slots=[]
        for index,records in enumerate(read_slot_record_runs_from_blob(data)):
            raw=b''.join(records);run=records_to_text_run(records)
            if run is None:continue
            positions=[];offset=0
            while raw:
                offset=data.find(raw,offset)
                if offset<0:break
                positions.append([offset,offset+len(raw)]);offset+=1
                if len(positions)>MAX_OCCURRENCES:raise ValueError('slot occurrence bound')
            slots.append({'finding_index':index,'decoded_run_candidate':run,'source_record_windows':positions,
                'record_lengths':[len(x) for x in records],'reviewed_v5_empty_layout_rejections':[_validate_current_empty_slot_layout(x) for x in records],
                'char_fields':[{'record_index':i,'offset_in_record':4,'raw_hex':x[4:8].hex(),'u32':int.from_bytes(x[4:8],'little')} for i,x in enumerate(records)]})
            if len(slots)>MAX_OCCURRENCES:raise ValueError('slot finding bound')
    extra=[]
    if ef:
        for probe in ef['diagnostic_contour_probe']:
            for candidate in probe['candidate_contours']:
                a,b=candidate['contour_range'];a+=envelope;b+=envelope
                raw=data[a:b];count=candidate['record_count']
                if not (0<=a<b<=len(data)) or len(raw)!=count*36:raise ValueError('existing probe range mismatch')
                records=parser._read_contour_records(raw,0,count);parser._assign_semantic_roles(records)
                bbox=bbox_from_contour_records(records)
                extra.append({'range':[a,b],'raw_sha256':sha(raw),'record_count':count,
                              'records':one.field(one.clean(records),'HEURISTIC','Existing record reader at the002 probe range'),
                              'bbox_candidate':one.field(one.clean(bbox),'HEURISTIC','Existing bbox helper'),
                              'shape_candidate':one.field(classify_shape_with_evidence(records,bbox)['shape_type'],'HEURISTIC','Existing classifier, not object type')})
    return one.clean(normalize(data,legacy,ef,slots,runs,extra))


def analyze_bytes(data,*,timeout=15):
    if not isinstance(data,bytes):raise TypeError('bytes required')
    if not math.isfinite(timeout) or not (0<timeout<=60):raise ValueError('timeout must be positive, finite and <=60 seconds')
    if len(data)>MAX_INPUT:return empty(data,'UNSUPPORTED','Input exceeds1MiB diagnostic admission limit')
    p=subprocess.Popen([sys._base_executable,'-B',str(Path(__file__).resolve()),'--worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    timed_out=False;started=time.monotonic()
    try:stdout,stderr=p.communicate(data,timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True;p.kill();stdout,stderr=p.communicate(timeout=5)
    try:
        if timed_out or p.returncode or len(stdout)>MAX_JSON:raise ValueError('incomplete worker')
        report=json.loads(stdout)
        if report.pop('_pid')!=p.pid or report['source_sha256']!=sha(data):raise ValueError('identity mismatch')
    except (ValueError,KeyError,TypeError):
        report=empty(data,'UNSUPPORTED','Owned child failed/timed out or exceeded output bound; partial result discarded')
    report['execution']={'child_pid':p.pid,'timed_out':timed_out,'returncode':p.returncode,'elapsed_seconds':time.monotonic()-started,
                         'kill_scope':'owned Python child only' if timed_out else 'none'}
    return report


def render_table(report):
    def cell(x):return str(x).replace('|','\\|').replace('\n',' ').replace('\r',' ')
    summary=report['selection_summary']
    lines=['선택 데이터 발생 기록 V2 — '+report['status'],f"SHA256: {report['source_sha256']}",
           f"정확한 선택 수: UNKNOWN / 선택 수 후보: {summary['top_level_selection_count_candidate']} / {summary['count_candidate_status']}",
           '완전한 객체 목록: false / 그룹 소유권: UNKNOWN',
           '| 형상 발생 ID | byte 범위 | 기록 수 | 형상 후보 | 원래 chain |', '|---|---|---|---|---|']
    for g in report['geometry_occurrences']:
        lines.append('| '+' | '.join(cell(x) for x in [g['occurrence_id'],g['range'],g['record_count'],g['shape_candidate']['value'],g['decoder_chain_included']])+' |')
    lines+=['','| 문자 발생 ID | record 범위 | 문자열 후보 | char DWORD | 기존 chain의 같은 내용 |','|---|---|---|---|---|']
    for t in report['text_occurrences']:
        lines.append('| '+' | '.join(cell(x) for x in [t['occurrence_id'],t['range'],t['text_candidate'],[x['u32'] for x in t['char_dwords']],t['legacy_chain_equal_text_indices']])+' |')
    lines.append('모든 발생 기록의 owner=UNKNOWN. 빈 목록은 객체 부재를 증명하지 않습니다.')
    return '\n'.join(lines)


def main(argv=None):
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    if argv is None and sys.argv[1:]==['--worker']:
        data=sys.stdin.buffer.read(MAX_INPUT+1)
        try:
            if len(data)>MAX_INPUT:raise ValueError('input bound')
            report=_worker(data)
        except Exception as error:report=empty(data,'UNSUPPORTED',type(error).__name__+': '+str(error))
        report['_pid']=os.getpid();encoded=json.dumps(report,ensure_ascii=True,allow_nan=False)
        if len(encoded.encode('utf8'))>MAX_JSON:
            report=empty(data,'UNSUPPORTED','Output JSON bound exceeded');report['_pid']=os.getpid();encoded=json.dumps(report)
        sys.stdout.write(encoded);return 0
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--format',choices=['json','table'],default='json')
    parser.add_argument('--output',type=Path);parser.add_argument('--timeout',type=float,default=15)
    args=parser.parse_args(argv)
    if args.output and args.output.exists():parser.error('Refusing to overwrite existing file')
    try:
        if args.input.stat().st_size>MAX_INPUT:raise ValueError('Input exceeds1MiB admission limit')
        with args.input.open('rb') as f:data=f.read(MAX_INPUT+1)
        report=analyze_bytes(data,timeout=args.timeout)
    except (OSError,ValueError) as error:parser.error(str(error))
    text=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False) if args.format=='json' else render_table(report)
    if args.output:
        with args.output.open('x',encoding='utf8') as f:f.write(text+'\n')
    else:print(text)
    return 0 if report['status']=='PARTIAL' else 2

if __name__=='__main__':raise SystemExit(main())
