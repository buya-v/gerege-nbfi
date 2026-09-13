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
# LIVE WORKTREES, resolved from the process table once. A conversation directory outlives
# its process, so idle alone cannot tell a stalled run from a finished one -- the control
# test caught that immediately, lighting up a run that had been merged hours earlier.
# Liveness is the honest discriminator, so it is measured rather than inferred.
#
# 2026-09-11: the cwd is read from lsof's NAME field (-Fn), with a trailing " (deleted)"
# stripped. The old `awk '{print $NF}'` returned the literal "(deleted)" for a run whose
# worktree had been removed, so a LIVE run was reported "(no live process)" -- the driver
# salvaged OH-TIERD-BG as dead while it was still working, in a deleted worktree, in parallel
# with its replacement. Such a process is now also printed on its own ORPHAN line.
OH_LIVE=""
for p in $(ps aux | grep '[o]penhands/bin/python' | awk '{print $2}'); do
  cwd="$(lsof -a -p "$p" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | sed 's/ (deleted)$//' | tail -1)"
  [ -n "$cwd" ] || continue
  OH_LIVE="$OH_LIVE $cwd"
  [ -d "$cwd" ] || echo "ORPHAN  pid $p is a LIVE openhands run whose worktree $cwd NO LONGER EXISTS -- kill it by pid"
done
export OH_LIVE
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

# TWO TRAILING -1s IS NOT ENOUGH, and firing on it alone cried wolf twice on 2026-09-10.
# A run at trailing=2 with idle=2s had just issued a real command: it wedged, and it was
# already recovering. Two other runs that day did exactly the same and went on to finish
# (one of them closed the fee/penalty finding). The instantaneous condition -- "cannot run
# a command right now" -- is TRUE for a healthy agent mid-recovery, so it cannot be the
# kill signal on its own.
#
# The signature that matters is SUSTAINED. K sat wedged for TWELVE MINUTES. So a kill needs
# either evidence of TIME (nothing written for a long while) or evidence of REPETITION (the
# agent has burned four or more consecutive probes into a dead terminal -- the run killed on
# 2026-09-10 reached six, having advanced 8 events in 5 minutes, all of them failed probes).
#
#   trailing >= 2                -> WEDGED, visible, NOT a kill signal
#   trailing >= 4                -> STALLED-NOW (dead terminal, regardless of idle)
#   trailing >= 2 and idle>=180s -> STALLED-NOW (wedged and not recovering)
# THERE IS A THIRD STALL THAT HAS NOTHING TO DO WITH THE TERMINAL, and it went
# undetected on 2026-09-10 until a driver checked by hand. OH-GLVEC-AB sat at 11.6% CPU
# for TEN MINUTES with `trailing-1 = 0`: its command had COMPLETED (no process left, its
# output file stopped growing), it had not probed anything, and it simply never emitted
# another event. The shell was fine; the agent was blocked on the LLM -- the same
# provider that logged `DeepseekException - peer closed connection without sending
# complete message body` earlier that day, retried with backoff, and never came back.
#
# That is EXACTLY the shape of run K, which the user described as "14% CPU doing nothing
# for 12 minutes" -- and neither terminal rule above catches it, because there is no -1
# to count. CPU is not the signal either: 11.6% of a core is indistinguishable from work.
#
# THE SIGNAL IS SILENCE. A working agent emits events. Even a long command emits one when
# it finishes. So idle time ALONE is a stall, whatever the cause -- and it subsumes both
# terminal cases as a backstop.
#
# The threshold must clear a legitimately long command: `conformance.sh` takes ~5 minutes
# and emits nothing while it runs, so idle can honestly reach 300-400s. 600s is chosen to
# sit clear of that, and it is the number that fired on OH-GLVEC-AB at 597s.
# A FINISHED RUN IS NOT A STALLED ONE, and the first version of this rule could not tell
# them apart: a conversation directory outlives its process, so `idle` grows without bound
# and every completed run eventually looks silent. The control test caught it immediately --
# run K and a run that had finished successfully and been MERGED hours earlier both lit up.
#
# So the silent rule applies only inside a WINDOW. Below SILENT_S the agent may legitimately
# be inside a long command; above FINISHED_S it has almost certainly exited, and the driver
# would have merged or salvaged it long before. Outside the window the terminal rules still
# apply, and an old conversation is labelled `(idle>1h: likely finished)` rather than accused.
#
# The honest limitation, stated: this is a WINDOW, not a liveness check. ohwatch reads event
# streams, not the process table, so it cannot prove a run is alive. Confirm with
# `ps aux | grep openhands` before killing anything on a silent verdict.
SILENT_S     = 600
FINISHED_S   = 3600
STALL_IDLE_S = 180
STALL_PROBES = 4
live_cwds = [c for c in os.environ.get('OH_LIVE','').split() if c]
def _acttext(f):
    # command (terminal) AND path (file_editor): a model that reads with the file editor --
    # Kimi does, from 2026-09-11 -- names its worktree only in `path` (OH-CHGGRADE-BI read
    # "(no live process)" while alive until this was added).
    a = json.load(open(f)).get('action') or {}
    return ' '.join(str(a.get(k) or '') for k in ('command', 'path'))
recent = ' '.join(_acttext(f) for f in ev[-25:] if os.path.exists(f)) if live_cwds else ''
# A run whose last 25 commands never name its worktree (e.g. a stretch of `docker logs` /
# `sleep` while a build runs) was read "(no live process)" while alive (OH-TIERD2-BH,
# 2026-09-11). So it is also live if ANY command of the conversation names a live worktree
# AND the conversation wrote an event within 300 s. A finished conversation that once
# touched the same path goes quiet and reads dead again.
whole = ' '.join(_acttext(f) for f in ev if os.path.exists(f)) if live_cwds else ''
is_live = any(c in recent for c in live_cwds) or (idle < 300 and any(c in whole for c in live_cwds))
# A RUN THAT DIED ON THE MODEL LOOKS FINISHED. On 2026-09-12 23:41 OH-CIXGRADE-DQ stopped after 3 events on
# DeepSeek "Insufficient Balance" and read "(no live process)" like a completed run; the driver lost 9.5 hours
# before noticing. A ConversationErrorEvent in the tail is now named on its own line.
errdetail = ''
for f in ev[-5:]:
    try: o = json.load(open(f))
    except Exception: continue
    if o.get('kind') == 'ConversationErrorEvent':
        errdetail = ('%s: %s' % (o.get('code',''), o.get('detail',''))).replace('\n',' ')[:150]
if errdetail:
    flag = 'ERRORED'
elif not is_live:
    flag = '(no live process)'
elif idle >= SILENT_S:
    flag = 'STALLED-NOW(silent)'
elif trailing >= STALL_PROBES or (trailing >= 2 and idle >= STALL_IDLE_S):
    flag = 'STALLED-NOW'
elif trailing >= 2:
    flag = 'wedged(recovering?)'
else:
    flag = ''
note = '' if not recovered else '  (%d recovered -1)' % recovered
print('%-34s events=%-5s idle=%4ds  trailing-1=%d%s  %s' %
      (os.path.basename(d.rstrip('/'))[:32], n, idle, trailing, note, flag))
print('    last: %s' % (lastact or '(none)'))
if errdetail: print('    ERROR: %s' % errdetail)
PY
done

