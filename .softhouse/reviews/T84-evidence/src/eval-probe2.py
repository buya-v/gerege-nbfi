import json
from decimal import Decimal

doc = json.load(open('/tmp/t84probe2/out/capture-t84b-raw.json'))
pred = json.load(open('/tmp/t84b-prediction.json'))

def minor(s):
    d = Decimal(s) * 100
    assert d == d.to_integral_value(), s
    return int(d)

rows = []
for c in doc['captures']:
    if not c['id'].startswith('T84B-'):
        continue
    i, o = c['inputs'], c['observed']
    B = minor(i['disbursementAmount']); n = i['numberOfRepayments']; rate = str(i['annualNominalInterestRate'])
    reps = [p for p in o['periods'] if p['type'] == 'REPAYMENT']
    last = minor(reps[-1]['balance'])
    psum = sum(minor(p['principal']) for p in reps)
    isum = sum(minor(p['interest']) for p in reps)
    rows.append(dict(id=c['id'], rate=rate, n=n, B=B, fails=last != 0, psum=psum, isum=isum,
                     toa=o['totalOutstandingAmount'], tp=o['totalPrincipalAmount'],
                     td=o['totalDisbursedAmount'],
                     bals_const=(set(minor(p['balance']) for p in reps) == {B})))

print("=== 600.0%% / B=1, n boundary (closed form predicts CLEAN everywhere: B*a > 0.5) ===")
print("%-5s %-6s %-12s %-10s %-9s %-9s %s" % ("n", "fails", "gap(B*a-.5)", "princSum", "intSum", "totOut", "principal-column-amortizes"))
for r in [x for x in rows if x['rate'] == '600.0']:
    g = pred[r['id']]['gap']
    print("%-5d %-6s %-12.3e %-10d %-9d %-9s %s"
          % (r['n'], r['fails'], g, r['psum'], r['isum'], r['toa'], r['psum'] == r['B']))

print("\n=== 300.0%% / B=2, n boundary ===")
print("%-5s %-6s %-12s %-10s %-9s %s" % ("n", "fails", "gap", "princSum", "intSum", "principal-column-amortizes"))
for r in [x for x in rows if x['rate'] == '300.0']:
    g = pred[r['id']]['gap']
    print("%-5d %-6s %-12.3e %-10d %-9d %s" % (r['n'], r['fails'], g, r['psum'], r['isum'], r['psum'] == r['B']))

print("\n=== XL: low rate x very long term -- how big does a failing principal get? ===")
for r in [x for x in rows if x['id'].startswith('T84B-XL')]:
    print("  rate %-6s n=%-4d B=%-4d (MNT %-5s) fails=%-6s princSum=%-4d ==B? %-6s balConst=%-6s totOut=%s"
          % (r['rate'], r['n'], r['B'], Decimal(r['B']).scaleb(-2), r['fails'], r['psum'],
             r['psum'] == r['B'], r['bals_const'], r['toa']))

print("\n=== closed-form check on this probe ===")
miss = [(r['id'], pred[r['id']]['gap'], pred[r['id']]['predictedFails'], r['fails'])
        for r in rows if pred[r['id']]['predictedFails'] != r['fails']]
print("refutations:", len(miss), "/", len(rows))
for m in miss:
    print("   ", m)

print("\n=== REFRAMING counterexamples in this probe (failing cells) ===")
f = [r for r in rows if r['fails']]
ce = [r for r in f if r['psum'] != r['B']]
print("  failing cells:", len(f), " where principal column != disbursement:", len(ce))
for r in ce:
    print("     %-28s rate=%-6s n=%-4d B=%d  principal column sums to %d, totalPrincipalAmount=%s, totalDisbursed=%s, totOut=%s"
          % (r['id'], r['rate'], r['n'], r['B'], r['psum'], r['tp'], r['td'], r['toa']))
print("  failing where balance column NOT constant:", len([r for r in f if not r['bals_const']]))
print("  failing where totalOutstandingAmount != 0:", len([r for r in f if Decimal(r['toa']) != 0]))
json.dump(rows, open('/tmp/t84b-rows.json', 'w'))
