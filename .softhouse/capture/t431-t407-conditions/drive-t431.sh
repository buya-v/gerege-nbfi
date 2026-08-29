#!/usr/bin/env bash
# =============================================================================================
# T431 -- THE DRIVE FOR C-T407-1 AND ITS NEIGHBOURS.
#
# SUBJECT. `guard_guards_dir_registration`, the WITNESS side. T375 built two refusals there --
# a symlink witness, and a witness whose tracked blob IS the member's. T404 closed the same
# disablement on the MEMBER side by pinning that lookup to `:(literal)$rel`, disclosed the
# WITNESS-side twin as `FU-T404-1`, and rated it unreachable. T407 reached it. This drive
# re-drives T407's route on today's tree, then asks what that route MISSES BY ONE.
#
# THE ROUTE (T407's arm X, lifted, not re-invented). `-f` runs on the TYPED witness spelling.
# For a pathspec-MAGIC spelling `:(literal)<path>` that string is an ORDINARY RELATIVE
# FILESYSTEM PATH, and an attacker already planting files simply CREATES it as a real tracked
# directory. Then the two git calls disagree, because only the first carries the magic:
#
#   git ls-files --error-unmatch -- ":(literal)<dir>/w?.txt"   ONE line  -> self_multi silent
#   git ls-files -s              -- "<dir>/w?.txt"             TWO lines -> the 100644 decoy
#                                                              sorts first, so the mode test
#                                                              and the blob test BOTH grade
#                                                              the wrong file
#
# THE ARM SET, AND WHY EACH ONE IS HERE. Arms are grouped by what they are evidence FOR.
#
#   THE ATTACK, AND THE THREE MAGIC SPELLINGS THAT REACH IT
#     X    `:(literal)` + decoy                     RED on main, refused after
#     XT   `:(top,literal)` + decoy                 the same hole, a spelling T407 did not try
#     XI   `:(literal,icase)` + decoy               likewise
#   THE CONTROLS THAT SAY "MAGIC CHARACTERS DO NOT GENERALLY BREAK THE GUARD"
#     XS   `:(literal)`, NO decoy                   refused as a symlink witness, both trees
#     XC   plain typed spelling + decoy             refused as multi, both trees
#     XG   `:(glob)` + decoy                        still globs -> multi, both trees
#     XX   `:!` exclusion + decoy                   matches every OTHER path -> multi
#     XA   `:(attr:zz)` + decoy                     matches nothing -> untracked refusal
#     XB   BACKSLASH-escaped + the `-f` pacifier    T404 said `-f` stops this. Once the
#                                                   pacifier is tracked `-f` PASSES, and the
#                                                   route is closed by the MULTI refusal
#                                                   instead. Same conclusion, different reason.
#   WHAT THE `:(literal)` PIN MISSES BY ONE -- T407's FU-T407-1, DRIVEN
#     XQ   C-QUOTED witness + a tracked file whose LITERAL NAME is the C-quoted rendering.
#          The pinned lookup then SUCCEEDS on that decoy. Neither the pin nor an
#          empty-result refusal catches it; only the ROUND-TRIP equality does.
#     XQ0  the same C-quoted witness with NO such decoy -- the empty-result case.
#   THE HEALTHY CONTROLS. A control that refuses everything is the same defect as one that
#   cannot fail (P-98).
#     Z    unmutated
#     Y    an honestly registered checker whose witness is an INDEPENDENT tracked regular file
#     XM   a member whose own path CARRIES the magic spelling, honestly registered -> ACCEPTED
#   P-22 REVERTS, on the fixed tree only, to say which line does what
#     RV1  revert the pin alone           + X    -> caught by the ROUND-TRIP backstop
#     RVQ  remove the round-trip alone    + XQ   -> THE HOLE REOPENS. Independently necessary.
#     RVE  remove the empty refusal alone + XQ0  -> caught by the round-trip. NOT independently
#                                                  necessary; it is a better message. Said so.
#     RV3  remove all three               + X    -> the hole reopens, i.e. main's behaviour
#
# DISCIPLINE, ADOPTED FROM T404 AND T407 RATHER THAN RE-LEARNED.
#   * EVERY ARM RUNS THE WHOLE BAR WITH `bash`, NEVER `sh` (`sh` exits 3 -- a refusal, not a
#     verdict), clones `--no-hardlinks`, mutates, `git add -A` AND COMMITS, and asserts the
#     tree is CLEAN before the bar runs.
#   * PROBE PRESENCE IS READ BEFORE ITS VALUE (P-84).
#   * PRECONDITIONS ARE ASSERTED INSIDE THE MUTATION, so an arm that stopped measuring what it
#     claims fails loudly instead of passing for the wrong reason.
#   * THE WORK ROOT IS UNIQUE PER INVOCATION and an existing root is a REFUSAL (T404's
#     instrument defect). PUT IT OUTSIDE THE REPOSITORY: the capture-rig lint walks
#     recursively rather than via `git ls-files`, so a nested checkout trips a HARD guard.
#   * FREEZE THIS SCRIPT BEFORE RUNNING IT. T404's `evidence/11` records a run where the drive
#     was EDITED WHILE `bash` WAS EXECUTING IT and the interpreter resumed at a stale byte
#     offset (`line 501: r: command not found`). A unique work root does not prevent that.
#   * THE MODE IS DETECTED FROM THE REF'S OWN BLOB and cannot be passed in.
#   * EVERY PLANTED PATH IS ASSEMBLED AT RUN TIME from a directory variable plus a leaf, so
#     this tracked `.sh` carries no quoted repo-rooted literal that fails to resolve and cannot
#     put a row on the dead-path frontier.
#
# USAGE:  T431_WORK=/tmp/... bash drive-t431.sh <repo-path> <git-ref> [arm-name ...]
# =============================================================================================
set -u

