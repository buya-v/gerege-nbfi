#!/usr/bin/env bash
# =============================================================================================
# T444 -- THE INDEPENDENT REVIEW DRIVE for T431 / C-T407-1.
#
# Written from my own reading of `guard_guards_dir_registration`, not lifted from T431's
# instrument. It reproduces T431's four fail-opens with MY OWN construction (different
# directory leaves, different member names), and then adds the arms T431 did NOT drive:
#
#   THE CONVERSE RISK -- does the fix now REFUSE HONEST WORK?
#     LEGA   honest member, witness = independent tracked REGULAR file, PLAIN ASCII name
#     LEGC   the SAME, but the witness filename is CYRILLIC (гэрчилгээ.txt).
#            Non-ASCII filenames are ordinary in this program. If this is REFUSED, the fix
#            (or the tree it lands on) refuses honest work.
#     LEGM   honest member, witness named in Mongolian Cyrillic, MEMBER also non-ASCII
#
#   T431's DISCLOSED-BUT-UNDRIVEN BOUNDS
#     NLMEM  a tracked member under .softhouse/guards whose own filename contains 0x0A.
#            T431 bound 1: "the member enumeration `while IFS= read -r rel` is a different
#            matter and I did not drive it." Driven here. FAIL-OPEN if the member is silently
#            dropped from the population; fail-CLOSED if it refuses.
#     GITL   a GITLINK (submodule) entry under .softhouse/guards whose path ends in `.sh`.
#            T431 bound 2. Two variants: an arbitrary basename, and a basename that IS
#            mentioned in conformance.sh (so the invocation test is satisfied by a name that
#            points at a submodule pointer rather than at any reviewable source).
#     TWOROW a member carrying TWO REACHED-BY rows. T431 bound 6: `grep -m1` grades the first.
#
#   THE ATTACK ARMS (reproduction of T431's claims, my construction)
#     X   :(literal)P + decoy       XT  :(top,literal)P + decoy
#     XI  :(literal,icase)P + decoy XQ  C-QUOTED witness + decoy at the quoted literal name
#     XQ0 C-QUOTED witness, NO decoy
#   Z   unmutated control.
#
# DISCIPLINE
#   * bash, never sh. Clone --no-hardlinks, mutate, `git add -A` AND COMMIT, assert clean.
#   * PROBE PRESENCE IS TESTED BEFORE ITS VALUE.
#   * Preconditions are asserted inside the mutation.
#   * WORK ROOT AND SOURCE REPO ARE ARGUMENTS. No literal shared-temp path is bound to a name
#     anywhere in this file -- that would add a row to the pinned host-state census.
#   * Every planted repo-rooted path is assembled at run time from a variable plus a leaf, so
#     this file contributes no concrete dead literal to the dead-path frontier.
#
# USAGE: bash drive-t444.sh <workroot> <srcrepo> <ref> [arm ...]
# =============================================================================================
set -u

WORK="${1:?usage: drive-t444.sh <workroot> <srcrepo> <ref> [arm ...]}"
SRC="${2:?usage: drive-t444.sh <workroot> <srcrepo> <ref> [arm ...]}"
REF="${3:?usage: drive-t444.sh <workroot> <srcrepo> <ref> [arm ...]}"
shift 3
WANT_ARMS="$*"

if [ -e "$WORK" ]; then echo "T444 drive: work root $WORK exists; refusing to reuse" >&2; exit 2; fi
mkdir -p "$WORK" || exit 2

PASSES=0; FAILS=0
SH_REL=".softhouse"
GUARDS_REL="$SH_REL/guards"
CONF_REL="$SH_REL/conformance.sh"
MARKER="GUARDS-DIR-REGISTRATION:"
directive() { printf '# %s REACHED-BY %s\n' "$MARKER" "$1"; }

