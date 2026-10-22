import pytest
import crosswalk as c

def sample():return (c.GROUP/'type3-clipboard-independent-prediction-006/samples/H1/typeeditzone.bin').read_bytes()

def test_saved_G1_H_crosswalk():
    for p in [c.GROUP/'type3-clipboard-member-color-003/samples/G1/typeeditzone.bin',c.GROUP/'type3-clipboard-independent-prediction-006/samples/H0-A/typeeditzone.bin',c.GROUP/'type3-clipboard-independent-prediction-006/samples/H1/typeeditzone.bin']:
        r=c.diagnose(p.read_bytes())
        assert r['class8_conditional']=='CPropertyExtend'
        assert r['color_ranges_equal_locator'] and not r['change_allowed']
        assert [p['body'][1]-p['body'][0] for p in r['properties']]==[112,112]
        assert r['verdict']=='ARCHIVE_CROSSWALK_PARTIAL'

@pytest.mark.parametrize('stop',[5,16,795,906,1656])
def test_truncation_rejected(stop):
    with pytest.raises((ValueError,struct.error)):c.diagnose(sample()[:stop])

import struct

def test_unregistered_class_reference_rejected():
    data=bytearray(sample());data[6:8]=bytes.fromhex('0880')
    with pytest.raises(ValueError,match='unknown class reference'):c.diagnose(bytes(data))

def test_property_optional_branch_not_skipped():
    data=bytearray(sample());data[895:899]=(1).to_bytes(4,'little')
    with pytest.raises(ValueError,match='optional'):c.diagnose(bytes(data))
