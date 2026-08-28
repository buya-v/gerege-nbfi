#!/bin/zsh
# T361 — the off-BSD verification, REGENERATED (P-22), not read off T353's transcript.
#
# Two questions the brief names, answered separately:
#   Q1 does the CEILING arm (arm 3) fire on a non-BSD host?  -- the liveness half.
#   Q2 what does every arm do when `_iso8601_epoch` REFUSES? -- the polarity half.
# and a third the brief does not, which is the reviewer's job:
#   Q3 does the self-test itself pass INSIDE the container, i.e. is the wired control
#      valid on the host the fix is for, or only on the host that never had the bug?
#
# Rows are the reviewer's, not T353's. In particular row F01 puts a FOREIGN host in the
# body — the one lock shape `--self-test-lock-readers` has no row for.
emulate -L zsh
set -uo pipefail
FP="${1:?usage: t361-linux-probe.zsh <fire-program.sh>}"

print -r -- "=== T361 linux probe: host facts ==="
uname -srm
print -r -- "zsh $ZSH_VERSION"
print -r -- "/bin/date is: $(/bin/date --version 2>&1 | head -1 || true)"
print -r -- "/bin/date -j test: $(TZ=UTC /bin/date -j -f '%Y-%m-%dT%H:%M:%SZ' '2026-08-28T14:00:05Z' +%s 2>&1 | head -1) [rc=$?]"
print -r -- "/bin/date -j as SHIPPED (stderr swallowed): [$(TZ=UTC /bin/date -j -f '%Y-%m-%dT%H:%M:%SZ' '2026-08-28T14:00:05Z' +%s 2>/dev/null)]"
print -r -- "/usr/bin/python3: $( [[ -x /usr/bin/python3 ]] && /usr/bin/python3 -V 2>&1 || print ABSENT )"
print -r -- "/usr/bin/stat -f test: $(/usr/bin/stat -f %m "$FP" 2>&1 | head -1)"
print -r -- ""

S="$(mktemp -d)" || exit 3
[[ -n "$S" && "$S" != "/" ]] || exit 3
mkdir -p "$S/.softhouse" "$S/home"
export GIT_CONFIG_NOSYSTEM=1 HOME="$S/home"
printf '[user]\n\tname = T361\n\temail = t361@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"
git init -q "$S" 2>/dev/null
( cd "$S" && echo x > .softhouse/x && git add -A >/dev/null 2>&1 && git commit -qm seed >/dev/null 2>&1 )

H="$(hostname -s 2>/dev/null || hostname)"
NOW="$(/usr/bin/python3 -c 'import datetime;print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
OLD="$(/usr/bin/python3 -c 'import sys,datetime;print((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=100)).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
sleep 900 & LIVE=$!
sleep 0.1 & DEAD=$!; wait $DEAD 2>/dev/null
trap "kill $LIVE 2>/dev/null; rm -rf '$S'" EXIT
print -r -- "host=$H live=$LIVE dead=$DEAD now=$NOW old=$OLD"
print -r -- ""

typeset -i n=0 fo=0 fs=0
row() {  # $1 id  $2 want  $3 body  $4 note
  local id="$1" want="$2" body="$3" note="$4" out sig verdict mark
  printf '%s' "$body" > "$S/.softhouse/LOCK"
  out="$(GEREGE_NBFI_REPO="$S" zsh "$FP" --lock-signals 2>&1)"
  sig="$(print -r -- "$out" | grep '^lock_present' || true)"
  verdict="$(print -r -- "$out" | sed -n 's/^verdict=//p' | head -1)"
  n+=1; mark=ok
  if [[ "$want" == HELD ]]; then
    [[ "$verdict" == HELD-* ]] || { mark="*** FAIL-OPEN"; fo+=1; }
  else
    [[ "$verdict" == "$want" ]] || { mark="*** FAIL-SHUT"; fs+=1; }
  fi
  printf '%-4s %-14s want=%-15s got=%-16s %s\n' "$id" "$mark" "$want" "${verdict:-<none>}" "$note"
  printf '     %s\n' "$sig"
}

print -r -- "--- Q1: can arm 3 (the CEILING) fire off-BSD? FAIL-SHUT here = the defect T353 repairs."
row C01 TAKE-ceiling "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$OLD\"}"   "100 h old, spaced"
row C02 TAKE-ceiling "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$OLD\"}"        "100 h old, compact"
row A01 HELD         "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\"}"   "fresh, live -> must stay HELD"
row B01 TAKE-dead-pid "{\"host\": \"$H\", \"pid\": $DEAD, \"started_at\": \"$NOW\"}"  "arm 2, dead pid here"

print -r -- ""
print -r -- "--- Q2: what every arm does when _iso8601_epoch REFUSES. want HELD (SHUT is correct here)."
row R01 HELD "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"not-a-date\"}"                       "started_at unparseable"
row R02 HELD "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"2026-02-30T00:00:00Z\"}"             "started_at an impossible DATE"
# R03: want corrected AFTER MEASURING, and the correction is the point. `released_at:"None"`
# is correctly NOT a release (arm 1 does not fire) but the body is ALSO 100 h old, so arm 3
# fires and the verdict is TAKE-ceiling. That is the DESIGNED answer, not a fail-open: the
# ceiling does not care why arm 1 declined. Recorded rather than silently rescored.
row R03 TAKE-ceiling "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$OLD\", \"released_at\": \"None\"}"  "100h old AND released_at=None -> arm 1 declines, arm 3 fires. CORRECT."
row R04 HELD "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"pending\"}" "released_at=pending -> NOT released"
# R05 is F-T361-1 and it is EXPECTED TO FAIL here. `0001-01-01T00:00:00Z` is what Go's zero
# `time.Time` marshals to through encoding/json (VERIFIED by running go, not recalled), and
# what `datetime.min` formats to in python. It is a syntactically perfect instant, so T353's
# tightened contract reads it as a RELEASE while a LIVE pid holds the lock. The row is left
# RED on purpose: a probe that hides its own finding is not a probe.
row R05 HELD "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"0001-01-01T00:00:00Z\"}" "F-T361-1: Go time.Time ZERO VALUE -- EXPECTED RED"
row D01 FREE-released "{\"host\": \"$H\", \"pid\": $LIVE, \"started_at\": \"$NOW\", \"released_at\": \"$NOW\"}" "a genuine release must still fire"

print -r -- ""
print -r -- "--- Q3 (T361's own): the FOREIGN-HOST row that --self-test-lock-readers has no case for."
row F01 HELD "{\"host\": \"some-other-machine\", \"pid\": $DEAD, \"started_at\": \"$NOW\"}"  "dead-looking pid but ANOTHER host: must NOT be judged"
row F02 HELD "{\"host\": \"some-other-machine\", \"pid\": 999999, \"started_at\": \"$NOW\"}" "impossible pid on another host"

print -r -- ""
print -r -- "ROWS=$n FAIL_OPEN=$fo FAIL_SHUT=$fs"
print -r -- ""
print -r -- "--- Q3b: does --self-test-lock-readers itself pass HERE?"
zsh "$FP" --self-test-lock-readers 2>&1 | tail -4
print -r -- "SELFTEST_EXIT=${pipestatus[1]}"
(( fo == 0 && fs == 0 )) || exit 1
exit 0
