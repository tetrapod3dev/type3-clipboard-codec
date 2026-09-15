"""File-only audit of the exact eight captured line bundles; emits no payload."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from analyze_typeeditzone_mfc_archive import analyze_bytes

IDS = ["L00", "L00_R", "L00_N", "L01", "L02", "L04", "LY0", "LZ"]
VARIANTS = ["L01", "L02", "L04", "LY0", "LZ"]
EXPECTED = [("CZone", 1), ("CCourbe", 1), ("CContour", 2), ("CPropertyExtend", 5)]
sha = lambda b: hashlib.sha256(b).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def changed_runs(a, b):
    require(len(a) == len(b), "length mismatch: no best-effort alignment")
    runs, start = [], None
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y and start is None:
            start = i
        if x == y and start is not None:
            runs.append((start, i)); start = None
    if start is not None:
        runs.append((start, len(a)))
    return runs

def main():
    manifest = json.loads((ROOT / "research/geometry-line/actual_capture_manifest.json").read_text(encoding="utf-8-sig"))
    supplied = {s["sample_id"]: s for s in manifest["samples"]}
    require(list(supplied) == IDS, "unexpected sample list/order")
    blobs, versions, rows, field_maps = {}, {}, {}, {}
    for sid in IDS:
        meta = supplied[sid]
        folder = ROOT / "tests/samples/bundles/geometry" / ("geometry_line_" + sid)
        b = (folder / "typeeditzone.bin").read_bytes()
        v = (folder / "typeeditzone_version.bin").read_bytes()
        require(meta["capture"]["bundle_verify"]["result"] == "passed", sid + " capture verify missing")
        for f in meta["capture"]["formats"]:
            payload = (ROOT / f["file"]).read_bytes()
            require(sha(payload) == f["sha256"] and len(payload) == f["byte_length"], sid + " raw hash mismatch")
        fixture = ROOT / "tests/samples" / ("geometry_line_" + sid + ".txt")
        require(hex_text_to_bytes(fixture.read_text(encoding="utf-8-sig")) == b, sid + " hex mismatch")
        require(len(b) <= 1024 * 1024, "input too large")
        audit = analyze_bytes(b, fixture=sid, category="geometry", context_bytes=0)
        desc = [h for h in audit["class_hits"] if h["descriptor_pattern_match"]]
        require([(h["class_name"], h["candidate_schema_word"]) for h in desc] == EXPECTED, sid + " unexpected descriptors")
        obj, parser = parse_type3_clipboard_bytes_with_parser(b)
        require(len(obj.object_chains) == 1 and obj.declared_object_count == 1, sid + " object count")
        chain = obj.object_chains[0]
        require(len(chain.contour_records) == 2, sid + " record count")
        origin = desc[0]["descriptor_start"]
        H = desc[2]["descriptor_start"]
        R = origin + chain.source_stream_offset
        require(R == H + 160, sid + " record-relative layout changed")
        require(struct.unpack_from("<II", b, R - 8) == (0, 2), sid + " kind/count")
        require(R + 72 == desc[3]["descriptor_start"], sid + " record-region extent")
        positions = [meta["human_confirmation"]["actual_p0"], meta["human_confirmation"]["actual_p1"]]
        scalar_fields = {}
        records = []
        for i in range(2):
            raw = b[R + i*36:R + (i+1)*36]
            values = struct.unpack("<4dI", raw)
            require(all(math.isfinite(x) for x in values[:4]), sid + " nonfinite record")
            records.append({"index":i,"offset_from_R":i*36,"xyzw_f64":list(values[:4]),"tag_u32_hex":hex(values[4]),"raw_hex":raw.hex()})
            for axis, label in enumerate("xyz"):
                name = f"record[{i}].{label}"
                offset = R + i*36 + axis*8
                observed = struct.unpack_from("<d", b, offset)[0]
                expected = float(positions[i][axis]) / 1000.0
                scalar_fields[name] = {"offset_diagnostic":offset,"origin":"R","offset_from_origin":i*36+axis*8,"role":"geometry-variable","value":observed,"expected_mm_div_1000":expected,"raw_hex":b[offset:offset+8].hex(),"expected_raw_hex":struct.pack("<d",expected).hex(),"bit_exact_to_binary64_mm_div_1000":b[offset:offset+8] == struct.pack("<d",expected),"abs_error":abs(observed-expected)}
        bounding = {}
        expected_box = [min(positions[0][a], positions[1][a])/1000.0 for a in range(3)] + [max(positions[0][a], positions[1][a])/1000.0 for a in range(3)]
        for h in desc[:3]:
            name, D = h["class_name"], h["descriptor_start"]
            base = D + 6 + h["class_name_length"]
            raw = b[base:base+48]
            bounding[name] = {"offset_from_descriptor":base-D,"values":list(struct.unpack("<6d",raw)),"raw_hex":raw.hex(),"bit_exact_expected":raw == struct.pack("<6d",*expected_box)}
            for i, label in enumerate(["min_x","min_y","min_z","max_x","max_y","max_z"]):
                offset = base + i*8
                scalar_fields[name+"."+label] = {"offset_diagnostic":offset,"origin":name+"_descriptor","offset_from_origin":offset-D,"role":"derived-geometry-variable","value":struct.unpack_from("<d",b,offset)[0],"raw_hex":b[offset:offset+8].hex()}
        raw_fields = {}
        for i in range(2):
            for offset, width, label in [(24,8,"w"),(32,4,"tag")]:
                raw_fields[f"record[{i}].{label}"] = {"offset_diagnostic":R+i*36+offset,"origin":"R","offset_from_origin":i*36+offset,"width":width,"role":"unknown","raw_hex":b[R+i*36+offset:R+i*36+offset+width].hex()}
        opaque_windows = {}
        for h in desc[:3]:
            D = h["descriptor_start"]
            # Observational windows found by completed-corpus differences, not GUID fields.
            U = D + 6 + h["class_name_length"] + 48 + 28
            name = h["class_name"] + ".opaque_metadata_window"
            raw_fields[name] = {"offset_diagnostic":U,"origin":h["class_name"]+"_descriptor","offset_from_origin":U-D,"width":16,"role":"unknown","raw_hex":b[U:U+16].hex()}
            opaque_windows[name] = raw_fields[name]
        fields = scalar_fields | raw_fields
        blobs[sid], versions[sid], field_maps[sid] = b, v, fields
        prop_start = desc[3]["descriptor_start"]
        prop_payload = prop_start + 6 + desc[3]["class_name_length"]
        rows[sid] = {"raw_size":len(b),"sha256":sha(b),"version_size":len(v),"version_sha256":sha(v),"human_ground_truth":positions,"parser":parser,"parser_confidence":chain.shape_classification_confidence,"prefix_hex":b[:origin].hex(),"descriptors":[{"class":h["class_name"],"schema":h["candidate_schema_word"],"offset_diagnostic":h["descriptor_start"],"offset_from_root_descriptor":h["descriptor_start"]-origin} for h in desc],"H_diagnostic":H,"R_diagnostic":R,"R_from_H":R-H,"kind_candidate":0,"point_count_candidate":2,"extracted_contour_regions":1,"contour_count_field":"unresolved","records":records,"bounds":bounding,"fields":fields,"opaque_metadata_windows":opaque_windows,"opaque_property_and_tail":{"origin":"CPropertyExtend_descriptor","payload_offset_from_descriptor":prop_payload-prop_start,"bytes_to_buffer_end":len(b)-prop_payload,"sha256":sha(b[prop_payload:]),"nonzero_byte_count":sum(x!=0 for x in b[prop_payload:]),"semantic_extent":"unresolved"},"strict_controlled_eligibility":False,"comparison_scope":"descriptive file observations only; protocol deviations are not cleared"}
    pairs = []
    for base, sid, purpose in [("L00",s,"requested") for s in IDS[1:]] + [("L00_N",s,"supplemental_B_baseline_not_original_A") for s in VARIANTS]:
        a,b = blobs[base],blobs[sid]
        require(rows[base]["descriptors"] == rows[sid]["descriptors"], "layout alignment failed")
        fields = field_maps[base]
        owner = {}
        for name,f in fields.items():
            for p in range(f["offset_diagnostic"],f["offset_diagnostic"]+f.get("width",8)):
                owner[p] = name
        segments=[]
        for lo,hi in changed_runs(a,b):
            cursor=lo
            while cursor<hi:
                name=owner.get(cursor)
                end=cursor+1
                while end<hi and owner.get(end)==name: end+=1
                f=fields.get(name,{})
                origin_offset = cursor-f["offset_diagnostic"]+f["offset_from_origin"] if name else cursor-rows[base]["H_diagnostic"]
                segments.append({"absolute_start_diagnostic":cursor,"length":end-cursor,"field":name,"origin":f.get("origin","CContour_descriptor_for_diagnostic_only"),"relative_offset":origin_offset,"classification":f.get("role","unknown"),"before_hex":a[cursor:end].hex(),"after_hex":b[cursor:end].hex()})
                cursor=end
        pairs.append({"base":base,"sample":sid,"purpose":purpose,"strict_controlled_pair":False,"identity_inference":"abstain","raw_equal":a==b,"changed_byte_count":sum(x!=y for x,y in zip(a,b)),"changed_fields":[name for name,f in fields.items() if f["raw_hex"] != field_maps[sid][name]["raw_hex"]],"unknown_changed_byte_count":sum(s["length"] for s in segments if s["classification"]=="unknown"),"changed_ranges":segments})
    checks = {}
    for i in range(2):
        for axis,label in enumerate("xyz"):
            name=f"record[{i}].{label}"
            expected_changes, actual_changes = [], []
            for sid in IDS[1:]:
                if rows[sid]["human_ground_truth"][i][axis] != rows["L00"]["human_ground_truth"][i][axis]: expected_changes.append(sid)
                if rows[sid]["fields"][name]["raw_hex"] != rows["L00"]["fields"][name]["raw_hex"]: actual_changes.append(sid)
            profile=[rows[s]["fields"][name]["raw_hex"] for s in IDS]
            equivalents=[other for other in field_maps["L00"] if other!=name and all(field_maps[s][other]["raw_hex"]==v for s,v in zip(IDS,profile))]
            checks[name]={"expected_changed_samples":expected_changes,"actual_changed_samples":actual_changes,"changed_and_invariant_requirements_match":expected_changes==actual_changes,"all_binary64_conversion_matches":all(rows[s]["fields"][name]["bit_exact_to_binary64_mm_div_1000"] for s in IDS),"identical_scalar_profiles":equivalents,"promotion":"candidate_only; strict provenance and no-competing-hypothesis criteria not satisfied"}
    encodings={}
    for fmt in ["<d","<f","<i","<q"]:
        values=[]
        for sid in IDS:
            for i in range(2):
                for axis in range(3):
                    offset=rows[sid]["R_diagnostic"]+36*i+8*axis
                    values.append((struct.unpack_from(fmt,blobs[sid],offset)[0],float(rows[sid]["human_ground_truth"][i][axis])))
        anchor=next(((raw,mm) for raw,mm in values if raw!=0 and mm!=0 and math.isfinite(raw)),None)
        scale=anchor[1]/anchor[0] if anchor else None
        mismatches=[{"raw":raw,"expected_mm":mm} for raw,mm in values if scale is None or not math.isfinite(raw) or not math.isclose(raw*scale,mm,rel_tol=1e-12,abs_tol=1e-12)]
        encodings[fmt]={"positions":"xyz slots at record +0/+8/+16 only","fitted_common_multiplier_to_mm":scale,"mismatches":len(mismatches),"first_mismatches":mismatches[:5],"limit":"Does not exclude arbitrary encodings at unmodeled positions or other scales per field"}
    before={s:sha(blobs[s]) for s in IDS}
    for sid in IDS:
        folder=ROOT/"tests/samples/bundles/geometry"/("geometry_line_"+sid)
        require(sha((folder/"typeeditzone.bin").read_bytes())==before[sid],"raw changed during analysis")
        require((folder/"typeeditzone_version.bin").read_bytes()==versions[sid],"version changed during analysis")
    result={"schema_version":1,"analysis_mode":"file_only_no_payload_generation","samples":rows,"pairs":pairs,"endpoint_checks":checks,"encoding_comparison":encodings,"version_all_byte_identical":len(set(versions.values()))==1,"property_tail_all_byte_identical":len({rows[s]["opaque_property_and_tail"]["sha256"] for s in IDS})==1,"version_bytes_hex":versions["L00"].hex(),"descriptor_layout_stable":all(rows[s]["descriptors"]==rows["L00"]["descriptors"] for s in IDS),"all_record_conversion_bit_exact":all(c["all_binary64_conversion_matches"] for c in checks.values()),"all_bounds_bit_exact":all(v["bit_exact_expected"] for r in rows.values() for v in r["bounds"].values()),"direction_hypotheses":{"record0_matches_human_P0":all(rows[s]["fields"][f"record[0].{a}"]["bit_exact_to_binary64_mm_div_1000"] for s in IDS for a in "xyz"),"record1_matches_human_P1":all(rows[s]["fields"][f"record[1].{a}"]["bit_exact_to_binary64_mm_div_1000"] for s in IDS for a in "xyz"),"record0_also_componentwise_min":all(all(p0[a]<=p1[a] for a in range(3)) for p0,p1 in [rows[s]["human_ground_truth"] for s in IDS]),"creation_direction_vs_minmax_order":"not_distinguishable_in_this_corpus"},"identity_limit":"L00_R known interference excludes recopy inference; L00_N changes confounded by A deletion, repeated copies and nearly-same method. No GUID labels assigned; paste identity untouched.","derived_limit":"Unknown changed ranges and stable opaque bytes do not establish derived-field completeness.","validation":{"eight_raw_pairs_sha256_matched":True,"eight_hex_roundtrips_matched":True,"raw_unchanged_during_analysis":True},"classifications":{"text_slot_milestone_status":"stable_pause_point","line_object_structure":"partial","line_endpoint_fields":"candidate_only","line_derived_fields":"partial","line_identity_fields":"unresolved","line_clipboard_synthesis_strategy":"unresolved","line_clipboard_runtime_readiness":"missing_specific_contract"}}
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))

if __name__ == "__main__":
    main()

