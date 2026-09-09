#!/bin/bash
# =============================================================================
# ohwatch.sh [conversation-dir ...]   -- status of every live OpenHands run.
#
# DETECTS THE STALL SIGNATURE, NOT CPU. A stalled agent is not an idle process:
# K sat at 14% CPU doing nothing for 12 minutes. The signature is the agent
# polling a DEAD TERMINAL -- an EMPTY terminal command, an observation carrying
# exit_code -1, then ANOTHER empty command. CPU load says nothing about it.
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
tail = ev[-12:]
empty_cmds = 0; neg_exit = 0; lastact = ''
for f in tail:
    try: o = json.load(open(f))
    except Exception: continue
    a = o.get('action') or {}
    if o.get('kind') == 'ActionEvent':
        c = (a.get('command') or '')
        lastact = c.strip().replace('\n',' ')[:88] or lastact
        if a.get('kind') == 'TerminalAction' and not c.strip():
            empty_cmds += 1
    ob = o.get('observation') or {}
    if ob.get('exit_code') == -1 or ob.get('metadata',{}).get('exit_code') == -1:
        neg_exit += 1
# The signature is the CONJUNCTION: repeated empty commands AND a -1 exit.
# Either alone is normal -- an agent legitimately sends an empty command once to
# drain a long-running terminal, and -1 appears on a genuine timeout.
stalled = 'STALLED' if (empty_cmds >= 2 and neg_exit >= 1) else ''
print('%-34s events=%-5s idle=%4ds  empty=%d exit-1=%d  %s' %
      (os.path.basename(d.rstrip('/'))[:32], n, idle, empty_cmds, neg_exit, stalled))
print('    last: %s' % (lastact or '(none)'))
PY
done
