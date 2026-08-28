#!/usr/bin/env bash
# =============================================================================================
# T407 -- THE INDEPENDENT REVIEWER'S OWN DRIVE FOR T404.
#
# THIS IS NOT T404's SCRIPT AND DOES NOT CALL IT. Every arm below is re-derived from T384's
# and T404's PROSE DESCRIPTION of the mechanism, with DIFFERENT filenames and a DIFFERENT glob
# metacharacter -- T404 used a bracket expression `zz-t404g[1].sh`, this drive uses a question
# mark `zz-t407g?.sh`. If the finding were an artefact of bracket syntax rather than of pathspec
# AMBIGUITY, these arms would not reproduce it.
#
# THE SUBJECT. `guard_guards_dir_registration` handed a member's own path to git as a PATHSPEC.
# A pathspec can match MORE THAN ONE tracked path and the code took the FIRST line, so:
#
#     zz-t407g1.sh   an ORDINARY member with an ENTIRELY HONEST REACHED-BY row -- the decoy
#     zz-t407g?.sh   a TRACKED SYMLINK -- the unwired checker being smuggled in
#
# `git ls-files` prints in byte order and `1` (0x31) sorts before `?` (0x3F), so the decoy is
# line 1: `member_mode` reads `100644` and the symlink refusal never fires, `member_blob` is the
# decoy's and the blob test compares the wrong file. T404's repair pins the lookup to
# `:(literal)` and refuses a multi-line or empty result separately.
#
# THE ARMS THIS DRIVE ADDS THAT T404 DOES NOT HAVE -- X, XS, XC, XF, XFY. They drive
# `FU-T404-1`, the residual T404 disclosed against ITSELF and declined to fix: the WITNESS-side
# second lookup `git ls-files -s -- "$self_norm"` is STILL a pathspec. T404 reasoned that no arm
# could reach it. ARM X REACHES IT, on T404's OWN FIXED TREE, and the whole bar goes GREEN with
# a member vouched for by a SYMLINK TO ITSELF.
#
#   THE ROUTE T404 DID NOT TRY. Its argument was that every non-literal spelling of the witness
#   fails the `-f` existence test, which runs on the TYPED spelling before normalisation. That
#   is true of `?`-globbed and backslash-escaped spellings. It is NOT true of a PATHSPEC-MAGIC
#   spelling, because `$REPO_ROOT/:(literal)<path>` is an ordinary relative filesystem path and
#   an attacker who is planting files can simply CREATE IT -- a real tracked directory named
#   `:(literal).softhouse` with a real tracked file inside it. Then:
#
#     -f  "$REPO_ROOT/:(literal)<dir>/w?.txt"                  PASSES  (the decoy dir is real)
#     git ls-files --error-unmatch -- ":(literal)<dir>/w?.txt"  ONE line -- `:(literal)` magic
#                                                              disables globbing, so `self_multi`
#                                                              never fires and self_norm becomes
#                                                              the bare globby path `<dir>/w?.txt`
#     git ls-files -s -- "<dir>/w?.txt"                        TWO lines -- and THAT call has no
#                                                              `:(literal)`, so the 100644 decoy
#                                                              sorts first and `self_mode` /
#                                                              `self_blob` are the WRONG FILE'S.
#
#   The symlink-WITNESS refusal and the byte-identical-blob refusal are both disabled at once --
#   the identical disablement T404 closed one call earlier on the member side.
#
# X's CONTROLS, SO THE FINDING IS NOT MIS-STATED (the discipline T404's own E and F keep):
#   XS  the same construction WITHOUT the decoy -- one match, `self_mode=120000`, and T375's
#       symlink-witness refusal FIRES. So a symlink witness is not generally accepted.
#   XC  the same construction with the PLAIN (non-magic) typed spelling -- `self_multi` FIRES.
#       So the plain spelling is genuinely closed, exactly as T404 says, and AMBIGUITY REACHED
#       THROUGH A MAGIC SPELLING is the whole of the defect.
#   XF  arm X with the ONE-TOKEN repair applied to the witness lookup in the scratch tree --
#       REFUSED. The repair is sufficient. (Applied ONLY in a scratch clone. This reviewer does
#       not edit `.softhouse/conformance.sh`.)
#   XFY the healthy control Y under that same repair -- still ACCEPTED. The repair refuses
#       nothing legitimate.
#
# EVERY ARM RUNS THE WHOLE BAR WITH `bash`, NEVER `sh` (`sh` exits 3, a refusal, not a verdict).
# EVERY ARM CLONES `--no-hardlinks`, MUTATES, `git add -A` AND COMMITS, AND ASSERTS THE TREE IS
# CLEAN BEFORE THE BAR RUNS. PROBE PRESENCE IS READ BEFORE ITS VALUE (P-84).
#
# THE WORK ROOT IS UNIQUE PER INVOCATION AND AN EXISTING ROOT IS A REFUSAL -- T404's own
# instrument defect, adopted here rather than re-learned.
#
# EVERY PLANTED PATH IS ASSEMBLED AT RUN TIME from a directory variable plus a leaf, so this
# tracked `.sh` under `.softhouse/` carries no QUOTED `.softhouse/`-rooted literal that fails to
# resolve and cannot put a row on T316's dead-path frontier.
#
# USAGE:  bash drive-t407.sh <repo-path> <git-ref> [arm-name ...]
# =============================================================================================
set -u

