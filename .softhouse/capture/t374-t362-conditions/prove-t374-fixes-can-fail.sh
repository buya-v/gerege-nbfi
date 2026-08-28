#!/bin/bash
# T374 — drive every fix in this branch RED, the way T362 drove the defects RED: on REAL
# captured bytes, in a SCRATCH CLONE, never in the tree. P-22: a guard you have not seen
# fail is not a guard.
#
#   bash .softhouse/capture/t374-t362-conditions/prove-t374-fixes-can-fail.sh
#
# It exits 0 only if EVERY drive produced the expected non-zero verdict AND the clean
# baseline is still green — a prover that always says "caught it" is the defect it is
# checking for, so the GREEN direction is asserted too.
#
# NOTHING IN THE WORKING TREE IS MUTATED. Every mutation happens inside a throwaway clone
# under $TMPDIR, which is removed at the end. The tree's own captured observations are
# never written to.
#
# No oracle is contacted: every check here replays committed bytes. (T367's standing fact —
# a 4xx BURNS the idempotency key, so a refused probe is as irreversible as an accepted one
# — is why this prover is entirely offline.)
set -u
SRC="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRATCH="$(mktemp -d -t t374-prove)"
OUT="$(dirname "$0")/out"
mkdir -p "$OUT"
PASS=0
FAIL=0

cleanup() { rm -rf "$SCRATCH"; }
trap cleanup EXIT

want() {   # want <label> <expected-rc> <actual-rc>
  if [ "$2" = "$3" ]; then
    printf '  PASS  %-72s rc=%s\n' "$1" "$3"; PASS=$((PASS + 1))
  else
    printf '  FAIL  %-72s rc=%s (wanted %s)\n' "$1" "$3" "$2"; FAIL=$((FAIL + 1))
  fi
}
grep_want() {  # grep_want <label> <FIXED STRING> <file>
  if grep -Fq -- "$2" "$3"; then
    printf '  PASS  %-72s\n' "$1"; PASS=$((PASS + 1))
  else
    printf '  FAIL  %-72s (pattern %s absent from %s)\n' "$1" "$2" "$3"; FAIL=$((FAIL + 1))
  fi
}
grep_want_re() {  # grep_want_re <label> <ERE> <file>
  if grep -Eq -- "$2" "$3"; then
    printf '  PASS  %-72s\n' "$1"; PASS=$((PASS + 1))
  else
    printf '  FAIL  %-72s (regex %s absent from %s)\n' "$1" "$2" "$3"; FAIL=$((FAIL + 1))
  fi
}
grep_absent() {
  if grep -Fq -- "$2" "$3"; then
    printf '  FAIL  %-72s (pattern %s PRESENT in %s)\n' "$1" "$2" "$3"; FAIL=$((FAIL + 1))
  else
    printf '  PASS  %-72s\n' "$1"; PASS=$((PASS + 1))
  fi
}

echo "############ T374 — driving the T362 conditions RED, in a scratch clone"
echo "source tree : $SRC"
echo "scratch     : $SCRATCH"
date -u +"generated %Y-%m-%dT%H:%M:%SZ"
echo
echo 'The scratch is a real git clone, which means it has NO local branch refs -- only'
echo "origin/*. That is exactly the fresh-clone condition of T362's F-6, so case 0 measures"
echo "F-6 on the same population as the fix."
echo

git clone -q "$SRC" "$SCRATCH/repo" || { echo "CLONE FAILED"; exit 1; }
R="$SCRATCH/repo"
OBS="$R/.softhouse/capture/tierA-a2/out/A2-000-glaccounts-preexisting.http"

echo "=== case 0 (F-6) — GREEN: a FRESH CLONE with NO local ref now completes ==="
echo "    BEFORE T374 this exited 1: sections 4 and 5 named the LOCAL branch"
echo "    softhouse/A2-7-capture-mandatory-accounts, which a clone does not have, and both"
echo "    aborted with 'returned non-zero exit status 128'. Measured, not assumed:"
echo "    out/10-F6-RED-fresh-clone-no-local-ref.txt. The repair is the LITERAL sha"
echo "    b3f2d9b2..., which is reachable from origin/main and therefore survives a clone."
( cd "$R" && git branch --list 'softhouse/A2-7-capture-mandatory-accounts' ) > "$SCRATCH/localref.txt"
if [ -s "$SCRATCH/localref.txt" ]; then
  echo "  SKIP  the scratch unexpectedly HAS the local ref; case 0 would not be a fresh-clone test"
  FAIL=$((FAIL + 1))
else
  echo "    confirmed: the scratch clone has NO local softhouse/A2-7-capture-mandatory-accounts"
