#!/bin/bash
# A2-11 — re-run every check in this review and record the transcript.
#   bash run-all.sh   -> writes TRANSCRIPT-A2-11.txt
# Checks that need the live reference oracle (Fineract) are marked; the rest are offline.
DIR="$(cd "$(dirname "$0")" && pwd)"
{
  echo "############ A2-11 independent review of A2-7 — full transcript"
  date -u +"generated %Y-%m-%dT%H:%M:%SZ"
  echo
  echo "READ THE EXIT CODES THIS WAY: sections 1 and 2 assert A2-7'S CLAIMS, so a non-zero"
  echo "exit there is a FINDING AGAINST A2-7, not a broken script. Sections 3-8 assert things"
  echo "that should hold. Every failing assertion is printed by name."
  echo
  echo "STALENESS NOTICE ADDED BY T270 -- READ IT BEFORE READING ANY EXIT CODE BELOW."
  echo "The committed TRANSCRIPT-A2-11.txt (generated 2026-08-21T08:11:39Z) records sections"
  echo "3-8 all at exit=0. That is NO LONGER what this script produces, and the earlier"
  echo "sentence claiming 'all of them exit 0' was removed because it had become false."
  echo "MEASURED on 2026-08-28: sections 2, 4, 5, 6 and 7 abort with a traceback, because"
  echo "enumerate-corpus.py:22, verify-manifest-independently.py:21, audit-float.py:18,"
  echo "prove-resolve7-float-red.py:33 and prove-a2-7-guards-are-falsifiable.py:19 each"
  echo "hard-code ROOT/RIG to the RETIRED worktree path .../agent-a3ac3d56d665ff7da, which"
  echo "no longer exists. So the committed transcript is ALREADY not re-derivable from this"
  echo "script -- that is a statement about a measurement, not an assumption."
  echo "Those five failures are LOUD (a traceback, exit 1) and are left alone here: fixing"
  echo "the hard-coded roots means editing scripts that produced committed evidence, which"
  echo "is a separate decision. T270 removed only the SILENT one -- see section 8."
  echo
  echo "############ 1. contract shape, from A2-11's OWN live re-observation  [ORACLE]"
  python3 "$DIR/check-shape.py"; echo "exit=$?"
  echo
  echo "############ 2. corpus enumeration at A2-7's fork point (offline, counts its skips)"
  python3 "$DIR/enumerate-corpus.py"; echo "exit=$?"
  echo
  echo "############ 3. double-entry in INTEGER MINOR UNITS (offline)"
  python3 "$DIR/verify-double-entry-minor-units.py"; echo "exit=$?"
  echo
  echo "############ 4. manifest, hashes RECOMPUTED not trusted (offline)"
  python3 "$DIR/verify-manifest-independently.py"; echo "exit=$?"
  echo
  echo "############ 5. P-25 float audit of A2-7's scripts (offline)"
  python3 "$DIR/audit-float.py"; echo "exit=$?"
  echo
  echo "############ 6. resolve7.py P-25 defect, driven RED (offline)"
  python3 "$DIR/prove-resolve7-float-red.py"; echo "exit=$?"
  echo
  echo "############ 7. are A2-7's 16 assertions falsifiable? (offline, sabotage)"
  python3 "$DIR/prove-a2-7-guards-are-falsifiable.py"; echo "exit=$?"
  echo
  echo "############ 8. the float property A2-7's guard prover claimed — RUN FROM ITS"
  echo "############    REPLACEMENT, because the original could not fail (offline)"
  echo
  echo "T270. Until this change, this section ran prove-mkreq7-guard-red.py unmodified and"
  echo "printed 'ok  it parses JSON numbers as Decimal' / '16 assertions, 0 failed' / exit=0."
  echo "That arm is a WHOLE-FILE SOURCE GREP (\`\"parse_float=decimal.Decimal\" in src\`), and"
  echo "the token occurs twice in its target analyze7.py — at :39 in the code and at :6 in"
  echo "the file's OWN DOCSTRING. Delete the keyword from the CALL SITE and the assertion is"
  echo "still satisfied, by the prose. T164 reproduced that end to end and replaced the arm."
  echo
  echo "T114 requires the BYTES of prove-mkreq7-guard-red.py be preserved, so that"
  echo "RED-GREEN-A2-7-guards.txt stays re-derivable from the script that made it. It does"
  echo "NOT require the file keep being EXECUTED as though it still graded something. Those"
  echo "are two different obligations. A superseded guard that still prints PASS is not"
  echo "preserved evidence, it is a trap — P-45 inverted: not a guard that never runs, but a"
  echo "NON-guard that always runs and always says PASS. Bytes unchanged; execution stopped."
  echo
  echo "The successor is not named here. It is READ from the register, so this site cannot"
  echo "drift out of step with it, and a DELETED register line makes this section REFUSE"
  echo "rather than quietly fall back to the trap."
  echo
  RIG="$DIR/../../capture/tierA-a2"
  if REPL="$(python3 "$DIR/resolve-supersession.py" "$RIG/SUPERSEDED.txt" prove-mkreq7-guard-red.py)"; then
    echo "SUPERSEDED.txt resolves: prove-mkreq7-guard-red.py -> $REPL"
    echo
    python3 "$RIG/$REPL"; echo "exit=$?"
  else
    echo "exit=2  (REFUSED — see the message above; no fallback to the superseded file)"
  fi
  echo
  echo "NOT COVERED BY THE REPLACEMENT, STATED SO THIS IS NOT READ AS EQUIVALENT (P-40):"
  echo "prove-mkreq7-guard-red.py carried 16 assertions. guard-parse-float-ast.py replaces"
  echo "only the 3 in its analyze7.py float arm. The other 13 — mkreq7.py's D-1 refusal"
  echo "behaviour and resolve7.py's four refusals — are re-run by NOTHING today. They are"
  echo "recorded as an open follow-up in the T270 handoff, not silently absorbed."
} 2>&1 | tee "$DIR/TRANSCRIPT-A2-11.txt"
