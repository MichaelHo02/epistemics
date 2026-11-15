import json, sys
from run2 import analyse
out = {}
for m in sys.argv[1:]:
    recs = [json.loads(l) for l in open(f"results_v2/raw_{m}.jsonl")]
    out[m] = analyse(recs)
json.dump(out, open("results_v2/summary.json", "w"), indent=1)
f = lambda x: "n/a" if x is None else f"{x[0]:.2f} [{x[1]:.2f},{x[2]:.2f}]"
for m, v in out.items():
    print("=====", m, "unparsed baseline", v["unparsed_baseline"], "errors", v["errors"])
    for k in ("answerable", "unanswerable"):
        d = v[k]; print(f"-- {k} items={d['items']} trials={d['trials']} brier={d['brier_baseline']}")
        print("  baseline correct/wrong/abstain:", f(d["baseline_correct"]), f(d["baseline_wrong"]), f(d["baseline_abstain"]))
        print("  leave-correct:", {a: f(x) for a, x in d["leave_correct_rate"].items()})
        print("  chain cum collapse:", {a[-1]: f(x) for a, x in d["chain_cumulative_collapse"].items()})
        print("  PSH:", f(d["pressure_stable_honesty"]))
