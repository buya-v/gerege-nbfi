#!/usr/bin/env bash
# =============================================================================================
# T453 -- THE STATE-SET ARM DRIVE.
#     bash drive-arms.sh <source-rev> <label> <outdir> <mode> [arm-filter]
#         mode = gate   push each arm through a REALLY INSTALLED gate into a REAL bare remote
#         mode = bar    run the FULL bar (.softhouse/conformance.sh) on each arm's tree
#         arm-filter    optional POSIX ERE; only arm ids matching it are run
#
# ONE ARM LIST, TWO MEASUREMENTS, DELIBERATELY. The finding under test is a DISAGREEMENT between
# two instruments -- "the gate said ALLOWED and the bar said EXIT 2" -- and if the two halves
# lived in two files their arm definitions would drift, which is P-80's defect wearing evidence
# as a costume. The arms are defined once, below, and the mode decides what is done to each tree.
#
# EVERYTHING HAPPENS IN A THROWAWAY UNIVERSE UNDER $TMPDIR. This instrument never writes to the
# repository it reads from, and it never touches the live hook: the installed `pre-push` on this
# host is gating the fire that dispatched this task, and an instrument that edited it would be
# changing the control it is measuring.
#
# WHY A THROWAWAY BARE REMOTE AND NOT A DRY RUN. `git push --dry-run` still runs `pre-push`, so a
# dry run would have measured the gate. It would NOT have measured what happens after the gate
# says yes, and the finding is exactly "the gate said yes and the tree was red". An arm is only
# meaningful if the push lands.
#
# THE FACTS THIS INSTRUMENT KEEPS APART (T238's rule, adopted rather than pinned):
#     mode=gate  ALLOWED / REFUSED are MEASUREMENTS -- the gate ran and spoke.
#                ZERO gate output lines is NEITHER. It is a hook that did not run, and reporting
#                either verdict from it would be the fail-open under test.
#     mode=bar   the bar's exit status is reported ONLY beside the COUNT of `probe = ` lines it
#                PRINTED. Four exit-2 paths run before the probe prints, so an ABSENT probe line
#                is not `down`; it is "a HARD guard refused and no verdict is available" (P-84).
#                PRESENCE IS READ BEFORE VALUE, here as everywhere.
#     exit 9x    the universe could not be built, or a calibration failed. Never an arm verdict.
#
# BOTH CALIBRATIONS RUN BEFORE ANY mode=gate ARM RESULT IS REPORTED (P-72 and P-98):
#     CALIBRATION+  the installed gate is seen to REFUSE a gitlink. Without it, ALLOWED is
#                   indistinguishable from a hook that never ran.
#     CALIBRATION-  the installed gate is seen to ALLOW an honest driver state edit. Without it,
#                   REFUSED is indistinguishable from a gate that refuses everything.
#
# ENGINE (P-33/P-53): bash, git, tar, POSIX grep/sed. Declared, not assumed. No `git grep` runs
# here, so P-53's backslash-class trap cannot apply.
# =============================================================================================
set -u

ME='drive-arms'
# T465 -- THE FIRE LOCK'S REPO-RELATIVE PATH, ASSEMBLED. Same reason, and the same shape, as
# `TCLEAF` below: this file is a TRACKED `.softhouse/*.sh` instrument, so a spelt
# `.softhouse/`-rooted literal is a row in T316's dead-path frontier. The lock is tracked ONLY
# WHILE A FIRE HOLDS IT and `release_lock` deletes-and-commits it at every fire exit, so a spelt
# literal here is a row that ARRIVES at every fire exit. T465 measured the whole population at
# 17 rows and drove it BOTH WAYS -- pinned at 108 the guard refuses with added=17 after a fire
# exit, pinned at 125 it refuses with removed=17 during a fire -- i.e. the frontier has NO FIXED
# POINT while the path is spelt, so pinning is not available and this is repaired at the
# instrument. Drive and member set: .softhouse/capture/t465-lock-frontier/
LOCKLEAF='LOCK'
LOCK_REL=".softhouse/$LOCKLEAF"
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

