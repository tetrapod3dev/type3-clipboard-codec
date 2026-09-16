"""Stored-evidence reassessment only; no constructed/modified clipboard payloads."""
from pathlib import Path
import json, hashlib, math, struct
from datetime import datetime, timezone
from analyze_exact_replay_paste import structure
ROOT=Path(__file__).resolve().parents[2]; R=ROOT/'research/geometry-line'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()
B=['L00_N','L01','L02','L04','LY0','LZ']
S={s:'geometry_line_'+s for s in ['L00']+B}
S.update({s:'geometry_line_meta_'+s for s in ['M00','M00_R1','M00_R2','M00_ER','M00_N']})
S.update(D00='geometry_line_direction_D00',replay='geometry_line_replay_M00_postpaste',R2_first='geometry_line_duplicate_R2_preexisting_M00',R2_second='geometry_line_duplicate_R2_second_M00')
WIN={'CZone':(93,109),'CCourbe':(252,268),'CContour':(412,428),'record0.tag.upper':(515,518),'record1.tag.upper':(551,554)}
def require(ok,msg):
    if not ok: raise ValueError(msg)
def grouped(offsets,key=lambda i:None):
    out=[]
    for i in sorted(offsets):
        k=key(i)
        if out and out[-1]['end_exclusive']==i and out[-1]['role']==k: out[-1]['end_exclusive']=i+1
        else: out.append({'start':i,'end_exclusive':i+1,'role':k})
    for r in out:r['length']=r['end_exclusive']-r['start']
    return out

