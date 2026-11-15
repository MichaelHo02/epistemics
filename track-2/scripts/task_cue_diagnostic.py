"""Exploratory, standard-library-only task-cue diagnostic; never calls an LLM."""
from __future__ import annotations

import collections
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import urllib.request

REVISION = "58f644a25e801cb19dca961ba6df0b354c640551"
EXPECTED_HASH = "9460a8ebb9004cc4366e17aea517e2fc6510a9b4c5bf190da95ffa1b138a0653"
URL = f"https://raw.githubusercontent.com/THU-Agent/ObligationGuard/{REVISION}/data/obligationbench.jsonl"
SEEDS = [1701, 1702, 1703]
GROUP_THRESHOLD = 0.55
OUTPUT_ROOT = Path("/Users/michaelho/.local/share/openresearch/files/epistemics/sprint-review/track-2-systematic-review/task-cue-diagnostic")


def tokens(text):
    return set(re.findall(r"[a-z_][a-z_0-9]{2,}", text.lower()))


def metrics(labels, predictions):
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predictions))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predictions))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predictions))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predictions))
    return {
        "n": len(labels), "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": (tp + tn) / len(labels),
        "balanced_accuracy": ((tp / (tp + fn)) + (tn / (tn + fp))) / 2,
        "positive_recall": tp / (tp + fn), "negative_recall": tn / (tn + fp),
    }


