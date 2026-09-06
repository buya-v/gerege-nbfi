"""T552 — independent re-derivation of the VETO 3 materiality floor.

Differences from T550's t550-materiality-floor.py, all deliberate:
  * VETO 2 (repeat payload) is APPLIED, as the shipped guard applies it.
    T550's script sets earned = anchor and subst only, i.e. it measures the
    floor against a classifier that is NOT the one shipped.
  * the 14-day lookback window is applied to the graded fire set, as the
    guard does (`graded`), and swept over historical `now` values.
  * the floor is swept 1..40 and the resulting longest no-op streak is
    reported, not just a single <=2 probe.

usage: python3 t552-floor.py <ref> <cwd> [now-iso]
"""
import subprocess, re, datetime, collections, hashlib, sys

REF = sys.argv[1]
CWD = sys.argv[2]
NOWS = sys.argv[3] if len(sys.argv) > 3 else None

SURF = re.compile(r'^nexus/|^\.softhouse/(capture|vectors|handoff|reviews|guards|bin)/|^\.claude/|^docs/adr/')
BOOK = re.compile(r'^\.softhouse/(LOCK|RESUME\.md)$|^\.softhouse/(state|logs|runs)/')
NULL = re.compile(r'^[\s{}()\[\];,.:*=_~`>|+-]*(//+|\#+|--+|<!--|-->|/\*+|\*+/|\*+)?'
                  r'[\s{}()\[\];,.:*=_~`>|+-]*$')
DIGIT_RUN = re.compile(r'[0-9a-f]{4,}|[0-9]+', re.I)
WS_RUN = re.compile(r'\s+')
LOCK = '.softhouse/LOCK'
LOOKBACK = 14

def sh(cmd):
    return subprocess.run(['bash', '-c', cmd], capture_output=True, text=True,
                          cwd=CWD, errors='replace').stdout

raw = sh(f"git log {REF} --no-merges --numstat --format='@@%H|%cI'")
commits = []
cur = None
for line in raw.splitlines():
    if line.startswith('@@'):
        sha, ts = line[2:].split('|', 1)
        cur = {'sha': sha, 'ts': ts, 'files': [], 'stat': []}
        commits.append(cur)
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
pay = collections.defaultdict(list)
sha = None; on = False
for line in p.splitlines():
    if line.startswith('@COMMIT@'):
        sha = line[8:].strip(); on = False
    elif line.startswith('+++ '):
        q = line[4:].strip()
        q = q[2:] if q.startswith('b/') else q
        on = q != '/dev/null' and bool(SURF.search(q))
    elif on and sha and line.startswith('+'):
        pay[sha].append(line[1:])

def digest(lines):
    norm = '\n'.join(DIGIT_RUN.sub('#', WS_RUN.sub(' ', l.strip().lower())) for l in lines)
    return hashlib.sha256(norm.encode('utf-8', 'replace')).hexdigest()[:16]

for c in commits:
    c['dt'] = datetime.datetime.fromisoformat(c['ts'])
    c['off'] = c['ts'][-6:]
    c['anchor'] = [f for f in c['files'] if SURF.search(f)]
    c['subst'] = [l for l in pay.get(c['sha'], []) if not NULL.match(l)]
    c['dig'] = digest(c['subst']) if c['subst'] else None
    c['n'] = len(c['subst'])

now = (datetime.datetime.fromisoformat(NOWS) if NOWS else commits[-1]['dt'])
if now.tzinfo is None:
    now = now.replace(tzinfo=datetime.timezone.utc)
commits = [c for c in commits if c['dt'] <= now]
window_start = now - datetime.timedelta(days=LOOKBACK)

def lev(c):
    if not c['stat'] or any(x != LOCK for x, _, _ in c['stat']):
        return None
    i = sum(a for _, a, _ in c['stat']); d = sum(b for _, _, b in c['stat'])
    if i > 0 and d == 0: return 'take'
    if d > 0 and i == 0: return 'release'
    return 'take' if i else None

def earned_set(floor, veto2=True):
    """Replicate the shipped classifier at a given VETO 3 floor.
    veto2=False reproduces T550's own measurement classifier."""
    seen = {}
    out = set()
    for c in commits:                      # veto 2 is keyed per producer offset
        if not c['anchor']:      continue
        if not c['subst']:       continue
        if c['n'] < floor:       continue
        if not veto2:
            out.add(c['sha']); continue
        key = (c['off'], c['dig'])
        first = seen.get(key)
        if first is None:
            seen[key] = c['sha']; out.add(c['sha'])
        elif c['dt'] < window_start:
            out.add(c['sha'])
    return out

for off, label in (('+08:00', 'local'), ('+00:00', 'cloud')):
    pool = [c for c in commits if c['off'] == off]
    fires = sorted([c for c in pool if lev(c) == 'take'], key=lambda c: c['dt'])
    wins = [(f, fires[i+1]['dt'] if i+1 < len(fires) else now) for i, f in enumerate(fires)]
    graded = [(f, e) for (f, e) in wins if f['dt'] >= window_start]
    print(f"\n=== {label}  fires(all)={len(fires)}  fires(graded, 14d)={len(graded)}  now={now.isoformat()}")
    for scope, fs in (('ALL FIRES', wins), ('GRADED (14d)', graded)):
        for v2, tag in ((False, 'veto2 OFF (=T550 method)'), (True, 'veto2 ON (=shipped)')):
            base = earned_set(1, v2)
            cleared, per_fire_max = 0, []
            for (f, e) in fs:
                r = [c for c in pool if f['dt'] <= c['dt'] < e and c['sha'] in base]
                if r:
                    cleared += 1
                    per_fire_max.append(max(c['n'] for c in r))
            mn = min(per_fire_max) if per_fire_max else None
            print(f"  {scope:<12} {tag:<26}: cleared={cleared}/{len(fs)}  "
                  f"min-over-cleared-fires(max subst lines)={mn}")
            if per_fire_max:
                print(f"      smallest ten per-fire maxima: {sorted(per_fire_max)[:10]}")
    # floor sweep on the graded set, longest no-op streak
    print("    floor sweep (graded 14d, veto2 ON): floor -> cleared fires, longest no-op run")
    prev = None
    for floor in list(range(1, 21)) + [24, 28, 32, 40]:
        es = earned_set(floor, True)
        run = best = 0; cleared = 0
        for (f, e) in graded:
            r = [c for c in pool if f['dt'] <= c['dt'] < e and c['sha'] in es]
            if r: cleared += 1; run = 0
            else: run += 1; best = max(best, run)
        line = (cleared, best)
        if line != prev:
            print(f"      floor={floor:>3}  cleared={cleared:>3}/{len(graded)}  longest-no-op-run={best}")
            prev = line
