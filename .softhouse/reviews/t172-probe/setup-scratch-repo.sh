#!/bin/zsh
# T172 -- rebuilds the SCRATCH git repo used to drive fire-program.sh:224's
# LOCK-pattern guard red (pre-fix) and green (post-fix). NEVER touches the
# real .softhouse/LOCK of a running fire -- this operates entirely inside
# /tmp/t172-scratch-repo, a throwaway repo with no relation to gerege-nbfi.
#
# Usage:
#   zsh setup-scratch-repo.sh
#   zsh run-pre-fix.sh     # requires pre-fix-line224.txt (captured from `git show main:...`)
#   zsh run-post-fix.sh    # requires post-fix-line224.txt (captured from the fixed file)
set -uo pipefail

SCRATCH=/tmp/t172-scratch-repo
rm -rf "$SCRATCH"
mkdir -p "$SCRATCH"
cd "$SCRATCH" || exit 1

git init -q
git -c user.name=t172 -c user.email=t172@example.com commit -q --allow-empty -m init
mkdir -p .softhouse some/other

# Baseline: track most of .softhouse/ and some/other/ so untracked additions
# show up as INDIVIDUAL porcelain lines rather than a collapsed directory
# entry -- matching the real repo, where .softhouse/ is a tracked directory.
print -r -- "baseline" > .softhouse/tasks.json
print -r -- "baseline" > some/other/baseline.go
git add .softhouse/tasks.json some/other/baseline.go
git -c user.name=t172 -c user.email=t172@example.com commit -q -m baseline

# Genuine dirty control file (ordinary modification).
print -r -- "modified" >> some/other/baseline.go

# The real LOCK file: untracked, legitimately expected to be dirty, and
# excluded by the guard on purpose.
print -r -- '{"holder":"local-launchd"}' > .softhouse/LOCK

# A SIBLING that merely shares the LOCK path's PREFIX -- genuine dirty work
# that the guard must NOT silently drop.
print -r -- "genuine work" > .softhouse/LOCKED_STATE.md

# An unrelated untracked control file.
print -r -- "new untracked control" > some/other/newfile.go

echo "Scratch repo rebuilt at $SCRATCH"
git status --porcelain
