#!/bin/zsh
# T211 -- the full RED/GREEN matrix in one transcript.
#
#   part 1  PRE-FIX vs POST-FIX under SIGTERM, the head-to-head
#   part 2  POST-FIX under every signal T202 gave a disposition (INT TERM HUP
#           QUIT KILL) -- T202's matrix must stay green
#   part 3  POST-FIX happy path: NO signal at all, driver exits 0 and 7,
#           because a fix that stops a fire promptly but breaks a normal run
#           is not a fix.  This is the control P-62 asks for: a refusal probe
#           and a success probe must be distinguishable by what SURVIVES, and
#           the surviving artefact here is the `driver exited rc=N` line.
set -uo pipefail
HERE="${0:A:h}"
PRE=/tmp/t211-scratch/fire-program-PREFIX.sh
POST=/Users/buv/gerege-nbfi/.claude/worktrees/agent-aee5211d1552d8546/.softhouse/bin/fire-program.sh

print -r -- "zsh: $(/bin/zsh --version)"
print -r -- "macOS: $(sw_vers -productVersion) $(sw_vers -buildVersion)"
print -r -- "PRE  bytes: $PRE  sha256=$(shasum -a 256 $PRE | cut -d' ' -f1)"
print -r -- "POST bytes: $POST  sha256=$(shasum -a 256 $POST | cut -d' ' -f1)"
print -r -- ""
print -r -- "######################################################################"
print -r -- "# PART 1 -- SIGTERM head-to-head"
print -r -- "######################################################################"
/bin/zsh "$HERE/run-case.zsh" "$PRE"  TERM m-pre-TERM
/bin/zsh "$HERE/run-case.zsh" "$POST" TERM m-post-TERM

print -r -- "######################################################################"
print -r -- "# PART 2 -- POST-FIX under every signal T202 dispositioned"
print -r -- "######################################################################"
for S in INT HUP QUIT KILL; do
  /bin/zsh "$HERE/run-case.zsh" "$POST" $S m-post-$S
done

print -r -- "######################################################################"
print -r -- "# PART 3 -- POST-FIX happy path, NO signal (rc must survive the rewrite)"
print -r -- "######################################################################"
for WANT in 0 7; do
  export T211_FAKE_RC=$WANT
  print -r -- "---- control: driver exits $WANT, nothing is signalled ----"
  /bin/zsh "$HERE/run-case.zsh" "$POST" none m-post-ok$WANT
  unset T211_FAKE_RC
done
print -r -- "MATRIX DONE"
