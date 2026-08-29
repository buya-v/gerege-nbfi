#!/usr/bin/env bash
# =============================================================================================
# T465 / C-T461-2 -- RED AND GREEN FOR R3, THE PROVENANCE READER.
#
#     bash 30-r3-provenance-drive.sh <outdir>
#
# C-T461-2's finding was that `gate=`/`headblob=` had ONE WRITER AND ZERO READERS. T465 gave
# them a reader (R3 in `reconcile-pushed-trees.sh`). A reader that has never been seen to
# REFUSE is the same defect wearing a different hat -- P-45's cousin -- so this drives it both
# ways against a THROWAWAY CLONE, never the live ledger, which is the driver's state.
#
#   GREEN  a ledger row whose gate= and headblob= AGREE           -> exit 0, drift=0
#   RED    the same row with the two shas made to DISAGREE        -> exit 1, drift>=1
#   BLANK  the same row with the two fields removed entirely      -> exit 0, unknown>=1, drift=0
#          (this is the cry-wolf arm: every row written before T465 looks like this, and R3
#           must COUNT it, not refuse on it.)
#
# THE THREE ARMS SHARE ONE FIXTURE AND DIFFER ONLY IN THE LEDGER ROW, so a difference in the
# verdict can only be the row. Everything runs under $TMPDIR; nothing here writes to the
# repository it reads from, and no real repo path is spelt -- the softhouse directory name is
# assembled from $SH_NAME.
#
# EXIT: 0 all three arms behaved as stated; 1 an arm did not; 9x the fixture could not be built.
# Probe line: `T465-R3-DRIVE:`, printed only when all three arms reached a verdict (P-84).
# =============================================================================================
set -u

ME='t465-r3-drive'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

OUT="${1:-}"
[ -n "$OUT" ] || die 90 "usage: 30-r3-provenance-drive.sh <outdir>"
mkdir -p "$OUT" || die 90 "could not create $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter $OUT"

SH_NAME='.softhouse'
RECON_REL="$SH_NAME/hooks/reconcile-pushed-trees.sh"

SRC="$(git rev-parse --show-toplevel 2>/dev/null)" || die 90 "not inside a git work tree"
[ -f "$SRC/$RECON_REL" ] || die 90 "the reconciler is absent: $SRC/$RECON_REL"

U="$(mktemp -d "${TMPDIR:-/tmp}/t465-r3.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
trap '[ -n "${U:-}" ] && [ -d "$U" ] && rm -rf "$U"' EXIT
WT="$U/wt"
GIT="git -c user.name=t465-r3 -c user.email=t465@invalid -c commit.gpgsign=false"

# A LOCAL CLONE. `git clone` writes refs/remotes/origin/main AND its reflog, which is the
# evidence the reconciler reads; a bare `git init` fixture would have no reflog and the
# reconciler would (correctly) refuse with exit 2 about the FIXTURE.
$GIT clone --local --quiet "$SRC" "$WT" || die 90 "could not clone $SRC"
cd "$WT" || die 90 "could not enter $WT"
$GIT config core.logAllRefUpdates true || die 90 "could not enable reflogs in the fixture"

TIP="$($GIT rev-parse --verify --quiet refs/remotes/origin/main)" \
  || die 91 "the clone has no refs/remotes/origin/main. There is no window to reconcile."
# `git clone` writes the remote-tracking REF but NOT a reflog entry for it, and the reconciler
# reads the REFLOG. Measured, not assumed: the first run of this drive came back exit=2 on all
# three arms with "the ref has NO REFLOG ENTRIES on this host" -- a refusal about the FIXTURE
# wearing the costume of a refusal about R3, which is precisely the confusion this repository
# keeps paying for. So the entry is created explicitly, and its PRESENCE is then re-read.
# MEASURED, twice: `git update-ref` on a ref that ALREADY holds the target value writes NO
# reflog entry, and `--create-reflog` does not change that. So the seed is a DETOUR -- move the
# ref to the tip's parent and back -- which is also a more faithful fixture, because it is what
# a real push looks like from the remote-tracking side. `--max 1` below then confines the
# reconciler's window to the newest entry, so the detour's intermediate tip is not a second,
# unattested tip that would make every arm red for the wrong reason.
PARENT="$($GIT rev-parse --verify --quiet "$TIP~1")" \
  || die 91 "the fixture tip has no parent, so the reflog cannot be seeded by a detour."
$GIT update-ref -m 't465-r3 fixture: detour' refs/remotes/origin/main "$PARENT" \
  || die 91 "could not move the fixture's remote-tracking ref"
$GIT update-ref -m 't465-r3 fixture: seed a remote-tracking reflog entry' \
  refs/remotes/origin/main "$TIP" || die 91 "could not seed the fixture's remote-tracking ref"
