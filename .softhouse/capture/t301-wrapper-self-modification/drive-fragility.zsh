#!/bin/zsh
# T301 FRAGILITY DRIVE — WHY DID *RED* COME BACK CLEAN, AND WOULD IT STAY CLEAN?
#
# drive-snapshot.txt records the result that decides this task: with the snapshot
# DISABLED (FIRE_NO_SNAPSHOT=1), an in-place rewrite of the live wrapper during the
# driver's run did NOT reach the running fire — while the CONTROL arm, same mutation
# against a top-level sleep, DID. So the shipped wrapper is already immune, and the
# question is no longer "does the hazard exist" (probe B: it does) but "WHY is this
# particular file immune, and is that immunity a property anyone is maintaining?"
#
# THE HYPOTHESIS. zsh must parse a compound command in FULL before executing any of it.
# fire-program.sh calls the driver from inside its final `while (( CHAIN_N < CHAIN_MAX ))`
# loop, so reaching the multi-hour `wait` forces a read through the loop's `done` — and
# the handful of bytes after `done` fall inside the ~7.6 KB read-ahead measured in
# probe-source-and-shift.txt PART 3b. Immunity by accident of layout, not by design.
#
# TWO MEASUREMENTS, because the hypothesis makes two separate predictions:
#   ARM OFFSET     read the fire's own file OFFSET out of lsof while it sits in `wait`.
#                  If the hypothesis holds, offset == file size: it has read everything.
#   ARM FRAGILE    append top-level code AFTER the chain loop, so there are bytes the
#                  loop does not force a read of, and re-run the RED arm. If the
#                  hypothesis holds, the hazard REAPPEARS — which measures exactly how
#                  far this file is from losing an immunity nobody knows it depends on.
#   ARM FRAGILE-SNAP  the same fragile shape WITH the snapshot on. This is the arm that
#                  decides whether T301's fix earns its place.

set -u
emulate -L zsh

SRC="${1:?usage: drive-fragility.zsh <path-to-worktree>}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t301-frag.XXXXX")"
print -r -- "zsh: $ZSH_VERSION"
print -r -- "work: $WORK"

FAKE="$WORK/fake-claude"
cat > "$FAKE" <<'EOF'
#!/bin/zsh
sleep "${FAKE_CLAUDE_SLEEP:-14}"
exit 0
EOF
chmod +x "$FAKE"
BARE="$WORK/origin.git"; git init -q --bare "$BARE"

mkclone() {
  # `local arm="$1" c="$WORK/clone-$arm"` on ONE line is wrong in zsh: the command line
  # is expanded before its assignments take effect, so $arm resolved to the CALLER's
  # `arm` under dynamic scoping -- right by accident inside run_fragile, empty when
  # called from top level (ARM OFFSET cloned to "$WORK/clone-"). Two statements.
  local arm="$1"
  local c="$WORK/clone-$arm"
  git clone --quiet --no-hardlinks "$SRC" "$c" >/dev/null 2>&1
  ( cd "$c"; git remote set-url origin "$BARE"; git checkout -q -B main
    git config user.email t301@local; git config user.name T301
    /bin/rm -f .softhouse/LOCK ) >/dev/null 2>&1
  chmod +x "$c/.softhouse/bin/fire-program.sh"
  print -r -- "$c"
}

mutate_inplace() {   # insert a printing line just above the anchor, SAME inode
  /usr/bin/python3 - "$1" "$2" <<'PY'
import sys
p, anchor = sys.argv[1], sys.argv[2].encode()
b = open(p, 'rb').read()
i = b.index(anchor)
ins = b'log "T301-MUTATION-MARKER-REACHED"\n'
out = b[:i] + ins + b[i:]
f = open(p, 'r+b'); f.truncate(0); f.write(out); f.close()
sys.stderr.write("    mutated in place at byte %d of %d (+%d)\n" % (i, len(b), len(ins)))
PY
}

# ------------------------------------------------------------------ ARM OFFSET ----
print -r -- ""
print -r -- "=== ARM OFFSET — how many bytes of itself has the fire read when it blocks? ==="
CO=$(mkclone offset)
FPO="$CO/.softhouse/bin/fire-program.sh"
SIZE=$(/usr/bin/stat -f %z "$FPO")
mkdir -p "$WORK/logs-offset"
(
  export REPO="$CO" GEREGE_NBFI_REPO="$CO" LOG_DIR="$WORK/logs-offset" CLAUDE_BIN="$FAKE" \
         CHAIN_MAX=1 FAKE_CLAUDE_SLEEP=14 FINERACT_SRC="$WORK" FIRE_NO_SNAPSHOT=1
  zsh "$FPO" --force > "$WORK/offset.out" 2>&1
) &
OFIRE=$!
w=0; while (( w < 90 )); do /usr/bin/grep -q 'driver job pid=' "$WORK/offset.out" 2>/dev/null && break; sleep 1; w=$((w+1)); done
print -r -- "  wrapper: $FPO  ($SIZE bytes)"
print -r -- "  the fire is in \`wait\`; asking lsof for the OFFSET of every fd it holds on that file:"
# find the zsh process whose fd points at the wrapper
# `lsof -o` alone printed the file SIZE in the SIZE/OFF column, which is not the
# measurement wanted and would have been read as "offset == size" by coincidence. Field
# output (-Fn -Fo) asks for the offset explicitly: `o0t<N>` is the seek position.
for pid in ${(f)"$(/usr/bin/pgrep -f 'zsh .*fire-program.sh' 2>/dev/null)"}; do
  out=$(/usr/sbin/lsof -p "$pid" -a -d 0-30 -o -Fn -Fo 2>/dev/null | /usr/bin/tr '\n' ' ')
  [[ "$out" == *fire-program.sh* ]] || continue
  # walk the field stream: an 'o...' record is followed by the 'n<path>' it belongs to
  print -r -- "    pid $pid raw: $(print -r -- "$out" | /usr/bin/tr ' ' '\n' | /usr/bin/grep -A1 '^o' | /usr/bin/grep -B1 'fire-program.sh' | /usr/bin/tr '\n' ' ')"
