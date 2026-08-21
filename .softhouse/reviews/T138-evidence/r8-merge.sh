#!/bin/sh
# T138 — P-24: an assertion about what happens ON MERGE can only be tested BY MERGING.
# Merge T91 + T107 + T115 together into a THROWAWAY clone of CURRENT main and re-run
# the artefacts there — not on the branch, where the interesting bug is invisible.
set -u
SRC=${1:?source repo}
MAIN=${2:?current main sha (literal)}
D=/tmp/T138-merge
rm -rf "$D"
git clone --quiet --no-hardlinks --shared "$SRC" "$D"
cd "$D" || exit 2
git checkout -q -B scratch "$MAIN"
echo "scratch main = $(git rev-parse HEAD)"
echo
for b in origin/softhouse/T91-preconditions-copy origin/softhouse/T107-review-t91 origin/softhouse/T115-t91-microfixes; do
  echo "--- merging $b ($(git rev-parse --short "$b"))"
  git -c user.name=T138 -c user.email=t138@local merge --no-edit "$b" > /tmp/T138-merge-$$.log 2>&1
  rc=$?
  tail -3 /tmp/T138-merge-$$.log | sed 's/^/    /'
  echo "    merge rc=$rc"
  if [ $rc -ne 0 ]; then
    echo "    CONFLICTS:"; git diff --name-only --diff-filter=U | sed 's/^/      /'
    exit 1
  fi
done
echo
echo "merged head = $(git rev-parse HEAD)"
echo
echo "=== BLOB IDENTITY: main vs merged, for the surfaces this branch must not touch"
for f in .softhouse/PIN.json .softhouse/capabilities.json nexus/internal/apps/loanschedule/contract/contract.go .softhouse/conformance.sh .softhouse/gates.md .softhouse/tasks.json; do
  a=$(git rev-parse "$MAIN:$f" 2>/dev/null || echo ABSENT)
  b=$(git rev-parse "HEAD:$f" 2>/dev/null || echo ABSENT)
  s=DIFFERS; [ "$a" = "$b" ] && s=IDENTICAL
  printf '   %-62s %s  %s\n' "$f" "$(echo "$a" | cut -c1-12)" "$s"
done
echo
echo "=== files the merge changed relative to main:"
git diff --stat "$MAIN" HEAD -- . ':(exclude).softhouse/capture/t91/out' | tail -20
echo
echo "=== sibling capture trees and vectors must be untouched:"
git diff --name-only "$MAIN" HEAD -- .softhouse/vectors/ nexus/ .softhouse/capture/pathb/ .softhouse/capture/charges/out/ .softhouse/capture/t74-multiplesof/ .softhouse/capture/t83-nonamortizing/ .softhouse/conformance.sh .softhouse/gates.md | sed 's/^/   /'
echo "   (empty above = nothing touched)"
