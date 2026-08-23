#!/usr/bin/env bash
# T273 — DID THIS DIFF ROT ANY conformance.sh LINE CITATION IN THE REPO?
#
# T254b quantified what the cloud T253 diff would have cost: 10 citations / 5 ranges /
# 17 live line numbers / 17 rot = 100%, because its insertion sat at line ~570 and every
# citation was below it. That is why the Mac implementation was merged and the cloud one
# was not. T273 inserts ~227 lines into the same file, so the same question has to be
# ASKED AND MEASURED, not assumed away.
#
# METHOD: collect every `conformance.sh:<N>` and `conformance.sh:<A>-<B>` citation in
# tracked .md/.sh/.py/.json, then for each cited line number compare the TEXT at that
# line in the BASE revision against the TEXT at that line in HEAD. Text identical = the
# citation still points at what its author read. Text different = ROT.
#
# ENGINE DECLARATION (P-33/P-53/P-75): `git grep -h -o -E` for the citations and `sed -n`
# for the line lookup. No bare `grep`, no `rg`.
#
#   usage: 70-citation-rot-check.sh <base-rev>
set -u
BASE="${1:?usage: 70-citation-rot-check.sh <base-rev>}"
R="$(git rev-parse --show-toplevel)" || { echo "T273: not in a git work tree"; exit 2; }
cd "$R" || { echo "T273: cannot enter $R"; exit 2; }
git rev-parse --verify -q "$BASE^{commit}" >/dev/null || { echo "T273: no such revision: $BASE"; exit 2; }

W="$(mktemp -d "${TMPDIR:-/tmp}/t273-rot.XXXXXXXXXX")" || exit 2
trap 'rm -rf "$W"' EXIT

git show "$BASE:.softhouse/conformance.sh" >"$W/base.sh" || exit 2
git show "HEAD:.softhouse/conformance.sh"  >"$W/head.sh" || exit 2
echo "### T273 citation-rot check"
echo "  base rev     : $BASE  ($(LC_ALL=C sed -n '$=' "$W/base.sh") lines)"
echo "  head rev     : $(git rev-parse HEAD)  ($(LC_ALL=C sed -n '$=' "$W/head.sh") lines)"

# `git grep` exits 1 on NO MATCH and >1 on ERROR. Zero citations would make every number
# below vacuous, so it refuses rather than reporting a clean sweep over nothing (P-35).
git grep -h -o -E 'conformance\.sh:[0-9]+(-[0-9]+)?' -- '*.md' '*.sh' '*.py' '*.json' >"$W/cites.raw"
rc=$?
if [ "$rc" -gt 1 ]; then echo "  git grep errored (exit $rc). REFUSED."; exit 2; fi
if [ "$rc" -eq 1 ]; then echo "  ZERO citations found. That is a broken search, not a clean tree. REFUSED."; exit 2; fi

LC_ALL=C sed -e 's/^conformance\.sh://' -e 's/-/ /' "$W/cites.raw" >"$W/nums.raw"
: >"$W/nums"
while read -r a b; do
  printf '%s\n' "$a" >>"$W/nums"
  [ -n "${b:-}" ] && printf '%s\n' "$b" >>"$W/nums"
done <"$W/nums.raw"
LC_ALL=C sort -n -u "$W/nums" >"$W/nums.uniq"
total=$(LC_ALL=C sed -n '$=' "$W/nums.uniq")
echo "  distinct cited line numbers : ${total:-0}"
echo

rot=0; ok=0; oob=0
while read -r n; do
  [ -n "$n" ] || continue
  bl="$(LC_ALL=C sed -n "${n}p" "$W/base.sh")"
  hl="$(LC_ALL=C sed -n "${n}p" "$W/head.sh")"
  if [ -z "$bl" ] && [ -z "$hl" ]; then oob=$((oob+1)); continue; fi
  if [ "$bl" = "$hl" ]; then ok=$((ok+1)); continue; fi
  rot=$((rot+1))
  echo "  ROT at line $n"
  echo "    base: $bl"
  echo "    head: $hl"
done <"$W/nums.uniq"

echo
echo "### RESULT  unmoved=$ok  ROTTED=$rot  blank-or-out-of-range=$oob  (of ${total:-0} cited lines)"
if [ "$rot" -eq 0 ]; then
  echo "### NO CITATION ROT. Every cited line in conformance.sh still holds the text its author read."
  exit 0
fi
echo "### CITATION ROT PRESENT — $rot cited line(s) now say something else."
exit 1
