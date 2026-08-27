#!/usr/bin/env bash
# T154 LEG 1 — the two no-float shell guards can be defeated by ONE invalid byte.
#
# WHAT THIS DRIVES RED.  conformance.sh's guard_no_float_in_vectors and
# guard_no_float_in_harness pipe through a BARE `grep -Eq`.  Inside a script the
# token `grep` is /usr/bin/grep, BSD grep 2.6.0-FreeBSD (P-33 / T108).  In a
# UTF-8 locale BSD grep goes blind to the part of a LINE at and to the RIGHT of
# an invalid byte — count 0, exit 1, no diagnostic.  These guards fire only when
# they FIND something bad, so a blind grep is a SILENT PASS ON A FLOAT.
#
# BOTH ARMS RUN AGAINST REAL BYTES, NOT A PARAPHRASE:
#   PRE  = the guard lines as committed at PIN_PREFIX_SHA — a literal immutable
#          sha, never `main:` and never `git merge-base main HEAD` (P-24).
#   POST = the guard lines in the WORKING TREE.
# Both are extracted from the file by anchored sed, so a rewrite that renames the
# function or moves the pipeline makes this script ERROR (exit 2) rather than
# silently grade nothing.
#
# Run:  bash .softhouse/capture/t154-nofloat/drive-leg1.sh
# Exit: 0 = every cell as wanted.  1 = a cell disagreed.  2 = apparatus broken.
set -u -o pipefail

PIN_PREFIX_SHA=187e9726dfad5076f4b68877f411d7d218280889   # T154's fork point

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# The file under test. Overridable ONLY so the RED transcript can be REGENERATED
# at will: point it at a pre-fix extraction and every POST row reproduces the
# state this leg exists to end. Nothing in normal use sets it.
CONF="${T154_CONF_UNDER_TEST:-$REPO_ROOT/.softhouse/conformance.sh}"
TMP="$(mktemp -d -t t154-leg1)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ok()  { printf 'OK    %s\n' "$*"; pass=$((pass+1)); }
bad() { printf 'FAIL  %s\n' "$*"; fail=$((fail+1)); }

echo "=== [0] APPARATUS — binary, version, locale, invocation, input shape (P-33) ==="
echo "grep resolves to  : $(type -a grep 2>&1 | head -3 | tr '\n' '|')"
echo "/usr/bin/grep     : $(/usr/bin/grep --version 2>&1 | head -1)"
echo "locale            : LANG=${LANG:-unset} LC_ALL=${LC_ALL:-unset} LC_CTYPE=${LC_CTYPE:-unset}"
echo "invocation        : inside a bash SCRIPT — shell functions are NOT inherited by a child"
echo "pinned pre-fix sha: $PIN_PREFIX_SHA"
echo "pre-fix subject   : $(cd "$REPO_ROOT" && git log -1 --format=%s "$PIN_PREFIX_SHA")"
echo

# ---------------------------------------------------------------------------
# Extract a guard's grep pipeline from a revision of conformance.sh ("-" = tree)
# ---------------------------------------------------------------------------
srcfor() {
  local rev="$1" src
  if [ "$rev" = "-" ]; then printf '%s' "$CONF"; return 0; fi
  src="$TMP/conf-$rev.sh"
  [ -f "$src" ] || (cd "$REPO_ROOT" && git show "$rev:.softhouse/conformance.sh") > "$src"
  printf '%s' "$src"
}

# The whole `if perl … | grep …; then` STATEMENT, not just the line carrying the
# word grep. The harness guard spells its pipeline across two lines with a
# trailing backslash, and taking only the grep line yields `| grep …` with no
# producer — which reads the script's own stdin, matches nothing, and reports
# SILENT on every row. That is a NULL CONTROL (P-36) and it looks exactly like a
# result; the v1/g1 POSITIVE CONTROL rows exist to make it impossible to ship.
extract() { # extract <rev|-> <vectors|harness>
  local src; src="$(srcfor "$1")"
  case "$2" in
    vectors) sed -n '/^guard_no_float_in_vectors()/,/^}/p' "$src" ;;
    harness) sed -n '/^guard_no_float_in_harness()/,/^}/p'  "$src" ;;
  esac | awk '
    /^[[:space:]]*if[[:space:]]*perl/ { p = 1 }
    p                                 { print }
    p && /;[[:space:]]*then[[:space:]]*$/ { exit }
  '
  # awk, not `sed -n /a/,/b/p`: sed will not close a range on the line that
  # opened it, so the vectors guard — whose whole `if … ; then` is ONE line —
  # came back as the entire function body including `done < <(find …)` and `}`.
  # That still "ran" and still printed a verdict for every row. It was wrong on
  # the POSITIVE CONTROL, which is the only reason it was caught.
}

