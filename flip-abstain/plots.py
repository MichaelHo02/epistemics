"""Figures for report.md from results_final.json and judge_out.json (run: python3 plots.py)."""
import json, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
R = json.load(open("results_final.json"))
M = ["gpt-5", "gpt-5-mini", "deepseek-v4-flash", "glm-5.2", "qwen3.5-397b"]
COL = ["#1f4e79", "#5b9bd5", "#c55a11", "#548235", "#7f7f7f"]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})

def bars(ax, keys, labels, title, ylabel):
    w = 0.16; x = np.arange(len(keys))
    for i, m in enumerate(M):
        v = [R[m][k] for k in keys]
        y = [a[0] if a else 0 for a in v]
        err = [[(a[0]-a[1]) if a else 0 for a in v], [(a[2]-a[0]) if a else 0 for a in v]]
        ax.bar(x + (i-2)*w, y, w, yerr=err, color=COL[i], label=m, capsize=1.5, error_kw={"lw": .7})
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05); ax.set_title(title); ax.set_ylabel(ylabel)

# Fig 1: UNKNOWN rate by category
fig, ax = plt.subplots(figsize=(7.5, 3.4))
cats = ["future unknown", "unsolved problem", "counterfactual", "false assumption"]
bars(ax, ["unk_" + c for c in cats], ["future\nunknown", "unsolved\nproblem", "counter-\nfactual", "false\nassumption"],
     "Fig 1. Share of unanswerable questions answered UNKNOWN (no pressure)", "UNKNOWN rate (95% CI over items)")
ax.legend(fontsize=7, ncol=5, loc="upper right", frameon=False, bbox_to_anchor=(1, 1.02)); fig.tight_layout(); fig.savefig("figures/fig1_unknown_by_category.png"); plt.close(fig)

# Fig 2: pushback effects
fig, axs = plt.subplots(1, 2, figsize=(9, 3.3), sharey=True)
arms = ["simple", "citation", "authority", "emotional"]; lab = ["simple\ndenial", "fake\ncitation", "claimed\nauthority", "emotional\nappeal"]
bars(axs[0], ["ans_leave_" + a for a in arms], lab, "Fig 2a. Correct answers abandoned (answerable)", "share of baseline-correct trials")
bars(axs[1], ["unans_leave_" + a for a in arms], lab, "Fig 2b. UNKNOWN abandoned (unanswerable)", "")
axs[1].legend(fontsize=6.5, frameon=False, loc="upper right")
fig.tight_layout(); fig.savefig("figures/fig2_pushback.png"); plt.close(fig)

# Fig 3: one-line fix, orig -> fix with CI on diff
A = [a for a in R["ablation"] if a["cat"] != "answerable"]
fig, axs = plt.subplots(1, 4, figsize=(10, 2.9), sharey=True)
for ax, m in zip(axs, ["gpt-5", "gpt-5-mini", "glm-5.2", "deepseek-v4-flash"]):
    rows = [a for a in A if a["model"] == m]
    for j, a in enumerate(rows):
        ax.plot([a["orig"], a["fix"]], [j, j], "-", color="#999", lw=1)
        ax.plot(a["orig"], j, "o", color="#c00000", ms=5); ax.plot(a["fix"], j, "o", color="#1f4e79", ms=5)
        sig = a["lo"] > 0
        ax.text(1.04, j, f"{a['fix']-a['orig']:+.2f}" + ("*" if sig else ""), va="center", fontsize=7)
    ax.set_xlim(0, 1.25); ax.set_xticks([0, .5, 1]); ax.set_title(m, fontsize=9)
axs[0].set_yticks(range(4)); axs[0].set_yticklabels(["future unknown", "unsolved problem", "counterfactual", "false assumption"]); axs[0].invert_yaxis()
axs[0].plot([], [], "o", color="#c00000", label="original prompt"); axs[0].plot([], [], "o", color="#1f4e79", label="with premise-check line")
axs[0].legend(fontsize=7, frameon=False, loc="lower left", bbox_to_anchor=(0, -0.30), ncol=2)
fig.suptitle("Fig 3. UNKNOWN rate before/after the one-line fix (* = paired 95% CI on difference excludes 0)", fontsize=9)
fig.tight_layout(); fig.savefig("figures/fig3_fix.png"); plt.close(fig)

# Fig 4: cost on answerable
ans = [a for a in R["ablation"] if a["cat"] == "answerable"]
fig, ax = plt.subplots(figsize=(4.5, 3))
x = np.arange(len(ans))
ax.bar(x-.18, [a["orig"] for a in ans], .36, color="#c00000", label="original"); ax.bar(x+.18, [a["fix"] for a in ans], .36, color="#1f4e79", label="with fix")
ax.set_xticks(x); ax.set_xticklabels([a["model"] for a in ans], rotation=20, ha="right"); ax.set_ylim(0, 1.05)
ax.set_title("Fig 4. Answerable questions answered correctly", fontsize=9); ax.legend(fontsize=7, frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig("figures/fig4_cost_answerable.png"); plt.close(fig)

# Fig 5: judge breakdown
J = json.load(open("judge_out.json")); order = ["COMMITTED", "HEDGED", "PREMISE_FLAGGED"]; cc = ["#c00000", "#f4b183", "#9dc3e6"]
ms = ["gpt-5", "gpt-5-mini", "deepseek-v4-flash", "glm-5.2"]
fig, ax = plt.subplots(figsize=(5.5, 2.8)); left = np.zeros(len(ms))
for k, c in zip(order, cc):
    v = np.array([sum(1 for o in J if o["model"] == m and o["j1"] == k) / max(1, sum(1 for o in J if o["model"] == m)) for m in ms])
    ax.barh(ms, v, left=left, color=c, label=k.lower().replace("_", " ")); left += v
ax.invert_yaxis(); ax.set_xlim(0, 1); ax.legend(fontsize=7, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(.5, -.4))
ax.set_title("Fig 5. What non-UNKNOWN replies on unanswerable items look like (judge 1)", fontsize=9)
fig.tight_layout(); fig.savefig("figures/fig5_judge.png"); plt.close(fig)
print("ok")
