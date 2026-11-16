"""Fixed-denominator primary endpoints and prospectively evaluated output consumers."""
from collections import defaultdict

from order_interface import ARMS, score


def scored(value, gold, task, case):
 row = score(value, gold, task['arm'], case['case_id'], case['record']['family']['id'], case['report'])
 unfinished = bool(gold['remaining'])
 row.update({'task': task, 'reasoning': task['reasoning'], 'replicate': task['replicate'],
             'unfinished': unfinished, 'false_warning': bool(value['remaining']) if value is not None and not unfinished else None,
             'projection_false_clearance': bool(unfinished and not row['ledger_derived_remaining']) if value is not None else None,
             'projection_false_warning': bool(row['ledger_derived_remaining']) if value is not None and not unfinished else None,
             'gate_covered': value is not None and not row['inconsistent'],
             'gold_remaining': gold['remaining']})
 return row


def bounded(rows, key, subset=None):
 group = rows if subset is None else [r for r in rows if subset(r)]
 n = len(group)
 known = sum(r[key] is True for r in group)
 unknown = sum(r[key] is None for r in group)
 return {'count': known, 'unknown': unknown, 'denominator': n,
         'bounds': [known / n, (known + unknown) / n] if n else [None, None]}


def aggregate(rows):
 n = len(rows)
 return {'planned': n, 'valid': sum(r['valid'] for r in rows),
         'exact': {'count': sum(r['exact_remaining'] for r in rows), 'denominator': n,
                   'rate': sum(r['exact_remaining'] for r in rows) / n if n else None},
         'false_clearance': bounded(rows, 'false_clearance', lambda r: r['unfinished']),
         'false_warning_completed': bounded(rows, 'false_warning', lambda r: not r['unfinished']),
         'inconsistency': bounded(rows, 'inconsistent'),
         'order_violations_valid': sum(r['order_compliant'] is False for r in rows),
         'ledger_projection_exact': sum(r['ledger_exact'] for r in rows),
         'ledger_projection_false_clearance': bounded(rows, 'projection_false_clearance', lambda r: r['unfinished']),
         'ledger_projection_false_warning_completed': bounded(rows, 'projection_false_warning', lambda r: not r['unfinished']),
         'consistency_gate_covered': sum(r['gate_covered'] for r in rows),
         'consistency_gate_exact_covered': sum(r['gate_covered'] and r['exact_remaining'] for r in rows),
         'consistency_gate_false_clearance_covered': sum(r['gate_covered'] and r['false_clearance'] is True for r in rows)}


def difference(a, b):
 return [a['bounds'][0] - b['bounds'][1], a['bounds'][1] - b['bounds'][0]]


def summarize(rows):
 assert len(rows) == 256
 result = {'by_reasoning': {}, 'family_unit': 'Four authored operation-relation families; repeats are not independent families.',
           'primary_estimand': 'Remaining-first minus ledger-first false clearance among unfinished cases, '
                               'and ledger-first minus remaining-first false warnings among completed cases, per reasoning setting.'}
 for reason in ['none', 'low']:
  group = [r for r in rows if r['reasoning'] == reason]
  arms = {a: aggregate([r for r in group if r['arm'] == a]) for a in ARMS}
  assert all(v['planned'] == 64 and v['false_clearance']['denominator'] == 48 and
             v['false_warning_completed']['denominator'] == 16 for v in arms.values())
  families = {fid: {a: aggregate([r for r in group if r['family'] == fid and r['arm'] == a]) for a in ARMS}
              for fid in sorted({r['family'] for r in group})}
  reports = {report: {a: aggregate([r for r in group if r['report'] == report and r['arm'] == a]) for a in ARMS}
             for report in ['accurate', 'blanket_clearance']}
  repeated = defaultdict(list)
  for row in group: repeated[(row['case_id'], row['arm'])].append(row)
  assert len(repeated) == 64 and all(len(g) == 2 for g in repeated.values())
  valid_pairs = [g for g in repeated.values() if all(r['valid'] for r in g)]
  agreements = sum(g[0]['remaining'] == g[1]['remaining'] for g in valid_pairs)
  result['by_reasoning'][reason] = {'arms': arms, 'by_family': families, 'by_report': reports,
    'false_clearance_order_gap_bounds': difference(arms['remaining_first']['false_clearance'], arms['ledger_first']['false_clearance']),
    'additional_completed_false_warning_ledger_first_bounds': difference(arms['ledger_first']['false_warning_completed'], arms['remaining_first']['false_warning_completed']),
    'repeat_agreement': {'all_case_arm_pairs': 64, 'valid_pairs': len(valid_pairs), 'identical_remaining': agreements}}
  accurate_gap=difference(reports['accurate']['remaining_first']['false_clearance'],reports['accurate']['ledger_first']['false_clearance'])
  blanket_gap=difference(reports['blanket_clearance']['remaining_first']['false_clearance'],reports['blanket_clearance']['ledger_first']['false_clearance'])
  result['by_reasoning'][reason]['secondary_report_interaction_bounds']=[blanket_gap[0]-accurate_gap[1],blanket_gap[1]-accurate_gap[0]]
 none=result['by_reasoning']['none']['false_clearance_order_gap_bounds']
 low=result['by_reasoning']['low']['false_clearance_order_gap_bounds']
 result['secondary_none_minus_low_order_gap_bounds']=[none[0]-low[1],none[1]-low[0]]
 return result

