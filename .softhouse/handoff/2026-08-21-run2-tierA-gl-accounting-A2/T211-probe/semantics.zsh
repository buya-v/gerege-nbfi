#!/bin/zsh
# T211 -- the zsh-5.9 semantics the fix has to be built on, MEASURED, not assumed.
# Run through the launchd shape (`/bin/zsh -lc <this>`), stdout a FILE, no tty.
#
# T202's brief says "background the child and wait" -- but `wait` alone answers
# only the first of five questions the rewrite actually raises:
#   S2  does a trap run promptly while the shell sits in `wait`?
#   S3  does `wait` RESUME after a handler that does not exit (EINTR restart)?
#   S4  what is `$!` for a background PIPELINE -- which member's pid?
#   S5  does `pipestatus` survive `wait`?  (RC=${pipestatus[1]} depends on it)
#   S6  are a background child's INT/QUIT SIG_IGN'd?  (the P-55 mechanism --
#       backgrounding is exactly what created T202's false "zsh ignores SIGINT")
#   S7  does killing the pid zsh hands back actually kill `claude` under
#       /usr/bin/caffeinate, or does caffeinate shield it?
set -uo pipefail
now() { date +%s.%N }
say() { print -r -- "[$(now)] $*" }

print -r -- "zsh: $(/bin/zsh --version)"
print -r -- "options: MONITOR=$([[ -o monitor ]] && print on || print off)  INTERACTIVE=$([[ -o interactive ]] && print on || print off)"
print -r -- "stdout is a tty? $([[ -t 1 ]] && print yes || print no)   (launchd: no)"
print -r -- ""

# ---------------------------------------------------------------- S4 + S5 ----
print -r -- "=== S4/S5  \$! and \$pipestatus for a background pipeline ==="
SELF=$$
/bin/sleep 3 | /usr/bin/cat | /bin/cat &
BGP=$!
print -r -- "shell pid          = $SELF"
print -r -- "\$! for 'a | b | c &' = $BGP"
ps -o pid,ppid,pgid,command -p $BGP 2>/dev/null | /usr/bin/sed -n '2p' \
  | /usr/bin/sed 's/^/   which process that is: /'
print -r -- "   -> children of this shell right now:"
pgrep -P $SELF | while read -r c; do
  ps -o pid,ppid,pgid,command -p "$c" 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/      /'
done
wait $BGP
WRC=$?
print -r -- "wait \$! rc          = $WRC"
print -r -- "\$pipestatus AFTER wait = (${pipestatus[*]})   <-- if this is not the 3 members, RC=\${pipestatus[1]} is DEAD after the rewrite"
print -r -- ""

# subshell-wrapped pipeline: is $! then unambiguous?
( /bin/sleep 2 | /usr/bin/cat ) &
BGS=$!
print -r -- "\$! for '( a | b ) &'  = $BGS"
ps -o pid,ppid,pgid,command -p $BGS 2>/dev/null | /usr/bin/sed -n '2p' \
  | /usr/bin/sed 's/^/   which process that is: /'
print -r -- "   pgid of that job vs shell pgid $(ps -o pgid= -p $SELF | tr -d ' ')"
wait $BGS
print -r -- ""

# ------------------------------------------------------------------- S6 ------
print -r -- "=== S6  dispositions of a BACKGROUND child in a non-monitor shell ==="
print -r -- "(this is P-55's actual mechanism: POSIX says an async child of a"
print -r -- " shell without job control gets SIGINT/SIGQUIT set to SIG_IGN)"
/bin/sleep 4 &
BGC=$!
sleep 0.4
# SigIgn mask, from the kernel, for the background child
/bin/ps -o pid,command -p $BGC >/dev/null 2>&1
print -r -- "background child pid = $BGC"
IGN=$(/usr/bin/python3 - "$BGC" <<'PY'
import subprocess, sys
pid = sys.argv[1]
# macOS: `ps -o sig,sigmask` is not portable; use proc_info via lsof-free route
try:
    out = subprocess.run(["/bin/ps", "-o", "pid=,stat=", "-p", pid],
                         capture_output=True, text=True).stdout.strip()
    print("ps stat: " + out)
except Exception as e:
    print("could not read: %r" % e)
PY
)
print -r -- "$IGN"
print -r -- "-- empirical test instead of reading a mask: send SIGINT to it and see if it dies"
kill -INT $BGC 2>/dev/null
sleep 0.6
if kill -0 $BGC 2>/dev/null; then
  print -r -- "   SIGINT did NOT kill the background child -> INT is SIG_IGN in it (POSIX async rule CONFIRMED)"
  print -r -- "   => a handler that merely forwards SIGINT to \`claude\` would be a NO-OP"
  kill -TERM $BGC 2>/dev/null; sleep 0.4
  kill -0 $BGC 2>/dev/null && print -r -- "   SIGTERM did not kill it either" \
                           || print -r -- "   SIGTERM DID kill it -> TERM is the signal the handler must forward"
