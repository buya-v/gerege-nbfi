#!/usr/bin/env bash
# =============================================================================================
# T453 -- THE RECONCILER DRIVE.  m-3, end to end.
#     bash drive-reconciler.sh <source-rev> <outdir>
#
# REPRODUCES T450's m-3 AND THEN DETECTS IT.
#
#   LEG 1  a lawful gated push. The gate speaks, the ledger gains a row, the reconciler is GREEN.
#   LEG 2  `git push --no-verify` of a tree carrying a GITLINK -- the one check the gate declares
#          unbypassable. The gate prints NOTHING. The push lands. This is m-3 verbatim.
#   LEG 3  the reconciler, run afterwards over the same reflog, EXITS 1 and names BOTH the
#          UNATTESTED tip and the GITLINK.
#   LEG 4  a bypass with a REASON is recorded, and the reconciler READS the bypass ledger --
#          which, until this task, nothing did.
#
# LEG 1 IS NOT DECORATION. An instrument that only ever reports findings cannot be told apart
# from one that reports findings unconditionally (P-98), so the GREEN leg runs first and its
# passing is a precondition for the RED leg meaning anything.
#
# Everything happens in a THROWAWAY UNIVERSE under $TMPDIR. The live hook on this host is gating
# a running fire and is never touched.
#
# ENGINE (P-33/P-53): bash, git, POSIX grep/sed. Declared, not assumed.
# =============================================================================================
set -u

ME='drive-reconciler'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

SRCREV="${1:-}"
OUT="${2:-}"
[ -n "$SRCREV" ] && [ -n "$OUT" ] || die 90 "usage: drive-reconciler.sh <source-rev> <outdir>"

SRC="$(git rev-parse --show-toplevel 2>/dev/null)" || die 90 "not inside a work tree"
SRCSHA="$(git -C "$SRC" rev-parse --verify --quiet "$SRCREV^{commit}")" \
  || die 90 "'$SRCREV' does not resolve to a commit in $SRC"
mkdir -p "$OUT" || die 90 "could not create $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter the output directory"

U="$(mktemp -d "${TMPDIR:-/tmp}/t453-recon.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
trap '[ -n "${U:-}" ] && [ -d "$U" ] && rm -rf "$U"' EXIT

BARE="$U/origin.git"
WT="$U/wt"
GIT="git -c user.name=t453-drive -c user.email=t453@invalid -c commit.gpgsign=false"

say "source   $SRCREV -> $SRCSHA"
say "universe $U"

$GIT clone --local --quiet --no-checkout "$SRC" "$WT" || die 90 "could not clone $SRC"
cd "$WT" || die 90 "could not enter the throwaway clone"
$GIT checkout -q -B main "$SRCSHA" || die 90 "could not check out $SRCSHA"
$GIT remote remove origin || die 90 "could not detach the clone from its source remote"
$GIT init --bare -q "$BARE" || die 90 "could not init the throwaway bare remote"
$GIT remote add origin "$BARE" || die 90 "could not add the throwaway remote"
RURL="$($GIT remote get-url origin)" || die 90 "could not read back the remote url"
[ "$RURL" = "$BARE" ] || die 90 "the throwaway remote is '$RURL', not the bare this drive created. REFUSING to push."

$GIT push -q origin main || die 90 "could not publish the base history"
bash .softhouse/hooks/install-driver-push-gate.sh >"$OUT/00-install.txt" 2>&1 \
  || { LC_ALL=C sed -n '1,25p' "$OUT/00-install.txt" >&2; die 92 "the installer refused"; }
[ -f "$WT/.git/hooks/pre-push" ] || die 92 "the installer exited 0 but the hook is absent"

GATE_DIR="$WT/.git/softhouse-driver-gate"
mkdir -p "$GATE_DIR" || die 92 "could not create the throwaway ledger directory"
BASE="$($GIT rev-parse HEAD)"; BASETREE="$($GIT rev-parse 'HEAD^{tree}')"
printf 'FULL\t%s\t%s\t%s\t%s\n' "$BASETREE" "$BASE" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  "SEEDED BY T453 drive-reconciler.sh" >>"$GATE_DIR/attest.tsv" \
  || die 92 "could not seed the throwaway ledger"

