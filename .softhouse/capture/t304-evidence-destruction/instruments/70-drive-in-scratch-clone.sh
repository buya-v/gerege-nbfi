#!/usr/bin/env bash
# T304 instrument 70 — DRIVE the classification in a SCRATCH CLONE.
#
# WHY A CLONE.  A live fire is running against /Users/buv/gerege-nbfi. Destroying tracked
# evidence there would take out other workers' input, and the whole subject of this task is
# instruments that destroy tracked evidence as a side effect of running. So every arm below
# runs in a throwaway clone and the verdict is `git status --porcelain` measured IN THE
# CLONE. Nothing here touches the real checkout.
#
# ARM (a)  — the eight instruments proven to rm -rf committed evidence, now wired to the
#            T304 guard. Expected: exit 2, the refusal text, and A CLEAN TREE. The clean
#            tree is the point: before the guard, running them left 14..426 tracked files
#            deleted.
# ARM (b/c)— instruments whose destruction is over a scratch path, or is self-healing.
#            Expected: whatever exit code they have, and A CLEAN TREE afterwards.
#
# The tree is checked back to clean between arms, so one arm cannot mask another.
set -u

SRC="${1:-$(git rev-parse --show-toplevel)}"
SCRATCH="${2:-/tmp/t304-scratch}"

rm -rf "$SCRATCH"
git clone --quiet --no-hardlinks "$SRC" "$SCRATCH" || { echo "clone failed"; exit 2; }
cd "$SCRATCH" || exit 2
echo "scratch clone : $SCRATCH"
echo "cloned from   : $SRC"
echo "HEAD          : $(git rev-parse --short HEAD)"
echo

PASS=0; FAIL=0
ok()  { echo "    OK   $*"; PASS=$((PASS+1)); }
bad() { echo "    ***  FAIL: $*"; FAIL=$((FAIL+1)); }

dirty() { git -C "$SCRATCH" status --porcelain; }

assert_clean() {   # $1 = label
  local d; d="$(dirty)"
  if [ -z "$d" ]; then
    ok "git status --porcelain is EMPTY after $1"
  else
    bad "$1 left the tree DIRTY:"
    printf '%s\n' "$d" | sed 's/^/         /'
    # restore so the next arm starts from a known state
    git -C "$SCRATCH" checkout -- . 2>/dev/null
    git -C "$SCRATCH" clean -fdq 2>/dev/null
  fi
}

echo "=============================================================================="
echo "ARM (a) — WIRED INSTRUMENTS MUST REFUSE, AND LEAVE THE TREE CLEAN"
echo "=============================================================================="
for f in \
  .softhouse/capture/t250-tenant-attestation/instruments/20-redA-sidecar-tracks-the-send.sh \
  .softhouse/capture/t250-tenant-attestation/instruments/30-redB-mismatch-detected.sh \
  .softhouse/capture/t250-tenant-attestation/instruments/40-redC-shapes-not-designed-around.sh \
  .softhouse/capture/t274-attestation-failopen/instruments/10-four-routes-red-green.sh \
  .softhouse/capture/t274-attestation-failopen/instruments/20-wrap-boundary-and-derivation-unchanged.sh \
  .softhouse/capture/t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh \
  .softhouse/reviews/t261-tenant-attestation/instruments/t261-redB-attack.sh \
  .softhouse/reviews/t261-tenant-attestation/instruments/t261-redC-wrap.sh \
  ; do
  echo
  echo "--- $f"
  out="$(cd "$SCRATCH" && bash "$f" 2>&1)"; rc=$?
  if [ "$rc" -eq 2 ]; then ok "exit 2"; else bad "exit $rc, expected 2"; fi
  if printf '%s' "$out" | grep -q "WOULD DESTROY COMMITTED EVIDENCE"; then
    ok "refusal fired: $(printf '%s' "$out" | grep -o 'holds  : [0-9]* TRACKED files')"
  else
    bad "no refusal text. first 6 lines:"; printf '%s\n' "$out" | head -6 | sed 's/^/         /'
  fi
  assert_clean "$(basename "$f")"
done

echo
echo "=============================================================================="
echo "ARM (a-scratch) — THE SANCTIONED ROUTE STILL WORKS: redirected, never in place"
echo "=============================================================================="
f=.softhouse/capture/t274-attestation-failopen/instruments/20-wrap-boundary-and-derivation-unchanged.sh
S="$(mktemp -d)"
echo "--- $f  with T304_EVIDENCE_SCRATCH=$S"
out="$(cd "$SCRATCH" && T304_EVIDENCE_SCRATCH="$S" bash "$f" 2>&1)"; rc=$?
echo "    exit=$rc"
if printf '%s' "$out" | grep -q "redirected to scratch"; then
  ok "guard redirected to the scratch root"
else
  bad "no redirect line; first 8 lines:"; printf '%s\n' "$out" | head -8 | sed 's/^/         /'
fi
assert_clean "the redirected run of $(basename "$f")"

echo
echo "=============================================================================="
echo "ARM (b/c) — DESTRUCTION THAT IS CORRECT BY DESIGN. UNTOUCHED. MUST STILL BE CLEAN."
echo "=============================================================================="
for f in \
  .softhouse/capture/t131-grep/probe-ignorefiles.sh \
  .softhouse/capture/t238-failopen/instruments/30-pr4-nondead-mechanisms.sh \
  .softhouse/capture/t253-portability/instruments/50-t234-residue-probe.sh \
  ; do
  echo
  echo "--- $f"
  out="$(cd "$SCRATCH" && bash "$f" 2>&1)"; rc=$?
  echo "    exit=$rc  (exit code is not the verdict here; the tree is)"
  assert_clean "$(basename "$f")"
done

echo
echo "=============================================================================="
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
