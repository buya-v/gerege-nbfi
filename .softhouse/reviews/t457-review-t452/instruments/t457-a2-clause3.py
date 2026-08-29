#!/usr/bin/env python3
# =============================================================================================
# T457 -- CLOSING T452'S OWN DECLARED HOLE.
#
# T452's fail-open definition has three clauses, and it declares the third one unsound in its
# own handoff:
#
#   "Clause (3) of my fail-open definition treats a row as safe when ANY other file carries the
#    probe -- if those are all same-task transcripts in another directory, it is still
#    effectively self-satisfying. 34 A2 rows are exposed to it; I re-read only the
#    self-only/family-only rows, not all 34."
#
# Every previous "the remaining rows are safe" claim in this chain has been reached, so this
# instrument reads them. For each row of the `A2. SELF + OTHERS` bucket of T452's own transcript
# it re-runs the row's OWN matcher -- the flags parsed back off the transcript, not a blanket
# `-F` -- and partitions the carriers by TASK NAMESPACE, the two path components under the
# instrument root (`capture/t388-accrual-capture`, `reviews/t367-review-t363`, ...), plus a
# single bucket for carriers OUTSIDE that root, which is the strongest independence evidence
# available: a file no task in this chain wrote.
#
# A row is INDEPENDENTLY CARRIED iff a carrier lies outside the instrument root, or in three or
# more namespaces that are not the searcher's own. Anything else is PRINTED IN FULL for a hand
# read and is never counted safe silently -- the same discipline T452 applied to its UNDECIDED
# rows, applied to the clause T452 says it did not discharge.
#
# TWO THINGS THIS INSTRUMENT ALSO MEASURES, both of which narrow the "34 exposed rows" figure:
#   * how many A2 rows are ENFORCED at all. Clause (1) gates the whole definition, so a row that
#     reaches no control-flow decision cannot be fail-open however self-satisfying its probe is.
#   * how many A2 rows are not searches at all -- `say`/`echo` message text containing the words
#     `git grep` / `git ls-files`, which T452's SHELL_SEARCH regex matches in command position.
#     T452 names this precision limit for its `unresolved_var` bucket and not for this one.
#
# EXIT 0 = it ran and printed. 1 = a row needing a hand read was found and is printed.
# EXIT 2 = it could not measure, which is NOT a pass.
# =============================================================================================
import collections
import os
import re
import subprocess
import sys

if len(sys.argv) != 3:
    sys.stderr.write('usage: t457-a2-clause3.py <subject-tree> <T452-classify-transcript>\n')
    sys.stderr.write('  Both are REQUIRED parameters. A path that stops resolving must be a\n')
    sys.stderr.write('  hard exit, never a silently empty scan.\n')
    sys.exit(2)

TREE, TRANS = sys.argv[1], sys.argv[2]
for p in (TREE, TRANS):
    if not os.path.exists(p):
        sys.stderr.write('REFUSED (exit 2): %s does not resolve\n' % p)
        sys.exit(2)

ROOT = '.softhouse'          # assembled, never spelled with a child path

head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=TREE,
                      capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=TREE,
                       capture_output=True, text=True).stdout.split('\n')
dirty = len([d for d in dirty if d])
if not head:
    sys.stderr.write('REFUSED (exit 2): %s is not a git work tree\n' % TREE)
    sys.exit(2)

text = open(TRANS, errors='replace').read().split('\n')
start = end = None
for i, line in enumerate(text):
    if line.startswith('A2. SELF + OTHERS'):
        start = i
    elif start is not None and line.startswith('MEMBER SET'):
        end = i
        break
if start is None or end is None:
    sys.stderr.write('REFUSED (exit 2): could not delimit the A2 section of the transcript.\n')
    sys.stderr.write('  Its format has changed and this instrument would scan nothing.\n')
    sys.exit(2)

rows, cur = [], None
for line in text[start:end]:
    m = re.match(r'^(\S+:\d+)\s+\[(.*)\]\s*$', line)
    if m:
        cur = {'row': m.group(1), 'scope': m.group(2)}
        rows.append(cur)
        continue
    if cur is None:
        continue
    m = re.match(r'^\s+probe\s+:\s+(.*?)\s+\((?:literal in source|resolved from [^)]*)\)\s*$', line)
    if m:
        cur['probe'] = m.group(1)
    m = re.match(r'^\s+matcher\s+:\s+git grep (.*?)\s+<-', line)
    if m:
        cur['flags'] = [f for f in m.group(1).split() if f != '-l']
    m = re.match(r'^\s+direction:\s+(\S+)\s+enforced:\s+(\S+)', line)
    if m:
        cur['dir'], cur['enf'] = m.group(1), m.group(2)

