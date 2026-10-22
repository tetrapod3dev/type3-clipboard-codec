"""Saved fixture crosswalk extension; no resynchronization or production parser changes."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,importlib.util,dataclasses
ROOT=Path(__file__).resolve().parent
CODEC=ROOT.parents[1]
sys.path.insert(0,str(CODEC/'src'))
from type3_clipboard_codec.utils.hex_text import hex_to_bytes
from type3_clipboard_codec.codec.decoder import Decoder
spec=importlib.util.spec_from_file_location('prior_crosswalk_002',ROOT.parent/'archive-crosswalk-001/crosswalk.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
FIXTURES=['polyline_3_points','polyline_5_points','polygon_5_sides','polygon_6_sides','default_circle','text/default_text']
def nodes(tree):
    yield tree
    for child in tree.get('children',[]):yield from nodes(child)
def analyse(name):
    path=CODEC/'tests/samples'/f'{name}.txt'
    raw=path.read_bytes();data=hex_to_bytes(raw.decode('utf-8-sig'))
    r=prior.Reader(data)
    result={'fixture':name,'fixture_file_sha256':hashlib.sha256(raw).hexdigest(),'payload_sha256':hashlib.sha256(data).hexdigest(),'payload_length':len(data),'change_allowed':False}
    if data[:6]!=bytes.fromhex('000000000100'):
        return {**result,'status':'REJECTED','reason':'unreviewed prefix','cursor':0}
    try:
        tree=r.obj()
        contours=[n for n in nodes(tree) if n['class']=='CContour']
        decoded=Decoder().decode_bytes(data)
        chain_bytes=[c.raw_contour_bytes for c in decoded.object_chains]
        for n in contours:
            a,b=n['point_records']['span']
            if b-a!=n['point_records']['count']*36:raise ValueError('point extent mismatch')
            if data[a:b] not in chain_bytes:raise ValueError('existing decoder contour differs')
        return {**result,'status':'BOUNDED_CROSSWALK_MATCH','tree':tree,'contours':[n['point_records'] for n in contours],
            'properties':r.properties,'color_suffixes':r.colors,'events':r.events,'end':r.pos,'unparsed_tail_length':len(data)-r.pos,
            'tail_meaning':'UNKNOWN','archive_initial_context':'UNKNOWN; unseeded start6 remains conditional',
            'existing_decoder_contour_bytes_equal':True,'additional_list_zero_scope':'CZone/CCourbe exact native vtables only'}
    except (ValueError,UnicodeDecodeError,IndexError) as error:
        return {**result,'status':'REJECTED','cursor':r.pos,'reason':str(error),'partial_events':r.events}
def build():
    report={name:analyse(name) for name in FIXTURES}
    (ROOT/'fixture-crosswalk.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for name,r in report.items():print(name,r['status'],r.get('end',r.get('cursor')),r.get('contours',r.get('reason')))
    return report
if __name__=='__main__':build()
