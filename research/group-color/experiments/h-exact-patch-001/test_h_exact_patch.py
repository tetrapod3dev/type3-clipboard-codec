import pytest
import h_exact_patch as h

def source():return h.check.bundle('H1')

def test_exact_output_and_source_immutable():
    a,v=source();original=bytes(a);out,info=h.patch_h1(a,v)
    assert a==original and len(out)==8192
    assert info['changed_offsets']==[915,916,917,927,928,929]
    assert info['computed_R2_ranges']==[[915,919],[927,931]]
    assert info['R1_color_unchanged'] and info['geometry_bbox_contours_unchanged']
    assert not info['locator_change_allowed']
    assert h.sha(out)=='f699289a52535d3d9dc3cf8098ae03d6fb8b2a7017109109f66c5f3833105885'

@pytest.mark.parametrize('kind',['truncate','append','other_byte','other_color','H0','G1','already_patched','bad_version'])
def test_invalid_input_rejected(kind):
    a,v=source()
    if kind=='truncate':a=a[:-1]
    elif kind=='append':a+=b'\0'
    elif kind=='other_byte':a=bytes([a[0]^1])+a[1:]
    elif kind=='other_color':
        m=h.plan(a,v)[0];b=bytearray(a)
        for start,end in m['R2']['color_pair_ranges_candidate']:b[start:end]=h.ARMY
        a=bytes(b)
    elif kind=='H0':a=h.check.bundle('H0-A')[0]
    elif kind=='G1':a=(h.GROUP/'type3-clipboard-member-color-003/samples/G1/typeeditzone.bin').read_bytes()
    elif kind=='already_patched':a=h.patch_h1(a,v)[0]
    elif kind=='bad_version':v=v[:-1]
    with pytest.raises(ValueError):h.patch_h1(a,v)

def test_G1_exact_patch_and_H_predictions_reproduced():
    g=(h.GROUP/'type3-clipboard-member-color-003/samples/G1/typeeditzone.bin').read_bytes()
    out=h.patch.patch_g1(g)
    assert out==(h.G1/'candidate/typeeditzone.bin').read_bytes()==(h.G1/'runtime-001/recopy/typeeditzone.bin').read_bytes()
    assert h.check.predict_bytes(g)['locator_result']['members'][1]['color_pair_ranges_candidate']==[[1641,1645],[1653,1657]]
    assert h.validate_evidence()['verdict']=='INDEPENDENT_FIELD_PREDICTION_VERIFIED'
