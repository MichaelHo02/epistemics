"""Dedicated Adaption datasets workflow. No Responses API or training calls.

Upload controlled pairs, generate similar rows, translate the expanded dataset,
then retain raw exports and a review queue. Service outputs are never gold labels.
"""
import json
import os
import re
import time
from pathlib import Path
from .pipeline import read_jsonl, write_jsonl
from .seeds import digest, render

WORKFLOW_VERSION = "adaptive-data-v1"


def plain(value):
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temp.replace(path)


def seed_pairs(seeds):
    """Use rigid JSON prompts so exported candidate data has an auditable seed schema."""
    result = []
    for seed in seeds:
        text = render(seed, "en")
        prompt = {"case_id": seed["case_id"], "family": seed["family"],
                  "facts": seed["facts"], "question": text["question"],
                  "source": text["source"], "options": seed["options"]}
        result.append({"prompt": json.dumps(prompt, ensure_ascii=False, sort_keys=True),
                       "completion": seed["gold_code"]})
    return result


def price(result):
    data = plain(result)
    for field in ("estimated_credits_consumed", "estimated_credits"):
        number = data.get(field)
        if isinstance(number, (int, float)) and not isinstance(number, bool) and number >= 0:
            return number
    raise ValueError("No usable credit estimate returned; not launching this operation")


def wait(client, dataset_id, label, timeout_seconds, poll_seconds=10):
    deadline = time.monotonic()+timeout_seconds
    while True:
        status = plain(client.datasets.get_status(dataset_id))
        state = status.get("status")
        print(json.dumps({"stage": label, "dataset_id": dataset_id, "status": state}), flush=True)
        if state == "succeeded":
            return status
        if state in ("failed", "awaiting_input", "cancelled"):
            raise ValueError(f"{label} stopped with status {state}; inspect the saved dataset ID")
        if time.monotonic() >= deadline:
            raise ValueError(f"{label} timed out locally; provider job may still run. Resume the same state, do not create a replacement")
        time.sleep(poll_seconds)


def text_column(row, names):
    for name in names:
        if isinstance(row.get(name), str) and row[name].strip():
            return row[name]
    return ""


def review_report(rows, seeds):
    """Triage only. Retain full raw rows even when schema/lineage is not recoverable."""
    by_id = {s["case_id"]: s for s in seeds}
    queue = []
    known = 0
    for i, row in enumerate(rows):
        prompt = text_column(row, ("prompt", "original_prompt", "enhanced_prompt"))
        completion = text_column(row, ("completion", "original_completion", "enhanced_completion"))
        parsed = None
        try:
            parsed = json.loads(prompt)
        except (ValueError, TypeError):
            pass
        case_id = parsed.get("case_id") if isinstance(parsed, dict) else None
        source_seed = by_id.get(case_id)
        exact_facts = bool(source_seed and parsed.get("facts") == source_seed["facts"]
                           and parsed.get("options") == source_seed["options"])
        answer_matches_seed = bool(exact_facts and completion.strip() == source_seed["gold_code"])
        known += int(answer_matches_seed)
        queue.append({"row_index": i, "prompt": prompt, "completion": completion,
                      "case_id_candidate": case_id, "facts_options_match_known_seed": exact_facts,
                      "answer_matches_known_seed": answer_matches_seed,
                      "language_metadata": {k:v for k,v in row.items() if "lang" in k.lower()},
                      "review_status": "pending", "approved": False})
    return {"raw_row_count": len(rows), "rows_matching_known_seed_facts_and_answer": known,
            "approved_rows": 0, "observed_columns": sorted({k for r in rows for k in r}),
            "warning": "Matching seed fields does not verify translated prose. New facts, altered schema, reused case IDs and language lineage require independent review; no inferred pairings or gold labels."}, queue


