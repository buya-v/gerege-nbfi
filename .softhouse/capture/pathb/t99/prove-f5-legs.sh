#!/bin/sh
# T152 — THE FOUR F-5 LEGS, AS A COMMITTED, RE-RUNNABLE ARTEFACT.
#
# F-5: `preconditions.sh` P5 (`$banned`), P6 (`$jarhits`) and P11 (`$scp`) each asserted an ABSENCE.
# `grep -icE` over an empty stream counts 0 and a `psql` that never ran returns the empty string, so
# a `docker` answering nothing produced three PASS lines carrying the CLAUDE.md "PostgreSQL is the
# only database / Oracle Database, MySQL and MariaDB are prohibited" non-negotiable — having scanned
# nothing.  The fix is a LIVENESS OPERAND on each: empty input is a FAIL that says the scan did not
# happen, never a PASS.
#
# T99b ran three legs and T135 re-ran them independently and added a fourth.  None of the four
# existed in this branch as a script or a transcript — T135 §7.1's complaint, which P-22 states in
# terms: "state the input that makes it fail, and commit the transcript".  This is that artefact.
#
#   RED       docker AND curl stubbed to exit 1.  main: 3 PASS / 18 FAIL, and THE ONLY THREE PASS
#             LINES IN THE WHOLE SUITE ARE THE THREE PROHIBITION ASSERTIONS.  branch: 0 PASS / 21.
#   GREEN     the live reference oracle, both sides.  22 PASS / 0 FAIL on BOTH — nothing was
#             weakened — and on the branch each verdict carries its witness count.
#   POSITIVE  a poisoned `docker` that ANSWERS, with mariadb in the env, a mysql-connector jar and a
#   CONTROL   MySQL-shaped tenant row.  Both sides must FAIL all three: the fix must not be
#             "refuse everything".  Without this leg, "0 PASS" is indistinguishable from a script
#             that has stopped working.
#   PARTIAL   the realistic outage: the fineract container is gone, the DB is alive, `docker` is
#   OUTAGE    REAL.  main prints 15 PASS / 7 FAIL with TWO vacuous PASSes; the branch 13 / 9, and
#             it fails both.  P11 is NOT vacuous here because the database really does answer —
#             which is the point: the three assertions have three different emptiness SOURCES and
#             only this leg separates them.  And it yields the sharpest statement of F-5 available:
#             main's P11 PASS line on this leg (a real observation) is BYTE-IDENTICAL to main's
#             P11 PASS line on the RED leg (nothing read at all).
#
# ORACLE SAFETY.  Read-only `docker inspect` / `docker exec ... psql` / `unzip -l`, plus the pinned
# canary POST /loans?command=calculateLoanSchedule, which is a pure calculation.  No restart, no
# rebuild, no re-seed, no write.  The poisoned and stubbed legs never reach the server at all.
#
# Usage:  sh prove-f5-legs.sh
# Exit:   0 = all four legs behaved as stated above; 1 = at least one did not; 2 = setup failed.
set -u

T99=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$T99" rev-parse --show-toplevel)
PB=.softhouse/capture/pathb
W=${T152_F5_WORK:-/tmp/t152-f5}
TENANT=gerege

die() { printf 'F5 LEG PROOF ABORT: %s\n' "$1" >&2; exit 2; }

# The pre-fix baseline is the LITERAL sha, for the reason lib.sh and FORK-POINT-SHA give.
PREFIX=$(LC_ALL=C grep -vE '^[[:space:]]*(#|$)' "$T99/FORK-POINT-SHA" | tail -n 1 | tr -d '[:space:]')
case "$PREFIX" in *[!0-9a-f]* | "") die "FORK-POINT-SHA does not hold a hex sha" ;; esac

rm -rf "$W" || die "cannot clear $W"
mkdir -p "$W/main" "$W/branch" "$W/deadbin" "$W/poisonbin" "$W/gonebin" || die "cannot create $W"
git -C "$REPO" archive "$PREFIX" | tar -x -C "$W/main"   || die "archive $PREFIX failed"
git -C "$REPO" archive HEAD      | tar -x -C "$W/branch" || die "archive HEAD failed"

echo "=== T152 — the four F-5 legs"
echo "main   (pre-fix) = $PREFIX   [literal, from t99/FORK-POINT-SHA]"
echo "branch (fixed)   = $(git -C "$REPO" rev-parse HEAD)"
echo "tenant           = $TENANT"

