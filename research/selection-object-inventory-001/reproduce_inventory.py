"""Preserved inputs and new artifacts only. Does not run the Type3 application."""
from pathlib import Path
import importlib.util
import json
import sys
import hashlib
import selection_inventory as inv
HERE = Path(__file__).resolve().parent
ROOT = inv.ROOT


def fixtures():
    sys.path.insert(0, str(ROOT/'src'))
    from type3_clipboard_codec.utils.hex_text import hex_to_bytes
    names = ['default_rectangle','polyline_3_points','polyline_5_points','polygon_5_sides','polygon_6_sides','default_circle','text/default_text']
    items={n:(ROOT/'tests/samples'/f'{n}.txt', None) for n in names}
    items['G1']=(ROOT/'research/group-color/type3-clipboard-member-color-003/samples/G1/typeeditzone.bin',None)
    items['H1']=(ROOT/'research/group-color/type3-clipboard-independent-prediction-006/samples/H1/typeeditzone.bin',None)
    items['E1']=(HERE/'samples/E1.bin',None)
    items['F']=(HERE/'samples/F.bin',None)
    return {n:(p, hex_to_bytes(p.read_text(encoding='utf-8-sig')) if p.suffix=='.txt' else p.read_bytes()) for n,(p,_) in items.items()}


def synthetic_inputs():
    path=ROOT/'research/archive-boundary-diagnostic-007/reproduce.py'
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location('inventory_saved007_reproduce',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return {**mod.synthetic_inputs(), 'unknown_bytes': b'unrecognized saved synthetic input', 'empty': b''}


def build_results():
    reports={}
    for name,(path,data) in fixtures().items():
        r=inv.analyze_bytes(data)
        reports[name]={'source_file':str(path.relative_to(ROOT)), 'source_file_sha256':inv.sha(path.read_bytes()),
                       'source_kind':'PRESERVED_TYPE3_CAPTURE', 'inventory':r}
    synth={name:{'source_kind':'SYNTHETIC_MEMORY_INPUT_NOT_TYPE3_CAPTURE','inventory':inv.analyze_bytes(data)} for name,data in synthetic_inputs().items()}
    # These are external observations. They are never injected into the analyzer's count.
    observations={
       'G1':{'top_level_ui_observation':1,'component_count_observation':2,'basis':'group-color/type3-clipboard-member-color-003/result.md; U0 2 -> Group 1; G1 colors/screens','geometry':'R1 80.024x60.053mm center(200.678,371.058), Navy Blue; R2 176.052x104.092mm center(488.764,349.039), Turquoise','level':'historical UI display and capture comparison'},
       'H1':{'top_level_ui_observation':1,'component_count_observation':2,'basis':'group-color/type3-clipboard-independent-prediction-006/result.md; group handles plus parameter screenshots, not independent Native count','geometry':'R2 55x35mm min(600,200), Turquoise; R1 30x20mm min(450,200), Navy Blue','level':'historical UI grouping operation/handles, not Native count'},
       'E1':{'top_level_ui_observation':3,'component_count_observation':4,'basis':'typeedit-automation research/feasibility/type3-mixed-clipboard-ef-001/result.md; screenshots and UI 3 regions','relation':'Group(R,T1A), standalone L, standalone T2B'},
       'F':{'top_level_ui_observation':4,'component_count_observation':4,'basis':'same E/F report, Ungroup and UI 4 regions','relation':'R,T1A,L,T2B independent'},
       'text/default_text':{'top_level_ui_observation':None,'fixture_intent_text':'abcdefg','fixture_intent_font':'Arial','basis':'tests/samples/README.md text table combines fixture intent and detected fields; not new independent UI count proof'},
    }
    for name in ['polyline_3_points','polyline_5_points','polygon_5_sides','polygon_6_sides']:
        observations[name]={'top_level_ui_observation':None,'fixture_intent_selected_count':1,'basis':'tests/samples/README.md geometry ground truth intent; status-bar curve-object observations; stored order unresolved','trust_note':'intent is not independent current UI count'}
    for name in ['default_rectangle','default_circle']:
        observations[name]={'top_level_ui_observation':None,'basis':'tests/samples/README.md fixture description only; no independently rechecked UI count'}
    for name,record in reports.items():
        record['external_validation_only']=observations[name]
        r=record['inventory']
        record['count_comparison']={'ui_count':observations[name].get('top_level_ui_observation'),
             'decoder_chains':r.get('decoder_chain_count'), 'inventory_candidates':r['candidate_count'],
             'inventory_exact_top_level_count':r['top_level_selection_count']['value'],
             'complete_object_list_verified':False}
    return {'verdict':'SELECTION_INVENTORY_PARTIAL','samples':reports,'synthetic':synth}


if __name__=='__main__':
    report=build_results()
    for name,r in report['samples'].items():
        i=r['inventory'];print(name,i['status'],i.get('decoder_chain_count'),i.get('payload_text',{}).get('value',{}).get('text_content'))
    for name,r in report['synthetic'].items():print(name,r['inventory']['status'],r['inventory']['execution']['timed_out'])
    with (HERE/'inventory-results.json').open('x',encoding='utf-8') as out:json.dump(report,out,ensure_ascii=False,indent=2,allow_nan=False)
