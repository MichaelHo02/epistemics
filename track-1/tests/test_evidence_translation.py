import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from epistemics_dataset.evidence_translation import prepare, reconcile, run
from epistemics_dataset.pipeline import write_jsonl
from epistemics_dataset.seeds import digest


class Result(SimpleNamespace):
    def model_dump(self, **kwargs):
        return vars(self)


class FakeDatasets:
    def __init__(self):
        self.calls = []
        self.uploaded = []

    def upload_file(self, path, **kwargs):
        self.calls.append('upload')
        self.uploaded = [json.loads(s) for s in Path(path).read_text().splitlines()]
        return Result(dataset_id='english-id')

    def get_status(self, dataset_id):
        return Result(status='succeeded')

    def translate(self, dataset_id, **kwargs):
        self.calls.append('estimate' if kwargs.get('estimate') else 'translate')
        return Result(dataset_id=None if kwargs.get('estimate') else 'translated-id',
                      estimated_credits_consumed=1, estimated_new_rows=len(self.uploaded) * 2)

    def download(self, dataset_id, **kwargs):
        rows = []
        for index, original in enumerate(self.uploaded):
            for lang in ('original', 'zh-Hans', 'vi'):
                text = original['completion'] if lang == 'original' else lang + ': ' + original['completion']
                rows.append({'original_prompt': original['prompt'], 'original_completion': text,
                             'enhanced_completion': text, 'target_language_code': lang,
                             'translation_join_id': 'join-' + str(index)})
        return SimpleNamespace(write_to_file=lambda path: write_jsonl(path, rows))


class EvidenceTranslationTests(unittest.TestCase):
    def fixture(self, folder):
        cases = [{'sample_id': 's/1', 'answer': 'A', 'languages': {'en': {'question': 'Private benchmark question'}}}]
        evidence = [{'sample_id': 's/1', 'source_url': 'https://example.org/rule',
                     'passage_en': 'An independently checked rule.', 'evidence_status': 'draft_supported'}]
        a, b = folder / 'cases.jsonl', folder / 'evidence.jsonl'
        write_jsonl(a, cases)
        write_jsonl(b, evidence)
        return {'cases_file': str(a), 'evidence_file': str(b), 'candidate_hash': digest(cases),
                'cases_sha256': hashlib.sha256(a.read_bytes()).hexdigest(),
                'evidence_sha256': hashlib.sha256(b.read_bytes()).hexdigest(),
                'expected_questions': 1, 'allow_unreviewed_drafts': True,
                'sdk_version': '0.19.0', 'languages': ['zh', 'vi'], 'sample_rate': 1.0,
                'credit_cap': 2, 'wait_timeout_seconds': 1}

    def test_native_translation_only_resume_and_no_automatic_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.fixture(root)
            fake = FakeDatasets()
            client = SimpleNamespace(datasets=fake)
            out = run(config, root / 'out', client)
            run(config, root / 'out', client)
            self.assertEqual(fake.calls, ['upload', 'estimate', 'translate'])
            self.assertNotIn('Private benchmark question', json.dumps(fake.uploaded))
            self.assertNotIn('"answer"', json.dumps(fake.uploaded))
            report = json.loads((out / 'translation-report.json').read_text())
            self.assertEqual(report['matched_draft_families'], 1)
            self.assertEqual(report['lineage_problems'], [])
            self.assertEqual(report['approved_families'], 0)
            candidates = [json.loads(s) for s in (out / 'translation-candidates.jsonl').read_text().splitlines()]
            self.assertFalse(candidates[0]['approved_for_experiment'])

    def test_corrupt_lineage_original_and_duplicate_language_are_quarantined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec, upload = prepare(self.fixture(root))
            marker = upload[0]['prompt']
            rows = [{'original_prompt': marker, 'original_completion': 'An independently checked rule.',
                     'target_language_code': lang, 'translation_join_id': 'same-join'}
                    for lang in ('original', 'zh-Hans', 'vi')]
            report, candidates = reconcile(rows, spec['materials'])
            self.assertEqual(len(candidates), 1)
            for mutate in ('join', 'original', 'duplicate', 'marker'):
                bad = copy.deepcopy(rows)
                if mutate == 'join':
                    bad[1]['translation_join_id'] = 'different'
                elif mutate == 'original':
                    bad[0]['original_completion'] = 'Changed original.'
                elif mutate == 'duplicate':
                    bad.append(copy.deepcopy(bad[1]))
                else:
                    bad[1]['original_prompt'] = '{"sample_id":"wrong","translation_id":"unknown"}'
                report, candidates = reconcile(bad, spec['materials'])
                self.assertEqual(candidates, [], mutate)
                self.assertTrue(report['lineage_problems'], mutate)

    def test_changed_input_and_credit_cap_block_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.fixture(root)
            api = FakeDatasets()
            config['credit_cap'] = 0
            with self.assertRaisesRegex(ValueError, 'credit cap'):
                run(config, root / 'out', SimpleNamespace(datasets=api))
            self.assertEqual(api.calls, ['upload', 'estimate'])
            Path(config['evidence_file']).write_text('{}\n')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                prepare(config)
