#!/bin/zsh
# T365 — DRIVE EVERY CONDITION RED BEFORE BELIEVING IT GREEN.
#
# P-22: *"a guard, a canary, or a control that cannot fail is worse than none — because it is
# believed"* [`.softhouse/patterns.md:473`]. A self-test that goes green after a fix proves
# nothing until you have seen it go RED when the fix is removed. So every condition T365
# applied is REVERTED on a throwaway copy of the shipped file, one at a time, and the wired
# control — `--self-test-lock-readers` — must catch it and name the right direction.
#
#   FAIL-OPEN = a lock held by a LIVE process on this host reads as takeable. P-85,
#               *"two orchestrators held the lock at once, and the cause was an unpushed
#               in-flight state"* [`.softhouse/patterns.md:2822`]. The direction that destroys work.
#   FAIL-SHUT = a reclaimable lock is not reclaimed, or the fire refuses to start. Liveness.
#
# Every mutation is `cmp`-checked and reports VOID if it did not apply — a mutation that
# silently misses turns this driver into the thing P-22 warns about.
#
# usage: t365-red-drives.zsh <path to fire-program.sh>
emulate -L zsh
set -uo pipefail

SRC="${1:?usage: t365-red-drives.zsh <fire-program.sh>}"
SRC="${SRC:A}"
W="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/t365-red.XXXXXX")" || exit 3
[[ -n "$W" && -d "$W" && "$W" != "/" ]] || exit 3
trap 'rm -rf "$W"' EXIT

print -r -- "T365 red drives"
print -r -- "source=$SRC"
print -r -- "sha256=$(shasum -a 256 "$SRC" | awk '{print $1}')"
print -r -- ""

typeset -i CHECKS=0 WRONG=0

# mutate <label> <sed program> -> writes $W/m.sh, aborts if the program changed nothing
mutate() {
  local label="$1"; shift
  cp "$SRC" "$W/m.sh"
  local p; for p in "$@"; do /usr/bin/sed -i '' -e "$p" "$W/m.sh"; done
  if cmp -s "$SRC" "$W/m.sh"; then
    print -r -- "*** VOID: mutation '$label' did not change the file — this driver would have lied"
    exit 3
  fi
}

# check <id> <want rc: 0|nonzero> <want-marker or -> <label>
#   runs the self-test on $W/m.sh and grades rc and (optionally) that a given row id is red
check() {
  local id="$1" wantrc="$2" marker="$3" label="$4" rc out summary
  out="$(/bin/zsh "$W/m.sh" --self-test-lock-readers 2>&1)"; rc=$?
  CHECKS+=1
  local ok=1
  # P-83 — READ THE PROBE LINE'S PRESENCE BEFORE ITS VALUE. A mutation that makes the
  # self-test CRASH also exits non-zero, so a bare `rc != 0` assertion would score it GREEN
  # and this driver would be certifying "the guard caught it" when the guard never ran. The
  # summary line must EXIST, and it must report at least the 27 rows this file shipped with
  # before T365, before its numbers are read at all.
  summary="$(print -r -- "$out" | grep -E '^ROWS=' )" || { summary='<NO SUMMARY LINE — the self-test did not reach its own tally>'; ok=0; }
  if [[ "$summary" == ROWS=* ]]; then
    local -i nrows="${${summary#ROWS=}%% *}"
    (( nrows >= 27 )) || { summary="$summary  <FEWER THAN 27 ROWS>"; ok=0; }
  fi
  if [[ "$wantrc" == 0 ]]; then (( rc == 0 )) || ok=0; else (( rc != 0 )) || ok=0; fi
  local mark_ok=""
  if [[ "$marker" != "-" ]]; then
    if print -r -- "$out" | grep -qE "^${marker}"; then mark_ok="yes"; else mark_ok="NO"; ok=0; fi
  fi
  (( ok )) || WRONG+=1
  printf '%-5s %-7s rc=%-3d %-46s %s\n' "$id" "$( (( ok )) && print -- GREEN || print -- '*** WRONG')" "$rc" "$summary" "$label"
  [[ "$marker" == "-" ]] || printf '        expected row pattern /^%s/ present: %s\n' "$marker" "$mark_ok"
  # keep the failing rows visible, so this transcript shows WHAT went red, not just that it did
  print -r -- "$out" | grep -E '\*\*\* FAIL' | sed 's/^/        /'
}

# ---------------------------------------------------------------- control, first
print -r -- "=== r00 CONTROL — the shipped file, unmutated. If this is not GREEN nothing below means anything."
cp "$SRC" "$W/m.sh"
check r00 0 - "shipped file, no mutation"

