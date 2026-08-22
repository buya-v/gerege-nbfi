#!/bin/sh
# T80 — proof for T85 F-1: a BREACHED attest.py run must leave the filesystem exactly as it found it.
#
# T85 showed that `python3 attest.py default emiloop` printed "no capture attempted, no attestation
# written" while having already stamped eleven `gerege` captures as `default` and replaced their
# HALF_UP precondition transcript with a breached HALF_EVEN one.  The emiloop set is the reachable
# victim because it is exempt from the directory-NAME check (its committed directory is `out/emiloop`,
# which cannot end in a tenant id without renaming committed evidence).
#
# This script runs the SAME invocation twice — once with the PRE-FIX attest.py, once with the fixed
# one — and diffs the digests of the committed set each time.  A proof that only shows the "after"
# cannot tell a fix from a no-op.
#
# =====================================================================================
# T180 — THE LIVE ATTESTER IS NOT OVERWRITTEN AT ALL ANY MORE.
#
# HISTORY, because the shape only makes sense with it.
#   * Until T161 this script wrote PRE-FIX BYTES OVER THE LIVE `t36/attest.py`, ran them,
#     and only then undid it, with NO trap anywhere in the file.  Any interruption inside
#     that window left the attester that mislabelled eleven captures sitting in the tree
#     wearing the name of the current one — and `t36/attest.py` is on the ENFORCED
#     PRECONDITION PATH (`preconditions.sh` breach -> `attest.py` abort) that this program
#     cites as the thing standing between a fabricated capture and the corpus.
#   * T161 made that window RECOVERABLE on every interruption path: traps, a verified and
#     idempotent restore from an immutable git blob, and start-up recovery for SIGKILL.
#   * T161 then MEASURED that the window need not exist at all, and recorded the evidence in
#     `out/F1-sibling-scratch-alternative.txt`.  T180 adopts it.
#
# WHY A SIBLING FILE AND NOT A SCRATCH PATH.  T158 proposed running the pre-fix bytes "from a
# scratch path, the way prove-f2.sh already does".  That is a NULL CONTROL (P-36) for THIS
# file, because `attest.py` derives everything from its OWN directory:
#
#     HERE  = os.path.dirname(os.path.abspath(__file__))
#     PATHB = HERE/..
#     OUT   = HERE/out/<capture-set>          # and it then GATES on the SHAPE of OUT
#
# so a copy under `t80/out/` moves HERE and trips the very guard under test before the defect
# can reproduce.  A SIBLING FILE IN THE SAME DIRECTORY — `t36/.f1-prefix-attest.py` — leaves
# HERE, PATHB and OUT identical, and the filename itself is read nowhere
# [VERIFIED: the only self-reference in the pre-fix file is `__file__` at line 34, consumed as
# a DIRECTORY; `'generator': 't36/attest.py'` at line 360 is a literal that is only written on
# a SUCCESSFUL run, and this invocation aborts].  The defect reproduces exactly, and the live
# attester is never opened for writing.
#
# WHAT THIS RETIRES, AND WHAT IT DOES NOT — read this before deleting anything.
#   RETIRED: the overwrite of `t36/attest.py`; the git-blob pin of the live attester
#            (this proof no longer writes into the repository's object store at all); the
#            in-run and on-exit RESTORE of the live attester.
#   NOT RETIRED — and a handoff that says otherwise is wrong: the pre-fix attester still
#            MUTATES THE COMMITTED EVIDENCE SET `t36/out/emiloop` whichever file it is run
#            from — it writes `CAPTURED-FROM-TENANT` and replaces `preconditions.txt` with a
#            breached HALF_EVEN one.  So the traps, `f1_clean_evidence`, the BEFORE/AFTER
#            census and the start-up recovery all stay.  This change REDUCES BLAST RADIUS; it
#            does not retire the recovery.
#   ALSO KEPT: the LEGACY start-up recovery branch, for a tree stranded by the OLD
#            overwrite-shaped script (marker with a `blob` line).  It is not dead code — it is
#            driven in `out/F1-noswap-redgreen.txt`.
#
# THE INVARIANT IS NOW ASSERTED, NOT MERELY INTENDED.  `f1_assert_attester_untouched` re-reads
# the live attester's sha256 after the pre-fix run and again on exit and FAILS if it moved.  It
# does NOT restore: this script no longer writes that file, so bytes that moved are somebody
# else's and silently reverting them would hide the fact.  The check is driven red in the
# ablation arm of `prove-f1-noswap.py`, which puts the overwrite back and watches it fire.
# =====================================================================================
set -u
T80=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T80/.." && pwd)
O=$T80/out
E=$W/t36/out/emiloop
A=$W/t36/attest.py                        # the LIVE rig file — WATCHED, never written
REPO=$(cd "$W/../../.." && pwd)
REL_A=.softhouse/capture/pathb/t36/attest.py
# T180: the pre-fix bytes are run from HERE — a sibling of the live attester, in the SAME
# directory, so HERE/PATHB/OUT are identical and the guard under test is the real one.
SIB=$W/t36/.f1-prefix-attest.py
REL_SIB=.softhouse/capture/pathb/t36/.f1-prefix-attest.py
STAMP=$E/CAPTURED-FROM-TENANT
GUARD=$T80/.f1-swap-in-progress           # in-flight marker.  It lives OUTSIDE `out/` so a
                                          # cleanup of the output directory cannot take it.
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