def main():
    old=read(R/'differential_results.json'); micro=read(R/'metadata_variability_results.json')
    replay=read(R/'exact_replay_paste_results.json'); r2=read(R/'duplicate_identity_replay_R2_results.json'); direction=read(R/'direction_disambiguation_results.json')
    require(direction['classifications']['line_endpoint_fields']=='resolved','Endpoint contract absent')
    require(r2['classifications']['duplicate_identity_replay']=='accepted_two_objects','Accepted R2 missing')
    blobs={};versions={};samples={}
    for sid,name in S.items():
        folder=ROOT/'tests/samples/bundles/geometry'/name
        b=(folder/'typeeditzone.bin').read_bytes();v=(folder/'typeeditzone_version.bin').read_bytes()
        require(len(b)==8192 and len(v)==32,sid+' size')
        st=structure(b);require(st['two_record_layout_retained'] and st['record_start']==482 and st['expected_schema_family'],sid+' structure')
        expected=old['samples'][sid] if sid in old['samples'] else micro['samples'][sid] if sid in micro['samples'] else None
        if expected:require(sha(b)==expected['sha256'] and sha(v)==expected['version_sha256'],sid+' recorded hash')
        else:
            hashes=read(folder/'sha256.json')
            require(all(sha((folder/x['file']).read_bytes())==x['sha256'] for x in hashes),sid+' recorded hash')
        xyz=[struct.unpack_from('<3d',b,p) for p in (482,518)]
        bounds=[struct.unpack_from('<6d',b,p) for p in (17,176,336)]
        delta=tuple(y-x for x,y in zip(*xyz));length=math.sqrt(sum(x*x for x in delta))
        samples[sid]={'bundle':str(folder.relative_to(ROOT)).replace('\\','/'),'sha256':sha(b),'version_sha256':sha(v),'xyz_stored':xyz,'xyz_mm':[[x*1000 for x in p] for p in xyz],'bounds':bounds,'delta':delta,'length_mm':length*1000,'orientation':tuple(x/length for x in delta),'opaque_hex':{n:b[lo:hi].hex() for n,(lo,hi) in WIN.items()},'tags_u32':[f'0x{struct.unpack_from("<I",b,p)[0]:08X}' for p in (514,550)],'tag_low_hex':[b[p:p+1].hex() for p in (514,550)]}
        blobs[sid]=b;versions[sid]=v
    allow=[]
    for i,start in enumerate((482,518)):
        for axis,a in enumerate('xyz'):allow.append({'field':f'record{i}.{a}','start':start+8*axis,'length':8,'status':'resolved','scope':'Location, binary64 mm/1000 and human START/END mapping; no write executed'})
    for name,start,rel in [('CZone',17,11),('CCourbe',176,13),('CContour',336,14)]:
        for i,label in enumerate(['min_x','min_y','min_z','max_x','max_y','max_z']):allow.append({'field':name+'.'+label,'start':start+8*i,'length':8,'descriptor_relative_offset':rel+8*i,'status':'candidate_only','mapping_status':'observed resolved min/max ordering','scope':'Formula/locations observed; safe writable-set completeness and general rounding remain unproven'})
    allowed={i for f in allow for i in range(f['start'],f['start']+f['length'])}
    def role(i):
        if any(p<=i<p+24 for p in (482,518)):return 'primary endpoint'
        if any(p<=i<p+48 for p in (17,176,336)):return 'derived bounds'
        if any(lo<=i<hi for n,(lo,hi) in WIN.items() if '.tag' not in n):return 'opaque metadata'
        if 514<=i<518 or 550<=i<554:return 'tag bytes'
        return 'unknown'
    def compare(a,b):
        offsets=[i for i in range(8192) if blobs[a][i]!=blobs[b][i]]
        ranges=grouped(offsets,role)
        for r in ranges:r.update(before_hex=blobs[a][r['start']:r['end_exclusive']].hex(),after_hex=blobs[b][r['start']:r['end_exclusive']].hex())
        return {'base':a,'sample':b,'exact_changed_offsets':offsets,'changed_ranges':ranges,'counts':{k:sum(role(i)==k for i in offsets) for k in ['primary endpoint','derived bounds','opaque metadata','tag bytes','unknown']}}
    baseline_pairs=[compare('L00_N',s) for s in B[1:]]
    transitions=[compare(a,b) for a,b in zip(B,B[1:])]
    profiles={}
    for name,(lo,hi) in WIN.items():
        values={s:blobs[s][lo:hi].hex() for s in B}
        profiles[name]={'raw_hex':values,'relative_to_B_baseline':{s:'unchanged' if values[s]==values[B[0]] else 'changed' for s in B},'successive_capture_transitions':[{ 'from':a,'to':b,'changed':values[a]!=values[b]} for a,b in zip(B,B[1:])],'profile':'changed only for Z translation in this sampled sequence; not a Z-specific law' if name=='CZone' else 'changed at every captured edit/restoration stage, including XY and Z' if name in ('CCourbe','CContour') else 'unchanged across all B variants'}
    # Only observed equal-input/different-output counterexamples, not a fitted function.
    relations={}
    feature=lambda s:{'start_xyz':samples[s]['xyz_stored'][0],'end_xyz':samples[s]['xyz_stored'][1],'bounds':samples[s]['bounds'][0],'translation_invariant_displacement':samples[s]['delta'],'orientation':samples[s]['orientation'],'length':samples[s]['length_mm'],'full_ordered_geometry':samples[s]['xyz_stored']}
    for name,(lo,hi) in WIN.items():
        tests={}
        for f in feature('M00'):
            groups={}
            for s in S:groups.setdefault(json.dumps(feature(s)[f]),[]).append(s)
            violations=[ids for ids in groups.values() if len({blobs[s][lo:hi] for s in ids})>1]
            tests[f]={'equal_feature_different_bytes_groups':violations,'deterministic_function_status':'refuted_by_observed_counterexample' if violations else 'not_established; finite consistency is not proof'}
        relations[name]={'feature_tests':tests,'edit_event': 'Candidate association, not deterministic formula; B captures contain restoration/history and L01 Undo confounds','lineage':'Same-geometry C vs D candidate difference' if blobs['M00'][lo:hi]!=blobs['M00_N'][lo:hi] else 'No C vs D change observed; no universal lineage claim','translation':'CZone changes at LZ only among sampled B edits; Z vs whole-object command/history not separable' if name=='CZone' else 'One Z translation; no deterministic translation rule inferred'}
    er=compare('M00','M00_ER')
    require(all(blobs['M00'][i]==blobs['M00_ER'][i] for i in allowed),'ER geometry not identical')
    geometry_novel_matches=[s for s in S if any(blobs[s][i]!=blobs['M00'][i] for i in allowed) and all(blobs[s][i]==blobs['M00'][i] for i in range(8192) if i not in allowed)]
    tail_equal=len({b[554:] for b in blobs.values()})==1
    zero_start=max(max(i for i,x in enumerate(b) if x!=0)+1 for b in blobs.values())
    # Exhaustive preserve partition: every byte outside the 192-byte hypothetical allowlist.
    def preserve_role(i):
        if i<6:return 'outer prefix'
        if any(lo<=i<hi for lo,hi in [(6,17),(163,176),(322,336)]):return 'class descriptors'
        if i>=zero_start:return 'trailing zeros (within retained property/tail)'
        if i>=554:return 'CPropertyExtend descriptor/property/tail'
        for n,(lo,hi) in WIN.items():
            if lo<=i<hi:return n+' opaque' if '.tag' not in n else n
        if i in (514,550):return 'record tag low byte'
        if 506<=i<514 or 542<=i<550:return 'record w'
        if 460<=i<466:return 'CObDao ASCII marker; enclosing metadata extent unresolved'
        return 'other metadata/framing (includes unresolved CObDao context)'
    preserve=grouped(set(range(8192))-allowed,preserve_role)
    for q in preserve:
        n=q['role'];lo,hi=q['start'],q['end_exclusive']
        status='unresolved' if ('opaque' in n or 'upper' in n or 'CObDao' in n or 'other metadata' in n) else 'candidate_only'
        q.update(preservation_status=status,stable_across_all_samples=len({b[lo:hi] for b in blobs.values()})==1,reason='Observed stability/replay only; no mutation acceptance test' if status=='candidate_only' else 'Unknown state, linkage or semantic extent; cannot certify stale-state preservation')
    require(sum(f['length'] for f in allow)==192 and sum(q['length'] for q in preserve)==8000,'Coverage gap')
    version_equal=len(set(versions.values()))==1
    table=[
      ['record xyz','ordered primary endpoints','yes, resolved mapping','values return on restore','not needed for coordinate mapping','yes','must update; field mapping resolved'],
      ['three bounds','derived min/max blocks','yes, accepted observed formula','return on restore','not needed for formula','yes','must update; complete writable contract candidate_only'],
      ['CZone opaque','unknown, distinct profile','not pure final-geometry function across C/D; B Z association only','not observed in C restore; B Z/history confounded','candidate: C/D differ','yes','unresolved'],
      ['CCourbe opaque','unknown edit/lineage-variable candidate','not pure final geometry (same-C counterexample)','candidate: M00_ER differs','candidate: C/D differ','yes','unresolved'],
      ['CContour opaque','unknown edit/lineage-variable candidate','not pure final geometry (same-C counterexample)','candidate: M00_ER differs','candidate: C/D differ','yes','unresolved'],
      ['record0 tag','low 0D; upper uninterpreted','no B edit variation; cross-context variation not a geometry rule','not observed for B/ER','C/D same; earlier cross-object differences confounded','yes','low candidate_only; upper unresolved'],
      ['record1 tag','low 0D; upper uninterpreted','no B edit variation; same geometry C/D differs','not observed for B/ER','candidate: C/D high bytes differ','yes','low candidate_only; upper unresolved'],
      ['property/tail','opaque stable retained region','variation not observed','variation not observed','variation not observed','yes','candidate_only; extent/semantics unresolved'],
      ['Version','32-byte uninterpreted format','variation not observed','variation not observed','variation not observed','yes','candidate_only; no regenerated version'],
      ['other unchanged bytes','prefix/descriptors/w/unknown metadata','not established','not established','not established','yes','candidate_only for fixed framing/w; unknown metadata unresolved']]
    classes={'opaque_metadata_pure_function_of_geometry':'no','opaque_metadata_replay_preservation':'observed','synthetic_state_novelty':True,'coordinate_patch_allowlist':'partial','opaque_fields_preservation_for_template_mutation':'unresolved','line_clipboard_synthesis_strategy':'unresolved','line_clipboard_runtime_readiness':'missing_specific_contract','line_record_order':'creation_direction','line_endpoint_fields':'resolved','line_derived_fields':'partial','line_identity_fields':'unresolved'}
    reasons={'safe_candidate':['Resolved endpoint order/xyz and observed min/max fields identify a narrow proposed edit set.','Exact replay and R2 preserve the complete existing M00 state; immediate exact-state coexistence observed.','B tags/w and property/tail/Version remain stable through observed edits.'], 'unsafe_candidate':['A proposed different-geometry/old-M00-metadata combination is unobserved; replay has not tested stale metadata.','Vendor edits change CCourbe/CContour even after restoration, so simply carrying them forward differs from observed edit lifecycle.','CZone change at whole-object Z step cautions against treating every opaque window as a fixed lineage marker.'], 'unknown':['No demonstrated rejection of stale metadata; cannot label preservation proven unsafe/unsupported.','No exact field meanings, references or complete Serialize extent.','No evidence that the three bounds exhaust derived state; unknown bytes may encode dependencies.','One tested family/session context cannot establish general version/property/tag safety.']}
    result={'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Stored files only; no synthetic payload constructed, no writes to byte arrays, no clipboard/native/vendor interaction','classifications':classes,'samples':samples,'B_baseline_pairs':baseline_pairs,'B_successive_profiles':transitions,'B_opaque_profiles':profiles,'B_provenance_limit':'L00_N is documented B, unlike L00 A; repeated copies and near-same construction, prior move/Undo in L01 and later restoration history remain confounders. Every-edit means every saved edited sample, not every unobserved UI step.','simple_relationship_tests':relations,'edit_restore_counterexample':er,'pure_geometry_conclusion':'The combined opaque metadata, specifically CCourbe and CContour windows, is NOT a pure function of final geometry: same C and byte-identical endpoints/bounds have different windows after edit/restore. This does not rule out dependence on geometry plus history or on other unobserved state.','replay_conclusion':'TypeEdit accepts and preserves existing self-consistent opaque state in exact replay and duplicate R2; stale opaque state after coordinate mutation was never tested.','synthetic_state_novelty_scope':{'new_geometry_with_entire_M00_preserve_complement_seen_in_stored_corpus':geometry_novel_matches,'meaning':'For a genuinely new geometry using old M00 preserved state, no vendor witness exists in these stored samples. Not a claim about unseen geometries or a no-op mutation.'},'hypothetical_patch_allowlist':allow,'allowlist_bytes':192,'allowlist_status_reason':'Six endpoint scalar mappings resolved. Eighteen bounds scalars have observed formula/locations but candidate write authorization; complete derived/writable set remains unproven. No mutator is built.','complete_preserve_partition':preserve,'preserve_bytes':8000,'separate_version_preservation':{'start':0,'length':32,'status':'candidate_only'},'decision_table':{'columns':['Region','Role','Geometry dependent?','Edit-history dependent?','Lineage dependent?','Replay-preserved?','Safe to preserve during coordinate mutation?'],'rows':table},'mutation_reasoning':reasons,'tail':{'start':554,'end_exclusive':8192,'length':7638,'all_16_equal':tail_equal,'sha256_by_sample':{s:sha(b[554:]) for s,b in blobs.items()},'semantic_status':'opaque stable region; not safe empty extension'},'trailing_zeros':{'common_start':zero_start,'end_exclusive':8192,'semantic_length':'unresolved; preserve exact captured capacity, do not regenerate padding'},'Version':{'all_equal':version_equal,'status':'version_payload_variation_not_observed_in_tested_family' if version_equal else 'variation_observed','sha256_by_sample':{s:sha(v) for s,v in versions.items()}},'tags':{'low_0D_all_records_all_samples':all(all(blobs[s][p]==13 for p in (514,550)) for s in S),'B_tags_stable':len({blobs[s][514:518]+blobs[s][550:554] for s in B})==1,'M00_to_N_record0_high_equal':blobs['M00'][515:518]==blobs['M00_N'][515:518],'M00_to_N_record1_high_equal':blobs['M00'][551:554]==blobs['M00_N'][551:554]},'excluded_data':'Compromised L00_R and user-withdrawn duplicate trial are not used. Historical integrity inventory may list other files but they are not analysis samples.','next_task':'Perform one bounded vendor-generated edit comparison to determine whether TypeEdit accepts stale opaque metadata after geometry changes before any synthetic mutator is built.','next_task_limit':'Recommendation only. A vendor-generated comparison alone can reveal state changes, not prove stale-state acceptance without a separately specified and authorized intervention. No such intervention is performed here.'}
    require(not geometry_novel_matches,'Novelty conclusion needs review')
    (R/'opaque_template_preservation_reassessment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    md=['# Opaque template preservation: static reassessment','','**Preserving every non-coordinate byte while changing xyz and three bounds remains unresolved.** Endpoint ordering is resolved; no stale-state mutation acceptance has been tested. No synthetic payload was constructed.','','## Evidence and B lineage controls','','Sixteen saved bundles were read: '+', '.join(S)+'. L00_N is the documented B baseline; no geometry-variant causal claim is made against original A/L00. Prior L01 move/Undo, restoration steps and fixed-setting unknowns are retained. Captured copy equality does not undo those limitations.','','## Exact B profiles','', '| Region | L00_N | L01 | L02 | L04 | LY0 | LZ |','| --- | --- | --- | --- | --- | --- | --- |']
    for n,p in profiles.items():md.append('| '+n+' | '+' | '.join(p['relative_to_B_baseline'][s] for s in B)+' |')
    md+=['','Relative to baseline and between successive stored edits, CCourbe/CContour change at every sampled stage; CZone changes only at the LZ step; both tags remain constant. This is association with the recorded operation/history, not a Z-specific or every-UI-edit law.','']
    for n,p in profiles.items():
        md+=['### '+n,'','| Sample | Exact bytes |','| --- | --- |']+[f'| {s} | `{p["raw_hex"][s]}` |' for s in B]+['']
    md+=['## Complete B raw differences','','Every changed byte was assigned by fixed ranges; adjacent runs split at role boundaries. JSON retains individual offsets and before/after bytes.','']
    for pair in baseline_pairs:
        md+=['### L00_N to '+pair['sample'],'','| Range [start,end) | Role | Before | After |','| --- | --- | --- | --- |']
        md += [f'| [{q["start"]},{q["end_exclusive"]}) | {q["role"]} | `{q["before_hex"]}` | `{q["after_hex"]}` |' for q in pair['changed_ranges']]
        md+=['']
    md+=['## Geometry, event and lineage interpretation','',result['pure_geometry_conclusion'],'','The JSON tests repeated start/end/bounds, length, direction and translation-invariant displacement only for equal-feature/different-bytes counterexamples. No checksum search, hash fitting or arbitrary formula was attempted. Equal geometry in C/D also refutes geometry-only explanations for CZone and record1 high bytes. Record0 high bytes are stable in C/D but differ across older contexts; that does not establish lineage tracking. Stable tags under B coordinate edits do not prove arbitrary-mutation safety.','',result['replay_conclusion'],'','Same length/orientation with differing metadata (including baseline vs Z translation) precludes a simple length/orientation-only explanation where the recorded counterexample applies. Edit history, object context and operation type are not independently randomized. Byte-level functions for event or lineage cannot be derived.','','## Decision table','','| '+' | '.join(result['decision_table']['columns'])+' |','| '+' | '.join(['---']*7)+' |']
    md += ['| '+' | '.join(row)+' |' for row in table]
    md+=['','## Hypothetical patch allowlist','','Exactly 192 bytes: six 8-byte xyz scalars and eighteen 8-byte bounds scalars. This is a field-location list, not implemented writes or complete mutation authorization. Endpoint mappings remain resolved; bounds ordering/formula observations are accepted, while bounds write authorization and derived completeness remain candidate-only.','','| Field | Offset | Length | Status |','| --- | ---: | ---: | --- |']
    md += [f'| {f["field"]} | {f["start"]} | 8 | {f["status"]} |' for f in allow]
    md+=['','## Complete preserve partition','','The following nonoverlapping ranges cover every other TypeEditZone byte (8000 total). The CObDao marker is located inside otherwise unresolved metadata; its string is not a separate serialized descriptor. Trailing zeros are a retained-buffer observation, not an established padding/semantic extent.','','| Range | Observed role | Stable in all 16? | Preserve status |','| --- | --- | --- | --- |']
    md += [f'| [{q["start"]},{q["end_exclusive"]}) | {q["role"]} | {q["stable_across_all_samples"]} | {q["preservation_status"]} |' for q in preserve]
    md+=['','Version is separate: [0,32), candidate_only preservation. Property/tail [554,8192) equality across all 16: '+str(tail_equal)+'. Full Version equality: '+str(version_equal)+'. Both tag low bytes are 0x0D in every sample; B high-byte profiles are constant. Stability supports a candidate, not an empty-extension or mutation-safety assertion.','','## Novel state and decision','', 'No different-geometry sample has the entire non-allowlist complement equal to M00. Thus new coordinates + new bounds + old M00 state is unobserved in the stored vendor evidence (`synthetic_state_novelty = true`). This comparison uses existing byte positions only; it does not construct patched bytes.','']
    for k,rs in reasons.items():md += ['### '+k,'']+['- '+x for x in rs]+['']
    md+=['```text']+[k+' = '+str(v).lower() if isinstance(v,bool) else k+' = '+v for k,v in classes.items()]+['```','','No demonstrated rejection warrants unsupported/unsafe as an established fact; replay support is insufficient for supported. Multiple contracts remain open, so this is not a strong candidate with exactly one remaining runtime uncertainty. Full encoding has no evidence advantage while metadata meaning remains unknown.','','Next task only:','',result['next_task'],'',result['next_task_limit'],'','Integrity is recorded separately against the pre-write baseline; all prior bundles/results are required unchanged. No clipboard access, TypeEdit action, new capture, Paste, payload mutation or vendor/native investigation occurred.']
    (R/'opaque_template_preservation_reassessment.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({'classifications':classes,'sample_count':len(S),'B_pair_counts':[{ 'sample':p['sample'],'counts':p['counts']} for p in baseline_pairs],'tail_equal':tail_equal,'Version_equal':version_equal,'common_trailing_zero_start':zero_start,'B_profiles':{n:p['profile'] for n,p in profiles.items()}},indent=2))
if __name__=='__main__':main()
