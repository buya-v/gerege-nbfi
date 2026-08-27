#!/usr/bin/env python3
"""T304 instrument 10 — derive the INSTRUMENT POPULATION and the DESTRUCTIVE-SITE population.

SELECTOR, printed beside every figure it produces (P-70: a count is a statement about a
search, never about the world):

  POPULATION = tracked file (`git ls-files`) AND
               ( extension in {.sh,.py,.zsh,.bash,.psql}
                 OR git index mode 100755 (exec bit)
                 OR first two bytes are '#!' )

  DESTRUCTIVE SITE = a line in a population member matching one of:
      rm -rf / rm -r / rm -f / rm          (removal)
      mv                                    (move-over / rename away)
      shutil.rmtree / os.remove / os.unlink / Path.unlink / pathlib .rmdir
      truncate / : >  / > FILE / >| FILE    (output redirection over a path)
      tee FILE (non-append)
      git clean
      git checkout -- / git restore / git reset --hard   (index/worktree overwrite)
      sed -i / perl -i                       (in-place edit)

Run from the repo root.  Writes TSV to stdout.
"""
import os
import re
import subprocess
import sys

EXT = {'.sh', '.py', '.zsh', '.bash', '.psql'}

PATTERNS = [
    ('rm',            re.compile(r'(?<![\w./-])rm\s+(-[a-zA-Z]+\s+)*')),
    ('mv',            re.compile(r'(?<![\w./-])mv\s+')),
    ('py-rmtree',     re.compile(r'shutil\.rmtree|os\.remove|os\.unlink|\.unlink\(|\.rmdir\(')),
    ('truncate',      re.compile(r'(?<![\w./-])truncate\s+|(?<![\w./-]):\s*>\s*\S')),
    ('redirect',      re.compile(r'(?<![0-9<>&|])>\s*(?!&|\s*>)[A-Za-z0-9_$"\'./{-]')),
    ('tee',           re.compile(r'(?<![\w./-])tee\s+(?!-a)')),
    ('git-clean',     re.compile(r'git\s+clean')),
    ('git-restore',   re.compile(r'git\s+(checkout\s+--|restore|reset\s+--hard)')),
    ('inplace-edit',  re.compile(r'(sed|perl)\s+(-[a-zA-Z]*\s+)*-i')),
]


def population():
    out = subprocess.run(['git', 'ls-files', '-s'], capture_output=True, text=True, check=True).stdout
    pop = []
    for line in out.splitlines():
        # <mode> <sha> <stage>\t<path>
        meta, _, path = line.partition('\t')
        mode = meta.split()[0]
        why = []
        if os.path.splitext(path)[1] in EXT:
            why.append('ext')
        if mode == '100755':
            why.append('execbit')
        if not why:
            try:
                with open(path, 'rb') as f:
                    if f.read(2) == b'#!':
                        why.append('shebang')
            except OSError:
                pass
        if why:
            pop.append((path, '+'.join(why)))
    return pop


def main():
    pop = population()
    sys.stderr.write('SELECTOR: tracked AND (ext in .sh/.py/.zsh/.bash/.psql OR mode 100755 OR shebang)\n')
    sys.stderr.write('POPULATION SIZE: %d instruments\n' % len(pop))
    hits = 0
    files = set()
    print('\t'.join(['file', 'why_in_pop', 'lineno', 'op', 'text']))
    for path, why in pop:
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        for i, raw in enumerate(lines, 1):
            s = raw.strip()
            if s.startswith('#') or s.startswith('//'):
                continue
            for op, rx in PATTERNS:
                if rx.search(raw):
                    print('\t'.join([path, why, str(i), op, s[:180]]))
                    hits += 1
                    files.add(path)
                    break
    sys.stderr.write('DESTRUCTIVE-SITE HITS: %d across %d files\n' % (hits, len(files)))


if __name__ == '__main__':
    main()
