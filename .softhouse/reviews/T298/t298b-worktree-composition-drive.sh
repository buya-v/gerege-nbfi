#!/usr/bin/env bash
# T298 (resumed) — brief item 4, DRIVEN IN THE FIXTURE.
# The reviewer IS an isolated worker worktree. The composition under test:
#   activation line uses `git rev-parse --show-toplevel`  -> resolves to THE WORKTREE
#   go-env.sh internally uses `git rev-parse --git-common-dir` -> resolves to THE MAIN CHECKOUT
# The question T256 asserts and I must drive: does a worktree end up with its own
# empty toolchain dir, or a SECOND module cache?
set -u -o pipefail
echo "T298 worktree-composition drive — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "HEAD = $(git rev-parse HEAD)"
echo

WT=$(git rev-parse --show-toplevel)
COMMON=$(git rev-parse --git-common-dir)
MAIN=$(cd "$COMMON/.." && pwd)
echo "FIXTURE"
echo "  git rev-parse --show-toplevel  = $WT"
echo "  git rev-parse --git-common-dir = $COMMON"
echo "  main checkout                  = $MAIN"
if [ "$WT" = "$MAIN" ]; then
  echo "  !! NOT A LINKED WORKTREE — this drive would be vacuous. ABORT."; exit 9
fi
echo "  CONFIRMED: worktree != main checkout, so the two git queries DISAGREE here."
echo "  => this is the exact condition under which a naive composition would break."
echo

echo "PRE-STATE (before sourcing anything)"
echo "  worktree-local toolchain dir exists?  $( [ -e "$WT/.softhouse/toolchain" ] && echo YES || echo 'no  <- must stay no' )"
echo "  main   toolchain dir exists?          $( [ -e "$MAIN/.softhouse/toolchain" ] && echo YES || echo no )"
echo "  inherited GOROOT     = ${GOROOT:-'(unset)'}"
echo "  inherited GOMODCACHE = ${GOMODCACHE:-'(unset)'}"
echo

FAIL=0
ASSERTS=0
ck() { # label expected actual
  ASSERTS=$((ASSERTS+1))
  if [ "$2" = "$3" ]; then printf '  ok   %-58s = %s\n' "$1" "$3"
  else printf '  FAIL %-58s\n       expected [%s]\n       actual   [%s]\n' "$1" "$2" "$3"; FAIL=$((FAIL+1)); fi
}

