import pytest
from prepare_patch import PRIOR,INPUT_SHA,OUTPUT_SHA,CHANGED,PRECONDITIONS,patch_g1,sha,Decoder,geometry,colors

def source():return (PRIOR/'samples/G1/typeeditzone.bin').read_bytes()

def test_exact_requested_result_and_geometry():
    original=source()
    changed=patch_g1(original)
    assert sha(original)==INPUT_SHA and sha(changed)==OUTPUT_SHA
    assert len(original)==len(changed)==8192
    assert tuple(i for i,(a,b) in enumerate(zip(original,changed)) if a!=b)==CHANGED
    assert all(changed[i:i+4]==bytes.fromhex('3060cc00') for i in (915,927))
    assert geometry(Decoder().decode_bytes(original))==geometry(Decoder().decode_bytes(changed))
    assert [v['name'] for v in colors(Decoder().decode_bytes(changed))]==['Navy Blue','Army Green']
    assert source()==original

@pytest.mark.parametrize('offset',[offset for offset,_ in PRECONDITIONS])
def test_each_required_field_is_checked_before_patch(offset):
    data=bytearray(source());data[offset]^=1
    with pytest.raises(ValueError,match='색상 사전 조건'):patch_g1(bytes(data))

@pytest.mark.parametrize('kind',['truncate','append','other_byte','G0-R','already_patched'])
def test_unsupported_or_changed_inputs_fail_closed(kind):
    data=source()
    if kind=='truncate':data=data[:-1]
    elif kind=='append':data+=b'\0'
    elif kind=='other_byte':data=bytes([data[0]^1])+data[1:]
    elif kind=='G0-R':data=(PRIOR/'samples/G0-R/typeeditzone.bin').read_bytes()
    else:data=patch_g1(data)
    with pytest.raises(ValueError):patch_g1(data)
