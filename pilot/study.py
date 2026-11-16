"""Predeclared zero-API filter gate and bounded reader test on a frozen child."""
import ast
from collections import defaultdict
import hashlib
import importlib.metadata
import json
import re
import warnings

from common import API, CFG, ROOT, destination, save
from materials import cases, contents


def load_functions():
    import numpy as np
    from rouge_score import rouge_scorer
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    names = {"calculate_similarity", "calculate_pairwise_rouge", "calculate_average_score",
             "group_n_gram_filtering", "k_mean_filtering", "conflict_query_gpt"}
    source = (ROOT / "upstream.py").read_bytes()
    assert hashlib.sha256(source).hexdigest() == CFG["upstream_sha256"]
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    ns = dict(np=np, rouge_scorer=rouge_scorer, KMeans=KMeans,
              StandardScaler=StandardScaler, cosine_similarity=cosine_similarity,
              progress_bar=lambda items, **kwargs: items)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "published-functions", "exec"), ns)
    return ns


def readiness_summary(rows):
    groups = defaultdict(list)
    index = {}
    for row in rows:
        groups[(row["condition"], row["policy"])].append(row)
        index[(row["family"], row["condition"], row["policy"])] = row
    table = [{"condition": c, "policy": p, "n": len(rs),
              "support_retained": sum(r["support_retained"] for r in rs),
              "false_retained": sum(r["false_retained"] for r in rs),
              "empty": sum(not r["kept"] for r in rs)} for (c, p), rs in groups.items()]
    clean = true_loss = distractor_loss = specific_loss = 0
    pairs = []
    for case in cases():
        retained = {c: index[(case["id"], c, "published_filter")]["support_retained"]
                    for c in CFG["conditions"]}
        clean += retained["clean"]
        tl = retained["clean"] and not retained["true_copies"]
        dl = retained["clean"] and not retained["distractor_copies"]
        sl = tl and retained["distractor_copies"]
        true_loss += tl
        distractor_loss += dl
        specific_loss += sl
        pairs.append({"family": case["id"], **retained, "true_copy_loss": tl,
                      "distractor_copy_loss": dl, "copy_specific_loss": sl})
    gate = {"clean_retained": clean, "required_clean": 8, "n": 12,
            "true_copy_losses_from_clean": true_loss,
            "distractor_copy_losses_from_clean": distractor_loss,
            "excess_loss_count": true_loss - distractor_loss, "required_excess_loss": 4,
            "clean_and_distractor_retained_but_true_lost": specific_loss,
            "required_specific_loss": 4}
    gate["pass"] = clean >= 8 and true_loss - distractor_loss >= 4 and specific_loss >= 4
    return {"summary": table, "paired_cases": pairs, "gate": gate}


