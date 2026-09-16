"""File-only completed mixed-XY probe audit. No payload construction or clipboard access."""
from pathlib import Path
import sys,json,hashlib,struct
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]; R=ROOT/'research/geometry-line'
sys.path.insert(0,str(R))
from analyze_exact_replay_paste import structure,diff
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(b): return hashlib.sha256(b).hexdigest()
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def need(v,msg):
    if not v: raise RuntimeError(msg)
m=read(R/'stale_opaque_probe_2d_manifest.json')
s=read(R/'staleprobe2/static_verification.json')
need(m['clipboard_load_count']==m['human_paste_count']==1,'Bounded count failure')
need(m['clipboard_access_closed_at_utc'] and m['loaded_readback']['both_formats_exact'],'Runtime evidence absent')
z={};ver={}
for k,name in m['samples'].items():
    folder=ROOT/'tests/samples/bundles/geometry'/name
    need(read(folder/'verification.json')['both_formats_equal'],'Capture verification missing')
    for f in read(folder/'sha256.json'):
        raw=(folder/f['file']).read_bytes()
        need(sha(raw)==f['sha256'] and len(raw)==f['size'],'Immutable capture mismatch')
    z[k]=(folder/'typeeditzone.bin').read_bytes()
    ver[k]=(folder/'typeeditzone_version.bin').read_bytes()
    need(bytes.fromhex((ROOT/'tests/samples'/f'{name}.txt').read_text(encoding='utf-8-sig'))==z[k],'Fixture mismatch')
z['STALE2']=(ROOT/m['candidate_path']).read_bytes()
ver['STALE2']=(ROOT/m['version_source']).read_bytes()
need(sha(z['STALE2'])==s['candidate_sha256']==m['candidate_sha256'],'Candidate changed')
for f in m['loaded_readback']['formats']:
    raw=(ROOT/f['readback_file']).read_bytes()
    need(raw==(ROOT/f['source']).read_bytes() and sha(raw)==f['sha256'],'Readback changed')
a,b,c,p=[z[k] for k in ('E0','E1_vendor','STALE2','postpaste')]
need(sha(a)==s['source_hashes']['E0'] and sha(b)==s['source_hashes']['E1_vendor'],'Static sources changed')
fixed=[482,490,518,526,17,25,41,49,176,184,200,208,336,344,360,368]
need([f['start'] for f in s['patch_fields']]==fixed,'Patch set mismatch')
allowed={i for off in fixed for i in range(off,off+8)}
need(all(c[off:off+8]==b[off:off+8] for off in fixed),'Slice mismatch')
need(all(c[i]==a[i] for i in range(8192) if i not in allowed),'Remainder mismatch')
structures={k:structure(v) for k,v in z.items()}
retained=all(v==structures['E0'] for v in structures.values()) and structures['E0']['two_record_layout_retained']
need(retained and all(len(v)==8192 for v in z.values()),'Structure mismatch: stop semantic analysis')
geometry=[]
for name,off,n in [('record0.xyz',482,3),('record1.xyz',518,3),('CZone.bounds',17,6),('CCourbe.bounds',176,6),('CContour.bounds',336,6)]:
    expect=(.015,-.005,0.) if name=='record0.xyz' else (-.01,.012,0.) if name=='record1.xyz' else (-.01,-.005,0.,.015,.012,0.)
    values={k:struct.unpack_from('<'+'d'*n,v,off) for k,v in z.items()}
    need(values['E1_vendor']==expect,'Vendor target mismatch')
    geometry.append(dict(name=name,start=off,length=n*8,stored=values,mm={k:[x*1000 for x in v] for k,v in values.items()},postpaste_expected=values['postpaste']==expect,postpaste_byte_equal_E1=p[off:off+n*8]==b[off:off+n*8]))
gm=all(g['postpaste_expected'] and g['postpaste_byte_equal_E1'] for g in geometry)
comparisons={k:dict(TypeEditZone=diff(v,p),TypeEditZoneVersion=diff(ver[k],ver['postpaste'])) for k,v in z.items() if k!='postpaste'}
regions=[]
for name,lo,hi in [('CZone.opaque',93,109),('CCourbe.opaque',252,268),('CContour.opaque',412,428),('record0.tag',514,518),('record1.tag',550,554),('property_tail',554,8192)]:
    regions.append(dict(name=name,start=lo,end_exclusive=hi,hex={k:v[lo:hi].hex() for k,v in z.items()} if hi<=554 else None,
        sha256={k:sha(v[lo:hi]) for k,v in z.items()},postpaste_equals={k:v[lo:hi]==p[lo:hi] for k,v in z.items() if k!='postpaste'},
        exact_changed_offsets_vs_postpaste={k:[i for i in range(lo,hi) if v[i]!=p[i]] for k,v in z.items() if k!='postpaste'}))