def lexical_groups(documents):
    parent = list(range(len(documents)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(documents):
        for j in range(i):
            b = documents[j]
            if len(a & b) / max(1, len(a | b)) >= GROUP_THRESHOLD:
                parent[root(i)] = root(j)
    groups = collections.defaultdict(list)
    for i in range(len(documents)):
        groups[root(i)].append(i)
    return list(groups.values())


def folds_from_groups(groups, seed, count=5):
    rng = random.Random(seed)
    groups = list(groups)
    rng.shuffle(groups)
    groups.sort(key=len, reverse=True)
    folds = [[] for _ in range(count)]
    for group in groups:
        candidates = [i for i in range(count) if len(folds[i]) == min(map(len, folds))]
        folds[rng.choice(candidates)].extend(group)
    return [fold for fold in folds if fold]


def predict(train, test, docs, labels, domains, method):
    counts = collections.Counter(labels[i] for i in train)
    majority = int(counts[1] > counts[0])
    if method == "majority":
        return [majority] * len(test), []
    if method == "domain_only":
        by_domain = collections.defaultdict(collections.Counter)
        for i in train:
            by_domain[domains[i]][labels[i]] += 1
        return [int(by_domain[domains[i]][1] > by_domain[domains[i]][0]) if domains[i] in by_domain else majority for i in test], []

    # Train-only vocabulary selection. Features are task words, never trajectories.
    df = collections.Counter(w for i in train for w in docs[i])
    vocabulary = set(sorted((w for w, n in df.items() if n >= 2), key=lambda w: (-df[w], w))[:1000])
    word_counts = [collections.Counter(), collections.Counter()]
    for i in train:
        word_counts[labels[i]].update(docs[i] & vocabulary)
    totals = [sum(c.values()) + max(1, len(vocabulary)) for c in word_counts]
    log_prob = [{w: math.log((word_counts[c][w] + 1) / totals[c]) for w in vocabulary} for c in [0, 1]]
    priors = [math.log((counts[c] + 1) / (len(train) + 2)) for c in [0, 1]]
    result = []
    for i in test:
        scores = [priors[c] + sum(log_prob[c][w] for w in docs[i] & vocabulary) for c in [0, 1]]
        result.append(int(scores[1] > scores[0]))
    ranked = sorted(vocabulary, key=lambda w: abs(log_prob[1][w] - log_prob[0][w]), reverse=True)
    return result, [{"word": w, "log_likelihood_ratio": log_prob[1][w] - log_prob[0][w]} for w in ranked[:12]]


def evaluate(folds, docs, labels, domains, method):
    predicted = [None] * len(labels)
    records = []
    for fold_no, test in enumerate(folds):
        test_set = set(test)
        train = [i for i in range(len(labels)) if i not in test_set]
        assert train and test_set.isdisjoint(train)
        output, features = predict(train, test, docs, labels, domains, method)
        for i, value in zip(test, output):
            assert predicted[i] is None
            predicted[i] = value
        records.append({"fold": fold_no, "train": train, "test": test, "features": features})
    assert all(value in [0, 1] for value in predicted)
    return {"metrics": metrics(labels, predicted), "predictions": predicted, "folds": records}


def main():
    config = {"dataset_revision": REVISION, "expected_sha256": EXPECTED_HASH,
              "seeds": SEEDS, "folds": 5, "lexical_jaccard_threshold": GROUP_THRESHOLD,
              "vocabulary_limit": 1000, "min_train_document_frequency": 2,
              "null_permutations": 20, "null_shuffle": "within task_domain",
              "status": "exploratory; observations and examples inspected before design",
              "endpoint": "nonempty reference obligation set; NOT obligation-set recall or guard safety"}
    print("CONFIG " + json.dumps(config), flush=True)
    raw = urllib.request.urlopen(URL, timeout=60).read()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_HASH, "source hash differs"
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    assert len(rows) == 240
    docs = [tokens(row["task"]) for row in rows]
    labels = [int(bool(row["obligations"])) for row in rows]
    domains = [row["task_domain"] for row in rows]
    assert collections.Counter(labels) == {0: 120, 1: 120}
    groups = lexical_groups(docs)
    group_summary = {"groups": len(groups), "largest_group": max(map(len, groups)),
                     "sizes": sorted(map(len, groups), reverse=True),
                     "mixed_label_groups": sum(len({labels[i] for i in group}) > 1 for group in groups)}
    print("GROUPS " + json.dumps(group_summary), flush=True)
    results = []
    for seed in SEEDS:
        for kind, split_groups in [("row", [[i] for i in range(len(rows))]), ("lexical_group", groups)]:
            folds = folds_from_groups(split_groups, seed)
            for method in ["majority", "domain_only", "task_nb"]:
                result = evaluate(folds, docs, labels, domains, method)
                result.update({"split": kind, "seed": seed, "method": method})
                results.append(result)
                print("RESULT " + json.dumps({k: result[k] for k in ["split", "seed", "method", "metrics"]}), flush=True)
    domain_folds = [[i for i, d in enumerate(domains) if d == name] for name in sorted(set(domains))]
    for method in ["majority", "domain_only", "task_nb"]:
        result = evaluate(domain_folds, docs, labels, domains, method)
        result.update({"split": "leave_domain_out", "seed": None, "method": method})
        results.append(result)
        print("RESULT " + json.dumps({k: result[k] for k in ["split", "seed", "method", "metrics"]}), flush=True)

    # A diagnostic null, not a confirmatory hypothesis test or a population CI.
    null = []
    fixed_folds = folds_from_groups(groups, SEEDS[0])
    for iteration in range(20):
        shuffled = list(labels)
        rng = random.Random(8800 + iteration)
        for domain in sorted(set(domains)):
            indices = [i for i, d in enumerate(domains) if d == domain]
            values = [labels[i] for i in indices]
            rng.shuffle(values)
            for i, value in zip(indices, values):
                shuffled[i] = value
        value = evaluate(fixed_folds, docs, shuffled, domains, "task_nb")["metrics"]["balanced_accuracy"]
        null.append(value)
    summary = {"task_nb_balanced_accuracy": {kind: [r["metrics"]["balanced_accuracy"] for r in results if r["split"] == kind and r["method"] == "task_nb"] for kind in ["row", "lexical_group", "leave_domain_out"]},
               "permuted_group_nb": {"values": null, "mean": sum(null) / len(null), "min": min(null), "max": max(null)},
               "limitations": ["No LLM auditor evaluated.", "No paper model score reproduced.", "Lexical clusters are not gold source/template families.", "Task-only predictability is not evidence of a guard's internal reliance.", "No unchanged-task counterfactual trajectory pairs executed."]}
    output = OUTPUT_ROOT / os.environ.get("ORX_RUN_ID", "untracked")
    output.mkdir(parents=True, exist_ok=False)
    report = {"config": config, "groups": group_summary, "ids": [r["instance_id"] for r in rows], "labels": labels,
              "results": results, "summary": summary}
    (output / "diagnostic.json").write_text(json.dumps(report, indent=2) + "\n")
    print("ARTIFACT " + str(output / "diagnostic.json"), flush=True)
    print("FINAL " + json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
