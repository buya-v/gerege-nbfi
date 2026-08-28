#!/bin/bash
# T428: run the conformance bar in a named tree, capture exit code and instants.
# usage: runbar.sh <treeroot> <outfile>
set -u
tree="$1"; out="$2"
cd "$tree" || exit 9
{
  echo "=== T428 bar run ==="
  echo "tree: $tree"
  echo "HEAD: $(git rev-parse HEAD)"
  echo "started_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$out"
bash .softhouse/conformance.sh >> "$out" 2>&1
rc=$?
{
  echo "EXIT=$rc"
  echo "finished_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$out"
echo "EXIT=$rc"