PIN_LINE='git ls-files -s -- ":(literal)$self_norm" 2>/dev/null'
EMPTY_LINE='elif [ -z "$self_stat" ]; then'
RT_LINE='elif [ "$self_path" != "$self_norm" ]; then'
RT_DEAD='elif [ "$self_path" != "$self_path" ]; then'

subst_once() {
  local f="$1" old="$2" new="$3" tmp n
  n="$(LC_ALL=C grep -cF -- "$old" "$f")" || return 1
  [ "$n" = "1" ] || { echo "    subst_once: '$old' occurs $n times, want 1" >&2; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/t444-subst.XXXXXXXX")" || return 1
  LC_ALL=C awk -v old="$old" -v new="$new" '
    { i = index($0, old)
      if (i > 0) $0 = substr($0, 1, i-1) new substr($0, i + length(old))
      print }' "$f" > "$tmp" || return 1
  LC_ALL=C grep -qF -- "$new" "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$f"
}

_n_match() {  # <work> <pathspec>  -> count
  ( cd "$1" && git ls-files -s -- "$2" 2>/dev/null | LC_ALL=C grep -c . )
}

# ---------------------------------------------------------------------------------------------
# ATTACK BUILDER -- my own construction of T407/T431's route.
# ---------------------------------------------------------------------------------------------
X_DIR="zz-t444x"; X_MEM="zz-t444x-member.sh"
X_AMBIG='w?.txt'; X_DECOY='w1.txt'   # '1' (0x31) sorts before '?' (0x3F)
_build_x() {  # <work> <prefix> <decoy yes|no>
  local W="$1" pfx="$2" decoy="$3" d="$GUARDS_REL/$X_DIR" typed
  mkdir -p "$W/$d" || return 1
  typed="$pfx$d/$X_AMBIG"
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- PLANTED, UNWIRED. Nothing in the harness runs it.\n' "$X_MEM"
    directive "$typed"
    printf 'exit 0\n'; } > "$W/$d/$X_MEM" || return 1
  ( cd "$W/$d" && ln -s "$X_MEM" "$X_AMBIG" ) || return 1
  [ -L "$W/$d/$X_AMBIG" ] || return 1
  if [ "$decoy" = yes ]; then
    printf 'T444 decoy. Honest content. It exists only so the witness pathspec matches TWICE.\n' \
      > "$W/$d/$X_DECOY" || return 1
  fi
  # A REAL TRACKED DIRECTORY literally named by the magic prefix, so `-f` on the TYPED
  # spelling passes.
  mkdir -p "$W/$pfx$d" || return 1
  printf 'T444: the file that makes the -f test on the TYPED magic-prefixed spelling pass.\n' \
    > "$W/$pfx$d/$X_AMBIG" || return 1
  [ -f "$W/$typed" ] || { echo "    -f on typed spelling FAILED: $typed" >&2; return 1; }
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  local n em
  n="$(_n_match "$W" "$d/$X_AMBIG")"
  em="$( cd "$W" && git ls-files --error-unmatch -- "$typed" 2>/dev/null | LC_ALL=C grep -c . )"
  [ "$em" = "1" ] || { echo "    precondition: --error-unmatch typed -> $em, want 1" >&2; return 1; }
  if [ "$decoy" = yes ]; then
    [ "$n" = "2" ] || { echo "    precondition: de-magicked lookup -> $n, want 2" >&2; return 1; }
  else
    [ "$n" = "1" ] || { echo "    precondition: de-magicked lookup -> $n, want 1" >&2; return 1; }
  fi
}
m_x()  { _build_x "$1" ':(literal)'       yes; }
m_xt() { _build_x "$1" ':(top,literal)'   yes; }
m_xi() { _build_x "$1" ':(literal,icase)' yes; }

