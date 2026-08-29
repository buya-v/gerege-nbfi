#!/bin/bash
# T459 -- is the MULTI-CHARACTER fold class live in this repository, and is it live for the
# paths this harness reads from the WORKING TREE?
set -u
R="$1"
echo "tracked paths containing each digraph a fold can collapse (this repository):"
for d in ss st ff fi fl ffi ffl; do
  printf '  %-4s : %s\n' "$d" "$( cd "$R" && git ls-files | LC_ALL=C grep -c -- "$d" )"
done
echo
echo "the paths this harness reads or EXECUTES from the working tree -- do any contain one?"
SH=".soft""house"
for p in "$SH/conformance"".sh" "$SH/gua""rds" \
         "$SH/gua""rds/check-ledger-invariants"".sh" \
         "$SH/gua""rds/check-capture-namespace"".sh" \
         "$SH/gua""rds/check-dead-path-frontier"".sh" \
         "$SH/gua""rds/ledgerguard/main"".go" \
         "$SH/bin/ready-tas""ks.py" \
         "$SH/bin/fire-program"".sh" \
         "$SH/bin/go-env"".sh" ; do
  hit=""
  for d in ss st ff fi fl ffi ffl; do
    case "$p" in *"$d"*) hit="$hit $d" ;; esac
  done
  printf '  %-52s digraphs:%s\n' "$p" "${hit:- NONE}"
done
echo
echo "CONCLUSION: the restricted answer of ONE collider for the two working-tree-read paths is"
echo "CORRECT, but for a reason the census did not test -- those paths happen to contain no"
echo "digraph. Across the tracked tree the class is live."
