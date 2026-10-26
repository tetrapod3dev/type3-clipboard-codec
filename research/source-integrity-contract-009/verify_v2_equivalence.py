from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"));sys.path.insert(0,str(ROOT/"research/selection-inventory-v2-004"))
import reproduce_v2 as replay
old=json.loads((ROOT/"research/selection-inventory-v2-004/v2-sample-results.json").read_text(encoding="utf-8"))
rows={}
for name,(path,data) in replay.corpus().items():
 current=replay.v2.analyze_bytes(data)
 baseline=old["samples"][name]["inventory"]
 # Only child PID and measured elapsed time are nondeterministic telemetry.
 def normalize(obj):
  result=json.loads(json.dumps(obj))
  execution=result.get("execution",{})
  execution.pop("child_pid",None);execution.pop("elapsed_seconds",None)
  return result
 equal=normalize(current)==normalize(baseline)
 rows[name]={"semantic_json_equal":equal,"source_sha256":hashlib.sha256(data).hexdigest(),"timed_out":current["execution"]["timed_out"]}
 assert equal,name
 assert not current["execution"]["timed_out"],name
out=ROOT/"research/source-integrity-contract-009/v2-equivalence.json"
out.write_text(json.dumps({"comparison":"all fields except child_pid/elapsed_seconds telemetry","samples":rows},indent=2),encoding="utf-8")
print(len(rows),"preserved V2 samples")
