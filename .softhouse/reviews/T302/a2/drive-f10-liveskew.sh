#!/bin/bash
# T302 attempt 2 -- F10: THE LIVE FIRE'S LOCK CARRIES NO `fire`, SO THE DISCRIMINATOR
# T309 SHIPPED IS INERT ON THE MACHINE IT SHIPPED TO.
#
# Read-only. Reads .softhouse/LOCK; never writes it, never removes it, sends no signal.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8
G="git -C $R"

echo "=== 1. the LOCK the live fire wrote, as committed at HEAD ==="
$G show HEAD:.softhouse/LOCK
echo
echo "    fire field present?"
$G show HEAD:.softhouse/LOCK | grep -c '"fire"'
echo "    (0 = ABSENT. caller_is_lock_holder() sets lock_fire=None, and"
echo "     dispatches_predating_this_fire() then returns None with"
echo "     'the LOCK records no \`fire\` id ... REFUSING (fail-closed)'.)"
echo
echo "=== 2. but fire-program.sh at HEAD DOES write it ==="
$G show HEAD:.softhouse/bin/fire-program.sh | grep -n '"fire":' | head -3
echo
echo "=== 3. why: version skew. the wrapper predates the code that writes the field ==="
echo "--- the running wrapper:"
/bin/ps -o pid=,lstart=,command= -p "$(python3 -c 'import json;print(json.load(open("'"$R"'/.softhouse/LOCK"))["pid"])')" 2>/dev/null
echo "--- when the field was introduced (T309 attempt 1) and merged to main:"
$G log -1 --format='    introduced: %h %ad %s' --date=iso 825c8e8f
$G log -1 --format='    merged    : %h %ad %s' --date=iso 2dfbe422
echo
echo "=== 4. and the running wrapper is executing its ORIGINAL bytes ==="
echo "    T309's own probe: git merge RENAMES into place (new inode), and zsh keeps"
echo "    reading the inode it started with -- LEG C printed 'TAIL: ORIGINAL'."
$G show HEAD:.softhouse/capture/t309-sigterm-reconcile-bypass/probe-zsh-reread.txt \
  | grep -A3 'LEG C'
echo
echo "=== CONSEQUENCE ==="
echo "  * in_session mode is 100% INERT for this fire: no \`fire\` on the LOCK -> refuse."
echo "  * wrapper mode is unaffected: it never calls dispatches_predating_this_fire,"
echo "    and --fire comes from \$STAMP on the command line, not from the LOCK."
echo "  * if THIS fire is SIGTERMed it runs the PRE-T309 on_signal (stop_driver;"
echo "    release_lock; exit) -- T288 defect 1 is still live for it."
