#!/usr/bin/env bash
# =============================================================================================
# T453 -- M-2: IS THE ABSENCE OF THE GATE DETECTABLE?
#     bash drive-install-detect.sh <source-rev> <outdir>
#
# M-2 is P-45 for the eighth recorded time in this program: T412 shipped a gate and an installer,
# and NOTHING CALLED THE INSTALLER. `.git/hooks` is untracked, so a FRESH CLONE -- which is
# exactly what the cloud fire and any CI runner is -- was silently ungated, and no guard said so.
#
# THE FIX HAS TWO HALVES AND THIS DRIVES THE ONE THAT MATTERS. Wiring the installer into
# `fire-program.sh` is necessary and cannot be proven here (it takes effect at the NEXT fire).
# What CAN be proven, on a fresh clone, right now, is the half that makes the wiring auditable:
#
#   A  A FRESH CLONE IS UNGATED, and `--status` now SAYS SO WITH AN EXIT CODE. Before T453 it
#      printed "the gate is NOT installed and enforces nothing" and exited 0, so nothing could
#      test for it. A report is not a check; an exit code is.
#   B  A PUSH TO main FROM THAT UNGATED CLONE IS UNGATED -- measured, not asserted. This is what
#      the cloud fire has been doing.
#   C  running the installer makes `--status` exit 0 and the same push GATED.
#   D  an INCOMPLETE install -- one part of the gate missing from the install-time snapshot -- is
#      also detected. That is m-4's exact shape: the installer used to CHECK three files and COPY
#      two, and on this very host `--status` catches it today.
#
# ENGINE (P-33/P-53): bash, git, POSIX grep. Declared, not assumed.
# =============================================================================================
set -u

ME='drive-install-detect'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

SRCREV="${1:-}"
OUT="${2:-}"
[ -n "$SRCREV" ] && [ -n "$OUT" ] || die 90 "usage: drive-install-detect.sh <source-rev> <outdir>"

SRC="$(git rev-parse --show-toplevel 2>/dev/null)" || die 90 "not inside a work tree"
SRCSHA="$(git -C "$SRC" rev-parse --verify --quiet "$SRCREV^{commit}")" \
  || die 90 "'$SRCREV' does not resolve to a commit in $SRC"
mkdir -p "$OUT" || die 90 "could not create $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter the output directory"

U="$(mktemp -d "${TMPDIR:-/tmp}/t453-install.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
trap '[ -n "${U:-}" ] && [ -d "$U" ] && rm -rf "$U"' EXIT
BARE="$U/origin.git"; WT="$U/wt"
GIT="git -c user.name=t453-drive -c user.email=t453@invalid -c commit.gpgsign=false"

say "source   $SRCREV -> $SRCSHA"
$GIT clone --local --quiet --no-checkout "$SRC" "$WT" || die 90 "could not clone $SRC"
cd "$WT" || die 90 "could not enter the clone"
$GIT checkout -q -B main "$SRCSHA" || die 90 "could not check out $SRCSHA"
$GIT remote remove origin || die 90 "could not detach the clone from its source remote"
$GIT init --bare -q "$BARE" || die 90 "could not init the bare remote"
$GIT remote add origin "$BARE" || die 90 "could not add the throwaway remote"
RURL="$($GIT remote get-url origin)" || die 90 "could not read back the remote url"
[ "$RURL" = "$BARE" ] || die 90 "the throwaway remote is '$RURL'. REFUSING to push."
$GIT push -q origin main || die 90 "could not publish the base history"

# --- A: a FRESH CLONE, before anything is installed ------------------------------------------
[ -f "$WT/.git/hooks/pre-push" ] \
  && die 91 "a freshly cloned repository already has a pre-push hook. The premise of this drive is false and nothing below would measure M-2."
bash .softhouse/hooks/install-driver-push-gate.sh --status >"$OUT/10-A-status-fresh-clone.txt" 2>&1
A_RC=$?
say "A  fresh clone: --status exit=$A_RC  (M-2: must be NON-ZERO; T412's exited 0 here)"
[ "$A_RC" -ne 0 ] \
  || die 92 "A FAILED: --status exited 0 on a repository with no hook at all. Absence is still undetectable and M-2 is not closed."

