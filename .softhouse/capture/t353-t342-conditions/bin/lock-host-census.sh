#!/bin/sh
# T353 / CONDITION 1, second half. "State what arms 3 and 5 have in fact been doing on the
# cloud fire" presupposes that the cloud fire EXECUTES `.softhouse/bin/fire-program.sh`.
# Test that presupposition against the record: every LOCK the wrapper has ever written
# carries a `host` field, so the set of distinct hosts in the LOCK's git history is the set
# of machines that have taken the lock through this wrapper.
set -u
cd "${1:?usage: lock-host-census.sh <repo-root>}" || exit 2
echo "=== commits touching .softhouse/LOCK ==="
git log --format=%H -- .softhouse/LOCK | wc -l
echo "=== distinct \"host\" values across every historical LOCK body ==="
for c in $(git log --format=%H -- .softhouse/LOCK); do
  git show "$c:.softhouse/LOCK" 2>/dev/null \
    | tr -d ' \n' \
    | sed -n 's/.*"host":"\([^"]*\)".*/\1/p'
  echo
done | sort | uniq -c
echo "=== distinct \"holder\" values ==="
for c in $(git log --format=%H -- .softhouse/LOCK); do
  git show "$c:.softhouse/LOCK" 2>/dev/null \
    | tr -d ' \n' \
    | sed -n 's/.*"holder":"\([^"]*\)".*/\1/p'
  echo
done | sort | uniq -c
echo "=== host PAIRED WITH holder, which is what decides whether the cloud fire runs this wrapper ==="
for c in $(git log --format=%H -- .softhouse/LOCK); do
  git show "$c:.softhouse/LOCK" 2>/dev/null \
    | tr -d ' \n' \
    | sed -n 's/.*"holder":"\([^"]*\)".*"host":"\([^"]*\)".*/\1 @ \2/p'
  echo
done | sort | uniq -c
echo "=== this host ==="
hostname -s
uname -s
