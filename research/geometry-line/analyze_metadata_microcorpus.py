"""File-only five-sample metadata audit. Never accesses or writes the clipboard."""
from pathlib import Path
import hashlib
import json
import struct
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from analyze_typeeditzone_mfc_archive import analyze_bytes

IDS = ['M00', 'M00_R1', 'M00_R2', 'M00_ER', 'M00_N']
PAIRS = [('M00', 'M00_R1'), ('M00', 'M00_R2'), ('M00_R1', 'M00_R2'), ('M00', 'M00_ER'), ('M00', 'M00_N')]
RESEARCH = ROOT / 'research/geometry-line'
sha = lambda b: hashlib.sha256(b).hexdigest()
read_json = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def runs(offsets):
    result = []
    for p in sorted(offsets):
        if result and result[-1]['end_exclusive'] == p:
            result[-1]['end_exclusive'] = p + 1
        else:
            result.append({'start': p, 'end_exclusive': p + 1})
    for r in result:
        r['length'] = r['end_exclusive'] - r['start']
    return result

def profile(values):
    stable_copy = len(set(values[:3])) == 1
    er = values[0] != values[3]
    independent = values[0] != values[4]
    labels = []
    if not stable_copy:
        labels.append('copy-volatile')
    else:
        if er:
            labels.append('edit-history-variable candidate')
        if independent:
            labels.append('object-lineage-variable candidate')
    if len(set(values)) == 1:
        labels.append('stable')
    return {'stable_across_clean_recopies': stable_copy,
            'copy_observation': 'copy_variability_not_observed' if stable_copy else 'copy_variability_observed',
            'changed_after_edit_restore': er, 'changed_for_independent_D': independent,
            'classifications': labels,
            'confounding': 'ER/D contrasts cannot isolate edit/lineage from observed copy variation' if not stable_copy else None}

