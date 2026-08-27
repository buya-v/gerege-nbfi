#!/usr/bin/env bash
# T300 — re-extract BOTH printed cardinal pairs from the red-drive artefacts.
#
# WHY THIS EXISTS AND WHY IT IS NOT A RE-RUN. 50-red-drive.sh's first summary printed only the
# host-state pair, so arm D — whose subject is the FAIL-OPEN pair — was summarised as
# `census=18 pinned=18`, a true statement about the wrong guard. The reporter is now widened,
# but the fix does not need five more bar runs: the ARTEFACTS ARE THE PRIMARY EVIDENCE and they
# recorded both lines all along. This script reads them, so the corrected table is derived from
# the same bytes the narrow summary was derived from, not from a fresh run whose numbers a
# reader would have to take on trust.
set -u
ROOT="$(git rev-parse --show-toplevel)"
RED="$ROOT/.softhouse/capture/t300-census-cardinal/red"

printf '%-34s %-6s %-26s %-26s %-6s\n' ARTEFACT EXIT FAIL-OPEN HOST-STATE PROBE
for f in "$RED"/A-pin-minus-one.txt "$RED"/B-pin-plus-one.txt \
         "$RED"/C1-prefix-minus-one.txt "$RED"/C2-prefix-plus-one.txt \
         "$RED"/D-failopen-minus-one.txt; do
  [ -f "$f" ] || continue
  rc="$(LC_ALL=C sed -n 's/^EXIT=\([0-9][0-9]*\)$/\1/p' "$f")"
  fo="$(LC_ALL=C sed -n 's/^conformance:   .*repository); frontier \([0-9][0-9]*\), pinned at \([0-9-][0-9]*\).*$/frontier=\1 pinned=\2/p' "$f")"
  hs="$(LC_ALL=C sed -n 's/^conformance:   .*path to a name: \([0-9][0-9]*\), pinned at \([0-9-][0-9]*\).*$/census=\1 pinned=\2/p' "$f")"
  # P-84 — the probe line's PRESENCE is read before any value. 0 here is a HARD guard refusing
  # upstream of the probe, never an oracle outage.
  pr="$(LC_ALL=C grep -ac 'probe = ' "$f")"
  printf '%-34s %-6s %-26s %-26s %-6s\n' "$(basename "$f")" "${rc:-?}" "${fo:-<not printed>}" "${hs:-<not printed>}" "$pr"
done
