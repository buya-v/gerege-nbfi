#!/usr/bin/env bash
# T350 -- P-45. "A guard wired to nothing enforces nothing." Establish BY GREP which
# AUTOMATIC path invokes the changed code, rather than asserting that one does.
#
# Two entry points are changed and both are established here:
#   (1) `reconcile()`  -- reached only through `--reconcile`
#   (2) `main()`       -- the READY/BLOCKED listing the driver dispatches from
set -u
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO" || exit 1

echo "repo: $REPO"
echo
echo "=============================================================================="
echo "1. THE SCHEDULED, UNATTENDED PATH -- launchd -> fire-program.sh"
echo "=============================================================================="
grep -n 'ProgramArguments' -A6 .softhouse/launchd/mn.gerege.nbfi.softhouse-program.plist
echo
grep -n 'StartCalendarInterval' -A6 .softhouse/launchd/mn.gerege.nbfi.softhouse-program.plist

echo
echo "=============================================================================="
echo "2. fire-program.sh INVOKES THE CHANGED FILE -- the --reconcile path"
echo "=============================================================================="
grep -n 'SCRIPT_DIR/ready-tasks.py' .softhouse/bin/fire-program.sh
echo "--- the function that contains it, and who calls that function ---"
grep -n 'reconcile_tasks_json' .softhouse/bin/fire-program.sh

echo
echo "=============================================================================="
echo "3. THE DRIVER'S OWN STEP 1 INVOKES main() -- the READY listing"
echo "=============================================================================="
grep -rn 'ready-tasks.py' .claude/skills/softhouse-program/SKILL.md

echo
echo "=============================================================================="
echo "4. THE CHANGED SYMBOLS ARE ON BOTH PATHS -- call sites inside the module"
echo "=============================================================================="
echo "--- landed_evidence() call sites ---"
grep -n 'landed_evidence(' .softhouse/bin/ready-tasks.py
echo "--- refs_carrying_content() call sites ---"
grep -n 'refs_carrying_content(' .softhouse/bin/ready-tasks.py
echo "--- the new kinds, and the ONE function that turns a kind into an action ---"
grep -n 'name-only-refs\|"stillborn"\|merged-unverified' .softhouse/bin/ready-tasks.py
echo "--- reconcile() consults reconcile_action(), it does not re-derive ---"
grep -n 'action = reconcile_action(kind)\|action.startswith("REFUSE")' .softhouse/bin/ready-tasks.py
echo "--- main()'s READY/BLOCKED listing consults it too ---"
grep -n '_landed_flag(tid' .softhouse/bin/ready-tasks.py
echo
echo 'NOT-FOUND STATEMENTS: the searches above are `grep -n` over'
echo "  .softhouse/launchd/*.plist, .softhouse/bin/fire-program.sh,"
echo "  .claude/skills/softhouse-program/SKILL.md and .softhouse/bin/ready-tasks.py"
echo "in $REPO at the committed tree. No other invoker was looked for outside those."
