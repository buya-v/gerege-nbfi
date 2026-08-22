#!/usr/bin/env bash
# T273 — RED DRIVE. A fix that cannot be made to FAIL is not proven, and a fix that
# makes the guard green UNCONDITIONALLY is strictly worse than the defect it replaced.
# Three arms, each a source mutation, each restored from git by a trap that runs on
# every exit path including a failure inside an arm.
#
# ENGINE DECLARATION (P-33/P-53/P-75): text is read with BSD /usr/bin/grep by ABSOLUTE
# PATH under LC_ALL=C. Never a bare `grep`, never `rg`. The tree is restored with
# `git checkout --`, and the restoration is VERIFIED with `git status --porcelain`
# rather than assumed.
#
#   R1  A GENUINE TIER REGRESSION must still be caught. The residue repair removed the
#       HOST-dependence of ...02-escape-matrix-fix.sh's tier; it must not have removed
#       the DETECTION. A dead absolute path under one of C1's legacy roots is planted in
#       that file, which flips it TIER2 -> TIER1 for a reason that is IN THE TREE, and
#       the BAR must refuse.
#   R2  A NEW HOST-STATE SITE must be caught by the new guard. A literal /tmp assignment
#       is planted in a repo-wide search instrument; the census must gain a '+' row.
#   R4  THE DEFECT REINTRODUCED, host in the UNLUCKY state. 02-escape-matrix-fix.sh is
#       restored to its pre-T273 bytes from the base revision. With the residue absent the
#       old fail-open pin catches it, exactly as it did before T273.
#   R5  THE DEFECT REINTRODUCED, host in the LUCKY state -- THE ARM THAT MATTERS. Same
#       mutation, but the residue is CREATED first, so the host is in precisely the state
#       that made every green bar before T273 green. The old fail-open pin sees TIER2 ==
#       TIER2 and is satisfied. `guard_frontier_host_sensitivity` must still refuse,
#       because the bracket asks what the tier would be at BOTH extremes of host state and
#       does not care which one this machine happens to be in today. If R5 passes, the
#       repair is reversible by anybody without the harness noticing -- which is the
#       property T273 exists to remove.
#   R3  THE '-' DIRECTION — the amnesty rule. One of the seventeen pinned sites is
#       GENUINELY REPAIRED without touching the pin. The census must lose a row and the
#       BAR must refuse, because a pin that keeps a row for a weakness that is gone has
#       started excusing something that is no longer there.
#
# THE RESIDUE IS ABSENT THROUGHOUT. Every arm below runs with /tmp/t234_matrix2.txt
# deleted, which is the state a clean host is in; the point of the whole task is that
# the verdict must no longer depend on it.
set -u
BASE="${1:-fe24419}"   # the revision holding the PRE-T273 bytes of the mutation target

R="$(git rev-parse --show-toplevel)" || { echo "T273: not in a git work tree"; exit 2; }
cd "$R" || { echo "T273: cannot enter $R"; exit 2; }
OUT="$R/.softhouse/capture/t273-residue/evidence"
mkdir -p "$OUT" || exit 2

M1="$R/.softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh"
M3="$R/.softhouse/reviews/T158-compare-enumerators.sh"
for f in "$M1" "$M3"; do
  [ -f "$f" ] || { echo "T273: mutation target missing: $f"; exit 2; }
done

restore() {
  git checkout -- "$M1" "$M3" 2>/dev/null
  rm -f /tmp/t234_matrix2.txt
}

# THE CLEANLINESS CHECK RUNS BEFORE THE TRAP IS ARMED, AND THE ORDER IS NOT COSMETIC.
# The first draft of this file armed `trap restore EXIT` first and then refused on a
# dirty tree — so the refusal path ran the restore and `git checkout --` DESTROYED THE
# VERY UNCOMMITTED FIX this task exists to make. It happened, it cost a re-apply, and
# it is recorded here rather than quietly corrected: a cleanup trap that can run before
# the script has established it OWNS the tree is a destructive fail-open.
pre_dirty="$(git status --porcelain -- "$M1" "$M3" | LC_ALL=C /usr/bin/grep -c '' || true)"
if [ "${pre_dirty:-0}" -ne 0 ]; then
  echo "T273: REFUSING — the mutation targets are already modified; a restore would destroy work:"
  git status --porcelain -- "$M1" "$M3"
  echo "T273: commit or stash them first. NO TRAP IS ARMED ON THIS PATH; the tree is untouched."
  exit 2
