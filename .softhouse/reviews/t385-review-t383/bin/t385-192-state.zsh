#!/bin/zsh
# T385 · Re-run T279's 192-state wrapper-vs-skill partition driver against BOTH
# main's shipped file and T383's file, and prove the seven lock arms did not move.
# A change to fire-program.sh that moved an arm without a matching SKILL.md edit is
# the P-85 double-holder hazard (.softhouse/patterns.md:2822).
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
D=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a8adf9efd2a6d654f/.softhouse/capture/t279-lock-partition/drive-wrapper-vs-skill.zsh
cd /tmp/t385 || exit 1

print -r -- "=== SUBJECT: T383's file 5c4f0244... ==="
/bin/zsh "$D" /tmp/t385/fixed.sh 2>&1
print -r -- ""
print -r -- "=== CONTROL: main's shipped file dbb18b7b... (same driver, must also be 0) ==="
/bin/zsh "$D" /tmp/t385/shipped.sh 2>&1
print -r -- ""
print -r -- "=== STRUCTURAL: is lock_decide() itself byte-identical between the two? ==="
/usr/bin/python3 - <<'PY'
import re
def fn(p):
    s=open(p,encoding='utf-8').read()
    i=s.index('lock_decide()')
    j=s.index('\n}\n', i)+3
    return s[i:j]
a=fn('/tmp/t385/shipped.sh'); b=fn('/tmp/t385/fixed.sh')
print("  lock_decide() bytes  shipped=%d  fixed=%d" % (len(a), len(b)))
print("  IDENTICAL" if a==b else "  *** DIFFERENT ***")
PY
