#!/usr/bin/env bash
# T285 — WATCH the shared residue file. It creates and deletes nothing; it only samples
# `[ -e ]` once a second and prints a timestamped line per sample, so a state change is a
# visible transition rather than an inference from two distant `ls` calls.
#
# It exists because the file vanished twice during this review with no action of mine,
# while sibling workers were live in the same /tmp namespace.
set -u
N="${1:-90}"
P=/tmp/t234_matrix2.txt
prev=""
echo "### T285 residue watch — $N samples, 1 s apart, read-only"
i=0
while [ "$i" -lt "$N" ]; do
  if [ -e "$P" ]; then now=PRESENT; else now=ABSENT; fi
  if [ "$now" != "$prev" ]; then
    printf '%s  %s\n' "$(date +%H:%M:%S)" "$now"
    prev="$now"
  fi
  i=$((i + 1))
  sleep 1
done
printf '%s  (end, %s)\n' "$(date +%H:%M:%S)" "$prev"
