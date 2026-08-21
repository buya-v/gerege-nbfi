#!/bin/bash
# T155 probe (xi) — the proposed MICRO-FIX for D-1, driven both ways.
#
# D-1: T154 added `no-float census  N Go files / T tokens inspected` to the
# report as its P-35 positive assertion, and NOTHING ASSERTS N. Delete the Run
# call site and conformance prints `0 Go files / 0 tokens` next to
# `VERDICT: PASS` on a tree that contains a float literal.
#
# The fix is five lines in grade.go, placed AFTER the census block so a minimal
# deletion of the call site leaves it behind. Driven here: with the fix in place
# the doctored tree goes RED, and the clean tree still goes GREEN with the same
# counts (no vector, no cell, no money number moves).
set -u
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
POST=/tmp/t155/post
G=nexus/internal/apps/loanschedule/conformance/grade.go

apply_fix() { # $1 tree
  perl -0pi -e 's{(\t\tfor _, v := range census\.Violations\(\) \{\n\t\t\ts\.FatalReasons = append\(s\.FatalReasons, "FLOATING POINT ON A MONEY PATH: "\+v\)\n\t\t\}\n\t\}\n)}{$1
\t// P-35 ASSERTED, NOT MERELY PRINTED \(T155\/D-1\). The report prints
\t// "no-float census N Go files \/ T tokens"; nothing checked N. With the call
\t// site above deleted, NoFloatCensus stays zero-valued, the report prints
\t// "0 Go files \/ 0 tokens" and the run was STILL exit 0 on a tree carrying a
\t// float literal. This statement is separate from the block above so that a
\t// minimal deletion of the call site leaves it behind and turns the run red.
\tif s.NoFloatCensus.FilesScanned == 0 \{
\t\ts.FatalReasons = append\(s.FatalReasons,
\t\t\t"THE NO-FLOAT CENSUS INSPECTED ZERO GO FILES: a guard that inspects nothing passes everything, "+
\t\t\t\t"so this is an ERROR and not a pass"\)
\t\}
}s' "$1/$G"
  LC_ALL=C grep -aq 'INSPECTED ZERO GO FILES' "$1/$G" || { echo "APPARATUS: the fix did not apply"; return 1; }
}

run() { # $1 tree, $2 label
  ( cd "$1" && bash "$1/.softhouse/conformance.sh" ) > "/tmp/t155/out/xi-$2.txt" 2>&1
  echo "  exit=$?"
  LC_ALL=C grep -aE '^VERDICT|no-float census|parity vectors|cells compared|NO-FLOAT CENSUS' "/tmp/t155/out/xi-$2.txt" | sed 's/^ */    /'
}

echo "=== ARM 1: fix applied, tree CLEAN — must stay GREEN with UNCHANGED counts ==="
S1=/tmp/t155/fix-clean; rm -rf $S1; cp -R "$POST" $S1
apply_fix $S1 || exit 9
( cd $S1/nexus && go build ./... ) || { echo "build failed"; exit 9; }
run $S1 fix-clean
echo
echo "=== ARM 2: fix applied, census call site DELETED, float literal planted — must go RED ==="
S2=/tmp/t155/fix-removed; rm -rf $S2; cp -R "$POST" $S2
apply_fix $S2 || exit 9
perl -0pi -e 's{\tif census, cerr := ScanGoTreeForFloatingPoint.*?\n\t\}\n}{}s' "$S2/$G"
LC_ALL=C grep -aq 'ScanGoTreeForFloatingPoint' "$S2/$G" && { echo "APPARATUS: call site still present"; exit 9; }
printf 'package loanschedule\n\nfunc t155Gone(p int64) int64 { r := 0.036; return p + int64(r) }\n\nvar _ = t155Gone\n' \
  > "$S2/nexus/internal/apps/loanschedule/t155_gone.go"
( cd $S2/nexus && go build ./... ) || { echo "build failed"; exit 9; }
run $S2 fix-removed
echo
echo "=== ARM 3: NO fix, census call site DELETED, float literal planted — the defect as it stands ==="
S3=/tmp/t155/nofix-removed; rm -rf $S3; cp -R "$POST" $S3
perl -0pi -e 's{\tif census, cerr := ScanGoTreeForFloatingPoint.*?\n\t\}\n}{}s' "$S3/$G"
printf 'package loanschedule\n\nfunc t155Gone(p int64) int64 { r := 0.036; return p + int64(r) }\n\nvar _ = t155Gone\n' \
  > "$S3/nexus/internal/apps/loanschedule/t155_gone.go"
( cd $S3/nexus && go build ./... ) || { echo "build failed"; exit 9; }
run $S3 nofix-removed
echo
echo "the fix diff, verbatim:"
diff -u "$POST/$G" "$S1/$G" | sed -n '1,40p'
