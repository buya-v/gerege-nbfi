#!/bin/bash
# T416 — F-T405-5, driven on the REAL corpus with the CORRECT port (ledger-go,
# no -ledger-impl flag), re-deriving T405's cardinals rather than inheriting them.
#
# One cell of the parity vector LDG-01 is mutated, the SAME store is graded by
# two binaries that differ ONLY in report.go — BEFORE = main's bytes,
# AFTER = this branch's — and the vector is reverted. Three mutation classes:
# structural, MONEY, and totals.
set -u
ROOT="${1:?repo root}"
OUT="$ROOT/.softhouse/capture/t416-t405-conditions/out"
V="$ROOT/.softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json"
mkdir -p "$OUT"

run_one() {
  local label="$1" bin="$2" tag="$3"
  CONFORMANCE_REPO_ROOT="$ROOT" "$bin" -oracle-probe=up > "$OUT/e5-$label-$tag.log" 2>&1
  local rc=$?
  printf '  %-8s exit=%s  %-42s | %s\n' "$tag" "$rc" \
    "$(LC_ALL=C grep -aE '^ *ledger parity' "$OUT/e5-$label-$tag.log" | head -1 | tr -s ' ')" \
    "$(LC_ALL=C grep -aE '^VERDICT' "$OUT/e5-$label-$tag.log")"
}

try() {
  local label="$1" expr="$2"
  git -C "$ROOT" checkout -- "$V"
  /usr/bin/sed -i '' "$expr" "$V"
  if git -C "$ROOT" diff --quiet -- "$V"; then echo "$label: MUTATION DID NOT APPLY"; return; fi
  echo "=== $label ==="
  LC_ALL=C grep -aE '^ *LDG-01|amount_minor:|gl_account_code:|total_debits_minor:' \
    <(CONFORMANCE_REPO_ROOT="$ROOT" /tmp/t416-conf-after -oracle-probe=up 2>&1) | head -4
  run_one "$label" /tmp/t416-conf-before BEFORE
  run_one "$label" /tmp/t416-conf-after  AFTER
  git -C "$ROOT" checkout -- "$V"
}

try glcode      's/"gl_account_code": "10300"/"gl_account_code": "10399"/'
try amountminor 's/"amount_minor": "10000025"/"amount_minor": "10000026"/'
try totals      's/"total_debits_minor": "12500062"/"total_debits_minor": "12500063"/'

echo "=== unmutated control (the run must be GREEN, or every row above is meaningless) ==="
run_one control /tmp/t416-conf-before BEFORE
run_one control /tmp/t416-conf-after  AFTER
git -C "$ROOT" checkout -- "$V"
echo "store clean: $(git -C "$ROOT" status --porcelain -- .softhouse/vectors | wc -l) dirty"