print -r -- ""
print -r -- "=== C1 (F-T361-1, direction OPEN) — reject implausible instants in released_at"
mutate "C1 lower bound" 's@^  (( _e > 0 )) || return 0$@  : # T365 red drive: C1 lower bound reverted@'
check r01 nonzero 'z01  \*\*\* FAIL-OPEN' "revert the >0 bound: Go zero / year zero / epoch free a LIVE lock"

mutate "C1 skew bound" 's@^  (( _e <= _now + LOCK_RELEASE_SKEW_SECS )) || return 0$@  : # T365 red drive: C1 skew bound reverted@'
check r02 nonzero 'z04  \*\*\* FAIL-OPEN' "revert the future bound: datetime.max / far-future sentinels free a LIVE lock"

mutate "C1 whole predicate" \
  's@^  (( _e > 0 )) || return 0$@  : # reverted@' \
  's@^  (( _e <= _now + LOCK_RELEASE_SKEW_SECS )) || return 0$@  : # reverted@'
check r03 nonzero 'z01  \*\*\* FAIL-OPEN' "revert C1 entirely: this is exactly T353's shipped behaviour, and it is 6 fail-open rows"

print -r -- ""
print -r -- "=== C4 (F-T361-4, direction OPEN-coverage) — the host guard, the literal P-85 line"
mutate "C4 host guard" 's@^  \[\[ "$host" == "$(hostname -s)" \]\].*$@  : # T365 red drive: host guard deleted@'
check r04 nonzero 'e01  \*\*\* FAIL-OPEN' "delete the host guard: this local fire now judges ANOTHER machine's pid dead and takes its lock"

print -r -- ""
print -r -- "=== C5 (F-T361-5, direction OPEN) — the parser's arithmetic, previously graded by nothing wired"
# THE SIGN MATTERS AND THE FIRST VERSION OF THIS DRIVER GOT IT BACKWARDS — recorded rather
# than quietly corrected, because it is the reason g01 is worded the way it is. An epoch that
# reads HIGH makes the instant LATER, so `now - e` reads SMALLER and arm 3 does NOT fire; the
# direction that fires arm 3 against a live holder is an epoch that reads LOW. So both signs
# are driven, and they are caught by DIFFERENT rows — which is the whole argument for group H.
mutate "epoch one day LOW" 's@^  print -r -- \$(( days \* 86400 + hh \* 3600 + mi \* 60 + ss ))$@  print -r -- $(( (days - 1) * 86400 + hh * 3600 + mi * 60 + ss ))@'
check r05 nonzero 'g01  \*\*\* FAIL-OPEN' "epoch one day LOW: a lock INSIDE the ceiling reads past it and arm 3 takes a LIVE holder's lock"

mutate "epoch one day HIGH" 's@^  print -r -- \$(( days \* 86400 + hh \* 3600 + mi \* 60 + ss ))$@  print -r -- $(( (days + 1) * 86400 + hh * 3600 + mi * 60 + ss ))@'
check r05b nonzero 'h01  \*\*\* FAIL-OPEN' "epoch one day HIGH: g01 is BLIND to this sign (ages read smaller, so arm 3 stays quiet) -- group H's exact constants are what catch it"

# `&` is the whole match in a sed replacement, so `&&` MUST be escaped. The first version of
# this driver did not escape it, the mutation landed as garbage, and the check failed for the
# wrong reason. Left as a comment because a silent mutation is exactly what `mutate`'s VOID
# check exists to stop — and VOID could not see this one, since the file DID change.
mutate "day-of-month bound" 's@^  (( d >= 1 && d <= maxd )) || return 1$@  (( d >= 1 \&\& d <= 31 )) || return 1@'
check r06 nonzero 'g02  \*\*\* FAIL-OPEN' "drop the day bound: 2026-02-30 becomes a valid past instant and frees a LIVE lock"

mutate "century non-leap rule" 's@^  (( (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 )) && leap=1$@  (( y % 4 == 0 )) \&\& leap=1@'
check r07 nonzero 'h04  \*\*\* FAIL-OPEN' "break the century rule: ONLY group H sees this — see r07b for why the body route cannot"

mutate "negative-epoch guard" 's@^  \[\[ "$e" == <1-> \]\] || return 0$@  : # T365 red drive: negative-epoch guard deleted@'
check r08 nonzero 'g03  \*\*\* FAIL-OPEN' "delete the negative-epoch guard: a pre-epoch started_at reads a ~57-year age and fires the ceiling"

