import copy
import unittest
from epistemics_dataset.global_mmlu import align, select


def row(i, answer="A"):
    return {"sample_id":f"astronomy/test/{i}","subject":"astronomy", "question":f"Question {i}?",
            "option_a":"one","option_b":"two","option_c":"three","option_d":"four",
            "answer":answer,"cultural_sensitivity_label":"CA"}


class PublishedDataChecks(unittest.TestCase):
    def setUp(self):
        self.rows={l:[row(i) for i in range(5)] for l in ("en","zh","vi")}
        self.config={"subjects":["astronomy"],"cultural_sensitivity_label":"CA",
                     "selection_salt":"fixed","per_subject":2,"split":"test"}

    def test_missing_ids_and_duplicate_ids_rejected(self):
        x=copy.deepcopy(self.rows); x["vi"].pop()
        self.assertRaises(ValueError,align,x)
        x=copy.deepcopy(self.rows); x["vi"].append(x["vi"][0])
        self.assertRaises(ValueError,align,x)

    def test_mismatched_keys_and_missing_options_excluded(self):
        x=copy.deepcopy(self.rows); x["vi"][0]["answer"]="B"; x["zh"][1]["option_c"]=""
        self.assertRaises(ValueError,align,x)
        chosen=select(align(x,allow_answer_disagreements=True),dict(self.config,per_subject=3))
        self.assertEqual({c["sample_id"] for c in chosen},{f"astronomy/test/{i}" for i in (2,3,4)})

    def test_selection_preserves_originals_and_is_order_independent(self):
        a=select(align(self.rows),self.config)
        b=select(align({l:list(reversed(rs)) for l,rs in self.rows.items()}),self.config)
        self.assertEqual(a,b)
        for case in a:
            for lang in self.rows:
                original=next(r for r in self.rows[lang] if r['sample_id']==case['sample_id'])
                self.assertEqual(case['languages'][lang],original)
                self.assertEqual(case['evidence_status'],'not_collected')

    def test_development_exclusions_and_main_purpose(self):
        config = dict(self.config, exclude_ids=["astronomy/test/0"],
                      purpose="main_evaluation_candidate", per_subject=4)
        chosen = select(align(self.rows), config)
        self.assertNotIn("astronomy/test/0", {c["sample_id"] for c in chosen})
        self.assertTrue(all(c["purpose"] == "main_evaluation_candidate" for c in chosen))
        self.assertRaises(ValueError, select, align(self.rows), dict(config, per_subject=5))