SRC="${1:?usage: drive-t407.sh <repo-path> <git-ref> [arm ...]}"
REF="${2:?usage: drive-t407.sh <repo-path> <git-ref> [arm ...]}"
shift 2
WANT_ARMS="$*"

WORK="${T407_WORK:?T407_WORK must name a fresh per-invocation work root}"
if [ -e "$WORK" ]; then
  echo "T407 drive: work root $WORK already exists; refusing to reuse it" >&2
  exit 2
fi
mkdir -p "$WORK" || exit 2

PASSES=0
FAILS=0

SH_REL=".softhouse"
GUARDS_REL="$SH_REL/guards"
CONF_REL="$SH_REL/conformance.sh"
MAGIC_DIR=':(literal)'      # the decoy directory prefix, spelled once

Y_DIR_LEAF="zz-t407y"
E_DIR_LEAF="zz-t407e"
F_DIR_LEAF="zz-t407f"
G_DIR_LEAF="zz-t407g"
X_DIR_LEAF="zz-t407x"

Y_MEMBER_LEAF="zz-t407y-member.sh"
Y_WIT_LEAF="w-y.txt"

E_MEMBER_LEAF="zz-t407e?.sh"
E_WIT_LEAF="w-e.txt"

F_LINK_LEAF="zz-t407f?.sh"
F_TARGET_LEAF="target-f.txt"
F_WIT_LEAF="w-f.txt"

G_DECOY_LEAF="zz-t407g1.sh"
G_LINK_LEAF="zz-t407g?.sh"
G_TARGET_LEAF="target-g.txt"
G_WIT1_LEAF="w-g1.txt"
G_WIT2_LEAF="w-g2.txt"

X_MEMBER_LEAF="zz-t407x-member.sh"
X_DECOY_WIT_LEAF="w1.txt"     # 0x31 -- sorts BEFORE '?' (0x3F). That ordering is the mechanism.
X_AMBIG_WIT_LEAF="w?.txt"

MARKER_WORD="GUARDS-DIR-REGISTRATION:"
directive() { printf '# %s REACHED-BY %s\n' "$MARKER_WORD" "$1"; }