else
  print -r -- "   SIGINT killed the background child -> INT is NOT ignored here"
fi
wait 2>/dev/null
print -r -- ""

# ------------------------------------------------------------------- S5b -----
print -r -- "=== S5b  same child, but with MONITOR (job control) turned on ==="
setopt localoptions 2>/dev/null
if setopt monitor 2>/tmp/t211-scratch/monitor-err.txt; then
  print -r -- "setopt monitor        = ACCEPTED (stderr: $(cat /tmp/t211-scratch/monitor-err.txt 2>/dev/null | tr '\n' ' '))"
  print -r -- "MONITOR now           = $([[ -o monitor ]] && print on || print off)"
  /bin/sleep 4 &
  MC=$!
  sleep 0.4
  MPG=$(ps -o pgid= -p $MC 2>/dev/null | tr -d ' ')
  print -r -- "bg child pid=$MC pgid=$MPG   shell pgid=$(ps -o pgid= -p $SELF | tr -d ' ')"
  if [[ -n "$MPG" && "$MPG" != "$(ps -o pgid= -p $SELF | tr -d ' ')" ]]; then
    print -r -- "   -> job got its OWN process group: 'kill -TERM -$MPG' reaches the whole job"
  else
    print -r -- "   -> job shares the SHELL's process group: a negative-pgid kill would kill the shell too"
  fi
  kill -INT $MC 2>/dev/null; sleep 0.5
  kill -0 $MC 2>/dev/null && print -r -- "   SIGINT still ignored under monitor" \
                          || print -r -- "   SIGINT KILLS it under monitor -> monitor also removes the SIG_IGN"
  kill -9 $MC 2>/dev/null
  unsetopt monitor
else
  print -r -- "setopt monitor        = REFUSED: $(cat /tmp/t211-scratch/monitor-err.txt 2>/dev/null)"
fi
print -r -- ""

# ------------------------------------------------------------------- S7 ------
print -r -- "=== S7  /usr/bin/caffeinate: does the pid zsh hands back BECOME the utility? ==="
/usr/bin/caffeinate -i -m -s /bin/sleep 30 &
CAF=$!
sleep 0.8
print -r -- "\$! from 'caffeinate ... sleep 30 &' = $CAF"
ps -o pid,ppid,pgid,comm -p $CAF 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/   /'
print -r -- "   its children:"
pgrep -P $CAF 2>/dev/null | while read -r c; do
  ps -o pid,ppid,comm -p "$c" 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/      /'
done
print -r -- "-- now TERM that one pid and see whether the UTILITY dies with it"
KIDS=($(pgrep -P $CAF 2>/dev/null))
kill -TERM $CAF 2>/dev/null
sleep 1.0
kill -0 $CAF 2>/dev/null && print -r -- "   pid $CAF survived TERM" || print -r -- "   pid $CAF is gone"
for c in $KIDS; do
  kill -0 "$c" 2>/dev/null \
    && { print -r -- "   child $c SURVIVED -- caffeinate shields it; a single kill is NOT enough"; kill -9 "$c" 2>/dev/null } \
    || print -r -- "   child $c is gone too"
done
pgrep -f 'caffeinate -i -m -s /bin/sleep' >/dev/null 2>&1 \
  && { print -r -- "   a stray caffeinate remains"; pkill -f 'caffeinate -i -m -s /bin/sleep' } \
  || print -r -- "   no stray caffeinate remains"
wait 2>/dev/null
print -r -- ""
print -r -- "SEMANTICS DONE"