# --- B: and a push to main from that clone really is ungated ---------------------------------
printf "\n<!-- T453 install-detect: a push from an UNGATED clone. -->\n" >>".softhouse/RESUME.md" \
  || die 93 "B: could not edit the state file"
$GIT add -A && $GIT commit -q -m "T453 install-detect: push from an ungated clone" \
  || die 93 "B: could not commit"
$GIT push origin main >"$OUT/20-B-push-from-ungated-clone.txt" 2>&1
B_RC=$?
B_LINES="$(LC_ALL=C grep -ac 'driver-push-gate' "$OUT/20-B-push-from-ungated-clone.txt" || true)"
case "${B_LINES:-}" in ''|*[!0-9]*) B_LINES=0 ;; esac
say "B  push from the ungated clone: exit=$B_RC gate lines=$B_LINES  (expected 0 and 0)"
[ "$B_RC" -eq 0 ] && [ "$B_LINES" -eq 0 ] \
  || die 92 "B FAILED: the fresh clone was not actually ungated (exit $B_RC, $B_LINES gate lines). The finding this drive exists for is not reproduced."

# --- C: install, and the same two facts flip -------------------------------------------------
bash .softhouse/hooks/install-driver-push-gate.sh >"$OUT/30-C-install.txt" 2>&1 \
  || { LC_ALL=C sed -n '1,25p' "$OUT/30-C-install.txt" >&2; die 92 "C: the installer refused"; }
bash .softhouse/hooks/install-driver-push-gate.sh --status >"$OUT/31-C-status-after-install.txt" 2>&1
C_RC=$?
say "C  after install: --status exit=$C_RC  (expected 0)"
[ "$C_RC" -eq 0 ] || { LC_ALL=C sed -n '1,25p' "$OUT/31-C-status-after-install.txt" >&2
  die 92 "C FAILED: --status still non-zero after a successful install. It would cry wolf every fire."; }

printf "\n<!-- T453 install-detect: a push from a GATED clone. -->\n" >>".softhouse/RESUME.md" \
  || die 93 "C: could not edit the state file"
$GIT add -A && $GIT commit -q -m "T453 install-detect: push from a gated clone" || die 93 "C: could not commit"
$GIT push origin main >"$OUT/32-C-push-from-gated-clone.txt" 2>&1 || true
C_LINES="$(LC_ALL=C grep -ac 'driver-push-gate' "$OUT/32-C-push-from-gated-clone.txt" || true)"
case "${C_LINES:-}" in ''|*[!0-9]*) C_LINES=0 ;; esac
say "C  push from the gated clone: gate lines=$C_LINES  (expected >0)"
[ "$C_LINES" -gt 0 ] || die 92 "C FAILED: the gate printed nothing after being installed."

# --- D: an INCOMPLETE install is detected too -- m-4's exact shape ----------------------------
SNAP="$WT/.git/hooks/softhouse-t412-gate"
[ -f "$SNAP/bar-attest.sh" ] \
  || die 92 "D: bar-attest.sh is not in the snapshot after a successful install. m-4 is NOT fixed."
mv "$SNAP/bar-attest.sh" "$U/bar-attest.sh.moved" || die 93 "D: could not move the snapshot part aside"
bash .softhouse/hooks/install-driver-push-gate.sh --status >"$OUT/40-D-status-incomplete.txt" 2>&1
D_RC=$?
say "D  one gate part removed from the snapshot: --status exit=$D_RC  (expected non-zero)"
[ "$D_RC" -ne 0 ] \
  || die 92 "D FAILED: --status exited 0 with a part of the gate missing from the snapshot. That is m-4 undetected."
mv "$U/bar-attest.sh.moved" "$SNAP/bar-attest.sh" || die 93 "D: could not restore the snapshot part"

say ""
say "T453-INSTALL-DETECT: A=$A_RC(non-zero) B=ungated(exit $B_RC, $B_LINES lines) C=$C_RC(zero, $C_LINES lines) D=$D_RC(non-zero)"
say "evidence $OUT"
exit 0