# ---------------------------------------------------------------------------------------------
# LITERAL, ONE-OCCURRENCE SUBSTITUTION IN THE SCRATCH HARNESS. `sed -i` is not portable; awk's
# sub() takes an ERE and every line rewritten here contains `*`, `$`, `(` and `"`. A mutation
# that silently failed to apply would make its arm pass for the wrong reason.
# ---------------------------------------------------------------------------------------------
subst_once() {  # subst_once <file> <literal-old> <literal-new>
  local f="$1" old="$2" new="$3" tmp n
  n="$(LC_ALL=C grep -cF -- "$old" "$f")" || return 1
  [ "$n" = "1" ] || { echo "    subst_once: '$old' occurs $n times, want 1" >&2; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/t407-subst.XXXXXXXX")" || return 1
  LC_ALL=C awk -v old="$old" -v new="$new" '
    { i = index($0, old)
      if (i > 0) $0 = substr($0, 1, i-1) new substr($0, i + length(old))
      print }
  ' "$f" > "$tmp" || return 1
  LC_ALL=C grep -qF -- "$new" "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$f" || return 1
}

# The two anchors of T404's repair, and the anchor of the residual FU-T404-1 names.
FIXED_LOOKUP='git ls-files -s -- ":(literal)$rel" 2>/dev/null'
UNFIXED_LOOKUP='git ls-files -s -- "$rel" 2>/dev/null'
FIXED_MULTI='*"$CONF_LF"*) member_multi=1 ;;'
DISARMED_MULTI='*"$CONF_LF"*) member_multi=0 ;;'
WITNESS_LOOKUP='git ls-files -s -- "$self_norm" 2>/dev/null'
WITNESS_LOOKUP_FIXED='git ls-files -s -- ":(literal)$self_norm" 2>/dev/null'

revert_literal()   { subst_once "$1/$CONF_REL" "$FIXED_LOOKUP" "$UNFIXED_LOOKUP"; }
disarm_multi()     { subst_once "$1/$CONF_REL" "$FIXED_MULTI"  "$DISARMED_MULTI"; }
fix_witness_side() { subst_once "$1/$CONF_REL" "$WITNESS_LOOKUP" "$WITNESS_LOOKUP_FIXED"; }

# ---------------------------------------------------------------------------------------------
# MUTATIONS.
# ---------------------------------------------------------------------------------------------
m_none() { : "$1"; return 0; }

# ---- Y: THE HEALTHY CONTROL. An honestly registered checker whose witness is an INDEPENDENT
# ---- TRACKED REGULAR FILE. Must stay ACCEPTED at reached-by=2. A control that refuses
# ---- everything is the same defect as one that cannot fail.
m_healthy() {
  local W="$1" d="$GUARDS_REL/$Y_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted checker with an HONEST registration.\n' "$Y_MEMBER_LEAF"
    directive "$d/$Y_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$Y_MEMBER_LEAF" || return 1
  { printf 'T407 arm Y witness: an independent tracked regular file, not a copy, a hard link\n'
    printf 'or a symlink of the member. Its job is to name the checker %s.\n' "$Y_MEMBER_LEAF"
  } > "$W/$d/$Y_WIT_LEAF" || return 1
  ! cmp -s "$W/$d/$Y_MEMBER_LEAF" "$W/$d/$Y_WIT_LEAF" || return 1
}

# ---- E: CONTROL. A glob-named member whose witness is a PLAIN COPY. Refutes "a glob character
# ---- alone defeats the guard": git tries exact literal equality before wildmatch, so this
# ---- member matches ITSELF, one line, and T375's blob test bites.
m_glob_member_copy_witness() {
  local W="$1" d="$GUARDS_REL/$E_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# a planted UNWIRED checker whose name carries a glob character. Nothing runs it.\n'
    directive "$d/$E_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$E_MEMBER_LEAF" || return 1
  cp "$W/$d/$E_MEMBER_LEAF" "$W/$d/$E_WIT_LEAF" || return 1
  cmp -s "$W/$d/$E_MEMBER_LEAF" "$W/$d/$E_WIT_LEAF" || return 1
  # PRECONDITION: exactly ONE match, or this arm is measuring arm G instead of itself.
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  _want_matches "$W" "$d/$E_MEMBER_LEAF" 1 || return 1
}

# ---- F: CONTROL. The same glob-named shape, but the MEMBER ITSELF is a tracked symlink and
# ---- there is NO second matching path. One match, mode 120000, T375's symlink refusal bites.
m_glob_member_is_symlink() {
  local W="$1" d="$GUARDS_REL/$F_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# The symlink target for T407 arm F. A .txt is not in the population.\n'
    directive "$d/$F_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$F_TARGET_LEAF" || return 1
  { printf 'T407 arm F witness. An independent tracked regular file naming %s.\n' "$F_LINK_LEAF"
  } > "$W/$d/$F_WIT_LEAF" || return 1
  ( cd "$W/$d" && ln -s "$F_TARGET_LEAF" "$F_LINK_LEAF" ) || return 1
  [ -L "$W/$d/$F_LINK_LEAF" ] || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  _want_matches "$W" "$d/$F_LINK_LEAF" 1 || return 1
}

# ---- G: THE FIFTH FAIL-OPEN. The decoy is HONEST -- nothing about it is forged. It exists only
# ---- so the member's own path, handed to git as a pathspec, matches TWICE.
m_ambiguous_symlink_member() {
  local W="$1" d="$GUARDS_REL/$G_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- an ordinary planted checker with an HONEST REACHED-BY row.\n' "$G_DECOY_LEAF"
    directive "$d/$G_WIT1_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$G_DECOY_LEAF" || return 1
  { printf 'T407 arm G witness 1: an independent tracked regular file naming %s.\n' "$G_DECOY_LEAF"
  } > "$W/$d/$G_WIT1_LEAF" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# The symlink target for T407 arm G. A .txt is not in the population.\n'
    directive "$d/$G_WIT2_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$G_TARGET_LEAF" || return 1
  { printf 'T407 arm G witness 2: an independent tracked regular file naming %s.\n' "$G_LINK_LEAF"
  } > "$W/$d/$G_WIT2_LEAF" || return 1
  ( cd "$W/$d" && ln -s "$G_TARGET_LEAF" "$G_LINK_LEAF" ) || return 1
  [ -L "$W/$d/$G_LINK_LEAF" ] || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  # THE PRECONDITIONS THAT MAKE THIS ARM WHAT IT CLAIMS TO BE, MEASURED NOT ASSUMED.
  _want_matches "$W" "$d/$G_LINK_LEAF" 2 || return 1
  _want_literal_matches "$W" "$d/$G_LINK_LEAF" 1 || return 1
  _want_first_mode "$W" "$d/$G_LINK_LEAF" 100644 || return 1
}

# ---- H: C-T384-2. F's construction AND G's together: TWO symlink members in one population.
# ---- The population does not change across the repair; the COUNT must.
m_two_symlink_members() {
  m_glob_member_is_symlink "$1" || return 1
  m_ambiguous_symlink_member "$1" || return 1
}

m_revert_literal_plus_G() { revert_literal "$1" || return 1; m_ambiguous_symlink_member "$1"; }
m_disarm_multi_plus_G()   { disarm_multi   "$1" || return 1; m_ambiguous_symlink_member "$1"; }
m_revert_both_plus_G()    { revert_literal "$1" || return 1; disarm_multi "$1" || return 1
                            m_ambiguous_symlink_member "$1"; }

# ---- X / XS / XC: FU-T404-1, THE WITNESS SIDE. `magic` selects the typed spelling, `decoy`
# ---- selects whether the second matching path exists. Three arms, one builder, so the ONLY
# ---- difference between the refused controls and the accepted fail-open is the variable named.
_build_x() {  # _build_x <work> <magic:yes|no> <decoy:yes|no>
  local W="$1" magic="$2" decoy="$3" d="$GUARDS_REL/$X_DIR_LEAF" typed
  mkdir -p "$W/$d" || return 1
  if [ "$magic" = yes ]; then typed="$MAGIC_DIR$d/$X_AMBIG_WIT_LEAF"
  else                        typed="$d/$X_AMBIG_WIT_LEAF"; fi
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted, UNWIRED checker. NOTHING in the harness runs it.\n' "$X_MEMBER_LEAF"
    directive "$typed"
    printf 'exit 0\n'
  } > "$W/$d/$X_MEMBER_LEAF" || return 1
  # THE WITNESS IS A SYMLINK TO THE MEMBER ITSELF. If this is accepted, the member has vouched
  # for itself -- the exact amnesty the REACHED-BY direction exists to refuse.
  ( cd "$W/$d" && ln -s "$X_MEMBER_LEAF" "$X_AMBIG_WIT_LEAF" ) || return 1
  [ -L "$W/$d/$X_AMBIG_WIT_LEAF" ] || return 1
  if [ "$decoy" = yes ]; then
    { printf 'T407 arm X decoy witness. Entirely honest content. It exists only so that the\n'
      printf 'witness path, handed to git as a pathspec, matches TWICE and sorts FIRST.\n'
    } > "$W/$d/$X_DECOY_WIT_LEAF" || return 1
  fi
  if [ "$magic" = yes ]; then
    # A REAL TRACKED DIRECTORY whose name is the pathspec magic prefix, so that the `-f`
    # existence test on the TYPED spelling PASSES. This is the step T404 did not try.
    mkdir -p "$W/$MAGIC_DIR$d" || return 1
    { printf 'T407 arm X: the file that makes the -f existence test on the TYPED, magic-prefixed\n'
      printf 'witness spelling pass. Its CONTENT is never read by the guard.\n'
    } > "$W/$MAGIC_DIR$d/$X_AMBIG_WIT_LEAF" || return 1
    [ -f "$W/$typed" ] || { echo "    arm X: -f on the typed spelling FAILED" >&2; return 1; }
  fi
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  # PRECONDITIONS, MEASURED. The typed spelling must resolve to exactly ONE tracked path when
  # magic is on (so `self_multi` cannot fire) and to TWO when it is off (so it must).
  local n
  n="$( cd "$W" && git ls-files --error-unmatch -- "$typed" 2>/dev/null | LC_ALL=C grep -c . )"
  if [ "$magic" = yes ]; then
    [ "$n" = "1" ] || { echo "    arm X: typed magic spelling matched $n, want 1" >&2; return 1; }
  else
    [ "$decoy" = yes ] && { [ "$n" = "2" ] || {
      echo "    arm X: typed plain spelling matched $n, want 2" >&2; return 1; }; }
  fi
  if [ "$decoy" = yes ]; then
    _want_matches "$W" "$d/$X_AMBIG_WIT_LEAF" 2 || return 1
    _want_first_mode "$W" "$d/$X_AMBIG_WIT_LEAF" 100644 || return 1
  else
    _want_matches "$W" "$d/$X_AMBIG_WIT_LEAF" 1 || return 1
    _want_first_mode "$W" "$d/$X_AMBIG_WIT_LEAF" 120000 || return 1
  fi
  return 0
}

