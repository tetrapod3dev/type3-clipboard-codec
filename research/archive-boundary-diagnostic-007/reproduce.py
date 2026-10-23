"""Read-only reproducibility runner; writes only explicitly selected new 007 artifacts."""
import json
from pathlib import Path
import boundary_diagnostic as d
OUT=Path(__file__).resolve().parent

def build_reports():
    s=d.load_shadow()
    results={}
    equivalence={}
    for name,(path,data) in s.fixtures().items():
        before=s.a.Decoder().decode_bytes_with_parser(data)
        r=d.diagnose_bytes(data,research_shadow=True)
        after=s.a.Decoder().decode_bytes_with_parser(data)
        assert d.fingerprint(before)==d.fingerprint(after)
        equivalence[name]={'before':d.fingerprint(before),'after':d.fingerprint(after),'equal':True,'source_sha256':d.sha(data)}
        r.update(source_path=str(path.relative_to(d.ROOT)), source_kind='PRESERVED_TYPE3_SAMPLE')
        results[name]=r
    return results,equivalence

def synthetic_inputs():
    s=d.load_shadow();data=s.fixtures()['G1'][1];base=s.shadow(data)
    contours=[n for n in d.nodes(base['tree']) if n['class']=='CContour']
    a,b=contours[0]['point_records']['span'];c,e=contours[1]['point_records']['span']
    duplicate=bytearray(data);duplicate[c:e]=data[a:b]
    count_bad=bytearray(data);count_bad[a-4:a]=(101).to_bytes(4,'little')
    schema_bad=bytearray(data);schema_bad[8:10]=(99).to_bytes(2,'little')
    ref=next(x for x in base['events'] if x['kind']=='class_reference')['span'][0]
    ref_bad=bytearray(data);ref_bad[ref:ref+2]=(0x8ffe).to_bytes(2,'little')
    return {'duplicate_contour':bytes(duplicate),'count_out_of_scope':bytes(count_bad),
        'count_stride_extent_truncated':data[:b-1],
        'property_truncated':data[:base['properties'][0]['body'][1]-1],
        'suffix_truncated':data[:base['colors'][0]['suffix_span'][1]-1],
        'unregistered_class_reference':bytes(ref_bad),'unsupported_schema':bytes(schema_bad),
        'unknown_tail_removed':data[:base['stop_cursor']]}

def main():
    reports,equivalence=build_reports()
    synthetic={name:{**d.diagnose_bytes(data,research_shadow=True),'source_kind':'SYNTHETIC_MEMORY_INPUT_NOT_TYPE3_SAMPLE'} for name,data in synthetic_inputs().items()}
    for filename,obj in [('sample-diagnostics.json',reports),('decoder-equivalence.json',equivalence),('synthetic-diagnostics.json',synthetic)]:
        with (OUT/filename).open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
    for n,r in reports.items():print(n,r['overall_status'],len(r['contours']))
    for n,r in synthetic.items():print(n,r['overall_status'],r['shadow_stop_cursor'],r['shadow_stop_reason'])
if __name__=='__main__':main()
