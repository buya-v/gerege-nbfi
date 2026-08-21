#!/bin/bash
# T155 probe (xiv) — P-40: state what this review's sweep COVERED and what it
# SKIPPED, with counts, so silence is distinguishable from not looking.
set -u
P=/tmp/t155/post2
cd "$P" || exit 9

echo "=== the ground T155 swept, sized ==="
printf '  %-56s %s\n' ".sh files under .softhouse/"            "$(find .softhouse -name '*.sh' -type f | wc -l | tr -d ' ')"
printf '  %-56s %s\n' ".py files under .softhouse/"            "$(find .softhouse -name '*.py' -type f | wc -l | tr -d ' ')"
printf '  %-56s %s\n' ".pl files under .softhouse/"            "$(find .softhouse -name '*.pl' -type f | wc -l | tr -d ' ')"
printf '  %-56s %s\n' "ALL files under .softhouse/"            "$(find .softhouse -type f | wc -l | tr -d ' ')"
echo
echo "  COVERED by T155 (read and/or driven):"
printf '    %-54s %s\n' ".softhouse/conformance.sh — every grep site"  "1 file / $(LC_ALL=C grep -acE '(^|[;|&(]|[[:space:]])(LC_ALL=C[[:space:]]+)?grep[[:space:]]' .softhouse/conformance.sh) grep lines"
printf '    %-54s %s\n' ".softhouse/bin/*.sh — every grep site"        "$(find .softhouse/bin -name '*.sh' | wc -l | tr -d ' ') files"
printf '    %-54s %s\n' "T154's own drivers, re-run post-merge"        "$(find .softhouse/capture/t154-nofloat -name '*.sh' | wc -l | tr -d ' ') files"
printf '    %-54s %s\n' "Go: the whole censused tree"                  "$(find nexus/internal/apps/loanschedule -name '*.go' | wc -l | tr -d ' ') files"
printf '    %-54s %s\n' "Go: files in the module OUTSIDE that tree"    "$(find nexus -name '*.go' -not -path '*/loanschedule/*' | wc -l | tr -d ' ') files"
echo
echo "  SKIPPED by T155, deliberately, and why:"
echo "    - historical evidence scripts under .softhouse/reviews/*-evidence/ and"
echo "      .softhouse/handoff/*-evidence/: $(find .softhouse/reviews .softhouse/handoff -name '*.sh' -o -name '*.py' 2>/dev/null | wc -l | tr -d ' ') files."
echo "      They are committed transcripts of past measurements; editing them falsifies"
echo "      the evidence they record. Same reasoning T154 gave. NOT audited for blind greps."
echo "    - Python: $(find .softhouse -name '*.py' -type f | wc -l | tr -d ' ') files. Different encoding behaviour from BSD grep;"
echo "      T156 swept .sh/.py, T155 did not re-do that ground."
echo "    - any grep on an unmerged sibling branch, and any grep built at runtime"
echo "      from a variable: a lexical sweep cannot see either."
echo
echo "=== the Go ground, which T156's .sh/.py sweep states is INVISIBLE to it ==="
echo "  Go files in the module:              $(find nexus -name '*.go' | wc -l | tr -d ' ')"
echo "  of which inside the censused tree:   $(find nexus/internal/apps/loanschedule -name '*.go' | wc -l | tr -d ' ')"
echo "  of which OUTSIDE it (uncensused):    $(find nexus -name '*.go' -not -path '*/loanschedule/*' | wc -l | tr -d ' ')"
echo "  -> the census root is the fixed path LoanScheduleTreeRel; today it happens to"
echo "     be the whole module, so the coverage gap is 0 files TODAY and grows silently"
echo "     the moment a second Go package is added. Reported as a residual, not a defect."
echo
echo "  float/complex identifiers anywhere in the module (should be 0 outside the"
echo "  guard's own split-string denylist and its comments):"
( cd nexus && LC_ALL=C grep -arnE '\b(float32|float64|complex64|complex128)\b' --include='*.go' . | LC_ALL=C grep -av 'nofloat.go' | sed 's/^/    /' )
echo "    (end)"
