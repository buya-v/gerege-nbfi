#!/usr/bin/env bash
# T154 LEG 1, END TO END — the whole harness, not just the guard's grep.
#
# drive-leg1.sh proves the GUARD goes blind. This proves what that BUYS an
# attacker: a `.json` carrying a float, planted at the STORE ROOT, takes the
# PRE-fix harness all the way to VERDICT: PASS (exit 0) with no diagnostic, and
# takes the POST-fix harness to exit 2 naming the file.
#
# WHY THE STORE ROOT AND NOT A CONTEXT DIRECTORY.  LoadStore reads only files
# INSIDE a context directory, one level down. A `.json` sitting at the store root
# is never decoded by Go, so RejectFloatTokens never sees it and the shell guard
# is the ONLY float check that covers it (T143's M-5). That makes the store root
# the place where the shell guard's blindness is not merely a redundancy loss but
# the whole check.
#
# BOTH ARMS RUN IN A SELF-CONSISTENT SCRATCH TREE built by `git archive` from a
# literal immutable sha (PRE) or copied from the working tree (POST). The
# COMMITTED store is never touched — no plant, no restore, nothing to leave
# behind if this script is killed.
#
# Run:  bash .softhouse/capture/t154-nofloat/drive-leg1-e2e.sh
# Exit: 0 = every cell as wanted. 1 = a cell disagreed. 2 = apparatus broken.
set -u -o pipefail

PIN_PREFIX_SHA=187e9726dfad5076f4b68877f411d7d218280889   # T154's fork point

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TMP="$(mktemp -d -t t154-leg1e2e)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ok()  { printf 'OK    %s\n' "$*"; pass=$((pass+1)); }
bad() { printf 'FAIL  %s\n' "$*"; fail=$((fail+1)); }

# The harness needs exactly these paths; copying the whole 135 MB capture tree
# would cost minutes and prove nothing extra.
PATHS=(.softhouse/conformance.sh .softhouse/bin .softhouse/vectors nexus)

mktree() { # mktree <rev|-> <dest>
  local rev="$1" dest="$2"
  mkdir -p "$dest"
  if [ "$rev" = "-" ]; then
    ( cd "$REPO_ROOT" && tar -cf - "${PATHS[@]}" ) | ( cd "$dest" && tar -xf - )
  else
    ( cd "$REPO_ROOT" && git archive "$rev" -- "${PATHS[@]}" ) | ( cd "$dest" && tar -xf - )
  fi
  # Every parity vector's provenance.capture_ref must resolve to a file in the
  # tree or the vector grades INADMISSIBLE — 0 parity, 25 cells, exit 2, on a
  # tree with nothing whatever wrong with its guards. That is a NULL CONTROL
  # (P-36) wearing the costume of a result, and it is why section [1] below runs
  # the clean control first and refuses to go on if it is not exit 0.
  # The capture tree is 135 MB of append-only evidence; it is symlinked, not
  # copied, and it is only ever stat'ed and read.
  ln -s "$REPO_ROOT/.softhouse/capture" "$dest/.softhouse/capture"
  [ -f "$dest/.softhouse/conformance.sh" ] || { echo "APPARATUS BROKEN: no conformance.sh in $dest"; exit 2; }
  [ -d "$dest/.softhouse/vectors/loanschedule" ] || { echo "APPARATUS BROKEN: no store in $dest"; exit 2; }
}

echo "=== [0] APPARATUS ==="
echo "pinned pre-fix sha : $PIN_PREFIX_SHA"
echo "pre-fix subject    : $(cd "$REPO_ROOT" && git log -1 --format=%s "$PIN_PREFIX_SHA")"
mktree "$PIN_PREFIX_SHA" "$TMP/pre"
mktree "-"               "$TMP/post"
echo "PRE  guard line    : $(sed -n '/^guard_no_float_in_vectors()/,/^}/p' "$TMP/pre/.softhouse/conformance.sh"  | sed -n '/grep/p' | sed 's/^ *//')"
echo "POST guard line    : $(sed -n '/^guard_no_float_in_vectors()/,/^}/p' "$TMP/post/.softhouse/conformance.sh" | sed -n '/grep/p' | sed 's/^ *//')"
echo "ANTI-NO-OP         : the two lines above must DIFFER, or this script compares a fix with itself"
if [ "$(sed -n '/^guard_no_float_in_vectors()/,/^}/p' "$TMP/pre/.softhouse/conformance.sh" | sed -n '/grep/p')" \
   = "$(sed -n '/^guard_no_float_in_vectors()/,/^}/p' "$TMP/post/.softhouse/conformance.sh" | sed -n '/grep/p')" ]; then
  echo "  -> IDENTICAL. The fix is not in the working tree yet; every POST row below is a RED row."