m_x_failopen()  { _build_x "$1" yes yes; }   # magic spelling + decoy  -> the hole
m_x_symlink()   { _build_x "$1" yes no;  }   # magic spelling, no decoy -> symlink-witness refusal
m_x_plain()     { _build_x "$1" no  yes; }   # plain spelling + decoy   -> self_multi refusal
m_x_repaired()  { fix_witness_side "$1" || return 1; _build_x "$1" yes yes; }
m_y_repaired()  { fix_witness_side "$1" || return 1; m_healthy "$1"; }

# ---------------------------------------------------------------------------------------------
# MEASUREMENT HELPERS -- used inside mutations as PRECONDITIONS.
# ---------------------------------------------------------------------------------------------
_want_matches() {  # <work> <path> <n>
  local n; n="$( cd "$1" && git ls-files -s -- "$2" 2>/dev/null | LC_ALL=C grep -c . )"
  [ "$n" = "$3" ] || { echo "    precondition: '$2' as pathspec matched $n, want $3" >&2; return 1; }
}
_want_literal_matches() {
  local n; n="$( cd "$1" && git ls-files -s -- ":(literal)$2" 2>/dev/null | LC_ALL=C grep -c . )"
  [ "$n" = "$3" ] || { echo "    precondition: '$2' as literal matched $n, want $3" >&2; return 1; }
}
_want_first_mode() {
  local m; m="$( cd "$1" && git ls-files -s -- "$2" 2>/dev/null | LC_ALL=C sed -n '1s/ .*//p' )"
  [ "$m" = "$3" ] || { echo "    precondition: first line mode '$m', want $3" >&2; return 1; }
}

