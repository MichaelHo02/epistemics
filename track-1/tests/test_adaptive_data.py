import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from epistemics_dataset.adaptive_data import price, review_report, run, seed_pairs
from epistemics_dataset.pipeline import write_jsonl
from epistemics_dataset.seeds import make_seeds


class Result(SimpleNamespace):
    def model_dump(self, **kwargs):
        return vars(self)


class FakeDatasets:
    def __init__(self):
        self.calls = []
        self.rows = []
    def upload_file(self, path, **kw):
        self.calls.append(("upload", kw))
        self.rows = [json.loads(s) for s in Path(path).read_text().splitlines()]
        return Result(dataset_id="seed-id")
    def get_status(self, dataset_id):
        return Result(status="succeeded")
    def augment(self, dataset_id, **kw):
        self.calls.append(("augment", kw))
        return Result(dataset_id=None if kw.get("estimate") else "expanded-id", estimated_credits_consumed=1)
    def translate(self, dataset_id, **kw):
        self.calls.append(("translate", kw))
        return Result(dataset_id=None if kw.get("estimate") else "translated-id", estimated_credits_consumed=2)
    def download(self, dataset_id, **kw):
        # Deliberately not a full language expansion: must not be promoted to reviewed data.
        return SimpleNamespace(write_to_file=lambda p: write_jsonl(p, self.rows))


class AdaptiveDataChecks(unittest.TestCase):
    def test_native_calls_estimates_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"root"
            seeds = make_seeds()
            write_jsonl(root/"data/seeds/pilot.jsonl", seeds)
            api = FakeDatasets()
            config = {"adaptive_data": {"seed_ids":["closing-01"], "similar_rows":1,
                       "languages":["zh","vi"], "credit_cap":5,"wait_timeout_seconds":1}}
            directory = run(config, root, Path(tmp)/"output", SimpleNamespace(datasets=api))
            self.assertEqual([n for n, _ in api.calls], ["upload","augment","augment","translate","translate"])
            self.assertEqual(api.calls[2][1]["similar_rows"], 1)
            self.assertEqual(api.calls[4][1]["sample_rate"], 1)
            self.assertTrue(api.calls[2][1]["idempotency_key"])
            report = json.loads((directory/"review-report.json").read_text())
            self.assertFalse(report["row_count_matches_expected"])
            self.assertEqual(report["approved_rows"], 0)
            run(config, root, Path(tmp)/"output", SimpleNamespace(datasets=api))
            self.assertEqual(len(api.calls), 5)  # no new upload/charged jobs on resume

    def test_no_generated_gold_or_assumed_pairing(self):
        seeds = make_seeds()
        rows = seed_pairs(seeds[:1])
        bad = json.loads(rows[0]["prompt"])
        bad["facts"]["closing"] = "22:00"
        rows.append({"prompt":json.dumps(bad),"completion":"A"})
        rows.append({"prompt":"not JSON", "completion":"A"})
        report, queue = review_report(rows, seeds)
        self.assertEqual(report["approved_rows"], 0)
        self.assertFalse(queue[1]["answer_matches_known_seed"])
        self.assertIsNone(queue[2]["case_id_candidate"])
        self.assertRaises(ValueError, price, {})

    def test_expansion_credit_cap_blocks_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            write_jsonl(root/"data/seeds/pilot.jsonl",make_seeds())
            api=FakeDatasets()
            c={"adaptive_data":{"seed_ids":["closing-01"],"similar_rows":1,"languages":["zh","vi"],"credit_cap":0,"wait_timeout_seconds":1}}
            self.assertRaises(ValueError,run,c,root,root/"out",SimpleNamespace(datasets=api))
            self.assertEqual([n for n,_ in api.calls],["upload","augment"])
