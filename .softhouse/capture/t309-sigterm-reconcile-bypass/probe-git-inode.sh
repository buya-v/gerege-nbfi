#!/bin/zsh
# T309 PROBE 2 — DOES `git merge` / `git checkout` / `git pull` REWRITE A FILE IN PLACE,
# OR RENAME A NEW INODE OVER IT?
#
# PROBE 1 measured that zsh 5.9 DOES go back to the script file for more input, and that
# an in-place rewrite (SAME inode) of a ~90 KB running script makes it execute lines it
# was never started with (leg B: "TAIL: REWRITTEN"), while a rename-into-place (NEW
# inode) does NOT (leg C: "TAIL: ORIGINAL"), because the running shell holds an open fd
# on the old inode.
#
# So "is it safe to merge fire-program.sh while a fire is live" reduces to ONE measurable
# fact about git per operation, and it is measured here rather than assumed.
#
# THE FIRST DRAFT OF THIS PROBE PASSED VACUOUSLY and it is worth recording why: its
# `git pull` leg cloned a repo whose HEAD was on a branch that then never received the
# new commit, so the pull had NOTHING to fetch, the file never changed, and the inode was
# trivially identical — reported as "SAME INODE — in-place", which is a real verdict
# reached by no measurement at all. Every leg below therefore ASSERTS THAT THE CONTENT
# ACTUALLY CHANGED before it is allowed to report an inode verdict, and a leg whose
# content did not change reports VACUOUS and fails the probe. (P-91's corollary: "A test
# rig is inside the trust boundary of the thing it grades; check that it cannot pass
# vacuously before quoting its counts.")
#
# PROGRAM NAMED (P-58): the `git` on PATH, printed below with its version.
set -uo pipefail
WORK="${TMPDIR:-/tmp}/t309-gitinode.$$"
mkdir -p "$WORK" || exit 1
trap 'rm -rf "$WORK"' EXIT

print "git: $(command -v git)  $(git --version)"
print "zsh: $ZSH_VERSION"
print "work: $WORK"
print ""

FAILED=0

mkver() {   # mkver <path> <tag> <linelen-pad>
  /usr/bin/python3 - "$1" "$2" "$3" <<'PY'
import sys
path, tag, pad = sys.argv[1], sys.argv[2], int(sys.argv[3])
open(path, "w").write("#!/bin/zsh\n" + "".join(
    "# %s pad %04d %s\n" % (tag, i, "-" * pad) for i in range(1200)))
PY
}

verdict() { # verdict <label> <ino_before> <ino_after> <sha_before> <sha_after>
  local label=$1 ib=$2 ia=$3 sb=$4 sa=$5
  print "  content sha before: $sb"
  print "  content sha after:  $sa"
  if [[ "$sb" == "$sa" ]]; then
    print "  VERDICT: **VACUOUS** — the file did not change, so this leg measured NOTHING."
    FAILED=1
    return
  fi
  print "  inode before: $ib"
  print "  inode after:  $ia"
  if [[ "$ib" == "$ia" ]]; then
    print "  VERDICT: SAME INODE — $label rewrote the file IN PLACE."
    print "           A zsh running these bytes WOULD read the new ones (PROBE 1 leg B)."
  else
    print "  VERDICT: NEW INODE — $label renamed a fresh file over the path."
    print "           A zsh running these bytes holds an fd on the OLD inode and is"
    print "           unaffected (PROBE 1 leg C)."
  fi
}

sha() { /usr/bin/shasum -a 256 "$1" | cut -c1-16 }

# ------------------------------------------------------------------ upstream repo ---
git init -q --initial-branch=main "$WORK/up" 2>/dev/null || { git init -q "$WORK/up"; git -C "$WORK/up" checkout -q -b main }
git -C "$WORK/up" config user.email t309@example.invalid
git -C "$WORK/up" config user.name  T309
mkdir -p "$WORK/up/.softhouse/bin"
mkver "$WORK/up/.softhouse/bin/w.sh" v1 40
git -C "$WORK/up" add -A && git -C "$WORK/up" commit -q -m v1