# ------------------------------------------------------------------ the three doubles
for t in docker curl; do
  printf '#!/bin/sh\nexit 1\n' > "$W/deadbin/$t"
  chmod +x "$W/deadbin/$t"
done

# `command -v` is the right instrument HERE and only here: this file always runs as `sh <file>`, so
# shell functions are not inherited and there is nothing for it to shadow (P-33 names the trap; the
# trap is the Bash tool, not a script).  The result is asserted executable before it is used.
REALDOCKER=$(command -v docker 2>/dev/null)
[ -n "${REALDOCKER:-}" ] && [ -x "$REALDOCKER" ] || die "cannot locate the real docker binary"
echo "real docker      = $REALDOCKER"

# A poisoned docker: everything is delegated to the real binary EXCEPT the three answers under
# test, each of which gets one prohibited string added.  It ANSWERS — that is what makes it a
# positive control rather than another emptiness test.
cat > "$W/poisonbin/docker" <<POISON
#!/bin/sh
REAL=$REALDOCKER
all="\$*"
case "\$all" in
  *Config.Env*)
      "\$REAL" "\$@"
      echo 'FINERACT_HIKARI_JDBC_URL=jdbc:mariadb://db:3306/fineract_tenants'
      exit 0 ;;
  *unzip\ -l*)
      "\$REAL" "\$@"
      echo '    12345  01-01-2026 00:00   BOOT-INF/lib/mysql-connector-j-8.3.0.jar'
      exit 0 ;;
  *schema_connection_parameters*)
      # Bracketed, so BOTH sides see a value: main's query has no wrapper and prints it raw,
      # the branch's wrapper-aware arm strips the brackets.  Either way it is a FAIL, which is
      # the point of a positive control.
      echo '[serverTimezone=UTC&useLegacyDatetimeCode=false]'
      exit 0 ;;
esac
exec "\$REAL" "\$@"
POISON
chmod +x "$W/poisonbin/docker"

# A docker whose fineract container name does not resolve.  The DB container is untouched, so this
# is a PARTIAL outage and the errors are docker's own, not a stub's.
# THE REWRITE MUST BE ARGUMENT-EXACT.  The first version of this double did
#     set -- $(printf '%s\n' "$@" | sed 's/^fineract-fineract-1$/.../')
# which word-splits the WHOLE argument list — so `psql -c "select ... where t.identifier='gerege';"`
# arrived as a dozen separate arguments and the DATABASE queries broke too.  The leg then reported
# main 7 PASS / 15 FAIL with THREE vacuous PASSes, which is not a partial outage at all: it is the
# total outage of leg 1 with extra steps.  That is P-36 — the manipulated variable reached more
# than the subject — and it looked exactly like a result.  Rebuild the list one argument at a time.
cat > "$W/gonebin/docker" <<GONE
#!/bin/sh
REAL=$REALDOCKER
i=\$#
while [ "\$i" -gt 0 ]; do
  a=\$1; shift
  case "\$a" in fineract-fineract-1) a=fineract-fineract-1-DOES-NOT-EXIST ;; esac
  set -- "\$@" "\$a"
  i=\$((i-1))
done
exec "\$REAL" "\$@"
GONE
chmod +x "$W/gonebin/docker"

# ------------------------------------------------------------------------------ the leg runner
leg() {   # <legname> <side> <extra PATH dir or ->  <live 0|1>
  _leg=$1; _side=$2; _bin=$3; _live=$4
  _base=$W/$_side/$PB
  _o=$W/$_leg-$_side.out; _e=$W/$_leg-$_side.err
  _p=$PATH
  [ "$_bin" = - ] || _p=$_bin:$PATH
  if [ "$_live" = 1 ]; then
    ( cd "$_base/t36" && PATH=$_p CANARY_REQ=$_base/t22-audit/req/calc-pmode2-$TENANT.json \
        sh preconditions.sh "$TENANT" ) > "$_o" 2> "$_e"
  else
    ( cd "$_base/t36" && PATH=$_p sh preconditions.sh "$TENANT" ) > "$_o" 2> "$_e"
  fi
  _st=$?
  _pass=$(LC_ALL=C grep -ac '^  PASS' "$_o" || true)
  _fail=$(LC_ALL=C grep -ac '^  FAIL' "$_e" || true)
  printf '  %-8s EXIT=%s  PASS=%-3s FAIL=%s\n' "$_side" "$_st" "$_pass" "$_fail"
  LEG_PASS=$_pass; LEG_FAIL=$_fail; LEG_ST=$_st
}