SRC="${1:?usage: drive-t431.sh <repo-path> <git-ref> [arm ...]}"
REF="${2:?usage: drive-t431.sh <repo-path> <git-ref> [arm ...]}"
shift 2
WANT_ARMS="$*"

WORK="${T431_WORK:?T431_WORK must name a fresh per-invocation work root, OUTSIDE the repo}"
case "$WORK" in /tmp/*|/private/tmp/*) : ;; *)
  echo "T431 drive: work root must be under /tmp; got $WORK" >&2; exit 2 ;; esac
if [ -e "$WORK" ]; then
  echo "T431 drive: work root $WORK already exists; refusing to reuse it" >&2; exit 2
fi
mkdir -p "$WORK" || exit 2

PASSES=0; FAILS=0

SH_REL=".softhouse"
GUARDS_REL="$SH_REL/guards"
CONF_REL="$SH_REL/conformance.sh"

MEMBER_LEAF="zz-t431-member.sh"
DECOY_WIT_LEAF="w1.txt"      # 0x31 sorts BEFORE '?' (0x3F). That ordering is the mechanism.
AMBIG_WIT_LEAF="w?.txt"
MARKER_WORD="GUARDS-DIR-REGISTRATION:"
directive() { printf '# %s REACHED-BY %s\n' "$MARKER_WORD" "$1"; }

# The three lines this task is about, spelled once each so mode detection and the revert arms
# cannot drift apart.
PIN_LINE='git ls-files -s -- ":(literal)$self_norm" 2>/dev/null'
UNPIN_LINE='git ls-files -s -- "$self_norm" 2>/dev/null'
EMPTY_LINE='elif [ -z "$self_stat" ]; then'
EMPTY_DEAD='elif [ -n "$self_stat" ] && [ -z "$self_stat" ]; then'
RT_LINE='elif [ "$self_path" != "$self_norm" ]; then'
RT_DEAD='elif [ "$self_path" != "$self_path" ]; then'

# ---------------------------------------------------------------------------------------------
# LITERAL, ONE-OCCURRENCE SUBSTITUTION. `sed -i` is not portable and every line rewritten here
# carries `$`, `(`, `[` and `"`. A mutation that silently failed to apply would make its arm
# pass for the wrong reason, so the occurrence count is asserted.
# ---------------------------------------------------------------------------------------------
subst_once() {  # subst_once <file> <literal-old> <literal-new>
  local f="$1" old="$2" new="$3" tmp n
  n="$(LC_ALL=C grep -cF -- "$old" "$f")" || return 1
  [ "$n" = "1" ] || { echo "    subst_once: '$old' occurs $n times, want 1" >&2; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/t431-subst.XXXXXXXX")" || return 1
  LC_ALL=C awk -v old="$old" -v new="$new" '
    { i = index($0, old)
      if (i > 0) $0 = substr($0, 1, i-1) new substr($0, i + length(old))
      print }
  ' "$f" > "$tmp" || return 1
  LC_ALL=C grep -qF -- "$new" "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$f" || return 1
}
revert_pin()   { subst_once "$1/$CONF_REL" "$PIN_LINE"   "$UNPIN_LINE"; }
kill_empty()   { subst_once "$1/$CONF_REL" "$EMPTY_LINE" "$EMPTY_DEAD"; }
kill_rt()      { subst_once "$1/$CONF_REL" "$RT_LINE"    "$RT_DEAD"; }

# ---------------------------------------------------------------------------------------------
# MEASUREMENT HELPERS -- used INSIDE mutations, as preconditions.
# ---------------------------------------------------------------------------------------------
_want_matches() {  # <work> <pathspec> <n>
  local n; n="$( cd "$1" && git ls-files -s -- "$2" 2>/dev/null | LC_ALL=C grep -c . )"
  [ "$n" = "$3" ] || { echo "    precondition: '$2' matched $n, want $3" >&2; return 1; }
}
_want_first_mode() {  # <work> <pathspec> <mode>
  local m; m="$( cd "$1" && git ls-files -s -- "$2" 2>/dev/null | LC_ALL=C sed -n '1s/ .*//p' )"
  [ "$m" = "$3" ] || { echo "    precondition: first mode '$m', want $3" >&2; return 1; }
}
_want_em_lines() {  # <work> <typed spelling> <n>
  local n; n="$( cd "$1" && git ls-files --error-unmatch -- "$2" 2>/dev/null \
                 | LC_ALL=C grep -c . )"
  [ "$n" = "$3" ] || { echo "    precondition: --error-unmatch '$2' -> $n lines, want $3" >&2
                       return 1; }
}

