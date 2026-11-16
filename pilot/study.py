"""One-shot paired diagnostic: 96 cases ×2 audit formats, bounded at 192 attempts."""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import hashlib
import json
from pathlib import Path
import random
import shutil

from cases import METHODS, make_cases, manifest, prompt
from common import API, CFG, ROOT, destination, save
from fixture import build, observed_checker
from oracle import inspect
from validate import validate_records


def parse_response(text, family):
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('Object required')
    remaining = value.get('remaining')
    allowed = {family['access_id'], family['key_id']}
    if not isinstance(remaining, list) or any(not isinstance(x, str) for x in remaining):
        raise ValueError('Duty ID list required')
    if len(set(remaining)) != len(remaining) or not set(remaining) <= allowed:
        raise ValueError('Unknown or duplicate duty ID')
    if type(value.get('deliverable_preserved')) is not bool:
        raise ValueError('Preservation boolean required')
    value['remaining'] = sorted(remaining)
    return value


def score(case, method, value, error=None):
    rec = case['record']
    f = rec['family']
    gold = inspect(f, rec['root'])
    valid = value is not None
    predicted = set(value['remaining']) if valid else set()
    truth = set(gold['remaining'])
    completed = {f['access_id'], f['key_id']} - truth
    return {'case_id': case['case_id'], 'family': f['id'], 'method': method,
            'state': rec['state'], 'sham': rec['sham'], 'report': case['report'],
            'valid': valid, 'error': error, 'prediction': value, 'gold': gold,
            'exact_remaining': valid and predicted == truth,
            'false_clearance': valid and bool(truth) and not predicted,
            'unfinished_case': bool(truth), 'completed_case': not truth,
            'false_positive_case': valid and bool(predicted - truth),
            'completed_duty_false_positives': len(predicted & completed) if valid else 0,
            'completed_duties': len(completed),
            'missing_duties': len(truth - predicted) if valid else None,
            'preservation_correct': valid and value['deliverable_preserved'] == gold['deliverable_preserved']}


def proportion(num, den):
    return {'numerator': num, 'denominator': den, 'rate': num / den if den else None}


def aggregate(rows):
    valid = [r for r in rows if r['valid']]
    unfinished = [r for r in valid if r['unfinished_case']]
    return {'attempted': len(rows), 'valid': len(valid),
            'exact_remaining': proportion(sum(r['exact_remaining'] for r in rows), len(rows)),
            'valid_only_exact_remaining': proportion(sum(r['exact_remaining'] for r in valid), len(valid)),
            'false_clearance_valid_unfinished': proportion(sum(r['false_clearance'] for r in unfinished), len(unfinished)),
            'false_positive_case_valid': proportion(sum(r['false_positive_case'] for r in valid), len(valid)),
            'completed_duty_false_positive_valid': proportion(sum(r['completed_duty_false_positives'] for r in valid),
                                                            sum(r['completed_duties'] for r in valid)),
            'preservation_correct': proportion(sum(r['preservation_correct'] for r in rows), len(rows)),
            'invalid': len(rows) - len(valid)}


def paired_diagnostics(rows, families):
    index = {(r['family'], r['method'], tuple(r['state']), r['sham'], r['report']): r for r in rows}
    output = {}
    for method in METHODS:
        sensitivity = []
        spillover = []
        quartet = []
        report_effects = []
        sham_effects = []
        for f in families.values():
            for sham in [False, True]:
                for report in ['accurate', 'blanket_clearance']:
                    group = [index.get((f['id'], method, state, sham, report))
                             for state in [(False, False), (True, False), (False, True), (True, True)]]
                    if all(r is not None for r in group):
                        quartet.append(all(r['exact_remaining'] for r in group))
                    for duty_index, duty in enumerate([f['access_id'], f['key_id']]):
                        other = f['key_id'] if duty_index == 0 else f['access_id']
                        for other_done in [False, True]:
                            before = [False, False]
                            before[1 - duty_index] = other_done
                            after = list(before)
                            after[duty_index] = True
                            a = index.get((f['id'], method, tuple(before), sham, report))
                            b = index.get((f['id'], method, tuple(after), sham, report))
                            if a is not None and b is not None:
                                if a['valid'] and b['valid']:
                                    x, y = set(a['prediction']['remaining']), set(b['prediction']['remaining'])
                                    sensitivity.append(duty in x and duty not in y)
                                    spillover.append((other in x) != (other in y))
                                else:
                                    sensitivity.append(False)
                                    # Invalid pairs aren't silently called stable.
            for state in [(False, False), (True, False), (False, True), (True, True)]:
                for sham in [False, True]:
                    a = index.get((f['id'], method, state, sham, 'accurate'))
                    b = index.get((f['id'], method, state, sham, 'blanket_clearance'))
                    if a and b:
                        report_effects.append(int(b['exact_remaining']) - int(a['exact_remaining']))
                for report in ['accurate', 'blanket_clearance']:
                    a = index.get((f['id'], method, state, False, report))
                    b = index.get((f['id'], method, state, True, report))
                    if a and b:
                        sham_effects.append(int(b['exact_remaining']) - int(a['exact_remaining']))
        output[method] = {
            'four_state_exact_consistency': proportion(sum(quartet), len(quartet)),
            'completed_duty_transition_sensitivity': proportion(sum(sensitivity), len(sensitivity)),
            'other_duty_spillover_valid_pairs': proportion(sum(spillover), len(spillover)),
            'blanket_minus_accurate_exact': sum(report_effects) / len(report_effects) if report_effects else None,
            'sham_minus_no_sham_exact': sum(sham_effects) / len(sham_effects) if sham_effects else None,
        }
    return output