def run(config, root, output_root, client=None):
    selected = []
    for seed in read_jsonl(root/"data/seeds/pilot.jsonl"):
        if seed["case_id"] in config["adaptive_data"]["seed_ids"]:
            selected.append(seed)
    settings = config["adaptive_data"]
    if len(selected) != len(settings["seed_ids"]):
        raise ValueError("Configured native-service seeds are missing or duplicated")
    if settings["similar_rows"] < 1 or set(settings["languages"]) != {"zh", "vi"}:
        raise ValueError("Native pilot must request positive similar rows and zh/vi translation")
    spec = {"workflow": WORKFLOW_VERSION, "seeds": selected, "settings": settings}
    operation = digest(spec)
    directory = output_root/"adaptive-data"/operation
    directory.mkdir(parents=True, exist_ok=True)
    state_path = directory/"state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        "operation": operation, "spec": spec, "approved_rows": 0}
    save(state_path, state)
    if client is None:
        from adaption import Adaption
        client = Adaption(max_retries=0, timeout=120.0)
    if not state.get("seed_dataset_id"):
        if state.get("upload_in_progress"):
            raise ValueError("Prior upload outcome is uncertain; recover its dataset ID before retrying upload")
        upload = directory/"seed-upload.jsonl"
        write_jsonl(upload, seed_pairs(selected))
        state["upload_in_progress"] = True
        save(state_path, state)
        result = client.datasets.upload_file(upload, name=f"epistemics-track1-{operation[:12]}",
                                             processing_mode="raw",
                                             column_mapping={"prompt":"prompt", "completion":"completion"})
        state["seed_dataset_id"] = result.dataset_id
        state["upload_in_progress"] = False
        save(state_path, state)
    wait(client, state["seed_dataset_id"], "seed_upload", settings["wait_timeout_seconds"])
    max_credits = settings["credit_cap"]
    if not state.get("expanded_dataset_id"):
        estimate = client.datasets.augment(state["seed_dataset_id"], similar_rows=settings["similar_rows"], estimate=True)
        state["expansion_estimate"] = plain(estimate)
        save(state_path, state)
        if price(estimate) > max_credits:
            raise ValueError("Expansion exceeds the configured credit cap; no expansion launched")
        result = client.datasets.augment(state["seed_dataset_id"], similar_rows=settings["similar_rows"],
                                         idempotency_key=f"{operation}-similar")
        state["expanded_dataset_id"] = result.dataset_id
        save(state_path, state)
    wait(client, state["expanded_dataset_id"], "generate_similar", settings["wait_timeout_seconds"])
    expanded_path = directory/"expanded-english.jsonl"
    client.datasets.download(state["expanded_dataset_id"], file_format="jsonl").write_to_file(expanded_path)
    if not state.get("translated_dataset_id"):
        estimate = client.datasets.translate(state["expanded_dataset_id"], sample_rate=1.0,
                                             languages=settings["languages"], estimate=True)
        state["translation_estimate"] = plain(estimate)
        save(state_path, state)
        if price(estimate)+price(state["expansion_estimate"]) > max_credits:
            raise ValueError("Expansion plus translation exceeds the configured credit cap; translation not launched")
        result = client.datasets.translate(state["expanded_dataset_id"], sample_rate=1.0,
                                           languages=settings["languages"],
                                           idempotency_key=f"{operation}-translate")
        state["translated_dataset_id"] = result.dataset_id
        save(state_path, state)
    wait(client, state["translated_dataset_id"], "translate_dataset", settings["wait_timeout_seconds"])
    export = directory/"multilingual-raw.jsonl"
    client.datasets.download(state["translated_dataset_id"], file_format="jsonl").write_to_file(export)
    rows = read_jsonl(export)
    report, queue = review_report(rows, selected)
    report.update({"seed_count": len(selected), "requested_similar_rows": settings["similar_rows"],
                   "expected_row_count_if_preserved": (len(selected)+settings["similar_rows"])*3,
                   "dataset_ids": {k:v for k,v in state.items() if k.endswith("dataset_id")},
                   "row_count_matches_expected": len(rows) == (len(selected)+settings["similar_rows"])*3,
                   "workflow": WORKFLOW_VERSION})
    save(directory/"review-report.json", report)
    write_jsonl(directory/"review-queue.jsonl", queue)
    state["status"] = "downloaded_pending_review"
    save(state_path, state)
    print(json.dumps({"status": state["status"], "output_path": str(directory), "report": report}), flush=True)
    return directory
