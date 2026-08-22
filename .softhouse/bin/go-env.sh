#!/bin/sh
# Repo-local Go toolchain for the gerege-nbfi migration.
# Installed by local fire 20260819-170001. NOT on Buyan's PATH and NOT committed
# (.gitignore'd) — `rm -rf .softhouse/toolchain` fully reverses it.
#
# Usage from any checkout OR worktree, on any host:
#     . /path/to/gerege-nbfi/.softhouse/bin/go-env.sh
#     go build ./...      # from nexus/
#
# GOROOT is still an ABSOLUTE path into the MAIN checkout, so isolated worktrees
# share one toolchain and one module cache. What changed (T253b) is that the path
# is DERIVED rather than hardcoded.
#
# ---------------------------------------------------------------------------
# T253b — D2. WHY THIS FILE STOPPED HARDCODING A PATH.
#
# It used to read `GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain`.
# On any other host that exported a GOROOT pointing at a directory that does not
# exist, and the failure surfaced downstream as
#     ledger-invariants: the guard DID NOT COMPILE ... EXIT 2 — NOT a pass
#     go: cannot find GOROOT directory
# The guard's refusal was CORRECT and fail-closed and is untouched. The defect was
# here: this file turned "the toolchain is not installed on this host" into the far
# more alarming "a HARD money guard did not compile", by exporting a broken GOROOT
# without a word of complaint.
#
# TWO RULES THIS FILE NOW OBEYS:
#   1. NEVER export a GOROOT that does not exist. An unset GOROOT lets the caller's
#      own `command -v go` refusal fire accurately; a bogus one does not.
#   2. NEVER substitute a toolchain silently. If the pinned toolchain is not the one
#      in use, say so on stderr, every time, unconditionally. A silent substitution
#      in a money-guard toolchain is the same class of defect as the one above.
#
# THE ENGINEERING DECISION, made under CLAUDE.md § Answering gates
# (ENGINEERING — decided, not escalated; chosen_by: agent; T253b):
#
#   CHOSEN — ANNOUNCED FALLBACK. If the pinned toolchain is absent and a `go` exists
#   on PATH, use it and print a loud, unmissable stderr banner naming the binary, its
#   version, the pinned path that was searched and missed, and the fact that it is NOT
#   the pinned toolchain. `GEREGE_GO_SOURCE` records the provenance for any caller that
#   wants to branch on it.
#
#   REJECTED — HARD REFUSAL (export nothing, return non-zero). Rejected for two
#   reasons, the second decisive:
#     (a) It preserves the exact symptom T253 exists to remove: on every non-Mac host
#         the ledger-invariants guard still cannot run, while a perfectly serviceable
#         `go` may be sitting on PATH.
#     (b) IT WOULD NOT ACTUALLY PREVENT THE SUBSTITUTION, ONLY THE ANNOUNCEMENT OF IT.
#         Both consumers — .softhouse/conformance.sh:load_toolchain and
#         .softhouse/guards/check-ledger-invariants.sh:build_guard — source this file
#         and then test `command -v go` for themselves. With nothing exported they
#         would find and use the PATH `go` regardless, and nobody would have said so.
#         Refusing here buys silence, not safety. Announcing is strictly stronger.
#
#   SUB-DECISION — THIS FILE ALWAYS RETURNS 0. It is SOURCED, so it must neither `exit`
#   (that would kill the caller's shell) nor mutate the caller's shell options: no
#   `set -e`, no `set -u`, no `pipefail` here, deliberately, and that is why the usual
#   `set -euo pipefail` standing rule does not apply to this one file. Returning
#   non-zero is also unsafe: a caller running under `set -e` would abort at the
#   `. go-env.sh` line — which is precisely the D1 failure mode (dying before the probe
#   line is ever printed) reintroduced by a different route. The fail-closed decision is
#   not this file's to make and it is already made correctly by both consumers, which
#   EXIT 2 on a missing compiler. This file's whole job is to be accurate and loud.
#
# NOTHING HERE CAN MAKE A GUARD PASS. The worst case is that a guard compiles with an
# unpinned Go and then refuses on its own merits. No guard is weakened by this file.
# ---------------------------------------------------------------------------

# _gerege_try PATH — record PATH as searched and, if it really holds a go binary,
# latch it into _g_found. Absence here is decided by `-x` on an actual file, never
# inferred from the exit status of anything else.
_gerege_try() {
    [ -n "$1" ] || return 0
    [ -z "$_g_found" ] || return 0
    _g_abs=$(CDPATH='' cd -- "$1" 2>/dev/null && pwd) || _g_abs="$1"
    _g_searched="$_g_searched
    $_g_abs"
    if [ -x "$_g_abs/go/bin/go" ]; then
        _g_found="$_g_abs"
    fi
    return 0
}