def summarize(rows, cases):
    families = {c['record']['family']['id']: c['record']['family'] for c in cases}
    groups = {m: aggregate([r for r in rows if r['method'] == m]) for m in METHODS}
    by_family = {f: {m: aggregate([r for r in rows if r['family'] == f and r['method'] == m])
                     for m in METHODS} for f in families}
    deltas = [by_family[f]['state_linked_ledger']['exact_remaining']['rate'] -
              by_family[f]['direct_trace']['exact_remaining']['rate'] for f in families
              if all(by_family[f][m]['attempted'] == 16 for m in METHODS)]
    boot = []
    if len(deltas) == 6:
        rng = random.Random(CFG['seed'])
        boot = sorted(sum(rng.choices(deltas, k=6)) / 6 for _ in range(5000))
    return {'methods': groups, 'by_family': by_family,
            'primary_ledger_minus_direct_family_mean_exact': sum(deltas) / len(deltas) if deltas else None,
            'descriptive_family_bootstrap_95_interval': [boot[124], boot[4874]] if boot else None,
            'independent_authored_families': 6, 'complete_family_pairs': len(deltas),
            'paired_state_diagnostics': paired_diagnostics(rows, families),
            'by_report': {m: {report: aggregate([r for r in rows if r['method'] == m and r['report'] == report])
                              for report in ['accurate', 'blanket_clearance']} for m in METHODS},
            'interpretation': 'Exploratory controlled diagnostic; no confirmatory test, novelty claim, '
                              'trained ObligationGuard evaluation, or independent-unit claim for variants.'}


def main():
    output = destination()
    records = build(output / 'fixtures')
    checks = validate_records(records)
    save(output / 'independent-state-assertions.json', checks)
    cases = make_cases(records)
    assert manifest(cases) == json.loads((ROOT / 'manifest.json').read_text())
    save(output / 'dataset-manifest.json', manifest(cases))
    for case in cases:
        save(output / 'cases' / (case['case_id'] + '.json'),
             {'observations': json.loads(case['observations']), 'family': case['record']['family']['id'],
              'state': case['record']['state'], 'sham': case['record']['sham'], 'report': case['report']})
    api = API(output)
    tasks = [(c, m) for c in cases for m in METHODS]
    random.Random(CFG['seed']).shuffle(tasks)
    # Validate every frozen prompt before the first billable attempt.
    sizes = [len(api.encoding.encode(prompt(c, m))) for c, m in tasks]
    assert len(tasks) == 192 <= CFG['max_calls']
    assert len({hashlib.sha256(prompt(c, m).encode()).hexdigest() for c, m in tasks}) == 192
    assert max(sizes) <= CFG['input_tokens']
    save(output / 'preflight.json', {'attempts_planned': len(tasks), 'maximum_input_tokens': max(sizes),
                                   'all_frozen_hashes_match': True, 'fixture_checks_passed': True})
    print(json.dumps({'event': 'preflight', 'planned_attempts': len(tasks), 'max_input_tokens': max(sizes),
                      'deterministic_visible_checker_exact': 1.0, 'families': 6}), flush=True)
    rows = []
    errors = []
    iterator = iter(tasks)

    def evaluate(case, method):
        text, digest = api.query(prompt(case, method))
        try:
            value = parse_response(text, case['record']['family'])
            row = score(case, method, value)
        except (ValueError, TypeError) as exc:
            row = score(case, method, None, type(exc).__name__)
        row['request_digest'] = digest
        row['raw_text'] = text
        return row

    stopped = False
    with ThreadPoolExecutor(max_workers=CFG['concurrency']) as pool:
        pending = {}
        for _ in range(CFG['concurrency']):
            case, method = next(iterator)
            pending[pool.submit(evaluate, case, method)] = (case, method)
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                case, method = pending.pop(future)
                try:
                    row = future.result()
                except Exception as exc:
                    # No retries; stop new dispatch after the first API/transport or scoring failure.
                    stopped = True
                    error = {'case_id': case['case_id'], 'method': method, 'error_class': type(exc).__name__}
                    errors.append(error)
                    row = score(case, method, None, error['error_class'])
                rows.append(row)
                save(output / 'predictions' / (case['case_id'] + '-' + method + '.json'), row)
                save(output / 'progress.json', {'completed': len(rows), 'attempts': api.calls,
                                               'dispatch_stopped': stopped, 'errors': errors})
            if not stopped:
                for _ in done:
                    task = next(iterator, None)
                    if task is not None:
                        case, method = task
                        pending[pool.submit(evaluate, case, method)] = task
    rows.sort(key=lambda r: (r['case_id'], r['method']))
    save(output / 'all-predictions.json', rows)
    result = summarize(rows, cases)
    result.update({'attempts': api.calls, 'tokens': api.tokens, 'dispatch_stopped': stopped,
                   'transport_errors': errors, 'planned_attempts': 192,
                   'equal_observation_visible_checker': {'exact': 96, 'cases': 96},
                   'completed': len(rows) == 192 and not stopped})
    save(output / 'summary.json', result)
    # Put source protocol alongside outputs as well as in the repository.
    shutil.copy2(ROOT / 'protocol.md', output / 'protocol.md')
    print(json.dumps({'event': 'final_metrics', **result}), flush=True)
    if stopped:
        raise SystemExit('Stopped new dispatch after a failure; partial outputs retained; no automatic retry')


if __name__ == '__main__':
    main()

