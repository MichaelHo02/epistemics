"""Lightweight, zero-request checks of labels, budgets and malformed responses."""
import itertools
import tiktoken
from materials import validate, render
from study import parse_ids, parse_choice

def check():
    cases = validate()
    encoding = tiktoken.get_encoding('o200k_base')
    for count in [2, 4]:
        lengths = {len(encoding.encode(render(list(group)))) for case in cases
                   for group in itertools.combinations(case['options'], count)}
        assert len(lengths) == 1, lengths
    assert parse_ids('{"ids":["A","B"]}', list('ABCDEFGH'), 2) == ['A', 'B']
    for text in ['{}', '[]', 'garbage', '{"ids":["A","A"]}',
                 '{"ids":["A","Z"]}', '{"ids":["A"]}', '{"ids":[1,2]}']:
        assert parse_ids(text, list('ABCDEFGH'), 2) is None
    assert parse_choice('{"choice":[]}') == 'INVALID'
    assert parse_choice('garbage') == 'INVALID'
    print('PASS token equality across all subsets and invalid response handling')

if __name__ == '__main__':
    check()
