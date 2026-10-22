"""Frozen-profile prediction then saved-file comparison. No UI/Clipboard/write API."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import struct

ROOT=Path(__file__).resolve().parent
CODEC=Path(__file__).resolve().parents[3]
def sha(data):return hashlib.sha256(data).hexdigest()
def read_json(path):return json.loads(path.read_text(encoding='utf-8-sig'))

def checked_profile():
    lock=read_json(ROOT/'execution-lock.json')
    blob=(ROOT/'frozen-profile.json').read_bytes()
    if sha(blob)!=lock['profile_sha256']:raise ValueError('Frozen profile SHA mismatch')
    for item in lock['dependencies']:
        if sha((CODEC/item['path']).read_bytes())!=item['sha256']:
            raise ValueError('Frozen locator/codec dependency changed: '+item['path'])
    return json.loads(blob),lock

def load_locator():
    path=ROOT.parent/'type3-clipboard-group-field-locator-005/field_locator.py'
    spec=importlib.util.spec_from_file_location('frozen_locator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def predict_bytes(data):
    profile,lock=checked_profile()
    result=load_locator().locate(data,profile) # Never call learn_profile/build.
    return {'profile_sha256':lock['profile_sha256'],'locator_result':result,
            'write_permission':False,'prediction_scope':'Empirical field prediction only'}

def bundle(name):
    folder=ROOT/'samples'/name
    data=(folder/'typeeditzone.bin').read_bytes()
    version=(folder/'typeeditzone_version.bin').read_bytes()
    manifest=read_json(folder/'manifest.json')
    formats={item['format_name']:item for item in manifest['formats']}
    for key,blob in [('TypeEditZone',data),('TypeEditZoneVersion',version)]:
        if key not in formats or formats[key]['byte_length']!=len(blob):raise ValueError('Invalid bundle manifest')
    return data,version

def predict_capture(name):
    if name not in ('H0-A','H1'):raise ValueError('Only H0-A/H1 prediction phases supported')
    out=ROOT/'predictions'/f'{name}.json'
    data,version=bundle(name)
    if out.exists():
        recorded=read_json(out)
        if recorded['locator_result']['input_sha256']!=sha(data):raise ValueError('Prediction/input conflict')
        if recorded['profile_sha256']!=checked_profile()[1]['profile_sha256']:raise ValueError('Prediction/profile conflict')
        return recorded # Preserve original prediction timestamp and result.
    if name=='H0-A' and (ROOT/'samples/H1/typeeditzone.bin').exists():
        raise ValueError('H0 prediction must be frozen before H1 is captured')
    if name=='H1':
        earlier=read_json(ROOT/'predictions/H0-A.json')
        if earlier['profile_sha256']!=checked_profile()[1]['profile_sha256']:raise ValueError('H0 profile changed')
        h0,_=bundle('H0-A')
        if earlier['locator_result']['input_sha256']!=sha(h0):raise ValueError('H0 input changed')
        if earlier['locator_result']['status']!='CANDIDATE_ONLY':raise ValueError('H0 rejected; do not continue experiment')
    result=predict_bytes(data)
    result.update({'sample':name,'version_sha256':sha(version),
                   'prediction_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    out.parent.mkdir(exist_ok=True)
    with out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    return result

def guid_candidate_spans(data,members):
    # Reuse existing bounded base grammar; do not infer C++ ownership or IDs.
    path=ROOT.parent/'type3-clipboard-base-serialize-003/walk_base.py'
    spec=importlib.util.spec_from_file_location('prior_base',path)
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    boxes=[m['bbox'] for m in members]
    union={key:(min if key.startswith(('xmin','ymin','zmin')) else max)(b[key] for b in boxes) for key in boxes[0]}
    boxes.append(union)
    spans=[]
    for at in range(0,len(data)-138+1):
        if data[at+52:at+56]!=(8).to_bytes(4,'little'):continue
        try:
            walked=base.walk(data,at)
            vals=struct.unpack_from('<6d',data,at)
            keys=['xmin_m','ymin_m','zmin_m','xmax_m','ymax_m','zmax_m']
            if not any(all(abs(vals[i]-box[key])<=1e-12 for i,key in enumerate(keys)) for box in boxes):continue
            spans.append(next(field['span'] for field in walked['fields'] if field['name']=='guid_raw'))
        except (ValueError,struct.error):continue
    return spans

def match_ui(prediction,truth):
    if truth['group_selected_count']!=1:raise ValueError('UI did not confirm one group')
    members=prediction['locator_result']['members']
    mapping={}
    for label in ('R1','R2'):
        observed=truth['members'][label]
        if set(observed['bbox_m'])!={'xmin_m','ymin_m','zmin_m','xmax_m','ymax_m','zmax_m'}:
            raise ValueError('Complete UI bbox observation required')
        matches=[m for m in members if all(abs(m['bbox'][key]-value)<=2e-6 for key,value in observed['bbox_m'].items())]
        if len(matches)!=1 or not observed.get('evidence'):raise ValueError('Ambiguous/missing UI member mapping')
        if matches[0]['color_name_candidate']!=observed['color_name']:raise ValueError('UI/locator color mismatch')
        mapping[label]=matches[0]
    if mapping['R1']['ordinal_in_this_decode']==mapping['R2']['ordinal_in_this_decode']:raise ValueError('UI labels map to the same candidate')
    return mapping

def compare_predictions():
    _,lock=checked_profile()
    # Require both immutable predictions before opening the pair for byte diff.
    before=read_json(ROOT/'predictions/H0-A.json')
    after=read_json(ROOT/'predictions/H1.json')
    if any(p['profile_sha256']!=lock['profile_sha256'] for p in (before,after)):
        raise ValueError('Prediction profile lock mismatch')
    a,av=bundle('H0-A');repeat,rv=bundle('H0-B');b,bv=bundle('H1')
    if before['locator_result']['input_sha256']!=sha(a) or after['locator_result']['input_sha256']!=sha(b):
        raise ValueError('Captured input changed after prediction')
    result={'verdict':'INDEPENDENT_FIELD_PREDICTION_PARTIAL','profile_sha256':before['profile_sha256'],
        'samples':{name:{'zone_sha256':sha(data),'length':len(data),'version_sha256':sha(version)} for name,data,version in [('H0-A',a,av),('H0-B',repeat,rv),('H1',b,bv)]},
        'repeat_exact':a==repeat and av==rv,'version_stable_across_H0_H1':av==bv,
        'write_permission':False,'member_serialize_boundary':'UNKNOWN','reference_ledger':'UNKNOWN'}
    if any(p['locator_result']['status']!='CANDIDATE_ONLY' for p in [before,after]):
        result['verdict']='PROFILE_FAMILY_MISMATCH'
    else:
        ui=read_json(ROOT/'ui-observations.json')
        old,new=match_ui(before,ui['H0-A']),match_ui(after,ui['H1'])
        if [old[k]['color_name_candidate'] for k in ('R1','R2')]!=['Navy Blue','Army Green']:
            raise ValueError('Unexpected H0 control colors')
        if [new[k]['color_name_candidate'] for k in ('R1','R2')]!=['Navy Blue','Turquoise']:
            raise ValueError('Unexpected H1 control colors')
        stable_ranges=all(old[k]['color_pair_ranges_candidate']==new[k]['color_pair_ranges_candidate'] for k in old)
        stable_bbox=all(all(abs(old[k]['bbox'][key]-value)<=1e-12 for key,value in new[k]['bbox'].items()) for k in old)
        diffs=[i for i,(left,right) in enumerate(zip(a,b)) if left!=right]
        target=old['R2']['color_pair_ranges_candidate'];untouched=old['R1']['color_pair_ranges_candidate']
        expected=bytes.fromhex('98cc9800');changed=bytes.fromhex('64ffcc00')
        fields_match=stable_ranges and all(a[start:end]==expected and b[start:end]==changed for start,end in target)
        target_changes=[i for i in diffs if any(start<=i<end for start,end in target)]
        r1_unchanged=stable_ranges and all(a[start:end]==b[start:end] for start,end in untouched)
        guid_before=guid_candidate_spans(a,before['locator_result']['members'])
        guid_after=guid_candidate_spans(b,after['locator_result']['members'])
        guid_spans=[span for span in guid_before if span in guid_after]
        remaining=[i for i in diffs if i not in target_changes]
        unknown=[i for i in remaining if not any(start<=i<end for start,end in guid_spans)]
        result.update({'H0_members':old,'H1_members':new,'stable_predicted_ranges':stable_ranges,
            'member_bbox_stable':stable_bbox,'R2_fields_match_actual_color_transition':fields_match,
            'R2_actual_changed_offsets':target_changes,'R1_fields_unchanged':r1_unchanged,
            'length_delta':len(b)-len(a),'all_changed_offsets_common_extent':diffs,'known_base_guid_candidate_spans':guid_spans,
            'unclassified_changed_offsets':unknown,'guid_difference_safety':'Not assumed harmless',
            'UI_evidence':ui})
        if result['repeat_exact'] and av==bv and len(a)==len(b) and stable_bbox and fields_match and r1_unchanged and len(target_changes)==6 and not unknown:
            result['verdict']='INDEPENDENT_FIELD_PREDICTION_VERIFIED'
    (ROOT/'recomputed-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['check','predict-H0','predict-H1','compare'])
    args=parser.parse_args()
    if args.action=='check':print('FROZEN_PROFILE_OK',checked_profile()[1]['profile_sha256'])
    elif args.action=='compare':print(compare_predictions()['verdict'])
    else:print(predict_capture('H0-A' if args.action=='predict-H0' else 'H1')['locator_result']['status'])