if len(rows) < 5:
    sys.stderr.write('REFUSED (exit 2): parsed only %d A2 rows. A scan over nothing is not a\n'
                     % len(rows))
    sys.stderr.write('  clean sheet.\n')
    sys.exit(2)


def unquote(p):
    p = (p or '').strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in "'\"":
        p = p[1:-1]
    return p


def namespace(path):
    parts = path.split('/')
    if parts[0] != ROOT:
        return '(outside the instrument root)'
    return '/'.join(parts[1:3]) if len(parts) >= 3 else '/'.join(parts[:2])


def source_line(rel, n):
    try:
        with open(os.path.join(TREE, rel), errors='replace') as fh:
            body = fh.read().split('\n')
    except OSError:
        return ''
    return body[n - 1] if 0 < n <= len(body) else ''


# a row whose "search" is the message text of a say/echo/printf is not a search at all
NOT_A_SEARCH = re.compile(r'^\s*(?:say|echo|printf|warn)\b')

print('=' * 96)
print('T457 -- INDEPENDENT-CARRIER READ OF EVERY A2 ROW (T452 clause 3)')
print('subject tree : %s' % TREE)
print('commit       : %s   dirty: %d path(s)' % (head, dirty))
print('transcript   : %s' % TRANS)
print('A2 rows      : %d' % len(rows))
print('=' * 96)
print()

hand, not_search = [], []
for r in rows:
    rel, ln = r['row'].rsplit(':', 1)
    src = source_line(rel, int(ln))
    r['src'] = src.strip()
    if NOT_A_SEARCH.match(src):
        r['verdict'] = 'NOT A SEARCH (message text of a say/echo/printf)'
        not_search.append(r)
        continue
    probe = unquote(r.get('probe'))
    if not probe:
        r['verdict'] = 'HAND-READ (probe not machine-readable from the transcript)'
        hand.append(r)
        continue
    cmd = ['git', 'grep', '-l'] + r.get('flags', ['-F']) + [probe, '--', '.']
    out = subprocess.run(cmd, cwd=TREE, capture_output=True, text=True).stdout
    carriers = [c for c in out.split('\n') if c]
    if not carriers:
        r['verdict'] = 'HAND-READ (the row matches nothing on this tree)'
        hand.append(r)
        continue
    own = namespace(rel)
    ns = collections.Counter(namespace(c) for c in carriers)
    foreign = {k: v for k, v in ns.items() if k != own}
    r['own'], r['foreign'], r['carriers'] = own, foreign, len(carriers)
    if '(outside the instrument root)' in foreign:
        r['verdict'] = 'INDEPENDENT (carried outside the instrument root)'
    elif len(foreign) >= 3:
        r['verdict'] = 'INDEPENDENT (%d foreign task namespaces)' % len(foreign)
    else:
        r['verdict'] = 'HAND-READ (%d foreign namespace(s) only)' % len(foreign)
        hand.append(r)

for r in rows:
    print('%-74s %-9s enf=%-4s %s' % (r['row'], r.get('dir'), r.get('enf'), r['verdict']))

enforced = [r for r in rows if r.get('enf') == 'YES']
present_enf = [r for r in enforced if r.get('dir') == 'PRESENT']
print()
print('-' * 96)
print('CLAUSE (1) GATES FIRST -- a row that reaches no control-flow decision cannot be fail-open')
print('  A2 rows marked ENFORCED by T452                : %d of %d' % (len(enforced), len(rows)))
print('  of those, PRESENT-direction                    : %d' % len(present_enf))
print('  A2 rows that are NOT SEARCHES AT ALL           : %d' % len(not_search))
for r in not_search:
    print('      %-74s %s' % (r['row'], r['src'][:70]))
print()
print('ROWS THIS INSTRUMENT WILL NOT CALL SAFE ON ITS OWN: %d' % len(hand))
for r in hand:
    print()
    print('  %s' % r['row'])
    print('    probe    : %s' % r.get('probe'))
    print('    direction: %-9s enforced: %s' % (r.get('dir'), r.get('enf')))
    print('    source   : %s' % r['src'][:110])
    if r.get('foreign') is not None:
        print('    own ns   : %s   carriers: %s' % (r.get('own'), r.get('carriers')))
        for k, v in sorted(r['foreign'].items()):
            print('      foreign: %-48s %d file(s)' % (k, v))
print()
print('=' * 96)
print('T457-CLAUSE3-RESULT: tree=%s%s a2_rows=%d independent=%d not_a_search=%d hand_read=%d'
      % (head[:8], '_clean' if dirty == 0 else '+%d_dirty' % dirty,
         len(rows), len(rows) - len(hand) - len(not_search), len(not_search), len(hand)))
print('=' * 96)
sys.exit(1 if hand else 0)
