#!/bin/zsh
# T336 P4 — OPTION (b): is there ANY hook on this git that CAN veto `git worktree add`?
#
# post-checkout cannot (F-C, reproduced in out/fc-reproduce.txt). This probe measures the
# other candidates that fire during `git worktree add`, in the order git runs them:
#
#   B1. reference-transaction   — fires for the creation of refs/heads/worktree-agent-<id>.
#                                 A non-zero exit in the "prepared" state aborts the ref
#                                 transaction. Does that abort the WORKTREE?
#   B2. pre-receive on a local remote — does NOT fire; `git worktree add` pushes nothing.
#                                 Measured anyway rather than asserted.
#   B3. post-index-change / post-checkout — post-action, cannot refuse (F-C).
#
# The question each case must answer is not "did git print an error" but: IS THERE A
# USABLE WORKER WORKTREE AFTERWARDS? A worker that can commit is a worker that was spawned.
set -u
GIT=/usr/bin/git
T=$(mktemp -d /tmp/t336-veto.XXXXXX)
$GIT init -q --bare "$T/remote.git"
$GIT clone -q "$T/remote.git" "$T/repo" 2>/dev/null
R="$T/repo"
$GIT -C "$R" config user.email t336@local
$GIT -C "$R" config user.name T336
mkdir -p "$R/.softhouse"
print '{"tasks":[]}' > "$R/.softhouse/tasks.json"
$GIT -C "$R" add -A >/dev/null
$GIT -C "$R" commit -qm base
$GIT -C "$R" push -q -u origin HEAD:main
$GIT -C "$R" branch --set-upstream-to=origin/main main >/dev/null 2>&1
# make the repo VIOLATING: an unpushed .softhouse commit
print '{"tasks":[{"id":"T999"}]}' > "$R/.softhouse/tasks.json"
$GIT -C "$R" commit -qam "unpushed dispatch record"

verdict () {  # $1 rc  $2 wtpath  $3 branch
  print "  rc=$1"
  print "  branch ref exists            : $($GIT -C "$R" rev-parse --verify --quiet "refs/heads/$3" >/dev/null && print YES || print no)"
  print "  worktree dir exists          : $([ -d "$2" ] && print YES || print no)"
  print "  files checked out            : $([ -f "$2/.softhouse/tasks.json" ] && print YES || print no)"
  print "  admin dir registered         : $([ -d "$R/.git/worktrees/$(basename $2)" ] && print YES || print no)"
  # THE question: can a worker actually work in it?
  if [ -d "$2" ]; then
    ( cd "$2" && print z > z.txt && $GIT add z.txt >/dev/null 2>&1 && $GIT commit -qm "worker commit" >/dev/null 2>&1 )
    print "  A WORKER COULD COMMIT IN IT  : $($GIT -C "$2" log -1 --format=%s 2>/dev/null | grep -q 'worker commit' && print YES--NOT-REFUSED || print no--REFUSED)"
  else
    print "  A WORKER COULD COMMIT IN IT  : no--REFUSED (no directory)"
  fi
}

print "git: $($GIT --version)"
print "scratch: $T\n"

print "===== B1a. reference-transaction, refusing in the 'prepared' state ====="
cat > "$R/.git/hooks/reference-transaction" <<'RT'
#!/bin/sh
state=$1
while read -r old new ref; do
  case "$ref" in
    refs/heads/worktree-agent-*)
      echo "T336 refusing $state $ref" >&2
      if [ "$state" = "prepared" ]; then exit 1; fi
      ;;
  esac
done
exit 0
RT
chmod +x "$R/.git/hooks/reference-transaction"
cd "$R"
$GIT worktree add -b worktree-agent-b1a "$T/b1a" >/dev/null
verdict $? "$T/b1a" worktree-agent-b1a

