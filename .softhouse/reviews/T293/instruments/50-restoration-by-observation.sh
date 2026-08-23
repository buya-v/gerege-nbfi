#!/usr/bin/env bash
# T293 test 5 -- DOES probe_tmp_dependency_t271.sh RESTORE THE STATE IT FOUND?
#
# The brief says: verify this BY OBSERVATION, NOT BY READING ITS SOURCE. So nothing below
# reads the probe. Each arm sets a known state, runs the probe, and reads the state back.
# Five arms: found-ABSENT, found-PRESENT, and three ABNORMAL exits (TERM, INT, KILL) landed
# mid-run, when the probe has the state INVERTED from how it found it.
#
# NOT `mktemp` -- THIS instrument's subject IS the one absolute path, same as the probe's.
# Its own scratch under $D is mktemp'd; the SUBJECT path cannot be, and that is the point.
set -uo pipefail

T=/tmp/t234_matrix2.txt
PROBE=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a05619873f54c8f39/.softhouse/capture/t271-b1-t219/probe_tmp_dependency_t271.sh
D="$(mktemp -d "${TMPDIR:-/tmp}/t293-restore.XXXXXXXXXX")" || exit 2
trap 'rm -rf "$D"' EXIT

state() { if [ -e "$T" ]; then echo PRESENT; else echo ABSENT; fi; }
FOUND_AT_START="$(state)"
echo "T293/50 -- restoration by observation.  host state at start: $FOUND_AT_START"
echo "subject path: $T"
echo "probe       : $PROBE"
echo ""

fails=0

# --- ARM 1: probe finds the file ABSENT ------------------------------------
rm -f "$T"
before="$(state)"
bash "$PROBE" >"$D/a1.out" 2>&1; rc=$?
after="$(state)"
echo "ARM 1 found=$before  probe exit=$rc  after=$after"
if [ "$before" != "$after" ]; then echo "  ARM 1 FAIL: state not restored"; fails=$((fails+1));
else echo "  ARM 1 OK: restored"; fi
grep -o 'T271-TMPDEP:.*' "$D/a1.out" || echo "  (no T271-TMPDEP line)"
grep -o 'T271-RESTORE:.*' "$D/a1.out" || { echo "  ARM: NO T271-RESTORE LINE"; fails=$((fails+1)); }
echo ""

# --- ARM 2: probe finds the file PRESENT -----------------------------------
printf 'x1y\nxdy\nx y\nxsy\nx_y\nxwy\n' > "$T"
before="$(state)"
bash "$PROBE" >"$D/a2.out" 2>&1; rc=$?
after="$(state)"
echo "ARM 2 found=$before  probe exit=$rc  after=$after"
if [ "$before" != "$after" ]; then echo "  ARM 2 FAIL: state not restored"; fails=$((fails+1));
else echo "  ARM 2 OK: restored"; fi
grep -o 'T271-TMPDEP:.*' "$D/a2.out" || echo "  (no T271-TMPDEP line)"
grep -o 'T271-RESTORE:.*' "$D/a2.out" || { echo "  ARM: NO T271-RESTORE LINE"; fails=$((fails+1)); }
echo ""

# --- ARMS 3-5: ABNORMAL EXIT, landed mid-run -------------------------------
# The probe deletes the path, reads, CREATES it, reads, deletes it, reads. A signal that
# lands in the middle catches the state INVERTED, which is the only interesting moment.
abnormal() {
  local sig="$1" delay="$2" before after rc
  rm -f "$T"                       # found ABSENT, so an unrestored exit shows as PRESENT
  before="$(state)"
  bash "$PROBE" >"$D/$sig.out" 2>&1 &
  local pid=$!
  sleep "$delay"
  local mid; mid="$(state)"
  kill -"$sig" "$pid" 2>/dev/null
  wait "$pid" 2>/dev/null; rc=$?
  sleep 0.3
  after="$(state)"
  echo "ARM $sig  found=$before  state when signalled=$mid  exit=$rc  after=$after"
  # A VACUOUS PASS IS NOT A PASS. The linter's runtime drifts run to run, so the signal can
  # land BEFORE the probe has inverted the state -- and then "restored" is true of an arm that
  # never tested anything. The first cut of this instrument reported exactly that as OK for
  # SIGKILL. So the WINDOW IS CHECKED FIRST and a miss is INCONCLUSIVE, counted as a failure
  # of the measurement rather than a success of the subject. (P-91's corollary: a rig that can
  # pass while skipping is a rig whose counts mean nothing.)
  if [ "$mid" = "$before" ]; then
    echo "  ARM $sig INCONCLUSIVE: the signal landed OUTSIDE the inverted window (state was"
    echo "    still $mid). This arm measured NOTHING and is NOT counted as restored. Re-run,"
    echo "    or widen the delay: the window is READING B, roughly t=6.5s..t=13s here."
    fails=$((fails+1))
    return
  fi
  if [ "$before" != "$after" ]; then
    echo "  ARM $sig FAIL: the probe left the host DIFFERENT from how it found it"
    fails=$((fails+1))
  else
    echo "  ARM $sig OK: restored, and the signal DID land while the state was inverted"
  fi
}
abnormal TERM 9
echo ""
abnormal INT  9
echo ""
abnormal KILL 9
echo ""

# --- put the host back the way THIS instrument found it --------------------
if [ "$FOUND_AT_START" = PRESENT ]; then
  printf 'x1y\nxdy\nx y\nxsy\nx_y\nxwy\n' > "$T"
else
  rm -f "$T"
fi
echo "host state restored to: $(state) (found $FOUND_AT_START)"
echo ""
echo "T293-RESTORE: arms=5 failures=$fails"
[ "$fails" -eq 0 ] && exit 0
exit 1