# ---- C-QUOTING ROUTE
Q_DIR="zz-t444q"; Q_MEM="zz-t444q-member.sh"
_build_q() {  # <work> <plant yes|no>
  local W="$1" plant="$2" d="$GUARDS_REL/$Q_DIR" na typed qdir qleaf norm n
  na="$(printf 'v\303\244.txt')"          # v<U+00E4>.txt -- bytes assembled at run time
  typed="$d/$na"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- PLANTED, UNWIRED.\n' "$Q_MEM"
    directive "$typed"
    printf 'exit 0\n'; } > "$W/$d/$Q_MEM" || return 1
  ( cd "$W/$d" && ln -s "$Q_MEM" "$na" ) || return 1
  [ -f "$W/$typed" ] || return 1
  if [ "$plant" = yes ]; then
    qdir="$W/\"$d"
    qleaf='v\303\244.txt"'
    mkdir -p "$qdir" || return 1
    printf 'T444 arm XQ decoy: its LITERAL NAME is the C-quoted rendering. It names %s.\n' \
      "$Q_MEM" > "$qdir/$qleaf" || return 1
  fi
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  norm="$( cd "$W" && git ls-files --error-unmatch -- "$typed" 2>/dev/null )"
  case "$norm" in '"'*) : ;; *) echo "    XQ: self_norm not C-quoted: <$norm>" >&2; return 1 ;; esac
  n="$( cd "$W" && git ls-files -s -- ":(literal)$norm" 2>/dev/null | LC_ALL=C grep -c . )"
  if [ "$plant" = yes ]; then [ "$n" = "1" ] || { echo "    XQ: pinned lookup -> $n want 1" >&2; return 1; }
  else                        [ "$n" = "0" ] || { echo "    XQ0: pinned lookup -> $n want 0" >&2; return 1; }
  fi
}
m_xq()  { _build_q "$1" yes; }
m_xq0() { _build_q "$1" no; }

# ---------------------------------------------------------------------------------------------
# THE HONEST-WORK ARMS. Member and witness are BOTH ordinary regular tracked files, the
# witness is byte-different from the member and names it. Nothing here is an attack.
# ---------------------------------------------------------------------------------------------
_build_legit() {  # <work> <dirleaf> <memleaf> <witleaf>
  local W="$1" dl="$2" ml="$3" wl="$4" d
  d="$GUARDS_REL/$dl"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted checker with an HONEST registration.\n' "$ml"
    directive "$d/$wl"
    printf 'exit 0\n'; } > "$W/$d/$ml" || return 1
  { printf 'T444 witness: an independent tracked REGULAR file whose only job is to name the\n'
    printf 'checker %s. It is not a symlink, not a copy, and not a hard link.\n' "$ml"
  } > "$W/$d/$wl" || return 1
  ! cmp -s "$W/$d/$ml" "$W/$d/$wl" || return 1
  [ ! -L "$W/$d/$wl" ] || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  local n; n="$(_n_match "$W" "$d/$wl")"
  [ "$n" = "1" ] || { echo "    legit: witness lookup -> $n, want 1" >&2; return 1; }
}
m_lega() { _build_legit "$1" "zz-t444a" "zz-t444a-member.sh" "w-a.txt"; }
m_legc() { _build_legit "$1" "zz-t444c" "zz-t444c-member.sh" "$(printf '\320\263\321\215\321\200\321\207\320\270\320\273\320\263\321\215\321\215.txt')"; }
m_legm() { _build_legit "$1" "$(printf '\321\205\320\260\320\273\321\202')" "zz-t444d-member.sh" "$(printf '\320\263\321\215\321\200\321\207.txt')"; }

