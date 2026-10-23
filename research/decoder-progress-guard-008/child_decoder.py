"""Standalone Python child for malformed bytes; no Type3 or Clipboard access."""
import argparse,faulthandler,inspect,json,os,sys,struct,types
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/archive-boundary-diagnostic-007'))
import reproduce
import boundary_diagnostic as d

def inputs():
    cases=reproduce.synthetic_inputs()
    data=d.load_shadow().fixtures()['G1'][1]
    tree=d.load_shadow().shadow(data)['tree']
    start=next(n for n in d.nodes(tree) if n['class']=='CContour')['point_records']['span'][0]
    for count in (0,0xffffffff,4097):
        b=bytearray(data);b[start-4:start]=count.to_bytes(4,'little');cases['count_'+str(count)]=bytes(b)
    return cases

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--trace',action='store_true');ap.add_argument('--before-scan',action='store_true');args=ap.parse_args()
    if args.case in ('scan_fallback','scan_no_marker'):
        fn=d.load_shadow().a.prior  # initialize unchanged Codec imports only
        from type3_clipboard_codec.parsers.geometry.contour_parser import analyze_contour_header_candidates
        if args.before_scan:
            m=types.ModuleType('baseline008');m.__package__='type3_clipboard_codec.parsers.geometry'
            source=(Path(__file__).parent/'contour_parser.before.py.txt').read_text(encoding='utf8')
            exec(compile(source,'contour_parser.before.py.txt','exec'),m.__dict__)
            analyze_contour_header_candidates=m.analyze_contour_header_candidates
        payload=b'no markers' if args.case=='scan_no_marker' else b'CObDao'+bytes(64)+b'CObDao'+bytes(8)+struct.pack('<II',1,2)+struct.pack('<4dI',1.,2.,0.,1.,12)*2
        print(json.dumps({'event':'child_start','pid':os.getpid(),'case':args.case}),flush=True)
        headers,diag=analyze_contour_header_candidates(payload)
        print(json.dumps({'event':'scan_returned','pid':os.getpid(),'headers':headers,'diagnostics':diag}),flush=True)
        return
    data=inputs()[args.case]
    print(json.dumps({'event':'child_start','pid':os.getpid(),'case':args.case,'input_sha256':d.sha(data),'length':len(data)}),flush=True)
    if args.trace:
        from type3_clipboard_codec.parsers.geometry.contour_parser import analyze_contour_header_candidates as fn
        lines,start=inspect.getsourcelines(fn)
        target=start+next(i for i,line in enumerate(lines) if 'diagnostics.append(marker_diag)' in line)
        hits=0
        def trace(frame,kind,arg):
            nonlocal hits
            if frame.f_code is fn.__code__ and kind=='line' and frame.f_lineno==target:
                if hits<3:
                    v=frame.f_locals
                    state={'event':'loop_completed','line':frame.f_lineno,'idx':v['idx'],'marker_pos':v['marker_pos'],
                        'selected_offsets':sorted(v['selected_offsets']),'found_headers':v['found_headers'],
                        'found_for_this_marker':v['found_for_this_marker'],'candidate_shift':v.get('shift'),
                        'legacy_candidate':v['marker_diag']['legacy_selected_candidate'],
                        'actual_selected':v['actual_selected'],'selection_reason':v['marker_diag']['selection_reason'],
                        'candidate_summary':[{k:c.get(k) for k in ['shift','kind','count','structural_valid','rejection_reason']} for c in v['structural_candidate_rows']]}
                    print(json.dumps(state),flush=True)
                hits+=1
            return trace
        faulthandler.dump_traceback_later(0.6)
        sys.settrace(trace)
    try:
        model,parser=d.load_shadow().a.Decoder().decode_bytes_with_parser(data)
        contours=[{'count':len(c.contour_records),'bytes_length':len(c.raw_contour_bytes)} for c in getattr(model,'object_chains',[])]
        print(json.dumps({'event':'decoder_returned','pid':os.getpid(),'parser':parser,'contours':contours,'archive_validation':'NOT_PERFORMED'}),flush=True)
    except Exception as e:
        print(json.dumps({'event':'decoder_exception','pid':os.getpid(),'type':type(e).__name__,'message':str(e)}),flush=True)
    finally:
        if args.trace:
            sys.settrace(None);faulthandler.cancel_dump_traceback_later()
if __name__=='__main__':main()
