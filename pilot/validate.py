"""Zero-request preflight for the numerical diagnostic."""
from materials import validate
from study import parse

validate()
assert parse('{"verdict":"UNRESOLVED"}') == 'UNRESOLVED'
for text in ['garbage', '[]', '{}', '{"verdict":"TRUE"}', '{"verdict":[]}']:
    assert parse(text) == 'INVALID'
print('PASS response parser and interval preflight; zero API requests')
