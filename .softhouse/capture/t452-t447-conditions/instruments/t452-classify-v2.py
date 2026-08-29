#!/usr/bin/env python3
# =============================================================================================
# T452 -- THE SELF-MATCHING PROBE CLASSIFICATION, RE-RUN WITH THE THREE HOLES T447 FOUND CLOSED.
#
# T442's census (`t442-selfmatching-probe-census.py`) established the class and did the hard
# part. T447 found three ways its classification is drawn with the wrong instrument. This is the
# re-run, not a replacement: same class, same corpus rule, same two directions.
#
#   F-T447-1  VARIABLE-INDIRECT PATTERNS.  T442 routes any pattern holding a `$VAR` into the
#             RUNTIME bucket and counts it safe ON SYNTAX ALONE. The T253/T266 blind-spot class.
#             HERE: one level of same-file dataflow is resolved -- `VAR='literal'` earlier in the
#             file -- and the row is re-classified with the literal it actually searches for. A
#             pattern assembled at run time (`$$`, `$RANDOM`, `date`, `printf`, command
#             substitution) is the CORRECT shape and is reported as such, separately from
#             "I could not resolve this", which is a blind spot and is listed row by row.
#
#   F-T447-5  THE ROW'S OWN FLAGS.  T442's `matching_files()` re-runs every row as
#             `git grep -l -F` (case-sensitive, fixed-string), discarding the row's own flags.
#             For a row spelled `-c -I -i -E` that is a different search, so `self_only` /
#             `self_plus_others` -- and therefore the whole A1/A2 split -- are computed under a
#             matcher that is not the row's matcher. HERE: the row's own `-i/-E/-F/-w/-P` are
#             parsed off the row and replayed.
#
#   F-T447-4  IMMUNISATION BY POST-PIPE FILTER.  T442 detects self-exclusion only as a `:!` /
#             `:(exclude)` PATHSPEC, and its `cut_at_pipe()` truncates the line before anything
#             else is looked at, so the same dodge spelled `| grep -v <own dir>` is invisible BY
#             CONSTRUCTION. HERE: the whole line is examined and both spellings are counted.
#
#   F-T447-3  THE CENSUS IS A MEMBER OF THE CLASS IT CENSUSES.  Publishing a transcript makes it
#             a new tracked carrier of the probes, which demotes A1 rows to A2 and collapses
#             family-only to 0. HERE: every count carries the tree it was taken on IN THE SAME
#             LINE, and a MEMBER SET -- paths and lines, which do not drift -- is printed
#             alongside the counts, which do. See the argument in the T452 handoff: excluding
#             one's own publication is the immunisation anti-pattern above, so this instrument
#             does NOT exclude it; it qualifies instead.
#
# WHAT A `fail_open` IS HERE, stated before it is counted, so the number has a definition:
#   a row is FAIL-OPEN iff  (1) its search result is CONSUMED by an enforcement -- an exit, an
#   abort, a refusal -- and not merely printed;  AND (2) the assertion is PRESENT-direction: it
#   is satisfied when the search FINDS something;  AND (3) it can be satisfied without the
#   property it asserts being true, which for a self-matching probe means every matching file is
#   the searcher itself (SELF-ONLY) or lies inside the searcher's own task directory
#   (FAMILY-ONLY).  Direction and enforcement are read from the eight lines following the search
#   and are reported as PRESENT / ABSENT / UNDECIDED. UNDECIDED rows are PRINTED IN FULL for
#   hand adjudication and counted as a named residual, never silently as safe.
#
# Exit 0 = it ran and printed its counts. It is a MEASUREMENT, not a guard.
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

# T452_ONLY: restrict the script list to paths containing this substring. Used by the a2-33
# drive to ask ONE question cheaply -- "is the repaired row still visible to this classifier?"
# It narrows the CORPUS OF SEARCHERS, never the corpus each row is matched against, and it
# REFUSES when it selects nothing, because a classifier over zero scripts would print a clean
# sheet.
ONLY = os.environ.get('T452_ONLY', '')
if ONLY:
    scripts = [f for f in scripts if ONLY in f]
    if not scripts:
        print('REFUSED: T452_ONLY=%r selected 0 scripts. A classification over nothing is not a'
              ' clean sheet.' % ONLY, file=sys.stderr)
        sys.exit(2)