verdicts() {   # <legname> <side>
  LC_ALL=C cat "$W/$1-$2.out" "$W/$1-$2.err" 2>/dev/null \
    | LC_ALL=C grep -aE 'prohibited-engine|prohibited driver jars|prohibited-driver-jar|schema_connection_parameters' \
    | cut -c1-118 | sed 's/^/      /'
}

rc=0
note() { echo "  >> $1"; }
check() { if [ "$1" = "$2" ]; then echo "  OK   $3 = $1"; else echo "  ****  $3 = $1, EXPECTED $2"; rc=1; fi; }

# ---------------------------------------------------------------------------------------- RED
echo
echo "=== LEG 1 — RED: docker AND curl stubbed to exit 1 (nothing to scan, anywhere)"
leg red main "$W/deadbin" 0
RED_MAIN_PASS=$LEG_PASS; RED_MAIN_FAIL=$LEG_FAIL
verdicts red main
note "in a completely dead environment the ONLY PASS lines in the entire suite are these three,"
note "and they are the three that carry the CLAUDE.md database-prohibition non-negotiable."
leg red branch "$W/deadbin" 0
RED_BR_PASS=$LEG_PASS; RED_BR_FAIL=$LEG_FAIL
verdicts red branch
check "$RED_MAIN_PASS" 3  "main   RED PASS"
check "$RED_MAIN_FAIL" 18 "main   RED FAIL"
check "$RED_BR_PASS"   0  "branch RED PASS"
check "$RED_BR_FAIL"   21 "branch RED FAIL"

# -------------------------------------------------------------------------------------- GREEN
echo
echo "=== LEG 2 — GREEN: the live reference oracle, both sides"
leg green main - 1
GR_MAIN_PASS=$LEG_PASS; GR_MAIN_FAIL=$LEG_FAIL
leg green branch - 1
GR_BR_PASS=$LEG_PASS; GR_BR_FAIL=$LEG_FAIL
echo "    branch witnesses:"
LC_ALL=C grep -aE 'env line\(s\) actually scanned|jar entry line\(s\) actually scanned|a row was returned|ALL PRECONDITIONS HOLD' \
  "$W/green-branch.out" | cut -c1-118 | sed 's/^/      /'
check "$GR_MAIN_PASS" 22 "main   GREEN PASS"
check "$GR_MAIN_FAIL" 0  "main   GREEN FAIL"
check "$GR_BR_PASS"   22 "branch GREEN PASS"
check "$GR_BR_FAIL"   0  "branch GREEN FAIL"
ENVW=$(LC_ALL=C sed -n 's/.*(\([0-9]*\) env line(s) actually scanned).*/\1/p' "$W/green-branch.out" | head -1)
JARW=$(LC_ALL=C sed -n 's/.*(\([0-9]*\) jar entry line(s) actually scanned).*/\1/p' "$W/green-branch.out" | head -1)
check "$ENVW" 47   "env-line witness"
check "$JARW" 5406 "jar-entry witness"
note "22 PASS on BOTH sides, so the liveness operands weakened nothing; the branch additionally"
note "prints what each scan actually read, which is the difference between 'clean' and 'not looked'."

# --------------------------------------------------------------------------- POSITIVE CONTROL
echo
echo "=== LEG 3 — POSITIVE CONTROL: a poisoned docker that ANSWERS (mariadb env, mysql-connector"
echo "    jar, MySQL-shaped tenant row).  Both sides must still FAIL all three."
leg pc main "$W/poisonbin" 1
PC_MAIN_FAIL3=$(verdicts pc main | LC_ALL=C grep -ac 'FAIL' || true)
verdicts pc main
leg pc branch "$W/poisonbin" 1
PC_BR_FAIL3=$(verdicts pc branch | LC_ALL=C grep -ac 'FAIL' || true)
verdicts pc branch
check "$PC_MAIN_FAIL3" 3 "main   prohibition FAILs"
check "$PC_BR_FAIL3"   3 "branch prohibition FAILs"
note "the fix is not 'refuse everything': the assertions still fire for their REAL reason."

