#!/usr/bin/env python3
"""t553-sweep.py <ref> <repo> [floor]

NEGATIVE CONTROL for T553's composition fix (T552 MAJOR-1).

Replays the WHOLE recorded history hourly under two classifiers and reports
every instant where the verdict differs:

  OLD  = T550's shipped classifier — VETO 2 over the WHOLE digit-collapsed
         payload digest, VETO 3 counting the RAW substantive multiset.
  NEW  = T553's composed classifier — VETO 2a (whole-payload digest, kept),
         VETO 2b (per-line novelty, digit-PRESERVING), VETO 3 counting only the
         NOVEL residue.

It also re-derives the materiality floor under the new rule: over every fire
that cleared, the minimum of (max NOVEL substantive lines carried by any of its
promotions). If that minimum sits at or below the floor of 8, the floor is
producing false REDs on real work and the number must move.

Both classifiers are re-implemented here from the shipped guard rather than
imported, so a mistake in the guard cannot hide inside its own control. The
axes are the guard's: AXIS 1 no-op streak, AXIS 2 silence, AXIS 3 earned
silence, verdict = OR.
"""
import subprocess, re, sys, datetime, hashlib, collections, bisect

REF  = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
CWD  = sys.argv[2] if len(sys.argv) > 2 else '.'
FLOOR = int(sys.argv[3]) if len(sys.argv) > 3 else 8
STREAK_N, SILENCE_H, EARNED_H, LOOKBACK_D, CAP = 6, 18.0, 36.0, 14.0, 200

SURF = re.compile(r'^nexus/|^\.softhouse/(capture|vectors|handoff|reviews|guards|bin)/|^\.claude/|^docs/adr/')
BOOK = re.compile(r'^\.softhouse/(LOCK|RESUME\.md)$|^\.softhouse/(state|logs|runs)/')
NULL = re.compile(r'^[\s{}()\[\];,.:*=_~`>|+-]*(//+|\#+|--+|<!--|-->|/\*+|\*+/|\*+)?'
                  r'[\s{}()\[\];,.:*=_~`>|+-]*$')
DIGIT = re.compile(r'[0-9a-f]{4,}|[0-9]+', re.I)
WS    = re.compile(r'\s+')
LOCK  = '.softhouse/LOCK'

def sh(args):
    return subprocess.run(args, capture_output=True, text=True, cwd=CWD,
                          errors='replace').stdout

raw = sh(['git', 'log', REF, '--no-merges', '--numstat', '--format=@@%H|%cI'])
commits, cur = [], None
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

pcmd = ("git log %s --no-merges -p -U0 --no-color --format='@COMMIT@%%H' | "
        "awk '/^@COMMIT@/{n=0;print;next} /^\\+\\+\\+ /{print;next} "
        "/^\\+/{if(n<%d){print;n++} next}'" % (REF, CAP))
pay = collections.defaultdict(list)
sha, on = None, False
for line in sh(['bash', '-c', pcmd]).splitlines():
    if line.startswith('@COMMIT@'):
        sha = line[8:].strip(); on = False
    elif line.startswith('+++ '):
        q = line[4:].strip()
        q = q[2:] if q.startswith('b/') else q
        on = q != '/dev/null' and bool(SURF.search(q))
    elif on and sha and line.startswith('+'):
        pay[sha].append(line[1:])

def norm_shape(l): return DIGIT.sub('#', WS.sub(' ', l.strip().lower()))
def norm_line(l):  return WS.sub(' ', l.strip().lower())
def lkey(l): return hashlib.blake2b(norm_line(l).encode('utf-8', 'replace'), digest_size=8).digest()
def pdig(ls):
    return hashlib.sha256('\n'.join(norm_shape(l) for l in ls).encode('utf-8', 'replace')).hexdigest()[:16]

for c in commits:
    c['dt']   = datetime.datetime.fromisoformat(c['ts'])
    c['off']  = c['ts'][-6:]
    c['carrying'] = any(not BOOK.search(f) for f in c['files'])
    c['anchor']   = any(SURF.search(f) for f in c['files'])
    c['subst']    = [l for l in pay.get(c['sha'], []) if not NULL.match(l)]
    c['digest']   = pdig(c['subst']) if c['subst'] else None
    c['keys']     = [lkey(l) for l in c['subst']] if c['subst'] else []

# ---- NEW classifier: now-INDEPENDENT (novelty is a property of what came before)
seen_p, seen_l = {}, {}
for c in commits:
    c['earned_new'], c['novel_n'] = False, 0
    if not (c['anchor'] and c['subst']):
        continue
    novel, here = 0, set()
    for k in c['keys']:
        if (c['off'], k) in seen_l or k in here:
            continue
        here.add(k); novel += 1
    repeat_payload = (c['off'], c['digest']) in seen_p
    seen_p.setdefault((c['off'], c['digest']), c['sha'])
    for k in c['keys']:
        seen_l.setdefault((c['off'], k), c['sha'])
    c['novel_n'] = novel
    c['earned_new'] = (not repeat_payload) and novel >= FLOOR