# ---------------------------------------------------------------------------------------------
# MUTATIONS.
# ---------------------------------------------------------------------------------------------
m_none() { : "$1"; return 0; }

# ---- Y: THE HEALTHY CONTROL. Witness is an INDEPENDENT tracked REGULAR file, asserted
# ---- byte-different from the member so it cannot be surviving via the blob refusal by luck.
Y_DIR_LEAF="zz-t431y"; Y_MEMBER_LEAF="zz-t431y-member.sh"; Y_WIT_LEAF="w-y.txt"
m_healthy() {
  local W="$1" d="$GUARDS_REL/$Y_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted checker with an HONEST registration.\n' "$Y_MEMBER_LEAF"
    directive "$d/$Y_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$Y_MEMBER_LEAF" || return 1
  { printf 'T431 arm Y witness: an independent tracked regular file. Its job is to name the\n'
    printf 'checker %s and nothing else.\n' "$Y_MEMBER_LEAF"
  } > "$W/$d/$Y_WIT_LEAF" || return 1
  ! cmp -s "$W/$d/$Y_MEMBER_LEAF" "$W/$d/$Y_WIT_LEAF" || return 1
}

# ---- XM: THE MEMBER, NOT THE WITNESS, CARRIES THE MAGIC SPELLING. Honestly registered. It
# ---- must stay ACCEPTED: T404's member-side pin handles it, and refusing a legitimate name
# ---- would be the wrong repair -- the same argument T404's own arms E and F make.
M_DIR_LEAF="zz-t431m"; M_MEMBER_LEAF='zz-t431m:(literal)x.sh'; M_WIT_LEAF="w-m.txt"
m_magic_member() {
  local W="$1" d="$GUARDS_REL/$M_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# a planted checker whose own PATH carries pathspec magic. Honestly registered.\n'
    directive "$d/$M_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$M_MEMBER_LEAF" || return 1
  { printf 'T431 arm XM witness: an independent tracked regular file naming the checker\n'
    printf '%s, whose path carries a pathspec magic prefix mid-path.\n' "$M_MEMBER_LEAF"
  } > "$W/$d/$M_WIT_LEAF" || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  # PRECONDITION: the magic-named member really is IN the population, or this arm measures
  # nothing at all.
  local n
  n="$( cd "$W" && git ls-files -- ":(glob)$GUARDS_REL/"'**/*.sh' 2>/dev/null \
        | LC_ALL=C grep -cF -- "$M_MEMBER_LEAF" )"
  [ "$n" = "1" ] || { echo "    XM: member not in population ($n)" >&2; return 1; }
}

