#!/bin/sh
# Repo-local Go toolchain for the gerege-nbfi migration.
# Installed by local fire 20260819-170001. NOT on a default PATH and NOT committed
# (.gitignore'd) — `rm -rf .softhouse/toolchain` fully reverses it.
#
# Usage from any checkout OR worktree — SOURCE it, do not execute it:
#     . .softhouse/bin/go-env.sh
#     go build ./...      # from nexus/
#
# ---------------------------------------------------------------------------------
# WHAT T253 CHANGED, AND WHY
#
# This file used to open with a single hard-coded line:
#
#     GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain
#
# — the absolute path of ONE developer's Mac. On every other host that directory does
# not exist, and the script SILENTLY exported `GOROOT=<nonexistent>/go` anyway. The
# `go` already on PATH then died with `go: cannot find GOROOT directory: …`, and the
# failure surfaced three layers away as:
#
#     ledger-invariants: the guard DID NOT COMPILE … EXIT 2 — NOT a pass
#
# THE GUARD'S REFUSAL THERE IS CORRECT AND FAIL-CLOSED, and T253 did not touch it. The
# defect was HERE: this script converted "the pinned toolchain is not installed on this
# host" — an ordinary, expected state of any machine but one — into "a HARD money guard
# did not compile", which reads like a code defect and is not one. A wrong diagnosis
# that fires on every host except the author's is a portability defect, not a guard.
#
# The location is now DERIVED, three ways, in this order:
#   1. $GEREGE_TOOLCHAIN, if the caller already set it — an explicit override wins.
#   2. the MAIN checkout, found with `git rev-parse --git-common-dir`. This is the
#      load-bearing step: the toolchain is gitignored, so it exists ONLY in the main
#      checkout and NEVER in an isolated worktree, while THIS FILE is tracked and is
#      therefore checked out in every worktree. Deriving from this script's own path
#      alone would resolve a worktree's own `.softhouse/toolchain`, which is never there.
#   3. this checkout, for a plain clone, a tarball, or anything git cannot answer for.
#
# Each candidate is tested for an EXECUTABLE `go/bin/go`, not for a directory that
# exists: a half-deleted or half-extracted toolchain directory is not a toolchain, and
# testing `-d` would have re-created exactly the defect above one level down.
#
# WHEN NO PINNED TOOLCHAIN IS FOUND — the T253 ENGINEERING decision, recorded here so a
# later reader does not have to reconstruct it:
#
#   DEFAULT: FALL BACK to the `go` already on PATH, and SAY SO, LOUDLY, ON STDERR,
#   naming the binary and its version. Rationale: (a) the pinned toolchain is gitignored
#   and host-local, so it is BY CONSTRUCTION absent everywhere except one Mac — a hard
#   refusal makes the program's only instrument unrunnable in CI, in a cloud sandbox and
#   on every new machine; (b) the fail-closed property that matters already lives in the
#   GUARDS — `check-ledger-invariants.sh` and `conformance.sh:load_toolchain` both refuse
#   loudly when there is no compiler — and duplicating that refusal in the layer beneath
#   them would create a second source of truth for one question; (c) the real defect was
#   SILENCE, not substitution, and a substitution that is printed is auditable evidence
#   in the BAR while a silent one is not.
#
#   ALTERNATIVE REJECTED: refuse outright with no fallback. It buys no protection the
#   two guards do not already provide, and it would leave the harness unable to run at
#   all on any host but one. It is REJECTED AS THE DEFAULT, NOT REMOVED: set
#   GEREGE_GO_STRICT=1 and this script refuses instead of substituting, so the rejected
#   arm stays reachable without editing this file, and reversing the decision is a
#   config change rather than a patch.
#
#   WHAT THE FALLBACK DOES NOT LICENSE: a substituted toolchain is fine for building and
#   for running the source-level guards. It is NOT a pinned-toolchain run. Any PARITY
#   claim must name the toolchain that produced it — which is why the substitution is
#   printed and why $GEREGE_GO_SOURCE is exported for anything that wants to report it.
# ---------------------------------------------------------------------------------