# ---------------------------------------------------------------------------------------------
# THE ARM RUNNER.  arm <name> <want-exit> <want-probe> <marker-ERE> <census-ERE|-> <fn>
# ---------------------------------------------------------------------------------------------
arm() {
  local name="$1" want_exit="$2" want_probe="$3" marker="$4" census_want="$5" fn="$6"
  local W out rc probe marker_seen census census_seen dirty

  if [ -n "$WANT_ARMS" ]; then
    case " $WANT_ARMS " in *" $name "*) : ;; *) return 0 ;; esac
  fi

  W="$WORK/$name"
  rm -rf "$W"
  git clone --no-hardlinks -q "$SRC" "$W" >/dev/null 2>&1 || {
    printf '%-46s CLONE-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }
  ( cd "$W" && git checkout -q "$REF" ) >/dev/null 2>&1 || {
    printf '%-46s CHECKOUT-FAILED %s\n' "$name" "$REF"; FAILS=$((FAILS+1)); return 0; }

  "$fn" "$W" || { printf '%-46s MUTATION-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }

  ( cd "$W" && git add -A \
      && git -c user.email=t407@x -c user.name=t407 commit -q -m "$name" ) >/dev/null 2>&1
  dirty="$( cd "$W" && git status --porcelain )"

  out="$WORK/$name.out"
  ( cd "$W" && bash .softhouse/conformance.sh ) > "$out" 2>&1
  rc=$?

  # P-84: PRESENCE of the probe line is established BEFORE any value is read.
  if [ "$(LC_ALL=C grep -c 'probe = ' "$out")" -gt 0 ]; then probe=PRESENT; else probe=ABSENT; fi
  if LC_ALL=C grep -Eq -- "$marker" "$out"; then marker_seen=YES; else marker_seen=NO; fi
  census="$(LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$out" \
              | LC_ALL=C sed 's/.*GUARDS-DIR-REGISTRATION: //')"
  if [ "$census_want" = "-" ]; then
    census_seen=NA
  elif printf '%s\n' "$census" | LC_ALL=C grep -Eq -- "$census_want"; then
    census_seen=YES
  else
    census_seen=NO
  fi

  local verdict=PASS
  [ "$rc" = "$want_exit" ]     || verdict=FAIL
  [ "$probe" = "$want_probe" ] || verdict=FAIL
  [ "$marker_seen" = YES ]     || verdict=FAIL
  [ "$census_seen" = NO ]      && verdict=FAIL
  [ -z "$dirty" ]              || verdict=FAIL

  printf '%-46s exit=%-2s(w %-2s) probe=%-7s(w %-7s) marker=%-3s census=%-3s dirty=%-3s >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "$marker_seen" "$census_seen" \
    "${dirty:+YES}${dirty:-no}" "$verdict"
  printf '    census: %s\n' "${census:-<none printed>}"
  if [ "$verdict" = FAIL ]; then
    FAILS=$((FAILS+1))
    echo "    --- transcript tail ---"
    LC_ALL=C tail -25 "$out" | LC_ALL=C sed -n 's/^/    /p'
  else
    PASSES=$((PASSES+1))
  fi
}

