#!/bin/sh
# Repo-local Go toolchain for the gerege-nbfi migration.
# Installed by local fire 20260819-170001. NOT on Buyan's PATH and NOT committed
# (.gitignore'd) — `rm -rf .softhouse/toolchain` fully reverses it.
#
# Usage from any checkout OR worktree, on any host — copy this line, not a path:
#     . "$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh"
#     go build ./...      # from nexus/
#
# Knobs, both OPT-IN and both OFF by default:
#     GEREGE_TOOLCHAIN=/abs/dir   search this directory first (announced, never silent)
#     GEREGE_GO_STRICT=1          refuse rather than substitute an unpinned `go`.
#                                 The ONLY thing that can make sourcing this file return
#                                 non-zero, and it does so only when the pinned toolchain
#                                 is absent. Under `set -e` that ABORTS the caller at the
#                                 activation line — intended; see the decision below.
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
#         Every consumer sources this file and then tests `command -v go` for itself.
#         With nothing exported they would find and use the PATH `go` regardless, and
#         nobody would have said so. Refusing here buys silence, not safety. Announcing
#         is strictly stronger. [T254b VERIFIED this premise by reading the consumers:
#         .softhouse/reviews/t254-harness-portability/REVIEW.md, F-8.]
#
#   SUB-DECISION — THIS FILE RETURNS 0 IN EVERY ARM EXCEPT ONE, AND THE EXCEPTION IS
#   OPT-IN. It is SOURCED, so it must neither `exit` (that would kill the caller's
#   shell) nor mutate the caller's shell options: no `set -e`, no `set -u`, no
#   `pipefail` here, deliberately, and that is why the usual `set -euo pipefail`
#   standing rule does not apply to this one file.
#
#   F-8 CORRECTION (T272), because a false premise left in the tree is a trap for the
#   next reader. This comment used to justify "always returns 0" partly by asserting
#   that "a caller running under `set -e` would abort at the `. go-env.sh` line".
#   THAT IS FACTUALLY WRONG ABOUT EVERY CURRENT CONSUMER and it is stated here as a
#   fact about them. MEASURED by T272 on this tree, all three consumers of this file:
#       .softhouse/conformance.sh:396                    set -u -o pipefail
#       .softhouse/guards/check-ledger-invariants.sh:39  set -u -o pipefail
#       .softhouse/guards/drive-red-ledger-invariants.sh:18  set -u -o pipefail
#   Not one sets `-e`. (T254b measured the first two and named "both consumers";
#   drive-red-ledger-invariants.sh is a THIRD and it agrees.) So the premise is WRONG
#   about today's callers. It is RIGHT about tomorrow's: `reference-oracle.md`
#   prescribes a bare `. "$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh"`
#   for new scripts to copy, and a new script written with `set -e` WILL abort at that
#   line in the one arm below that returns non-zero. Saying exactly that is more useful
#   than deleting the sentence, so it is said rather than deleted.
#
#   THE ONE NON-ZERO ARM — `GEREGE_GO_STRICT` (grafted by T272 from the cloud's T253
#   implementation, origin/softhouse/T253-harness-portability = d7a7ea35,
#   go-env.sh:159-167; recipe in REVIEW.md F-6).
#
#     WHAT IT MEANS. `GEREGE_GO_STRICT` set to any NON-EMPTY value makes the REJECTED
#     hard-refusal decision above reachable as CONFIGURATION instead of as a patch.
#     It does not add a new policy; it selects the alternative that was already
#     written down and rejected as the DEFAULT.
#
#     WHAT TURNS ON WHEN IT IS SET. Exactly one thing, in exactly one arm: if the
#     PINNED toolchain is NOT found, this file refuses instead of substituting — it
#     exports no GOROOT and no GEREGE_GO_BIN, sets GEREGE_GO_SOURCE=refused, prints a
#     refusal banner, and the sourcing returns 2.
#
#     WHAT FAILS WHEN IT IS SET: nothing at all when the pinned toolchain IS present
#     (the arm is not reached, and the sourcing returns 0 exactly as before). When the
#     toolchain is ABSENT: the sourcing returns 2, so a caller that tests the status of
#     the `. go-env.sh` line fails there, and a caller under `set -e` ABORTS there.
#     THAT IS THE INTENDED BEHAVIOUR AND T272 DECIDES IT DELIBERATELY (T256 asked for
#     the decision rather than the discovery): if you asked for strict, dying at the
#     activation line on a host with no pinned toolchain is the answer you asked for.
#     It is also why strict is OPT-IN and OFF BY DEFAULT — see the P-84 caveat below.
#
#     WHAT FAILS WHEN IT IS NOT SET: nothing changes from the pre-graft file. Every
#     arm returns 0, the announced fallback stands, and no transcript differs.
#
#     WHICH FIRE SETS IT: NEITHER, TODAY. MEASURED by T272 — `GEREGE_GO_STRICT` does
#     not appear in .softhouse/bin, .softhouse/launchd or .claude anywhere in this
#     tree (evidence: .softhouse/capture/t272-goenv-graft/evidence/10-locate-cloud-arm
#     .txt, section 6). So the launchd fire on Buyan's Mac and the cloud fire BOTH run
#     with it unset, and this graft is behaviour-identical for both of them. That is
#     the point: A GRADED PATH MUST NOT DEPEND ON WHERE IT RUNS, and an opt-in switch
#     that no fire sets cannot make it depend on that.
#
#     THE HOST-STATE STATEMENT, SAID PLAINLY. `.softhouse/toolchain` is gitignored and
#     host-local, so "is the pinned toolchain here?" ALREADY answers differently on the
#     two fires — that is the fact this whole file exists to handle, and no switch can
#     remove it. What strict does is change the CONSEQUENCE of that difference from a
#     loud substitution to a loud refusal. It never makes the difference quieter, and
#     it never changes anything on a host where the toolchain IS present. If a future
#     fire sets it, it must set it for BOTH fires or state in writing why not.
#
#     P-84 CAVEAT, WHICH IS WHY STRICT IS NOT THE DEFAULT. P-84: "exit 2 with NO probe
#     line PRINTED is a FAILED HARD GUARD, not an oracle outage — test for the line's
#     PRESENCE before its value." A strict refusal inside a `set -e` caller kills that
#     caller BEFORE it can print a probe line, producing the single most ambiguous
#     signal this harness can emit. Default-off keeps that signal unreachable unless
#     somebody deliberately asks for it.
#
#     WHAT STRICT DOES *NOT* DO, STATED SO NOBODY OVER-READS IT. It does not remove a
#     `go` from PATH. This file will not hide a compiler it did not install. A caller
#     that ignores both the sourcing status and GEREGE_GO_SOURCE will still find that
#     `go` and build with it. NONE OF THE THREE CURRENT CONSUMERS CHECKS EITHER, so
#     today strict is LOUD BUT ADVISORY at the call site. Wiring the three call sites
#     is FU-T272-1, filed with an exact patch in
#     .softhouse/capture/t272-goenv-graft/GOENV-STRICT-WIRING.md, because
#     .softhouse/conformance.sh and the guards are not T272's to edit this batch.
#
#     THE TWO PREDICATES MUST NOT BE MERGED (the T292 shape). "Did go-env.sh refuse?"
#     and "is there a compiler on PATH?" are DIFFERENT questions whose fail-closed
#     directions point opposite ways: the first fails closed by treating non-zero as
#     STOP, the second fails closed by treating absence as STOP. Do not widen one
#     predicate to answer both. Each call site's direction is written out in
#     GOENV-STRICT-WIRING.md.
#
# NOTHING HERE CAN MAKE A GUARD PASS. The worst case is that a guard compiles with an
# unpinned Go and then refuses on its own merits. No guard is weakened by this file,
# and the strict arm can only ever make it refuse EARLIER, never later.
#
# VARIABLES THIS FILE EXPORTS, AND WHICH OF THEM MAY BE COMPARED ACROSS HOSTS:
#   GEREGE_GO_SOURCE  a BARE TOKEN, host-independent by construction, one of
#                     `pinned` | `fallback-path` | `absent` | `refused`.
#                     SAFE to compare across hosts and safe to print into a graded
#                     transcript. The first three are T253b's and are kept unchanged:
#                     `reference-oracle.md:660-661` documents them and T256's drive
#                     ASSERTS on them, so renaming them would rot a document this task
#                     does not own and redden a drive it did not write. `refused` is new.
#   GEREGE_GO_BIN     the ABSOLUTE PATH of the `go` actually in use, or unset when
#                     there is none. This is T254b's "richer GEREGE_GO_SOURCE value"
#                     (REVIEW.md merge-step 3 — the path is what a parity claim has to
#                     name) carried in a SEPARATE variable rather than folded into the
#                     token. Deliberate, and inside the latitude the reviewer gave
#                     ("Keep the Mac's pinned/absent tokens or the cloud's pinned:$PATH
#                     — either is fine"). The reason to split them: an absolute path is
#                     HOST STATE, and the cloud's `pinned:/Users/buv/...` form would
#                     bake this Mac's home directory into the very variable T267 wants
#                     printed into the graded verdict block. **NEVER compare
#                     GEREGE_GO_BIN across hosts.** Print it as host detail; grade on
#                     the token.
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
    # GEREGE_GO_STRICT IS NOT CONSULTED HERE, ON PURPOSE. Strict asks "refuse rather than
    # SUBSTITUTE"; nothing is being substituted on this path. So on a host that has the
    # pinned toolchain, setting strict changes nothing at all — same exports, same rc 0,
    # same transcript. That is what keeps the switch from becoming a second axis of
    # host-dependent behaviour.
    if [ -n "$_g_found" ]; then
        GEREGE_TOOLCHAIN="$_g_found"
        GEREGE_GO_SOURCE=pinned
        export GEREGE_GO_SOURCE
        export GOROOT="$GEREGE_TOOLCHAIN/go"
        export GOPATH="$GEREGE_TOOLCHAIN/gopath"
        export GOCACHE="$GEREGE_TOOLCHAIN/gocache"
        export GOMODCACHE="$GEREGE_TOOLCHAIN/gomodcache"
        export PATH="$GOROOT/bin:$PATH"
        # Host detail, never a graded token. See the variable table in the header.
        GEREGE_GO_BIN="$GOROOT/bin/go"
        export GEREGE_GO_BIN
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

    # Decided ONCE, by testing for a real executable, and reused by both arms below.
    _g_pathgo=$(command -v go 2>/dev/null) || _g_pathgo=''

    # --- 4b-i. GEREGE_GO_STRICT — the REJECTED hard refusal, reachable as CONFIG. ---
    # GRAFTED BY T272 from d7a7ea35:.softhouse/bin/go-env.sh:159-167, per T254b's recipe
    # (REVIEW.md:36-44 "graft it AFTER the Mac's stale-GOROOT drop, which must be kept").
    # It sits AFTER the drop above and AFTER the search diagnostics, so a strict refusal
    # still tells the reader which paths were searched and still repairs a stale GOROOT
    # it inherited — the two things that make the refusal actionable rather than merely
    # negative. The cloud version did NEITHER: it kept the stale GOROOT (F-3 HIGH).
    if [ -n "${GEREGE_GO_STRICT:-}" ]; then
        GEREGE_GO_SOURCE=refused
        export GEREGE_GO_SOURCE
        unset GEREGE_GO_BIN 2>/dev/null
        printf '%s\n' "go-env.sh: GEREGE_GO_STRICT is set, so this is a REFUSAL and not a substitution." >&2
        if [ -n "$_g_pathgo" ]; then
            printf '%s\n' "go-env.sh:   there IS a \`go\` on PATH and it was DELIBERATELY NOT adopted:" >&2
            printf '%s\n' "go-env.sh:   $_g_pathgo" >&2
        else
            printf '%s\n' "go-env.sh:   there is no \`go\` on PATH either, so nothing was available to adopt." >&2
        fi
        printf '%s\n' "go-env.sh: Nothing was exported. Install the pinned toolchain, or set GEREGE_TOOLCHAIN," >&2
        printf '%s\n' "go-env.sh: or unset GEREGE_GO_STRICT to allow a STATED fallback to the go on PATH." >&2
        printf '%s\n' "go-env.sh: GEREGE_GO_SOURCE=refused, and SOURCING THIS FILE RETURNS 2 — this arm is" >&2
        printf '%s\n' "go-env.sh: the ONLY one that returns non-zero. A caller under \`set -e\` aborts here;" >&2
        printf '%s\n' "go-env.sh: that is strict mode working, not a bug." >&2
        printf '%s\n' "go-env.sh: PATH IS UNCHANGED — this file will not hide a compiler it did not install." >&2
        printf '%s\n' "go-env.sh: A caller that checks NEITHER this status NOR GEREGE_GO_SOURCE will still find" >&2
        printf '%s\n' "go-env.sh: that \`go\` and build with it. As of T272 none of the three consumers checks" >&2
        printf '%s\n' "go-env.sh: either, so STRICT IS LOUD BUT ADVISORY AT THE CALL SITE until FU-T272-1 lands" >&2
        printf '%s\n' "go-env.sh: (.softhouse/capture/t272-goenv-graft/GOENV-STRICT-WIRING.md)." >&2
        return 2
    fi

    # --- 4b-ii. Not strict: the CHOSEN announced fallback. ---
    if [ -n "$_g_pathgo" ]; then
        GEREGE_GO_SOURCE=fallback-path
        export GEREGE_GO_SOURCE
        # Only a real executable file becomes GEREGE_GO_BIN. `command -v` also answers for
        # a function or an alias, and a caller told "here is the absolute path of the go in
        # use" must not be handed a name it cannot exec (P-70: absence — and presence —
        # decided by testing the actual file, never inferred from another command's output).
        if [ -x "$_g_pathgo" ]; then
            GEREGE_GO_BIN="$_g_pathgo"
            export GEREGE_GO_BIN
        else
            unset GEREGE_GO_BIN 2>/dev/null
        fi
        printf '%s\n' "go-env.sh: FALLBACK IN EFFECT — using the \`go\` already on PATH:" >&2
        printf '%s\n' "go-env.sh:   $_g_pathgo" >&2
        printf '%s\n' "go-env.sh:   $(go version 2>&1)" >&2
        printf '%s\n' "go-env.sh: THIS IS NOT THE PINNED TOOLCHAIN. It is announced, never silent." >&2
        printf '%s\n' "go-env.sh: Guards may build with it; VECTOR CAPTURE and any parity claim must" >&2
        printf '%s\n' "go-env.sh: use the pinned toolchain. GEREGE_GO_SOURCE=fallback-path." >&2
        printf '%s\n' "go-env.sh: GEREGE_GO_STRICT=1 refuses instead of substituting (returns 2)." >&2
        return 0
    fi

    GEREGE_GO_SOURCE=absent
    export GEREGE_GO_SOURCE
    unset GEREGE_GO_BIN 2>/dev/null
    printf '%s\n' "go-env.sh: and there is NO \`go\` on PATH either. Nothing was exported." >&2
    printf '%s\n' "go-env.sh: The caller's own toolchain check will now refuse — that refusal is" >&2
    printf '%s\n' "go-env.sh: correct and fail-closed. GEREGE_GO_SOURCE=absent." >&2
    return 0
}

