"""Read-only structure-anchored hypotheses, never a write admission API.

Learn a style-prefix profile from two controlled standalone rectangles. Locate
it immediately after validated contour records and an observed archive tag.
Class-reference resolution and full member ownership remain unverified.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import dataclasses
import hashlib
import json
import math
import struct

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'type3-clipboard-member-color-003'
CODEC=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(CODEC/'src'))
from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser
from type3_clipboard_codec.models.colors import TYPE3_COLORS_BY_RGB0_RAW

class Rejected(ValueError):pass
def sha(data):return hashlib.sha256(data).hexdigest()

def property_tag(data,start):
    if start<0 or start+2>len(data):raise Rejected('truncated property tag')
    tag=struct.unpack_from('<H',data,start)[0]
    if tag==0xffff:
        if start+6>len(data):raise Rejected('truncated class header')
        schema,size=struct.unpack_from('<HH',data,start+2)
        end=start+6+size
        if size>63 or end>len(data):raise Rejected('unsupported class name extent')
        if data[start+6:end]!=b'CPropertyExtend':raise Rejected('next new class is not CPropertyExtend')
        if schema!=5:raise Rejected('unreviewed CPropertyExtend schema')
        return {'kind':'observed_new_class','class':'CPropertyExtend','schema':schema,
                'span':[start,end],'body_candidate':end,'archive_context':'UNKNOWN'}
    if tag&0x8000 and tag!=0xfffe:
        return {'kind':'unresolved_small_class_reference','class':'UNKNOWN',
                'reference_index':tag&0x7fff,'span':[start,start+2],
                'body_candidate':start+2,'archive_context':'UNKNOWN'}
    raise Rejected('unsupported/null/object/extended reference at contour end')

def contour_anchor(data,obj,chain):
    _,_,prefix=Type3ChainParser()._read_top_level_header(data)
    if prefix!=6:raise Rejected('unsupported top-level prefix')
    if chain.shape_type!='rectangle' or len(chain.contour_records)!=4:
        raise Rejected('not a four-record rectangle candidate')
    if chain.source_stream_offset is None:raise Rejected('missing contour origin')
    start=prefix+chain.source_stream_offset
    raw=chain.raw_contour_bytes
    if len(raw)!=4*36 or start<8 or start+len(raw)>len(data):raise Rejected('invalid contour extent')
    if data[start:start+len(raw)]!=raw:raise Rejected('raw contour does not match source range')
    kind,count=struct.unpack_from('<II',data,start-8)
    if kind not in (1,2) or count!=4:raise Rejected('unsupported contour header')
    if chain.bbox is None:raise Rejected('missing bbox')
    box=dataclasses.asdict(chain.bbox)
    if not all(math.isfinite(v) for v in box.values()):raise Rejected('nonfinite bbox')
    if box['xmax_m']<=box['xmin_m'] or box['ymax_m']<=box['ymin_m']:raise Rejected('degenerate rectangle')
    return {'contour_range':[start,start+len(raw)],'header_kind_candidate':kind,
            'bbox':box,'width_mm':chain.bbox.width_mm,'height_mm':chain.bbox.height_mm,
            'tag':property_tag(data,start+len(raw))}

def common_prefix(a,b):
    return next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))

def learn_profile(first,second):
    bodies=[]
    anchors=[]
    expected=[]
    for data in (first,second):
        obj=Decoder().decode_bytes(data)
        if obj.is_grouped or obj.declared_object_count!=1 or len(obj.object_chains)!=1:
            raise Rejected('training requires controlled standalone rectangles')
        chain=obj.object_chains[0]
        anchor=contour_anchor(data,obj,chain)
        if anchor['tag']['kind']!='observed_new_class':raise Rejected('training needs named property class')
        name=chain.style.line_color_name
        matches=[raw for raw,color in TYPE3_COLORS_BY_RGB0_RAW.items() if color.name==name]
        if len(matches)!=1:raise Rejected('ambiguous training palette encoding')
        expected.append(matches[0].to_bytes(4,'little'))
        bodies.append(data[anchor['tag']['body_candidate']:])
        anchors.append(anchor)
    if expected[0]==expected[1]:raise Rejected('training colors must differ')
    primary=common_prefix(*bodies)
    if primary<4 or primary>4096:raise Rejected('unbounded or missing style prefix')
    if not all(body[primary:primary+4]==color for body,color in zip(bodies,expected)):
        raise Rejected('first structural divergence is not the controlled four-byte color')
    gap=common_prefix(bodies[0][primary+4:],bodies[1][primary+4:])
    secondary=primary+4+gap
    if gap>256 or not all(body[secondary:secondary+4]==color for body,color in zip(bodies,expected)):
        raise Rejected('second controlled color pair not reproducible')
    return {'training_sha256':[sha(first),sha(second)],'schema_candidate':5,
        'prefix_hex':bodies[0][:primary].hex(),'between_fields_hex':bodies[0][primary+4:secondary].hex(),
        'relative_color_slots':[primary,secondary],
        'evidence':'Empirical profile from standalone property bodies; not verified general Serializer layout.',
        'profile_semantics':'UNKNOWN_OUTSIDE_CONTROLLED_FAMILY'}

def locate(data,profile):
    report={'input_sha256':sha(data),'length':len(data),'members':[],
            'change_allowed':False,'ownership':'UNKNOWN','status':'REJECTED','reasons':[]}
    try:
        obj=Decoder().decode_bytes(data)
        if not obj.is_grouped or obj.declared_object_count!=1 or len(obj.object_chains)!=2:
            raise Rejected('requires one group candidate with exactly two chain candidates')
        prefix=bytes.fromhex(profile['prefix_hex'])
        gap=bytes.fromhex(profile['between_fields_hex'])
        primary,secondary=profile['relative_color_slots']
        if len(prefix)!=primary or secondary!=primary+4+len(gap):raise Rejected('invalid profile')
        ranges=[]
        boxes=[]
        for index,chain in enumerate(obj.object_chains):
            anchor=contour_anchor(data,obj,chain)
            origin=anchor['tag']['body_candidate']
            if data[origin:origin+primary]!=prefix:raise Rejected('style prefix does not match controlled profile')
            if data[origin+primary+4:origin+secondary]!=gap:raise Rejected('inter-field structure mismatch')
            if origin+secondary+4>len(data):raise Rejected('truncated color pair')
            first=data[origin+primary:origin+primary+4]
            second=data[origin+secondary:origin+secondary+4]
            if first!=second:raise Rejected('unequal color pair: unsupported profile')
            raw=int.from_bytes(first,'little')
            if raw not in TYPE3_COLORS_BY_RGB0_RAW:raise Rejected('unrecognized RGB0 palette value')
            slots=[[origin+p,origin+p+4] for p in (primary,secondary)]
            if any(a<d and c<b for a,b in slots for c,d in ranges):raise Rejected('member color ranges overlap')
            ranges.extend(slots)
            if anchor['bbox'] in boxes:raise Rejected('indistinguishable member bbox candidates')
            boxes.append(anchor['bbox'])
            report['members'].append({'ordinal_in_this_decode':index,**anchor,
                'color_name_candidate':TYPE3_COLORS_BY_RGB0_RAW[raw].name,
                'raw_rgb0_hex':first.hex(),'color_pair_ranges_candidate':slots,
                'source':'contour end + archive-tag hypothesis + controlled style prefix; no color search or nearest-offset choice',
                'member_serialize_end':'UNKNOWN'})
        report['status']='CANDIDATE_ONLY'
        report['reasons']=['Archive class/reference ledger not resolved',
            'Complete member Serialize/property ownership boundary not verified',
            'Profile is empirical and has no independent group-family validation']
    except (ValueError,IndexError,AttributeError,TypeError,KeyError,OverflowError) as error:
        report['reasons']=[type(error).__name__+': '+str(error)]
    return report

def build():
    sample_root=PRIOR/'samples'
    first=(sample_root/'S1-confirmed/typeeditzone.bin').read_bytes()
    second=(sample_root/'S2-confirmed/typeeditzone.bin').read_bytes()
    profile=learn_profile(first,second)
    rows={name:locate((sample_root/folder/'typeeditzone.bin').read_bytes(),profile)
          for name,folder in [('S1','S1-confirmed'),('S2','S2-confirmed'),('U0','U0'),
          ('G0-A','G0-A'),('G0-B','G0-B'),('G0-R','G0-R'),('G1','G1')]}
    prior_patch=HERE.parent/'type3-clipboard-group-patch-runtime-004'
    for name,path in [('patched_G1',prior_patch/'candidate/typeeditzone.bin'),
                      ('runtime_recopy',prior_patch/'runtime-001/recopy/typeeditzone.bin')]:
        rows[name]=locate(path.read_bytes(),profile)
    out={'verdict':'FIELD_LOCATOR_PARTIAL','operation':'SAVED_FILES_READ_ONLY',
        'profile':profile,'samples':rows,'stage_B':'NOT_PLANNED_BECAUSE_OWNERSHIP_ADMISSION_IS_AMBIGUOUS',
        'patch_outputs_created':False,'decoder_modified':False}
    (HERE/'recomputed-locator-result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out['verdict'])
    print('Learned relative slots:',profile['relative_color_slots'])
    for name,row in rows.items():
        print(name,row['status'],[m['color_pair_ranges_candidate'] for m in row['members']], 'write=',row['change_allowed'])
    return out

if __name__=='__main__':build()