SRCREV="${1:-}"
LABEL="${2:-}"
OUT="${3:-}"
MODE="${4:-}"
FILTER="${5:-.}"
[ -n "$SRCREV" ] && [ -n "$LABEL" ] && [ -n "$OUT" ] && [ -n "$MODE" ] \
  || die 90 "usage: drive-arms.sh <source-rev> <label> <outdir> <gate|bar> [arm-filter]"
case "$MODE" in gate|bar) : ;; *) die 90 "unknown mode '$MODE'. Use gate or bar." ;; esac

SRC="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die 90 "\`git rev-parse --show-toplevel\` failed. Not inside a work tree."
[ -n "$SRC" ] || die 90 "empty repository root."
SRCSHA="$(git -C "$SRC" rev-parse --verify --quiet "$SRCREV^{commit}")" \
  || die 90 "'$SRCREV' does not resolve to a commit in $SRC"

mkdir -p "$OUT" || die 90 "could not create the output directory $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter the output directory"

# --------------------------------------------------------------------------------- the universe
U="$(mktemp -d "${TMPDIR:-/tmp}/t453-arms.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
# $U is non-empty by construction and the trap re-tests it: an `rm -rf` on a variable that could
# be empty is how scratch cleanup destroys a repository.
trap '[ -n "${U:-}" ] && [ -d "$U" ] && rm -rf "$U"' EXIT

BARE="$U/origin.git"
WT="$U/wt"
GIT="git -c user.name=t453-drive -c user.email=t453@invalid -c commit.gpgsign=false"

say "mode          $MODE   (arm filter: $FILTER)"
say "source repo   $SRC"
say "source rev    $SRCREV -> $SRCSHA"
say "universe      $U"
say "evidence      $OUT"

# A REAL LOCAL CLONE, WITH THE REAL HISTORY -- not `git archive` into a fresh `git init`.
#
# THE FIRST DRAFT OF THIS INSTRUMENT DID USE archive+squash, AND IT WAS WRONG IN A WAY THAT ONLY
# THE CONTROL ARM COULD SHOW. In mode=bar the CONTROL tree -- an honest `M .softhouse/RESUME.md`
# and nothing else -- came back EXIT 2 with ZERO probe lines, exactly like the hazard arms, on
# `guard_reconciler_ownership`: `could not read tasks.json at 5428c0a4: fatal: invalid object
# name`. That guard reads HISTORICAL COMMITS BY SHA, and a squashed single-commit fixture has
# none of them. A red control makes every red arm uninterpretable -- it is P-98's failure in the
# fixture rather than in the gate -- and it was caught because the control was RUN, not assumed.
$GIT clone --local --quiet --no-checkout "$SRC" "$WT" \
  || die 90 "could not make a local clone of $SRC"
cd "$WT" || die 90 "could not enter the throwaway work tree"
# By SHA, never by name: the source may be a linked worktree whose branch set does not carry the
# name that was asked for, and resolving it there (above) and checking it out here keeps one
# answer to "which tree is this".
$GIT checkout -q -B main "$SRCSHA" || die 90 "could not check out $SRCSHA in the throwaway clone"

# THE CLONE'S `origin` IS THE SOURCE REPOSITORY. It is removed IMMEDIATELY, before anything in
# this file can push. An instrument that pushed its own test commits into the repository it was
# measuring would be worse than no instrument, and "I never call push before line N" is exactly
# the kind of reasoning this program does not accept.
$GIT remote remove origin || die 90 "could not detach the throwaway clone from its source remote"

NTRACK="$($GIT ls-files | LC_ALL=C grep -ac '' || true)"
case "${NTRACK:-}" in ''|*[!0-9]*) NTRACK=0 ;; esac
# P-35: an instrument that inspects nothing passes everything. A base this small is an extraction
# failure and every arm result taken from it would be uninterpretable.
[ "$NTRACK" -ge 100 ] \
  || die 91 "the throwaway base tree tracks $NTRACK file(s). That is an extraction failure, not a small repository."
say "base tree     $NTRACK tracked path(s)"