_gerege_go_env
# THE RETURN STATUS IS CAPTURED BEFORE ANY CLEANUP RUNS. `_gerege_go_env` returns 2 in
# exactly one arm (GEREGE_GO_STRICT + toolchain absent) and 0 in every other. Without
# this capture the graft would be INERT: the whole body lives inside a function, so a
# `return 2` there only sets the FUNCTION's status, and the `unset` commands below —
# which succeed — would overwrite it with 0 before the sourcing ever ended. The refusal
# would print and then report success. That is precisely the "loud but ineffective"
# shape this file was already criticising, so it is closed here rather than shipped.
_g_rc=$?
unset -f _gerege_go_env _gerege_try 2>/dev/null
# No `|| true` anywhere in this file, and the only `return` is the strict one below.
# `unset` of a name that is already unset succeeds, so each cleanup line sets status 0
# on its own merits — there is no swallowed failure here to hide one (P-80).
unset _g_anchor _g_root _g_pinned _g_gitrc _g_common _g_abs _g_found _g_searched _g_pathgo 2>/dev/null
if [ "${_g_rc:-0}" -ne 0 ]; then
    # STRICT REFUSAL ONLY. `return` is correct when this file is SOURCED, which is the
    # only supported use; `exit 2` covers the unsupported case of running it directly,
    # where a top-level `return` is an error in bash and dash. The 2>/dev/null suppresses
    # that error message and the `||` reads its non-zero status — the same idiom the cloud
    # arm used, and the reason it is kept.
    unset _g_rc 2>/dev/null
    return 2 2>/dev/null || exit 2
fi
# EVERY OTHER ARM ENDS HERE, ON A COMMAND THAT SUCCEEDS. Sourcing returns 0, exactly as
# it did before the graft, and with GEREGE_GO_STRICT unset that is every arm there is.
unset _g_rc 2>/dev/null
