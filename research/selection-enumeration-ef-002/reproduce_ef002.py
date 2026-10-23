from pathlib import Path
import sys,importlib.util,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def original_inputs():
 sys.path.insert(0,str(ROOT/'research/selection-object-inventory-001'))
 import reproduce_inventory
 return reproduce_inventory.fixtures()

def build():
 d=load('ef002_diagnostic',HERE/'enumeration-diagnostic.py')
 samples={name:{'source':str(p.relative_to(ROOT)), 'source_file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'diagnostic':d.diagnose_bytes(data)} for name,(p,data) in original_inputs().items()}
 captures={}
 automation=ROOT.parent/'typeedit-automation'
 for name in ['E1','F']:
  data=original_inputs()[name][1];p=automation/'research/feasibility/type3-mixed-clipboard-ef-001'/name
  zone=(p/'typeeditzone.bin').read_bytes();version=(p/'typeeditzone_version.bin').read_bytes()
  captures[name]={'source':str(p),'original_zone_sha256':hashlib.sha256(zone).hexdigest(),'inventory_copy_sha256':hashlib.sha256(data).hexdigest(),'equal':zone==data,'zone_length':len(zone),
                  'version_length':len(version),'version_sha256':hashlib.sha256(version).hexdigest(),
                  'manifest_sha256':hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest(),
                  'registered_ids':json.loads((p/'manifest.json').read_text(encoding='utf-8'))['formats'],
                  'whole_archive_valid_length':'UNKNOWN'}
 synthetic={}
 # Reuse existing diagnostic synthetic inputs; all Decoder execution stays in owned children.
 sys.path.insert(0,str(ROOT/'research/selection-object-inventory-001'))
 import reproduce_inventory
 for name,data in reproduce_inventory.synthetic_inputs().items():
  synthetic[name]={'kind':'SYNTHETIC_MEMORY_INPUT_NOT_TYPE3_CAPTURE','diagnostic':d.diagnose_bytes(data)}
 return {'verdict':'SELECTION_EF_ENUMERATION_CAUSE_VERIFIED','cause_classification':'MULTIPLE_CAUSES',
         'exact_top_level_enumeration':False,'capture_integrity':captures,'samples':samples,'synthetic':synthetic,
         'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/type3_clipboard_codec/parsers/binary/node_scanner.py',ROOT/'src/type3_clipboard_codec/parsers/binary/node_parser.py',ROOT/'src/type3_clipboard_codec/parsers/geometry/chain_builder.py',ROOT/'src/type3_clipboard_codec/parsers/type3_chain_parser.py',ROOT/'src/type3_clipboard_codec/parsers/text/text_pipeline.py',ROOT/'src/type3_clipboard_codec/parsers/text/cparagraphe_parser.py']}}

if __name__=='__main__':
 r=build()
 with (HERE/'ef-parser-trace.json').open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
 for n,v in r['samples'].items():
  d=v['diagnostic'];print(n,d['status'],len(d.get('decoder_chains',[])),[x['text'] for x in d.get('all_extracted_text_runs',[])])
