#!/bin/bash
# T155 probe (iv) — is ZERO FILES INSPECTED an ERROR, in BOTH guards?
# and probe (M-5 corollary) — is the allowlist really covered by RejectFloatTokens?
#
# The two shell guard FUNCTIONS are lifted whole from IMMUTABLE git blobs by
# anchored awk (never sed ranges — a sed range will not close on the line that
# opened it, which is how T154's own first extractor silently turned every row
# into a null control). The blob shas are asserted. Positive and negative
# controls are run through the SAME lifted function, so a bad lift shows up as a
# wrong control rather than a plausible table.
set -u
REPO="${REPO:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0e4fbacb5cf6d93f}"
PRE_SHA=187e9726dfad5076f4b68877f411d7d218280889
PRE_BLOB_SHA=11d3729eedee3ee70d4d95a0f0f93d4a9850412244e621c7cfab67610d198853
POST_BLOB_SHA=a55d7f5270a3933bcf3e0c6986a217971e621f65f0de723fca9f803d3aed27a7
T=/tmp/t155
cd "$REPO" || exit 9
[ "$(git show "$PRE_SHA:.softhouse/conformance.sh" | shasum -a 256 | cut -d' ' -f1)" = "$PRE_BLOB_SHA" ] || { echo "REFUSE: pre blob drifted"; exit 9; }
[ "$(git show softhouse/T154-nofloat-guards:.softhouse/conformance.sh | shasum -a 256 | cut -d' ' -f1)" = "$POST_BLOB_SHA" ] || { echo "REFUSE: post blob drifted"; exit 9; }
git show "$PRE_SHA:.softhouse/conformance.sh"                        > "$T/pre.sh"
git show softhouse/T154-nofloat-guards:.softhouse/conformance.sh     > "$T/post.sh"

lift() { # $1 file, $2 function name  -> the whole function, anchored, awk not sed
  awk -v fn="$2" '
    $0 ~ "^"fn"\\(\\) \\{" {inside=1}
    inside {print}
    inside && $0 == "}" {exit}
  ' "$1"
}

mkharness() { # $1 srcfile, $2 outfile
  {
    echo '#!/bin/bash'
    echo 'set -u -o pipefail'
    echo 'STORE_ROOT="$1"; NEXUS_DIR="$2"'
    echo 'say()  { printf "%s\n" "$*"; }'
    echo 'warn() { printf "%s\n" "$*" >&2; }'
    lift "$1" guard_no_float_in_vectors
    lift "$1" guard_no_float_in_harness
    echo 'guard_no_float_in_vectors; rcv=$?'
    echo 'guard_no_float_in_harness; rch=$?'
    echo 'echo "RC vectors=$rcv harness=$rch"'
  } > "$2"
  # anti-vacuity: the lift must actually contain the loop and the closing return
  LC_ALL=C grep -aq 'find "\$STORE_ROOT"' "$2" || { echo "REFUSE: vectors lift is incomplete"; exit 9; }
  LC_ALL=C grep -aq 'loanschedule' "$2"        || { echo "REFUSE: harness lift is incomplete"; exit 9; }
}
mkharness "$T/pre.sh"  "$T/guards-pre.sh"
mkharness "$T/post.sh" "$T/guards-post.sh"
echo "lifted guard functions: $(wc -l < "$T/guards-pre.sh") lines PRE, $(wc -l < "$T/guards-post.sh") lines POST"
echo

# --- fixture trees ---------------------------------------------------------
rm -rf "$T/zero"; mkdir -p "$T/zero/emptystore" "$T/zero/emptygo/internal/apps/loanschedule"
mkdir -p "$T/zero/goodstore" "$T/zero/goodgo/internal/apps/loanschedule"
printf '{ "amount": "1250000" }\n'                 > "$T/zero/goodstore/ok.json"
printf 'package x\n\nfunc A() { var v int64; _ = v }\n' > "$T/zero/goodgo/internal/apps/loanschedule/ok.go"
mkdir -p "$T/zero/badstore" "$T/zero/badgo/internal/apps/loanschedule"
printf '{ "rate": 3.6 }\n'                         > "$T/zero/badstore/bad.json"
printf 'package x\n\nfunc A() { var v float64; _ = v }\n' > "$T/zero/badgo/internal/apps/loanschedule/bad.go"

FAILS=0
row() { # 1 label 2 store 3 go 4 want_pre 5 want_post
  local pre post out mark=""
  out="$(bash "$T/guards-pre.sh"  "$2" "$3" 2>&1)"; pre="$(printf '%s' "$out" | tail -1)"
  out="$(bash "$T/guards-post.sh" "$2" "$3" 2>&1)"; post="$(printf '%s' "$out" | tail -1)"
  [ "$pre"  = "$4" ] || { mark="$mark  !!PRE-wanted[$4]";  FAILS=$((FAILS+1)); }
  [ "$post" = "$5" ] || { mark="$mark  !!POST-wanted[$5]"; FAILS=$((FAILS+1)); }
  printf '%-30s PRE{%s}  POST{%s}%s\n' "$1" "$pre" "$post" "$mark"
}
echo "0 = guard returned success.  1 = guard refused."
echo
row "POSITIVE CONTROL (both bad)"  "$T/zero/badstore"   "$T/zero/badgo"   "RC vectors=1 harness=1" "RC vectors=1 harness=1"
row "NEGATIVE CONTROL (both good)" "$T/zero/goodstore"  "$T/zero/goodgo"  "RC vectors=0 harness=0" "RC vectors=0 harness=0"
row "ZERO INPUT (both empty)"      "$T/zero/emptystore" "$T/zero/emptygo" "RC vectors=0 harness=0" "RC vectors=1 harness=1"
row "ZERO store only"              "$T/zero/emptystore" "$T/zero/goodgo"  "RC vectors=0 harness=0" "RC vectors=1 harness=0"
row "ZERO go tree only"            "$T/zero/goodstore"  "$T/zero/emptygo" "RC vectors=0 harness=0" "RC vectors=0 harness=1"
echo
echo "the POST wording on zero input:"
bash "$T/guards-post.sh" "$T/zero/emptystore" "$T/zero/emptygo" 2>&1 | sed 's/^/    /'
echo
echo "rows disagreeing with T155's own expectation: $FAILS"

# --- HAZARD: does the P-35 counter reflect files actually SCANNED? ----------
# The counter increments once per file ENUMERATED by find, before perl runs. If
# perl is unavailable the pipeline yields nothing, `set -o pipefail` makes the
# `if` false, and the guard reports "inspected N files" and returns 0 — on a
# store that contains a real, plainly visible float.
echo
echo "=== HAZARD PROBE: guard behaviour when perl cannot run ==="
mkdir -p "$T/zero/noperl"
printf '#!/bin/sh\nexit 127\n' > "$T/zero/noperl/perl"; chmod +x "$T/zero/noperl/perl"
echo "-- POST guards over a store holding a PLAIN float, with perl replaced by exit-127 --"
PATH="$T/zero/noperl:$PATH" bash "$T/guards-post.sh" "$T/zero/badstore" "$T/zero/badgo" 2>&1 | sed 's/^/    /'
echo "   (wanted: a refusal. 'RC vectors=0 harness=0' here is a VACUOUS PASS ON A FLOAT.)"
[ "$FAILS" -eq 0 ] || exit 1
