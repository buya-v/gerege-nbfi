#!/usr/bin/env bash
# T386 -- write a committed copy of a casualty-sweep transcript with the QUOTED HIT LINES removed,
# and say so in the file itself.
#
#   bash .../t386-filter-transcript.sh <raw> <dst> <label> <cmd>
#
# WHY. The sweep lists every LIVE hit, quoting other files' lines verbatim -- 235 kB of them on
# this corpus. Committing that would import those files' repo-path references into T316's
# dead-path census, which is exactly how T371's own bar went RED. Removed are ONLY the indented
# hit-listing lines (`^      `); every calibration line, every per-selector cardinal and the
# SWEEP-RESULT summary survive untouched. The filter, the raw line count and the command that
# regenerates the full output are written into the head of the file, so the omission is a stated
# fact and not a silent one.
set -uo pipefail
RAW=${1:?raw}; DST=${2:?dst}; LABEL=${3:?label}; CMD=${4:?cmd}
[ -f "$RAW" ] || { echo "no such raw transcript: $RAW" >&2; exit 2; }
{
  echo "T386 -- $LABEL"
  echo "  cmd  : $CMD"
  echo
  echo "FILTERED, and the filter is stated so the omission is not a claim:"
  echo "  removed are ONLY the indented hit-listing lines (^' '{6}) -- the sweep quoting other"
  echo "  files' lines verbatim. Committing them would import those files' repo-path references"
  echo "  into T316's dead-path census; that is how T371's own bar went RED. Every calibration"
  echo "  line, every per-selector cardinal and the SWEEP-RESULT summary are untouched."
  echo "  raw output: $(grep -c . "$RAW") non-empty lines; regenerate with the command above."
  echo "  raw sha256: $(shasum -a 256 < "$RAW" | cut -d' ' -f1)"
  echo "=============================================================================="
  grep -v '^      ' "$RAW"
} > "$DST"
echo "wrote $DST ($(grep -c . "$DST") non-empty lines, from $(grep -c . "$RAW"))"