# --- 1. Where is this script? -----------------------------------------------------
# A SOURCED script cannot read its own path in POSIX sh — `$0` is the CALLER's. bash and
# zsh each expose it, by syntax the other shell cannot even parse, so both spellings are
# hidden behind `eval` and are never parsed by the shell that is not running.
_ge_self=''
if [ -n "${BASH_VERSION-}" ]; then
  eval '_ge_self=${BASH_SOURCE[0]}'
elif [ -n "${ZSH_VERSION-}" ]; then
  eval '_ge_self=${(%):-%x}'
fi
# Executed rather than sourced (or a shell with neither): $0 is then correct.
[ -n "$_ge_self" ] || _ge_self=$0

_ge_dir=''
case "$_ge_self" in
  ''|-*|sh|bash|dash|zsh|ksh) ;;   # a login-shell $0, not a path — leave empty
  *) _ge_dir=$(CDPATH= cd -- "$(dirname -- "$_ge_self")" 2>/dev/null && pwd) || _ge_dir='' ;;
esac
# Last resort: assume the caller is standing in a checkout.
[ -n "$_ge_dir" ] || _ge_dir=$(CDPATH= cd -- "$PWD/.softhouse/bin" 2>/dev/null && pwd) || _ge_dir=''

# <checkout>/.softhouse/bin  ->  <checkout>
_ge_here=''
[ -n "$_ge_dir" ] && _ge_here=$(CDPATH= cd -- "$_ge_dir/../.." 2>/dev/null && pwd)
[ -n "$_ge_here" ] || _ge_here=$PWD

