#!/bin/bash
# A2-32 whole-repo sweep for THE CLAIM, not the sentence.
#
# Population: ALL TRACKED CONTENT (git grep over the worktree), widened past A2-31's
# six classes. A2-31's classes R1..R6 are re-run VERBATIM as a control that my
# substitution reaches at least what its 123 hits reached; classes W1..W8 are mine.
set -u
cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-a356a016636abdd7e || exit 9

echo "worktree HEAD: $(git rev-parse --short HEAD)"
echo "tracked files searched: $(git ls-files | wc -l | tr -d ' ')"
echo

section() { echo; echo "############################################################"; echo "## $*"; echo "############################################################"; }
pat() { echo "--- pattern: $1"; git grep -n -i -E "$1" -- . || echo "    (no hits)"; }

section "F-1 CLAIM CLASS — 'the head DROPS / SWALLOWS CANNOT-CATCH on the pass path' (T209 closed FU-T208-1)"
pat 'DROPS on the pass path'
pat 'head (swallows|drops) CANNOT-CATCH'
pat '(drops|dropped|swallow(s|ed)?|filters out|suppress(es|ed)?|omits|strips) .{0,60}CANNOT-CATCH'
pat 'CANNOT-CATCH.{0,80}(drop|swallow|not present|absent|never (arrives|reaches))'
pat 'FU-T208-1'
pat 'T208-1'
pat 'block is not present anywhere'
pat 'not present anywhere in the output'
pat 'never reaches (the )?(green|transcript)'
pat 'absent from every green run'
pat 'its head DROPS'
pat 'on the pass path'

section "F-2 CLAIM CLASS — the empty-population NUMERATOR/DENOMINATOR for the ledger guard's detection classes"
pat 'three of (its |the |the guard.s )?(seven|7|four|4)'
pat 'THREE OF (ITS |THE )?(SEVEN|FOUR)'
pat '(3|three) of (4|7|four|seven) detection'
pat '(seven|four|7|4) (declared )?detection class'
pat 'detection class(es)?'
pat 'THREE OF THEM INSPECTED'
pat '(three|3|four|4).{0,40}inspected an empty population'
pat 'inspected an empty population'
pat 'empty population'
pat 'denominator'
pat 'numerator'
pat 'I4-BUILDER'
pat 'NIL-COVERAGE'
pat 'harness-enforced'
