"""Bounded Responses API client, adapted from project scaffold f634526.

Every transport attempt is logged before dispatch. No retry or resubmission.
"""
import hashlib
import json
import os
from pathlib import Path
import threading
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'config.json').read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


class API:
    def __init__(self, output):
        import tiktoken
        self.output = output
        self.calls = 0
        self.tokens = {'input': 0, 'output': 0}
        self.encoding = tiktoken.get_encoding('o200k_base')
        self.lock = threading.Lock()
        # Load only the authorized key, never source an arbitrary env file as shell code.
        self.key = ''
        for line in Path(CFG['env_file']).read_text().splitlines():
            if line.strip().startswith('OPENAI_API_KEY='):
                self.key = line.split('=', 1)[1].strip().strip('"').strip("'")
        if not self.key:
            raise RuntimeError('Configured credential missing')

    def query(self, prompt):
        digest = hashlib.sha256(prompt.encode()).hexdigest()
        count = len(self.encoding.encode(prompt))
        if count > CFG['input_tokens']:
            raise RuntimeError('Input token limit exceeded')
        with self.lock:
            if self.calls >= CFG['max_calls']:
                raise RuntimeError('Hard request cap reached')
            self.calls += 1
            call = self.calls
        body = {'model': CFG['model'], 'input': prompt, 'store': False,
                'reasoning': {'effort': 'none'}, 'max_output_tokens': CFG['output_tokens']}
        path = self.output / 'requests' / (digest + '.json')
        save(path, {'call': call, 'request': body, 'local_input_tokens': count, 'transport': 'pending'})
        req = urllib.request.Request('https://api.openai.com/v1/responses', data=json.dumps(body).encode(),
                                     headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            # HTTP response bodies or exception strings might contain sensitive request context.
            save(path, {'call': call, 'request': body, 'local_input_tokens': count,
                        'transport': 'http_error', 'http_status': exc.code})
            raise RuntimeError(f'HTTP status {exc.code}; no retry') from None
        except Exception as exc:
            save(path, {'call': call, 'request': body, 'local_input_tokens': count,
                        'transport': 'transport_error', 'error_class': type(exc).__name__})
            raise RuntimeError('Transport failure; no retry') from None
        save(path, {'call': call, 'request': body, 'local_input_tokens': count, 'transport': 'received',
                    'response': result})
        text = ''.join(p.get('text', '') for item in result.get('output', []) if item.get('type') == 'message'
                       for p in item.get('content', []) if p.get('type') == 'output_text')
        with self.lock:
            usage = result.get('usage', {})
            for name in self.tokens:
                self.tokens[name] += usage.get(name + '_tokens', 0)
            print(json.dumps({'event': 'api_progress', 'attempts': self.calls, 'returned_call': call,
                              'usage': self.tokens}), flush=True)
        if result.get('status') != 'completed' or not text.strip():
            raise RuntimeError('Incomplete or empty model response; retained without retry')
        return text, digest


def destination():
    run = os.environ.get('ORX_RUN_ID')
    if not run:
        raise RuntimeError('Tracked execution required')
    output = Path(CFG['artifact_root']) / run
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'configuration.json', {**CFG, 'commit': os.environ.get('ORX_COMMIT'), 'run_id': run})
    print(json.dumps({'event': 'configuration', **CFG, 'output': str(output)}), flush=True)
    return output

