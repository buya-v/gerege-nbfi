#!/bin/bash
# T416 — F-T405-4, re-driven rather than inherited.
#
# T405 NARROWED this against its own first statement: making a PARITY vector
# inadmissible DOES move EXEMPTION_PIN_LEDGER_PARITY (7 -> 6), so the four pinned
# LEDGER figures do guard the parity and oracle-refusal classes. The hole is
# specific to the DIVERGENCE class, which contributes to none of the four.
#
# Both halves are driven here, on the same store, with the same binary.
set -u
ROOT="${1:?repo root}"
OUT="$ROOT/.softhouse/capture/t416-t405-conditions/out"
DIV="$ROOT/.softhouse/vectors/ledger/LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json"
PAR="$ROOT/.softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json"
mkdir -p "$OUT"

census() {
  LC_ALL=C grep -aE '^ *ledger (parity|oracle-refusal|inadmissible|cells compared|exemptions)|^ *divergence vectors|^VERDICT' "$1" \
    | sed 's/  */ /g' | head -8
}

show() {
  local label="$1" file="$2" expr="$3"
  git -C "$ROOT" checkout -- "$file"
  if [ -n "$expr" ]; then
    /usr/bin/sed -i '' "$expr" "$file"
    if git -C "$ROOT" diff --quiet -- "$file"; then echo "$label: MUTATION DID NOT APPLY"; return; fi
  fi
  CONFORMANCE_REPO_ROOT="$ROOT" /tmp/t416-conf-after -oracle-probe=up > "$OUT/e4-$label.log" 2>&1
  echo "=== $label (exit $?) ==="
  census "$OUT/e4-$label.log"
  echo
  git -C "$ROOT" checkout -- "$file"
}

show baseline                "$DIV" ""
# THE HOLE: a DIVERGENCE vector refused admission. Every pinned LEDGER figure
# must be re-read from this transcript, not assumed.
show divergence-inadmissible "$DIV" 's/"100.125000"/"100.12500"/'
# THE CONTROL: a PARITY vector refused admission, which T405 measured as CAUGHT
# by EXEMPTION_PIN_LEDGER_PARITY. If this one does not move the parity figure
# either, the finding is about inadmissibility generally and not the divergence
# class, and the request below would be aimed at the wrong pin.
show parity-inadmissible     "$PAR" 's/"http_status": 200/"http_status": 201/'

echo "store clean: $(git -C "$ROOT" status --porcelain -- .softhouse/vectors | wc -l) dirty"
