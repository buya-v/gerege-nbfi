#!/usr/bin/env bash
# =============================================================================================
# T424, part 3 -- "AFTER YOU FIX EACH, LOOK FOR ITS NEIGHBOURS."
#
# Both defects T424 closed have the same shape: something that works on the case that was tried.
# This census looks for the neighbours of defect 2 -- OTHER places in this harness where a
# verdict is derived by reading a file that another process is still writing.
#
# THE SEARCH, stated so a reader can disagree with it rather than trust it:
#   S-A  every `| tee <target>` and `tee -a <target>` in a tracked .sh/.py under .softhouse/,
#        then: does the SAME FILE later read that target? That is T402's exact shape.
#   S-B  every background job (`... &`, excluding `&&`, `2>&1`, `>&2`), then: is there a `wait`
#        for it before the file it writes is read?
#   S-C  every read of a file whose writer is another process still running -- approximated by
#        `$(<file)`, `cat`, `grep`, `awk` over a path that a `&`-job or a `tee` writes.
#
# It PRINTS the denominator for each search. A census that reports "0 found" without saying how
# many it looked at is the fail-open it is hunting.
#
# EXIT: 0 always -- this is a CENSUS, not a gate. Its output is adjudicated by a human in the
# handoff. Saying so out loud because an instrument that returns a status nobody defined is how
# the next reader mistakes it for a guard.
# =============================================================================================
set -uo pipefail
REPO=${T424_REPO:-$(git rev-parse --show-toplevel)}
cd "$REPO" || exit 2

FILES=$(git ls-files '.softhouse/*.sh' '.softhouse/*.py'); _rc=$?
if [ "$_rc" -ge 2 ] || [ -z "$FILES" ]; then
  echo "REFUSED: could not enumerate the corpus (rc=$_rc). No denominator, no census." >&2
  exit 2
fi
N=$(printf '%s\n' "$FILES" | grep -c .)
echo "corpus: $N tracked .sh/.py files under .softhouse/"
echo

echo "=== S-A  scripts that TEE to a file and then READ THAT SAME FILE ==========="
hits=0; teefiles=0
while IFS= read -r f; do
  tgts=$(grep -oE 'tee (-a )?"[^"]+"' "$f" | sed 's/.*"\(.*\)"/\1/' | sort -u)
  [ -z "$tgts" ] && continue
  teefiles=$((teefiles+1))
  while IFS= read -r t; do
    [ -z "$t" ] && continue
    # the variable name, if the target is a variable
    v=$(printf '%s' "$t" | sed -n 's/^[$]{\{0,1\}\([A-Za-z_][A-Za-z_0-9]*\)}\{0,1\}$/\1/p')
    [ -z "$v" ] && continue
    if grep -nE "(grep|awk|sed|cat|wc|<)[^\n]*[\"']?[$]\{?$v\}?" "$f" | grep -vE 'tee ' | grep -q .; then
      echo "  HIT $f  (tees to \$$v and also reads it)"
      grep -nE "(grep|awk|sed|cat|wc)[^\n]*[$]\{?$v\}?" "$f" | grep -v 'tee ' | sed 's/^/        /' | head -4
      hits=$((hits+1))
    fi
  done <<EOF
$tgts
EOF
done <<EOF
$FILES
EOF
echo "  files containing a \`tee <file>\`: $teefiles ; of those, files that also read the target: $hits"
echo

echo "=== S-B  background jobs, and whether anything waits for them ============="
bg=0
while IFS= read -r f; do
  lines=$(grep -nE '[^&>|]&[[:space:]]*$' "$f" | grep -vE '&&|2>&1|>&2')
  [ -z "$lines" ] && continue
  w=$(grep -c -E '^[[:space:]]*(wait|wait_bounded)[[:space:]]' "$f")
  printf '  %s : %s background job line(s), %s wait/wait_bounded statement(s)\n' \
    "$f" "$(printf '%s\n' "$lines" | grep -c .)" "$w"
  printf '%s\n' "$lines" | sed 's/^/        /'
  bg=$((bg+1))
done <<EOF
$FILES
EOF
echo "  files with a background job: $bg"
echo

echo "=== S-D  SHIPPED PATCHES -- where the defect actually lived ==============="
# T402's instance was NOT in a tracked .sh at all: it was in an UNAPPLIED .patch. A census over
# executable files only would have reported a clean zero for the very defect it is hunting, so
# the patch corpus is searched too. This is the same mistake in miniature as the one this task
# is about: a corpus narrower than the defect class certifies only what the corpus could see.
PATCHES=$(git ls-files '.softhouse/*.patch'); _prc=$?
if [ "$_prc" -ge 2 ]; then
  echo "  REFUSED: could not enumerate the patch corpus (rc=$_prc)."
else
  PN=$(printf '%s\n' "$PATCHES" | grep -c .)
  echo "  corpus: $PN tracked .patch files under .softhouse/"
  ph=0
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    if grep -qE '^\+.*(tee |DRIVE_LOG)' "$p"; then
      echo "  HIT $p"
      grep -nE '^\+.*(tee |DRIVE_LOG)' "$p" | sed 's/^/        /' | head -6
      ph=$((ph+1))
    fi
  done <<EOF
$PATCHES
EOF
  echo "  patches whose ADDED lines mention a tee/transcript log: $ph"
fi
echo

echo "=== S-C  the harness's own bar: does conformance.sh have either shape? ===="
C=.softhouse/conformance.sh
printf '  %s : tee sites = %s ; background jobs = %s\n' "$C" \
  "$(grep -cE '\| *tee|tee -a' "$C")" \
  "$(grep -E '[^&>|]&[[:space:]]*$' "$C" | grep -vcE '&&|2>&1|>&2')"
echo
echo "T424-NEIGHBOUR-CENSUS: complete. Adjudication is in the handoff, by name."
exit 0
