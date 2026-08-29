#!/usr/bin/env bash
# T350 -- build the fixture repos the RED/GREEN drives run against.
#
# WHY A FIXTURE AND NOT JUST TODAY'S REPO. All four real cases have since been
# repaired by hand and their work merged, so on TODAY'S main every one of them
# carries a `<TID>:` commit subject and the current code answers "merged" for all
# four -- which HIDES the two defects. The fixture rewinds `main` to the exact
# commit the reconciler was standing on when it got each case wrong, and recreates
# the refs that existed then. Every sha below was read out of this repo's own
# history; none is synthetic.
#
#   A/T339   main = ac72956b  (softhouse: local fire lock (20260828-140005))
#            ref  = softhouse/rescued-t339-base-20260828-080001 @ 7e8825b9
#            recorded branch softhouse/T339-review-t270 -- absent, as it was then.
#   B/T431   main = 280817a1f (softhouse: iter4 wave 2 -- five dispatched ...)
#            ref  = softhouse/T431-t407-conditions @ 280817a1f  -- the branch head
#            IS the driver's own dispatch commit, because `git worktree add`
#            branches from wherever the driver is.
#   C/T421   main = today's tip; recorded branch absent (pruned post-merge);
#            33 tracked deliverable files on main under
#            .softhouse/capture/t421-t406-conditions/.
#   D/T428   main = today's tip; recorded branch DELETED in the fixture to
#            reproduce the brief's "branch gone, content present" shape.
#   E/T351   main = today's tip; recorded branch softhouse/T351-old-name absent;
#            live ref softhouse/T351-progress-accounting carries 1 commit and a
#            path naming t351. THIS ONE MUST BLOCK DEMOTION, before and after.
#   F/T442   same shape as E, second must-block control.
set -u
SRC="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIX=/tmp/t350-fixture
rm -rf "$FIX"
git clone --quiet --shared "$SRC" "$FIX" || exit 1
git -C "$FIX" config gc.auto 0
# `git clone` creates ONE local head; every other branch arrives as
# refs/remotes/origin/*, which branch_sweep.RefIndex (refs/heads + packed-refs)
# does NOT read. The first cut of this fixture made that mistake and both
# must-block controls came back "no live ref carries the id" -- a fixture that
# cannot show the guard blocking is not a fixture. Detach, then mirror every head.
git -C "$FIX" checkout --quiet --detach
git -C "$FIX" fetch --quiet "$SRC" '+refs/heads/*:refs/heads/*' || exit 1
echo "fixture:  $FIX"
echo "source:   $SRC"
echo -n "local heads in fixture: "; git -C "$FIX" for-each-ref refs/heads --format='%(refname)' | wc -l
git -C "$FIX" log -1 --format='clone HEAD: %H %s'
