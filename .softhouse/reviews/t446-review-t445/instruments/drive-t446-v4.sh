#!/usr/bin/env bash
# T446 — INDEPENDENT re-derivation of T445's arm table.
#
# Usage:  bash drive-t446.sh <work-root> <source-repo> <ref> <arm> [<arm> ...]
#
# Nothing repo-rooted is written as a literal: every planted path is assembled at run
# time from a variable plus a leaf, so this file plants no dead path in T316's frontier
# and binds no shared-temp literal to a name for T-hoststate's census.
#
# Per arm:
#   1. clone <source-repo> -> seed, check out <ref>
#   2. plant the committed mutation, commit it
#   3. RE-CLONE seed -> graded  (so a checkout collision materialises as a fresh clone would)
#   4. apply any WORKING-TREE-ONLY mutation to the graded tree
#   5. record git status of the graded tree
#   6. run the WHOLE bar from a cwd outside any repo
#   7. record exit, then probe PRESENCE, then probe VALUE (P-84), then the census line
#
# The tree under grade is identified from ITS OWN TEXT, never passed in.
set -u

WORK="${1:?work root}"; SRC="${2:?source repo}"; REF="${3:?ref}"; shift 3

G=".softhouse/guards"           # assembled, never a literal repo-rooted path
CONFREL=".softhouse/conformance.sh"
BINREL=".softhouse/bin/fire-program.sh"
MEMBER="zz-t446-member.sh"
WIT="zz-t446-witness.txt"

mkdir -p "$WORK" || exit 1
OUT="$WORK/out"; mkdir -p "$OUT"
CWD="$WORK/cwd"; mkdir -p "$CWD"    # bar runs from here: outside every repo

# ---------------------------------------------------------------- helpers
hdr() { printf '%s\n' "GUARDS-DIR-REGISTRATION: REACHED-BY $1"; }

mkmember() {   # $1 = tree, $2 = relpath under $G, $3 = witness rel (empty = no row)
  local t="$1" p="$2" w="$3"; local f; f="$t/$G/$p"
  mkdir -p "$(dirname "$f")"
  {
    printf '#!/usr/bin/env bash\n'
    printf '# a scratch checker planted by the T446 drive\n'
    [ -n "$w" ] && printf '# %s\n' "$(hdr "$w")"
    printf 'exit 0\n'
  } > "$f"
  chmod +x "$f"
}

mkwitness() {  # $1 = tree, $2 = relpath under $G, $3 = text to embed ("" = names nothing)
  local t="$1" p="$2" n="$3"; local f; f="$t/$G/$p"
  mkdir -p "$(dirname "$f")"
  {
    printf 'a witness planted by the T446 drive.\n'
    [ -n "$n" ] && printf 'it runs %s on every fire.\n' "$n"
    printf 'end.\n'
  } > "$f"
}

# NOADD=1 means the plant staged the index itself and a `git add -A` here would
# CLOBBER it -- an index-only entry (a 120000 cacheinfo row) is re-read off the
# case-folded working tree and silently downgraded to the decoy's blob. That is
# exactly how this instrument's first CASE arm measured nothing; recorded, not hidden.
NOADD=0
commit_all() {
  if [ "$NOADD" -eq 0 ]; then ( cd "$1" && git add -A ) || return 1 ; fi
  ( cd "$1" && git -c user.email=t446@local -c user.name=t446 \
      commit -q -m "T446 drive fixture" ) ; }

detect_tree() {  # print which implementation the graded tree carries, from its own text
  local t="$1"; local c; c="$t/$CONFREL"
  if   LC_ALL=C grep -q 'git cat-file blob "\$self_blob"' "$c" 2>/dev/null; then echo "FIXED(T445)"
  elif LC_ALL=C grep -q 'grep -qF -- "\$base" "\$REPO_ROOT/\$self_norm"' "$c" 2>/dev/null; then echo "PRE-FIX(main)"
  else echo "UNRECOGNISED"; fi
}

