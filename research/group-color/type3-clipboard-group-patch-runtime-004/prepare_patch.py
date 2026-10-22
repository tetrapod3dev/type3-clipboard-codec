"""Exact-G1-only offline patch. No Clipboard, UI, Native or production codec writes."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import dataclasses
import hashlib
import json

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'type3-clipboard-member-color-003'
CODEC=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(CODEC/'src'))
from type3_clipboard_codec.codec.decoder import Decoder

INPUT_SHA='0b62011ff898b414fce086a6c775d1073bb08fe0b49edacf98e9d5a1d185ad4c'
OUTPUT_SHA='d70bc09ac7b8f4bfff4d131acecda4d831f99b249d4fc6f1996c2d65ae605fb8'
PRECONDITIONS=((1641,bytes.fromhex('64ffcc00')),(1653,bytes.fromhex('64ffcc00')),
               (915,bytes.fromhex('3060cc00')),(927,bytes.fromhex('3060cc00')))
CHANGED=(1641,1642,1643,1653,1654,1655)

def sha(data):return hashlib.sha256(data).hexdigest()

def patch_g1(data):
    if len(data)!=8192:raise ValueError('입력 길이가 8192바이트가 아닙니다.')
    for offset,expected in PRECONDITIONS:
        if data[offset:offset+4]!=expected:
            raise ValueError(f'색상 사전 조건 불일치: [{offset},{offset+4})')
    if sha(data)!=INPUT_SHA:raise ValueError('허용된 G1 입력 SHA가 아닙니다.')
    result=bytearray(data)
    for offset in (1641,1653):result[offset:offset+4]=bytes.fromhex('98cc9800')
    result=bytes(result)
    if tuple(i for i,(a,b) in enumerate(zip(data,result)) if a!=b)!=CHANGED:
        raise ValueError('허용된 6바이트 외에 차이가 있습니다.')
    if sha(result)!=OUTPUT_SHA:raise ValueError('예상 출력 SHA 불일치')
    return result

def geometry(obj):
    return {'object_type_candidate':obj.object_type,'group_candidate':obj.is_grouped,
        'declared_count_candidate':obj.declared_object_count,'group_children_candidate_count':len(obj.group_children),
        'group_bbox':None if obj.group_bbox is None else dataclasses.asdict(obj.group_bbox),
        'aggregate_bbox':None if obj.aggregate_bbox is None else dataclasses.asdict(obj.aggregate_bbox),
        'chains':[{'shape':c.shape_type,'bbox':None if c.bbox is None else dataclasses.asdict(c.bbox),
            'contour_records':[dataclasses.asdict(v) for v in c.contour_records],
            'points':[dataclasses.asdict(v) for v in c.points],
            'raw_contour_sha256':sha(c.raw_contour_bytes)} for c in obj.object_chains]}

def colors(obj):
    return [{'ordinal_in_this_snapshot':i,'bbox':dataclasses.asdict(c.bbox),
        'name':c.style.line_color_name,'hex_rgb':c.style.line_color_hex,
        'confidence':c.style.line_color_confidence} for i,c in enumerate(obj.object_chains)]

def save_new_or_identical(path,data):
    if path.exists():
        if path.read_bytes()!=data:raise ValueError(f'기존 출력 충돌: {path.name}')
    else:
        with path.open('xb') as stream:stream.write(data)

def build():
    source=PRIOR/'samples/G1'
    original=(source/'typeeditzone.bin').read_bytes()
    version=(source/'typeeditzone_version.bin').read_bytes()
    result=patch_g1(original)
    before,after=Decoder().decode_bytes(original),Decoder().decode_bytes(result)
    if geometry(before)!=geometry(after):raise ValueError('Decoder 형상/그룹 후보 변경')
    if [v['name'] for v in colors(before)]!=['Navy Blue','Turquoise']:raise ValueError('예상 G1 색상과 다릅니다.')
    if [v['name'] for v in colors(after)]!=['Navy Blue','Army Green']:raise ValueError('수정 후 색상 후보 불일치')
    if not after.is_grouped or after.declared_object_count!=1 or len(after.object_chains)!=2:
        raise ValueError('예상 그룹 Decoder 구조와 다릅니다.')
    if len(version)!=32 or sha(version)!='33078d77a7e1220490bfdd499fe98ad4187fd850d70d287dfa7cfb641c90a14f':
        raise ValueError('G1 Version 입력 불일치')
    control=(PRIOR/'samples/G0-R/typeeditzone.bin').read_bytes()
    remaining=[i for i,(a,b) in enumerate(zip(result,control)) if a!=b]
    evidence=json.loads((PRIOR/'ownership-evidence.json').read_text(encoding='utf-8'))
    spans=[c['guid_raw_span'] for c in evidence['samples']['G0-R']['base_candidates']]
    if len(control)!=8192 or len(remaining)!=111:raise ValueError('G0-R과 111바이트 차분 재현 실패')
    inside=all(any(start<=i<end for start,end in spans) for i in remaining)
    if not inside:raise ValueError('남은 차분에 기존 GUID 기록 후보 밖의 값이 있습니다.')
    out=HERE/'candidate'
    out.mkdir(exist_ok=True)
    save_new_or_identical(out/'typeeditzone.bin',result)
    save_new_or_identical(out/'typeeditzone_version.bin',version)
    save_new_or_identical(out/'manifest.json',(source/'manifest.json').read_bytes())
    report={'verdict':'GROUP_PATCH_OFFLINE_READY','input_path':str(source/'typeeditzone.bin'),
        'input_sha256':sha(original),'output_sha256':sha(result),'lengths':[len(original),len(result)],
        'version_sha256':sha(version),'version_length':len(version),'version_copied_exactly':True,
        'writes':[{'range':[i,i+4],'before':original[i:i+4].hex(),'after':result[i:i+4].hex()} for i in (1641,1653)],
        'actual_changed_offsets':list(CHANGED),'other_bytes_identical':True,
        'R1_fields_unchanged':all(original[i:i+4]==result[i:i+4]==bytes.fromhex('3060cc00') for i in (915,927)),
        'colors_before':colors(before),'colors_after':colors(after),'decoder_geometry_identical':True,
        'geometry':geometry(after),'G0_R_sha256':sha(control),'G0_R_remaining_difference_count':len(remaining),
        'G0_R_remaining_difference_offsets':remaining,'recognized_guid_candidate_spans':spans,
        'remaining_differences_within_guid_candidates':inside,
        'remaining_difference_safety':'UNKNOWN; not assumed harmless',
        'member_serialize_boundary':'UNKNOWN','reference_table_semantics':'NOT_VERIFIED',
        'runtime_approval':'NOT_GRANTED_FOR_THIS_STAGE','clipboard_access':'NOT_EXECUTED','Type3_operations':'NOT_EXECUTED'}
    (HERE/'recomputed-offline-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    r=build()
    print(r['verdict'])
    print('output SHA256:',r['output_sha256'])
    print('changed offsets:',r['actual_changed_offsets'])
    print('remaining G0-R difference:',r['G0_R_remaining_difference_count'])
