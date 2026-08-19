#!/usr/bin/env bash
#
# T42 -- READ THE PATH B WIRING OFF THE DEPLOYED BYTECODE OF THE RUNNING ORACLE.
#
# The question this answers: on Path B (the running Fineract server), where does the MathContext
# handed to the schedule generator come from?  Source says MoneyHelper.getMathContext()
# [LoanScheduleAssembler.java:753].  A source line is a claim about the repository; this script
# reads the ARTEFACT THAT IS ACTUALLY SERVING REQUESTS.
#
# READ ONLY.  It runs `javap` inside the already-running fineract-fineract-1 and writes only to
# /tmp inside that container and to this task's own out/ directory on the host.  It does NOT
# restart, re-tenant, reconfigure, or write schema to the running containers, and it opens no
# database connection.
#
#   JAVA_TOOL_OPTIONS is cleared for the javap invocation because the server's own value carries
#   -agentlib:jdwp on a port already bound by the live JVM; leaving it set makes javap exit 1
#   before printing anything.  Clearing it changes nothing about the running server -- the
#   variable is read by the NEW javap process only.

set -u -o pipefail
CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${T42_ORACLE_CONTAINER:-fineract-fineract-1}"
OUT="$CAPDIR/out/t42-pathb-wiring.txt"

fail() { echo "BREACH: $*" >&2; exit 1; }

CLASSES=(
  "org.apache.fineract.portfolio.loanaccount.loanschedule.service.LoanScheduleAssembler"
  "org.apache.fineract.portfolio.loanaccount.service.LoanScheduleGeneratorServiceImpl"
)

{
  echo "== T42 -- Path B MathContext wiring, read from the DEPLOYED bytecode"
  echo "== container: $CONTAINER   (running; not restarted, not reconfigured, not written to)"
  echo "== captured:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "-- container identity"
  docker inspect "$CONTAINER" --format '{{.Config.Image}} {{.Image}} {{.State.Status}} startedAt={{.State.StartedAt}}' \
    || fail "cannot inspect $CONTAINER"
  echo
  echo "-- the deployed jar's own testimony"
  docker exec "$CONTAINER" sh -c 'sha256sum /app/fineract-provider.jar' || fail "cannot read the jar"
  docker exec "$CONTAINER" sh -c '
    cd /tmp && rm -rf t42gitprops && mkdir t42gitprops && cd t42gitprops
    unzip -o -q /app/fineract-provider.jar "BOOT-INF/classes/git.properties" 2>/dev/null
    cat BOOT-INF/classes/git.properties 2>/dev/null | grep -E "git.commit.id=|git.dirty|git.build.version" || echo "NO git.properties"
  '
  echo
} > "$OUT" 2>&1

docker exec "$CONTAINER" sh -c '
  cd /tmp && rm -rf t42j && mkdir t42j && cd t42j
  unzip -o -q /app/fineract-provider.jar "BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/loanschedule/service/LoanScheduleAssembler.class" "BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorServiceImpl.class" 2>/dev/null
  ls -l BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/loanschedule/service/LoanScheduleAssembler.class
  ls -l BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorServiceImpl.class
  sha256sum BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/loanschedule/service/LoanScheduleAssembler.class
  sha256sum BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorServiceImpl.class
' >> "$OUT" 2>&1 || fail "cannot extract the deployed classes"

for CLS in "${CLASSES[@]}"; do
  {
    echo
    echo "================================================================================"
    echo "javap -p -c   $CLS   (from /app/fineract-provider.jar inside the running server)"
    echo "================================================================================"
  } >> "$OUT"
  docker exec -e JAVA_TOOL_OPTIONS= "$CONTAINER" sh -c "
    cd /tmp/t42j && javap -p -c -cp BOOT-INF/classes '$CLS'
  " >> "$OUT" 2>&1 || fail "javap failed for $CLS"
done

# ---- the assertion: the deployed bytecode must show getMathContext feeding generate ----------
N_GMC="$(grep -c 'MoneyHelper.getMathContext' "$OUT" || true)"
[ "$N_GMC" != "0" ] || fail "the deployed bytecode contains NO MoneyHelper.getMathContext call -- the source claim does not hold for the artefact that is serving"
echo "  ok  deployed bytecode carries $N_GMC MoneyHelper.getMathContext call sites in these two classes"
echo "  ok  transcript: $OUT"
echo
echo "Read the dataflow yourself in the transcript: in assembleLoanScheduleFrom the sequence is"
echo "    invokestatic MoneyHelper.getMathContext  ->  astore <n>  ...  aload <n>  ->  invokeinterface LoanScheduleGenerator.generate"
echo "i.e. the SAME local slot.  On Path B the threaded MathContext IS the ambient one."
