#!/usr/bin/env bash
set -uo pipefail
R=/tmp/t440/k8-rows.txt
O="$1"
{
  echo "T440 -- the 29 wide-K8 rows on the AFTER ref, partitioned mechanically."
  echo "source: out/T440-census-after.txt (the '--- K8' block, verbatim)"
  echo
  printf 'TOTAL K8 rows            : %s\n' "$(grep -c . "$R")"
  printf '  sel calls              : %s\n' "$(grep -cE '\| *sel ' "$R")"
  printf '  SWEEP_*=$((...)) rows  : %s\n' "$(grep -cE 'SWEEP_[A-Z_]*=[$][(][(]' "$R")"
  printf '  neither (parent-side)  : %s\n' "$(grep -vE '\| *sel |SWEEP_[A-Z_]*=[$][(][(]' "$R" | grep -c .)"
  echo
  echo "AUDIT-CLASS.md and T424's handoff say 16 + 8 + 6 = 30, which is neither the measured"
  echo "partition (13 / 10 / 6) nor its own stated total of 29. [T440 C-T440-2]"
  echo
  echo "There ARE sixteen sel calls in the file; three of them (S1, S3, S7) use -F patterns with"
  echo "no '|' in them, so they never match K8_RIGHT and never reach this list. That is the"
  echo "likely origin of the 16."
  echo
  cat -n "$R"
} > "$O"
echo "wrote $O"
