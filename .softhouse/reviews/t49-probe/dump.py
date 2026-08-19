#!/usr/bin/env python3
"""T49 probe: dump cited line ranges from the pinned Fineract checkout (read-only)."""
import os, sys, collections

ROOT = '/Users/buv/fineract'
_idx = None

def index():
    global _idx
    if _idx is None:
        _idx = collections.defaultdict(list)
        for dp, dn, fn in os.walk(ROOT):
            if '/.git/' in dp:
                continue
            for f in fn:
                if f.endswith('.java'):
                    _idx[f].append(os.path.join(dp, f))
    return _idx

def resolve(name):
    cands = index().get(name, [])
    mains = [c for c in cands if '/src/main/' in c]
    use = mains if mains else cands
    if not use:
        raise SystemExit('no such file: ' + name)
    return sorted(use)[0]

def dump(name, a, b):
    p = resolve(name)
    lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
    print('### %s:%d-%d   (%s)' % (name, a, b, p.replace(ROOT, '<fineract>')))
    for i in range(a, min(b, len(lines)) + 1):
        print('%5d\t%s' % (i, lines[i - 1]))
    print()

if __name__ == '__main__':
    args = sys.argv[1:]
    for spec in args:
        name, rng = spec.split(':')
        if '-' in rng:
            a, b = rng.split('-')
        else:
            a = b = rng
        dump(name, int(a), int(b))