echo "=== T407 INDEPENDENT DRIVE -- src=$SRC ref=$REF arms=${WANT_ARMS:-ALL} work=$WORK ==="
echo

# The mode is DETECTED FROM THE REF'S OWN BLOB, never passed in.
PROBE_CLONE="$WORK/_mode"
git clone --no-hardlinks -q "$SRC" "$PROBE_CLONE" >/dev/null 2>&1 || {
  echo "cannot clone $SRC" >&2; exit 2; }
( cd "$PROBE_CLONE" && git checkout -q "$REF" ) >/dev/null 2>&1 || {
  echo "cannot check out $REF" >&2; exit 2; }
if LC_ALL=C grep -qF -- "$FIXED_LOOKUP" "$PROBE_CLONE/$CONF_REL"; then MODE=FIXED; else MODE=UNFIXED; fi
echo "MODE: the member-side lookup at $REF is $MODE (detected from its own blob, not asserted)"
echo "      the WITNESS-side lookup is a PATHSPEC in BOTH modes -- that is FU-T404-1."
echo

if [ "$MODE" = UNFIXED ]; then
  arm T407-Z-healthy-UNMUTATED \
      0 PRESENT 'guards-dir registration: PASS' \
      'population=6 .*reached-by=1 .*symlink-members=0' m_none
  arm T407-Y-healthy-honest-witness-ACCEPTED \
      0 PRESENT 'REACHED-BY .*zz-t407y-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_healthy
  arm T407-E-globname-witness-COPY-REFUSED \
      2 ABSENT 'BYTE-IDENTICAL TO THIS MEMBER' \
      'population=7 .*symlink-members=0' m_glob_member_copy_witness
  arm T407-F-globname-member-IS-SYMLINK-REFUSED \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=7 .*symlink-members=1' m_glob_member_is_symlink
  arm T407-G-AMBIGUOUS-symlink-member-FAILOPEN \
      0 PRESENT 'VERDICT: PASS' \
      'population=8 .*reached-by=3 .*symlink-members=0' m_ambiguous_symlink_member
  arm T407-H-TWO-symlink-members-UNDERCOUNTED \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=9 .*symlink-members=1' m_two_symlink_members
  arm T407-X-WITNESS-ambiguity-FAILOPEN \
      0 PRESENT 'REACHED-BY .*zz-t407x-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_x_failopen
  arm T407-XS-witness-symlink-NO-decoy-REFUSED \
      2 ABSENT 'THAT WITNESS IS A SYMLINK' \
      'population=7 .*symlink-members=0' m_x_symlink
  arm T407-XC-witness-PLAIN-spelling-REFUSED \
      2 ABSENT 'MORE THAN ONE TRACKED PATH' \
      'population=7' m_x_plain
