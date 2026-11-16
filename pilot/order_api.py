"""Strict request transport. No caching. Every smoke replicate is a distinct attempt."""
import json
from pathlib import Path
import threading
import urllib.error
import urllib.request

from common import save
from order_interface import request_digest, wire_bytes


class Budget:
    def __init__(self, total=76, smoke=4, assay=72):
        self.total = total
        self.limits = {'smoke': smoke, 'assay': assay}
        self.counts = {'smoke': 0, 'assay': 0}
        self.lock = threading.Lock()

    def reserve(self, phase):
        with self.lock:
            if phase not in self.counts or sum(self.counts.values()) >= self.total or self.counts[phase] >= self.limits[phase]:
                raise RuntimeError('Hard API attempt budget reached')
            self.counts[phase] += 1
            return sum(self.counts.values())


class API:
    def __init__(self, output, cfg, encoding):
        self.output, self.cfg, self.encoding = output, cfg, encoding
        self.budget = Budget(cfg['max_calls'], cfg['max_smoke_calls'], cfg['max_assay_calls'])
        self.tokens = {'input': 0, 'output': 0, 'reasoning': 0}
        self.lock = threading.Lock()
        self.key = ''
        for line in Path(cfg['env_file']).read_text().splitlines():
            if line.strip().startswith('OPENAI_API_KEY='):
                self.key = line.split('=', 1)[1].strip().strip('"').strip("'")
        if not self.key:
            raise RuntimeError('Configured credential missing')

    def query(self, body, task):
        # Include entire ordered schema in digest/wire bytes. Never cache either arm.
        digest = request_digest(body)
        wire = wire_bytes(body)
        estimated = len(self.encoding.encode(wire.decode())) + 256
        if estimated > self.cfg['input_tokens']:
            raise RuntimeError('Pre-dispatch input token budget exceeded')
        attempt = self.budget.reserve(task['phase'])
        path = self.output / 'requests' / f'{attempt:03}-{digest}.json'
        record = {'attempt': attempt, 'task': task, 'request': body,
                  'wire_sha256': digest, 'estimated_input_tokens_plus_margin': estimated}
        save(path, {**record, 'transport': 'pending'})
        req = urllib.request.Request('https://api.openai.com/v1/responses', data=wire,
                headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            save(path, {**record, 'transport': 'http_error', 'http_status': exc.code})
            raise RuntimeError('HTTP failure; no retry') from None
        except Exception as exc:
            save(path, {**record, 'transport': 'transport_error', 'error_class': type(exc).__name__})
            raise RuntimeError('Transport failure; no retry') from None
        save(path, {**record, 'transport': 'received', 'response': result})
        usage = result.get('usage', {})
        with self.lock:
            for key in ['input', 'output']:
                self.tokens[key] += usage.get(key + '_tokens', 0)
            self.tokens['reasoning'] += usage.get('output_tokens_details', {}).get('reasoning_tokens', 0)
        if result.get('status') != 'completed':
            raise RuntimeError('Incomplete response; no retry')
        if result.get('model') != self.cfg['model']:
            raise RuntimeError('Unexpected model in response')
        if result.get('reasoning', {}).get('effort') != body['reasoning']['effort']:
            raise RuntimeError('Unexpected reasoning configuration in response')
        if usage.get('input_tokens', 0) > self.cfg['input_tokens'] or usage.get('output_tokens', 0) > self.cfg['output_tokens']:
            raise RuntimeError('Billed token budget violated; stop dispatch')
        text = ''.join(p.get('text', '') for item in result.get('output', []) if item.get('type') == 'message'
                       for p in item.get('content', []) if p.get('type') == 'output_text')
        if not text:
            raise RuntimeError('Empty output or refusal; no retry')
        print(json.dumps({'event': 'api_response', 'attempt': attempt, 'phase': task['phase'],
                          'case_id': task['case_id'], 'arm': task['arm'],
                          'reasoning': body['reasoning']['effort'],
                          'logical_call_id': task.get('logical_call_id'), 'usage': usage}), flush=True)
        return text, str(path.relative_to(self.output))

