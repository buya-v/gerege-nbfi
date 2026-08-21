#!/usr/bin/env bash
# T154 LEG 2 — a float LITERAL was invisible to every no-float guard in the repo.
#
# THE HOLE (T134's row M-3, registered as T143). Both no-float guards inspected
# IDENTIFIERS. `rate := 0.036 / 12.0` declares none: Go infers an untyped float
# constant, the arithmetic is IEEE-754 binary floating point, and the word
# "float" appears nowhere. So the expression
#
#     func t154InterestProbe(p int64) int64 { rate := 0.036 / 12.0; amt := rate * 1.0; return p + int64(amt) }
#
# BUILT, PASSED `go test -run TestNoFloatInTheLoanScheduleTree`, AND TOOK
# `bash .softhouse/conformance.sh` TO EXIT 0 — three greens over a violation of
# the first non-negotiable in CLAUDE.md.
#
# THREE ARMS, because the defect had three greens and a fix that closes two of
# them is not a fix:
#     go build   ·   go test (the guard)   ·   conformance.sh (the verdict)
#
# BOTH TREES ARE SCRATCH TREES. PRE is `git archive` of a literal immutable sha
# (P-24); POST is a copy of the working tree. The real tree is never poisoned,
# and section [4] asserts that.
#
# Run:  bash .softhouse/capture/t154-nofloat/drive-leg2.sh
# Exit: 0 = every cell as wanted. 1 = a cell disagreed. 2 = apparatus broken.
set -u -o pipefail

PIN_PREFIX_SHA=187e9726dfad5076f4b68877f411d7d218280889   # T154's fork point

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TMP="$(mktemp -d -t t154-leg2)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ok()  { printf 'OK    %s\n' "$*"; pass=$((pass+1)); }
bad() { printf 'FAIL  %s\n' "$*"; fail=$((fail+1)); }

PATHS=(.softhouse/conformance.sh .softhouse/bin .softhouse/vectors nexus)
mktree() {
  local rev="$1" dest="$2"
  mkdir -p "$dest"
  if [ "$rev" = "-" ]; then ( cd "$REPO_ROOT" && tar -cf - "${PATHS[@]}" ) | ( cd "$dest" && tar -xf - )
  else ( cd "$REPO_ROOT" && git archive "$rev" -- "${PATHS[@]}" ) | ( cd "$dest" && tar -xf - ); fi
  ln -s "$REPO_ROOT/.softhouse/capture" "$dest/.softhouse/capture"
  [ -d "$dest/nexus/internal/apps/loanschedule" ] || { echo "APPARATUS BROKEN: no Go tree in $dest"; exit 2; }
}

# T134's exact probe. It is a MONEY path by construction — it takes minor units
# in and returns minor units — and it names none of the forbidden identifiers.
PROBE_SRC='package loanschedule

func t154InterestProbe(p int64) int64 { rate := 0.036 / 12.0; amt := rate * 1.0; return p + int64(amt) }
'
probe_path() { printf '%s/nexus/internal/apps/loanschedule/t154probe.go' "$1"; }
inject()   { printf '%s' "$PROBE_SRC" > "$(probe_path "$1")"; }
uninject() { rm -f "$(probe_path "$1")"; }

echo "=== [0] APPARATUS ==="
echo "pinned pre-fix sha : $PIN_PREFIX_SHA"
# T154_POST_REV exists ONLY so the RED transcript can be regenerated: set it to
# the pre-fix sha and the POST arm becomes the pre-fix bytes, reproducing the
# state this leg exists to end. Nothing in normal use sets it.
mktree "$PIN_PREFIX_SHA"        "$TMP/pre"
mktree "${T154_POST_REV:--}"    "$TMP/post"
echo "PRE  has nofloat.go : $( [ -f "$TMP/pre/nexus/internal/apps/loanschedule/conformance/nofloat.go" ] && echo yes || echo no )"
echo "POST has nofloat.go : $( [ -f "$TMP/post/nexus/internal/apps/loanschedule/conformance/nofloat.go" ] && echo yes || echo no )"
echo "the injected probe  :"
printf '%s' "$PROBE_SRC" | sed 's/^/    /'
echo "    -- forbidden identifiers in it: $(printf '%s' "$PROBE_SRC" | LC_ALL=C grep -acoE '\bfloat(32|64)\b|\bbig\.Float\b|\bcomplex(64|128)\b|\b(Parse|Format|Append)Float\b' || true)"
echo

gorun() { # gorun <tree> <label> -- <go args...>
  local tree="$1" label="$2"; shift 3
  ( . /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
    cd "$tree/nexus" && go "$@" ) > "$TMP/$label.txt" 2>&1
  printf '%s' "$?"
}
confrun() { # confrun <tree> <label>
  ( cd "$1" && bash .softhouse/conformance.sh ) > "$TMP/$2.txt" 2>&1
  printf '%s' "$?"
}

echo "=== [1] CONTROL — both trees clean, no probe ==="
for arm in pre post; do
  b="$(gorun "$TMP/$arm" "$arm-clean-build" -- build ./...)"
  g="$(gorun "$TMP/$arm" "$arm-clean-test"  -- test -run TestNoFloatInTheLoanScheduleTree ./internal/apps/loanschedule/conformance/)"
  c="$(confrun "$TMP/$arm" "$arm-clean-conf")"
  printf '  %-4s build=%s  no-float test=%s  conformance=%s\n' "$arm" "$b" "$g" "$c"
  [ "$b" = 0 ] && ok "$arm clean: go build 0"       || bad "$arm clean: go build $b, wanted 0"
  [ "$g" = 0 ] && ok "$arm clean: no-float test 0"  || bad "$arm clean: no-float test $g, wanted 0"
  [ "$c" = 0 ] && ok "$arm clean: conformance 0"    || bad "$arm clean: conformance $c, wanted 0"
