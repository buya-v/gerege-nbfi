#!/bin/sh
# T36 — re-run T22's ten property invariants (I1-I6, S1-S4) on the T36 re-captures.
# Reusing the audited checker rather than writing a fourth one: T27 already proved it
# failable by one-minor-unit mutation, and reuse keeps the corpus comparable.
set -u
D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)
R=$D/out/recapture-gerege
python3 "$W/t22-audit/t22_invariants.py" \
  "$R/B-01-baseline-raw.json::T36 B-01 baseline (gerege, 19/HALF_UP)" \
  "$R/B-02-multiplesof100-raw.json::T36 B-02 multiplesOf100 (gerege, 19/HALF_UP)" \
  "$R/B-03-diycs-fullleapyear-raw.json::T36 B-03 FULL_LEAP_YEAR (gerege, 19/HALF_UP)" \
  "$R/B-04-diycs-feb29only-raw.json::T36 B-04 FEB_29_PERIOD_ONLY (gerege, 19/HALF_UP)"
