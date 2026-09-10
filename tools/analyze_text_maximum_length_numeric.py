"""Fixed-window maximum-length numeric closeout; no field discovery or runtime changes."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_maximum_length as previous  # noqa: E402

FIXTURES = previous.FIXTURES
WINDOWS = {'object_setting': (262, 270), 'scalar_a': (214, 222), 'scalar_b': (286, 294)}
# Carried forward verbatim from the previous negative-only payload range inventory.
# These ranges are inspected, not rediscovered or numerically decoded here.
NEGATIVE_RANGES = ((8, 15), (32, 39), (2162, 2169), (2186, 2193), (2210, 2213), (2218, 2221),
    (2226, 2229), (2234, 2237), (2246, 2249), (2254, 2257), (2262, 2265), (2270, 2273),
    (2282, 2285), (2290, 2293), (2298, 2301), (2306, 2309), (2318, 2321), (2326, 2329),
    (2332, 2333), (2334, 2337), (2340, 2341), (2342, 2345), (2352, 2353), (2354, 2357),
    (2360, 2361), (2362, 2365), (2370, 2373), (2378, 2381), (2390, 2393), (2398, 2401),
    (2406, 2409), (2414, 2417), (2426, 2429), (2434, 2437), (2442, 2445), (2450, 2453),
    (2462, 2465), (2470, 2473), (2478, 2481), (2486, 2489), (2498, 2501), (2506, 2509),
    (2514, 2517), (2522, 2525))
LIMITS = dict(fixtures=5, json_bytes=100000, text_bytes=50000)
POLICY = dict(scope='maximum_length_fixed_window_numeric_closeout_only', field_discovery='not_performed',
              runtime_parser_behavior='not_modified', f4_runtime_change='not_performed',
              oracle_isolation=True, constant_fitting='not_performed', typed_width=None,
              ownership_assignment='not_performed', semantic_formula_readiness='provisional_not_ready')
compact = previous.compact


def numeric(value):
    """JSON number plus explicit round-trip repr/hex, never presentation rounding."""
    return dict(value=value if math.isfinite(value) else None, repr=repr(value), hex=value.hex())


def raw_numeric(raw):
    if len(raw) != 8:
        raise ValueError('fixed f64 window must contain eight bytes')
    return dict(raw_hex=raw.hex(), f64le=numeric(struct.unpack('<d', raw)[0]))


def czone_extent(data):
    zones = [n for n in data['nodes'] if n.header.class_name == 'CZone']
    if len(zones) != 1 or zones[0].bbox is None:
        raise ValueError('unique decoded CZone bbox required')
    node = zones[0]
    # Existing parse_single_node: common object header followed by six f64 bbox components.
    start = data['base'] + node.start_offset + 6 + node.header.name_len
    if start+48 != data['base']+node.payload_offset:
        raise ValueError('CZone bbox provenance disagrees with parser framing')
    xmin_raw, xmax_raw = data['raw'][start:start+8], data['raw'][start+24:start+32]
    xmin, xmax = node.bbox.xmin_m, node.bbox.xmax_m
    if (struct.unpack('<d', xmin_raw)[0], struct.unpack('<d', xmax_raw)[0]) != (xmin, xmax):
        raise ValueError('decoded coordinates disagree with raw provenance')
    extent_m = xmax-xmin
    return dict(xmin_m=raw_numeric(xmin_raw), xmax_m=raw_numeric(xmax_raw),
                extent_m=numeric(extent_m), extent_mm=numeric(extent_m*1000),
                exact_difference_of_decoded_binary64_m=str(Fraction(xmax)-Fraction(xmin)),
                calculation='N = (decoded xmax_m - decoded xmin_m) * 1000 in Python binary64',
                precision='binary64; repr is shortest round-trip-safe decimal; hex is exact binary float',
                provenance=dict(class_name='CZone', bbox_absolute_start=start,
                    xmin_absolute_range=[start, start+8], xmax_absolute_range=[start+24, start+32],
                    parser='parsers/binary/node_parser.py:parse_single_node -> parsers/common.py:read_bbox'))


def structural_phase(paths):
    if len(paths) != 5 or len({p.name for p in paths}) != 5:
        raise ValueError('exactly five unique fixture paths required; reference first')
    loaded = [previous.research.read_capture(path) for path in paths]
    if any(not data['selected'] or data['selected']['count'] != 9 for data in loaded):
        raise ValueError('previous nine-slot structural alignment unresolved')
    slot_rows = [previous.research.slots(d) for d in loaded]
    if any([r[:8] for r in rows] != [r[:8] for r in slot_rows[0]] for rows in slot_rows):
        raise ValueError('previous raw slot alignment disagrees')
    windows, geometry = {}, {}
    payloads = [d['paragraphs'][d['selected']['paragraph_index']].payload for d in loaded]
    for i, (data, payload) in enumerate(zip(loaded, payloads, strict=True)):
        windows[f'f{i}'] = {key: dict(relative_range=[lo, hi], **raw_numeric(payload[lo:hi]))
                            for key, (lo, hi) in WINDOWS.items()}
        geometry[f'f{i}'] = [dict(class_name=n.header.class_name, bbox=asdict(n.bbox) if n.bbox else None)
                             for n in data['nodes']]
    return dict(fixture_inventory=[dict(id=f'f{i}', fixture=p.name, file_sha256=d['file_sha256'],
                    raw_sha256=hashlib.sha256(d['raw']).hexdigest()) for i, (p, d) in enumerate(zip(paths, loaded))],
                windows=windows, natural_extent=czone_extent(loaded[0]), geometry=geometry,
                duplicated_scalars=dict(byte_identical=all(r['scalar_a']['raw_hex'] == r['scalar_b']['raw_hex']
                                                          for r in windows.values()),
                    numeric_identical=all(r['scalar_a']['f64le'] == r['scalar_b']['f64le'] for r in windows.values())),
                runtime_candidate_summary={f'f{i}': d['runtime'] for i, d in enumerate(loaded)},
                slot_invariance={f'f{i}': dict(all_204_bytes_unchanged=rows == slot_rows[0],
                    terminal_204_bytes_unchanged=rows[-1] == slot_rows[0][-1],
                    width_values=[raw_numeric(r[20:28]) for r in rows],
                    spacing_values=[raw_numeric(r[64:72]) for r in rows]) for i, rows in enumerate(slot_rows)},
                f4_invariance=previous.audit(loaded, previous.F4),
                previous_negative_ranges=dict(coordinate_domain='CParagraphe_payload_relative',
                    rows=[dict(relative_range=[lo, hi], raw=[p[lo:hi].hex() for p in payloads])
                          for lo, hi in NEGATIVE_RANGES]))


def ulp_distance(a, b):
    if not (math.isfinite(a) and math.isfinite(b)):
        return None
    if a == b:
        return 0
    def ordered(value):
        bits = struct.unpack('<Q', struct.pack('<d', value))[0]
        return (~bits & ((1 << 64)-1)) if bits >> 63 else bits | (1 << 63)
    return abs(ordered(a)-ordered(b))


def residual(predicted, observed):
    absolute = abs(predicted-observed)
    return dict(predicted=numeric(predicted), observed=numeric(observed), absolute_residual=absolute,
                relative_residual=absolute/abs(observed) if observed else (0.0 if absolute == 0 else None),
                relative_residual_denominator='abs(observed)', ulp_distance=ulp_distance(predicted, observed))


def hypotheses(length_mm, natural_mm):
    """Only user-specified expressions; 0.001 is fixed, never fitted."""
    magnitude = abs(length_mm)
    return {'H1': magnitude/natural_mm, 'H2': magnitude/natural_mm-0.001,
            'H3': (magnitude-0.001*natural_mm)/natural_mm}


def oracle_phase(frozen, enabled):
    raw = json.loads(frozen)
    result = dict(enabled=enabled, labels={}, warnings=[], below_natural={}, clamps={},
                  below_natural_formula_status='unresolved', above_natural_clamp_status='unresolved',
                  zero_default_mode_status='unresolved', positive_negative_magnitude_status='unresolved',
                  semantic_formula_readiness='provisional_not_ready')
    if not enabled:
        return result
    for row in raw['fixture_inventory'][1:]:
        meta = previous.load_intent(row['fixture'])
        if meta['property'] != 'maximum_length' or meta['changed_scope'] != 'text_object':
            raise ValueError('invalid maximum-length intent')
        result['labels'][row['id']] = {key: meta[key] for key in (
            'changed_value_mm', 'baseline_value_mm', 'baseline_natural_length_mm',
            'expected_ui_relationship', 'observed_program_behavior')}
    requested = {'f0': 0.0, **{key: m['changed_value_mm'] for key, m in result['labels'].items()}}
    n = raw['natural_extent']['extent_mm']['value']
    if n is None or n <= 0:
        raise ValueError('positive finite serialized natural extent required')
    for key, length in requested.items():
        s = raw['windows'][key]['scalar_a']['f64le']['value']
        if s is None:
            result['warnings'].append(key+': non-finite scalar')
            continue
        values = hypotheses(length, n)
        if 0 < abs(length) < n:
            result['below_natural'][key] = {h: residual(v, s) for h, v in values.items()}
        result['clamps'][key] = {name: residual(predicted, s) for name, predicted in (
            ('min_1_L_over_N', min(1.0, values['H1'])), ('min_1_L_over_N_minus_001', min(1.0, values['H2'])))}
    ids = {length: key for key, length in requested.items()}
    designed = (len(ids) == 5 and set(ids) == {0, 100, 60, 40, -60} and
                all(m['baseline_value_mm'] == 0 for m in result['labels'].values()))
    if designed:
        below = result['below_natural']
        close = all(ids[v] in below and below[ids[v]]['H2']['ulp_distance'] is not None and
                    below[ids[v]]['H2']['ulp_distance'] <= 4 for v in (60, 40, -60))
        result['below_natural_formula_status'] = ('h2_hypothesis_supported_within_4_ulp_not_semantic_formula'
                                                    if close else 'explicit_hypotheses_not_supported')
        result['ulp_support_threshold'] = 4
        result['above_natural_diagnostics'] = {h: residual(v, raw['windows'][ids[100]]['scalar_a']['f64le']['value'])
                                              for h, v in hypotheses(100, n).items()}
        if (100 > n and raw['windows'][ids[100]]['scalar_a']['f64le']['value'] == 1.0):
            result['above_natural_clamp_status'] = 'no_compression_clamp_candidate'
        result['zero_default_mode_status'] = 'default_natural_mode_scalar_candidate'
        result['zero_mode_note'] = ('0 mm is the UI sentinel/default natural mode; binary sentinel semantics '
                                   'remain provisional; neither constrained-length expression explains its scalar')
        pos, neg = raw['windows'][ids[60]], raw['windows'][ids[-60]]
        identical = all(pos[k]['raw_hex'] == neg[k]['raw_hex'] for k in ('scalar_a', 'scalar_b'))
        result['positive_negative_magnitude_status'] = ('compression_magnitude_uses_absolute_length_candidate'
                                                        if identical else 'raw_identity_not_supported')
        result['positive_negative'] = dict(ids=[ids[60], ids[-60]],
            object_setting_raw=[pos['object_setting']['raw_hex'], neg['object_setting']['raw_hex']],
            scalar_byte_identical=identical,
            scalar_numeric_equal=pos['scalar_a']['f64le']['value'] == neg['scalar_a']['f64le']['value'],
            geometry_reference='structural.geometry', negative_range_reference='structural.previous_negative_ranges')
    result['clamp_whole_set'] = {name: dict(
        exact_matches_all=len(result['clamps']) == 5 and all(r[name]['absolute_residual'] == 0
                                                           for r in result['clamps'].values()),
        nonzero_residual_fixtures=[key for key, r in result['clamps'].items() if r[name]['absolute_residual'] != 0])
        for name in ('min_1_L_over_N', 'min_1_L_over_N_minus_001')}
    return result


def build_report(paths=None, oracle_enabled=True):
    paths = [previous.research.TEXT/n for n in FIXTURES] if paths is None else list(paths)
    frozen = compact(structural_phase(paths))
    raw = json.loads(frozen)
    oracle = oracle_phase(frozen, oracle_enabled)
    identity = raw['duplicated_scalars']['byte_identical']
    return dict(mode='fixed_window_numeric_closeout', policy=POLICY, limits=LIMITS, structural=raw,
        structural_sha256=hashlib.sha256(frozen.encode()).hexdigest(), oracle_summary=oracle,
        answers=dict(exact_object_setting_raw_values={k: v['object_setting'] for k, v in raw['windows'].items()},
            exact_scalar_a_raw_values={k: v['scalar_a'] for k, v in raw['windows'].items()},
            exact_scalar_b_raw_values={k: v['scalar_b'] for k, v in raw['windows'].items()},
            duplicate_scalar_byte_identity=identity,
            duplicate_scalar_status='duplicate_scalar_storage_observed' if identity else 'unresolved',
            exact_natural_extent=raw['natural_extent'],
            h1_residuals={k: v['H1'] for k, v in oracle['below_natural'].items()},
            h2_residuals={k: v['H2'] for k, v in oracle['below_natural'].items()},
            h3_residuals={k: v['H3'] for k, v in oracle['below_natural'].items()},
            below_natural_formula_status=oracle['below_natural_formula_status'],
            above_natural_clamp_status=oracle['above_natural_clamp_status'],
            zero_default_mode_status=oracle['zero_default_mode_status'],
            positive_negative_magnitude_status=oracle['positive_negative_magnitude_status'],
            compression_scalar_readiness='strong_correlated_numeric_candidate' if identity and
                oracle['below_natural_formula_status'].startswith('h2_hypothesis_supported') else 'unresolved',
            semantic_formula_readiness='provisional_not_ready', runtime_change_readiness='not_authorized_in_this_task',
            f4_status='not_falsified_by_current_maxlength_controls',
            parser_safe=False, typed_width=None, ownership_status='unresolved'))


def render(report, json_output=False):
    output = compact(report)+'\n' if json_output else 'Maximum-length numeric closeout\n'+compact(report)+'\n'
    if len(output.encode()) >= LIMITS['json_bytes' if json_output else 'text_bytes']:
        raise ValueError('output budget exceeded')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--no-oracle', action='store_true')
    parser.add_argument('--fixtures', type=Path, nargs=5)
    args = parser.parse_args()
    try:
        print(render(build_report(args.fixtures, not args.no_oracle), args.json), end='')
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
