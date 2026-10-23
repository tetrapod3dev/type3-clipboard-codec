"""Saved TypeEditZone inventory candidates. Never reads the system Clipboard.
All decoding is isolated in an owned Python child with a timeout. No write API.
"""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 16 * 1024 * 1024  # Admission bound, not an Archive-format length.


def sha(data):
    return hashlib.sha256(data).hexdigest()


def field(value, confidence, basis):
    return {'value': value, 'confidence': confidence, 'basis': basis}


def clean(value):
    if dataclasses.is_dataclass(value):
        return clean(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {'value': None, 'confidence': 'UNKNOWN', 'reason': 'non-finite decoded value'}
    if isinstance(value, bytes):
        return {'length': len(value), 'sha256': sha(value)}
    return value


def load_diagnostic():
    path = ROOT / 'research/archive-boundary-diagnostic-007/boundary_diagnostic.py'
    spec = importlib.util.spec_from_file_location('inventory_original_007', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def empty_report(data, status, reason):
    return {'status': status, 'source_sha256': sha(data), 'input_length': len(data),
            'complete_inventory': False, 'top_level_selection_count': field(None, 'UNKNOWN', 'No proven selected-object boundary contract'),
            'candidate_count': 0, 'candidates': [], 'group_hierarchy': field(None, 'UNKNOWN', 'Archive edges are not UI ownership'),
            'unknowns': [reason], 'change_allowed': False, 'persistent_object_ids': 'UNSUPPORTED',
            'archive_valid_length': 'UNKNOWN'}


def build_candidates(decoded, parser_name, data, shadow, diagnostic):
    """Normalize the existing model; this function does not discover new objects."""
    s = diagnostic.load_shadow()
    envelope = s.Type3ChainParser()._read_top_level_header(data)[2]
    rows = []
    chains = getattr(decoded, 'object_chains', [])
    for index, chain in enumerate(chains):
        raw = chain.raw_contour_bytes
        start = chain.source_stream_offset
        span = [envelope + start, envelope + start + len(raw)] if start is not None and raw else None
        if span and not (0 <= span[0] <= span[1] <= len(data)):
            span = None
        row = {'display_index': index, 'unit': 'DECODER_CHAIN_CANDIDATE_NOT_SELECTED_OBJECT',
               'top_level_selection': field(None, 'UNKNOWN', 'Chain boundaries do not establish top-level objects'),
               'parent_group': field(None, 'UNKNOWN', 'No proven member ownership'),
               'color_member_association': field(None, 'UNKNOWN', 'Candidate color is not a proven member attribute'),
               'kind': field(chain.shape_type or 'unknown', 'HEURISTIC', chain.shape_classification_reason or 'Existing chain classifier'),
               'original_classifier_confidence': chain.shape_classification_confidence,
               'contour_range': field(span, 'HEURISTIC' if span else 'UNKNOWN', 'Existing envelope plus stream offset; contour records only, not object extent'),
               'object_byte_range': field(None, 'UNKNOWN', 'Entire selected-object Serialize extent unresolved'),
               'contour_sha256': sha(raw) if raw else None,
               'record_count': len(chain.contour_records),
               'records': field(clean(chain.contour_records), 'HEURISTIC', 'Existing Decoder records; tag/role semantics provisional'),
               'bbox': field(clean(chain.bbox), 'HEURISTIC', 'Existing Decoder bbox; not independently reconstructed'),
               'coordinate_unit': field('m; multiply by 1000 for mm', 'CONDITIONAL', 'Supported captured geometry family, not all object types'),
               'text': field(chain.text_candidate, 'HEURISTIC' if chain.text_candidate else 'UNKNOWN', 'Chain-associated text candidate; ownership unresolved'),
               'color': field({'raw': chain.style.line_color_selected_raw, 'name': chain.style.line_color_name,
                               'hex': chain.style.line_color_hex, 'original_confidence': chain.style.line_color_confidence,
                               'source': chain.style.line_color_source}, 'HEURISTIC', 'Existing color ranking; shared Property windows may misassign members'),
               'layer': field(None, 'UNKNOWN', 'No proven layer ownership'),
               'font': field(None, 'UNKNOWN', 'Global font candidate not assigned to chains'),
               'evidence': ['Existing Decoder ' + parser_name], 'ambiguities': []}
        rows.append(row)
    text = getattr(decoded, 'text_content', None)
    # Global text is kept separate: never copied into every contour or counted as another object.
    payload_text = field({'text_content': text, 'font_name': getattr(decoded, 'font_name', None),
                          'source_text_candidate': getattr(decoded, 'source_text_candidate', None),
                          'display_text_candidate': getattr(decoded, 'display_text_candidate', None)},
                         'HEURISTIC' if text else 'UNKNOWN', 'Payload-level Decoder output; not an independent text-object enumeration')
    if not chains and text:
        rows.append({'display_index': 0, 'unit': 'PAYLOAD_TEXT_CANDIDATE_NOT_SELECTED_OBJECT',
                     'kind': field('text_candidate', 'HEURISTIC', 'Existing Decoder text'),
                     'top_level_selection': field(None, 'UNKNOWN', 'Payload may include multiple text objects'),
                     'parent_group': field(None, 'UNKNOWN', 'Unresolved'),
                     'object_byte_range': field(None, 'UNKNOWN', 'Unresolved'), 'text': payload_text,
                     'ambiguities': []})
    compared = None
    if shadow.get('status') == 'CONDITIONAL_MATCH':
        normalized = diagnostic.normalize_codec(decoded, parser_name, data, s)
        compared = diagnostic.compare_views(data, normalized, shadow)
        for event in compared['observations']:
            if event['code'] == 'SHARED_PROPERTY_CANDIDATE_WINDOW':
                for index in event['codec_chain_indices']:
                    rows[index]['ambiguities'].append('SHARED_PROPERTY_CANDIDATE_WINDOW; color ownership UNKNOWN')
        for observed in compared['contours']:
            indices = observed['matching_chain_indices']
            for index in indices:
                rows[index]['archive_boundary_observation'] = clean(observed)
                if len(indices) != 1:
                    rows[index]['ambiguities'].append('Multiple chains match identical sequential contour bytes')
    # Distinct occurrences survive even if their shapes and raw bytes are identical.
    for row in rows:
        raw_sha = row.get('contour_sha256')
        if raw_sha and sum(c.get('contour_sha256') == raw_sha for c in rows) > 1:
            row['ambiguities'].append('DUPLICATE_CONTOUR_CANDIDATES; no deduplication or ownership assignment')
    return rows, payload_text, compared


def _decode_worker(data):
    d = load_diagnostic()
    s = d.load_shadow()
    shadow = s.shadow(data)
    if shadow['status'] != 'CONDITIONAL_MATCH' and data[:6].hex() == shadow['prefix_condition']:
        report = empty_report(data, 'UNSUPPORTED', '007 policy: known prefix with unsupported/truncated structure; Decoder not run')
        report.update({'decoder_status': 'NOT_RUN_UNSUPPORTED_STRUCTURE', 'stop_cursor': shadow['stop_cursor'],
                       'stop_reason': shadow.get('reason'), 'unknown_ranges': shadow['unknown_ranges']})
        return report
    decoded, parser = s.a.Decoder().decode_bytes_with_parser(data)
    fingerprint = d.fingerprint(decoded)
    rows, payload_text, compared = build_candidates(decoded, parser, data, shadow, d)
    report = empty_report(data, 'PARTIAL' if rows else 'UNSUPPORTED', 'Top-level selection count, group ownership and full valid Archive length are unresolved')
    report.update({'decoder_status': 'COMPLETED', 'parser_name': parser, 'decoder_object_type': decoded.object_type,
                   'decoder_fingerprint': fingerprint, 'decoder_model_unchanged': d.fingerprint(decoded) == fingerprint,
                   'candidate_count': len(rows), 'decoder_chain_count': len(getattr(decoded, 'object_chains', [])),
                   'candidates': rows, 'payload_text': payload_text,
                   'declared_count_candidate': field(getattr(decoded, 'declared_object_count', None), 'HEURISTIC', 'Existing header candidate, not a trusted selection count'),
                   'decoder_group_candidate': field(getattr(decoded, 'is_grouped', None), 'HEURISTIC', 'Decoder group flag is not proof of group absence or ownership'),
                   'archive_structure': {'status': shadow['status'], 'confidence': 'CONDITIONAL' if shadow['status']=='CONDITIONAL_MATCH' else 'UNSUPPORTED',
                      'consumed_range': shadow.get('consumed_range'), 'stop_cursor': shadow['stop_cursor'], 'reason': shadow.get('reason'),
                      'descriptor_events': shadow.get('events', []),
                      'serialization_tree_not_group_hierarchy': shadow.get('tree'),
                      'ownership': 'UNKNOWN', 'unknown_ranges': shadow['unknown_ranges']},
                   'boundary_comparison': compared,
                   'warnings': list(getattr(decoded, 'warnings', [])),
                   'input_contract': 'Saved TypeEditZone bytes only; TypeEditZoneVersion not interpreted; no Clipboard access'})
    return clean(report)


def analyze_bytes(data, *, timeout=8.0):
    """Bytes input seam for a future separate capture adapter; never accesses Clipboard."""
    if not isinstance(data, bytes):
        raise TypeError('bytes required')
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('positive finite timeout required')
    if len(data) > MAX_BYTES:
        return empty_report(data, 'UNSUPPORTED', 'Input exceeds diagnostic admission limit of 16 MiB')
    command = [sys._base_executable, '-B', str(Path(__file__).resolve()), '--worker']
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1'}
    # Direct real interpreter: the Popen handle owns the only parser process.
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    start = time.monotonic()
    timed_out = False
    try:
        stdout, stderr = p.communicate(data, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        p.kill()  # Only this child handle; never enumerate or kill other processes.
        stdout, stderr = p.communicate(timeout=5)
    execution = {'child_pid': p.pid, 'returncode': p.returncode, 'timed_out': timed_out,
                 'timeout_seconds': timeout, 'elapsed_seconds': time.monotonic()-start,
                 'kill_scope': 'owned Python child only' if timed_out else 'none'}
    try:
        if timed_out or p.returncode != 0:
            raise ValueError('child timeout' if timed_out else 'child failed')
        report = json.loads(stdout)
        if report.pop('_worker_pid') != p.pid:
            raise ValueError('worker PID mismatch')
        if report['source_sha256'] != sha(data):
            raise ValueError('worker input SHA mismatch')
    except (ValueError, KeyError, TypeError):
        report = empty_report(data, 'UNSUPPORTED', 'Isolated parser did not return a complete valid report')
        report['child_stderr'] = stderr.decode('utf-8', errors='replace')[-4000:]
    report['execution'] = execution
    return report


def render_table(report):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    lines = [f"Status: {report['status']} | SHA256: {report['source_sha256']}",
             'Top-level selected objects: UNKNOWN | group ownership: UNKNOWN | complete: false',
             '| candidate | shape (HEURISTIC) | records | contour bytes | text candidate | color candidate | bbox m (HEURISTIC) |',
             '|---|---|---|---|---|---|---|']
    for row in report['candidates']:
        lines.append('| ' + ' | '.join(cell(v) for v in [row['display_index'], row['kind']['value'], row.get('record_count', 'UNKNOWN'), row.get('contour_range',{}).get('value','UNKNOWN'), row.get('text',{}).get('value'), row.get('color',{}).get('value',{}).get('name'), row.get('bbox',{}).get('value')]) + ' |')
    text = report.get('payload_text', {}).get('value', {}).get('text_content')
    if text:
        lines.append('Payload text candidate (ownership UNKNOWN): ' + cell(text))
    lines.append('Candidates are not a complete object list. No persistent IDs or write permission.')
    return '\n'.join(lines)


def main(argv=None):
    if argv is None and sys.argv[1:] == ['--worker']:
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
        try:
            if len(data) > MAX_BYTES:
                raise ValueError('worker input admission limit')
            report = _decode_worker(data)
        except Exception as error:
            report = empty_report(data, 'UNSUPPORTED', type(error).__name__ + ': ' + str(error))
            report['decoder_status'] = 'ERROR_NO_PARTIAL_SUCCESS'
        report['_worker_pid'] = os.getpid()
        sys.stdout.write(json.dumps(report, ensure_ascii=True, allow_nan=False))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Existing saved binary TypeEditZone file')
    parser.add_argument('--format', choices=['json','table'], default='json')
    parser.add_argument('--timeout', type=float, default=8.0)
    parser.add_argument('--output', type=Path, help='New output path; existing files are never overwritten')
    args = parser.parse_args(argv)
    if args.output and args.output.exists():
        parser.error('output exists; refusing overwrite')
    try:
        if args.input.stat().st_size > MAX_BYTES:
            raise ValueError('Input exceeds diagnostic admission limit of 16 MiB')
        with args.input.open('rb') as source:
            data = source.read(MAX_BYTES + 1)
        report = analyze_bytes(data, timeout=args.timeout)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) if args.format=='json' else render_table(report)
    if args.output:
        with args.output.open('x', encoding='utf-8') as dest:
            dest.write(text + '\n')
    else:
        print(text)
    return 0 if report['status']=='PARTIAL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
