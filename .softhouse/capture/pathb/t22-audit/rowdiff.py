import json
import sys

rows = [json.loads(l) for l in open(sys.argv[1])]
d = {r['id']: r for r in rows}
for a, b in ((1, 2), (3, 4)):
    print('--- DB row diff product %d vs %d' % (a, b))
    ks = sorted(set(d[a]) | set(d[b]))
    n = 0
    for k in ks:
        if d[a].get(k) != d[b].get(k):
            print('  %s: %r -> %r' % (k, d[a].get(k), d[b].get(k)))
            n += 1
    print('  total differing columns:', n)
