#!/bin/bash
# Print, for each POST census row, the refusal in the harness's OWN WORDS.
# A refusal that does not NAME the planted file is a green for the wrong reason.
set -u
for c in C1 C2 C3 C4 C5 C6 C7 C8 C9; do
  f="/tmp/t155/out/iii-POST-$c.txt"
  echo "===================== POST-$c ====================="
  LC_ALL=C grep -aiE 'STORE FILE CENSUS|CASE_ID INTEGRITY|T155|evilctx|loanschedule/sub|symlink|the store|VERDICT' "$f" | head -12
  echo
done
