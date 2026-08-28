#!/bin/zsh
# T301 PROBE A — WHICH WRITERS CAN REACH A RUNNING SHELL'S SCRIPT?
#
# T309 measured the two halves of the hazard:
#   * zsh 5.9 re-reads a script from the fd mid-execution, so an IN-PLACE rewrite
#     (SAME inode) of a ~90 KB script made the running shell execute the rewritten
#     tail  [.../t309-sigterm-reconcile-bypass/probe-zsh-reread.txt leg B];
#   * a rename-into-place (NEW inode) does NOT reach it, because the shell holds an
#     fd on the old inode  [same file, leg C];
#   * git merge / checkout -- <path> / pull --ff-only all rename  [probe-git-inode.txt].
#
# T309 stopped there. That leaves the question T301 must answer: WHICH OTHER WRITERS
# exist, and do THEY rename or truncate? The wrapper's own comment block (written by
# T309) names four writers as dangerous -- `sed -i ''`, `cat >`, python `open(path,"w")`,
# "an editor that saves without an atomic rename" -- but only two of those were ever
# measured. This probe measures every writer an agent or a human plausibly reaches for.
#
# THE ASSERTION THAT MAKES EACH LEG NON-VACUOUS (T309's first draft passed vacuously,
# so this is deliberate): every leg checks that the CONTENT actually changed. A writer
# that silently did nothing would otherwise be scored "safe: preserved nothing to see".
#
# READ THE VERDICT COLUMN:
#   RENAME  = new inode  -> a running shell is ISOLATED from this writer
#   INPLACE = same inode -> a running shell CAN execute bytes it never started with
#   NOOP    = content unchanged -> leg is vacuous, verdict is meaningless

set -u
emulate -L zsh
setopt no_unset

WORK="$(mktemp -d "${TMPDIR:-/tmp}/t301-writers.XXXXX")"
print -r -- "zsh: $ZSH_VERSION"
print -r -- "uname: $(uname -sr)"
print -r -- "sed: $(command -v sed)   patch: $(command -v patch)   git: $(command -v git) $(git --version)"
print -r -- "work: $WORK"
print -r -- ""
printf '%-34s %-12s %-12s %-8s %s\n' WRITER INODE_BEFORE INODE_AFTER CHANGED VERDICT
printf '%-34s %-12s %-12s %-8s %s\n' ---------------------------------- ------------ ------------ -------- -------

# Each leg gets a fresh subject file of realistic size (the live wrapper is ~124 KB,
# T309's big leg was ~90 KB; size does not change the inode question but keeping it
# realistic keeps the comparison honest).
seed() {
  local f="$1"
  {
    print -r -- "#!/bin/zsh"
    print -r -- "# T301 subject file"
    local i
    for i in {1..1500}; do print -r -- "# filler line $i ------------------------------------------------------------"; done
    print -r -- "print -r -- 'TAIL: ORIGINAL'"
  } > "$f"
}

leg() {
  local name="$1"; shift
  local f="$WORK/subject-$$-${name//[^a-zA-Z0-9]/_}"
  seed "$f"
  local before_i before_s
  before_i=$(/usr/bin/stat -f %i "$f")
  before_s=$(/usr/bin/shasum -a 256 "$f" | cut -c1-16)
  # the writer is passed as a function name; it receives the path
  "$@" "$f" >/dev/null 2>&1
  local rc=$?
  local after_i after_s
  after_i=$(/usr/bin/stat -f %i "$f" 2>/dev/null || print '?')
  after_s=$(/usr/bin/shasum -a 256 "$f" 2>/dev/null | cut -c1-16 || print '?')
  local changed verdict
  if [[ "$before_s" == "$after_s" ]]; then
    changed=no;  verdict="NOOP (vacuous — writer rc=$rc)"
  else
    changed=yes
    if [[ "$before_i" == "$after_i" ]]; then verdict="INPLACE  <-- CAN REACH A RUNNING SHELL"
    else                                     verdict="RENAME   (isolated)"; fi
  fi
  printf '%-34s %-12s %-12s %-8s %s\n' "$name" "$before_i" "$after_i" "$changed" "$verdict"
}