else
  echo "  -> DIFFER."
fi
echo

# The poison: a lone 0xE2 (a truncated UTF-8 lead byte) OUTSIDE any string,
# immediately before a float, on the same line.
plant() { printf '{\n  "case_id": "T154-POISON",\n  \xe2 "rate_pct": 3.6\n}\n' > "$1/.softhouse/vectors/T154-POISON-store-root.json"; }
unplant() { rm -f "$1/.softhouse/vectors/T154-POISON-store-root.json"; }

run() { # run <tree> <label>  -> prints exit code; full output to $TMP/<label>.txt
  ( cd "$1" && bash .softhouse/conformance.sh ) > "$TMP/$2.txt" 2>&1
  printf '%s' "$?"
}

report() { # report <label>
  echo "--- $1 ---"
  grep -E 'probe =|FLOAT-SHAPED NUMBER|HARD guard failed|parity vectors|cells compared|^VERDICT' "$TMP/$1.txt" \
    | sed 's/^/    /'
}

echo "=== [1] CONTROL — both trees clean, no poison ==="
rc_pre_clean="$(run "$TMP/pre" pre-clean)";   report pre-clean
rc_post_clean="$(run "$TMP/post" post-clean)"; report post-clean
[ "$rc_pre_clean"  = 0 ] && ok "PRE  clean  exit 0"  || bad "PRE  clean  exit $rc_pre_clean, wanted 0"
[ "$rc_post_clean" = 0 ] && ok "POST clean  exit 0"  || bad "POST clean  exit $rc_post_clean, wanted 0"
if [ "$rc_pre_clean" != 0 ]; then
  echo "APPARATUS BROKEN: the PRE tree does not grade clean, so 'the poison did not"
  echo "                  change the verdict' would mean nothing. Aborting rather than"
  echo "                  printing a coherent table over a broken rig (P-36)."
  exit 2
fi
echo

echo "=== [2] THE DEFEAT — one .json at the store root, float + one invalid byte ==="
plant "$TMP/pre"; plant "$TMP/post"
od -c "$TMP/pre/.softhouse/vectors/T154-POISON-store-root.json"
rc_pre="$(run "$TMP/pre" pre-poisoned)";   report pre-poisoned
rc_post="$(run "$TMP/post" post-poisoned)"; report post-poisoned
unplant "$TMP/pre"; unplant "$TMP/post"

[ "$rc_pre" = 0 ] \
  && ok "PRE  poisoned exit 0 — SILENT PASS ON A FLOAT, which is the finding" \
  || bad "PRE  poisoned exit $rc_pre, wanted 0 (the pre-fix harness is supposed to be blind here)"
grep -q 'FLOAT-SHAPED NUMBER' "$TMP/pre-poisoned.txt" \
  && bad "PRE  poisoned named the float — then there was nothing to fix" \
  || ok "PRE  poisoned printed NO 'FLOAT-SHAPED NUMBER' line anywhere"
[ "$rc_post" = 2 ] \
  && ok "POST poisoned exit 2" \
  || bad "POST poisoned exit $rc_post, wanted 2"
grep -q 'FLOAT-SHAPED NUMBER in .*T154-POISON-store-root.json' "$TMP/post-poisoned.txt" \
  && ok "POST poisoned names the file: $(grep -h 'FLOAT-SHAPED NUMBER' "$TMP/post-poisoned.txt" | head -1)" \
  || bad "POST poisoned did not name T154-POISON-store-root.json"
echo

echo "=== [3] THE COMMITTED STORE WAS NEVER TOUCHED ==="
dirty="$( cd "$REPO_ROOT" && git status --porcelain -- .softhouse/vectors )"
[ -z "$dirty" ] && ok "git status --porcelain -- .softhouse/vectors is EMPTY" \
                || bad "the committed store is dirty:
$dirty"
echo

echo "======================================================================="
echo "LEG 1 E2E: $pass as wanted, $fail not as wanted"
echo "======================================================================="
[ "$fail" -eq 0 ]
