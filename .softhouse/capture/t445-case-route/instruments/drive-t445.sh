#!/usr/bin/env bash
# T445 drive — index-versus-filesystem divergence in guard_guards_dir_registration.
#
# USAGE:  bash drive-t445.sh <workroot> <source-repo> <arm> [<arm> ...]
#
# EVERY path this instrument writes is derived from <workroot>, which is an ARGUMENT.
# No name in this file is bound to a literal /tmp path, so it adds no row to
# HOSTSTATE_PIN_TEMP_ASSIGN_LIST.
#
# Each arm: clone <source-repo> -> mutate + commit -> RE-CLONE (so a case collision
# materialises exactly as a fresh checkout would) -> run the WHOLE BAR from a cwd outside
# the repo -> record exit code, then probe PRESENCE, then probe value (P-84: "'exit 2 with
# no probe line' is the guard working — read the ABSENCE, not the value"), then the census
# line and the decisive refusal sentences.
#
# The MODE of the tree under test is DETECTED from the tree itself and is not passable in.
set -u -o pipefail

W="${1:?workroot}"; SRC="${2:?source repo}"; shift 2
mkdir -p "$W"

MARK='GUARDS-DIR-REGISTRATION: REACHED-BY'
# The guards directory is spelled ONCE and every planted leaf is assembled from it at run
# time, so no repo-rooted path that does not resolve is ever spelled whole in this file
# (T316's dead-path frontier reads literals, not variables).
GDR='.softhouse/guards'

detect_mode() {
  # Which of the decisive lines does the tree under test carry? Needles are ASSEMBLED here
  # so that this file cannot satisfy a grep it is also the subject of.
  local f="$1" n
  n="$(printf '%s' '[ "$self_path" '; printf '%s' '!= "$self_norm" ]')"
  if LC_ALL=C grep -qF -- "$n" "$f"; then printf 'roundtrip=yes '; else printf 'roundtrip=NO '; fi
  n="$(printf '%s' 'git cat-file blob "$self_blob"')"
  if LC_ALL=C grep -qF -- "$n" "$f"; then printf 'witness-blob=yes '; else printf 'witness-blob=NO '; fi
  n="$(printf '%s' 'git cat-file blob "$member_blob"')"
  if LC_ALL=C grep -qF -- "$n" "$f"; then printf 'member-blob=yes '; else printf 'member-blob=NO '; fi
  n="$(printf '%s' 'guard_registration_decisive_lines')"
  if LC_ALL=C grep -qF -- "$n" "$f"; then printf 'decisive-arm=yes\n'; else printf 'decisive-arm=NO\n'; fi
}

plant_Z() { :; }

# ---- CASE: the WITNESS-side index/filesystem case divergence (T444 M-1). -------------
# index holds W.txt (100644, a decoy that does NOT name the member) and w.txt (120000, a
# symlink to the member). 'W' sorts before 'w', so the SYMLINK is written last and wins the
# checkout collision. Every index-reading test grades W.txt; the closing grep opens the
# filesystem and dereferences w.txt to the member itself.
plant_CASE() {
  local R="$1" D="$GDR/zz-t445k" B blob
  mkdir -p "$R/$D"
  B="zz-t445k-member.sh"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# planted by T445: %s\n' "$B"
    printf '# %s %s/W.txt\n' "$MARK" "$D"
    printf '%s\n' 'exit 0'; } > "$R/$D/$B"
  printf 'a decoy that names nothing\n' > "$R/$D/W.txt"
  git -C "$R" add "$D/$B" "$D/W.txt" >/dev/null
  blob="$(printf '%s' "$B" | git -C "$R" hash-object -w --stdin)"
  git -C "$R" update-index --add --cacheinfo "120000,$blob,$D/w.txt"
  git -C "$R" commit -q -m 'T445 arm CASE' >/dev/null
}

