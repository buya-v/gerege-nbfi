#!/usr/bin/env bash
# =============================================================================================
# T412 -- DRIVE THE *INSTALLED* HOOK, in THIS repository, through the REAL shared hooks dir.
#     bash .softhouse/capture/t412-driver-selfgrading/bin/drive-installed.sh <outdir>
#
# WHY THIS EXISTS SEPARATELY FROM drive-gate.sh. That drive proves the GATE LOGIC, in a throwaway
# clone with its own hooks directory. It says nothing about whether the file at
# `$(git rev-parse --git-common-dir)/hooks/pre-push` on this machine fires. This program has
# logged SEVEN guards built and wired to nothing, and "I wrote a hook" is exactly the claim that
# census refutes -- so the installed file is driven here, red and green, from a real worktree of
# the real repository, against the real git.
#
# IT NEVER TOUCHES `origin`. Every push in this file goes to a BARE REMOTE created under a
# scratch root, using the refspec `HEAD:refs/heads/main` -- which is what makes the gate engage,
# because the gate keys on the REMOTE ref name. The scratch remote is removed at the end.
#
# ENGINE (P-33/P-53): bash, git. Declared, not assumed.
# =============================================================================================
set -u

OUT="${1:-}"
[ -n "$OUT" ] || { echo "usage: drive-installed.sh <outdir>"; exit 2; }
mkdir -p "$OUT" || { echo "drive: could not create $OUT"; exit 2; }
OUT="$(cd "$OUT" && pwd)" || { echo "drive: could not resolve $OUT"; exit 2; }

