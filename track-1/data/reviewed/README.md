# Reviewed data

The approved 300-family snapshot is stored at `artifacts/track-1/global-mmlu-main/final-v1/`. It contains original questions and reviewed supporting evidence in English, Chinese and Vietnamese, with provenance, hashes and integrity checks. `configs/openai-eval.json` points to that snapshot; the model remains unset.

Reviews are assistant reviews, not independent human or blinded bilingual reviews. There are 299 upstream CA-labelled families and one explicitly documented unannotated astronomy fallback. No model experiment has been run.
