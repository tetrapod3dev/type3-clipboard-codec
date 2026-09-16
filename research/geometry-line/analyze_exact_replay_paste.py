"""File-only exact replay comparison. No clipboard imports, writes or payload mutation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
RESEARCH=ROOT/'research/geometry-line'
sys.path.insert(0,str(ROOT/'tools'))
from analyze_typeeditzone_mfc_archive import analyze_bytes
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def require(ok,msg):
    if not ok: raise ValueError(msg)

def diff(a,b):
    offsets=[i for i in range(max(len(a),len(b))) if i>=len(a) or i>=len(b) or a[i]!=b[i]]
    runs=[]
    for i in offsets:
        if runs and runs[-1]['end_exclusive']==i: runs[-1]['end_exclusive']=i+1
        else: runs.append({'start':i,'end_exclusive':i+1})
    for r in runs:
        lo,hi=r['start'],r['end_exclusive']
        r.update(length=hi-lo,source_hex=a[lo:hi].hex(),postpaste_hex=b[lo:hi].hex())
    return {'equal':a==b,'source_size':len(a),'postpaste_size':len(b),'changed_byte_count':len(offsets),'exact_changed_offsets':offsets,'ranges':runs}

def structure(b):
    audit=analyze_bytes(b,fixture='exact_replay',category='geometry',context_bytes=0)
    hits=[h for h in audit['class_hits'] if h['descriptor_pattern_match']]
    desc=[{'name':h['class_name'],'schema':h['candidate_schema_word'],'offset':h['descriptor_start']} for h in hits]
    family=[(d['name'],d['schema']) for d in desc]==[('CZone',1),('CCourbe',1),('CContour',2),('CPropertyExtend',5)]
    offsets={d['name']:d['offset'] for d in desc}
    r=offsets.get('CContour',-1000)+160
    valid=family and r>=8 and r+72<=len(b)
    kind,count=struct.unpack_from('<II',b,r-8) if valid else (None,None)
    layout=valid and kind==0 and count==2 and r+72==offsets.get('CPropertyExtend')
    return {'descriptors':desc,'expected_schema_family':family,'kind_candidate':kind,'point_count_candidate':count,'record_start':r if valid else None,'record_stride':36 if layout else None,'record_count':2 if layout else None,'two_record_layout_retained':layout}

def main():
    manifest=read(RESEARCH/'exact_replay_paste_manifest.json')
    require(manifest['human_paste_count']==1 and manifest['clipboard_load_count']==1,'Bounded runtime count failed')
    require('clipboard_access_closed_at_utc' in manifest,'Runtime collection not closed')
    source=ROOT/manifest['source_bundle']
    post=ROOT/'tests/samples/bundles/geometry/geometry_line_replay_M00_postpaste'
    for folder,entries in [(source,manifest['source_raw_verification']),(post,manifest['postpaste_capture']['capture']['files'])]:
        for f in entries:
            data=(folder/f['file']).read_bytes()
            require(sha(data)==f['sha256'] and len(data)==f['size'],'Raw hash/size mismatch: '+str(folder/f['file']))
    require(manifest['loaded_readback']['all_exact'],'Source load equality absent')
    for f in manifest['loaded_readback']['formats']:
        require((ROOT/f['readback_file']).read_bytes()==(source/Path(f['readback_file'].replace('\\','/')).name).read_bytes(),'Loaded readback changed')
    verify=manifest['postpaste_capture']['capture']['verification']
    require(verify['exit_code']==0 and 'typeeditzone_match=true' in verify['output'] and 'typeeditzone_version_match=true' in verify['output'],'Postcapture verify missing')
    a=(source/'typeeditzone.bin').read_bytes(); b=(post/'typeeditzone.bin').read_bytes()
    va=(source/'typeeditzone_version.bin').read_bytes(); vb=(post/'typeeditzone_version.bin').read_bytes()
    require(bytes.fromhex((ROOT/'tests/samples/geometry_line_replay_M00_postpaste.txt').read_text(encoding='utf-8-sig'))==b,'Hex fixture differs')
    sa,sb=structure(a),structure(b)
    structure_same=sa==sb and sb['two_record_layout_retained'] and len(a)==len(b)==8192 and len(va)==len(vb)==32
    geometry=[]
    if sa['two_record_layout_retained'] and sb['two_record_layout_retained']:
        da={d['name']:d['offset'] for d in sa['descriptors']}; db={d['name']:d['offset'] for d in sb['descriptors']}
        fields=[(f'record[{i}].xyz',sa['record_start']+36*i,sb['record_start']+36*i,3) for i in range(2)]
        fields += [(n+'.bounds',da[n]+off,db[n]+off,6) for n,off in [('CZone',11),('CCourbe',13),('CContour',14)]]
        for name,pa,pb,n in fields:
            x,y=a[pa:pa+8*n],b[pb:pb+8*n]
            xv,yv=struct.unpack('<'+'d'*n,x),struct.unpack('<'+'d'*n,y)
            geometry.append({'name':name,'source_start':pa,'postpaste_start':pb,'length':8*n,'source_hex':x.hex(),'postpaste_hex':y.hex(),'source_values':xv,'postpaste_values':yv,'byte_equal':x==y,'numeric_equal':xv==yv})
    fidelity='unresolved' if not geometry else 'byte_identical' if all(g['byte_equal'] for g in geometry) else 'geometry_equivalent_but_reencoded' if all(g['numeric_equal'] for g in geometry) else 'geometry_transformed'
    known=[('CZone.window',93,109),('CCourbe.window',252,268),('CContour.window',412,428),('record[0].tag',514,518),('record[1].tag',550,554)]
    regions=[{'name':n,'start':lo,'end_exclusive':hi,**diff(a[lo:hi],b[lo:hi])} for n,lo,hi in known]
    for q in regions:
        q['relative_exact_changed_offsets']=q.pop('exact_changed_offsets')
        q['absolute_exact_changed_offsets']=[q['start']+i for i in q['relative_exact_changed_offsets']]
        q['range_offsets_relative_to_region']=q.pop('ranges')
        q['source_hex']=a[q['start']:q['end_exclusive']].hex()
        q['postpaste_hex']=b[q['start']:q['end_exclusive']].hex()
    raw=diff(a,b); version=diff(va,vb)
    known_offsets={i for _,lo,hi in known for i in range(lo,hi)}
    outside=[i for i in raw['exact_changed_offsets'] if i not in known_offsets]
    geometry_offsets={i for g in geometry for i in range(g['source_start'],g['source_start']+g['length'])}
    nongeometry=[i for i in raw['exact_changed_offsets'] if i not in geometry_offsets]
    rewrite='unresolved' if not structure_same else 'observed' if nongeometry else 'not_observed'
    if not structure_same: serialization='structural_change'
    elif a==b and va==vb: serialization='byte_identical'
    elif fidelity=='byte_identical' and nongeometry and va==vb: serialization='opaque_metadata_changed_only'
    elif fidelity!='byte_identical': serialization='geometry_and_metadata_changed' if nongeometry else 'structural_change'
    else: serialization='structural_change'
    classifications={'exact_replay_paste':'accepted','paste_geometry_fidelity':fidelity,'post_paste_reserialization':serialization,'paste_opaque_metadata_rewrite':rewrite,'paste_serialized_identity_behavior':'rewrite_candidate' if rewrite=='observed' else 'preservation_candidate' if rewrite=='not_observed' else 'unresolved','line_clipboard_document_portability':'observed_in_one_replay','opaque_fields_preservation_for_template_mutation':'unresolved','line_clipboard_runtime_readiness':'missing_specific_contract'}
    tail=diff(a[554:8192],b[554:8192])
    tail['range_offsets_relative_to_554']=tail.pop('ranges')
    tail['absolute_exact_changed_offsets']=[554+i for i in tail.pop('exact_changed_offsets')]
    tags=[{'record':i,'source_u32_hex':f'0x{struct.unpack_from("<I",a,p)[0]:08X}','postpaste_u32_hex':f'0x{struct.unpack_from("<I",b,p)[0]:08X}','source_low_byte_hex':a[p:p+1].hex(),'postpaste_low_byte_hex':b[p:p+1].hex(),'source_upper_three_bytes_hex':a[p+1:p+4].hex(),'postpaste_upper_three_bytes_hex':b[p+1:p+4].hex()} for i,p in enumerate([514,550])] if structure_same else []
    next_task='Capture one direction-disambiguating line whose user-defined start point is componentwise greater than its end point; do not synthesize coordinates yet.' if fidelity=='byte_identical' and rewrite=='observed' else 'Perform exactly one bounded duplicate-identity replay experiment before coordinate synthesis.' if serialization=='byte_identical' else 'Perform one file-only analysis of the transformation behavior using the source/post-paste captures; do not manually correct the object.'
    baseline=read(RESEARCH/'exact_replay_paste_baseline.json')
    failures=[f['path'] for f in baseline['files'] if f['path']!='docs/geometry_line_clipboard_contract.md' and (not (ROOT/f['path']).is_file() or sha((ROOT/f['path']).read_bytes())!=f['sha256'])]
    require(not failures,'Protected files changed: '+repr(failures))
    result={'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'analysis_mode':'file_only_after_clipboard_access_closed','offset_convention':'zero-based absolute offsets unless explicitly marked relative; exclusive ends','source':{'bundle':manifest['source_bundle'],'zone_sha256':sha(a),'version_sha256':sha(va)},'postpaste':{'bundle':str(post.relative_to(ROOT)).replace('\\','/'),'zone_sha256':sha(b),'version_sha256':sha(vb)},'structure':{'source':sa,'postpaste':sb,'retained':structure_same,'evaluated_before_semantic_interpretation':True},'geometry_fields':geometry,'typeeditzone_diff':raw,'opaque_windows_and_tags':regions,'record_tags':tags,'changed_offsets_outside_known_windows_and_tags':outside,'non_geometry_changed_offsets':nongeometry,'property_and_tail':{'start':554,'end_exclusive':8192,'includes_descriptor':True,'semantic_extent':'unresolved; not asserted empty or identity-free',**tail},'version':{'source_hex':va.hex(),'postpaste_hex':vb.hex(),**version},'classifications':classifications,'runtime_observations':manifest['runtime_observations'],'interpretation':'Observed differences describe the paste/selection/inspection/Copy lifecycle. No isolated attribution to Paste alone, field identity meaning or duplicate-identity safety is established.','limitations':['One paste into one disposable blank document; no original-object collision tested.','Source bytes were unmodified; arbitrary coordinate mutation is not tested or authorized.','User deselected and inspected vertices/length before Copy, with no edit/save/Undo/Redo reported.','No GUID, timestamp, checksum or object ID semantics assigned.','Document units were not confirmed before load; user subsequently reported 10 mm length and source-equivalent endpoints.'],'integrity':{'protected_baseline_files_unchanged':True,'baseline_tracked_count':len(baseline['files']),'source_loaded_and_postpaste_raw_hashes_verified':True,'postpaste_hex_roundtrip':True},'next_task':next_task}
    (RESEARCH/'exact_replay_paste_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'classifications':classifications,'structure_retained':structure_same,'raw_diff':raw,'known_regions':[{k:q[k] for k in ['name','equal','absolute_exact_changed_offsets']} for q in regions],'outside_known_regions':outside,'tail_equal':tail['equal'],'version_equal':version['equal'],'record_tags':tags,'next_task':next_task},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
