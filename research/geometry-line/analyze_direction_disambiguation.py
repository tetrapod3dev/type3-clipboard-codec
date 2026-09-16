"""One-sample, file-only D00 ordering audit. No clipboard or payload writer."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct
from analyze_exact_replay_paste import structure
ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research/geometry-line'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok: raise ValueError(msg)
def main():
    m=read(R/'direction_disambiguation_manifest.json')
    require(m['capture_attempt_count']==1 and m['capture']['eligible_for_analysis'],'Capture gate failed')
    require(m['capture']['verification']['both_formats_equal'] and not m['capture']['clipboard_interference_reported'],'Verification/provenance failed')
    require('clipboard_access_closed_at_utc' in m,'Clipboard collection not closed')
    folder=ROOT/'tests/samples/bundles/geometry'/m['sample_name']
    for f in m['capture']['hashes']:
        data=(folder/f['file']).read_bytes()
        require(len(data)==f['size'] and sha(data)==f['sha256'],'Capture hash mismatch')
    b=(folder/'typeeditzone.bin').read_bytes(); v=(folder/'typeeditzone_version.bin').read_bytes()
    require(bytes.fromhex((ROOT/'tests/samples'/ (m['sample_name']+'.txt')).read_text(encoding='utf-8-sig'))==b,'Hex roundtrip failed')
    s=structure(b)
    expected_offsets={'CZone':6,'CCourbe':163,'CContour':322,'CPropertyExtend':554}
    matches=s['expected_schema_family'] and s['two_record_layout_retained'] and {d['name']:d['offset'] for d in s['descriptors']}==expected_offsets and s['record_start']==482 and len(b)==8192
    records=[]; bounds=[]; order='other_or_unresolved'; direction=False; minmax=False
    if matches:
        for i in range(2):
            start=s['record_start']+36*i
            raw=b[start:start+24]; xyz=struct.unpack('<3d',raw)
            records.append({'index':i,'start':start,'xyz_raw_hex':raw.hex(),'stored_xyz':xyz,'ui_mm_xyz':[x*1000 for x in xyz]})
        hi=struct.pack('<3d',0.01,0.01,0.0); lo=struct.pack('<3d',0.0,0.0,0.0)
        actual=[bytes.fromhex(r['xyz_raw_hex']) for r in records]
        direction=actual==[hi,lo]; minmax=actual==[lo,hi]
        if direction and not minmax: order='creation_direction'
        elif minmax and not direction: order='componentwise_minmax'
        expected=struct.pack('<6d',0,0,0,0.01,0.01,0)
        for name,off in [('CZone',11),('CCourbe',13),('CContour',14)]:
            start=expected_offsets[name]+off
            raw=b[start:start+48]
            values=struct.unpack('<6d',raw)
            bounds.append({'name':name,'descriptor_relative_offset':off,'start':start,'raw_hex':raw.hex(),'stored_values':values,'ui_mm_values':[x*1000 for x in values],'expected_raw_hex':expected.hex(),'byte_exact_expected':raw==expected})
    bounds_ok=matches and all(x['byte_exact_expected'] for x in bounds)
    resolved=matches and bounds_ok and (direction != minmax)
    opaque=[{'name':n,'start':lo,'end_exclusive':hi,'raw_hex':b[lo:hi].hex(),'meaning':'uninterpreted provenance only'} for n,lo,hi in [('CZone',93,109),('CCourbe',252,268),('CContour',412,428),('record0.tag',514,518),('record1.tag',550,554)]]
    mv=(ROOT/'tests/samples/bundles/geometry/geometry_line_meta_M00/typeeditzone_version.bin').read_bytes()
    classifications={'line_record_order':order,'line_endpoint_fields':'resolved' if resolved else 'candidate_only','line_derived_fields':'partial','line_identity_fields':'unresolved','opaque_fields_preservation_for_template_mutation':'unresolved','line_clipboard_runtime_readiness':'missing_specific_contract'}
    baseline=read(R/'direction_disambiguation_baseline.json')
    changed=[f['path'] for f in baseline['files'] if f['path']!='docs/geometry_line_clipboard_contract.md' and (not (ROOT/f['path']).is_file() or sha((ROOT/f['path']).read_bytes())!=f['sha256'])]
    require(not changed,'Protected files changed: '+repr(changed))
    result={'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'sample':m['sample_name'],'mode':'file_only_after_raw_preservation_and_immediate_verification','source_sha256':sha(b),'source_size':len(b),'human_ground_truth':m['human_ground_truth'],'fixed_settings':m['fixed_settings'],'structure':s,'structure_matches_observed_family':matches,'coordinates_read_only_after_structure_pass':True,'records':records,'hypothesis_tests':{'creation_direction_byte_exact':direction,'componentwise_minmax_byte_exact':minmax,'predictions_mutually_exclusive':True,'conversion':'accepted little-endian binary64 mm/1000; report mm via *1000','no_alternative_float_search':True},'bounds':bounds,'all_bounds_byte_exact_expected':bounds_ok,'opaque_provenance':opaque,'version':{'size':len(v),'expected_32_bytes':len(v)==32,'sha256':sha(v),'raw_hex':v.hex(),'M00_sha256':sha(mv),'exact_equal_M00':v==mv,'meaning':'not inferred'},'classifications':classifications,'endpoint_resolution_scope':'Observed single-line family, established xyz slots and the two specified ordering hypotheses; based on human UI vertex/start-point direction. Not all arbitrary serializers, geometries or native identities.','geometry_wording':'START exceeds END in X/Y, ties in Z; opposite predicted record orders remain unambiguous.','limitations':['Exact construction tool sequence and UI command names not supplied; no same-family construction assertion.','Line style/width, origin/workplane, identifiers and precision remain unknown.','Raw equality does not independently establish human selection/direction provenance.','No synthesis, Paste, identity interpretation, full Serialize extent, property/tail semantic closure or derived completeness claim.'],'integrity':{'baseline_file_count':len(baseline['files']),'preexisting_files_except_authorized_contract_unchanged':True,'raw_hashes_and_hex_roundtrip_verified':True},'next_task':'Reassess whether the observed opaque metadata can be safely carried through a minimal coordinate-template mutation now that endpoint ordering is resolved; do not generate or paste a synthetic payload yet.' if resolved else 'Capture one line with UI-confirmed START (10,20,0) and END (0,0,0), after establishing explicit start/end ground truth; do not synthesize or paste.'}
    (R/'direction_disambiguation_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'structure_matches':matches,'records':records,'bounds_match':bounds_ok,'version_equal_M00':v==mv,'classifications':classifications},ensure_ascii=True,indent=2))
if __name__=='__main__': main()
