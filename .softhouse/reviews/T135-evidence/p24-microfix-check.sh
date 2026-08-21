#!/bin/sh
# Does the one-line MICRO-FIX (a literal fork sha) restore the rig post-merge?
set -u
T=/tmp/t135/merge/clone/.softhouse/capture/pathb/t99
echo "post-merge, with T99_PREFIX_REF pinned to the literal fork sha ab2de893…:"
for f in f1 f2 f3 f4; do
  T99_PREFIX_REF=ab2de89356986c8ed85a9d2e26c2bc86b0fb8720 \
  T99_EXPORT_ROOT=/tmp/t135/merge/y-$f sh "$T/prove-$f.sh" > /tmp/t135/merge/y$f.txt 2>&1
  echo "  prove-$f.sh -> exit $?"
  tail -1 /tmp/t135/merge/y$f.txt | sed 's/^/      /'
done
echo
echo "the established convention already on main:"
ls -l /Users/buv/gerege-nbfi/.softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA 2>&1
cat /Users/buv/gerege-nbfi/.softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA 2>&1 | tail -3