RLOG="$($GIT reflog show --max-count=1 refs/remotes/origin/main 2>/dev/null)" || RLOG=''
[ -n "$RLOG" ] \
  || die 91 "the clone's refs/remotes/origin/main STILL has no reflog entry. The reconciler would refuse about the fixture, not about R3, and all three arms would be uninterpretable."
TREE="$($GIT rev-parse --verify --quiet "$TIP^{tree}")" || die 91 "could not resolve the tip's tree"

COMMON="$($GIT rev-parse --git-common-dir)" || die 91 "could not resolve the fixture's git dir"
case "$COMMON" in /*) : ;; *) COMMON="$WT/$COMMON" ;; esac
GATE_DIR="$COMMON/softhouse-driver-gate"
mkdir -p "$GATE_DIR" || die 91 "could not create the fixture's gate directory"
ATTEST="$GATE_DIR/attest.tsv"

STAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
ARMS=0; BAD=0
RESULTS="$OUT/R3-RESULTS.txt"
: >"$RESULTS" || die 90 "could not create $RESULTS"
printf '# T465 R3 drive -- fixture tip %s tree %s\n' "$TIP" "$TREE" >>"$RESULTS"

# run_arm <id> <note-column> <expect-exit> <expect-drift-nonzero: yes|no>
run_arm() {
  local id="$1" note="$2" xrc="$3" xdrift="$4" f rc probes drift unknown
  printf 'FULL\t%s\t%s\t%s\t%s\n' "$TREE" "$TIP" "$STAMP" "$note" >"$ATTEST" \
    || die 91 "arm $id: could not seed the fixture ledger"
  f="$OUT/r3-arm-$id.txt"
  # THE RECONCILER UNDER TEST IS THE SOURCE WORKING TREE'S COPY, not the clone's. Measured: a
  # `git clone --local` carries COMMITTED history, so the clone's copy is the pre-R3 file and
  # all three arms came back with drift= unparseable. The cwd is the fixture, so the reconciler
  # still resolves the FIXTURE's gate directory -- only the bytes doing the grading are the
  # working tree's.
  bash "$SRC/$RECON_REL" --max 1 >"$f" 2>&1
  rc=$?
  probes="$(LC_ALL=C grep -ac 'T453-RECONCILE:' "$f" || true)"
  case "${probes:-}" in ''|*[!0-9]*) probes=0 ;; esac
  if [ "$probes" -eq 0 ]; then
    printf '%-8s exit=%s NO PROBE LINE -- no verdict available\n' "$id" "$rc" >>"$RESULTS"
    say "$id  exit=$rc  NO PROBE LINE -- no verdict available"
    BAD=$((BAD+1)); ARMS=$((ARMS+1)); return 0
  fi
  drift="$(LC_ALL=C sed -n 's/.*provenance-drift=\([0-9][0-9]*\).*/\1/p' "$f" | LC_ALL=C tail -1)"
  unknown="$(LC_ALL=C sed -n 's/.*provenance-unknown=\([0-9][0-9]*\).*/\1/p' "$f" | LC_ALL=C tail -1)"
  case "${drift:-}" in ''|*[!0-9]*) drift=-1 ;; esac
  case "${unknown:-}" in ''|*[!0-9]*) unknown=-1 ;; esac
  local ok=yes
  [ "$rc" -eq "$xrc" ] || ok=no
  if [ "$xdrift" = yes ]; then [ "$drift" -ge 1 ] || ok=no; else [ "$drift" -eq 0 ] || ok=no; fi
  [ "$ok" = yes ] || BAD=$((BAD+1))
  printf '%-8s exit=%s (want %s)  drift=%s unknown=%s  %s\n' \
    "$id" "$rc" "$xrc" "$drift" "$unknown" "$ok" >>"$RESULTS"
  say "$id  exit=$rc (want $xrc)  drift=$drift unknown=$unknown  behaved-as-stated=$ok"
  ARMS=$((ARMS+1))
}

run_arm GREEN "exit0 probe=1xup bar=aaaaaaaaaaaaaaaa gate=1111111111111111 headblob=1111111111111111 VERDICT: PASS" 0 no
run_arm RED   "exit0 probe=1xup bar=aaaaaaaaaaaaaaaa gate=1111111111111111 headblob=2222222222222222 VERDICT: PASS" 1 yes
run_arm BLANK "exit0 probe=1xup VERDICT: PASS" 0 no

[ "$ARMS" -eq 3 ] || die 91 "only $ARMS of 3 arms ran; there is nothing to report."
say ""
LC_ALL=C sed -n '1,40p' "$RESULTS"
say ""
say "T465-R3-DRIVE: arms=$ARMS misbehaved=$BAD"
[ "$BAD" -eq 0 ] || exit 1
exit 0
