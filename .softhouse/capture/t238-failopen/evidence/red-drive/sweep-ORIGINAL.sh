#!/bin/bash
# A2-33 independent claim sweep.
# TARGET: a file, or "REPO" to sweep all tracked content at HEAD.
# Patterns are deliberately NOT right-anchored on inflected stems (T227's 0/9-recall lesson:
# \bexist\b cannot match EXISTING). Every stem is left-anchored or bare.
set -u
WT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a5244bad2b6814a39
MODE="${1:-REPO}"

run() {  # run <label> <regex>
  local label="$1" re="$2"
  echo "########## PATTERN $label :: $re"
  if [ "$MODE" = "REPO" ]; then
    ( cd "$WT" && git grep -n -I -i -E "$re" -- . ) || echo "   (no hits)"
  else
    grep -n -i -E "$re" "$MODE" || echo "   (no hits)"
  fi
  echo
}

# ---- F-2 CLASS: "the number of detection classes with an empty population is THREE" ----
run F2-01 'three of (its |the |them|these )?(seven|7|four|4)'
run F2-02 '(^|[^0-9])3 of (7|4|seven|four)'
run F2-03 'three of them'
run F2-04 'empty population'
run F2-05 'inspect.{0,40}empty'
run F2-06 'numerator'
run F2-07 'denominator'
run F2-08 'i4.?builder'
run F2-09 'nil.?coverage'
run F2-10 'detection class'
run F2-11 'not established'
run F2-12 'i.?4 arm'
run F2-13 'three .{0,80}(class|detect)'
run F2-14 '(57|43|25) ?%|57 per ?cent|43 per ?cent'
run F2-15 '(three|3|four|4) declared'
run F2-16 'declared detection'
run F2-17 'the (three|four)( that| classes| of them)?'
run F2-18 'i3.?sql.?balance'
run F2-19 'i4.?dml'
run F2-20 'opaque.?sql'
run F2-21 'selftest only|--selftest. only|self-test and .{0,20}nothing'
run F2-22 'guard is (25|43|57)|% live|per ?cent live'

# ---- F-1 CLASS: "the guard head DROPS the CANNOT-CATCH block on the pass path" ----
run F1-01 'fu.?t208.?1|t208.?1'
run F1-02 'cannot.?catch.{0,100}(drop|swallow|filter|omit|strip|suppress|absent|not present|never|does not|doesn.t)'
run F1-03 '(drop|swallow|filter|omit|strip|suppress|absent|never|does not arrive|doesn.t arrive).{0,100}cannot.?catch'
run F1-04 'head drop'
run F1-05 'pass.?path|pass path'
run F1-06 'not present anywhere'
run F1-07 'absent from every'
run F1-08 'never reach'
run F1-09 'does not arrive|do not arrive|doesn.t arrive'
run F1-10 'only .{0,12}\^?census'
run F1-11 'condensed copy|redundant restatement|8.line condensation|eight.line condensation'
run F1-12 'green run'
