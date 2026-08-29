#!/bin/bash
# =============================================================================================
# T477 -- THE ARMS.  ONE THROWAWAY CLONE PER ARM, ALWAYS OUTSIDE THE REPOSITORY.
#
#   usage:  arm.sh <ARM> <COMMIT-ISH>
#
# THE FIXTURE, SHARED BY EVERY FORGERY ARM, IS A SMUDGE.  A `filter=` attribute in the clone's
# private `.git/info/attributes` with an inverting clean half, applied to ONE tracked file, so
# that after `git checkout --` the bytes on disk are NOT the committed bytes while
# `git status --porcelain` is EMPTY and `git diff-index` lists nothing.  That is deliberate:
# it is the one forgery shape whose ONLY detector in the shipped harness is the whole-tree
# RECOMPUTE.  The index-bit census cannot see it (there is no bit) and the harness`s own two
# ids cannot see it (the forged file is not the harness).  So an arm that neutralises the
# recompute is an arm that certifies this forgery -- which is exactly what is under test.
#
#   CTL        no forgery, honest interpreter            expect EXIT 0, PASS
#   WDIRTY     an HONEST uncommitted edit to the harness expect EXIT 0, PASS, NAMED and PRINTED
#   SKIPWT     forged harness + --skip-worktree          expect EXIT 2
#   ASSUME     forged harness + --assume-unchanged       expect EXIT 2
#   CTLSMUDGE  forgery, honest interpreter               expect EXIT 2, SUPPRESSED at the victim
#   NOPY       the interpreter path made unreachable     expect EXIT 2, named by the pre-check
#   ECHO       forgery + an ECHO shim first on PATH      the T473 M-2 route
#   SITE       forgery + PYTHONPATH sitecustomize        the same route through the environment
#   HASHER     forgery + a shim that really hashes       the DECLARED BOUND, driven
#
#   env T477_MUT=abs     rewrite a bare `python3 -c` to `/usr/bin/python3 -c` (no flags).
#       T477_MUT=barepy  rewrite `"$recpython" -I -S -c` back to a bare `python3 -c`.
#       T477_MUT=nopy    point ONLY this guard`s interpreter at a path that cannot exist.
#   Both mutate ONLY the recompute`s invocation line and are left UNCOMMITTED, which the
#   harness accepts and prints as an uncommitted edit [the T454 honest-dirty boundary].
#
# THE REPOSITORY IS ENTERED ONCE, FATALLY.  Every listing prints its MATCH COUNT before its
# rows, so an empty list is a number rather than an absence a reader has to interpret.
# =============================================================================================
set -u

ARM="${1:-}"
REV="${2:-HEAD}"
[ -n "$ARM" ] || { echo "usage: arm.sh <ARM> <COMMIT-ISH>" >&2; exit 3; }

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 3
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd) || exit 3
SH=".soft""house"
CONF="$SH/conformance"".sh"

SCR="${T477_WORK:-}"
if [ -z "$SCR" ]; then
  SCR=$(mktemp -d "${TMPDIR:-/tmp}/t477-work.XXXXXXXXXX") || exit 3
