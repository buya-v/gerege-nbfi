#!/usr/bin/env bash
# T179 SHELL FIXTURE (b) — a REAL trap on every exit path.
# This tool must REFUSE it too: the refusal is symmetric and honest, because without
# a shell parser this tool cannot tell these two files apart.
set -euo pipefail
cp .softhouse/vectors/t179-fixture-never-run/case.json /tmp/x.bak
trap 'mv /tmp/x.bak .softhouse/vectors/t179-fixture-never-run/case.json' EXIT INT TERM HUP
sed -i '' 's/a/b/' .softhouse/vectors/t179-fixture-never-run/case.json
