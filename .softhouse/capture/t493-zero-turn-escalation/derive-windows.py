#!/usr/bin/env python3
"""T493 — re-derive the outage windows straight from git. Self-contained:
it shells out to git itself, so it can be re-run in any full clone.

An outage is measured as a GAP BETWEEN CONSECUTIVE *REAL* COMMITS, not as a
count of calendar days. Calendar-day counting is timezone-dependent (the brief's
"09-01 = 2 commits" and this repo's "09-01 = 34 commits" are the same history
read in UTC vs Asia/Ulaanbaatar), whereas a gap between two commit timestamps is
the same fact in every zone.

Usage: derive-windows.py [ref] [--now ISO8601]
"""
import re, sys, subprocess, datetime

BOOK = re.compile(r'^\.softhouse/(LOCK|RESUME\.md)$|^\.softhouse/(state|logs|runs)/')
UTC  = datetime.timezone.utc

ref = 'origin/main'
now = None
args = sys.argv[1:]
while args:
    a = args.pop(0)
    if a == '--now': now = datetime.datetime.fromisoformat(args.pop(0))
    else: ref = a
now = now or datetime.datetime.now(UTC)

raw = subprocess.run(['git', 'log', ref, '--no-merges', '--name-only',
                      '--format=@@%H|%cI'], capture_output=True, text=True).stdout
rows, cur = [], None
for ln in raw.split('\n'):
    if ln.startswith('@@'):
        if cur: rows.append(cur)
        h, t = ln[2:].split('|'); cur = {'h': h[:8], 't': t, 'f': []}
    elif ln.strip() and cur is not None:
        cur['f'].append(ln)
if cur: rows.append(cur)
rows.reverse()
for r in rows:
    r['d'] = datetime.datetime.fromisoformat(r['t'])
    r['local'] = r['t'].endswith('+08:00')
    r['real'] = any(not BOOK.search(f) for f in r['f'])

print(f"ref={ref}  non-merge commits={len(rows)}  "
      f"real={sum(1 for r in rows if r['real'])}  bookkeeping={sum(1 for r in rows if not r['real'])}")

def gaps(seq, label, thresh=12.0):
    print(f"\n=== {label}: gaps between consecutive REAL commits > {thresh:g}h ===")
    for a, b in zip(seq, seq[1:]):
        g = (b['d'] - a['d']).total_seconds() / 3600
        if g > thresh:
            print(f"  {g:6.1f}h  {a['d'].astimezone(UTC):%Y-%m-%d %H:%MZ} {a['h']}"
                  f"  ->  {b['d'].astimezone(UTC):%Y-%m-%d %H:%MZ} {b['h']}")

real  = [r for r in rows if r['real']]
lreal = [r for r in real if r['local']]
gaps(real,  "ALL PRODUCERS")
print("  NOTE: the 19-25h entries here are the CLOUD fire's once-daily cadence, which is")
print("  healthy. This is why a guard must watch ONE PRODUCER, not the ref as a whole.")
gaps(lreal, "LOCAL PRODUCER ONLY (+08:00, Buyan's Mac)")

print(f"\nlast LOCAL real commit : {lreal[-1]['d'].astimezone(UTC):%Y-%m-%d %H:%M:%SZ} {lreal[-1]['h']}"
      f"   -> silence {(now - lreal[-1]['d']).total_seconds()/3600:.1f}h")
print(f"last ANY   real commit : {real[-1]['d'].astimezone(UTC):%Y-%m-%d %H:%M:%SZ} {real[-1]['h']}"
      f"   -> silence {(now - real[-1]['d']).total_seconds()/3600:.1f}h")
print("\nTHE DECISIVE PAIR: while the LOCAL producer has been silent for ~49h, the ALL-")
print("PRODUCERS silence is ~0h, because the cloud fire is committing. A watcher aimed")
print("at the ref rather than at a producer reports GREEN throughout the live outage.")
