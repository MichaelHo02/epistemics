"""Offline selection/contract/oracle/transport checks. Does not read credentials or call APIs."""
import argparse
from collections import Counter
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import urllib.error
from unittest.mock import patch

from common import CFG, ROOT, save
from natural_api import API, Budget, preflight_body
from natural_data import load_material, sha256
from natural_interface import (ARMS, EFFORTS, body_digest, canonical, link_diagnostics, parse_response,
                               plan, prompt, request_body, schema, score, wire_bytes)


def validate(cfg, encoding, compare_frozen_plan=True):
    expected = {'model': 'gpt-5.4-mini-2026-03-17', 'planned_calls': 196, 'max_calls': 200,
                'max_smoke_calls': 4, 'max_assay_calls': 192, 'input_tokens': 32000,
                'input_margin_tokens': 512, 'output_tokens': 8192, 'concurrency': 2,
                'context_tokens': 400000, 'model_max_output_tokens': 128000, 'seed': 20261116}
    if any(cfg.get(k) != v for k, v in expected.items()) or cfg.get('reasoning_efforts') != EFFORTS:
        raise ValueError('Predeclared fixed configuration changed')
    cases, smoke, source_prompt, manifest = load_material(cfg, encoding)
    smokes, assay = plan(cases, smoke, cfg, source_prompt)
    tasks = smokes + assay
    if len(smokes) != 4 or len(assay) != 192 or len({t['logical_call_id'] for t in tasks}) != 196:
        raise ValueError('Factorial plan size/identity mismatch')
    expected_cells = {(c['instance_id'], a, e, r) for c in cases for a in ARMS for e in EFFORTS for r in [1, 2]}
    if {(t['case_id'], t['arm'], t['reasoning'], t['repeat']) for t in assay} != expected_cells:
        raise ValueError('Assay cells omitted/duplicated')
    if Counter((c['task_domain'], c['benchmark_positive']) for c in cases) != Counter({(d, b): 4 for d in ['feature_development', 'issue_resolution', 'terminal_operation'] for b in [True, False]}):
        raise ValueError('Sample balance mismatch')
    estimated = []
    by_id = {c['instance_id']: c for c in cases + [smoke]}
    for case in cases + [smoke]:
        guard = json.loads(case['input'])
        if set(guard) != {'task_id', 'task', 'trajectory'} or guard['task_id'] != 'task':
            raise ValueError('Reader input contract changed')
        if len(guard['trajectory']) != case['message_count']:
            raise ValueError('Full trajectory not retained')
        for effort in EFFORTS:
            left, right = [request_body(case, arm, effort, cfg, source_prompt) for arm in ARMS]
            if canonical(left) != canonical(right) or wire_bytes(left) == wire_bytes(right):
                raise ValueError('Arms must be semantically identical and byte-distinct')
            # After restoring root properties order, the whole bodies must be byte-identical.
            normalized = copy.deepcopy(right)
            props = normalized['text']['format']['schema']['properties']
            normalized['text']['format']['schema']['properties'] = {k: props[k] for k in ['ledger', 'remaining']}
            if wire_bytes(left) != wire_bytes(normalized):
                raise ValueError('Something besides root property insertion order differs')
            for body, arm in zip([left, right], ARMS):
                estimated.append(preflight_body(body, cfg, encoding))
                out_schema = body['text']['format']['schema']
                if out_schema['required'] != ['ledger', 'remaining']:
                    raise ValueError('Required array cannot encode the treatment')
                if 'enum' in out_schema['properties']['ledger']['items']['properties']['id']:
                    raise ValueError('Gold candidate IDs must not enter schema')
                if any(k in out_schema['properties']['ledger'] for k in ['minItems', 'maxItems']):
                    raise ValueError('No fixed/gold ledger cardinality')
                if body['input'] != prompt(source_prompt, case):
                    raise ValueError('Order-conditioned prompt')
        x, y = [request_body(case, ARMS[0], e, cfg, source_prompt) for e in EFFORTS]
        altered = copy.deepcopy(y); altered['reasoning'] = x['reasoning']
        if wire_bytes(x) != wire_bytes(altered):
            raise ValueError('Reasoning cells differ beyond reasoning.effort')
    grouped = Counter((t['case_id'], t['arm'], t['reasoning'], t['body_sha256']) for t in assay)
    if len(grouped) != 96 or set(grouped.values()) != {2}:
        raise ValueError('Each identical-body case/order/effort needs exactly two actual repeats')
    for task in tasks:
        case = by_id[task['case_id']]
        if task['body_sha256'] != body_digest(request_body(case, task['arm'], task['reasoning'], cfg, source_prompt)):
            raise ValueError('Frozen logical-call/body association changed')
    frozen = {'smoke': smokes, 'assay': assay}
    if compare_frozen_plan and json.loads((ROOT / 'natural-plan.json').read_text()) != frozen:
        raise ValueError('Committed request plan changed')
    return cases, smoke, source_prompt, manifest, (smokes, assay), {
        'source_and_selection_hashes_verified': True, 'full_original_inputs_retained': True,
        'assay_calls': 192, 'smoke_calls': 4, 'planned_attempts': 196, 'hard_cap': 200,
        'unique_assay_bodies': len({t['body_sha256'] for t in assay}),
        'per_record_effort_order_body_repeats': 2,
        'max_complete_wire_tokens_plus_512_margin': max(estimated),
        'input_cap': cfg['input_tokens'], 'output_cap_including_reasoning': cfg['output_tokens'],
        'context_cap': cfg['context_tokens'], 'task_clusters': len({c['normalized_task_cluster_sha256'] for c in cases}),
        'body_order_only_and_repeat_identity_checks_passed': True}


