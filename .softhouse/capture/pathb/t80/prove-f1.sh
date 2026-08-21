#!/bin/sh
# T80 — proof for T85 F-1: a BREACHED attest.py run must leave the filesystem exactly as it found it.
#
# T85 showed that `python3 attest.py default emiloop` printed "no capture attempted, no attestation
# written" while having already stamped eleven `gerege` captures as `default` and replaced their
# HALF_UP precondition transcript with a breached HALF_EVEN one.  The emiloop set is the reachable
# victim because it is exempt from the directory-NAME check (its committed directory is `out/emiloop`,
# which cannot end in a tenant id without renaming committed evidence).
#
# This script runs the SAME invocation twice — once against the PRE-FIX attest.py restored from git,
# once against the fixed one — and diffs the digests of the committed set each time.  A proof that
# only shows the "after" cannot tell a fix from a no-op.
#
# =====================================================================================
# T161 — THE LIVE RIG FILE THIS PROOF OVERWRITES MUST COME BACK, ON EVERY EXIT PATH.
#
# To show the pre-fix behaviour this script writes PRE-FIX BYTES OVER THE LIVE
# t36/attest.py, runs them (which stamps `out/emiloop/CAPTURED-FROM-TENANT` and replaces
# `out/emiloop/preconditions.txt`), and then undoes all three.  Until this fix there was
# NO trap anywhere in the file: a Ctrl-C, a `kill`, a closed terminal, a `| head` that
# exits early, or any abrupt exit inside that window left
#
#   * `t36/attest.py` sitting in the tree AT THE PRE-FIX BYTES — the attester that
#     mislabelled eleven captures, wearing the name of the current one; and
#   * a forged-looking `CAPTURED-FROM-TENANT` stamp plus a breached HALF_EVEN
#     `preconditions.txt` inside the COMMITTED evidence set.
#
# A stranded vector is at least detectable by counting.  A silently downgraded attester
# keeps producing attestations that look entirely normal, and `t36/attest.py` is on the
# ENFORCED PRECONDITION PATH (`preconditions.sh` breach -> `attest.py` abort) that this
# program cites as the thing standing between a fabricated capture and the corpus.
#
# The fix is T156's shape, deliberately not a second idiom (`t149/prove-redgreen.sh`):
#   * `trap` on EXIT, INT, TERM, HUP, QUIT and PIPE — see the trap block for why each;
#   * the restore is VERIFIED, never assumed: the attester's sha256 is checked against the
#     digest pinned at start-up, and the whole evidence set is re-censused;
#   * the restore is IDEMPOTENT — running it twice is a no-op, by construction;
#   * START-UP RECOVERY, because SIGKILL runs no handler and no trap can change that;
#   * the restore source is an IMMUTABLE GIT BLOB, not the old `$O/.f1-fixed` dotfile.
#     A backup living inside the output directory is part of the defect: `rm -rf out/`
#     takes the only copy of the live attester with it.
# =====================================================================================
set -u
T80=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T80/.." && pwd)
O=$T80/out
E=$W/t36/out/emiloop
A=$W/t36/attest.py                        # the LIVE rig file this proof overwrites
REPO=$(cd "$W/../../.." && pwd)
REL_A=.softhouse/capture/pathb/t36/attest.py
STAMP=$E/CAPTURED-FROM-TENANT
GUARD=$T80/.f1-swap-in-progress           # in-flight marker: a POINTER INTO GIT'S OBJECT
                                          # STORE, not a copy of the bytes, and it lives
                                          # outside `out/` so a cleanup cannot take it.
PREFIX_COMMIT=813acb1                     # T80's own pre-F-1 attest.py
# P-24: the commit above is immutable, but the proof still says WHICH BYTES it tested, and
# refuses to run if `git show` hands it anything else.
PREFIX_BLOB=8e9f865ba6e9f8841c9be81962770e3c818fe53f
PREFIX_SHA256=c56825ad6f915063703240ac7ea6a6a54608c4f06333f21d2ddff0327de52f92
cd "$W"

fail() { echo "PROOF FAILED: $*" >&2; exit 1; }

