#!/bin/sh
# T99 — shared setup for the four proofs.  Sourced, never executed.
#
# EVERY PROOF RUNS BOTH SIDES.  T85 forced this lesson on T80: a proof that shows only the "after"
# cannot tell a fix from a no-op.  So each prove-f*.sh materialises TWO trees from git —
#   prefix/  = `git archive <PREFIX_REF>` , the bytes the defect was found in
#   fixed/   = `git archive HEAD`         , this branch
# — and runs the same attack against both.  A proof exits non-zero unless the defect REPRODUCES on
# prefix AND is REFUSED on fixed; "both refused" would mean the demonstration is not demonstrating
# anything, and it fails just as loudly as "both admitted".
#
# Destructive work happens only inside the export under /tmp (T85's hygiene).  Nothing here writes
# into the repository, and no proof needs a dirty worktree.
#
# The pre-fix files are pinned by digest below, so a reader can confirm the "before" side really is
# main's bytes and not a convenient rewrite of them.

set -u

T99=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$T99" rev-parse --show-toplevel)
EXPORT=${T99_EXPORT_ROOT:-/tmp/t99-proof}
PB=.softhouse/capture/pathb

# ------------------------------------------------------------------ THE PRE-FIX BASELINE (T152)
# THE BASELINE IS A LITERAL SHA READ FROM `FORK-POINT-SHA`.  NOT `main:`.  NOT
# `merge-base main HEAD`.  NOT ANY COMPUTED REF.  There is deliberately NO COMPUTED FALLBACK.
#
# This line used to read `PREFIX_REF=${T99_PREFIX_REF:-$(git -C "$T99" merge-base main HEAD)}`,
# with a comment claiming it named "the fork point, not the moving branch".  It does — ON THIS
# BRANCH, which is the one state in which the defect is invisible.  On merged `main`, HEAD == main,
# so `merge-base main HEAD` is THE MERGE COMMIT ITSELF and the "before" tree contains the fix.
# That is the third occurrence in this program (v1 `main:`, v2 T98, v3 here), and T135 MEASURED it
# on a scratch merge into current `main`: f1/f2/f3 abort exit 3 on their digest pins, and
# **prove-f4 exits 1 reporting "F-4 NOT CLOSED"**, because prove-f4 has no digest pin to protect
# it.  The full history and the measurement are in FORK-POINT-SHA's header.
#
# The digest pins below remain the second operand: even with the right ref, if the exported bytes
# are not the bytes the defect was found in, the proof aborts rather than concluding.
t99_read_fork_point() {
  _f=$T99/FORK-POINT-SHA
  if [ ! -f "$_f" ]; then
    printf 'T99 PROOF ABORT: %s is missing.\n' "$_f" >&2
    printf '  The proof baseline is a LITERAL sha and this rig has NO computed fallback:\n' >&2
    printf '  `main:`, `merge-base main HEAD` and every other ref computed from `main` resolve to\n' >&2
    printf '  code that CONTAINS THE FIX once this branch is merged.  Restore the file; do not\n' >&2
    printf '  substitute a computed ref.  See T102 (which closed this the second time) and T135.\n' >&2
    exit 3
  fi
  _sha=$(LC_ALL=C grep -vE '^[[:space:]]*(#|$)' "$_f" | tail -n 1 | tr -d '[:space:]')
  case "$_sha" in
    *[!0-9a-f]* | "")
      printf 'T99 PROOF ABORT: %s does not contain a 40-hex commit sha (read: %s).\n' "$_f" "'$_sha'" >&2
      printf '  Refusing to guess a baseline.  See T102.\n' >&2
      exit 3 ;;
  esac
  if [ "$(printf '%s' "$_sha" | wc -c | tr -d ' ')" -ne 40 ]; then
    printf 'T99 PROOF ABORT: %s must hold a FULL 40-hex sha; got %s chars.\n' "$_f" \
      "$(printf '%s' "$_sha" | wc -c | tr -d ' ')" >&2
    printf '  An abbreviated sha can become ambiguous as the repository grows.  See T102.\n' >&2
    exit 3
  fi
  if ! git -C "$REPO" cat-file -e "$_sha^{commit}" 2>/dev/null; then
    printf 'T99 PROOF ABORT: %s is not a commit in this repository.\n' "$_sha" >&2
    printf '  The pinned fork point must be reachable to extract the pre-fix bytes.  See T102.\n' >&2
    exit 3
  fi
  printf '%s' "$_sha"
}

