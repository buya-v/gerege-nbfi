#!/usr/bin/env python3
# =============================================================================================
# T447 -- INDEPENDENT ATTACK ON T442's LARGEST SELF-DECLARED BLIND SPOT.
#
# T442's class census (`t442-selfmatching-probe-census.py`) put 131 of its 399 search rows into
# a bucket called RUNTIME and counted them SAFE. Its own handoff concedes the reason is
# SYNTAX ONLY:
#
#     "The census's 131 'runtime' rows are counted safe on syntax alone. A pattern held in a
#      variable that was assigned from a literal earlier in the same file would land there and
#      would still be in the class."
#
# A third of the corpus judged safe because a `$` appeared in the pattern operand is not a
# measurement, it is a deferral. This instrument does the deferred work for ONE level of
# indirection: it resolves `$VAR` in the pattern operand back to a LITERAL assignment earlier
# in the same file, and then asks the same question T442 asked of its literal rows --
#
#     does `git grep -l -F <resolved literal>` over that row's own corpus return the SEARCHING
#     FILE ITSELF?
#
# If it does, the row is in the C-T440-1 class and T442 missed it.
#
# DIRECTION is then adjudicated by hand from the printed context, exactly as T442 did, because
# direction lives in what the script does with the status and that is prose, not syntax.
#
# THIS INSTRUMENT'S OWN BLIND SPOTS, named so that "none found" is a statement about this search:
#   * one level of indirection only (VAR=$OTHER chains are reported UNRESOLVED, not safe);
#   * same-file assignments only (no sourced files, no exported environment);
#   * the last assignment textually BEFORE the search line wins -- loops and conditionals that
#     reassign are not modelled;
#   * RHS must be a pure literal: any `$`, backtick or `$(` makes it UNRESOLVED;
#   * corpus is tracked files under `.softhouse/`, as T442's was, PLUS a whole-repo widening
#     pass reported separately;
#   * the row set is taken from T442's own RUNTIME bucket, so any search T442's detector never
#     saw at all is invisible here too. That gap is measured separately by the widening pass.
#
# Exit 0 = the sweep ran and printed its counts. It is a MEASUREMENT, not a guard.
# Exit 2 = it could not measure, which is not a pass.
# =============================================================================================
import os
import re
import shlex
import subprocess
import sys

REPO = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                      capture_output=True, text=True).stdout.strip()
if not REPO:
    print('REFUSED: not in a git repository', file=sys.stderr)
    sys.exit(2)

TRANSCRIPT = sys.argv[1] if len(sys.argv) > 1 else None
if not TRANSCRIPT or not os.path.isfile(TRANSCRIPT):
    print('REFUSED: usage: %s <T442-CLASS-SWEEP.txt>' % sys.argv[0], file=sys.stderr)
    sys.exit(2)

text = open(TRANSCRIPT, encoding='utf-8', errors='replace').read()

# ---- pull T442's RUNTIME bucket out of its own transcript, by content ------------------------
m = re.search(r'^B\. RUNTIME / NON-LITERAL PATTERN.*?\(\s*(\d+) rows\)\s*$',
              text, re.M)
if not m:
    print('REFUSED: could not locate T442\'s RUNTIME section header in the transcript',
          file=sys.stderr)
    sys.exit(2)
declared = int(m.group(1))
block = text[m.end():]
end = re.search(r'^C\. IMMUNISED', block, re.M)
if not end:
    print('REFUSED: could not locate the end of the RUNTIME section', file=sys.stderr)
    sys.exit(2)
block = block[:end.start()]

rows = []
for rm in re.finditer(r'^  (\.softhouse/\S+?):(\d+)  \[(.*?)\]\n      (.*)$', block, re.M):
    rows.append((rm.group(1), int(rm.group(2)), rm.group(3), rm.group(4)))

if len(rows) != declared:
    print('REFUSED: parsed %d RUNTIME rows but the transcript declares %d -- refusing to '
          'report a partial sweep as a complete one' % (len(rows), declared), file=sys.stderr)
    sys.exit(2)

ASSIGN = re.compile(r'''^\s*(?:local\s+|readonly\s+|declare\s+(?:-\w+\s+)*|export\s+)?
                        ([A-Za-z_][A-Za-z0-9_]*)=(.*)$''', re.X)
