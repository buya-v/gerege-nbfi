import gzip, json, sys
p = sys.argv[1]
d = json.loads(gzip.open(p, 'rt').read())
caps = d['captures']
print('captures keys type', type(caps).__name__)
if isinstance(caps, dict):
    print('capture groups:', list(caps.keys()))
    cases = []
    for k, v in caps.items():
        for c in v:
            c = dict(c)
            c['_group'] = k
            cases.append(c)
else:
    cases = caps
print('n cases', len(cases))
err = [c for c in cases if c.get('error')]
print('errored', len(err), [c.get('id') for c in err])
for c in err:
    print('   ', c.get('id'), '->', c.get('error'), '| has errorStackDepthTotal?', 'errorStackDepthTotal' in c, '| keys', sorted(c.keys()))
for cid in ('T159-R600p0-N3000-B1001', 'T159-R600p0-N3000-B10001', 'T159-R600p0-N2000-B10001'):
    hit = [c for c in cases if c.get('id') == cid]
    for c in hit:
        o = c.get('observed') or {}
        print(cid, 'error=', c.get('error'),
              {k: o.get(k) for k in ('totalDisbursedAmount', 'totalPrincipalAmount', 'totalInterestAmount')})
    if not hit:
        print(cid, 'NOT PRESENT')
ids = [c.get('id') for c in cases]
print('order, first 10:', ids[:10])
print('index of disputed:', ids.index('T159-R600p0-N3000-B10001') if 'T159-R600p0-N3000-B10001' in ids else None)
print('index of red:', ids.index('T159-R600p0-N2000-B10001') if 'T159-R600p0-N2000-B10001' in ids else None)
