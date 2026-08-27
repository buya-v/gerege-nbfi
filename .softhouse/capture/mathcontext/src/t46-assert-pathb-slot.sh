#!/usr/bin/env bash
#
# T46 -- close audit finding M-6 by MACHINE-ASSERTING the Path B same-local-slot dataflow,
# and by exercising that assertion NEGATIVELY.
#
# M-6: `src/read-pathb-wiring.sh`'s only machine assertion is
#     N_GMC="$(grep -c 'MoneyHelper.getMathContext' "$OUT")" ; [ "$N_GMC" != "0" ]
# i.e. "the string appears at least once".  The claim that carries T42 attestation rule 4 --
# that the MathContext handed to the schedule generator is THE SAME local slot
# MoneyHelper.getMathContext stored into -- was left to the reader.
#
# This script:
#   1. RE-READS the deployed bytecode off the RUNNING oracle with `javap` (read-only: it unzips
#      two .class files into a fresh /tmp dir inside the container and runs javap there; it does
#      not restart, re-tenant, reconfigure, write schema, or open a database connection), into
#      out/t46-pathb-wiring-reread.txt;
#   2. runs analysis/t46_assert_pathb_slot.py against BOTH the committed T42 transcript and the
#      fresh re-read -- POSITIVE leg, must exit 0;
#   3. runs the SAME assertion against a slot-DRIFTED copy of the transcript (the `astore` that
#      receives getMathContext's result is rewritten to a different slot, simulating a build in
#      which the generator is handed some other MathContext) -- NEGATIVE leg, must exit 1.
#
# An assertion that has never failed has not been tested (`.softhouse/patterns.md`).
#
# No money value is read, computed or published by this script.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SET="$(cd "$HERE/.." && pwd)"
CONTAINER="${T42_ORACLE_CONTAINER:-fineract-fineract-1}"
ASSERT="$SET/analysis/t46_assert_pathb_slot.py"
COMMITTED="$SET/out/t42-pathb-wiring.txt"
REREAD="$SET/out/t46-pathb-wiring-reread.txt"
DRIFTED="$SET/out/negative/t46-pathb-wiring-slot-drifted.txt"
TRANSCRIPT="$SET/analysis/t46-pathb-slot-assertion-output.txt"

CLASSES=(
  "org.apache.fineract.portfolio.loanaccount.loanschedule.service.LoanScheduleAssembler"
  "org.apache.fineract.portfolio.loanaccount.service.LoanScheduleGeneratorServiceImpl"
)

mkdir -p "$SET/out/negative"
verdict=0

{
  echo "== T46 -- Path B same-local-slot dataflow, MACHINE-ASSERTED (audit finding M-6)"
  echo "== captured: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo

  # ---- 1. fresh read-only re-read off the running oracle ---------------------------------
  echo "---- 1. re-reading the DEPLOYED bytecode (read-only) ----"
  if docker inspect "$CONTAINER" >/dev/null 2>&1; then
    {
      echo "== T46 -- Path B MathContext wiring, re-read from the DEPLOYED bytecode"
      echo "== container: $CONTAINER (running; not restarted, not reconfigured, not written to)"
      echo "== captured:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo
      docker inspect "$CONTAINER" --format '{{.Config.Image}} {{.Image}} {{.State.Status}} startedAt={{.State.StartedAt}}'
      echo
      docker exec "$CONTAINER" sh -c 'sha256sum /app/fineract-provider.jar'
      echo
      docker exec "$CONTAINER" sh -c '
        cd /tmp && rm -rf t46j && mkdir t46j && cd t46j
        unzip -o -q /app/fineract-provider.jar "BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/loanschedule/service/LoanScheduleAssembler.class" "BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorServiceImpl.class" 2>/dev/null
        sha256sum BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/loanschedule/service/LoanScheduleAssembler.class
        sha256sum BOOT-INF/classes/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorServiceImpl.class
      '
      for CLS in "${CLASSES[@]}"; do
        echo
        echo "================================================================================"
        echo "javap -p -c   $CLS"
        echo "================================================================================"
        docker exec -e JAVA_TOOL_OPTIONS= "$CONTAINER" sh -c "cd /tmp/t46j && javap -p -c -cp BOOT-INF/classes '$CLS'"
      done
    } > "$REREAD" 2>&1
    echo "re-read written to $REREAD ($(wc -l < "$REREAD" | tr -d ' ') lines)"
    echo "deployed class digests, from THIS re-read:"
    grep -E 'sha256|[0-9a-f]{64}' "$REREAD" | head -5 | sed 's/^/    /'
  else
    echo "SKIPPED: container $CONTAINER is not present.  Only the committed transcript is checked."
    REREAD=""
  fi
  echo

  # ---- 2. POSITIVE leg -------------------------------------------------------------------
  echo "---- 2. POSITIVE leg: the assertion against real transcripts (must exit 0) ----"
  # shellcheck disable=SC2086
  python3 "$ASSERT" "$COMMITTED" ${REREAD:+"$REREAD"}
  rc_pos=$?
  echo "-- positive leg exit: $rc_pos --"
  [ "$rc_pos" -eq 0 ] || { echo "FAIL: the assertion does not hold on the real bytecode."; verdict=1; }
  echo

  # ---- 3. NEGATIVE leg -------------------------------------------------------------------
  echo "---- 3. NEGATIVE leg: slot drift injected (must exit 1) ----"
  python3 - "$COMMITTED" "$DRIFTED" <<'PYDRIFT'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
lines = open(src, errors="replace").readlines()
out, armed, n = [], False, 0
for line in lines:
    if "MoneyHelper.getMathContext" in line and "invokestatic" in line:
        armed = True
        out.append(line)
        continue
    if armed:
        m = re.match(r"^(\s+\d+:\s+astore\s+)(\d+)(\s*)$", line)
        if m:
            # rewrite the slot to one that is never loaded back
            out.append("%s%d%s\n" % (m.group(1), int(m.group(2)) + 90, m.group(3)))
            n += 1
            armed = False
            continue
        m = re.match(r"^(\s+\d+:\s+astore)_(\d+)(\s*)$", line)
        if m:
            out.append("%s        %d%s\n" % (m.group(1), int(m.group(2)) + 90, m.group(3)))
            n += 1
            armed = False
            continue
        armed = False
    out.append(line)
open(dst, "w").writelines(out)
print("  slot-drift injected at %d of the getMathContext store sites" % n)
if n == 0:
    raise SystemExit("could not inject drift -- the negative leg would be vacuous")
PYDRIFT
  python3 "$ASSERT" "$DRIFTED"
  rc_neg=$?
  echo "-- negative leg exit: $rc_neg --"
  if [ "$rc_neg" -eq 0 ]; then
    echo "FAIL: the assertion PASSED a slot-drifted transcript -- it asserts nothing."
    verdict=1
  else
    echo "OK: the assertion FAILED the slot-drifted transcript.  It is failable."
  fi
  echo

  echo "verdict: $([ "$verdict" -eq 0 ] && echo PASS || echo FAIL)"
} 2>&1 | tee "$TRANSCRIPT"

exit "$verdict"
