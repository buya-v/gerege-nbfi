#!/bin/zsh
# T202 RED for T-b: fire-program.sh:250's rescue `git add -A -- . ':!...LOCK'`
# is CWD-RELATIVE and now ASYMMETRIC with the :(top)-anchored `git status`
# directly above it. From any cwd below the repo root the guard SEES the dirty
# path, stages NOTHING, and still logs `rescued:`.
# Runs the SHIPPED BYTES (sed -n '239,254p' of fire-program.sh) verbatim.
set -uo pipefail
S=/tmp/t202/tb
STAMP=REDTB-000000
log() { print -r -- "  [log] $*" }

build_repo() {
  rm -rf "$S"; mkdir -p "$S"
  cd "$S" || exit 1
  git init -q -b main
  mkdir -p .softhouse docs tools/deep
  print -r -- baseline > .softhouse/tasks.json
  print -r -- baseline > docs/baseline.md
  print -r -- baseline > tools/deep/keep.txt
  print -r -- '{"holder":"local-launchd"}' > .softhouse/LOCK
  git add -A
  git -c user.name=t202 -c user.email=t202@example.com commit -q -m baseline
  # real deliverables the driver left behind, all ABOVE the cwd we will use
  print -r -- "a whole DEC-1 retry" > "$S/docs/T999-handoff.md"
  print -r -- "vector capture"      > "$S/.softhouse/vector.json"
  print -r -- "lock churn"         >> "$S/.softhouse/LOCK"
}

run_guard() {   # `local -a` at :248 requires a function context
  source /tmp/t202/prefix-guard.zsh
}

for CWD in "$S" "$S/tools/deep"; do
  build_repo
  BASE=$(git -C "$S" rev-parse HEAD)
  cd "$CWD" || exit 1
  print -r -- "=== cwd = $CWD  (repo root? $([[ $CWD == $S ]] && print YES || print NO)) ==="
  run_guard
  print -r -- "  still-uncommitted after the rescue:"
  git -C "$S" status --porcelain -- ':(top)' | sed 's/^/      /'
  if [[ "$(git -C "$S" rev-parse HEAD)" == "$BASE" ]]; then
    print -r -- "  HEAD UNCHANGED - the rescue commit never happened"
    print -r -- "  *** the log said 'rescued:' but NOTHING was committed - FAIL-OPEN ***"
  else
    print -r -- "  rescue commit contents:"
    git -C "$S" show --name-only --format= HEAD | sed 's/^/      /'
  fi
  print -r -- ""
done