# T99_PREFIX_REF is retained as a RESEARCH override — prove-f4's 4a precondition was driven red
# against `T99_PREFIX_REF=352f623` — but it is announced in the transcript as an override, because a
# baseline supplied by the runner is not a proof (the same argument that makes an environment-
# supplied CANARY_EXPECT a defect).  Unset, the baseline is the literal above and nothing else.
if [ -n "${T99_PREFIX_REF:-}" ]; then
  PREFIX_REF=$T99_PREFIX_REF
  PREFIX_SOURCE="T99_PREFIX_REF OVERRIDE — a runner-supplied baseline; this run is a research probe, not a proof"
else
  PREFIX_REF=$(t99_read_fork_point) || exit 3
  PREFIX_SOURCE="literal 40-hex sha from t99/FORK-POINT-SHA — NOT a ref computed from \`main\` (T102/T135)"
fi

# sha256 of each PRE-FIX file as committed on main d0ef08d, computed with the hardened instrument.
PIN_PREFIX_RECAPTURE=efccb0a4323628b45952a7e2dff12590e7dce3a2705ae66aa73aa53cd3b0d7d7
PIN_PREFIX_PRECOND=7c68f2dcc539a27648f2fb0623927c1231c9b3729bdfb77eb01bd90e67ae876b
PIN_PREFIX_FORBIDDEN=71142e40b4af9ec873f0eca6a3ecb60d18033f2f0d37f75a2b29ffc4b9bf798f
PIN_PREFIX_ATTEST=0edced54a750fa17981af5a287b413c1a8298680ce2b7d4952087a14e61ce780

. "$REPO/$PB/t36/sha256.sh"

t99_die() { printf 'T99 PROOF ABORT: %s\n' "$1" >&2; exit 3; }

t99_export() {
  rm -rf "$EXPORT"
  mkdir -p "$EXPORT/prefix" "$EXPORT/fixed" "$EXPORT/stub" "$EXPORT/poison" || t99_die "cannot create $EXPORT"
  git -C "$REPO" archive "$PREFIX_REF" | tar -x -C "$EXPORT/prefix" || t99_die "git archive $PREFIX_REF failed"
  git -C "$REPO" archive HEAD          | tar -x -C "$EXPORT/fixed"  || t99_die "git archive HEAD failed"
  P=$EXPORT/prefix/$PB
  F=$EXPORT/fixed/$PB
  echo "prefix ref:  $PREFIX_REF = $(git -C "$REPO" rev-parse "$PREFIX_REF")"
  # T152: run-all.sh normalises the line above to <PREFIX-COMMIT>, so a reader of the transcript
  # cannot see WHICH commit it was — and could not see, therefore, whether it was pinned or
  # computed.  That is precisely the ambiguity in which the moving-baseline bug survived twice
  # (T98 reported "the immutable fork point 8da4b83" and was believed).  Say where it came from.
  echo "baseline:    $PREFIX_SOURCE"
  echo "fixed ref:   HEAD = $(git -C "$REPO" rev-parse HEAD)"
  echo "export:      $EXPORT   (git archive, so nothing uncommitted can leak into a proof)"
  sha256_init || t99_die "no trustworthy sha256 instrument: $SHA256_ERROR"
}

# t99_pin <file> <pinned digest> <label> — a reader must be able to see the "before" is really main.
t99_pin() {
  sha256_file "$1" || t99_die "cannot digest $1: $SHA256_ERROR"
  if [ "$SHA256_RESULT" = "$2" ]; then
    echo "pre-fix $3 sha256 $SHA256_RESULT — matches the pin, this IS main's byte sequence"
  else
    echo "pre-fix $3 sha256 $SHA256_RESULT — DOES NOT MATCH the pinned $2"
    t99_die "the pre-fix $3 in the export is not the file the defect was found in"
  fi
}

# Hermetic doubles: refuse every call, so a guard-only proof never touches the shared oracle.
t99_stubs() {
  for t in docker curl; do
    cat > "$EXPORT/stub/$t" <<EOF
#!/bin/sh
echo "STUB $t: refusing (T99 hermetic proof; the shared reference oracle is untouched)" >&2
exit 1
EOF
    chmod +x "$EXPORT/stub/$t"
  done
}

t99_verdict() {   # <prefix-admitted 0|1> <fixed-refused 0|1> <label>
  echo
  echo "defect reproduces on the PRE-FIX bytes: $( [ "$1" = 1 ] && echo YES || echo 'NO — this proof proves nothing' )"
  echo "defect refused by the FIXED bytes:      $( [ "$2" = 1 ] && echo YES || echo 'NO — the fix does not work' )"
  if [ "$1" = 1 ] && [ "$2" = 1 ]; then
    echo "RESULT: $3 CLOSED — red before, green after."
    exit 0
  fi
  echo "RESULT: $3 NOT CLOSED."
  exit 1
}
