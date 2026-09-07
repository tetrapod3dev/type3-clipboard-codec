"""Controlled per-slot differential research. No runtime family or model changes."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser  # noqa: E402
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes  # noqa: E402
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser  # noqa: E402

TEXT_DIR = ROOT / 'tests/samples/text'
INTENT_DIR = ROOT / 'tests/samples/intents/text'
BASELINE = 'text_slotstyle_a8_baseline.txt'
POLICY = dict(scope='cparagraphe_per_slot_style_field_differential_analysis_only',
              runtime_parser_behavior='not_modified', prefix_family_runtime_change='not_performed',
              semantic_model_change='not_performed', color_ownership_assignment='not_performed',
              anchor_ownership_used=False, oracle_isolation=True)
LIMITS = dict(max_fixtures=9, max_hex_bytes=8_388_608, max_payload_bytes=1_048_576,
              max_nodes=128, max_paragraphs=32, max_prefix_hits=4096, max_slots=256,
              max_changed_ranges=256, max_probe_windows=64, max_detail_slots=4,
              max_fragment_bytes=16, json_bytes=100000, text_bytes=50000)
STRIDE = 204
TOKEN = b'\x05\0\0\0'
STRUCTURAL_KEYS = ('fixture_inventory', 'runtime_candidate_behavior', 'structural_alignment_summary',
                   'per_fixture_differentials', 'target_slot_isolation_summary',
                   'global_derived_change_summary', 'provisional_slot_field_map')


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def ranges(a, b):
    """Half-open ranges; unequal-length tails remain explicit, never zip-truncated."""
    result = []
    for i in range(max(len(a), len(b))):
        if i < min(len(a), len(b)) and a[i] == b[i]:
            continue
        if result and result[-1][1] == i:
            result[-1][1] += 1
        else:
            result.append([i, i + 1])
        if len(result) > LIMITS['max_changed_ranges']:
            raise ValueError('changed-range budget exceeded')
    return result


def delta(a, b):
    changed = ranges(a, b)
    return dict(changed_byte_count=sum(y-x for x, y in changed), ranges=changed,
                baseline_length=len(a), capture_length=len(b))


def discover(payload):
    """Analyzer-only count+terminal framed token recurrence, NOT runtime acceptance.

    Every maximal recurrence is retained. No semantic value, filename, target index,
    style mask or runtime exact family participates. Ambiguity remains unresolved.
    """
    if len(payload) > LIMITS['max_payload_bytes']:
        raise ValueError('payload budget exceeded')
    hits = set()
    start = 0
    while (p := payload.find(TOKEN, start)) >= 0:
        hits.add(p)
        if len(hits) > LIMITS['max_prefix_hits']:
            raise ValueError('prefix hit budget exceeded')
        start = p + 1
    runs = []
    for p in sorted(hits):
        if p - STRIDE in hits:
            continue
        count = 1
        while p + count * STRIDE in hits:
            count += 1
            if count > LIMITS['max_slots']:
                raise ValueError('slot budget exceeded')
        if count < 2:
            continue
        end = p + count * STRIDE
        complete = p >= 16 and end + 32 <= len(payload)
        views = [int.from_bytes(payload[p-4:p-4+w], 'little') for w in (1, 2, 4)] if p >= 16 else []
        terminal = payload[end-STRIDE+4:end-STRIDE+8] == b'\0' * 4
        eligible = complete and terminal and views == [count] * 3
        runs.append(dict(start=p, count=count, end=end, complete_period_windows=complete,
                         count_views=views, zero_terminal=terminal, eligible=eligible))
    return runs


def numeric_probes(a, b, changed):
    """Only 4-byte-grid windows intersecting discovered ranges; no expected encoding.

    f64 candidates may begin at either half of an 8-byte alignment. Probe width
    is diagnostic and is deliberately separate from changed-byte width.
    """
    windows = sorted({(p, width) for lo, hi in changed for width in (4, 8)
                      for p in range(max(0, (lo-width+4)//4*4), min(hi, STRIDE-width+1), 4)
                      if p < hi and p+width > lo})
    if len(windows) > LIMITS['max_probe_windows']:
        raise ValueError('probe budget exceeded')
    output = []
    for p, width in windows:
        def decode(data):
            value = struct.unpack('<f' if width == 4 else '<d', data[p:p+width])[0]
            return dict(float=value if math.isfinite(value) else None,
                        signed_integer=int.from_bytes(data[p:p+width], 'little', signed=True))
        output.append(dict(offset=p, probe_width=width, baseline=decode(a), capture=decode(b),
                           baseline_hex=a[p:p+width].hex(), capture_hex=b[p:p+width].hex(),
                           neighboring_bytes_stable=a[max(0,p-4):p] == b[max(0,p-4):p]
                           and a[p+width:p+width+4] == b[p+width:p+width+4]))
    return output


def load_raw(path):
    if path.stat().st_size > LIMITS['max_hex_bytes']:
        raise ValueError('hex input budget exceeded')
    raw = hex_text_to_bytes(path.read_text(encoding='utf-8'))
    parser = Type3ChainParser()
    _, _, offset = parser._read_top_level_header(raw)
    nodes = parser._extract_nodes(raw[offset:])
    if len(nodes) > LIMITS['max_nodes']:
        raise ValueError('node budget exceeded')
    paragraphs = [n for n in nodes if n.header.class_name == 'CParagraphe']
    if len(paragraphs) > LIMITS['max_paragraphs'] or sum(len(n.payload) for n in paragraphs) > LIMITS['max_payload_bytes']:
        raise ValueError('paragraph budget exceeded')
    discoveries = [discover(n.payload) for n in paragraphs]
    selected = [(i, r) for i, runs in enumerate(discoveries) for r in runs if r['eligible']]
    obj, parser_name = parse_type3_clipboard_bytes_with_parser(raw)
    candidate = obj.candidate_fields.get('text_slot_run')
    runtime = dict(parse_success=True, parser=parser_name, source_text=obj.source_text_candidate,
                   existing_visible_text=obj.display_text_candidate,
                   chain_text=[dict(source=c.source_text_candidate, display=c.display_text_candidate)
                               for c in obj.object_chains],
                   candidate_present=candidate is not None,
                   status='candidate_present' if candidate else 'safe_abstention')
    if candidate:
        runtime.update(slot_count=len(candidate['slots']), prefix_variant=candidate['prefix_variant'],
                       slot_code_sequence=[s['slot_code_candidate']['numeric_view'] for s in candidate['slots']])
    result = dict(raw=raw, nodes=nodes, paragraphs=paragraphs, discoveries=discoveries, runtime=runtime,
                  selected=None, top_offset=offset)
    if len(selected) == 1:
        index, run = selected[0]
        node = paragraphs[index]
        result['selected'] = dict(**run, paragraph_index=index, payload=node.payload,
                                  raw_payload_start=offset+node.payload_offset)
    return result


def compare(base, capture, details):
    a, b = base['selected'], capture['selected']
    if a is None or b is None or a['count'] != b['count']:
        return dict(status='unresolved', reason='no unique compatible independent alignment')
    aa = [a['payload'][p:p+STRIDE] for p in range(a['start'], a['end'], STRIDE)]
    bb = [b['payload'][p:p+STRIDE] for p in range(b['start'], b['end'], STRIDE)]
    # Byte-level code/layout alignment across captures, without expected text.
    if [v[:8] for v in aa] != [v[:8] for v in bb]:
        return dict(status='unresolved', reason='prefix/code alignment disagrees')
    rows, ranking = [], Counter()
    for ordinal, (left, right) in enumerate(zip(aa, bb)):
        changed = ranges(left, right)
        if not changed:
            continue
        probes = numeric_probes(left, right, changed)
        row = dict(slot_ordinal_zero_based=ordinal, slot_index_1based=ordinal+1,
                   terminal=ordinal == len(aa)-1, changed_ranges=changed, numeric_probes=probes)
        if details and len(rows) < LIMITS['max_detail_slots']:
            row['fragments'] = [dict(start=max(0, lo-4), baseline_hex=left[max(0,lo-4):min(hi+4,lo+12)].hex(),
                                     capture_hex=right[max(0,lo-4):min(hi+4,lo+12)].hex()) for lo, hi in changed]
        rows.append(row)
        ranking.update(tuple(v) for v in changed)
    header = delta(a['payload'][:a['start']], b['payload'][:b['start']])
    suffix = delta(a['payload'][a['end']:], b['payload'][b['end']:])
    outside = dict(before_payload=delta(base['raw'][:a['raw_payload_start']], capture['raw'][:b['raw_payload_start']]),
                   after_payload=delta(base['raw'][a['raw_payload_start']+len(a['payload']):],
                                       capture['raw'][b['raw_payload_start']+len(b['payload']):]))
    node_changes = []
    for x, y in zip(base['nodes'], capture['nodes']):
        if x.header.class_name != y.header.class_name:
            node_changes.append(dict(status='node_alignment_unresolved'))
            break
        if x.header.class_name == 'CParagraphe':
            continue
        changes = delta(x.payload, y.payload)
        if changes['changed_byte_count'] or x.bbox != y.bbox:
            node_changes.append(dict(class_name=x.header.class_name, payload_changed_bytes=changes['changed_byte_count'],
                                     bbox_changed=x.bbox != y.bbox, interpretation='diagnostic_only_ownership_unresolved'))
    probe_offsets = sorted({p['offset'] for row in rows for p in row['numeric_probes'] if p['probe_width']==8})
    def profile(slots, off):
        values = [struct.unpack_from('<d', slot, off)[0] for slot in slots]
        return [v if math.isfinite(v) else None for v in values]
    return dict(status='aligned', total_aligned_slots=len(aa), baseline_start=a['start'], capture_start=b['start'],
                relocation_bytes=b['start']-a['start'], changed_slot_ordinals_zero_based=[r['slot_ordinal_zero_based'] for r in rows],
                changed_slot_indices_1based=[r['slot_index_1based'] for r in rows], changed_slots=rows,
                all_slot_change=len(rows) == len(aa), terminal_changed=any(r['terminal'] for r in rows),
                count_changed=a['payload'][a['start']-4:a['start']] != b['payload'][b['start']-4:b['start']],
                header_upstream=header, suffix_after_period_windows=suffix, outside_payload=outside,
                other_structural_nodes=node_changes,
                field_candidate_ranking=[dict(range=list(r), changed_slot_count=n) for r,n in
                                         sorted(ranking.items(), key=lambda item:(item[1],item[0]))],
                stable_slot_count=len(aa)-len(rows),
                discovered_f64_profiles={str(off):dict(baseline=profile(aa,off), capture=profile(bb,off))
                                         for off in probe_offsets})


def structural_phase(paths, baseline, details=False):
    """All structural discovery/ranking completes here, before intent can be read."""
    if len(paths) > LIMITS['max_fixtures']:
        raise ValueError('fixture budget exceeded')
    loaded, inventory, warnings = {}, [], []
    for path in sorted(paths):
        try:
            data = load_raw(path)
            loaded[path.name] = data
            inventory.append(dict(fixture=path.name, sha256=hashlib.sha256(data['raw']).hexdigest(),
                                  raw_size=len(data['raw']), status='loaded'))
        except (ValueError, OSError, EOFError) as exc:
            warnings.append(f'{path.name}: unresolved: {exc}')
            inventory.append(dict(fixture=path.name, status='unresolved'))
    ref = loaded.get(baseline)
    diffs = {name: compare(ref, data, details) if ref else dict(status='unresolved', reason='baseline_missing')
             for name,data in loaded.items()}
    if len(paths) < LIMITS['max_fixtures']:
        warnings.append('Controlled inventory incomplete; continuing available captures')
    if not ref:
        warnings.append('Baseline missing; comparisons unresolved')
    alignment = {name: dict(status='aligned' if data['selected'] else 'unresolved',
                           paragraph_runs=data['discoveries']) for name,data in loaded.items()}
    field_map = Counter()
    probe_map = Counter()
    for diff in diffs.values():
        probe_map.update(int(off) for off in diff.get('discovered_f64_profiles', {}))
        for row in diff.get('field_candidate_ranking', []):
            field_map[tuple(row['range'])] += 1
    reference_regions = [dict(relative_range=[off,off+8], fixture_count=n, status='cross_fixture_candidate',
        interpretation='unresolved', typed_width=None,
        structural_observation='diagnostic 8-byte probe intersecting discovered delta; not confirmed extent')
        for off,n in sorted(probe_map.items())]
    reference_regions += [dict(relative_range=[4,8], fixture_count=0, status='unresolved',
        interpretation='slot_code_candidate_diagnostic_only', typed_width=None,
        structural_observation='prefix/code windows equal in aligned comparisons')]
    return dict(warnings=warnings, fixture_inventory=inventory,
                runtime_candidate_behavior={name:data['runtime'] for name,data in loaded.items()},
                structural_alignment_summary=alignment, per_fixture_differentials=diffs,
                target_slot_isolation_summary={name:dict(changed_slot_ordinals_zero_based=d.get('changed_slot_ordinals_zero_based', []),
                    single_changed_slot=len(d.get('changed_slots', [])) == 1) for name,d in diffs.items()},
                global_derived_change_summary={name:{k:d[k] for k in ('header_upstream','suffix_after_period_windows',
                    'outside_payload','other_structural_nodes') if k in d} for name,d in diffs.items()},
                provisional_slot_field_map=reference_regions+[dict(relative_range=list(r), fixture_count=n, status='cross_fixture_candidate',
                    interpretation='unresolved', typed_width=None) for r,n in sorted(field_map.items())])


def load_oracle(name):
    import yaml
    text = (INTENT_DIR / (Path(name).stem+'.md')).read_text(encoding='utf-8')
    return yaml.safe_load(text.split('```yaml\n',1)[1].split('```',1)[0])['intent_metadata']


def oracle_phase(frozen, enabled):
    """Only frozen JSON crosses this boundary; no discovery reruns or raw buffer access."""
    evidence = json.loads(frozen)
    if not enabled:
        return dict(enabled=False, status='unresolved')
    controls, results, warnings = {}, {}, []
    for item in evidence['fixture_inventory']:
        name = item['fixture']
        try:
            meta = load_oracle(name)
        except (OSError, ValueError, KeyError, IndexError) as exc:
            warnings.append(f'{name}: intent unavailable: {exc}')
            continue
        controls[name] = meta
        diff = evidence['per_fixture_differentials'].get(name, {})
        target = meta['target_character_index_1based']-1
        prop, expected = meta['changed_property'], meta['changed_value']
        tests = []
        for row in diff.get('changed_slots', []):
            for probe in row['numeric_probes']:
                matches = []
                for encoding, value in [('f32le' if probe['probe_width']==4 else 'f64le', probe['capture']['float']),
                                        ('signed_integer', probe['capture']['signed_integer'])]:
                    if not isinstance(expected, (float,int)) or value is None:
                        continue
                    candidates = {'native':expected}
                    if prop == 'height_mm':
                        candidates['meters'] = expected/1000
                    if prop == 'width_percent':
                        candidates['ratio'] = expected/100
                    if prop in ('slant_degrees','rotation_degrees'):
                        candidates['radians'] = math.radians(expected)
                    for units, number in candidates.items():
                        if math.isclose(value, number, rel_tol=1e-6, abs_tol=1e-9):
                            matches.append(dict(encoding=encoding, units=units, value=value))
                if matches:
                    tests.append(dict(slot_ordinal_zero_based=row['slot_ordinal_zero_based'], offset=probe['offset'],
                                      probe_width=probe['probe_width'], matches=matches,
                                      baseline_value=probe['baseline']['float'],
                                      baseline_hex=probe['baseline_hex'], capture_hex=probe['capture_hex'],
                                      neighboring_bytes_stable=probe['neighboring_bytes_stable']))
        color = None
        if prop == 'color':
            changed = next((r for r in diff.get('changed_slots',[]) if r['slot_ordinal_zero_based']==target),None)
            # The 80-byte probe only exists if independently discovered changes intersect it.
            probe = next((p for p in (changed or {}).get('numeric_probes',[]) if p['offset']==80),None)
            color = bool(probe and probe['baseline_hex'].startswith('98cc98') and
                         probe['capture_hex'].startswith('3060cc') and changed['changed_ranges']==[[80,83]])
        results[name] = dict(changed_property=prop, base_value=meta['base_value'], changed_value=expected,
            human_target_index_1based=target+1, slot_ordinal_zero_based=target,
            only_target_slot_differs=diff.get('changed_slot_ordinals_zero_based')==[target],
            target_has_local_change=target in diff.get('changed_slot_ordinals_zero_based', []),
            encoding_matches=tests, color_control_alignment_status=('strong_style_field_candidate' if color else 'contradicted')
            if prop=='color' else 'not_applicable')
    expected_matrix={('none',None),('height_mm',20),('width_percent',50),('width_percent',150),
                     ('slant_degrees',15),('slant_degrees',-15),('rotation_degrees',15),('rotation_degrees',-15),
                     ('color','Navy Blue')}
    observed={(m['changed_property'],m['changed_value']) for m in controls.values()}
    warnings.extend(f'Missing logical control: {p}={v}' for p,v in sorted(expected_matrix-observed, key=str))
    shared_keys=('visible_text','font','character_count','lower_left_mm','anchor_mm','alignment',
                 'target_character_index_1based','base_character_attributes','all_other_character_properties_held_constant',
                 'capture_reset_between_fixtures','z_coordinate_note')
    shared = {k:next(iter(controls.values()))[k] for k in shared_keys} if controls else {}
    consistent = all(all(m[k]==shared[k] for k in shared) for m in controls.values())
    return dict(enabled=True, controls=controls, results=results, shared_capture_controls=shared,
                shared_controls_consistent=consistent, warnings=warnings,
                fixture_control_quality='documented_controls_with_unexplained_secondary_changes' if consistent else 'unresolved')


def summarize(oracle, property_name, evidence):
    rows={name:r for name,r in oracle.get('results',{}).items() if r['changed_property']==property_name}
    matches=[dict(fixture=name, **m) for name,r in rows.items() for m in r['encoding_matches']
             if m['slot_ordinal_zero_based']==r['slot_ordinal_zero_based']]
    profiles = []
    for m in matches:
        if m['probe_width'] != 8:
            continue
        profile = evidence['per_fixture_differentials'][m['fixture']]['discovered_f64_profiles'][str(m['offset'])]
        ordinal = m['slot_ordinal_zero_based']
        profiles.append(dict(fixture=m['fixture'], offset=m['offset'], **profile,
            other_visible_slots_stable=all(a==b for i,(a,b) in enumerate(zip(profile['baseline'][:-1],profile['capture'][:-1]))
                                           if i!=ordinal),
            terminal_field_stable=profile['baseline'][-1]==profile['capture'][-1]))
    covered = {m['fixture'] for m in matches}
    strong = bool(rows) and covered == set(rows)
    values = [p['capture'][rows[p['fixture']]['slot_ordinal_zero_based']] for p in profiles]
    symmetry = len(values)==2 and math.isclose(values[0],-values[1],abs_tol=1e-9)
    return dict(status='strong_style_field_candidate' if strong else 'unresolved',
                candidate_label=property_name.replace('_degrees','')+'_correlated_field_candidate',
                fixtures=list(rows), target_encoding_matches=matches, field_profiles=profiles,
                positive_negative_symmetry=symmetry if property_name.endswith('_degrees') else None,
                hypotheses_tested=['f32le native/degrees and radians', 'f64le native/degrees and radians',
                                   'signed integer diagnostic views', 'meters/ratio when intent applicable'],
                typed_width=None, ownership='unresolved')


def build_report(paths=None, baseline=BASELINE, oracle_enabled=True, details=False):
    paths = sorted(TEXT_DIR.glob('text_slotstyle_a8_*.txt')) if paths is None else paths
    frozen = compact(structural_phase(paths, baseline, details))
    # All raw discovery and candidate ranking are immutable before this call.
    oracle = oracle_phase(frozen, oracle_enabled)
    report = json.loads(frozen)
    report.update(mode='details' if details else 'summary', policy=POLICY, limits=LIMITS,
                  shared_capture_controls=oracle.get('shared_capture_controls',{}), oracle_summary=oracle)
    for label, prop in [('height','height_mm'),('width','width_percent'),('slant','slant_degrees'),('rotation','rotation_degrees')]:
        report[label+'_candidate_summary']=summarize(oracle,prop,report)
    color_rows=[r for r in oracle.get('results',{}).values() if r['changed_property']=='color']
    color_ok=bool(color_rows) and all(r['color_control_alignment_status']=='strong_style_field_candidate' and
                                    r['only_target_slot_differs'] for r in color_rows)
    report['color_control_summary']=dict(color_control_alignment_status='strong_style_field_candidate' if color_ok else 'unresolved',
                                        typed_width=None, ownership='unresolved')
    ready=color_ok and all(report[k+'_candidate_summary']['status']=='strong_style_field_candidate' for k in ('height','width'))
    report['runtime_prefix_family_implication']=dict(
        runtime_prefix_family_review_readiness='ready_for_review' if ready else 'not_ready',
        v1_height_explanation='supported_as_diagnostic_f64_height' if ready else 'unresolved',
        v0_v1_prior_f64_views_meters=[0.01,0.03] if ready else [],
        v2_plus08_explanation='unresolved', style_dependent_prefix_identity=ready,
        current_family_overconstrained_for_controlled_styles=ready,
        future_review='Evaluate separation of style bytes from framing; no new variants or masks authorized',
        candidate_parser_change_readiness='not_ready')
    report['oracle_summary']['slant_rotation_comparison'] = dict(
        primary_ranges='independent_disjoint_ranges' if all(report[k+'_candidate_summary']['status']==
            'strong_style_field_candidate' for k in ('slant','rotation')) else 'unresolved',
        secondary_changes='Both have upstream/suffix changes and unexplained +0x2D..+0x2F changes in other slots; see raw diffs')
    report['oracle_summary']['provisional_interpretations'] = [
        dict(relative_range=[m['offset'],m['offset']+m['probe_width']],
             diagnostic_semantic_candidate=label+'_correlated_field_candidate',
             status=report[label+'_candidate_summary']['status'], typed_width=None)
        for label in ('height','width','slant','rotation')
        for m in report[label+'_candidate_summary']['target_encoding_matches'][:1]]
    report['answers']=dict(fixture_control_quality=oracle.get('fixture_control_quality','unresolved'),
        target_slot_isolation_status='primary_changes_at_target_with_secondary_slot_changes' if ready else 'unresolved',
        color_control_alignment_status=report['color_control_summary']['color_control_alignment_status'],
        slot_style_struct_readiness='not_ready', runtime_prefix_family_review_readiness='ready_for_review' if ready else 'not_ready',
        candidate_parser_change_readiness='not_ready', color_ownership_readiness='not_ready')
    for label in ('height','width','slant','rotation'):
        summary=report[label+'_candidate_summary']
        report['answers'][label+'_field_candidate']=summary['status']
        report['answers'][label+'_encoding_candidate']=sorted({m['encoding']+'_'+m['units']
            for row in summary['target_encoding_matches'] for m in row['matches']})
    report['warnings'].extend(oracle.get('warnings',[]))
    if not oracle_enabled:
        report['warnings'].append('Intent/oracle disabled; semantic hypotheses unresolved')
    return report


def render_text(report):
    lines=['CParagraphe per-slot style differential analysis (candidate-only research)',
           compact(report['answers']), 'All ranges are half-open; slot ordinals are zero-based.']
    for name,diff in report['per_fixture_differentials'].items():
        lines.append(name+': '+compact({k:v for k,v in diff.items() if k not in
                     ('changed_slots','discovered_f64_profiles','outside_payload','other_structural_nodes')}))
        for row in diff.get('changed_slots',[]):
            lines.append('  slot '+str(row['slot_ordinal_zero_based'])+' (human '+str(row['slot_index_1based'])+'): '+
                         compact({k:v for k,v in row.items() if k!='numeric_probes'}))
    lines.extend(report['warnings'])
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--details',action='store_true')
    parser.add_argument('--no-oracle',action='store_true')
    parser.add_argument('--baseline',default=BASELINE,help='Reference file label only, not a structural selector')
    parser.add_argument('--fixtures',nargs='+',type=Path)
    args=parser.parse_args()
    try:
        report=build_report(args.fixtures,args.baseline,not args.no_oracle,args.details)
        output=compact(report)+'\n' if args.json else render_text(report)
        if len(output.encode()) >= LIMITS['json_bytes' if args.json else 'text_bytes']:
            raise ValueError('output budget exceeded; no partial report emitted')
    except ValueError as exc:
        parser.error(str(exc))
    print(output,end='')


if __name__=='__main__':
    main()