# T99 (sweep for the F-2 shape): this snapshot IS the evidence this proof turns on — a bare
# `shasum` on $PATH could make BEFORE and AFTER agree by fiat.  Hardened instrument instead.
. "$W/t36/sha256.sh"
sha256_init || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }
snap() {
  for f in "$E"/*; do
    [ -f "$f" ] || continue
    sha256_file "$f" || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }
    printf '%s  %s\n' "$SHA256_RESULT" "$f"
  done | sed "s|$W/||"
}

# Digest of one file, or the literal MISSING.  Used by the guard, which must be able to
# describe a file that an interrupted run left absent, not just one that changed.
sha_or_missing() {
  if [ -f "$1" ] && sha256_file "$1"; then printf '%s\n' "$SHA256_RESULT"
  else printf 'MISSING\n'; fi
}

# ---------------------------------------------------------------- T161: the recovery
# Put the attester back at <sha256> from immutable blob <blob>.  IDEMPOTENT: if the file
# already hashes to <sha256> it does nothing and succeeds, so calling it from start-up
# recovery, from the middle of the run and again from the EXIT trap is safe.  VERIFIED:
# it re-hashes after writing and fails if the bytes are not the ones asked for — `cp`
# and `git cat-file` are not assumed to have succeeded because they printed nothing.
f1_restore_attester() {                   # <want-sha256> <blob>
  _want=$1; _blob=$2
  [ "$(sha_or_missing "$A")" = "$_want" ] && return 0
  git cat-file blob "$_blob" > "$A.t161-restore" || {
    rm -f "$A.t161-restore"; return 1; }
  mv -f "$A.t161-restore" "$A" || { rm -f "$A.t161-restore"; return 1; }
  [ "$(sha_or_missing "$A")" = "$_want" ] || return 1
  return 0
}

# Remove the two things a PRE-FIX attester run leaves inside the COMMITTED evidence set.
# Restoring the attester and leaving a forged-looking stamp behind is a half fix, so this
# runs on every path the attester restore runs on.  IDEMPOTENT.
f1_clean_evidence() {
  if [ -e "$STAMP" ]; then
    rm -f "$STAMP" && echo "guard: removed the stray CAPTURED-FROM-TENANT stamp from t36/out/emiloop" >&2
  fi
  if [ -n "$(git status --porcelain -- "$E" 2>/dev/null)" ]; then
    git checkout -- "$E" \
      && echo "guard: restored the committed evidence set t36/out/emiloop from git" >&2 \
      || echo "guard: COULD NOT restore t36/out/emiloop — run: git checkout -- $E" >&2
  fi
}

# --- START-UP RECOVERY.  SIGKILL runs no handler; this is the only place that hole can be
# --- closed.  It runs BEFORE anything else this script does, including the BEFORE census,
# --- because a census taken over a corrupted evidence set would enshrine the corruption as
# --- the baseline and the proof would then "pass" against it.
if [ -f "$GUARD" ]; then
  g_blob=$(sed -n 's/^blob //p' "$GUARD" | head -1)
  g_sha=$(sed -n 's/^sha256 //p' "$GUARD" | head -1)
  case "${g_blob:-}" in ''|*[!0-9a-f]*) fail "in-flight marker $GUARD is unreadable (blob='${g_blob:-}') — repair $REL_A by hand before re-running" ;; esac
  case "${g_sha:-}"  in ''|*[!0-9a-f]*) fail "in-flight marker $GUARD is unreadable (sha256='${g_sha:-}') — repair $REL_A by hand before re-running" ;; esac
  git cat-file -e "$g_blob" 2>/dev/null \
    || fail "in-flight marker names blob $g_blob, which is not in this repository's object store — repair $REL_A by hand"
  git cat-file blob "$g_blob" > "$T80/.f1-blobcheck" \
    || fail "cannot read blob $g_blob"
  if [ "$(sha_or_missing "$T80/.f1-blobcheck")" != "$g_sha" ]; then
    rm -f "$T80/.f1-blobcheck"
    fail "blob $g_blob does not hash to the $g_sha recorded in $GUARD — refusing to restore bytes I cannot identify"
  fi
  rm -f "$T80/.f1-blobcheck"
  found=$(sha_or_missing "$A")
  if [ "$found" = "$g_sha" ]; then
    echo "note: an in-flight marker from an earlier run was found; $REL_A is already at the recorded bytes ($g_sha) — nothing to restore"
  else
    f1_restore_attester "$g_sha" "$g_blob" \
      || fail "an earlier run left $REL_A at $found and it could NOT be restored — run: git cat-file blob $g_blob > $A"
    echo "RECOVERED: an earlier run died mid-swap and left $REL_A at $found; restored to $g_sha from blob $g_blob"
  fi
  f1_clean_evidence
  rm -f "$GUARD" "$A.t161-restore" "$T80/.f1-blobcheck" \
        "$O"/.f1-before "$O"/.f1-after-prefix "$O"/.f1-restored \
        "$O"/.f1-after-fixed "$O"/.f1-fixed "$O"/.f1-out1 "$O"/.f1-out2
fi

echo "=== T85 F-1 — a breached attest.py run must write NOTHING"
echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "victim set: t36/out/emiloop  (11 EL-* captures taken on tenant gerege, plus attestation and transcripts)"
echo

# The census the guard compares against is held in a SHELL VARIABLE as well as in the file
# under `out/`: the file is for the reader, the variable is what the trap trusts, because
# the trap must still work when `out/` has been removed underneath it.  An EMPTY census is
# a refusal, never a silently-satisfied comparison (P-40).
CENSUS_BEFORE=$(snap)
CENSUS_N=$(printf '%s\n' "$CENSUS_BEFORE" | grep -c '.')
[ "${CENSUS_N:-0}" -gt 0 ] \
  || fail "the census over $E is EMPTY — refusing, because 'restored' over nothing is not a fact"
printf '%s\n' "$CENSUS_BEFORE" > "$O/.f1-before"
echo "--- BEFORE: $CENSUS_N files"
grep 'preconditions.txt' "$O/.f1-before"
echo "  stamp present: $( [ -f "$STAMP" ] && echo yes || echo no )"
echo

# ---------------------------------------------------------------- 1. the PRE-FIX behaviour
# Pin the LIVE attester into git's IMMUTABLE object store before a single byte is written
# over it.  Preference order: the blob already in the index (the ordinary case — no new
# object is created), else a new blob written from the working-tree bytes, so that a
# locally-modified attester is preserved exactly rather than reverted to the index.
A_SHA=$(sha_or_missing "$A")
[ "$A_SHA" = MISSING ] && fail "$REL_A is missing or unreadable — nothing to pin, refusing to overwrite it"
A_BLOB=$(git rev-parse --verify --quiet ":$REL_A" 2>/dev/null) || A_BLOB=''
if [ -n "$A_BLOB" ]; then
  git cat-file blob "$A_BLOB" > "$T80/.f1-blobcheck" 2>/dev/null || : > "$T80/.f1-blobcheck"
  [ "$(sha_or_missing "$T80/.f1-blobcheck")" = "$A_SHA" ] || A_BLOB=''
  rm -f "$T80/.f1-blobcheck"
fi
if [ -z "$A_BLOB" ]; then
  A_BLOB=$(git hash-object -w -- "$A") \
    || fail "could not pin the live $REL_A into the git object store"
  echo "note: $REL_A differs from the index; its working-tree bytes were pinned as a new blob"
fi
git cat-file blob "$A_BLOB" > "$T80/.f1-blobcheck" || fail "cannot read the pin blob $A_BLOB"
[ "$(sha_or_missing "$T80/.f1-blobcheck")" = "$A_SHA" ] \
  || { rm -f "$T80/.f1-blobcheck"; fail "the pin blob $A_BLOB does not hash to $A_SHA — refusing to open the window"; }
rm -f "$T80/.f1-blobcheck"

# The marker is written BEFORE the traps are armed and BEFORE the overwrite, because the
# only state that cannot be recovered is one that was never recorded.
printf 'blob %s\nsha256 %s\npath %s\nopened %s\npid %s\n' \
  "$A_BLOB" "$A_SHA" "$REL_A" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$$" > "$GUARD" \
  || fail "could not write the in-flight marker $GUARD"
echo "guard: pinned $REL_A at sha256 $A_SHA as immutable blob $A_BLOB; marker $GUARD"

f1_guard_exit() {
  _st=$?
  # Never re-enter, whatever the handler itself does or receives.
  trap - EXIT INT TERM HUP QUIT PIPE
  _rc=$_st
  # If the pre-fix attester is STILL RUNNING, stop it first: a child that outlives the
  # handler would re-create the stamp after the restore had removed it.  STATED LIMIT:
  # `wait` reaps the DIRECT child only.  A writer this handler did not spawn — or a
  # DESCENDANT of the attester that outlived it — can still dirty t36/out/emiloop after
  # the cleanup, and no handler can prevent that.  What is guaranteed is that the census
  # below DETECTS it, names the files and exits non-zero; it is never silent.  Measured:
  # `out/F1-recovery-descendant-race.txt`.  In the real invocation there is no such
  # descendant — attest.py writes the stamp and the transcript itself, in process, and
  # preconditions.sh writes nothing under out/emiloop [VERIFIED: grep 'emiloop'
  # t36/preconditions.sh -> no match].
  if [ -n "${ATTEST_PID:-}" ]; then
    kill -TERM "$ATTEST_PID" 2>/dev/null
    wait "$ATTEST_PID" 2>/dev/null
  fi
  _cur=$(sha_or_missing "$A")
  if [ "$_cur" = "$A_SHA" ]; then
    echo "guard: $REL_A is at its pre-run bytes ($A_SHA)" >&2
  else
    echo "guard: $REL_A is NOT at its pre-run bytes (found $_cur) — restoring from blob $A_BLOB" >&2
    if f1_restore_attester "$A_SHA" "$A_BLOB"; then
      echo "guard: RESTORED $REL_A from blob $A_BLOB; sha256 re-read and VERIFIED as $A_SHA" >&2
    else
      echo "guard: RESTORE FAILED for $REL_A. REPAIR BY HAND: git cat-file blob $A_BLOB > $A" >&2
      _rc=1
    fi
  fi
  f1_clean_evidence
  _after=$(snap)
  if [ "$_after" = "$CENSUS_BEFORE" ]; then
    echo "guard: evidence set restored — $CENSUS_N files, census identical to the pre-run census" >&2
  else
    echo "guard: EVIDENCE SET NOT RESTORED — t36/out/emiloop differs from the pre-run census." >&2
    _tb=$(mktemp); _ta=$(mktemp)
    printf '%s\n' "$CENSUS_BEFORE" > "$_tb"
    printf '%s\n' "$_after"        > "$_ta"
    diff "$_tb" "$_ta" >&2
    rm -f "$_tb" "$_ta"
    _rc=1
  fi
  rm -f "$GUARD" "$A.t161-restore" "$T80/.f1-blobcheck" \
        "$O"/.f1-before "$O"/.f1-after-prefix "$O"/.f1-restored \
        "$O"/.f1-after-fixed "$O"/.f1-fixed "$O"/.f1-out1 "$O"/.f1-out2
  exit "$_rc"
}
# EXIT covers the ordinary paths AND every `fail`/`exit` inside the window — the script
# carries no `set -e`, so before this trap existed an error exit between the overwrite and
# the undo left the downgraded attester behind exactly as a signal did.
trap f1_guard_exit EXIT
# A signal handler that RETURNED would resume the proof mid-flight with pre-fix bytes on
# disk, so each of these exits with the conventional 128+signo, which fires EXIT above.
#   INT  — a terminal Ctrl-C, the overwhelmingly likely interruption.
#   TERM — `kill <pid>`, a supervisor, a shell teardown.
#   HUP  — the terminal or ssh session closed.
#   QUIT — Ctrl-\ at a terminal.  T161 DECISION: covered, although the task's list stopped
#          at HUP and the sibling defect in `t149/prove-redgreen.sh` is T168's (whose files
#          are not touched here).  SIGQUIT is catchable, it is producible by a single
#          keystroke from the same terminal that produces SIGINT, and the state it strands
#          is byte-for-byte the state SIGINT strands.  Omitting it would leave a hole whose
#          only distinguishing feature is which key the operator hit.
#   PIPE  — T161 addition, not in the task's list either, and NOT hypothetical: running
#          this proof as `sh prove-f1.sh | head` closes the pipe mid-run and kills the
#          script with SIGPIPE inside the window.  Reading a proof's output through `head`
#          must not downgrade the attester it is proving.
trap 'echo "INTERRUPTED (SIGINT) — restoring the rig" >&2;  exit 130' INT
trap 'echo "INTERRUPTED (SIGTERM) — restoring the rig" >&2; exit 143' TERM
trap 'echo "INTERRUPTED (SIGHUP) — restoring the rig" >&2;  exit 129' HUP
trap 'echo "INTERRUPTED (SIGQUIT) — restoring the rig" >&2; exit 131' QUIT
trap 'echo "INTERRUPTED (SIGPIPE) — restoring the rig" >&2; exit 141' PIPE

git show "$PREFIX_COMMIT:$REL_A" > "$A" || fail "could not read the pre-fix attest.py from $PREFIX_COMMIT"
got=$(sha_or_missing "$A")
[ "$got" = "$PREFIX_SHA256" ] \
  || fail "the bytes written from $PREFIX_COMMIT hash to $got, not the pinned $PREFIX_SHA256 (blob $PREFIX_BLOB) — this proof will not test bytes it cannot identify"
echo "--- 1. PRE-FIX attest.py ($PREFIX_COMMIT, blob $PREFIX_BLOB, sha256 $PREFIX_SHA256)"
echo "    invocation: python3 t36/attest.py default emiloop"
# Backgrounded and `wait`ed rather than run in the foreground: a shell defers a trapped
# signal until the current FOREGROUND child finishes, so a `kill` arriving while the
# attester ran would not restore the rig until the attester chose to end — and never at all
# if it hung on a docker exec.  `wait` is interruptible, so the trap fires at once, and it
# yields the child's status, which is exactly the foreground semantics this line had.
python3 t36/attest.py default emiloop > "$O/.f1-out1" 2>&1 &
ATTEST_PID=$!
wait "$ATTEST_PID"
st1=$?
ATTEST_PID=''
echo "EXIT=$st1"
tail -2 "$O/.f1-out1" | sed 's/^/  /'
snap > "$O/.f1-after-prefix"
echo "  stamp now present: $( [ -f "$STAMP" ] && echo "YES, contents: $(cat "$STAMP")" || echo no )"
if diff -q "$O/.f1-before" "$O/.f1-after-prefix" > /dev/null; then
  echo "  RESULT: committed set UNCHANGED (unexpected — the defect did not reproduce)"
  prefix_broke=0
else
  echo "  RESULT: COMMITTED SET MUTATED BY A RUN THAT SAID IT WROTE NOTHING:"
  diff "$O/.f1-before" "$O/.f1-after-prefix" | sed 's/^/    /'
  echo "    transcript first line is now: $(head -1 "$E/preconditions.txt")"
  prefix_broke=1
fi
echo

# ------------------------------------------------------------------- restore the evidence
# The same two idempotent, verifying helpers the trap uses.  There is exactly ONE recovery
# idiom in this file; the in-run path is not a second one.
f1_restore_attester "$A_SHA" "$A_BLOB" \
  || fail "could not restore $REL_A to $A_SHA from blob $A_BLOB — DO NOT COMMIT until it is back"
f1_clean_evidence
snap > "$O/.f1-restored"
if diff -q "$O/.f1-before" "$O/.f1-restored" > /dev/null; then
  echo "--- evidence restored from git: all digests back to BEFORE, and $REL_A is back at $A_SHA"
else
  echo "--- WARNING: restore incomplete"; diff "$O/.f1-before" "$O/.f1-restored"
fi
echo

# ------------------------------------------------------------------ 2. the FIXED behaviour
echo "--- 2. FIXED attest.py, same invocation: python3 t36/attest.py default emiloop"
python3 t36/attest.py default emiloop > "$O/.f1-out2" 2>&1 &
ATTEST_PID=$!
wait "$ATTEST_PID"
st2=$?
ATTEST_PID=''
echo "EXIT=$st2"
tail -2 "$O/.f1-out2" | sed 's/^/  /'
snap > "$O/.f1-after-fixed"
echo "  stamp present: $( [ -f "$STAMP" ] && echo "YES — FIX FAILED, contents: $(cat "$STAMP")" || echo "no" )"
rc=0
if diff -q "$O/.f1-before" "$O/.f1-after-fixed" > /dev/null; then
  echo "  RESULT: committed set UNCHANGED — all $CENSUS_N digests identical, including preconditions.txt"
else
  echo "  RESULT: STILL MUTATING:"; diff "$O/.f1-before" "$O/.f1-after-fixed"; rc=1
fi
[ -f "$STAMP" ] && rc=1
echo
echo "prefix-defect-reproduced=$prefix_broke   fixed-run-clean=$( [ "$rc" = 0 ] && echo yes || echo no )"
# The dotfiles and the in-flight marker are removed by the EXIT trap, on this path and on
# every other one, so there is no cleanup line here that an interruption could skip.
[ "$rc" = 0 ] || exit 1
[ "$prefix_broke" = 1 ] || exit 1
echo "RESULT: F-1 CLOSED — the defect reproduces on the pre-fix file and is absent after the fix."
exit 0
