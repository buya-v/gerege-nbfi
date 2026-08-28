#!/bin/bash
set -u
tree="$1"; out="$2"
{
  echo "T428 BUILD + TEST -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "tree: $tree"
  echo
  echo "=== go build -C $tree/nexus ./... ==="
} > "$out"
go build -C "$tree/nexus" ./... >> "$out" 2>&1
echo "go build EXIT=$?" >> "$out"
echo >> "$out"
echo "=== go vet -C $tree/nexus ./... ===" >> "$out"
go vet -C "$tree/nexus" ./... >> "$out" 2>&1
echo "go vet EXIT=$?" >> "$out"
echo >> "$out"
echo "=== go test -count=1 -C $tree/nexus ./... ===" >> "$out"
go test -C "$tree/nexus" -count=1 ./... >> "$out" 2>&1
echo "go test EXIT=$?" >> "$out"
cat "$out"
