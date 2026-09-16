"""File-only final audit of the single authorized stale probe. Never builds payloads."""
from pathlib import Path
import sys,json,hashlib,struct
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
R=ROOT/'research/geometry-line'
sys.path.insert(0,str(R))
from analyze_exact_replay_paste import structure,diff
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(b): return hashlib.sha256(b).hexdigest()
def need(v,msg):
    if not v: raise RuntimeError(msg)
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=read(R/'stale_opaque_probe_manifest.json')
static=read(R/'staleprobe/static_verification.json')
need(m['human_paste_count']==m['clipboard_load_count']==1,'Runtime count violation')
need(m['clipboard_access_closed_at_utc'] and m['loaded_readback']['both_formats_exact'],'Runtime evidence absent')
zones={};versions={}
for key,name in m['samples'].items():
    folder=ROOT/'tests/samples/bundles/geometry'/name
    need(read(folder/'verification.json')['both_formats_equal'],'Verification absent')
    for f in read(folder/'sha256.json'):
        b=(folder/f['file']).read_bytes()
        need(len(b)==f['size'] and sha(b)==f['sha256'],'Raw source hash mismatch')
    zones[key]=(folder/'typeeditzone.bin').read_bytes()
    versions[key]=(folder/'typeeditzone_version.bin').read_bytes()
    need(bytes.fromhex((ROOT/'tests/samples'/f'{name}.txt').read_text(encoding='utf-8-sig'))==zones[key],'Fixture mismatch')
zones['STALE']=(ROOT/m['candidate_path']).read_bytes()
versions['STALE']=(ROOT/m['version_source']).read_bytes()
need(sha(zones['STALE'])==m['candidate_sha256']==static['candidate_sha256'],'Candidate changed')
for f in m['loaded_readback']['formats']:
    b=(ROOT/f['readback_file']).read_bytes()
    need(b==(ROOT/f['source']).read_bytes() and sha(b)==f['sha256'],'Loaded readback changed')
a,b,c,p=[zones[k] for k in ('E0','E1_vendor','STALE','postpaste')]
need(sha(a)==static['source_hashes']['E0'] and sha(b)==static['source_hashes']['E1_vendor'],'Static source mismatch')
patches=[(518,526),(41,49),(200,208),(360,368)]
patch_offsets={i for lo,hi in patches for i in range(lo,hi)}
need(all(c[lo:hi]==b[lo:hi] for lo,hi in patches),'Transplant mismatch')
need(all(c[i]==a[i] for i in range(8192) if i not in patch_offsets),'E0 remainder mismatch')
structures={k:structure(v) for k,v in zones.items()}
same_structure=all(v==structures['E0'] for v in structures.values()) and structures['E0']['two_record_layout_retained']
need(same_structure and all(len(v)==8192 for v in zones.values()),'Unexpected structure: stop semantic interpretation')
geometry=[]
for name,offset,count in [('record0.xyz',482,3),('record1.xyz',518,3),('CZone.bounds',17,6),('CCourbe.bounds',176,6),('CContour.bounds',336,6)]:
    geometry.append(dict(name=name,start=offset,length=count*8,stored_values={k:struct.unpack_from('<'+'d'*count,v,offset) for k,v in zones.items()},
        ui_mm={k:[x*1000 for x in struct.unpack_from('<'+'d'*count,v,offset)] for k,v in zones.items()},
        postpaste_equals_E1=p[offset:offset+count*8]==b[offset:offset+count*8]))
geometry_equal=all(g['postpaste_equals_E1'] for g in geometry)
comparisons={k:dict(TypeEditZone=diff(v,p),TypeEditZoneVersion=diff(versions[k],versions['postpaste'])) for k,v in zones.items() if k!='postpaste'}
windows=[]
for name,lo,hi in [('CZone.opaque',93,109),('CCourbe.opaque',252,268),('CContour.opaque',412,428),('record0.tag',514,518),('record1.tag',550,554)]:
    windows.append(dict(name=name,start=lo,end_exclusive=hi,hex={k:v[lo:hi].hex() for k,v in zones.items()},
        postpaste_equals={k:v[lo:hi]==p[lo:hi] for k,v in zones.items() if k!='postpaste'},
        exact_changed_offsets_vs_postpaste={k:[lo+i for i in diff(v[lo:hi],p[lo:hi])['exact_changed_offsets']] for k,v in zones.items() if k!='postpaste'}))
