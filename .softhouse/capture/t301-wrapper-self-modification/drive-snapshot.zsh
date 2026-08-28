#!/bin/zsh
# T301 DRIVE — RED/GREEN AGAINST THE SHIPPED WRAPPER, NOT A MODEL OF IT.
#
# Probes A and B measured the mechanism on synthetic subjects. This drives the REAL
# fire-program.sh end to end in a scratch clone, with a fake `claude` that just sleeps,
# and rewrites the wrapper IN PLACE while the "driver" runs.
#
# ARM RED    FIRE_NO_SNAPSHOT=1 — pre-T301 behaviour. Does the in-place edit reach the
#            running fire?
# ARM GREEN  default — snapshot + re-exec. It must NOT reach, and the fire must still
#            complete its whole tail (lib sourced, attest run, prune sweep, chain end).
# ARM COST-* the failure modes the fix INTRODUCES: a broken SCRIPT_DIR, a re-exec loop,
#            and a snapshot that cannot be taken.
#
# WHY A CONTROL ARM EXISTS. The wrapper invokes the driver from inside its final
# `while` loop, and zsh must parse a compound command in full before running any of it —
# so the shipped wrapper may already read itself to EOF before the multi-hour wait, which
# would make RED come back clean for a reason that has nothing to do with safety. A RED
# that does not reproduce is only informative if the harness can be shown to detect a
# reach at all, so arm CONTROL runs the identical mutation against a subject whose sleep
# is at TOP LEVEL. CONTROL must be REACHED or the whole drive is uninterpretable.
#
# Touches nothing outside $TMPDIR: scratch clone, throwaway bare origin, own LOG_DIR.

set -u
emulate -L zsh

SRC="${1:?usage: drive-snapshot.zsh <path-to-worktree>}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t301-drive.XXXXX")"
print -r -- "zsh: $ZSH_VERSION   git: $(git --version)"
print -r -- "source worktree: $SRC"
print -r -- "work: $WORK"

# ---- a fake claude that just occupies the foreground for a while -------------------
FAKE="$WORK/fake-claude"
cat > "$FAKE" <<'EOF'
#!/bin/zsh
sleep "${FAKE_CLAUDE_SLEEP:-10}"
exit 0
EOF
chmod +x "$FAKE"

BARE="$WORK/origin.git"
git init -q --bare "$BARE"

mkclone() {  # $1 = arm name -> echoes clone path
  # `local arm="$1" c="$WORK/clone-$arm"` is WRONG in zsh and was wrong here: the whole
  # command line is expanded before any of its assignments take effect, so $arm on the
  # same line resolved to the CALLER's `arm` under dynamic scoping. Inside run_arm that
  # accidentally gave the right answer; called from top level it gave "", so every
  # top-level arm cloned to the same path "$WORK/clone-" and the second one silently
  # reused the first one's clone. Two statements, so the value is real.
  local arm="$1"
  local c="$WORK/clone-$arm"
  git clone --quiet --no-hardlinks "$SRC" "$c" >/dev/null 2>&1
  ( cd "$c"; git remote set-url origin "$BARE"; git checkout -q -B main
    git config user.email t301@local; git config user.name T301
    /bin/rm -f .softhouse/LOCK ) >/dev/null 2>&1
  chmod +x "$c/.softhouse/bin/fire-program.sh"
  print -r -- "$c"
}

# The mutation: insert a PRINTING line just above the wrapper's final "chain finished"
# log, IN PLACE (r+b / truncate / write = same inode, the `cat >` shape measured in
# probe-writer-inode.txt). If the running fire executes it, the marker lands in the log.
mutate_inplace() {
  /usr/bin/python3 - "$1" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
anchor = b'log "chain finished after $CHAIN_N iteration(s)"'
i = b.index(anchor)
ins = b'log "T301-MUTATION-MARKER-REACHED"\n'
out = b[:i] + ins + b[i:]
f = open(p, 'r+b'); f.truncate(0); f.write(out); f.close()
sys.stderr.write("    mutated in place at byte %d (+%d bytes); inode preserved\n" % (i, len(ins)))
PY
}

run_arm() {  # $1 arm, rest: env assignments
  local arm="$1"; shift
  local c; c=$(mkclone "$arm")
  local fp="$c/.softhouse/bin/fire-program.sh"
  local ld="$WORK/logs-$arm"; mkdir -p "$ld"
  print -r -- ""
  print -r -- "=== ARM $arm ==="
  print -r -- "  clone: $c"
  print -r -- "  wrapper inode before: $(/usr/bin/stat -f %i "$fp") bytes=$(/usr/bin/stat -f %z "$fp")"
  (
    export REPO="$c" GEREGE_NBFI_REPO="$c" LOG_DIR="$ld" CLAUDE_BIN="$FAKE" \
           CHAIN_MAX=1 FAKE_CLAUDE_SLEEP=10 FINERACT_SRC="$WORK"
    for kv in "$@"; do export "$kv"; done
    zsh "$fp" --force > "$WORK/$arm.out" 2>&1
  ) &
  local firepid=$!
  # wait for the driver child to actually be running, then mutate
  local waited=0
  while (( waited < 90 )); do
    /usr/bin/grep -q 'driver job pid=' "$WORK/$arm.out" 2>/dev/null && break
    sleep 1; waited=$((waited+1))
  done
  if (( waited >= 90 )); then
    print -r -- "  !! the fire never reached 'driver job pid=' — arm is UNINTERPRETABLE"
  else
    print -r -- "  driver is up after ${waited}s; mutating the wrapper IN PLACE now"
    mutate_inplace "$fp"
    print -r -- "  wrapper inode after:  $(/usr/bin/stat -f %i "$fp") bytes=$(/usr/bin/stat -f %z "$fp")"
  fi
  wait $firepid
  print -r -- "  fire rc=$?"
  local reached
  reached=$(/usr/bin/grep -c 'T301-MUTATION-MARKER-REACHED' "$WORK/$arm.out")
  print -r -- "  MARKER REACHED THE RUNNING FIRE: $( (( reached > 0 )) && print YES || print no ) (count=$reached)"
  print -r -- "  --- the lines that prove the fire completed its tail ---"
  /usr/bin/grep -E 'wrapper identity|wrapper snapshot|FATAL|could not source|refguard\||attest-preflight|worktree prune sweep|chain finished|chain: stopping' \
    "$WORK/$arm.out" | /usr/bin/sed 's/^/    /' | /usr/bin/head -14
  # 'fire start' as a bare string also matches "...before this fire started" in the
  # attest line, which made the first draft report 2 for every arm including the ones
  # that never re-exec. Anchor on the actual log line.
  print -r -- "  'fire start —' lines (a re-exec loop would show more than 1): $(/usr/bin/grep -c 'fire start —' "$WORK/$arm.out")"
}

