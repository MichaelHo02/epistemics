"""Tracked strict-schema order assay. Four smoke calls, then 72 fixed assay calls; no retries."""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
from pathlib import Path
import shutil

from cases import make_cases
from common import CFG, ROOT, destination, save
from fixture import build, observed_checker
from oracle import inspect
from order_api import API
from order_interface import ARMS, parse_response, request_body, request_digest, score, wire_bytes
from order_validate import validate


def aggregate(rows):
    assert len(rows) == 36
    unknown = sum(not r['valid'] for r in rows)
    clear = sum(r['false_clearance'] is True for r in rows)
    inconsistent = sum(r['inconsistent'] is True for r in rows)
    return {'planned': 36, 'valid': 36 - unknown, 'invalid_or_unavailable': unknown,
            'exact_remaining_itt': {'numerator': sum(r['exact_remaining'] for r in rows), 'denominator': 36,
                                    'rate': sum(r['exact_remaining'] for r in rows) / 36},
            'false_clearance_itt': {'known_count': clear, 'unknown_count': unknown, 'denominator': 36,
                                    'identification_bounds': [clear / 36, (clear + unknown) / 36],
                                    'rate_if_complete': clear / 36 if not unknown else None},
            'inconsistency_itt': {'known_count': inconsistent, 'unknown_count': unknown, 'denominator': 36,
                                  'identification_bounds': [inconsistent / 36, (inconsistent + unknown) / 36]},
            'order_violations_among_valid': sum(r['order_compliant'] is False for r in rows),
            'ledger_exact_all_planned': sum(r['ledger_exact'] for r in rows),
            'preservation_correct_all_planned': sum(r['preservation_correct'] for r in rows)}


def summarize(rows):
    arms = {a: aggregate([r for r in rows if r['arm'] == a]) for a in ARMS}
    family = {}
    for fid in sorted({r['family'] for r in rows}):
        family[fid] = {}
        for a in ARMS:
            group = [r for r in rows if r['family'] == fid and r['arm'] == a]
            assert len(group) == 6
            family[fid][a] = {'exact': sum(r['exact_remaining'] for r in group),
                              'known_false_clearances': sum(r['false_clearance'] is True for r in group),
                              'invalid': sum(not r['valid'] for r in group), 'denominator': 6}
    l, r = [arms[a] for a in ARMS]
    lb, rb = l['false_clearance_itt']['identification_bounds'], r['false_clearance_itt']['identification_bounds']
    return {'assigned_arms': arms, 'by_family': family,
            'primary_ledger_first_minus_remaining_first': {
                'exact_remaining_itt': l['exact_remaining_itt']['rate'] - r['exact_remaining_itt']['rate'],
                'false_clearance_itt_bounds': [lb[0] - rb[1], lb[1] - rb[0]]},
            'independent_authored_families': 6,
            'analysis_population': '36 fixed known developer cases; not held-out confirmation; paired conditions',
            'interpretation': 'Controlled replication/extension of existing schema-order work. '
                              'ITT by assigned order includes order violations. No novelty or internal-state claim.'}


