#!/bin/bash
# A2-31 PROBE — resolve every harness file:line citation DEC-2 rev 4 carries, on THIS
# worktree's HEAD, and print the bytes so each is bound BY CONTENT (P-63: line numbers in
# this repo have drifted twice). READ-ONLY: sed -n only.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3fcb4c7f1ea451ee
C="$R/nexus/internal/apps/loanschedule/conformance"
echo "worktree HEAD: $(cd "$R" && git rev-parse --short HEAD)"
echo
show() { echo "===== $1:$2-$3"; sed -n "$2,$3p" "$1" | sed 's/^/    /'; echo; }
cd "$R" || exit 1
show .softhouse/conformance.sh 1152 1153
show .softhouse/conformance.sh 1186 1190
show .softhouse/conformance.sh 1209 1213
show .softhouse/conformance.sh 1254 1254
show .softhouse/conformance.sh 401 401
show .softhouse/conformance.sh 411 411
show .softhouse/conformance.sh 718 721
show .softhouse/conformance.sh 1180 1186
show .softhouse/guards/ledgerguard/main.go 852 853
show nexus/internal/apps/ledger/slots_test.go 187 187
show nexus/internal/apps/ledger/glaccount.go 324 324
show "$C/vector.go" 16 18
show "$C/vector.go" 77 81
show "$C/vector.go" 83 91
show "$C/vector.go" 542 546
show "$C/vector.go" 647 649
show "$C/vector.go" 1006 1009
show "$C/vector.go" 1016 1018
show "$C/admit.go" 109 110
show "$C/admit.go" 115 117
show "$C/admit.go" 139 147
show "$C/admit.go" 149 149
show "$C/admit.go" 159 162
show "$C/admit.go" 160 170
show "$C/admit.go" 384 388
show "$C/admit.go" 417 421
show "$C/admit.go" 545 545
show "$C/capability.go" 245 247
show "$C/capability.go" 262 278
show "$C/capability.go" 351 356
show "$C/grade.go" 373 379
show "$C/grade.go" 473 474
show "$C/grade.go" 478 480
show "$C/grade.go" 561 561
show "$C/registry.go" 11 11
show "$C/registry.go" 26 28
show "$C/registry.go" 34 34
show "$C/registry.go" 173 173
show "$C/enums.go" 92 104
show "$C/coverage_refusal_test.go" 50 50