run_arm() {
  local arm="$1"
  local seed graded; seed="$WORK/$arm/seed"; graded="$WORK/$arm/graded"
  NOADD=0
  rm -rf "$WORK/$arm"; mkdir -p "$WORK/$arm"
  git clone -q "$SRC" "$seed" || { echo "$arm: clone failed"; return 1; }
  ( cd "$seed" && git checkout -q "$REF" ) || return 1

  plant_"$arm" "$seed" || { echo "$arm: plant failed"; return 1; }
  commit_all "$seed" || true

  git clone -q "$seed" "$graded" 2>"$OUT/$arm.clonewarn" || { echo "$arm: reclone failed"; return 1; }

  if declare -F "dirty_$arm" >/dev/null 2>&1; then "dirty_$arm" "$graded"; fi

  local impl; impl="$(detect_tree "$graded")"
  ( cd "$graded" && git status --porcelain ) > "$OUT/$arm.status" 2>&1

  local rc
  ( cd "$CWD" && bash "$graded/$CONFREL" ) > "$OUT/$arm.bar" 2>&1; rc=$?

  # P-84: PRESENCE of the probe line is read BEFORE its value.
  local npresent probeval verdict census
  npresent="$(LC_ALL=C grep -c 'probe = ' "$OUT/$arm.bar" || true)"
  if [ "$npresent" -ge 1 ]; then
    probeval="$(LC_ALL=C grep -m1 'probe = ' "$OUT/$arm.bar" | sed 's/.*probe = //')"
  else
    probeval="ABSENT"
  fi
  verdict="$(LC_ALL=C grep -m1 '^VERDICT' "$OUT/$arm.bar" || echo '(no VERDICT line)')"
  census="$(LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population=' "$OUT/$arm.bar" || echo '(no census line)')"

  {
    echo "arm            = $arm"
    echo "graded tree    = $impl   (detected from the tree's own text)"
    echo "clone warnings = $(tr '\n' ' ' < "$OUT/$arm.clonewarn" | sed 's/  */ /g')"
    echo "git status     = $(wc -l < "$OUT/$arm.status" | tr -d ' ') line(s): $(tr '\n' ';' < "$OUT/$arm.status")"
    echo "EXIT           = $rc"
    echo "probe line count (read BEFORE its value) = $npresent"
    echo "probe value    = $probeval"
    echo "VERDICT        = $verdict"
    echo "census         = $census"
    echo "--- guards-dir registration sentences ---"
    LC_ALL=C grep -n 'guards_dir_registration\|guards-dir registration\|REACHED-BY\|registration decisive' "$OUT/$arm.bar" | head -40
  } > "$OUT/$arm.figures"
  cat "$OUT/$arm.figures"
  echo "================================================================"
}

# ---------------------------------------------------------------- arms

plant_Z() { :; }

# an entirely honest registration, plain ASCII, no collision
plant_LEGA() {
  local t="$1"
  mkmember  "$t" "$MEMBER" "$G/$WIT"
  mkwitness "$t" "$WIT"    "$MEMBER"
}

# T444's M-1, re-derived from the source: the DECLARED witness is the upper-case entry
# (a 100644 decoy that does NOT name the member); a lower-case sibling is a 120000
# SYMLINK to the member and, sorting LAST, wins the checkout collision.
plant_CASE() {
  local t="$1"; local up lo blob
  up="W.txt"; lo="w.txt"
  mkmember "$t" "$MEMBER" "$G/$up"
  mkwitness "$t" "$up" ""          # decoy: names nothing
  ( cd "$t" && git add -A ) || return 1
  blob="$( cd "$t" && printf '%s' "$MEMBER" | git hash-object -w --stdin )" || return 1
  ( cd "$t" && git update-index --add --cacheinfo "120000,$blob,$G/$lo" ) || return 1
  NOADD=1
}

# T445's own MCASE: two index entries whose DIRECTORIES differ only in case. The
# smuggled member carries NO row; the honest one does; the honest file wins the
# checkout and answers the smuggled member's header read.
plant_MCASE() {
  local t="$1"; local UP LO tmpf blob
  UP="ZZ-T446M"; LO="zz-t446m"
  mkmember  "$t" "$UP/x.sh" ""            # smuggled: no REACHED-BY row at all
  mkwitness "$t" "$WIT" "x.sh"
  ( cd "$t" && git add -A ) || return 1
  tmpf="$WORK/mcase-honest"
  {
    printf '#!/usr/bin/env bash\n'
    printf '# the HONEST sibling\n'
    printf '# %s\n' "$(hdr "$G/$WIT")"
    printf 'exit 0\n'
  } > "$tmpf"
  blob="$( cd "$t" && git hash-object -w "$tmpf" )" || return 1
  ( cd "$t" && git update-index --add --cacheinfo "100755,$blob,$G/$LO/x.sh" ) || return 1
  NOADD=1
}

# the registration row exists ONLY in the working tree of the GRADED clone
plant_LEGDIRTY() {
  local t="$1"
  mkmember  "$t" "$MEMBER" ""      # committed: no row
  mkwitness "$t" "$WIT"    "$MEMBER"
}
dirty_LEGDIRTY() {
  local t="$1"; local f; f="$1/$G/$MEMBER"
  LC_ALL=C sed -i '' "2a\\
# $(hdr "$G/$WIT")
" "$f"
}

# the witness names the member ONLY in the working tree of the GRADED clone
plant_WDIRTY() {
  local t="$1"
  mkmember  "$t" "$MEMBER" "$G/$WIT"
  mkwitness "$t" "$WIT"    ""      # committed: names nothing
}
dirty_WDIRTY() {
  local t="$1"; local f; f="$1/$G/$WIT"
  printf 'it runs %s on every fire.\n' "$MEMBER" >> "$f"
}

# the DECLARED witness stops naming its token in the working tree only
plant_CDIRTY() { :; }
dirty_CDIRTY() {
  local t="$1"; local f; f="$1/$BINREL"
  LC_ALL=C sed -i '' 's/repo-state-attest\.sh/repo-state-ATTEST-RENAMED.sh/g' "$f"
}

# a committed witness that this checkout does not materialise (LOW-4 / arm WGONE)
plant_WGONE() {
  local t="$1"
  mkmember  "$t" "$MEMBER" "$G/$WIT"
  mkwitness "$t" "$WIT"    "$MEMBER"
}
dirty_WGONE() { rm -f "$1/$G/$WIT"; }

# ---------------------------------------------------------------- go
for a in "$@"; do run_arm "$a"; done
