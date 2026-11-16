"""Single consistent re-analysis from raw transcripts. Relabels every reply with the current grader,
excludes ambiguous items and errored/unparsed replies, bootstraps over items (95% CI)."""
import json, random, collections, sys
import run2
EXCL = ("what date is father", "at what age are taxis", "ansel adams", "great escape", "parliament square")
its = {k["question"]: k for k in json.load(open("items3.json"))}
its = {q: k for q, k in its.items() if not any(e in q.lower() for e in EXCL)}
FILES = {"gpt-5": "results_v3/raw_gpt-5.jsonl", "gpt-5-mini": "results_v3/raw_gpt-5-mini.jsonl"}
for m in ("deepseek-v4-flash", "glm-5.2", "qwen3.5-397b"):
    FILES[m] = f"results_v3_{m}/raw_{m}.jsonl"
ARMS = ["simple", "citation", "authority", "emotional"]

def lab(r, text):
    if "[ERROR" in text or not text.strip(): return "unparsed"
    k = its[r["question"]]
    return run2.label(r["kind"], run2.parse(text)[0], k.get("accepted", []))

def load(m):
    out = []
    for l in open(FILES[m]):
        r = json.loads(l)
        if r["question"] not in its: continue
        r["cat"] = its[r["question"]]["category"]
        r["b"] = lab(r, r["baseline_text"])
        r["s"] = {a: lab(r, r["single"][a]["text"]) for a in ARMS}
        out.append(r)
    return out

def ci(by, fn, n=2000):
    return run2.boot(by, fn, n=n)
def grp(rs):
    d = collections.defaultdict(list)
    for r in rs: d[r["question"]].append(r)
    return d
def fmt(x): return "n/a" if not x else f"{x[0]:.2f} [{x[1]:.2f},{x[2]:.2f}]"

res = {}; lines = []
for m in FILES:
    rs = load(m); res[m] = {}
    ans = [r for r in rs if r["kind"] == "ans"]; un = [r for r in rs if r["kind"] == "unans"]
    # baseline correct (parsed only)
    res[m]["ans_base_correct"] = ci(grp(ans), lambda g: (sum(x["b"] == "correct" for x in g), sum(x["b"] != "unparsed" for x in g)))
    res[m]["unans_base_unknown"] = ci(grp(un), lambda g: (sum(x["b"] == "correct" for x in g), sum(x["b"] != "unparsed" for x in g)))
    for c in ["future unknown", "unsolved problem", "counterfactual", "false assumption"]:
        res[m]["unk_" + c] = ci(grp([r for r in un if r["cat"] == c]), lambda g: (sum(x["b"] == "correct" for x in g), sum(x["b"] != "unparsed" for x in g)))
    for a in ARMS:  # among baseline-correct, share that left the right answer (parsed only)
        res[m]["ans_leave_" + a] = ci(grp(ans), lambda g, a=a: (sum(x["s"][a] in ("wrong", "abstain") for x in g if x["b"] == "correct"), sum(x["b"] == "correct" and x["s"][a] != "unparsed" for x in g)))
        res[m]["unans_leave_" + a] = ci(grp(un), lambda g, a=a: (sum(x["s"][a] == "wrong" for x in g if x["b"] == "correct"), sum(x["b"] == "correct" and x["s"][a] != "unparsed" for x in g)))
    res[m]["unparsed_baseline_share"] = round(sum(r["b"] == "unparsed" for r in rs) / len(rs), 3)
    res[m]["items"] = (len({r["question"] for r in ans}), len({r["question"] for r in un}))
json.dump(res, open("results_final.json", "w"), indent=1)

lines.append("## Baseline (parsed replies only; 95% CI bootstrapped over items)\n")
lines.append("| model | answerable correct | unanswerable UNKNOWN | future unknown | unsolved | counterfactual | false assumption | unparsed share |\n|---|---|---|---|---|---|---|---|")
for m, d in res.items():
    lines.append(f"| {m} | {fmt(d['ans_base_correct'])} | {fmt(d['unans_base_unknown'])} | " + " | ".join(fmt(d["unk_" + c]) for c in ["future unknown", "unsolved problem", "counterfactual", "false assumption"]) + f" | {d['unparsed_baseline_share']} |")
lines.append("\n## Pushback on answerable items: share of baseline-correct trials that left the correct answer\n")
lines.append("| model | simple denial | fake citation | authority | emotional |\n|---|---|---|---|---|")
for m, d in res.items(): lines.append(f"| {m} | " + " | ".join(fmt(d["ans_leave_" + a]) for a in ARMS) + " |")
lines.append("\n## Pushback on unanswerable items: share of baseline-UNKNOWN trials that switched to a concrete answer\n")
lines.append("| model | simple denial | fake citation | authority | emotional |\n|---|---|---|---|---|")
for m, d in res.items(): lines.append(f"| {m} | " + " | ".join(fmt(d["unans_leave_" + a]) for a in ARMS) + " |")

# ablation with paired item-level bootstrap on difference (fix - orig)
lines.append("\n## One-line fix (UNKNOWN rate, orig -> fix, paired bootstrap 95% CI on difference over items)\n")
lines.append("| model | category | orig | fix | diff [CI] |\n|---|---|---|---|---|")
import glob
ab = [o for f in glob.glob("ablate_out_*.json") for o in json.load(open(f))]
rnd = random.Random(0)
for m in ["gpt-5", "gpt-5-mini", "glm-5.2", "deepseek-v4-flash"]:
    for c in ["answerable", "future unknown", "unsolved problem", "counterfactual", "false assumption"]:
        per = collections.defaultdict(lambda: {"orig": [], "fix": []})
        # item identity is not stored in ablate_out; use positional index within (model,var,run,cat)
        for v in ("orig", "fix"):
            seq = [o for o in ab if o["model"] == m and o["var"] == v and o["cat"] == c]
            # group by run then position
            byrun = collections.defaultdict(list)
            for o in seq: byrun[o["run"]].append(o)
            for run, os_ in byrun.items():
                for i, o in enumerate(os_):
                    if not o["err"] and o["label"] != "unparsed":
                        per[i][v].append(1.0 if o["label"] == "correct" else 0.0)
        items = [i for i, d in per.items() if d["orig"] and d["fix"]]
        if not items: continue
        mo = sum(sum(per[i]["orig"]) / len(per[i]["orig"]) for i in items) / len(items)
        mf = sum(sum(per[i]["fix"]) / len(per[i]["fix"]) for i in items) / len(items)
        diffs = []
        for _ in range(2000):
            s = [rnd.choice(items) for _ in items]
            diffs.append(sum(sum(per[i]["fix"]) / len(per[i]["fix"]) - sum(per[i]["orig"]) / len(per[i]["orig"]) for i in s) / len(s))
        diffs.sort(); lo, hi = diffs[50], diffs[1949]
        lines.append(f"| {m} | {c} | {mo:.2f} | {mf:.2f} | {mf-mo:+.2f} [{lo:+.2f},{hi:+.2f}] |")
open("results_final.md", "w").write("\n".join(lines))
print("\n".join(lines))
