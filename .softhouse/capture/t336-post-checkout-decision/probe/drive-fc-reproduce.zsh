#!/bin/zsh
# T336 P1 — REPRODUCE T280's F-C FIRST-HAND. Do not inherit it.
#
# Question 1: on this host's git, does a non-zero `post-checkout` exit abort `git worktree add`?
# Question 2: if it does not, is the "refused" worktree actually usable as a worker worktree?
#
# Everything happens in a scratch repo under /tmp. Nothing here touches the program repo.
set -u
GIT=/usr/bin/git
HOOK=${1:?path to the post-checkout hook under test}
T=$(mktemp -d /tmp/t336-fc.XXXXXX)
print "git: $($GIT --version)"
print "hook under test: $HOOK"
print "scratch: $T\n"

$GIT init -q --bare "$T/remote.git"
$GIT clone -q "$T/remote.git" "$T/repo" 2>/dev/null
R="$T/repo"
$GIT -C "$R" config user.email t336@local
$GIT -C "$R" config user.name T336
mkdir -p "$R/.softhouse"
print '{"tasks":[]}' > "$R/.softhouse/tasks.json"
$GIT -C "$R" add -A >/dev/null
$GIT -C "$R" commit -qm "base"
$GIT -C "$R" push -q -u origin HEAD:main
$GIT -C "$R" branch --set-upstream-to=origin/main main >/dev/null 2>&1
install -m 755 "$HOOK" "$R/.git/hooks/post-checkout"

report () {  # $1 rc  $2 wtpath  $3 branch
  print "  rc=$1"
  print "  worktree dir exists        : $([ -d "$2" ] && print yes || print no)"
  print "  files checked out          : $([ -f "$2/.softhouse/tasks.json" ] && print yes || print no)"
  print "  branch ref exists          : $($GIT -C "$R" rev-parse --verify --quiet "refs/heads/$3" >/dev/null && print yes || print no)"
  print "  registered in worktree list: $($GIT -C "$R" worktree list --porcelain | grep -qx "worktree $2" && print yes || print no)"
  print "  worktree USABLE (git status): $($GIT -C "$2" status --porcelain >/dev/null 2>&1 && print yes || print no)"
}

print "===== CASE 1: everything pushed, gate=enforce -> hook must be SILENT, rc 0 ====="
cd "$R"
SOFTHOUSE_PUSH_GATE=enforce $GIT worktree add -b wt1 "$T/wt1" >/dev/null
report $? "$T/wt1" wt1

print "\n===== CASE 2: UNPUSHED .softhouse commit, gate=warn (the hook default) ====="
print '{"tasks":[{"id":"T999"}]}' > "$R/.softhouse/tasks.json"
$GIT -C "$R" commit -qam "unpushed dispatch record"
cd "$R"
$GIT worktree add -b wt2 "$T/wt2" >/dev/null
report $? "$T/wt2" wt2

print "\n===== CASE 3: UNPUSHED .softhouse commit, gate=ENFORCE   <-- THIS IS F-C ====="
cd "$R"
SOFTHOUSE_PUSH_GATE=enforce $GIT worktree add -b wt3 "$T/wt3" >/dev/null
report $? "$T/wt3" wt3

print "\n===== CASE 4: spawn FROM A LINKED WORKTREE, gate=ENFORCE (what this pipeline does) ====="
cd "$T/wt1"
SOFTHOUSE_PUSH_GATE=enforce $GIT worktree add -b wt4 "$T/wt4" >/dev/null
report $? "$T/wt4" wt4

print "\n===== CASE 5: is the 'refused' worktree of case 3 a fully working worker worktree? ====="
cd "$T/wt3"
$GIT switch -q -c softhouse/T999-slug
print "x" > f.txt
$GIT add f.txt
$GIT commit -qm "worker commit made inside the worktree the hook 'refused'"
print "  HEAD branch there : $($GIT -C "$T/wt3" symbolic-ref --short HEAD 2>&1)"
print "  commit made       : $($GIT -C "$T/wt3" log -1 --format='%h %s' 2>&1)"
print "  visible from repo : $($GIT -C "$R" log -1 --format='%h %s' softhouse/T999-slug 2>&1)"

print "\n===== CASE 6: gate=off (the escape hatch) ====="
cd "$R"
SOFTHOUSE_PUSH_GATE=off $GIT worktree add -b wt6 "$T/wt6" >/dev/null
report $? "$T/wt6" wt6

print "\n===== CASE 7: what does the hook OBSERVE at hook time? ====="
cat > "$R/.git/hooks/post-checkout" <<'PROBE'
#!/bin/sh
echo "  \$1(old)=$1"
echo "  \$2(new)=$2"
echo "  \$3(branch?)=$3"
echo "  PWD=$(pwd)"
echo "  GIT_DIR=${GIT_DIR:-<unset>}"
echo "  HEAD symbolic-ref here = $(git symbolic-ref --quiet --short HEAD 2>&1)"
echo "  git-common-dir         = $(git rev-parse --git-common-dir)"
echo "  refs visible: $(git for-each-ref --format='%(refname:short)' refs/heads | tr '\n' ' ')"
exit 0
PROBE
chmod +x "$R/.git/hooks/post-checkout"
cd "$R"
$GIT worktree add -b worktree-agent-deadbeef "$T/wt7" >/dev/null
print "  (above printed by the hook itself)"

print "\nscratch kept at $T"
