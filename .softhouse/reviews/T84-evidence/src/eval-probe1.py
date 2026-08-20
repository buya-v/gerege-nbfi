import json
from decimal import Decimal

doc = json.load(open('/tmp/t84probe/out/capture-t84-raw.json'))
pred = json.load(open('/tmp/t84-prediction.json'))
t83 = {c['id']: c for c in json.load(open(
    '.softhouse/capture/t83-nonamortizing/out/capture-t83-raw.json'))['captures']}

def minor(s):
    d = Decimal(s) * 100
    assert d == d.to_integral_value(), s
    return int(d)

rows = []
for c in doc['captures']:
    if not c['id'].startswith('T84-'):
        continue
    i, o = c['inputs'], c['observed']
    B = minor(i['disbursementAmount']); n = i['numberOfRepayments']; rate = str(i['annualNominalInterestRate'])
    reps = [p for p in o['periods'] if p['type'] == 'REPAYMENT']
    assert len(reps) == n, (c['id'], len(reps))
    last = minor(reps[-1]['balance'])
    fails = last != 0
    rows.append(dict(id=c['id'], tag=c['id'].split('-')[1], rate=rate, n=n, B=B, fails=fails,
                     psum=sum(minor(p['principal']) for p in reps),
                     bals=[minor(p['balance']) for p in reps],
                     isum=sum(minor(p['interest']) for p in reps),
                     toa=o['totalOutstandingAmount'],
                     tob_last=minor(reps[-1]['totalOutstandingBalance']),
                     total_int=o['totalInterestAmount']))

print("cells:", len(rows), " FAIL:", sum(r['fails'] for r in rows))

# --- 1. closed form, outside the sampled grid ---
print("\n=== CLOSED FORM vs OBSERVATION, by attack family ===")
fam = {}
for r in rows:
    p = pred[r['id']]
    ok = (p['predictedFails'] == r['fails'])
    d = fam.setdefault(r['tag'], [0, 0, []])
    d[0] += 1
    if ok:
        d[1] += 1
    else:
        d[2].append((r['id'], p['BtimesA'], "predFail=%s obsFail=%s" % (p['predictedFails'], r['fails'])))
for k in sorted(fam):
    n, ok, miss = fam[k]
    print("  %-5s %3d cells, %3d held, %2d REFUTED" % (k, n, ok, len(miss)))
    for m in miss[:12]:
        print("        REFUTED", m)
tot_miss = sum(len(v[2]) for v in fam.values())
print("TOTAL closed-form refutations:", tot_miss, "/", len(rows))

# --- 2. RP: does T83's answer move under a different tenant id / ordering? ---
print("\n=== RP: tenant-id and ordering independence vs T83's own cells ===")
for r in [x for x in rows if x['tag'] == 'RP']:
    tid = "T83-SW-R%s-N%d-B%d" % (r['rate'].replace('.', 'p'), r['n'], r['B'])
    ref = t83.get(tid)
    if ref is None:
        print("  %-28s no T83 counterpart" % r['id']); continue
    same_obs = ref['observed'] == [c for c in doc['captures'] if c['id'] == r['id']][0]['observed']
    rreps = [p for p in ref['observed']['periods'] if p['type'] == 'REPAYMENT']
    reffail = minor(rreps[-1]['balance']) != 0
    print("  %-28s obs-identical-to-T83=%-5s  fails: T84=%-5s T83=%-5s  %s"
          % (r['id'], same_obs, r['fails'], reffail,
             "OK" if (same_obs and r['fails'] == reffail) else "*** DIVERGENCE ***"))

# --- 3. the reframing, on MY failing cells ---
f = [r for r in rows if r['fails']]
print("\n=== REFRAMING counterexample hunt on %d NEW failing cells ===" % len(f))
print("  principal column != disbursement :", [r['id'] for r in f if r['psum'] != r['B']][:6],
      len([r for r in f if r['psum'] != r['B']]))
print("  totalOutstandingAmount != 0      :", [r['id'] for r in f if Decimal(r['toa']) != 0][:6],
      len([r for r in f if Decimal(r['toa']) != 0]))
print("  balance column not constant = B  :", [r['id'] for r in f if set(r['bals']) != {r['B']}][:6],
      len([r for r in f if set(r['bals']) != {r['B']}]))
print("  interest column sums != 0        :", [r['id'] for r in f if r['isum'] != 0][:6],
      len([r for r in f if r['isum'] != 0]))
print("  last-row totalOutstandingBalance != 0:", [r['id'] for r in f if r['tob_last'] != 0][:6],
      len([r for r in f if r['tob_last'] != 0]))

# --- 4. boundedness: how large does a failing principal actually get? ---
print("\n=== BOUNDEDNESS: largest failing principal per shape (MY cells) ===")
sh = {}
for r in rows:
    sh.setdefault((r['rate'], r['n']), []).append(r)
big = []
for k in sorted(sh, key=lambda k: (float(k[0]), k[1])):
    ff = [r['B'] for r in sh[k] if r['fails']]
    cc = [r['B'] for r in sh[k] if not r['fails']]
    if ff:
        big.append((max(ff), k, min(cc) if cc else None))
big.sort(reverse=True)
for b, k, sc in big[:14]:
    print("  rate %-7s n=%-4d largest failing B = %-4d (MNT %s)   smallest clean = %s"
          % (k[0], k[1], b, Decimal(b).scaleb(-2), sc))
print("\n  MAX failing principal anywhere in T84's probe: %d minor = MNT %s"
      % (big[0][0], Decimal(big[0][0]).scaleb(-2)))

# --- 5. FAR family ---
print("\n=== FAR: does the region reappear above the swept top? ===")
far = [r for r in rows if r['tag'] == 'FAR']
print("  %d far cells, %d fail" % (len(far), sum(r['fails'] for r in far)))
json.dump(rows, open('/tmp/t84-eval-rows.json', 'w'))
