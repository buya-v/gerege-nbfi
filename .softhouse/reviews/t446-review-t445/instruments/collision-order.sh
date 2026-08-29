#!/usr/bin/env bash
# T446 independent re-derivation of T445's collision-order claim.
#
# T445 claims: "the index entry that sorts LAST wins a checkout collision, so a
# target spelled in all lower case cannot be beaten by any case variant."
# The second half of that sentence is the load-bearing one: it is what licenses the
# guard to keep reading .softhouse/conformance.sh FROM THIS HOST.
#
# We test (a) does last-in-index-order win, and (b) is an all-lowercase ASCII name
# really unbeatable -- U+017F LATIN SMALL LETTER LONG S folds to 's' on APFS and its
# UTF-8 bytes (c5 bf) sort AFTER ascii 's' (73).
set -u
W="$1"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
echo "git: $(git --version)"
echo

mk() {
  # $1 = label, $2..$n = names to commit (content = the name's label index)
  local label="$1"; shift
  rm -rf seed clone; mkdir seed; cd seed || return
  git init -q .; git config user.email t@t; git config user.name t
  local i=0 n
  for n in "$@"; do
    i=$((i+1))
    local blob; blob=$(printf 'CONTENT-%d name=%s\n' "$i" "$(printf '%s' "$n" | xxd -p)" | git hash-object -w --stdin)
    git update-index --add --cacheinfo "100644,$blob,$n"
  done
  git commit -q -m x >/dev/null 2>&1
  echo "--- $label ---"
  echo "index order (git ls-files, C-quoted):"
  git ls-files | sed 's/^/    /'
  cd ..
  git clone -q seed clone 2>&1 | sed 's/^/    clone: /'
  echo "  after clone, files present:"
  ( cd clone && ls -1b | grep -v '^\.git$' | sed 's/^/    /' )
  echo "  content at each materialised path:"
  ( cd clone && for f in *; do [ -f "$f" ] && printf '    %s = %s\n' "$(printf '%s' "$f" | xxd -p)" "$(cat "$f")"; done )
  echo "  core.ignorecase = $(cd clone && git config core.ignorecase)"
  echo "  core.precomposeunicode = $(cd clone && git config core.precomposeunicode)"
  echo "  git status --porcelain after clone:"
  ( cd clone && git status --porcelain | sed 's/^/    /' )
  echo
}

# 1. pure case: lowercase target vs uppercase decoy. lowercase sorts LAST.
mk "case: A.txt (first) vs a.txt (last)" "A.txt" "a.txt"

# 2. the real shape: an all-lowercase target beaten by a LONG-S variant that sorts LAST
mk "longs: conformance.sh vs conformance.<U+017F>h" \
   "conformance.sh" "$(printf 'conformance.\xc5\xbfh')"

# 3. NFC vs NFD pair
mk "nfd/nfc: cafe<U+00E9>.sh vs cafe+combining-acute.sh" \
   "$(printf 'caf\xc3\xa9.sh')" "$(printf 'cafe\xcc\x81.sh')"
