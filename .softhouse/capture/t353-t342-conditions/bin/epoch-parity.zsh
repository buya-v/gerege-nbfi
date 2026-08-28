#!/bin/zsh
# T353 — DIFFERENTIAL: `_iso8601_epoch` (the new fork-free zsh parser) against the two
# implementations it has to agree with, on whichever of them exists on this host:
#   BSD   TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "$v" +%s     (what the wrapper shipped)
#   PY    datetime.strptime(...).replace(tzinfo=utc).timestamp()   (what ready-tasks.py-class
#                                                                   code would do)
# Replacing a working parser with a hand-rolled one is only safe if the answers are IDENTICAL,
# so this is the drive that earns the replacement. It also drives the REFUSAL half: the
# malformed corpus must return rc 1, because on the lock path a parse that guesses is a
# fail-open (`released_at` shape) and a fail-shut (`started_at`).
#
# usage: epoch-parity.zsh <path-to-fire-program.sh>
emulate -L zsh
set -uo pipefail
FP="${1:?usage: epoch-parity.zsh <fire-program.sh>}"

# Pull the function out of the shipped file rather than retyping it (P-46: quote by
# extraction). It is self-contained and touches no global but its argument.
eval "$(sed -n '/^_iso8601_epoch() {$/,/^}$/p' "$FP")"
typeset -f _iso8601_epoch >/dev/null || { print -r -- "EXTRACTION FAILED -- test is void"; exit 2; }

have_bsd=0; have_py=0
TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "2000-01-01T00:00:00Z" +%s >/dev/null 2>&1 && have_bsd=1
[[ -x /usr/bin/python3 ]] && have_py=1
print -r -- "reference implementations available: BSD date -j=$have_bsd  /usr/bin/python3=$have_py"
print -r -- ""

typeset -i n=0 bad=0

good() {  # $1 = a well-formed instant
  local v="$1" mine bsd py mark="ok"
  n+=1
  mine="$(_iso8601_epoch "$v")" || mine="<REFUSED>"
  bsd="-"; py="-"
  (( have_bsd )) && bsd="$(TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "$v" +%s 2>/dev/null || print '<REFUSED>')"
  (( have_py ))  && py="$(/usr/bin/python3 -c 'import sys,datetime;print(int(datetime.datetime.strptime(sys.argv[1],"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()))' "$v" 2>/dev/null || print '<REFUSED>')"
  (( have_bsd )) && [[ "$mine" != "$bsd" ]] && { mark="*** DISAGREES WITH BSD date"; bad+=1; }
  (( have_py ))  && [[ "$mine" != "$py"  ]] && { mark="*** DISAGREES WITH python"; bad+=1; }
  printf '  %-22s mine=%-13s bsd=%-13s py=%-13s %s\n' "$v" "$mine" "$bsd" "$py" "$mark"
}

bad_() {  # $1 = a body that MUST be refused, $2 = why
  local v="$1" why="$2" mine mark="ok refused"
  n+=1
  if mine="$(_iso8601_epoch "$v")"; then mark="*** ACCEPTED (must refuse)"; bad+=1; else mine="<REFUSED>"; fi
  printf '  %-30s -> %-12s %-24s %s\n' "'$v'" "$mine" "$mark" "$why"
}

print -r -- "--- A. WELL-FORMED. mine must equal every reference present."
good "1970-01-01T00:00:00Z"
good "1970-01-01T00:00:01Z"
good "1999-12-31T23:59:59Z"
good "2000-01-01T00:00:00Z"
good "2000-02-29T12:00:00Z"     # leap year, div by 400
good "2001-02-28T23:59:59Z"
good "2004-02-29T00:00:00Z"     # leap year, div by 4
good "2024-02-29T06:30:00Z"
good "2026-08-28T14:00:05Z"     # this fire
good "2026-08-24T02:36:16Z"     # the 100 h stamp the linux probe uses
good "2026-01-31T00:00:00Z"
good "2026-03-01T00:00:00Z"
good "2026-12-31T23:59:59Z"
good "2038-01-19T03:14:07Z"     # the 32-bit signed boundary
good "2038-01-19T03:14:08Z"
good "2100-02-28T00:00:00Z"     # NOT a leap year: div by 100, not by 400
good "2100-03-01T00:00:00Z"
good "2400-02-29T00:00:00Z"
good "9999-12-31T23:59:59Z"

print -r -- ""
print -r -- "--- B. MALFORMED. mine must REFUSE every one (rc 1, nothing on stdout)."
bad_ ""                          "empty"
bad_ " "                         "a space"
bad_ "null"                      "the string null"
bad_ "None"                      "str(None) -- F-T346-1"
bad_ "NULL"                      "SQL-ish null"
bad_ "pending"                   "a hand-writer's not-yet"
bad_ "false"                     "a bool spelled as a string"
bad_ "0"                         "a zero"
bad_ "-"                         "a dash"
bad_ "2026-08-28"                "date only, no time"
bad_ "2026-08-28T14:00:05"       "no Z"
bad_ "2026-08-28T14:00:05+08:00" "an offset, not UTC"
bad_ "2026-08-28t14:00:05z"      "lowercase separators"
bad_ "2026-08-28 14:00:05Z"      "space instead of T"
bad_ "26-08-28T14:00:05Z"        "two-digit year"
bad_ "2026-8-28T14:00:05Z"       "unpadded month"
bad_ "2026-13-01T00:00:00Z"      "month 13"
bad_ "2026-00-01T00:00:00Z"      "month 0"
bad_ "2026-02-30T00:00:00Z"      "30 February"
bad_ "2026-02-29T00:00:00Z"      "29 Feb in a NON-leap year"
bad_ "2100-02-29T00:00:00Z"      "29 Feb in a century non-leap year"
bad_ "2026-04-31T00:00:00Z"      "31 April"
bad_ "2026-08-00T00:00:00Z"      "day 0"
bad_ "2026-08-32T00:00:00Z"      "day 32"
bad_ "2026-08-28T24:00:00Z"      "hour 24"
bad_ "2026-08-28T14:60:00Z"      "minute 60"
bad_ "2026-08-28T14:00:61Z"      "second 61"
bad_ "2026-08-28T14:00:05Z "     "trailing space"
bad_ " 2026-08-28T14:00:05Z"     "leading space"
bad_ "2026-08-28T14:00:05Zx"     "trailing junk"
bad_ "202X-08-28T14:00:05Z"      "a letter in the year"
bad_ "2026-08-28T14:00:05.123Z"  "fractional seconds"

print -r -- ""
print -r -- "--- C. LEAP SECOND. Deliberately ACCEPTED as :60 and mapped onto the next second,"
print -r -- "    which is what a POSIX epoch can represent. BSD date does the same; python's"
print -r -- "    strptime refuses it. Recorded, not treated as a disagreement."
printf '  %-22s mine=%s  bsd=%s\n' "2016-12-31T23:59:60Z" \
  "$(_iso8601_epoch 2016-12-31T23:59:60Z || print '<REFUSED>')" \
  "$( (( have_bsd )) && (TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "2016-12-31T23:59:60Z" +%s 2>/dev/null || print '<REFUSED>') || print '-')"

print -r -- ""
print -r -- "ROWS=$n DISAGREEMENTS=$bad"
(( bad == 0 )) || exit 1
exit 0
