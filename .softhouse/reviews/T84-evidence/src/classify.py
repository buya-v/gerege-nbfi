import json, sys
from decimal import Decimal
from fractions import Fraction

RAW = sys.argv[1] if len(sys.argv) > 1 else '.softhouse/capture/t83-nonamortizing/out/capture-t83-raw.json'
doc = json.load(open(RAW))
caps = doc['captures']

def minor(s):
    d = Decimal(s) * 100
    assert d == d.to_integral_value(), ("non-integral minor", s)
    return int(d)

sweep = [c for c in caps if c['id'].startswith('T83-SW-')]
cal   = [c for c in caps if not c['id'].startswith('T83-SW-')]
print("sweep cells:", len(sweep), " calibration:", len(cal), [c['id'] for c in cal])

grid = {}
rows = []
for c in sweep:
    i = c['inputs']; o = c['observed']
    rate = i['annualNominalInterestRate']; n = i['numberOfRepayments']
    B = minor(i['disbursementAmount'])
    want = "T83-SW-R%s-N%d-B%d" % (str(rate).replace('.','p'), n, B)
    assert c['id'] == want, (c['id'], want, rate, n, B)
    reps = [p for p in o['periods'] if p['type']=='REPAYMENT']
    disb = [p for p in o['periods'] if p['type']=='DISBURSEMENT']
    assert len(reps)==n, (c['id'], len(reps), n)
    assert len(disb)==1
    last_bal = minor(reps[-1]['balance'])
    fails = last_bal != 0
    psum = sum(minor(p['principal']) for p in reps)
    bals = [minor(p['balance']) for p in reps]
    isum = sum(minor(p['interest']) for p in reps)
    toa = o['totalOutstandingAmount']
    rows.append(dict(id=c['id'], rate=str(rate), n=n, B=B, fails=fails, last_bal=last_bal,
                     psum=psum, bals=bals, isum=isum, toa=toa,
                     disb_principal=minor(disb[0]['principal']),
                     tob_last=minor(reps[-1]['totalOutstandingBalance'])))
    grid.setdefault((str(rate), n), {})[B] = fails

nfail = sum(1 for r in rows if r['fails'])
print("FAIL:", nfail, " CLEAN:", len(rows)-nfail)

print("\n--- grid completeness ---")
bad=[]
for k in sorted(grid, key=lambda k:(float(k[0]),k[1])):
    ks = sorted(grid[k])
    if ks != list(range(1, max(ks)+1)):
        bad.append(("HOLE IN SWEEP", k, ks))
print("shapes:", len(grid), " sweeps with a missing principal:", len(bad))
for b in bad: print(b)

print("\n--- prefix check ---")
tbl=[]; notprefix=[]
for k in sorted(grid, key=lambda k:(float(k[0]),k[1])):
    d=grid[k]; ks=sorted(d)
    failset=[b for b in ks if d[b]]
    largest = max(failset) if failset else None
    cleanset=[b for b in ks if not d[b]]
    smallest_clean = min(cleanset) if cleanset else None
    isprefix = failset == list(range(1, largest+1)) if failset else True
    allclean_above = all(not d[b] for b in ks if largest is None or b>largest)
    ok = isprefix and allclean_above
    if not ok: notprefix.append(k)
    tbl.append((k[0],k[1],min(ks),max(ks),len(ks),largest,smallest_clean,ok))
print("shapes where failing set is NOT a contiguous prefix:", notprefix)
print("%-6s %-4s %-8s %-6s %-9s %-9s %s" % ("rate","n","swept","cells","largestF","smallestC","prefix"))
for t in tbl:
    print("%-6s %-4d %-8s %-6d %-9s %-9s %s" % (t[0],t[1],"%d..%d"%(t[2],t[3]),t[4],str(t[5]),str(t[6]),t[7]))

print("\n--- reframing counterexample hunt (failing cases) ---")
ce_psum=[r['id'] for r in rows if r['fails'] and r['psum']!=r['B']]
ce_toa =[r['id'] for r in rows if r['fails'] and Decimal(r['toa'])!=0]
ce_const=[r['id'] for r in rows if r['fails'] and set(r['bals'])!={r['B']}]
ce_int =[r['id'] for r in rows if r['fails'] and r['isum']!=0]
ce_disb=[r['id'] for r in rows if r['fails'] and r['disb_principal']!=r['B']]
ce_tob =[r['id'] for r in rows if r['fails'] and r['tob_last']!=0]
print("failing where principal column != disbursement :", len(ce_psum), ce_psum[:5])
print("failing where totalOutstandingAmount != 0      :", len(ce_toa), ce_toa[:5])
print("failing where balance column NOT constant=B    :", len(ce_const), ce_const[:5])
print("failing where interest column sums != 0        :", len(ce_int), ce_int[:5])
print("failing where disbursement principal != B      :", len(ce_disb))
print("failing row-last totalOutstandingBalance != 0  :", len(ce_tob), ce_tob[:5])
ce_clean=[r['id'] for r in rows if not r['fails'] and r['psum']!=r['B']]
print("CLEAN where principal column != disbursement   :", len(ce_clean), ce_clean[:5])

print("\n--- closed form, exact rationals ---")
mism=[]
for r in rows:
    rr = Fraction(Decimal(r['rate']))/100/12
    a = rr/(1-(1+rr)**(-r['n']))
    pred = (Fraction(r['B'])*a) < Fraction(1,2)
    if pred != r['fails']: mism.append((r['id'], float(Fraction(r['B'])*a), r['fails'], pred))
print("closed-form mismatches over %d cells:" % len(rows), len(mism))
for m in mism[:10]: print(m)
json.dump(rows, open('/tmp/t84-rows.json','w'))