# ------------------------------------------------------------------------------- FOURTH LEG
echo
echo "=== LEG 4 — PARTIAL OUTAGE: the fineract container is gone, the DB is alive, docker is REAL"
leg gone main "$W/gonebin" 1
GONE_MAIN_PASS=$LEG_PASS; GONE_MAIN_FAIL=$LEG_FAIL
verdicts gone main
leg gone branch "$W/gonebin" 1
GONE_BR_PASS=$LEG_PASS; GONE_BR_FAIL=$LEG_FAIL
verdicts gone branch
# THE APPARATUS CHECK COMES FIRST (P-36): if the DB is not answering, this is not a partial
# outage and none of the rows below mean what they say.  P12 reads the SAME psql join as P11.
DBLIVE=$(LC_ALL=C grep -ac 'PASS  tenant schema_server_port = 5432' "$W/gone-main.out" || true)
check "$DBLIVE" 1 "apparatus: the DATABASE still answered (P12 from the same join)"
# Vacuity is per assertion.  Exactly TWO of the three read the dead container (P5's env dump and
# P6's jar listing); P11 reads the LIVE database, so on this leg its PASS is a real observation.
GONE_MAIN_VAC=0
LC_ALL=C grep -qa '^  PASS  0 prohibited-engine hits' "$W/gone-main.out" && GONE_MAIN_VAC=$((GONE_MAIN_VAC+1))
LC_ALL=C grep -qa '^  PASS  0 prohibited driver jars' "$W/gone-main.out" && GONE_MAIN_VAC=$((GONE_MAIN_VAC+1))
GONE_BR_INSP=$(LC_ALL=C grep -ac 'INSPECTED NOTHING' "$W/gone-branch.err" || true)
check "$GONE_MAIN_VAC" 2 "main   vacuous prohibition PASSes on the partial outage"
check "$GONE_BR_INSP"  2 "branch INSPECTED NOTHING messages"
note "P11 is NOT vacuous here — the database really answers, so its PASS is a REAL observation."
note "That is the point of this leg: the three assertions have three different emptiness SOURCES,"
note "and only a partial outage separates them.  A total outage makes all three look alike."
# AND HERE IS THE WHOLE OF F-5 IN TWO LINES.  main's P11 PASS on this leg (real) is BYTE-IDENTICAL
# to main's P11 PASS on leg 1 (vacuous).  The branch's is not: it carries its witness.
echo "    main   P11, partial outage: $(LC_ALL=C grep -a 'schema_connection_parameters is empty' "$W/gone-main.out" | sed 's/^ *//')"
echo "    main   P11, TOTAL   outage: $(LC_ALL=C grep -a 'schema_connection_parameters is empty' "$W/red-main.out" | sed 's/^ *//')"
echo "    branch P11, partial outage: $(LC_ALL=C grep -a 'schema_connection_parameters is empty' "$W/gone-branch.out" | sed 's/^ *//')"
M_REAL=$(LC_ALL=C grep -a 'schema_connection_parameters is empty' "$W/gone-main.out" | sed 's/^ *//')
M_VAC=$(LC_ALL=C grep -a 'schema_connection_parameters is empty' "$W/red-main.out" | sed 's/^ *//')
if [ "$M_REAL" = "$M_VAC" ]; then
  echo "  OK   main's two P11 PASS lines are BYTE-IDENTICAL — one read a row, one read nothing,"
  echo "       and no reader of the transcript can tell which.  That is F-5."
else
  echo "  ****  main's two P11 PASS lines differ, so this demonstration does not hold"; rc=1
fi


echo
echo "=== VERDICT"
if [ "$rc" = 0 ]; then
  echo "RESULT: all four F-5 legs reproduce.  RED 3/18 -> 0/21; GREEN 22/0 on both sides with the"
  echo "        47 and 5406 witnesses; the poisoned docker still fails 3 on both sides; and on a"
  echo "        partial outage main prints two vacuous PASSes where the branch says INSPECTED"
  echo "        NOTHING.  The three assertions are no longer capable of passing on no input."
else
  echo "RESULT: AT LEAST ONE LEG DID NOT BEHAVE AS STATED — see the **** rows above."
fi
exit $rc