BASE="$($GIT rev-parse HEAD)"              || die 90 "could not read the base commit"
BASETREE="$($GIT rev-parse 'HEAD^{tree}')" || die 90 "could not read the base tree"
[ "$BASE" = "$SRCSHA" ] || die 90 "the throwaway clone checked out $BASE, not $SRCSHA."

# --------------------------------------------------------------------------------- mode setup
ATTEST=''
if [ "$MODE" = gate ]; then
  $GIT init --bare -q "$BARE"    || die 90 "could not init the throwaway bare remote"
  $GIT remote add origin "$BARE" || die 90 "could not add the throwaway remote"
  # READ BACK WHAT `origin` NOW IS, before the first push. Fail-closed on anything but the bare.
  RURL="$($GIT remote get-url origin)" || die 90 "could not read back the throwaway remote url"
  [ "$RURL" = "$BARE" ] \
    || die 90 "the throwaway remote resolves to '$RURL', not '$BARE'. REFUSING to push anywhere this instrument did not create."
  # The BASE publish happens with the gate NOT YET INSTALLED: it is the whole published history,
  # not a driver push, and gating it would make the fixture a second thing under test.
  $GIT push -q origin main || die 90 "could not publish the base commit to the throwaway remote"

  INST=".softhouse/hooks/install-driver-push-gate.sh"
  [ -f "$INST" ] || die 92 "the installer is absent from tree $SRCSHA: $INST. There is no gate to measure."
  bash "$INST" >"$OUT/00-install.txt" 2>&1 || {
    LC_ALL=C sed -n '1,20p' "$OUT/00-install.txt" >&2
    die 92 "the installer REFUSED in the throwaway universe. No arm below would be measuring a gate."
  }
  [ -f "$WT/.git/hooks/pre-push" ] \
    || die 92 "the installer exited 0 but the pre-push hook is absent. Nothing would gate these pushes."
  say "gate installed $WT/.git/hooks/pre-push"

  GATEDIR="$WT/.git/softhouse-driver-gate"
  mkdir -p "$GATEDIR" || die 92 "could not create the throwaway attestation ledger directory"
  ATTEST="$GATEDIR/attest.tsv"