print "\n===== B1b. reference-transaction, refusing in EVERY state ====="
cat > "$R/.git/hooks/reference-transaction" <<'RT'
#!/bin/sh
state=$1
while read -r old new ref; do
  case "$ref" in
    refs/heads/worktree-agent-*) echo "T336 refusing $state $ref" >&2; exit 1 ;;
  esac
done
exit 0
RT
chmod +x "$R/.git/hooks/reference-transaction"
cd "$R"
$GIT worktree add -b worktree-agent-b1b "$T/b1b" >/dev/null
verdict $? "$T/b1b" worktree-agent-b1b

print "\n===== B1c. control: reference-transaction present but PERMITS (must succeed) ====="
cat > "$R/.git/hooks/reference-transaction" <<'RT'
#!/bin/sh
exit 0
RT
chmod +x "$R/.git/hooks/reference-transaction"
cd "$R"
$GIT worktree add -b worktree-agent-b1c "$T/b1c" >/dev/null
verdict $? "$T/b1c" worktree-agent-b1c

print "\n===== B1d. THE REAL SHAPE: refuse only when .softhouse/ is UNPUSHED ====="
cat > "$R/.git/hooks/reference-transaction" <<'RT'
#!/bin/sh
[ "$1" = "prepared" ] || exit 0
seen=0
while read -r old new ref; do
  case "$ref" in refs/heads/worktree-agent-*) seen=1 ;; esac
done
[ "$seen" = "1" ] || exit 0
C=$(git rev-parse --git-common-dir); case "$C" in /*) ;; *) C="$(pwd)/$C";; esac
M=$(cd "$C/.." && pwd)
U=$(git -C "$M" rev-list --count origin/main..main -- .softhouse/ 2>/dev/null || echo 0)
D=$(git -C "$M" status --porcelain -- .softhouse/ 2>/dev/null | wc -l | tr -d ' ')
[ "$U" = "0" ] && [ "$D" = "0" ] && exit 0
echo "T336: REFUSED - $U unpushed / $D dirty .softhouse paths. Push before you spawn." >&2
exit 1
RT
chmod +x "$R/.git/hooks/reference-transaction"
cd "$R"
$GIT worktree add -b worktree-agent-b1d "$T/b1d" >/dev/null
verdict $? "$T/b1d" worktree-agent-b1d

print "\n===== B1e. same hook, but the repo is now CLEAN (must NOT refuse) ====="
$GIT -C "$R" push -q origin main
cd "$R"
$GIT worktree add -b worktree-agent-b1e "$T/b1e" >/dev/null
verdict $? "$T/b1e" worktree-agent-b1e

print "\n===== B1f. does the refusing hook also block ordinary branch work? (blast radius) ====="
# make it violating again
print '{"tasks":[{"id":"T998"}]}' > "$R/.softhouse/tasks.json"
$GIT -C "$R" commit -qam "unpushed again"
cd "$R"
$GIT switch -q -c some-ordinary-branch 2>&1 | sed 's/^/    /'
print "  ordinary `git switch -c` rc=$?  branch now: $($GIT -C "$R" symbolic-ref --short HEAD)"
$GIT -C "$R" switch -q main
cd "$R"
$GIT worktree add -b softhouse/T998-manual "$T/b1f" >/dev/null 2>&1
print "  a NON worktree-agent-* worktree add rc=$?  exists: $([ -d "$T/b1f" ] && print yes || print no)"

print "\n===== B2. pre-receive on a local remote — does `git worktree add` push anything? ====="
cat > "$T/remote.git/hooks/pre-receive" <<'PR'
#!/bin/sh
echo "T336: pre-receive FIRED" >&2
exit 1
PR
chmod +x "$T/remote.git/hooks/pre-receive"
rm -f "$R/.git/hooks/reference-transaction"
cd "$R"
$GIT worktree add -b worktree-agent-b2 "$T/b2" >/dev/null
print "  worktree add rc=$?   (if pre-receive had fired it would have printed above)"
print "  exists: $([ -d "$T/b2" ] && print yes || print no)"

print "\nscratch: $T"
