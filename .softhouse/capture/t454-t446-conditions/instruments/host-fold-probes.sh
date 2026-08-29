#!/bin/bash
# T454 -- the host record, and the three filesystem fold probes the census rests on.
#
# The third probe is T446's own U+212A construction, reproduced so the correction is visible
# rather than asserted: substituting the Kelvin sign into a path with NO `k` in it compares two
# genuinely different names, and "files=2" there says nothing about whether the fold exists.
#
# Every probe writes TWO DISTINGUISHABLE contents and reads back WHICH ONE SURVIVED. A probe that
# only counted files could not tell "they collided" from "the second write failed".
set -u
d="${1:?scratch dir, absolute, OUTSIDE the repository}"
case "$d" in /*) ;; *) printf 'scratch dir must be absolute: %s\n' "$d" >&2; exit 3 ;; esac

printf 'T454 HOST AND FOLD PROBES\n'
printf 'host    : %s\n' "$(uname -srm)"
printf 'macOS   : %s build %s\n' "$(sw_vers -productVersion)" "$(sw_vers -buildVersion)"
printf 'git     : %s\n' "$(git --version)"
printf 'bash    : %s\n' "$BASH_VERSION"
printf 'fs      : %s\n' "$(diskutil info / | grep 'File System Personality' | sed 's/^ *//')"
printf 'core.precomposeunicode = %s\n' "$(git config --get core.precomposeunicode)"
printf 'core.ignorecase        = %s\n' "$(git config --get core.ignorecase)"
printf '\n'

probe() {
  local label="$1" a="$2" b="$3" n got
  rm -rf "$d"; mkdir -p "$d" || { printf 'PROBE FAILURE: cannot create %s\n' "$d"; exit 3; }
  printf 'AAA' > "$d/$a" || { printf 'PROBE FAILURE: cannot write %s\n' "$a"; exit 3; }
  printf 'BBB' > "$d/$b" || { printf 'PROBE FAILURE: cannot write %s\n' "$b"; exit 3; }
  n=$(ls "$d" | wc -l | tr -d ' ')
  got="$(cat "$d/$a")" || { printf 'PROBE FAILURE: cannot read back %s\n' "$a"; exit 3; }
  case "$got" in
    AAA|BBB) ;;
    *) printf 'PROBE FAILURE: %s read back %s, which is neither content written\n' "$a" "$got"
       exit 3 ;;
  esac
  printf '%-50s : files=%s  first name reads=%s\n' "$label" "$n" "$got"
}

probe "U+212A KELVIN vs ASCII k" "xky" "$(printf 'x\xe2\x84\xaay')"
probe "U+017F LONG S in conformance.sh" "conformance.sh" "$(printf 'conformance.\xc5\xbfh')"
probe "U+212A appended where there is no k to fold" "conformance.sh" "$(printf 'conformance.s\xe2\x84\xaa')"
rm -rf "$d"

printf '\n'
printf 'READING: files=1 with the first name reading BBB means the two spellings are ONE file and\n'
printf 'the second write won. files=2 means they are distinct. The third probe is T446 U+212A row:\n'
printf 'it reports files=2 because there is no `k` in "conformance.sh" for the Kelvin sign to fold\n'
printf 'onto -- which is a fact about that probe, not about the filesystem. Probe 1 is the same\n'
printf 'question asked of a name that DOES contain a `k`, and the fold is there.\n'