# ------------------------------------------------------------- T180: the invariant, asserted
# The live attester must hash to what it hashed at start-up, because this proof never writes
# it.  Deliberately NOT a restore: a mismatch means bytes this script did not put there, and
# quietly reverting them would destroy the evidence of whoever did.
f1_assert_attester_untouched() {          # <where>
  _cur=$(sha_or_missing "$A")
  [ "$_cur" = "$A_SHA" ] && return 0
  echo "guard: INVARIANT VIOLATED at $1 — $REL_A is at $_cur, not the $A_SHA it had at start-up." >&2
  echo "guard: THIS PROOF NEVER WRITES THAT FILE (T180): the pre-fix bytes go to $REL_SIB." >&2
  echo "guard: refusing to guess whose bytes those are. Inspect, then: git checkout -- $REL_A" >&2
  return 1
}

# Remove the scratch sibling.  IDEMPOTENT, so it can run from start-up recovery, from the
# middle of the run and again from the EXIT trap.
f1_remove_sibling() {
  if [ -e "$SIB" ]; then
    if rm -f "$SIB"; then echo "guard: removed the scratch sibling attester $REL_SIB" >&2
    else echo "guard: COULD NOT remove $SIB — remove it by hand" >&2; return 1; fi
  fi
  return 0
}

# ------------------------------------------------- LEGACY (pre-T180) attester restore
# Put the attester back at <sha256> from immutable blob <blob>.  IDEMPOTENT and VERIFIED: it
# re-hashes after writing and fails if the bytes are not the ones asked for — `git cat-file`
# is not assumed to have succeeded because it printed nothing.
#
# Reached ONLY from the legacy branch of start-up recovery, i.e. when a tree was stranded by
# the OLD overwrite-shaped script (T161 and earlier) and this newer script is the next to run.
# Nothing on the normal path calls it, because nothing on the normal path writes $A.
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
# STILL NEEDED AFTER T180: the evidence set is mutated whichever file the pre-fix bytes are
# run from.  IDEMPOTENT.
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
# --- Two marker formats are understood: the T180 one (`sibling` line) and the LEGACY
# --- overwrite-shaped one (`blob` line), so upgrading this script cannot strand a tree that
# --- the previous version left mid-swap.
if [ -f "$GUARD" ]; then
  g_blob=$(sed -n 's/^blob //p' "$GUARD" | head -1)
  g_sha=$(sed -n 's/^sha256 //p' "$GUARD" | head -1)
  g_sib=$(sed -n 's/^sibling //p' "$GUARD" | head -1)
  g_watch=$(sed -n 's/^watch-sha256 //p' "$GUARD" | head -1)
  if [ -n "${g_blob:-}" ]; then
    # ---- LEGACY: a run of the OLD overwrite-shaped script died mid-swap.
    case "${g_blob:-}" in *[!0-9a-f]*) fail "in-flight marker $GUARD is unreadable (blob='${g_blob:-}') — repair $REL_A by hand before re-running" ;; esac
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
      echo "note: a LEGACY in-flight marker from an earlier (overwrite-shaped) run was found; $REL_A is already at the recorded bytes ($g_sha) — nothing to restore"
    else
      f1_restore_attester "$g_sha" "$g_blob" \
        || fail "an earlier run left $REL_A at $found and it could NOT be restored — run: git cat-file blob $g_blob > $A"
      echo "RECOVERED: a LEGACY (pre-T180, overwrite-shaped) run died mid-swap and left $REL_A at $found; restored to $g_sha from blob $g_blob"
    fi
  elif [ -n "${g_sib:-}" ]; then
    # ---- T180: the live attester was never written, so there is nothing to restore there.
    # ---- What an interrupted run CAN leave is the scratch sibling and the mutated evidence.
    [ "$g_sib" = "$REL_SIB" ] \
      || fail "in-flight marker $GUARD names sibling '$g_sib', not '$REL_SIB' — refusing to clean a path I do not recognise"
    case "${g_watch:-}" in ''|*[!0-9a-f]*) fail "in-flight marker $GUARD is unreadable (watch-sha256='${g_watch:-}')" ;; esac
    cur=$(sha_or_missing "$A")
    if [ "$cur" = "$g_watch" ]; then
      echo "RECOVERED: an earlier run died before it could clean up; $REL_A is UNTOUCHED at $cur, as this shape guarantees — only the scratch sibling and the evidence set need clearing"
    else
      echo "RECOVERED: an earlier run died before it could clean up. WARNING: $REL_A is at $cur, not the $g_watch that run recorded — THIS PROOF DOES NOT WRITE THAT FILE, so something else changed it. Not restoring bytes it did not put there; investigate before trusting an attestation."
    fi
    f1_remove_sibling
  else
    fail "in-flight marker $GUARD carries neither a 'blob' (legacy) nor a 'sibling' (T180) line — refusing to act on a marker I cannot read"
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
# T180: record — do not pin, do not copy, do not hash-object — the live attester's digest.
# Nothing below writes $A, so there is nothing to restore it FROM; what is needed is a
# baseline to ASSERT against.  A git blob pin here would be a backup for a write that no
# longer happens, and an unreachable restore path is a control that cannot fail (P-22).
A_SHA=$(sha_or_missing "$A")
[ "$A_SHA" = MISSING ] \
  && fail "$REL_A is missing or unreadable — refusing to run a proof about an attester that is not there"
