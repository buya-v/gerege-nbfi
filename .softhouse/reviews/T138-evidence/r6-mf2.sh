#!/bin/sh
# T138 — independent re-derivation of MF-2, and of T115's NEGATIVE claim that MF-2
# does NOT close N9 or N10.  Written from scratch; t115-drive-mf2.sh was not invoked.
#
# Baselines are literal immutable shas (P-24):
#   PRE  tree  = ccf3c14171dea52bd044d81d5ca67aba8054b74c   (T91 tip)
#   POST tree  = bd59187cf83c7c7161db23668e91d45bd46be2a8   (T115 tip)
#   pre-hardening rig/shim blob = e6c1795a172168105d788321a71ee4ca62b73e36
# Every destructive step happens inside a `git archive` export under /tmp.
# Oracle contact: read-only psql/docker + POST /loans?command=calculateLoanSchedule only.
set -u
C=${1:?usage: r6-mf2.sh <git checkout>}
PRE_SHA=ccf3c14171dea52bd044d81d5ca67aba8054b74c
POST_SHA=bd59187cf83c7c7161db23668e91d45bd46be2a8
BLOB=e6c1795a172168105d788321a71ee4ca62b73e36

export_at() {  # export_at <sha> <dir>
  rm -rf "$2"; mkdir -p "$2"
  (cd "$C" && git archive "$1") | tar -x -C "$2"
}
A=/tmp/T138-mf2-pre;  export_at "$PRE_SHA"  "$A"
B=/tmp/T138-mf2-post; export_at "$POST_SHA" "$B"
SHIM=.softhouse/capture/charges/bin/preconditions.sh
RIG=.softhouse/capture/pathb/t36/preconditions.sh
CANON=.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json

echo "PRE  shim sha256 $(shasum -a 256 "$A/$SHIM" | cut -c1-16)   POST shim sha256 $(shasum -a 256 "$B/$SHIM" | cut -c1-16)"
echo "rig sha256 (both exports) $(shasum -a 256 "$A/$RIG" | cut -c1-16) / $(shasum -a 256 "$B/$RIG" | cut -c1-16)"
LC_ALL=C grep -q 'returned without exiting' "$A/$SHIM" && { echo "ABORT: PRE already has MF-2"; exit 2; }
LC_ALL=C grep -q 'returned without exiting' "$B/$SHIM" || { echo "ABORT: POST lacks MF-2"; exit 2; }
echo

echo "=================================================================="
echo "MF-2 PREMISE re-measured: exit statements in the hardened rig"
echo "=================================================================="
LC_ALL=C grep -n '^[[:space:]]*exit ' "$B/$RIG" | sed 's/^/   /'
echo "   total 'exit' statements: $(LC_ALL=C grep -c '^[[:space:]]*exit ' "$B/$RIG")"
echo "   function definitions in the rig:"
LC_ALL=C grep -n '^[a-zA-Z_][a-zA-Z_0-9]*()' "$B/$RIG" | sed 's/^/      /'
echo

echo "=================================================================="
echo "MF-2 RED — the rig EMPTIED"
echo "=================================================================="
for t in pre post; do
  E=$A; [ "$t" = post ] && E=$B
  X=/tmp/T138-mf2-empty-$t; rm -rf "$X"; cp -R "$E" "$X"
  : > "$X/$RIG"
  echo "--- $t, DIRECT call"
  CANARY_REQ="$X/$CANON" sh "$X/$SHIM" gerege > "$X/direct.txt" 2>"$X/direct.err"
  rc=$?
  echo "    exit=$rc  stdout bytes=$(wc -c < "$X/direct.txt" | tr -d ' ')  stderr bytes=$(wc -c < "$X/direct.err" | tr -d ' ')"
  [ -s "$X/direct.err" ] && sed 's/^/    stderr: /' "$X/direct.err"
  echo "--- $t, through bin/run-preconditions.sh (the T40 wrapper)"
  T40_WORKTREE="$X" sh "$X/.softhouse/capture/charges/bin/run-preconditions.sh" "$X/wrap.txt" > "$X/wrapout.txt" 2>&1
  rc=$?
  echo "    exit=$rc  transcript bytes=$(wc -c < "$X/wrap.txt" | tr -d ' ')"
  LC_ALL=C grep -a 'PRECONDITIONS_EXIT' "$X/wrapout.txt" | sed 's/^/    /'
  [ -s "$X/wrap.txt" ] && sed 's/^/    transcript: /' "$X/wrap.txt"
  echo
done

