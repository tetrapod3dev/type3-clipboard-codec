from pathlib import Path
import sys,subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"src"))
from tests.text_slot_v1_replay import historical_root
from tests.source_integrity import source_integrity
root=historical_root()
proc=subprocess.run([sys.executable,"-B",str(root/"tools/analyze_text_slot_family_shadow.py"),"--json"],cwd=root,capture_output=True,timeout=60)
assert proc.returncode==0,proc.stderr
assert len(proc.stdout)<100000
result={"historical_cli_json_bytes":len(proc.stdout),"unchanged_cap":100000,"cli_returncode":proc.returncode,"historical_contract":source_integrity(root,"family"),"current_contract":source_integrity(ROOT,"current_production"),"historical_contract_against_current_checkout":source_integrity(ROOT,"family")}
assert result["historical_contract"]["canonical_source_equal"]
assert result["current_contract"]["canonical_source_equal"]
assert not result["historical_contract_against_current_checkout"]["canonical_source_equal"]
(ROOT/"research/source-integrity-contract-009/contract-observations.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(len(proc.stdout))
