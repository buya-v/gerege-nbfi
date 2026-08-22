#!/usr/bin/env bash
# T234 — the one LIVE script instrument that carries a \b under git grep -E:
#   .softhouse/reviews/T138-evidence/r11-hygiene.sh:35
#     git grep -n -a -E 'merge-base|main:|origin/main|rev-parse main|\bmain\b' ...
# The first four alternatives are literal and work. The fifth, \bmain\b, compiles under
# git's ERE to the literal string "bmainb" and can never match.  MEASURE the loss.
set -u
P=".softhouse/capture/t91/ .softhouse/capture/charges/bin/preconditions.sh .softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh"
echo "engine: git grep, Apple Git 2.50.1. paths as r11-hygiene.sh passes them."
for f in -E -P; do
  full=$(git grep $f -c -a -- 'merge-base|main:|origin/main|rev-parse main|\bmain\b' -- $P 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  four=$(git grep $f -c -a -- 'merge-base|main:|origin/main|rev-parse main' -- $P 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  echo "  git grep $f  five-alternative=$full   four-alternative=$four   \\bmain\\b contributes=$((full-four))"
done
echo
echo "  what \\bmain\\b WOULD have contributed if the engine honoured it (git grep -P, five vs four):"
p5=$(git grep -P -c -a -- 'merge-base|main:|origin/main|rev-parse main|\bmain\b' -- $P 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
p4=$(git grep -P -c -a -- 'merge-base|main:|origin/main|rev-parse main' -- $P 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
echo "    -P five=$p5  four=$p4  genuine contribution of the word-boundary term = $((p5-p4)) lines"
echo
echo "  literal proof the term degrades to 'bmainb':"
echo -n "    git grep -E -c 'bmainb' repo-wide  : "; git grep -E -c -- 'bmainb' 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo -n "    git grep -E -c '\\bmain\\b' repo-wide : "; git grep -E -c -- '\bmain\b' 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo -n "    git grep -P -c '\\bmain\\b' repo-wide : "; git grep -P -c -- '\bmain\b' 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
