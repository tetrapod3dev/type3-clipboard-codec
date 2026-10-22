import json
from pathlib import Path
import pytest
import prediction_check as check

PRIOR=check.ROOT.parent/'type3-clipboard-member-color-003'
def old_sample(name):return (PRIOR/'samples'/name/'typeeditzone.bin').read_bytes()

def test_frozen_profile_hash_is_recorded():
    profile,lock=check.checked_profile()
    assert lock['profile_sha256']=='d0f179eaee2c9e625a936f7ce7ad7c3db0d78928df5a782bfd4a18d8130d3197'
    assert profile['relative_color_slots']==[120,132]

def test_old_input_rehearsal_never_retrains_or_grants_write(monkeypatch):
    locator=check.load_locator()
    def forbidden(*args,**kwargs):raise AssertionError('training forbidden')
    monkeypatch.setattr(locator,'learn_profile',forbidden)
    monkeypatch.setattr(check,'load_locator',lambda:locator)
    report=check.predict_bytes(old_sample('G1'))
    assert report['locator_result']['status']=='CANDIDATE_ONLY'
    assert not report['write_permission']
    assert report['locator_result']['members'][1]['color_pair_ranges_candidate']==[[1641,1645],[1653,1657]]

def test_profile_change_is_rejected(tmp_path,monkeypatch):
    original=check.ROOT
    (tmp_path/'execution-lock.json').write_bytes((original/'execution-lock.json').read_bytes())
    data=json.loads((original/'frozen-profile.json').read_text())
    data['relative_color_slots']=[121,133]
    (tmp_path/'frozen-profile.json').write_text(json.dumps(data))
    monkeypatch.setattr(check,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='SHA mismatch'):check.checked_profile()

def test_H0_prediction_cannot_be_created_after_H1_capture(tmp_path,monkeypatch):
    folder=tmp_path/'samples/H1';folder.mkdir(parents=True)
    (folder/'typeeditzone.bin').write_bytes(b'unit-test sentinel, not a Type3 sample')
    monkeypatch.setattr(check,'ROOT',tmp_path)
    monkeypatch.setattr(check,'bundle',lambda name:(b'unit-test-only',b''))
    with pytest.raises(ValueError,match='before H1'):check.predict_capture('H0-A')
    assert not (tmp_path/'predictions/H0-A.json').exists()

def test_H1_prediction_requires_earlier_H0_prediction(tmp_path,monkeypatch):
    monkeypatch.setattr(check,'ROOT',tmp_path)
    monkeypatch.setattr(check,'bundle',lambda name:(b'unit-test-only',b''))
    with pytest.raises(FileNotFoundError):check.predict_capture('H1')

def test_existing_GUID_comparison_is_only_a_rehearsal():
    before=old_sample('G0-R');after=old_sample('G1')
    members=check.predict_bytes(before)['locator_result']['members']
    spans=check.guid_candidate_spans(before,members)
    assert len(spans)==7
    diffs=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
    outside=[i for i in diffs if not any(start<=i<end for start,end in spans)]
    assert outside==[1641,1642,1643,1653,1654,1655]
