import gzip, json, glob, os
from fractions import Fraction

files = sorted(glob.glob('.softhouse/capture/**/*.json.gz', recursive=True)) + sorted(
    glob.glob('.softhouse/reviews/**/*.json.gz', recursive=True))
FOUR = {'capture-t117-raw.json.gz', 'capture-t117p2-raw.json.gz',
        'capture-t159-raw.json.gz', 'capture-t223-raw.json.gz'}


def term(r):
    fr = Fraction(r) / 1200
    d = fr.denominator
    a = b = 0
    while d % 2 == 0:
        d //= 2
        a += 1
    d = fr.denominator
    while d % 5 == 0:
        d //= 5
        b += 1
    d = fr.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1 and max(a, b) <= 19


preds = {
    'row1zero': lambda pr: pr[0] == 0,
    'allbutlast': lambda pr: all(x == 0 for x in pr[:-1]),
    'row1and2zero': lambda pr: len(pr) > 1 and pr[0] == 0 and pr[1] == 0,
}
for scope, sel in (('t229corpus', FOUR), ('all', None)):
    for name, pred in preds.items():
        st = 0
        stcal = 0
        for f in files:
            bn = os.path.basename(f)
            if sel is not None and bn not in sel:
                continue
            d = json.loads(gzip.open(f, 'rt').read())
            for c in d['captures']:
                if c.get('observed') is None:
                    continue
                if not term(c['inputs']['annualNominalInterestRate']):
                    continue
                rows = [p for p in c['observed']['periods'] if p['type'] == 'REPAYMENT']
                pr = [int(r['principal'].replace('.', '')) for r in rows]
                if pred(pr):
                    st += 1
                    if c['id'].startswith('P-CAL') or 'WARM' in c['id']:
                        stcal += 1
        print(scope, name, 'stuck', st, 'cal/warm', stcal, 'minus', st - stcal)
