#!/usr/bin/env python3
"""T304 instrument 80 — the REDIRECT class: which redirects land on a TRACKED file, and
does the instrument OWN that file?

WHY THIS IS A SEPARATE INSTRUMENT, AND WHY IT DOES NOT REUSE 20's OUTPUT.
Instrument 20 ranks every path-shaped operand on a line and reports the best-ranked one.
For `rm`/`mv` that is the target. For a REDIRECT it is not: in

    git show "$REV:docs/adr/DEC-2-gl-accounting-adapter.md" > "$T/rev4.md"

the tracked operand is the INPUT and `$T/rev4.md` is the target, so 20 reports a tracked
`docs/adr/...` for a line that writes only to a temp file. A first pass of this instrument
built on 20's output and reported 157 "FOREIGN writes"; inspection showed the leading
entries were all that artifact. THE 157 IS WITHDRAWN. This instrument therefore parses the
redirect operator itself and takes ONLY the token that follows it.

Operators taken   : `>` and `>|` (truncating).
Operators ignored : `>>` (append -- adds, never destroys), `2>` / `&>` / `>&` (fd dup and
                    stderr, handled as their own token), and any `>` inside quotes.

Classification of a redirect whose target is an exact tracked file:
  OWN     — target under the writer's own `.softhouse/<kind>/<task>/` directory.
            Class (b)/(c): re-running an instrument rewrites its own transcript, which is
            how it gets re-committed at all, and the change is VISIBLE in `git status`.
  FOREIGN — target under a different task's directory, or outside `.softhouse`.
            Candidate class (a).
"""
import os
import re
import subprocess
import sys

SOFT = re.compile(r'^\.softhouse/(capture|reviews|handoff|runs|vectors)/([^/]+)/')
EXT = {'.sh', '.py', '.zsh', '.bash', '.psql'}
TEMP = ('/tmp/', '$TMPDIR', 'mktemp', '/var/folders', '/dev/', '$TMP')

tracked = set(subprocess.run(['git', 'ls-files'], capture_output=True, text=True,
                             check=True).stdout.splitlines())

# `>` not preceded by a digit/&/> and not followed by > or &, then the next word.
REDIR = re.compile(r'(?<![0-9&>])>\|?\s*(["\']?)([^\s"\';|&)<>]+)\1')

ASSIGN = re.compile(r'^\s*(?:export\s+|readonly\s+|local\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.+?)\s*$')
SUBSHELL_CD = re.compile(r'\$\(\s*cd\s+"?([^"&|)]+?)"?\s*&&\s*pwd\s*\)')


def strip_quotes(v):
    if len(v) > 1 and v[0] == v[-1] and v[0] in '"\'':
        return v[1:-1]
    return v


def file_vars(path):
    v = {}
    try:
        lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    except OSError:
        return v
    for line in lines:
        if line.lstrip().startswith('#'):
            continue
        m = ASSIGN.match(line)
        if m and not line.lstrip().startswith(('if', 'for', 'while')):
            v.setdefault(m.group(1), strip_quotes(m.group(2).strip()))
    return v


def resolve(tok, v, sd):
    for _ in range(8):
        before = tok
        tok = tok.replace('$(dirname "$0")', sd or '.').replace('$(dirname $0)', sd or '.')
        tok = SUBSHELL_CD.sub(
            lambda m: m.group(0) if '$' in m.group(1) else os.path.normpath(m.group(1)), tok)
        tok = re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-[^}]*)?\}',
                     lambda m: v.get(m.group(1), m.group(0)), tok)
        tok = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)',
                     lambda m: v.get(m.group(1), m.group(0)), tok)
        if tok == before:
            break
    return tok


def owner(path):
    m = SOFT.match(path)
    if m:
        return m.group(1) + '/' + m.group(2)
    return path.split('/')[0] if '/' in path else '<root>'


def population():
    out = subprocess.run(['git', 'ls-files', '-s'], capture_output=True, text=True,
                         check=True).stdout
    pop = []
    for line in out.splitlines():
        meta, _, path = line.partition('\t')
        mode = meta.split()[0]
        if os.path.splitext(path)[1] in EXT or mode == '100755':
            pop.append(path)
    return pop


def main():
    own = []
    foreign = []
    unresolved = 0
    for path in population():
        v = file_vars(path)
        sd = os.path.dirname(path)
        try:
            lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
        except OSError:
            continue
        for i, raw in enumerate(lines, 1):
            s = raw.strip()
            if s.startswith('#'):
                continue
            for m in REDIR.finditer(raw):
                tok = m.group(2)
                if any(t in tok for t in TEMP):
                    continue
                r = resolve(tok, v, sd)
                if '$' in r or any(t in r for t in TEMP):
                    unresolved += 1
                    continue
                r = os.path.normpath(r)
                if r.startswith('./'):
                    r = r[2:]
                cand = [r, os.path.normpath(os.path.join(sd, r))] if not r.startswith('/') else [r]
                hit = next((c for c in cand if c in tracked), None)
                if hit is None:
                    continue
                rec = (path, i, hit, s[:130])
                (own if owner(hit) == owner(path) else foreign).append(rec)

    print('=== REDIRECT (`>` / `>|`) LANDING ON AN EXACT TRACKED FILE ===')
    print()
    print('--- FOREIGN: the writer does not own the target ---')
    if not foreign:
        print('(none)')
    for path, i, hit, s in sorted(foreign):
        print('%s:%d' % (path, i))
        print('    -> %s   [owner %s, writer %s]' % (hit, owner(hit), owner(path)))
        print('       %s' % s)
    print()
    print('--- OWN: the writer rewrites its own tracked transcript (%d sites) ---' % len(own))
    for path, i, hit, s in sorted(own)[:40]:
        print('%s:%d -> %s' % (path, i, hit))
    if len(own) > 40:
        print('... and %d more' % (len(own) - 40))
    sys.stderr.write('OWN %d   FOREIGN %d   (unresolved targets skipped: %d)\n'
                     % (len(own), len(foreign), unresolved))


if __name__ == '__main__':
    main()