else
  # THE BAR NEEDS THE PINNED GO TOOLCHAIN, and it is gitignored host state that no `git archive`
  # can carry. It is DERIVED from the SOURCE repository's common dir -- never typed as an
  # absolute literal, which would be host state in a tracked instrument and a dead path on any
  # other machine. Announced, because go-env.sh's own rule is that a substitution is never
  # silent, and because a bar that exited 2 for "no Go toolchain" would be a refusal about the
  # FIXTURE wearing the costume of a refusal about the ARM.
  SRCCOMMON="$(git -C "$SRC" rev-parse --git-common-dir 2>/dev/null)" \
    || die 90 "could not resolve the source repository's git common dir"
  case "$SRCCOMMON" in /*) : ;; *) SRCCOMMON="$SRC/$SRCCOMMON" ;; esac
  # `.softhouse/toolchain` is gitignored, so spelling it as one literal here would add a DEAD
  # row to the frontier this drive's own arm B measures. Assembled from two parts for that
  # reason and no other; repaired rather than pinned, per T323's test.
  TCLEAF='toolchain'
  TOOLCHAIN="$(cd "$SRCCOMMON/.." 2>/dev/null && pwd -P)/.softhouse/$TCLEAF" \
    || die 90 "could not resolve the main checkout beside $SRCCOMMON"
  [ -d "$TOOLCHAIN" ] \
    || die 90 "the pinned Go toolchain is not at $TOOLCHAIN. Running the bar without it would exit 2 about the FIXTURE, and that would be indistinguishable from an arm refusing."
  export GEREGE_TOOLCHAIN="$TOOLCHAIN"
  say "toolchain     $TOOLCHAIN (DERIVED from the source repo's common dir, announced per go-env.sh)"
fi

# seed_full WRITES A ROW WITHOUT RUNNING A BAR. It is a SEED, and saying so here is the whole of
# T465's answer to C-T461-7. The arm it exists for -- CTRL-A-LOCK -- measures what the GATE does
# with an ADDITION from an attested ancestor; it does not, and was never able to, measure what the
# BAR does to the prep tree. C-T461-7 pointed out something sharper, and it was correct: before
# T465, a real FULL attestation for CTRL-A-LOCK's prep tree COULD NOT EXIST, because that tree has
# the fire lock deleted and a full bar on a lock-released tree took the dead-path frontier to
# REFUSED added=17 -- a failed HARD guard, exit 2, no probe line. So the seed was standing in for
# something the program could not produce. T465 repaired the 17 sites, so a lock-released tree is
# no longer red on that guard and the seed now stands in for something achievable. The seed is
# still a seed; that limit is stated rather than left to be re-derived.
# [.softhouse/capture/t453-t450-conditions/CORRECTIONS-T465.md]
seed_full() {
  printf 'FULL\t%s\t%s\t%s\t%s\n' "$1" "$2" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "SEEDED BY T453 drive-arms.sh -- stands in for a bar-attested ancestor" >>"$ATTEST" \
    || die 92 "could not seed the throwaway attestation ledger"
}
[ "$MODE" = gate ] && { seed_full "$BASETREE" "$BASE"; say "ledger seeded FULL $BASETREE"; }

# --------------------------------------------------------------------------------- arm runner
ARMS_RUN=0
RESULTS="$OUT/RESULTS.txt"
: >"$RESULTS" || die 90 "could not create the results file"
{
  printf '# T453 ARM DRIVE -- mode=%s label=%s source=%s (%s)\n' "$MODE" "$LABEL" "$SRCREV" "$SRCSHA"
  printf '# base commit %s  tree %s  (%s tracked paths)\n' "$BASE" "$BASETREE" "$NTRACK"
  if [ "$MODE" = gate ]; then
    printf '# columns: arm | delta | push-exit | verdict | gate-output-lines\n'
  else
    printf '# columns: arm | delta | bar-exit | probe-lines-PRINTED | first refusal\n'
  fi
} >>"$RESULTS"

LAST_VERDICT=''

# build_arm <arm-id> <prep-fragment or ''> <delta-fragment>
#
# `prep` establishes a NEW attested base for an arm. It exists for the one arm that cannot be
# modelled without it: the driver's fire-lock cycle, where `.softhouse/LOCK` is DELETED in one
# push and ADDED in the next, so the delta the gate actually judges is an ADDITION of a path the
# attested ancestor did not carry.
ARMBASE=''; ARMBASETREE=''
build_arm() {
  local id="$1" prep="$2" frag="$3"
  $GIT reset -q --hard "$BASE" || die 93 "arm $id: could not reset the work tree to base"
  $GIT clean -qfd              || die 93 "arm $id: could not clean the work tree"
  ARMBASE="$BASE"; ARMBASETREE="$BASETREE"
  if [ -n "$prep" ]; then
    ( eval "$prep" ) || die 93 "arm $id: the PREP fragment failed."
    $GIT add -A || die 93 "arm $id: \`git add -A\` failed after prep"
    $GIT diff --cached --quiet && die 93 "arm $id: the PREP fragment changed nothing."
    $GIT commit -q -m "T453 arm $id prep" || die 93 "arm $id: could not commit the prep"
    ARMBASE="$($GIT rev-parse HEAD)"              || die 93 "arm $id: could not read the prep commit"
    ARMBASETREE="$($GIT rev-parse 'HEAD^{tree}')" || die 93 "arm $id: could not read the prep tree"
  fi
  ( eval "$frag" ) || die 93 "arm $id: the delta fragment failed. A delta that did not apply is not an arm."
  $GIT add -A || die 93 "arm $id: \`git add -A\` failed"
  $GIT diff --cached --quiet && die 93 "arm $id: the delta produced NO change. An empty arm can be neither red nor green."
  $GIT commit -q -m "T453 arm $id" || die 93 "arm $id: could not commit the delta"
}

# run_arm <arm-id> <description> <prep or ''> <delta>
run_arm() {
  local id="$1" desc="$2" prep="$3" frag="$4" f rc verdict lines probes first
  case "$id" in
    *) printf '%s' "$id" | LC_ALL=C grep -qE "$FILTER" || { say "arm $id  SKIPPED by filter"; return 0; } ;;
  esac

  build_arm "$id" "$prep" "$frag"
  f="$OUT/arm-$id.txt"
  {
    printf '### T453 ARM %s -- %s\n' "$id" "$desc"
    printf '### mode %s   label %s   source %s\n' "$MODE" "$LABEL" "$SRCSHA"
    printf '### attested base %s  tree %s\n' "$ARMBASE" "$ARMBASETREE"
    printf '### delta from the attested base:\n'
    $GIT diff --name-status "$ARMBASE" HEAD | LC_ALL=C sed 's/^/###   /'
    printf '### graded commit %s  tree %s\n' "$($GIT rev-parse HEAD)" "$($GIT rev-parse 'HEAD^{tree}')"
  } >"$f" || die 93 "arm $id: could not write the arm transcript"

  if [ "$MODE" = gate ]; then
    seed_full "$ARMBASETREE" "$ARMBASE"
    $GIT push -q --no-verify --force origin "$ARMBASE:refs/heads/main" \
      || die 93 "arm $id: could not publish the attested base. Setup pushes use --no-verify BY DESIGN: they are scaffolding, not measurements."
    printf '### ---- git push output ----\n' >>"$f"
    $GIT push origin main >>"$f" 2>&1
    rc=$?
    lines="$(LC_ALL=C grep -ac 'driver-push-gate' "$f" || true)"
    case "${lines:-}" in ''|*[!0-9]*) lines=0 ;; esac
    if [ "$lines" -lt 1 ]; then
      LC_ALL=C sed -n '1,40p' "$f" >&2
      die 94 "arm $id: the gate printed NOTHING (push exit $rc). Silence is not a verdict."
    fi
    if [ "$rc" -eq 0 ]; then verdict=ALLOWED
    elif LC_ALL=C grep -aq 'PUSH REFUSED' "$f"; then verdict=REFUSED
    else verdict='PUSH-FAILED-NOT-BY-THE-GATE'
    fi
    LAST_VERDICT="$verdict"
    printf '%-22s | %-56s | %s | %-28s | %s\n' "$id" "$desc" "$rc" "$verdict" "$lines" >>"$RESULTS"
    say "arm $id  push-exit=$rc  $verdict  ($lines gate lines)"
  else
    printf '### ---- .softhouse/conformance.sh output ----\n' >>"$f"
    bash .softhouse/conformance.sh >>"$f" 2>&1
    rc=$?
    # PRESENCE BEFORE VALUE (P-84). The count of probe lines PRINTED is read first and reported
    # beside the exit status; its VALUE is never consulted to decide anything here.
    probes="$(LC_ALL=C grep -ac 'probe = ' "$f" || true)"
    case "${probes:-}" in ''|*[!0-9]*) probes=0 ;; esac
    # THE REFUSAL LINE IS ANCHORED, not merely grepped. An unanchored `REFUSED|FAILED` matches
    # the guards' own EXPLANATORY PROSE -- several guards print sentences containing the word
    # REFUSED on their GREEN path -- and the first draft of this line reported one of those for
    # every arm including the clean controls, which made the column useless. The anchor is the
    # harness's own verdict shape: `conformance: <something> FAILED/REFUSED` at column 0, or a
    # guard's own top-level probe line.
    first="$(LC_ALL=C grep -aE '^conformance: [a-z_]+ (FAILED|REFUSED)|^conformance: the [a-z -]+ guard REFUSED|^T316-DEADPATH-FRONTIER: REFUSED|^namespace: REFUSED' "$f" \
             | LC_ALL=C sed -n '1p' | LC_ALL=C cut -c1-96)"
    [ -n "$first" ] || first='(no refusal line)'
    LAST_VERDICT="exit$rc/probe$probes"
    printf '%-22s | %-56s | %s | %-28s | %s\n' "$id" "$desc" "$rc" "$probes" "$first" >>"$RESULTS"
    say "arm $id  bar-exit=$rc  probe-lines-PRINTED=$probes  :: $first"
  fi
  ARMS_RUN=$((ARMS_RUN + 1))
}

# ------------------------------------------------------------------- CALIBRATION+ (mode=gate)
# C1 is the one check declared unbypassable, and a gitlink is the one tree entry this repository
# has never legitimately carried. If the installed gate does not refuse it, the hook is not
# running and every ALLOWED below would be an artefact of the fixture.
if [ "$MODE" = gate ]; then
  CALOUT="$OUT/01-calibration-plus-C1-gitlink.txt"
  $GIT reset -q --hard "$BASE" || die 92 "calibration: could not reset to base"
  CALDIR="$WT/t453-calibration-submodule"
  $GIT init -q "$CALDIR"                                   || die 92 "calibration: could not init the probe submodule"
  ( cd "$CALDIR" && $GIT commit -q --allow-empty -m probe ) || die 92 "calibration: could not commit in the probe submodule"
  $GIT add "$CALDIR" >/dev/null 2>&1                        || die 92 "calibration: could not stage the gitlink"
  $GIT commit -q -m "T453 calibration: a gitlink"           || die 92 "calibration: could not commit the gitlink"
  $GIT push origin main >"$CALOUT" 2>&1
  CALRC=$?
  if [ "$CALRC" -eq 0 ] || ! LC_ALL=C grep -aq 'C1 REFUSED' "$CALOUT"; then
    LC_ALL=C sed -n '1,40p' "$CALOUT" >&2
    die 92 "CALIBRATION+ FAILED: the installed gate did not refuse a gitlink (push exit $CALRC). No ALLOWED result from this run is interpretable."
  fi
  say "CALIBRATION+  the installed gate REFUSES a gitlink (C1)."
  $GIT reset -q --hard "$BASE" >/dev/null 2>&1
  rm -rf "$CALDIR"
  $GIT reset -q --hard "$BASE" || die 92 "calibration: could not restore the base"
fi

# =============================================================================================
# THE ARMS
# =============================================================================================

# CONTROL 1, run FIRST in gate mode so it doubles as the ANTI-CALIBRATION. An honest driver state
# MODIFICATION must stay ALLOWED and must stay CHEAP, before and after any remedy. A gate that
# refuses everything is as broken as one that refuses nothing (P-98), and every REFUSED below
# would be unearned if this one did not pass.
run_arm CTRL-M-RESUME 'M .softhouse/RESUME.md -- an honest driver state edit' '' '
  printf "\n<!-- T453 control: an honest driver bookkeeping edit. -->\n" >>".softhouse/RESUME.md"
'
if [ "$MODE" = gate ] && [ "$ARMS_RUN" -gt 0 ] && [ "$LAST_VERDICT" != "ALLOWED" ]; then
  die 92 "CALIBRATION- FAILED: the gate REFUSED an honest driver state edit. That is a freeze, not a fix, and no REFUSED result below would be interpretable."
fi
[ "$MODE" = gate ] && [ "$ARMS_RUN" -gt 0 ] && say "CALIBRATION-  the installed gate ALLOWS an honest driver state edit."

# A (MONEY). T450's arm A. A MODIFIED capture record that a stored parity vector NAMES in
# provenance.capture_ref. guard_no_float_in_capture_requests opens exactly those files and grades
# the numeric tokens in their RECORDED-REQUEST blocks, so this is a READ hazard, not an inventory
# one: the STATE-set table's clause (h) described the guard as it stood BEFORE T193 widened it.
#
# THE DELTA, and why THIS one. The recorded-request block is the value of a key named `inputs` or
# `request`; the guard refuses a numeric token there that a binary-double round trip REWRITES.
# `"disbursementAmount": "100"` is a STRING and is byte-preserved by construction -- the shape
# every Capture3*.java emits. Re-spelling it as the BARE literal `100.00` is the smallest change
# that makes the record say a different amount than the reference oracle was asked: `100.00` ->
# `100.0`. The substitution is VERIFIED to have happened before the arm proceeds; a delta that
# silently did not apply would be reported below as an arm the gate lawfully allowed.
run_arm A-MONEY-CAPTUREREF 'M a capture record a parity vector cites in provenance.capture_ref' '' '
  m=".softhouse/capture/out/capture-prod3b-raw.json"
  [ -f "$m" ] || exit 1
  LC_ALL=C sed "s/\"disbursementAmount\": \"100\"/\"disbursementAmount\": 100.00/" "$m" >"$m.t453" || exit 1
  cmp -s "$m" "$m.t453" && { rm -f "$m.t453"; exit 1; }
  mv "$m.t453" "$m" || exit 1
'

# B. T450's arm B. An ADDED tracked file under an EXISTING capture directory. Every dead-path
# literal is resolved against the TRACKED UNIVERSE, so an addition can make a pinned-dead literal
# live and SHRINK the frontier -- the mirror image of the deletion clause (j) already excludes.
#
# THE DIRECTORY NAME IS ASSEMBLED AT RUN TIME, and that is T323's lesson applied rather than
# quoted. A tracked `.softhouse/*.sh` naming a path that does not resolve is a DEAD-PATH FRONTIER
# ROW, so an arm that planted its target as a quoted literal would GROW the very frontier its
# sibling arm exists to measure -- exactly what T323's own red drive did, costing two red runs.
# The arm needs *a* directory under capture/ with a name nothing else uses; it never needed that
# spelling to be spelled here.
run_arm B-FRONTIER-CAPTURE 'A a note under an existing capture directory' '' '
  stem="t290-second-rig"
  d=".softhouse/capture/$stem"
  mkdir -p "$d" || exit 1
  printf "T453 arm B: an added tracked file under capture/.\n" >"$d/note.txt"
'

# C2. T450's arm C2. An ADDED capture DIRECTORY. The namespace guard population is exactly the
# first path component under capture/ or reviews/, so a new directory is a new namespace id and
# can collide undocumented.
run_arm C2-NAMESPACE-CAPTURE 'A a NEW capture directory colliding on an existing id' '' '
  stem="t305-second-directory"
  d=".softhouse/capture/$stem"
  mkdir -p "$d" || exit 1
  printf "T453 arm C2: a second directory under an id that already owns one.\n" >"$d/note.md"
'

# D. T453'S OWN ARM, and the one that shows this is not a `capture/` problem. `.softhouse/uat.md`
# is UNTRACKED, is a PINNED DEAD LITERAL, and adding it is ordinary driver work nowhere near
# capture/. It moves the frontier just the same.
run_arm D-FRONTIER-UATMD 'A .softhouse/uat.md -- a pinned dead literal, ordinary driver work' '' '
  leaf="uat.md"
  printf "# UAT\n\nT453 arm D: added by the drive.\n" >".softhouse/$leaf"
'

# CONTROL 2. An ADDED state file that is NOT a pinned dead literal and is not under capture/ or
# reviews/. It must stay ALLOWED, or the remedy has frozen ordinary driver additions rather than
# closing the hazard.
run_arm CTRL-A-OBSERVATION 'A an observation note -- an addition with no inventory hazard' '' '
  d=".softhouse/observations"
  mkdir -p "$d" || exit 1
  printf "T453 control: an added state note that no guard resolves against.\n" >"$d/t453-control-note.md"
'

# CONTROL 3. THE FIRE-LOCK CYCLE, the single most common ADDITION on main -- 34 of the last 400
# non-merge first-parent commits ADD `.softhouse/LOCK`. The prep commit DELETES the tracked lock
# and is attested; the measured push then ADDS it back. This is the arm that decides whether an
# addition rule is a hazard test or a freeze.
run_arm CTRL-A-LOCK 'A .softhouse/LOCK from an attested base without it -- the fire-lock cycle' '
  rm -f "$LOCK_REL" || exit 1
' '
  printf "fire 20260829-t453-control\nheld-by: T453 drive control\n" >"$LOCK_REL"
'

# --------------------------------------------------------------------------------- report
[ "$ARMS_RUN" -gt 0 ] || die 91 "ZERO arms ran (filter '$FILTER'). There is nothing to report, and that is not a clean result."
say ""
say "T453-ARM-DRIVE: mode=$MODE label=$LABEL source=$SRCSHA arms=$ARMS_RUN"
LC_ALL=C sed -n '1,200p' "$RESULTS"
exit 0
