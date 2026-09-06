#!/usr/bin/env python3
"""T493 — measure the FOOTPRINT classifier against the naive SUBJECT-KEYWORD
classifier over this repository's entire real history.

B-11 and P-104 record what happens when a guard keys on a word list:
guard_no_float_in_vectors matched words and was defeated by rewording; T528
defeated T527's anchor rule with a one-word reword. This script measures how
often a word list would have been wrong HERE, on real commits nobody planted.

Ground truth = the changed-file footprint (what the commit actually did).
Candidate  = the commit subject (what the commit says it did).
"""
import re, subprocess, sys, collections

BOOK_PATH = re.compile(r'^\.softhouse/(LOCK|RESUME\.md)$|^\.softhouse/(state|logs|runs)/')
# The naive guard someone would plausibly write: bookkeeping words in the subject.
NAIVE = re.compile(r'\b(lock|locked|reconcil\w*|release[ds]?|checkpoint\w*|wrapper|'
                   r'state|banner|bookkeep\w*|no-?op|housekeep\w*)\b', re.I)

ref = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
raw = subprocess.run(['git','log',ref,'--no-merges','--name-only',
                      '--format=@@%H|%cI|%s'], capture_output=True, text=True).stdout

commits, cur = [], None
for line in raw.split('\n'):
    if line.startswith('@@'):
        if cur: commits.append(cur)
        sha, ts, subj = line[2:].split('|', 2)
        cur = {'sha': sha, 'ts': ts, 'subj': subj, 'files': []}
    elif line.strip() and cur is not None:
        cur['files'].append(line)
if cur: commits.append(cur)

for c in commits:
    c['truth'] = 'REAL' if any(not BOOK_PATH.search(f) for f in c['files']) else 'BOOK'
    c['naive'] = 'BOOK' if NAIVE.search(c['subj']) else 'REAL'

m = collections.Counter((c['truth'], c['naive']) for c in commits)
n = len(commits)
tb, tr = m[('BOOK','BOOK')], m[('REAL','REAL')]
fn = m[('BOOK','REAL')]   # bookkeeping commit whose SUBJECT looks real -> MISSED OUTAGE
fp = m[('REAL','BOOK')]   # real commit whose SUBJECT looks like bookkeeping -> FALSE ALARM

print(f"ref={ref}   non-merge commits analysed: {n}")
print(f"footprint truth: REAL={sum(1 for c in commits if c['truth']=='REAL')}  "
      f"BOOK={sum(1 for c in commits if c['truth']=='BOOK')}\n")
print("NAIVE SUBJECT-KEYWORD CLASSIFIER, graded against the footprint truth")
print(f"  agree                                     : {tb+tr}  ({100*(tb+tr)/n:.1f}%)")
print(f"  FALSE NEGATIVE (BOOK commit, subject reads REAL): {fn}  ({100*fn/n:.2f}%)")
print( "      -> the guard believes work happened. THE OUTAGE IS MISSED. This is the")
print( "         reviewer's 'bookkeeping fire whose subject looks real' attack, and it")
print( "         occurs naturally in this history without anyone planting it.")
print(f"  FALSE POSITIVE (REAL commit, subject reads BOOK): {fp}  ({100*fp/n:.2f}%)")
print( "      -> the guard cries RED on a productive fire. This is the reviewer's")
print( "         'real fire whose subject looks like bookkeeping' attack.\n")

print("FOOTPRINT CLASSIFIER (the one shipped in no-op-fire-streak.sh)")
print(f"  FALSE NEGATIVE : 0 / {n}   FALSE POSITIVE : 0 / {n}")
print( "  ...BY CONSTRUCTION, AND THAT IS A CAVEAT, NOT A BOAST. The footprint IS the")
print( "  ground truth here, so this row is definitionally 0 and proves nothing on its")
print( "  own. What it does establish is INDEPENDENCE: the subject line is never an")
print( "  input, so neither reword attack can move a commit across the line. The")
print( "  footprint classifier is graded against EXTERNAL truth in windows.md instead:")
print( "  the recorded outage windows, where it must report 0 real, and the recorded")
print( "  productive windows, where it must report many.\n")

print("WORKED EXAMPLES — real commits that defeat the word list (first 8 of each):")
print("\n  FALSE NEGATIVES — bookkeeping, but the subject reads as real work:")
for c in [c for c in commits if c['truth']=='BOOK' and c['naive']=='REAL'][:8]:
    print(f"    {c['sha'][:8]} {c['ts'][:16]}  files={c['files']}")
    print(f"             subject: {c['subj'][:96]}")
print("\n  FALSE POSITIVES — real work, but the subject reads as bookkeeping:")
for c in [c for c in commits if c['truth']=='REAL' and c['naive']=='BOOK'][:8]:
    print(f"    {c['sha'][:8]} {c['ts'][:16]}  {len(c['files'])} file(s), e.g. {c['files'][:3]}")
    print(f"             subject: {c['subj'][:96]}")
