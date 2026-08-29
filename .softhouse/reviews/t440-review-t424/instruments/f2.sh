#!/usr/bin/env bash
# T440 independent re-derivation of the F-2 cause. Written from scratch by T440;
# T424's t424-f2-true-cause.sh was NOT used, read for its result only after this ran.
# $1 = path to the SHIPPED casualty-sweep.sh to extract the NEW block from (by content).
# $2 = path to the PRE-T402 casualty-sweep.sh to extract the OLD block from (by content).
set -uo pipefail
fails=0
ok(){ printf '  [OK]   %s\n' "$1"; }
no(){ printf '  [FAIL] %s\n' "$1"; fails=$((fails+1)); }

SHIPPED="$1"; PRE="$2"
REPO="$3"

echo "T440 F-2 DRIVE"
echo "bash: $BASH_VERSION   uname: $(uname -srm)   git: $(git --version)"
echo

echo "== PART 0: the primitives that decide it =="

out=$(true | grep -c .); rc=$?
printf '  true | grep -c .                 -> captured=[%s] rc=%s\n' "$out" "$rc"
[ "$out" = "0" ] && ok "grep -c . PRINTS 0 for an empty stream" || no "expected 0, got [$out]"
[ "$rc" = "1" ] && ok "and its rc is 1" || no "expected rc 1, got $rc"

( git ls-files --no-such-flag-zzz >/dev/null 2>&1 ); gitrc=$?
out=$(git ls-files --no-such-flag-zzz 2>/dev/null | grep -c .); rc=$?
printf '  git(FAILS rc=%s) | grep -c .     -> captured=[%s] rc=%s\n' "$gitrc" "$out" "$rc"
[ "$out" = "0" ] && ok "a FAILING git ls-files STILL yields the string 0 -- the stream is NOT empty" \
                 || no "expected 0, got [$out]"

out=$( set -o pipefail; git ls-files --no-such-flag-zzz 2>/dev/null | grep -c . ); rc=$?
printf '  PIPEFAIL git(%s) | grep -c .(1)  -> captured=[%s] rc=%s\n' "$gitrc" "$out" "$rc"
if [ "$rc" = "1" ]; then ok "pipefail returned grep's 1, NOT git's $gitrc -- RIGHTMOST non-zero wins"
else no "pipefail returned $rc; expected 1 (rightmost)"; fi

out=$(printf 'a\nb\n' | grep -c -E '[' 2>/dev/null); rc=$?
printf '  REAL grep, INVALID REGEX         -> captured=[%s] rc=%s\n' "$out" "$rc"
[ -z "$out" ] && ok "stdout EMPTY when grep ITSELF fails" || no "expected empty, got [$out]"
[ "$rc" -ge 2 ] && ok "rc >= 2 ($rc) when grep ITSELF fails" || no "expected rc>=2, got $rc"

if [ "0" -lt 1 ]; then r=TRUE; else r=FALSE; fi
brc=0; ( [ "0" -lt 1 ] ) || brc=$?
printf '  [ "0" -lt 1 ]                    -> %s (test rc=%s)\n' "$r" "$brc"
[ "$r" = TRUE ] && ok 'the abort FIRES on "0"' || no "got $r"

e=""
if [ "$e" -lt 1 ] 2>/dev/null; then r=TRUE; else r=FALSE; fi
brc=0; ( [ "$e" -lt 1 ] ) 2>/dev/null || brc=$?
printf '  [ "" -lt 1 ]                     -> %s (test rc=%s)\n' "$r" "$brc"
if [ "$r" = FALSE ] && [ "$brc" -ge 2 ]; then ok 'malformed test returns 2 -> if reads FALSE -> FALLS THROUGH'
else no "got $r rc=$brc"; fi

echo
echo "== PART 0b: pipefail rightmost, isolated from git =="
rc=0; ( set -o pipefail; sh -c 'exit 128' | sh -c 'exit 1' ) || rc=$?
printf '  pipefail  (exit 128) | (exit 1)  -> rc=%s\n' "$rc"
[ "$rc" = "1" ] && ok "rightmost non-zero (1) wins over the left arm's 128" || no "got $rc"
rc=0; ( set -o pipefail; sh -c 'exit 1' | sh -c 'exit 128' ) || rc=$?
printf '  pipefail  (exit 1) | (exit 128)  -> rc=%s\n' "$rc"
[ "$rc" = "128" ] && ok "and reversed, the rightmost (128) wins -- it is POSITION, not magnitude" || no "got $rc"
rc=0; ( set -o pipefail; sh -c 'exit 3' | sh -c 'exit 0' ) || rc=$?
printf '  pipefail  (exit 3) | (exit 0)    -> rc=%s\n' "$rc"
[ "$rc" = "3" ] && ok "rightmost NON-ZERO: a trailing 0 does not mask an earlier failure" || no "got $rc"

