#!/bin/zsh
# T279 — BOTH FIRES, SIMULATED, IN SCRATCH CLONES. Nothing outside /tmp is touched and no
# live worktree is created, removed or read for writing.
#
# A rule set that partitions on paper and has never been executed is a claim. This builds a
# real bare origin, two independent clones standing in for the LOCAL fire (which holds the
# lock) and the CLOUD fire (which must decide whether it may run), writes a real
# `.softhouse/LOCK` with real hostnames and real pids, backdates real commits so
# `git log -1 --format=%ct origin/main` reads what each scenario needs, and then asks the
# SHIPPED wrapper — `fire-program.sh --lock-signals`, which runs `lock_released_at`,
# `lock_started_age`, `origin_main_tip_age`, `lock_pid_state` and `lock_decide` — what the
# second orchestrator should do.
#
# Scenarios, all of them taken from measured history rather than invented:
#   S1  P-85 replay: the cloud fire at 12:10:00Z, tip 19m27s old, started_at 6h07m old.
#   S2  THE HOLE: fresh started_at, stale tip. Matched NO shipped arm; the state of every
#       08:00 fire.
#   S3  fire-20260827-230001: a 105 h lock facing a 2.99 h tip. Rule 2 reads HELD forever.
#   S4  dead pid on this host with a FRESH tip. Shipped arms 2 and 4 give OPPOSITE answers.
#   S5  released_at set.
#   S6  no LOCK at all.
#   S7  the mtime trap: a lock 8 h old whose file was rewritten 12 min ago by `git pull`.
set -uo pipefail
HERE="${0:A:h}"
WRAPPER="${HERE}/../../bin/fire-program.sh"; WRAPPER="${WRAPPER:A}"
SB="$(mktemp -d /tmp/t279-fires.XXXXXX)"
trap 'rm -rf "$SB"' EXIT
HOST="$(hostname -s)"

print -r -- "sandbox      : $SB"
print -r -- "wrapper      : $WRAPPER"
print -r -- "this host    : $HOST     this pid: $$"
print -r -- ""

git init -q --bare "$SB/origin.git"
git clone -q "$SB/origin.git" "$SB/local"     # the LOCAL fire's checkout (the holder)
cd "$SB/local"; git config user.email t279@local; git config user.name T279
mkdir -p .softhouse; print -r -- seed > .softhouse/seed
git add -A; git commit -q -m seed; git push -q origin HEAD:refs/heads/main
git branch -q -M main 2>/dev/null || true
git clone -q "$SB/origin.git" "$SB/cloud"     # the CLOUD fire's checkout (the challenger)
cd "$SB/cloud"; git config user.email t279@cloud; git config user.name T279cloud

# publish a commit whose committer date is N seconds in the past, from the LOCAL clone
publish_at_age() {
  local age="$1" msg="$2" d
  d="$(TZ=UTC /bin/date -u -r $(( $(date +%s) - age )) +%Y-%m-%dT%H:%M:%SZ)"
  cd "$SB/local"
  print -r -- "$msg $age" > .softhouse/pub.txt
  git add -A
  GIT_AUTHOR_DATE="$d" GIT_COMMITTER_DATE="$d" git commit -q -m "$msg"
  git push -q origin main
  cd "$SB/cloud"; git fetch -q origin
}

# write a LOCK into the CLOUD clone (that is where the challenger reads it)
write_lock() {  # $1 started_age  $2 pid  $3 host  $4 released_at ("" = omit)
  local sage="$1" pid="$2" host="$3" rel="$4" iso
  iso="$(TZ=UTC /bin/date -u -r $(( $(date +%s) - sage )) +%Y-%m-%dT%H:%M:%SZ)"
  mkdir -p "$SB/cloud/.softhouse"
  {
    print -r -- '{'
    print -r -- '  "holder": "local-fire-sim",'
    print -r -- "  \"host\": \"$host\","
    print -r -- "  \"pid\": $pid,"
    print -r -- "  \"started_at\": \"$iso\","
    print -r -- "  \"heartbeat\": \"$iso\","
    [[ -n "$rel" ]] && print -r -- "  \"released_at\": \"$rel\","
    print -r -- '  "live_workers": 0'
    print -r -- '}'
  } > "$SB/cloud/.softhouse/LOCK"
}

ask() {  # the CLOUD fire asks the SHIPPED wrapper what to do
  GEREGE_NBFI_REPO="$SB/cloud" zsh "$WRAPPER" --lock-signals | sed 's/^/    /'
}

scen() { print -r -- ""; print -r -- "================ $* ================"; }

# a pid that is certainly dead on this host, and one that is certainly alive
DEAD_PID=$(zsh -c 'exit 0' & print $!); wait $DEAD_PID 2>/dev/null
ALIVE_PID=$$

