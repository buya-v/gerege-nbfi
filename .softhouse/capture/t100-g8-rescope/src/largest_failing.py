#!/usr/bin/env python3
"""T100 — how large does a FAILING principal get, over the cells actually swept?

Re-derives, per (annual rate, n) shape, the largest failing principal and the smallest
clean principal from the raw captures, and reports whether the shape is BRACKETED
(i.e. some clean cell was measured above the largest failing one at the same shape).
Integer minor units only.
"""
import json, gzip, sys, collections

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from classify_two_families import minor, load, classify   # noqa: E402

shapes = collections.defaultdict(lambda: {'fail': [], 'clean': [], 'famB': []})
for path in sys.argv[1:]:
    for cap in load(path)['captures']:
        if cap['id'].startswith('P-CAL'):
            continue
        r = classify(cap)
        key = (r['rate'], r['n'])
        if r['family'] == 'clean':
            shapes[key]['clean'].append(r['disbursed_minor'])
        else:
            shapes[key]['fail'].append(r['disbursed_minor'])
            if r['family'] == 'B':
                shapes[key]['famB'].append(r['disbursed_minor'])

out = []
for (rate, n), v in sorted(shapes.items(), key=lambda kv: (-max(kv[1]['fail'] or [0]),)):
    if not v['fail']:
        continue
    lf = max(v['fail'])
    above = [c for c in v['clean'] if c > lf]
    out.append({'rate': rate, 'n': n,
                'largest_failing_minor': lf,
                'smallest_clean_above_minor': min(above) if above else None,
                'bracketed': bool(above),
                'family': 'B' if v['famB'] else 'A',
                'cells_swept': len(v['fail']) + len(v['clean'])})

print('%-8s %-6s %-18s %-22s %-10s %s' % ('rate%', 'n', 'largest failing', 'smallest clean above',
                                          'bracketed', 'family'))
for r in out:
    print('%-8s %-6d %-18s %-22s %-10s %s'
          % (r['rate'], r['n'],
             '%d minor (MNT %s)' % (r['largest_failing_minor'],
                                    '%d.%02d' % divmod(r['largest_failing_minor'], 100)),
             ('%d minor' % r['smallest_clean_above_minor']) if r['bracketed'] else 'NONE MEASURED',
             r['bracketed'], r['family']))
json.dump(out, open(__file__.replace('/src/', '/out/').replace('largest_failing.py',
          'largest-failing.json'), 'w'), indent=1)
