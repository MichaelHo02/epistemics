import copy
import json
import tempfile
import unittest
from types import SimpleNamespace
from epistemics_dataset.seeds import digest, make_seeds, render
from epistemics_dataset.pipeline import build, validate
from epistemics_dataset.adaption_client import translate


class DatasetChecks(unittest.TestCase):
    def setUp(self):
        self.seeds = make_seeds()
        self.rows = [render(s, lang) for s in self.seeds for lang in ("en", "zh", "vi")]

    def test_facts_determine_gold_independently(self):
        for s in self.seeds:
            f = s["facts"]
            if s["family"] == "closing":
                expected = f["closing"]
            elif s["family"] == "arrival":
                h, m = map(int, f["departure"].split(":"))
                total = h*60+m+f["minutes"]
                expected = f"{total//60:02d}:{total%60:02d}"
            elif s["family"] == "fee":
                expected = str(f["entry"]+f["booking"])
            else:
                expected = str(f["total"]-f["reserved"])
            self.assertEqual(s["options"][s["gold_code"]], expected)
            self.assertNotEqual(s["options"][s["wrong_code"]], expected)

    def test_numeric_corruption_and_missing_language_fail(self):
        self.assertTrue(validate(self.seeds, self.rows)["structurally_valid"])
        bad = copy.deepcopy(self.rows)
        bad[1]["source"] = bad[1]["source"].replace("16:30", "17:30")
        self.assertFalse(validate(self.seeds, bad)["structurally_valid"])
        self.assertFalse(validate(self.seeds, self.rows[:-1])["structurally_valid"])

    def test_rehashed_wrong_gold_is_rejected(self):
        seeds = copy.deepcopy(self.seeds)
        seeds[0]["gold_code"], seeds[0]["wrong_code"] = seeds[0]["wrong_code"], seeds[0]["gold_code"]
        original = dict(seeds[0])
        original.pop("seed_hash")
        seeds[0]["seed_hash"] = digest(original)
        rows = [render(s, lang) for s in seeds for lang in ("en", "zh", "vi")]
        self.assertTrue(any("gold answer" in e for e in validate(seeds, rows)["errors"]))

    def test_review_gate_blocks_drafts(self):
        self.assertRaises(ValueError, list, build(self.seeds, self.rows, reviewed=True))

    def test_pairs_and_no_duplicate_absent_controls(self):
        variants = list(build(self.seeds, self.rows))
        self.assertEqual(len(variants), 780)
        self.assertEqual(len({v["variant_id"] for v in variants}), len(variants))
        for seed in self.seeds:
            rows = [v for v in variants if v["case_id"] == seed["case_id"]]
            self.assertEqual(len({r["split"] for r in rows}), 1)
            for v in rows:
                self.assertEqual(v["gold_code"], seed["gold_code"])
                if v["condition"] == "wrong":
                    self.assertEqual(len(v["peers"]), 3)
                    self.assertTrue(all(seed["wrong_code"] in p for p in v["peers"]))
                if v["stage"] == "initial":
                    self.assertNotIn("initial_answer", v)

    def test_sdk_cache_and_rejects_changed_facts(self):
        seed = self.seeds[0]
        responses = SimpleNamespace(create=lambda **kwargs: SimpleNamespace(
            output_text=json.dumps({k: render(seed, "vi")[k] for k in ("question", "source")}),
            id="mock-response", usage=None))
        client = SimpleNamespace(responses=responses)
        with tempfile.TemporaryDirectory() as tmp:
            a = translate(seed, "vi", "test-model", tmp, client)
            fail = SimpleNamespace(responses=SimpleNamespace(create=lambda **kw: self.fail("Cache miss")))
            self.assertEqual(a, translate(seed, "vi", "test-model", tmp, fail))
        responses.create = lambda **kwargs: SimpleNamespace(output_text='{"question":"When?", "source":"17:30"}')
        with tempfile.TemporaryDirectory() as tmp:
            self.assertRaises(ValueError, translate, seed, "vi", "test-model", tmp, client)


if __name__ == "__main__":
    unittest.main()
