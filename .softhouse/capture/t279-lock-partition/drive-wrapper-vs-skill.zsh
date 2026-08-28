#!/bin/zsh
# T279 F-3 — DRIVE THE SHIPPED WRAPPER OVER THE SAME STATE SPACE AS THE SKILL, AND DIFF.
#
# T265 F-3: `fire-program.sh` decided staleness on the lock FILE'S MTIME while
# `softhouse-program/SKILL.md` STEP 0 declared push recency authoritative, so the two
# documents that must agree provably did not. This script makes "they agree" a
# measurement: `rules.py` holds the arms as STEP 0 states them, the wrapper holds them as
# zsh, and every one of the 192 states is put through both.
#
# It calls the REAL FILE (`fire-program.sh --lock-decide ...`), not a copy of the
# function, so a future edit that changes the wrapper's mind and not the skill's fails here.
#
# Usage: zsh drive-wrapper-vs-skill.zsh [path-to-fire-program.sh]
set -uo pipefail
HERE="${0:A:h}"
WRAPPER="${1:-$HERE/../../bin/fire-program.sh}"
WRAPPER="${WRAPPER:A}"

print -r -- "wrapper under test: $WRAPPER"
print -r -- "thresholds in force: LOCK_MAX_AGE_SECS=${LOCK_MAX_AGE_SECS:-21600} LOCK_CEILING_SECS=${LOCK_CEILING_SECS:-86400}"
print -r -- ""

# The python side prints "<state-key>\t<expected-verdict>" for every state, using the
# SAME arm names the wrapper prints.
python3 - "$HERE" <<'PY' > /tmp/t279-expected.tsv
import sys, os
sys.path.insert(0, sys.argv[1])
import rules
NAME = {"N0": "FREE-no-lock", "N1": "FREE-released", "N2": "TAKE-dead-pid",
        "N3": "TAKE-ceiling", "N4": "HELD-live", "N5": "TAKE-both-stale",
        "N6": "HELD-default"}
for s in rules.states():
    m = rules.matches(rules.NEW_ARMS, s)
    assert len(m) == 1, (s, m)          # the partition property, re-asserted here
    print("\t".join([s["lock"], s["released"], s["started"], s["tip"], s["pid"],
                     NAME[m[0][0]]]))
PY
print -r -- "expected verdicts generated: $(wc -l < /tmp/t279-expected.tsv | tr -d ' ')"

# Concrete seconds for each symbolic age. 6h = 21600, 24h = 86400.
sec_started() { case "$1" in
  lt6) print 3600 ;; b6_24) print 43200 ;; ge24) print 90000 ;; unreadable) print "" ;; esac }
sec_tip() { case "$1" in
  lt6) print 3600 ;; ge6) print 43200 ;; unreadable) print "" ;; esac }

typeset -i n=0 bad=0
: > /tmp/t279-actual.tsv
while IFS=$'\t' read -r lock rel st tip pid want; do
  present=1; [[ "$lock" == absent ]] && present=0
  relv=""; [[ "$rel" == set ]] && relv="2026-08-28T00:00:00Z"
  got="$(zsh "$WRAPPER" --lock-decide "$present" "$relv" "$(sec_started $st)" "$(sec_tip $tip)" "$pid")"
  print -r -- "$lock\t$rel\t$st\t$tip\t$pid\t$got" >> /tmp/t279-actual.tsv
  (( n++ ))
  if [[ "$got" != "$want" ]]; then
    (( bad++ ))
    print -r -- "MISMATCH  lock=$lock released=$rel started=$st tip=$tip pid=$pid  skill=$want wrapper=$got"
  fi
done < /tmp/t279-expected.tsv

print -r -- ""
print -r -- "states driven through the SHIPPED wrapper: $n"
print -r -- "disagreements with SKILL.md STEP 0 as modelled in rules.py: $bad"
if (( bad )); then
  print -r -- "RESULT: FAIL — the wrapper and the skill do not decide the same way."
  exit 1
fi
print -r -- "RESULT: PASS — the wrapper and the skill agree on all $n states."

# ---------------------------------------------------------------------------------
# THE CASE THAT MADE F-3 A DEFECT RATHER THAN A TIDINESS COMPLAINT: mtime and
# push-recency disagreeing. T265 measured 12.6 min of mtime against ~8 h of real lock
# age, because `git pull --ff-only` rewrites the lock file just before the check.
print -r -- ""
print -r -- "--- the state where the OLD mtime signal and the NEW push signal disagree ---"
OLD_MTIME_AGE=759          # T265's live reading, seconds
STARTED_AGE=28800          # the same lock's true age, 8 h
TIP_AGE=43200              # 12 h since anything was published
print -r -- "  lock file mtime age : ${OLD_MTIME_AGE}s  (what the wrapper used to read)"
print -r -- "  started_at age      : ${STARTED_AGE}s"
print -r -- "  origin/main tip age : ${TIP_AGE}s"
print -r -- "  OLD wrapper rule (AGE < LOCK_MAX_AGE_SECS ? held : stale) -> $(( OLD_MTIME_AGE < 21600 )) => HELD, fire exits, 6 h lost"
print -r -- "  NEW wrapper rule                                          -> $(zsh "$WRAPPER" --lock-decide 1 "" $STARTED_AGE $TIP_AGE absent)"
print -r -- "  SKILL.md STEP 0 arm 5 (both signals over 6 h)             -> TAKE-both-stale"
print -r -- "  => the two now agree; before this change they did not."