# ---- X / XT / XI / XS / XC / XG / XX / XA / XB: one builder, so the ONLY difference between a
# ---- refused control and an accepted fail-open is the argument named.
X_DIR_LEAF="zz-t431x"
_build_x() {  # _build_x <work> <prefix-or-PLAIN-or-BSLASH> <decoy:yes|no>
  local W="$1" pfx="$2" decoy="$3" d="$GUARDS_REL/$X_DIR_LEAF" typed
  mkdir -p "$W/$d" || return 1
  case "$pfx" in
    PLAIN)  typed="$d/$AMBIG_WIT_LEAF" ;;
    BSLASH) typed="$d/w\\$AMBIG_WIT_LEAF" ; typed="$d/w\\?.txt" ;;
    *)      typed="$pfx$d/$AMBIG_WIT_LEAF" ;;
  esac
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted, UNWIRED checker. NOTHING in the harness runs it.\n' "$MEMBER_LEAF"
    directive "$typed"
    printf 'exit 0\n'
  } > "$W/$d/$MEMBER_LEAF" || return 1
  # THE WITNESS IS A SYMLINK TO THE MEMBER ITSELF. If this is ACCEPTED the member has vouched
  # for itself, which is the exact amnesty this direction exists to refuse.
  ( cd "$W/$d" && ln -s "$MEMBER_LEAF" "$AMBIG_WIT_LEAF" ) || return 1
  [ -L "$W/$d/$AMBIG_WIT_LEAF" ] || return 1
  if [ "$decoy" = yes ]; then
    { printf 'T431 decoy witness. Entirely honest content. It exists only so that the witness\n'
      printf 'path, handed to git as a pathspec, matches TWICE and sorts FIRST.\n'
    } > "$W/$d/$DECOY_WIT_LEAF" || return 1
  fi
  case "$pfx" in
    PLAIN) : ;;
    BSLASH)
      # THE `-f` PACIFIER. T404 said a backslash-escaped spelling dies at `-f`; a real file of
      # that literal name makes `-f` pass, which is the same move the magic route uses.
      printf 'T431 arm XB: the file that makes -f pass on the BACKSLASH-escaped spelling.\n' \
        > "$W/$d/w\\?.txt" || return 1
      [ -f "$W/$typed" ] || { echo "    XB: -f on the typed spelling FAILED" >&2; return 1; } ;;
    *)
      # A REAL TRACKED DIRECTORY whose NAME is the pathspec magic prefix, so `-f` on the TYPED
      # spelling passes. This is the step T404 did not try.
      mkdir -p "$W/$pfx$d" || return 1
      { printf 'T431: the file that makes the -f existence test on the TYPED, magic-prefixed\n'
        printf 'witness spelling pass. Its CONTENT is never read by the guard.\n'
      } > "$W/$pfx$d/$AMBIG_WIT_LEAF" || return 1
      [ -f "$W/$typed" ] || { echo "    -f on the typed spelling FAILED: $typed" >&2; return 1; }
      ;;
  esac
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  if [ "$decoy" = yes ]; then
    _want_matches "$W" "$d/$AMBIG_WIT_LEAF" 2 || return 1
    _want_first_mode "$W" "$d/$AMBIG_WIT_LEAF" 100644 || return 1
  else
    _want_matches "$W" "$d/$AMBIG_WIT_LEAF" 1 || return 1
    _want_first_mode "$W" "$d/$AMBIG_WIT_LEAF" 120000 || return 1
  fi
  return 0
}
m_x()   { _build_x "$1" ':(literal)'       yes; }
m_xt()  { _build_x "$1" ':(top,literal)'   yes; }
m_xi()  { _build_x "$1" ':(literal,icase)' yes; }
m_xs()  { _build_x "$1" ':(literal)'       no;  }
m_xc()  { _build_x "$1" PLAIN              yes; }
m_xg()  { _build_x "$1" ':(glob)'          yes; }
m_xx()  { _build_x "$1" ':!'               yes; }
m_xa()  { _build_x "$1" ':(attr:zz)'       yes; }
m_xb()  { _build_x "$1" BSLASH             yes; }

