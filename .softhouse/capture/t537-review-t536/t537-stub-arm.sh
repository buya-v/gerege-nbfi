#!/bin/sh
# T537 item 5 -- THE STUB ARM, driven adversarially.
#
# T536's repair for T528 F-5 is: `branch_published_gate()` believes an exit code of 0
# only when the checker's stdout also contains the literal string
# `check-branch-published: CLEAN`. This script replaces the checker with a SEVEN-LINE
# stub that prints that exact banner and exits 0, checks nothing at all, and asks the
# gate what it thinks. The record it is asked to vouch for claims a branch and a commit
# that origin has never heard of.
set -e
S="$1"                       # scratchpad root
T="$S/t536wt"                # worktree at the T536 commit
W="$S/stubtest"
rm -rf "$W"
mkdir -p "$W/.softhouse/bin" "$W/.softhouse/runs"
cp "$T/.softhouse/bin/ready-tasks.py" "$W/.softhouse/bin/"

cat > "$W/.softhouse/bin/check-branch-published.py" <<'PYEOF'
#!/usr/bin/env python3
# T537 ADVERSARIAL STUB: prints the exact verdict line the gate looks for, checks nothing.
import sys
print("=" * 78)
print("check-branch-published: CLEAN")
print("=" * 78)
sys.exit(0)
PYEOF

cat > "$W/.softhouse/tasks.json" <<'JEOF'
{"run_id":"t537-stub","tasks":[
 {"id":"T999","status":"done","branch":"softhouse/T999-never-pushed-anywhere",
  "note":"landed deadbeef on softhouse/T999-never-pushed-anywhere"}]}
JEOF

cat > "$W/drive.py" <<PYEOF
import importlib.util
spec = importlib.util.spec_from_file_location("rt", "$W/.softhouse/bin/ready-tasks.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.set_repo("$W")
ok = m.branch_published_gate()
print()
print("branch_published_gate() RETURNED:", ok)
PYEOF

echo "---- stub is $(wc -l < "$W/.softhouse/bin/check-branch-published.py") lines ----"
python3 "$W/drive.py"
