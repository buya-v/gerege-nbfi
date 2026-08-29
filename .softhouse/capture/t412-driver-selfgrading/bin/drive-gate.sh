#!/usr/bin/env bash
# =============================================================================================
# T412 -- DRIVE THE DRIVER PUSH GATE RED AND GREEN.
#     bash .softhouse/capture/t412-driver-selfgrading/bin/drive-gate.sh <outdir>
#
# P-22: a guard, a canary or a control that cannot fail is worse than none, because it is
# believed. P-98: a guard that cannot refuse anything is the same defect as one that refuses
# everything. So every arm below is paired -- a REFUSAL and the CONTROL that shows the same gate
# lets a healthy push through.
#
# It runs in a THROWAWAY CLONE with its own hooks directory and its own bare remote, both under
# a scratch root. Nothing here touches `origin`, `main`, or the running fire. The separate
# question -- does the hook file ACTUALLY INSTALLED in this repository's shared hooks directory
# fire and refuse -- is driven by 20-drive-installed.sh, because a gate proven only in a clone is
# the P-45 shape this task exists to close.
#
# THE LEDGER IS SEEDED BY HAND IN THIS DRIVE, AND THAT IS DECLARED RATHER THAN HIDDEN. The
# attestation ledger is an INPUT to the gate; a drive supplies inputs. Whether `bar-attest.sh`
# is the only thing that can lawfully write a FULL row in real use is a different question, and
# it is answered by running it for real against `main` -- see the handoff.
#
# ENGINE (P-33/P-53): bash, git, /usr/bin/python3. Declared, not assumed.
# =============================================================================================
set -u

OUT="${1:-}"
[ -n "$OUT" ] || { echo "usage: drive-gate.sh <outdir>"; exit 2; }
mkdir -p "$OUT" || { echo "drive: could not create $OUT"; exit 2; }
OUT="$(cd "$OUT" && pwd)" || { echo "drive: could not resolve $OUT"; exit 2; }

SRCWT="$(git rev-parse --show-toplevel)" || { echo "drive: not in a work tree"; exit 2; }

D="$(mktemp -d "${TMPDIR:-/tmp}/t412-drive.XXXXXXXXXX")" || { echo "drive: no scratch"; exit 2; }
REPO="$D/repo"
BARE="$D/remote.git"

PASS=0
FAIL=0

hdr() { printf '\n===============================================================\n%s\n===============================================================\n' "$*"; }

# expect <arm> <expected-rc> <actual-rc> <transcript> <marker-that-must-appear>
#
# NO PIPELINE. An earlier draft ended `| tee -a`, which runs the counter in a SUBSHELL, so PASS
# and FAIL stayed 0 and the summary would have reported a clean drive whatever happened. That is
# the shape this whole task is about, met in the drive harness itself.
#
# THE MARKER IS NOT DECORATION, AND THE FIRST RUN OF THIS DRIVE PROVES IT. Run 1 reported
# `ARM nonmain-stands-aside  EXPECT rc=0  GOT rc=0  PASS` while the hook WAS NOT INSTALLED AT ALL
# -- the installer had exited 127 because the clone was taken from a commit that did not yet
# carry these files, and a push that no gate examined exits 0 for the same reason a push a gate
# approved does. An exit code alone cannot tell "allowed" from "never asked". So every arm also
# asserts a STRING THE GATE ITSELF PRINTS; an arm whose marker is missing FAILS however its rc
# came out.  [P-22 / P-35]
expect() {
  local line ok=1 why=''
  if [ "$2" -ne "$3" ]; then ok=0; why="rc"; fi
  if ! LC_ALL=C grep -aqF "$5" "$4"; then
    ok=0
    if [ -n "$why" ]; then why="rc+marker"; else why="marker"; fi
  fi
  if [ "$ok" -eq 1 ]; then
    line="$(printf 'ARM %-28s EXPECT rc=%s GOT rc=%s  marker %-34s PASS' "$1" "$2" "$3" "[$5]")"
    PASS=$((PASS + 1))
  else
    line="$(printf 'ARM %-28s EXPECT rc=%s GOT rc=%s  marker %-34s *** ARM FAILED (%s) ***' "$1" "$2" "$3" "[$5]" "$why")"
    FAIL=$((FAIL + 1))
  fi
  printf '%s\n' "$line"
  printf '\n%s\n' "$line" >> "$4"
}

