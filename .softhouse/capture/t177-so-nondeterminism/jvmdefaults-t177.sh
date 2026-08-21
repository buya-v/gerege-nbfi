#!/bin/bash
# T177 — read the JVM's OWN default thread stack size and compiler settings out of the pinned image,
# so the -Xss sweep can be stated against a MEASURED default instead of an assumed one. This reads
# JVM configuration; it calls no seam, computes no money value and touches no capture.
set -uo pipefail
EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
OUT="$1"
ACTUAL_IMAGE_ID=$(docker image inspect "$EXPECTED_IMAGE_REF" --format '{{.Id}}')
[ "$ACTUAL_IMAGE_ID" = "$EXPECTED_IMAGE_ID" ] || { echo "PRECONDITION FAILED: image $ACTUAL_IMAGE_ID" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"
{
  printf 'image %s\n' "$ACTUAL_IMAGE_ID"
  docker run --rm --entrypoint sh "$EXPECTED_IMAGE_REF" -c '
    java -version 2>&1
    echo "--- flags ---"
    java -XX:+PrintFlagsFinal -version 2>/dev/null | grep -E "ThreadStackSize|MaxJavaStackTraceDepth|TieredCompilation|TieredStopAtLevel|CICompilerCount|Tier3InvocationThreshold|Tier4InvocationThreshold"
    echo "--- nproc / memory ---"
    nproc
    cat /sys/fs/cgroup/memory.max 2>/dev/null || echo "no cgroup memory.max"
  '
} > "$OUT" 2>&1
cat "$OUT"