identical=p==c and ver['postpaste']==ver['STALE2']
normalized=p==b and ver['postpaste']==ver['E1_vendor']
outcome='identical_to_stale' if identical else 'normalized_to_vendor_E1' if normalized else 'geometry_matches_E1_but_metadata_other' if gm else 'geometry_changed'
success=identical and gm
classes=dict(m['static_classifications'])
classes.update(broad2d_stale_paste_acceptance='accepted',broad2d_postpaste_reserialization=outcome,broad2d_geometry_fidelity='expected' if gm else 'transformed',
    stale_opaque_state_preservation_2d='observed_in_mixed_xy_probe' if success else 'not_observed',
    broad2d_stale_opaque_state_normalization='observed' if normalized else 'not_observed',
    opaque_fields_preservation_for_template_mutation='strong_candidate' if success else 'candidate_only' if gm else 'unresolved',
    line_clipboard_synthesis_strategy='template_mutation_candidate' if gm else 'unresolved',
    line_2d_template_mutation_readiness='ready_for_static_fail_closed_mutator_design' if success else 'needs_one_more_specific_contract',
    line_clipboard_runtime_readiness='missing_specific_contract',line_identity_fields='unresolved',line_record_order='creation_direction',line_endpoint_fields='resolved',line_derived_fields='partial')
base=read(R/'stale_opaque_probe_2d_baseline.json'); failures=[]
for f in base['files']:
    path=ROOT/f['path']
    if not path.is_file(): failures.append(f['path']);continue
    raw=path.read_bytes()
    check=raw[:f['size']] if f['path']=='docs/geometry_line_clipboard_contract.md' else raw
    if sha(check)!=f['sha256']: failures.append(f['path'])
need(not failures,'Protected artifacts changed: '+repr(failures))
next_task='Design a static fail-closed 2D single-line template mutator restricted to the observed schema/layout and Z=0; do not paste generated arbitrary lines yet.' if success else 'Analyze the observed normalization using the saved captures.' if normalized else 'Keep template mutation blocked; do not broaden coordinates.'
report=dict(schema_version=1,generated_at_utc=datetime.now(timezone.utc).isoformat(),stage='completed',analysis_mode='file_only_after_final_capture_verification',
    offset_convention='zero-based absolute, end exclusive',static_evidence='research/geometry-line/staleprobe2/static_verification.json',
    hashes={k:dict(TypeEditZone=sha(v),TypeEditZoneVersion=sha(ver[k])) for k,v in z.items()},
    structures=structures,structure_retained=retained,geometry_fields=geometry,
    bounds_sources=dict(min_x='END',max_x='START',min_y='START',max_y='END'),
    vendor_edit_diff=diff(a,b),vendor_difference_partition=s['vendor_difference_partition'],patch_fields=s['patch_fields'],
    comparisons_to_postpaste=comparisons,opaque_tags_and_tail=regions,
    record_tags=[dict(record=i,low_byte={k:v[off:off+1].hex() for k,v in z.items()},upper_three_bytes={k:v[off+1:off+4].hex() for k,v in z.items()}) for i,off in enumerate((514,550))],
    Version=dict(lengths={k:len(v) for k,v in ver.items()},all_equal=all(v==ver['E0'] for v in ver.values()),hex={k:v.hex() for k,v in ver.items()}),
    classifications=classes,runtime_observations=m['human_ground_truth']['postpaste'],
    interpretation='In this one mixed-XY transition, TypeEdit accepted and preserved E1 ordered endpoints and mixed min/max bounds with E0 opaque/non-patched remainder. Full postpaste serialization equals STALE2; vendor E1 opaque state was not restored.',
    readiness_scope='Static fail-closed design only; observed single-line schema/layout; unchanged Z=0; mm-tested convention. Not arbitrary generated-line Paste authorization or full XYZ readiness.',
    rationale='Prior END.x-only and current mixed-XY probes both preserved intentionally stale remainder. This strengthens a restricted template-mutation candidate but does not resolve all framing, derived-field or identity semantics.',
    limitations=['Only one mixed-XY vendor pair and one STALE2 Paste.','No Z mutation tested.','Property/tail remains opaque; full Serialize extent and derived-field completeness remain unresolved.',
        'No GUID, object ID, timestamp or checksum semantics inferred.','CLI object count records human intent, not independently measured document totals.',
        'User reported automatic single-curve selection and expected geometry; inspection method not specified.'],
    integrity=dict(baseline_files_checked=len(base['files']),protected_prior_artifacts_unchanged=True,original_contract_prefix_preserved=True,raw_hashes_and_loaded_readback_verified=True),
    stop=dict(capture_count=3,candidate_count=1,clipboard_load_count=1,human_paste_count=1,clipboard_access='closed',further_runtime_actions=False),next_task=next_task)
save(R/'stale_opaque_probe_2d_results.json',report)
m.update(status='completed',completed_at_utc=datetime.now(timezone.utc).isoformat(),classifications=classes,final_results='research/geometry-line/stale_opaque_probe_2d_results.json',next_task=next_task)
save(R/'stale_opaque_probe_2d_manifest.json',m)
print(json.dumps(dict(classifications=classes,postpaste_equals_STALE2=identical,postpaste_vs_E0_changed_bytes=comparisons['E0']['TypeEditZone']['changed_byte_count'],
    postpaste_vs_E1_ranges=comparisons['E1_vendor']['TypeEditZone']['ranges'],version_equal=report['Version']['all_equal'],
    baseline_files_checked=len(base['files']),next_task=next_task),indent=2))
