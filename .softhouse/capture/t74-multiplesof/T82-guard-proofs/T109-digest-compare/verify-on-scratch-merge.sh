#!/bin/bash
# T109 / P-24 — VERIFY ON A SCRATCH MERGE INTO `main`, IN A THROWAWAY CLONE, NOT A WORKTREE.
#
# A worktree cannot reproduce this family of bug: `git worktree add --detach <tmp> main` leaves the
# ref `main` at the PRE-merge commit, so anything main-relative still resolves to pre-fix bytes and
# the rig passes FOR THE WRONG REASON (T102's finding, confirmed by T103). The bug needs `main`
# ITSELF to be the merge. So: clone, merge into the clone's own main, run there.
set -u
SRC="${1:?source repo}"
BR="softhouse/T109-fork-point-digest-compare"
C=/tmp/t109-clone
rm -rf "$C"
git clone --local --no-hardlinks -q "$SRC" "$C" || exit 1

echo "=== the clone's own main, BEFORE the merge ==="
git -C "$C" checkout -q main
git -C "$C" log --oneline -1
echo
echo "=== merge $BR into the clone's main ==="
git -C "$C" merge --no-edit "origin/$BR" 2>&1 | tail -3
echo "  clone main is now: $(git -C "$C" rev-parse HEAD)"
echo "  main == HEAD ?     $([ "$(git -C "$C" rev-parse main)" = "$(git -C "$C" rev-parse HEAD)" ] && echo YES || echo no)"
echo "  merge-base main HEAD = $(git -C "$C" merge-base main HEAD)   <- what the T98 form would have resolved to"
echo
echo "=== the pin, post-merge ==="
grep -vE '^[[:space:]]*(#|$)' "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA" | sed -e 's/^/  | /'
echo
echo "=== A. prove-guards-go-red.sh ON THE MERGE ==="
bash "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh" > /tmp/t109-clone-green.txt 2>&1
echo "  exit $?"
head -9 /tmp/t109-clone-green.txt | sed -e 's/^/  | /'
tail -2 /tmp/t109-clone-green.txt | sed -e 's/^/  | /'
echo
echo "=== B. the RED leg on the merge: pin the clone's own main (== the merge commit) ==="
{
  echo "commit $(git -C "$C" rev-parse main)"
  grep '^sha256 ' "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA"
} > "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA.new"
mv "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA.new" \
   "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA"
bash "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh" > /tmp/t109-clone-red.txt 2>/tmp/t109-clone-red.err
echo "  exit $?   stdout bytes $(wc -c < /tmp/t109-clone-red.txt | tr -d ' ')"
sed -e 's/^/  2| /' /tmp/t109-clone-red.err | head -6
git -C "$C" checkout -q -- .softhouse/capture/t74-multiplesof/T82-guard-proofs/FORK-POINT-SHA

echo
echo "=== C. drive the NEW capture pin red — mutate the CLONE's capture (never the real one) ==="
CAPF="$C/.softhouse/capture/out/capture-prod3i-raw.json"
printf '\n' >> "$CAPF"
bash "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh" > /tmp/t109-clone-cap.txt 2>/tmp/t109-clone-cap.err
echo "  exit $?   stdout bytes $(wc -c < /tmp/t109-clone-cap.txt | tr -d ' ')"
sed -e 's/^/  2| /' /tmp/t109-clone-cap.err | head -8
git -C "$C" checkout -q -- .softhouse/capture/out/capture-prod3i-raw.json

echo
echo "=== D. drive the NEW sliced-block pin red — edit the CLONE's precondition block ==="
SRCF="$C/.softhouse/capture/src/run-pass3i.sh"
python3 - "$SRCF" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
# add one harmless comment line INSIDE the sliced heredoc: the block's behaviour is unchanged,
# only its bytes move. Exactly the silent edit the digest is supposed to reveal.
i = s.index("<<'PY'")
j = s.index("\n", i) + 1
open(p, "w", encoding="utf-8").write(s[:j] + "# a harmless-looking comment nobody re-validated\n" + s[j:])
print("  inserted one comment line into the sliced heredoc")
PY
bash "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh" > /tmp/t109-clone-slice.txt 2>&1
echo "  exit $?"
grep -n "FATAL: THE SLICED\|expected:\|observed:\|NOT WHAT WAS EXPECTED\|guard proofs:" /tmp/t109-clone-slice.txt | head -8 | sed -e 's/^/  | /'
git -C "$C" checkout -q -- .softhouse/capture/src/run-pass3i.sh

echo
echo "=== E. back to the committed state on the merge: 25/25 again ==="
bash "$C/.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-guards-go-red.sh" > /tmp/t109-clone-green2.txt 2>&1
echo "  exit $?"
tail -2 /tmp/t109-clone-green2.txt | sed -e 's/^/  | /'
echo
echo "=== F. is the post-merge transcript identical to the branch transcript (root-normalised)? ==="
sed -e "s|$C|ROOT|g" /tmp/t109-clone-green.txt > /tmp/t109-n-merged.txt
sed -e "s|$SRC|ROOT|g" "$SRC/.softhouse/capture/t74-multiplesof/T82-guard-proofs/TRANSCRIPT.txt" > /tmp/t109-n-branch.txt
if diff -q /tmp/t109-n-merged.txt /tmp/t109-n-branch.txt >/dev/null; then
  echo "  BYTE-IDENTICAL after root normalisation — the score does not depend on merge state"
else
  echo "  DIFFERS:"; diff /tmp/t109-n-branch.txt /tmp/t109-n-merged.txt | head -20 | sed -e 's/^/  | /'
fi
echo
echo "=== G. clone hygiene ==="
git -C "$C" status --porcelain | sed -e 's/^/  | /'
echo "  (empty above == clone restored; the real repo was never written)"
