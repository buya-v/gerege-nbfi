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
  echo "that should hold, and all of them exit 0. Every failing assertion is printed by name."
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
  echo "############ 8. A2-7's own guard prover, re-run unmodified (offline)"
  python3 "$DIR/../../capture/tierA-a2/prove-mkreq7-guard-red.py"; echo "exit=$?"
} 2>&1 | tee "$DIR/TRANSCRIPT-A2-11.txt"
