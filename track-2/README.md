# Track 2: exploratory obligation benchmark diagnostic

The fixed command is `python3 track-2/scripts/run.py`. It uses only the Python
standard library and public data at a pinned revision, checked against SHA-256.
It makes no model/API calls and reads no private environment file.

The endpoint is predicting whether a reference obligation set is nonempty from
the task text alone. This is a corpus diagnostic, not obligation-set recall,
correctness of a guard, or a reproduction of the paper's model results.

The script compares train-only task-word Naive Bayes with majority and task-domain
baselines using row folds, label-blind lexical-family folds, and domain holdout.
It retains held-out predictions, fold indices, influential training features, and
20 within-domain label-permutation controls. All choices are exploratory because
source examples and construction cues were inspected before this design.

Lexical families use connected components of task-word Jaccard similarity at
0.55. They are not verified source families. Splits are label-blind, and metrics
pool held-out predictions over the whole release rather than averaging unequal
folds. Three split seeds are sensitivity checks, not independent datasets.

Results are printed in the run log and saved under the project artifacts folder,
in a subdirectory named with the run ID. No raw upstream dataset is redistributed.
No claim is made about source dataset licensing beyond reading the public file.
