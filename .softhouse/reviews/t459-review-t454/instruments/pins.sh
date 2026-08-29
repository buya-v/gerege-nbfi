#!/bin/bash
# T459 evidence 05 -- the moved pin, and the hand-typed cardinals.
set -u
M=/tmp/t459-main-conf.sh
T=/tmp/t459-tip-conf.sh
echo "=============================================================================="
echo "A. THE LIVE PIN patterns.md:3426 -> conformance.sh:3271"
echo "=============================================================================="
echo "patterns.md:3426 (main) : $(sed -n '3426p' /tmp/t459-main-patterns.md)"
echo "patterns.md:3426 (tip)  : $(sed -n '3426p' /tmp/t459-tip-patterns.md)"
echo "conformance.sh:3271 main: $(sed -n '3271p' "$M")"
echo "conformance.sh:3271 tip : $(sed -n '3271p' "$T")"
a=$(sed -n '3271p' "$M"); b=$(sed -n '3271p' "$T")
if [ "$a" = "$b" ]; then echo "RESULT: 3271 BYTE-IDENTICAL on both trees"; else echo "RESULT: 3271 DIFFERS"; fi
if cmp -s /tmp/t459-main-patterns.md /tmp/t459-tip-patterns.md; then
  echo "RESULT: patterns.md UNTOUCHED by T454 (it is outside T454's grant)"
else
  echo "RESULT: patterns.md CHANGED by T454"
fi
echo
echo "=============================================================================="
echo "B. THE DERIVED GUARD COUNT -- 16 is a COUNT, not a typed number"
echo "=============================================================================="
echo "timed_guard call sites on main : $(LC_ALL=C grep -c '^  timed_guard ' "$M")"
echo "timed_guard call sites on tip  : $(LC_ALL=C grep -c '^  timed_guard ' "$T")"
echo "the say line that prints it    : $(LC_ALL=C grep -m1 'GUARD-COST CENSUS' "$T")"
echo
echo "the hand-typed cardinal T454 says it DELETED, on main:"
LC_ALL=C grep -n 'fifteen guards' "$M"
echo "the same search on the tip (expect: absent from warn text, present only as a comment):"
LC_ALL=C grep -ni 'fifteen' "$T"
echo
echo "=============================================================================="
echo "C. C-T459-4 -- a hand-typed cardinal that SURVIVED, in refusal text"
echo "=============================================================================="
LC_ALL=C grep -n 'yet three of them' "$T"
LC_ALL=C grep -n 'yet three of them' "$M"
echo "(the quantity it narrates is derived and printed on every run as invoked=N)"
echo
echo "=============================================================================="
echo "D. is guard_harness_text_is_committed pinned by anything?"
echo "=============================================================================="
echo -n "occurrences of 'harness_text' inside guard_registration_decisive_lines: "
sed -n '/^guard_registration_decisive_lines()/,/^}/p' "$T" | LC_ALL=C grep -c 'harness_text'
echo "(0 == the guard that closes MAJOR-1 is watched by nothing; this is why LONGNOP is one line)"