VARREF = re.compile(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?')
DYNAMIC = re.compile(r'[$`]')
CMD_WORDS = ('git', 'grep', 'egrep', 'fgrep', 'rg', 'ag', '/usr/bin/grep', '/usr/bin/git',
             '/bin/grep', 'ls-files', 'xargs', 'sudo', 'command', 'time', 'LC_ALL=C')


def literal_rhs(rhs):
    """the RHS as a literal string, or None if anything about it is dynamic"""
    rhs = rhs.strip()
    # strip a trailing comment only when it is outside quotes -- cheap and conservative:
    # if stripping changes quote balance, keep the original.
    if DYNAMIC.search(rhs):
        return None
    try:
        toks = shlex.split(rhs, posix=True, comments=True)
    except ValueError:
        return None
    if len(toks) != 1:
        return None
    return toks[0]


def resolve(path, lineno, frag):
    """resolve $VARs in the search fragment to same-file literal assignments.

    returns (dict var->literal, list of unresolved var names)"""
    full = os.path.join(REPO, path)
    try:
        lines = open(full, encoding='utf-8', errors='replace').read().split('\n')
    except OSError:
        return {}, []
    wanted = []
    for vm in VARREF.finditer(frag):
        v = vm.group(1)
        if v not in wanted:
            wanted.append(v)
    got, missing = {}, []
    for v in wanted:
        lit = None
        for n in range(min(lineno, len(lines)) - 1, -1, -1):
            am = ASSIGN.match(lines[n])
            if am and am.group(1) == v:
                lit = literal_rhs(am.group(2))
                break
        if lit is not None and len(lit) >= 2:
            got[v] = lit
        else:
            missing.append(v)
    return got, missing


def pattern_operand_vars(frag):
    """which $VARs sit in PATTERN position (not pathspec, not option) of a grep-family call"""
    head = re.split(r'\s--\s', frag)[0]
    head = re.split(r'(?<!\\)[|>;]', head)[0]
    out, i = [], 0
    try:
        toks = shlex.split(head, posix=False)
    except ValueError:
        toks = head.split()
    while i < len(toks) and (toks[i] in CMD_WORDS
                             or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', toks[i])):
        if toks[i] == 'ls-files':
            return []
        i += 1
    while i < len(toks):
        t = toks[i]
        if t in ('-e', '-f', '--regexp', '--file'):
            if i + 1 < len(toks):
                out.append(toks[i + 1])
            i += 2
            continue
        if t.startswith('-') and t != '-':
            i += 1
            continue
        out.append(t)
        break
    return out


def specs_of(frag):
    mm = re.search(r'\s--\s+(.*)$', frag)
    if not mm:
        return []
    tail = mm.group(1)
    for cut in ('|', '>', ';', '&&', '||', '2>'):
        tail = tail.split(cut)[0]
    out = []
    for t in re.split(r'[\s,\]\[)]+', tail):
        t = t.strip('\'"')
        if not t or t.startswith('$') or '$' in t or t.startswith(':'):
            continue
        out.append(t)
    return out


def grep_l(lit, specs):
    cmd = ['git', 'grep', '-l', '-F', '-e', lit]
    if specs:
        cmd += ['--'] + specs
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if p.returncode >= 2:
        return None
    return [f for f in p.stdout.split('\n') if f]


print('=' * 96)
print('T447 -- VARIABLE-INDIRECT SELF-MATCHING PROBES  (T442 RUNTIME bucket, re-opened)')
print('=' * 96)
HEAD = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
print('repo      : %s' % REPO)
print('commit    : %s' % HEAD)
print('transcript: %s' % TRANSCRIPT)
print('T442 RUNTIME rows re-opened: %d (transcript declares %d -- MATCH)' % (len(rows), declared))
print()

resolved_rows, unresolved_rows, novar_rows = [], [], []
class_members = []

for (path, lineno, why, line) in rows:
    at = 0
    frag = line
    pvars = pattern_operand_vars(frag)
    pat_var_names = []
    for p in pvars:
        pat_var_names += [vm.group(1) for vm in VARREF.finditer(p)]
    if not pat_var_names:
        novar_rows.append((path, lineno, why, line, pvars))
        continue
    got, missing = resolve(path, lineno, ' '.join(pvars))
    hit = False
    for v in pat_var_names:
        if v in got:
            lit = got[v]
            specs = specs_of(frag)
            hits = grep_l(lit, specs if specs else ['.softhouse'])
            if hits is None:
                continue
            resolved_rows.append((path, lineno, v, lit, hits, line))
            if path in hits:
                class_members.append((path, lineno, v, lit, hits, line))
            hit = True
    if not hit:
        unresolved_rows.append((path, lineno, why, line, pat_var_names, missing))

print('-' * 96)
print('R1. rows whose PATTERN operand contains no $VAR at all  (%d)' % len(novar_rows))
print('    T442 put these in RUNTIME for a different reason (short literal, ls-files, or no')
print('    self-matching literal). Listed so the partition is complete.')
print('-' * 96)
for (path, lineno, why, line, pvars) in novar_rows:
    print('  %s:%d  operand=%s' % (path, lineno, pvars))
    print('      %s' % line)
print()

print('-' * 96)
print('R2. PATTERN-operand $VARs RESOLVED to a same-file literal  (%d)' % len(resolved_rows))
print('-' * 96)
for (path, lineno, v, lit, hits, line) in resolved_rows:
    flag = '  *** SEARCHER IS IN ITS OWN HIT SET -- CLASS MEMBER' if path in hits else ''
    print('  %s:%d  $%s -> %r%s' % (path, lineno, v, lit, flag))
    print('      corpus hits: %d  %s' % (len(hits), hits if len(hits) <= 5 else hits[:5] + ['...']))
    print('      %s' % line)
print()

print('-' * 96)
print('R3. PATTERN-operand $VARs NOT resolvable to a same-file literal  (%d)' % len(unresolved_rows))
print('    UNRESOLVED IS NOT SAFE. These are the residual after one level of dataflow.')
print('-' * 96)
for (path, lineno, why, line, names, missing) in unresolved_rows:
    print('  %s:%d  vars=%s unresolved=%s' % (path, lineno, names, missing))
    print('      %s' % line)
print()

print('=' * 96)
print('T447-VARINDIRECT-RESULT: reopened=%d novar=%d resolved=%d unresolved=%d class_members=%d'
      % (len(rows), len(novar_rows), len(resolved_rows), len(unresolved_rows),
         len(class_members)))
print('=' * 96)
if class_members:
    print('CLASS MEMBERS T442 COUNTED SAFE:')
    for (path, lineno, v, lit, hits, line) in class_members:
        print('  %s:%d  $%s = %r  -> %d hit(s), including itself' % (path, lineno, v, lit, len(hits)))
sys.exit(0)