fi
trap restore EXIT

echo "### T273 RED DRIVE"
echo "  tree : $R"
echo "  HEAD : $(git rev-parse HEAD)"
echo "  bash : $BASH_VERSION"
echo "  date : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo

bar() {   # bar <tag> [lucky] -- run the BAR and report the four signals.
          # Default host state is the residue ABSENT, which is what a clean host looks
          # like. Passing `lucky` CREATES it first, reproducing the exact host state that
          # made every pre-T273 green bar green.
  local tag="$1" log="$OUT/50-reddrive-$1.log" rc
  if [ "${2:-}" = "lucky" ]; then
    { printf 'x1y\nxdy\nx y\nxsy\nx_y\nxwy\n'; } >/tmp/t234_matrix2.txt
    echo "  host state       : residue CREATED (the lucky state, 24 bytes)"
  else
    rm -f /tmp/t234_matrix2.txt
    echo "  host state       : residue ABSENT (the clean-host state)"
  fi
  bash "$R/.softhouse/conformance.sh" >"$log" 2>&1
  rc=$?
  echo "  BAR exit code    : $rc"
  echo "  PROBE LINE COUNT : $(LC_ALL=C /usr/bin/grep -ac 'reference oracle .* probe = ' "$log"; :)"
  echo "  VERDICT line     : $(LC_ALL=C /usr/bin/grep -a '^VERDICT' "$log" || echo '(none)')"
  echo "  first refusal    : $(LC_ALL=C /usr/bin/grep -a 'IS NOT THE PINNED' "$log" | head -1 || echo '(none)')"
  local rows
  rows="$(LC_ALL=C /usr/bin/grep -a -E '^[+-](\.softhouse|TIER)' "$log")" || rows=""
  if [ -n "$rows" ]; then
    echo "  diff rows        :"
    printf '%s\n' "$rows" | sed 's/^/      /'
  else
    echo "  diff rows        : (none — no pin diverged)"
  fi
  echo "  log              : ${log#"$R"/}"
  return $rc
}

# --- CONTROL: the unmutated tree, residue absent ----------------------------
echo "=== CONTROL — unmutated tree, /tmp/t234_matrix2.txt ABSENT ==="
bar control && echo "  => GREEN, as required before any negative below is believed (P-72)." \
            || echo "  => NOT GREEN. Every arm below is uninterpretable; stop and read the log."
echo

# --- R1: a genuine TIER regression, in the tree, not on the host ------------
echo "=== R1 — genuine TIER regression planted in 02-escape-matrix-fix.sh ==="
printf 'SRC=/Users/buv/t273-red-drive-corpus-that-does-not-exist/x\n' >>"$M1"
echo "  planted: SRC=/Users/buv/t273-red-drive-corpus-that-does-not-exist/x"
echo "  path exists on this host? $([ -e /Users/buv/t273-red-drive-corpus-that-does-not-exist/x ] && echo YES || echo NO)"
bar r1-tier-regression
r1=$?
git checkout -- "$M1"
[ "$r1" -eq 2 ] && echo "  => R1 CAUGHT (exit 2). The tier detection survived the residue repair." \
                || echo "  => R1 NOT CAUGHT (exit $r1). THE FIX REMOVED THE DETECTION — that is worse than the defect."
echo

# --- R2: a new host-state site ----------------------------------------------
echo "=== R2 — a NEW literal /tmp assignment planted in a repo-wide search instrument ==="
printf 'T273_PLANTED=/tmp/t273-planted-scratch\n' >>"$M1"
echo "  planted: T273_PLANTED=/tmp/t273-planted-scratch"
bar r2-new-host-state-site
r2=$?
git checkout -- "$M1"
[ "$r2" -eq 2 ] && echo "  => R2 CAUGHT (exit 2). A new host-state site cannot enter the lint corpus silently." \
                || echo "  => R2 NOT CAUGHT (exit $r2). The new guard is inert."
echo