# ---------------------------------------------------------------------------- S1 -----
scen "S1  P-85 REPLAY — cloud fire at 12:10:00Z: tip 19m27s old, started_at 6h07m old"
print -r -- "  On 2026-08-22 the pre-fix rule read started_at alone (6h07m > 6h) and TOOK THE LOCK."
print -r -- "  Four worker branches died with the cloud's sandbox. Expected now: HELD-live."
publish_at_age 1167 "CHECKPOINT — fire closed clean, zero live workers"
write_lock 22020 $ALIVE_PID "$HOST" ""
ask

# ---------------------------------------------------------------------------- S2 -----
scen "S2  THE HOLE — released_at null, started_at 0.5h, tip 8.75h (every 08:00 fire)"
print -r -- "  Shipped arms 1-4: NONE match. No verdict. An agent that matches nothing improvises,"
print -r -- "  and improvising is how the incident happened. Expected now: HELD-default (arm 6)."
publish_at_age 31500 "overnight quiet"
write_lock 1800 $ALIVE_PID "$HOST" ""
ask

# ---------------------------------------------------------------------------- S3 -----
scen "S3  fire-20260827-230001 — lock 105h old, tip 2.99h old"
print -r -- "  Arm 4 alone reads HELD-by-a-live-holder, and there is no bound on how long."
print -r -- "  Expected now: TAKE-ceiling (arm 3)."
publish_at_age 10764 "somebody else pushed"
write_lock 378000 $ALIVE_PID "$HOST" ""
ask

# ---------------------------------------------------------------------------- S4 -----
scen "S4  DEAD PID ON THIS HOST, TIP FRESH — the shipped arms CONTRADICT each other"
print -r -- "  Shipped arm 2 says HELD (tip <6h); shipped arm 4 says TAKE (dead pid). Two"
print -r -- "  orchestrators reading in different orders get different answers."
print -r -- "  Expected now: TAKE-dead-pid (arm 2), unambiguously — dead pid outranks freshness."
publish_at_age 600 "a fresh push by anyone"
write_lock 3600 $DEAD_PID "$HOST" ""
print -r -- "  (dead pid used: $DEAD_PID — reaped above; kill -0 rc=$(kill -0 $DEAD_PID 2>/dev/null; print $?))"
ask

scen "S4b SAME STATE, BUT THE PID IS ON ANOTHER HOST — must NOT be judged"
write_lock 3600 $DEAD_PID "some-other-machine" ""
print -r -- "  Expected: pid_state=other_host, verdict HELD-live (the tip is still fresh)."
ask

# ---------------------------------------------------------------------------- S5 -----
scen "S5  released_at SET"
write_lock 3600 $ALIVE_PID "$HOST" "2026-08-28T01:00:00Z"
print -r -- "  Expected: FREE-released (arm 1)."
ask

# ---------------------------------------------------------------------------- S6 -----
scen "S6  NO LOCK AT ALL"
rm -f "$SB/cloud/.softhouse/LOCK"
print -r -- "  Expected: FREE-no-lock (arm 0)."
ask

# ---------------------------------------------------------------------------- S7 -----
scen "S7  THE MTIME TRAP — T265 F-3, reproduced"
print -r -- "  A lock stamped 8h ago whose FILE was rewritten 12.6 minutes ago by the"
print -r -- "  \`git pull --ff-only\` the wrapper runs seconds earlier. The old wrapper read"
print -r -- "  759s and exited 'another orchestrator holds the lock', costing the fire 6h."
publish_at_age 43200 "nothing published for 12h"
write_lock 28800 $ALIVE_PID "$HOST" ""      # written just now => mtime age ~0
print -r -- "  Expected: mtime_age near 0 (the OLD signal, which would say HELD) while"
print -r -- "  started_age=28800 and tip_age=43200 give TAKE-both-stale (arm 5)."
ask

# ---------------------------------------------------------------------------- S8 -----
scen "S8  THE CASE NO LOCK DESIGN CAN FIX — the holder committed and NEVER PUSHED"
print -r -- "  This is P-85's actual cause. The holder is live with five workers running; its"
print -r -- "  lock refresh, dispatch record and in-flight RESUME.md are COMMITTED LOCALLY and"
print -r -- "  unpushed, so the published tip is the previous fire's \"closed clean, zero live"
print -r -- "  workers\" attestation, 12h old, and the published LOCK is the previous fire's."
print -r -- "  Expected: TAKE-both-stale — the repaired rules take the lock and the incident"
print -r -- "  HAPPENS AGAIN. This is not a defect in the arms; it is the proof that the arms"
print -r -- "  are the SECOND line of defence. The first is the obligation in STEP 0, and the"
print -r -- "  only mechanical backing for it is the post-checkout hook in this directory."
publish_at_age 43200 "CHECKPOINT — fire closed clean, zero live workers"
write_lock 43200 $ALIVE_PID "other-machine-the-holder-is-on" ""
ask

print -r -- ""
print -r -- "================ what this drive did NOT touch ================"
print -r -- "  no worktree was added or removed anywhere;"
print -r -- "  \$GEREGE_NBFI_REPO was pointed at $SB/cloud for every call;"
print -r -- "  the real repo at /Users/buv/gerege-nbfi was never opened by this script."
