"""File-only audit of the bounded two-paste experiment; never accesses clipboard."""
from pathlib import Path
import json
import hashlib
import struct
from datetime import datetime, timezone
from analyze_exact_replay_paste import structure, diff

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research/geometry-line'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()

def require(ok,message):
    if not ok: raise ValueError(message)

def main():
    m=read(R/'duplicate_identity_replay_manifest.json')
    require(m['human_paste_count']==2 and m['clipboard_load_count']==2,'Bounded runtime counts not satisfied')
    require('clipboard_access_closed_at_utc' in m,'Clipboard collection not closed')
    require(m['preexisting_object_exact_M00'],'Precondition not met')
    require(m['first_load_verification']['both_formats_byte_equal'] and m['second_load_verification']['both_formats_byte_equal'],'Load verification absent')
    folders={'source':ROOT/m['source_bundle'],'preexisting':ROOT/'tests/samples/bundles/geometry'/m['preexisting_sample'],'second':ROOT/'tests/samples/bundles/geometry'/m['second_sample']}
    blobs={}; versions={}; rows={}
    for label,folder in folders.items():
        entries=m['source_validation'] if label=='source' else m[label+'_capture']['hashes']
        for f in entries:
            raw=(folder/f['file']).read_bytes()
            require(sha(raw)==f['sha256'] and len(raw)==f['size'],label+' hash/size mismatch')
        if label!='source':
            require(m[label+'_capture']['verification']['both_formats_equal'],label+' immediate verify missing')
            fixture=ROOT/'tests/samples'/(folder.name+'.txt')
            require(bytes.fromhex(fixture.read_text(encoding='utf-8-sig'))==(folder/'typeeditzone.bin').read_bytes(),label+' hex mismatch')
        b=(folder/'typeeditzone.bin').read_bytes(); v=(folder/'typeeditzone_version.bin').read_bytes()
        blobs[label]=b; versions[label]=v
        rows[label]={'bundle':str(folder.relative_to(ROOT)).replace('\\','/'),'zone_size':len(b),'zone_sha256':sha(b),'version_size':len(v),'version_sha256':sha(v),'structure':structure(b)}
    require(blobs['source']==blobs['preexisting'] and versions['source']==versions['preexisting'],'Preexisting equality not retained')
    comparisons=[]
    for x,y in [('source','preexisting'),('source','second'),('preexisting','second')]:
        comparisons.append({'base':x,'sample':y,'typeeditzone':diff(blobs[x],blobs[y]),'version':diff(versions[x],versions[y])})
    a,b=blobs['source'],blobs['second']
    same_structure=rows['source']['structure']==rows['second']['structure'] and rows['second']['structure']['two_record_layout_retained'] and len(a)==len(b)==8192
    known=[('CZone.window',93,109),('CCourbe.window',252,268),('CContour.window',412,428),('record0.tag',514,518),('record1.tag',550,554)]
    windows=[{'name':n,'start':lo,'end_exclusive':hi,'source_hex':a[lo:hi].hex(),'second_hex':b[lo:hi].hex(),'equal':a[lo:hi]==b[lo:hi],'exact_changed_offsets':[i for i in range(lo,hi) if a[i:i+1]!=b[i:i+1]]} for n,lo,hi in known]
    geometry=[]
    if same_structure:
        for name,start,n in [('record0.xyz',482,3),('record1.xyz',518,3),('CZone.bounds',17,6),('CCourbe.bounds',176,6),('CContour.bounds',336,6)]:
            av,bv=a[start:start+8*n],b[start:start+8*n]
            geometry.append({'name':name,'start':start,'length':8*n,'equal':av==bv,'source_values':struct.unpack('<'+'d'*n,av),'second_values':struct.unpack('<'+'d'*n,bv)})
    raw_changes=comparisons[1]['typeeditzone']['exact_changed_offsets']
    known_offsets={i for _,lo,hi in known for i in range(lo,hi)}
    geo_offsets={i for g in geometry for i in range(g['start'],g['start']+g['length'])}
    nongeo=[i for i in raw_changes if i not in geo_offsets]
    exact=a==b and versions['source']==versions['second']
    require(exact or (same_structure and nongeo),'Unexpected profile requires explicit classification review')
    serialization='byte_identical_to_M00' if exact else 'opaque_metadata_changed_only' if all(g['equal'] for g in geometry) and versions['source']==versions['second'] else 'geometry_and_metadata_changed'
    count=m.get('postcapture_object_count',{})
    count_evidence_valid=count.get('method') in ('human ordinary UI select-all object count','human ordinary UI drag-selection object count')
    count_confirmed=count.get('confirmed_count')==2 and count_evidence_valid
    unexpected_count=count_evidence_valid and isinstance(count.get('confirmed_count'),int) and count['confirmed_count']>2
    outcome='accepted_two_objects' if count_confirmed else 'accepted_merge_or_other' if unexpected_count else 'unresolved_object_count'
    coexistence='observed_in_one_document' if count_confirmed and exact else 'unresolved'
    classifications={'duplicate_identity_replay':outcome,'preexisting_object_exact_M00':True,'duplicate_second_object_reserialization':serialization,'duplicate_paste_opaque_rewrite':'not_observed' if not nongeo else 'observed','duplicate_exact_payload_coexistence':coexistence,'line_identity_fields':'unresolved','opaque_fields_preservation_for_template_mutation':'unresolved','line_clipboard_runtime_readiness':'missing_specific_contract'}
    baseline=read(R/'duplicate_identity_replay_baseline.json')
    changed=[f['path'] for f in baseline['files'] if f['path']!='docs/geometry_line_clipboard_contract.md' and (not (ROOT/f['path']).is_file() or sha((ROOT/f['path']).read_bytes())!=f['sha256'])]
    require(not changed,'Protected files changed: '+repr(changed))
    result={'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'analysis_mode':'file_only_after_second_capture_and_verification','samples':rows,'comparisons':comparisons,'structure_retained':same_structure,'geometry':geometry,'known_opaque_regions_and_tags':windows,'changed_offsets_outside_known_regions':[i for i in raw_changes if i not in known_offsets],'property_and_tail':{'start':554,'end_exclusive':8192,'equal':a[554:8192]==b[554:8192],'source_sha256':sha(a[554:8192]),'second_sha256':sha(b[554:8192]),'semantic_extent':'unresolved; not asserted empty or identity-free'},'versions':{'all_three_equal':len(set(versions.values()))==1,'hex_by_sample':{k:v.hex() for k,v in versions.items()}},'classifications':classifications,'object_count_evidence':count,'outcome_interpretation':'Other accepted outcome: three regions selected in basic mode after two reported pastes. No merge, replacement, third paste or source of the extra count is inferred. Exact M00 coexistence remains unresolved.' if unexpected_count else 'See classifications and UI count evidence','automatic_second_selection':m['second_capture']['human_ground_truth'],'first_object_after_second_paste':'Not individually reselected or serialized; unexpected total count does not establish the identities, origin or unchanged state of the selected objects.','limitations':['Opaque ranges are not identified GUID/object ID fields.','One document and one duplicate action; no general session/version/document guarantees.','Document units not explicitly confirmed; first pasted length/position confirmed by user.','No coordinate mutation or direction-disambiguation tested.','No third paste, object movement or edits to separate overlapping objects.','Capture/verify equality establishes raw preservation, not independent proof of human provenance.'],'synthesis_consequence':'Observed exact-payload coexistence, if UI count confirms two objects, lowers concern about necessary immediate collision but cannot establish opaque preservation safety under coordinate mutation.','integrity':{'baseline_tracked_files':len(baseline['files']),'all_preexisting_files_except_authorized_contract_unchanged':True,'all_source_and_captured_hashes_verified':True},'next_task':'Capture one direction-disambiguating line whose user-defined start point is componentwise greater than its end point; do not synthesize coordinates yet.' if count_confirmed else 'Perform one bounded file-and-provenance analysis of the unexpected three-region selection after the two reported pastes; do not paste again or modify payload bytes.' if unexpected_count else 'Object-count confirmation pending; no further paste authorized.'}
    (R/'duplicate_identity_replay_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'classifications':classifications,'full_raw_changed_byte_count':len(raw_changes),'version_equal':result['versions']['all_three_equal'],'structure_retained':same_structure,'object_count_evidence':count},ensure_ascii=False,indent=2))

if __name__=='__main__': main()

