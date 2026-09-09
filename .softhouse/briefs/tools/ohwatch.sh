#!/bin/bash
# =============================================================================
# ohwatch.sh [conversation-dir ...]   -- status of every live OpenHands run.
#
# DETECTS THE STALL SIGNATURE, NOT CPU. A stalled agent is not an idle process:
# K sat at 14% CPU doing nothing for 12 minutes. The signature is the agent unable to
# run a command -- observations carrying exit_code -1 because a previous command is
# still running. CPU load says nothing about it.
#
# FIRES ON THE TAIL, NOT ON PRESENCE. A -1 followed by a success is a stall the agent
# RECOVERED from ("Terminal session has been reset"), which is normal and must not fire.
#
# Prints, per run: age, event count, seconds since the last event, the last
# action, and STALLED if the signature is present in the recent tail.
# =============================================================================
set -u
now=$(date +%s)
dirs=${@:-$(ls -dt ~/.openhands/conversations/*/ 2>/dev/null | head -6)}
printf '%s\n' "$dirs" | tr ' ' '\n' | while IFS= read -r d; do
  [ -d "$d/events" ] || continue
  n=$(ls "$d/events" 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" -gt 0 ] || continue
  last=$(ls -t "$d/events" | head -1)
  lm=$(stat -f %m "$d/events/$last")
  python3 - "$d" "$n" $((now-lm)) <<'PY'
import json,sys,os,glob
d,n,idle = sys.argv[1], sys.argv[2], int(sys.argv[3])
ev = sorted(glob.glob(os.path.join(d,'events','event-*.json')))

# THE PROPERTY IS "CANNOT RUN A COMMAND RIGHT NOW", NOT "SENT AN EMPTY COMMAND".
# The first version of this tested empty-command-plus-a--1, which is the SHAPE OF ONE
# EXAMPLE, not the property. Measured against a real stall on 2026-09-09: the agent
# probed a wedged terminal with `echo hi`, `C-c` and `echo alive` -- none of them empty
# -- and six -1 exits went undetected because the empty-command clause never fired.
#
# What actually says "stalled" is the TAIL: the most recent observations still carrying
# exit_code -1. A -1 EARLIER in the tail followed by a success is a stall the agent
# RECOVERED from -- OpenHands prints "Terminal session has been reset" and carries on --
# and firing on that would cry wolf on a healthy run. So: walk observations backwards
# and fire only while the LAST ones are -1.
def exit_code(o):
    ob = o.get('observation') or {}
    ec = ob.get('exit_code')
    return ob.get('metadata',{}).get('exit_code') if ec is None else ec

obs, lastact = [], ''
for f in ev[-40:]:
    try: o = json.load(open(f))
    except Exception: continue
    if o.get('kind') == 'ActionEvent':
        c = ((o.get('action') or {}).get('command') or '').strip().replace('\n',' ')
        if c: lastact = c[:88]
    else:
        obs.append(exit_code(o))

trailing = 0
for ec in reversed(obs):
    if ec == -1: trailing += 1
    else: break
recovered = sum(1 for ec in obs if ec == -1) - trailing

# Two trailing -1s is the threshold: one alone is an ordinary timeout the agent is about
# to handle, and the recovery path itself costs one probe.
flag = 'STALLED-NOW' if trailing >= 2 else ''
note = '' if not recovered else '  (%d recovered -1)' % recovered
print('%-34s events=%-5s idle=%4ds  trailing-1=%d%s  %s' %
      (os.path.basename(d.rstrip('/'))[:32], n, idle, trailing, note, flag))
print('    last: %s' % (lastact or '(none)'))
PY
done

