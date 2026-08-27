#!/bin/sh
# T138 — MF-2 GREEN, corrected.  My first pass ran C3 WITH a CANARY_REQ; the real
# form (leapboundary/bin/t55-negative-tests.sh:52, N2) passes none.  Re-run in the
# true form and normalise the export path out of the digest line before diffing.
set -u
A=/tmp/T138-mf2-pre; B=/tmp/T138-mf2-post
SHIM=.softhouse/capture/charges/bin/preconditions.sh
CANON=.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json
cells() { printf '%s/%s' "$(LC_ALL=C grep -ac '^  PASS ' "$1")" "$(LC_ALL=C grep -ac '^  FAIL ' "$1")"; }

for t in pre post; do
  W=$A; [ "$t" = post ] && W=$B
  echo "--- tree: $t   ($W)"
  T40_WORKTREE="$W" sh "$W/.softhouse/capture/charges/bin/run-preconditions.sh" "$W/g1.txt" >/dev/null 2>&1; r1=$?
  echo "    C1 wrapper/gerege                        $(cells "$W/g1.txt")/$r1"
  sh "$W/$SHIM" default > "$W/g2.txt" 2>&1; r2=$?
  echo "    C2 direct/default/no CANARY_REQ          $(cells "$W/g2.txt")/$r2"
  sh "$W/$SHIM" t55-no-such-tenant > "$W/g3.txt" 2>&1; r3=$?
  echo "    C3 direct/t55-no-such-tenant/no CANARY   $(cells "$W/g3.txt")/$r3"
  echo "       'has no row in fineract_tenants.tenants': $(LC_ALL=C grep -ac 'has no row in fineract_tenants.tenants' "$W/g3.txt")"
  CANARY_REQ="$W/$CANON" sh "$W/.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh" default > "$W/g4.txt" 2>&1; r4=$?
  echo "    C4 COPY shim/default                     $(cells "$W/g4.txt")/$r4"
  (cd /tmp && T40_WORKTREE="$W" sh "$W/.softhouse/capture/charges/bin/run-preconditions.sh" "$W/g5.txt" >/dev/null 2>&1); r5=$?
  echo "    C5 wrapper from /tmp                     $(cells "$W/g5.txt")/$r5"
done
echo
echo "--- cell-for-cell, pre vs post, with the export path normalised out:"
for g in g1 g2 g3 g4 g5; do
  LC_ALL=C sed "s|$A|EXPORT|g" "$A/$g.txt" > /tmp/T138-n-$g-a
  LC_ALL=C sed "s|$B|EXPORT|g" "$B/$g.txt" > /tmp/T138-n-$g-b
  if diff -q /tmp/T138-n-$g-a /tmp/T138-n-$g-b >/dev/null; then
    echo "    $g: IDENTICAL after path normalisation"
  else
    echo "    $g: DIFFERS —"; diff /tmp/T138-n-$g-a /tmp/T138-n-$g-b | head -10 | sed 's/^/       /'
  fi
done
echo
echo "--- MF-2 message byte count is PATH-DEPENDENT (T115 reports 162):"
for p in /tmp/x /tmp/T138-mf2-empty-post/.softhouse/capture/pathb/t36/preconditions.sh; do
  printf "PRECONDITIONS NOT RUN: the rig at '%s' returned without exiting — nothing was asserted.\n" "$p" | wc -c | tr -d ' ' | sed "s|^|    len for path '$p' = |"
done
