import io
p = ".softhouse/bin/fire-program.sh"
s = io.open(p, encoding="utf-8").read()

old = '''cat > "$LOCK" <<EOF
{
  "holder": "local-launchd",
  "host": "$(hostname -s)",
  "pid": $$,
'''
assert s.count(old) == 1
new = '''#
# T309 -- `fire` IS RECORDED HERE, AND IT IS LOAD-BEARING, NOT DECORATION. It is the
# only unfakeable answer to "which fire dispatched this task?" available to a process
# running INSIDE a live fire. `ready-tasks.py --reconcile`, in `in_session` mode, demotes
# an `in_progress` task only when the task's own `fire` differs from THIS value -- the
# argument being the lock's exclusivity: at most one fire holds this file, so a task
# stamped with a different fire id belongs to a fire that is over. The id was previously
# recoverable only by parsing `"log"` for the stamp, which is a derivation, not a field.
cat > "$LOCK" <<EOF
{
  "holder": "local-launchd",
  "host": "$(hostname -s)",
  "pid": $$,
  "fire": "$STAMP",
'''
s = s.replace(old, new)

old2 = '''SCRIPT_DIR="${0:A:h}"
source "$SCRIPT_DIR/lib-worktree-prune.zsh" || { log "FATAL: could not source lib-worktree-prune.zsh"; exit 1; }
'''
assert s.count(old2) == 1
new2 = '''SCRIPT_DIR="${0:A:h}"

# T309 -- WHICH BYTES IS THIS FIRE ACTUALLY RUNNING?
# T301 exists because a branch that changed THIS FILE was landed while a fire was live,
# and afterwards nobody could say from the evidence whether the live fire had been
# running the pre-landing or the post-landing bytes. That question is answerable by a
# measurement taken at start, so take it. Two facts, because they answer different halves:
#   * the sha256 identifies the VERSION;
#   * the inode identifies the FILE OBJECT the running shell has open, which is what
#     decides whether a later rewrite can reach it at all.
#
# WHAT THE HAZARD ACTUALLY IS, MEASURED (T309 probes, .softhouse/capture/
# t309-sigterm-reconcile-bypass/probe-zsh-reread.txt and probe-git-inode.txt):
#   * zsh 5.9 does NOT slurp a script: it goes back to the file for more input. A ~90 KB
#     script rewritten IN PLACE (same inode) mid-run executed the REWRITTEN tail
#     [probe 1 leg B]. So "editing the running wrapper" is a real hazard, not folklore.
#   * but a rename-into-place (NEW inode) does NOT reach the running shell, which holds
#     an fd on the old inode [probe 1 leg C] -- and every git operation that lands a
#     change (merge, checkout -- <path>, pull --ff-only) was measured to write a NEW
#     inode and rename it over the path [probe 2, git 2.50.1 (Apple Git-155); every leg
#     asserts the content actually changed, because the first draft passed vacuously].
# CONSEQUENCE: landing a branch that edits this file while a fire is live is SAFE; the
# live fire finishes on the bytes it started with. What is NOT safe is an IN-PLACE
# rewrite of the live path -- `sed -i ''`, `cat > fire-program.sh`, a python
# `open(path,"w")`, or an editor that saves without an atomic rename. Do not do that to a
# checkout that has a fire running in it; edit in a worktree and land it through git.
if [[ -r "${0:A}" ]]; then
  log "wrapper identity: path=${0:A} inode=$(/usr/bin/stat -f %i "${0:A}" 2>/dev/null || print '?') sha256=$(/usr/bin/shasum -a 256 "${0:A}" 2>/dev/null | cut -c1-16 || print '?') bytes=$(/usr/bin/stat -f %z "${0:A}" 2>/dev/null || print '?')"
else
  log "WARN: could not read this script's own bytes at ${0:A} -- the version of the wrapper this fire ran is UNRECORDED"
fi

source "$SCRIPT_DIR/lib-worktree-prune.zsh" || { log "FATAL: could not source lib-worktree-prune.zsh"; exit 1; }
'''
s = s.replace(old2, new2)
io.open(p, "w", encoding="utf-8").write(s)
print("patch1 ok")