def main():
    import tiktoken
    output = destination()
    records = build(output / 'fixtures')
    all_cases = make_cases(records)
    cases, smoke, plan, frozen = validate(all_cases, records)
    save(output / 'frozen-manifest.json', frozen)
    shutil.copy2(ROOT / 'order-protocol.md', output / 'protocol.md')
    by_id = {c['case_id']: c for c in cases + [smoke]}
    gold = {}
    for cid, case in by_id.items():
        gold[cid] = inspect(case['record']['family'], case['record']['root'])
        visible = observed_checker(case['record']['family'], case['record']['events'])
        assert visible['remaining'] == gold[cid]['remaining']
        save(output / 'cases' / (cid + '.json'), {'observations': json.loads(case['observations']),
             'gold_independent_state': gold[cid], 'visible_probe_comparator': visible})
    encoding = tiktoken.get_encoding('o200k_base')
    estimated = [len(encoding.encode(wire_bytes(request_body(c, a, CFG)).decode())) + 256
                 for c in cases + [smoke] for a in ARMS]
    assert max(estimated) <= CFG['input_tokens']
    save(output / 'preflight.json', {'offline_checks_passed': True, 'assay_cells': 36,
                                   'assay_calls': 72, 'smoke_calls': 4, 'hard_attempt_cap': 76,
                                   'max_wire_tokens_plus_256_margin': max(estimated),
                                   'deterministic_visible_checker_exact': [36, 36]})
    print(json.dumps({'event': 'preflight', 'assay_cases': 36, 'assay_calls': 72, 'smoke_calls': 4,
                      'max_wire_tokens_plus_256_margin': max(estimated), 'hard_cap': 76}), flush=True)
    api = API(output, CFG, encoding)

    def evaluate(task):
        case = by_id[task['case_id']]
        f = case['record']['family']
        args = (gold[case['case_id']], task['arm'], case['case_id'], f['id'], case['report'])
        body = request_body(case, task['arm'], CFG)
        raw = None
        request_path = None
        fatal = False
        error = None
        try:
            raw, request_path = api.query(body, task)
        except Exception as exc:
            fatal = True
            error = {'kind': 'api_or_transport', 'class': type(exc).__name__}
            value = None
        else:
            try:
                value = parse_response(raw, case)
            except (ValueError, TypeError) as exc:
                value = None
                error = {'kind': 'full_schema_validation', 'class': type(exc).__name__}
        row = score(value, *args)
        row.update({'task': task, 'raw_text': raw, 'parsed': value, 'error': error,
                    'fatal_dispatch_error': fatal, 'request_file': request_path,
                    'request_sha256': request_digest(body)})
        save(output / 'predictions' / f'{task["phase"]}-{case["case_id"]}-{task["arm"]}-{task["replicate"]}.json', row)
        return row

    # Separately identified completed-case live acceptance checks. No retries or feedback tuning.
    smoke_rows = []
    for index, task in enumerate(plan[0]):
        task = {**task, 'planned_index': index}
        row = evaluate(task)
        smoke_rows.append(row)
        save(output / 'smoke-results.json', smoke_rows)
        if row['fatal_dispatch_error'] or not row['valid'] or not row['order_compliant']:
            save(output / 'stopped.json', {'phase': 'smoke', 'attempts': dict(api.budget.counts),
                                          'reason': 'Acceptance/status/structure/order smoke check failed; no retry'})
            raise SystemExit('Smoke validation failed; stopped without retry or assay')
    print(json.dumps({'event': 'smoke_passed', 'attempts': 4, 'provider_schema_and_order_accepted': True}), flush=True)
    rows = []
    stopped = False
    iterator = iter([{**t, 'planned_index': i} for i, t in enumerate(plan[1])])
    with ThreadPoolExecutor(max_workers=CFG['concurrency']) as pool:
        pending = {pool.submit(evaluate, next(iterator)): True for _ in range(CFG['concurrency'])}
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                pending.pop(future)
                row = future.result()
                rows.append(row)
                if row['fatal_dispatch_error']:
                    stopped = True
            if not stopped:
                for _ in done:
                    task = next(iterator, None)
                    if task is not None:
                        pending[pool.submit(evaluate, task)] = True
            save(output / 'progress.json', {'returned_assay': len(rows), 'attempts': dict(api.budget.counts),
                                           'new_dispatch_stopped': stopped})
    # Keep every randomized cell in the ITT denominator, including unavailable results.
    present = {(r['case_id'], r['arm']) for r in rows}
    for task in plan[1]:
        if (task['case_id'], task['arm']) not in present:
            case = by_id[task['case_id']]
            row = score(None, gold[case['case_id']], task['arm'], case['case_id'],
                        case['record']['family']['id'], case['report'])
            row.update({'task': task, 'error': {'kind': 'not_dispatched_after_failure'}, 'raw_text': None})
            rows.append(row)
    rows.sort(key=lambda r: (r['case_id'], r['arm']))
    save(output / 'all-assay-predictions.json', rows)
    result = summarize(rows)
    result.update({'attempts': dict(api.budget.counts), 'total_attempts': sum(api.budget.counts.values()),
                   'token_usage': api.tokens, 'transport_stop': stopped,
                   'complete_assay_dispatch': api.budget.counts['assay'] == 72,
                   'visible_probe_comparator': {'exact': 36, 'denominator': 36},
                   'smoke_separate_from_assay': True})
    save(output / 'summary.json', result)
    print(json.dumps({'event': 'final_metrics', **result}), flush=True)
    if stopped:
        raise SystemExit('New dispatch stopped after API failure; partial ITT outputs retained; no retry')


if __name__ == '__main__':
    main()