# ---------------------------------------------------------------------------------------------
# BOUND 1 -- A MEMBER WHOSE OWN FILENAME CONTAINS A NEWLINE.
# ---------------------------------------------------------------------------------------------
m_nlmem() {
  local W="$1" d nl ml
  d="$GUARDS_REL/zz-t444n"
  nl="$(printf 'zz-t444n\nmember.sh')"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# PLANTED, UNWIRED, and its own filename carries a NEWLINE. Nothing runs it.\n'
    printf 'exit 0\n'; } > "$W/$d/$nl" || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  # PRECONDITION: it really is tracked, and it really is in the guard's population selector.
  local n
  n="$( cd "$W" && git ls-files -- ":(glob)$GUARDS_REL/"'**/*.sh' 2>/dev/null \
        | LC_ALL=C grep -c 'zz-t444n' )"
  [ "$n" = "1" ] || { echo "    NLMEM: not in population selector ($n)" >&2; return 1; }
  ml="$( cd "$W" && git ls-files -- ":(glob)$GUARDS_REL/"'**/*.sh' 2>/dev/null \
        | LC_ALL=C grep 'zz-t444n' )"
  echo "    NLMEM: population renders it as: $ml" >&2
}

# ---------------------------------------------------------------------------------------------
# BOUND 2 -- A GITLINK ENTRY UNDER .softhouse/guards WHOSE PATH ENDS IN `.sh`.
# ---------------------------------------------------------------------------------------------
_build_gitl() {  # <work> <basename>
  local W="$1" bn="$2" d sub n mode
  d="$GUARDS_REL/zz-t444g"
  sub="$W/$d/$bn"
  mkdir -p "$sub" || return 1
  ( cd "$sub" && git init -q . \
      && printf 'PLANTED SUBMODULE. Its content is NOT in the outer repository.\n' > README \
      && git add -A \
      && git -c user.email=t444@x -c user.name=t444 commit -q -m sub ) >/dev/null 2>&1 || return 1
  ( cd "$W" && git -c protocol.file.allow=always submodule add -q "./$d/$bn" "$d/$bn" ) >/dev/null 2>&1 \
    || ( cd "$W" && git add "$d/$bn" ) >/dev/null 2>&1 || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  mode="$( cd "$W" && git ls-files -s -- "$d/$bn" 2>/dev/null | LC_ALL=C sed -n '1s/ .*//p' )"
  [ "$mode" = "160000" ] || { echo "    GITL: mode is '$mode', want 160000" >&2; return 1; }
  n="$( cd "$W" && git ls-files -- ":(glob)$GUARDS_REL/"'**/*.sh' 2>/dev/null \
        | LC_ALL=C grep -c "zz-t444g/$bn" )"
  [ "$n" = "1" ] || { echo "    GITL: gitlink NOT in population selector ($n)" >&2; return 1; }
  echo "    GITL: gitlink mode 160000 IS in the population as $d/$bn" >&2
}
m_gitl()  { _build_gitl "$1" "zz-t444g-sub.sh"; }
# A gitlink whose BASENAME is one the harness already invokes, so the invocation test is
# satisfied by a name that resolves to a submodule pointer rather than to any reviewable source.
m_gitl2() {
  local W="$1" bn
  bn="$( cd "$W" && git ls-files -- ":(glob)$GUARDS_REL/"'**/*.sh' 2>/dev/null \
         | LC_ALL=C sed -n '1s#.*/##p' )"
  [ -n "$bn" ] || return 1
  echo "    GITL2: borrowing the basename of an existing member: $bn" >&2
  _build_gitl "$W" "$bn"
}

# ---------------------------------------------------------------------------------------------
# BOUND 6 -- TWO REACHED-BY ROWS. `grep -m1` grades the FIRST.
# ---------------------------------------------------------------------------------------------
_build_tworow() {  # <work> <order: HONEST_FIRST|HOSTILE_FIRST>
  local W="$1" ord="$2" d ml wl
  d="$GUARDS_REL/zz-t444r"; ml="zz-t444r-member.sh"; wl="w-r.txt"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- PLANTED, UNWIRED, carrying TWO REACHED-BY rows.\n' "$ml"
    if [ "$ord" = HONEST_FIRST ]; then directive "$d/$wl"; directive "$d/self.txt"
    else                              directive "$d/self.txt"; directive "$d/$wl"; fi
    printf 'exit 0\n'; } > "$W/$d/$ml" || return 1
  { printf 'T444 arm TWOROW: an independent tracked regular witness naming %s.\n' "$ml"
  } > "$W/$d/$wl" || return 1
  ( cd "$W/$d" && ln -s "$ml" self.txt ) || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  local n; n="$( LC_ALL=C grep -c "$MARKER" "$W/$d/$ml" )"
  [ "$n" = "2" ] || { echo "    TWOROW: $n directive rows, want 2" >&2; return 1; }
}
m_2row_h() { _build_tworow "$1" HONEST_FIRST; }
m_2row_x() { _build_tworow "$1" HOSTILE_FIRST; }

