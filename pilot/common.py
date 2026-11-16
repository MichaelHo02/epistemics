import hashlib
import json
import os
from pathlib import Path
import urllib.request
import tiktoken

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'config.json').read_text())

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

class API:
    def __init__(self, output):
        self.output = output
        self.calls = 0
        self.tokens = {'input': 0, 'output': 0}
        self.encoding = tiktoken.get_encoding('o200k_base')
        self.cache = {}
        self.key = os.environ.get('OPENAI_API_KEY', '')
        if not self.key:
            for line in Path(CFG['env_file']).read_text().splitlines():
                if line.strip().startswith('OPENAI_API_KEY='):
                    self.key = line.split('=', 1)[1].strip().strip('"').strip("'")
        if not self.key:
            raise RuntimeError('Configured credential missing')

    def query(self, prompt):
        digest = hashlib.sha256(prompt.encode()).hexdigest()
        if digest in self.cache:
            return self.cache[digest]
        if self.calls >= CFG['max_calls']:
            raise RuntimeError('Hard request cap reached')
        if len(self.encoding.encode(prompt)) > 6000:
            raise RuntimeError('Input token limit exceeded')
        self.calls += 1
        body = {'model': CFG['model'], 'input': prompt, 'store': False,
                'reasoning': {'effort': 'none'}, 'max_output_tokens': CFG['output_tokens']}
        # No automatic retries: partial output is retained and failures remain visible.
        req = urllib.request.Request('https://api.openai.com/v1/responses',
            data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + self.key,
            'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.load(response)
        text = ''.join(p.get('text', '') for item in result.get('output', [])
                       if item.get('type') == 'message' for p in item.get('content', [])
                       if p.get('type') == 'output_text')
        save(self.output / 'requests' / (digest + '.json'),
             {'prompt': prompt, 'response': result, 'call': self.calls})
        if result.get('status') != 'completed' or not text.strip():
            raise RuntimeError('Incomplete or empty model response; see saved response')
        usage = result.get('usage', {})
        for name in self.tokens:
            self.tokens[name] += usage.get(name + '_tokens', 0)
        self.cache[digest] = text
        print(json.dumps({'event': 'api_progress', 'requests': self.calls,
                          'usage': self.tokens}), flush=True)
        return text

def destination():
    run = os.environ.get('ORX_RUN_ID')
    if not run:
        raise RuntimeError('Tracked execution required')
    out = Path(CFG['artifact_root']) / run
    out.mkdir(parents=True, exist_ok=True)
    save(out / 'configuration.json', {**CFG, 'commit': os.environ.get('ORX_COMMIT'),
                                      'run_id': run})
    print(json.dumps({'event': 'configuration', **CFG, 'output': str(out)}), flush=True)
    return out
