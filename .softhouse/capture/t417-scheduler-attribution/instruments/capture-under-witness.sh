#!/usr/bin/env bash
# capture-under-witness.sh -- RUN A CAPTURE INSIDE A WITNESSED WINDOW.
#
#   bash .../instruments/capture-under-witness.sh <label> -- <command> [args...]
#
# This is the one-line adoption of the pin. It:
#   1. opens an oracle-window-witness over the WHOLE graded surface (273 base tables and 249
#      sequences today -- everything except the 8 named scheduler-bookkeeping tables),
#   2. runs your capture command,
#   3. closes the witness,
#   4. writes a PROVENANCE block for the capture, and
#   5. REFUSES -- non-zero, loudly -- if the oracle moved while the capture was open.
#
# WHY A WRAPPER AND NOT A BAR GUARD. The bar (`conformance.sh`) runs on a tree, at a time
# nobody chose, against an oracle that legitimately moves every night. A digest pinned in the
# bar would go red at 00:01 Asia/Ulaanbaatar every day for reasons no diff caused -- P-45
# wearing the opposite hat, a check that cries so reliably that its red carries no information.
# The question this pin answers is not "has the oracle EVER moved" (it has, and it will) but
# "did it move WHILE THIS CAPTURE WAS BEING TAKEN", and that question only exists at capture
# time. So the enforcement point is the capture, not the bar.
#
# WHAT THE PROVENANCE BLOCK IS FOR. Vectors already carry `provenance.capture_ref` +
# `capture_sha256` and `oracle.fineract_commit` + `oracle.captured_at`
# [.softhouse/vectors/ledger/*.json]. None of that says whether the oracle was still. The block
# written here adds the missing field: the graded-surface rollup the capture was taken against,
# the job_run_history high-water mark at both ends, and the verdict. A later reader can then run
# `oracle-window-witness.sh verify <label>` and learn whether a parity divergence is the port or
# THE CLOCK -- which is the whole reason this exists, because parity sign-off is a `user` gate.
#
# EXIT CODES
#   0  the capture command succeeded AND the window was certified quiescent
#   1  the window was CONTAMINATED, or the capture command failed, or the witness refused
#   2  the oracle's database was UNREACHABLE -- no verdict; NOT a failure of the capture
#   3  wrong interpreter
#
# READ-ONLY with respect to the oracle: this wrapper issues only SELECTs. Whatever your capture
# command does is your responsibility -- and if it writes, this wrapper will tell you exactly
# what it moved, which is a feature and not a bug.

if [ -z "${BASH_VERSION:-}" ]; then echo "REFUSING: run with bash." >&2; exit 3; fi
if shopt -qo posix 2>/dev/null; then echo "REFUSING: bash in POSIX mode (you ran 'sh')." >&2; exit 3; fi
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
W="$HERE/oracle-window-witness.sh"
DIR=$(cd "$HERE/.." && pwd)
WIT="${ORACLE_WITNESS_DIR:-$DIR/witness}"

label="${1:-}"
if [ -z "$label" ] || [ "${2:-}" != "--" ]; then
  echo "usage: capture-under-witness.sh <label> -- <command> [args...]" >&2; exit 1
