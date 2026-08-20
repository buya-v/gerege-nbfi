import json, os
from fractions import Fraction
from decimal import Decimal

RATE_FRAC = {}
cases = []
for src, idsf in (('/tmp/t84-prediction.json', None), ('/tmp/t84b-prediction.json', None)):
    d = json.load(open(src))
    for cid, v in d.items():
        f = Fraction(Decimal(v['rate'])) / 100
        cases.append((cid, v['B'], v['n'], f.numerator, f.denominator))
cases.sort()
lines = ['\t\tcs{"P-CAL-ZPA", 28, 56, 27, 125}, cs{"P-CAL-ZPB", 28, 55, 27, 125},']
for cid, B, n, num, den in cases:
    lines.append('\t\tcs{"%s", %d, %d, %d, %d},' % (cid, B, n, num, den))

tmpl = open('.softhouse/capture/t83-nonamortizing/src/t83port.go.txt').read()
start = tmpl.index('\trates := []rate{')
end = tmpl.index('\tstart := contract.CivilDate{')
block = ('\ttype cs struct {\n\t\tid        string\n\t\tprincipal int64\n\t\tn         int32\n'
         '\t\tnum, den  int64\n\t}\n\tcases := []cs{\n' + "\n".join(lines) + '\n\t}\n\n')
go = tmpl[:start] + block + tmpl[end:]
go = go.replace('"strings"\n', '')
go = go.replace('\t"fmt"\n', '\t"fmt"\n')
os.makedirs('/tmp/t84portsrc', exist_ok=True)
open('/tmp/t84portsrc/main.go', 'w').write(go)
print("cases:", len(cases) + 2)
