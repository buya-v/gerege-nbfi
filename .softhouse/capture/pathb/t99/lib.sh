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
# The fork point, not the moving branch: `main` advances under a running fire, and a proof whose
# "before" changes underneath it proves nothing reproducible.  The digest pins below are the second
# operand — if the pre-fix bytes are ever not the bytes the defect was found in, the proof aborts.
PREFIX_REF=${T99_PREFIX_REF:-$(git -C "$T99" merge-base main HEAD)}
EXPORT=${T99_EXPORT_ROOT:-/tmp/t99-proof}
PB=.softhouse/capture/pathb

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
