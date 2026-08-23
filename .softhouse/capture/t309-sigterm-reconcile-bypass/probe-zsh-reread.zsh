#!/bin/zsh
# T309 PROBE 1 — DOES ZSH RE-READ A RUNNING SCRIPT FROM DISK?
#
# This is the premise behind the task brief's warning ("you will be editing the very
# wrapper that is running you right now") and behind T301. It is MEASURED here rather
# than asserted, because the self-insulation change in fire-program.sh is only justified
# if the hazard is real on THIS zsh.
#
# METHOD, AND A FIRST DRAFT THAT MEASURED NOTHING. The first version of this probe put
# the `sleep` AFTER the padding, so by the time the rewrite landed zsh had already
# consumed the whole file and every leg reported "TAIL: ORIGINAL" — a green bar that
# proved only that the probe was pointed at the wrong instant. The subject below puts the
# `sleep` on line 3 and the marker ~90 KB later, so at the moment of the rewrite zsh has
# read at most its first input buffer and MUST go back to the file for the rest.
#
# Three legs, because the two ways a file changes are not the same event:
#   A  in-place rewrite, same inode (`cat > file`) — what `sed -i''` on some systems,
#      an editor without atomic-save, and a plain `>` redirection do.
#   B  same, at ~90 KB (fire-program.sh is ~60 KB).
#   C  write-new-then-rename (`mv -f`) — a NEW inode. This is what `git checkout`,
#      `git merge` and `git stash pop` do, and it is the case that matters for
#      "the orchestrator merged a branch while the fire was live".
#
# Run:  zsh probe-zsh-reread.zsh
set -uo pipefail
WORK="${TMPDIR:-/tmp}/t309-zshreread.$$"
mkdir -p "$WORK" || exit 1
trap 'rm -rf "$WORK"' EXIT

print "zsh: $ZSH_VERSION"
print "work: $WORK"
print ""

# Build subject/replacement pairs whose ONLY structural difference is length, so a saved
# byte offset into the old file lands somewhere arbitrary in the new one.
build() {                 # build <name> <padcount>
  local name=$1 n=$2
  /usr/bin/python3 - "$WORK" "$name" "$n" <<'PY'
import sys
w, name, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
head = '#!/bin/zsh\nprint "A: start (pid $$)"\n/bin/sleep 2\n'
pad_o = "".join("# pad %04d ---------------------------------------------------------------\n" % i for i in range(n))
pad_n = "".join("# PAD %04d (rewritten; this line is deliberately a different length) ------------------\n" % i for i in range(n))
o = head + pad_o + 'print "TAIL: ORIGINAL"\nexit 0\n'
r = head + pad_n + 'print "TAIL: REWRITTEN"\nexit 0\n'
open("%s/%s.zsh" % (w, name), "w").write(o)
open("%s/%s.new" % (w, name), "w").write(r)
print("  %s: original %d bytes / replacement %d bytes" % (name, len(o), len(r)))
PY
}

leg() {                   # leg <label> <name> <how>
  local label=$1 name=$2 how=$3
  print "=== LEG $label — $how ==="
  print "  inode before: $(/usr/bin/stat -f %i "$WORK/$name.zsh")"
  if [[ "$how" == rename* ]]; then
    { /bin/sleep 1; cp "$WORK/$name.new" "$WORK/$name.tmp"; mv -f "$WORK/$name.tmp" "$WORK/$name.zsh" } &
  else
    { /bin/sleep 1; cat "$WORK/$name.new" > "$WORK/$name.zsh" } &
  fi
  local rew=$!
  zsh "$WORK/$name.zsh"
  print "  LEG $label subject rc=$?"
  wait $rew 2>/dev/null
  print "  inode after:  $(/usr/bin/stat -f %i "$WORK/$name.zsh")"
  print ""
}

build small 4
build big  1200
build rn   1200

leg A small "in-place rewrite, SAME inode, small file (cat > file)"
leg B big   "in-place rewrite, SAME inode, ~90 KB file (cat > file)"
leg C rn    "rename-into-place, NEW inode (what git checkout/merge does)"

print "READ THE MARKERS, NOT THE rc:"
print "  TAIL: ORIGINAL  = the running script was NOT affected by the rewrite"
print "  TAIL: REWRITTEN = the running script executed lines it was never started with"
print "  a parse error / rc!=0 = the saved offset landed mid-token — corruption, not a swap"
print "DONE"