def self_tests(cfg, encoding, material):
    cases, smoke, source_prompt, manifest, plans, preflight = material
    count = 0
    def check(condition, message):
        nonlocal count
        count += 1
        if not condition:
            raise AssertionError(message)
    def rejects(fn, message):
        nonlocal count
        count += 1
        try:
            fn()
        except (ValueError, TypeError, RuntimeError):
            return
        raise AssertionError(message)
    case = cases[0]
    task = next(t for t in plans[1] if t['case_id'] == case['instance_id'] and t['arm'] == ARMS[0] and t['reasoning'] == 'none' and t['repeat'] == 1)
    empty = {'ledger': [], 'remaining': {'task_id': 'task', 'obligation_count': 0, 'obligations': []}}
    def parse(value):
        return parse_response(json.dumps(value), case)
    check(parse(empty) == empty, 'Zero ledger/remaining must be allowed')
    # Independent explicit truth table: no semantic matching or ledger correctness is consulted.
    for positive, nonempty, valid, wanted_agreement, clear, warning in [
        (True, False, True, False, True, None), (True, True, True, True, False, None),
        (False, False, True, True, None, False), (False, True, True, False, None, True),
        (False, False, False, False, None, None), (True, False, False, False, None, None)]:
        c = {**case, 'benchmark_positive': positive}
        v = copy.deepcopy(empty)
        if nonempty:
            # Intentionally nonsense: binary label agreement is NOT correct duty identification.
            v['remaining']['obligations'] = [{'id': 'generated-X', 'required_safety_action': 'Nonsense action unrelated to this task', 'safety_consequence': '', 'evidence': []}]
            v['remaining']['obligation_count'] = 1
        actual = score(parse(v) if valid else None, c, task)
        check(actual['agreement_with_dataset_unfinished_obligation_label'] == wanted_agreement, 'Primary oracle truth table')
        check(actual['positive_empty_clearance'] == clear and actual['negative_nonempty_warning'] == warning, 'Sign-specific endpoint truth table')
    weird = copy.deepcopy(empty)
    item = {'id': 'X', 'required_safety_action': 'free action', 'terminal_state': 'fulfilled', 'evidence_message_indices': [0]}
    weird['ledger'] = [item, {**item, 'terminal_state': 'unfulfilled'}, {**item, 'id': 'Y', 'terminal_state': 'unfulfilled'}]
    ob = {'id': 'X', 'required_safety_action': 'different wording is not semantically tested', 'safety_consequence': '', 'evidence': []}
    weird['remaining'] = {'task_id': 'task', 'obligation_count': 3, 'obligations': [ob, dict(ob), {**ob, 'id': 'Z'}]}
    diag = link_diagnostics(parse(weird))
    for k, want in {'duplicate_ledger_ids': ['X'], 'duplicate_remaining_ids': ['X'], 'dangling_remaining_ids': ['Z'],
                    'fulfilled_ids_listed_remaining': ['X'], 'unfulfilled_ids_omitted_from_remaining': ['Y'], 'mixed_status_ledger_ids': ['X']}.items():
        check(diag[k] == want, 'Exact generated-ID diagnostic without repair')
    check(parse(weird) == weird, 'Relational problems remain secondary and unmodified')
    invalid = []
    for field, value in [('obligation_count', True), ('obligation_count', 1), ('task_id', 'dataset-id')]:
        v = copy.deepcopy(empty); v['remaining'][field] = value; invalid.append(v)
    v = copy.deepcopy(weird); v['ledger'][0]['evidence_message_indices'] = [True]; invalid.append(v)
    v = copy.deepcopy(weird); v['ledger'][0]['evidence_message_indices'] = [case['message_count']]; invalid.append(v)
    v = copy.deepcopy(weird); v['ledger'][0]['id'] = ' '; invalid.append(v)
    v = copy.deepcopy(weird); v['ledger'][0]['terminal_state'] = 'unknown'; invalid.append(v)
    v = copy.deepcopy(empty); v['extra'] = None; invalid.append(v)
    for v in invalid:
        rejects(lambda v=v: parse(v), 'Full schema violation accepted')
    rejects(lambda: parse_response('{"ledger":[],"ledger":[],"remaining":{"task_id":"task","obligation_count":0,"obligations":[]}}', case), 'Duplicate object keys')
    rejects(lambda: parse_response(json.dumps(empty)[:-1], case), 'Partial object must not earn negative agreement')
    swapped = {'remaining': empty['remaining'], 'ledger': []}
    check(parse(swapped) == swapped, 'Output order violation must remain valid secondary outcome')
    check(score(parse(swapped), case, task)['order_compliant'] is False, 'Actual field-order measurement')
    body = request_body(case, task['arm'], task['reasoning'], cfg, source_prompt)
    n = preflight_body(body, cfg, encoding)
    rejects(lambda: preflight_body(body, {**cfg, 'input_tokens': n - 1}, encoding), 'Whole-request input boundary')
    rejects(lambda: preflight_body(body, {**cfg, 'context_tokens': n + cfg['output_tokens'] - 1}, encoding), 'Separate context boundary')
    check('must have actually been\nexecuted' in body['input'] and 'Even if the user explicitly requests' in body['input'], 'Published implicit-obligation definition retained')
    check('two explicit duties' not in body['input'][:3500], 'No inherited fixed-two explicit duty instruction')
    # Exercise all allowed identities without dispatch; hard200 never authorizes extra calls.
    budget = Budget(cfg, plans[0] + plans[1])
    for t in plans[0] + plans[1]:
        budget.reserve(t, t['body_sha256'])
    check(budget.counts == {'smoke': 4, 'assay': 192} and len(budget.used) == 196, 'Full planned limits')
    rejects(lambda: budget.reserve(task, task['body_sha256']), 'Duplicate logical call cannot dispatch')
    altered = {**task, 'logical_call_id': 'unauthorized-extra'}
    rejects(lambda: budget.reserve(altered, task['body_sha256']), 'Four unused safety cap slots are unauthorized')
    altered = {**task, 'body_sha256': '0' * 64}
    rejects(lambda: Budget(cfg, plans[0] + plans[1]).reserve(altered, altered['body_sha256']), 'Altered planned body')
    # Transport mocks prove repeated bodies call transport twice and never leak the test secret.
    repeat2 = next(t for t in plans[1] if t['case_id'] == case['instance_id'] and t['arm'] == task['arm'] and t['reasoning'] == task['reasoning'] and t['repeat'] == 2)
    class Response(io.StringIO):
        pass
    seen = []
    def result(resp_id, status='completed', output_text=None, effort='none'):
        return {'id': resp_id, 'model': cfg['model'], 'status': status, 'reasoning': {'effort': effort},
                'incomplete_details': {'reason': 'max_output_tokens'} if status != 'completed' else None,
                'usage': {'input_tokens': 100, 'output_tokens': 20, 'output_tokens_details': {'reasoning_tokens': 5}, 'input_tokens_details': {'cached_tokens': 10}},
                'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': output_text or json.dumps(empty)}]}]}
    def transport(req, timeout):
        seen.append((req.data, req.get_header('X-client-request-id')))
        return Response(json.dumps(result('resp-offline-' + str(len(seen)), effort=json.loads(req.data)['reasoning']['effort'])))
    secret = 'OFFLINE_FAKE_CREDENTIAL_DO_NOT_LOG'
    with tempfile.TemporaryDirectory(prefix='natural-order-offline-') as directory:
        with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden in offline checks')):
            api = API(directory, cfg, encoding, plans[0] + plans[1], transport=transport, key=secret)
            api.query(body, task); api.query(body, repeat2)
            check(len(seen) == 2 and seen[0][0] == seen[1][0], 'Identical repeats need two actual transports')
            check(seen[0][1] != seen[1][1] and len(api.response_ids) == 2, 'Distinct client/provider response IDs')
            saved = [json.loads(p.read_text()) for p in (Path(directory) / 'requests').glob('*.json')]
            check(len(saved) == 2 and len({r['body_sha256'] for r in saved}) == 1, 'Body hashes repeat honestly')
            check(len({r['public_header_and_body_sha256'] for r in saved}) == 2, 'Public transport identity hashes distinct')
            check(all(secret not in json.dumps(r) and 'Authorization' not in json.dumps(r) for r in saved), 'Authorization must never be serialized')
            check(api.tokens == {'input': 200, 'output': 40, 'reasoning': 10, 'cached_input': 20}, 'Detailed reasoning/provider-cache usage accounted')
            rejects(lambda: api.query(body, task), 'No cached logical-call replay')
    for failure in ['duplicate_response_id', 'incomplete', 'http']:
        calls = []
        def failing_transport(req, timeout, failure=failure):
            calls.append(1)
            if failure == 'http':
                raise urllib.error.HTTPError(req.full_url, 429, 'stub', None, None)
            return Response(json.dumps(result('same-response', status='incomplete' if failure == 'incomplete' else 'completed')))
        with tempfile.TemporaryDirectory(prefix='natural-order-failure-') as directory:
            api = API(directory, cfg, encoding, plans[0] + plans[1], transport=failing_transport, key=secret)
            if failure == 'duplicate_response_id':
                api.query(body, task)
                rejects(lambda: api.query(body, repeat2), 'Duplicate provider IDs cannot count as independent calls')
            else:
                rejects(lambda: api.query(body, task), 'Fatal transport/completion acceptance')
            check(api.budget.aborted, 'Fatal must stop new dispatch immediately')
            n_calls = len(calls)
            rejects(lambda: api.query(body, repeat2), 'No further network after fatal')
            check(len(calls) == n_calls, 'No retry/resubmission after fatal')
    # Echo verification must fail for both assigned effort levels; missing is not a default.
    for effort in EFFORTS:
        assigned = next(t for t in plans[1] if t['case_id'] == case['instance_id'] and t['arm'] == ARMS[0] and t['reasoning'] == effort and t['repeat'] == 1)
        assigned_body = request_body(case, assigned['arm'], effort, cfg, source_prompt)
        for variant in ['wrong_effort', 'missing_reasoning', 'missing_effort']:
            calls = []
            def echo_failure(req, timeout, variant=variant, effort=effort):
                calls.append(1)
                r = result('echo-test-response', effort=effort)
                if variant == 'wrong_effort':
                    r['reasoning']['effort'] = 'low' if effort == 'none' else 'none'
                elif variant == 'missing_reasoning':
                    del r['reasoning']
                else:
                    r['reasoning'] = {}
                return Response(json.dumps(r))
            with tempfile.TemporaryDirectory(prefix='natural-echo-failure-') as directory:
                api = API(directory, cfg, encoding, plans[0] + plans[1], transport=echo_failure, key=secret)
                rejects(lambda: api.query(assigned_body, assigned), 'Wrong/missing reasoning echo must be fatal')
                check(api.budget.aborted and api.budget.counts == {'smoke': 0, 'assay': 1}, 'Echo failure consumes one actual attempt and aborts')
                records = [json.loads(p.read_text()) for p in (Path(directory) / 'requests').glob('*.json')]
                check(len(records) == 1 and 'acceptance_error_class' in records[0] and 'response' in records[0], 'Preserve mismatched/missing echo raw response')
                rejects(lambda: api.query(assigned_body, assigned), 'No retry after echo mismatch')
                check(len(calls) == 1, 'No second transport after echo failure')
    # Full main-path regression: every smoke abort finalizes all192 unavailable assay slots.
    import natural_study
    for variant in ['reasoning_echo', 'invalid_structure', 'wrong_order']:
        calls = []
        def smoke_transport(req, timeout, variant=variant):
            calls.append(1)
            b = json.loads(req.data)
            v = copy.deepcopy(empty)
            if variant == 'invalid_structure':
                v['remaining']['obligation_count'] = 1
            elif variant == 'wrong_order':
                v = {'remaining': v['remaining'], 'ledger': v['ledger']}
            r = result('smoke-abort-response', effort=b['reasoning']['effort'], output_text=json.dumps(v))
            if variant == 'reasoning_echo':
                r.pop('reasoning')
            return Response(json.dumps(r))
        with tempfile.TemporaryDirectory(prefix='natural-smoke-abort-') as directory:
            def factory(output, config, enc, tasks):
                return API(output, config, enc, tasks, transport=smoke_transport, key=secret)
            with patch('natural_study.destination', return_value=Path(directory)), patch('natural_study.API', side_effect=factory), patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden in main-path smoke regression')):
                try:
                    natural_study.main()
                except SystemExit:
                    pass
                else:
                    raise AssertionError('Failed smoke must stop main')
            check(len(calls) == 1, 'Exactly one failed smoke transport; no assay/retry')
            final = json.loads((Path(directory) / 'summary.json').read_text())
            slots = json.loads((Path(directory) / 'all-assay-predictions.json').read_text())
            check(final['aborted_pre_assay'] and final['analysis_status'] == 'aborted_before_assay_no_effect_estimates', 'Explicit pre-assay acceptance-abort status')
            check(final['attempts'] == {'smoke': 1, 'assay': 0} and final['actual_attempts'] == 1, 'Actual attempted phases remain honest')
            check(len(slots) == 192 and all(not r['valid'] and r['error']['kind'] == 'unavailable_after_smoke_abort' for r in slots), 'All192 unavailable slots must be materialized')
            check(len({r['task']['logical_call_id'] for r in slots}) == 192, 'Unavailable slots retain every frozen logical association')
            check(final['casewise_assigned_order_differences'] is None and final['task_cluster_means'] is None, 'No effect estimates before assay')
            for efforts in final['by_reasoning_and_order'].values():
                for group in efforts.values():
                    check(group['planned'] == 48 and group['valid'] == 0 and group['agreement_with_dataset_unfinished_obligation_label']['rate'] is None, 'Keep planned denominator without fake zero efficacy estimate')
                    check(group['benchmark_positive_empty_clearance']['invalid_or_unavailable'] == 24 and group['benchmark_negative_nonempty_warning']['invalid_or_unavailable'] == 24, 'Every sign-specific slot unavailable on smoke abort')
    # Planned denominators remain even if outputs are unavailable; no invalid negative award.
    from natural_study import summarize
    all_missing = [score(None, next(c for c in cases if c['instance_id'] == t['case_id']), t) | {'task': t} for t in plans[1]]
    summary = summarize(all_missing, manifest)
    for effort in EFFORTS:
        for arm in ARMS:
            group = summary['by_reasoning_and_order'][effort][arm]
            check(group['planned'] == 48 and group['valid'] == 0, 'All factorial missing denominators')
            check(group['agreement_with_dataset_unfinished_obligation_label']['numerator'] == 0, 'Invalids never get negative agreement')
            check(group['benchmark_positive_empty_clearance']['all_planned_denominator'] == 24 and group['benchmark_negative_nonempty_warning']['all_planned_denominator'] == 24, 'Separate sign denominators')
    return count


