"""Lightweight preflight: executed fixtures, independent oracle, and frozen input hashes."""
import hashlib
import json
from pathlib import Path
import tempfile
import sys

from cases import METHODS, make_cases, manifest, prompt
from fixture import FAMILIES, build, observed_checker
from oracle import inspect

ROOT = Path(__file__).resolve().parent


def validate_records(records):
    prefix_digests = {}
    checks = []
    for rec in records:
        f, state = rec['family'], rec['state']
        gold = inspect(f, rec['root'])
        assert gold['access_pending'] is not state[0]
        assert gold['signing_pending'] is not state[1]
        assert gold['deliverable_preserved']
        visible = observed_checker(f, rec['events'])
        assert visible == {k: gold[k] for k in visible}
        prefix = rec['events'][:rec['prefix_events']]
        digest = hashlib.sha256(json.dumps(prefix, sort_keys=True).encode()).hexdigest()
        assert prefix_digests.setdefault(f['id'], digest) == digest
        checks.append({'family': f['id'], 'state': state, 'sham': rec['sham'],
                       'prefix_sha256': digest, 'raw_state': gold, 'visible_checker': visible})
    assert len(prefix_digests) == 6
    # Verify changing only one duty leaves the other oracle component invariant.
    for f in FAMILIES:
        for sham in [False, True]:
            group = [r for r in records if r['family']['id'] == f['id'] and r['sham'] == sham]
            for a in group:
                for b in group:
                    sa, sb = a['state'], b['state']
                    if sa[1] == sb[1]:
                        assert inspect(f, a['root'])['signing_pending'] == inspect(f, b['root'])['signing_pending']
                    if sa[0] == sb[0]:
                        assert inspect(f, a['root'])['access_pending'] == inspect(f, b['root'])['access_pending']
    return checks


def main():
    with tempfile.TemporaryDirectory(prefix='completion-check-') as temp:
        records = build(Path(temp) / 'fixtures')
        checks = validate_records(records)
        cases = make_cases(records)
        assert len(cases) == 96
        assert len({c['case_id'] for c in cases}) == 96
        assert all(len(c['observations'].encode()) < 16000 for c in cases)
        planned = len(cases) * len(METHODS)
        assert planned == 192
        # Exercise scoring independently of model outputs: oracle predictions must be
        # perfect, always-clear must fail unfinished states, always-warn must flag
        # already completed duties, and a valid ledger must flip exactly one duty.
        from study import parse_response, score, summarize
        oracle_rows = []
        for case in cases:
            visible = observed_checker(case['record']['family'], case['record']['events'])
            for method in METHODS:
                value = parse_response(json.dumps(visible), case['record']['family'])
                oracle_rows.append(score(case, method, value))
            clear = score(case, 'direct_trace', {'remaining': [], 'deliverable_preserved': True})
            assert clear['false_clearance'] == bool(visible['remaining'])
            warn = score(case, 'direct_trace', {'remaining': case['record']['family']['order'],
                                              'deliverable_preserved': True})
            assert warn['false_positive_case'] == (len(visible['remaining']) < 2)
        metric_check = summarize(oracle_rows, cases)
        assert metric_check['primary_ledger_minus_direct_family_mean_exact'] == 0
        for method in METHODS:
            assert metric_check['methods'][method]['exact_remaining']['rate'] == 1
            paired = metric_check['paired_state_diagnostics'][method]
            assert paired['completed_duty_transition_sensitivity']['rate'] == 1
            assert paired['other_duty_spillover_valid_pairs']['rate'] == 0
            assert paired['four_state_exact_consistency']['rate'] == 1
        found = manifest(cases)
        if '--write-manifest' in sys.argv:
            (ROOT / 'manifest.json').write_text(json.dumps(found, indent=2) + '\n')
        else:
            assert found == json.loads((ROOT / 'manifest.json').read_text()), 'Frozen manifest mismatch'
        # Deliberately destroy one output: independently verify preservation assertion catches it.
        target = records[0]
        deliverable = Path(target['root']) / target['family']['deliverable']
        deliverable.unlink()
        assert not inspect(target['family'], target['root'])['deliverable_preserved']
        # No model call or API credential access during this check.
        print(json.dumps({'event': 'fixture_validation', 'families': 6, 'executed_states': len(checks),
                          'cases': len(cases), 'planned_attempts': planned,
                          'prefix_checks': 'passed', 'orthogonality_checks': 'passed',
                          'raw_state_vs_visible_checks': 'passed', 'preservation_negative_control': 'passed',
                          'metric_negative_and_positive_controls': 'passed',
                          'manifest_sha256': hashlib.sha256(json.dumps(found, sort_keys=True).encode()).hexdigest()}))


if __name__ == '__main__':
    main()

