"""E/F research diagnostics over saved bytes; no production Parser changes."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
MAX_BYTES=16*1024*1024


def load_inventory():
    path=ROOT/'research/selection-object-inventory-001/selection_inventory.py'
    spec=importlib.util.spec_from_file_location('ef002_original_inventory',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def sha(data):return hashlib.sha256(data).hexdigest()


def compact(value):
    if isinstance(value,bytes):return {'length':len(value),'sha256':sha(value)}
    if isinstance(value,(str,int,float,bool,type(None))):return value
    if isinstance(value,dict):return {k:compact(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [compact(v) for v in value]
    if hasattr(value,'header'):
        return {'class':value.header.class_name,'descriptor_candidate_span':[value.start_offset,value.payload_offset-(48 if value.bbox else 0)],
                'scanner_payload_span':[value.payload_offset,value.end_offset],
                'note':'scanner window, not proven Serialize object extent'}
    if hasattr(value,'nodes'):
        return {'node_classes':[n.header.class_name for n in value.nodes],
                'contour_range':[value.source_stream_offset,value.source_stream_offset+len(value.raw_contour_bytes)] if value.source_stream_offset is not None and value.raw_contour_bytes else None,
                'contour_sha256':sha(value.raw_contour_bytes) if value.raw_contour_bytes else None,
                'record_count':len(value.contour_records),'text_candidate':value.text_candidate,
                'shape_candidate':value.shape_type}
    return type(value).__name__


def _worker(data):
    sys.path.insert(0,str(ROOT/'src'))
    from type3_clipboard_codec.codec.decoder import Decoder
    from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser
    from type3_clipboard_codec.parsers.text.cparagraphe_parser import extract_text_runs,read_slot_record_runs_from_blob,records_to_text_run
    from type3_clipboard_codec.parsers.text.text_slot_candidate import _validate_current_empty_slot_layout
    from type3_clipboard_codec.models.geometry import Type3ObjectChain
    inv=load_inventory();d=inv.load_diagnostic();s=d.load_shadow()
    events=[];trace_truncated=False
    functions={'can_parse','detect_parser','_read_top_level_header','extract_nodes','parse_single_node','group_nodes_into_chains','_process_object_chain',
               '_read_embedded_contour_chains','analyze_contour_header_candidates','extract_text_runs','attach_text_runs_to_chains'}
    source,start=inspect.getsourcelines(Type3ChainParser._process_object_chain)
    branch_lines={start+i:line.strip() for i,line in enumerate(source)
                  if 'if node.header.class_name' in line}
    def trace(frame,event,arg):
        nonlocal trace_truncated
        func=frame.f_code.co_name
        if 'type3_clipboard_codec' not in frame.f_code.co_filename:return trace
        if len(events)>=1000:
            trace_truncated=True;return trace
        file=str(Path(frame.f_code.co_filename).relative_to(ROOT)).replace('\\','/')
        if event=='line' and func=='_process_object_chain' and frame.f_lineno in branch_lines:
            node=frame.f_locals.get('node')
            events.append({'event':'branch','function':func,'file':file,'line':frame.f_lineno,'condition':branch_lines[frame.f_lineno],
                           'node':compact(node)})
        if event=='return' and func in functions:
            values={k:compact(v) for k,v in frame.f_locals.items() if k in ['node_start_offset','idx','headers','node','chain','chains','runs']}
            if func=='analyze_contour_header_candidates':
                headers,diagnostics=arg
                returned={'headers':headers,'markers':[{'marker_offset':x['marker_offset'],'selected_payload_offset':x['selected_payload_offset'],
                    'selected_count':x['selected_count'],'selection_reason':x['selection_reason'],
                    'rejections':[{'shift':c['shift'],'reason':c.get('rejection_reason'),'structural_failures':c.get('structural_failure_reasons')} for c in x['candidates']]} for x in diagnostics]}
            else:returned=compact(arg)
            events.append({'event':'return','function':func,'file':file,'line':frame.f_lineno,'locals':values,'return':returned})
        return trace
    # Unreviewed E/F prefix never admitted into the sequential Shadow Reader.
    shadow=s.shadow(data)
    if data[:6].hex()=='000000000100' and shadow['status']!='CONDITIONAL_MATCH':
        return {'source_sha256':sha(data),'status':'UNSUPPORTED','reason':'007 known-prefix unsupported structure policy',
                'shadow_status':shadow['status'],'stop_cursor':shadow['stop_cursor'],'exact_top_level_enumeration':False,
                'change_allowed':False,'complete_inventory':False,'top_level_selection_count':'UNKNOWN','group_hierarchy':'UNKNOWN'}
    sys.settrace(trace)
    try:decoded,parser_name=Decoder().decode_bytes_with_parser(data)
    finally:sys.settrace(None)
    before=d.fingerprint(decoded)
    parser=Type3ChainParser()
    prefix,count,envelope=parser._read_top_level_header(data)
    nodes=parser._extract_nodes(data[envelope:])
    text_runs,_,text_notes=extract_text_runs(nodes)
    slot_candidates=[]
    for index,records in enumerate(read_slot_record_runs_from_blob(data)):
        raw=b''.join(records);matches=[];cursor=0
        while raw:
            cursor=data.find(raw,cursor)
            if cursor<0:break
            matches.append([cursor,cursor+len(raw)]);cursor+=1
        slot_candidates.append({'finding_index':index,'decoded_run_candidate':records_to_text_run(records),
            'source_record_windows':matches,'source_window_assignment':'UNIQUE_BYTE_WINDOW' if len(matches)==1 else 'AMBIGUOUS',
            'record_lengths':[len(record) for record in records],
            'reviewed_v5_empty_layout_rejections':[_validate_current_empty_slot_layout(record) for record in records],
            'char_fields':[{'record_index':i,'offset_in_record':4,'raw_hex':record[4:8].hex(),
                            'u32':int.from_bytes(record[4:8],'little')} for i,record in enumerate(records)],
            'confidence':'HEURISTIC','layout_contract':'Existing 204-byte AttrChar v5/empty extension validator applied, no new alignment search',
            'object_extent':'UNKNOWN','owner':'UNKNOWN','top_level_object':'UNKNOWN'})
    # A counterfactual research call only: do not add results to Decoder/Inventory chains.
    extra=[]
    for node in nodes:
        if node.header.class_name!='CParagraphe':continue
        template=Type3ObjectChain()
        candidates=parser._read_embedded_contour_chains(node,template,parser._read_style_properties(b''))
        extra.append({'scanner_payload_span':[envelope+node.payload_offset,envelope+node.end_offset],
                      'method':'Existing _read_embedded_contour_chains applied diagnostically to a CParagraphe scanner window',
                      'candidate_contours':compact(candidates),'confidence':'HEURISTIC','ownership':'UNKNOWN',
                      'merged_into_decoder':False,'not_selected_object_count':True})
    result={'source_sha256':sha(data),'input_length':len(data),'status':'DIAGNOSTIC_COMPLETE',
            'exact_top_level_enumeration':False,'complete_inventory':False,'top_level_selection_count':'UNKNOWN',
            'group_hierarchy':'UNKNOWN','change_allowed':False,'parser':parser_name,
            'input_prefix_hex':data[:6].hex(),
            'coordinate_system':'Node/chain/trace spans relative to envelope_offset; slot windows absolute input bytes; all half-open. Trace contour-header offsets are local to their caller payload.',
            'header':{'prefix_hex':prefix.hex(),'declared_count_candidate':count,'envelope_offset':envelope,
                      'basis':'existing _read_top_level_header; not selected-object proof'},
            'shadow':{'status':shadow['status'],'reason':shadow.get('reason'),'stop_cursor':shadow['stop_cursor']},
            'node_candidates':compact(nodes),'decoder_chains':compact(decoded.object_chains),
            'payload_text':getattr(decoded,'text_content',None),'all_extracted_text_runs':text_runs,
            'slot_record_findings':slot_candidates,'diagnostic_contour_probe':extra,
            'trace':events,'trace_truncated':trace_truncated,'decoder_fingerprint':before,
            'decoder_model_unchanged_after_diagnostic':d.fingerprint(decoded)==before,
            'unknowns':['full Archive valid length','reference-class object starts','UI ownership','Group/Member boundaries','entire object extents']}
    return result


def diagnose_bytes(data,timeout=10):
    if not isinstance(data,bytes):raise TypeError('bytes required')
    if not (0<timeout<120):raise ValueError('timeout must be positive and under 120 seconds')
    if len(data)>MAX_BYTES:raise ValueError('diagnostic input limit')
    p=subprocess.Popen([sys._base_executable,'-B',str(Path(__file__).resolve()),'--worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                       env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    timed_out=False;started=time.monotonic()
    try:stdout,stderr=p.communicate(data,timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True;p.kill();stdout,stderr=p.communicate(timeout=5)
    try:
        if timed_out or p.returncode:raise ValueError('worker failed')
        result=json.loads(stdout)
        if result.pop('_pid')!=p.pid or result['source_sha256']!=sha(data):raise ValueError('worker identity mismatch')
    except (ValueError,KeyError,TypeError):
        result={'source_sha256':sha(data),'status':'UNSUPPORTED','reason':'worker did not complete','exact_top_level_enumeration':False,
                'complete_inventory':False,'top_level_selection_count':'UNKNOWN','group_hierarchy':'UNKNOWN','change_allowed':False,
                'stderr':stderr.decode('utf8',errors='replace')[-3000:]}
    result['execution']={'child_pid':p.pid,'returncode':p.returncode,'timed_out':timed_out,'elapsed_seconds':time.monotonic()-started,
                         'kill_scope':'owned Python child only' if timed_out else 'none'}
    return result


def main(argv=None):
    if argv is None and sys.argv[1:]==['--worker']:
        data=sys.stdin.buffer.read(MAX_BYTES+1)
        try:
            if len(data)>MAX_BYTES:raise ValueError('input limit')
            result=_worker(data)
        except Exception as error:
            result={'source_sha256':sha(data),'status':'UNSUPPORTED','reason':type(error).__name__+': '+str(error),
                    'exact_top_level_enumeration':False,'complete_inventory':False,'top_level_selection_count':'UNKNOWN','group_hierarchy':'UNKNOWN','change_allowed':False}
        result['_pid']=os.getpid();print(json.dumps(result,ensure_ascii=True,allow_nan=False));return 0
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    if args.output and args.output.exists():parser.error('Refusing overwrite')
    if args.input.stat().st_size>MAX_BYTES:parser.error('input limit')
    result=diagnose_bytes(args.input.read_bytes());text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        with args.output.open('x',encoding='utf8') as f:f.write(text+'\n')
    else:print(text)
    return 0 if result['status']=='DIAGNOSTIC_COMPLETE' else 2

if __name__=='__main__':raise SystemExit(main())
