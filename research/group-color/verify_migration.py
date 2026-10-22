"""Saved-evidence migration replay. Never imports UI/Clipboard capture tools."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util
import hashlib
import json

ROOT=Path(__file__).resolve().parent
CODEC=ROOT.parents[1]
N={'003':'type3-clipboard-member-color-003','004':'type3-clipboard-group-patch-runtime-004','005':'type3-clipboard-group-field-locator-005','006':'type3-clipboard-independent-prediction-006'}
def digest(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def verify():
    manifest=read(ROOT/'migration-manifest.json')
    for item in manifest['copied_evidence_and_original_code']:
        if digest((ROOT/item['target']).read_bytes())!=item['sha256']:
            raise ValueError('Historical evidence changed: '+item['target'])
    # Existing evidence remains immutable. Recalculation only writes separate outputs.
    p=ROOT/N['006']
    before={name:digest((p/name).read_bytes()) for name in ['frozen-profile.json','profile-lock.json','comparison.json','predictions/H0-A.json','predictions/H1.json','ui-observations.json']}
    forbidden_reads=[]
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            name=str(args[0]).lower().replace('\\','/')
            if 'typeedit-automation/' in name:
                forbidden_reads.append(name)
                raise RuntimeError('Migration may not read source repository: '+name)
    sys.addaudithook(audit)
    sys.path.insert(0,str(ROOT/N['004']))
    sys.path.insert(0,str(CODEC/'src'))
    patch=load('migration_patch',ROOT/N['004']/'prepare_patch.py')
    check=load('migration_prediction',p/'prediction_check.py')
    locator=check.load_locator()
    def training_forbidden(*args,**kwargs):raise RuntimeError('H replay must not train')
    locator.learn_profile=training_forbidden
    check.load_locator=lambda:locator
    g1=(ROOT/N['003']/'samples/G1/typeeditzone.bin').read_bytes()
    g1_pred=check.predict_bytes(g1)['locator_result']
    assert g1_pred['members'][0]['color_name_candidate']=='Navy Blue'
    assert g1_pred['members'][1]['color_name_candidate']=='Turquoise'
    assert g1_pred['members'][1]['color_pair_ranges_candidate']==[[1641,1645],[1653,1657]]
    assert not g1_pred['change_allowed']
    candidate=patch.patch_g1(g1) # In-memory exact-G1 reproduction; no new fixture or Clipboard writes.
    original_candidate=(ROOT/N['004']/'candidate/typeeditzone.bin').read_bytes()
    recopy=(ROOT/N['004']/'runtime-001/recopy/typeeditzone.bin').read_bytes()
    assert candidate==original_candidate==recopy
    assert (ROOT/N['004']/'candidate/typeeditzone_version.bin').read_bytes()==(ROOT/N['004']/'runtime-001/recopy/typeeditzone_version.bin').read_bytes()
    assert patch.geometry(patch.Decoder().decode_bytes(g1))==patch.geometry(patch.Decoder().decode_bytes(recopy))
    assert [x['name'] for x in patch.colors(patch.Decoder().decode_bytes(recopy))]==['Navy Blue','Army Green']
    recomputed={}
    for name in ('H0-A','H1'):
        data,version=check.bundle(name)
        actual=check.predict_bytes(data)
        preserved=read(p/'predictions'/f'{name}.json')
        assert actual['locator_result']==preserved['locator_result']
        assert actual['profile_sha256']==preserved['profile_sha256']
        assert digest(version)==preserved['version_sha256']
        recomputed[name]=actual
    for row in recomputed.values():
        r2=next(m for m in row['locator_result']['members'] if abs(m['width_mm']-55)<1e-9)
        r1=next(m for m in row['locator_result']['members'] if abs(m['width_mm']-30)<1e-9)
        assert r2['color_pair_ranges_candidate']==[[915,919],[927,931]]
        assert r1['color_pair_ranges_candidate']==[[1641,1645],[1653,1657]]
    recalculated=check.compare_predictions()
    assert recalculated==read(p/'comparison.json')
    assert recalculated['verdict']=='INDEPENDENT_FIELD_PREDICTION_VERIFIED'
    assert recalculated['repeat_exact'] and recalculated['member_bbox_stable']
    assert recalculated['R1_fields_unchanged'] and not recalculated['unclassified_changed_offsets']
    assert recalculated['R2_actual_changed_offsets']==[915,916,917,927,928,929]
    assert len(recalculated['all_changed_offsets_common_extent'])==116
    assert not recalculated['write_permission']
    assert before=={name:digest((p/name).read_bytes()) for name in before}
    assert not forbidden_reads
    result={'migration_replay':'PASS','historical_files_sha_verified':len(manifest['copied_evidence_and_original_code']),
        'profile_sha256':recalculated['profile_sha256'],'G1_candidate_recopy_sha256':digest(candidate),
        'G1_exact_patch_reproduced_in_memory':True,'H_predictions_equal_preserved':True,
        'H_comparison_equal_preserved':True,'H_verdict':recalculated['verdict'],
        'source_repository_reads':forbidden_reads,'training':'FORBIDDEN_DURING_REPLAY',
        'historical_outputs_unchanged':True,'write_permission':False,'Type3':'NOT_EXECUTED','Clipboard':'NOT_ACCESSED'}
    (ROOT/'migration-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':verify()
