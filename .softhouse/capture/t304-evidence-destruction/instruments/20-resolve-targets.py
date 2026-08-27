#!/usr/bin/env python3
"""T304 instrument 20 — narrow the raw destructive-site hits to sites whose TARGET is TRACKED.

Input : the TSV emitted by `10-population-census.py` on stdin.
Output: TSV of sites whose resolved target is a tracked file or a tracked directory prefix.

RESOLUTION METHOD, stated because a resolver's blind spots are the finding's blind spots:
  1. Collect `VAR=value` / `VAR="value"` / `VAR=$(...)` assignments in the same file, plus
     python `VAR = "value"` assignments.  Substitute `$VAR` / `${VAR}` iteratively (5 passes).
  2. Any operand still containing an unresolved `$`, or resolving under a temp root
     (`/tmp`, `$TMPDIR`, `mktemp`, `/var/folders`), is classed UNRESOLVED / TEMP and reported
     separately -- NOT silently dropped.  A dropped unknown is a P-70 waiting to happen.
  3. A resolved operand is TRACKED if it is in `git ls-files`, or is a directory prefix of
     at least one tracked path.  Relative operands are tried against the repo root AND against
     the instrument's own directory (instruments commonly `cd` to their dir).
"""
import os
import re
import subprocess
import sys

TEMP_MARKERS = ('/tmp/', '/tmp"', '$TMPDIR', 'mktemp', '/var/folders', '/dev/null',
                '/dev/stderr', '/dev/stdout', '$TMP', 'tempfile', 'TemporaryDirectory')

tracked = set(subprocess.run(['git', 'ls-files'], capture_output=True, text=True,
                             check=True).stdout.splitlines())
tracked_dirs = set()
for p in tracked:
    parts = p.split('/')
    for i in range(1, len(parts)):
        tracked_dirs.add('/'.join(parts[:i]))

ASSIGN_SH = re.compile(r'^\s*(?:export\s+|readonly\s+|local\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.+?)\s*$')
ASSIGN_PY = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*["\'](.+?)["\']\s*$')


def file_vars(path):
    v = {}
    try:
        lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    except OSError:
        return v
    for line in lines:
        if line.lstrip().startswith('#'):
            continue
        m = ASSIGN_SH.match(line)
        if m and not line.lstrip().startswith(('if', 'for', 'while')):
            val = m.group(2).strip()
            if val.startswith('"') and val.endswith('"') and len(val) > 1:
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'") and len(val) > 1:
                val = val[1:-1]
            v.setdefault(m.group(1), val)
            continue
        m = ASSIGN_PY.match(line)
        if m:
            v.setdefault(m.group(1), m.group(2))
    return v


SUBSHELL_CD = re.compile(r'\$\(\s*cd\s+"?([^"&|)]+?)"?\s*&&\s*pwd\s*\)')


def desubshell(tok, script_dir):
    """Resolve the two idioms every instrument in this repo uses to find itself:
         HERE=$(cd "$(dirname "$0")" && pwd)      -> the script's own directory
         TASK=$(cd "$HERE/.." && pwd)             -> normalised relative to it
    Without this, every self-locating instrument classes UNRESOLVED and the sweep
    misses exactly the population it was written to find."""
    for _ in range(8):
        before = tok
        tok = tok.replace('$(dirname "$0")', script_dir or '.')
        tok = tok.replace('$(dirname $0)', script_dir or '.')
        tok = tok.replace('${BASH_SOURCE[0]%/*}', script_dir or '.')

        def _cd(m):
            inner = m.group(1).strip()
            if '$' in inner:
                return m.group(0)
            return os.path.normpath(inner)
        tok = SUBSHELL_CD.sub(_cd, tok)
        if tok == before:
            break
    return tok


def expand(tok, v):
    for _ in range(6):
        before = tok
        tok = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-[^}]*)?\}',
                     lambda m: v.get(m.group(1), m.group(0)), tok)
        tok = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)',
                     lambda m: v.get(m.group(1), m.group(0)), tok)
        if tok == before:
            break
    return tok


OPERAND = re.compile(r'[A-Za-z0-9_$@{}./~*?\[\]-]+')


def operands(text):
    """Path-shaped operands: contain a '/' or a known repo top-level name."""
    out = []
    for t in OPERAND.findall(text):
        t = t.strip('"\'`,);')
        if not t or t.startswith('-'):
            continue
        if '/' in t or t.startswith('.softhouse') or t.startswith('$'):
            out.append(t)
    return out


def classify(tok, script_dir):
    """-> (verdict, normalised)"""
    if any(m in tok for m in TEMP_MARKERS):
        return 'TEMP', tok
    tok = desubshell(tok, script_dir)
    if '$' not in tok:
        tok = os.path.normpath(tok)
    if '$' in tok:
        # PREFIX RULE: a target like <tracked-dir>/$arm/P0 still destroys inside a
        # tracked subtree.  Class it by the literal prefix before the first '$'.
        pre = os.path.normpath(tok.split('$', 1)[0].rstrip('/'))
        if pre.startswith('./'):
            pre = pre[2:]
        for c in ([pre] + ([os.path.normpath(os.path.join(script_dir, pre))] if script_dir and not pre.startswith('/') else [])):
            if c in tracked_dirs:
                return 'TRACKED-DIR', tok
            if c in tracked:
                return 'TRACKED-FILE', tok
        return 'UNRESOLVED', tok
    cand = []
    t = tok.rstrip('/')
    if t.startswith('./'):
        t = t[2:]
    if t.startswith('/'):
        # absolute: only interesting if inside the repo
        root = os.path.realpath('.')
        rt = os.path.realpath(t) if os.path.exists(t) else t
        if rt.startswith(root + '/'):
            cand.append(rt[len(root) + 1:])
        else:
            return 'OUTSIDE', tok
    else:
        cand.append(t)
        if script_dir:
            cand.append(os.path.normpath(os.path.join(script_dir, t)))
    for c in cand:
        if c in tracked:
            return 'TRACKED-FILE', c
        if c in tracked_dirs:
            return 'TRACKED-DIR', c
    return 'UNTRACKED', tok


def main():
    hdr = sys.stdin.readline()
    varcache = {}
    counts = {}
    print('\t'.join(['verdict', 'file', 'lineno', 'op', 'target', 'text']))
    for line in sys.stdin:
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 5:
            continue
        path, why, lineno, op, text = parts[0], parts[1], parts[2], parts[3], parts[4]
        if path not in varcache:
            varcache[path] = file_vars(path)
        v = varcache[path]
        sd = os.path.dirname(path)
        best = None
        for tok in operands(text):
            ex = desubshell(expand(desubshell(tok, sd), v), sd)
            verdict, norm = classify(ex, sd)
            rank = {'TRACKED-FILE': 0, 'TRACKED-DIR': 1, 'UNRESOLVED': 2, 'TEMP': 3,
                    'UNTRACKED': 4, 'OUTSIDE': 5}[verdict]
            if best is None or rank < best[0]:
                best = (rank, verdict, norm)
        if best is None:
            continue
        _, verdict, norm = best
        counts[verdict] = counts.get(verdict, 0) + 1
        if verdict in ('TRACKED-FILE', 'TRACKED-DIR', 'UNRESOLVED'):
            print('\t'.join([verdict, path, lineno, op, norm, text]))
    for k in sorted(counts):
        sys.stderr.write('%-14s %d\n' % (k, counts[k]))


if __name__ == '__main__':
    main()