SHELL_SEARCH = re.compile(
    r'(?:^|[|;&(!]|(?<!\\)`|\$\(|<\(|=|\bthen\b|\bdo\b|\belse\b|\bif\b|\bxargs\b)\s*'
    r'(?:LC_ALL=\S+\s+|LANG=\S+\s+|[A-Za-z_]+=\S+\s+)*'
    r'((?:/usr/bin/)?git\s+grep|(?:/usr/bin/)?grep\s+-[A-Za-z]*[rR]\b|\brg\b|'
    r'(?:/usr/bin/)?git\s+ls-files)')
PY_EXEC = re.compile(r'subprocess|check_output|Popen|\brun\(|_git\(|_run\(')
PY_SEARCH = re.compile(r"['\"]git['\"]\s*,\s*['\"](?:grep|ls-files)['\"]|git\s+grep|git\s+ls-files")
QUOTED = re.compile(r"""'([^']{2,})'|"([^"]{2,})\"""")
VAR = re.compile(r'\$[A-Za-z_{(@*0-9]|%[sd]|\{[A-Za-z_]')
CMD_WORDS = ('git', 'grep', 'egrep', 'fgrep', 'rg', 'ag', '/usr/bin/grep', '/usr/bin/git',
             '/bin/grep', 'ls-files', 'xargs', 'sudo', 'command', 'time')
# a pattern operand that is EXACTLY one variable reference, which is what T442 dropped
BARE_VAR = re.compile(r'^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?$')
# a same-file assignment of a plain single/double quoted literal
ASSIGN = re.compile(r"""^\s*([A-Za-z_][A-Za-z0-9_]*)=(?:'([^']*)'|"([^"$`]*)")\s*(?:#.*)?$""")
# an assignment whose right-hand side is built at run time -- the CORRECT shape
RUNTIME_RHS = re.compile(r'\$\(|`|\$RANDOM|\$\$|\bdate\b|\bmktemp\b|\bprintf\b|\$\{?[A-Za-z_]')
unparsed = []


def cut_at_pipe(frag):
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


def tokens_of(frag, where):
    try:
        return shlex.split(cut_at_pipe(frag), posix=True)
    except ValueError:
        unparsed.append(where)
        return None


