#!/usr/bin/env bash
# =============================================================================================
# T453 -- M-2: DO THE WIRED LINES ACTUALLY DO WHAT THEY SAY?
#     bash drive-fire-wiring.sh <source-rev> <outdir>
#
# `.softhouse/bin/fire-program.sh` IS THE RUNNING WRAPPER. A change landed in it mid-fire does
# not take effect until the NEXT fire, and T301 already recorded the wrapper editing itself
# mid-run as a defect. So the wiring for M-2 cannot be proven by running a fire.
#
# WHAT CAN BE PROVEN, AND IS: the block itself is EXTRACTED FROM THE TRACKED FILE by its
# sentinels and EXECUTED, verbatim, against a throwaway clone with a stub `log`. Nothing is
# retyped here -- retyping the block would test a copy, and the copy is not what runs.
#
#   LEG A  the block, run against an UNGATED throwaway clone, INSTALLS the gate and logs
#          `STATUS OK`. Before T453 nothing called the installer at all.
#   LEG B  the SAME block, with the installer made unavailable, logs the NOT-INSTALLED banner
#          instead of falling through silently. This is the arm that decides whether the wiring
#          is a control or a decoration (P-22).
#   LEG C  the reconciliation line runs and its output reaches the log.
#
# THIS IS NOT A LIVE FIRE AND THE HANDOFF SAYS SO. It is the difference between "the lines are
# in the file" and "the lines do what they say"; it is not the difference between that and "the
# lines ran in production".
#
# ENGINE (P-33/P-53): bash, zsh (the wrapper's own shell), git, POSIX grep/sed. Declared.
# =============================================================================================
set -u

ME='drive-fire-wiring'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

SRCREV="${1:-}"
OUT="${2:-}"
[ -n "$SRCREV" ] && [ -n "$OUT" ] || die 90 "usage: drive-fire-wiring.sh <source-rev> <outdir>"

SRC="$(git rev-parse --show-toplevel 2>/dev/null)" || die 90 "not inside a work tree"
SRCSHA="$(git -C "$SRC" rev-parse --verify --quiet "$SRCREV^{commit}")" \
  || die 90 "'$SRCREV' does not resolve to a commit"
mkdir -p "$OUT" || die 90 "could not create $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter the output directory"
command -v zsh >/dev/null 2>&1 || die 93 "zsh is not on PATH. fire-program.sh is a zsh script; running its block under another shell would be testing something else."

U="$(mktemp -d "${TMPDIR:-/tmp}/t453-wiring.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
trap '[ -n "${U:-}" ] && [ -d "$U" ] && rm -rf "$U"' EXIT
WT="$U/wt"
GIT="git -c user.name=t453-drive -c user.email=t453@invalid -c commit.gpgsign=false"

$GIT clone --local --quiet --no-checkout "$SRC" "$WT" || die 90 "could not clone $SRC"
$GIT -C "$WT" checkout -q -B main "$SRCSHA" || die 90 "could not check out $SRCSHA"
$GIT -C "$WT" remote remove origin || die 90 "could not detach the clone from its source remote"
say "throwaway REPO $WT (a fresh clone: no hook, exactly like the cloud fire)"

# --- EXTRACT THE BLOCK FROM THE TRACKED WRAPPER, BY ITS SENTINELS -----------------------------
WRAP="$WT/.softhouse/bin/fire-program.sh"
[ -f "$WRAP" ] || die 91 "the wrapper is absent from tree $SRCSHA. There is no wiring to test."
BEG="$(LC_ALL=C grep -an 'T453-PUSHGATE-BLOCK-BEGIN' "$WRAP" | LC_ALL=C sed -n '1p' | LC_ALL=C cut -d: -f1)"
END="$(LC_ALL=C grep -an 'T453-PUSHGATE-BLOCK-END'   "$WRAP" | LC_ALL=C sed -n '1p' | LC_ALL=C cut -d: -f1)"
case "${BEG:-}" in ''|*[!0-9]*) die 92 "the BEGIN sentinel is not in the wrapper. Either the wiring was removed or it was renamed; either way this drive REFUSES rather than reporting a pass about a block it could not find." ;; esac
case "${END:-}" in ''|*[!0-9]*) die 92 "the END sentinel is not in the wrapper. REFUSING." ;; esac
[ "$END" -gt "$BEG" ] || die 92 "the sentinels are in the wrong order ($BEG..$END)."
BLOCK="$U/block.zsh"
LC_ALL=C sed -n "$((BEG + 1)),$((END - 1))p" "$WRAP" >"$BLOCK" || die 92 "could not extract the block"
NB="$(LC_ALL=C grep -ac '' "$BLOCK" || true)"
case "${NB:-}" in ''|*[!0-9]*) NB=0 ;; esac
[ "$NB" -ge 5 ] || die 92 "the extracted block is $NB line(s). That is an extraction failure, not a small block (P-35)."
say "extracted $NB line(s) from $WRAP:$BEG..$END"
cp "$BLOCK" "$OUT/00-extracted-block.zsh"