w_cat()      { cat > "$1" <<< "print -r -- 'TAIL: REWRITTEN'"; }
w_pyopen()   { /usr/bin/python3 -c "import sys;open(sys.argv[1],'w').write(\"print -r -- 'TAIL: REWRITTEN'\n\")" "$1"; }
w_sed_i()    { /usr/bin/sed -i '' "s/TAIL: ORIGINAL/TAIL: REWRITTEN/" "$1"; }
w_append()   { print -r -- "print -r -- 'TAIL: APPENDED'" >> "$1"; }
w_tee()      { print -r -- "print -r -- 'TAIL: REWRITTEN'" | /usr/bin/tee "$1"; }
w_ddnotrunc(){ print -r -- "XXXXXXXX" | /bin/dd of="$1" bs=1 seek=10 conv=notrunc; }
w_cp()       { local t="$1.src"; print -r -- "print -r -- 'TAIL: REWRITTEN'" > "$t"; /bin/cp "$t" "$1"; }
w_mv()       { local t="$1.src"; print -r -- "print -r -- 'TAIL: REWRITTEN'" > "$t"; /bin/mv "$t" "$1"; }
w_install()  { local t="$1.src"; print -r -- "print -r -- 'TAIL: REWRITTEN'" > "$t"; /usr/bin/install -m 755 "$t" "$1"; }
w_patch()    {
  local f="$1" t="$1.new"
  /usr/bin/sed "s/TAIL: ORIGINAL/TAIL: REWRITTEN/" "$f" > "$t"
  ( cd "${f:h}"; /usr/bin/diff -u "${f:t}" "${t:t}" > "${f:t}.patch" )
  /usr/bin/patch "$f" "$f.patch"
}
# /bin/echo on macOS does NOT honour -e, so the first draft of this leg fed `ex` the
# literal string "-e ,s/..." and scored NOOP rc=1. printf, which is portable.
w_ex()       { printf ',s/TAIL: ORIGINAL/TAIL: REWRITTEN/\nwq\n' | /usr/bin/ex -s "$1"; }
w_truncgrow(){ /usr/bin/python3 -c "
import sys
p=sys.argv[1]
b=open(p,'rb').read()
# insert 19 KB ABOVE the tail, exactly the T288 shape: same inode, everything shifts
i=b.index(b'# filler line 700')
open(p,'wb').write(b[:i] + (b'# INSERTED ' + b'x'*60 + b'\n')*270 + b[i:])
" "$1"; }

leg "cat > file"                w_cat
leg "python open(path,'w')"     w_pyopen
leg "sed -i '' (BSD/macOS)"     w_sed_i
leg ">> append"                 w_append
leg "tee file"                  w_tee
leg "dd conv=notrunc"           w_ddnotrunc
leg "cp src dst"                w_cp
leg "mv src dst"                w_mv
leg "install -m 755"            w_install
leg "patch file file.patch"     w_patch
leg "ex -s (vi line editor)"    w_ex
leg "python insert-above-tail"  w_truncgrow

# ---- git legs, in a real repo, because git's write path depends on the operation ----
print -r -- ""
print -r -- "GIT OPERATIONS BEYOND THE THREE T309 MEASURED (merge / checkout -- <path> / pull --ff-only):"
printf '%-34s %-12s %-12s %-8s %s\n' WRITER INODE_BEFORE INODE_AFTER CHANGED VERDICT
printf '%-34s %-12s %-12s %-8s %s\n' ---------------------------------- ------------ ------------ -------- -------

GR="$WORK/repo"
mkdir -p "$GR"; ( cd "$GR"; git init -q .; git config user.email t301@local; git config user.name T301 )
seed "$GR/subject.sh"
( cd "$GR"; git add -A; git commit -qm base )

# FIRST DRAFT WAS VACUOUS AND THE HARNESS CAUGHT IT: the restore-shaped legs
# (reset --hard, checkout-index, restore) dirtied the file INSIDE the measured window
# and then put it back, so before-sha == after-sha and all three scored NOOP. The
# dirtying is a separate writer (and is already scored in the table above); what this
# section must measure is what git's RESTORE path does to a file that is already dirty.
# So a leg is now `git_leg <name> <pre-fn> <op-fn>`: pre runs BEFORE the snapshot.
git_leg() {
  local name="$1" pre="$2"; shift 2
  local f="$GR/subject.sh"
  ( cd "$GR"; "$pre" ) >/dev/null 2>&1
  local before_i before_s
  before_i=$(/usr/bin/stat -f %i "$f"); before_s=$(/usr/bin/shasum -a 256 "$f" | cut -c1-16)
  ( cd "$GR"; "$@" ) >/dev/null 2>&1
  local rc=$?
  local after_i after_s
  after_i=$(/usr/bin/stat -f %i "$f" 2>/dev/null || print '?')
  after_s=$(/usr/bin/shasum -a 256 "$f" 2>/dev/null | cut -c1-16 || print '?')
  local changed verdict
  if [[ "$before_s" == "$after_s" ]]; then changed=no; verdict="NOOP (vacuous — rc=$rc)"
  else
    changed=yes
    if [[ "$before_i" == "$after_i" ]]; then verdict="INPLACE  <-- CAN REACH A RUNNING SHELL"
    else verdict="RENAME   (isolated)"; fi
  fi
  printf '%-34s %-12s %-12s %-8s %s\n' "$name" "$before_i" "$after_i" "$changed" "$verdict"
}

nop()    { : ; }
dirty()  { cat > subject.sh <<< "print -r -- 'TAIL: DIRTY'"; }   # itself INPLACE — see table above
stashit(){ /usr/bin/sed -i '' "s/TAIL: ORIGINAL/TAIL: STASHED/" subject.sh; git stash -q; }

g_reset_hard()     { git reset -q --hard HEAD; }
g_stash_pop()      { git stash pop -q; }
g_apply()          {
  /usr/bin/sed "s/TAIL: ORIGINAL/TAIL: APPLIED/" subject.sh > "$WORK/apply-new"
  /usr/bin/diff -u subject.sh "$WORK/apply-new" \
    | /usr/bin/sed "1s|.*|--- a/subject.sh|;2s|.*|+++ b/subject.sh|" > "$WORK/apply.patch"
  git apply "$WORK/apply.patch"
}
g_checkout_index() { git checkout-index -f -a; }
g_restore()        { git restore subject.sh; }

git_leg "git reset --hard (dirty tree)"  dirty   g_reset_hard
( cd "$GR"; git reset -q --hard HEAD )
git_leg "git stash pop"                  stashit g_stash_pop
( cd "$GR"; git reset -q --hard HEAD )
git_leg "git apply <patch>"              nop     g_apply
( cd "$GR"; git reset -q --hard HEAD )
git_leg "git checkout-index -f -a"       dirty   g_checkout_index
( cd "$GR"; git reset -q --hard HEAD )
git_leg "git restore <path>"             dirty   g_restore

print -r -- ""
print -r -- "NOTE — the Claude Code Write and Edit TOOLS cannot be driven from a script."
print -r -- "They were measured by hand in the T301 transcript; see writer-inode.txt footer."
print -r -- "DONE"
