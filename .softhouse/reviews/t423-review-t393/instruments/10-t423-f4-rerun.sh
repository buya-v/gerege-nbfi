#!/bin/bash
# T423 — INDEPENDENT re-run of T393's F-4 arms, and of the disclosed residual.
#
# This is NOT `10-drive-conditions.sh` re-invoked. It is a second driver: it picks its own
# mutation target with its own selector, applies the one-line constant move with its own
# matcher, and reads the result columns with its own parsers. If T393's driver and this one
# disagree about any row, one of them is wrong and the disagreement is the finding.
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298). Every location is a required parameter.
#
#   T423_SRC=<repo at T393's tip>  T423_CLONE=<scratch OUTSIDE the repo>  T423_OUT=<dir> \
#   T423_BEFORE=<pre-fix sha>  T423_AFTER=<post-fix sha>  bash 10-t423-f4-rerun.sh
#
# EXIT 0 every case produced the expected section-10 code at both refs.
# EXIT 1 at least one did not, named.
# EXIT 3 the harness could not run. Never read as a result.
set -u

SRC="${T423_SRC:?T423_SRC must name the source repository}"
SCROOT="${T423_CLONE:?T423_CLONE must name a scratch directory OUTSIDE the repository}"
OUT="${T423_OUT:?T423_OUT must name the directory to write transcripts into}"
BEFORE="${T423_BEFORE:?T423_BEFORE must name the commit-ish carrying the PRE-fix bytes}"
AFTER="${T423_AFTER:?T423_AFTER must name the commit-ish carrying the POST-fix bytes}"

CAP=".softhouse/capture/tierA-a2"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
RUNALL=".softhouse/reviews/A2-11/run-all.sh"
MAN="$CAP/MANIFEST.sha256"
FORK="12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"

mkdir -p "$OUT" "$SCROOT" || exit 3
MATRIX="$OUT/T423-MATRIX.tsv"
: > "$MATRIX" || exit 3
printf 'case\tref\tsec10\trunall_rc\tverdict\tsec4_named\tarmA_pop\texpected\tresult\n' >> "$MATRIX"

# --- my own target selection, by measurement. Sorted-first of each set; refuse on empty.
FORKOBS="$(git -C "$SRC" ls-tree -r --name-only "$FORK" -- "$CAP/out" "$CAP/req" \
           | sed "s|^$CAP/||" | LC_ALL=C sort | head -1)"
POSTFORK="$(comm -13 \
             <(git -C "$SRC" ls-tree -r --name-only "$FORK" -- "$CAP/out" "$CAP/req" | sed "s|^$CAP/||" | LC_ALL=C sort) \
             <(git -C "$SRC" ls-tree -r --name-only HEAD    -- "$CAP/out" "$CAP/req" | sed "s|^$CAP/||" | LC_ALL=C sort) \
           | head -1)"
if [ -z "$FORKOBS" ] || [ -z "$POSTFORK" ]; then
  echo "REFUSED: empty target set [$FORKOBS] [$POSTFORK]" >&2; exit 3
fi
echo "T423 targets (my own selector): FORKOBS=$FORKOBS  POSTFORK=$POSTFORK"

FAILURES=0

prepare() {   # prepare <dir> <ref>
  local d="$1" ref="$2"
  rm -rf "$d" || return 1
  git clone --quiet --shared "$SRC" "$d" || return 1
  git -C "$d" config user.email "t423@softhouse.local" || return 1
  git -C "$d" config user.name "T423" || return 1
  git -C "$d" checkout --quiet --detach "$ref" || return 1
  git -C "$d" reset --quiet --hard "$ref" || return 1
}

# --- mutations, mine.
mut_f4a() {   # commit a mutation of a FORK-SHA observation. ARM A must catch this at BOTH refs.
  printf '\nT423-MUTATION-MARKER\n' >> "$1/$CAP/$FORKOBS" || return 1
  git -C "$1" add -- "$CAP/$FORKOBS" || return 1
  git -C "$1" commit -q -m "T423 probe: committed mutation of a FORK-SHA observation" || return 1
}

