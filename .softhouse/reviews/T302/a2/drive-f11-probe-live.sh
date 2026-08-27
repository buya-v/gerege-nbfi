#!/bin/bash
# T302 attempt 2 -- F11: re-drive T302 attempt 1's F3b on TODAY's process table.
#
# foreign_live_session_in_repo() returns 0 (REFUSE) if ANY live `claude` has a cwd
# inside the repo. T309 added a skip list, but it holds ONLY the pids stop_driver just
# signalled (this fire's DRIVER_TREE). Anything else in-repo still forces a refusal.
#
# T309's fail-direction table leans on the claim that in_session mode's non-destructive
# error is fine "because that lie has a second reader: the wrapper's own exit path, in
# wrapper mode, clears whatever is left". That reader only fires when this probe
# returns 1. So: does it?
#
# READ-ONLY. `ps` and `lsof` only. No signal is sent to any process. The real
# .softhouse/LOCK is not touched.
set -u
REPO=/Users/buv/gerege-nbfi
LSOF=/usr/sbin/lsof
[ -x "$LSOF" ] || LSOF=$(command -v lsof)

echo "repo (physical): $REPO"
echo "lsof: $LSOF"
echo
printf '%-8s %-6s %-9s %s\n' PID STAT IN-REPO CWD
found=0; checked=0
while read -r pid st first _rest; do
  case "${first##*/}" in claude) ;; *) continue ;; esac
  case "$st" in Z*) continue ;; esac
  kill -0 "$pid" 2>/dev/null || continue
  checked=$((checked+1))
  cwd=$("$LSOF" -w -a -d cwd -p "$pid" -Fn 2>/dev/null | sed -n 's/^n//p' | tail -1)
  case "$cwd" in
    "$REPO"|"$REPO"/*) inrepo=YES; found=$((found+1)) ;;
    "") inrepo=UNREADABLE ;;
    *) inrepo=no ;;
  esac
  printf '%-8s %-6s %-9s %s\n' "$pid" "$st" "$inrepo" "${cwd:-?}"
done < <(/bin/ps -Ao pid=,stat=,command=)
echo
echo "claude processes examined=$checked in-repo=$found"
if [ "$found" -gt 0 ]; then
  echo "VERDICT: foreign_live_session_in_repo() would return 0 -> the wrapper REFUSES to"
  echo "         reconcile. The 'second reader' T309's fail-direction table relies on"
  echo "         does not fire while any of the above is alive."
else
  echo "VERDICT: would return 1 -> the wrapper may reconcile."
fi
echo
echo "NOTE ON THE SKIP LIST: STOPPED_TREE holds only the pids stop_driver signalled"
echo "(this fire's DRIVER_TREE). Any OTHER in-repo claude above is still counted."
