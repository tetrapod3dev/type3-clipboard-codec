from pathlib import Path
import json,sys,hashlib
import selection_inventory_v2 as v2
HERE=Path(__file__).resolve().parent;ROOT=v2.ROOT

def corpus():
 sys.path.insert(0,str(ROOT/'research/selection-object-inventory-001'))
 import reproduce_inventory
 items=reproduce_inventory.fixtures()
 group=ROOT/'research/group-color/type3-clipboard-member-color-003'
 for name in ['S1-confirmed','S2-confirmed','U0','G0-A','G0-B','G0-R']:
  p=group/'samples'/name/'typeeditzone.bin';items[name]=(p,p.read_bytes())
 for name in ['H0-A','H0-B']:
  p=ROOT/'research/group-color/type3-clipboard-independent-prediction-006/samples'/name/'typeeditzone.bin';items[name]=(p,p.read_bytes())
 from type3_clipboard_codec.utils.hex_text import hex_to_bytes
 for name in ['text_three_objects_grouped_order_abc','text_three_objects_not_grouped','text_three_objects_grouped_order_cba','text_two_objects_same_color_not_grouped','text_two_objects_mixed_color_not_grouped','text_three_objects_grouped_order_abc_mixed_color','text_three_objects_grouped_order_abc_font_arial_bold','text_three_objects_grouped_order_abc_content_variation','text_two_objects_not_grouped_selection_reversed']:
  p=ROOT/'tests/samples/text'/f'{name}.txt'
  if p.is_file():items[name]=(p,hex_to_bytes(p.read_text(encoding='utf-8-sig')))
 return items


def count_evidence(items):
 old={'E1','F','text_three_objects_grouped_order_abc','text_three_objects_not_grouped','text_three_objects_grouped_order_cba','text_two_objects_same_color_not_grouped','text_two_objects_mixed_color_not_grouped','text_three_objects_grouped_order_abc_mixed_color'}
 ui={'E1':3,'F':4,'S1-confirmed':1,'S2-confirmed':1,'U0':2,'G0-A':1,'G0-B':1,'G0-R':1,'G1':1,'H0-A':1,'H0-B':1,'H1':1}
 rows={}
 for name,(p,data) in items.items():
  candidate=v2.count_candidate(data)
  observed=ui.get(name)
  if name in ['E1','F']:source='automation research/feasibility/type3-mixed-clipboard-ef-001/result.md; historical UI 3/4 areas'
  elif name.startswith('H'):source='research/group-color/type3-clipboard-independent-prediction-006/result.md; grouping/handles/UI input, no independent Native count'
  else:source='research/group-color/type3-clipboard-member-color-003/result.md and capture-metadata.json; explicit single/U0/group selections'
  ambiguous=None
  intent=ROOT/'tests/samples/intents/text'/f'{name}.md'
  if observed is None and intent.is_file():
   # Retain literal metadata without interpreting constituent count as top-level count.
   text=intent.read_text(encoding='utf-8-sig')
   selected=[line for line in text.splitlines() if 'selected/copied object count:' in line]
   grouping=[line for line in text.splitlines() if 'grouped/not grouped:' in line]
   ambiguous={'source':str(intent.relative_to(ROOT)),'literal_selected_count_lines':selected,'grouping_lines':grouping,
              'validation_use':'EXCLUDED: intent/constituent or attempted setup, no independent UI top-level count established'}
  rows[name]={'source':str(p.relative_to(ROOT)),'source_sha256':v2.sha(data),'candidate':candidate,'previous_003_evaluated':name in old,
              'ui_top_level_count':observed,'ui_count_evidence':source if observed is not None else None,
              'metadata_only':ambiguous,'value_validation':'MATCH' if observed is not None and candidate['value']==observed else 'CONTRADICTED' if observed is not None else 'NOT_ESTABLISHED',
              'new_independent_validation':observed is not None and name not in old}
 qualified=[r for r in rows.values() if r['new_independent_validation']]
 contradicted=[n for n,r in rows.items() if r['value_validation']=='CONTRADICTED']
 return {'count_candidate_status':'COUNT_CANDIDATE_CONTRADICTED' if contradicted else 'COUNT_CANDIDATE_CONDITIONAL',
         'producer_contract_verified':False,'rows':rows,'contradicted_samples':contradicted,
         'new_ui_validated_captures':len(qualified),'new_ui_validated_unique_sha':len({r['source_sha256'] for r in qualified}),
         'conclusion':'Independent count evidence is concentrated in geometry n0 fixtures; text n>0 retains old E/F controls, new text intent is not independent UI truth. No broad corroboration claim.'}


def build_results():
 items=corpus();reports={}
 for name,(p,data) in items.items():
  report=v2.analyze_bytes(data)
  reports[name]={'source':str(p.relative_to(ROOT)),'source_sha256':v2.sha(data),'inventory':report}
  print(name,report['status'],report['selection_summary']['top_level_selection_count_candidate'],len(report['geometry_occurrences']),len(report['text_occurrences']),flush=True)
 sys.path.insert(0,str(ROOT/'research/selection-object-inventory-001'))
 import reproduce_inventory
 synthetic={n:{'kind':'SYNTHETIC_NOT_TYPEEDIT_CAPTURE','inventory':v2.analyze_bytes(data)} for n,data in reproduce_inventory.synthetic_inputs().items()}
 # Duplicate text at two distinct source windows; not a new real capture.
 f=bytearray(items['F'][1]);old=json.loads((ROOT/'research/selection-enumeration-ef-002/ef-parser-trace.json').read_text(encoding='utf-8'))
 start=next(r for r in old['samples']['F']['diagnostic']['slot_record_findings'] if r['decoded_run_candidate']['text']=='T2B')['source_record_windows'][0][0]
 f[start+204+4:start+204+8]=(49).to_bytes(4,'little');f[start+408+4:start+408+8]=(65).to_bytes(4,'little')
 synthetic['same_text_distinct_windows']={'kind':'SYNTHETIC_NOT_TYPEEDIT_CAPTURE','inventory':v2.analyze_bytes(bytes(f))}
 return {'classification':'SELECTION_INVENTORY_V2_VERIFIED_LIMITED','samples':reports,'synthetic':synthetic},count_evidence(items)

if __name__=='__main__':
 r,c=build_results()
 for name,obj in [('v2-sample-results.json',r),('selection-count-evidence.json',c)]:
  with (HERE/name).open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
