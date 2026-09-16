"""One-shot mixed-XY research builder bound to fixed input/output hashes and 16 fields.
No geometry arguments, reusable coordinate setter, clipboard or TypeEdit access.
"""
from pathlib import Path
import sys,json,hashlib,struct
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
R=ROOT/'research/geometry-line'
sys.path.insert(0,str(R))
from analyze_exact_replay_paste import structure,diff
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
m=read(R/'stale_opaque_probe_2d_manifest.json')
out=R/'staleprobe2/stale2_E0_geometry_from_E1_typeeditzone.bin'
need(not out.exists() and not m['candidate_constructed'],'One-shot already constructed')
blobs=[];versions=[]
for name in ['geometry_line_staleprobe2_E0','geometry_line_staleprobe2_E1_vendor']:
    folder=ROOT/'tests/samples/bundles/geometry'/name
    need(read(folder/'verification.json')['both_formats_equal'],'Capture verification absent')
    for f in read(folder/'sha256.json'):
        raw=(folder/f['file']).read_bytes()
        need(sha(raw)==f['sha256'] and len(raw)==f['size'],'Source integrity failure')
    blobs.append((folder/'typeeditzone.bin').read_bytes())
    versions.append((folder/'typeeditzone_version.bin').read_bytes())
a,b=blobs
va,vb=versions
need(sha(a)=='1025dbbb0cb5101992147a0fc21acccf3b0087e1fd44fc924855dedef0307a4b','Wrong E0')
need(sha(b)=='cf7a071c69e30abb923462e197388f86ec469a37be838c614f967a96984eae9d','Wrong E1')
sa,sb=structure(a),structure(b)
need(sa==sb and sa['two_record_layout_retained'] and sa['record_start']==482,'Structure mismatch')
need(len(a)==len(b)==8192 and len(va)==len(vb)==32 and va==vb,'Length or Version mismatch')
need(a[554:]==b[554:],'Property/tail changed')
fields=[('record0.x',482),('record0.y',490),('record1.x',518),('record1.y',526),
        ('CZone.min_x',17),('CZone.min_y',25),('CZone.max_x',41),('CZone.max_y',49),
        ('CCourbe.min_x',176),('CCourbe.min_y',184),('CCourbe.max_x',200),('CCourbe.max_y',208),
        ('CContour.min_x',336),('CContour.min_y',344),('CContour.max_x',360),('CContour.max_y',368)]
need([(f['field'],f['start'],f['end_exclusive']) for f in m['allowed_transplants']]==[(n,p,p+8) for n,p in fields],'Allowlist mismatch')
known=[('CZone.opaque',93,109),('CCourbe.opaque',252,268),('CContour.opaque',412,428),('record0.tag',514,518),('record1.tag',550,554)]
geometry=[('record0.xyz',482,3),('record1.xyz',518,3),('CZone.bounds',17,6),('CCourbe.bounds',176,6),('CContour.bounds',336,6)]
decoded=[]
for n,p,count in geometry:
    x,y=struct.unpack_from('<'+'d'*count,a,p),struct.unpack_from('<'+'d'*count,b,p)
    ex0=(0.,0.,0.) if n=='record0.xyz' else (.01,0.,0.) if n=='record1.xyz' else (0.,0.,0.,.01,0.,0.)
    ex1=(.015,-.005,0.) if n=='record0.xyz' else (-.01,.012,0.) if n=='record1.xyz' else (-.01,-.005,0.,.015,.012,0.)
    need(x==ex0 and y==ex1,'Unexpected geometry: '+n)
    decoded.append(dict(name=n,start=p,length=count*8,E0_stored=x,E1_stored=y,E0_mm=[v*1000 for v in x],E1_mm=[v*1000 for v in y]))
allowed={i for _,p in fields for i in range(p,p+8)}
known_offsets={i for _,lo,hi in known for i in range(lo,hi)}
d=diff(a,b)
unknown=[i for i in d['exact_changed_offsets'] if i not in allowed|known_offsets]
need(not unknown,'Unexpected difference outside fixed XY/opaque/tag ranges: '+repr(unknown))
partition=[]
for n,lo,hi in [(n,p,p+8) for n,p in fields]+known:
    partition.append(dict(region=n,start=lo,end_exclusive=hi,E0_hex=a[lo:hi].hex(),E1_hex=b[lo:hi].hex(),exact_changed_offsets=[i for i in d['exact_changed_offsets'] if lo<=i<hi]))
