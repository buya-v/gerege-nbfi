#!/usr/bin/env python3
# =============================================================================================
# T442 -- THE CLASS SWEEP FOR C-T440-1.
#
# THE CLASS. An instrument that searches the repository with a probe token SPELLED AS A LITERAL
# IN ITS OWN TRACKED SOURCE changes meaning the moment it is committed, because the search then
# finds the searcher. `t424-comment-claims-drive.sh` did exactly that: its no-match control
# searched `.softhouse` for `zzq-no-such-token-t424`, a string that existed in exactly one
# tracked file -- the control itself -- so the control scored "found", and the drive shipped a
# transcript its own committed code cannot produce.
#
# THE TWO DIRECTIONS, AND THEY ARE NOT EQUALLY DANGEROUS:
#
#   * probe expected ABSENT (rc 1 / count 0) -- the self-match makes it PRESENT, the check
#     fires, the drive goes red on a healthy tree. FAIL-CLOSED: noisy, visible, harmless.
#     This is C-T440-1.
#
#   * probe expected PRESENT (rc 0 / count > 0) -- the self-match SATISFIES the check whatever
#     the corpus contains. The assertion passes VACUOUSLY. FAIL-OPEN, silent, and the half
#     worth hunting.
#
# THE SHARP DISCRIMINATOR, and the reason this census is short enough to adjudicate by hand:
# a literal probe only *matters* when the searching file's own bytes are what decide the
# result. So every candidate is re-run as a real `git grep -l` over its own corpus and split:
#
#   A1  SELF-ONLY   -- the searching file is the ONLY file in the corpus that contains the
#                      literal. The entire search result is manufactured by the searcher. Every
#                      such row is in the class, in one direction or the other.
#   A2  SELF+OTHERS -- the searcher matches, and so do other files. Harmless for a "present"
#                      assertion (the others carry it); still INVERTING for an "absent" one.
#
# A third shape exists and is counted: an instrument that EXCLUDES ITSELF from the pathspec to
# dodge the self-match. That repairs the row and opens a hole -- everything else under the
# excluded path stops being scanned. Counted as "immunised" and listed in full.
#
# WHAT THIS DOES NOT DO. It does not guess the direction: direction lives in what the script
# does with the status, which is prose, not syntax. Rows are printed with context and the
# adjudication is written down, per row, in `out/T442-CLASS-SWEEP-ADJUDICATION.md`.
#
# Exit 0 = the census ran and printed its counts. It is a MEASUREMENT, not a guard. Exit 2 = it
# could not measure, which is not a pass.
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

files = subprocess.run(['git', 'ls-files', '--', '.softhouse'],
                       cwd=REPO, capture_output=True, text=True).stdout.split('\n')
files = [f for f in files if f]
if not files:
    print('REFUSED: `git ls-files -- .softhouse` listed nothing', file=sys.stderr)
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


scripts = [f for f in files if is_script(f)]

# ---- detectors -----------------------------------------------------------------------------
# A search must be in COMMAND POSITION in a shell script: start of line, or after one of
# | ; & ( ` $( && || ! then do else = <(  -- otherwise the words are inside a message.
SHELL_SEARCH = re.compile(
    r'(?:^|[|;&(!]|(?<!\\)`|\$\(|<\(|=|\bthen\b|\bdo\b|\belse\b|\bif\b|\bxargs\b)\s*'
    r'(?:LC_ALL=\S+\s+|LANG=\S+\s+|[A-Za-z_]+=\S+\s+)*'
    r'((?:/usr/bin/)?git\s+grep|(?:/usr/bin/)?grep\s+-[A-Za-z]*[rR]\b|\brg\b|'
    r'(?:/usr/bin/)?git\s+ls-files)')
# In python, a search is executed through subprocess; require that on the line.
PY_EXEC = re.compile(r'subprocess|check_output|Popen|\brun\(|_git\(|_run\(')
PY_SEARCH = re.compile(r"['\"]git['\"]\s*,\s*['\"](?:grep|ls-files)['\"]|git\s+grep|git\s+ls-files")
QUOTED = re.compile(r"""'([^']{2,})'|"([^"]{2,})\"""")
VAR = re.compile(r'\$[A-Za-z_{(@*0-9]|%[sd]|\{[A-Za-z_]')
CMD_WORDS = ('git', 'grep', 'egrep', 'fgrep', 'rg', 'ag', '/usr/bin/grep', '/usr/bin/git',
             '/bin/grep', 'ls-files', 'xargs', 'sudo', 'command', 'time')
