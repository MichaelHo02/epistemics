"""Mandatory executed-fixture and request/scoring preflight, no API or credential access."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import sys
import threading
from contextlib import redirect_stdout
from unittest.mock import patch

from common import CFG, ROOT
from order_api import API, Budget
from order_interface import ARMS, canonical, parse_response, request_body, request_digest, wire_bytes
from structural_cases import make_cases, manifest, smoke_case
from structural_fixture import FAMILIES, build, visible_checker
from structural_metrics import scored, summarize
from structural_oracle import inspect


def validate_fixtures(records):
 assert len(records) == 16
 prefix_hashes = {}
 checks = []
 for r in records:
  f, state = r['family'], r['state']
  raw = inspect(f, r['root'])
  assert raw['pending'] == [not state[0], not state[1]]
  assert raw['deliverable_preserved']
  visible = visible_checker(f, r['events'])
  assert visible == {k: raw[k] for k in visible}
  digest = hashlib.sha256(canonical(r['events'][:r['prefix_events']]).encode()).hexdigest()
  assert prefix_hashes.setdefault(f['id'], digest) == digest
  checks.append({'family': f['id'], 'relation': f['kind'], 'intervention_expected': state,
                 'independent_raw_state': raw, 'visible_checker': visible, 'prefix_sha256': digest})
 for f in FAMILIES:
  group = [r for r in records if r['family']['id'] == f['id']]
  assert len(group) == 4
  for a in group:
   for b in group:
    for idx in [0, 1]:
     if a['state'][idx] == b['state'][idx]:
      assert inspect(f, a['root'])['pending'][idx] == inspect(f, b['root'])['pending'][idx]
 # Relation-specific checks prevent flattening new tasks into successful cleanup flags.
 for r in records:
  f, e = r['family'], r['events']
  ops = [x['operation'] for x in e]
  if f['kind'] == 'transaction':
   assert ops.count('begin_transaction') == 2
   assert ops.count('commit_transaction') == sum(r['state'])
   assert ops.count('rollback_transaction') == 2 - sum(r['state'])
   assert all(x['result']['rows_changed'] == 1 for x in e if x['operation'] in ['delete_grant', 'delete_key_material'])
  if f['kind'] == 'regrant':
   assert 'grant_permission' in ops if not r['state'][0] else 'grant_permission' not in ops
   assert 'restore_material_from_local_seed' in ops if not r['state'][1] else 'restore_material_from_local_seed' not in ops
   assert any(x['operation'] == 'request_authorization' and x['result']['decision'] == 'reject' for x in e)
  if f['kind'] == 'binding':
   action = next(x for x in e if x['operation'] == 'delete_grant')
   assert action['arguments']['scope'] == ('publish' if r['state'][0] else 'inspect')
   assert action['result']['rows_changed'] == 1
   action = next(x for x in e if x['operation'] == 'delete_key_material')
   assert action['arguments']['key_name'] == ('approval' if r['state'][1] else 'preview')
   assert action['result']['rows_changed'] == 1
  if f['kind'] == 'baseline':
   updates = [x for x in e if x['operation'] == 'replace_acl']
   assert len(updates) == 2
   for index, update in enumerate(updates):
    assert bool(update['result']['installed_permissions']) == r['state'][index]
 # Negative controls on disposable copies, never alter the actual fixture branches.
 target = records[0]
 with tempfile.TemporaryDirectory(prefix='structural-negative-') as temp:
  path = Path(temp) / 'copy'
  shutil.copytree(target['root'], path)
  (path / 'deliverable.md').unlink()
  assert not inspect(target['family'], path)['deliverable_preserved']
 with tempfile.TemporaryDirectory(prefix='structural-independent-') as temp:
  path = Path(temp) / 'copy'
  shutil.copytree(target['root'], path)
  with sqlite3.connect(path / 'authority.sqlite') as db:
   db.execute('DELETE FROM grants WHERE principal=? AND scope=?', ('publisher', 'publish'))
  altered = inspect(target['family'], path)
  assert altered['pending'] == [False, True]
  assert altered['remaining'] != visible_checker(target['family'], target['events'])['remaining']
 return checks


def scoring_checks(cases, tasks):
 by_id = {c['case_id']: c for c in cases}
 perfect = []; unavailable = []; contradictory = []
 for task in tasks:
  c = by_id[task['case_id']]
  truth = inspect(c['record']['family'], c['record']['root'])
  ids = [d['id'] for d in json.loads(c['observations'])['requirements']['explicit_duties']]
  fields = request_body(c, task['arm'], CFG, task['reasoning'])['text']['format']['schema']['properties']
  values = {'ledger': [{'duty_id': d, 'terminal_state': 'unfulfilled' if d in truth['remaining'] else 'fulfilled',
                        'evidence_receipts': []} for d in ids],
            'remaining': truth['remaining'], 'deliverable_preserved': True, 'evidence_receipts': []}
  ordered = {k: values[k] for k in fields}
  value = parse_response(json.dumps(ordered), c)
  reversed_fields = {k: ordered[k] for k in reversed(list(ordered))}
  violation = scored(parse_response(json.dumps(reversed_fields), c), truth, task, c)
  assert violation['valid'] and violation['exact_remaining'] and not violation['order_compliant']
  perfect.append(scored(value, truth, task, c))
  unavailable.append(scored(None, truth, task, c))
  wrong = deepcopy(ordered)
  wrong['remaining'] = [] if truth['remaining'] else [ids[0]]
  wrong = parse_response(json.dumps(wrong), c)
  row = scored(wrong, truth, task, c)
  assert row['inconsistent'] and not row['exact_remaining'] and row['ledger_exact'] and not row['gate_covered']
  contradictory.append(row)
  # Full validator negative cases: missing/extra fields, invalid status/ref, duplicate duty/key.
  invalid = deepcopy(ordered); invalid['ledger'][0]['terminal_state'] = 'notfulfilled'
  invalid_ref = deepcopy(ordered); invalid_ref['ledger'][0]['evidence_receipts'] = ['agent_final_report']
  duplicate = deepcopy(ordered); duplicate['ledger'][1]['duty_id'] = duplicate['ledger'][0]['duty_id']
  missing = deepcopy(ordered); missing.pop('ledger')
  extra = deepcopy(ordered); extra['extra'] = True
  unknown_id = deepcopy(ordered); unknown_id['remaining'] = ['not-a-duty']
  duplicate_remaining = deepcopy(ordered); duplicate_remaining['remaining'] = [ids[0],ids[0]]
  wrong_type = deepcopy(ordered); wrong_type['deliverable_preserved'] = 'true'
  for bad in [invalid, invalid_ref, duplicate, missing, extra,unknown_id,duplicate_remaining,wrong_type]:
   try: parse_response(json.dumps(bad), c)
   except ValueError: pass
   else: raise AssertionError('Malformed full response accepted')
  try: parse_response(json.dumps(ordered)[:-1] + ',"remaining":[]}', c)
  except ValueError: pass
  else: raise AssertionError('Duplicate JSON key accepted')
 for rows, correct, unknown in [(perfect, 1, False), (unavailable, 0, True)]:
  result = summarize(rows)
  for reason in CFG['reasoning_levels']:
   for arm in ARMS:
    stats = result['by_reasoning'][reason]['arms'][arm]
    assert stats['exact']['rate'] == correct
    assert stats['false_clearance']['bounds'] == ([0, 1] if unknown else [0, 0])
    assert stats['false_warning_completed']['bounds'] == ([0, 1] if unknown else [0, 0])
 result = summarize(contradictory)
 for reason in CFG['reasoning_levels']:
  for arm in ARMS:
   s = result['by_reasoning'][reason]['arms'][arm]
   assert s['false_clearance']['bounds'] == [1, 1] and s['false_warning_completed']['bounds'] == [1, 1]
   assert s['consistency_gate_covered'] == 0 and s['ledger_projection_exact'] == 64


def validate(cases, smoke, records, write=False):
 checks = validate_fixtures(records)
 assert len(cases) == 32 and len({c['case_id'] for c in cases}) == 32
 assert Counter((c['record']['family']['id'], tuple(c['record']['state']), c['report']) for c in cases) == {
  (f['id'], state, report): 1 for f in FAMILIES for state in [(False,False),(True,False),(False,True),(True,True)]
  for report in ['accurate', 'blanket_clearance']}
 for c in cases + [smoke]:
  obs = json.loads(c['observations'])
  assert set(obs) == {'case', 'requirements', 'execution_record', 'agent_final_report'}
  assert len(obs['requirements']['explicit_duties']) == 2
  for reason in CFG['reasoning_levels']:
   a, b = [request_body(c, arm, CFG, reason) for arm in ARMS]
   assert a['input'] == b['input'] and canonical(a) == canonical(b)
   assert wire_bytes(a) != wire_bytes(b) and request_digest(a) != request_digest(b)
   sa, sb = [x['text']['format']['schema'] for x in [a,b]]
   assert sa['required'] == sb['required'] == ['ledger','remaining','deliverable_preserved','evidence_receipts']
   for field in sa['properties']:
    assert wire_bytes(sa['properties'][field]) == wire_bytes(sb['properties'][field])
   ca, cb = deepcopy(a), deepcopy(b)
   ca['text']['format']['schema'].pop('properties'); cb['text']['format']['schema'].pop('properties')
   assert wire_bytes(ca) == wire_bytes(cb)
   assert a['reasoning']['effort'] == reason and a['max_output_tokens'] == 8192
   assert len(wire_bytes(a)) + 256 <= CFG['input_tokens'], 'Conservative byte upper bound exceeded'
  none_body=request_body(c,'ledger_first',CFG,'none')
  low_body=request_body(c,'ledger_first',CFG,'low')
  none_body['reasoning']=low_body['reasoning']
  assert wire_bytes(none_body)==wire_bytes(low_body), 'Reasoning comparison changed more than effort'
 frozen = manifest(cases, smoke, CFG)
 assert frozen == manifest(cases, smoke, CFG)
 tasks = frozen['dispatch']['assay']; smokes = frozen['dispatch']['smoke']
 assert len(tasks) == 256 and len(smokes) == 4
 assert len({t['logical_call_id'] for t in tasks+smokes}) == 260
 assert Counter((t['case_id'],t['arm'],t['reasoning'],t['replicate']) for t in tasks) == {
  (c['case_id'],arm,reason,rep): 1 for c in cases for arm in ARMS for reason in ['none','low'] for rep in [0,1]}
 assert Counter((t['arm'],t['reasoning']) for t in smokes) == {(a,r):1 for a in ARMS for r in ['none','low']}
 assert smoke['case_id'] not in {c['case_id'] for c in cases}
 by_id = {c['case_id']:c for c in cases+[smoke]}
 hashes = [request_digest(request_body(by_id[t['case_id']],t['arm'],CFG,t['reasoning'])) for t in tasks]
 assert len(set(hashes)) == 128 and set(Counter(hashes).values()) == {2}
 # Distinct logical calls repeat identical bodies without nonce, idempotency or local cache.
 scoring_checks(cases,tasks)
 transport_checks(cases[0])
 budget = Budget(CFG['max_calls'],CFG['max_smoke_calls'],CFG['max_assay_calls'])
 def reserve(phase):
  try: return budget.reserve(phase)
  except RuntimeError: return None
 with ThreadPoolExecutor(max_workers=16) as pool:
  reservations=list(pool.map(reserve,['smoke']*20+['assay']*300))
 accepted=[x for x in reservations if x is not None]
 assert len(accepted)==len(set(accepted))==260 and budget.counts=={'smoke':4,'assay':256}
 assert CFG['max_calls']==272 and CFG['concurrency']==2 and CFG['repeats']==2
 if write: (ROOT/'structural-manifest.json').write_text(json.dumps(frozen,indent=2)+'\n')
 else: assert frozen==json.loads((ROOT/'structural-manifest.json').read_text()), 'Frozen structural manifest mismatch'
 return checks,frozen


def transport_checks(case):
 """Injected offline transport, isolated temporary logs; never invokes a provider or reads a key."""
 class ByteEncoding:
  def encode(self,text): return list(text.encode())
 def client(folder):
  api=API.__new__(API)
  api.output=Path(folder); api.cfg=CFG; api.encoding=ByteEncoding()
  api.budget=Budget(CFG['max_calls'],CFG['max_smoke_calls'],CFG['max_assay_calls'])
  api.tokens={'input':0,'output':0,'reasoning':0}; api.lock=threading.Lock()
  api.key='OFFLINE-UNIT-TEST-ONLY'
  return api
 for fault in [None,'incomplete','wrong_model','wrong_reasoning']:
  with tempfile.TemporaryDirectory(prefix='structural-mock-transport-') as temp:
   api=client(temp); captured=[]
   def fake_urlopen(req,timeout):
    assert timeout==120
    captured.append(req.data)
    body=json.loads(req.data)
    effort=body['reasoning']['effort']
    result={'status':'incomplete' if fault=='incomplete' else 'completed',
            'model':'wrong-model' if fault=='wrong_model' else CFG['model'],
            'reasoning':{'effort':('low' if effort=='none' else 'none') if fault=='wrong_reasoning' else effort},
            'usage':{'input_tokens':50,'output_tokens':10,'output_tokens_details':{'reasoning_tokens':3}},
            'output':[{'type':'message','content':[{'type':'output_text','text':'OFFLINE TRANSPORT TEST'}]}]}
    return io.BytesIO(json.dumps(result).encode())
   with patch('order_api.urllib.request.urlopen',side_effect=fake_urlopen),redirect_stdout(io.StringIO()):
    if fault is None:
     for reason in ['none','low']:
      for arm in ARMS:
       body=request_body(case,arm,CFG,reason)
       task={'phase':'assay','case_id':case['case_id'],'arm':arm,'reasoning':reason}
       api.query(body,task)
       assert captured[-1]==wire_bytes(body)
     assert len(captured)==4 and len(set(captured))==4
     assert api.budget.counts=={'smoke':0,'assay':4} and api.tokens['reasoning']==12
    else:
     body=request_body(case,'ledger_first',CFG,'none')
     task={'phase':'assay','case_id':case['case_id'],'arm':'ledger_first','reasoning':'none'}
     try: api.query(body,task)
     except RuntimeError: pass
     else: raise AssertionError('Fatal provider status/model/reasoning mismatch accepted')
     assert len(captured)==1 and api.budget.counts['assay']==1, 'Unexpected retry'


if __name__=='__main__':
 with tempfile.TemporaryDirectory(prefix='structural-preflight-') as temp:
  records=build(Path(temp)/'fixtures')
  cases=make_cases(records); smoke=smoke_case(Path(temp)/'smoke')
  checks,frozen=validate(cases,smoke,records,'--write-manifest' in sys.argv)
  print(json.dumps({'event':'structural_offline_validation','families':4,'executed_states':16,'cases':32,
   'assay':256,'smoke':4,'hard_cap':272,'phase_cap_total':260,'all_checks':'passed',
   'manifest_sha256':hashlib.sha256(canonical(frozen).encode()).hexdigest()}))

