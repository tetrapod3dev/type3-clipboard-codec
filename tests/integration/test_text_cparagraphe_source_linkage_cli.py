from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools/analyze_text_cparagraphe_source_linkage.py'


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture(scope='module')
def analyzer():
    spec = importlib.util.spec_from_file_location('source_linkage_test', CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def report():
    output = run_cli('--json')
    assert len(output.encode('utf-8')) < 100000
    return json.loads(output)


def test_coverage_policy_and_bounds(report, analyzer):
    assert len(report['fixture_results']) == 13
    assert {r['fixture'] for r in report['fixture_results']} == set(analyzer.FIXTURES)
    assert report['policy'] == {'scope': 'cparagraphe_source_linkage_analysis_only',
        'parser_behavior': 'not_modified', 'ownership_assignment': 'not_performed',
        'active_anchor_behavior': 'unchanged', 'oracle_isolation': True}
    assert not report['warnings']
    assert len(run_cli().encode('utf-8')) < 50000
    for forbidden in ('file_offset', 'stream_offset', 'absolute_offset', 'matched_chain', 'raw_payload'):
        assert forbidden not in json.dumps(report)
    assert report['answers']['conclusion'] == 'raw_source_chain_relationship_supported'
    assert not report['answers']['parser_safe_ownership_ready']


def test_counts_and_ranges(report):
    for h in report['hypothesis_summary']:
        assert [h[k] for k in ('support_count', 'conflict_count', 'abstention_count')] == (
            [13, 0, 0] if h['name'] in ('H1', 'H3', 'H4') else [0, 0, 13])
        assert h['parser_safe'] is False and h['semantic_linkage_proven'] is False
    assert report['source_chain_provenance_summary']['chain_count'] == 34
    assert report['source_chain_provenance_summary']['changed_index_count'] == 10
    for r in report['fixture_results']:
        s = r['structural']
        assert s['mapping_complete'] and not s['truncated']
        assert s['hypotheses']['H1'] == s['hypotheses']['H3'] == s['hypotheses']['H4'] == [0]
        rows = s['source_chain_provenance']
        assert [x['source_chain_ordinal'] for x in rows] == list(range(len(rows)))
        assert sorted(rows, key=lambda x: x['sort_key']) == sorted(rows, key=lambda x: x['final_chain_index'])
        assert rows[0]['source_node_class'] == 'CContour'
        assert all(x['source_node_class'] == 'CPropertyExtend' for x in rows[1:])
        block = s['local_blocks'][0]
        assert block['cparagraphe_node_ordinal'] == 1
        assert block['first_producing_CContour_after'] == 3
        assert block['next_scanner_boundary_class'] == 'CPropertyExtend'
        assert block['independent_enclosing_object_range'] is None
        assert block['other_producing_sources_before_parser_group_end']
        assert all(x['parser_group_node_ordinals'] == rows[0]['parser_group_node_ordinals'] for x in rows)


def test_oracle_off(report):
    disabled = json.loads(run_cli('--json', '--no-oracle'))
    assert [r['structural'] for r in report['fixture_results']] == [r['structural'] for r in disabled['fixture_results']]
    for key in ('source_chain_provenance_summary', 'structural_block_summary'):
        assert report[key] == disabled[key]
    assert all(r['oracle'] is None for r in disabled['fixture_results'])


@pytest.mark.parametrize('index', range(13))
def test_active_objects_parser_files_and_intent_independence(analyzer, monkeypatch, tmp_path, index):
    fixture = analyzer.FIXTURES[index]
    blob = analyzer.visible._read_fixture(analyzer.TEXT_DIR / fixture)
    parsed, _ = analyzer.visible.parse_type3_clipboard_bytes_with_parser(blob)
    nodes = analyzer.visible._read_nodes(blob)
    before, before_nodes = copy.deepcopy(parsed), copy.deepcopy(nodes)
    sources = {p: p.read_bytes() for p in (ROOT / 'src').rglob('*.py')}
    result = analyzer.analyze_parsed(parsed, nodes, fixture)
    monkeypatch.setattr(analyzer.visible, 'INTENT_DIR', tmp_path)
    without_intent = analyzer.analyze_parsed(parsed, nodes, 'arbitrary_name.txt')
    assert result['structural'] == without_intent['structural']
    monkeypatch.setattr(analyzer.visible, '_intent_metadata', lambda *_: pytest.fail('intent loaded'))
    monkeypatch.setattr(analyzer.owner.shadow, 'anchor_oracle', lambda *_: pytest.fail('oracle loaded'))
    assert analyzer.analyze_parsed(parsed, nodes, fixture, False)['structural'] == result['structural']
    assert parsed == before and nodes == before_nodes
    again, _ = analyzer.visible.parse_type3_clipboard_bytes_with_parser(blob)
    assert again == before
    assert all(c['matched_chain'] is None for c in parsed.candidate_fields['cproperty_anchor_candidates'])
    assert all(p.read_bytes() == content for p, content in sources.items())
    # Change final ordering and coordinate sort inputs: raw candidate selection is invariant.
    parsed.object_chains.reverse()
    for chain in parsed.object_chains:
        chain.text_anchor = None
        chain.bbox = None
    reordered = analyzer.structural_phase(parsed, nodes)
    assert reordered['hypotheses'] == result['structural']['hypotheses']
    assert reordered['local_blocks'] == result['structural']['local_blocks']
    assert [r['source_structural_span'] for r in reordered['source_chain_provenance']] == [r['source_structural_span'] for r in result['structural']['source_chain_provenance']]


def test_corpus_freezes_before_oracle_or_intent(analyzer, monkeypatch):
    phase = analyzer.structural_phase
    intent = analyzer.visible._intent_metadata
    oracle = analyzer.owner.shadow.anchor_oracle
    frozen = []
    def capture(*args):
        result = phase(*args)
        frozen.append(analyzer.compact(result))
        return result
    def checked(fn):
        def call(*args):
            assert len(frozen) == 13
            return fn(*args)
        return call
    monkeypatch.setattr(analyzer, 'structural_phase', capture)
    monkeypatch.setattr(analyzer.visible, '_intent_metadata', checked(intent))
    monkeypatch.setattr(analyzer.owner.shadow, 'anchor_oracle', checked(oracle))
    result = analyzer.build_report()
    assert frozen == [analyzer.compact(r['structural']) for r in result['fixture_results']]
