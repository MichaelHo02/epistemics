"""Natural source-row output-order validation; no fixtures or semantic judge calls."""
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
import shutil

from common import CFG, ROOT, destination, save
from natural_api import API
from natural_data import sha256
from natural_interface import ARMS, EFFORTS, body_digest, parse_response, request_body, score
from natural_validate import validate


def group_summary(rows):
    def error(sign, field):
        selected = [r for r in rows if r['benchmark_positive'] == sign]
        valid = [r for r in selected if r['valid']]
        n, missing = len(selected), len(selected) - len(valid)
        count = sum(r[field] is True for r in valid)
        return {'known_count': count, 'all_planned_denominator': n, 'invalid_or_unavailable': missing,
                'strict_valid_denominator': len(valid), 'rate_among_valid': count / len(valid) if valid else None,
                'bounds_over_all_planned': [count / n, (count + missing) / n] if n else None}
    n = len(rows); good = sum(r['agreement_with_dataset_unfinished_obligation_label'] for r in rows)
    return {'planned': n, 'valid': sum(r['valid'] for r in rows),
            'agreement_with_dataset_unfinished_obligation_label': {'numerator': good, 'denominator': n, 'rate': good / n if n else None},
            'benchmark_positive_empty_clearance': error(True, 'positive_empty_clearance'),
            'benchmark_negative_nonempty_warning': error(False, 'negative_nonempty_warning'),
            'actual_order_violations_among_valid': sum(r['order_compliant'] is False for r in rows),
            'mechanical_crossfield_flags_among_valid': {k: sum(bool(r['link_diagnostics'][k]) for r in rows if r['valid']) for k in [
                'duplicate_ledger_ids', 'duplicate_remaining_ids', 'dangling_remaining_ids',
                'fulfilled_ids_listed_remaining', 'unfulfilled_ids_omitted_from_remaining', 'mixed_status_ledger_ids']}}


def summarize(rows, manifest):
    if len(rows) != 192:
        raise ValueError('All planned assay rows must remain in denominator')
    groups = {effort: {arm: group_summary([r for r in rows if r['reasoning'] == effort and r['arm'] == arm])
                      for arm in ARMS} for effort in EFFORTS}
    cells = {(r['case_id'], r['reasoning'], r['arm'], r['repeat']): r for r in rows}
    if len(cells) != 192:
        raise ValueError('Duplicate/missing factorial association')
    paired = []
    repeat_concordance = []
    for case in manifest['assay_records']:
        for effort in EFFORTS:
            differences = []
            for repeat in [1, 2]:
                left = cells[(case['instance_id'], effort, ARMS[0], repeat)]
                right = cells[(case['instance_id'], effort, ARMS[1], repeat)]
                differences.append(int(left['agreement_with_dataset_unfinished_obligation_label']) - int(right['agreement_with_dataset_unfinished_obligation_label']))
            paired.append({'case_id': case['instance_id'], 'task_cluster': case['normalized_task_cluster_sha256'],
                           'reasoning': effort, 'mean_assigned_order_agreement_difference': sum(differences) / 2})
            for arm in ARMS:
                x, y = [cells[(case['instance_id'], effort, arm, rep)] for rep in [1, 2]]
                repeat_concordance.append({'case_id': case['instance_id'], 'reasoning': effort, 'arm': arm,
                    'both_valid': x['valid'] and y['valid'],
                    'same_binary_prediction': (x['predicted_nonempty'] == y['predicted_nonempty']) if x['valid'] and y['valid'] else None})
    clusters = defaultdict(list)
    for pair in paired:
        clusters[(pair['reasoning'], pair['task_cluster'])].append(pair['mean_assigned_order_agreement_difference'])
    return {'endpoint_name': 'agreement with dataset unfinished-obligation label', 'by_reasoning_and_order': groups,
            'casewise_assigned_order_differences': paired, 'repeat_binary_concordance': repeat_concordance,
            'task_cluster_means': [{'reasoning': e, 'task_cluster': c, 'mean_agreement_difference': sum(v) / len(v)} for (e, c), v in sorted(clusters.items())],
            'original_assay_rows': 24, 'distinct_normalized_task_clusters': len({r['task_cluster'] for r in rows}),
            'caveat': 'Nonempty wrong/nonsense duty lists can agree with positive labels. No semantic duty correctness, full ledger truth, trained guard accuracy or unseen benchmark claim.'}


