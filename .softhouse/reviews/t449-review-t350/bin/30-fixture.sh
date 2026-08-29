#!/bin/bash
# T449 -- a SYNTHETIC repo, built from scratch outside the real one, in which every
# state of interest is CONSTRUCTED rather than found.  Independent of T350's fixture
# (which was a --shared clone of the real repo).
set -eu
F=/tmp/t449/fixture
rm -rf "$F"; mkdir -p "$F"; cd "$F"
git init -q -b main .
git config user.email r@t449; git config user.name T449

mk() { mkdir -p "$(dirname "$1")"; printf '%s\n' "${2:-x}" > "$1"; git add "$1"; }

mk .softhouse/README.md seed
git commit -qm "softhouse: seed"

# --- C/T421-shape: work LANDED on main under an OWNING dir, branch later deleted ----
mk .softhouse/capture/t421-t406-conditions/out/a.txt a
mk .softhouse/capture/t421-t406-conditions/out/b.txt b
git commit -qm "T421: stop the handoff counting its own commits"

# --- D/T428-shape: review landed under .softhouse/reviews/t428-review-t421/ ---------
mk .softhouse/reviews/t428-review-t421/REVIEW.md r
git commit -qm "T428: independent review of T421 -- APPROVED WITH CONDITIONS"

# --- the MENTIONING trap: T286's retry directory that NAMES T268 --------------------
for i in 1 2 3; do mk ".softhouse/capture/t286-t268-retry/out/$i.txt" "$i"; done
git commit -qm "T286: retry of T268's capture"

# --- a task whose work landed with NO owning path and NO `<id>:` subject ------------
mk nexus/ledger/posting.go "package ledger"
git commit -qm "softhouse: T870+T871 merged; conditions filed as T872"

# --- THE DISPATCH COMMIT (what `git worktree add -b` branches from) -----------------
mk .softhouse/state/dispatch.txt "iter5"
git commit -qm "softhouse fire 20260829-080002 iter5: dispatch record for 5 workers"
DISPATCH=$(git rev-parse HEAD)

# B/T431-shape: branch parked AT the dispatch commit, worker killed before commit 1
git branch softhouse/T431-t407-conditions "$DISPATCH"

# G/ATTACK: same, but the wrapper's sweep RESCUED real WIP to a second ref and the
# ORIGINAL BRANCH IS STILL ALIVE (fire-program.sh:3127 `git checkout -q -b` does not
# delete the prior branch).
git branch softhouse/T900-work "$DISPATCH"
git checkout -q -b softhouse/rescued-t900-base-20260829 "$DISPATCH"
mk .softhouse/capture/t900-work/out/wip.txt "real work, uncommitted when the worker died"
git commit -qm "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"

# G2/CONTROL: identical content evidence, but the ORIGINAL BRANCH WAS DELETED.
git branch softhouse/T901-work "$DISPATCH"
git checkout -q -b softhouse/rescued-t901-base-20260829 "$DISPATCH"
mk .softhouse/capture/t901-work/out/wip.txt "real work"
git commit -qm "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git branch -D softhouse/T901-work >/dev/null

# E/T351-shape CONTROL: a live ref carrying REAL content, recorded branch deleted
git checkout -q -b softhouse/T351-progress-accounting "$DISPATCH"
mk .softhouse/capture/t351-progress-accounting/out/x.txt x
git commit -qm "T351: progress accounting"

# F/T442-shape CONTROL: same shape, second instance
git checkout -q -b softhouse/T442-nonneg-guard "$DISPATCH"
mk .softhouse/capture/t442-nonneg-guard/out/x.txt x
git commit -qm "T442: non-negotiable guard audit"

# A/T339-shape: a NAME-ONLY rescue ref -- content belongs to a DIFFERENT task
git checkout -q -b softhouse/rescued-t339-base-20260828-080001 "$DISPATCH"
mk .t347-postcheckout-marker m
git commit -qm "RESCUED: WIP from a worker that never signalled done (fire 20260828-080001)"

# H/CAP ATTACK: 9 name-matching refs for T950; only the LAST in sort order carries
# real content.  MAX_REFS_PROBED = 8.
git checkout -q -b softhouse/zz-t950-real "$DISPATCH"
mk .softhouse/capture/t950-real/out/x.txt x
git commit -qm "T950: the real work"
for i in 1 2 3 4 5 6 7 8; do
  git branch "softhouse/aa$i-t950-decoy" "$DISPATCH"
done

git checkout -q main
mkdir -p .softhouse/bin
echo "fixture built at $F"
git --no-pager log --oneline main | sed -n '1,12p'
echo "--- refs ---"
git for-each-ref --format='%(refname:short)' refs/heads
