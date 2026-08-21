#!/usr/bin/env python3
"""P-46 quote check for T177. Every line inside a fenced block in the review and the handoff that
looks like a transcript line MUST occur, byte for byte, in a committed analysis transcript. A quoted
excerpt is a claim; this proves it was extracted and not retyped.

Zero lines checked is an ERROR, not a pass (P-35).

Usage: verify_quotes_t177.py <repo-root>
"""
import glob
import os
import sys

repo = sys.argv[1]
rig = repo + '/.softhouse/capture/t177-so-nondeterminism'
docs = [repo + '/.softhouse/reviews/T177-stackoverflow-nondeterminism.md',
        repo + '/.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T177.md']

corpus = []
for p in sorted(glob.glob(rig + '/out/ANALYSIS-*.txt')) + sorted(glob.glob(rig + '/out/*/run-index.txt')) \
        + sorted(glob.glob(rig + '/out/jvm-defaults.txt')):
    corpus.append((os.path.relpath(p, repo), open(p, errors='replace').read()))
if not corpus:
    sys.exit('ERROR: no analysis transcripts found to check against (P-35)')

checked = missing = 0
for doc in docs:
    if not os.path.exists(doc):
        print('note: %s does not exist yet, skipped' % os.path.relpath(doc, repo))
        continue
    infence = False
    for lineno, raw in enumerate(open(doc, errors='replace'), 1):
        line = raw.rstrip('\n')
        if line.strip().startswith('```'):
            infence = not infence
            continue
        if not infence:
            continue
        if not line.strip():
            continue
        checked += 1
        hit = any(line in text for _, text in corpus)
        if not hit:
            missing += 1
            print('  NOT FOUND in any transcript: %s:%d  %r' % (os.path.relpath(doc, repo), lineno, line))

print('P-46 QUOTE CHECK: %d fenced line(s) checked, %d not found in any committed transcript'
      % (checked, missing))
if checked == 0:
    print('ERROR: zero lines checked — a quote check that inspects nothing is a FAILURE (P-35)')
    sys.exit(1)
sys.exit(1 if missing else 0)
