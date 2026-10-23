"""Opt-in saved-file Archive boundary diagnostics. No production Parser registration."""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_SHADOW = None

def load_shadow():
    """Load the original 006 Reader only for an explicitly requested diagnostic."""
    global _SHADOW
    if _SHADOW is None:
        path = ROOT / 'research/archive-parser-crosswalk-006/shadow_reader.py'
        spec = importlib.util.spec_from_file_location('boundary007_original006', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _SHADOW = module
    return _SHADOW

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fingerprint(value) -> str:
    # In-memory serialization only, never unpickle input. Memoization preserves
    # shared diagnostic subtrees without expanding them exponentially.
    import pickle
    return sha(pickle.dumps(value, protocol=5))
def event(code, level, basis, **fields):
    return {'code': code, 'confidence': level, 'basis': basis, **fields}

def nodes(tree):
    yield tree
    for child in tree.get('children', []):
        yield from nodes(child)

def normalize_codec(decoded, parser, data, shadow_module):
    envelope = shadow_module.Type3ChainParser()._read_top_level_header(data)[2]
    rows = []
    for i, chain in enumerate(getattr(decoded, 'object_chains', [])):
        style = chain.style
        stream = chain.source_stream_offset
        offset = getattr(style, 'property_extend_payload_offset', None)
        length = getattr(style, 'property_extend_payload_length', None)
        raw = chain.raw_contour_bytes
        rows.append({'chain_index': i, 'contour_range': [envelope + stream, envelope + stream + len(raw)] if stream is not None and raw else None,
            'raw_contour': raw, 'count': len(chain.contour_records),
            'property_candidate_range': [envelope + offset, envelope + offset + length] if offset is not None and length is not None else None,
            'selected_color_raw': style.line_color_selected_raw,
            'selected_color_name': style.line_color_name,
            'codec_confidence_original': style.line_color_confidence,
            'codec_color_source': style.line_color_source})
    return {'parser_name': parser, 'decoder_object_type': decoded.object_type,
        'text_content': getattr(decoded, 'text_content', None),
        'declared_count_candidate': getattr(decoded, 'declared_object_count', None),
        'group_candidate': getattr(decoded, 'is_grouped', None),
        'envelope_payload_start': envelope,
        'coordinate_system': 'Absolute byte offsets in input; half-open ranges. Node-local offsets are not used as absolute positions.',
        'confidence': 'HEURISTIC', 'chains': rows}

def compare_views(data, codec, shadow):
    """Compare observations, not a second parser. Test seams accept synthetic observations."""
    events = []
    rows = []
    if shadow['status'] != 'CONDITIONAL_MATCH':
        events.append(event('UNSUPPORTED', 'UNSUPPORTED', shadow.get('reason', 'research Reader did not complete'), stop_cursor=shadow['stop_cursor']))
        return {'overall_status': 'UNSUPPORTED', 'observations': events, 'contours': rows}
    used = set()
    for node in nodes(shadow['tree']):
        if node['class'] != 'CContour':
            continue
        native_range = node['point_records']['span']
        raw = data[native_range[0]:native_range[1]]
        candidates = [c for c in codec['chains'] if c['raw_contour'] == raw]
        row = {'class_name': node['class'], 'archive_class_id_conditional': node['class_id'],
            'archive_object_id_scope_only': node['object_id_archive_scope_only'],
            'class_descriptor_schema': next((e['schema'] for e in shadow['events'] if e['kind']=='new_class' and e['class_id']==node['class_id']), None),
            'class_record_event': next((e for e in shadow['events'] if e.get('span')==node['tag_span']), None),
            'native_contour_range': native_range, 'native_count': node['point_records']['count'],
            'native_record_width': node['point_records']['record_width'],
            'width_contract': {'confidence': 'VERIFIED', 'basis': '002: CPtCtr4D 32+4-byte writes, supported family only'},
            'boundary_confidence': 'CONDITIONAL', 'matching_chain_indices': [c['chain_index'] for c in candidates],
            'ownership': 'UNKNOWN', 'observations': []}
        if len(candidates) > 1:
            row['observations'].append(event('AMBIGUOUS', 'UNKNOWN', 'Identical contour bytes correspond to multiple Codec chains; no member assigned'))
            used.update(c['chain_index'] for c in candidates)
        elif not candidates:
            row['observations'].append(event('BOUNDARY_MISMATCH', 'CONDITIONAL', 'No Codec contour has the sequentially read bytes'))
        else:
            chain = candidates[0]
            used.add(chain['chain_index'])
            row.update({'codec_chain_index': chain['chain_index'], 'codec_contour_range': chain['contour_range'],
                        'codec_count': chain['count'], 'codec_property_candidate_range': chain['property_candidate_range'],
                        'codec_selected_color_raw': chain['selected_color_raw'],
                        'codec_selected_color_name': chain['selected_color_name'],
                        'codec_confidence_original': chain['codec_confidence_original'],
                        'codec_color_confidence': 'HEURISTIC'})
            match = chain['contour_range'] == native_range and chain['count'] == row['native_count']
            row['observations'].append(event('BOUNDARY_MATCH' if match else 'BOUNDARY_MISMATCH', 'CONDITIONAL', 'Compare absolute start/end and record count, independently of colors'))
            prop = node['children'][-1]
            body = [prop['body_start'], prop['body_end']]
            row['native_property_body_range'] = body
            window = chain['property_candidate_range']
            if window and window != body and window[0] <= body[0] and window[1] >= body[1]:
                row['observations'].append(event('CANDIDATE_WINDOW_WIDER_THAN_NATIVE_BODY', 'CONDITIONAL', 'Codec heuristic window contains more than the sequential Property body; not a Parser error or corruption'))
            suffix = next((c for c in shadow['colors'] if c['suffix_span'][0] == node['body_end']), None)
            row['ccourbe_suffix_range'] = suffix['suffix_span'] if suffix else None
            row['color_fields'] = []
            if suffix:
                for key in ('b8_range', 'c4_range'):
                    a,b = suffix[key]
                    value = int.from_bytes(data[a:b], 'little')
                    row['color_fields'].append({'range': [a,b], 'value_u32': value, 'bytes_hex': data[a:b].hex(),
                        'equals_codec_selected_color': value == chain['selected_color_raw'],
                        'outside_native_property_body': b <= body[0] or a >= body[1],
                        'record_scope': 'CCourbe suffix under supported sequential traversal; member ownership UNKNOWN',
                        'confidence': 'CONDITIONAL'})
            rows.append(row)
            continue
        rows.append(row)
    for i, left in enumerate(codec['chains']):
        a = left['property_candidate_range']
        if a is None:
            continue
        for right in codec['chains'][i+1:]:
            b = right['property_candidate_range']
            if b is not None and max(a[0],b[0]) < min(a[1],b[1]):
                events.append(event('SHARED_PROPERTY_CANDIDATE_WINDOW', 'HEURISTIC', 'Distinct chains share or overlap a Property search window; this does not prove member ownership',
                    codec_chain_indices=[left['chain_index'],right['chain_index']], overlap_range=[max(a[0],b[0]),min(a[1],b[1])]))
    unmatched = [c['chain_index'] for c in codec['chains'] if c['raw_contour'] and c['chain_index'] not in used]
    if unmatched:
        events.append(event('BOUNDARY_MISMATCH','CONDITIONAL','Codec contours were not matched to sequential observations',codec_chain_indices=unmatched))
    codes = {e['code'] for e in events} | {e['code'] for r in rows for e in r['observations']}
    overall = 'BOUNDARY_MISMATCH' if 'BOUNDARY_MISMATCH' in codes else 'AMBIGUOUS' if 'AMBIGUOUS' in codes else 'CONDITIONAL_COMPARISON_COMPLETE'
    return {'overall_status': overall, 'observations': events, 'contours': rows}

def diagnose_bytes(data: bytes, *, research_shadow: bool = False):
    if not research_shadow:
        raise ValueError('Explicit research_shadow=True is required; Decoder defaults are unchanged')
    s = load_shadow()
    # Admission is diagnostic-only. A malformed known-prefix input can make the
    # legacy heuristic loop fail to advance; never force that path to run here.
    shadow_error = None
    try:
        shadow = s.shadow(data)
    except Exception as error:
        shadow_error = error
    if shadow_error is None and shadow['status'] != 'CONDITIONAL_MATCH' and data[:6].hex() == shadow['prefix_condition']:
        return {'source_sha256':sha(data),'input_length':len(data),'research_shadow_selected':True,
            'overall_status':'UNSUPPORTED','observations':[event('UNSUPPORTED','UNSUPPORTED',shadow['reason'],stop_cursor=shadow['stop_cursor'])],
            'contours':[],'codec':None,'decoder_observation_status':'NOT_RUN_UNSUPPORTED_STRUCTURE',
            'decoder_object_unchanged':None,'decoder_note':'No Decoder result was produced or substituted; default Decoder implementation is unchanged',
            'archive_prefix':{'range':[0,6],'hex':data[:6].hex(),'confidence':'CONDITIONAL'},
            'shadow_stop_cursor':shadow['stop_cursor'],'shadow_stop_reason':shadow['reason'],
            'unknown_ranges':shadow['unknown_ranges'],'uninterpreted_tail_start':None,
            'descriptor_and_reference_events':[],
            'partial_shadow_events_diagnostic_only':shadow.get('partial_events_diagnostic_only',[]),
            'archive_valid_length':'UNKNOWN','ownership':'UNKNOWN','change_allowed':False}
    # For admitted inputs the independent Decoder sees the original full bytes,
    # not a slice or cursor selected by the research Reader.
    decoded, parser = s.a.Decoder().decode_bytes_with_parser(data)
    original = fingerprint(decoded)
    codec = normalize_codec(decoded, parser, data, s)
    try:
        if shadow_error is not None:
            raise shadow_error
    except Exception as error:
        # A research failure is diagnostic only; do not replace or retry Decoder results.
        return {'source_sha256':sha(data),'overall_status':'DIAGNOSTIC_ERROR','reason':type(error).__name__+': '+str(error),
            'codec':{k:v for k,v in codec.items() if k!='chains'},'decoder_fingerprint':original,
            'decoder_object_unchanged':fingerprint(decoded)==original,'change_allowed':False,'ownership':'UNKNOWN'}
    compared = compare_views(data, codec, shadow)
    descriptors = [{**e, 'schema_confidence':'CONDITIONAL', 'class_id_scope':'Archive-local conditional registration, never persistent identity'}
                   for e in shadow.get('events',[]) if e['kind'] in ('new_class','class_reference')]
    # No raw decoded model is returned or modified by the diagnostic.
    public_codec = {**codec, 'chains':[{k:v for k,v in c.items() if k!='raw_contour'} for c in codec['chains']]}
    return {'source_sha256':sha(data),'input_length':len(data),'research_shadow_selected':True,
        **compared,'codec':public_codec,'archive_prefix':{'range':[0,min(6,len(data))],'hex':data[:6].hex(),'confidence':'CONDITIONAL','required_hex':shadow['prefix_condition']},
        'descriptor_and_reference_events':descriptors,
        'class_id_note':'Schema and Archive class ID are separate. Existing ObjectHeader.class_id API is not changed.',
        'shadow_consumed_range':shadow.get('consumed_range'), 'shadow_stop_cursor':shadow['stop_cursor'],
        'shadow_stop_reason':shadow.get('reason'), 'unknown_ranges':shadow['unknown_ranges'],
        'uninterpreted_tail_start':shadow['stop_cursor'] if shadow['status']=='CONDITIONAL_MATCH' else None,
        'archive_valid_length':'UNKNOWN','ownership':'UNKNOWN','change_allowed':False,
        'decoder_observation_status':'COMPLETED','decoder_fingerprint':original,'decoder_object_unchanged':fingerprint(decoded)==original,
        'assumptions':['Reviewed prefix and fresh unseeded class map at byte6 are conditional',
                       'Additional direct Serialize list zero contribution applies only to reviewed CZone/CCourbe types',
                       'Unsupported optional Property/reference branches are not resynchronized'],
        'partial_shadow_events_diagnostic_only':shadow.get('partial_events_diagnostic_only',[])}

def main(argv=None):
    parser = argparse.ArgumentParser(description='Saved TypeEditZone binary boundary diagnostics; never reads Windows Clipboard')
    parser.add_argument('--input',type=Path,required=True,help='Existing saved TypeEditZone binary (not hex text)')
    parser.add_argument('--research-shadow',action='store_true',required=True,help='Explicitly enable original research Reader 006')
    parser.add_argument('--output',type=Path,help='New JSON file; existing files are never overwritten; default stdout')
    args=parser.parse_args(argv)
    if args.output and args.output.exists():
        parser.error('output already exists; choose a new path')
    try:
        data=args.input.read_bytes()
        result=diagnose_bytes(data,research_shadow=args.research_shadow)
        result['source_path']=str(args.input.resolve())
        text=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        if args.output:
            with args.output.open('x',encoding='utf-8') as f:f.write(text)
        else:
            print(text,end='')
    except (OSError,ValueError,TypeError) as e:
        parser.exit(2, f'Diagnostic failed (Decoder unchanged): {e}\n')
    return 0  # Successful diagnostic may report UNSUPPORTED; inspect overall_status.

if __name__=='__main__':
    raise SystemExit(main())
