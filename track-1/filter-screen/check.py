"""Development-only published-filter mechanism screen; no reader/API calls."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import warnings

import numpy as np
from rouge_score import rouge_scorer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import torch
from transformers import AutoModel, AutoTokenizer

HERE = Path(__file__).resolve().parent
MODEL = "princeton-nlp/sup-simcse-bert-base-uncased"
REVISION = "2d82fab19ac3a73a20dd20333d27eb8a52d6e97f"
FUNCTIONS = {"calculate_similarity", "calculate_pairwise_rouge", "calculate_average_score",
             "group_n_gram_filtering", "k_mean_filtering"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not os.environ.get("ORX_RUN_ID"):
        p.error("Use the recorded experiment runner")
    args.output.mkdir(parents=True, exist_ok=True)
    cases = json.loads((HERE/"development-contexts.json").read_text())
    source = (HERE/"upstream_defend_module.py").read_text()
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
    assert {node.name for node in functions} == FUNCTIONS
    # Execute unchanged original function bodies; omit CUDA/model/server imports.
    namespace = dict(np=np, KMeans=KMeans, StandardScaler=StandardScaler,
                     cosine_similarity=cosine_similarity, rouge_scorer=rouge_scorer)
    exec(compile(ast.Module(body=functions, type_ignores=[]), "upstream-filter-functions", "exec"), namespace)
    filt = namespace["k_mean_filtering"]
    metadata = {"stage": "development_mechanism_only", "families": len(cases),
                "model": MODEL, "revision": REVISION, "device": "cpu",
                "pooling": "last-hidden-layer CLS, identical to released embedding function",
                "upstream_file_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "network": "public model download only; no private env read or reader calls",
                "reader_calls": 0, "original_functions_unchanged": True,
                "limits": "constructed contexts, known support group only; no full-defense or answer-accuracy result"}
    (args.output/"configuration.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata), flush=True)
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModel.from_pretrained(MODEL, revision=REVISION).eval().cpu()
    texts = list(dict.fromkeys(d["text"] for c in cases for d in c["documents"]))
    embeddings = {}
    for i, text in enumerate(texts):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            value = model(**inputs, output_hidden_states=True, return_dict=True).hidden_states[-1][0, 0].numpy()
        embeddings[text] = value
        if (i+1) % 20 == 0:
            print(json.dumps({"stage": "embedding", "done": i+1, "total": len(texts)}), flush=True)
    all_rows = []
    with (args.output/"measurements.jsonl").open("w") as out:
        for case in cases:
            original = [d["text"] for d in case["documents"]]
            support = original[0]
            for condition in ["base", "support_copies", "distractor_copies"]:
                for budget in ([0] if condition == "base" else [1, 2, 4]):
                    for order in (["unchanged"] if condition == "base" else ["before", "after"]):
                        copies = [original[0 if condition == "support_copies" else 1]] * budget
                        contents = copies + original if order == "before" else original + copies
                        assert all(x in contents for x in original)
                        matrix = np.stack([embeddings[t] for t in contents])
                        for ngram in [True, False]:
                            row = dict(sample_id=case["sample_id"], condition=condition, budget=budget,
                                       order=order, ngram=ngram, original_count=len(original), input_count=len(contents))
                            try:
                                with warnings.catch_warnings(record=True) as captured:
                                    _, kept = filt(matrix.copy(), list(contents), [], ngram)
                                row.update(known_support_group_retained=support in kept, kept=kept,
                                           retained_count=len(kept), warnings=[str(w.message) for w in captured], error=None)
                            except Exception as e:
                                row.update(error=type(e).__name__+": "+str(e))
                            all_rows.append(row)
                            out.write(json.dumps(row)+"\n")
            out.flush()
            print(json.dumps({"stage": "filtered", "sample_id": case["sample_id"]}), flush=True)
    summaries = []
    for ngram in [True, False]:
        base = {r["sample_id"]: r for r in all_rows if r["condition"] == "base" and r["ngram"] == ngram}
        for budget in [1, 2, 4]:
            for order in ["before", "after"]:
                for condition in ["support_copies", "distractor_copies"]:
                    rows = [r for r in all_rows if r["condition"] == condition and r["ngram"] == ngram and r["budget"] == budget and r["order"] == order]
                    eligible = [r for r in rows if not r["error"] and not base[r["sample_id"]]["error"]]
                    summaries.append(dict(ngram=ngram, budget=budget, order=order, condition=condition,
                        evaluated=len(eligible), errors=len(rows)-len(eligible),
                        baseline_support_retained=sum(base[r["sample_id"]]["known_support_group_retained"] for r in eligible),
                        support_retained=sum(r["known_support_group_retained"] for r in eligible),
                        new_losses=sum(base[r["sample_id"]]["known_support_group_retained"] and not r["known_support_group_retained"] for r in eligible)))
    result = dict(configuration=metadata, summaries=summaries, measurement_rows=len(all_rows),
                  errors=sum(bool(r["error"]) for r in all_rows), reader_calls=0,
                  interpretation="Development mechanism only; no held-out result, reader harm or novelty established")
    (args.output/"summary.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"stage": "complete", **result}), flush=True)


if __name__ == "__main__":
    main()
