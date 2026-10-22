"""Bounded current-version base walk from an explicit descriptor-end hypothesis.

Not a complete MFC stream reader, and never assigns document parent/identity.
"""
from pathlib import Path
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parent
INPUT=ROOT.parent/'type3-mixed-clipboard-ef-001'
CODEC=Path(r'C:\work\develop\type3-clipboard-codec')

class Unsupported(ValueError):pass

class Cursor:
    def __init__(self,data,pos):
        self.data,self.pos,self.fields=data,pos,[]
    def take(self,n,name,evidence):
        if n<0 or self.pos+n>len(self.data):
            raise ValueError(f'truncated {name}: cursor={self.pos} required={n}')
        start=self.pos; self.pos+=n; raw=self.data[start:self.pos]
        self.fields.append({'name':name,'span':[start,self.pos],'width':n,
                            'raw_hex':raw.hex(),'code_evidence':evidence})
        return raw
    def integer(self,n,name,evidence):
        raw=self.take(n,name,evidence); value=int.from_bytes(raw,'little')
        self.fields[-1]['value']=value
        return value

def walk(data,origin):
    c=Cursor(data,origin)
    c.take(48,'cube_two_vectors','58462 -> reused LGeom 110F0/11770, six binary64 stores')
    flags=c.integer(4,'stored_flags','58482 Write4; source this+50 OR 01001000')
    if flags & 0x01001000 != 0x01001000:raise Unsupported('stored flags outside reviewed path')
    if c.integer(4,'base_version','58498 Write4 constant8')!=8:raise Unsupported('not base version8')
    for member,rva in ((0x58,'584A5'),(0x5c,'584B2'),(0x60,'584BF'),(0x64,'584CC')):
        c.integer(4,f'member_{member:x}',rva+' Write4')
    if c.integer(4,'guid_version','584DB -> reused 5D9AA Write4')!=2:
        raise Unsupported('GUID serializer version not reviewed')
    c.take(16,'guid_raw','reused 5D9B7 Write16; not document identity')
    count=c.integer(4,'guid_property_count','reused 5D324 Write4')
    if count>100:raise Unsupported('property count exceeds diagnostic limit100')
    for index in range(count):
        for part in ('key','value'):
            size=c.integer(4,f'property_{index}_{part}_length','reused 5CDF8 Write4')
            if size>4096:raise Unsupported('string length exceeds diagnostic limit4096')
            c.take(size,f'property_{index}_{part}_bytes','reused 5CE09 Write exactly stored byte length')
    extra=c.integer(8,'extra_map_count','584E0 -> reused 5817D Write8')
    if extra:raise Unsupported('nonempty extra map requires additional entry parsing; not skipped')
    return {'origin_hypothesis':origin,'base_end':c.pos,'consumed':c.pos-origin,
            'fields':c.fields,'origin_status':'descriptor_end_hypothesis_not_global_WriteObject_proof',
            'parent_children':'Unknown'}

def diagnose(data):
    signature=b'\xff\xff\x01\x00\x05\x00CZone'
    at=data.find(signature)
    if at<0:raise Unsupported('no reviewed CZone descriptor candidate')
    origin=at+len(signature)
    result=walk(data,origin)
    c=Cursor(data,result['base_end'])
    version=c.integer(4,'ctn_version','5ACAF Write4; constant3')
    if version!=3:raise Unsupported('following container version is not3')
    count=c.integer(4,'helper_count','5AB28 Write4; CVnNContener count, ownership Unknown')
    result.update({'descriptor_candidate_span':[at,origin], 'following_fields':c.fields,
                   'following_count_raw':count,'next_object_candidate':c.pos,
                   'verdict':'BASE_SERIALIZE_FRAMING_PARTIAL'})
    return result

def main():
    rows=[]
    for name in ('E1','E2','F'):
        data=(INPUT/name/'typeeditzone.bin').read_bytes()
        rows.append({'sample':name,'sha256':hashlib.sha256(data).hexdigest(),**diagnose(data)})
    # Original geometry fixtures are file-only regression inputs, not newly captured samples.
    for name in ('default_rectangle','two_rectangle','two_rectangle_group'):
        raw=(CODEC/'tests/samples'/f'{name}.txt').read_text(encoding='utf-8-sig')
        import sys
        sys.dont_write_bytecode=True
        sys.path.insert(0,str(CODEC/'src'))
        from type3_clipboard_codec.utils.hex_text import hex_to_bytes
        data=hex_to_bytes(raw)
        rows.append({'sample':name,'sha256':hashlib.sha256(data).hexdigest(),**diagnose(data)})
    print(json.dumps({'samples':rows,'scope':'saved_files_only',
                      'unconditional_origin_verified':False},indent=2))

if __name__=='__main__':main()