# ---- MCASE: the MEMBER-side index/filesystem case divergence (T445's own finding). ----
# Two index entries whose DIRECTORIES differ only in case, same basename. The lowercase
# directory sorts last and wins the checkout, so the honest member's text is what the
# filesystem returns for BOTH paths — and the smuggled member's REACHED-BY row is read out
# of a file that is not it.
plant_MCASE() {
  local R="$1" D1="$GDR/zz-t445m" D2="$GDR/ZZ-T445M" blob
  mkdir -p "$R/$D1"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# honest planted checker x.sh, registered against its witness\n'
    printf '# %s %s/wit.txt\n' "$MARK" "$D1"
    printf '%s\n' 'exit 0'; } > "$R/$D1/x.sh"
  printf 'this witness runs x.sh nightly\n' > "$R/$D1/wit.txt"
  git -C "$R" add "$D1/x.sh" "$D1/wit.txt" >/dev/null
  blob="$( { printf '%s\n' '#!/usr/bin/env bash'
             printf '%s\n' '# SMUGGLED: an unwired checker with NO registration row of its own.'
             printf '%s\n' 'exit 0'; } | git -C "$R" hash-object -w --stdin )"
  git -C "$R" update-index --add --cacheinfo "100644,$blob,$D2/x.sh"
  git -C "$R" commit -q -m 'T445 arm MCASE' >/dev/null
}

# ---- LEGA: an entirely honest, plain-ASCII registration. Must stay ACCEPTED. ----------
plant_LEGA() {
  local R="$1" D="$GDR/zz-t445a"
  mkdir -p "$R/$D"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# honest planted checker\n'
    printf '# %s %s/witness.txt\n' "$MARK" "$D"
    printf '%s\n' 'exit 0'; } > "$R/$D/zz-t445a-member.sh"
  printf 'the fire driver runs zz-t445a-member.sh\n' > "$R/$D/witness.txt"
  git -C "$R" add "$D" >/dev/null
  git -C "$R" commit -q -m 'T445 arm LEGA' >/dev/null
}

# ---- LEGDIRTY: the MEMBER's registration row exists ONLY in the working tree. -------
# The committed member carries no row at all. The row is written into the checkout AFTER the
# clone, so the index and the filesystem disagree by an ordinary uncommitted edit — the
# simplest instance of the class, and the one every worker can produce by accident.
plant_LEGDIRTY() {
  local R="$1" D="$GDR/zz-t445d"
  mkdir -p "$R/$D"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# honest planted checker, row added but NOT COMMITTED\n'
    printf '%s\n' 'exit 0'; } > "$R/$D/zz-t445d-member.sh"
  printf 'the fire driver runs zz-t445d-member.sh\n' > "$R/$D/witness.txt"
  git -C "$R" add "$D" >/dev/null
  git -C "$R" commit -q -m 'T445 arm LEGDIRTY base' >/dev/null
}
dirty_LEGDIRTY() {
  local R="$1" D="$GDR/zz-t445d"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# honest planted checker, row added but NOT COMMITTED\n'
    printf '# %s %s/witness.txt\n' "$MARK" "$D"
    printf '%s\n' 'exit 0'; } > "$R/$D/zz-t445d-member.sh"
}

# ---- WDIRTY: the WITNESS names the member ONLY in the working tree. ------------------
# The committed witness names nothing. The member's basename is written into the witness's
# checkout after the clone, so the closing naming test is the only thing that can tell the
# difference between the index and this host.
plant_WDIRTY() {
  local R="$1" D="$GDR/zz-t445w"
  mkdir -p "$R/$D"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# %s %s/witness.txt\n' "$MARK" "$D"
    printf '%s\n' 'exit 0'; } > "$R/$D/zz-t445w-member.sh"
  printf 'a committed witness that names nothing\n' > "$R/$D/witness.txt"
  git -C "$R" add "$D" >/dev/null
  git -C "$R" commit -q -m 'T445 arm WDIRTY base' >/dev/null
}
dirty_WDIRTY() {
  local R="$1" D="$GDR/zz-t445w"
  printf 'the fire driver runs zz-t445w-member.sh\n' > "$R/$D/witness.txt"
}

