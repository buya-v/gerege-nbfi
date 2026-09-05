"""T552 — false-RED sweep. Replays BOTH classifiers hourly over the whole
recorded history and reports every instant where the T550 guard says RED and
the T493 guard said GREEN, split by which axis caused it.

usage: python3 t552-sweep.py <ref> <cwd>
"""
import subprocess, re, datetime, collections, hashlib, sys

REF, CWD = sys.argv[1], sys.argv[2]
SURF = re.compile(r'^nexus/|^\.softhouse/(capture|vectors|handoff|reviews|guards|bin)/|^\.claude/|^docs/adr/')
BOOK = re.compile(r'^\.softhouse/(LOCK|RESUME\.md)$|^\.softhouse/(state|logs|runs)/')
NULL = re.compile(r'^[\s{}()\[\];,.:*=_~`>|+-]*(//+|\#+|--+|<!--|-->|/\*+|\*+/|\*+)?'
                  r'[\s{}()\[\];,.:*=_~`>|+-]*$')
DR = re.compile(r'[0-9a-f]{4,}|[0-9]+', re.I); WS = re.compile(r'\s+')
LOCK = '.softhouse/LOCK'
SIL, EARN, STREAK, LOOK, FLOOR = 18.0, 36.0, 6, 14, 8

def sh(c):
    return subprocess.run(['bash', '-c', c], capture_output=True, text=True,
                          cwd=CWD, errors='replace').stdout

raw = sh(f"git log {REF} --no-merges --numstat --format='@@%H|%cI'")
commits = []; cur = None
for line in raw.splitlines():
    if line.startswith('@@'):
        sha, ts = line[2:].split('|', 1)
        cur = {'sha': sha, 'ts': ts, 'files': [], 'stat': []}; commits.append(cur)
    elif line.strip() and cur:
        p = line.split('\t')
        if len(p) >= 3:
            cur['files'].append(p[2])
            cur['stat'].append((p[2], 0 if p[0] == '-' else int(p[0]),
                                       0 if p[1] == '-' else int(p[1])))
commits.reverse()
p = sh(f"git log {REF} --no-merges -p -U0 --no-color --format='@COMMIT@%H' | "
       "awk '/^@COMMIT@/{n=0;print;next} /^\\+\\+\\+ /{print;next} "
       "/^\\+/{if(n<200){print;n++} next}'")
pay = collections.defaultdict(list); sha = None; on = False
for line in p.splitlines():
    if line.startswith('@COMMIT@'): sha = line[8:].strip(); on = False
    elif line.startswith('+++ '):
        q = line[4:].strip(); q = q[2:] if q.startswith('b/') else q
        on = q != '/dev/null' and bool(SURF.search(q))
    elif on and sha and line.startswith('+'): pay[sha].append(line[1:])

def dig(ls):
    return hashlib.sha256('\n'.join(DR.sub('#', WS.sub(' ', l.strip().lower()))
                                    for l in ls).encode('utf-8', 'replace')).hexdigest()[:16]

for c in commits:
    c['dt'] = datetime.datetime.fromisoformat(c['ts']); c['off'] = c['ts'][-6:]
    c['carry'] = [f for f in c['files'] if not BOOK.search(f)]
    c['anchor'] = [f for f in c['files'] if SURF.search(f)]
    c['subst'] = [l for l in pay.get(c['sha'], []) if not NULL.match(l)]
    c['dig'] = dig(c['subst']) if c['subst'] else None

def lev(c):
    if not c['stat'] or any(x != LOCK for x, _, _ in c['stat']): return None
    i = sum(a for _, a, _ in c['stat']); d = sum(b for _, _, b in c['stat'])
    if i > 0 and d == 0: return 'take'
    if d > 0 and i == 0: return 'release'
    return 'take' if i else None

def verdicts(now, off):
    cs = [c for c in commits if c['dt'] <= now]
    if not cs: return None
    ws = now - datetime.timedelta(days=LOOK)
    seen = {}; earned = set()
    for c in cs:
        if not (c['anchor'] and c['subst'] and len(c['subst']) >= FLOOR): continue
        k = (c['off'], c['dig'])
        if k not in seen: seen[k] = c['sha']; earned.add(c['sha'])
        elif c['dt'] < ws: earned.add(c['sha'])
    pool = [c for c in cs if c['off'] == off]
    if not pool: return None
    fires = sorted([c for c in pool if lev(c) == 'take'], key=lambda c: c['dt'])
    wins = [(f, fires[i+1]['dt'] if i+1 < len(fires) else now) for i, f in enumerate(fires)]
    graded = [(f, e) for (f, e) in wins if f['dt'] >= ws]
    def streak(pred):
        s = 0
        for (f, e) in reversed(graded):
            if any(pred(c) and f['dt'] <= c['dt'] < e for c in pool): break
            s += 1
        return s
    # NEW
    s_new = streak(lambda c: c['sha'] in earned)
    carrys = [c for c in pool if c['carry']]
    a2 = (not carrys) or ((now - carrys[-1]['dt']).total_seconds()/3600.0 > SIL)
    reals = [c for c in pool if c['sha'] in earned]
    a3 = (not reals) or ((now - reals[-1]['dt']).total_seconds()/3600.0 > EARN)
    new = (s_new >= STREAK, a2, a3)
    # OLD (T493): real == carries anything outside the bookkeeping blocklist
    s_old = streak(lambda c: bool(c['carry']))
    old = (s_old >= STREAK, a2)
    return new, old, s_new, s_old

start = commits[0]['dt']; end = commits[-1]['dt']
for off, label in (('+08:00', 'local'), ('+00:00', 'cloud')):
    t = start.astimezone(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
    flips = []; n = 0
    while t <= end:
        r = verdicts(t, off)
        if r:
            new, old, sn, so = r
            n += 1
            if any(new) and not any(old):
                cause = ('AXIS1' if new[0] else '') + ('+AXIS3' if new[2] else '')
                flips.append((t, cause, sn, so))
        t += datetime.timedelta(hours=1)
    print(f"\n{label}: {n} hourly instants replayed, {len(flips)} instants RED(new) but GREEN(old)")
    # collapse to runs
    runs = []
    for f in flips:
        if runs and (f[0] - runs[-1][1]) <= datetime.timedelta(hours=1) and runs[-1][2] == f[1]:
            runs[-1][1] = f[0]
        else:
            runs.append([f[0], f[0], f[1]])
    for a, b, c in runs:
        print(f"   {a.astimezone(datetime.timezone.utc):%Y-%m-%dT%H}Z .. {b.astimezone(datetime.timezone.utc):%Y-%m-%dT%H}Z  ({int((b-a).total_seconds()//3600)+1}h)  cause={c}")
