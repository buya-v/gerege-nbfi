#!/bin/zsh
# T361 — do to T353's self-test what T346 did to the 192-state driver: MUTATE the thing it
# grades and see whether it moves. T353 reports three reader mutations caught; the brief says
# do not accept that claim. These mutations are chosen by the reviewer and are NOT T353's
# M07b/M08b/M09b — the point is to find the self-test's BLIND SPOT, not to reproduce its hits.
#
# For each mutation the driver reports BOTH graders:
#   192  = `drive-wrapper-vs-skill.zsh`-equivalent: does mutating this move `lock_decide`?
#          (it cannot — the driver SUPPLIES the signals — so this column exists to show that
#          the self-test is the only grader in play.)
#   ST   = `--self-test-lock-readers` exit code and counts.
#
# Every mutation is `cmp`-checked against the pristine copy: a mutation that did not apply is
# reported VOID, never as a pass (P-22 — a control that cannot fail is worse than none).
emulate -L zsh
set -uo pipefail

SRC="${1:?usage: t361-mutate-readers.zsh <path to fire-program.sh>}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t361-mut.XXXXXX")" || { print -u2 "ABORT: mktemp failed"; exit 3; }
[[ -n "$WORK" && "$WORK" != "/" ]] || { print -u2 "ABORT: refusing to work in '$WORK'"; exit 3; }
trap 'rm -rf "$WORK"' EXIT
cp "$SRC" "$WORK/pristine.sh"

print -r -- "T361 mutation drive of --self-test-lock-readers"
print -r -- "source=$SRC sha256=$(shasum -a 256 "$SRC" | awk '{print $1}')"
print -r -- ""

typeset -i NCHK=0 NWRONG=0
mutate() {  # $1 id  $2 expect (CAUGHT|BLIND)  $3 description  $4.. sed program(s)
  local id="$1" expect="$2" desc="$3"; shift 3
  local f="$WORK/m-$id.sh"
  cp "$WORK/pristine.sh" "$f"
  local prog
  for prog in "$@"; do /usr/bin/sed -i '' -e "$prog" "$f"; done
  if cmp -s "$WORK/pristine.sh" "$f"; then
    printf '%-5s %-9s %-58s %s\n' "$id" "VOID" "$desc" "the sed did not change the file — NOT a pass"
    NCHK+=1; NWRONG+=1; return
  fi
  if ! zsh -n "$f" 2>/dev/null; then
    printf '%-5s %-9s %-58s %s\n' "$id" "VOID" "$desc" "mutant does not parse — NOT a pass"
    NCHK+=1; NWRONG+=1; return
  fi
  local out rc
  out="$(zsh "$f" --self-test-lock-readers 2>&1)"; rc=$?
  local counts="${out##*$'\n'}"
  local got
  (( rc != 0 )) && got=CAUGHT || got=BLIND
  NCHK+=1
  local mark=ok
  [[ "$got" == "$expect" ]] || { mark='*** UNEXPECTED'; NWRONG+=1; }
  printf '%-5s %-9s %-58s rc=%d %s   [%s]\n' "$id" "$got" "$desc" $rc "$mark" "$counts"
}

print -r -- "--- control"
mutate c00 BLIND "CONTROL: comment-only edit, self-test MUST stay green" \
  's|^# T279 — `lock_pid_state` is the four-way form|# T361 CONTROL COMMENT — `lock_pid_state` is the four-way form|'

print -r -- ""
print -r -- "--- mutations the self-test SHOULD catch (fail-OPEN direction, P-85 safety)"
mutate n01 CAUGHT "lock_released_at: drop the _iso8601_epoch shape gate" \
  's|^  _iso8601_epoch "\$v" >/dev/null \|\| return 0$|  : # T361 n01 shape gate removed|'
mutate n02 CAUGHT "python reader: accept DUPLICATE keys (drop object_pairs_hook)" \
  's|json.load(fh, object_pairs_hook=no_dupes)|json.load(fh)|'