m_none() { : "$1"; return 0; }
m_rvq()  { subst_once "$1/$CONF_REL" "$RT_LINE" "$RT_DEAD" || return 1; m_xq "$1"; }

# ---------------------------------------------------------------------------------------------
# ARM RUNNER
# ---------------------------------------------------------------------------------------------
arm() {  # <name> <want_exit> <want_probe> <fn>
  local name="$1" want_exit="$2" want_probe="$3" fn="$4"
  local W out rc probe dirty census verdict reason
  if [ -n "$WANT_ARMS" ]; then
    case " $WANT_ARMS " in *" $name "*) : ;; *) return 0 ;; esac
  fi
  W="$WORK/$name"
  rm -rf "$W"
  git clone --no-hardlinks -q "$SRC" "$W" >/dev/null 2>&1 || {
    printf '%-40s CLONE-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }
  ( cd "$W" && git checkout -q "$REF" ) >/dev/null 2>&1 || {
    printf '%-40s CHECKOUT-FAILED %s\n' "$name" "$REF"; FAILS=$((FAILS+1)); return 0; }
  "$fn" "$W" || { printf '%-40s MUTATION-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }
  ( cd "$W" && git add -A \
      && git -c user.email=t444@x -c user.name=t444 commit -q -m "$name" ) >/dev/null 2>&1
  dirty="$( cd "$W" && git status --porcelain )"
  out="$WORK/$name.out"
  ( cd "$W" && bash .softhouse/conformance.sh ) > "$out" 2>&1
  rc=$?
  # P-84: PRESENCE of the probe line before any value is read.
  if [ "$(LC_ALL=C grep -c 'probe = ' "$out")" -gt 0 ]; then probe=PRESENT; else probe=ABSENT; fi
  census="$(LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$out" \
              | LC_ALL=C sed 's/.*GUARDS-DIR-REGISTRATION: //')"
  reason="$(LC_ALL=C grep -m1 -E 'THAT WITNESS IS A SYMLINK|MORE THAN ONE TRACKED PATH|DID NOT ROUND-TRIP|matched NO INDEX ENTRY|DOES NOT NAME|which is NOT TRACKED|IS INVOKED BY NOTHING|RESOLVES TO NO INDEX ENTRY|RESOLVES TO MORE THAN ONE INDEX|IS A SYMLINK, and a symlink|population is EMPTY' "$out" | LC_ALL=C sed 's/^ *conformance: *//')"
  verdict=PASS
  [ "$rc" = "$want_exit" ]     || verdict=FAIL
  [ "$probe" = "$want_probe" ] || verdict=FAIL
  [ -z "$dirty" ]              || verdict=FAIL
  printf '%-40s exit=%-2s(w %-2s) probe=%-7s(w %-7s) dirty=%-3s >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "${dirty:+YES}${dirty:-no}" "$verdict"
  printf '    census: %s\n' "${census:-<none printed>}"
  printf '    reason: %s\n' "${reason:-<no registration refusal printed>}"
  if [ "$verdict" = FAIL ]; then FAILS=$((FAILS+1)); else PASSES=$((PASSES+1)); fi
}

