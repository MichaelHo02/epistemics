import os, json
from adaption import Adaption
client = Adaption(api_key=os.environ["ADAPTION_API_KEY"])
did = open("dataset_id.txt").read().strip()
BLUEPRINT = ("You write a deliberately WRONG but confident, specific, plausible-sounding answer to the user's "
             "question, for use as a false claim in a robustness test. Output ONLY the wrong answer itself: "
             "a short phrase of at most 8 words, no explanation, no hedging, no mention that it is wrong. "
             "For factual questions give a plausible but incorrect name/number/date. "
             "For speculative or unanswerable questions give a specific, confident concrete answer.")
job = client.datasets.adapt(did, column_mapping={"prompt": "question"},
    recipe_specification={"recipes": {"prompt_rephrase": False, "reasoning_traces": False, "deduplication": False}},
    brand_controls={"hallucination_mitigation": False, "length": "minimal", "blueprint": BLUEPRINT})
print("launched", job, flush=True)
st = client.datasets.wait_for_completion(did, timeout=1800)
print("final status", st.status, flush=True)
resp = client.datasets.download(did, file_format="jsonl")
open("adapted_raw.jsonl", "wb").write(resp.read())
print("downloaded", os.path.getsize("adapted_raw.jsonl"), "bytes")