# ---- WGONE: an honest, committed registration whose WITNESS FILE is not in the checkout.
# The commit is untouched; only this host's working tree lacks the file — a sparse checkout,
# or the loser of a case collision, looks exactly like this. Nothing about the record changed,
# so the record must still be gradeable.
plant_WGONE() {
  local R="$1" D="$GDR/zz-t445g"
  mkdir -p "$R/$D"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# %s %s/witness.txt\n' "$MARK" "$D"
    printf '%s\n' 'exit 0'; } > "$R/$D/zz-t445g-member.sh"
  printf 'the fire driver runs zz-t445g-member.sh\n' > "$R/$D/witness.txt"
  git -C "$R" add "$D" >/dev/null
  git -C "$R" commit -q -m 'T445 arm WGONE' >/dev/null
}
dirty_WGONE() {
  local R="$1" D="$GDR/zz-t445g"
  rm -f "$R/$D/witness.txt"
}

# ---- GITLW: the declared WITNESS is a GITLINK (mode 160000). Its object is a COMMIT, not a
# blob, so a tracked-blob read cannot return anything. Must fail CLOSED.
plant_GITLW() {
  local R="$1" D="$GDR/zz-t445l" c
  mkdir -p "$R/$D"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# %s %s/witness.txt\n' "$MARK" "$D"
    printf '%s\n' 'exit 0'; } > "$R/$D/zz-t445l-member.sh"
  git -C "$R" add "$D" >/dev/null
  git -C "$R" commit -q -m 'T445 arm GITLW base' >/dev/null
  c="$( git -C "$R" rev-parse HEAD )"
  git -C "$R" update-index --add --cacheinfo "160000,$c,$D/witness.txt"
  git -C "$R" commit -q -m 'T445 arm GITLW gitlink witness' >/dev/null
}

# ---- CDIRTY: the DECLARED witness stops naming its token IN THE WORKING TREE ONLY. ----
# The reverse discrimination: the committed bytes still name the token, the checkout does
# not. A guard reading the FILESYSTEM refuses; a guard reading the INDEX accepts, and is
# right to — nothing about the commit changed.
dirty_CDIRTY() {
  local R="$1"
  printf '%s\n' '#!/usr/bin/env bash' > "$R/.softhouse/bin/fire-program.sh"
  printf '%s\n' '# working-tree stub planted by T445 arm CDIRTY; names no token' >> "$R/.softhouse/bin/fire-program.sh"
}
plant_CDIRTY() { :; }

# ---- 2ROW: a member carrying TWO registration rows (T444 LOW-5). ---------------------
plant_2ROW() {
  local R="$1" D="$GDR/zz-t445r"
  mkdir -p "$R/$D"
  { printf '%s\n' '#!/usr/bin/env bash'
    printf '# %s %s/witness.txt\n' "$MARK" "$D"
    printf '# %s %s/second.txt\n' "$MARK" "$D"
    printf '%s\n' 'exit 0'; } > "$R/$D/zz-t445r-member.sh"
  printf 'the fire driver runs zz-t445r-member.sh\n' > "$R/$D/witness.txt"
  printf 'this second row is never graded\n' > "$R/$D/second.txt"
  git -C "$R" add "$D" >/dev/null
  git -C "$R" commit -q -m 'T445 arm 2ROW' >/dev/null
}

# ---- RVQ: delete the round-trip line. C-2's subject. ---------------------------------
plant_RVQ() {
  local R f n
  R="$1"; f="$R/.softhouse/conformance.sh"
  n="$(printf '%s' '[ "$self_path" '; printf '%s' '!= "$self_norm" ]')"
  LC_ALL=C grep -vF -- "$n" "$f" > "$f.new" && mv "$f.new" "$f"
  git -C "$R" commit -q -am 'T445 arm RVQ: delete the round-trip line' >/dev/null
}

# ---- RWB: revert the M-1 remedy (witness grep back to the filesystem). ----------------
plant_RWB() {
  local R f n
  R="$1"; f="$R/.softhouse/conformance.sh"
  n="$(printf '%s' 'git cat-file blob "$self_blob"')"
  LC_ALL=C grep -vF -- "$n" "$f" > "$f.new" && mv "$f.new" "$f"
  git -C "$R" commit -q -am 'T445 arm RWB: delete the witness tracked-blob read' >/dev/null
}

