#!/usr/bin/env python3
# =============================================================================================
# T447 -- TWO MORE INDEPENDENT ATTACKS ON T442's CLASS SWEEP.
#
# ATTACK 1 -- THE CORPUS RESTRICTION. T442's census walked TRACKED FILES UNDER `.softhouse/`
# ONLY and said so. That is a real restriction and "none found" outside it would be a statement
# about nothing. So: enumerate every tracked file in the WHOLE repository that could be a
# searcher (extension or `#!` first line) and report how many lie outside `.softhouse/`. If the
# answer is zero the restriction costs nothing; if it is not, T442's sweep has an unmeasured
# remainder.
#
# ATTACK 2 -- `immunised = 0`. T442 reports that NO instrument dodges its own self-match, and
# invites the reader to read that as "nobody has done it". Its detector recognises exactly ONE
# mechanism: a `:!path` / `:(exclude)path` PATHSPEC. Its `cut_at_pipe()` truncates the line at
# the first unquoted `|`, so a searcher that self-excludes by POST-FILTERING its own output --
#     git grep ... -- . | grep -v '<its own path>'
# is invisible to it BY CONSTRUCTION. That is the same dodge with a different spelling, and it
# has the same consequence: everything else matching that filter stops being reported. This
# sweep looks for BOTH mechanisms, over the whole line, and counts them separately.
#
# BLIND SPOTS OF THIS INSTRUMENT, named: it matches self-exclusion only when the filter argument
# is a substring of the searcher's own path or of its task directory name; a filter built from a
# variable is reported UNRESOLVED, not safe; and it reads single lines, so a filter on a
# continuation line is missed here too.
#
# Exit 0 = measured. Exit 2 = could not measure.
# =============================================================================================
import os
import re
import subprocess
import sys

REPO = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                      capture_output=True, text=True).stdout.strip()
if not REPO:
    print('REFUSED: not in a git repository', file=sys.stderr)
    sys.exit(2)

all_files = [f for f in subprocess.run(['git', 'ls-files'], cwd=REPO,
                                       capture_output=True, text=True).stdout.split('\n') if f]
if not all_files:
    print('REFUSED: `git ls-files` listed nothing', file=sys.stderr)
    sys.exit(2)

SCRIPT_EXT = ('.sh', '.py', '.bash', '.zsh')


def is_script(path):
    if path.endswith(SCRIPT_EXT):
        return True
    try:
        with open(os.path.join(REPO, path), 'rb') as fh:
            return fh.read(2) == b'#!'
    except OSError:
        return False


scripts = [f for f in all_files if is_script(f)]
inside = [f for f in scripts if f.startswith('.softhouse/')]
outside = [f for f in scripts if not f.startswith('.softhouse/')]

print('=' * 96)
print('T447 -- WIDENING + IMMUNISATION RE-COUNT')
print('=' * 96)
HEAD = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
print('repo   : %s' % REPO)
print('commit : %s' % HEAD)
print()
print('-' * 96)
print('ATTACK 1 -- what T442\'s `.softhouse/`-only corpus restriction actually costs')
print('-' * 96)
print('  tracked files, whole repository : %d' % len(all_files))
print('  of them, candidate searchers    : %d' % len(scripts))
print('    inside  .softhouse/           : %d' % len(inside))
print('    OUTSIDE .softhouse/           : %d' % len(outside))
for f in outside:
    print('      %s' % f)
print()

SEARCH = re.compile(r'(?:git\s+grep|grep\s+-[A-Za-z]*[rR]\b|\brg\b|git\s+ls-files)')
EXCLUDE_PATHSPEC = re.compile(r"(?::!|:\(exclude\))([^\s'\"]+)")
POSTFILTER = re.compile(r"\|\s*(?:/usr/bin/|/bin/)?(?:grep|egrep|fgrep)\s+(?:-[A-Za-z]+\s+)*-\w*v\w*\s+"
                        r"""(?:-[A-Za-z]+\s+)*['"]?([^'"|]+)['"]?""")


def task_dir(path):
    parts = path.split('/')
    return parts[2] if len(parts) >= 3 else parts[-1]


pathspec_rows, postfilter_rows, unresolved_rows = [], [], []

for path in scripts:
    try:
        body = open(os.path.join(REPO, path), encoding='utf-8', errors='replace').read()
    except OSError:
        continue
    td = task_dir(path)
    base = os.path.basename(path)
    for i, line in enumerate(body.split('\n'), 1):
        if line.lstrip().startswith('#'):
            continue
        if not SEARCH.search(line):
            continue
        for m in EXCLUDE_PATHSPEC.finditer(line):
            body_spec = m.group(1)
            if path.startswith(body_spec.rstrip('/')) or td in body_spec or base in body_spec:
                pathspec_rows.append((path, i, body_spec, line.strip()))
        for m in POSTFILTER.finditer(line):
            arg = m.group(1).strip()
            if '$' in arg:
                unresolved_rows.append((path, i, arg, line.strip()))
                continue
            if arg and (arg in path or td in arg or (base and base in arg)):
                postfilter_rows.append((path, i, arg, line.strip()))

print('-' * 96)
print('ATTACK 2a -- self-exclusion by `:!` / `:(exclude)` PATHSPEC  (T442\'s "immunised")  : %d'
      % len(pathspec_rows))
print('-' * 96)
for r in pathspec_rows:
    print('  %s:%d  excludes %r\n      %s' % r)
if not pathspec_rows:
    print('  (none -- T442\'s count of 0 for THIS mechanism reproduces)')
print()

print('-' * 96)
print('ATTACK 2b -- self-exclusion by POST-PIPE `grep -v <own path/own task dir>`  : %d' % len(postfilter_rows))
print('   INVISIBLE to T442\'s census: its cut_at_pipe() truncates the line at the first')
print('   unquoted `|` before any of this is looked at.')
print('-' * 96)
for r in postfilter_rows:
    print('  %s:%d  filters out %r\n      %s' % r)
print()

print('-' * 96)
print('ATTACK 2c -- post-pipe `grep -v` whose argument is a VARIABLE (unresolved, not safe) : %d'
      % len(unresolved_rows))
print('-' * 96)
for r in unresolved_rows:
    print('  %s:%d  filters out %r\n      %s' % r)
print()

print('=' * 96)
print('T447-WIDEN-RESULT: tracked=%d scripts=%d inside_softhouse=%d outside_softhouse=%d '
      'immunised_pathspec=%d immunised_postpipe=%d immunised_unresolved=%d'
      % (len(all_files), len(scripts), len(inside), len(outside),
         len(pathspec_rows), len(postfilter_rows), len(unresolved_rows)))
print('=' * 96)
sys.exit(0)
