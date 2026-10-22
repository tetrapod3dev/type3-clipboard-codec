import pytest
import analyse_fixtures as a

@pytest.mark.parametrize('name,count',[('polyline_3_points',3),('polyline_5_points',5),('polygon_5_sides',5),('polygon_6_sides',6)])
def test_variable_records_reproduce_native_width_and_decoder(name,count):
    r=a.analyse(name)
    assert r['status']=='BOUNDED_CROSSWALK_MATCH'
    assert r['contours'][0]['count']==count
    assert r['contours'][0]['span'][1]-r['contours'][0]['span'][0]==count*36
    assert r['existing_decoder_contour_bytes_equal']
    assert r['color_suffixes'][0]['suffix_span'][1]-r['color_suffixes'][0]['suffix_span'][0]==24
    assert not r['change_allowed']

def test_circle_is_reviewed_not_assumed_equivalent_geometry():
    r=a.analyse('default_circle')
    assert r['status']=='BOUNDED_CROSSWALK_MATCH'
    assert r['existing_decoder_contour_bytes_equal']
    assert not r['change_allowed']

def test_other_native_family_is_rejected():
    r=a.analyse('text/default_text')
    assert r['status']=='REJECTED' and r['reason']=='unreviewed prefix' and r['cursor']==0
    assert not r['change_allowed']

def test_G1_H_previous_results_unchanged():
    old=a.prior.check.read_json(a.ROOT.parent/'archive-crosswalk-001/crosswalk.json')
    paths={'G1':a.prior.GROUP/'type3-clipboard-member-color-003/samples/G1/typeeditzone.bin',**{n:a.prior.GROUP/'type3-clipboard-independent-prediction-006/samples'/n/'typeeditzone.bin' for n in ['H0-A','H1']}}
    for name,path in paths.items():
        actual=a.prior.diagnose(path.read_bytes())
        # JSON object keys normalize conditional class IDs to strings.
        import json
        assert json.loads(json.dumps(actual))==old[name]
