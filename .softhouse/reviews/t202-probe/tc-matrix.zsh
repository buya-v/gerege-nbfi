#!/bin/zsh
# T202 -- the T-c signal matrix, PRE vs POST, all five signals, in one file.
set -uo pipefail
for V in pre post; do
  print -r -- "########## SUBJECT = $V-fix (trap bytes extracted from the file) ##########"
  for S in INT TERM HUP QUIT KILL; do
    /bin/zsh /tmp/t202/tc-run.zsh /tmp/t202/tc-subject-$V.zsh $S $V 2>&1
    print -r -- ""
  done
done
