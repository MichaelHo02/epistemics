"""Read-only verified source adapter. Never returns gold action text to a reader."""
import hashlib
import json
from pathlib import Path
import unicodedata

from common import ROOT

SOURCE_SHA256 = '9460a8ebb9004cc4366e17aea517e2fc6510a9b4c5bf190da95ffa1b138a0653'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def guard_input(row):
    return {'task_id': 'task', 'task': row['task'], 'trajectory': row['trajectory']}


def guard_text(row):
    return json.dumps(guard_input(row), ensure_ascii=False, indent=2)


def task_cluster(task):
    return sha256(' '.join(unicodedata.normalize('NFKC', task).split()).casefold().encode())


def load_material(cfg, encoding):
    manifest = json.loads((ROOT / 'natural-manifest.json').read_text())
    raw = Path(cfg['source_file']).read_bytes()
    if sha256(raw) != SOURCE_SHA256 or sha256(raw) != manifest['source_sha256']:
        raise ValueError('Canonical source SHA mismatch; no substitute/download/truncation')
    if len(raw) != manifest['source_bytes']:
        raise ValueError('Source size mismatch')
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != 240 or len({r['instance_id'] for r in rows}) != 240:
        raise ValueError('Source record population mismatch')
    meta = []
    by_id = {}
    for line, row in enumerate(rows, 1):
        if set(row) != {'instance_id', 'task', 'trajectory', 'obligations', 'task_domain'}:
            raise ValueError('Canonical source fields changed')
        text = guard_text(row)
        entry = {'instance_id': row['instance_id'], 'source_line': line,
                 'task_domain': row['task_domain'], 'benchmark_positive': bool(row['obligations']),
                 'guard_json_tokens': len(encoding.encode(text)), 'guard_input_sha256': sha256(text.encode()),
                 'record_sha256': sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()),
                 'normalized_task_cluster_sha256': task_cluster(row['task'])}
        meta.append(entry)
        # Only input and binary label/association metadata escape this adapter.
        by_id[row['instance_id']] = {**entry, 'input': text, 'message_count': len(row['trajectory'])}
    eligible = [r for r in meta if r['guard_json_tokens'] <= 24000]
    selected = []
    for domain in sorted({r['task_domain'] for r in meta}):
        for positive in [True, False]:
            selected.extend(sorted([r for r in eligible if r['task_domain'] == domain and
                                    r['benchmark_positive'] == positive], key=lambda r: r['instance_id'])[:4])
    if selected != manifest['assay_records'] or len(selected) != 24:
        raise ValueError('Frozen stratified selection changed')
    excluded = [r for r in meta if r['guard_json_tokens'] > 24000]
    if excluded != manifest['excluded_over_proxy_cap'] or len(eligible) != 228:
        raise ValueError('Frozen eligibility exclusions changed')
    selected_ids = {r['instance_id'] for r in selected}
    smoke = min([r for r in eligible if not r['benchmark_positive'] and r['instance_id'] not in selected_ids],
                key=lambda r: r['instance_id'])
    if smoke != manifest['smoke_record']:
        raise ValueError('Separate original-negative smoke changed')
    source_prompt = Path(cfg['published_prompt_file']).read_bytes()
    if sha256(source_prompt) != manifest['published_prompt_sha256']:
        raise ValueError('Published prompt source SHA mismatch')
    blob = hashlib.sha1(b'blob ' + str(len(source_prompt)).encode() + b'\0' + source_prompt).hexdigest()
    if blob != manifest['published_prompt_git_blob_sha1']:
        raise ValueError('Published prompt Git blob mismatch')
    return ([by_id[r['instance_id']] for r in selected], by_id[smoke['instance_id']],
            source_prompt.decode('utf-8'), manifest)