hdr "SETUP -- throwaway clone and bare remote under $D"
git clone --quiet --no-hardlinks "$SRCWT" "$REPO" || { echo "drive: clone failed"; exit 2; }
git init --quiet --bare "$BARE" || { echo "drive: bare init failed"; exit 2; }
cd "$REPO" || { echo "drive: could not enter the clone"; exit 2; }
git config user.email t412@local || exit 2
git config user.name  T412Drive  || exit 2
git checkout --quiet -B main || exit 2
git remote add scratch "$BARE" || exit 2
git push --quiet scratch main >/dev/null 2>&1 || { echo "drive: seed push failed"; exit 2; }

bash .softhouse/hooks/install-driver-push-gate.sh > "$OUT/00-install.txt" 2>&1
IRC=$?
echo "installed in the clone (rc=$IRC)"
if [ "$IRC" -ne 0 ]; then
  echo "drive: THE INSTALLER FAILED (rc=$IRC). Every arm below would push through an ABSENT gate"
  echo "drive: and exit 0, which reads exactly like a gate that approved. REFUSING to drive."
  LC_ALL=C sed -n '1,20p' "$OUT/00-install.txt"
  exit 2
fi
[ -f "$REPO/.git/hooks/pre-push" ] || { echo "drive: no pre-push hook after install. REFUSING."; exit 2; }
GATEDIR="$REPO/.git/softhouse-driver-gate"
LEDGER="$GATEDIR/attest.tsv"
mkdir -p "$GATEDIR" || exit 2

BASE="$(git rev-parse HEAD)" || exit 2
BASETREE="$(git rev-parse 'HEAD^{tree}')" || exit 2
echo "base commit $BASE  tree $BASETREE"

# ---------------------------------------------------------------------------------------------
hdr "ARM 1 (CONTROL) -- a NON-MAIN ref. The gate must STAND ASIDE."
git checkout --quiet -b softhouse/T412-probe || exit 2
date -u > probe-arm1.txt
git add probe-arm1.txt && git commit --quiet -m "T412 drive: arm 1 probe" || exit 2
git push scratch softhouse/T412-probe > "$OUT/01-nonmain-CONTROL.txt" 2>&1
expect nonmain-stands-aside 0 $? "$OUT/01-nonmain-CONTROL.txt" "STANDS ASIDE for refs/heads/softhouse/T412-probe"
git checkout --quiet main || exit 2

# ---------------------------------------------------------------------------------------------
hdr "ARM 2 (RED) -- state-only commit, EMPTY LEDGER. No graded ancestor => REFUSE."
: > "$LEDGER" || exit 2
printf '\nT412 drive arm 2 -- an ordinary healthy note.\n' >> .softhouse/RESUME.md
git add .softhouse/RESUME.md && git commit --quiet -m "T412 drive: arm 2 state-only, unattested" || exit 2
A2="$(git rev-parse HEAD)"
git push scratch main > "$OUT/02-RED-no-graded-ancestor.txt" 2>&1
expect no-graded-ancestor 1 $? "$OUT/02-RED-no-graded-ancestor.txt" "C3 REFUSED -- NO GRADED ANCESTOR"

# ---------------------------------------------------------------------------------------------
hdr "ARM 3 (GREEN) -- same commit, with the BASE tree attested FULL. Cheap subset must PASS."
printf 'FULL\t%s\t%s\t%s\t%s\n' "$BASETREE" "$BASE" "1970-01-01T00:00:00Z" \
  "DRIVE FIXTURE -- seeded by drive-gate.sh, not by bar-attest.sh" > "$LEDGER" || exit 2
git push scratch main > "$OUT/03-GREEN-state-only-cheap-pass.txt" 2>&1
expect state-only-cheap-pass 0 $? "$OUT/03-GREEN-state-only-cheap-pass.txt" "C3 PASS -- cheap subset clean"