run_from() { # cwd-label cwd
  local label="$1" dir="$2"
  echo "STEP — activation line run VERBATIM from $label ($dir)"
  # the line exactly as the document prescribes it, extracted below in STEP X
  local out
  out=$(cd "$dir" && env -u GOROOT -u GOPATH -u GOCACHE -u GOMODCACHE -u GEREGE_TOOLCHAIN -u GEREGE_GO_SOURCE bash -c '
      . "$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh"
      printf "SRC=%s\n" "${GEREGE_GO_SOURCE:-UNSET}"
      printf "GOROOT=%s\n" "${GOROOT:-UNSET}"
      printf "GOPATH=%s\n" "${GOPATH:-UNSET}"
      printf "GOCACHE=%s\n" "${GOCACHE:-UNSET}"
      printf "GOMODCACHE=%s\n" "${GOMODCACHE:-UNSET}"
      printf "TOOLCHAIN=%s\n" "${GEREGE_TOOLCHAIN:-UNSET}"
      printf "WHICHGO=%s\n" "$(command -v go || echo NONE)"
      printf "GOVER=%s\n" "$(go version 2>&1 || true)"
      printf "ENVGOMODCACHE=%s\n" "$(go env GOMODCACHE 2>&1 || true)"
      printf "ENVGOROOT=%s\n" "$(go env GOROOT 2>&1 || true)"
  ' 2>/dev/null)
  printf '%s\n' "$out" | sed 's/^/    /'
  local src goroot modc envmodc envroot
  src=$(printf '%s\n' "$out"      | sed -n 's/^SRC=//p')
  goroot=$(printf '%s\n' "$out"   | sed -n 's/^GOROOT=//p')
  modc=$(printf '%s\n' "$out"     | sed -n 's/^GOMODCACHE=//p')
  envmodc=$(printf '%s\n' "$out"  | sed -n 's/^ENVGOMODCACHE=//p')
  envroot=$(printf '%s\n' "$out"  | sed -n 's/^ENVGOROOT=//p')
  ck "[$label] GEREGE_GO_SOURCE"            "pinned"                                 "$src"
  ck "[$label] GOROOT is the MAIN checkout" "$MAIN/.softhouse/toolchain/go"          "$goroot"
  ck "[$label] GOMODCACHE is the MAIN one"  "$MAIN/.softhouse/toolchain/gomodcache"  "$modc"
  ck "[$label] go itself agrees on GOMODCACHE" "$MAIN/.softhouse/toolchain/gomodcache" "$envmodc"
  ck "[$label] go itself agrees on GOROOT"  "$MAIN/.softhouse/toolchain/go"          "$envroot"
  case "$goroot" in
    "$WT"/*) echo "  FAIL [$label] GOROOT points INSIDE THE WORKTREE — second toolchain"; FAIL=$((FAIL+1));;
    *) echo "  ok   [$label] GOROOT does not point inside the worktree";;
  esac
  ASSERTS=$((ASSERTS+1))
  echo
}

# ---- STEP X: extract the line from the document, do not retype it -------------
echo "STEP X — the line under test, EXTRACTED from .softhouse/reference-oracle.md"
ACT=$(awk '/T298-MARKER-NEVER/{next} /T256-ACTIVATION-LINE:BEGIN/{b=1;next} /T256-ACTIVATION-LINE:END/{b=0} b&&/^```/{f=!f;next} b&&f{print}' .softhouse/reference-oracle.md)
printf '  extracted [%s]\n' "$ACT"
ACTN=$(printf '%s\n' "$ACT" | grep -c . || true)
ck "exactly one line between the markers" "1" "$ACTN"
if [ "$ACT" != '. "$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh"' ]; then
  echo "  !! the document's line differs from the line this drive hardcodes; ABORTING to avoid testing a stale line"; exit 9
fi
echo "  ok   the line this drive runs is BYTE-IDENTICAL to the document's"
echo

run_from "repo root (worktree)" "$WT"
run_from "nexus/"               "$WT/nexus"
run_from ".softhouse/guards/"   "$WT/.softhouse/guards"

echo "STEP — did anything CREATE a worktree-local toolchain or cache?"
for d in toolchain toolchain/go toolchain/gomodcache toolchain/gocache toolchain/gopath; do
  printf '  %-34s %s\n' "$WT/.softhouse/$d" "$( [ -e "$WT/.softhouse/$d" ] && echo 'EXISTS  <-- DEFECT' || echo 'absent' )"
done
ASSERTS=$((ASSERTS+1))
if [ -e "$WT/.softhouse/toolchain" ]; then echo "  FAIL worktree grew its own toolchain dir"; FAIL=$((FAIL+1)); else echo "  ok   no worktree-local toolchain dir was created"; fi
echo

echo "STEP — does it ACTUALLY COMPILE from the worktree, against the shared cache?"
BUILD=$(cd "$WT/nexus" && env -u GOROOT -u GOMODCACHE bash -c '
   . "$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh" >/dev/null 2>&1
   go build ./... 2>&1; echo "BUILDRC=$?"' )
printf '%s\n' "$BUILD" | tail -5 | sed 's/^/    /'
BRC=$(printf '%s\n' "$BUILD" | sed -n 's/^BUILDRC=//p')
ck "go build ./... from the worktree" "0" "$BRC"
echo

echo "STEP — module cache identity: is there exactly ONE, shared?"
echo "  main-checkout gomodcache inode/dev:"
stat -f '    %d:%i  %N' "$MAIN/.softhouse/toolchain/gomodcache" 2>/dev/null || stat -c '    %d:%i  %n' "$MAIN/.softhouse/toolchain/gomodcache"
echo "  count of *.softhouse/toolchain dirs under the whole worktree root (should be 0):"
find "$WT/.softhouse" -maxdepth 1 -name toolchain 2>/dev/null | wc -l | tr -d ' '
echo

echo "STEP — NEGATIVE CONTROL: the OLD hardcoded line, run from this worktree."
echo "  (On THIS Mac the old absolute path still resolves — so it appears to work while"
echo "   silently binding a worktree to a path that exists only on one host.)"
env -u GOROOT bash -c '
   . /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
   printf "    OLD-LINE SRC=%s GOROOT=%s\n" "${GEREGE_GO_SOURCE:-UNSET}" "${GOROOT:-UNSET}"' 2>&1 | tail -2
echo "  => it resolves HERE and only here. That is the invisibility T256 named, reproduced."
echo

printf 'asserts: %d   failures: %d\n' "$ASSERTS" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "DRIVE: GREEN"; exit 0; else echo "DRIVE: RED"; exit 1; fi