_gerege_go_env() {
    _g_anchor=''
    _g_root=''
    _g_pinned=''
    _g_gitrc=0

    # --- 1. Anchor on this script's own directory, if the shell will disclose it. ---
    # POSIX sh gives a sourced script no way to find itself, so this is best-effort and
    # every result below is validated against the filesystem before it is believed.
    if [ -n "${BASH_VERSION:-}" ]; then
        _g_anchor=$(eval 'printf %s "${BASH_SOURCE[0]}"' 2>/dev/null) || _g_anchor=''
    elif [ -n "${ZSH_VERSION:-}" ]; then
        _g_anchor=$(eval 'printf %s "${(%):-%x}"' 2>/dev/null) || _g_anchor=''
    fi
    if [ -n "$_g_anchor" ]; then
        _g_anchor=$(CDPATH='' cd -- "$(dirname -- "$_g_anchor")" 2>/dev/null && pwd) \
            || _g_anchor=''
    fi
    [ -n "$_g_anchor" ] || _g_anchor=$PWD

    # --- 2. The MAIN checkout, which is NOT this worktree. ---
    # `--git-common-dir` is the honest route: inside a linked worktree it resolves to the
    # main checkout's .git, which is where the shared, gitignored toolchain actually lives.
    # P-80: the rc is CLASSIFIED, not swallowed — it is carried in _g_gitrc and reported in
    # the diagnostic below. No absence is ever asserted from this rc alone; the candidates
    # are validated by testing for a real executable, so a git error cannot fabricate one.
    _g_common=$(git -C "$_g_anchor" rev-parse --git-common-dir 2>/dev/null)
    _g_gitrc=$?
    if [ "$_g_gitrc" -eq 0 ] && [ -n "$_g_common" ]; then
        case $_g_common in
            /*) ;;
            *)  _g_common=$_g_anchor/$_g_common ;;
        esac
        _g_root=$(CDPATH='' cd -- "$_g_common/.." 2>/dev/null && pwd) || _g_root=''
    fi

    # --- 3. Candidate toolchains, most authoritative first. ---
    #   a. an explicit caller override         (announced, never silent)
    #   b. the MAIN checkout via git           (the worktree-correct answer)
    #   c. the script's own checkout, git-free (this file lives in .softhouse/bin)
    # Candidates are tried ONE AT A TIME rather than word-split out of a delimited
    # string: a checkout path containing a space must not silently become two paths,
    # and IFS is not touched at all, so nothing about the caller's shell changes.
    _g_found=''
    _g_searched=''
    _gerege_try "${GEREGE_TOOLCHAIN:-}"
    if [ -z "$_g_found" ] && [ -n "$_g_root" ]; then
        _gerege_try "$_g_root/.softhouse/toolchain"
    fi
    if [ -z "$_g_found" ]; then
        _gerege_try "$_g_anchor/../../toolchain"
    fi

    # --- 4a. The pinned toolchain is here. Export it and say nothing. ---
    if [ -n "$_g_found" ]; then
        GEREGE_TOOLCHAIN="$_g_found"
        GEREGE_GO_SOURCE=pinned
        export GEREGE_GO_SOURCE
        export GOROOT="$GEREGE_TOOLCHAIN/go"
        export GOPATH="$GEREGE_TOOLCHAIN/gopath"
        export GOCACHE="$GEREGE_TOOLCHAIN/gocache"
        export GOMODCACHE="$GEREGE_TOOLCHAIN/gomodcache"
        export PATH="$GOROOT/bin:$PATH"
        return 0
    fi

    # --- 4b. It is not. Export NO GOROOT, and be loud about what happens instead. ---
    # An inherited GOROOT that points nowhere is the D2 symptom itself and would break a
    # PATH `go` too, so it is dropped rather than passed along.
    if [ -n "${GOROOT:-}" ] && [ ! -d "${GOROOT:-}" ]; then
        printf '%s\n' "go-env.sh: dropping inherited GOROOT=$GOROOT — that directory does not exist." >&2
        unset GOROOT
    fi

    printf '%s\n' "go-env.sh: the PINNED Go toolchain was NOT found on this host." >&2
    printf '%s\n' "go-env.sh:   searched (needed <cand>/go/bin/go):$_g_searched" >&2
    printf '%s\n' "go-env.sh:   anchor: $_g_anchor (git rev-parse --git-common-dir rc=$_g_gitrc)" >&2

    if command -v go >/dev/null 2>&1; then
        GEREGE_GO_SOURCE=fallback-path
        export GEREGE_GO_SOURCE
        printf '%s\n' "go-env.sh: FALLBACK IN EFFECT — using the \`go\` already on PATH:" >&2
        printf '%s\n' "go-env.sh:   $(command -v go)" >&2
        printf '%s\n' "go-env.sh:   $(go version 2>&1)" >&2
        printf '%s\n' "go-env.sh: THIS IS NOT THE PINNED TOOLCHAIN. It is announced, never silent." >&2
        printf '%s\n' "go-env.sh: Guards may build with it; VECTOR CAPTURE and any parity claim must" >&2
        printf '%s\n' "go-env.sh: use the pinned toolchain. GEREGE_GO_SOURCE=fallback-path." >&2
        return 0
    fi

    GEREGE_GO_SOURCE=absent
    export GEREGE_GO_SOURCE
    printf '%s\n' "go-env.sh: and there is NO \`go\` on PATH either. Nothing was exported." >&2
    printf '%s\n' "go-env.sh: The caller's own toolchain check will now refuse — that refusal is" >&2
    printf '%s\n' "go-env.sh: correct and fail-closed. GEREGE_GO_SOURCE=absent." >&2
    return 0
}

_gerege_go_env
unset -f _gerege_go_env _gerege_try 2>/dev/null
# No `|| true` and no trailing `return` anywhere in this file. `unset` of a name that
# is already unset succeeds, so this last command sets the sourced status to 0 on its
# own merits — there is no swallowed failure here to hide one (P-80).
unset _g_anchor _g_root _g_pinned _g_gitrc _g_common _g_abs _g_found _g_searched 2>/dev/null