else
  arm T407-Z-healthy-UNMUTATED \
      0 PRESENT 'guards-dir registration: PASS' \
      'population=6 .*reached-by=1 .*symlink-members=0' m_none
  arm T407-Y-healthy-honest-witness-ACCEPTED \
      0 PRESENT 'REACHED-BY .*zz-t407y-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_healthy
  arm T407-E-globname-witness-COPY-REFUSED \
      2 ABSENT 'BYTE-IDENTICAL TO THIS MEMBER' \
      'population=7 .*symlink-members=0' m_glob_member_copy_witness
  arm T407-F-globname-member-IS-SYMLINK-REFUSED \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=7 .*symlink-members=1' m_glob_member_is_symlink
  arm T407-G-AMBIGUOUS-symlink-member-REFUSED \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=8 .*symlink-members=1' m_ambiguous_symlink_member
  arm T407-H-TWO-symlink-members-COUNTS-BOTH \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=9 .*symlink-members=2' m_two_symlink_members
  arm T407-R1-REVERT-literal-ONLY-multi-CATCHES \
      2 ABSENT 'RESOLVES TO MORE THAN ONE INDEX' \
      'population=8' m_revert_literal_plus_G
  arm T407-R2-DISARM-multi-ONLY-literal-CATCHES \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=8 .*symlink-members=1' m_disarm_multi_plus_G
  arm T407-R3-REVERT-BOTH-THE-HOLE-REOPENS \
      0 PRESENT 'VERDICT: PASS' \
      'population=8 .*reached-by=3 .*symlink-members=0' m_revert_both_plus_G
  # FU-T404-1, ON T404's OWN FIXED TREE.
  arm T407-X-WITNESS-ambiguity-FAILOPEN \
      0 PRESENT 'REACHED-BY .*zz-t407x-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_x_failopen
  arm T407-XS-witness-symlink-NO-decoy-REFUSED \
      2 ABSENT 'THAT WITNESS IS A SYMLINK' \
      'population=7 .*symlink-members=0' m_x_symlink
  arm T407-XC-witness-PLAIN-spelling-REFUSED \
      2 ABSENT 'MORE THAN ONE TRACKED PATH' \
      'population=7' m_x_plain
  arm T407-XF-witness-literal-REPAIR-REFUSES-X \
      2 ABSENT 'MORE THAN ONE TRACKED PATH|THAT WITNESS IS A SYMLINK' \
      'population=7' m_x_repaired
  arm T407-XFY-healthy-Y-UNDER-the-repair-ACCEPTED \
      0 PRESENT 'REACHED-BY .*zz-t407y-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_y_repaired
fi

echo
echo "=== T407 DRIVE: $PASSES PASS / $FAILS FAIL of $((PASSES+FAILS)) ==="
[ "$FAILS" -eq 0 ] || exit 1
exit 0
