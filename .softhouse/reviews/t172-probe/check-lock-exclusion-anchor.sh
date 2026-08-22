#!/bin/zsh
# T210 -- live-anchored regression probe for the .softhouse/LOCK exclusion
# guard inside fire-program.sh's exit-protocol dirty-tree check.
#
# SUPERSEDES run-pre-fix.sh / run-post-fix.sh as the LIVE regression gate.
# Those two scripts replay BYTES captured at T172 time into
# pre-fix-line224.txt / post-fix-line224.txt and say nothing about the file
# as it exists today -- measured 22 Aug 2026 (T210): T190 deleted the exact
# grep pattern those files replay ("LC_ALL=C grep -av '^?? \.softhouse/LOCK'"
# and its anchored fix), so `grep -c` for that pattern against the CURRENT
# fire-program.sh returns 0, yet both old scripts kept passing against
# frozen bytes that exist nowhere in the real file any more.
#   P-22 (patterns.md): a control that cannot fail is worse than none,
#   because it is believed.
#   P-35 (patterns.md): a check inspecting zero items is an ERROR, not a
#   pass.
#
# This script instead:
#   1. EXTRACTS the current DIRTY=... guard line from the TARGET file by
#      grep PATTERN, never by line number -- line numbers drift on every
#      rewrite (T172 was :224 pre-T190; T190/T202 moved the equivalent
#      logic to :313 and changed its shape from a piped grep to a git
#      pathspec exclusion).
#   2. ERRORS LOUDLY, naming the pattern and the file, if that extraction
#      matches the target ZERO times or MORE THAN ONCE (an anchor used to
#      pull a single line must be unique).
#   3. Confirms the matched line still concerns .softhouse/LOCK exclusion --
#      if that reference is gone, this script SAYS SO and exits nonzero
#      rather than inventing a replacement anchor to keep a green bar.
#   4. EVALUATES the extracted line VERBATIM (never a hand-transcribed
#      copy) against a fresh scratch git repo fixture and checks the
#      property T172 fixed: a sibling path sharing LOCK's directory prefix
#      (.softhouse/LOCKED_STATE.md) must survive the filter, and
#      .softhouse/LOCK itself must not.
#
# Usage:
#   zsh check-lock-exclusion-anchor.sh [TARGET_FILE]
#     TARGET_FILE defaults to the live .softhouse/bin/fire-program.sh,
#     resolved relative to this script's own location. Pass a scratch
#     COPY here to drive RED / zero-match demonstrations without ever
#     touching the live file -- see run-red-demo.sh and
#     run-zero-match-demo.sh in this same directory.
#
# grep binding (P-58, patterns.md): in this repo's interactive shells,
# `grep` is shadowed by a function that re-execs as ugrep with -G -I
# --exclude-dir=... . That shadow is a shell FUNCTION, not exported, so it
# does not survive into a fresh `zsh script.sh` child process -- measured
# 22 Aug 2026 (T210): a bare `#!/bin/zsh` script invoked as its own process
# resolves bare `grep` to /usr/bin/grep (BSD grep 2.6.0-FreeBSD) both under
# plain `zsh script.sh` and under `zsh -lc '...'` (the shape launchd uses
# for fire-program.sh itself). This script does not rely on that
# resolution holding for whatever CALLER shell invokes it, though: it
# hardcodes GREP=/usr/bin/grep below and uses only that binding, plus
# LC_ALL=C for byte-deterministic matching and -a so a binary-looking byte
# sequence is never silently skipped -- so the anchor check is
# byte-identical regardless of what bare `grep` means in the caller.
set -uo pipefail

GREP=/usr/bin/grep
if [[ ! -x "$GREP" ]]; then
  print -u2 -- "ERROR: $GREP not found or not executable -- this probe hardcodes that binary (P-58) and refuses to fall back to a shell-shadowed grep."
  exit 2
fi

HERE="${0:A:h}"
DEFAULT_TARGET="${HERE}/../../bin/fire-program.sh"
DEFAULT_TARGET="${DEFAULT_TARGET:A}"
TARGET="${1:-$DEFAULT_TARGET}"

if [[ ! -f "$TARGET" ]]; then
  print -u2 -- "ERROR: target file does not exist: $TARGET"
  exit 2
fi

# --- 1/2: locate the guard line by pattern, error loudly on 0 or >1 -------
ANCHOR_PATTERN='DIRTY=\$\(git status --porcelain'
LOCK_REF_PATTERN='\.softhouse/LOCK'

