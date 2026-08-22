#!/bin/bash
# T131 F-T131-2 -- the SECOND silent-miss mode of the Bash-tool `grep`, which
# T108's ruling never states: --ignore-files (and --exclude-dir=.git/.svn/.hg/
# .bzr/.jj/.sl) are hard-coded into the shell function alongside -I.
#
# THIS SCRIPT CANNOT DEMONSTRATE THE DEFECT BY ITSELF, and that is the point:
# run from a script you get /usr/bin/grep and the function does not exist.  It
# builds the fixture and prints the two commands an agent must type INTO THE
# BASH TOOL to see the difference.  Real transcript: T131 review section 5.
D="$(cd "$(dirname "$0")" && pwd)/ignoretest"
rm -rf "$D"; mkdir -p "$D"
printf 'ignored.txt\n'            > "$D/.gitignore"
printf 'principal: 1250000.75\n'  > "$D/ignored.txt"
printf 'principal: 1250000.75\n'  > "$D/visible.txt"
echo "fixture built at $D"
echo
echo "control -- /usr/bin/grep (what a SCRIPT gets) sees BOTH files:"
LC_ALL=C /usr/bin/grep -arl '[0-9]\.[0-9]' "$D"
echo
echo "now TYPE THESE INTO THE CLAUDE CODE BASH TOOL (the function only exists there):"
echo "    grep -rl  '[0-9]\\.[0-9]' $D           # omits ignored.txt"
echo "    grep -arl '[0-9]\\.[0-9]' $D           # STILL omits it -- -a does not help"
echo "    LC_ALL=C grep -arl '[0-9]\\.[0-9]' $D  # STILL omits it -- neither token helps"
echo
echo "and the live consequence in this repo (.gitignore carries .claude/worktrees/):"
echo "    cd /Users/buv/gerege-nbfi && grep -rl '<any string in a sibling worktree>' ."
echo "  -> exit 1, no output.  Start at .claude instead of . and it is found."