done
print -r -- "  READ THIS AS: o0t<N> is the byte the shell will read next. If N equals the"
print -r -- "  $SIZE-byte file size, the fire has consumed ITS WHOLE SELF before blocking,"
print -r -- "  and no later edit of any kind can change what it goes on to execute."
wait $OFIRE
print -r -- "  fire rc=$?  — chain finished: $(/usr/bin/grep -c 'chain finished' "$WORK/offset.out")"

# ----------------------------------------------------------------- ARM FRAGILE ----
run_fragile() {   # $1 = arm label, $2 = FIRE_NO_SNAPSHOT value
  local arm="$1" nosnap="$2"
  local c; c=$(mkclone "$arm")
  local fp="$c/.softhouse/bin/fire-program.sh"
  # THE ONE-LINE CHANGE THAT REMOVES THE IMMUNITY: put top-level code after the chain
  # loop, far enough past it to be outside the ~7.6 KB read-ahead. Nothing about this is
  # exotic -- it is what "add a step to the end of the fire" looks like.
  /usr/bin/python3 - "$fp" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
anchor = 'log "chain finished after $CHAIN_N iteration(s)"'
i = s.index(anchor)
pad = '\n'.join('# fragility pad %d %s' % (k, '-'*60) for k in range(200)) + '\n'
# 200 padded comment lines ~ 15 KB of top-level text between `done` and the tail
s = s[:i] + pad + s[i:]
open(p, 'w').write(s)
PY
  local ld="$WORK/logs-$arm"; mkdir -p "$ld"
  print -r -- ""
  print -r -- "=== ARM $arm — top-level code after the chain loop, FIRE_NO_SNAPSHOT=$nosnap ==="
  print -r -- "  wrapper now $(/usr/bin/stat -f %z "$fp") bytes; zsh -n: $(zsh -n "$fp" 2>&1 && print parses)"
  (
    export REPO="$c" GEREGE_NBFI_REPO="$c" LOG_DIR="$ld" CLAUDE_BIN="$FAKE" \
           CHAIN_MAX=1 FAKE_CLAUDE_SLEEP=14 FINERACT_SRC="$WORK" FIRE_NO_SNAPSHOT="$nosnap"
    zsh "$fp" --force > "$WORK/$arm.out" 2>&1
  ) &
  local fpid=$!
  local w=0
  while (( w < 90 )); do /usr/bin/grep -q 'driver job pid=' "$WORK/$arm.out" 2>/dev/null && break; sleep 1; w=$((w+1)); done
  print -r -- "  driver up after ${w}s; mutating IN PLACE"
  mutate_inplace "$fp" 'log "chain finished after $CHAIN_N iteration(s)"'
  wait $fpid
  # CAPTURE THE FIRE'S rc HERE. The first draft printed `$?` one statement later, after
  # a `grep -c` assignment -- and `grep -c` exits 1 when the count is 0, so the arm that
  # PASSED (marker not reached) reported "fire rc=1" and looked like a failure it was not.
  local FIRE_RC=$?
  local reached
  reached=$(/usr/bin/grep -c 'T301-MUTATION-MARKER-REACHED' "$WORK/$arm.out")
  print -r -- "  fire rc=$FIRE_RC   chain finished: $(/usr/bin/grep -c 'chain finished' "$WORK/$arm.out")"
  print -r -- "  MARKER REACHED THE RUNNING FIRE: $( (( reached > 0 )) && print YES || print no ) (count=$reached)"
  /usr/bin/grep -E 'wrapper snapshot' "$WORK/$arm.out" | /usr/bin/sed 's/^/    /' | /usr/bin/head -2
}

run_fragile FRAGILE      1
run_fragile FRAGILE-SNAP 0

print -r -- ""
print -r -- "HOW TO READ THIS:"
print -r -- "  FRAGILE reached + FRAGILE-SNAP not reached  => the shipped wrapper's immunity is"
print -r -- "    a LAYOUT ACCIDENT that one ordinary edit removes, and the snapshot is what"
print -r -- "    makes the immunity a property of the mechanism instead of the layout."
print -r -- "  FRAGILE not reached                         => the immunity is more robust than"
print -r -- "    the hypothesis says, and the snapshot is buying much less than it looks."
print -r -- "DONE"