def main():
    import tiktoken
    output = destination()
    encoding = tiktoken.get_encoding('o200k_base')
    cases, smoke, source_prompt, manifest, plans, preflight = validate(CFG, encoding)
    by_id = {c['instance_id']: c for c in cases + [smoke]}
    smoke_plan, assay_plan = plans
    save(output / 'preflight.json', preflight)
    save(output / 'frozen-selection-manifest.json', manifest)
    save(output / 'frozen-request-plan.json', {'smoke': smoke_plan, 'assay': assay_plan})
    shutil.copy2(ROOT / 'natural-protocol.md', output / 'protocol.md')
    save(output / 'source-provenance.json', {'source_sha256': manifest['source_sha256'],
        'source_revision': manifest['source_revision'], 'selection_manifest_sha256': sha256((ROOT / 'natural-manifest.json').read_bytes()),
        'protocol_sha256': sha256((ROOT / 'natural-protocol.md').read_bytes()),
        'published_prompt_sha256': manifest['published_prompt_sha256'], 'standalone_source_dataset_file_copied': False})
    print(json.dumps({'event': 'natural_preflight', **preflight}), flush=True)
    # No credential read occurs until all source, plan, structural and wire/token checks pass.
    api = API(output, CFG, encoding, smoke_plan + assay_plan)

    def evaluate(task):
        case = by_id[task['case_id']]
        body = request_body(case, task['arm'], task['reasoning'], CFG, source_prompt)
        raw = path = provider_id = None
        error = None; fatal = False; value = None
        try:
            raw, path, provider_id = api.query(body, task)
        except Exception as exc:
            fatal = True
            error = {'kind': 'api_or_transport', 'class': type(exc).__name__}
        else:
            try:
                value = parse_response(raw, case)
            except (ValueError, TypeError) as exc:
                error = {'kind': 'full_structural_validation', 'class': type(exc).__name__}
        row = score(value, case, task)
        row.update(task=task, raw_text=raw, parsed=value, error=error, fatal_dispatch_error=fatal,
                   request_file=path, body_sha256=body_digest(body), provider_response_id=provider_id)
        save(output / 'predictions' / (task['logical_call_id'] + '.json'), row)
        return row

    smoke_rows = []
    for task in smoke_plan:
        row = evaluate(task); smoke_rows.append(row)
        save(output / 'smoke-results.json', smoke_rows)
        if row['fatal_dispatch_error'] or not row['valid'] or not row['order_compliant']:
            api.budget.abort()
            save(output / 'stopped.json', {'phase': 'smoke', 'attempts': dict(api.budget.counts),
                'reason': 'Provider/full-structure/assigned-order smoke failed; no retry or assay'})
            raise SystemExit('Natural-order smoke acceptance failed')
    rows = []
    iterator = iter(assay_plan)
    with ThreadPoolExecutor(max_workers=CFG['concurrency']) as pool:
        pending = {pool.submit(evaluate, next(iterator)): True for _ in range(CFG['concurrency'])}
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                pending.pop(future)
                row = future.result(); rows.append(row)
                if row['fatal_dispatch_error']:
                    api.budget.abort()
            if not api.budget.aborted:
                for _ in done:
                    task = next(iterator, None)
                    if task is not None:
                        pending[pool.submit(evaluate, task)] = True
            save(output / 'progress.json', {'returned_assay': len(rows), 'attempts': dict(api.budget.counts),
                                           'new_dispatch_stopped': api.budget.aborted})
    present = {r['task']['logical_call_id'] for r in rows}
    for task in assay_plan:
        if task['logical_call_id'] not in present:
            row = score(None, by_id[task['case_id']], task)
            row.update(task=task, error={'kind': 'unavailable_after_dispatch_stop'}, raw_text=None,
                       parsed=None, body_sha256=task['body_sha256'], provider_response_id=None)
            rows.append(row)
    rows.sort(key=lambda r: r['task']['logical_call_id'])
    save(output / 'all-assay-predictions.json', rows)
    result = summarize(rows, manifest)
    result.update(attempts=dict(api.budget.counts), actual_attempts=sum(api.budget.counts.values()),
                  actual_unique_provider_response_ids=len(api.response_ids), token_usage=api.tokens,
                  dispatch_stopped=api.budget.aborted, planned_assay_calls=192, planned_smoke_calls=4,
                  assay_dispatch_complete=api.budget.counts['assay'] == 192,
                  complete_valid_assay_responses=sum(r['valid'] for r in rows))
    save(output / 'summary.json', result)
    print(json.dumps({'event': 'natural_final_summary', **result}), flush=True)
    if api.budget.aborted:
        raise SystemExit('Stopped new dispatch; partial planned denominators retained; no retry')


if __name__ == '__main__':
    main()