# ---------------------------------------------------------------------------------------------
hdr "ARM 4 (RED) -- the RECORDED DEFECT: an UNDEFINED P-number in RESUME.md, a DIRECTIVE file."
printf '\nT412 drive arm 4 -- dispatching under P-150, the rule about grading your own pushes.\n' \
  >> .softhouse/RESUME.md
git add .softhouse/RESUME.md && git commit --quiet -m "T412 drive: arm 4 bad citation in RESUME.md" || exit 2
git push scratch main > "$OUT/04-RED-bad-citation.txt" 2>&1
expect bad-citation-refused 1 $? "$OUT/04-RED-bad-citation.txt" "C3 REFUSED -- THE CHEAP SUBSET FAILED ON THE PUSHED TREE"

# ---------------------------------------------------------------------------------------------
hdr "ARM 5 (GREEN) -- repair the citation in place. The SAME gate must now allow the push."
git reset --quiet --hard "HEAD~1" || exit 2
printf '\nT412 drive arm 5 -- dispatching under the rule about grading your own pushes.\n' \
  >> .softhouse/RESUME.md
git add .softhouse/RESUME.md && git commit --quiet -m "T412 drive: arm 5 citation repaired" || exit 2
git push scratch main > "$OUT/05-GREEN-citation-repaired.txt" 2>&1
expect citation-repaired 0 $? "$OUT/05-GREEN-citation-repaired.txt" "C3 PASS -- cheap subset clean"

# ---------------------------------------------------------------------------------------------
hdr "ARM 6 (RED) -- a GITLINK in the pushed tree. Instance 3. Must refuse."
BASE6="$(git rev-parse HEAD)"
BASE6T="$(git rev-parse 'HEAD^{tree}')"
printf 'FULL\t%s\t%s\t%s\t%s\n' "$BASE6T" "$BASE6" "1970-01-01T00:00:00Z" "DRIVE FIXTURE" > "$LEDGER" || exit 2
STRAY="$(git rev-parse HEAD)"
git update-index --add --cacheinfo 160000,"$STRAY",main || exit 2
git commit --quiet -m "T412 drive: arm 6 gitlink at 'main', exactly the 8c08f7d8 shape" || exit 2
git push scratch main > "$OUT/06-RED-gitlink.txt" 2>&1
expect gitlink-refused 1 $? "$OUT/06-RED-gitlink.txt" "C1 REFUSED -- THE PUSHED TREE CONTAINS A GITLINK"

hdr "ARM 7 (RED) -- the SAME gitlink push WITH a bypass reason set. C1 has NO bypass."
SOFTHOUSE_DRIVER_GATE_BYPASS="deliberate rescue push, arm 7 of the T412 drive" \
  git push scratch main > "$OUT/07-RED-gitlink-bypass-still-refused.txt" 2>&1
expect gitlink-bypass-refused 1 $? "$OUT/07-RED-gitlink-bypass-still-refused.txt" "THERE IS NO BYPASS FOR C1"
git reset --quiet --hard "$BASE6" || exit 2

# ---------------------------------------------------------------------------------------------
hdr "ARM 8 (RED) -- a NON-MERGE commit writing OUTSIDE the driver allowlist."
mkdir -p nexus/internal/apps/ledger/conformance || exit 2
printf 'package conformance\n' > nexus/internal/apps/ledger/conformance/t412probe.go
git add nexus/internal/apps/ledger/conformance/t412probe.go || exit 2
git commit --quiet -m "T412 drive: arm 8 a Go file in a driver state commit" || exit 2
git push scratch main > "$OUT/08-RED-outside-allowlist.txt" 2>&1
expect outside-allowlist 1 $? "$OUT/08-RED-outside-allowlist.txt" "C2 REFUSED -- a NON-MERGE commit"