# --- 2. Where is the MAIN checkout? -----------------------------------------------
# In a worktree, `--git-common-dir` is the MAIN repo's .git; in the main checkout it is
# that checkout's own .git. It may come back relative, so it is resolved to absolute by
# cd-ing to it rather than by string surgery.
_ge_main=''
_ge_common=$(CDPATH= cd -- "$_ge_here" 2>/dev/null && git rev-parse --git-common-dir 2>/dev/null) || _ge_common=''
if [ -n "$_ge_common" ]; then
  case "$_ge_common" in
    /*) : ;;
    *)  _ge_common=$(CDPATH= cd -- "$_ge_here" 2>/dev/null && CDPATH= cd -- "$_ge_common" 2>/dev/null && pwd) || _ge_common='' ;;
  esac
  [ -n "$_ge_common" ] && _ge_main=$(dirname -- "$_ge_common")
fi

# --- 3. Pick the first candidate with an EXECUTABLE go ----------------------------
_ge_found=''
_ge_origin=''
_ge_tried=''
for _ge_cand in \
    "${GEREGE_TOOLCHAIN:-}" \
    "${_ge_main:+$_ge_main/.softhouse/toolchain}" \
    "${_ge_here:+$_ge_here/.softhouse/toolchain}"
do
  [ -n "$_ge_cand" ] || continue
  case " $_ge_tried " in *" $_ge_cand "*) continue ;; esac
  _ge_tried="$_ge_tried $_ge_cand"
  if [ -x "$_ge_cand/go/bin/go" ]; then
    _ge_found=$_ge_cand
    break
  fi
done
if [ -n "$_ge_found" ]; then
  case "$_ge_found" in
    "${GEREGE_TOOLCHAIN:-@none@}") _ge_origin='GEREGE_TOOLCHAIN override' ;;
    "${_ge_main:-@none@}/.softhouse/toolchain") _ge_origin='pinned toolchain in the main checkout' ;;
    *) _ge_origin='pinned toolchain in this checkout' ;;
  esac
fi

if [ -n "$_ge_found" ]; then
  # THE NORMAL PATH. Unchanged from what this file has always exported, except that the
  # directory is now derived instead of hard-coded. GOROOT is still an ABSOLUTE path into
  # the main checkout, so isolated worktrees share one toolchain and one module cache.
  GEREGE_TOOLCHAIN=$_ge_found
  export GEREGE_TOOLCHAIN
  export GOROOT="$GEREGE_TOOLCHAIN/go"
  export GOPATH="$GEREGE_TOOLCHAIN/gopath"
  export GOCACHE="$GEREGE_TOOLCHAIN/gocache"
  export GOMODCACHE="$GEREGE_TOOLCHAIN/gomodcache"
  export PATH="$GOROOT/bin:$PATH"
  export GEREGE_GO_SOURCE="pinned:$GEREGE_TOOLCHAIN"
else
  # NO PINNED TOOLCHAIN ON THIS HOST. Two arms, and BOTH are loud. Neither exports a
  # GOROOT — exporting one that does not exist is the entire defect this replaces.
  _ge_path_go=$(command -v go 2>/dev/null) || _ge_path_go=''
  _ge_say() { printf 'gerege go-env: %s\n' "$1" >&2; }
  _ge_say 'THE PINNED GO TOOLCHAIN IS NOT ON THIS HOST.'
  _ge_say '  looked for an executable go/bin/go under, in order:'
  for _ge_cand in $_ge_tried; do
    _ge_say "    $_ge_cand   ABSENT"
  done
  [ -n "$_ge_tried" ] || _ge_say '    (no candidate could be derived: no script path, no git, no CWD checkout)'

  if [ -n "${GEREGE_GO_STRICT:-}" ]; then
    _ge_say 'GEREGE_GO_STRICT is set, so this is a REFUSAL and not a substitution.'
    _ge_say '  Nothing was exported. Install the pinned toolchain, or set GEREGE_TOOLCHAIN,'
    _ge_say '  or unset GEREGE_GO_STRICT to allow a STATED fallback to the go on PATH.'
    export GEREGE_GO_SOURCE='refused:strict'
    unset _ge_self _ge_dir _ge_here _ge_main _ge_common _ge_found _ge_origin _ge_tried _ge_cand _ge_path_go
    unset -f _ge_say 2>/dev/null || true
    return 2 2>/dev/null || exit 2
  fi

  if [ -n "$_ge_path_go" ]; then
    export GEREGE_GO_SOURCE="substituted:$_ge_path_go"
    _ge_say "SUBSTITUTING the go already on PATH:   $_ge_path_go"
    _ge_say "  $("$_ge_path_go" version 2>&1)"
    _ge_say '  WHY: the pinned toolchain is gitignored and host-local, so it is absent on'
    _ge_say '  every host but the one it was installed on. Refusing here would make the'
    _ge_say '  harness unrunnable rather than safer — the compiler-absent refusals in'
    _ge_say '  check-ledger-invariants.sh and conformance.sh:load_toolchain still stand.'
    _ge_say '  GOROOT/GOPATH/GOCACHE/GOMODCACHE are deliberately NOT exported on this path;'
    _ge_say '  this go uses its own built-in GOROOT.'
    _ge_say 'THIS IS A TOOLCHAIN SUBSTITUTION AND IT IS STATED, NOT HIDDEN. It is fine for'
    _ge_say '  building and for the source-level guards. It is NOT a pinned-toolchain run,'
    _ge_say '  and any PARITY claim must name the toolchain above. GEREGE_GO_STRICT=1'
    _ge_say '  refuses instead of substituting.'
  else
    export GEREGE_GO_SOURCE='absent:no-go-on-path'
    _ge_say 'and there is NO `go` on PATH either, so nothing was exported and nothing was'
    _ge_say '  substituted. The caller`s own compiler-absent refusal is about to fire; that'
    _ge_say '  message is the authoritative one and this note only says why PATH is unchanged.'
  fi
  unset -f _ge_say 2>/dev/null || true
fi

unset _ge_self _ge_dir _ge_here _ge_main _ge_common _ge_found _ge_origin _ge_tried _ge_cand _ge_path_go
