#!/bin/sh
# T99 F-3 — forbidden-sentence.sh PASSED VACUOUSLY ON ZERO FILES.
#
# Both `for` patterns in that script are globs.  When a glob matches nothing the shell hands the
# pattern through literally, `[ -f "$f" ] || continue` skips it, the loop body never runs, and the
# script printed "violations: 0" and "RESULT: the HALF_UP claim is never made except on tenant
# gerege with the pinned canary" — having inspected NOTHING — and exited 0.
#
# This is P-22 exactly: a guard that cannot fail is worse than no guard, because it is believed.
#
# The fix must not weaken what T85 already proved about this script: it reproduces 27 files with 0
# violations on the committed evidence, and it FIRES on planted violations.  Every leg below is run
# against BOTH the pre-fix and the fixed bytes, so a no-op would be visible.
#
# Entirely hermetic: no oracle, no network, no docker.  Everything happens inside the /tmp export.
. "$(dirname "$0")/lib.sh"

echo "=== T99 F-3 — a check that reports success on an empty file set is not a check"
t99_export
t99_stubs
t99_pin "$P/t80/forbidden-sentence.sh" "$PIN_PREFIX_FORBIDDEN" forbidden-sentence.sh
echo

prefix_admitted=0
fixed_refused=0

run() {   # <tree> <label> ; echoes EXIT and the last three lines
  sh "$1/t80/forbidden-sentence.sh" > "$EXPORT/f3.txt" 2>&1
  st=$?
  echo "  EXIT=$st"
  tail -4 "$EXPORT/f3.txt" | sed 's/^/    /'
  return $st
}

# ------------------------------------------------------- 3a. ZERO FILES: the finding itself
echo "--- 3a — ZERO FILES.  The script is copied to a directory whose out/ is empty, which is what"
echo "         a moved script, a pruned worktree or an edited glob all look like."
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  d=$EXPORT/empty-$side/t80
  mkdir -p "$d/out"
  cp "$TREE/t80/forbidden-sentence.sh" "$d/"
  echo "  $side: files visible to the globs: $(ls -A "$d/out" | wc -l | tr -d ' ')"
  sh "$d/forbidden-sentence.sh" > "$EXPORT/f3-$side.txt" 2>&1
  st=$?
  echo "  EXIT=$st"
  sed 's/^/    /' "$EXPORT/f3-$side.txt"
  if [ "$side" = prefix ]; then
    if [ "$st" = 0 ] && LC_ALL=C grep -qa 'RESULT: the HALF_UP claim is never made' "$EXPORT/f3-$side.txt"; then
      prefix_admitted=1
      echo "  VERDICT: exit 0 and the strongest sentence in the file, on an empty input set."
    else
      echo "  VERDICT: the vacuous pass did not reproduce."
    fi
  else
    if [ "$st" = 2 ] && LC_ALL=C grep -qa 'INSPECTED NOTHING' "$EXPORT/f3-$side.txt"; then
      fixed_refused=1
      echo "  VERDICT: exit 2, named as an ERROR, and the RESULT sentence is not printed."
    else
      echo "  VERDICT: the fixed bytes did not refuse the empty input set."
    fi
  fi
  echo
done

# ------------------------- 3b. the OTHER vacuity: files present, none carrying the sentence
echo "--- 3b — the second way to be vacuous: files ARE read, but not one contains the guarded"
echo "         sentence, so the co-occurrence rule adjudicates nothing."
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  d=$EXPORT/quiet-$side/t80
  mkdir -p "$d/out"
  cp "$TREE/t80/forbidden-sentence.sh" "$d/"
  echo "nothing interesting here" > "$d/out/attack-9z-decoy.txt"
  echo "nor here" > "$d/out/attack-9y-decoy.txt"
  sh "$d/forbidden-sentence.sh" > "$EXPORT/f3b-$side.txt" 2>&1
  echo "  $side: EXIT=$?"
  tail -3 "$EXPORT/f3b-$side.txt" | sed 's/^/    /'
done
echo

# --------------------------------- 3c. T85's two properties must survive: 27/0, and it fires
echo "--- 3c — what T85 proved must still hold: the committed evidence reproduces, and a planted"
echo "         violation still fires.  (A fix that made the check quieter would show up here.)"
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  echo "  $side, committed evidence untouched:"
  run "$TREE" >/dev/null 2>&1 || true
  sh "$TREE/t80/forbidden-sentence.sh" > "$EXPORT/f3c-$side.txt" 2>&1
  echo "    EXIT=$?  OK=$(LC_ALL=C grep -ac '^OK' "$EXPORT/f3c-$side.txt")  absent=$(LC_ALL=C grep -ac '^absent' "$EXPORT/f3c-$side.txt")  violations=$(LC_ALL=C grep -a '^violations:' "$EXPORT/f3c-$side.txt" | tr -d ' ' | cut -d: -f2)"