echo "=================================================================="
echo "MF-2 GREEN — five real callers, pre vs post, against the LIVE oracle"
echo "=================================================================="
cells() {  # cells <file>
  p=$(LC_ALL=C grep -ac '^  PASS ' "$1"); f=$(LC_ALL=C grep -ac '^  FAIL ' "$1")
  echo "$p/$f"
}
for t in pre post; do
  E=$A; [ "$t" = post ] && E=$B
  W=/tmp/T138-mf2-green-$t; rm -rf "$W"; cp -R "$E" "$W"
  echo "--- tree: $t"
  # C1: the T40 wrapper, tenant gerege
  T40_WORKTREE="$W" sh "$W/.softhouse/capture/charges/bin/run-preconditions.sh" "$W/c1.txt" >/dev/null 2>&1
  echo "    C1 wrapper/gerege                 $(cells "$W/c1.txt")/$(T40_WORKTREE="$W" sh "$W/.softhouse/capture/charges/bin/run-preconditions.sh" "$W/c1.txt" >/dev/null 2>&1; echo $?)"
  # C2: t51-negative.sh's form — direct, tenant default, no CANARY_REQ
  sh "$W/$SHIM" default > "$W/c2.txt" 2>&1; rc2=$?
  echo "    C2 direct/default/no CANARY_REQ   $(cells "$W/c2.txt")/$rc2"
  # C3: t55-negative-tests.sh N2 — a tenant with no row
  CANARY_REQ="$W/$CANON" sh "$W/$SHIM" t55-no-such-tenant > "$W/c3.txt" 2>&1; rc3=$?
  echo "    C3 direct/t55-no-such-tenant      $(cells "$W/c3.txt")/$rc3"
  echo "       'has no row in fineract_tenants.tenants' occurrences: $(LC_ALL=C grep -ac 'has no row in fineract_tenants.tenants' "$W/c3.txt")"
  # C4: T44's control through preconditions-COPY.sh, tenant default
  CANARY_REQ="$W/$CANON" sh "$W/.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh" default > "$W/c4.txt" 2>&1; rc4=$?
  echo "    C4 COPY shim/default              $(cells "$W/c4.txt")/$rc4"
  # C5: C1's call from a foreign CWD, absolute path
  (cd /tmp && T40_WORKTREE="$W" sh "$W/.softhouse/capture/charges/bin/run-preconditions.sh" "$W/c5.txt" >/dev/null 2>&1)
  rc5=$?
  echo "    C5 wrapper from /tmp              $(cells "$W/c5.txt")/$rc5"
  echo
done
echo "--- cell-for-cell diff of the five transcripts, pre vs post (headers aside):"
for c in c1 c2 c3 c4 c5; do
  if diff -q /tmp/T138-mf2-green-pre/$c.txt /tmp/T138-mf2-green-post/$c.txt >/dev/null 2>&1; then
    echo "    $c: byte-identical"
  else
    echo "    $c: differs —"
    diff /tmp/T138-mf2-green-pre/$c.txt /tmp/T138-mf2-green-post/$c.txt | head -8 | sed 's/^/       /'
  fi
done
echo

echo "=================================================================="
echo "N9 — the rig at its path REPLACED by the pre-hardening bytes,"
echo "     measured THROUGH the POST-MF-2 shim"
echo "=================================================================="
X=/tmp/T138-n9; rm -rf "$X"; cp -R "$B" "$X"
(cd "$C" && git cat-file blob "$BLOB") > "$X/$RIG"
echo "   rig now sha256 $(shasum -a 256 "$X/$RIG" | cut -d' ' -f1)"
echo "   (T91 records the pre-hardening blob's sha256 as 9256b881153d3dea…)"
echo "   shim is the POST-MF-2 one: $(LC_ALL=C grep -c 'returned without exiting' "$X/$SHIM") MF-2 marker(s) present"
CANARY_REQ="$X/$CANON" sh "$X/$SHIM" gerege > "$X/n9.txt" 2>&1; rc=$?
echo "   EXIT=$rc"
tail -4 "$X/n9.txt" | sed 's/^/   /'
LC_ALL=C grep -a 'effective rounding mode canary' "$X/n9.txt" | sed 's/^/   /'
echo

echo "=================================================================="
echo "N10 — the shim reached through a SYMLINK placed in a foreign tree,"
echo "      measured THROUGH the POST-MF-2 shim"
echo "=================================================================="
Y=/tmp/T138-n10; rm -rf "$Y"; mkdir -p "$Y/evil/pathb/t36" "$Y/evil/charges/bin"
cat > "$Y/evil/pathb/t36/preconditions.sh" <<'STUB'
# ATTACKER'S STUB — asserts nothing, certifies everything.
echo "  PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)"
echo "ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only."
exit 0
STUB
ln -s "$B/$SHIM" "$Y/evil/charges/bin/preconditions.sh"
echo "   symlink: $Y/evil/charges/bin/preconditions.sh -> $(readlink "$Y/evil/charges/bin/preconditions.sh")"
echo "   the shim resolves its rig as \$(dirname \$0)/../../pathb/t36/preconditions.sh"
CANARY_REQ="$B/$CANON" sh "$Y/evil/charges/bin/preconditions.sh" gerege > "$Y/n10.txt" 2>&1; rc=$?
echo "   EXIT=$rc"
sed 's/^/   /' "$Y/n10.txt"
echo
echo "=== SUMMARY"
echo "N9  exit was printed above; N10 exit was printed above."
