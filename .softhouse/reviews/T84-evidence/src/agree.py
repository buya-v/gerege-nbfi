import json
rep = json.load(open('/tmp/t84-port-report.json'))
rows = {r['id']: r for r in json.load(open('/tmp/t84-eval-rows.json')) + json.load(open('/tmp/t84b-rows.json'))}
fail = [k for k, v in rows.items() if v['fails']]
div = {r[0] for r in rep if r[1] == 'OK' and r[2]}
agree_fail = sorted(set(fail) - div)
print("failing cells:", len(fail), " port-divergent:", len(set(fail) & div),
      " port AGREES (both non-amortizing):", len(agree_fail))
for k in agree_fail:
    v = rows[k]
    print("   %-28s rate=%-6s n=%-4d B=%-3d principalColumnSum=%d (disbursed %d)"
          % (k, v['rate'], v['n'], v['B'], v['psum'], v['B']))
print("\nclean cells the port diverges on:", sorted(div - set(fail)))