baseline=read(R/'stale_opaque_probe_2d_baseline.json')
failures=[f['path'] for f in baseline['files'] if not (ROOT/f['path']).is_file() or sha((ROOT/f['path']).read_bytes())!=f['sha256']]
need(not failures,'Protected files changed: '+repr(failures))
c=bytearray(a)
for _,p in fields:c[p:p+8]=b[p:p+8]
c=bytes(c)
need(sha(c)=='7b91e443c0927a3879ad2373bbd5f7457ba2f9f8362e87a9e5c10cd9a7f7f574','Unexpected candidate hash')
gm=all(c[p:p+n*8]==b[p:p+n*8] for _,p,n in geometry)
rm=all(c[i]==a[i] for i in range(8192) if i not in allowed)
need(gm and rm,'Geometry/remainder verification failed')
need(set(diff(a,c)['exact_changed_offsets'])<=allowed,'Candidate changed forbidden range')
need(set(diff(b,c)['exact_changed_offsets'])<=known_offsets,'STALE2 vs E1 unexpected difference')
out.write_bytes(c)
need(out.read_bytes()==c,'Output readback mismatch')
classes=dict(broad2d_vendor_pair_valid=True,broad2d_stale_constructed=True,broad2d_geometry_matches_vendor_E1=gm,broad2d_remainder_matches_E0=rm,
    broad2d_stale_paste_acceptance='unresolved',broad2d_postpaste_reserialization='unavailable',broad2d_geometry_fidelity='unresolved',
    opaque_fields_preservation_for_template_mutation='candidate_only',line_clipboard_synthesis_strategy='template_mutation_candidate',
    line_2d_template_mutation_readiness='unresolved',line_clipboard_runtime_readiness='missing_specific_contract')
report=dict(schema_version=1,generated_at_utc=datetime.now(timezone.utc).isoformat(),stage='static_complete_awaiting_runtime_approval',
    offset_convention='zero-based absolute, end exclusive',source_hashes=dict(E0=sha(a),E1_vendor=sha(b),Version=sha(va)),
    candidate_path=str(out.relative_to(ROOT)).replace('\\','/'),candidate_sha256=sha(c),
    structures=dict(E0=sa,E1_vendor=sb),geometry_fields=decoded,
    endpoint_order='creation_direction',bounds_sources=dict(min_x='END',max_x='START',min_y='START',max_y='END'),
    vendor_diff=d,vendor_difference_partition=partition,unexpected_changed_offsets=unknown,
    patch_fields=[dict(name=n,start=p,end_exclusive=p+8,E1_hex=b[p:p+8].hex()) for n,p in fields],
    transferred_slice_bytes=128,stale_vs_E0=diff(a,c),stale_vs_E1=diff(b,c),
    opaque_and_tags=[dict(name=n,start=lo,end_exclusive=hi,E0=a[lo:hi].hex(),E1=b[lo:hi].hex(),STALE2=c[lo:hi].hex()) for n,lo,hi in known],
    property_tail=dict(start=554,end_exclusive=8192,equal=True,sha256=sha(a[554:]),semantic_extent='unresolved opaque region'),
    Version=dict(equal=True,size=32,hex=va.hex(),sha256=sha(va)),
    version_source='tests/samples/bundles/geometry/geometry_line_staleprobe2_E0/typeeditzone_version.bin',
    classifications=classes,integrity=dict(baseline_files_checked=len(baseline['files']),all_prior_files_unchanged=True),
    interpretation='Runtime not performed. This single candidate retains E0 remainder with E1 mixed-XY endpoints and bounds; acceptance is untested.')
save(R/'staleprobe2/static_verification.json',report)
save(R/'stale_opaque_probe_2d_results.json',report)
m.update(status='awaiting_explicit_stale2_load_approval_and_blank_target',candidate_constructed=True,candidate_path=report['candidate_path'],
    candidate_sha256=sha(c),version_source=report['version_source'],static_verification='research/geometry-line/staleprobe2/static_verification.json',
    static_classifications={k:classes[k] for k in ['broad2d_vendor_pair_valid','broad2d_stale_constructed','broad2d_geometry_matches_vendor_E1','broad2d_remainder_matches_E0']})
save(R/'stale_opaque_probe_2d_manifest.json',m)
print(json.dumps(dict(classifications=m['static_classifications'],candidate_sha256=sha(c),vendor_changed_bytes=len(d['exact_changed_offsets']),
    stale_vs_E0_changed_bytes=len(diff(a,c)['exact_changed_offsets']),stale_vs_E1_ranges=diff(b,c)['ranges'],baseline_files_checked=len(baseline['files'])),indent=2))
