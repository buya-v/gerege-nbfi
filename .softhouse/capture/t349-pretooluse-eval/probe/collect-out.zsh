#!/bin/zsh
# T349 -- copy the scratch evidence into the capture directory (the scratch tree is /tmp
# and will not survive; the measurements must).
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
CAP=${T349_CAP:?capture dir}
mkdir -p "$CAP/out"
for f in "$ROOT"/out/*.report.txt "$ROOT"/out/*.hook.jsonl "$ROOT"/out/candidate.gate.jsonl \
         "$ROOT"/out/cost.txt "$ROOT"/out/replay.txt "$ROOT"/out/unit-drive.txt; do
  [[ -e "$f" ]] && cp "$f" "$CAP/out/"
done
ls -la "$CAP/out"