# --- R3: the '-' direction — a genuine repair with a stale pin --------------
echo "=== R3 — one pinned site GENUINELY REPAIRED, pin left stale (the amnesty rule) ==="
LC_ALL=C sed -i.t273bak 's%^C=/tmp/t158-clone$%C="$(mktemp -d "${TMPDIR:-/tmp}/t158-clone.XXXXXXXXXX")"%' "$M3"
rm -f "$M3.t273bak"
echo "  repaired line now reads: $(LC_ALL=C /usr/bin/grep -a -n 'mktemp -d' "$M3" | head -1 || echo '(SED DID NOT APPLY — R3 is void)')"
bar r3-stale-pin-minus-row
r3=$?
git checkout -- "$M3"
[ "$r3" -eq 2 ] && echo "  => R3 CAUGHT (exit 2). A '-' row refuses: the pin cannot outlive the weakness." \
                || echo "  => R3 NOT CAUGHT (exit $r3). The pin would quietly excuse a repaired site."
echo

# --- R4/R5: the repair itself reverted, in both host states -----------------
git rev-parse --verify -q "$BASE^{commit}" >/dev/null || { echo "T273: no such revision: $BASE"; exit 2; }
echo "=== R4 — 02-escape-matrix-fix.sh restored to its PRE-T273 bytes from $BASE, host UNLUCKY ==="
git checkout "$BASE" -- "$M1" || exit 2
echo "  line 6 now reads : $(LC_ALL=C sed -n '6p' "$M1")"
bar r4-defect-reintroduced-unlucky
r4=$?
[ "$r4" -eq 2 ] && echo "  => R4 CAUGHT (exit 2)." || echo "  => R4 NOT CAUGHT (exit $r4)."
echo

echo "=== R5 — SAME reverted bytes, host in the LUCKY state (residue present) ==="
echo "  This is the state every pre-T273 green bar was recorded in. The OLD pin is satisfied"
echo "  by it. The bracket guard must refuse anyway."
bar r5-defect-reintroduced-lucky lucky
r5=$?
frontier_ok=$(LC_ALL=C /usr/bin/grep -ac 'frontier == pinned' "$OUT/50-reddrive-r5-defect-reintroduced-lucky.log" ; :)
delta_bad=$(LC_ALL=C /usr/bin/grep -ac 'HOST-SENSITIVE FRONTIER DELTA IS NOT THE PINNED DELTA' "$OUT/50-reddrive-r5-defect-reintroduced-lucky.log" ; :)
echo "  old fail-open pin SATISFIED in this run? $([ "${frontier_ok:-0}" -ge 1 ] && echo YES || echo NO)"
echo "  bracket guard REFUSED in this run?       $([ "${delta_bad:-0}" -ge 1 ] && echo YES || echo NO)"
git checkout HEAD -- "$M1"
if [ "$r5" -eq 2 ] && [ "${frontier_ok:-0}" -ge 1 ] && [ "${delta_bad:-0}" -ge 1 ]; then
  echo "  => R5 CAUGHT BY THE NEW GUARD ALONE. The old pin saw nothing wrong; the bracket did."
  r5ok=1
else
  echo "  => R5 DID NOT DISCRIMINATE (exit $r5). The repair would be silently reversible."
  r5ok=0
fi
echo

# --- restoration, VERIFIED --------------------------------------------------
restore
post_dirty="$(git status --porcelain -- "$M1" "$M3" | LC_ALL=C /usr/bin/grep -c '' || true)"
echo "### RESTORED — mutation targets modified after restore: ${post_dirty:-0} (0 required)"
echo "### residue /tmp/t234_matrix2.txt at exit: $([ -e /tmp/t234_matrix2.txt ] && echo PRESENT || echo ABSENT)"
echo "### SUMMARY  R1=$r1  R2=$r2  R3=$r3  R4=$r4  R5=$r5 (discriminated=$r5ok)   (2 = caught)"
if [ "$r1" -eq 2 ] && [ "$r2" -eq 2 ] && [ "$r3" -eq 2 ] && [ "$r4" -eq 2 ] \
   && [ "$r5" -eq 2 ] && [ "$r5ok" -eq 1 ] && [ "${post_dirty:-1}" -eq 0 ]; then
  echo "### RED DRIVE: 5/5 CAUGHT, tree restored, residue absent at exit."
  exit 0
fi
echo "### RED DRIVE: NOT 5/5 — read the arms above."
exit 1
