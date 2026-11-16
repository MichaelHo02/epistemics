"""Mandatory offline preflight. No token/key access or network; model execution is separate."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import sys

from cases import make_cases, manifest
from common import CFG, ROOT
from fixture import build, observed_checker
from oracle import inspect
from order_api import Budget
from order_interface import (ARMS, FIELDS, canonical, dispatch_plan, parse_response, request_body,
                             request_digest, schema, score, select_cases, wire_bytes)
from validate import validate_records


def frozen_manifest(all_cases, cases, smoke, plan):
    bodies = []
    for case in cases + [smoke]:
        for arm in ARMS:
            body = request_body(case, arm, CFG)
            bodies.append({'case_id': case['case_id'], 'arm': arm,
                           'request_sha256': request_digest(body),
                           'observation_sha256': hashlib.sha256(case['observations'].encode()).hexdigest()})
    return {'assay_case_ids': [c['case_id'] for c in cases], 'smoke_case_id': smoke['case_id'],
            'ordered_request_hashes': bodies, 'dispatch_plan': list(plan),
            'parent_manifest_sha256': hashlib.sha256(canonical(manifest(all_cases)).encode()).hexdigest()}


def verify_order_only(case):
    a, b = [request_body(case, arm, CFG) for arm in ARMS]
    assert a['input'] == b['input']
    assert canonical(a) == canonical(b), 'Semantic request differs beyond property order'
    assert request_digest(a) != request_digest(b), 'Ordered-schema request hashes must differ'
    assert wire_bytes(a) != wire_bytes(b)
    sa, sb = [schema(case, arm) for arm in ARMS]
    assert sa['required'] == sb['required'] == FIELDS
    assert list(sa['properties']) == FIELDS
    assert list(sb['properties']) == ['remaining', 'ledger', 'deliverable_preserved', 'evidence_receipts']
    # Stronger than canonical equality: non-treatment nested objects keep identical byte order.
    for key in sa['properties']:
        assert wire_bytes(sa['properties'][key]) == wire_bytes(sb['properties'][key])
    without_a, without_b = deepcopy(a), deepcopy(b)
    without_a['text']['format']['schema'].pop('properties')
    without_b['text']['format']['schema'].pop('properties')
    assert wire_bytes(without_a) == wire_bytes(without_b)
    assert a['text']['format']['strict'] is True
    assert a['text']['format']['name'] == b['text']['format']['name'] == 'obligation_audit'
    assert a['reasoning'] == {'effort': 'none'}
    assert a['model'] == 'gpt-5.4-mini-2026-03-17'
    assert a['max_output_tokens'] == 1024


def verify_response_scoring(case):
    f = case['record']['family']
    gold = inspect(f, case['record']['root'])
    refs = [case['record']['events'][-1]['receipt']]
    row = {'ledger': [{'duty_id': duty, 'terminal_state': 'unfulfilled' if duty in gold['remaining'] else 'fulfilled',
                       'evidence_receipts': refs} for duty in f['order']],
           'remaining': list(gold['remaining']), 'deliverable_preserved': True, 'evidence_receipts': refs}
    assert parse_response(json.dumps(row), case) == row
    args = (gold, 'ledger_first', case['case_id'], f['id'], case['report'])
    correct = score(row, *args)
    assert correct['exact_remaining'] and not correct['inconsistent']
    assert correct['order_compliant'] and correct['ledger_exact'] and correct['preservation_correct']
    # A contradictory output remains measurable, never rejected or silently repaired.
    if gold['remaining']:
        contradiction = deepcopy(row)
        contradiction['remaining'] = []
        parsed = parse_response(json.dumps(contradiction), case)
        result = score(parsed, *args)
        assert not result['exact_remaining'] and result['false_clearance'] and result['inconsistent']
        assert result['ledger_exact']
    order_violation = {k: row[k] for k in ['remaining', 'ledger', 'deliverable_preserved', 'evidence_receipts']}
    violation_score = score(parse_response(json.dumps(order_violation), case), *args)
    assert violation_score['exact_remaining'] and not violation_score['order_compliant']
    invalid = score(None, *args)
    assert not invalid['valid'] and not invalid['exact_remaining'] and invalid['false_clearance'] is None
    corruptions = []
    for key in FIELDS:
        malformed = deepcopy(row)
        malformed.pop(key)
        corruptions.append(malformed)
    for mutate in [
        lambda x: x.update(extra=True),
        lambda x: x.update(deliverable_preserved='true'),
        lambda x: x.update(remaining=['unknown-duty']),
        lambda x: x.update(remaining=[f['order'][0], f['order'][0]]),
        lambda x: x.update(evidence_receipts=['not-a-receipt']),
        lambda x: x['ledger'].pop(),
        lambda x: x['ledger'][0].update(terminal_state='notfulfilled'),
        lambda x: x['ledger'][0].update(evidence_receipts=['agent_final_report']),
        lambda x: x['ledger'][0].update(duty_id=x['ledger'][1]['duty_id']),
    ]:
        malformed = deepcopy(row)
        mutate(malformed)
        corruptions.append(malformed)
    for malformed in corruptions:
        try:
            parse_response(json.dumps(malformed), case)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid full response was accepted')
    duplicate_key = json.dumps(row)[:-1] + ',"remaining":[]}'
    try:
        parse_response(duplicate_key, case)
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate JSON key was accepted')


def verify_budget():
    budget = Budget(76, 4, 72)
    tasks = ['smoke'] * 20 + ['assay'] * 100
    def attempt(phase):
        try:
            return budget.reserve(phase)
        except RuntimeError:
            return None
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(attempt, tasks))
    accepted = [r for r in results if r is not None]
    assert len(accepted) == len(set(accepted)) == 76
    assert sorted(accepted) == list(range(1, 77))
    assert budget.counts == {'smoke': 4, 'assay': 72}


def validate(all_cases, records, write=False):
    validate_records(records)
    assert manifest(all_cases) == json.loads((ROOT / 'manifest.json').read_text()), 'Parent inputs changed'
    cases, smoke = select_cases(all_cases)
    counts = Counter((c['record']['family']['id'], tuple(c['record']['state']), c['report']) for c in cases)
    assert len(counts) == 36 and set(counts.values()) == {1}
    assert len({c['record']['family']['id'] for c in cases}) == 6
    assert Counter(c['report'] for c in cases) == {'accurate': 18, 'blanket_clearance': 18}
    assert Counter(tuple(c['record']['state']) for c in cases) == {(False, False): 12, (False, True): 12, (True, False): 12}
    assert not any(c['record']['sham'] for c in cases)
    assert smoke['case_id'] not in {c['case_id'] for c in cases}
    for c in cases + [smoke]:
        verify_order_only(c)
        verify_response_scoring(c)
        visible = observed_checker(c['record']['family'], c['record']['events'])
        gold = inspect(c['record']['family'], c['record']['root'])
        assert visible['remaining'] == gold['remaining']
    verify_budget()
    plan = dispatch_plan(cases, smoke, CFG['seed'])
    assert plan == dispatch_plan(cases, smoke, CFG['seed'])
    assert len(plan[0]) == 4 and len(plan[1]) == 72
    assert Counter(t['arm'] for t in plan[0]) == {a: 2 for a in ARMS}
    assert Counter((t['case_id'], t['arm']) for t in plan[1]) == {(c['case_id'], a): 1 for c in cases for a in ARMS}
    assert len({request_digest(request_body(c, a, CFG)) for c in cases for a in ARMS}) == 72
    assert CFG['max_calls'] == 76 <= 80 and CFG['max_smoke_calls'] == 4 and CFG['max_assay_calls'] == 72
    # ITT aggregation must keep all cells, invalid outputs, and actual-order violations.
    from order_study import summarize
    perfect_rows = []
    missing_rows = []
    for c in cases:
        f = c['record']['family']
        truth = inspect(f, c['record']['root'])
        for arm in ARMS:
            fields = schema(c, arm)['properties']
            values = {'ledger': [{'duty_id': duty, 'terminal_state': 'unfulfilled' if duty in truth['remaining'] else 'fulfilled',
                                  'evidence_receipts': []} for duty in f['order']],
                      'remaining': truth['remaining'], 'deliverable_preserved': True, 'evidence_receipts': []}
            ordered = {k: values[k] for k in fields}
            perfect_rows.append(score(ordered, truth, arm, c['case_id'], f['id'], c['report']))
            missing_rows.append(score(None, truth, arm, c['case_id'], f['id'], c['report']))
    perfect, unavailable = summarize(perfect_rows), summarize(missing_rows)
    assert perfect['primary_ledger_first_minus_remaining_first']['exact_remaining_itt'] == 0
    for arm in ARMS:
        assert perfect['assigned_arms'][arm]['exact_remaining_itt']['rate'] == 1
        assert perfect['assigned_arms'][arm]['false_clearance_itt']['identification_bounds'] == [0, 0]
        assert unavailable['assigned_arms'][arm]['exact_remaining_itt']['rate'] == 0
        assert unavailable['assigned_arms'][arm]['false_clearance_itt']['identification_bounds'] == [0, 1]
    frozen = frozen_manifest(all_cases, cases, smoke, plan)
    if write:
        (ROOT / 'order-manifest.json').write_text(json.dumps(frozen, indent=2) + '\n')
    else:
        assert frozen == json.loads((ROOT / 'order-manifest.json').read_text()), 'Child manifest changed'
    return cases, smoke, plan, frozen


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='order-offline-check-') as temp:
        records = build(Path(temp) / 'fixtures')
        _, smoke, _, frozen = validate(make_cases(records), records, '--write-manifest' in sys.argv)
        print(json.dumps({'event': 'offline_validation', 'families': 6, 'assay_cases': 36,
                          'assay_attempts': 72, 'smoke_attempts': 4, 'hard_cap': 76,
                          'validation_equivalent_order_only_schemas': 'passed',
                          'distinct_ordered_request_digests': 'passed',
                          'full_response_and_scoring_controls': 'passed', 'thread_safe_budget': 'passed',
                          'original_inputs_unchanged': 'passed', 'smoke_case_id': smoke['case_id'],
                          'manifest_sha256': hashlib.sha256(canonical(frozen).encode()).hexdigest()}))

