#!/bin/bash
# T130 — what does `read` with a SINGLE variable do to a line, as a function of IFS?
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T130-evidence/read-ifs-predicate.sh
#
# Exit 0 = the candidate rule matched `read` in every case. Exit 1 = at least one
# disagreement, printed with the exact (IFS, line) that produced it.
#
# WHY THIS EXISTS. `conformance.sh` has now carried TWO wrong statements of this
# rule — T106's, and the one T113 wrote when it withdrew T106's. T121 caught the
# second and stated the rule in words. This script does not test a wording; it turns
# the rule into a PREDICATE and brute-forces `read` against it, so "the rule" is
# something a reviewer can falsify on their own bash in one command (P-11: review the
# justification as a separate artefact, and re-derive it).
#
# THE CANDIDATE RULE, which is what conformance.sh now states:
#
#   With IFS containing no whitespace, a single-variable `read -r` returns the line
#   unchanged UNLESS the line's LAST character is an IFS delimiter AND that is the
#   ONLY position in the whole line holding ANY IFS delimiter — in which case exactly
#   that one character is removed.
#
#   Note "ANY IFS delimiter", not "that character": `abcze` survives IFS=ze (two
#   delimiter positions, different characters) while `abcz` does not.
#
# T130 ran it over 3,282 (line, IFS) pairs on bash 3.2.57, 4.4.0 and 5.3.9 — 0
# disagreements on each:
#   read-ifs-predicate.sh ab  6  a b ab
#   read-ifs-predicate.sh abc 5  a b c ab bc abc : a:
#
# Integer counters and string comparison only; no floating point and no money
# quantity anywhere (P-25).
set -u

if [ "$#" -lt 3 ]; then
  cat >&2 <<USAGE
usage: read-ifs-predicate.sh <alphabet> <maxlen> <ifs> [<ifs> ...]
   eg: read-ifs-predicate.sh ab 6 a b ab
USAGE
  exit 2
fi
alpha="$1"; maxlen="$2"; shift 2
ifs_list=("$@")

# Every non-empty string of length 1..maxlen over the alphabet.
gen() { # gen <prefix> <remaining-depth>
  local p="$1" d="$2" i c
  [ -n "$p" ] && printf '%s\n' "$p"
  [ "$d" -eq 0 ] && return
  i=0
  while [ "$i" -lt "${#alpha}" ]; do
    c="${alpha:$i:1}"
    gen "$p$c" $((d - 1))
    i=$((i + 1))
  done
}

predict() { # predict <line> <ifs> -> what the candidate rule says `read` returns
  local line="$1" ifs="$2" n i c d=0 lastpos=-1
  n=${#line}
  i=0
  while [ "$i" -lt "$n" ]; do
    c="${line:$i:1}"
    case "$ifs" in *"$c"*) d=$((d + 1)); lastpos=$i ;; esac
    i=$((i + 1))
  done
  if [ "$d" -eq 1 ] && [ "$lastpos" -eq $((n - 1)) ]; then
    printf '%s' "${line:0:$((n - 1))}"
  else
    printf '%s' "$line"
  fi
}

checked=0; agree=0; disagree=0
while builtin read -r line; do
  for ifs in "${ifs_list[@]}"; do
    got="$(IFS="$ifs" builtin read -r v <<< "$line"; builtin printf '%s' "$v")"
    want="$(predict "$line" "$ifs")"
    checked=$((checked + 1))
    if [ "$got" = "$want" ]; then
      agree=$((agree + 1))
    else
      disagree=$((disagree + 1))
      printf '  DISAGREE IFS=[%s] line=[%s] read=[%s] rule=[%s]\n' "$ifs" "$line" "$got" "$want"
    fi
  done
done < <(gen "" "$maxlen")

if [ "$checked" -eq 0 ]; then
  echo "read-ifs-predicate: zero cases generated — a sweep that inspects nothing is an error, not a pass (P-22)." >&2
  exit 1
fi

printf 'bash %s  alphabet=[%s] maxlen=%s  ifs={%s}\n' "$BASH_VERSION" "$alpha" "$maxlen" "${ifs_list[*]}"
printf 'PREDICATE CHECK: %d cases, %d agree, %d DISAGREE\n' "$checked" "$agree" "$disagree"
[ "$disagree" -eq 0 ]