fi
export T477_WORK="$SCR"
case "$SCR" in
  "$R"|"$R"/*)
    echo "REFUSED: the scratch root is inside the repository under test: $SCR" >&2
    exit 3 ;;
esac

# T477_TAG names the RUN, not the arm: two runs of the same arm (say, with and without the
# `barepy` mutation) must not share a clone directory, and the second one deleting the first
# one`s tree mid-run would be a measurement nobody took.
TAG="${T477_TAG:-$ARM}"
C="$SCR/clone-$TAG"
rm -rf "$C"
git clone --quiet --no-hardlinks "$R" "$C" || { echo "REFUSED: clone failed." >&2; exit 3; }
git -C "$C" checkout --quiet --detach "$REV" \
  || { echo "REFUSED: cannot check out $REV in the clone." >&2; exit 3; }

echo "=== ARM $ARM  (run tag $TAG) ================================================================"
echo "source repository : $R"
echo "clone             : $C"
echo "checked out       : $REV = $(git -C "$C" rev-parse HEAD)"
echo "harness blob      : $(git -C "$C" rev-parse "HEAD:$CONF")"

# ---- the optional mutation of the recompute`s invocation line ---------------------------
MUT="${T477_MUT:-}"
if [ -n "$MUT" ]; then
  # The pattern must match the invocation in EVERY form it can take -- bare `python3 -c`,
  # `/usr/bin/python3 -c`, and `"$recpython" -c` -- or a mutation that did nothing would be
  # reported with the same `before=1 after=1` as one that worked.
  RECPAT='-c "\$recpy"'
  before=$(LC_ALL=C grep -c -e "$RECPAT" "$C/$CONF" || true)
  beforepy=$(LC_ALL=C grep -c "^  recpython=" "$C/$CONF" || true)
  case "$MUT" in
    abs)
      LC_ALL=C sed -i.bak 's|&& python3 -c "\$recpy"|\&\& /usr/bin/python3 -c "$recpy"|' \
        "$C/$CONF" ;;
    barepy)
      LC_ALL=C sed -i.bak 's|&& "\$recpython" -I -S -c "\$recpy"|\&\& python3 -c "$recpy"|' \
        "$C/$CONF" ;;
    nopy)
      # Point ONLY this guard`s interpreter at a path that cannot exist, so the [ ! -x ]
      # pre-check fires. Every other guard`s /usr/bin/python3 is untouched, which is why the
      # assignment was made a local in the first place.
      LC_ALL=C sed -i.bak "s|recpython='/usr/bin/python3'|recpython='/usr/bin/python3-t477-absent'|" \
        "$C/$CONF" ;;
    *) echo "REFUSED: unknown T477_MUT=$MUT" >&2; exit 3 ;;
  esac
  rm -f "$C/$CONF.bak"
  echo "mutation          : $MUT"
  echo "  invocation lines matching the recompute pattern, before=$before after=$(LC_ALL=C grep -c -e "$RECPAT" "$C/$CONF" || true)"
  echo "  recpython assignment lines,                     before=$beforepy after=$(LC_ALL=C grep -c '^  recpython=' "$C/$CONF" || true)"
  echo "  the lines now read:"
  LC_ALL=C grep -n -e "$RECPAT" "$C/$CONF" | LC_ALL=C sed 's/^/    /'
  LC_ALL=C grep -n '^  recpython=' "$C/$CONF" | LC_ALL=C sed 's/^/    /' || true
fi

# ---- the delimiter the harness under test expects ---------------------------------------
if LC_ALL=C grep -q "read -r -d ''" "$C/$CONF"; then
  export T477_SHIM_D=nul
else
  export T477_SHIM_D=nl
fi
echo "recompute framing : $T477_SHIM_D"

# ---- the forgery fixture -----------------------------------------------------------------
VICTIM=""
case "$ARM" in
  CTL|NOPY) : ;;
  WDIRTY)
    # An HONEST uncommitted edit to the harness. T454`s boundary says this must PASS, be named
    # and be printed; a bar that refuses every dirty tree is a bar that gets switched off.
    printf '\n# T477 WDIRTY: an honest uncommitted edit.\n' >>"$C/$CONF"
    ;;
  SKIPWT|ASSUME)
    # The two routes that leave `git status --porcelain` EMPTY over forged bytes.
    if [ "$ARM" = "SKIPWT" ]; then
      git -C "$C" update-index --skip-worktree -- "$CONF" || exit 3
    else
      git -C "$C" update-index --assume-unchanged -- "$CONF" || exit 3
    fi
    printf '\n# T477 %s: FORGED TEXT, hidden behind an index bit.\n' "$ARM" >>"$C/$CONF"
    ;;
  *)
    VICTIM=$(git -C "$C" ls-files -- "*/evidence/*.txt" | LC_ALL=C sed -n '1p')
    [ -n "$VICTIM" ] || { echo "REFUSED: no victim candidate in the tree." >&2; exit 3; }
    cat >"$SCR/smudge.sh" <<'SM'
#!/bin/bash
cat
echo "T477-FORGED-MARKER"
SM
    cat >"$SCR/clean.sh" <<'CL'
#!/bin/bash
LC_ALL=C sed '/^T477-FORGED-MARKER$/d'
CL
    chmod +x "$SCR/smudge.sh" "$SCR/clean.sh"
    mkdir -p "$C/.git/info"
    printf '%s filter=t477\n' "$VICTIM" >"$C/.git/info/attributes"
    git -C "$C" config filter.t477.clean  "$SCR/clean.sh"
    git -C "$C" config filter.t477.smudge "$SCR/smudge.sh"
    rm -f "$C/$VICTIM"
    git -C "$C" checkout -- "$VICTIM" \
      || { echo "REFUSED: could not materialise the smudged victim." >&2; exit 3; }
    ;;
esac

if [ -n "$VICTIM" ]; then
  echo "victim            : $VICTIM"
  echo "  committed blob                 : $(git -C "$C" rev-parse "HEAD:$VICTIM")"
  echo "  hash-object --no-filters       : $(git -C "$C" hash-object --no-filters -- "$VICTIM")"
  echo "  hash-object (no flag)          : $(git -C "$C" hash-object -- "$VICTIM")"
  echo "  forged marker present on disk  : $(LC_ALL=C grep -c '^T477-FORGED-MARKER$' "$C/$VICTIM" || true)"
fi
echo "git status --porcelain lines      : $(git -C "$C" status --porcelain | LC_ALL=C grep -c '' || true)"
git -C "$C" status --porcelain | LC_ALL=C sed 's/^/    /' || true
echo "git diff-index --name-only lines  : $(git -C "$C" diff-index --name-only HEAD -- | LC_ALL=C grep -c '' || true)"
echo "ls-files -v entries NOT in state H: $(git -C "$C" ls-files -v | LC_ALL=C grep -vc '^H ' || true)"

# ---- the interpreter substitution --------------------------------------------------------
SHIMLOG="$SCR/shimlog-$TAG.txt"
: >"$SHIMLOG"
export T477_SHIM_LOG="$SHIMLOG"
BIN="$SCR/bin-$TAG"
rm -rf "$BIN"; mkdir -p "$BIN"
RUNPATH="$PATH"
RUNPYPATH="${PYTHONPATH:-}"
case "$ARM" in
  ECHO)
    cp "$SELF_DIR/shim-echo.sh" "$BIN/python3"; chmod +x "$BIN/python3"
    RUNPATH="$BIN:$PATH" ;;
  HASHER)
    cp "$SELF_DIR/shim-hasher.sh" "$BIN/python3"; chmod +x "$BIN/python3"
    export T477_SHIM_HIDE="$VICTIM"
    RUNPATH="$BIN:$PATH" ;;
  SITE)
    RUNPYPATH="$SELF_DIR/hijack"
    export T477_SELFREL="$CONF" ;;
esac
echo "PATH shim         : $(ls "$BIN" | LC_ALL=C grep -c '' || true) file(s) in $BIN"
echo "PYTHONPATH        : [$RUNPYPATH]"

# ---- the run -----------------------------------------------------------------------------
LOG="$SCR/log-$TAG.txt"
cd "$C" || { echo "REFUSED: could not enter the clone." >&2; exit 3; }
rc=0
PATH="$RUNPATH" PYTHONPATH="$RUNPYPATH" bash "$CONF" >"$LOG" 2>&1 || rc=$?
if [ ! -s "$LOG" ]; then
  echo "INSTRUMENT FAILURE: the bar produced an EMPTY log. That is not a refusal." >&2
  exit 3
fi
echo
echo "EXIT = $rc"
n=$(LC_ALL=C grep -c 'probe = ' "$LOG" || true)
echo "probe line PRESENCE (grep -c 'probe = ') = $n     <-- PRESENCE, read FIRST"
if [ "$n" -gt 0 ]; then
  echo "probe value = $(LC_ALL=C grep 'probe = ' "$LOG" | LC_ALL=C sed -n 's/.*probe = //p' | tr '\n' ' ')"
fi
echo "VERDICT lines: $(LC_ALL=C grep -c '^VERDICT' "$LOG" || true)"
LC_ALL=C grep '^VERDICT' "$LOG" | LC_ALL=C sed 's/^/    /' || true
echo "shim fired    : $(LC_ALL=C grep -c '' "$SHIMLOG" || true) time(s)"
LC_ALL=C sed 's/^/    /' "$SHIMLOG" || true
echo "guard_harness_text_is_committed REFUSAL lines: $(LC_ALL=C grep -c 'guard_harness_text_is_committed:' "$LOG" || true)"
LC_ALL=C grep 'guard_harness_text_is_committed:' "$LOG" | LC_ALL=C sed 's/^/    /' || true
echo "the guard's own census lines: $(LC_ALL=C grep -c 'LOCAL-STATE\|HARNESS-TEXT\|RECOMPUTE\|this harness ' "$LOG" || true)"
LC_ALL=C grep 'LOCAL-STATE\|HARNESS-TEXT\|RECOMPUTE\|this harness ' "$LOG" | LC_ALL=C sed 's/^/    /' || true
echo "full log kept at: $LOG"