def pattern_operands(toks):
    """the PATTERN operand(s): not options, not pathspecs, not messages."""
    pats, i = [], 0
    while i < len(toks) and (toks[i] in CMD_WORDS or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', toks[i])):
        if toks[i] == 'ls-files':
            return []
        i += 1
    while i < len(toks):
        t = toks[i]
        if t == '--':
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
        pats.append(t)
        break
    return pats


def flags_of(frag):
    """F-T447-5: the row's OWN matcher flags, replayed instead of a blanket -F."""
    out = []
    for m in re.finditer(r'(?:^|\s)-([A-Za-z]+)(?=\s|$)', cut_at_pipe(frag)):
        for ch in m.group(1):
            if ch in 'iEFwPGx':
                out.append('-' + ch)
    seen, ordered = set(), []
    for f in out:
        if f not in seen:
            seen.add(f)
            ordered.append(f)
    if '-F' not in ordered and '-E' not in ordered and '-G' not in ordered and '-P' not in ordered:
        ordered.append('-F')        # git grep's own default is basic regex; -F is the safe read
    return ordered


def pathspec_of(frag, lines=None, upto=0):
    """operands after a bare `--`.

    F-T447-1, SECOND HALF. T442 (and this file's own first draft) marked any pathspec
    containing a `$` as built-at-run-time and dropped the row. That is the SAME blind spot as
    the pattern-position one, one operand to the right -- and T452's own repair to
    `a2-33-dec2-rev5/sweep.sh` walked straight into it: hoisting the literal task directory into
    `SELF_DIR=` would have made the row INVISIBLE to the census that found it. A repair that
    hides the repaired row from the instrument that found it is not a repair. So one level of
    same-file dataflow is resolved here too."""
    m = re.search(r'\s--\s+(.*)$', cut_at_pipe(frag))
    if not m:
        m = re.search(r"['\"]--['\"]\s*,\s*(.*)$", frag)
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
        if '$' in t:
            sub, ok = t, True
            for vm in re.finditer(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', t):
                kind, val = (resolve_var(vm.group(1), lines, upto)
                             if lines is not None else ('unresolved', None))
                if kind == 'literal':
                    sub = sub.replace(vm.group(0), val)
                else:
                    ok = False
            if ok and '$' not in sub:
                out.append(sub)
            else:
                runtime_spec = True
            continue
        out.append(t)
    if runtime_spec and not out:
        return ['<runtime>']
    return out


def family(path):
    parts = path.split('/')
    return '/'.join(parts[:3]) if len(parts) >= 3 else '/'.join(parts[:2])


def resolve_var(name, body_lines, upto):
    """F-T447-1: one level of same-file dataflow.
    -> ('literal', s) | ('runtime', rhs) | ('unresolved', None)"""
    lit = None
    for ln in body_lines[:upto]:
        m = ASSIGN.match(ln)
        if m and m.group(1) == name:
            lit = m.group(2) if m.group(2) is not None else m.group(3)
    if lit is not None:
        return ('literal', lit)
    for ln in body_lines[:upto]:
        m = re.match(r'^\s*(?:local\s+|export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$', ln)
        if m and m.group(1) == name and RUNTIME_RHS.search(m.group(2)):
            return ('runtime', m.group(2).strip()[:90])
    return ('unresolved', None)


def matching_files(lit, specs, flags):
    cmd = ['git', 'grep', '-l', '-I'] + flags + ['-e', lit]
    real = [s for s in specs if s != '<runtime>']
    if real and all(x.startswith(':') for x in real):
        real = ['.'] + real
    if real:
        cmd += ['--'] + real
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if p.returncode >= 2:
        return None
    return [f for f in p.stdout.split('\n') if f]


ENFORCE = re.compile(r'\bexit\b|\b_sw_die\b|\bdie\b|REFUS|ABORT|\bfail\b|FAILED=|\breturn 1\b|'
                     r'sys\.exit|\braise\b')
# the branch fires when the count is ZERO / the search FAILED  -> a PRESENT-assertion
PRESENT_TEST = re.compile(r'-lt\s+1\b|-eq\s+0\b|-le\s+0\b|!=\s*0\s*\]|\brc\b[^\n]*-ne\s+0|'
                          r'\[\s*-z\s|==\s*0\b|<\s*1\b|not\s+\w+\b')
# the branch fires when the count is NON-ZERO / the search SUCCEEDED -> an ABSENT-assertion
ABSENT_TEST = re.compile(r'-gt\s+0\b|-ge\s+1\b|-ne\s+0\b|-eq\s+0\s*\]\s*(&&|;\s*then\s*$)|'
                         r'\[\s*-n\s|>\s*0\b|>=\s*1\b')


def direction_of(lines, i):
    """PRESENT / ABSENT / UNDECIDED, read from the 8 lines after the search, plus enforcement."""
    window = lines[i:i + 8]
    txt = '\n'.join(window)
    enforced = bool(ENFORCE.search(txt))
    p = bool(PRESENT_TEST.search(txt))
    a = bool(ABSENT_TEST.search(txt))
    if p and not a:
        return 'PRESENT', enforced, txt
    if a and not p:
        return 'ABSENT', enforced, txt
    return 'UNDECIDED', enforced, txt


# ---- sweep ----------------------------------------------------------------------------------
A1, A2 = [], []
runtime_assembled, unresolved_var, immun_pathspec, immun_postpipe, elsewhere, nolit = \
    [], [], [], [], [], []
searched_files, search_calls, resolved_var_rows = 0, 0, 0

for path in scripts:
    full = os.path.join(REPO, path)
    try:
        body = open(full, encoding='utf-8', errors='replace').read()
    except OSError:
        continue
    lines = body.split('\n')
    fam = family(path)
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
        where = '%s:%d' % (path, i)

        # ---- F-T447-4: immunisation, looked for on the WHOLE line, both spellings
        specs = pathspec_of(frag, lines, i - 1)
        excl = [s for s in specs if s.startswith(':!') or s.startswith(':(exclude)')]
        if excl and any(path.startswith(s.replace(':(exclude)', '').lstrip(':!').rstrip('/'))
                        for s in excl):
            immun_pathspec.append((path, i, line.strip(), 'pathspec %s' % excl))
            continue
        postpipe = line[at:]
        after = postpipe.split('|', 1)[1] if '|' in postpipe else ''
        pp = None
        for mm in re.finditer(r"grep\s+(?:-[A-Za-z]+\s+)*-[A-Za-z]*v[A-Za-z]*\s+"
                              r"""(?:-[A-Za-z]+\s+)*(?:-e\s+)?['"]?([^'"\s|]+)""", after):
            t = mm.group(1)
            if t and (path.startswith(t) or fam.endswith(t) or t in path):
                pp = t
        if pp:
            immun_postpipe.append((path, i, line.strip(), "post-pipe grep -v %r" % pp))
            continue

        # ---- corpus membership
        inc = False
        why = ''
        if 'git grep' in frag or 'git ls-files' in frag:
            if not specs:
                inc, why = True, 'whole tracked tree (no pathspec)'
            elif specs == ['<runtime>']:
                inc, why = False, 'pathspec built at RUN TIME (named blind spot)'
            else:
                for s in specs:
                    if s in ('.', './'):
                        inc, why = True, 'pathspec . covers it'
                        break
                    if s and not s.startswith(':') and path.startswith(s.rstrip('/')):
                        inc, why = True, 'pathspec %r covers it' % s
                        break
                else:
                    why = 'pathspec %s does not cover it' % specs
        else:
            for tok in re.split(r'\s+', frag):
                t = tok.strip('\'"')
                if t in ('.', './'):
                    inc, why = True, 'recursive grep over .'
                    break
                if t.startswith('.softhouse') and path.startswith(t.rstrip('/')):
                    inc, why = True, 'recursive grep over %r' % t
                    break
            else:
                why = 'no directory operand covering it'
        if not inc:
            elsewhere.append((path, i, line.strip(), why))
            continue

        # ---- pattern operands, WITH one level of variable resolution
        if is_py:
            head = re.split(r"['\"]--['\"]", frag)[0]
            head = re.sub(r"^.*?['\"]grep['\"]\s*,?", '', head, count=1) or head
            lits = []
            for mm in QUOTED.finditer(head):
                t = mm.group(1) if mm.group(1) is not None else mm.group(2)
                if t is None or t.startswith('-') or VAR.search(t):
                    continue
                lits.append(t)
            lits = lits[:2]
            flags = ['-F']
            origin = {}
        else:
            toks = tokens_of(frag, where)
            if toks is None:
                unresolved_var.append((path, i, line.strip(), 'UNPARSED by shlex'))
                continue
            raw = pattern_operands(toks)
            flags = flags_of(frag)
            lits, origin = [], {}
            for t in raw:
                bv = BARE_VAR.match(t)
                if bv:
                    kind, val = resolve_var(bv.group(1), lines, i - 1)
                    if kind == 'literal' and len(val) >= 2 and not VAR.search(val):
                        lits.append(val)
                        origin[val] = '$%s resolved to %r (same-file literal)' % (bv.group(1), val)
                        resolved_var_rows += 1
                    elif kind == 'runtime':
                        runtime_assembled.append(
                            (path, i, line.strip(), '$%s := %s' % (bv.group(1), val)))
                    else:
                        unresolved_var.append(
                            (path, i, line.strip(), '$%s not resolvable in this file' % bv.group(1)))
                elif len(t) >= 2 and not VAR.search(t):
                    lits.append(t)
                    origin[t] = 'literal in source'
        if not lits:
            nolit.append((path, i, line.strip(), why))
            continue

        placed = False
        for lit in lits:
            if lit not in body:
                continue
            hits = matching_files(lit, specs, flags)
            if hits is None:
                continue
            direction, enforced, ctx = direction_of(lines, i)
            fam_only = bool(hits) and all(family(h) == fam for h in hits)
            row = dict(path=path, line=i, lit=lit, why=why, flags=flags,
                       origin=origin.get(lit, ''), hits=hits, fam_only=fam_only,
                       direction=direction, enforced=enforced,
                       src='\n'.join('      %5d| %s' % (n, lines[n - 1])
                                     for n in range(max(1, i - 2), min(len(lines), i + 6) + 1)))
            if hits == [path]:
                A1.append(row)
                placed = True
            elif path in hits:
                A2.append(row)
                placed = True
        if not placed:
            nolit.append((path, i, line.strip(), why + ' / no self-matching literal'))
    if hit_here:
        searched_files += 1

# ---- report ---------------------------------------------------------------------------------
HEAD = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
DIRTY = len([l for l in subprocess.run(['git', 'status', '--porcelain'], cwd=REPO,
                                       capture_output=True, text=True).stdout.split('\n') if l])
TREE = '%s%s' % (HEAD[:8], ('+%d dirty' % DIRTY) if DIRTY else ' clean')

print('=' * 96)
print('T452 SELF-MATCHING PROBE CLASSIFICATION v2  --  T442\'s class, three holes closed')
print('=' * 96)
print('repo                      : %s' % REPO)
print('TREE THIS WAS TAKEN ON    : %s' % TREE)
print('                            (F-T447-3: every count below is a fact about THIS tree. A')
print('                            self-referential census changes what it measures the moment')
print('                            it is committed, so no count from it may be quoted bare.)')
print('tracked files .softhouse/ : %d' % len(files))
print('of them, scripts          : %d' % len(scripts))
print('scripts with >=1 search   : %d' % searched_files)
print('search invocations found  : %d' % search_calls)
print('  of those, rows whose pattern was VARIABLE-INDIRECT and RESOLVED to a same-file')
print('  literal (T442 counted these safe on syntax alone)            : %d' % resolved_var_rows)
print()
print('WHERE I LOOKED, AND WHERE I DID NOT. Corpus: TRACKED files under `.softhouse/` only --')
print('T447 measured 0 candidate searchers outside it, so the restriction costs nothing. A')
print('search counts only in COMMAND POSITION (shell) or on a line that also executes a')
print('subprocess (python). BLIND SPOTS STILL OPEN, named: a search continued onto the next')
print('line; TWO levels of dataflow (one is resolved here, two is not); a pathspec built at run')
print('time; `find -exec grep`; a search performed by a non-script; `git grep` reached through a')
print('shell helper whose name I do not know.')
print()


def dump(title, rows, note):
    print('-' * 96)
    print('%s  (%d rows, %d files)' % (title, len(rows), len({r['path'] for r in rows})))
    print('   %s' % note)
    print('-' * 96)
    for r in sorted(rows, key=lambda r: (r['path'], r['line'])):
        print('\n%s:%d   [%s]' % (r['path'], r['line'], r['why']))
        print('  probe    : %r   (%s)' % (r['lit'], r['origin']))
        print('  matcher  : git grep -l -I %s   <- THE ROW\'S OWN FLAGS' % ' '.join(r['flags']))
        print('  matches  : %d file(s)  %s' % (len(r['hits']),
              r['hits'] if len(r['hits']) <= 4 else r['hits'][:4] + ['...']))
        print('  direction: %-9s enforced: %s' % (r['direction'], 'YES' if r['enforced'] else 'no'))
        if r['fam_only']:
            print('  *** FAMILY-ONLY: every match lies inside %s.' % family(r['path']))
            print('      A PRESENT-assertion here is satisfied by the author\'s own artefacts.')
        print(r['src'])
    print()


dump('A1. SELF-ONLY -- the searching file is the ONLY corpus file containing the probe', A1,
     'Every row here is in the class, in one direction or the other.')
dump('A2. SELF + OTHERS -- the searcher matches, and so do other files', A2,
     'Inverts an ABSENT-assertion; a PRESENT-assertion is safe ONLY if a non-family file carries it.')

fam_only_rows = [r for r in (A1 + A2) if r['fam_only']]
print('-' * 96)
print('FAMILY-ONLY rows (every match inside the searcher\'s own task directory) : %d'
      % len(fam_only_rows))
print('-' * 96)
for r in fam_only_rows:
    print('  %s:%d  probe %r  %d file(s)  direction=%s enforced=%s'
          % (r['path'], r['line'], r['lit'], len(r['hits']), r['direction'],
             'YES' if r['enforced'] else 'no'))
print()

fail_open = [r for r in fam_only_rows if r['direction'] == 'PRESENT' and r['enforced']]
undecided = [r for r in fam_only_rows if r['direction'] == 'UNDECIDED']
print('-' * 96)
print('FAIL-OPEN by the definition stated at the head of this file : %d' % len(fail_open))
print('-' * 96)
for r in fail_open:
    print('  %s:%d  probe %r' % (r['path'], r['line'], r['lit']))
print('UNDECIDED direction, requiring HAND adjudication (NOT counted safe) : %d' % len(undecided))
for r in undecided:
    print('  %s:%d  probe %r' % (r['path'], r['line'], r['lit']))
print()


def listing(title, rows, note):
    print('-' * 96)
    print('%s  (%d rows)' % (title, len(rows)))
    print('   %s' % note)
    print('-' * 96)
    for (p, ln, line, why) in rows:
        print('  %s:%d  [%s]\n      %s' % (p, ln, why, line))
    print()


listing('B1. RUN-TIME ASSEMBLED PATTERN -- the CORRECT shape', runtime_assembled,
        'No tracked byte sequence can equal the probe. Not in the class.')
listing('B2. VARIABLE NOT RESOLVABLE IN THIS FILE -- the residual blind spot', unresolved_var,
        'Two levels of dataflow, or a value from the environment. Read these by hand.')
listing('B3. NO SELF-MATCHING LITERAL in pattern position', nolit,
        'Pathspec-only calls, short literals, and rows whose literal is not in their own body.')
listing('C1. IMMUNISED BY `:!` / `:(exclude)` PATHSPEC', immun_pathspec,
        'Repairs the row, opens a hole: everything else under the excluded path is unscanned.')
listing('C2. IMMUNISED BY POST-PIPE `grep -v` -- INVISIBLE TO T442 BY CONSTRUCTION [F-T447-4]',
        immun_postpipe,
        'cut_at_pipe() truncates before this is ever looked at. Same dodge, same hole.')
print('D. searching a corpus that does not contain the searcher : %d rows (not in the class)'
      % len(elsewhere))
print()

print('=' * 96)
print('MEMBER SET -- the drift-stable figure. Paths and lines do not change when a transcript is')
print('published; bucket LABELS do. Quote this, and tree-qualify the counts.')
print('=' * 96)
for r in sorted(A1 + A2, key=lambda r: (r['path'], r['line'])):
    if r['fam_only'] or r['hits'] == [r['path']]:
        print('  MEMBER %s:%d  %r  direction=%s enforced=%s'
              % (r['path'], r['line'], r['lit'], r['direction'],
                 'YES' if r['enforced'] else 'no'))
print()
print('=' * 96)
print('T452-CLASSIFY-V2-RESULT: tree=%s scripts=%d searches=%d var_resolved=%d self_only=%d '
      'self_plus_others=%d family_only=%d fail_open=%d undecided=%d runtime_assembled=%d '
      'unresolved_var=%d nolit=%d immunised_pathspec=%d immunised_postpipe=%d elsewhere=%d '
      'unparsed=%d'
      % (TREE.replace(' ', '_'), len(scripts), search_calls, resolved_var_rows, len(A1),
         len(A2), len(fam_only_rows), len(fail_open), len(undecided), len(runtime_assembled),
         len(unresolved_var), len(nolit), len(immun_pathspec), len(immun_postpipe),
         len(elsewhere), len(unparsed)))
print('=' * 96)
sys.exit(0)
