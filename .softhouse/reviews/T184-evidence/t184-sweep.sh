#!/bin/bash
# T184 (P-37): my OWN sweep of T173's added content for fail-open / EPIPE shapes.
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
echo "=== A. grep -q inside a pipeline (the P-57 EPIPE shape) in the T173 block (conformance.sh 670-815)"
sed -n '670,815p' .softhouse/conformance.sh | grep -n 'grep -[a-z]*q' || echo "   none"
echo
echo "=== B. fail-open shapes in the T173 block"
sed -n '670,815p' .softhouse/conformance.sh | grep -n '|| return 0\||| true\|2>/dev/null\|:-0' || echo "   none but the two counted greps below"
echo
echo "=== C. every '|| true' in the T173 block, with what it masks"
sed -n '670,815p' .softhouse/conformance.sh | grep -n '|| true'
echo
echo "=== D. swallowed exceptions in the two guard scripts"
grep -n 'except' .softhouse/capture/lib/check_wire_float_roundtrip.py .softhouse/capture/lib/check_no_narrow_catch.py
echo
echo "=== E. 'pass' / 'continue' as an exception body"
grep -n -A2 'except' .softhouse/capture/lib/check_wire_float_roundtrip.py | grep -n 'pass$\|continue' || echo "   (the one 'continue' is after append to unparsed[], checked by hand)"
echo
echo "=== F. does anything in the T173 block redirect stderr away?"
sed -n '670,815p' .softhouse/conformance.sh | grep -n '2>&1\|>/dev/null'
echo
echo "=== G. bare 'grep -q' ANYWHERE that pipes from printf of a large var (whole file)"
grep -n 'printf .*"\$out.*| *LC_ALL=C grep -[a-z]*q' .softhouse/conformance.sh | head -20
echo "   (count: $(grep -c 'printf .*"\$out.*| *LC_ALL=C grep -[a-z]*q' .softhouse/conformance.sh))"