fi
shift 2
[ $# -ge 1 ] || { echo "REFUSING: no capture command given after --." >&2; exit 1; }

OPENLOG="$WIT/$label.open.log"
CLOSELOG="$WIT/$label.close.log"
PROV="$WIT/$label.provenance.tsv"
mkdir -p "$WIT"

bash "$W" open "$label" > "$OPENLOG" 2>&1
orc=$?
cat "$OPENLOG"
if [ "$orc" -eq 2 ]; then
  echo "capture-under-witness: ORACLE UNREACHABLE (exit 2). The capture was NOT run --"
  echo "  a capture nobody can witness is a capture nobody can reproduce."
  exit 2
fi
[ "$orc" -eq 0 ] || { echo "capture-under-witness: the witness REFUSED to open. Capture not run."; exit 1; }

echo "-----------------------------------------------------------------------------"
echo "RUNNING THE CAPTURE: $*"
echo "-----------------------------------------------------------------------------"
"$@"
crc=$?
echo "-----------------------------------------------------------------------------"
echo "capture command exit = $crc"

bash "$W" close "$label" > "$CLOSELOG" 2>&1
wrc=$?
cat "$CLOSELOG"

# --- the provenance block --------------------------------------------------------------
# Machine-greppable, one fact per line, every value DERIVED from the two witness files.
{
  echo "# capture provenance v1 -- written by capture-under-witness.sh"
  printf 'label\t%s\n' "$label"
  printf 'command\t%s\n' "$*"
  printf 'command_exit\t%s\n' "$crc"
  printf 'fineract_commit\t%s\n' "$(awk -F'\t' '$2=="fineract_commit"{print $3; exit}' "$WIT/$label.open.tsv" 2>/dev/null)"
  printf 'window_open_db_utc\t%s\n'  "$(awk -F'\t' '$2=="db_now_utc"{print $3; exit}' "$WIT/$label.open.tsv" 2>/dev/null)"
  printf 'window_close_db_utc\t%s\n' "$(awk -F'\t' '$2=="db_now_utc"{print $3; exit}' "$WIT/$label.close.tsv" 2>/dev/null)"
  printf 'jrh_high_water_open\t%s\n'  "$(awk -F'\t' '$2=="max_id"{print $3; exit}' "$WIT/$label.open.tsv" 2>/dev/null)"
  printf 'jrh_high_water_close\t%s\n' "$(awk -F'\t' '$2=="max_id"{print $3; exit}' "$WIT/$label.close.tsv" 2>/dev/null)"
  printf 'jobs_active\t%s\n' "$(awk -F'\t' '$2=="active"{print $3; exit}' "$WIT/$label.open.tsv" 2>/dev/null)"
  printf 'runs_in_window\t%s\n' "$(awk '/RUNS OVERLAPPING WINDOW/{print $NF; exit}' "$CLOSELOG" 2>/dev/null)"
  printf 'graded_tables\t%s\n' "$(grep -c '^tbl	' "$WIT/$label.open.tsv" 2>/dev/null)"
  printf 'graded_sequences\t%s\n' "$(grep -c '^seq	' "$WIT/$label.open.tsv" 2>/dev/null)"
  printf 'rollup_open\t%s\n'  "$(grep -E '^(tbl|seq)	' "$WIT/$label.open.tsv"  2>/dev/null | LC_ALL=C sort | { command -v md5 >/dev/null 2>&1 && md5 -q || md5sum | awk '{print $1}'; })"
  printf 'rollup_close\t%s\n' "$(grep -E '^(tbl|seq)	' "$WIT/$label.close.tsv" 2>/dev/null | LC_ALL=C sort | { command -v md5 >/dev/null 2>&1 && md5 -q || md5sum | awk '{print $1}'; })"
  printf 'witness_verdict\t%s\n' "$(grep -o 'VERDICT: [A-Z-]*' "$CLOSELOG" 2>/dev/null | head -1 | sed 's/VERDICT: //')"
  printf 'witness_exit\t%s\n' "$wrc"
  printf 'shelf_life_check\tbash %s verify %s\n' "${W#"$DIR/"}" "$label"
} > "$PROV"

echo "-----------------------------------------------------------------------------"
echo "PROVENANCE -> $PROV"
sed 's/^/  /' "$PROV"
echo "-----------------------------------------------------------------------------"

if [ "$wrc" -eq 2 ]; then
  echo "capture-under-witness: ORACLE UNREACHABLE at close (exit 2). No verdict is available."
  echo "  This is NOT a statement that the capture is bad, and NOT a statement that it is good."
  exit 2
fi
if [ "$wrc" -ne 0 ]; then
  echo "capture-under-witness: REFUSED (exit 1). THE ORACLE MOVED WHILE THIS CAPTURE WAS OPEN."
  echo "  Do not promote anything captured in this window to a vector. Re-capture in a window"
  echo "  the witness certifies QUIESCENT, and read the run list above for the candidate author."
  exit 1
fi
if [ "$crc" -ne 0 ]; then
  echo "capture-under-witness: the window was quiescent, but THE CAPTURE COMMAND FAILED ($crc)."
  echo "  A clean window is not a successful capture."
  exit 1
fi
echo "capture-under-witness: OK. The capture was taken against a still oracle, and the"
echo "  provenance above records exactly which state that was."
exit 0