echo
echo "== PART 1: OLD block (pre-T402), extracted BY CONTENT, driven under PATH shims =="
OLDANCH='if [ "$(git ls-files .softhouse | grep -c .)" -lt 1 ]; then'
n=$(grep -c -F "$OLDANCH" "$PRE")
printf '  OLD anchor occurrences in %s: %s\n' "$(basename "$PRE")" "$n"
[ "$n" = "1" ] || { echo "REFUSING: OLD anchor not unique"; exit 3; }
s=$(grep -n -F "$OLDANCH" "$PRE" | cut -d: -f1)
OLD=$(sed -n "${s},$((s+4))p" "$PRE")
printf '%s\n' "$OLD" | sed 's/^/    | /'

SHIM=$(mktemp -d "${TMPDIR:-/tmp}/t440.shim.XXXXXX")
GITBIN=$(command -v git)
GREPBIN=$(command -v grep)
mkgitshim(){ printf '#!/bin/sh\nif [ "$1" = "ls-files" ]; then exit 128; fi\nexec %s "$@"\n' "$GITBIN" > "$SHIM/git"; chmod +x "$SHIM/git"; }
mkgrepshim(){ printf '#!/bin/sh\nexit 2\n' > "$SHIM/grep"; chmod +x "$SHIM/grep"; }
noshim(){ :; }

runblk(){ # $1 = block text, $2 = shim fn
  rm -f "$SHIM/git" "$SHIM/grep"; "$2"
  local out rc
  out=$(cd "$REPO" && PATH="$SHIM:$PATH" bash -c "set -uo pipefail
$1
echo 'FELL THROUGH'" 2>&1); rc=$?
  printf '%s|%s' "$(printf '%s' "$out" | tr '\n' ';' | cut -c1-100)" "$rc"
}

r=$(runblk "$OLD" mkgitshim);  printf '  OLD + failing git ls-files  -> [%s]\n' "$r"
case "$r" in *ABORT*"|2") ok "OLD ABORTS rc2 on a failing git ls-files -- T402'S STATED CAUSE DOES NOT REPRODUCE" ;;
             *) no "expected an ABORT|2, got [$r]" ;; esac
r=$(runblk "$OLD" mkgrepshim); printf '  OLD + failing grep          -> [%s]\n' "$r"
case "$r" in *"FELL THROUGH|0") ok "OLD FALLS THROUGH rc0 when grep ITSELF fails -- THE TRUE CAUSE, REPRODUCED" ;;
             *) no "expected FELL THROUGH|0, got [$r]" ;; esac
r=$(runblk "$OLD" noshim);     printf '  OLD healthy                 -> [%s]\n' "$r"
case "$r" in *"FELL THROUGH|0") ok "OLD healthy passes through (arm is non-vacuous)" ;; *) no "got [$r]" ;; esac

echo
echo "== PART 2: SHIPPED block, extracted BY CONTENT from casualty-sweep.sh =="
NEWANCH='SWEEP_CORPUS_N=$(git ls-files .softhouse | grep -c .); _corpus_rc=$?'
n=$(grep -c -F "$NEWANCH" "$SHIPPED")
printf '  NEW anchor occurrences in %s: %s\n' "$(basename "$SHIPPED")" "$n"
[ "$n" = "1" ] || { echo "REFUSING: NEW anchor not unique"; exit 3; }
s=$(grep -n -F "$NEWANCH" "$SHIPPED" | cut -d: -f1)
NEW=$(sed -n "${s},$((s+19))p" "$SHIPPED")
printf '%s\n' "$NEW" | sed 's/^/    | /'

r=$(runblk "$NEW" mkgitshim);  printf '  NEW + failing git ls-files  -> [%s]\n' "$r"
case "$r" in *ABORT*"|2") ok "NEW aborts rc2 on a failing git ls-files (through the VALUE test)" ;;
             *) no "expected ABORT|2, got [$r]" ;; esac
case "$r" in *"COUNT DID NOT RUN"*) no "NEW blamed the COUNT for a git failure (misattribution in the message)" ;;
             *) ok "and it does NOT claim 'the count did not run' -- the message matches the cause" ;; esac
r=$(runblk "$NEW" mkgrepshim); printf '  NEW + failing grep          -> [%s]\n' "$r"
case "$r" in *"COUNT DID NOT RUN"*"|2") ok "NEW aborts rc2 on a failing grep, naming 'the corpus COUNT DID NOT RUN'" ;;
             *) no "expected COUNT DID NOT RUN|2, got [$r]" ;; esac
r=$(runblk "$NEW" noshim);     printf '  NEW healthy                 -> [%s]\n' "$r"
case "$r" in *"FELL THROUGH|0") ok "NEW healthy passes through (arm is non-vacuous)" ;; *) no "got [$r]" ;; esac

rm -rf "$SHIM"
echo
echo "T440-F2-DRIVE-RESULT: arms_failed=$fails"
[ "$fails" -eq 0 ] || exit 1
exit 0
