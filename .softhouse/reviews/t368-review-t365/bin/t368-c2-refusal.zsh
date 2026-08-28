#!/bin/zsh
# T368 — drive T361's condition C2 on the REAL host, both vintages.
#
# T365 declined to reproduce the pre-C2 `rm -rf /` and reconstructed the shape with the trap's
# `rm -rf` replaced by a `print`, relying on T361's container measurement. That is defensible
# but it proves REACHABILITY, not ISSUANCE. This drive proves issuance without risk, because
# BSD `rm` refuses `/` and prints so: the refusal line IS the evidence that the trap ran.
#
# NOTHING HERE CAN DELETE ANYTHING. The only destructive act possible is `rm -rf /`, which
# both BSD and GNU `rm` refuse by their own guard — which is precisely T361's finding: the
# safety comes from `rm`, not from the code, and C2 is what moves it into the code.
#
# Usage: zsh t368-c2-refusal.zsh <T365's fire-program.sh> <main's fire-program.sh>
emulate -L zsh
set -uo pipefail

AFTER="${1:?usage: t368-c2-refusal.zsh <after> <before>}"
BEFORE="${2:?usage: t368-c2-refusal.zsh <after> <before>}"
BAD="/nonexistent-t368-$$/"

print -r -- "=== T368: condition C2, driven on this host. TMPDIR=$BAD (unwritable, absent)"
print -r -- ""
print -r -- "--- AFTER (T365)  sha256=$(shasum -a 256 "$AFTER" | awk '{print $1}')"
TMPDIR="$BAD" /bin/zsh "$AFTER" --self-test-lock-readers 2>&1
print -r -- "rc=$?   <- expected 2, refusing BEFORE any trap is installed"
print -r -- ""
print -r -- "--- BEFORE (main, PRE-C2)  sha256=$(shasum -a 256 "$BEFORE" | awk '{print $1}')"
print -r -- "    first 3 lines and the tail; look for scratch=/ and the rm refusal."
TMPDIR="$BAD" /bin/zsh "$BEFORE" --self-test-lock-readers 2>&1 | sed -n '1,3p;$!d;p'
print -r -- ""
print -r -- "--- BEFORE, tail only:"
TMPDIR="$BAD" /bin/zsh "$BEFORE" --self-test-lock-readers 2>&1 | tail -4
print -r -- "rc=$?"