# ---- XQ / XQ0: THE C-QUOTING ROUTE. `git ls-files` C-QUOTES a path carrying a non-ASCII byte
# ---- and prints it WRAPPED IN LITERAL DOUBLE QUOTES, so `self_norm` -- the OUTPUT of a
# ---- pathspec lookup -- is not a path at all. XQ plants a tracked file whose LITERAL NAME is
# ---- that C-quoted rendering, which makes even the `:(literal)`-PINNED lookup succeed on the
# ---- WRONG FILE. XQ0 omits it, leaving the lookup empty.
Q_DIR_LEAF="zz-t431q"; Q_MEMBER_LEAF="zz-t431q-member.sh"
_build_q() {  # _build_q <work> <plant-quoted-decoy:yes|no>
  local W="$1" plant="$2" d="$GUARDS_REL/$Q_DIR_LEAF" na typed qdir qleaf
  na="$(printf 'w\303\251.txt')"          # w<U+00E9>.txt, assembled from bytes at run time
  typed="$d/$na"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted, UNWIRED checker. NOTHING in the harness runs it.\n' "$Q_MEMBER_LEAF"
    directive "$typed"
    printf 'exit 0\n'
  } > "$W/$d/$Q_MEMBER_LEAF" || return 1
  ( cd "$W/$d" && ln -s "$Q_MEMBER_LEAF" "$na" ) || return 1
  [ -L "$W/$typed" ] || return 1
  [ -f "$W/$typed" ] || { echo "    XQ: -f on the typed spelling FAILED" >&2; return 1; }
  if [ "$plant" = yes ]; then
    # THE C-QUOTED LITERAL PATH, built from the same pieces: a leading dquote, the escaped
    # bytes, a trailing dquote. Its FIRST component is a directory whose name begins with `"`.
    qdir="$W/\"$d"
    qleaf='w\303\251.txt"'
    mkdir -p "$qdir" || return 1
    { printf 'T431 arm XQ: a tracked file whose LITERAL NAME is the C-quoted rendering of the\n'
      printf 'real witness. It names %s, so the closing grep is satisfied by it.\n' "$Q_MEMBER_LEAF"
    } > "$qdir/$qleaf" || return 1
  fi
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  # PRECONDITIONS. The typed spelling must resolve to exactly ONE entry (so self_multi cannot
  # fire) and that entry must come back C-QUOTED (so self_norm is not a path).
  _want_em_lines "$W" "$typed" 1 || return 1
  local norm; norm="$( cd "$W" && git ls-files --error-unmatch -- "$typed" 2>/dev/null )"
  case "$norm" in '"'*) : ;; *) echo "    XQ: self_norm not C-quoted: <$norm>" >&2; return 1 ;; esac
  local n; n="$( cd "$W" && git ls-files -s -- ":(literal)$norm" 2>/dev/null | LC_ALL=C grep -c . )"
  if [ "$plant" = yes ]; then
    [ "$n" = "1" ] || { echo "    XQ: pinned lookup on quoted norm matched $n, want 1" >&2; return 1; }
  else
    [ "$n" = "0" ] || { echo "    XQ0: pinned lookup on quoted norm matched $n, want 0" >&2; return 1; }
  fi
}
m_xq()  { _build_q "$1" yes; }
m_xq0() { _build_q "$1" no;  }

# ---- P-22 REVERTS. Fixed tree only.
m_rv1() { revert_pin "$1" || return 1; m_x "$1"; }
m_rvq() { kill_rt    "$1" || return 1; m_xq "$1"; }
m_rve() { kill_empty "$1" || return 1; m_xq0 "$1"; }
m_rv3() { revert_pin "$1" || return 1; kill_empty "$1" || return 1; kill_rt "$1" || return 1
          m_x "$1"; }

