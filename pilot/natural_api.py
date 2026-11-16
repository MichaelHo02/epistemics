"""Bounded uncached Responses transport; every planned replicate is an actual attempt."""
import json
from pathlib import Path
import threading
import urllib.error
import urllib.request
import uuid

from common import save
from natural_data import sha256
from natural_interface import body_digest, wire_bytes


class Budget:
    def __init__(self, cfg, tasks):
        self.cfg = cfg
        self.allowed = {t['logical_call_id']: t for t in tasks}
        if len(self.allowed) != 196 or len(tasks) != 196:
            raise ValueError('Exactly 196 distinct planned calls required')
        self.counts = {'smoke': 0, 'assay': 0}
        self.used = set()
        self.aborted = False
        self.lock = threading.Lock()

    def abort(self):
        with self.lock:
            self.aborted = True

    def reserve(self, task, digest):
        with self.lock:
            ident = task['logical_call_id']
            if self.aborted:
                raise RuntimeError('New dispatch stopped')
            if self.allowed.get(ident) != task or digest != task['body_sha256']:
                raise RuntimeError('Unplanned or altered request')
            if ident in self.used:
                raise RuntimeError('No repeat dispatch of a logical call')
            phase = task['phase']
            total = sum(self.counts.values())
            if total >= min(self.cfg['max_calls'], self.cfg['planned_calls']) or self.counts[phase] >= self.cfg['max_' + phase + '_calls']:
                raise RuntimeError('Planned/hard attempt cap reached')
            self.used.add(ident)
            self.counts[phase] += 1
            return sum(self.counts.values())


def preflight_body(body, cfg, encoding):
    estimated = len(encoding.encode(wire_bytes(body).decode('utf-8'))) + cfg['input_margin_tokens']
    if estimated > cfg['input_tokens']:
        raise ValueError('Complete ordered request plus margin exceeds input cap')
    if body['max_output_tokens'] != cfg['output_tokens'] or cfg['output_tokens'] > cfg['model_max_output_tokens']:
        raise ValueError('Output budget mismatch/exceeds documented maximum')
    if estimated + cfg['output_tokens'] > cfg['context_tokens']:
        raise ValueError('Separate input plus output exceeds documented context')
    return estimated


def credential(cfg):
    for line in Path(cfg['env_file']).read_text().splitlines():
        if line.strip().startswith('OPENAI_API_KEY='):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    raise RuntimeError('Authorized credential missing')


class API:
    def __init__(self, output, cfg, encoding, tasks, transport=None, key=None):
        self.output, self.cfg, self.encoding = Path(output), cfg, encoding
        self.budget = Budget(cfg, tasks)
        self.tokens = {'input': 0, 'output': 0, 'reasoning': 0, 'cached_input': 0}
        self.response_ids = set()
        self.lock = threading.Lock()
        self.transport = transport or urllib.request.urlopen
        self.key = credential(cfg) if key is None else key

    def query(self, body, task):
        wire = wire_bytes(body)
        digest = body_digest(body)
        estimated = preflight_body(body, self.cfg, self.encoding)
        attempt = self.budget.reserve(task, digest)
        client_id = str(uuid.uuid4())
        public_headers = {'X-Client-Request-Id': client_id}
        public_transport_sha = sha256(json.dumps(public_headers, sort_keys=True, separators=(',', ':')).encode() + b'\n' + wire)
        path = self.output / 'requests' / f'{attempt:03}-{task["logical_call_id"]}.json'
        record = {'attempt': attempt, 'logical_call_id': task['logical_call_id'], 'task': task,
                  'request': body, 'body_sha256': digest, 'public_client_headers': public_headers,
                  'public_header_and_body_sha256': public_transport_sha,
                  'estimated_complete_wire_tokens_plus_margin': estimated}
        save(path, {**record, 'transport': 'pending'})
        req = urllib.request.Request('https://api.openai.com/v1/responses', data=wire,
              headers={**public_headers, 'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        try:
            with self.transport(req, timeout=180) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            save(path, {**record, 'transport': 'http_error', 'http_status': exc.code})
            self.budget.abort()
            raise RuntimeError('HTTP failure; no retry') from None
        except Exception as exc:
            save(path, {**record, 'transport': 'transport_error', 'error_class': type(exc).__name__})
            self.budget.abort()
            raise RuntimeError('Transport failure; no retry') from None
        save(path, {**record, 'transport': 'received', 'response': result})
        try:
            usage = result.get('usage')
            if type(usage) is not dict or any(type(usage.get(k)) is not int or usage[k] < 0 for k in ['input_tokens', 'output_tokens']):
                raise ValueError('Missing/invalid billed usage')
            rt = usage.get('output_tokens_details', {}).get('reasoning_tokens', 0)
            ct = usage.get('input_tokens_details', {}).get('cached_tokens', 0)
            if type(rt) is not int or type(ct) is not int or not 0 <= rt <= usage['output_tokens'] or not 0 <= ct <= usage['input_tokens']:
                raise ValueError('Invalid detailed reasoning/cache usage')
            response_id = result.get('id')
            with self.lock:
                if not isinstance(response_id, str) or not response_id or response_id in self.response_ids:
                    raise ValueError('Missing/duplicate provider response ID')
                self.response_ids.add(response_id)
                self.tokens['input'] += usage['input_tokens']; self.tokens['output'] += usage['output_tokens']
                self.tokens['reasoning'] += rt; self.tokens['cached_input'] += ct
            if result.get('model') != self.cfg['model']:
                raise ValueError('Unexpected model')
            if result.get('status') != 'completed' or result.get('incomplete_details'):
                raise ValueError('Incomplete provider response')
            if usage['input_tokens'] > self.cfg['input_tokens'] or usage['output_tokens'] > self.cfg['output_tokens'] or usage['input_tokens'] + usage['output_tokens'] > self.cfg['context_tokens']:
                raise ValueError('Billed token budget exceeded')
            parts = [p for item in result.get('output', []) if item.get('type') == 'message' for p in item.get('content', [])]
            if any(p.get('type') == 'refusal' for p in parts):
                raise ValueError('Provider refusal')
            text = ''.join(p.get('text', '') for p in parts if p.get('type') == 'output_text')
            if not text.strip():
                raise ValueError('Empty output')
        except Exception as exc:
            save(path, {**record, 'transport': 'received', 'response': result, 'acceptance_error_class': type(exc).__name__})
            self.budget.abort()
            raise RuntimeError('Provider acceptance failure; retained without retry') from None
        print(json.dumps({'event': 'natural_api_response', 'attempt': attempt, 'phase': task['phase'],
                          'logical_call_id': task['logical_call_id'], 'provider_response_id': response_id,
                          'usage': usage}), flush=True)
        return text, str(path.relative_to(self.output)), response_id
