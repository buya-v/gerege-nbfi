#!/usr/bin/env bash
# T291 -- reproduce F-T291-1 INSIDE T286's OWN no-lost-refusal sweep, unmodified.
#
# T286's sweep asserts `PRE==1 => NEW==1` over 38 fixtures and reports 0 lost refusals. That is a
# statement about ITS CORPUS, not about the rule. Drop this review's four fixtures into that
# corpus -- changing not one line of T286's instrument -- and the same sweep reports FOUR LOST
# REFUSALS and the battery goes 31/1, exit 1.
#
# Requires T286's branch state present in the tree (merged, or `git checkout softhouse/t286-t268-
# retry -- .softhouse/capture/...` first). IF IT IS NOT THERE THIS SCRIPT SAYS SO AND EXITS 2. It
# never reports "clean" from an absence.
#
# The fixtures are copied in and REMOVED again, and T268's committed red-green-legs.json -- which
# T286's driver overwrites as a side effect -- is restored, so running this cannot move another
# task's committed bytes (T286's own FU-T286-2).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
G=/usr/bin/grep                       # NOT the bundled ugrep on PATH
T286FIX="$ROOT/.softhouse/capture/t286-rvpa-retry/red/fixtures"
DRIVER="$ROOT/.softhouse/capture/t286-rvpa-retry/red/drive_red_t286.py"
T268LEGS="$ROOT/.softhouse/capture/t268-rvpa-failopen/out/red-green-legs.json"
FIXTURES="X2-header-in-nested-list X3-header-in-list-of-lists X4-toplevel-array-header-only X7-header-in-deep-nested-list"

if [ ! -d "$T286FIX" ] || [ ! -f "$DRIVER" ]; then
  printf 'NOT MEASURED: T286 branch state is absent from this tree.\n' >&2
  printf '  expected %s\n' "$DRIVER" >&2
  printf '  This is a statement about THIS TREE, never about the rule. Check T286 out first.\n' >&2
  exit 2
fi

cleanup() {
  for f in $FIXTURES; do rm -f "$T286FIX/$f.json"; done
  if [ -f "$T268LEGS" ]; then
    local crc=0
    git -C "$ROOT" checkout -- "$T268LEGS" || crc=$?
    # NOT `|| true`. If the restore fails, another task's committed evidence is left moved, and
    # that must be SAID, not swallowed -- it is the same defect class this review is about.
    [ "$crc" -eq 0 ] || printf '*** FAILED to restore %s (git checkout exit %s). ANOTHER TASK\n*** EVIDENCE FILE IS LEFT MODIFIED. Restore it by hand before committing anything.\n' "$T268LEGS" "$crc" >&2
  fi
}
trap cleanup EXIT

for f in $FIXTURES; do
  cp "$HERE/fixtures/$f.json" "$T286FIX/$f.json"
done

RC=0
python3 "$DRIVER" > "$HERE/../out/t286-own-sweep-with-t291-fixtures.txt" 2>&1 || RC=$?
printf 'T286 driver exit: %s\n' "$RC"
$G -a 'LOST REFUSAL\|SWEEP:\|T286 BATTERY:' "$HERE/../out/t286-own-sweep-with-t291-fixtures.txt"

# The POINT of this script is that the driver FAILS. A zero exit here means the finding did not
# reproduce, which is itself the news -- so it is reported, never swallowed.
if [ "$RC" -eq 0 ]; then
  printf '\n*** T286 BATTERY PASSED WITH THE T291 FIXTURES PRESENT. F-T291-1 did NOT reproduce\n'
  printf '*** on this tree. Do not read this as agreement with T291; read it as a disagreement\n'
  printf '*** that must be resolved before either finding is acted on.\n'
  exit 1
fi
printf '\nF-T291-1 REPRODUCED inside T286 own instrument, unmodified. Driver exit %s.\n' "$RC"
exit 0