done
echo

echo "=== [2] WITH THE FLOAT LITERAL INJECTED ==="
inject "$TMP/pre"; inject "$TMP/post"
pre_b="$(gorun "$TMP/pre" pre-probe-build -- build ./...)"
pre_g="$(gorun "$TMP/pre" pre-probe-test  -- test -run TestNoFloatInTheLoanScheduleTree ./internal/apps/loanschedule/conformance/)"
pre_c="$(confrun "$TMP/pre" pre-probe-conf)"
post_b="$(gorun "$TMP/post" post-probe-build -- build ./...)"
post_g="$(gorun "$TMP/post" post-probe-test  -- test -run TestNoFloatInTheLoanScheduleTree ./internal/apps/loanschedule/conformance/)"
post_c="$(confrun "$TMP/post" post-probe-conf)"
uninject "$TMP/pre"; uninject "$TMP/post"

printf '  %-4s build=%s  no-float test=%s  conformance=%s   (wanted 0 / 0 / 0 — all three green on a float)\n' pre  "$pre_b"  "$pre_g"  "$pre_c"
printf '  %-4s build=%s  no-float test=%s  conformance=%s   (wanted 0 / 1 / 2 — build still fine, guard RED, verdict RED)\n' post "$post_b" "$post_g" "$post_c"
echo
echo "  --- what the PRE-fix guard said about the injected float ---"
LC_ALL=C grep -aE 'PASS|FAIL|ok |scanned' "$TMP/pre-probe-test.txt" | sed 's/^/      /'
LC_ALL=C grep -aE 'FLOATING-POINT|floating-point|^VERDICT' "$TMP/pre-probe-conf.txt" | sed 's/^/      /'
echo "  --- what the POST-fix guard says ---"
LC_ALL=C grep -aE 'floating-point literal|FAIL' "$TMP/post-probe-test.txt" | head -4 | sed 's/^/      /'
LC_ALL=C grep -aE 'FLOATING POINT ON A MONEY PATH|no-float census|^VERDICT' "$TMP/post-probe-conf.txt" | head -6 | sed 's/^/      /'
echo

[ "$pre_b" = 0 ] && ok "PRE  probe: go build exit 0 — a float literal compiles, of course"           || bad "PRE  probe: go build $pre_b, wanted 0"
[ "$pre_g" = 0 ] && ok "PRE  probe: the no-float GUARD passed on a float — the finding"               || bad "PRE  probe: no-float test $pre_g, wanted 0"
[ "$pre_c" = 0 ] && ok "PRE  probe: conformance exit 0 on a float — the finding"                      || bad "PRE  probe: conformance $pre_c, wanted 0"
[ "$post_b" = 0 ] && ok "POST probe: go build exit 0 — the fix does not break the build"              || bad "POST probe: go build $post_b, wanted 0"
[ "$post_g" != 0 ] && ok "POST probe: the no-float guard FAILS (exit $post_g)"                        || bad "POST probe: the no-float guard still passed"
[ "$post_c" = 2 ] && ok "POST probe: conformance exit 2"                                              || bad "POST probe: conformance $post_c, wanted 2"
LC_ALL=C grep -aq 'floating-point literal "0.036"' "$TMP/post-probe-test.txt" \
  && ok "POST probe: the guard names the literal 0.036 and its file:line" \
  || bad "POST probe: the guard did not name 0.036"
LC_ALL=C grep -aq 'FLOATING POINT ON A MONEY PATH' "$TMP/post-probe-conf.txt" \
  && ok "POST probe: conformance names it as FLOATING POINT ON A MONEY PATH" \
  || bad "POST probe: conformance did not name it"
echo

echo "=== [3] THE GUARD SPEAKS WHEN IT IS HAPPY, TOO (P-35) ==="
echo "  A guard that reports only failures cannot be told apart from one that never ran."
LC_ALL=C grep -aA1 'no-float census' "$TMP/post-clean-conf.txt" | sed 's/^/      /'
LC_ALL=C grep -aq 'no-float census' "$TMP/post-clean-conf.txt" \
  && ok "POST clean conformance PRINTS the census (files, tokens, each violation count)" \
  || bad "POST clean conformance prints no census"
LC_ALL=C grep -aq 'no-float census' "$TMP/pre-clean-conf.txt" \
  && bad "PRE clean conformance already printed a census — then there was nothing to add" \
  || ok "PRE clean conformance printed NO census — the guard was silent whether or not it ran"
echo

echo "=== [4] THE REAL TREE WAS NEVER POISONED ==="
# Scoped to the probe, not to the whole tree: this script is expected to run
# while T154's own edits are still uncommitted, so "nexus is clean" is the wrong
# assertion and would fail for the right reason at the wrong time.
if [ -e "$(probe_path "$REPO_ROOT")" ]; then
  bad "the probe was left behind in the REAL tree: $(probe_path "$REPO_ROOT")"
else
  ok "no t154probe.go in the real tree — both arms ran in scratch trees"
fi
if ( cd "$REPO_ROOT" && git status --porcelain -- nexus ) | LC_ALL=C grep -aq 't154probe'; then
  bad "git status names t154probe in the real tree"
else
  ok "git status --porcelain -- nexus names no t154probe"
fi
echo
echo "======================================================================="
echo "LEG 2 ROWS: $pass as wanted, $fail not as wanted"
echo "======================================================================="
[ "$fail" -eq 0 ]