hdr "ARM 9 (GREEN-BY-BYPASS) -- the same push WITH a reason. C2 is bypassable, and LOGGED."
SOFTHOUSE_DRIVER_GATE_BYPASS="arm 9: deliberate in-place repair of a merge conflict" \
  git push scratch main > "$OUT/09-BYPASS-outside-allowlist.txt" 2>&1
R9=$?
echo "--- bypass ledger ---" >> "$OUT/09-BYPASS-outside-allowlist.txt"
cat "$GATEDIR/bypass.log" >> "$OUT/09-BYPASS-outside-allowlist.txt" 2>&1
expect outside-allowlist-bypass 0 $R9 "$OUT/09-BYPASS-outside-allowlist.txt" "BYPASSED: C2 allowlist"

hdr "ARM 10 (RED) -- a bypass reason that is TOO SHORT is not a bypass."
git reset --quiet --hard "$BASE6" || exit 2
git push --quiet --force scratch main >/dev/null 2>&1 || exit 2
mkdir -p nexus/internal/apps/ledger/conformance || exit 2
printf 'package conformance\n' > nexus/internal/apps/ledger/conformance/t412probe2.go
git add nexus/internal/apps/ledger/conformance/t412probe2.go || exit 2
git commit --quiet -m "T412 drive: arm 10 short-reason bypass" || exit 2
SOFTHOUSE_DRIVER_GATE_BYPASS="ok" git push scratch main > "$OUT/10-RED-short-bypass.txt" 2>&1
expect short-bypass-refused 1 $? "$OUT/10-RED-short-bypass.txt" "C2 REFUSED -- a NON-MERGE commit"
git reset --quiet --hard "$BASE6" || exit 2

# ---------------------------------------------------------------------------------------------
hdr "ARM 11 (RED) -- an UNGRADED delta that LEAVES the STATE set (a *.sh under guards/)."
printf '# T412 drive arm 11\n' >> .softhouse/guards/check-capture-namespace.sh
git add .softhouse/guards/check-capture-namespace.sh || exit 2
git commit --quiet -m "T412 drive: arm 11 edit a guard script, unattested" || exit 2
git push scratch main > "$OUT/11-RED-delta-leaves-state-set.txt" 2>&1
expect delta-leaves-state 1 $? "$OUT/11-RED-delta-leaves-state-set.txt" "C3 REFUSED -- THE PUSHED TREE WAS NEVER GRADED"
git reset --quiet --hard "$BASE6" || exit 2

hdr "ARM 12 (RED) -- a DELETION of a state file. Deletions take the full bar."
git rm --quiet .softhouse/obligations.md || exit 2
git commit --quiet -m "T412 drive: arm 12 delete a state file" || exit 2
git push scratch main > "$OUT/12-RED-deletion.txt" 2>&1
expect deletion-refused 1 $? "$OUT/12-RED-deletion.txt" "C3 REFUSED -- THE PUSHED TREE WAS NEVER GRADED"
git reset --quiet --hard "$BASE6" || exit 2

hdr "ARM 13 (GREEN) -- the pushed tree is ITSELF attested FULL. Fast path, no subset run."
printf '\nT412 drive arm 13.\n' >> .softhouse/observations/t412-arm13.md
git add .softhouse/observations/t412-arm13.md || exit 2
git commit --quiet -m "T412 drive: arm 13 attested tree" || exit 2
A13="$(git rev-parse HEAD)"
A13T="$(git rev-parse 'HEAD^{tree}')"
printf 'FULL\t%s\t%s\t%s\t%s\n' "$A13T" "$A13" "1970-01-01T00:00:00Z" "DRIVE FIXTURE" >> "$LEDGER" || exit 2
git push scratch main > "$OUT/13-GREEN-tree-itself-attested.txt" 2>&1
expect tree-itself-attested 0 $? "$OUT/13-GREEN-tree-itself-attested.txt" "C3 the pushed tree is ATTESTED FULL"

# ---------------------------------------------------------------------------------------------
hdr "SUMMARY"
printf 'arms passed: %s   arms failed: %s\n' "$PASS" "$FAIL"
cd / || exit 2
rm -rf "$D"
[ "$FAIL" -eq 0 ] || exit 1
exit 0
