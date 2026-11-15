import sys, types, json, random, collections
import datasets  # import before stubbing torch
# stub torch: only used as a base class in data.py
torch = types.ModuleType("torch"); torch.utils = types.ModuleType("torch.utils"); torch.utils.data = types.ModuleType("torch.utils.data")
torch.utils.data.Dataset = object
sys.modules.update({"torch": torch, "torch.utils": torch.utils, "torch.utils.data": torch.utils.data})
sys.path.insert(0, "hf_src")
import data as D
for k in [k for k in sys.modules if k=='torch' or k.startswith('torch.')]: del sys.modules[k]  # remove stub after import

out = []
for name, cls in [("big_bench_known_unknowns", D.BigBenchKnownUnknownsDataset),
                  ("known_unknown_questions", D.KUQDataset),
                  ("falseqa", D.FalseQADataset)]:
    try:
        ds = cls()
        n = len(ds)
        c = collections.Counter()
        for i in range(n):
            p = ds[i]
            out.append({"source": name, "idx": i, "question": p.question,
                        "reference_answers": p.reference_answers, "should_abstain": p.should_abstain,
                        "metadata": p.metadata})
            c[p.should_abstain] += 1
        print(name, n, dict(c), flush=True)
    except Exception as e:
        print(name, "FAILED", type(e).__name__, str(e)[:300], flush=True)
json.dump(out, open("abstentionbench_raw.json", "w"))
print("total", len(out))
