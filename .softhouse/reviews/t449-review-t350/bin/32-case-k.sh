#!/bin/bash
# T449 -- CASE K.  A task whose GENUINE work legitimately lives under ANOTHER task's
# directory (this program's condition-bundle / retry convention), rescued by the
# wrapper's sweep, whose rescue commit subject is the sweep's own boilerplate.
# Under T330 this ref BLOCKED the demotion.  Does it still?
set -eu
F=/tmp/t449/fixture
cd "$F"
git checkout -q main
git checkout -q -b softhouse/rescued-t945-base-20260829 main
mkdir -p .softhouse/capture/t944-t945-conditions/out
printf 'T945 closing T944 condition C-2: the real, uncommitted work\n' \
  > .softhouse/capture/t944-t945-conditions/out/work.txt
git add -A
git commit -qm "RESCUED: WIP from a worker that never signalled done (fire 20260829-080002)"
git checkout -q main
echo "case K built:"
git --no-pager log --oneline -1 softhouse/rescued-t945-base-20260829
git --no-pager diff --name-only main...softhouse/rescued-t945-base-20260829
