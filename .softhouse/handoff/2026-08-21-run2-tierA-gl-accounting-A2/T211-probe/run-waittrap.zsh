#!/bin/zsh
# T211 -- the fg/bg x exit/return matrix for `wait`-vs-trap, through the
# launchd shape.  Each cell reports: handler latency, wrapper exit latency,
# and whether the child was orphaned.
set -uo pipefail
HERE="${0:A:h}"
mkdir -p /tmp/t211-scratch
export T211_CHILD_SECS=300
for SHAPE in fg bg; do
  for HMODE in exit return; do
    export T211_SHAPE=$SHAPE T211_HMODE=$HMODE
    LBL="waittrap-$SHAPE-$HMODE"
    export T211_CHILDPID=/tmp/t211-scratch/childpid-$LBL
    rm -f "$T211_CHILDPID"
    print -r -- "############ SHAPE=$SHAPE  HANDLER=$HMODE ############"
    /usr/bin/python3 "$HERE/spawn.py" "$HERE/waittrap.zsh" TERM "$LBL" READY 1.0 20
    if [[ -r "$T211_CHILDPID" ]]; then
      CP=$(<"$T211_CHILDPID")
      if kill -0 "$CP" 2>/dev/null; then
        print -r -- "POST-MORTEM: child $CP ORPHANED (still running after the wrapper was reaped)"
        ps -o pid,ppid,pgid,comm -p "$CP" 2>/dev/null | /usr/bin/sed -n '2p' | /usr/bin/sed 's/^/   /'
        kill -9 "$CP" 2>/dev/null
      else
        print -r -- "POST-MORTEM: child $CP is gone"
      fi
    fi
    print -r -- ""
  done
done
print -r -- "MATRIX DONE"
