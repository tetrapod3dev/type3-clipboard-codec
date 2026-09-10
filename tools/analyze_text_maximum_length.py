"""Bounded maximum-length research; oracle-free object differences precede interpretation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_slot_spacing_fields as research  # noqa: E402

FIXTURES = ('text_slotstyle_a8_baseline.txt', 'text_maxlength_a8_100mm.txt',
            'text_maxlength_a8_60mm.txt', 'text_maxlength_a8_40mm.txt', 'text_maxlength_a8_m60mm.txt')
POLICY = dict(scope='text_object_maximum_length_differential_analysis_only',
              runtime_parser_behavior='not_modified', f4_runtime_change='not_performed',
              semantic_maxlength_promotion='not_performed', ownership_assignment='not_performed',
              oracle_isolation=True)
LIMITS = dict(max_fixtures=5, max_ranges=256, max_numeric_windows=128,
              max_raw_bytes=8388608, fragment_bytes=8, detail_ranges=4,
              json_bytes=100000, text_bytes=50000)
FIELDS = {'height': (12, 20), 'width': (20, 28), 'slant': (28, 36), 'auxiliary': (44, 48),
          'spacing': (64, 72), 'rotation': (72, 80), 'rgb': (80, 83)}
F4 = {'plus00': (0, 4), 'plus08': (8, 9), 'plus09': (9, 12), 'plus24': (36, 44), 'plus38': (56, 64)}
compact = research.compact


def delta(a, b, details=False):
    spans = research.prior.ranges(a, b)
    result = dict(lengths=[len(a), len(b)], changed_bytes=sum(hi-lo for lo, hi in spans), ranges=spans)
    if details:
        result['fragments'] = [[lo, hi, a[lo:min(hi, lo+8)].hex(), b[lo:min(hi, lo+8)].hex()]
                               for lo, hi in spans[:LIMITS['detail_ranges']]]
    return result


def merged_ranges(points):
    result = []
    for p in sorted(points):
        if result and result[-1][1] == p:
            result[-1][1] += 1
        else:
            result.append([p, p+1])
    return result


def numeric_windows(payloads):
    """Only isolated cohort-union 8-byte deltas, or 7-byte deltas + one stable byte.

    Never scan offsets for expected values, split wider blobs, or probe alternate
    alignments/types. Seven-byte extension is an explicit untyped f64 hypothesis.
    """
    if not payloads or len({len(p) for p in payloads}) != 1:
        return []
    points = {i for p in payloads[1:] for lo, hi in research.prior.ranges(payloads[0], p)
              for i in range(lo, hi)}
    result = []
    for lo, hi in merged_ranges(points):
        width = hi-lo
        if width not in (7, 8) or lo+8 > len(payloads[0]):
            continue
        if width == 7 and len({p[hi] for p in payloads}) != 1:
            continue
        result.append(dict(relative_range=[lo, lo+8], discovered_delta=[lo, hi],
                           nomination='exact_eight_byte_union' if width == 8 else 'seven_byte_union_plus_stable_high_byte',
                           raw=[p[lo:lo+8].hex() for p in payloads], typed_width=None))
    return result


def geometry(node):
    if node.bbox is None:
        return None
    bbox = asdict(node.bbox)
    return dict(bbox=bbox, x_extent_mm=(bbox['xmax_m']-bbox['xmin_m'])*1000,
                y_extent_mm=(bbox['ymax_m']-bbox['ymin_m'])*1000,
                role='parsed_geometry_not_rendered_glyph_measurement')


def outside(data):
    spans = sorted((data['base']+n.start_offset, data['base']+n.payload_offset+len(n.payload))
                   for n in data['nodes'])
    parts, cursor = [], 0
    for lo, hi in spans:
        if lo < cursor or hi > len(data['raw']):
            raise ValueError('overlapping/out-of-bounds node extents')
        parts.append((cursor, data['raw'][cursor:lo]))
        cursor = hi
    parts.append((cursor, data['raw'][cursor:]))
    return parts


def audit(loaded, regions):
    result = {}
    baseline = research.slots(loaded[0]) if loaded[0]['selected'] else []
    for name, (lo, hi) in regions.items():
        result[name] = dict(relative_range=[lo, hi], fixtures={})
        for i, data in enumerate(loaded):
            if not data['selected']:
                continue
            rows = research.slots(data)
            result[name]['fixtures'][f'f{i}'] = [
                [j, j == len(rows)-1, row[lo:hi].hex(),
                 None if len(rows) != len(baseline) else row[lo:hi] != baseline[j][lo:hi]]
                for j, row in enumerate(rows)]
    return dict(columns=['ordinal', 'terminal', 'raw_hex', 'changed_from_baseline'], regions=result)


def structural_phase(paths, details=False):
    if len(paths) != 5 or len({p.name for p in paths}) != 5:
        raise ValueError('exactly five uniquely labelled inputs required; first is reference')
    # Each read observes runtime before research recurrence; no intent reader is called.
    loaded = [research.read_capture(p) for p in paths]
    inventory = [dict(id=f'f{i}', fixture=p.name, file_sha256=d['file_sha256'],
                      raw_sha256=hashlib.sha256(d['raw']).hexdigest(), raw_size=len(d['raw']))
                 for i, (p, d) in enumerate(zip(paths, loaded, strict=True))]
    warnings = []
    node_classes = [n.header.class_name for n in loaded[0]['nodes']]
    aligned = all([n.header.class_name for n in d['nodes']] == node_classes for d in loaded)
    node_diffs, para_diffs, geometry_rows, candidates = {}, {}, {}, []
    # Complete node/header comparisons happen before slot-region breakdown.
    for i, d in enumerate(loaded):
        geometry_rows[f'f{i}'] = [dict(node=j, class_name=n.header.class_name, geometry=geometry(n))
                                  for j, n in enumerate(d['nodes'])]
    if aligned:
        for a, b in combinations(range(5), 2):
            x, y = loaded[a], loaded[b]
            pair = f'f{a}:f{b}'
            pair_details = details and (a, b) == (0, 1)
            rows = []
            for j, (n, m) in enumerate(zip(x['nodes'], y['nodes'], strict=True)):
                rows.append(dict(node=j, class_name=n.header.class_name,
                                 payload=delta(n.payload, m.payload, pair_details),
                                 header=delta(x['raw'][x['base']+n.start_offset:x['base']+n.payload_offset],
                                              y['raw'][y['base']+m.start_offset:y['base']+m.payload_offset], pair_details),
                                 bbox_changed=n.bbox != m.bbox))
            gaps_a, gaps_b = outside(x), outside(y)
            node_diffs[pair] = dict(nodes=rows, outside_nodes=[
                dict(starts=[ga[0], gb[0]], **delta(ga[1], gb[1], pair_details))
                for ga, gb in zip(gaps_a, gaps_b, strict=True)])
        for j, cls in enumerate(node_classes):
            for candidate in numeric_windows([d['nodes'][j].payload for d in loaded]):
                candidate.update(node=j, class_name=cls, coordinate_domain='node_payload_relative')
                candidates.append(candidate)
        if len(candidates) > LIMITS['max_numeric_windows']:
            raise ValueError('numeric nomination budget exceeded')
    else:
        warnings.append('node sequence alignment unresolved; no object numeric nominations')
    alignment = {}
    for i, d in enumerate(loaded):
        compatible = bool(d['selected'] and loaded[0]['selected'] and
                          d['selected']['count'] == loaded[0]['selected']['count'])
        if compatible:
            compatible = [s[:8] for s in research.slots(d)] == [s[:8] for s in research.slots(loaded[0])]
        alignment[f'f{i}'] = dict(status='aligned' if aligned and compatible else 'unresolved',
                                  selected=d['selected'], raw_runs=d['runs'])
        if alignment[f'f{i}']['status'] != 'aligned':
            warnings.append(f'f{i}: independent slot alignment unresolved')
    for a, b in combinations(range(5), 2):
        pair = f'f{a}:f{b}'
        pair_details = details and (a, b) == (0, 1)
        if any(alignment[f'f{i}']['status'] != 'aligned' for i in (a, b)):
            para_diffs[pair] = dict(status='unresolved')
            continue
        x, y = loaded[a], loaded[b]
        r, s = x['selected'], y['selected']
        p, q = x['paragraphs'][r['paragraph_index']].payload, y['paragraphs'][s['paragraph_index']].payload
        para_diffs[pair] = dict(status='aligned', starts=[r['start'], s['start']], stride=204,
                               upstream=delta(p[:r['start']], q[:s['start']], pair_details),
                               suffix=delta(p[r['end']:], q[s['end']:], pair_details),
                               suffix_starts=[r['end'], s['end']],
                               slots=[dict(ordinal=j, terminal=j == r['count']-1, **delta(u, v, pair_details))
                                      for j, (u, v) in enumerate(zip(research.slots(x), research.slots(y), strict=True))])
    return dict(mode='details' if details else 'summary', policy=POLICY, limits=LIMITS, warnings=warnings,
                fixture_inventory=inventory, runtime_candidate_summary={f'f{i}': d['runtime'] for i, d in enumerate(loaded)},
                structural_alignment_summary=alignment, node_level_differentials=node_diffs,
                cparagraphe_region_differentials=para_diffs,
                slot_field_audit=audit(loaded, FIELDS), f4_summary=audit(loaded, F4),
                geometry_summary=geometry_rows,
                numeric_candidate_summary=dict(nomination_policy='isolated cohort-union 7/8-byte payload ranges only',
                                               candidates=candidates, typed_width=None))


def load_intent(name):
    return research.load_intent(name)


def payload_points(report, pair):
    return {(n['node'], p) for n in report['node_level_differentials'].get(pair, {}).get('nodes', [])
            for lo, hi in n['payload']['ranges'] for p in range(lo, hi)}


def point_table(points):
    return {str(node): merged_ranges(p for j, p in points if j == node)
            for node in sorted({j for j, _ in points})}


def pair_key(a, b):
    return ':'.join(sorted((a, b)))


def comparison_brief(report, pair):
    para = report['cparagraphe_region_differentials'].get(pair, {})
    return dict(pair=pair, paragraph_upstream=para.get('upstream'),
                paragraph_suffix_changed_bytes=para.get('suffix', {}).get('changed_bytes'),
                slot_changed_bytes=sum(s['changed_bytes'] for s in para.get('slots', [])),
                nodes=[dict(node=n['node'], class_name=n['class_name'],
                            payload_changed_bytes=n['payload']['changed_bytes'],
                            header_changed_bytes=n['header']['changed_bytes'], bbox_changed=n['bbox_changed'])
                       for n in report['node_level_differentials'].get(pair, {}).get('nodes', [])])


def oracle_phase(frozen, enabled):
    """Only frozen bounded JSON crosses this boundary; no binary reads/selectors."""
    evidence = json.loads(frozen)
    result = dict(enabled=enabled, labels={}, warnings=[], numeric_tests=[], requested_matches=[],
                  compression_candidates=[], classifications=[], comparisons={}, symmetry={},
                  requested_vs_geometry={}, f32_integer_status='not_tested: no justified exact four-byte '
                  'nomination; no integer-width evidence', status='unresolved')
    if not enabled:
        return result
    labels = result['labels']
    for row in evidence['fixture_inventory'][1:]:
        try:
            meta = load_intent(row['fixture'])
            if meta['property'] != 'maximum_length' or meta['changed_scope'] != 'text_object':
                raise ValueError('wrong intent property/scope')
            labels[row['id']] = {k: meta[k] for k in ('baseline_value_mm', 'changed_value_mm',
                'baseline_natural_length_mm', 'expected_ui_relationship', 'observed_program_behavior')}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result['warnings'].append(f"{row['id']}: intent unresolved: {exc}")
    requested = {'f0': 0}
    requested.update({key: m['changed_value_mm'] for key, m in labels.items()})
    naturals = {m['baseline_natural_length_mm'] for m in labels.values()}
    natural = next(iter(naturals)) if len(naturals) == 1 else None
    valid = len(labels) == 4 and all(m['baseline_value_mm'] == 0 for m in labels.values())
    ids = {v: k for k, v in requested.items()}
    designed = valid and len(ids) == 5 and set(ids) == {0, 100, 60, 40, -60}
    for key, value in requested.items():
        result['requested_vs_geometry'][key] = dict(requested_mm=value,
            natural_mm=natural, relationship=('unresolved' if natural is None else
                'negative' if value < 0 else 'default' if value == 0 else
                'above_natural' if value > natural else 'below_natural'),
            geometry_reference='geometry_summary.'+key)
    for index, c in enumerate(evidence['numeric_candidate_summary']['candidates']):
        values = [struct.unpack('<d', bytes.fromhex(raw))[0] for raw in c['raw']]
        values = [v if math.isfinite(v) else None for v in values]
        tests = {unit: valid and all(v is not None and math.isclose(v, requested[f'f{i}']/scale,
                        rel_tol=1e-12, abs_tol=1e-15) for i, v in enumerate(values))
                 for unit, scale in (('f64le_meters', 1000), ('f64le_millimeters', 1))}
        row = dict(candidate=index, values=values, hypotheses=tests, category='unresolved')
        if any(tests.values()):
            row['category'] = 'object_setting_candidate'
            result['requested_matches'].append(dict(candidate=index, node=c['node'],
                relative_range=c['relative_range'], encoding=[k for k, v in tests.items() if v]))
        if designed:
            v0, v100, v60, v40, vm60 = [values[int(ids[v][1:])] for v in (0, 100, 60, 40, -60)]
            if (all(v is not None for v in values) and 0 < v40 < v60 < v100 == 1 and
                    v100 >= v0 > v60 and v60 == vm60):
                row['category'] = 'compression_correlated_candidate'
                row['duplicate_raw_candidates'] = [j for j, other in enumerate(
                    evidence['numeric_candidate_summary']['candidates']) if j != index and c['raw'] == other['raw']]
                if natural is not None and natural > 0:
                    row['ratio_diagnostics'] = [dict(requested_mm=v, candidate=values[int(ids[v][1:])],
                        requested_over_natural=v/natural, natural_over_requested=natural/v,
                        residual=values[int(ids[v][1:])]-v/natural,
                        matches=math.isclose(values[int(ids[v][1:])], v/natural, rel_tol=1e-9, abs_tol=1e-12))
                        for v in (60, 40)]
                result['compression_candidates'].append(dict(candidate=index, node=c['node'],
                                                              relative_range=c['relative_range']))
            if (c['raw'][int(ids[60][1:])] == c['raw'][int(ids[-60][1:])] and
                    row['category'] == 'compression_correlated_candidate'):
                row['positive_negative_magnitude_identical'] = True
        # Whole-profile equality to existing parsed bbox supports geometry diagnostics only.
        for field in ('xmin_m', 'xmax_m', 'ymin_m', 'ymax_m'):
            profiles = [[n['geometry']['bbox'][field] for n in evidence['geometry_summary'][f'f{i}']
                         if n['geometry']] for i in range(5)]
            if all(v is not None and v in profiles[i] for i, v in enumerate(values)):
                row['geometry_match'] = field
                if row['category'] == 'unresolved':
                    row['category'] = 'geometry_derived_candidate'
        result['numeric_tests'].append(row)
    if designed:
        for label, a, b in (('baseline_vs_100', 0, 100), ('baseline_vs_60', 0, 60),
                ('baseline_vs_40', 0, 40), ('baseline_vs_negative', 0, -60),
                ('compression_activation', 100, 60), ('sixty_vs_forty', 60, 40), ('positive_negative', 60, -60)):
            result['comparisons'][label] = comparison_brief(evidence, pair_key(ids[a], ids[b]))
        b100 = payload_points(evidence, pair_key(ids[0], ids[100]))
        b60 = payload_points(evidence, pair_key(ids[0], ids[60]))
        b40 = payload_points(evidence, pair_key(ids[0], ids[40]))
        bn = payload_points(evidence, pair_key(ids[0], ids[-60]))
        pn = payload_points(evidence, pair_key(ids[60], ids[-60]))
        result['comparisons']['compression_activation']['additional_vs_baseline_100'] = point_table(b60-b100)
        result['symmetry'] = dict(shared_baseline_changed_ranges=point_table(b60 & bn),
            identical_baseline_range_boundaries={str(n['node']): [r for r in n['payload']['ranges'] if r in
                evidence['node_level_differentials'][pair_key(ids[0], ids[-60])]['nodes'][n['node']]['payload']['ranges']]
                for n in evidence['node_level_differentials'][pair_key(ids[0], ids[60])]['nodes']},
            negative_only_vs_all_positive=point_table(bn-(b100 | b60 | b40)),
            positive_negative_differences=point_table(pn), numeric_symmetry=[])
        for index, c in enumerate(evidence['numeric_candidate_summary']['candidates']):
            a, b = [bytes.fromhex(c['raw'][int(ids[v][1:])]) for v in (60, -60)]
            va, vb = [struct.unpack('<d', raw)[0] for raw in (a, b)]
            sign_only = a[:7] == b[:7] and a[7] ^ b[7] == 128
            if a == b or sign_only:
                result['symmetry']['numeric_symmetry'].append(dict(candidate=index,
                    raw_identical=a == b, sign_only=sign_only, magnitude_identical=abs(va) == abs(vb),
                    category='sign_correlated_candidate' if sign_only else 'meaning_unresolved'))
        # A bounded category map applies to every raw range; unassigned bytes stay unresolved.
        result['classifications'] = dict(default='unresolved',
            candidate_windows=[dict(node=c['node'], relative_range=c['relative_range'], category=t['category'])
                for t in result['numeric_tests'] if t['category'] != 'unresolved'
                for c in [evidence['numeric_candidate_summary']['candidates'][t['candidate']]]],
            negative_only_ranges=result['symmetry']['negative_only_vs_all_positive'],
            negative_only_category='negative_length_correlated_candidate',
            rule='split a changed range at map boundaries; no whole-blob semantic assignment')
        result['status'] = 'evaluated'
    return result


def finish_report(evidence, oracle):
    region_status = {}
    for key, region in evidence['f4_summary']['regions'].items():
        rows = [r for fixture in region['fixtures'].values() for r in fixture]
        region_status[key] = ('unresolved' if len(rows) != 45 or any(r[3] is None for r in rows) else
            'current_f4_structural_constant_candidate_falsified_by_maximum_length' if any(r[3] for r in rows)
            else 'not_falsified_by_current_maxlength_controls')
    changed_f4 = any(v.startswith('current_f4') for v in region_status.values())
    invariant = all(v == 'not_falsified_by_current_maxlength_controls' for v in region_status.values())
    def field_state(key):
        rows = [r for values in evidence['slot_field_audit']['regions'][key]['fixtures'].values() for r in values]
        return 'unchanged_all_visible_and_terminal' if len(rows) == 45 and all(r[3] is False for r in rows) else 'unresolved'
    comparisons = oracle['comparisons']
    matches = oracle['requested_matches']
    setting = matches[0] if len(matches) == 1 else None
    evidence.update(
        baseline_vs_100_summary=comparisons.get('baseline_vs_100', {'status': 'oracle_disabled_or_unresolved'}),
        compression_activation_summary=comparisons.get('compression_activation', {'status': 'oracle_disabled_or_unresolved'}),
        sixty_vs_forty_summary=comparisons.get('sixty_vs_forty', {'status': 'oracle_disabled_or_unresolved'}),
        positive_negative_symmetry_summary=oracle['symmetry'], oracle_summary=oracle,
        answers=dict(fixtures_aligned=sum(r['status'] == 'aligned' for r in evidence['structural_alignment_summary'].values()),
            runtime_candidate_presence={k: r['candidate_present'] for k, r in evidence['runtime_candidate_summary'].items()},
            object_setting_candidate_range=setting, object_setting_diagnostic_encoding=setting['encoding'] if setting else 'unresolved',
            baseline_vs_100_primary_changes=comparisons.get('baseline_vs_100', {}).get('paragraph_upstream'),
            compression_activation_candidate_ranges=oracle['compression_candidates'],
            sixty_vs_forty_scaling_status='decreasing_candidates_simple_ratio_not_established' if oracle['compression_candidates'] else 'unresolved',
            positive_negative_shared_ranges='positive_negative_symmetry_summary.shared_baseline_changed_ranges',
            negative_only_ranges='positive_negative_symmetry_summary.negative_only_vs_all_positive',
            sign_correlated_candidate=[r for r in oracle['symmetry'].get('numeric_symmetry', []) if r['sign_only']],
            per_slot_width_candidate_behavior=field_state('width'), spacing_candidate_behavior=field_state('spacing'),
            terminal_behavior='complete_204_bytes_unchanged' if all(not s['changed_bytes']
                for d in evidence['cparagraphe_region_differentials'].values() for s in d.get('slots', []) if s['terminal'])
                and all(r['status'] == 'aligned' for r in evidence['structural_alignment_summary'].values()) else 'unresolved',
            f4_plus24_status=region_status['plus24'], f4_plus38_status=region_status['plus38'],
            f4_style_contamination_status='demonstrated_by_current_controls' if changed_f4 else
                'not_demonstrated_by_current_controls' if invariant else 'unresolved',
            geometry_change_status='parsed_bbox_changes_reported_separately_from_rendering',
            maximum_length_field_readiness='strong_object_setting_candidate' if setting else 'unresolved',
            compression_model_readiness='provisional_correlated_candidates_model_unresolved',
            negative_length_model_readiness='sign_correlation_only_reflection_model_unresolved',
            runtime_f4_review_readiness='ready_for_review' if changed_f4 else
                'no_maxlength_falsification_trigger' if invariant else 'unresolved',
            runtime_change_readiness='not_authorized_in_this_task', parser_safe=False, ownership_status='unresolved'))
    return evidence


def build_report(paths=None, oracle_enabled=True, details=False):
    paths = [research.TEXT / n for n in FIXTURES] if paths is None else list(paths)
    frozen = compact(structural_phase(paths, details))
    report = json.loads(frozen)
    oracle = oracle_phase(frozen, oracle_enabled)
    oracle['structural_sha256'] = hashlib.sha256(frozen.encode()).hexdigest()
    return finish_report(report, oracle)


def render(report, json_output=False):
    if json_output:
        output = compact(report) + '\n'
    else:
        output = 'Maximum-length research (half-open ranges)\n' + compact(report['fixture_inventory']) + '\n'
        for key in ('answers', 'runtime_candidate_summary',
                    'baseline_vs_100_summary', 'compression_activation_summary', 'sixty_vs_forty_summary',
                    'positive_negative_symmetry_summary', 'numeric_candidate_summary', 'geometry_summary'):
            output += key + ': ' + compact(report[key]) + '\n'
        output += 'numeric_diagnostics: ' + compact(report['oracle_summary']['numeric_tests']) + '\n'
        for pair, d in report['node_level_differentials'].items():
            output += pair + ': ' + compact(d) + '\n'
    if len(output.encode()) >= LIMITS['json_bytes' if json_output else 'text_bytes']:
        raise ValueError('output budget exceeded; no partial output')
    return output



BOUNDARY_FIXTURES = tuple(f'text_maxlength_a8_74p{s}mm.txt' for s in ('50', '58', '60', '66'))


def boundary_structural(paths):
    """Fixed windows only; filenames/order never select structures or fields."""
    import analyze_text_maximum_length_numeric as numeric
    reference = research.read_capture(research.TEXT / FIXTURES[0])
    reference_slots = research.slots(reference) if reference['selected'] else []
    rows = {}
    for path in paths:
        data = research.read_capture(path)
        run = data['selected']
        slots = research.slots(data) if run else []
        aligned = bool(run and len(data['paragraphs']) == 1 and len(slots) == 9 and
                       run['start'] == reference['selected']['start'] and
                       [n.header.class_name for n in data['nodes']] ==
                       [n.header.class_name for n in reference['nodes']] and
                       [s[:8] for s in slots] == [s[:8] for s in reference_slots])
        f4 = {name: [s[lo:hi].hex() for s in slots]
              for name, (lo, hi) in F4.items() if name in ('plus24', 'plus38')}
        invariant = aligned and all(
            f4[name] == [s[F4[name][0]:F4[name][1]].hex() for s in reference_slots] for name in f4)
        row = dict(file_sha256=data['file_sha256'], runtime=data['runtime'],
                   alignment='aligned' if aligned else 'unresolved', run=run,
                   f4=f4, f4_unchanged=invariant)
        if aligned and invariant:
            payload = data['paragraphs'][run['paragraph_index']].payload
            row['windows'] = {name: dict(relative_range=[lo, hi], **numeric.raw_numeric(payload[lo:hi]))
                              for name, (lo, hi) in numeric.WINDOWS.items()}
            row['extent'] = numeric.czone_extent(data)
            a, b = row['windows']['scalar_a'], row['windows']['scalar_b']
            row['duplicate_byte_identity'] = a['raw_hex'] == b['raw_hex']
            row['duplicate_numeric_identity'] = a['f64le']['value'] == b['f64le']['value']
        rows[data['file_sha256']] = row
    if len(rows) != 5:
        raise ValueError('five distinct captures required')
    return dict(reference_sha256=reference['file_sha256'],
                natural_extent=numeric.czone_extent(reference), rows=rows)


def boundary_hypotheses(length, natural):
    ratio = length / natural
    return dict(H1=ratio, H2=ratio-0.001, H3=min(1.0, ratio), H4=min(1.0, ratio-0.001))


def boundary_oracle(frozen, enabled):
    """Labels and hypothesis interpretation are strictly downstream of frozen bytes."""
    import analyze_text_maximum_length_numeric as numeric
    from decimal import Decimal
    raw = json.loads(frozen)
    result = dict(enabled=enabled, cases={}, boundary_model_status='unresolved',
                  compression_formula_status='unresolved')
    if not enabled:
        return result
    n = raw['natural_extent']['extent_mm']['value']
    for name in BOUNDARY_FIXTURES:
        digest = hashlib.sha256((research.TEXT / name).read_bytes()).hexdigest()
        row = raw['rows'].get(digest)
        if row is None or 'windows' not in row:
            continue
        meta = load_intent(name)
        if meta['property'] != 'maximum_length' or meta['changed_scope'] != 'text_object':
            raise ValueError('wrong boundary intent scope')
        length = float(meta['changed_value_mm'])
        observed = row['windows']['scalar_a']['f64le']['value']
        values = boundary_hypotheses(length, n)
        result['cases'][name] = dict(
            file_sha256=digest, labels=meta, requested_mm=length,
            observed_scalar=observed, scalar_raw=row['windows']['scalar_a']['raw_hex'],
            extent_mm=row['extent']['extent_mm']['value'],
            relation_to_n='below' if length < n else 'above' if length > n else 'equal',
            relation_to_crossover='below' if length < 1.001*n else 'above' if length > 1.001*n else 'equal',
            hypotheses={h: numeric.residual(p, observed) for h, p in values.items()},
            requested_setting=numeric.residual(float(Decimal(str(length))/1000),
                                               row['windows']['object_setting']['f64le']['value']),
            requested_setting_binary64_division=numeric.residual(
                length/1000, row['windows']['object_setting']['f64le']['value']),
            extent_vs_requested=numeric.residual(length, row['extent']['extent_mm']['value']),
            extent_vs_natural=numeric.residual(n, row['extent']['extent_mm']['value']),
            ui_compression='not_recorded')
    cases = result['cases']
    by_length = {r['requested_mm']: r for r in cases.values()}
    if set(by_length) == {74.50, 74.58, 74.60, 74.66}:
        def close(row):
            distance = row['hypotheses']['H2']['ulp_distance']
            return distance is not None and distance <= 4
        continuous = all(close(by_length[v]) for v in (74.50, 74.58))
        mid, high = by_length[74.60], by_length[74.66]
        result['below_boundary_continuity'] = ('below_boundary_formula_continuity_supported'
                                              if continuous else 'formula_breaks_near_boundary')
        result['discriminator_74p60'] = ('exactly_one' if mid['observed_scalar'] == 1 else
                                        'h2_below_one' if close(mid) and mid['observed_scalar'] < 1 else 'other')
        result['discriminator_74p66'] = ('exactly_one' if high['observed_scalar'] == 1 else
                                        'h2_above_one' if close(high) and high['observed_scalar'] > 1 else 'other')
        if continuous and close(mid) and mid['observed_scalar'] < 1 and high['observed_scalar'] == 1:
            result.update(boundary_model_status='scalar_crossover_supported',
                          compression_formula_status='clamp_like_transition_observed',
                          transition_status='clamp_like_transition_candidate')
        elif continuous and mid['observed_scalar'] == high['observed_scalar'] == 1:
            result.update(boundary_model_status='natural_threshold_supported',
                          compression_formula_status='formula_breaks_near_boundary')
        else:
            result.update(boundary_model_status='mixed_boundary_behavior' if continuous else 'neither_model_supported',
                          compression_formula_status='below_boundary_formula_extended'
                          if all(close(r) for r in by_length.values()) else 'formula_breaks_near_boundary')
    # Previously frozen broad evidence, never rerun broad differential discovery.
    previous = json.loads((ROOT / 'docs/text_maximum_length_numeric_closeout.json').read_text(encoding='utf-8'))
    structural = previous['structural']
    ordered = []
    for key, length in (('f3', 40), ('f2', 60), ('f1', 100)):
        zone = next(r['bbox'] for r in structural['geometry'][key] if r['class_name'] == 'CZone')
        ordered.append(dict(requested_mm=length,
            observed_scalar=structural['windows'][key]['scalar_a']['f64le']['value'],
            scalar_raw=structural['windows'][key]['scalar_a']['raw_hex'],
            extent_mm=(zone['xmax_m']-zone['xmin_m'])*1000,
            relation_to_n='below' if length < n else 'above',
            relation_to_crossover='below' if length < 1.001*n else 'above', evidence='previous_frozen_report'))
    keys = ('requested_mm', 'observed_scalar', 'scalar_raw', 'extent_mm', 'relation_to_n', 'relation_to_crossover')
    ordered.extend({k: r[k] for k in keys} for r in cases.values())
    result['ordered_positive_scalars'] = sorted(ordered, key=lambda r: r['requested_mm'])
    result['baseline_separate'] = dict(requested_mm=0, scalar=structural['windows']['f0']['scalar_a'],
                                      mode='default_natural_mode_scalar_candidate')
    result['prior_negative_sign_control'] = structural['windows']['f4']
    result['natural_mm'] = n
    result['provisional_crossover_mm'] = 1.001*n
    result['ulp_comparison_threshold'] = 4
    result['duplicate_scalar_status'] = ('duplicate_scalar_storage_observed'
        if len(cases) == 4 and all(raw['rows'][r['file_sha256']]['duplicate_byte_identity']
                                   for r in cases.values()) else 'unresolved_or_contradicted')
    result['object_setting_readiness'] = ('strong_object_setting_candidate_extended_to_boundary_controls'
        if len(cases) == 4 and all(r['requested_setting']['ulp_distance'] == 0 for r in cases.values()) else 'unresolved')
    result['bbox_relationship'] = ('tracks_requested_object_length_within_1_ulp'
        if len(cases) == 4 and all(r['extent_vs_requested']['ulp_distance'] <= 1 for r in cases.values()) else 'other_or_unresolved')
    result['whole_boundary_clamp_comparison'] = {
        h: dict(within_4_ulp_all=len(cases) == 4 and all(r['hypotheses'][h]['ulp_distance'] <= 4 for r in cases.values()),
                contradicted_by=[name for name, r in cases.items() if r['hypotheses'][h]['ulp_distance'] > 4])
        for h in ('H3', 'H4')}
    return result


def build_boundary_report(paths=None, oracle_enabled=True):
    paths = list(paths) if paths is not None else [research.TEXT / n for n in (FIXTURES[0], *BOUNDARY_FIXTURES)]
    if len(paths) != 5:
        raise ValueError('baseline and four boundary captures required')
    frozen = compact(boundary_structural(paths))
    return dict(mode='boundary', structural=json.loads(frozen),
                structural_sha256=hashlib.sha256(frozen.encode()).hexdigest(),
                oracle_summary=boundary_oracle(frozen, oracle_enabled),
                policy=dict(field_discovery='not_performed', full_payload_differential='not_performed',
                    runtime_v2_replacement_acceptance='accepted_candidate_only',
                    constant_fitting='not_performed', compression_scalar_readiness='strong_correlated_numeric_candidate',
                    semantic_formula_readiness='provisional_not_ready', parser_safe=False, typed_width=None,
                    ownership_status='unresolved', matched_chain=None, runtime_change_readiness='not_authorized_in_this_task',
                    rendered_behavior='unresolved'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--no-oracle', action='store_true')
    parser.add_argument('--details', action='store_true')
    parser.add_argument('--boundary', action='store_true')
    parser.add_argument('--fixtures', type=Path, nargs=5)
    args = parser.parse_args()
    try:
        if args.boundary:
            output = compact(build_boundary_report(args.fixtures, not args.no_oracle)) + '\n'
            if len(output.encode()) >= LIMITS['json_bytes' if args.json else 'text_bytes']:
                raise ValueError('boundary output budget exceeded')
            print(output, end='')
        else:
            print(render(build_report(args.fixtures, not args.no_oracle, args.details), args.json), end='')
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()

