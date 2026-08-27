#!/usr/bin/env bash
# T254 reviewer instrument: ADJUDICATE the t234 /tmp-residue disagreement by
# running it, not by preferring an author.
#
# THE DISAGREEMENT
#   CLOUD (T253): fixing D1 unmasked a THIRD defect -- the t234 escape-matrix
#     instrument's fail-open TIER depends on leftover /tmp state, flipping
#     TIER2 -> TIER1 off the Mac. It REFUSED to move the pin or weaken the
#     guard to make its own bar green.
#   MAC (T253b): reproduces the residue effect, but says the frontier COUNT and
#     PATH-SET are identical in both arms, and the harness pins BY PATH, so it
#     fails no BAR -- a CLASSIFICATION defect, not a FRONTIER defect.
#
# THE EXPERIMENT. Run the same tree twice, changing only whether
# /tmp/t234_matrix2.txt exists. Compare, in order:
#   (a) BAR exit code
#   (b) probe line PRESENCE, then value      (P-83)
#   (c) frontier COUNT and PINNED count
#   (d) the frontier PATH SET, sorted        <-- the Mac's decisive claim
#   (e) any TIER classification difference
#
# The residue is BACKED UP and RESTORED. This instrument does not destroy state.
#
# P-80: no absence is inferred from a grep rc; rc>1 aborts.
set -euo pipefail

TREE="${1:?tree}"
OUT="${2:?outdir}"
G=/usr/bin/grep
RESIDUE=/tmp/t234_matrix2.txt
BACKUP="$OUT/.t234_matrix2.backup"

echo "======================================================================"
echo "T234 /tmp-RESIDUE ADJUDICATION"
echo "tree: $TREE"
echo "======================================================================"

had_residue=0
if [ -e "$RESIDUE" ]; then
  had_residue=1
  cp -p "$RESIDUE" "$BACKUP"
  echo "residue $RESIDUE PRESENT at start; backed up to $BACKUP"
else
  echo "residue $RESIDUE ABSENT at start"
fi

restore() {
  if [ "$had_residue" -eq 1 ]; then
    cp -p "$BACKUP" "$RESIDUE" 2>/dev/null || true
    echo "[restore] residue put back at $RESIDUE"
  else
    rm -f "$RESIDUE" 2>/dev/null || true
    echo "[restore] residue removed again (it was absent at start)"
  fi
}
trap restore EXIT

run_arm() {   # run_arm LABEL
  local label="$1"
  local so="$OUT/70-residue-$label.stdout.txt"
  local se="$OUT/70-residue-$label.stderr.txt"
  local rc=0
  # A NON-ZERO BAR EXIT IS THE MEASUREMENT, NOT AN ERROR OF THIS SCRIPT, so
  # `set -e` is lifted for exactly this call and restored immediately.
  set +e
  ( cd "$TREE" && bash .softhouse/conformance.sh ) > "$so" 2> "$se"
  rc=$?
  set -e
  echo "$rc" > "$OUT/70-residue-$1.rc"
  echo "  BAR_EXIT=$rc"
}

report_arm() {  # report_arm LABEL
  # NOTE: bash 3.2 (this host) does NOT make an earlier name on the SAME `local`
  # statement visible to a later one, so these are declared separately.
  local label="$1"
  local so="$OUT/70-residue-$label.stdout.txt"
  local se="$OUT/70-residue-$label.stderr.txt"
  local both="$OUT/70-residue-$label.both.txt"
  cat "$so" "$se" > "$both"

  echo "  --- ARM: $label ---"
  echo "  (a) BAR_EXIT ............... $(cat "$OUT/70-residue-$label.rc")"

  # (b) PRESENCE BEFORE VALUE (P-83)
  local n rc
  set +e; n=$("$G" -c -E -e 'probe[[:space:]]*=' -- "$both"); rc=$?; set -e
  [ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 91; }
  echo "  (b) PROBE LINE PRESENT? .... $([ "$n" -gt 0 ] && echo YES || echo 'NO — NOT PRINTED')"
  if [ "$n" -gt 0 ]; then
    set +e; "$G" -h -E -e 'probe[[:space:]]*=' -- "$both" | sed 's/^/      value: /'; rc=$?; set -e
  fi

  # (c) frontier / pinned counts
  set +e; "$G" -h -E -e 'frontier [0-9]+, pinned at [0-9]+' -- "$both" | sed 's/^/  (c) /'; rc=$?; set -e
  [ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 92; }
  [ "$rc" -eq 1 ] && echo "  (c) frontier line ABSENT (measured negative)"

  set +e; "$G" -h -E -e 'frontier == pinned|frontier != pinned|rows, by path' -- "$both" | sed 's/^/  (c) /'; rc=$?; set -e
  [ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 93; }

  # (d) the frontier PATH SET
  set +e
  "$G" -h -E -e '^[[:space:]]*(TIER[0-9A-Z]*)[[:space:]]+\.softhouse/' -- "$both" \
    | sed 's/^[[:space:]]*//' | sort > "$OUT/70-residue-$label.paths.txt"
  rc=$?
  set -e
  [ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 94; }
  echo "  (d) frontier rows printed .. $(wc -l < "$OUT/70-residue-$label.paths.txt" | tr -d ' ')"
}

echo
echo "### ARM 1: residue PRESENT"
[ -e "$RESIDUE" ] || cp -p "$BACKUP" "$RESIDUE" 2>/dev/null || : > "$RESIDUE"
run_arm present
report_arm present

echo
echo "### ARM 2: residue ABSENT"
rm -f "$RESIDUE"
[ ! -e "$RESIDUE" ] || { echo "FATAL: could not remove $RESIDUE" >&2; exit 95; }
run_arm absent
report_arm absent

echo
echo "======================================================================"
echo "ADJUDICATION"
echo "======================================================================"
echo "exit codes:  present=$(cat "$OUT/70-residue-present.rc")   absent=$(cat "$OUT/70-residue-absent.rc")"
echo
echo "--- diff of the frontier PATH SETS (empty == the Mac's claim holds) ---"
if diff -u "$OUT/70-residue-present.paths.txt" "$OUT/70-residue-absent.paths.txt"; then
  echo "  (no difference in the printed frontier rows)"
fi
echo
echo "--- diff of the FULL stdout (what the residue actually changes) ---"
diff -u "$OUT/70-residue-present.stdout.txt" "$OUT/70-residue-absent.stdout.txt" \
  | head -80 || true
