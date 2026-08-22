#!/usr/bin/env bash
# T203 - REGRESSION, not a defect proof.  Run T82's own prover
# (`prove-promote-guards.py`) over every mode against BOTH the pre-fix bytes
# (extracted with `git show HEAD:` - the literal committed blob, not a
# reconstruction) and the T203-hardened bytes, and diff the transcripts.
# Identical output across every mode means T203 changed nothing T82 measures.
set -uo pipefail
ROOT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a4762772d2f0d5192
EV="$ROOT/.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T203-evidence"
PRE=/tmp/t203-T74-prefix.py
POST="$ROOT/.softhouse/handoff/T74-promote-vectors.py"
MODES="day-count down-payment down-payment-enabled repayment-every-absent \
repayment-every-conflict period-number-zero period-number-bad \
period-number-absent-payable period-number-on-nonpayable"

same=0; diffn=0; n=0
: > "$EV/T82-parity.txt"
for m in $MODES; do
  n=$((n+1))
  python3 "$ROOT/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-promote-guards.py" \
      "$ROOT" "$m" "$PRE"  > "/tmp/t203-pre-$m.txt"  2>&1; rcpre=$?
  python3 "$ROOT/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-promote-guards.py" \
      "$ROOT" "$m" "$POST" > "/tmp/t203-post-$m.txt" 2>&1; rcpost=$?
  # The PROMOTER: line necessarily names a different path; strip only that line.
  /usr/bin/sed -e '/^PROMOTER:/d' -e 's#/tmp/t203-T74-prefix.py##' "/tmp/t203-pre-$m.txt"  > /tmp/t203-a.txt
  /usr/bin/sed -e '/^PROMOTER:/d' -e 's#/tmp/t203-T74-prefix.py##' "/tmp/t203-post-$m.txt" > /tmp/t203-b.txt
  if diff -q /tmp/t203-a.txt /tmp/t203-b.txt > /dev/null && [ "$rcpre" = "$rcpost" ]; then
    same=$((same+1)); verdict="IDENTICAL"
  else
    diffn=$((diffn+1)); verdict="*** DIFFERS ***"
  fi
  printf '%-32s pre_rc=%s post_rc=%s  %s\n' "$m" "$rcpre" "$rcpost" "$verdict" \
      | tee -a "$EV/T82-parity.txt"
  if [ "$verdict" != "IDENTICAL" ]; then diff /tmp/t203-a.txt /tmp/t203-b.txt | tee -a "$EV/T82-parity.txt"; fi
done
printf '\nT82 modes inspected: %s | identical: %s | differing: %s\n' "$n" "$same" "$diffn" \
    | tee -a "$EV/T82-parity.txt"
[ "$n" -eq 0 ] && { echo "P-35: ZERO modes inspected - ERROR"; exit 3; }
[ "$diffn" -eq 0 ] || exit 1
exit 0
