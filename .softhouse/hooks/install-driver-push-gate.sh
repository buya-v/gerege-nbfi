#!/usr/bin/env bash
# =============================================================================================
# INSTALLER FOR THE DRIVER PUSH GATE.  [T412]
#     bash .softhouse/hooks/install-driver-push-gate.sh [--status | --uninstall]
#
# WHY AN INSTALLER EXISTS AT ALL. This program has logged SEVEN guards built and wired to nothing
# (T399's census), and the pattern for it is P-45: a guard that only works when someone remembers
# to run it enforces nothing. A `pre-push` hook that ships as a file in `.softhouse/hooks/` and is
# never copied into `$(git rev-parse --git-common-dir)/hooks/` is precisely that defect, so
# INSTALLING IS PART OF THE DELIVERABLE and this script is how it is done and re-done.
#
# WHY A SHIM AND A SNAPSHOT, RATHER THAN A COPY OR A SYMLINK.
#   * A COPY of the gate into the hooks directory rots the moment the tracked file is edited, and
#     the rotted copy is the one that runs. Rejected.
#   * A SYMLINK into the tracked file cannot work before this branch merges: `main`'s checkout has
#     no such file yet, so the hook would be broken during exactly the window it is needed.
#   * So: a SHIM that prefers the tracked file in the main checkout and falls back to a SNAPSHOT
#     taken at install time. The shim prints which one it used and that file's sha256 on every
#     run, the same identity discipline `.softhouse/bin/fire-program.sh` already prints for
#     itself at every fire start.
#
# THE HOOKS DIRECTORY IS SHARED ACROSS EVERY WORKTREE (`core.hooksPath` is unset at every level
# and `$(git rev-parse --git-common-dir)` is one directory for all of them), so this hook fires
# for worker pushes too. That is why the gate's first act is to stand aside for any ref that is
# not `refs/heads/main`: 35 `softhouse/*` heads exist on origin and must keep pushing.
#
# T336 MEASURED THAT THE AGENT HARNESS SUPPRESSES HOOKS AT WORKTREE SPAWN -- neither
# `post-checkout` nor `reference-transaction` fires for an `Agent`-tool worktree creation. THAT
# MEASUREMENT DOES NOT APPLY HERE and the difference is the whole reason this gate can work: the
# same T336 evidence records that BOTH hooks fired for an agent's OWN git commands, in the same
# minute, from the same hooks directory. A `git push` is an agent's own git command. The existing
# `reference-transaction` hook installed by `.softhouse/bin/branch_sweep.py` (T312) is the
# precedent: a git hook in this repository's shared hooks directory that demonstrably refuses.
#
# ENGINE (P-33/P-53): bash, git, shasum. Declared, not assumed.
# =============================================================================================
set -u

say() { printf 'install-driver-push-gate: %s\n' "$*"; }
die() { printf 'install-driver-push-gate: %s\n' "$*"; exit 2; }

MODE="${1:-install}"

TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die "ABORT(2) -- \`git rev-parse --show-toplevel\` failed. Not inside a work tree."
[ -n "$TOPLEVEL" ] || die "ABORT(2) -- empty repository root."
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" \
  || die "ABORT(2) -- \`git rev-parse --git-common-dir\` failed."
case "$COMMON" in /*) : ;; *) COMMON="$TOPLEVEL/$COMMON" ;; esac
[ -d "$COMMON" ] || die "ABORT(2) -- the git common dir does not resolve to a directory: $COMMON"

HOOKS="$COMMON/hooks"
HOOK="$HOOKS/pre-push"
SNAPDIR="$HOOKS/softhouse-t412-gate"

# The MAIN checkout is the common dir's parent when the common dir is a `.git` DIRECTORY, which
# is how this repository is laid out. Derived, never typed: an absolute path literal in a tracked
# instrument is host state and a dead absolute path on any other machine.
MAINWT="$(dirname "$COMMON")"

HOOKSPATH="$(git config --get core.hooksPath || true)"
if [ -n "$HOOKSPATH" ]; then
  die "ABORT(2) -- core.hooksPath is set to '$HOOKSPATH'. This installer writes to \$(git rev-parse --git-common-dir)/hooks and would install a hook git will not run. REFUSING rather than installing something inert."
fi

case "$MODE" in
  --status)
    say "hooks dir     $HOOKS"
    say "main checkout $MAINWT"
    if [ -f "$HOOK" ]; then
      say "pre-push      PRESENT"
      if grep -q 'softhouse-t412-driver-push-gate' "$HOOK"; then
        say "              and it IS this gate's shim."
      else
        say "              but it is NOT this gate's shim. Inspect it before overwriting."
      fi
      say "--- installed shim ---"
      cat "$HOOK"
    else
      say "pre-push      ABSENT -- the gate is NOT installed and enforces nothing."
    fi
    if [ -f "$SNAPDIR/driver-push-gate.sh" ]; then
      say "snapshot      $(shasum -a 256 "$SNAPDIR/driver-push-gate.sh" | cut -c1-16)  $SNAPDIR"
    else
      say "snapshot      ABSENT"
    fi
    say "ledger        $COMMON/softhouse-driver-gate/attest.tsv"
    exit 0 ;;
  --uninstall)
    if [ -f "$HOOK" ] && grep -q 'softhouse-t412-driver-push-gate' "$HOOK"; then
      rm -f "$HOOK" || die "ABORT(2) -- could not remove $HOOK"
      say "removed $HOOK"
    else
      say "nothing to remove: $HOOK is absent or is not this gate's shim."
    fi
    exit 0 ;;
  install) : ;;
  *) die "ABORT(2) -- unknown mode '$MODE'. Use --status, --uninstall, or no argument." ;;
esac

SRC="$TOPLEVEL/.softhouse/hooks"
for f in driver-push-gate.sh cheap-subset.sh bar-attest.sh; do
  [ -f "$SRC/$f" ] || die "ABORT(2) -- $f is missing from $SRC. Refusing to install a partial gate."
done

if [ -f "$HOOK" ] && ! grep -q 'softhouse-t412-driver-push-gate' "$HOOK"; then
  die "ABORT(2) -- $HOOK exists and is NOT this gate's shim. REFUSING to overwrite another hook silently. Inspect it, then move it aside deliberately."
fi

mkdir -p "$SNAPDIR" || die "ABORT(2) -- could not create $SNAPDIR"
for f in driver-push-gate.sh cheap-subset.sh; do
  cp "$SRC/$f" "$SNAPDIR/$f" || die "ABORT(2) -- could not snapshot $f"
done

cat >"$HOOK" <<SHIM
#!/bin/sh
# softhouse-t412-driver-push-gate -- installed by .softhouse/hooks/install-driver-push-gate.sh
# Refuses a push to refs/heads/main that carries a gitlink, writes outside the driver allowlist,
# or lands a tree no bar has graded.  Stands aside for every other ref.
# Escape hatch for C2/C3 only, never C1:  SOFTHOUSE_DRIVER_GATE_BYPASS="<reason, 12+ chars>"
GATE="$MAINWT/.softhouse/hooks/driver-push-gate.sh"
if [ ! -f "\$GATE" ]; then
  GATE="$SNAPDIR/driver-push-gate.sh"
fi
if [ ! -f "\$GATE" ]; then
  echo "driver-push-gate: ABORT -- the gate script is absent from BOTH the main checkout and the" >&2
  echo "driver-push-gate: install-time snapshot. A pre-push hook that cannot find its gate REFUSES;" >&2
  echo "driver-push-gate: an absent guard that passes is the defect this whole gate exists for." >&2
  exit 1
fi
echo "driver-push-gate: running \$GATE (sha256 \$(shasum -a 256 "\$GATE" | cut -c1-16))" >&2
exec bash "\$GATE" "\$@"
SHIM
chmod 755 "$HOOK" || die "ABORT(2) -- could not chmod $HOOK"

say "INSTALLED $HOOK"
say "  primary  $MAINWT/.softhouse/hooks/driver-push-gate.sh  $( [ -f "$MAINWT/.softhouse/hooks/driver-push-gate.sh" ] && echo PRESENT || echo 'ABSENT (pre-merge; the snapshot carries it)')"
say "  snapshot $SNAPDIR/driver-push-gate.sh  sha256 $(shasum -a 256 "$SNAPDIR/driver-push-gate.sh" | cut -c1-16)"
say ""
say "  It is INSTALLED, not merely written. Verify with:  bash .softhouse/hooks/install-driver-push-gate.sh --status"
exit 0