# Turn the extracted `if perl … | grep …; then` into a runnable command with $f
# bound by the caller.
runnable() {
  extract "$1" "$2" \
    | sed 's/^[[:space:]]*if[[:space:]]*//; s/[[:space:]]*\\$//; s/;[[:space:]]*then[[:space:]]*$//' \
    | tr '\n' ' '
}

for rev in "$PIN_PREFIX_SHA" -; do
  for which in vectors harness; do
    r="$(runnable "$rev" "$which")"
    case "$r" in
      *grep*) : ;;
      *) echo "APPARATUS BROKEN: no grep pipeline extracted for rev=$rev which=$which"; exit 2 ;;
    esac
    label="PRE "; [ "$rev" = "-" ] && label="POST"
    printf '%s %-8s %s\n' "$label" "$which" "$r"
  done
done
echo

# ---------------------------------------------------------------------------
# CORPUS.  The poison byte is a LONE 0xE2 — a truncated UTF-8 lead byte, invalid
# on its own — placed OUTSIDE any JSON string, so the guard's own perl
# string-stripper cannot carry it away with a string literal.
# ---------------------------------------------------------------------------
mkdir -p "$TMP/corpus"
printf '{\n  "case_id": "V1",\n  "rate_pct": 3.6\n}\n'                  > "$TMP/corpus/v1-clean-float.json"
printf '{\n  "case_id": "V2",\n  \xe2 "rate_pct": 3.6\n}\n'             > "$TMP/corpus/v2-poison-before-same-line.json"
printf '{\n  "case_id": "V3",\n  "rate_pct": 3.6 \xe2\n}\n'             > "$TMP/corpus/v3-poison-after-same-line.json"
printf '{\n  "case_id": "V4",\n  \xe2 "n": 36e2\n}\n'                   > "$TMP/corpus/v4-poison-before-exponent.json"
printf '{\n  "case_id": "V5",\n  "principal_minor": "120000000"\n}\n'   > "$TMP/corpus/v5-clean-integers.json"
printf 'package p\n\nfunc f() { var x float64 = 1 ; _ = x }\n'          > "$TMP/corpus/g1-clean-float64.go"
printf 'package p\n\nfunc f() { var \xe2 x float64 = 1 ; _ = x }\n'     > "$TMP/corpus/g2-poison-before-same-line.go"
printf 'package p\n\nfunc f() { var x int64 = 1 ; _ = x }\n'            > "$TMP/corpus/g3-clean-int.go"