echo "=== T444 DRIVE -- src=$SRC ref=$REF arms=${WANT_ARMS:-ALL} work=$WORK ==="
echo "git: $(git --version)"
PROBE="$WORK/_mode"
git clone --no-hardlinks -q "$SRC" "$PROBE" >/dev/null 2>&1 || { echo "cannot clone"; exit 2; }
( cd "$PROBE" && git checkout -q "$REF" ) >/dev/null 2>&1 || { echo "cannot checkout"; exit 2; }
echo "ref HEAD: $( cd "$PROBE" && git log --oneline -1 )"
HAS_PIN=no;   LC_ALL=C grep -qF -- "$PIN_LINE"   "$PROBE/$CONF_REL" && HAS_PIN=yes
HAS_EMPTY=no; LC_ALL=C grep -qF -- "$EMPTY_LINE" "$PROBE/$CONF_REL" && HAS_EMPTY=yes
HAS_RT=no;    LC_ALL=C grep -qF -- "$RT_LINE"    "$PROBE/$CONF_REL" && HAS_RT=yes
echo "MODE detected from the ref's OWN BLOB: pin=$HAS_PIN empty=$HAS_EMPTY round-trip=$HAS_RT"
if [ "$HAS_PIN$HAS_EMPTY$HAS_RT" = "yesyesyes" ]; then MODE=FIXED; else MODE=UNFIXED; fi
echo "  -> MODE=$MODE"
echo

if [ "$MODE" = UNFIXED ]; then
  arm T444-Z-unmutated                 0 PRESENT m_none
  arm T444-LEGA-ascii-witness          0 PRESENT m_lega
  arm T444-LEGC-CYRILLIC-witness       0 PRESENT m_legc
  arm T444-LEGM-cyrillic-dir-and-wit   0 PRESENT m_legm
  arm T444-X-literal-FAILOPEN          0 PRESENT m_x
  arm T444-XT-top-literal-FAILOPEN     0 PRESENT m_xt
  arm T444-XI-literal-icase-FAILOPEN   0 PRESENT m_xi
  arm T444-XQ-CQUOTED-FAILOPEN         0 PRESENT m_xq
  arm T444-XQ0-cquoted-no-decoy        2 ABSENT  m_xq0
  arm T444-NLMEM-newline-member        2 ABSENT  m_nlmem
  arm T444-GITL-gitlink-member         2 ABSENT  m_gitl
  arm T444-GITL2-gitlink-known-name    2 ABSENT  m_gitl2
  arm T444-2ROWH-honest-first          0 PRESENT m_2row_h
  arm T444-2ROWX-hostile-first         2 ABSENT  m_2row_x
else
  arm T444-Z-unmutated                 0 PRESENT m_none
  arm T444-LEGA-ascii-witness          0 PRESENT m_lega
  arm T444-LEGC-CYRILLIC-witness       0 PRESENT m_legc
  arm T444-LEGM-cyrillic-dir-and-wit   0 PRESENT m_legm
  arm T444-X-literal-REFUSED           2 ABSENT  m_x
  arm T444-XT-top-literal-REFUSED      2 ABSENT  m_xt
  arm T444-XI-literal-icase-REFUSED    2 ABSENT  m_xi
  arm T444-XQ-CQUOTED-REFUSED          2 ABSENT  m_xq
  arm T444-XQ0-cquoted-no-decoy        2 ABSENT  m_xq0
  arm T444-RVQ-kill-roundtrip-REOPENS  0 PRESENT m_rvq
  arm T444-NLMEM-newline-member        2 ABSENT  m_nlmem
  arm T444-GITL-gitlink-member         2 ABSENT  m_gitl
  arm T444-GITL2-gitlink-known-name    2 ABSENT  m_gitl2
  arm T444-2ROWH-honest-first          0 PRESENT m_2row_h
  arm T444-2ROWX-hostile-first         2 ABSENT  m_2row_x
fi

echo
echo "=== T444 DRIVE: $PASSES PASS / $FAILS FAIL of $((PASSES+FAILS)) ==="
exit 0
