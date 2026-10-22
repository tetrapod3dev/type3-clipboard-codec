import copy
import pytest
import field_locator as module
from field_locator import PRIOR,CODEC,learn_profile,locate
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput

@pytest.fixture
def profile():
    root=PRIOR/'samples'
    return learn_profile((root/'S1-confirmed/typeeditzone.bin').read_bytes(),
                         (root/'S2-confirmed/typeeditzone.bin').read_bytes())

def g1():return (PRIOR/'samples/G1/typeeditzone.bin').read_bytes()

def test_known_G1_reproduced_without_write_admission(profile):
    row=locate(g1(),profile)
    assert row['status']=='CANDIDATE_ONLY'
    assert row['members'][1]['color_pair_ranges_candidate']==[[1641,1645],[1653,1657]]
    assert row['members'][0]['color_name_candidate']=='Navy Blue'
    assert row['members'][1]['color_name_candidate']=='Turquoise'
    assert not row['change_allowed']
    assert row['members'][1]['tag']['class']=='UNKNOWN'

def test_synthetic_prefix_shift_is_not_product_validation(profile):
    data=g1();shifted=data[:6]+bytes(8)+data[6:]
    a,b=locate(data,profile),locate(shifted,profile)
    assert b['status']=='CANDIDATE_ONLY'
    for before,after in zip(a['members'],b['members']):
        assert after['color_pair_ranges_candidate']==[[start+8,end+8] for start,end in before['color_pair_ranges_candidate']]
    assert not b['change_allowed']

@pytest.mark.parametrize('name',['S1-confirmed','S2-confirmed','U0'])
def test_non_group_captures_rejected(profile,name):
    row=locate((PRIOR/'samples'/name/'typeeditzone.bin').read_bytes(),profile)
    assert row['status']=='REJECTED' and not row['change_allowed']

def test_style_prefix_change_rejected(profile):
    data=bytearray(g1());initial=locate(bytes(data),profile)
    data[initial['members'][0]['tag']['body_candidate']]^=1
    row=locate(bytes(data),profile)
    assert row['status']=='REJECTED' and not row['change_allowed']

def test_unequal_pair_rejected(profile):
    data=bytearray(g1());initial=locate(bytes(data),profile)
    data[initial['members'][1]['color_pair_ranges_candidate'][0][0]]^=1
    row=locate(bytes(data),profile)
    assert row['status']=='REJECTED' and not row['change_allowed']

def test_truncated_pair_rejected(profile):
    data=g1();row=locate(data,profile)
    stop=row['members'][1]['color_pair_ranges_candidate'][1][1]-1
    result=locate(data[:stop],profile)
    assert result['status']=='REJECTED' and not result['change_allowed']

def test_duplicate_geometry_anchors_rejected(profile,monkeypatch):
    original=module.Decoder().decode_bytes(g1())
    original.object_chains=[copy.deepcopy(original.object_chains[0]),copy.deepcopy(original.object_chains[0])]
    class FakeDecoder:
        def decode_bytes(self,data):return original
    monkeypatch.setattr(module,'Decoder',FakeDecoder)
    row=locate(g1(),profile)
    assert row['status']=='REJECTED' and not row['change_allowed']

@pytest.mark.parametrize('name',['two_rectangle_group_navy_blue','two_rectangle_group_army_green'])
def test_old_group_family_not_forced_into_new_profile(profile,name):
    data=ManualHexInput((CODEC/'tests/samples'/f'{name}.txt').read_text()).fetch_data()
    row=locate(data,profile)
    assert row['status']=='REJECTED' and not row['change_allowed']

def test_input_remains_immutable(profile):
    data=g1();before=bytes(data)
    locate(data,profile)
    assert data==before
