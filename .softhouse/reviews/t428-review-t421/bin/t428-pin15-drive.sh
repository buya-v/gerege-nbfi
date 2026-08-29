#!/bin/bash
# T428: independently reproduce T421's P-83 evidence. Set the wrong-impl pin back
# to 15 on the T421 tree, run the bar, and require:
#   exit 2, POPULATION 16 / PINNED 15, and THE PROBE LINE PRESENT (so the exit 2
#   is the hard guard firing, not an oracle outage).
# The pin is restored by a trap and the file digest is checked byte-for-byte.
set -u
tree="$1"; out="$2"
sh_file="$tree/.softhouse/conformance.sh"
BACKUP=$(mktemp)
cp "$sh_file" "$BACKUP"
BEFORE=$(shasum -a 256 "$sh_file" | cut -d' ' -f1)
restore() {
  cp "$BACKUP" "$sh_file"
  AFTER=$(shasum -a 256 "$sh_file" | cut -d' ' -f1)
  if [ "$BEFORE" != "$AFTER" ]; then
    echo "*** RESTORE FAILED: $AFTER != $BEFORE" >&2
    exit 9
  fi
  echo "conformance.sh RESTORED byte-for-byte ($AFTER)" | tee -a "$out"
  rm -f "$BACKUP"
}
trap restore EXIT

{
  echo "T428 PIN-AT-15 DRIVE -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "tree: $tree"
  echo "conformance.sh sha256 before: $BEFORE"
} > "$out"

LC_ALL=C sed -i '' 's/^EXEMPTION_PIN_LEDGER_WRONGIMPLS=16$/EXEMPTION_PIN_LEDGER_WRONGIMPLS=15/' "$sh_file"
echo "pin line now: $(LC_ALL=C grep -n '^EXEMPTION_PIN_LEDGER_WRONGIMPLS=' "$sh_file")" >> "$out"

cd "$tree" || exit 9
bash .softhouse/conformance.sh >> "$out" 2>&1
rc=$?
{
  echo "EXIT=$rc"
  echo "--- the three lines that decide the reading ---"
  LC_ALL=C grep -nE 'WRONG-IMPLEMENTATION POPULATION|probe = |EXIT 2' "$out" | tail -20
  echo -n "probe lines present: "
  LC_ALL=C grep -c 'probe = ' "$out"
} >> "$out"
echo "EXIT=$rc"
