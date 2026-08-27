#!/usr/bin/env bash
# T308 -- every out/ and probe/ path cited by REVIEW.md must resolve to a NON-EMPTY file,
# either under this review's own directory or under T292's committed capture directory.
#
# Why this exists: this lineage's whole subject is the vacuous green, and a review that cites a
# transcript which does not exist is exactly that at the level of the report rather than the rule.
# Pass 1 of this review shipped a commit titled "point every transcript reference at a file that
# exists and is non-empty" -- done by hand, and therefore not re-checkable. This makes it a
# program.
#
# ABSENT BY DESIGN: some paths are cited precisely IN ORDER to say they are absent. They are
# listed here by name with their reason, so that "absent" is a DECLARED state and not a miss.
# Each is also checked in the other direction: if a declared-absent file ever APPEARS, this
# script fails, so the declaration cannot rot into a lie.
set -u
cd "$(dirname "$0")/../../../.." || exit 3
R=.softhouse/reviews/T308
C=.softhouse/capture/t286-t268-retry

absent_reason() {
  case "$1" in
    out/t308-survivor-mutants.txt)
      echo "pass 3 of t308_survivor_mutants.py was killed mid-run when the host went to load 24."
      echo "DELETED rather than committed at zero bytes -- a zero-byte transcript in an evidence"
      echo "directory reads as a measurement that was taken. Passes 1 and 2 are the record." ;;
    out/this-file-does-not-exist.txt)
      echo "NOT a transcript. Appears in REVIEW.md section 0 only as the quoted output of this"
      echo "script's own NEGATIVE CONTROL run -- the demonstration that the checker fails when a"
      echo "citation dangles. It must never resolve." ;;
    *) return 1 ;;
  esac
}

list=$(mktemp)
grep -o -E '(out|probe)/[A-Za-z0-9._-]+' "$R/REVIEW.md" | sort -u > "$list"

bad=0
total=0
while read -r f; do
  total=$((total + 1))
  if [ -s "$R/$f" ]; then
    echo "OK       (T308) $f"
  elif [ -s "$C/$f" ]; then
    echo "OK       (T292) $f"
  elif reason=$(absent_reason "$f"); then
    if [ -e "$R/$f" ]; then
      echo "*** DECLARED ABSENT BUT PRESENT: $f -- the declaration is now false"
      bad=1
    else
      echo "ABSENT   (declared) $f"
      printf '%s\n' "$reason" | sed 's/^/         | /'
    fi
  else
    echo "*** UNRESOLVED OR EMPTY: $f"
    bad=1
  fi
done < "$list"
rm -f "$list"

echo
echo "$total cited paths checked."
if [ "$bad" = "0" ]; then
  echo "ALL CITED PATHS RESOLVE NON-EMPTY, OR ARE ABSENT BY DECLARATION."
  exit 0
fi
echo "SOME CITED PATHS DO NOT RESOLVE."
exit 1