# ---- RWB2: REVERT the M-1 remedy properly. --------------------------------------------
# RWB (above) deleted every line carrying the tracked-blob read. That line is the SECOND
# line of a two-line command substitution, so deleting it left an unterminated `$(` and the
# harness died of a SYNTAX ERROR at exit 2 with the probe absent — a refusal, but not the
# refusal the arm was asking about. RECORDED RATHER THAN QUIETLY REPLACED: an arm that
# refuses for the wrong reason looks exactly like an arm that worked.
# RWB2 SUBSTITUTES instead of deleting, so the mutant is a real semantic revert of T445's
# witness-side remedy — the naming test goes back to reading this host — and stays valid
# shell.
plant_RWB2() {
  local R f
  R="$1"; f="$R/.softhouse/conformance.sh"
  LC_ALL=C sed 's|git cat-file blob "$self_blob"|cat "$REPO_ROOT/$self_norm"|' "$f" > "$f.new" \
    && mv "$f.new" "$f"
  git -C "$R" commit -q -am 'T445 arm RWB2: revert the witness tracked-blob read to a host read' >/dev/null
}

run_arm() {
  # bash EXPANDS EVERY WORD of a `local` before assigning any of them, so a later name
  # cannot reference an earlier one on the same line under `set -u`. Declared, then assigned.
  local arm base seed run log
  arm="$1"; base="$W/$arm"; seed="$base/seed"; run="$base/run"; log="$base/bar.log"
  rm -rf "$base"; mkdir -p "$base"
  git clone -q "$SRC" "$seed" 2>/dev/null || { echo "$arm: CLONE FAILED"; return 9; }
  git -C "$seed" config user.email t445@example.invalid
  git -C "$seed" config user.name  T445
  "plant_$arm" "$seed" > "$base/plant.log" 2>&1
  git clone -q "$seed" "$run" 2>"$base/clone2.log"
  # POST-CLONE mutation. An uncommitted edit is the SIMPLEST index-versus-filesystem
  # divergence there is, and it has to be applied to the tree that is actually graded — a
  # working-tree change in the seed does not survive `git clone`, which is how the first
  # version of arm LEGDIRTY measured nothing.
  if declare -F "dirty_$arm" >/dev/null 2>&1; then
    "dirty_$arm" "$run" >> "$base/plant.log" 2>&1
  fi
  ( cd "$W" && bash "$run/.softhouse/conformance.sh" ) > "$log" 2>&1
  local rc=$?
  local present value census
  present="$(LC_ALL=C grep -c 'probe = ' "$log" || true)"
  if [ "$present" -ge 1 ]; then
    value="$(LC_ALL=C sed -n 's/.*probe = //p' "$log" | LC_ALL=C sed -n 1p)"
  else
    value='(ABSENT — not "down")'
  fi
  census="$(LC_ALL=C sed -n 's/.*GUARDS-DIR-REGISTRATION: population/population/p' "$log" | LC_ALL=C sed -n 1p)"
  {
    printf '=== ARM %s ===\n' "$arm"
    printf 'tree mode under test: '; detect_mode "$run/.softhouse/conformance.sh"
    printf 'EXIT=%s\n' "$rc"
    printf "grep -c 'probe = ' = %s\n" "$present"
    printf 'probe = %s\n' "$value"
    printf 'census: %s\n' "${census:-<no census line printed>}"
    printf 'VERDICT: %s\n' "$(LC_ALL=C grep -m1 '^VERDICT' "$log" || echo '<none>')"
    printf -- '--- decisive registration sentences ---\n'
    LC_ALL=C grep -n 'REACHED-BY\|IS INVOKED BY NOTHING\|DID NOT ROUND-TRIP\|IS A SYMLINK\|NO INDEX ENTRY\|BYTE-IDENTICAL\|DOES NOT NAME\|MORE THAN ONE\|DECISIVE\|is DECLARED' "$log" \
      | LC_ALL=C grep -v '^ *[0-9]*:conformance: THE FIX YOU CAN' | LC_ALL=C sed -n '1,40p' || true
    printf -- '--- checkout collision warnings ---\n'
    LC_ALL=C sed -n '1,20p' "$base/clone2.log" || true
    printf -- '--- git status of the fresh clone ---\n'
    ( cd "$run" && git status --porcelain ) | LC_ALL=C sed -n '1,20p'
    printf '\n'
  } > "$base/figures.txt" 2>&1
  cat "$base/figures.txt"
  return 0
}

for a in "$@"; do run_arm "$a"; done