run_arm RED   FIRE_NO_SNAPSHOT=1
run_arm GREEN FIRE_NO_SNAPSHOT=0

# ---- CONTROL: the same mutation against a top-level sleep --------------------------
print -r -- ""
print -r -- "=== ARM CONTROL — can this harness detect a reach at all? ==="
print -r -- "Identical in-place insertion, but the subject's sleep is at TOP LEVEL rather"
print -r -- "than inside a compound command, so zsh has NOT been forced to read to EOF."
CS="$WORK/control.zsh"
{
  print -r -- "#!/bin/zsh"
  print -r -- "print -r -- 'driver job pid=fake'"
  print -r -- "sleep 6"
  local i; for i in {1..1500}; do print -r -- "# filler $i --------------------------------------------------------"; done
  print -r -- 'log() { print -r -- "$*"; }'
  print -r -- 'CHAIN_N=1'
  print -r -- 'log "chain finished after $CHAIN_N iteration(s)"'
} > "$CS"
( zsh "$CS" > "$WORK/control.out" 2>&1 ) &
cpid=$!
sleep 2
mutate_inplace "$CS"
wait $cpid
print -r -- "  MARKER REACHED: $( /usr/bin/grep -q 'T301-MUTATION-MARKER-REACHED' "$WORK/control.out" && print YES || print no )"
print -r -- "  control output tail:"
/usr/bin/tail -3 "$WORK/control.out" | /usr/bin/sed 's/^/    /'

# ---- COST arms: the failure modes the fix introduces --------------------------------
print -r -- ""
print -r -- "=== ARM COST-SNAPSHOT-FAILS — TMPDIR unwritable; must fall back, not die ==="
CF=$(mkclone costfail)
RO="$WORK/readonly"; mkdir -p "$RO"; chmod 500 "$RO"
mkdir -p "$WORK/logs-costfail"
REPO="$CF" GEREGE_NBFI_REPO="$CF" LOG_DIR="$WORK/logs-costfail" CLAUDE_BIN="$FAKE" \
  FAKE_CLAUDE_SLEEP=1 CHAIN_MAX=1 FINERACT_SRC="$WORK" TMPDIR="$RO/" \
  zsh "$CF/.softhouse/bin/fire-program.sh" --probe > "$WORK/costfail.out" 2>&1
print -r -- "  rc=$?"
/usr/bin/grep -E 'SNAPSHOT FAILED|wrapper snapshot|wrapper identity|FATAL|probe only' "$WORK/costfail.out" \
  | /usr/bin/sed 's/^/    /'
chmod 700 "$RO"

print -r -- ""
print -r -- "=== ARM COST-SCRIPT-DIR — does SCRIPT_DIR still find bin/ and guards/ ? ==="
CD=$(mkclone costdir)
mkdir -p "$WORK/logs-costdir"
REPO="$CD" GEREGE_NBFI_REPO="$CD" LOG_DIR="$WORK/logs-costdir" CLAUDE_BIN="$FAKE" \
  FAKE_CLAUDE_SLEEP=1 CHAIN_MAX=1 FINERACT_SRC="$WORK" \
  zsh "$CD/.softhouse/bin/fire-program.sh" --probe > "$WORK/costdir.out" 2>&1
print -r -- "  rc=$?"
print -r -- "  a snapshot run resolves SCRIPT_DIR to the REPO's bin/, so all four"
print -r -- "  siblings must still be found: lib-worktree-prune.zsh (source),"
print -r -- "  branch_sweep.py (refguard/sweep), ../guards/repo-state-attest.sh (attest)."
/usr/bin/grep -E 'wrapper snapshot|could not source|FATAL|refguard\||sweep\||attest-preflight|probe only' \
  "$WORK/costdir.out" | /usr/bin/sed 's/^/    /' | /usr/bin/head -10

print -r -- ""
print -r -- "=== ARM COST-EXEC-LOOP — exactly one re-exec, never two ==="
print -r -- "  'fire start —' lines in the COST-SCRIPT-DIR run: $(/usr/bin/grep -c 'fire start —' "$WORK/costdir.out")"
print -r -- "  'RUNNING FROM A SNAPSHOT' lines:               $(/usr/bin/grep -c 'RUNNING FROM A SNAPSHOT' "$WORK/costdir.out")"
print -r -- "  snapshot dirs left under TMPDIR by this drive: $(/usr/bin/find "${TMPDIR:-/tmp}" -maxdepth 1 -name 'fire-wrapper-snap.*' -type d 2>/dev/null | /usr/bin/wc -l | tr -d ' ')"

print -r -- ""
print -r -- "DONE"
