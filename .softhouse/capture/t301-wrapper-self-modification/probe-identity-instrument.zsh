#!/bin/zsh
# T301 PROBE C — IS THE "wrapper identity" INSTRUMENT STILL ALIVE?
#
# T309 added a line to fire-program.sh that logs, at start, which BYTES the fire is
# running: path, inode, sha256, size. The T301 brief requires that instrument be
# re-checked rather than assumed, and P-95 -- "a fallback and a fail-open are
# indistinguishable by reading" -- says the only way to know a guard fires is to make
# it not fire and watch the output change. So this probe has a GREEN arm and a RED arm.
#
# It never touches the live checkout. Everything runs against a scratch clone, with
# REPO/LOG_DIR redirected, and --probe exits before the lock is taken
# [VERIFIED: fire-program.sh, `if (( PROBE_ONLY )); then ... exit 0` above the lock].

set -u
emulate -L zsh

SRC="${1:?usage: probe-identity-instrument.zsh <path-to-worktree-with-fire-program.sh>}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t301-identity.XXXXX")"
CLONE="$WORK/clone"
print -r -- "zsh: $ZSH_VERSION"
print -r -- "source worktree: $SRC"
print -r -- "work: $WORK"

git clone --quiet --no-hardlinks "$SRC" "$CLONE" || { print -r -- "FATAL: clone failed"; exit 1; }
FP="$CLONE/.softhouse/bin/fire-program.sh"
chmod +x "$FP"
print -r -- "subject: $FP"
print -r -- "subject inode=$(/usr/bin/stat -f %i "$FP") bytes=$(/usr/bin/stat -f %z "$FP") sha256=$(/usr/bin/shasum -a 256 "$FP" | cut -c1-16)"

run_probe() {  # $1 = label, rest = env overrides already exported by caller
  local label="$1"
  local ld="$WORK/logs-$label"; mkdir -p "$ld"
  print -r -- ""
  print -r -- "=== ARM: $label ==="
  REPO="$CLONE" LOG_DIR="$ld" GEREGE_NBFI_REPO="$CLONE" \
    zsh "$FP" --probe 2>&1 | /usr/bin/grep -E 'wrapper identity|UNRECORDED|fire start|probe only' \
    || print -r -- "  (no matching lines)"
}

# ---- GREEN: the instrument as shipped -------------------------------------------
run_probe green

# ---- RED: remove the instrument's INPUT and confirm the log changes --------------
# The instrument is guarded by `[[ -r "${0:A}" ]]`. Make the script unreadable-as-a-file
# to its own `stat`/`shasum` while still being executable content... which is not
# possible on a plain file, so the RED arm instead DELETES the observation and checks
# the WARN branch prints. The realistic way to reach the WARN branch is `zsh < script`
# (stdin), where ${0} is not a path at all.
print -r -- ""
print -r -- "=== ARM: red-stdin — feed the script on STDIN so \${0:A} is not a real path ==="
print -r -- "(this is also the honest test of the instrument's OWN assumption: it claims to"
print -r -- " identify 'the bytes this fire is running', which it can only do when it was"
print -r -- " invoked BY PATH.)"
mkdir -p "$WORK/logs-red"
REPO="$CLONE" LOG_DIR="$WORK/logs-red" GEREGE_NBFI_REPO="$CLONE" \
  zsh -s --probe < "$FP" > "$WORK/red.out" 2>&1
print -r -- "  rc=$?  — FULL output, unfiltered (the filtered first draft printed"
print -r -- "  '(no matching lines)', which is not a result, it is a missing result):"
if [[ -s "$WORK/red.out" ]]; then
  /usr/bin/head -12 "$WORK/red.out" | while IFS= read -r l; do print -r -- "    $l"; done
else
  print -r -- "    (the run produced NO output at all)"
fi

# ---- RED-EXCISE: delete the instrument, confirm the log line disappears -----------
# This is the remove-and-observe arm proper. If the 'wrapper identity' line still
# appeared with the code deleted, it would be coming from somewhere else and the
# instrument would be decorative.
print -r -- ""
print -r -- "=== ARM: red-excise — delete the identity block, require the line to VANISH ==="
CLONE2="$WORK/clone-excised"
git clone --quiet --no-hardlinks "$SRC" "$CLONE2" || { print -r -- "FATAL: clone2 failed"; exit 1; }
FP2="$CLONE2/.softhouse/bin/fire-program.sh"
/usr/bin/python3 - "$FP2" <<'PY'
import sys, re
p = sys.argv[1]
s = open(p).read()
start = s.index('if [[ -r "${0:A}" ]]; then')
end   = s.index('\nfi\n', start) + len('\nfi\n')
open(p, 'w').write(s[:start] + '# T301 red arm: identity block excised\n' + s[end:])
sys.stderr.write("  excised %d bytes\n" % (end - start))
PY
chmod +x "$FP2"
print -r -- "  zsh -n on the excised copy: $(zsh -n "$FP2" 2>&1 && print 'parses')"
mkdir -p "$WORK/logs-excise"
REPO="$CLONE2" LOG_DIR="$WORK/logs-excise" GEREGE_NBFI_REPO="$CLONE2" \
  zsh "$FP2" --probe 2>&1 | /usr/bin/grep -E 'wrapper identity|UNRECORDED|fire start|probe only' \
  | while IFS= read -r l; do print -r -- "    $l"; done
print -r -- "  'wrapper identity' lines in the excised arm: $(REPO="$CLONE2" LOG_DIR="$WORK/logs-excise2" GEREGE_NBFI_REPO="$CLONE2" zsh "$FP2" --probe 2>&1 | /usr/bin/grep -c 'wrapper identity')"

# ---- DISCRIMINATION: does the reported sha actually track the bytes? --------------
# A sha that never changes is a constant dressed as a measurement. Change one byte of
# the subject and require the reported sha to change with it.
print -r -- ""
print -r -- "=== ARM: discrimination — mutate one comment byte, require the sha to move ==="
print -r -- "  sha on disk before: $(/usr/bin/shasum -a 256 "$FP" | cut -c1-16)  bytes=$(/usr/bin/stat -f %z "$FP")"
print -r -- "# t301 discrimination marker" >> "$FP"
print -r -- "  sha on disk after:  $(/usr/bin/shasum -a 256 "$FP" | cut -c1-16)  bytes=$(/usr/bin/stat -f %z "$FP")"
run_probe mutated

print -r -- ""
print -r -- "PASS CRITERIA:"
print -r -- "  green   -> one 'wrapper identity:' line with a real inode/sha/bytes"
print -r -- "  red     -> NO 'wrapper identity:' line; the WARN/UNRECORDED branch instead"
print -r -- "  mutated -> a 'wrapper identity:' line whose sha DIFFERS from green's and"
print -r -- "             matches the post-mutation sha printed above"
print -r -- "DONE"