fi
( cd "$R" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$SCRATCH/c0.txt" 2>&1
want "(0) run-all.sh in a fresh clone, no local ref" 0 "$?"
grep_want "(0) 10 sections recorded, 0 deviations" "sections run: 10    deviations: 0" "$SCRATCH/c0.txt"
grep_absent "(0) no 'exit status 128' anywhere in the transcript" "exit status 128" "$SCRATCH/c0.txt"
cp "$SCRATCH/c0.txt" "$OUT/30-case0-F6-fresh-clone-GREEN.txt"
( cd "$R" && git checkout -q -- .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt )
echo

echo "=== case 1 (F-1) — RED: a MUTATED captured oracle observation ==="
echo "    The SAME mutation T362 used: one line appended to"
echo "    out/A2-000-glaccounts-preexisting.http. Before T374, section 4 detected it,"
echo "    printed DIFF for it BY NAME, and run-all.sh STILL exited 0 printing PASS"
echo "    (out/11-F1-RED-mutated-observation-absorbed.txt). It must now be fatal."
printf '\nT374-PROVER-MUTATION-MARKER\n' >> "$OBS"
( cd "$R" && python3 .softhouse/reviews/A2-11/verify-capture-integrity.py ) > "$SCRATCH/c1a.txt" 2>&1
want "(1a) verify-capture-integrity.py on a mutated observation" 1 "$?"
grep_want "(1a) it names the mutated file" "MUTATED .softhouse/capture/tierA-a2/out/A2-000-glaccounts-preexisting.http" "$SCRATCH/c1a.txt"
grep_want "(1a) both arms catch it (fork-sha arm and HEAD arm)" "differ=1" "$SCRATCH/c1a.txt"
( cd "$R" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$SCRATCH/c1b.txt" 2>&1
want "(1b) run-all.sh AGGREGATE now fails on a mutated observation" 1 "$?"
grep_want_re "(1b) section 10 is the one that MOVED" "^  10 +0 +1 +\\*\\*\\* MOVED \\*\\*\\*" "$SCRATCH/c1b.txt"
grep_want "(1b) RUN-ALL VERDICT is FAIL, not PASS" "RUN-ALL VERDICT: FAIL" "$SCRATCH/c1b.txt"
grep_want_re "(1b) section 4 is STILL as adjudicated -- the drift arm was not disturbed" "^  4 +1 +1 +as adjudicated" "$SCRATCH/c1b.txt"
cp "$SCRATCH/c1b.txt" "$OUT/31-case1-F1-mutated-observation-now-FATAL.txt"
( cd "$R" && git checkout -q -- .softhouse/capture/tierA-a2/out/A2-000-glaccounts-preexisting.http .softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt )
echo

echo "=== case 2 (F-1) — RED: a DELETED captured oracle observation ==="
echo "    Deletion is the other way evidence rots, and a comparator that only diffs"
echo "    existing files would report 'all identical' over a shrinking population."
rm -f "$OBS"
( cd "$R" && python3 .softhouse/reviews/A2-11/verify-capture-integrity.py ) > "$SCRATCH/c2.txt" 2>&1
want "(2) verify-capture-integrity.py on a DELETED observation" 1 "$?"
grep_want "(2) it names the missing file" "MISSING .softhouse/capture/tierA-a2/out/A2-000-glaccounts-preexisting.http" "$SCRATCH/c2.txt"
cp "$SCRATCH/c2.txt" "$OUT/32-case2-F1-deleted-observation.txt"
( cd "$R" && git checkout -q -- .softhouse/capture/tierA-a2/out/A2-000-glaccounts-preexisting.http )
echo

echo "=== case 3 (F-1 / F-2 class) — REFUSED: an EMPTY observation population ==="
echo "    Committing away out/ and req/ leaves nothing to compare. 'Zero differences over"
echo "    zero files' is a SELECTOR failure, not a clean corpus. It must REFUSE (exit 2),"
echo "    never pass, and the refusal must move section 10 too."
( cd "$R" && git rm -r -q .softhouse/capture/tierA-a2/out .softhouse/capture/tierA-a2/req \
   && git -c user.email=t374@local -c user.name=T374 commit -q -m "scratch: delete the observation corpus" )
( cd "$R" && python3 .softhouse/reviews/A2-11/verify-capture-integrity.py ) > "$SCRATCH/c3.txt" 2>&1
want "(3) verify-capture-integrity.py on an EMPTY population" 2 "$?"
grep_want "(3) it REFUSES rather than passing" "REFUSED" "$SCRATCH/c3.txt"
grep_want "(3) the verdict line says REFUSED, not PASS" "VERDICT: REFUSED (exit 2)" "$SCRATCH/c3.txt"
cp "$SCRATCH/c3.txt" "$OUT/33-case3-empty-population-REFUSED.txt"
( cd "$R" && git reset -q --hard HEAD~1 )
echo

echo "=== case 4 (F-6) — REFUSED: the baseline commit-ish is ABSENT ==="
echo "    A2_11_ROOT is pointed at a git repo that has neither the fork sha nor A2-7's head."
echo "    Every arm below then has nothing to measure against, and each script must say so"
echo "    by name instead of aborting on a traceback or reporting an empty clean run."
mkdir -p "$SCRATCH/bare/.softhouse/capture/tierA-a2"
( cd "$SCRATCH/bare" && git init -q . && git -c user.email=t374@local -c user.name=T374 \
    commit -q --allow-empty -m "empty" )
( cd "$R" && A2_11_ROOT="$SCRATCH/bare" python3 .softhouse/reviews/A2-11/verify-capture-integrity.py ) > "$SCRATCH/c4a.txt" 2>&1
want "(4a) verify-capture-integrity.py with no baseline" 2 "$?"
grep_want "(4a) the missing baseline is named" "is not present in this repository" "$SCRATCH/c4a.txt"
( cd "$R" && A2_11_ROOT="$SCRATCH/bare" python3 .softhouse/reviews/A2-11/audit-float.py ) > "$SCRATCH/c4b.txt" 2>&1
want "(4b) audit-float.py with no A2-7 head REFUSES instead of auditing 0 files" 2 "$?"
grep_want "(4b) it says REFUSED and explains the vacuous-pass shape" "vacuous pass" "$SCRATCH/c4b.txt"
cp "$SCRATCH/c4a.txt" "$OUT/34-case4a-missing-baseline-REFUSED.txt"
cp "$SCRATCH/c4b.txt" "$OUT/34-case4b-auditfloat-missing-head-REFUSED.txt"
echo

echo "=== case 5 (F-2) — RED: the vector store hidden, the corpus guard must REFUSE ==="
echo "    T362 measured the shipped behaviour: population 0, 'all zero', PASS, rc=0"
echo "    (out/12-F2-RED-vacuous-pass-empty-vector-store.txt)."
mv "$R/.softhouse/vectors" "$SCRATCH/vectors-hidden"
( cd "$R" && python3 .softhouse/reviews/A2-11/adjudicate-section1.py ) > "$SCRATCH/c5.txt" 2>&1
want "(5) adjudicate-section1.py with an EMPTY vector store" 1 "$?"
grep_want "(5) the empty population is REFUSED by name" "FAIL  POSITIVE CONTROL — the vector store was actually READ" "$SCRATCH/c5.txt"
grep_want "(5) the provenance-ref enumeration refuses too" "FAIL  POSITIVE CONTROL — provenance refs were actually ENUMERATED" "$SCRATCH/c5.txt"
cp "$SCRATCH/c5.txt" "$OUT/35-case5-F2-empty-vector-store-REFUSED.txt"
mv "$SCRATCH/vectors-hidden" "$R/.softhouse/vectors"
echo

echo "=== case 6 (F-3) — the (a) control no longer prints a FALSE message under a 4th failure ==="
echo "    T362 saw 'NEGATIVE CONTROL DID NOT TRIP: (a) ...' while driving a genuine fourth"
echo "    failure — the control had tripped HARDER than expected, and said the opposite."
python3 - "$R" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1]) / ".softhouse/reviews/A2-11/obs/a2-11-get-glaccount-2.json"
d = json.loads(p.read_text())
d["name"] = "T374 PROVER MUTATION"
p.write_text(json.dumps(d))
PY
( cd "$R" && python3 .softhouse/reviews/A2-11/adjudicate-section1.py ) > "$SCRATCH/c6.txt" 2>&1
want "(6) adjudicate-section1.py still RED on a genuine fourth failure" 1 "$?"
grep_want "(6) the fourth failure is reported as UNADJUDICATED" "FAIL  NO UNADJUDICATED FAILURE" "$SCRATCH/c6.txt"
grep_absent "(6) and control (a) does NOT falsely claim it did not trip" "NEGATIVE CONTROL DID NOT TRIP" "$SCRATCH/c6.txt"
cp "$SCRATCH/c6.txt" "$OUT/36-case6-F3-fixed-synthetic-base.txt"
( cd "$R" && git checkout -q -- .softhouse/reviews/A2-11/obs/a2-11-get-glaccount-2.json )
echo