TOP="$(git rev-parse --show-toplevel)" || { echo "drive: not in a work tree"; exit 2; }
COMMON="$(git rev-parse --git-common-dir)" || { echo "drive: no common dir"; exit 2; }
case "$COMMON" in /*) : ;; *) COMMON="$TOP/$COMMON" ;; esac
HOOK="$COMMON/hooks/pre-push"

PASS=0
FAIL=0
hdr() { printf '\n===============================================================\n%s\n===============================================================\n' "$*"; }

expect() {
  local line ok=1 why=''
  if [ "$2" -ne "$3" ]; then ok=0; why="rc"; fi
  if ! LC_ALL=C grep -aqF "$5" "$4"; then
    ok=0
    if [ -n "$why" ]; then why="rc+marker"; else why="marker"; fi
  fi
  if [ "$ok" -eq 1 ]; then
    line="$(printf 'ARM %-26s EXPECT rc=%s GOT rc=%s  marker %-38s PASS' "$1" "$2" "$3" "[$5]")"
    PASS=$((PASS + 1))
  else
    line="$(printf 'ARM %-26s EXPECT rc=%s GOT rc=%s  marker %-38s *** ARM FAILED (%s) ***' "$1" "$2" "$3" "[$5]" "$why")"
    FAIL=$((FAIL + 1))
  fi
  printf '%s\n' "$line"
  printf '\n%s\n' "$line" >> "$4"
}

hdr "PRECONDITION -- the hook must be INSTALLED in the shared hooks directory of THIS repo"
if [ ! -f "$HOOK" ]; then
  echo "drive: $HOOK is ABSENT. There is nothing installed to drive, and every push below would"
  echo "drive: exit 0 for want of a gate -- which reads exactly like a gate that approved."
  exit 2
fi
if ! LC_ALL=C grep -q 'softhouse-t412-driver-push-gate' "$HOOK"; then
  echo "drive: $HOOK exists but is NOT this gate's shim. REFUSING to report on someone else's hook."
  exit 2
fi
echo "installed hook: $HOOK"
cp "$HOOK" "$OUT/00-installed-pre-push.txt" || exit 2
bash .softhouse/hooks/install-driver-push-gate.sh --status > "$OUT/01-status.txt" 2>&1
LC_ALL=C sed -n '1,12p' "$OUT/01-status.txt"

D="$(mktemp -d "${TMPDIR:-/tmp}/t412-installed.XXXXXXXXXX")" || exit 2
BARE="$D/remote.git"
git init --quiet --bare "$BARE" || exit 2
git remote remove t412scratch >/dev/null 2>&1
git remote add t412scratch "$BARE" || exit 2

MAIN="$(git rev-parse main)" || exit 2
MINE="$(git rev-parse HEAD)" || exit 2
BR="$(git rev-parse --abbrev-ref HEAD)" || exit 2
echo "main=$MAIN  mine=$MINE  branch=$BR"

finish() {
  git checkout --quiet "$BR" >/dev/null 2>&1
  git branch -D t412-installed-probe >/dev/null 2>&1
  git remote remove t412scratch >/dev/null 2>&1
  [ -n "${D:-}" ] && [ -d "$D" ] && rm -rf "$D"
}
trap finish EXIT

# ---------------------------------------------------------------------------------------------
hdr "ARM I1 (CONTROL) -- push THIS branch to a NON-main ref. The installed gate stands aside."
git push t412scratch "HEAD:refs/heads/softhouse/T412-installed-probe" > "$OUT/10-I1-nonmain.txt" 2>&1
expect I1-nonmain-stands-aside 0 $? "$OUT/10-I1-nonmain.txt" "STANDS ASIDE for refs/heads/softhouse/T412-installed-probe"

hdr "ARM I2 (RED) -- push THIS BRANCH as refs/heads/main. Its delta from main is *.sh files,"
echo    "                which leave the STATE set, so the cheap subset may not stand in for the bar."
git push t412scratch "HEAD:refs/heads/main" > "$OUT/11-I2-RED-own-branch-as-main.txt" 2>&1
expect I2-own-branch-refused 1 $? "$OUT/11-I2-RED-own-branch-as-main.txt" "C3 REFUSED"

hdr "ARM I3 (GREEN) -- push main itself. Its tree carries a REAL FULL attestation written by"
echo    "                bar-attest.sh from a real bar run, not seeded by this drive."
git push t412scratch "main:refs/heads/main" > "$OUT/12-I3-GREEN-attested-main.txt" 2>&1
expect I3-attested-main 0 $? "$OUT/12-I3-GREEN-attested-main.txt" "C3 the pushed tree is ATTESTED FULL"

# ---------------------------------------------------------------------------------------------
hdr "ARM I4 (RED) -- a state-only commit off main carrying the RECORDED DEFECT: an undefined"
echo    "                P-number in .softhouse/RESUME.md, a DIRECTIVE file."
git checkout --quiet -b t412-installed-probe main || exit 2
printf '\nT412 installed drive -- dispatching under P-150, the rule about grading your own pushes.\n' \
  >> .softhouse/RESUME.md
git add .softhouse/RESUME.md || exit 2
git -c user.email=t412@local -c user.name=T412Drive commit --quiet -m "T412 installed drive: bad citation" || exit 2
S4=$(date +%s)
git push t412scratch "HEAD:refs/heads/main" > "$OUT/13-I4-RED-bad-citation.txt" 2>&1
R4=$?
E4=$(date +%s)
expect I4-bad-citation-refused 1 $R4 "$OUT/13-I4-RED-bad-citation.txt" "C3 REFUSED -- THE CHEAP SUBSET FAILED ON THE PUSHED TREE"
echo "cheap path wall clock (RED): $((E4 - S4)) s" | tee -a "$OUT/13-I4-RED-bad-citation.txt"

hdr "ARM I5 (GREEN) -- the same commit with the citation repaired. Same gate, healthy push."
git reset --quiet --hard main || exit 2
printf '\nT412 installed drive -- an ordinary healthy dispatch note.\n' >> .softhouse/RESUME.md
git add .softhouse/RESUME.md || exit 2
git -c user.email=t412@local -c user.name=T412Drive commit --quiet -m "T412 installed drive: healthy" || exit 2
S5=$(date +%s)
git push t412scratch "HEAD:refs/heads/main" > "$OUT/14-I5-GREEN-healthy.txt" 2>&1
R5=$?
E5=$(date +%s)
expect I5-healthy-allowed 0 $R5 "$OUT/14-I5-GREEN-healthy.txt" "C3 PASS -- cheap subset clean"
echo "cheap path wall clock (GREEN): $((E5 - S5)) s" | tee -a "$OUT/14-I5-GREEN-healthy.txt"

hdr "SUMMARY"
printf 'arms passed: %s   arms failed: %s\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
exit 0