# ------------------------------------------------------------------- LEG 1: a lawful gated push
printf "\n<!-- T453 reconciler drive: a lawful driver state edit. -->\n" >>".softhouse/RESUME.md" \
  || die 93 "leg 1: could not edit the state file"
$GIT add -A && $GIT commit -q -m "T453 reconciler drive leg 1: lawful state edit" \
  || die 93 "leg 1: could not commit"
$GIT push origin main >"$OUT/10-leg1-gated-push.txt" 2>&1
L1RC=$?
LC_ALL=C grep -aq 'driver-push-gate' "$OUT/10-leg1-gated-push.txt" \
  || die 94 "leg 1: the gate printed NOTHING. Silence is not a verdict, and no leg below would be interpretable."
[ "$L1RC" -eq 0 ] || { LC_ALL=C sed -n '1,40p' "$OUT/10-leg1-gated-push.txt" >&2
  die 92 "leg 1: the gate REFUSED a lawful state edit (exit $L1RC). That is a freeze, and the RED leg below would be unearned."; }
say "LEG 1  lawful gated push ALLOWED, ledger row written."

bash .softhouse/hooks/reconcile-pushed-trees.sh >"$OUT/11-leg1-reconcile-GREEN.txt" 2>&1
R1RC=$?
say "LEG 1  reconciler exit=$R1RC (expected 0)"
[ "$R1RC" -eq 0 ] || { LC_ALL=C sed -n '1,40p' "$OUT/11-leg1-reconcile-GREEN.txt" >&2
  die 92 "CONTROL FAILED: the reconciler reports findings on a universe where every push was gated. Every RED result below would be unearned (P-98)."; }

# ------------------------------------------------------- LEG 2: --no-verify drives a gitlink in
# THIS IS m-3 VERBATIM. C1 says "THERE IS NO BYPASS FOR C1". That is true about the gate and
# false about git: `pre-push` is client-side, and `--no-verify` does not run it.
SUBM="$WT/t453-nv-submodule"
$GIT init -q "$SUBM"                                  || die 93 "leg 2: could not init the probe submodule"
( cd "$SUBM" && $GIT commit -q --allow-empty -m probe ) || die 93 "leg 2: could not commit in the probe submodule"
$GIT add "$SUBM" >/dev/null 2>&1                       || die 93 "leg 2: could not stage the gitlink"
$GIT commit -q -m "T453 reconciler drive leg 2: a gitlink, pushed with --no-verify" \
                                                       || die 93 "leg 2: could not commit the gitlink"
NVTIP="$($GIT rev-parse HEAD)"
$GIT push --no-verify origin main >"$OUT/20-leg2-no-verify-push.txt" 2>&1
L2RC=$?
GATELINES="$(LC_ALL=C grep -ac 'driver-push-gate' "$OUT/20-leg2-no-verify-push.txt" || true)"
case "${GATELINES:-}" in ''|*[!0-9]*) GATELINES=0 ;; esac
say "LEG 2  --no-verify push exit=$L2RC, gate output lines=$GATELINES (m-3: expected 0 and 0)"
[ "$L2RC" -eq 0 ] || die 93 "leg 2: the --no-verify push did not land (exit $L2RC); m-3 is not reproduced and leg 3 would be measuring nothing."
[ "$GATELINES" -eq 0 ] || die 93 "leg 2: the gate SPOKE during a --no-verify push ($GATELINES lines). That contradicts m-3 and this drive would be measuring something else."

