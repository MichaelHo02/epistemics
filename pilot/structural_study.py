"""Tracked structural validation, 256 fixed assay cells plus four provider smoke calls."""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
from pathlib import Path
import shutil

from common import CFG, ROOT, destination, save
from oracle import inspect as smoke_oracle
from order_api import API
from order_interface import parse_response, request_body, request_digest, wire_bytes
from structural_cases import make_cases, smoke_case
from structural_fixture import build
from structural_metrics import scored, summarize
from structural_oracle import inspect
from structural_validate import validate


def main():
 import tiktoken
 output = destination()
 records = build(output / 'fixtures')
 cases = make_cases(records)
 smoke = smoke_case(output / 'provider-smoke-fixture')
 checks, frozen = validate(cases, smoke, records)
 save(output / 'independent-state-checks.json', checks)
 save(output / 'frozen-manifest.json', frozen)
 shutil.copy2(ROOT / 'structural-protocol.md', output / 'protocol.md')
 by_id = {c['case_id']: c for c in cases + [smoke]}
 truths = {c['case_id']: inspect(c['record']['family'], c['record']['root']) for c in cases}
 truths[smoke['case_id']] = smoke_oracle(smoke['record']['family'], smoke['record']['root'])
 for cid, case in by_id.items():
  save(output / 'cases' / (cid + '.json'), {'observations': json.loads(case['observations']),
       'independent_gold': truths[cid], 'family': case['record']['family']['id'],
       'state': case['record']['state'], 'report': case['report']})
 encoding = tiktoken.get_encoding('o200k_base')
 token_checks = []
 for task in frozen['dispatch']['smoke'] + frozen['dispatch']['assay']:
  body = request_body(by_id[task['case_id']], task['arm'], CFG, task['reasoning'])
  estimate = len(encoding.encode(wire_bytes(body).decode())) + 256
  assert estimate <= CFG['input_tokens']
  token_checks.append({'logical_call_id': task['logical_call_id'], 'wire_sha256': request_digest(body),
                       'wire_tokens_plus_256_margin': estimate})
 save(output / 'request-token-checks.json', token_checks)
 print(json.dumps({'event': 'structural_preflight', 'families': 4, 'cases': 32, 'assay': 256,
                   'smoke': 4, 'hard_total_cap': 272, 'phase_total_cap': 260,
                   'max_wire_tokens_plus_margin': max(t['wire_tokens_plus_256_margin'] for t in token_checks),
                   'reasoning_levels': CFG['reasoning_levels'], 'output_cap_both': 8192,
                   'deterministic_visible_checker': [32, 32]}), flush=True)
 api = API(output, CFG, encoding)

 def evaluate(task):
  case = by_id[task['case_id']]
  body = request_body(case, task['arm'], CFG, task['reasoning'])
  raw = path = None
  value = None
  fatal = False
  error = None
  try:
   raw, path = api.query(body, task)
  except Exception as exc:
   fatal = True
   error = {'kind': 'provider_transport_status_model_config_or_budget', 'class': type(exc).__name__}
  else:
   try: value = parse_response(raw, case)
   except (ValueError, TypeError) as exc:
    error = {'kind': 'full_response_structure', 'class': type(exc).__name__}
  row = scored(value, truths[case['case_id']], task, case)
  row.update({'raw_text': raw, 'parsed': value, 'request_file': path, 'error': error,
              'fatal_dispatch_error': fatal, 'wire_sha256': request_digest(body)})
  save(output / 'predictions' / (task['logical_call_id'] + '.json'), row)
  return row

 stopped = False
 smoke_rows = []
 for task in frozen['dispatch']['smoke']:
  row = evaluate(task)
  smoke_rows.append(row)
  save(output / 'smoke-results.json', smoke_rows)
  # Provider acceptance only: no accuracy or internal-consistency gate.
  if row['fatal_dispatch_error'] or not row['valid'] or not row['order_compliant']:
   stopped = True
   save(output / 'stopped.json', {'phase': 'smoke', 'reason': 'Provider/status/config/structure/order acceptance failed',
                                 'no_retry': True})
   break
 if not stopped:
  print(json.dumps({'event': 'provider_smoke_passed', 'attempts': 4,
                    'settings': ['ledger_first/none', 'remaining_first/none', 'ledger_first/low', 'remaining_first/low'],
                    'accuracy_gate': False}), flush=True)
 rows = []
 if not stopped:
  iterator = iter(frozen['dispatch']['assay'])
  with ThreadPoolExecutor(max_workers=CFG['concurrency']) as pool:
   pending = {pool.submit(evaluate, next(iterator)): True for _ in range(CFG['concurrency'])}
   while pending:
    done, _ = wait(pending, return_when=FIRST_COMPLETED)
    for future in done:
     pending.pop(future)
     row = future.result()
     rows.append(row)
     if row['fatal_dispatch_error']: stopped = True
    if not stopped:
     for _ in done:
      task = next(iterator, None)
      if task is not None: pending[pool.submit(evaluate, task)] = True
    save(output / 'progress.json', {'returned_assay': len(rows), 'attempts': dict(api.budget.counts),
                                    'dispatch_stopped': stopped, 'token_usage': dict(api.tokens)})
 # Retain every fixed assay cell even if smoke or later dispatch failed.
 present = {r['task']['logical_call_id'] for r in rows}
 for task in frozen['dispatch']['assay']:
  if task['logical_call_id'] not in present:
   c = by_id[task['case_id']]
   row = scored(None, truths[c['case_id']], task, c)
   row.update({'error': {'kind': 'not_dispatched_after_stop'}, 'raw_text': None, 'parsed': None})
   rows.append(row)
 rows.sort(key=lambda r: r['task']['logical_call_id'])
 save(output / 'all-assay-predictions.json', rows)
 result = summarize(rows)
 result.update({'attempts': dict(api.budget.counts), 'total_attempts': sum(api.budget.counts.values()),
                'token_usage': dict(api.tokens), 'dispatch_stopped': stopped,
                'completed': api.budget.counts == {'smoke': 4, 'assay': 256} and not stopped,
                'deterministic_same_observation_exact': [32, 32], 'provider_smoke_separate': True})
 save(output / 'summary.json', result)
 print(json.dumps({'event': 'final_metrics', **result}), flush=True)
 if stopped: raise SystemExit('Dispatch stopped after acceptance/provider failure; no retry; fixed-denominator outputs retained')


if __name__ == '__main__':
 main()