# ---------------------------------------------------------------------------------------------
# THE ARM RUNNER.  arm <name> <want-exit> <want-probe> <marker-ERE> <census-ERE|-> <fn>
# ---------------------------------------------------------------------------------------------
arm() {
  local name="$1" want_exit="$2" want_probe="$3" marker="$4" census_want="$5" fn="$6"
  local W out rc probe marker_seen census census_seen dirty verdict

  if [ -n "$WANT_ARMS" ]; then
    case " $WANT_ARMS " in *" $name "*) : ;; *) return 0 ;; esac
  fi

  W="$WORK/$name"
  rm -rf "$W"
  git clone --no-hardlinks -q "$SRC" "$W" >/dev/null 2>&1 || {
    printf '%-44s CLONE-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }
  ( cd "$W" && git checkout -q "$REF" ) >/dev/null 2>&1 || {
    printf '%-44s CHECKOUT-FAILED %s\n' "$name" "$REF"; FAILS=$((FAILS+1)); return 0; }

  "$fn" "$W" || { printf '%-44s MUTATION-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }

  ( cd "$W" && git add -A \
      && git -c user.email=t431@x -c user.name=t431 commit -q -m "$name" ) >/dev/null 2>&1
  dirty="$( cd "$W" && git status --porcelain )"

  out="$WORK/$name.out"
  ( cd "$W" && bash .softhouse/conformance.sh ) > "$out" 2>&1
  rc=$?

  # P-84: PRESENCE of the probe line is established BEFORE any value is read.
  if [ "$(LC_ALL=C grep -c 'probe = ' "$out")" -gt 0 ]; then probe=PRESENT; else probe=ABSENT; fi
  if LC_ALL=C grep -Eq -- "$marker" "$out"; then marker_seen=YES; else marker_seen=NO; fi
  census="$(LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$out" \
              | LC_ALL=C sed 's/.*GUARDS-DIR-REGISTRATION: //')"
  if [ "$census_want" = "-" ]; then census_seen=NA
  elif printf '%s\n' "$census" | LC_ALL=C grep -Eq -- "$census_want"; then census_seen=YES
  else census_seen=NO; fi

  verdict=PASS
  [ "$rc" = "$want_exit" ]     || verdict=FAIL
  [ "$probe" = "$want_probe" ] || verdict=FAIL
  [ "$marker_seen" = YES ]     || verdict=FAIL
  [ "$census_seen" = NO ]      && verdict=FAIL
  [ -z "$dirty" ]              || verdict=FAIL

  printf '%-44s exit=%-2s(w %-2s) probe=%-7s(w %-7s) marker=%-3s census=%-3s dirty=%-3s >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "$marker_seen" "$census_seen" \
    "${dirty:+YES}${dirty:-no}" "$verdict"
  printf '    census: %s\n' "${census:-<none printed>}"
  if [ "$verdict" = FAIL ]; then
    FAILS=$((FAILS+1)); echo "    --- transcript tail ---"
    LC_ALL=C tail -25 "$out" | LC_ALL=C sed -n 's/^/    /p'
  else
    PASSES=$((PASSES+1))
  fi
}

echo "=== T431 DRIVE -- src=$SRC ref=$REF arms=${WANT_ARMS:-ALL} work=$WORK ==="
echo "git: $(git --version)"
echo

# THE MODE IS DETECTED FROM THE REF'S OWN BLOB, never passed in.
PROBE_CLONE="$WORK/_mode"
git clone --no-hardlinks -q "$SRC" "$PROBE_CLONE" >/dev/null 2>&1 || {
  echo "cannot clone $SRC" >&2; exit 2; }
( cd "$PROBE_CLONE" && git checkout -q "$REF" ) >/dev/null 2>&1 || {
  echo "cannot check out $REF" >&2; exit 2; }
HAS_PIN=no;   LC_ALL=C grep -qF -- "$PIN_LINE"   "$PROBE_CLONE/$CONF_REL" && HAS_PIN=yes
HAS_EMPTY=no; LC_ALL=C grep -qF -- "$EMPTY_LINE" "$PROBE_CLONE/$CONF_REL" && HAS_EMPTY=yes
HAS_RT=no;    LC_ALL=C grep -qF -- "$RT_LINE"    "$PROBE_CLONE/$CONF_REL" && HAS_RT=yes
echo "MODE (detected from the ref's own blob, not asserted):"
echo "      witness lookup pinned to :(literal) ... $HAS_PIN"
echo "      empty-result refusal present ......... $HAS_EMPTY"
echo "      round-trip refusal present ........... $HAS_RT"
if [ "$HAS_PIN$HAS_EMPTY$HAS_RT" = "yesyesyes" ]; then MODE=FIXED; else MODE=UNFIXED; fi
echo "      -> MODE=$MODE"
echo

