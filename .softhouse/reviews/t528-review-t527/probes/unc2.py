import json, subprocess, sys
REPO = sys.argv[1]
d = json.load(open('/tmp/claude-0/-home-user/871c1a31-81ad-5dca-b34a-be2993091ecc/scratchpad/real.json'))
checked = {f['subject'] for f in d['findings']}
checked |= {w['branch'] for w in d['waived']}
# per (task, sha): is that sha checked for that task anywhere?
pairs = {}
for x in d['unclassified_hex']:
    pairs.setdefault((x['task'], x['hex']), x['why'])
findpairs = {(f['task'], f['subject']) for f in d['findings']}
findpairs |= {(w['task'], w['branch']) for w in d['waived']}
resid = {}
for (tid, h), why in pairs.items():
    if (tid, h) in findpairs:
        continue
    resid.setdefault(h, []).append((tid, why))
print('distinct hex never checked for the task that names it:', len(resid))
by = {}
for h, v in resid.items():
    for tid, why in v:
        by[why] = by.get(why, 0) + 1
for k, n in sorted(by.items(), key=lambda x: -x[1]):
    print('   %-55s %d' % (k, n))
print()
print('--- no-anchor residue that does NOT resolve to a commit in this repo ---')
n = 0
for h in sorted(resid):
    whys = {w for _, w in resid[h]}
    if whys != {'no claim anchor matched'}:
        continue
    p = subprocess.run(['git', '-C', REPO, 'rev-parse', '--verify', '--quiet', h + '^{commit}'],
                       capture_output=True, text=True)
    if p.returncode == 0:
        continue
    n += 1
    print('  %-42s %s' % (h, ','.join(t for t, _ in resid[h])))
print('  total:', n)