mut_f4b() {   # the same, then move section 10's OWN baseline constant onto the probe commit.
  mut_f4a "$1" || return 1
  local probe n
  probe="$(git -C "$1" rev-parse HEAD)" || return 1
  n="$(grep -c -E '^FORK = "[0-9a-f]{40}"$' "$1/$INT")"
  if [ "$n" != "1" ]; then
    echo "REFUSED: $n FORK assignments in $1/$INT, expected exactly 1" >&2; return 1
  fi
  # one line, in place, with my own matcher
  perl -pi -e "s/^FORK = \"[0-9a-f]{40}\"\$/FORK = \"$probe\"/" "$1/$INT" || return 1
  grep -q -E "^FORK = \"$probe\"\$" "$1/$INT" || return 1
  echo "      FORK moved to the probe commit $probe (one line)"
}

mut_residual() {   # T393's DISCLOSED RESIDUAL: committed mutation of a POST-FORK observation
                   # whose MANIFEST row is rewritten in the SAME commit. Laundering done by
                   # my own shasum call, not T393's relaunder script.
  local f="$1/$CAP/$POSTFORK" newhash
  printf '\nT423-RESIDUAL-MARKER\n' >> "$f" || return 1
  newhash="$(shasum -a 256 "$f" | awk '{print $1}')" || return 1
  perl -pi -e "s|^[0-9a-f]{64}(\s+\*?\Q$POSTFORK\E)\$|$newhash\$1|" "$1/$MAN" || return 1
  grep -q -E "^$newhash" "$1/$MAN" || { echo "REFUSED: manifest row not laundered" >&2; return 1; }
  git -C "$1" add -- "$CAP/$POSTFORK" "$MAN" || return 1
  git -C "$1" commit -q -m "T423 probe: post-fork mutation with its manifest row rewritten in the same commit" || return 1
}

run_case() {   # run_case <name> <mutfn> <expect_before> <expect_after>
  local name="$1" mutfn="$2" eb="$3" ea="$4" ref tag d rc sec10 verdict named pop expect result
  for ref in BEFORE AFTER; do
    if [ "$ref" = "BEFORE" ]; then tag="$BEFORE"; d="$SCROOT/before"; else tag="$AFTER"; d="$SCROOT/after"; fi
    prepare "$d" "$tag" || { echo "REFUSED: could not prepare $d at $tag" >&2; exit 3; }
    echo "--- $name @ $ref ($tag)"
    "$mutfn" "$d" || { echo "REFUSED: mutation $mutfn did not apply in $d" >&2; exit 3; }
    ( cd "$d" && bash "$RUNALL" ) > "$OUT/T423-case-$name-$ref.txt" 2>&1
    rc=$?
    sec10="$(awk '/^  10 /{print $3}' "$OUT/T423-case-$name-$ref.txt" | tail -1)"; : "${sec10:=none}"
    verdict="$(sed -n 's/.*RUN-ALL VERDICT: \([A-Z]*\).*/\1/p' "$OUT/T423-case-$name-$ref.txt" | tail -1)"; : "${verdict:=none}"
    # section 4's OWN output line, anchored, so section 10's banner quoting the defect is not counted
    named="$(grep -c -E -- "^ +DIFF ${FORKOBS}\$" "$OUT/T423-case-$name-$ref.txt")"
    # ARM A's reported population -- the number that collapses 403 -> 1035 in the F-4 defect
    pop="$(sed -n 's/^ *at the fork sha *: \([0-9]*\) observations.*/\1/p' "$OUT/T423-case-$name-$ref.txt" | tail -1)"; : "${pop:=none}"
    if [ "$ref" = "BEFORE" ]; then expect="$eb"; else expect="$ea"; fi
    if [ "$sec10" = "$expect" ]; then result="as expected"; else result="*** UNEXPECTED ***"; FAILURES=$((FAILURES+1)); fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$name" "$ref" "$sec10" "$rc" "$verdict" "$named" "$pop" "$expect" "$result" >> "$MATRIX"
    echo "      section10=$sec10 rc=$rc verdict=$verdict sec4-named=$named armA-pop=$pop expected=$expect $result"
  done
}

echo "############ T423 INDEPENDENT RE-RUN"
echo "BEFORE = $BEFORE"
echo "AFTER  = $AFTER"
echo

run_case t423-f4a-control-mutate-forkobs  mut_f4a       1 1
run_case t423-f4b-move-fork-constant      mut_f4b       0 2
run_case t423-residual-postfork-laundered mut_residual  0 0

echo
echo "############ T423 MATRIX"
cat "$MATRIX"
echo
echo "unexpected results: $FAILURES"
if [ "$FAILURES" -ne 0 ]; then
  echo "T423 DRIVE VERDICT: FAIL"; exit 1
fi
echo "T423 DRIVE VERDICT: PASS"
exit 0