def main():
    manifest = read_json(RESEARCH / 'metadata_microcorpus_manifest.json')
    require([x['sample_id'] for x in manifest['completed_samples']] == IDS, 'Need exactly five captures in order')
    require('clipboard_access_closed_at_utc' in manifest, 'Collection must be closed')
    blobs, versions, rows, layouts = {}, {}, {}, {}
    for sid in IDS:
        folder = ROOT / 'tests/samples/bundles/geometry' / ('geometry_line_meta_' + sid)
        meta = read_json(folder / 'capture_metadata.json')
        require(meta['eligible_for_differential'] and not meta['capture']['capture_interference'], sid + ' ineligible provenance')
        verification = meta['capture']['verification']
        require(verification['exit_code'] == 0 and 'typeeditzone_match=true' in verification['output'] and 'typeeditzone_version_match=true' in verification['output'], sid + ' verification absent')
        for entry in meta['capture']['files']:
            data = (folder / entry['file']).read_bytes()
            require(len(data) == entry['size'] and sha(data) == entry['sha256'], sid + ' hash/size mismatch')
        b = (folder / 'typeeditzone.bin').read_bytes()
        v = (folder / 'typeeditzone_version.bin').read_bytes()
        require(len(b) == 8192 and len(v) == 32, sid + ' unexpected buffer sizes')
        fixture = ROOT / 'tests/samples' / ('geometry_line_meta_' + sid + '.txt')
        require(bytes.fromhex(fixture.read_text(encoding='utf-8-sig')) == b, sid + ' hex fixture mismatch')
        audit = analyze_bytes(b, fixture=sid, category='geometry', context_bytes=0)
        desc = [h for h in audit['class_hits'] if h['descriptor_pattern_match']]
        require([(h['class_name'], h['candidate_schema_word']) for h in desc] == [('CZone',1), ('CCourbe',1), ('CContour',2), ('CPropertyExtend',5)], sid + ' descriptor family mismatch')
        d = {h['class_name']: h['descriptor_start'] for h in desc}
        r = d['CContour'] + 160
        require(struct.unpack_from('<II', b, r-8) == (0,2), sid + ' kind/count layout mismatch')
        require(r+72 == d['CPropertyExtend'], sid + ' record extent mismatch')
        layouts[sid] = {'descriptors':d, 'record_start':r}
        records = [list(struct.unpack_from('<4dI', b, r+36*i)) for i in range(2)]
        require([x[:3] for x in records] == [[0.,0.,0.],[0.01,0.,0.]], sid + ' geometry differs from baseline')
        require(all(x[3] == 1.0 for x in records), sid + ' record +24 differs from 1.0')
        rows[sid] = {'raw_size':len(b), 'sha256':sha(b), 'version_size':len(v), 'version_sha256':sha(v), 'version_raw_hex':v.hex(), 'layout':layouts[sid], 'record_values':records, 'capture_metadata':str((folder/'capture_metadata.json').relative_to(ROOT)).replace('\\','/')}
        blobs[sid], versions[sid] = b,v
    require(all(x == layouts['M00'] for x in layouts.values()), 'Layout differs; no guessed alignment')
    d, r = layouts['M00']['descriptors'], layouts['M00']['record_start']
    geometry = []
    for i in range(2):
        geometry.append({'name':f'record[{i}].xyz', 'start':r+36*i, 'length':24, 'classification':'accepted geometry coordinate observations; no promotion'})
    for name, off in [('CZone',11),('CCourbe',13),('CContour',14)]:
        start = d[name]+off
        geometry.append({'name':name+'.bounds','start':start,'length':48,'classification':'geometry-derived (accepted bounds observation)'})
        require(all(blobs[s][start:start+48] == struct.pack('<6d',0,0,0,0.01,0,0) for s in IDS), name + ' bounds differ')
    geometry_offsets = {p for g in geometry for p in range(g['start'],g['start']+g['length'])}
    require(all(len({blobs[s][p] for s in IDS}) == 1 for p in geometry_offsets), 'Geometry byte mismatch')
    byte_profiles = []
    for p in range(8192):
        vals = [blobs[s][p] for s in IDS]
        byte_profiles.append({'offset':p,'values_hex':{s:f'{v:02x}' for s,v in zip(IDS,vals)}, **profile(vals)})
    varying = [p for p in range(8192) if len({blobs[s][p] for s in IDS}) > 1]
    pairs=[]
    for a,b in PAIRS:
        offsets = [p for p in range(8192) if blobs[a][p] != blobs[b][p]]
        nongeo = [p for p in offsets if p not in geometry_offsets]
        pairs.append({'base':a,'sample':b,'raw_equal':not offsets,'changed_byte_count':len(offsets),'exact_changed_offsets':offsets,'changed_ranges':[{**t,'before_hex':blobs[a][t['start']:t['end_exclusive']].hex(),'after_hex':blobs[b][t['start']:t['end_exclusive']].hex()} for t in runs(offsets)],'coordinates_bounds_identical':not (set(offsets)&geometry_offsets),'non_geometry_changed_ranges':runs(nongeo),'version_equal':versions[a]==versions[b], 'version_exact_changed_offsets':[p for p in range(32) if versions[a][p]!=versions[b][p]]})
    def region(name,start,length):
        vals = [blobs[s][start:start+length] for s in IDS]
        return {'name':name,'start':start,'length':length,'raw_hex':{s:v.hex() for s,v in zip(IDS,vals)},**profile(vals),'bytes':byte_profiles[start:start+length]}
    windows = [region(name+'.opaque_window',d[name]+off,16) for name,off in [('CZone',87),('CCourbe',89),('CContour',90)]]
    tags=[]
    for i in range(2):
        p=r+36*i+32
        tags.append({'record_index':i,'u32':{s:f'0x{struct.unpack_from("<I",blobs[s],p)[0]:08X}' for s in IDS},'low_byte':region(f'record[{i}].tag.low_byte',p,1),'upper_three_bytes':region(f'record[{i}].tag.upper_three_bytes',p+1,3)})
    tail=d['CPropertyExtend']
    copy = any(not q['stable_across_clean_recopies'] for q in byte_profiles)
    er = any(q['stable_across_clean_recopies'] and q['changed_after_edit_restore'] for q in byte_profiles)
    lineage = any(q['stable_across_clean_recopies'] and q['changed_for_independent_D'] for q in byte_profiles)
    roles = set()
    for q in byte_profiles:
        if not q['stable_across_clean_recopies']: roles.add('copy_variable')
        if q['stable_across_clean_recopies'] and q['changed_after_edit_restore']: roles.add('edit_state_variable')
        if q['stable_across_clean_recopies'] and q['changed_for_independent_D']: roles.add('lineage_variable')
    classifications={'line_copy_variability':'observed' if copy else 'not_observed','line_edit_history_variability':'observed' if er else ('unresolved' if copy else 'not_observed'),'line_object_lineage_variability':'observed' if lineage else ('unresolved' if copy else 'not_observed'),'line_opaque_metadata_role':('mixed' if len(roles)>1 else next(iter(roles)) if roles else 'stable'),'opaque_fields_preservation_for_template_mutation':'unresolved'}
    baseline=read_json(RESEARCH/'metadata_microcorpus_baseline.json')
    mismatches=[]
    for item in baseline['files']:
        if item['path']=='docs/geometry_line_clipboard_contract.md': continue
        path=ROOT/item['path']
        if not path.is_file() or sha(path.read_bytes()) != item['sha256']:
            mismatches.append(item['path'])
    require(not mismatches,'Pre-existing protected file changed: '+repr(mismatches))
    result={'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'analysis_mode':'file_only_after_all_five_captures; no clipboard access','offset_convention':'zero-based absolute offsets; end_exclusive for ranges','samples':rows,'pairs':pairs,'geometry_ranges':geometry,'all_coordinates_and_bounds_byte_identical':True,'primary_windows':windows,'window_extent_warning':'16-byte observational windows, not established serialized field boundaries','record_tags':tags,'all_non_geometry_varying_ranges':[{**t,'sample_hex':{s:blobs[s][t['start']:t['end_exclusive']].hex() for s in IDS}} for t in runs(varying)],'exact_varying_byte_profiles':[byte_profiles[p] for p in varying],'stable_byte_ranges':runs(set(range(8192))-set(varying)),'version':{'all_five_exact_equal':len(set(versions.values()))==1,'profile':profile([versions[s] for s in IDS]),'semantic_meaning':'unknown'},'property_and_tail':{'start':tail,'length':8192-tail,'includes_descriptor':True,'end_exclusive':8192,'all_five_exact_equal':len({blobs[s][tail:] for s in IDS})==1,'sha256_by_sample':{s:sha(blobs[s][tail:]) for s in IDS},'semantic_extent':'unresolved; not an empty-extension assertion'},'classifications':classifications,'limitations':['One session, one edit/restore cycle, one independently constructed D; absence of variation is scoped to these captures.','Unknown baseline origin/workplane, line style, width and identifiers remain unknown; same settings were reported.','Capture and verification read formats separately; human provenance is not established by byte equality alone.','No field is named GUID, timestamp, checksum or object ID.','No direction disambiguation, paste-time identity/reference evidence or arbitrary geometry mutation safety follows.'],'synthesis_consequence':'Opaque preservation is not established as safe. Edit/restore differences, if observed, prevent treating stable geometry as a sufficient preservation contract; unchanged bytes alone would not settle paste-time identity.','accepted_findings_retained':{'line_object_structure':'partial','line_endpoint_fields':'candidate_only','line_derived_fields':'partial','line_identity_fields':'unresolved','line_clipboard_synthesis_strategy':'unresolved','line_clipboard_runtime_readiness':'missing_specific_contract'},'integrity':{'baseline_tracked_file_count':len(baseline['files']),'preexisting_files_except_authorized_contract_unchanged':True,'five_raw_hash_pairs_and_hex_roundtrips_verified':True},'next_task':'Perform one bounded exact-replay geometry paste experiment using an unmodified vendor-captured bundle to determine TypeEdit\'s paste-time identity/reference behavior; do not synthesize coordinates yet.'}
    for sid in IDS:
        folder=ROOT/'tests/samples/bundles/geometry'/('geometry_line_meta_'+sid)
        require((folder/'typeeditzone.bin').read_bytes()==blobs[sid] and (folder/'typeeditzone_version.bin').read_bytes()==versions[sid], sid+' changed during analysis')
    (RESEARCH/'metadata_variability_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'classifications':classifications,'pairs':[{k:p[k] for k in ['base','sample','raw_equal','changed_byte_count']} for p in pairs],'varying_ranges':runs(varying),'windows':[{k:w[k] for k in ['name','start','stable_across_clean_recopies','changed_after_edit_restore','changed_for_independent_D']} for w in windows],'tags':tags,'version_equal':result['version']['all_five_exact_equal'],'tail_equal':result['property_and_tail']['all_five_exact_equal'],'integrity':result['integrity']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
