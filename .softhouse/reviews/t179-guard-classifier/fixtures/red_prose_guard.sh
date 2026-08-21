#!/usr/bin/env bash
# T179 SHELL FIXTURE (a) — the word `trap` appears only inside an echoed string.
# T156's GUARD regex scores this GUARDED. This tool must REFUSE it, not classify it.
set -euo pipefail
echo "One trap worth naming: restore with a trap, not a plain statement" > /dev/null
cp .softhouse/vectors/t179-fixture-never-run/case.json /tmp/x
sed -i '' 's/a/b/' .softhouse/vectors/t179-fixture-never-run/case.json
