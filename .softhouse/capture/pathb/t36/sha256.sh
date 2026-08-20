#!/bin/sh
# T99 — a sha256 that a PATH-poisoned `shasum` cannot answer for.
#
# WHY THIS FILE EXISTS.  T76 pinned the rounding-mode canary by SUBSTRING; T77 defeated it with a
# one-character edit.  T80 replaced the substring with a DIGEST COMPARISON, which is the right
# shape — but computed the digest with the bare word `shasum`, resolved through $PATH:
#
#     creqsha=$(shasum -a 256 "$CANARY_REQ" | cut -d' ' -f1)     # preconditions.sh:195, pre-T99
#
# A `shasum` earlier on $PATH that prints the pinned constant for any input collapses the two
# operands of that comparison back into one — and it is WORSE than the tautology it replaced,
# because the recipe now LOOKS hardened, the transcript prints "PASS  canary request pinned by
# DIGEST COMPARISON", and NOTHING IN ANY DIFF CHANGES.  T99 reproduced it against main's bytes:
# the mutated canary (true sha256 13ce2f4f21a1ad568b080b859682b9e995aac97712e00fcf44c6fc177d6b9ca5)
# was certified "== pinned sha256 2a6621be…" and SENT.  See t99/out/f2-*.
#
# THE THREE PROPERTIES.  None is asserted here; each is exercised by t99/prove-f2.sh.
#
#  1. ABSOLUTE PATHS ONLY, IN ROOT-OWNED SYSTEM DIRECTORIES.  Never a bare word, so $PATH is not
#     consulted — not for the digest tools, and not for the `awk`/`mktemp`/`rm` this file uses to
#     drive them.  /usr/local/bin and /opt/homebrew/bin are deliberately NOT candidates: they are
#     user-writable, which is the same capability a $PATH attacker already has.
#  2. A KNOWN-ANSWER TEST PER TOOL, EVERY RUN.  Each candidate must reproduce sha256("") and
#     sha256("abc") before it is allowed to answer anything.  A tool that constant-returns the
#     pinned digest dies here even if it somehow occupies /usr/bin.
#  3. TWO INDEPENDENT IMPLEMENTATIONS MUST AGREE.  Perl (`shasum`), C (`sha256sum`), LibreSSL
#     (`openssl dgst`) and CPython (`hashlib`) are four separate implementations; at least two must
#     survive the KAT and return the same digest for the file under test, or the caller gets a
#     refusal and no digest at all.  A check has two operands; this is that principle applied one
#     level down, to the instrument.
#
# Each tool runs under `/usr/bin/env -i` with a fixed minimal environment, so PERL5LIB / PERL5OPT
# (the perl `shasum` is a perl script — `head -1 /usr/bin/shasum` is `#!/usr/bin/perl`), PYTHONPATH
# / PYTHONHOME and OPENSSL_CONF cannot inject code either; python3 additionally runs with -I.
#
# WHAT THIS DOES NOT DEFEND AGAINST, stated so nobody reads more into it: an attacker who can write
# to /usr/bin, /sbin or /bin, or who can patch the running kernel, owns the machine and every
# instrument on it.  The claim is bounded — a $PATH an ordinary user controls no longer decides what
# sha256 means.
#
# Usage:   . "$D/sha256.sh"        # sourced; POSIX sh, no bashisms
#          sha256_init             # KATs every candidate; returns 1 if fewer than 2 survive
#          sha256_file <path>      # sets SHA256_RESULT / SHA256_USED, or SHA256_ERROR and returns 1
#                                  # NOTE: sets globals, so do NOT call it in $( ) — a subshell
#                                  # would discard exactly the fields the transcript needs.
#          $SHA256_TOOLS           # tools that passed the KAT, for the transcript
#
# Standalone:  sh sha256.sh <file>...   # "<digest>  <file>" per file; non-zero on any refusal.

SHA256_KAT_EMPTY=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
SHA256_KAT_ABC=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
SHA256_TOOLS=''
SHA256_ERROR=''
SHA256_RESULT=''
SHA256_USED=''

# Absolute helpers.  A poisoned `awk` could rewrite a digest on its way out of a correct tool, so
# the plumbing is pinned too.
SHA256_AWK=/usr/bin/awk
SHA256_ENV=/usr/bin/env
SHA256_MKTEMP=/usr/bin/mktemp
SHA256_RM=/bin/rm
SHA256_MINENV='LC_ALL=C PATH=/usr/bin:/bin:/sbin:/usr/sbin'

# Candidate table.  Label -> absolute path(s), first executable wins.  Extending it means editing
# THIS committed file, which shows up in a diff — the whole point.
# NOTE the `if`, not `[ -x … ] && { … }`: a caller may have `set -e` in force (recapture.sh does),
# and an AND-OR list whose test fails is a failed command, which would kill the caller's run on a
# machine where the first candidate happens to be absent.
_sha256_path() {
  case "$1" in
    shasum)    _cands='/usr/bin/shasum /bin/shasum' ;;
    sha256sum) _cands='/sbin/sha256sum /usr/bin/sha256sum /bin/sha256sum' ;;
    openssl)   _cands='/usr/bin/openssl /bin/openssl' ;;
    python3)   _cands='/usr/bin/python3 /bin/python3' ;;
    *)         return 1 ;;
  esac
  for _p in $_cands; do
    if [ -x "$_p" ]; then
      echo "$_p"
      return 0
    fi
  done
  return 1
}

