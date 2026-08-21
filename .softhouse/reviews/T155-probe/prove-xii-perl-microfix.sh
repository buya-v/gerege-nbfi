#!/bin/bash
# T155 probe (xii) — the proposed MICRO-FIX for D-2, driven both ways.
#
# D-2: both shell no-float guards count files ENUMERATED by `find`, not files
# actually SCANNED. Their pipeline is `perl … | grep …`; if perl cannot run the
# pipeline yields nothing, `set -o pipefail` makes the `if` false, the counter
# still increments, and the guard prints "inspected N files" and returns 0 on a
# store carrying a plainly visible float.
#
# Minimum fix: make perl a stated PRECONDITION of the harness, next to the
# existing `go` precondition in load_toolchain. This closes ABSENCE. It does NOT
# close "perl ran and died on one file" — recorded as a residual, not fixed here.
set -u
POST=/tmp/t155/post
C=.softhouse/conformance.sh
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

S=/tmp/t155/perlfix; rm -rf $S; cp -R "$POST" $S
perl -0pi -e 's{(  if ! command -v go >/dev/null 2>&1; then\n.*?\n    exit "\$EXIT_UNUSABLE"\n  fi\n)}{$1  # perl is a PRECONDITION, not an optional convenience: both no-float guards
  # pipe every file through it, and with perl gone the pipeline yields nothing,
  # the guard reports "inspected N files" and returns 0 ON A FLOAT \(T155\/D-2\).
  if ! command -v perl >/dev/null 2>&1; then
    warn "conformance: no perl. Both no-float guards pipe every file through perl; without it they"
    warn "conformance: enumerate files and inspect none. EXIT 2 — the harness is unusable. NOT a pass."
    exit "\$EXIT_UNUSABLE"
  fi
}s' "$S/$C"
LC_ALL=C grep -aq 'no perl' "$S/$C" || { echo "APPARATUS: fix did not apply"; exit 9; }

echo "=== ARM 1: fix applied, perl present, clean store — must stay GREEN, counts unchanged ==="
( cd $S && bash "$S/$C" ) > /tmp/t155/out/xii-clean.txt 2>&1; echo "  exit=$?"
LC_ALL=C grep -aE '^VERDICT|parity vectors|cells compared|no-float guard' /tmp/t155/out/xii-clean.txt | sed 's/^ */    /'
echo
mkdir -p /tmp/t155/noperl2; printf '#!/bin/sh\nexit 127\n' > /tmp/t155/noperl2/perl; chmod +x /tmp/t155/noperl2/perl
echo "=== ARM 2: perl replaced by exit-127, WITHOUT the fix (the defect) ==="
( cd "$POST" && PATH="/tmp/t155/noperl2:$PATH" bash "$POST/$C" ) > /tmp/t155/out/xii-nofix.txt 2>&1; echo "  exit=$?"
LC_ALL=C grep -aE '^VERDICT|no-float guard|FLOAT-SHAPED' /tmp/t155/out/xii-nofix.txt | sed 's/^ */    /'
echo
echo "=== ARM 3: perl replaced by exit-127, WITH the fix — must refuse ==="
( cd $S && PATH="/tmp/t155/noperl2:$PATH" bash "$S/$C" ) > /tmp/t155/out/xii-fix.txt 2>&1; echo "  exit=$?"
LC_ALL=C grep -aE '^VERDICT|no perl|EXIT 2' /tmp/t155/out/xii-fix.txt | sed 's/^ */    /'
echo
echo "the fix diff, verbatim:"
diff -u "$POST/$C" "$S/$C"
