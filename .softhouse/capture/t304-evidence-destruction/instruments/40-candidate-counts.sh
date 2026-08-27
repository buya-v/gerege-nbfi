#!/usr/bin/env bash
# T304 instrument 40 — print, for each candidate destructive target, the exact number of
# TRACKED files under it, from `git ls-files` and nothing else.  No inference: if the
# number is 0 the target is scratch, if it is >0 the run destroys committed evidence.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

n() { git ls-files -- "$1" | wc -l | tr -d ' '; }

printf '%-8s %s\n' 'TRACKED' 'TARGET'
for t in \
  .softhouse/capture/t250-tenant-attestation/evidence/redA \
  .softhouse/capture/t250-tenant-attestation/evidence/redB \
  .softhouse/capture/t250-tenant-attestation/evidence/redC \
  .softhouse/capture/t274-attestation-failopen/evidence/red \
  .softhouse/capture/t274-attestation-failopen/evidence/green \
  .softhouse/capture/t274-attestation-failopen/evidence/wrap \
  .softhouse/capture/t274-attestation-failopen/evidence/t250arms \
  .softhouse/reviews/t261-tenant-attestation/evidence/redB \
  .softhouse/reviews/t261-tenant-attestation/evidence/redC \
  .softhouse/reviews/t285-review-t273/evidence \
  .softhouse/vectors/ledger \
  .softhouse/capture/t91/out \
  .softhouse/capture/tierA-a2/out \
  .softhouse/capture/t287-closure-refusals/out \
  .softhouse/capture/t294-openingbalance-refusal/out \
  .softhouse/capture/charges/req \
  .softhouse/capture/pathb/t36/out/emiloop \
  .softhouse/capture/t131-grep/ignoretest \
  ; do
  printf '%-8s %s\n' "$(n "$t")" "$t"
done