# The stub `log`, and the two variables the block reads. Nothing else is supplied: if the block
# depends on anything this harness has not declared, it fails here rather than in a fire.
mk_runner() {
  {
    printf '%s\n' 'log() { printf "%s\n" "$*"; }'
    printf 'REPO=%s\n' "$1"
    cat "$BLOCK"
  } >"$U/runner.zsh"
}

# --- LEG A: the block installs the gate on a fresh clone -------------------------------------
[ -f "$WT/.git/hooks/pre-push" ] \
  && die 91 "the fresh clone already has a pre-push hook; the premise of leg A is false."
mk_runner "$WT"
( cd "$WT" && zsh "$U/runner.zsh" ) >"$OUT/10-legA-fresh-clone.txt" 2>&1
A_RC=$?
say "LEG A  block exit=$A_RC"
[ -f "$WT/.git/hooks/pre-push" ] \
  || { LC_ALL=C sed -n '1,30p' "$OUT/10-legA-fresh-clone.txt" >&2
       die 92 "LEG A FAILED: the block ran and the hook is still absent. The wiring is a decoration."; }
LC_ALL=C grep -aq 'pushgate| STATUS OK' "$OUT/10-legA-fresh-clone.txt" \
  || { LC_ALL=C sed -n '1,30p' "$OUT/10-legA-fresh-clone.txt" >&2
       die 92 "LEG A FAILED: no 'pushgate| STATUS OK' line. The status check did not run or did not reach the log."; }
say "LEG A  the fresh clone is now GATED and the fire log says STATUS OK."

# --- LEG C (taken here, on the same run): the reconciliation reaches the log ------------------
LC_ALL=C grep -aq 'reconcile|' "$OUT/10-legA-fresh-clone.txt" \
  || { LC_ALL=C sed -n '1,40p' "$OUT/10-legA-fresh-clone.txt" >&2
       die 92 "LEG C FAILED: the reconciliation produced no 'reconcile|' line. A reconciler whose output never reaches the fire log has no reader, which is the defect it was built to close."; }
say "LEG C  the post-hoc reconciliation ran and its output reached the log."

# --- LEG B: the ABSENT branch is reachable, and is LOUD --------------------------------------
# P-22: an arm that has never been seen to fire is not an arm. The installer is moved aside so
# the block's own `--status` check fails, and the NOT-INSTALLED banner must appear.
rm -f "$WT/.git/hooks/pre-push" || die 93 "leg B: could not remove the hook"
mv "$WT/.softhouse/hooks/install-driver-push-gate.sh" "$U/installer.moved" \
  || die 93 "leg B: could not move the installer aside"
( cd "$WT" && zsh "$U/runner.zsh" ) >"$OUT/20-legB-installer-unavailable.txt" 2>&1
B_RC=$?
mv "$U/installer.moved" "$WT/.softhouse/hooks/install-driver-push-gate.sh" \
  || die 93 "leg B: could not restore the installer"
say "LEG B  block exit=$B_RC (the block is deliberately non-fatal; a broken guard must not stop a fire)"
LC_ALL=C grep -aq 'THE DRIVER PUSH GATE IS NOT INSTALLED' "$OUT/20-legB-installer-unavailable.txt" \
  || { LC_ALL=C sed -n '1,30p' "$OUT/20-legB-installer-unavailable.txt" >&2
       die 92 "LEG B FAILED: the block did not log the NOT-INSTALLED banner when the gate could not be installed. Absence is still silent, and M-2 is not closed."; }
say "LEG B  with the gate uninstallable, the fire log carries the NOT-INSTALLED banner."

say ""
say "T453-FIRE-WIRING: legA=installed+STATUS-OK legB=NOT-INSTALLED-banner-printed legC=reconcile-logged block=$NB lines from $WRAP:$BEG..$END"
say "NOT a live fire. The block was extracted from the tracked wrapper and executed; it has not"
say "  yet run inside a real fire, and it cannot until the next one."
say "evidence $OUT"
exit 0