echo "=== [1] CORPUS BYTES (od -c) ==="
for f in "$TMP"/corpus/*; do
  printf '%-36s %s\n' "$(basename "$f")" "$(od -An -c "$f" | tr -s ' ' | tr '\n' ' ' | cut -c1-130)"
done
echo

fires() { # fires <rev> <which> ; $f is bound by the caller
  local r rc; r="$(runnable "$1" "$2")"
  eval "$r" >/dev/null 2>&1; rc=$?
  [ "$rc" = 0 ] && printf 'FIRES' || printf 'SILENT'
}

echo "=== [2] THE MATRIX — guard verdict per (guard, file) ==="
printf '%-36s %-8s %-8s %-8s %-8s\n' FILE PRE POST 'want-PRE' 'want-POST'
rows='
vectors|v1-clean-float.json|FIRES|FIRES|POSITIVE CONTROL: without this cell the whole matrix is a null control
vectors|v2-poison-before-same-line.json|SILENT|FIRES|THE DEFEAT
vectors|v3-poison-after-same-line.json|FIRES|FIRES|byte AFTER the match — BSD grep survives; the shape T91 used
vectors|v4-poison-before-exponent.json|SILENT|FIRES|THE DEFEAT, exponent form
vectors|v5-clean-integers.json|SILENT|SILENT|NEGATIVE CONTROL: no false positive on a legitimate vector
harness|g1-clean-float64.go|FIRES|FIRES|POSITIVE CONTROL
harness|g2-poison-before-same-line.go|SILENT|FIRES|THE DEFEAT
harness|g3-clean-int.go|SILENT|SILENT|NEGATIVE CONTROL
'
printf '%s\n' "$rows" | while IFS='|' read -r which file wantpre wantpost why; do
  [ -n "${which:-}" ] || continue
  f="$TMP/corpus/$file"
  [ -f "$f" ] || { echo "APPARATUS BROKEN: missing corpus file $file"; exit 2; }
  gotpre="$(fires "$PIN_PREFIX_SHA" "$which")"
  gotpost="$(fires "-" "$which")"
  printf '%-36s %-8s %-8s %-8s %-8s  %s\n' "$file" "$gotpre" "$gotpost" "$wantpre" "$wantpost" "$why"
  st=0
  [ "$gotpre"  = "$wantpre"  ] || st=1
  [ "$gotpost" = "$wantpost" ] || st=1
  printf '%s\n' "$st" >> "$TMP/verdicts"
done
echo

# The while-loop above runs in a subshell (pipeline), so tally from the file.
pass=0; fail=0
while read -r st; do
  [ "$st" = 0 ] && pass=$((pass+1)) || fail=$((fail+1))
done < "$TMP/verdicts"

echo "=== [3] ZERO FILES INSPECTED IS AN ERROR, NOT A PASS (P-35) ==="
# The guards are lifted whole out of conformance.sh and run against an EMPTY
# directory. Pre-fix they return 0 — "I found no float", over no files at all.
zero_verdict() { # zero_verdict <rev> <vectors|harness>
  local src fn root out rc
  src="$(srcfor "$1")"
  case "$2" in
    vectors) fn=guard_no_float_in_vectors ;;
    harness) fn=guard_no_float_in_harness ;;
  esac
  root="$TMP/empty-$2"; mkdir -p "$root"
  {
    echo 'warn() { printf "%s\n" "$*" >&2; }'
    echo 'say()  { printf "%s\n" "$*"; }'
    echo "STORE_ROOT='$root'"
    echo "NEXUS_DIR='$root'"
    echo "mkdir -p '$root/internal/apps/loanschedule'"
    sed -n "/^$fn()/,/^}/p" "$src"
    echo "$fn"
  } > "$TMP/zero-$1-$2.sh"
  out="$(bash "$TMP/zero-$1-$2.sh" 2>&1)"; rc=$?
  printf '%s|%s' "$rc" "$(printf '%s' "$out" | tr '\n' ' ')"
}
zfail=0
for which in vectors harness; do
  pre="$(zero_verdict "$PIN_PREFIX_SHA" "$which")"; prerc="${pre%%|*}"
  post="$(zero_verdict "-" "$which")";             postrc="${post%%|*}"
  printf '  %-8s PRE  exit %s   POST exit %s\n' "$which" "$prerc" "$postrc"
  printf '  %-8s POST says: %s\n' "$which" "${post#*|}"
  if [ "$prerc" = 0 ]; then ok "PRE  $which over an EMPTY directory returned 0 — the vacuous pass"
  else bad "PRE  $which over an EMPTY directory returned $prerc, wanted 0"; zfail=1; fi
  if [ "$postrc" != 0 ]; then ok "POST $which over an EMPTY directory returned $postrc — an ERROR"
  else bad "POST $which over an EMPTY directory returned 0 — still vacuous"; zfail=1; fi
done
[ "$zfail" = 0 ] || true
echo

echo "=== [4] THE SENTENCE THIS LEG EXISTS TO MAKE FALSE ==="
echo "  BEFORE: a vector file carrying a float AND one invalid byte earlier on the"
echo "          same line takes guard_no_float_in_vectors to a SILENT PASS."
echo "  AFTER : it FIRES."
echo
echo "======================================================================="
echo "LEG 1 ROWS: $pass as wanted, $fail not as wanted"
echo "======================================================================="
[ "$fail" -eq 0 ]
