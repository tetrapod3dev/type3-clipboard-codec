"""Audit source construction and scanner boundaries without assigning ownership."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_text_cparagraphe_owner_structure as owner

visible = owner.visible
FIXTURES = owner.FIXTURES
TEXT_DIR = owner.TEXT_DIR
compact = owner.compact
MAX_NODES, MAX_CHAINS = 32, 8
DEFINITIONS = {
    'H1': 'immediate-next-chain-producing-node: first producing CContour after CParagraphe',
    'H2': 'same-local-block: independently delimited object block selects one source',
    'H3': 'raw-source-chain ordinal relationship: first raw chain from the paragraph parser group',
    'H4': 'CCourbe/CContour linkage: contiguous CParagraphe, CCourbe, producing CContour sequence',
    'H5': 'adjacency-only: layout ordering alone explains the correlation (null hypothesis)',
}


def source_key(chain, nodes, origin=0):
    # Addresses reconcile provenance only; never choose an owner or appear in output.
    hits = [i for i, n in enumerate(nodes)
            if n.header.class_name == chain.source_node_class
            and chain.source_payload_offset is not None
            and n.payload_offset + origin + chain.source_payload_offset == chain.source_stream_offset]
    return (hits[0], chain.source_payload_offset) if len(hits) == 1 else None


def structural_phase(parsed, nodes):
    parser = visible.Type3ChainParser()
    working = copy.deepcopy(nodes)
    groups = parser._group_nodes_into_chains(working)
    ordinal = {id(n): i for i, n in enumerate(working)}
    raw, group_rows = [], []
    for gi, group in enumerate(groups):
        members = [ordinal[id(n)] for n in group.nodes]
        produced = parser._process_object_chain(group)
        group_rows.append({'group_ordinal': gi, 'node_ordinals': members,
                           'raw_chain_ordinals': list(range(len(raw), len(raw) + len(produced))),
                           'boundary_basis': 'parser CZone/repeated-CContour heuristic'})
        raw.extend(produced)
    truncated = len(nodes) > MAX_NODES or len(raw) > MAX_CHAINS
    final_keys = [source_key(c, nodes, visible.TOP_LEVEL_HEADER_LEN) for c in parsed.object_chains]
    rows = []
    for ri, chain in enumerate(raw[:MAX_CHAINS]):
        key = source_key(chain, working)
        matches = [i for i, k in enumerate(final_keys) if key is not None and k == key]
        fi = matches[0] if len(matches) == 1 else None
        final = parsed.object_chains[fi] if fi is not None else None
        point = (final.text_anchor or (final.bbox.center_mm if final.bbox else None)) if final else None
        members = [ordinal[id(n)] for n in chain.nodes]
        source = key[0] if key else None
        rows.append({'source_chain_ordinal': ri, 'final_chain_index': fi,
                     'source_node_ordinals': [source] if source is not None else [],
                     'source_node_class': chain.source_node_class,
                     'source_CContour_ordinal': source if chain.source_node_class == 'CContour' else None,
                     'source_CCourbe_ordinal': source if chain.source_node_class == 'CCourbe' else None,
                     'context_CCourbe_ordinals': [i for i in members if nodes[i].header.class_name == 'CCourbe'],
                     'parser_group_node_ordinals': members[:MAX_NODES],
                     'source_structural_span': {'node_ordinal': source, 'payload_relative_begin': key[1],
                         'byte_length': len(chain.raw_contour_bytes)} if key else None,
                     'sort_key': [point.x, point.y] if point else None,
                     'sort_key_basis': 'text_anchor.xy else bbox.center_mm.xy else infinity',
                     'index_changed_after_sorting': ri != fi if fi is not None else None})
    classes = [n.header.class_name for n in nodes]
    blocks = []
    for pi in [i for i, c in enumerate(classes[:MAX_NODES]) if c == 'CParagraphe']:
        following = [r for r in rows if r['source_CContour_ordinal'] is not None and r['source_CContour_ordinal'] > pi]
        ci = min((r['source_CContour_ordinal'] for r in following), default=None)
        group = next(g for g in group_rows if pi in g['node_ordinals'])
        blocks.append({'cparagraphe_node_ordinal': pi,
            'nearest_CZone_before': next((i for i in range(pi-1, -1, -1) if classes[i] == 'CZone'), None),
            'nearest_CCourbe_after': next((i for i in range(pi+1, len(classes)) if classes[i] == 'CCourbe'), None),
            'first_producing_CContour_after': ci,
            'next_scanner_boundary': ci+1 if ci is not None and ci+1 < len(nodes) else None,
            'next_scanner_boundary_class': classes[ci+1] if ci is not None and ci+1 < len(nodes) else None,
            'intervening_node_ordinals': list(range(pi+1, ci)) if ci is not None else [],
            'common_parser_group': group['group_ordinal'] if ci in group['node_ordinals'] else None,
            'group_raw_chain_ordinals': group['raw_chain_ordinals'],
            'other_producing_sources_before_parser_group_end': [r['source_chain_ordinal'] for r in rows
                if r['source_node_ordinals'] and r['source_node_ordinals'][0] in group['node_ordinals']
                and r['source_node_ordinals'][0] != ci],
            'another_producer_before_next_scanner_boundary': sum(r['source_CContour_ordinal'] == ci for r in rows) > 1 if ci is not None else None,
            'independent_enclosing_object_range': None})
    proposals = {name: [] for name in DEFINITIONS}
    if len(blocks) == 1 and not truncated:
        b = blocks[0]
        proposals['H1'] = [r['source_chain_ordinal'] for r in rows if r['source_CContour_ordinal'] is not None
                           and r['source_CContour_ordinal'] == b['first_producing_CContour_after']]
        proposals['H3'] = b['group_raw_chain_ordinals'][:1]
        pi = b['cparagraphe_node_ordinal']
        if classes[pi:pi+3] == ['CParagraphe', 'CCourbe', 'CContour']:
            proposals['H4'] = proposals['H1'][:]
    return {'node_scan_order': [{'ordinal': i, 'class': n.header.class_name,
                'payload_length': len(n.payload), 'markers': [m.decode('ascii') for m in
                (b'CObDao', b'OBJECTINFOS_CLASSNAME', b'OBJETINFOS_CLASSNAME') if m in n.payload]}
                for i, n in enumerate(nodes[:MAX_NODES])],
            'source_chain_provenance': rows, 'parser_groups': group_rows[:MAX_NODES],
            'local_blocks': blocks, 'hypotheses': proposals, 'truncated': truncated,
            'mapping_complete': len(raw) == len(parsed.object_chains) and all(r['final_chain_index'] is not None for r in rows),
            'scanner_boundary_semantics': 'next plausible class header, not validated object length or parent-child delimiter'}


def finish_fixture(parsed, nodes, frozen, fixture, oracle_enabled=True):
    structure = json.loads(frozen)
    oracle = None
    intent = None
    if oracle_enabled:
        intent = visible._intent_metadata(fixture)
        paragraphs = [n for n in nodes if n.header.class_name == 'CParagraphe']
        if len(paragraphs) == 1 and not structure['truncated']:
            oracle = owner.shadow.anchor_oracle(visible._decode_cparagraphe_direct_anchor(paragraphs[0].payload),
                                                owner.shadow._chain_rows(parsed))
    matches = oracle['matching_chain_indices'] if oracle and oracle['status'] == 'unique' else None
    comparisons = {}
    for name, candidates in structure['hypotheses'].items():
        mapped = [r['final_chain_index'] for r in structure['source_chain_provenance']
                  if r['source_chain_ordinal'] in candidates]
        comparisons[name] = ('support' if mapped == matches else 'conflict') if matches is not None and len(mapped) == 1 and mapped[0] is not None else 'abstention'
    return {'fixture': fixture, 'structural': structure, 'oracle': oracle,
            'reporting_grouping': intent['grouping'] if intent else None, 'comparisons': comparisons}


def analyze_parsed(parsed, nodes, fixture, oracle_enabled=True):
    return finish_fixture(parsed, nodes, compact(structural_phase(parsed, nodes)), fixture, oracle_enabled)


def build_report(oracle_enabled=True):
    prepared = []
    for fixture in FIXTURES:
        blob = visible._read_fixture(TEXT_DIR / fixture)
        parsed, _ = visible.parse_type3_clipboard_bytes_with_parser(blob)
        nodes = visible._read_nodes(blob)
        prepared.append((parsed, nodes, compact(structural_phase(parsed, nodes)), fixture))
    results = [finish_fixture(*p, oracle_enabled=oracle_enabled) for p in prepared]
    rows = [c for r in results for c in r['structural']['source_chain_provenance']]
    hypotheses = []
    for name, definition in DEFINITIONS.items():
        hypotheses.append({'name': name, 'definition': definition,
            **{outcome+'_count': sum(r['comparisons'][name] == outcome for r in results)
               for outcome in ('support', 'conflict', 'abstention')},
            'structural_evidence': {'proposal_fixture_count': sum(bool(r['structural']['hypotheses'][name]) for r in results)},
            'unresolved_dependencies': ['independent object delimiter or explicit reference absent',
                'H3 uses parser grouping and construction order; H4 sequence has no established semantic distinction',
                'H2 and H5 abstain: no unique block selector; oracle agreement cannot prove accidental adjacency'],
            'semantic_linkage_proven': False, 'parser_safe': False})
    return {'mode': 'text_cparagraphe_source_linkage',
        'policy': {'scope': 'cparagraphe_source_linkage_analysis_only', 'parser_behavior': 'not_modified',
                   'ownership_assignment': 'not_performed', 'active_anchor_behavior': 'unchanged', 'oracle_isolation': True},
        'limits': {'nodes_per_fixture': MAX_NODES, 'chains_per_fixture': MAX_CHAINS, 'json_bytes': 100000, 'text_bytes': 50000},
        'warnings': ['bounded inventory; affected hypotheses abstain'] if any(r['structural']['truncated'] for r in results) else [],
        'fixture_results': results,
        'source_chain_provenance_summary': {'chain_count': len(rows), 'changed_index_count': sum(r['index_changed_after_sorting'] is True for r in rows),
            'mapping_complete': all(r['structural']['mapping_complete'] for r in results),
            'construction': 'scan -> CZone/repeated-CContour groups -> CContour records and CPropertyExtend embedded records -> text pipeline XY sort'},
        'structural_block_summary': {'independent_block_found': False,
            'parser_group_is_format_object_block': False,
            'boundary': 'flat plausible class-header scan; CPropertyExtend is a node boundary, not an object terminator',
            'shared_membership': 'embedded chains inherit template nodes; common range does not uniquely link paragraph to one chain'},
        'hypothesis_summary': hypotheses,
        'oracle_summary': {'enabled': oracle_enabled, 'unique_count': sum(bool(r['oracle'] and r['oracle']['status'] == 'unique') for r in results),
            'count_basis': 'diagnostic owner agreement only; H2/H5 are not falsified by abstention',
            'cross_fixture_contrasts': [{'fixture': r['fixture'], 'grouping': r['reporting_grouping'],
                'raw_to_final': [[c['source_chain_ordinal'], c['final_chain_index']] for c in r['structural']['source_chain_provenance']],
                'H1': r['comparisons']['H1']} for r in results]},
        'answers': {'Q1': 'Common parser group exists; independently delimited object block is not demonstrated.',
            'Q2': 'Class headers delimit scanner nodes; no validated enclosing object delimiter is decoded.',
            'Q3': 'Parser group is heuristic; embedded chains share it. It explains construction, not unique ownership.',
            'Q4': 'Source candidates are selected before sorting; final indices only reconcile diagnostic comparisons.',
            'Q5': 'First raw chain in paragraph parser group is expressible without next-CContour wording, but still depends on order.',
            'adjacency_only': 'Consistent with evidence; accidental versus semantic relation remains unresolved.',
            'counterexample': 'See H1 conflicts; current fixtures cannot distinguish H1/H3/H4.',
            'conclusion': 'raw_source_chain_relationship_supported' if oracle_enabled and all(r['comparisons']['H1'] == 'support' for r in results) else 'no_independent_linkage_found',
            'independent_linkage_found': False, 'parser_safe_ownership_ready': False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--no-oracle', action='store_true')
    args = parser.parse_args()
    report = build_report(not args.no_oracle)
    if args.json:
        output = compact(report)
    else:
        output = 'CParagraphe Source Linkage\n' + '\n'.join(
            f"{h['name']}: support={h['support_count']} conflict={h['conflict_count']} abstention={h['abstention_count']}" for h in report['hypothesis_summary'])
        output += '\n' + json.dumps(report['answers'], ensure_ascii=False, indent=2)
        output += '\n' + json.dumps(report['oracle_summary']['cross_fixture_contrasts'], ensure_ascii=False, indent=2)
    if len(output.encode('utf-8')) >= (100000 if args.json else 50000):
        raise RuntimeError('output budget exceeded')
    print(output)


if __name__ == '__main__':
    main()
