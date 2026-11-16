"""Summarise pressure_fix_*.json (pressure arms under the premise-check prompt) vs no-fix results_final.json; writes pressure_fix_results.md and figures/fig6_pressure_fix.png"""
import glob, json, collections
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, numpy as np
import run2
EXCL = ("great escape", "parliament square")
R = json.load(open("results_final.json"))
out = [o for f in sorted(glob.glob("pressure_fix_*.json")) for o in json.load(open(f))]
ARMS = run2.SINGLE; rows = []; lines = ["| model | UNKNOWN at baseline (fix) | UNKNOWN at baseline (orig) | switch rate under fix: simple / citation / authority / emotional | same, no fix |", "|---|---|---|---|---|"]
for m in ["gpt-5", "gpt-5-mini", "glm-5.2", "deepseek-v4-flash"]:
    rs = [o for o in out if o["model"] == m]
    if not rs: continue
    by = collections.defaultdict(list)
    for o in rs: by[o["q"]].append(o)
    base = run2.boot(by, lambda g: (sum(x["base"] == "correct" for x in g), sum(x["base"] != "unparsed" for x in g)))
    sw = {a: run2.boot(by, lambda g, a=a: (sum(x["arms"][a] == "wrong" for x in g if x["base"] == "correct"), sum(x["base"] == "correct" and x["arms"][a] != "unparsed" for x in g))) for a in ARMS}
    f = lambda v: "n/a" if not v else f"{v[0]:.2f}"
    nofix = [R[m]["unans_leave_" + a] for a in ARMS]
    lines.append(f"| {m} | {f(base)} | {R[m]['unans_base_unknown'][0]:.2f} | " + " / ".join(f(sw[a]) for a in ARMS) + " | " + " / ".join(f(v) for v in nofix) + " |")
    rows.append((m, [sw[a][0] if sw[a] else 0 for a in ARMS], [v[0] if v else 0 for v in nofix]))
open("pressure_fix_results.md", "w").write("\n".join(lines))
fig, axs = plt.subplots(1, len(rows), figsize=(2.6 * len(rows), 2.8), sharey=True)
axs = np.atleast_1d(axs)
for ax, (m, fx, nf) in zip(axs, rows):
    x = np.arange(4); ax.bar(x - .19, nf, .38, color="#c00000", label="original prompt"); ax.bar(x + .19, fx, .38, color="#1f4e79", label="with fix")
    ax.set_xticks(x); ax.set_xticklabels(["simple", "citation", "auth.", "emot."], fontsize=7); ax.set_title(m, fontsize=8); ax.set_ylim(0, .5)
    ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("UNKNOWN abandoned under pushback", fontsize=7); axs[0].legend(fontsize=6, frameon=False)
fig.suptitle("Fig 6. Pushback on unanswerable items, original vs premise-check prompt", fontsize=8); fig.tight_layout(); fig.savefig("figures/fig6_pressure_fix.png", dpi=150)
print("\n".join(lines))
