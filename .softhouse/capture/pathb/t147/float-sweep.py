"""T147 — P-25 sweep: no binary float on any path that reasons about money.

Structural, not textual: every .py file T147 authored or touched is parsed with `ast` and
searched for float LITERALS (ast.Constant of type float), calls to float()/round(), true
division, and json load/loads without parse_float=str.  A grep over identifiers would miss a
bare literal (P-35's second question: does the guard detect every FORM the violation takes?).
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # .softhouse/capture/pathb/t147
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))  # worktree root
FILES = [
    '.softhouse/capture/lib/attest_gate.py',
    '.softhouse/capture/pathb/t125/compare-bytes.py',
    '.softhouse/capture/pathb/t125/gate-selftest.py',
    '.softhouse/capture/pathb/t125/blast-radius.py',
    '.softhouse/capture/pathb/t147/cp-digest-census.py',
    '.softhouse/capture/pathb/t147/probe-doc-grader.py',
    '.softhouse/capture/pathb/t147/mutate-blast-radius-provenance.py',
    '.softhouse/capture/pathb/t36/attest.py',
    '.softhouse/capture/charges/bin/attest-t40.py',
]

print('=' * 78)
print(' T147 — P-25 structural float sweep over every .py T147 authored or touched')
print('=' * 78)
print()
print('  %-58s %6s %6s %6s' % ('file', 'floats', 'div', 'json!'))
print('  ' + '-' * 78)
bad = 0
inspected = 0
for rel in FILES:
    path = os.path.join(ROOT, rel)
    tree = ast.parse(open(path, 'rb').read(), filename=rel)
    inspected += 1
    floats, divs, jsonbare = 0, 0, 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            floats += 1
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ('float', 'round'):
            floats += 1
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            divs += 1
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ('load', 'loads') \
                and isinstance(node.func.value, ast.Name) and node.func.value.id == 'json':
            if not any(k.arg == 'parse_float' for k in node.keywords):
                jsonbare += 1
    flag = '' if (floats or divs or jsonbare) == 0 else '   <-- LOOK'
    print('  %-58s %6d %6d %6d%s' % (rel.replace('.softhouse/capture/', ''),
                                     floats, divs, jsonbare, flag))
    bad += floats + divs + jsonbare
print('  ' + '-' * 78)
if inspected == 0:
    print('  *** SWEEP NOT PERFORMED *** zero files inspected is an error, not a pass (P-35).')
    sys.exit(2)
if bad:
    print('  *** %d SUSPECT CONSTRUCTS *** re-read every flagged file before believing it.' % bad)
    sys.exit(1)
print('  ASSERTED: %d files parsed, and across all of them ZERO float literals, ZERO' % inspected)
print('  float()/round() calls, ZERO true divisions and ZERO bare json.load(s).')
sys.exit(0)