tags=[dict(record=i,low_byte={k:v[off:off+1].hex() for k,v in zones.items()},upper_three_bytes={k:v[off+1:off+4].hex() for k,v in zones.items()}) for i,off in enumerate((514,550))]
identical=p==c and versions['postpaste']==versions['STALE']
normalized=p==b and versions['postpaste']==versions['E1_vendor']
outcome='identical_to_stale' if identical else 'normalized_to_vendor_E1' if normalized else 'geometry_matches_E1_but_metadata_other' if geometry_equal else 'geometry_changed'
classes=dict(vendor_edit_pair_valid=True,stale_probe_constructed=True,stale_opaque_paste_acceptance='accepted',
    stale_postpaste_reserialization=outcome,stale_probe_geometry_fidelity='expected' if geometry_equal else 'transformed',
    stale_opaque_state_preservation='observed_in_one_probe' if identical else 'not_observed',
    stale_opaque_state_normalization='observed' if normalized else 'not_observed',
    opaque_fields_preservation_for_template_mutation='candidate_only' if geometry_equal else 'unresolved',
    line_clipboard_synthesis_strategy='template_mutation_candidate' if geometry_equal else 'unresolved',
    line_clipboard_runtime_readiness='missing_specific_contract',line_identity_fields='unresolved',
    line_record_order='creation_direction',line_endpoint_fields='resolved',line_derived_fields='partial')
baseline=read(R/'stale_opaque_probe_baseline.json')
failures=[]
for f in baseline['files']:
    path=ROOT/f['path']
    if not path.is_file(): failures.append(f['path']);continue
    raw=path.read_bytes()
    checked=raw[:f['size']] if f['path']=='docs/geometry_line_clipboard_contract.md' else raw
    if sha(checked)!=f['sha256']:failures.append(f['path'])
need(not failures,'Protected artifact changed: '+repr(failures))
result=dict(schema_version=1,generated_at_utc=datetime.now(timezone.utc).isoformat(),stage='completed',
    analysis_mode='file_only_after_final_capture_verification',offset_convention='zero-based absolute; end exclusive; diff offsets within full payload',
    static_evidence='research/geometry-line/staleprobe/static_verification.json',
    hashes={k:dict(TypeEditZone=sha(v),TypeEditZoneVersion=sha(versions[k])) for k,v in zones.items()},
    structures=structures,structure_retained=same_structure,geometry_fields=geometry,
    vendor_edit_diff=diff(a,b),vendor_difference_partition=static['vendor_difference_partition'],
    stale_probe_geometry_matches_vendor_E1=True,stale_probe_remainder_matches_E0=True,
    comparisons_to_postpaste=comparisons,opaque_windows_and_tags=windows,record_tags=tags,
    property_tail=dict(start=554,end_exclusive=8192,all_equal=all(v[554:]==a[554:] for v in zones.values()),
        sha256={k:sha(v[554:]) for k,v in zones.items()},semantic_status='Opaque stable region; semantic extent unresolved'),
    Version=dict(lengths={k:len(v) for k,v in versions.items()},all_equal=all(v==versions['E0'] for v in versions.values()),hex={k:v.hex() for k,v in versions.items()}),
    classifications=classes,runtime_observations=m['human_ground_truth']['postpaste'],
    scope='One observed single-line family, same-object END.x 10 to 20 mm; four exact vendor-generated eight-byte fields transplanted into E0.',
    interpretation='TypeEdit accepted and preserved E1 geometry with the E0 opaque/non-geometry remainder in this single probe. The postpaste Copy equals the complete STALE payload and unchanged Version. It did not normalize to the vendor E1 serialization.',
    limitations=['No general coordinate mutation safety established.','No field assigned GUID, timestamp, checksum or object ID semantics.',
        'Full Serialize extent, property/tail meaning and derived-field completeness remain unresolved.',
        'One reported human Paste; no automated TypeEdit actions. Automatic selection and geometry inspection method were not separately described.',
        'Target layer name and document units not independently recorded; user reported final endpoints in mm.'],
    integrity=dict(baseline_files_checked=len(baseline['files']),protected_prior_artifacts_unchanged=True,original_contract_prefix_preserved=True,
        E0_E1_postpaste_hashes_verified=True,loaded_readback_verified=True,candidate_static_proof_rechecked=True),
    stop=dict(captures=3,candidate_count=1,clipboard_loads=1,human_pastes=1,additional_runtime_actions_authorized=False))
save(R/'stale_opaque_probe_results.json',result)
m.update(status='completed',final_results='research/geometry-line/stale_opaque_probe_results.json',classifications=classes,
    completed_at_utc=datetime.now(timezone.utc).isoformat())
save(R/'stale_opaque_probe_manifest.json',m)
print(json.dumps(dict(classifications=classes,postpaste_vs_stale_equal=identical,
    postpaste_vs_E0_offsets=comparisons['E0']['TypeEditZone']['exact_changed_offsets'],
    postpaste_vs_E1_ranges=comparisons['E1_vendor']['TypeEditZone']['ranges'],
    tail_equal=result['property_tail']['all_equal'],Version_equal=result['Version']['all_equal'],
    baseline_checked=len(baseline['files'])),indent=2))