print -r -- ""
print -r -- "=== r07b — THE FINDING THIS TASK MADE WHILE PROVING C5."
print -r -- "T361 proposed grading the century rule with a BODY row: released_at = 2100-02-29T00:00:00Z."
print -r -- "Under C1 that row is BLIND, because if the century rule breaks the date decodes to 2100-03-01,"
print -r -- "which C1 then refuses as far-future — so the body still reads HELD and the mutation is invisible."
print -r -- "Driven below on the SAME mutated file that r07 caught: the body route says HELD, group H says FAIL."
mutate "century non-leap rule" 's@^  (( (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 )) && leap=1$@  (( y % 4 == 0 )) \&\& leap=1@'
{
  sed -n '/^lock_decide() {/,/^}/p'         "$W/m.sh"
  sed -n '/^_lock_json_fields() {/,/^}$/p'  "$W/m.sh"
  sed -n '/^_lock_json_field() {/,/^}$/p'   "$W/m.sh"
  sed -n '/^_iso8601_epoch() {/,/^}/p'      "$W/m.sh"
  sed -n '/^lock_pid_state() {/,/^}/p'      "$W/m.sh"
  sed -n '/^lock_released_at() {/,/^}/p'    "$W/m.sh"
  sed -n '/^lock_started_age() {/,/^}/p'    "$W/m.sh"
} > "$W/readers.zsh"
for f in lock_decide _lock_json_field _iso8601_epoch lock_pid_state lock_released_at lock_started_age; do
  grep -q "^${f}() {" "$W/readers.zsh" || { print -r -- "*** ABORT: extraction of $f failed"; exit 3; }
done
eval "$(grep -E '^LOCK_[A-Z_]+=' "$W/m.sh")"
LOCK="$W/probe-LOCK"
source "$W/readers.zsh"
_h="$(hostname -s)"
printf '%s' "{\"host\":\"$_h\",\"pid\":$$,\"started_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"released_at\":\"2100-02-29T00:00:00Z\"}" > "$LOCK"
_v="$(lock_decide 1 "$(lock_released_at)" "$(lock_started_age)" 60 "$(lock_pid_state)")"
_e="$(_iso8601_epoch 2100-02-29T00:00:00Z 2>/dev/null || print -r -- REFUSE)"
CHECKS+=1
if [[ "$_v" == HELD-* && "$_e" != REFUSE ]]; then
  printf '%-5s %-7s %s\n' r07b GREEN "body verdict=$_v (BLIND) while _iso8601_epoch accepted it -> $_e. The body row could not have caught this; group H did."
else
  printf '%-5s %-7s %s\n' r07b '*** WRONG' "expected body=HELD-* and parser=accepted; got body=$_v parser=$_e"
  WRONG+=1
fi

print -r -- ""
print -r -- "=== C3 (F-T361-3, direction SHUT) — the group-C fixture must DERIVE from LOCK_CEILING_SECS"
mutate "C3 hard-coded fixture" 's@^  _OLD_AGE=\$(( LOCK_CEILING_SECS \* 2 + 60 )).*$@  _OLD_AGE=360000@'
_out="$(LOCK_CEILING_SECS=604800 /bin/zsh "$W/m.sh" --self-test-lock-readers 2>&1)"; _rc=$?
CHECKS+=1
if (( _rc != 0 )) && print -r -- "$_out" | grep -qE '^c01  \*\*\* FAIL-SHUT'; then
  printf '%-5s %-7s rc=%-3d %-46s %s\n' r09 GREEN $_rc "$(print -r -- "$_out" | grep -E '^ROWS=')" "hard-coded fixture at LOCK_CEILING_SECS=604800: group C goes SHUT and THE FIRE DOES NOT START"
else
  printf '%-5s %-7s rc=%-3d %s\n' r09 '*** WRONG' $_rc "expected a non-zero rc with c01 FAIL-SHUT; got $(print -r -- "$_out" | grep -E '^ROWS=')"
  WRONG+=1
fi
_out="$(LOCK_CEILING_SECS=604800 /bin/zsh "$SRC" --self-test-lock-readers 2>&1)"; _rc=$?
CHECKS+=1
if (( _rc == 0 )); then
  printf '%-5s %-7s rc=%-3d %-46s %s\n' r10 GREEN $_rc "$(print -r -- "$_out" | grep -E '^ROWS=')" "CONTROL: the SHIPPED derived fixture at the same threshold — the value that used to stop the fire no longer does"
else
  printf '%-5s %-7s rc=%-3d %s\n' r10 '*** WRONG' $_rc "the shipped file must pass at LOCK_CEILING_SECS=604800"
  WRONG+=1
fi

