#!/bin/sh
# T135 — F-6 item 2: prove-f4 leg 4a now asserts its preconditions POSITIVELY and aborts.
set -u
T=/tmp/t135/clone/.softhouse/capture/pathb/t99
echo "=== against the pre-stamp commit 352f623 (t80/out/recapture-gerege has no stamp to delete)"
T99_PREFIX_REF=352f623 T99_EXPORT_ROOT=/tmp/t135/f6/f4a sh "$T/prove-f4.sh" > /tmp/t135/f6/f4a.txt 2>&1
echo "  EXIT=$?"
tail -6 /tmp/t135/f6/f4a.txt | sed 's/^/    /'
echo
echo "=== control: the same proof at its real fork point"
T99_EXPORT_ROOT=/tmp/t135/f6/f4b sh "$T/prove-f4.sh" > /tmp/t135/f6/f4b.txt 2>&1
echo "  EXIT=$?"
tail -4 /tmp/t135/f6/f4b.txt | sed 's/^/    /'
echo
echo "=== and what 352f623 actually is:"
git -C /tmp/t135/clone log --oneline -1 352f623
git -C /tmp/t135/clone show 352f623:.softhouse/capture/pathb/t80/out/recapture-gerege/CAPTURED-FROM-TENANT 2>&1 | head -2 | sed 's/^/    /'
