"""One-shot file-only builder for the specifically authorized E0/E1 transition.
No coordinate arguments, reusable setter, clipboard access or TypeEdit automation.
"""
from pathlib import Path
import sys, json, hashlib, struct
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
R = ROOT / 'research/geometry-line'
sys.path.insert(0, str(R))
from analyze_exact_replay_paste import structure, diff

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def need(ok, message):
    if not ok: raise RuntimeError(message)
def save(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    manifest = read(R/'stale_opaque_probe_manifest.json')
    out = R/'staleprobe/stale_E0_geometry_from_E1_typeeditzone.bin'
    need(not out.exists() and not manifest['candidate_constructed'], 'One-shot output already exists')
    folders = [ROOT/'tests/samples/bundles/geometry'/n for n in
               ['geometry_line_staleprobe_E0','geometry_line_staleprobe_E1_vendor']]
    blobs, versions = [], []
    for folder in folders:
        need(read(folder/'verification.json')['both_formats_equal'], 'Capture verification absent')
        for entry in read(folder/'sha256.json'):
            raw = (folder/entry['file']).read_bytes()
            need(sha(raw)==entry['sha256'] and len(raw)==entry['size'], 'Immutable source changed')
        blobs.append((folder/'typeeditzone.bin').read_bytes())
        versions.append((folder/'typeeditzone_version.bin').read_bytes())
    a,b = blobs
    va,vb = versions
    need(sha(a)=='775a3492152249a871e76f6dad53220dadb091f59c757fa8bf6406a3e2108f7d', 'Wrong E0')
    need(sha(b)=='6e056f4f776ed3ffb34028bf77a8c7ffd4ab72e7600acd713352779a5509e6d1', 'Wrong E1')
    sa,sb = structure(a),structure(b)
    need(sa==sb and sa['two_record_layout_retained'] and sa['record_start']==482, 'Structure mismatch')
    need(len(a)==len(b)==8192 and len(va)==len(vb)==32 and va==vb, 'Length/Version mismatch')
    need(a[554:]==b[554:], 'Property/tail changed')
    fields = [('record1.x',518,526),('CZone.max_x',41,49),('CCourbe.max_x',200,208),('CContour.max_x',360,368)]
    known = [('CZone.opaque',93,109),('CCourbe.opaque',252,268),('CContour.opaque',412,428),
             ('record0.tag',514,518),('record1.tag',550,554)]
    geometry = [('record0.xyz',482,3),('record1.xyz',518,3),
                ('CZone.bounds',17,6),('CCourbe.bounds',176,6),('CContour.bounds',336,6)]
    decoded=[]
    for name,p,n in geometry:
        x,y=struct.unpack_from('<'+'d'*n,a,p),struct.unpack_from('<'+'d'*n,b,p)
        expected0 = (0.,0.,0.) if name=='record0.xyz' else (0.01,0.,0.) if name=='record1.xyz' else (0.,0.,0.,0.01,0.,0.)
        expected1 = (0.,0.,0.) if name=='record0.xyz' else (0.02,0.,0.) if name=='record1.xyz' else (0.,0.,0.,0.02,0.,0.)
        need(x==expected0 and y==expected1, 'Geometry mismatch: '+name)
        decoded.append(dict(field=name,start=p,length=n*8,E0_stored=x,E1_stored=y,E0_mm=[v*1000 for v in x],E1_mm=[v*1000 for v in y]))
    rawdiff=diff(a,b)
    partition=[]
    for name,lo,hi in fields+known:
        partition.append(dict(region=name,start=lo,end_exclusive=hi,
                              exact_changed_offsets=[i for i in rawdiff['exact_changed_offsets'] if lo<=i<hi],
                              E0_hex=a[lo:hi].hex(),E1_hex=b[lo:hi].hex()))
    allowed={i for _,lo,hi in fields for i in range(lo,hi)}
    classified={i for _,lo,hi in fields+known for i in range(lo,hi)}
    other=[i for i in rawdiff['exact_changed_offsets'] if i not in classified]
    need(not other, 'Unexpected changed bytes: '+repr(other))
    allgeometry={i for _,p,n in geometry for i in range(p,p+n*8)}
    need(not (set(rawdiff['exact_changed_offsets']) & allgeometry)-allowed, 'Geometry change beyond four fields')
    baseline=read(R/'stale_opaque_probe_baseline.json')
    failures=[f['path'] for f in baseline['files'] if not (ROOT/f['path']).is_file() or sha((ROOT/f['path']).read_bytes())!=f['sha256']]
    need(not failures, 'Baseline artifacts changed: '+repr(failures))
    # The sole output copies vendor bytes, never regenerates floating point values.
    c=bytearray(a)
    for _,lo,hi in fields: c[lo:hi]=b[lo:hi]
    c=bytes(c)
    need(sha(c)=='d3c728869a783a19ca9cc79fa4444fcc07392246cff4edca0f842ed458f6453e', 'Unexpected candidate SHA256')
    geometry_match=all(c[p:p+n*8]==b[p:p+n*8] for _,p,n in geometry)
    remainder_match=all(c[i]==a[i] for i in range(8192) if i not in allowed)
    need(geometry_match and remainder_match, 'Static proof failed')
    need(set(diff(a,c)['exact_changed_offsets'])<=allowed, 'Candidate changed forbidden byte')
    out.write_bytes(c)
    need(out.read_bytes()==c, 'Output readback failed')
    report=dict(schema_version=1,generated_at_utc=datetime.now(timezone.utc).isoformat(),
        stage='static_proof_complete_runtime_not_started',offset_convention='zero-based absolute, exclusive ends',
        source_hashes=dict(E0=sha(a),E1_vendor=sha(b),Version=sha(va)),candidate_sha256=sha(c),
        structure=dict(E0=sa,E1_vendor=sb,identical=True),
        geometry_fields=decoded,version=dict(equal=True,size=32,hex=va.hex(),sha256=sha(va)),
        vendor_diff=rawdiff,vendor_difference_partition=partition,unexpected_changed_offsets=other,
        property_tail=dict(start=554,end_exclusive=8192,byte_identical=True,sha256=sha(a[554:]),semantic_extent='unresolved'),
        transplant_fields=[dict(field=n,start=lo,end_exclusive=hi,E0_hex=a[lo:hi].hex(),E1_hex=b[lo:hi].hex(),STALE_hex=c[lo:hi].hex()) for n,lo,hi in fields],
        stale_vs_E0=diff(a,c),stale_vs_E1=diff(b,c),
        stale_probe_geometry_matches_vendor_E1=geometry_match,stale_probe_remainder_matches_E0=remainder_match,
        version_source='tests/samples/bundles/geometry/geometry_line_staleprobe_E0/typeeditzone_version.bin',
        classifications=dict(vendor_edit_pair_valid=True,stale_probe_constructed=True,
            stale_opaque_paste_acceptance='unresolved',stale_postpaste_reserialization='unavailable',
            stale_probe_geometry_fidelity='unresolved',opaque_fields_preservation_for_template_mutation='unresolved',
            line_clipboard_synthesis_strategy='unresolved',line_clipboard_runtime_readiness='missing_specific_contract'),
        interpretation='Runtime not performed. STALE retains E0 opaque state with E1 geometry; acceptance is unknown.',
        integrity=dict(baseline_files_checked=len(baseline['files']),all_baseline_files_unchanged_before_doc_update=True))
    save(R/'staleprobe/static_verification.json',report)
    save(R/'stale_opaque_probe_results.json',report)
    manifest.update(status='awaiting_explicit_stale_load_approval_and_blank_target',candidate_constructed=True,
                    candidate_sha256=sha(c),static_verification='research/geometry-line/staleprobe/static_verification.json',
                    version_source=report['version_source'],vendor_edit_pair_valid=True,
                    stale_probe_geometry_matches_vendor_E1=True,stale_probe_remainder_matches_E0=True)
    save(R/'stale_opaque_probe_manifest.json',manifest)
    print(json.dumps(dict(candidate_sha256=sha(c),vendor_changed_bytes=len(rawdiff['exact_changed_offsets']),
                         stale_vs_E0_offsets=diff(a,c)['exact_changed_offsets'],
                         stale_vs_E1_ranges=diff(b,c)['ranges'],baseline_files_checked=len(baseline['files']),
                         status=manifest['status']),indent=2))
if __name__=='__main__': main()