echo "=== case 7 — GREEN AGAIN: the scratch is byte-clean and the whole review reproduces ==="
echo "    A prover that only ever produces RED is as useless as one that only produces GREEN."
( cd "$R" && git checkout -q -- . )
( cd "$R" && git status --porcelain ) > "$SCRATCH/c7-status.txt"
if [ -s "$SCRATCH/c7-status.txt" ]; then
  echo "  FAIL  (7) scratch tree NOT clean after all mutations were reverted:"
  cat "$SCRATCH/c7-status.txt"
  FAIL=$((FAIL + 1))
else
  printf '  PASS  %-72s\n' "(7) every mutation reverted; scratch tree byte-clean"
  PASS=$((PASS + 1))
fi
( cd "$R" && bash .softhouse/reviews/A2-11/run-all.sh ) > "$SCRATCH/c7.txt" 2>&1
want "(7) run-all.sh green again after every mutation is reverted" 0 "$?"
grep_want "(7) 10/10 as adjudicated, 0 deviations" "sections run: 10    deviations: 0" "$SCRATCH/c7.txt"
cp "$SCRATCH/c7.txt" "$OUT/37-case7-GREEN-again.txt"
echo

echo "############ SUMMARY   PASS=$PASS   FAIL=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  echo "T374 PROVER: FAIL — a fix did not go red where it was supposed to."
  exit 1
fi
echo "T374 PROVER: PASS — every fix on this branch was driven RED on real bytes, and the"
echo "clean tree is still GREEN. Nothing in the working tree was mutated at any point."
exit 0
