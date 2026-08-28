#!/usr/bin/env bash
# T397 -- A17 driven END TO END on both sides of the change, in one script.
#
# BEFORE: verbatimInCapture neutralised back to a bare bytes.Contains (the exact
#   pre-T397 semantics). The prefix is ADMITTED, the port converts "100.12"
#   happily and posts, and the DIVERGENCE COMPARATOR catches it -- exit 1. That
#   is T387's self-correction, reproduced rather than quoted, and it is the
#   control this task must keep alive.
# AFTER: the boundary rule refuses the vector at ADMISSION -- exit 2,
#   `ledger inadmissible 1`, and the comparator never runs.
#
# Two independent layers, each demonstrated separately (P-45).
#
# Usage: bash a17-before-after.sh <repo-root>
set -euo pipefail

ROOT="${1:?repo root}"
ADMIT="$ROOT/nexus/internal/apps/ledger/conformance/admit.go"
OUT="$ROOT/.softhouse/capture/t397-t387-conditions/out"
SAVE="$OUT/../admit.go.a17"
mkdir -p "$OUT/attacks"

cp "$ADMIT" "$SAVE"
trap 'cp "$SAVE" "$ADMIT"; rm -f "$SAVE"; git -C "$ROOT" checkout -- .softhouse/vectors/' EXIT

# --- BEFORE -----------------------------------------------------------------
perl -pi -e 's/\Qif tokenBoundedIndex(raw, \E/if false \&\& tokenBoundedIndex(raw, /' "$ADMIT"
grep -q 'if false && tokenBoundedIndex' "$ADMIT" || { echo "NEUTRALISATION DID NOT APPLY"; exit 9; }
( cd "$ROOT/nexus" && go build -o /tmp/t397-conf-before ./internal/apps/loanschedule/conformance/cmd/conformance )
python3 "$ROOT/.softhouse/capture/t397-t387-conditions/instruments/a17.py" /tmp/t397-conf-before \
  > "$OUT/attacks/A17-BEFORE-bare-contains.txt" 2>&1 || true
mv "$OUT/attacks/A17-request-prefix-substring.log" "$OUT/attacks/A17-BEFORE-bare-contains.log"

# --- AFTER ------------------------------------------------------------------
cp "$SAVE" "$ADMIT"
( cd "$ROOT/nexus" && go build -o /tmp/t397-conf-after ./internal/apps/loanschedule/conformance/cmd/conformance )
python3 "$ROOT/.softhouse/capture/t397-t387-conditions/instruments/a17.py" /tmp/t397-conf-after \
  > "$OUT/attacks/A17-AFTER-token-bounded.txt" 2>&1 || true
mv "$OUT/attacks/A17-request-prefix-substring.log" "$OUT/attacks/A17-AFTER-token-bounded.log"

echo "===== BEFORE (bare bytes.Contains -- T387's measured state) ====="
cat "$OUT/attacks/A17-BEFORE-bare-contains.txt"
echo "===== AFTER (token-bounded) ====="
cat "$OUT/attacks/A17-AFTER-token-bounded.txt"
