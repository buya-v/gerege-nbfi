#!/bin/zsh
# T211 -- drive ONE (fire-program.sh, signal) pair end to end and report the
# four things that decide whether a fire can be stopped:
#
#   1. EXIT LATENCY   signal -> wrapper exit          (the defect is a latency)
#   2. TRAP RAN?      did on_signal print at all
#   3. LOCK           released, or STRANDED on disk
#   4. ORPHAN         is the `claude` stand-in still alive after the wrapper
#                     exited -- because a wrapper that exits promptly and leaves
#                     the driver running is not a fix, it is a worse strand.
#
# usage: run-case.zsh <fire-program.sh> <SIGNAL> <label>
set -uo pipefail
HERE="${0:A:h}"
SRC=$1; SIG=$2; LABEL=$3

export T211_REPO=/tmp/t211-scratch/repo
export T211_LOGDIR=/tmp/t211-scratch/logs
export T211_CHILDPID=/tmp/t211-scratch/childpid-$LABEL
export T211_FRAG=/tmp/t211-scratch/frag-$LABEL
export T211_CHILD_SECS=300

rm -rf "$T211_FRAG"; mkdir -p "$T211_FRAG"
rm -f "$T211_CHILDPID"

print -r -- "############################################################"
print -r -- "# CASE $LABEL   signal=SIG$SIG"
print -r -- "# subject bytes: $SRC"
print -r -- "# zsh: $(/bin/zsh --version)"
print -r -- "############################################################"
/usr/bin/python3 "$HERE/extract.py" "$SRC" "$T211_FRAG" || exit 1
print -r -- ""
/bin/zsh "$HERE/setup-scratch.zsh" || exit 1
print -r -- ""
if [[ "$SIG" == none ]]; then
  # control run: no signal at all, so give the subject room to finish normally
  /usr/bin/python3 "$HERE/spawn.py" "$HERE/subject.zsh" none "$LABEL" READY 0 40
else
  /usr/bin/python3 "$HERE/spawn.py" "$HERE/subject.zsh" "$SIG" "$LABEL" READY 1.5 45
fi
print -r -- ""
print -r -- "=== post-mortem (measured after the wrapper process was reaped) ==="
# What SURVIVED, not an exit code (P-62): read the lines the wrapper actually
# printed. Zero external programs -- zsh's own ${(f)} split, so there is no
# grep binary/locale/byte-class question inside the probe's own verdict (P-58).
if [[ -r "$HERE/out-$LABEL.txt" ]]; then
  BODY=$(<"$HERE/out-$LABEL.txt")
  SAW_RC=0; SAW_STOP=0; SAW_BODY=0
  for L in ${(f)BODY}; do
    [[ "$L" == *"driver exited rc="*      ]] && { print -r -- "OBSERVED  $L"; SAW_RC=1 }
    [[ "$L" == *"stopping the driver:"*   ]] && SAW_STOP=1
    [[ "$L" == *"BODY COMPLETED NORMALLY"* ]] && SAW_BODY=1
  done
  (( SAW_RC ))   || print -r -- "OBSERVED  no 'driver exited rc=' line was ever printed"
  (( SAW_STOP )) && print -r -- "OBSERVED  the handler enumerated and stopped the driver tree"
  (( SAW_BODY )) && print -r -- "OBSERVED  the wrapper body ran to completion (control run)"
else
  print -r -- "OBSERVED  no transcript at $HERE/out-$LABEL.txt"
fi
if [[ -f "$T211_REPO/.softhouse/LOCK" ]]; then
  print -r -- "LOCK        = PRESENT-STRANDED   <-- the next fire parks behind it for up to 6h"
else
  print -r -- "LOCK        = released"
fi
if [[ -r "$T211_CHILDPID" ]]; then
  CPID=$(<"$T211_CHILDPID")
  if kill -0 "$CPID" 2>/dev/null; then
    print -r -- "DRIVER CHILD= ORPHANED, pid $CPID STILL RUNNING   <-- unlocked driver still alive"
    ps -o pid,ppid,pgid,command -p "$CPID" 2>/dev/null | /usr/bin/sed -n '2p'
    kill -9 "$CPID" 2>/dev/null
    print -r -- "              (harness killed it so it cannot pollute the next case)"
  else
    print -r -- "DRIVER CHILD= reaped, pid $CPID is gone"
  fi
else
  print -r -- "DRIVER CHILD= never recorded a pid"
fi
# sweep any caffeinate the case left behind
pkill -f 'caffeinate .*fake-claude' 2>/dev/null && print -r -- "(swept a leftover caffeinate)"
print -r -- ""
