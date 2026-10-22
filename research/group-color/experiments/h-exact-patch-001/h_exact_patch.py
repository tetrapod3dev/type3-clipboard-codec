"""Exact historical H1 experiment only. No Clipboard, Host or general write API."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util
import hashlib
import json

HERE=Path(__file__).resolve().parent
GROUP=HERE.parents[1]
CODEC=GROUP.parents[1]
H=GROUP/'type3-clipboard-independent-prediction-006'
G1=GROUP/'type3-clipboard-group-patch-runtime-004'
INPUT_SHA='1e2d803df75b56385d97ee8a0021ae94b80cb1da2cd37f96abdf95e4242957af'
PROFILE_SHA='d0f179eaee2c9e625a936f7ce7ad7c3db0d78928df5a782bfd4a18d8130d3197'
TURQUOISE=bytes.fromhex('64ffcc00')
ARMY=bytes.fromhex('98cc9800')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

check=load('h_exact_prediction',H/'prediction_check.py')
patch=load('h_exact_g1_reference',G1/'prepare_patch.py')

def validate_evidence():
    manifest=read(GROUP/'migration-manifest.json')
    for item in manifest['copied_evidence_and_original_code']:
        if sha((GROUP/item['target']).read_bytes())!=item['sha256']:
            raise ValueError('Historical evidence SHA mismatch: '+item['target'])
    profile,lock=check.checked_profile()
    if lock['profile_sha256']!=PROFILE_SHA:raise ValueError('Wrong frozen profile')
    # Lock itself is fixed against the pre-experiment snapshot, not silently re-created.
    snapshot=read(HERE/'before.json')['existing_files']
    rel=(H/'execution-lock.json').relative_to(CODEC).as_posix()
    if sha((H/'execution-lock.json').read_bytes())!=snapshot[rel]:raise ValueError('Execution lock changed')
    comparison=read(H/'comparison.json')
    if comparison['verdict']!='INDEPENDENT_FIELD_PREDICTION_VERIFIED':raise ValueError('H evidence not verified')
    for name in ('H0-A','H1'):
        data,version=check.bundle(name)
        expected=comparison['samples'][name]
        if sha(data)!=expected['zone_sha256'] or sha(version)!=expected['version_sha256']:
            raise ValueError('H bundle SHA mismatch')
        prediction=read(H/'predictions'/f'{name}.json')
        if check.predict_bytes(data)['locator_result']!=prediction['locator_result']:
            raise ValueError('Historical prediction differs')
    return comparison

def plan(data,version):
    evidence=validate_evidence()
    expected=evidence['samples']['H1']
    if len(data)!=expected['length'] or sha(data)!=INPUT_SHA or sha(data)!=expected['zone_sha256']:
        raise ValueError('Exact H1 input SHA/length mismatch')
    if len(version)!=32 or sha(version)!=expected['version_sha256']:raise ValueError('Version SHA mismatch')
    prediction=check.predict_bytes(data)
    row=prediction['locator_result']
    if row['status']!='CANDIDATE_ONLY' or row['change_allowed'] or len(row['members'])!=2:
        raise ValueError('Ambiguous locator result')
    if row!=read(H/'predictions/H1.json')['locator_result']:raise ValueError('H1 prediction mismatch')
    mapping=check.match_ui(prediction,read(H/'ui-observations.json')['H1'])
    if mapping['R1']['color_name_candidate']!='Navy Blue' or mapping['R2']['color_name_candidate']!='Turquoise':
        raise ValueError('Unexpected member colors')
    obj=patch.Decoder().decode_bytes(data)
    if not obj.is_grouped or obj.declared_object_count!=1 or len(obj.object_chains)!=2:
        raise ValueError('Not the verified one-group/two-rectangle candidate')
    ranges=mapping['R2']['color_pair_ranges_candidate']
    other=mapping['R1']['color_pair_ranges_candidate']
    all_ranges=ranges+other
    if len(ranges)!=2 or len(other)!=2:raise ValueError('Unexpected color pair count')
    for index,(start,end) in enumerate(all_ranges):
        if start<0 or end-start!=4 or end>len(data):raise ValueError('Invalid field extent')
        if any(start<b and a<end for a,b in all_ranges[:index]):raise ValueError('Overlapping color fields')
    if any(data[a:b]!=TURQUOISE for a,b in ranges):raise ValueError('R2 is not Turquoise')
    if any(data[a:b]!=bytes.fromhex('3060cc00') for a,b in other):raise ValueError('R1 is not Navy Blue')
    return mapping,obj

def patch_h1(data,version):
    mapping,before=plan(data,version)
    target=mapping['R2']['color_pair_ranges_candidate'] # Locator result; no absolute patch offsets.
    result=bytearray(data)
    for start,end in target:result[start:end]=ARMY
    result=bytes(result)
    changed=[i for i,(a,b) in enumerate(zip(data,result)) if a!=b]
    if len(result)!=len(data) or len(changed)!=6 or any(not any(a<=i<b for a,b in target) for i in changed):
        raise ValueError('Changes outside computed six-byte scope')
    if any(data[a:b]!=result[a:b] for a,b in mapping['R1']['color_pair_ranges_candidate']):raise ValueError('R1 changed')
    after=patch.Decoder().decode_bytes(result)
    if patch.geometry(before)!=patch.geometry(after):raise ValueError('Geometry/bbox/group/contour changed')
    predicted_after=check.predict_bytes(result)
    after_mapping=check.match_ui(predicted_after,read(H/'ui-observations.json')['H0-A'])
    if after_mapping['R2']['color_name_candidate']!='Army Green':raise ValueError('Output color differs')
    if predicted_after['locator_result']['change_allowed']:raise ValueError('Write admission must stay false')
    return result,{'computed_R2_ranges':target,'R1_ranges':mapping['R1']['color_pair_ranges_candidate'],
        'changed_offsets':changed,'geometry_bbox_contours_unchanged':True,'R1_color_unchanged':True,
        'locator_change_allowed':False,'member_serialize_boundary':'UNKNOWN','reference_ledger':'UNKNOWN'}

def build():
    data,version=check.bundle('H1')
    result,details=patch_h1(data,version)
    # Expected positions are checks only, never supplied to the patch operation.
    if details['computed_R2_ranges']!=[[915,919],[927,931]]:raise ValueError('Unexpected historical H field prediction')
    h0,_=check.bundle('H0-A')
    diffs=[i for i,(a,b) in enumerate(zip(h0,result)) if a!=b]
    spans=check.guid_candidate_spans(h0,check.predict_bytes(h0)['locator_result']['members'])
    unknown=[i for i in diffs if not any(a<=i<b for a,b in spans)]
    out=HERE/'candidate'
    # All checks precede any candidate creation.
    report={'verdict':'H_EXACT_PATCH_OFFLINE_READY','input_sha256':sha(data),'input_length':len(data),
        'output_sha256':sha(result),'output_length':len(result),'version_sha256':sha(version),
        'profile_sha256':PROFILE_SHA,**details,'H0_A_difference_count':len(diffs),
        'H0_A_difference_offsets':diffs,'H0_A_unclassified_differences':unknown,
        'extra_difference_safety':'UNKNOWN; GUID candidates are not assumed harmless',
        'runtime':'NOT_EXECUTED','clipboard':'NOT_ACCESSED','general_write_permission':False}
    for path,blob in [(out/'typeeditzone.bin',result),(out/'typeeditzone_version.bin',version)]:
        if path.exists() and path.read_bytes()!=blob:raise ValueError('Existing candidate collision: '+str(path))
    out.mkdir(exist_ok=True)
    for path,blob in [(out/'typeeditzone.bin',result),(out/'typeeditzone_version.bin',version)]:
        if not path.exists():
            with path.open('xb') as f:f.write(blob)
    (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(report['verdict'],report['output_sha256'])
    return report

if __name__=='__main__':build()
