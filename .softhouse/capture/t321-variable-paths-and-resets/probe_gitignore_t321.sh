#!/usr/bin/env bash
# T321 item 3 (FU-T316-5) -- IS THE TOOLCHAIN DIRECTORY GITIGNORED?
#
# T316 recorded: "go-env.sh:4 says the toolchain dir is (.gitignore'd) and it is NOT
# [VERIFIED: git check-ignore -v reports no match]". T321 re-derives that and it is WRONG --
# not because T316 mis-ran the command, but because `git check-ignore` answered a different
# question than the one asked. THE NEGATIVE WAS A STATEMENT ABOUT THE PROBE.
#
# The repo's rule is DIRECTORY-ONLY (a trailing slash). `git check-ignore <path>` with no
# trailing slash and no directory on disk cannot match a directory-only rule -- so it returns
# rc=1 on a host where the toolchain has not been installed. Install it, or put the slash on
# the QUERY, and the same rule matches. This script drives all three in a throwaway repo.
#
# This is P-95's shape one level out: an instrument's negative result is a fact about the
# instrument until you drive the positive control.
#
# NOTE ON THIS FILE'S OWN PATH LITERALS, and it is on-topic rather than incidental:
# every repo-shaped path here is ASSEMBLED FROM VARIABLES (SH + "/" + TOOLCHAIN_LEAF) and is
# therefore INVISIBLE to T316's literal census -- which is the very hole T321 part 1 measures.
# It is also why writing this file could not move the dead-path frontier.
#
# EXIT: 0 all three readings taken; 2 could not measure. Probe line: T321-GITIGNORE-PROBE:
set -uo pipefail

SH=".softhouse"
TOOLCHAIN_LEAF="toolchain"
TARGET="$SH/$TOOLCHAIN_LEAF"

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t321-ignore-XXXXXX") || { echo "ERROR: no scratch" >&2; exit 2; }
trap 'rm -rf "$SCRATCH"' EXIT
cd "$SCRATCH" || { echo "ERROR: cannot enter scratch" >&2; exit 2; }
git init -q . || { echo "ERROR: git init failed" >&2; exit 2; }

# The SAME pattern the real repo carries. Derived, not typed: printed below beside the reading.
printf '%s/\n' "$TARGET" > .gitignore
mkdir -p "$SH"

echo "the rule under test (one line, directory-only):"
sed 's/^/    /' .gitignore
echo

echo "READING 1 -- directory ABSENT, query without trailing slash (what T316 ran):"
git check-ignore -v "$TARGET"; r1=$?
echo "    rc=$r1"
echo

mkdir -p "$TARGET"; : > "$TARGET/f"
echo "READING 2 -- directory PRESENT, same query:"
git check-ignore -v "$TARGET"; r2=$?
echo "    rc=$r2"
rm -rf "$TARGET"
echo

echo "READING 3 -- directory ABSENT again, trailing slash on the QUERY:"
git check-ignore -v "$TARGET/"; r3=$?
echo "    rc=$r3"
echo

# 1 = not ignored, 0 = ignored. The claim under test is "the source comment is stale".
verdict="INDETERMINATE"
if [ "$r1" -eq 1 ] && [ "$r2" -eq 0 ] && [ "$r3" -eq 0 ]; then
  verdict="COMMENT-IS-CORRECT/FU-T316-5-REFUTED"
elif [ "$r1" -eq 1 ] && [ "$r2" -eq 1 ] && [ "$r3" -eq 1 ]; then
  verdict="COMMENT-IS-STALE/FU-T316-5-CONFIRMED"
fi

echo "T321-GITIGNORE-PROBE: absentNoSlash=$r1 presentNoSlash=$r2 absentWithSlash=$r3 verdict=$verdict"
echo "gitVersion: $(git --version)"
exit 0