if [ "$MODE" = UNFIXED ]; then
  arm T431-Z-healthy-UNMUTATED             0 PRESENT 'guards-dir registration: PASS' \
      'population=6 .*reached-by=1 .*symlink-members=0' m_none
  arm T431-Y-healthy-honest-witness        0 PRESENT 'REACHED-BY .*zz-t431y-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_healthy
  arm T431-XM-MAGIC-NAMED-member-ACCEPTED  0 PRESENT 'REACHED-BY .*zz-t431m' \
      'population=7 .*reached-by=2' m_magic_member
  arm T431-X-literal-FAILOPEN              0 PRESENT 'VERDICT: PASS' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_x
  arm T431-XT-top-literal-FAILOPEN         0 PRESENT 'VERDICT: PASS' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_xt
  arm T431-XI-literal-icase-FAILOPEN       0 PRESENT 'VERDICT: PASS' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_xi
  arm T431-XQ-CQUOTED-FAILOPEN             0 PRESENT 'VERDICT: PASS' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_xq
  arm T431-XS-no-decoy-REFUSED             2 ABSENT  'THAT WITNESS IS A SYMLINK' \
      'population=7' m_xs
  arm T431-XC-plain-REFUSED                2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xc
  arm T431-XG-glob-REFUSED                 2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xg
  arm T431-XX-exclude-REFUSED              2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xx
  arm T431-XA-attr-REFUSED                 2 ABSENT  'which is NOT TRACKED' \
      'population=7' m_xa
  arm T431-XB-backslash-REFUSED            2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xb
  arm T431-XQ0-cquoted-no-decoy-REFUSED    2 ABSENT  'DOES NOT NAME' \
      'population=7' m_xq0
else
  arm T431-Z-healthy-UNMUTATED             0 PRESENT 'guards-dir registration: PASS' \
      'population=6 .*reached-by=1 .*symlink-members=0' m_none
  arm T431-Y-healthy-honest-witness        0 PRESENT 'REACHED-BY .*zz-t431y-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_healthy
  arm T431-XM-MAGIC-NAMED-member-ACCEPTED  0 PRESENT 'REACHED-BY .*zz-t431m' \
      'population=7 .*reached-by=2' m_magic_member
  arm T431-X-literal-REFUSED               2 ABSENT  'THAT WITNESS IS A SYMLINK' \
      'population=7' m_x
  arm T431-XT-top-literal-REFUSED          2 ABSENT  'THAT WITNESS IS A SYMLINK' \
      'population=7' m_xt
  arm T431-XI-literal-icase-REFUSED        2 ABSENT  'THAT WITNESS IS A SYMLINK' \
      'population=7' m_xi
  arm T431-XQ-CQUOTED-REFUSED              2 ABSENT  'DID NOT ROUND-TRIP' \
      'population=7' m_xq
  arm T431-XS-no-decoy-REFUSED             2 ABSENT  'THAT WITNESS IS A SYMLINK' \
      'population=7' m_xs
  arm T431-XC-plain-REFUSED                2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xc
  arm T431-XG-glob-REFUSED                 2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xg
  arm T431-XX-exclude-REFUSED              2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xx
  arm T431-XA-attr-REFUSED                 2 ABSENT  'which is NOT TRACKED' \
      'population=7' m_xa
  arm T431-XB-backslash-REFUSED            2 ABSENT  'MORE THAN ONE TRACKED PATH' \
      'population=7' m_xb
  arm T431-XQ0-cquoted-no-decoy-REFUSED    2 ABSENT  'matched NO INDEX ENTRY' \
      'population=7' m_xq0
  # P-22: which line does what. RV1 and RVE are caught by the OTHER line, and that is stated
  # rather than dressed up as independence.
  arm T431-RV1-revert-pin-RT-CATCHES       2 ABSENT  'DID NOT ROUND-TRIP' \
      'population=7' m_rv1
  arm T431-RVQ-kill-roundtrip-HOLE-REOPENS 0 PRESENT 'VERDICT: PASS' \
      'population=7 .*reached-by=2' m_rvq
  arm T431-RVE-kill-empty-RT-CATCHES       2 ABSENT  'DID NOT ROUND-TRIP' \
      'population=7' m_rve
  arm T431-RV3-revert-ALL-HOLE-REOPENS     0 PRESENT 'VERDICT: PASS' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_rv3
fi

echo
echo "=== T431 DRIVE: $PASSES PASS / $FAILS FAIL of $((PASSES+FAILS)) ==="
[ "$FAILS" -eq 0 ] || exit 1
exit 0