[ -e "$SIB" ] \
  && fail "$REL_SIB already exists — refusing to overwrite a scratch file this proof did not create; inspect it, remove it, and re-run"

# The marker is written BEFORE the traps are armed and BEFORE the sibling is created, because
# the only state that cannot be recovered is one that was never recorded.
printf 'sibling %s\nwatch-sha256 %s\npath %s\nopened %s\npid %s\n' \
  "$REL_SIB" "$A_SHA" "$REL_A" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$$" > "$GUARD" \
  || fail "could not write the in-flight marker $GUARD"
echo "guard: WATCHING $REL_A at sha256 $A_SHA — it is never written by this proof (T180)"
echo "guard: the pre-fix bytes go to the SCRATCH SIBLING $REL_SIB; marker $GUARD"

f1_guard_exit() {
  _st=$?
  # Never re-enter, whatever the handler itself does or receives.
  trap - EXIT INT TERM HUP QUIT PIPE
  _rc=$_st
  # If the pre-fix attester is STILL RUNNING, stop it first: a child that outlives the
  # handler would re-create the stamp after the cleanup had removed it.  STATED LIMIT:
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
  if f1_assert_attester_untouched "exit"; then
    echo "guard: $REL_A is UNTOUCHED at $A_SHA — this proof no longer overwrites it (T180)" >&2
  else
    _rc=1
  fi
  f1_remove_sibling || _rc=1
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
# STILL REQUIRED AFTER T180 — the blast radius shrank, it did not vanish.  The pre-fix
# attester stamps `t36/out/emiloop/CAPTURED-FROM-TENANT` and replaces the committed
# `preconditions.txt` with a breached HALF_EVEN one WHICHEVER FILE IT IS RUN FROM, and an
# interruption between those writes and the cleanup would leave both behind, plus the
# scratch sibling.
# EXIT covers the ordinary paths AND every `fail`/`exit` inside the window — the script
# carries no `set -e`, so an error exit between the sibling's creation and its removal would
# otherwise leave the evidence set dirty exactly as a signal does.
trap f1_guard_exit EXIT
# A signal handler that RETURNED would resume the proof mid-flight, so each of these exits
# with the conventional 128+signo, which fires EXIT above.
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
#          must not leave a forged-looking stamp inside the committed evidence set.
trap 'echo "INTERRUPTED (SIGINT) — restoring the rig" >&2;  exit 130' INT
trap 'echo "INTERRUPTED (SIGTERM) — restoring the rig" >&2; exit 143' TERM
trap 'echo "INTERRUPTED (SIGHUP) — restoring the rig" >&2;  exit 129' HUP
trap 'echo "INTERRUPTED (SIGQUIT) — restoring the rig" >&2; exit 131' QUIT
trap 'echo "INTERRUPTED (SIGPIPE) — restoring the rig" >&2; exit 141' PIPE

git show "$PREFIX_COMMIT:$REL_A" > "$SIB" || fail "could not read the pre-fix attest.py from $PREFIX_COMMIT"
got=$(sha_or_missing "$SIB")
[ "$got" = "$PREFIX_SHA256" ] \
  || fail "the bytes written from $PREFIX_COMMIT hash to $got, not the pinned $PREFIX_SHA256 (blob $PREFIX_BLOB) — this proof will not test bytes it cannot identify"
echo "--- 1. PRE-FIX attest.py ($PREFIX_COMMIT, blob $PREFIX_BLOB, sha256 $PREFIX_SHA256)"
echo "    run from the SCRATCH SIBLING $REL_SIB — same directory, so HERE/PATHB/OUT and the"
echo "    directory-shape guard are identical; the live $REL_A is NOT touched"
echo "    invocation: python3 t36/.f1-prefix-attest.py default emiloop"
# Backgrounded and `wait`ed rather than run in the foreground: a shell defers a trapped
# signal until the current FOREGROUND child finishes, so a `kill` arriving while the
# attester ran would not clean the evidence set until the attester chose to end — and never
# at all if it hung on a docker exec.  `wait` is interruptible, so the trap fires at once,
# and it yields the child's status, which is exactly the foreground semantics this line had.
python3 "$SIB" default emiloop > "$O/.f1-out1" 2>&1 &
ATTEST_PID=$!
wait "$ATTEST_PID"
st1=$?
ATTEST_PID=''
echo "EXIT=$st1"
tail -2 "$O/.f1-out1" | sed 's/^/  /'
snap > "$O/.f1-after-prefix"
echo "  stamp now present: $( [ -f "$STAMP" ] && echo "YES, contents: $(cat "$STAMP")" || echo no )"
echo "  live $REL_A sha256: $(sha_or_missing "$A")"
f1_assert_attester_untouched "after the pre-fix run" \
  || fail "the live attester moved while the pre-fix bytes ran — the overwrite T180 removed is back, or something else wrote it"
echo "  ^^ unchanged from the start-up digest $A_SHA — the defect below was reproduced WITHOUT touching the live attester"
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

# ------------------------------------------------------------------- clean up after part 1
# The scratch sibling goes; the evidence set is restored from git.  The same two idempotent
# helpers the trap uses — there is exactly ONE cleanup idiom in this file.
f1_remove_sibling || fail "could not remove the scratch sibling $REL_SIB"
f1_clean_evidence
snap > "$O/.f1-restored"
if diff -q "$O/.f1-before" "$O/.f1-restored" > /dev/null; then
  echo "--- evidence restored from git: all digests back to BEFORE; the scratch sibling is gone"
  echo "    and $REL_A never moved off $A_SHA"
else
  echo "--- WARNING: restore incomplete"; diff "$O/.f1-before" "$O/.f1-restored"
fi
echo

# ------------------------------------------------------------------ 2. the FIXED behaviour
# This arm runs the LIVE attester, in place, read-only as far as this script is concerned.
echo "--- 2. FIXED attest.py ($REL_A, sha256 $A_SHA), same invocation: python3 t36/attest.py default emiloop"
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
echo "--- T180 invariant"
echo "  $REL_A  at start-up: $A_SHA"
echo "  $REL_A  now        : $(sha_or_missing "$A")"
f1_assert_attester_untouched "end of run" || rc=1
[ "$rc" = 0 ] && echo "  the live attester was never written by this proof, on either arm"
echo
echo "prefix-defect-reproduced=$prefix_broke   fixed-run-clean=$( [ "$rc" = 0 ] && echo yes || echo no )"
# The dotfiles, the scratch sibling and the in-flight marker are removed by the EXIT trap, on
# this path and on every other one, so there is no cleanup line here that an interruption
# could skip.
[ "$rc" = 0 ] || exit 1
[ "$prefix_broke" = 1 ] || exit 1
echo "RESULT: F-1 CLOSED — the defect reproduces on the pre-fix file and is absent after the fix,"
echo "        and the live attester was not overwritten at any point (T180)."
exit 0