# ---- OLD classifier: depends on `now` through VETO 2's pre-window exemption
def old_earned(window_start):
    seen, out = {}, set()
    for c in commits:
        if not (c['anchor'] and c['subst'] and len(c['subst']) >= FLOOR):
            continue
        key = (c['off'], c['digest'])
        if key not in seen:
            seen[key] = c['sha']; out.add(c['sha'])
        elif c['dt'] < window_start:
            out.add(c['sha'])
    return out

def lock_event(c):
    if not c['stat'] or any(p != LOCK for p, _, _ in c['stat']):
        return None
    ins = sum(i for _, i, _ in c['stat']); dele = sum(d for _, _, d in c['stat'])
    if ins > 0 and dele == 0: return 'take'
    if dele > 0 and ins == 0: return 'release'
    return 'take' if ins else None

for c in commits:
    c['is_take'] = lock_event(c) == 'take'
DTS = [c['dt'] for c in commits]

def verdict(now, off, earned_shas):
    idx = bisect.bisect_right(DTS, now)
    pool = [c for c in commits[:idx] if c['off'] == off]
    if not pool:
        return 'REFUSE', None
    ws = now - datetime.timedelta(days=LOOKBACK_D)
    reals  = [c for c in pool if c['sha'] in earned_shas]
    carrys = [c for c in pool if c['carrying']]
    fires  = sorted([c for c in pool if c['is_take']], key=lambda c: c['dt'])
    wins = [(c, fires[i+1]['dt'] if i+1 < len(fires) else now) for i, c in enumerate(fires)]
    graded = [(c, e) for (c, e) in wins if c['dt'] >= ws]
    streak = 0
    for (c, e) in reversed(graded):
        if [r for r in reals if c['dt'] <= r['dt'] < e]:
            break
        streak += 1
    a1 = streak >= STREAK_N
    a2 = (not carrys) or ((now - carrys[-1]['dt']).total_seconds() / 3600.0 > SILENCE_H)
    a3 = (not reals)  or ((now - reals[-1]['dt']).total_seconds() / 3600.0 > EARNED_H)
    return ('RED' if (a1 or a2 or a3) else 'GREEN'), (streak, a1, a2, a3)

new_shas = {c['sha'] for c in commits if c['earned_new']}
t0 = commits[0]['dt'].astimezone(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
t1 = commits[-1]['dt'].astimezone(datetime.timezone.utc)

for off, label in [('+08:00', 'local'), ('+00:00', 'cloud')]:
    n, diffs = 0, []
    t = t0 + datetime.timedelta(hours=1)
    while t <= t1:
        old = verdict(t, off, old_earned(t - datetime.timedelta(days=LOOKBACK_D)))
        new = verdict(t, off, new_shas)
        n += 1
        if old[0] != new[0]:
            diffs.append((t, old, new))
        t += datetime.timedelta(hours=1)
    print(f"{label}: {n} hourly instants replayed")
    newred = [d for d in diffs if d[2][0] == 'RED' and d[1][0] == 'GREEN']
    newgrn = [d for d in diffs if d[2][0] == 'GREEN' and d[1][0] == 'RED']
    print(f"   RED(new) but GREEN(old): {len(newred)}")
    for t, old, new in newred:
        print(f"      {t:%Y-%m-%dT%HZ}  old={old[1]}  new={new[1]}  (streak,a1,a2,a3)")
    print(f"   GREEN(new) but RED(old): {len(newgrn)}")
    for t, old, new in newgrn:
        print(f"      {t:%Y-%m-%dT%HZ}  old={old[1]}  new={new[1]}")

    # ---- floor re-derivation under the NEW rule ----------------------------
    pool  = [c for c in commits if c['off'] == off]
    fires = sorted([c for c in pool if c['is_take']], key=lambda c: c['dt'])
    now   = commits[-1]['dt']
    ws    = now - datetime.timedelta(days=LOOKBACK_D)
    for scope, sel in (('ALL FIRES', lambda f: True), ('GRADED (14d)', lambda f: f['dt'] >= ws)):
        mins, cleared = [], 0
        for i, f in enumerate(fires):
            if not sel(f):
                continue
            end = fires[i+1]['dt'] if i+1 < len(fires) else now
            r = [c for c in pool if c['earned_new'] and f['dt'] <= c['dt'] < end]
            if not r:
                continue
            cleared += 1
            mins.append(max(c['novel_n'] for c in r))
        tot = len([f for f in fires if sel(f)])
        print(f"   {scope:12s} NEW rule: cleared={cleared}/{tot}  "
              f"min-over-cleared-fires(max NOVEL lines)={min(mins) if mins else None}  "
              f"smallest ten={sorted(mins)[:10]}")
