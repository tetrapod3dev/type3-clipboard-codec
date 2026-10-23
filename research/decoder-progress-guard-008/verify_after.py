import json,sys,hashlib,difflib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'research/archive-boundary-diagnostic-007'))
import reproduce,boundary_diagnostic as d
import bounded_child as b
CASES=['count_stride_extent_truncated','property_truncated','suffix_truncated','count_out_of_scope','count_0','count_4294967295','count_4097','unregistered_class_reference','unsupported_schema','duplicate_contour','unknown_tail_removed']

def main():
    outcomes=[b.run_case(n,trace=(i==0)) for i,n in enumerate(CASES)]
    assert all(not r['timed_out'] and r['returncode']==0 for r in outcomes)
    (HERE/'child-results-after.json').write_text(json.dumps(outcomes,indent=2),encoding='utf8')
    report,e=reproduce.build_reports()
    old=json.loads((HERE/'normal-before.json').read_text())
    olddiag=json.loads((HERE/'diagnostic-before.json').read_text(encoding='utf8'))
    assert old==e and olddiag==report
    (HERE/'normal-after.json').write_text(json.dumps(e,indent=2),encoding='utf8')
    (HERE/'equivalence.json').write_text(json.dumps({'normal_samples_equal':8,'complete_decoder_and_parser_fingerprints_equal':True,'007_complete_diagnostic_reports_equal':True,'007_change_allowed':False,'007_ownership':'UNKNOWN','007_policy':'NOT_RUN_UNSUPPORTED_STRUCTURE unchanged','postfix_child_cases':len(outcomes),'postfix_timeouts':0},indent=2),encoding='utf8')
    oldtext=(HERE/'contour_parser.before.py.txt').read_text(encoding='utf8').splitlines(keepends=True)
    newtext=(ROOT/'src/type3_clipboard_codec/parsers/geometry/contour_parser.py').read_text(encoding='utf8').splitlines(keepends=True)
    (HERE/'minimal-change.diff').write_text(''.join(difflib.unified_diff(oldtext,newtext,fromfile='before/contour_parser.py',tofile='after/contour_parser.py')),encoding='utf8')
    print('Child cases',len(outcomes),'timeouts',0,'normal and 007 reports equal')
if __name__=='__main__':main()
