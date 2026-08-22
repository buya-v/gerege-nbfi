#!/bin/bash
# T131 independent re-derivation: BSD grep only (a script never sees the shell function)
D="$(dirname "$0")/corpus"
for f in before after otherline clean; do
  for loc in en_US.UTF-8 C.UTF-8 C; do
    for fl in -c -ac; do
      o=$(LC_ALL=$loc /usr/bin/grep $fl 'unbound variable' "$D/$f.txt" 2>&1); r=$?
      printf "BSD  %-10s %-12s %-4s out=%-8s exit=%s\n" "$f" "$loc" "$fl" "'$o'" "$r"
    done
  done
done