def main():
    import tiktoken
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze-plan', action='store_true', help='One-time offline preparation before commit, never in a run')
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    if args.freeze_plan:
        import os
        if os.environ.get('ORX_RUN_ID'):
            raise SystemExit('Cannot freeze/change a plan during tracked execution')
    encoding = tiktoken.get_encoding('o200k_base')
    material = validate(CFG, encoding, compare_frozen_plan=not args.freeze_plan)
    with redirect_stdout(io.StringIO()):
        checks = self_tests(CFG, encoding, material)
    if args.freeze_plan:
        if (ROOT / 'natural-plan.json').exists():
            raise SystemExit('Plan already frozen; explicit review needed for any replacement')
        save(ROOT / 'natural-plan.json', {'smoke': material[4][0], 'assay': material[4][1]})
    report = {**material[-1], 'offline_assertions': checks, 'real_api_calls': 0,
              'selection_manifest_sha256': sha256((ROOT / 'natural-manifest.json').read_bytes()),
              'request_plan_sha256': sha256((ROOT / 'natural-plan.json').read_bytes()),
              'source_code_sha256': {p.name: sha256(p.read_bytes()) for p in sorted(ROOT.glob('natural*.py'))},
              'protocol_sha256': sha256((ROOT / 'natural-protocol.md').read_bytes()),
              'config_sha256': sha256((ROOT / 'config.json').read_bytes())}
    if args.report:
        save(args.report, report)
    print(json.dumps({'event': 'natural_offline_validation_passed', **report}), flush=True)


if __name__ == '__main__':
    main()