_sha256_with() {          # <label> <file> -> digest on stdout, or nothing
  _t=$1; _f=$2
  _p=$(_sha256_path "$_t") || return 1
  case "$_t" in
    shasum)    $SHA256_ENV -i $SHA256_MINENV "$_p" -a 256 "$_f" 2>/dev/null \
                 | $SHA256_AWK 'NR==1{print $1}' ;;
    sha256sum) $SHA256_ENV -i $SHA256_MINENV "$_p" "$_f" 2>/dev/null \
                 | $SHA256_AWK 'NR==1{print $1}' ;;
    openssl)   $SHA256_ENV -i $SHA256_MINENV "$_p" dgst -sha256 "$_f" 2>/dev/null \
                 | $SHA256_AWK 'NR==1{print $NF}' ;;
    python3)   $SHA256_ENV -i $SHA256_MINENV "$_p" -I -c 'import hashlib,sys
h=hashlib.sha256()
with open(sys.argv[1],"rb") as fh:
    for b in iter(lambda: fh.read(1<<20), b""):
        h.update(b)
print(h.hexdigest())' "$_f" 2>/dev/null ;;
  esac
}

_sha256_is_hex() {        # exactly 64 lowercase hex characters, no more, no less
  case "$1" in
    *[!0-9a-f]* | '') return 1 ;;
  esac
  [ "${#1}" -eq 64 ]
}

sha256_init() {
  SHA256_ERROR=''
  _kd=$($SHA256_MKTEMP -d "${TMPDIR:-/tmp}/sha256kat.XXXXXX") || {
    SHA256_ERROR='cannot create a known-answer-test directory'; return 1; }
  : > "$_kd/empty"
  printf 'abc' > "$_kd/abc"
  SHA256_TOOLS=''
  _n=0
  for _t in shasum sha256sum openssl python3; do
    _a=$(_sha256_with "$_t" "$_kd/empty") || _a=''
    _b=$(_sha256_with "$_t" "$_kd/abc")   || _b=''
    if [ "$_a" = "$SHA256_KAT_EMPTY" ] && [ "$_b" = "$SHA256_KAT_ABC" ]; then
      SHA256_TOOLS="${SHA256_TOOLS:+$SHA256_TOOLS }$_t($(_sha256_path "$_t"))"
      eval "SHA256_OK_$_t=1"
      _n=$((_n+1))
    else
      eval "SHA256_OK_$_t=0"
    fi
  done
  $SHA256_RM -rf "$_kd"
  if [ "$_n" -lt 2 ]; then
    SHA256_ERROR="only $_n of 4 sha256 implementations passed the known-answer test, and a cross-check needs 2 independent ones. Survivors: [${SHA256_TOOLS:-none}]"
    return 1
  fi
  return 0
}

sha256_file() {           # <file> -> SHA256_RESULT, SHA256_USED ; 1 + SHA256_ERROR on refusal
  _f=$1
  SHA256_ERROR=''; SHA256_RESULT=''; SHA256_USED=''
  [ -f "$_f" ] || { SHA256_ERROR="'$_f' is not a readable regular file"; return 1; }
  [ -n "$SHA256_TOOLS" ] || sha256_init || return 1
  _first=''; _firstt=''; _used=''
  for _t in shasum sha256sum openssl python3; do
    eval "_ok=\${SHA256_OK_$_t:-0}"
    [ "$_ok" = "1" ] || continue
    _d=$(_sha256_with "$_t" "$_f") || _d=''
    if ! _sha256_is_hex "$_d"; then
      SHA256_ERROR="$_t returned '$_d' for '$_f', which is not a 64-character lowercase-hex sha256"
      return 1
    fi
    if [ -z "$_first" ]; then
      _first=$_d; _firstt=$_t; _used=$_t
    else
      _used="$_used+$_t"
      if [ "$_d" != "$_first" ]; then
        SHA256_ERROR="sha256 IMPLEMENTATIONS DISAGREE on '$_f': $_firstt says '$_first', $_t says '$_d'. At least one of them is not computing sha256 — the instrument is compromised and no digest is returned."
        return 1
      fi
    fi
  done
  [ -n "$_first" ] || { SHA256_ERROR="no sha256 implementation answered for '$_f'"; return 1; }
  SHA256_RESULT=$_first
  SHA256_USED=$_used
  return 0
}

# Standalone mode, only when executed under its own name.
case "${0##*/}" in
  sha256.sh)
    [ $# -gt 0 ] || { echo "usage: sh sha256.sh <file>..." >&2; exit 2; }
    if ! sha256_init; then echo "REFUSED: $SHA256_ERROR" >&2; exit 1; fi
    echo "# sha256 by $SHA256_TOOLS — absolute paths, known-answer tested, cross-checked" >&2
    _rc=0
    for _f in "$@"; do
      if sha256_file "$_f"; then printf '%s  %s\n' "$SHA256_RESULT" "$_f"
      else echo "REFUSED: $SHA256_ERROR" >&2; _rc=1; fi
    done
    exit $_rc
    ;;
esac