def main():
    import numpy as np
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.set_num_threads(2)
    torch.set_num_interop_threads(2)
    out = destination()
    data = cases()
    assert len(data) == 12 and [c["id"] for c in data[:5]] == CFG["reader_case_ids"]
    data_hash = hashlib.sha256((json.dumps(data, sort_keys=True) + "\n").encode()).hexdigest()
    save(out / "cases.json", data)
    save(out / "provenance.json", {
        "source": "https://github.com/HuichiZhou/TrustRAG/blob/main/defend_module.py",
        "upstream_sha256": CFG["upstream_sha256"],
        "license_sha256": hashlib.sha256((ROOT / "LICENSE.upstream").read_bytes()).hexdigest(),
        "cases_sha256": data_hash, "materials_sha256": hashlib.sha256((ROOT / "materials.py").read_bytes()).hexdigest(),
        "adaptations": "CPU embedding/API adapter only; exact original filtering and three consolidation function bodies",
        "packages": {name: importlib.metadata.version(name) for name in
                     ["numpy", "scikit-learn", "rouge-score", "torch", "transformers", "tiktoken"]}})
    funcs = load_functions()
    tokenizer = AutoTokenizer.from_pretrained(CFG["embedding_model"], revision=CFG["embedding_revision"])
    model = AutoModel.from_pretrained(CFG["embedding_model"], revision=CFG["embedding_revision"]).eval().cpu()
    embeddings = {}
    for text in dict.fromkeys(t for c in data for t in c["documents"] + [c["false"]]):
        inputs = tokenizer(text, return_tensors="pt")
        assert inputs["input_ids"].shape[1] <= 512, "No silent material truncation"
        with torch.no_grad():
            embeddings[text] = model(**inputs, output_hidden_states=True).hidden_states[-1][0, 0].numpy()
    np.savez_compressed(out / "embeddings.npz", **{"e%d" % i: v for i, v in enumerate(embeddings.values())})
    save(out / "embedding_index.json", list(embeddings))
    del model

    def filtered(docs, policy):
        if policy == "no_filter":
            return list(docs), []
        incoming = list(dict.fromkeys(docs)) if policy == "dedup_before_filter" else list(docs)
        with warnings.catch_warnings(record=True) as ws:
            _, kept = funcs["k_mean_filtering"](np.stack([embeddings[t] for t in incoming]), incoming, [], True)
        return list(kept), [str(w.message) for w in ws]

    rows = []
    with (out / "readiness-measurements.jsonl").open("w") as handle:
        for case in data:
            for condition in CFG["conditions"]:
                docs = contents(case, condition)
                for policy in CFG["policies"]:
                    kept, filter_warnings = filtered(docs, policy)
                    row = {"family": case["id"], "condition": condition, "policy": policy,
                           "input": docs, "kept": kept, "support_retained": case["support"] in kept,
                           "false_retained": case["false"] in kept, "filter_warnings": filter_warnings}
                    rows.append(row)
                    handle.write(json.dumps(row) + "\n"); handle.flush()
            print(json.dumps({"event": "readiness_family_complete", "family": case["id"], "requests": 0}), flush=True)
    ready = readiness_summary(rows)
    save(out / "readiness-summary.json", ready)
    print(json.dumps({"event": "readiness_result", "cases_sha256": data_hash, **ready}), flush=True)
    if CFG["stage"] == "readiness":
        result = {"stage": "readiness_complete", "requests": 0, "api_attempts": 0,
                  "cases_sha256": data_hash, **ready,
                  "decision": "eligible_for_predeclared_reader_child" if ready["gate"]["pass"] else "stop_no_paid_reader"}
    elif CFG["stage"] == "reader":
        assert ready["gate"]["pass"], "Readiness gate failed; API forbidden"
        assert data_hash == CFG["readiness_cases_sha256"], "Cannot change material after readiness"
        api = API(out)
        index = {(r["family"], r["condition"], r["policy"]): r for r in rows}
        measured = []
        with (out / "reader-measurements.jsonl").open("w") as handle:
            for case in data[:5]:
                for condition in CFG["conditions"]:
                    for policy in CFG["policies"]:
                        row = dict(index[(case["id"], condition, policy)])
                        answers, memories, consolidated = funcs["conflict_query_gpt"]([row["kept"]], [case["question"]], api)
                        codes = set(re.findall(r"(?<!\d)\d{4}(?!\d)", answers[0]))
                        row.update(answer_text=answers[0], memory=memories[0], consolidated=consolidated[0],
                                   correct=codes == {case["answer"]}, false_answer=codes == {case["wrong"]})
                        measured.append(row)
                        handle.write(json.dumps(row) + "\n"); handle.flush()
                print(json.dumps({"event": "reader_family_complete", "family": case["id"]}), flush=True)
        groups = defaultdict(list)
        for row in measured:
            groups[(row["condition"], row["policy"])].append(row)
        table = [{"condition": c, "policy": p, "n": len(rs), "correct": sum(r["correct"] for r in rs),
                  "false_answers": sum(r["false_answer"] for r in rs),
                  "support_retained": sum(r["support_retained"] for r in rs)} for (c, p), rs in groups.items()]
        result = {"stage": "reader_complete", "cases_sha256": data_hash, "reader_summary": table,
                  "requests": api.calls, "usage": api.tokens, "readiness_gate": ready["gate"],
                  "limits": "Five fixed development cases, synthetic fixed retrieval, no prevalence or novelty claim; exact dedup is established."}
    else:
        raise ValueError("Unrecognized stage")
    save(out / "summary.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