MATCH_COUNT=$(LC_ALL=C "$GREP" -Ea -c -- "$ANCHOR_PATTERN" "$TARGET")
GREP_RC=$?
# BSD grep: rc=0 match found, rc=1 legitimately zero matches (still prints
# "0"), rc>=2 a real read/pattern error. Only >=2 is "grep itself broke".
if (( GREP_RC >= 2 )); then
  print -u2 -- "ERROR: grep failed reading target (rc=$GREP_RC) -- cannot conclude anything about the anchor."
  print -u2 -- "  pattern: $ANCHOR_PATTERN"
  print -u2 -- "  file:    $TARGET"
  exit 2
fi

if (( MATCH_COUNT == 0 )); then
  print -u2 -- "ERROR (P-35, patterns.md): anchor pattern matched ZERO times -- this is not a pass."
  print -u2 -- "  pattern: $ANCHOR_PATTERN"
  print -u2 -- "  file:    $TARGET"
  print -u2 -- "The guard line this probe checks no longer exists at that text in the target file. Investigate and re-point the anchor by hand; do NOT treat a zero-match as green."
  exit 1
fi

if (( MATCH_COUNT > 1 )); then
  print -u2 -- "ERROR: anchor pattern matched $MATCH_COUNT times -- not unique, refusing to guess which line to extract."
  print -u2 -- "  pattern: $ANCHOR_PATTERN"
  print -u2 -- "  file:    $TARGET"
  exit 1
fi

GUARD_LINE=$(LC_ALL=C "$GREP" -Ea -- "$ANCHOR_PATTERN" "$TARGET")

# --- 3: the matched line must still be ABOUT .softhouse/LOCK exclusion ----
if ! print -r -- "$GUARD_LINE" | LC_ALL=C "$GREP" -Eaq -- "$LOCK_REF_PATTERN"; then
  print -u2 -- "STOP: the guard line matched the anchor but no longer references .softhouse/LOCK at all:"
  print -u2 -- "  $GUARD_LINE"
  print -u2 -- "The LOCK-exclusion property this probe exists to check appears to have been removed or moved elsewhere. Refusing to invent a replacement anchor -- re-scope this probe by hand after confirming where (or whether) the property still lives."
  exit 1
fi

echo "anchor: extracted from $TARGET"
echo "  $GUARD_LINE"
echo

# --- 4: replay the EXTRACTED bytes against a fresh scratch fixture --------
zsh "${HERE}/setup-scratch-repo.sh" >/dev/null
SCRATCH=/tmp/t172-scratch-repo
if [[ ! -d "$SCRATCH/.git" ]]; then
  print -u2 -- "ERROR: scratch repo fixture missing at $SCRATCH after setup-scratch-repo.sh ran."
  exit 2
fi

builtin cd "$SCRATCH" || { print -u2 -- "ERROR: could not cd into scratch repo $SCRATCH"; exit 2; }

eval "$GUARD_LINE"
EVAL_RC=$?
if (( EVAL_RC != 0 )); then
  print -u2 -- "ERROR: the extracted guard line's git command exited $EVAL_RC in the scratch repo -- cannot conclude anything about filtering."
  exit 2
fi

echo "DIRTY (from the live-extracted guard line, run against the scratch fixture) ="
print -r -- "$DIRTY"
echo

PASS=1

if print -r -- "$DIRTY" | "$GREP" -Faq -- 'LOCKED_STATE.md'; then
  echo "CHECK 1 PASS: sibling .softhouse/LOCKED_STATE.md survived the filter (not silently dropped)"
else
  echo "CHECK 1 FAIL: sibling .softhouse/LOCKED_STATE.md was DROPPED from DIRTY -- the prefix-collision regression T172 fixed is reproduced"
  PASS=0
fi

if print -r -- "$DIRTY" | "$GREP" -Fxq -- '?? .softhouse/LOCK'; then
  echo "CHECK 2 FAIL: .softhouse/LOCK itself is present in DIRTY -- the guard is not excluding the real lock file at all"
  PASS=0
else
  echo "CHECK 2 PASS: .softhouse/LOCK is correctly excluded from DIRTY (no over-correction)"
fi

echo
if (( PASS )); then
  echo "VERDICT: PASS -- live LOCK-exclusion anchor holds against $TARGET"
  exit 0
else
  echo "VERDICT: FAIL -- live LOCK-exclusion anchor is BROKEN against $TARGET"
  exit 1
fi
