#!/usr/bin/env bash
# T446: does a 120000 (symlink) index entry WIN a case collision against a 100644
# entry that sorts before it?  T444's M-1 and T445's arm CASE both require that it
# does.  My first construction produced the opposite, so measure it rather than
# assume it.
set -u
W="$1"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1

trial() {   # $1 label  $2 name-of-regular  $3 name-of-symlink  $4 symlink target
  local label="$1" reg="$2" lnk="$3" tgt="$4"
  rm -rf seed clone; mkdir seed; cd seed || return
  git init -q .; git config user.email t@t; git config user.name t
  printf 'DECOY-CONTENT-does-not-name-the-target\n' > "$reg"
  printf 'MEMBER BODY names %s\n' "$tgt" > "$tgt"
  git add -A >/dev/null 2>&1
  local blob rc
  blob="$(printf '%s' "$tgt" | git hash-object -w --stdin)"
  git update-index --add --cacheinfo "120000,$blob,$lnk"; rc=$?
  echo "--- $label ---"
  echo "  update-index --cacheinfo 120000 $lnk : rc=$rc"
  git commit -q -m x >/dev/null 2>&1
  echo "  index:"; git ls-files -s | sed 's/^/    /'
  cd ..
  git clone -q seed clone 2>&1 | grep -v '^$' | sed 's/^/    clone: /'
  echo "  materialised:"; ( cd clone && ls -la | grep -v '^total\|^d' | sed 's/^/    /' )
  echo "  what a filesystem read of '$reg' returns:"
  ( cd clone && cat "$reg" 2>&1 | sed 's/^/    /' )
  echo "  git status --porcelain:"; ( cd clone && git status --porcelain | sed 's/^/    /' )
  echo
}

# the shape T444/T445 describe: decoy W.txt sorts FIRST, symlink w.txt sorts LAST
trial "decoy=W.txt (first)  symlink=w.txt (last)"  "W.txt" "w.txt" "member.sh"
# the mirror: symlink sorts FIRST, decoy sorts LAST
trial "symlink=W.txt (first) decoy=w.txt (last)"   "w.txt" "W.txt" "member.sh"
