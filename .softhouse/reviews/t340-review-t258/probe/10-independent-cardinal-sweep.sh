#!/usr/bin/env bash
# T340 INDEPENDENT restatement sweep.
#
# The four cardinal shapes below were re-derived by T340 from the HARNESS OUTPUT LINES
# (`.softhouse/conformance.sh` guard_failopen_frontier: "frontier $n, pinned at $p" and
# "frontier == pinned (all $n rows, by path).") BEFORE reading T258's RULES_WIDE/RULES.
# Arms B, C and D deliberately probe shapes T258 DECLARED it cannot see, so that the
# declared blind spots are MEASURED rather than accepted.
#
# Usage: 10-independent-cardinal-sweep.sh <tree-root>
set -u
R="${1:?tree root}"
cd "$R" || exit 2
echo "T340 INDEPENDENT SWEEP over $R at $(git rev-parse HEAD)"
echo
echo "== CORPUS =="
git ls-files '.softhouse/*.sh' '.softhouse/*.py' > /tmp/t340-corpus.txt || exit 2
echo "tracked .softhouse .sh/.py files: $(wc -l < /tmp/t340-corpus.txt)"
git ls-files '.softhouse/*.md' '.softhouse/*.json' > /tmp/t340-corpus2.txt || exit 2
echo "tracked .softhouse .md/.json files: $(wc -l < /tmp/t340-corpus2.txt)"
echo
echo "== CALIBRATION (P-72), FATAL — a known positive must be found before any zero is reported =="
# This arm exists because T340's FIRST draft of this sweep used GNU `xargs -a`, which BSD/macOS
# xargs does not support, and every arm printed EMPTY. With 2>/dev/null on the pipeline that
# empty read exactly like "no restatements exist". It is the fail-open class this review is
# about, committed by the review instrument itself. MEASURED: `xargs: invalid option -- a`.
# SECOND self-catch: `xargs ... LC_ALL=C grep` makes xargs exec `LC_ALL=C` as the COMMAND
# (`xargs: LC_ALL=C: No such file or directory`) -- every arm empty again. `env` fixes it.
# The calibration below caught BOTH. That is what a fatal calibration is for (P-72).
CALHIT="$(xargs < /tmp/t340-corpus.txt env LC_ALL=C grep -laE 'pinned[[:space:]]+at[[:space:]]+[0-9]+' | LC_ALL=C grep -c '')"
echo "  CAL+ files containing a literal \`pinned at <N>\`: $CALHIT (want >= 1)"
if [ "${CALHIT:-0}" -lt 1 ]; then
  echo "  *** CALIBRATION FAILED: the corpus pipeline found NO known positive."
  echo "  *** Every zero below would be a statement about this sweep, not about the tree. REFUSED."
  exit 2
fi
echo
echo "== A. cardinal-shaped restatements in live scripts =="
xargs < /tmp/t340-corpus.txt env LC_ALL=C grep -HnaE 'all[[:space:]]+[0-9]+[[:space:]]+rows|pinned[[:space:]]+at[[:space:]]+[0-9]+|frontier[[:space:]]+[0-9]+|frontier[[:space:]]*==[[:space:]]*pinned' 
echo
echo "== B. NUMERIC COMPARISONS to a bar cardinal (a shape T258's R1-R4 CANNOT see) =="
xargs < /tmp/t340-corpus.txt env LC_ALL=C grep -HnaE '(-ne|-eq|-gt|-lt|==|!=)[[:space:]]*"?(9|10|11|46|109|1281|7884|39)"?([^0-9.]|$)' 
echo
echo "== C. WORD-FORM cardinals (T258 declared blind spot (a)) =="
xargs < /tmp/t340-corpus.txt env LC_ALL=C grep -HnaiE '(nine|ten|eleven|twelve|seventeen|eighteen)[[:space:]]+(rows?|instruments?|files?)|frontier[^;]{0,40}(NINE|TEN|ELEVEN)' 
echo
echo "== D. non-script file types, driver state excluded from the tally (blind spot (d)) =="
xargs < /tmp/t340-corpus2.txt env LC_ALL=C grep -HnaE 'frontier[[:space:]]+(of[[:space:]]+)?[0-9]+|all[[:space:]]+[0-9]+[[:space:]]+rows|pinned[[:space:]]+at[[:space:]]+[0-9]+' 2>/dev/null | grep -vE '^\.softhouse/(handoff/|reviews/|capture/|gates\.md|patterns\.md)'
echo
echo "T340 SWEEP DONE"
