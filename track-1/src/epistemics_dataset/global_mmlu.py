"""Read-only published-data import, alignment and deterministic pilot selection.

No generation, augmentation, translation or evaluation requests.
"""
import argparse
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from .pipeline import write_jsonl
from .seeds import digest

TOKEN_NAMES = ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGING_FACE_HUB_TOKEN",
               "HUGGINGFACE_API_KEY", "HF_API_KEY", "HUGGINGFACE_TOKEN",
               "HF_ACCESS_TOKEN", "HUGGINGFACEHUB_API_TOKEN", "HUGGINGFACE_API_TOKEN")


def get_token(env_path):
    from dotenv import dotenv_values
    values = dotenv_values(env_path) if Path(env_path).exists() else {}
    return next((os.environ.get(k) or values.get(k) for k in TOKEN_NAMES
                 if os.environ.get(k) or values.get(k)), None)


def download(config, output, token=None):
    manifest = []
    for name, expected in config["sha256"].items():
        path = output/"upstream"/name
        url = f"https://huggingface.co/datasets/{config['dataset']}/resolve/{config['revision']}/{name}"
        if not path.exists():
            # Attach credentials only to the HF request; never save/log headers or redirect URLs.
            req = urllib.request.Request(url, headers={"Authorization":f"Bearer {token}"} if token else {})
            with urllib.request.urlopen(req, timeout=90) as response:
                content = response.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Upstream file checksum mismatch: {name}")
        manifest.append({"path":name,"sha256":actual,"bytes":path.stat().st_size,"source":url})
    return manifest


def align(rows_by_language, allow_answer_disagreements=False):
    indexes = {}
    for language, rows in rows_by_language.items():
        ids = [r["sample_id"] for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError(f"Duplicate sample IDs in {language}")
        indexes[language] = dict(zip(ids, rows))
    baseline = set(indexes["en"])
    for language, index in indexes.items():
        if set(index) != baseline:
            raise ValueError(f"Sample ID sets differ for {language}")
    mismatches = []
    for sample_id in sorted(baseline):
        rows = {language: index[sample_id] for language,index in indexes.items()}
        if len({r["answer"] for r in rows.values()}) != 1:
            mismatches.append(sample_id)
        for row in rows.values():
            if row["answer"] not in "ABCD" or len(row["answer"]) != 1:
                raise ValueError(f"Invalid answer key for {sample_id}")
    if mismatches and not allow_answer_disagreements:
        raise ValueError(f"Cross-language answer disagreements: {len(mismatches)} IDs; first {mismatches[:3]}")
    return indexes


def answer_agrees(indexes, sample_id):
    return len({index[sample_id]["answer"] for index in indexes.values()}) == 1


def complete(indexes, sample_id):
    return all(isinstance(index[sample_id].get(k), str) and index[sample_id][k].strip()
               for index in indexes.values() for k in ("question","option_a","option_b","option_c","option_d"))


def select(indexes, config):
    chosen = []
    for subject in config["subjects"]:
        candidates = [r for r in indexes["en"].values()
                      if r["subject"] == subject and r["cultural_sensitivity_label"] == config["cultural_sensitivity_label"]
                      and r["sample_id"] not in config.get("exclude_ids", [])
                      and complete(indexes,r["sample_id"]) and answer_agrees(indexes,r["sample_id"])]
        candidates.sort(key=lambda r: hashlib.sha256((config["selection_salt"]+r["sample_id"]).encode()).hexdigest())
        if len(candidates) < config["per_subject"]:
            raise ValueError(f"Insufficient eligible rows for {subject}")
        for original in candidates[:config["per_subject"]]:
            sample_id = original["sample_id"]
            chosen.append({"sample_id":sample_id, "subject":subject,"answer":original["answer"],
                           "upstream_split":config["split"],"purpose":config.get("purpose", "development_pilot_not_final_test"),
                           "cultural_sensitivity_label": original["cultural_sensitivity_label"],
                           "languages":{lang: index[sample_id] for lang,index in indexes.items()},
                           "evidence_status":"not_collected", "language_review_status":"pending"})
    return chosen


def preview(cases, config):
    lines = ["# Global-MMLU: published question preview", "",
             f"Dataset: {config['dataset']}; pinned revision `{config['revision']}`.", "",
             "Original questions/options and dataset answer keys, unchanged. Source passages are not yet collected. Dataset labels have not been independently re-adjudicated. These cases are development material, not the final test set.", ""]
    for case in cases:
        lines += [f"## {case['sample_id']}", ""]
        for language, row in case["languages"].items():
            lines += [f"**{language}**", "", row["question"], ""]
            lines += [f"- {code}. {row['option_'+code.lower()]}" for code in "ABCD"]
            lines += ["",f"Dataset answer: **{row['answer']}**", ""]
    return "\n".join(lines)


def prepare(config, output, token=None):
    import pyarrow.parquet as pq
    manifest = download(config,output,token)
    rows = {lang:pq.read_table(output/"upstream"/f"{lang}/{config['split']}-00000-of-00001.parquet").to_pylist()
            for lang in config["languages"]}
    indexes = align(rows, allow_answer_disagreements=True)
    cases = select(indexes,config)
    write_jsonl(output/"pilot-cases.jsonl",cases)
    tasks = [{"sample_id":c["sample_id"], "question":c["languages"]["en"]["question"],
              "answer_code":c["answer"], "answer_text":c["languages"]["en"]["option_"+c["answer"].lower()],
              "source_url":None, "passage_en":None, "passage_zh":None,"passage_vi":None,
              "evidence_status":"not_collected", "support_review":"pending"} for c in cases]
    write_jsonl(output/"evidence-tasks.jsonl", tasks)
    (output/"question-preview.md").write_text(preview(cases,config),encoding="utf-8")
    report = {"dataset":config["dataset"],"revision":config["revision"],"upstream_declared_license":"apache-2.0",
              "files":manifest,"rows_per_language":{lang:len(r) for lang,r in rows.items()},
              "ids_aligned":True,"pilot_answer_keys_aligned":True,
              "upstream_answer_disagreement_ids_excluded_from_selection":[i for i in sorted(indexes["en"]) if not answer_agrees(indexes,i)],
              "incomplete_upstream_ids_excluded_from_selection":[i for i in sorted(indexes["en"]) if not complete(indexes,i)],
              "pilot_cases":len(cases),
              "pilot_language_records":len(cases)*len(rows),"selection":config,
              "pilot_hash":digest(cases),"evidence_passages_ready":0,"generation_calls":0,"model_evaluation_calls":0,
              "limits":["Selected culturally agnostic items in four subjects; not representative of all MMLU.",
                        "Original test split is used as pilot development material; exclude these IDs from a later held-out study.",
                        "Alignment does not certify translation meaning or answer correctness.",
                        "reference metadata is not a supplied evidence passage."]}
    (output/"import-manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    return report


def main():
    root=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config",type=Path,default=root/"configs/global-mmlu.json")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--env-file",type=Path,default=root/".env")
    args=p.parse_args()
    config=json.loads(args.config.read_text())
    try:
        report=prepare(config,args.output,get_token(args.env_file))
    except ValueError as exc:
        p.exit(1,f"Validation failed: {exc}\n")
    except Exception as exc:
        p.exit(1,f"Import failed ({type(exc).__name__}); no dataset approved.\n")
    print(json.dumps({k:report[k] for k in ("dataset","revision","rows_per_language","pilot_cases","pilot_language_records","evidence_passages_ready")},indent=2))


if __name__ == "__main__":
    main()