unparsed = []


def cut_at_pipe(frag):
    """the fragment up to the first UNQUOTED | > ; or & -- the search command's own words"""
    out, q = [], None
    i = 0
    while i < len(frag):
        c = frag[i]
        if q:
            if c == q:
                q = None
            elif c == '\\' and q == '"':
                out.append(c)
                i += 1
                if i < len(frag):
                    out.append(frag[i])
                    i += 1
                continue
            out.append(c)
        elif c in ('"', "'"):
            q = c
            out.append(c)
        elif c in '|>;&':
            break
        else:
            out.append(c)
        i += 1
    return ''.join(out)


def pattern_operands(frag, where):
    """the PATTERN operand(s) of a grep-family call: not options, not pathspecs, not messages.

    Returns None when the fragment cannot be tokenised -- counted, not silently dropped."""
    frag = cut_at_pipe(frag)
    try:
        toks = shlex.split(frag, posix=True)
    except ValueError:
        unparsed.append(where)
        return None
    pats, i = [], 0
    # step past env assignments and the command words themselves
    while i < len(toks) and (toks[i] in CMD_WORDS or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', toks[i])):
        if toks[i] == 'ls-files':          # ls-files takes PATHSPECS, never a pattern
            return []
        i += 1
    while i < len(toks):
        t = toks[i]
        if t == '--':                      # everything after is a pathspec
            break
        if t in ('-e', '-f', '--regexp', '--file'):
            if i + 1 < len(toks):
                pats.append(toks[i + 1])
                i += 2
                continue
            break
        if t.startswith('-') and t != '-':
            i += 1
            continue
        pats.append(t)                     # the first bare operand is the pattern
        break
    return pats


UNKNOWN = ['<runtime>']


def py_pattern_operands(frag):
    """python subprocess form: the quoted strings between the `grep` element and `--`."""
    head = re.split(r"['\"]--['\"]", frag)[0]
    head = re.sub(r"^.*?['\"]grep['\"]\s*,?", '', head, count=1) or head
    out = []
    for mm in QUOTED.finditer(head):
        t = mm.group(1) if mm.group(1) is not None else mm.group(2)
        if t is None or t.startswith('-') or VAR.search(t):
            continue
        out.append(t)
    return out[:2]


def pathspec_of(frag):
    """operands after a bare `--`; [] = no pathspec given; UNKNOWN = built at run time."""
    m = re.search(r'\s--\s+(.*)$', cut_at_pipe(frag))
    if not m:
        m = re.search(r"['\"]--['\"]\s*,\s*(.*)$", frag)   # python list form
        if not m:
            return []
    tail = m.group(1)
    for cut in ('|', '>', ';', '&&', '||', '2>'):
        tail = tail.split(cut)[0]
    out, runtime_spec = [], False
    for t in re.split(r'[\s,\]\[)]+', tail):
        t = t.strip('\'"')
        if not t:
            continue
        if t.startswith('$') or '$' in t:
            runtime_spec = True
            continue
        out.append(t)
    if runtime_spec and not out:
        return UNKNOWN
    return out


def corpus_of(path, line):
    """(includes_self, pathspec_list_or_None, why)"""
    specs = pathspec_of(line)
    if specs is UNKNOWN:
        return False, [], 'pathspec is built at RUN TIME -- not decidable here (blind spot)'
    if 'git grep' in line or 'git ls-files' in line:
        if not specs:
            return True, [], 'whole tracked tree (no pathspec)'
        for s in specs:
            if s.startswith(':!') or s.startswith(':(exclude)'):
                body = s.replace(':(exclude)', '').lstrip(':!')
                if path.startswith(body.rstrip('/')):
                    return False, specs, 'EXCLUDED by pathspec %r' % s
        for s in specs:
            if s in ('.', './'):
                return True, specs, 'pathspec . covers it'
            if s and path.startswith(s.rstrip('/')):
                return True, specs, 'pathspec %r covers it' % s
        return False, specs, 'pathspec %s does not cover it' % specs
    for tok in re.split(r'\s+', line):
        t = tok.strip('\'"')
        if t in ('.', './'):
            return True, ['.'], 'recursive grep over .'
        if t.startswith('.softhouse') and path.startswith(t.rstrip('/')):
            return True, [t], 'recursive grep over %r' % t
    return False, specs, 'no directory operand covering it'


def family(path):
    """the task directory a file belongs to, e.g. .softhouse/reviews/t367-review-t363"""
    parts = path.split('/')
    return '/'.join(parts[:3]) if len(parts) >= 3 else '/'.join(parts[:2])


def matching_files(lit, specs):
    """which corpus files does `git grep -l -F` actually match?"""
    cmd = ['git', 'grep', '-l', '-F', '-e', lit]
    real = [s for s in specs if not s.startswith(':')] or []
    if real:
        cmd += ['--'] + real
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if p.returncode >= 2:
        return None
    return [f for f in p.stdout.split('\n') if f]


# ---- sweep ---------------------------------------------------------------------------------
A1, A2, runtime, immunised, elsewhere = [], [], [], [], []
searched_files, search_calls = 0, 0

for path in scripts:
    full = os.path.join(REPO, path)
    try:
        body = open(full, encoding='utf-8', errors='replace').read()
    except OSError:
        continue
    lines = body.split('\n')
    is_py = path.endswith('.py')
    hit_here = False
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith('#'):
            continue
        if is_py:
            m = PY_SEARCH.search(line)
            if not (PY_EXEC.search(line) and m):
                continue
            at = m.start()
        else:
            m = SHELL_SEARCH.search(line)
            if not m:
                continue
            at = m.start(1)
        search_calls += 1
        hit_here = True
        frag = line[at:]
        inc, specs, why = corpus_of(path, frag)
        ctx = '\n'.join('      %5d| %s' % (n, lines[n - 1])
                        for n in range(max(1, i - 2), min(len(lines), i + 2) + 1))
        if not inc:
            (immunised if why.startswith('EXCLUDED') else elsewhere).append(
                (path, i, line.strip(), why))
            continue
        if is_py:
            lits = py_pattern_operands(frag)
        else:
            lits = pattern_operands(frag, '%s:%d' % (path, i))
        if lits is None:
            runtime.append((path, i, line.strip(), why + ' / UNPARSED (blind spot, counted)'))
            continue
        lits = [t for t in lits if len(t) >= 2 and not VAR.search(t)]
        if not lits:
            runtime.append((path, i, line.strip(), why))
            continue
        placed = False
        for lit in lits:
            if lit not in body:
                continue
            hits = matching_files(lit, specs)
            if hits is None:
                continue
            row = (path, i, lit, why, body.count(lit), hits, ctx)
            if hits == [path]:
                A1.append(row)
            elif path in hits:
                A2.append(row)
            else:
                continue
            placed = True
        if not placed:
            runtime.append((path, i, line.strip(), why + ' / no self-matching literal'))
    if hit_here:
        searched_files += 1

# ---- report --------------------------------------------------------------------------------
HEAD = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
print('=' * 96)
print('T442 SELF-MATCHING PROBE CENSUS  --  the C-T440-1 class, swept over .softhouse/')
print('=' * 96)
print('repo                      : %s' % REPO)
print('commit                    : %s' % HEAD)
print('tracked files .softhouse/ : %d' % len(files))
print('of them, scripts          : %d  (*.sh *.py *.bash *.zsh, or a #! first line)' % len(scripts))
print('scripts with >=1 search   : %d' % searched_files)
print('search invocations found  : %d' % search_calls)
print()
print('WHERE I LOOKED, AND WHERE I DID NOT -- so that "none found" is a statement about this')
print('search and not about the world. Corpus: TRACKED files under `.softhouse/` only. Not')
print('`docs/`, not `.claude/`, not untracked files, not the Fineract checkout. A search counts')
print('only in COMMAND POSITION (shell) or on a line that also executes a subprocess (python).')
print('BLIND SPOTS, named: a search continued onto the next line; a pattern held in a variable')
print('assigned from a literal earlier (lands in RUNTIME, counted safe when it may not be); a')
print('pathspec built at run time; `find -exec grep`; a search performed by a non-script; and')
print('`git grep` invoked through a shell helper function whose name I do not know.')
print('ADDED BY T452 [F-T447-5, F-T447-4, F-T447-3] -- three ways THIS census measures a row with')
print('an instrument that is not the row\'s own:')
print('  * matching_files() re-runs EVERY row as `git grep -l -F` -- fixed-string, case-SENSITIVE')
print('    -- discarding the row\'s own -i/-E/-w/-P. For a2-33-dec2-rev5/sweep.sh, whose command')
print('    is `git grep -c -I -i -E`, this reports 2 files where the row itself matches 11. The')
print('    A1/A2 boundary is drawn by that function, so self_only / self_plus_others are computed')
print('    under the wrong matcher. It moves none of the four adjudicated members (each re-checked')
print('    by hand) but the next reader should not take the split as the rows\' own.')
print('  * IMMUNISATION is detected only as a `:!` / `:(exclude)` PATHSPEC, and cut_at_pipe()')
print('    truncates each line at the first unquoted `|` before anything else is examined -- so')
print('    the same self-exclusion spelled `| grep -v <own task dir>` is invisible BY')
print('    CONSTRUCTION. Three such rows exist in two files. `immunised = 0` is a statement about')
print('    one spelling.')
print('  * THIS CENSUS IS A MEMBER OF THE CLASS IT CENSUSES. Committing its own transcript makes')
print('    that transcript a tracked carrier of the probes below, which demotes A1 rows to A2 and')
print('    collapses family_only. The counts on the RESULT line are therefore facts about the')
print('    commit named above and about no other tree. Quote them WITH that commit, and prefer')
print('    the member set (paths and lines), which does not drift.')
print()


def dump(title, rows, note):
    print('-' * 96)
    print('%s  (%d rows, %d files)' % (title, len(rows), len({r[0] for r in rows})))
    print('   %s' % note)
    print('-' * 96)
    by = {}
    for r in rows:
        by.setdefault(r[0], []).append(r)
    for p in sorted(by):
        print('\n%s' % p)
        for (_, ln, lit, why, n, hits, ctx) in by[p]:
            print('  line %-5d  literal occurs %d time(s) in this file   [%s]' % (ln, n, why))
            print('  probe   : %r' % lit)
            fam = family(p)
            fam_only = bool(hits) and all(family(h) == fam for h in hits)
            print('  corpus files matching it: %d  %s'
                  % (len(hits), hits if len(hits) <= 4 else hits[:4] + ['...']))
            if fam_only:
                print('  *** EVERY match lies inside the searcher\'s OWN task directory (%s):'
                      % fam)
                print('      a PRESENT-assertion here would be satisfied only by the author\'s own')
                print('      artefacts -- the VACUOUS-PASS / fail-OPEN shape. Adjudicate the direction.')
            print(ctx)
    print()


dump('A1. SELF-ONLY -- the searching file is the ONLY corpus file containing the probe', A1,
     'Every row here is in the class. Direction adjudicated in out/T442-CLASS-SWEEP-ADJUDICATION.md')
dump('A2. SELF + OTHERS -- the searcher matches, and so do other files', A2,
     'Inverts an ABSENT-assertion; harmless to a PRESENT-assertion. Adjudicated per row.')

print('-' * 96)
print('B. RUNTIME / NON-LITERAL PATTERN, corpus includes the searcher  (%d rows)' % len(runtime))
print('   The repaired shape: no tracked byte sequence can equal the probe.')
print('-' * 96)
for (path, ln, line, why) in runtime:
    print('  %s:%d  [%s]\n      %s' % (path, ln, why, line))
print()
print('  of which UNPARSED by shlex (a named blind spot, listed rather than swallowed): %d'
      % len(unparsed))
for u in unparsed:
    print('    %s' % u)
print()

print('-' * 96)
print('C. IMMUNISED -- the searcher EXCLUDES ITSELF from the pathspec  (%d rows)' % len(immunised))
print('   Repairs the row, opens a hole: everything else under the excluded path is unscanned.')
print('-' * 96)
for (path, ln, line, why) in immunised:
    print('  %s:%d  [%s]\n      %s' % (path, ln, why, line))
print()
print('D. searching a corpus that does not contain the searcher : %d rows (not in the class)'
      % len(elsewhere))
print()

fam_only_rows = [r for r in (A1 + A2)
                 if r[5] and all(family(h) == family(r[0]) for h in r[5])]
print('FAMILY-ONLY rows (every match inside the searcher\'s own task directory) : %d'
      % len(fam_only_rows))
for r in fam_only_rows:
    print('    %s:%d  probe %r  -> %d file(s) all under %s'
          % (r[0], r[1], r[2], len(r[5]), family(r[0])))
print()

print('=' * 96)
print('T442-CLASS-SWEEP-RESULT: scripts=%d searches=%d self_only=%d self_only_files=%d '
      'self_plus_others=%d family_only=%d unparsed=%d runtime=%d immunised=%d elsewhere=%d'
      % (len(scripts), search_calls, len(A1), len({r[0] for r in A1}), len(A2),
         len(fam_only_rows), len(unparsed), len(runtime), len(immunised), len(elsewhere)))
print('=' * 96)
sys.exit(0)