done
echo "  planting two violations (the guarded sentence with no digest pin, one on tenant default):"
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  printf "== planted, tenant 'gerege' ==\n  PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)\n" \
    > "$TREE/t80/out/attack-9x-planted-nopin.txt"
  printf "== planted, tenant 'default' ==\n  PASS  canary request pinned by DIGEST COMPARISON: x\n  PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)\n" \
    > "$TREE/t80/out/attack-9w-planted-default.txt"
  sh "$TREE/t80/forbidden-sentence.sh" > "$EXPORT/f3d-$side.txt" 2>&1
  echo "  $side: EXIT=$?  violations=$(LC_ALL=C grep -a '^violations:' "$EXPORT/f3d-$side.txt" | tr -d ' ' | cut -d: -f2)"
  LC_ALL=C grep -a '^VIOLATION' "$EXPORT/f3d-$side.txt" | sed "s|$TREE/||" | sed 's/^/    /'
  rm -f "$TREE/t80/out/attack-9x-planted-nopin.txt" "$TREE/t80/out/attack-9w-planted-default.txt"
done
echo
echo "  (a planted violation is written into the /tmp export only; the committed transcripts in"
echo "   the repository are never touched by this proof)"


# ------------------- 3e. the SWEEP hit: two more gates that could not fail, found by shape
echo "--- 3e — the same 'guard that cannot fail' shape, found by sweeping, in two OTHER scripts."
echo "         t36/recreate-products.sh and t36/emiloop-probe.sh carried the EXACT defect T77 found"
echo "         and T80 fixed in recapture.sh: preconditions.sh's bad() writes FAIL to STDERR"
echo "         (preconditions.sh:58) and both scripts redirected STDOUT ONLY, so the '^  FAIL' grep"
echo "         they abort on could never match, and neither looked at the exit status."
echo
echo "  the mechanical fact, measured on the pre-fix bytes — where do FAIL lines go?"
( PATH=$EXPORT/stub:$PATH; export PATH
  CANARY_REQ=$P/t22-audit/req/calc-pmode2-gerege.json sh "$P/t36/preconditions.sh" gerege ) \
    > "$EXPORT/f3e-stdout.txt" 2>"$EXPORT/f3e-stderr.txt"
echo "    preconditions.sh exit status: (breached environment, docker/curl stubbed)"
echo "    '^  FAIL' lines on STDOUT: $(LC_ALL=C grep -ac '^  FAIL' "$EXPORT/f3e-stdout.txt" || true)"
echo "    '^  FAIL' lines on STDERR: $(LC_ALL=C grep -ac '^  FAIL' "$EXPORT/f3e-stderr.txt" || true)"
echo "    => a gate that greps a stdout-only transcript for '^  FAIL' matches nothing, ever."
echo
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  for s in recreate-products emiloop-probe; do
    echo "  $side/$s.sh, run in a breached environment (docker and curl stubbed):"
    ( PATH=$EXPORT/stub:$PATH; export PATH
      sh "$TREE/t36/$s.sh" ) > "$EXPORT/f3e-$side-$s.txt" 2>&1
    st=$?
    echo "    EXIT=$st   aborted before capturing: $(LC_ALL=C grep -qa 'ABORT: preconditions breached' "$EXPORT/f3e-$side-$s.txt" && echo YES || echo 'NO — it went on to capture')"
    LC_ALL=C grep -a 'ALL PASS\|preconditions: ALL PASS\|ABORT: preconditions breached' "$EXPORT/f3e-$side-$s.txt" \
      | head -1 | cut -c1-160 | sed 's/^/      /'
  done
done
echo
echo "  (both are additionally reported in the handoff: they were NOT in T85's four findings.)"

# ------- 3f. T99b: the SAME vacuous-pass shape inside preconditions.sh, on the money-adjacent
#             assertions that carry a CLAUDE.md non-negotiable.
echo
echo "--- 3f — T99b.  The F-3 shape again, in preconditions.sh, on the PostgreSQL-only prohibition."
echo "         P5's \$banned and P6's \$jarhits are \`grep -icE\` counts and P11's \$scp is a psql"
echo "         result; all three were adjudicated by \`= 0\` / \`-z\`, and an empty stream counts 0"
echo "         and reads empty.  So a \`docker\` that answers NOTHING produced:"
echo "             PASS  0 prohibited-engine hits in container env"
echo "             PASS  0 prohibited driver jars in fineract-provider.jar"
echo "             PASS  schema_connection_parameters is empty"
echo "         — the Oracle Database / MySQL / MariaDB prohibition, PASSED WITHOUT LOOKING."
echo "         Below: the same stubbed run against both sides.  A liveness operand now makes an"
echo "         empty scan a FAIL that says the scan did not happen."
for side in prefix fixed; do
  if [ "$side" = prefix ]; then TREE=$P; else TREE=$F; fi
  ( PATH=$EXPORT/stub:$PATH; export PATH
    CANARY_REQ=$TREE/t22-audit/req/calc-pmode2-gerege.json sh "$TREE/t36/preconditions.sh" gerege ) \
      > "$EXPORT/f3f-$side.txt" 2>&1
  echo "  $side: EXIT=$?  FAIL lines=$(LC_ALL=C grep -ac '^  FAIL' "$EXPORT/f3f-$side.txt")"
  echo "    prohibition verdicts printed while docker answered nothing:"
  LC_ALL=C grep -a 'prohibited-engine\|prohibited driver jars\|schema_connection_parameters' \
    "$EXPORT/f3f-$side.txt" | cut -c1-190 | sed 's/^/      /'
done
echo "  (a PASS on any of those three lines on the 'fixed' side would mean the correction failed)"

t99_verdict "$prefix_admitted" "$fixed_refused" "F-3 (vacuous pass on zero files)"