# ------------------------------------------------------------- LEG 3: the reconciler detects it
bash .softhouse/hooks/reconcile-pushed-trees.sh >"$OUT/30-leg3-reconcile-RED.txt" 2>&1
R3RC=$?
say "LEG 3  reconciler exit=$R3RC (expected 1)"
UNATT="$(LC_ALL=C grep -ac 'UNATTESTED' "$OUT/30-leg3-reconcile-RED.txt" || true)"
GLK="$(LC_ALL=C grep -ac 'GITLINK ' "$OUT/30-leg3-reconcile-RED.txt" || true)"
case "${UNATT:-}" in ''|*[!0-9]*) UNATT=0 ;; esac
case "${GLK:-}"   in ''|*[!0-9]*) GLK=0 ;; esac
say "LEG 3  UNATTESTED lines=$UNATT  GITLINK lines=$GLK"
if [ "$R3RC" -ne 1 ] || [ "$UNATT" -lt 1 ] || [ "$GLK" -lt 1 ]; then
  LC_ALL=C sed -n '1,40p' "$OUT/30-leg3-reconcile-RED.txt" >&2
  die 92 "LEG 3 FAILED: the reconciler did not detect the bypassed push. A guard that cannot be shown to fail is not a guard (P-22)."
fi
say "LEG 3  the bypassed tip $($GIT rev-parse --short "$NVTIP") is NAMED, post hoc, with its gitlink."

# --------------------------------------------------------- LEG 4: the bypass ledger gets a row
$GIT reset -q --hard "$BASE" || die 93 "leg 4: could not reset"
# `git reset --hard` does not remove an untracked directory, and the leg-2 probe submodule is
# one. Left in place, the next `git add -A` re-adds it as an EMBEDDED GIT REPOSITORY and this leg
# commits a gitlink -- which C1 refuses with NO BYPASS, so the leg would measure C1 instead of the
# bypass ledger. Driven: leg 4 failed exactly this way on its first run. This is instance 3's own
# mechanism turning up inside the instrument written to detect instance 3.
rm -rf "$SUBM" || die 93 "leg 4: could not remove the leg-2 probe submodule"
$GIT clean -qfd || die 93 "leg 4: could not clean the work tree"
# THE DELTA MUST BE ONE THE GATE REFUSES, or no bypass is ever recorded and this leg measures
# nothing. Driven: the first version edited a STATE file, the gate lawfully ALLOWED it on the
# cheap path, `record_bypass` was never reached, and the leg reported zero rows -- a green-looking
# failure. A write OUTSIDE the driver allowlist (.softhouse/, docs/, .claude/) is what C2 exists
# to refuse, so it is what exercises the bypass.
printf "T453 reconciler drive leg 4: a write outside the driver allowlist.\n" >"t453-bypass-probe.txt" \
  || die 93 "leg 4: could not write the out-of-allowlist probe"
$GIT add -A && $GIT commit -q -m "T453 reconciler drive leg 4" || die 93 "leg 4: could not commit"
# Force, because leg 2 moved the remote onto a history this commit does not descend from. The
# BYPASS is what is under test here, not the fast-forward.
SOFTHOUSE_DRIVER_GATE_BYPASS='T453 drive: proving the bypass ledger gains a readable row' \
  $GIT push --force origin main >"$OUT/40-leg4-bypass-push.txt" 2>&1 || true
bash .softhouse/hooks/reconcile-pushed-trees.sh >"$OUT/41-leg4-reconcile-reads-bypass.txt" 2>&1
R4RC=$?
NBY="$(LC_ALL=C sed -n 's/.*bypasses=\([0-9][0-9]*\).*/\1/p' "$OUT/41-leg4-reconcile-reads-bypass.txt" | LC_ALL=C sed -n '1p')"
case "${NBY:-}" in ''|*[!0-9]*) NBY=-1 ;; esac
say "LEG 4  reconciler exit=$R4RC  bypasses READ from the ledger=$NBY"
if [ "$NBY" -lt 1 ]; then
  LC_ALL=C sed -n '1,40p' "$OUT/40-leg4-bypass-push.txt" >&2
  LC_ALL=C sed -n '1,40p' "$OUT/41-leg4-reconcile-reads-bypass.txt" >&2
  die 92 "LEG 4 FAILED: no bypass row was recorded, or the reconciler did not read it. bypass.log having no reader is half of m-3."
fi

say ""
say "T453-RECONCILER-DRIVE: leg1=GREEN(exit $R1RC) leg2=m-3-REPRODUCED(gate lines $GATELINES) leg3=RED(exit $R3RC, unattested $UNATT, gitlink $GLK) leg4=bypass-rows-read=$NBY"
say "evidence $OUT"
exit 0