# n03/n04 were EXPECTED to be caught and are not. Measured, then explained rather than
# rescored: both are masked by a SECOND, downstream check, so neither mutation actually
# produces a fail-open. n03 makes the python raise a TypeError outside the `try`, which the
# caller reads as "unreadable" -> HELD; n04 lets `True` through python and `[[ "$pid" == <1-> ]]`
# in `lock_pid_state` then rejects the string "True" -> absent -> HELD. That is defence in
# depth working, not a hole — but it also means the self-test cannot distinguish "the python
# check is present" from "the zsh check is catching it", and the expectation is corrected here
# rather than in the score.
mutate n03 BLIND "python reader: drop the released_at str/ctrl check (MASKED downstream)" \
  's|if not isinstance(v, str) or any(ord(c) < 0x20 for c in v):|if False:|'
mutate n04 BLIND "python reader: accept a BOOL as pid (MASKED by <1-> in lock_pid_state)" \
  's|if not isinstance(v, int) or isinstance(v, bool):|if not isinstance(v, int):|'
mutate n05 CAUGHT "lock_started_age: negate the age (now-e -> e-now)" \
  's|  print -r -- \$(( now - e ))|  print -r -- $(( e - now ))|'
# n06 measured BLIND, expectation corrected here rather than in the score: no self-test row
# puts an IMPOSSIBLE DATE in `released_at`, so the day-of-month bound is ungraded by the wired
# control. In production that is the OPEN direction — `"released_at": "2026-02-30T00:00:00Z"`
# would read as a release. (T361's own reader corpus row x15 covers it; the SHIPPED control
# does not.) Moved to the BLIND block below in spirit; kept here to preserve the reading order.
mutate n06 BLIND "_iso8601_epoch: drop the day-of-month upper bound (BLIND, see note)" \
  's@  (( d >= 1 && d <= maxd )) || return 1@  (( d >= 1 )) || return 1@'
mutate n12 CAUGHT "_iso8601_epoch: shift the epoch by MINUS one whole day" \
  's@  print -r -- $(( days \* 86400 + hh \* 3600 + mi \* 60 + ss ))@  print -r -- $(( (days - 1) * 86400 + hh * 3600 + mi * 60 + ss ))@'

print -r -- ""
print -r -- "--- mutations I EXPECT the self-test to be BLIND to. Each is a real fail-OPEN or"
print -r -- "    fail-SHUT in production; BLIND here means the new control does not cover it."
mutate n07 BLIND "lock_pid_state: DELETE the host check -> judges ANOTHER machine's pid" \
  's|^  \[\[ "\$host" == "\$(hostname -s)" \]\] .*$|  : # T361 n07 host check deleted|'
mutate n08 BLIND "_iso8601_epoch: century leap rule -> plain %4 (2100-02-29 accepted)" \
  's|(( (y % 4 == 0 \&\& y % 100 != 0) \|\| y % 400 == 0 )) \&\& leap=1|(( y % 4 == 0 )) \&\& leap=1|'
mutate n09 BLIND "lock_started_age: delete the <1-> guard -> a NEGATIVE epoch passes" \
  's@  \[\[ "$e" == <1-> \]\] || return 0@  : # T361 n09 epoch sanity guard deleted@'
mutate n10 BLIND "python reader: drop the CONTROL-CHARACTER rejection only" \
  's|or any(ord(c) < 0x20 for c in v)||'
mutate n11 BLIND "_iso8601_epoch: shift the epoch by one whole DAY" \
  's|  print -r -- \$(( days \* 86400 + hh \* 3600 + mi \* 60 + ss ))|  print -r -- $(( (days + 1) * 86400 + hh * 3600 + mi * 60 + ss ))|'

print -r -- ""
print -r -- "CHECKS=$NCHK UNEXPECTED=$NWRONG"
print -r -- ""
print -r -- "READ THIS AS: 'BLIND' rows are the self-test's coverage boundary. n07 is the one that"
print -r -- "matters — deleting the host check makes the wrapper judge a LIVE process on ANOTHER"
print -r -- "machine, which is a FAIL-OPEN, and NEITHER grader sees it."
(( NWRONG == 0 )) || exit 1
exit 0