# a feature branch carrying a DIFFERENT-LENGTH version of the same file
git -C "$WORK/up" checkout -q -b feature
mkver "$WORK/up/.softhouse/bin/w.sh" v2 90
git -C "$WORK/up" add -A && git -C "$WORK/up" commit -q -m v2
git -C "$WORK/up" checkout -q main

# ------------------------------------------------------------------------ LEG 1 ---
print "=== LEG 1 — git merge <feature>  (what the orchestrator does when it lands a branch) ==="
IB=$(/usr/bin/stat -f %i "$WORK/up/.softhouse/bin/w.sh"); SB=$(sha "$WORK/up/.softhouse/bin/w.sh")
git -C "$WORK/up" merge -q --no-edit feature
IA=$(/usr/bin/stat -f %i "$WORK/up/.softhouse/bin/w.sh"); SA=$(sha "$WORK/up/.softhouse/bin/w.sh")
verdict "git merge" "$IB" "$IA" "$SB" "$SA"
print ""

# ------------------------------------------------------------------------ LEG 2 ---
print "=== LEG 2 — git checkout <other-commit> -- <path> ==="
IB=$(/usr/bin/stat -f %i "$WORK/up/.softhouse/bin/w.sh"); SB=$(sha "$WORK/up/.softhouse/bin/w.sh")
git -C "$WORK/up" checkout -q "$(git -C "$WORK/up" rev-list --max-parents=0 HEAD)" -- .softhouse/bin/w.sh
IA=$(/usr/bin/stat -f %i "$WORK/up/.softhouse/bin/w.sh"); SA=$(sha "$WORK/up/.softhouse/bin/w.sh")
verdict "git checkout -- <path>" "$IB" "$IA" "$SB" "$SA"
git -C "$WORK/up" checkout -q -- .softhouse/bin/w.sh
print ""

# ------------------------------------------------------------------------ LEG 3 ---
# THE ONE THAT MATTERS MOST: fire-program.sh runs `git pull --ff-only` at :107, in the
# SAME checkout it is executing from, BEFORE it takes the lock. If a pull is in-place,
# a fire can rewrite its own running bytes with no merge involved at all.
print "=== LEG 3 — git pull --ff-only  (fire-program.sh:107, in its own checkout) ==="
git clone -q "$WORK/up" "$WORK/clone"
git -C "$WORK/clone" config user.email t309@example.invalid
git -C "$WORK/clone" config user.name  T309
CLONE_BRANCH=$(git -C "$WORK/clone" rev-parse --abbrev-ref HEAD)
print "  clone is on branch: $CLONE_BRANCH"
# advance THAT SAME branch upstream, with a third, different length
git -C "$WORK/up" checkout -q "$CLONE_BRANCH"
mkver "$WORK/up/.softhouse/bin/w.sh" v3 140
git -C "$WORK/up" add -A && git -C "$WORK/up" commit -q -m v3
print "  upstream $CLONE_BRANCH advanced to $(git -C "$WORK/up" rev-parse --short HEAD)"
IB=$(/usr/bin/stat -f %i "$WORK/clone/.softhouse/bin/w.sh"); SB=$(sha "$WORK/clone/.softhouse/bin/w.sh")
git -C "$WORK/clone" pull -q --ff-only origin "$CLONE_BRANCH"
print "  clone HEAD now:     $(git -C "$WORK/clone" rev-parse --short HEAD)"
IA=$(/usr/bin/stat -f %i "$WORK/clone/.softhouse/bin/w.sh"); SA=$(sha "$WORK/clone/.softhouse/bin/w.sh")
verdict "git pull --ff-only" "$IB" "$IA" "$SB" "$SA"
print ""

if (( FAILED )); then
  print "PROBE 2: **FAILED** — at least one leg was VACUOUS. Do not quote its verdicts."
  exit 1
fi
print "PROBE 2: every leg changed the file's content, so every verdict above was measured."
print "DONE"
