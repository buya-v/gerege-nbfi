#!/bin/bash
# T155 probe (xii, corrected) — D-2 driven with perl TRULY ABSENT.
#
# The first version of this probe put a `perl` that exits 127 on PATH. That is
# NOT absence: `command -v perl` finds it, so the proposed precondition patch
# did not fire and the arm proved nothing. Recorded rather than deleted, because
# the corrected arm below is only meaningful next to the mistake it fixes.
#
# Here PATH is a minimal directory holding symlinks to exactly the tools the two
# lifted guard functions need — find, sort, grep — and NOT perl.
set -u
T=/tmp/t155
B=$T/minbin
rm -rf "$B"; mkdir -p "$B"
for t in bash sh find sort grep wc sed awk cat rm mkdir; do
  src="$(command -v "$t" 2>/dev/null)" || continue
  ln -sf "$src" "$B/$t"
done
echo "minimal PATH holds: $(ls "$B" | tr '\n' ' ')"
echo "perl present in it? $(PATH="$B" command -v perl >/dev/null 2>&1 && echo YES || echo NO)"
echo

[ -f "$T/guards-post.sh" ] || { echo "REFUSE: run prove-iv-zero-input.sh first (it lifts the guards)"; exit 9; }

echo "=== the POST guards over a store holding a PLAIN, PLAINLY VISIBLE float ==="
echo "--- with perl available (control) ---"
bash "$T/guards-post.sh" "$T/zero/badstore" "$T/zero/badgo" 2>&1 | sed 's/^/    /'
echo "    ^ wanted: RC vectors=1 harness=1 (the float is found)"
echo
echo "--- with perl TRULY ABSENT ---"
PATH="$B" bash "$T/guards-post.sh" "$T/zero/badstore" "$T/zero/badgo" 2>&1 | sed 's/^/    /'
echo "    ^ 'RC vectors=0 harness=0' here is a VACUOUS PASS ON A FLOAT:"
echo "      the guard reports 'inspected N files' and returns success having"
echo "      inspected none of them. The P-35 counter counts files ENUMERATED by"
echo "      find, not files SCANNED."