print -r -- ""
print -r -- "=== C2 (F-T361-2, direction SHUT) — mktemp must be checked; _st_dir must never be /"
print -r -- "SAFETY: the pre-C2 shape is reconstructed with its trap's \`rm -rf\` REPLACED BY A PRINT."
print -r -- "This driver runs on the real host. It proves the code REACHES _st_dir=/ ; it does not"
print -r -- "re-measure the deletion, which T361 measured in a throwaway container [T361 out/21]."
mutate "C2 reverted, rm neutered" \
  's@^  _st_dir="\$(/usr/bin/mktemp -d "\${TMPDIR:-/tmp}/fire-selftest.XXXXXX" 2>/dev/null)" || _st_dir=""$@  LOCK="$(mktemp -d "${TMPDIR:-/tmp}/fire-selftest.XXXXXX")/LOCK"\n  _st_dir="${LOCK:h}"\n  _OLD_C2_SHAPE=1@' \
  's@^  if \[\[ -z "\$_st_dir" || ! -d "\$_st_dir" || "\$_st_dir" == "/" \]\]; then$@  if false; then@' \
  's@^  LOCK="\$_st_dir/LOCK"$@  :@' \
  "s@^  trap .*rm -rf .\$_st_dir.' EXIT\$@  trap '[[ -n \"\${_st_dir:-}\" ]] \&\& print -u2 \"T365 NEUTERED: the pre-C2 trap WOULD HAVE RUN: rm -rf \$_st_dir\"' EXIT@"
_out="$(TMPDIR=/nonexistent-t365-unwritable /bin/zsh "$W/m.sh" --self-test-lock-readers 2>&1)"; _rc=$?
CHECKS+=1
if print -r -- "$_out" | grep -q 'WOULD HAVE RUN: rm -rf /$'; then
  printf '%-5s %-7s rc=%-3d %s\n' r11 GREEN $_rc "pre-C2 shape with an unwritable TMPDIR reaches _st_dir=/ and its trap targets the ROOT DIRECTORY:"
  print -r -- "$_out" | grep 'WOULD HAVE RUN' | sed 's/^/        /'
  print -r -- "$_out" | grep -E '^self-test: host=' | sed 's/^/        /'
else
  printf '%-5s %-7s rc=%-3d %s\n' r11 '*** WRONG' $_rc "expected the neutered pre-C2 trap to report a root target; it did not"
  print -r -- "$_out" | tail -5 | sed 's/^/        /'
  WRONG+=1
fi
_out="$(TMPDIR=/nonexistent-t365-unwritable /bin/zsh "$SRC" --self-test-lock-readers 2>&1)"; _rc=$?
CHECKS+=1
if (( _rc == 2 )) && print -r -- "$_out" | grep -q 'refusing to run against an unknown path'; then
  printf '%-5s %-7s rc=%-3d %s\n' r12 GREEN $_rc "CONTROL: the SHIPPED file refuses instead, before any trap is installed"
else
  printf '%-5s %-7s rc=%-3d %s\n' r12 '*** WRONG' $_rc "the shipped file must exit 2 with the refusal message"
  WRONG+=1
fi
CHECKS+=1
if (( $(grep -c '_st_dir="${LOCK:h}"' "$SRC") == 0 )); then
  printf '%-5s %-7s %s\n' r13 GREEN "the shipped file contains 0 occurrences of _st_dir=\"\${LOCK:h}\""
else
  printf '%-5s %-7s %s\n' r13 '*** WRONG' "_st_dir is still derived from an unchecked LOCK"
  WRONG+=1
fi

print -r -- ""
print -r -- "=== P-83 ON THIS DRIVER ITSELF — read the summary line's PRESENCE before its value"
print -r -- "A mutation that makes the self-test CRASH also exits non-zero. Every 'want nonzero' check"
print -r -- "above would score that GREEN on rc alone, and this driver would certify 'the guard caught"
print -r -- "it' about a guard that never ran. r14 removes the tally line and shows the presence test"
print -r -- "firing; if r14 is not caught, none of r01-r09 above means what it says."
mutate "delete the self-test's own tally line" \
  's@^  print -r -- "ROWS=\$_n FAIL_OPEN=\$_open FAIL_SHUT=\$_shut SKIPPED=\$_skipped"$@  print -r -- "T365 r14: tally line deleted"@'
_out="$(/bin/zsh "$W/m.sh" --self-test-lock-readers 2>&1)"; _rc=$?
CHECKS+=1
if print -r -- "$_out" | grep -qE '^ROWS='; then
  printf '%-5s %-7s rc=%-3d %s\n' r14 '*** WRONG' $_rc "the tally line survived the mutation; the presence test below proves nothing"
  WRONG+=1
else
  printf '%-5s %-7s rc=%-3d %s\n' r14 GREEN $_rc "no ROWS= line in the output -> check() scores this '<NO SUMMARY LINE>' and marks it WRONG, which is the point"
fi

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG"
(( WRONG == 0 )) || exit 1
exit 0
