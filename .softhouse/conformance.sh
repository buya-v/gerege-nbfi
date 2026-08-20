#!/bin/bash
# Golden-vector conformance harness — Fineract reference oracle vs the Go module.
#
#   .softhouse/conformance.sh [CONTEXT]      grade the store (optionally one context)
#   .softhouse/conformance.sh --prove        run the harness's own mutation proofs
#   .softhouse/conformance.sh --self-test    grade the HARNESS via the replay implementation
#   .softhouse/conformance.sh --help
#
# EXIT CODES
#   0  every graded vector passed AND at least one PARITY vector was graded AND the
#      reference oracle was confirmed reachable. Means "matches the reference oracle
#      on captured vectors, within the graded domain". NEVER means safe to cut over.
#   1  a mismatch or a violated property invariant. A definite, reproducible defect.
#   2  the harness, the corpus or the oracle is unusable: no Go toolchain, no
#      implementation to grade, an unreachable oracle, zero parity vectors, an
#      inadmissible vector, a refused vector, a failed HARD guard.
#   3  WRONG INTERPRETER — the harness never started. This file was handed to a
#      shell that could not be OBSERVED to run the one construct the harness is
#      built on, `< <(...)`. That covers a shell that is not bash at all (dash,
#      zsh, ksh, busybox ash), a bash with process substitution switched off
#      (bash 3.2 in POSIX mode — which is what BOTH `sh conformance.sh` and
#      `bash --posix conformance.sh` give you on macOS), and a bash that stops
#      the probe from running at all (`bash -r`). Nothing was graded, no vector
#      was read, and the reference oracle was never contacted — so 3 says
#      NOTHING about the corpus and NOTHING about the oracle. The fix is always
#      the same: re-run it under bash, `bash .softhouse/conformance.sh` or
#      `./.softhouse/conformance.sh`.
#      The test is a CAPABILITY test, never a test of the shell's name: where
#      /bin/sh IS a bash 5.x (Fedora, RHEL, and any distro that links sh to
#      bash), `sh conformance.sh` is ADMITTED and works [VERIFIED: T97 — bash
#      5.2.37 and 5.3.9, argv[0]=sh, admitted; matrix in the T97 handoff].
#
# 0, 1 and 2 are the verdict codes and there are still only three of them; 3 is not
# a verdict, it is a refusal to start, and it is deliberately NOT 2 so that a
# shell-selection mistake can never be mistaken for an oracle outage. There is no
# silent success: an empty vector set is 2, not 0, because a harness that reported
# PASS over zero vectors would be worse than no harness at all.
#
# "The oracle" here means the FINERACT REFERENCE IMPLEMENTATION we grade Go output
# against. Oracle Database is a prohibited product in this program and appears
# nowhere in this stack. PostgreSQL is the only permitted database.
#=END-OF-HELP=

# ---------------------------------------------------------------------------
# INTERPRETER GUARD. This is the FIRST EXECUTABLE STATEMENT IN THE FILE and it
# must stay first. It runs before any shell option is set, before a vector file is
# opened, before the Go toolchain is looked for and before the oracle is probed,
# so it cannot swallow, delay, or reassign a verdict: on the path where it fires,
# no verdict has been computed and none is printed.
#
# WHY IT EXISTS (T76 and T77 found this independently in the same fire).
# `sh .softhouse/conformance.sh` used to die at the first process substitution
# (the `done < <(find …)` in guard_no_float_in_vectors) with a bash syntax error
# and **exit 2** — and 2 is this harness's "unusable / oracle unreachable" code AND
# the /softhouse-program driver's oracle-is-down stop condition. So a one-word
# shell-selection typo was indistinguishable from a genuine oracle outage and could
# park every vector task in the program under a reason that was not true. Under
# `zsh` it was worse: BASH_SOURCE is unset, SCRIPT_DIR resolved to the wrong
# directory, the toolchain was therefore "not found", and the harness printed its
# OWN "EXIT 2 — the harness is unusable" line over a diagnosis that was fiction.
#
# WHAT IT TESTS, and why "is this bash?" is not enough:
#   (a) BASH_VERSION unset  →  not bash at all (dash, zsh, ksh, busybox ash).
#   (b) BASH_VERSION set is NOT sufficient. bash 3.2 — which is BOTH /bin/sh and
#       /bin/bash on macOS — disables process substitution in POSIX mode, and it
#       enters POSIX mode when invoked as `sh` and under `--posix`. Those runs ARE
#       bash by every name test and still cannot parse this file. So the guard
#       feature-tests the construct itself: if `< <(…)` does not work HERE, this
#       shell cannot run this file, whatever it calls itself. Equally, a bash
#       where POSIX mode keeps process substitution (5.1+) passes the test and is
#       correctly left alone — the guard keys on the CAPABILITY, never on the
#       shell's name. On Fedora/RHEL, where /bin/sh IS bash 5.x, `sh` is admitted
#       and works [VERIFIED: T97 matrix — 5.2.37 and 5.3.9, plain, `--posix`,
#       argv[0]=sh, and argv[0]=sh + `--posix`: eight of eight ADMITTED].
#
# POSITIVE EVIDENCE, and why the first version of this guard was not enough (T86
# raised this while APPROVING T81; closed by T97).
#   The original probe asked "did a process-substitution command FAIL?" and
#   admitted the shell when the answer was no. That cannot distinguish
#   "process substitution works" from "the probe never executed", and a shell in
#   the second state is exactly as unable to run this file as one in the first.
#   `bash -r` (restricted) is such a shell: it refuses the `>/dev/null 2>&1` the
#   old probe redirected itself with, so the subshell never ran, the `if`
#   condition read false, and the harness was ADMITTED — then died at
#   `SCRIPT_DIR="$(cd …)"` (restricted shells refuse `cd` too), reported
#   `no Go toolchain. Expected /.softhouse/bin/go-env.sh` — a path that exists
#   nowhere — and exited **2**. A shell-selection mistake wearing the oracle's
#   outage code: precisely the defect exit 3 was created to abolish, one layer in.
#   [VERIFIED: T97 reproduced it against `git show main:.softhouse/conformance.sh`
#   — exit 2, that exact fabricated line.]
#
#   So the probe no longer looks for the ABSENCE of a failure. It demands a
#   VALUE. `$CONFORMANCE_PSUB_TOKEN` is written on the far side of a process
#   substitution and read back through `< <(…)`; the guard proceeds only when it
#   compares equal to what was expected. The token can reach the comparison by
#   exactly one route — the construct working — so every way of not running the
#   probe (syntax error, refused redirection, killed subshell, a shell that never
#   reached the line) yields an empty observation and FAILS CLOSED.
#
#   Detail that matters, and the exact rock T86's own first draft split on:
#   `printf '%s\n'`, WITH the newline. A `while read -r x; do …; done < <(printf
#   %s value)` reads a final line that has no terminator, `read` returns non-zero,
#   the loop body never runs, and plain, healthy bash is REFUSED. This probe uses
#   a single `read` and grades the VARIABLE, not `read`'s status, so it is immune
#   to that either way — but the newline is there so nothing downstream inherits
#   the trap. `IFS=` stops a hostile inherited IFS from splitting the token away
#   [VERIFIED: T97 — `IFS=oc`, `IFS=' '` and `IFS=$'\n'` in the environment, all
#   ADMITTED], and `builtin` pins `eval`/`read`/`printf` to bash's own so an
#   exported shell function of any of those names can neither forge the token nor
#   suppress it. `builtin eval` is not decoration: with a bare `eval`, an exported
#   `eval()` function made bash 5.2.37 refuse the harness, and that WOULD have
#   been a false refusal [VERIFIED: T97 hostile-environment matrix, both readings].
#   `builtin` itself has no such shield and there is no fixed point for the game:
#   an exported `builtin()` function DOES make this guard refuse [VERIFIED: T97,
#   bash 5.2.37]. That is one name instead of three, the refusal is fail-CLOSED,
#   and no fail-closed refusal can turn a red run green — which is why the trade
#   is taken in this direction and written down rather than hidden.
#
#   The whole probe runs inside a COMMAND SUBSTITUTION, i.e. a subshell, so a
#   shell that aborts on a syntax error inside `eval` (which is what POSIX mode
#   does to a special builtin) kills only that subshell; the outer script survives
#   to print the refusal. It is reached only once BASH_VERSION is known to be set,
#   so that `builtin` and `eval` are always bash's own.
# ---------------------------------------------------------------------------
EXIT_WRONG_INTERPRETER=3
CONFORMANCE_PSUB_TOKEN="conformance-psub-live"
conformance_psub_seen=""
if [ -n "${BASH_VERSION:-}" ]; then
  conformance_psub_seen="$(
    builtin eval '
      IFS= builtin read -r _conformance_psub_line \
           < <(builtin printf "%s\n" "$CONFORMANCE_PSUB_TOKEN")
      builtin printf "%s" "$_conformance_psub_line"
    ' 2>/dev/null
  )"
fi
conformance_shell_why=""
if [ -z "${BASH_VERSION:-}" ]; then
  # Reported exactly as observed. zsh, for instance, HAS process substitution but
  # is still fatal here (BASH_SOURCE unset -> SCRIPT_DIR wrong -> a fabricated
  # "no Go toolchain" exit 2), so the diagnosis must not claim a missing feature
  # this shell actually has. A guard that says the wrong true-sounding thing is
  # how the next reader is sent to the wrong place.
  conformance_shell_why="BASH_VERSION is unset, so this shell is not bash at all."
elif [ "$conformance_psub_seen" != "$CONFORMANCE_PSUB_TOKEN" ]; then
  # Deliberately phrased as an OBSERVATION, not as a diagnosis. The guard knows
  # the token did not arrive; in general it does NOT know which of "the construct
  # is unavailable" and "the probe was never allowed to run" is true, and
  # inventing one would be the same class of fiction as the old `no Go toolchain`
  # line. The ONE case it can name for certain is a restricted shell, which
  # advertises itself in `$-` [VERIFIED: T97 — `$-` contains `r` under `bash -r`
  # on 3.2.57, 5.2.37 and 5.3.9: `hrB` running a script, `hrBc` under `-c`; the
  # test is for the `r`, not for the whole string]. Worth naming, because
  # `bash -r` is the ONE refusal here where process substitution itself is fine:
  # `bash -r -c 'IFS= read -r v <
  # <(printf "%s\n" X)'` returns X. What `bash -r` cannot do is the rest of the
  # harness — `cd` is refused, so SCRIPT_DIR and REPO_ROOT come out EMPTY, and
  # every `>` redirection is refused too. Refusing it is correct; the old guard
  # admitted it and the run then died at exit 2 blaming a missing Go toolchain.
  conformance_shell_why="this IS bash ${BASH_VERSION}, but the process-substitution probe did not deliver its token: expected [${CONFORMANCE_PSUB_TOKEN}], observed [${conformance_psub_seen}]. Either '< <(...)' does not work in this shell, or this shell stopped the probe from running at all."
  case "$-" in
    *r*) conformance_shell_why="$conformance_shell_why It is the latter: this is a RESTRICTED shell (\$- = $-, i.e. 'bash -r'). A restricted shell refuses the redirection the probe needs AND the 'cd' this harness needs, so it could never have run the harness either." ;;
  esac
fi
if [ -n "$conformance_shell_why" ]; then
  printf '%s\n' \
    "conformance: WRONG INTERPRETER — this harness requires bash, and the shell that" \
    "conformance: was handed this file cannot execute it." \
    "conformance:   $conformance_shell_why" \
    "conformance:" \
    "conformance: THE HARNESS NEVER STARTED. Nothing was graded, no vector was read, and" \
    "conformance: the reference oracle (Fineract) was NEVER CONTACTED. This is not a" \
    "conformance: verdict and it is not evidence about the oracle. THE ORACLE IS NOT DOWN;" \
    "conformance: the invocation is wrong. Do NOT read this as exit 2 (harness/corpus/" \
    "conformance: oracle unusable) and do NOT park a task on an oracle-outage reason." \
    "conformance:" \
    "conformance: FIX — re-run it under bash:" \
    "conformance:     bash .softhouse/conformance.sh" \
    "conformance:     ./.softhouse/conformance.sh        (the shebang selects bash)" \
    "conformance: On bash 3.2 (macOS) 'sh conformance.sh' and 'bash --posix conformance.sh'" \
    "conformance: are BOTH wrong: invoked either way, bash switches process substitution" \
    "conformance: off. Where /bin/sh IS a bash 5.x (Fedora, RHEL), 'sh' is fine — this" \
    "conformance: guard tests the CAPABILITY, not the name of the shell. 'bash -r' is" \
    "conformance: refused everywhere: a restricted shell cannot run this harness." \
    "conformance:" \
    "conformance: EXIT 3 — wrong interpreter. See the EXIT CODES table at the top of this" \
    "conformance: file and the 'Running it' section of .softhouse/vectors/README.md." >&2
  exit "$EXIT_WRONG_INTERPRETER"
fi
unset conformance_shell_why conformance_psub_seen CONFORMANCE_PSUB_TOKEN

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STORE_ROOT="$REPO_ROOT/.softhouse/vectors"
NEXUS_DIR="$REPO_ROOT/nexus"
# NO CONTRACT PATH CONSTANT LIVES HERE, DELIBERATELY. The frozen DEC-1 artefact is
# named by .softhouse/vectors/PIN.json ("contract_file") and its bytes are checked
# against PIN.json ("contract_sha256") by Go — admit.go VerifyContractDigest. A
# second copy of that path in this script would be a second source of truth that
# nothing keeps in step, and it read like a guard while enforcing nothing: the
# CONTRACT_REL variable that used to sit on this line was assigned and never used.
# Removed rather than wired up, because wiring it up would ADD an enforcement the
# harness does not currently have and duplicate one it already has (T62).
HARNESS_PKG="$NEXUS_DIR/internal/apps/loanschedule/conformance"
CMD_PKG="./internal/apps/loanschedule/conformance/cmd/conformance"

# The reference oracle's health endpoint. Overridable ONLY so the unreachable-oracle
# code path can be demonstrated without touching the live containers, which several
# captures' comparability rests on having run uninterrupted.
ORACLE_HEALTH_URL="${CONFORMANCE_ORACLE_HEALTH_URL:-https://localhost:8443/fineract-provider/actuator/health}"

EXIT_UNUSABLE=2

# Scratch paths are script-global, not function-local: an EXIT trap fires after the
# function that created them has returned, so a `local` would be out of scope by
# then and `set -u` would abort the cleanup.
CONF_BIN=""
CONF_TMP=""
cleanup() {
  [ -n "$CONF_BIN" ] && rm -f "$CONF_BIN"
  [ -n "$CONF_TMP" ] && rm -rf "$CONF_TMP"
  return 0
}
trap cleanup EXIT

say()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }

usage() {
  # SELF-LOCATING. --help prints the header comment block, from line 2 down to the
  # line before the sentinel. It used to name a hard-coded range, and that range
  # had ALREADY drifted once: '2,30p' when the block ended at line 24 trailed five
  # lines of raw shell (`set -u -o pipefail`, `SCRIPT_DIR=…`) into --help, was
  # corrected to '2,34p', and would have drifted again the moment anyone edited the
  # header — which T97 did. A literal line number in a file that gets edited is not
  # a bound, it is a countdown. The sentinel moves with the block.
  #
  # The sentinel is matched anchored at column 0 (`^#=END-OF-HELP=$`), so the
  # mention of it in this comment cannot match. If it is ever deleted, this is an
  # ERROR and not a silent short/long --help: a help function that cannot find its
  # own text must say so, not print whatever it happens to find.
  local src="${BASH_SOURCE[0]}" end
  end="$(grep -n '^#=END-OF-HELP=$' "$src" | head -1 | cut -d: -f1)"
  if [ -z "$end" ] || [ "$end" -lt 3 ]; then
    warn "conformance: --help is broken: the '#=END-OF-HELP=' sentinel that bounds the"
    warn "conformance: header comment block is missing from $src (or is at line $end)."
    warn "conformance: Restore it on the line directly after the header block."
    return 1
  fi
  sed -n "2,$((end - 1))p" "$src" | sed 's/^# \{0,1\}//'
}

# ---------------------------------------------------------------------------
# Toolchain
# ---------------------------------------------------------------------------
load_toolchain() {
  # The Go toolchain is repo-local and gitignored, and it is NOT on the default
  # PATH. A bare `go` saying "command not found" is the expected state of a fresh
  # shell, not a broken environment.
  local env_script="$REPO_ROOT/.softhouse/bin/go-env.sh"
  if [ -f "$env_script" ]; then
    # shellcheck disable=SC1090
    . "$env_script"
  fi
  if ! command -v go >/dev/null 2>&1; then
    warn "conformance: no Go toolchain. Expected $env_script to put one on PATH."
    warn "conformance: EXIT 2 — the harness is unusable. This is NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

# ---------------------------------------------------------------------------
# HARD guards. They prove the ABSENCE of known-bad patterns and nothing more.
# ---------------------------------------------------------------------------

# guard_no_float_in_vectors: no JSON number in any vector file may carry a '.',
# 'e' or 'E'. Every monetary value in the store is an integer STRING in minor
# units, so nothing legitimate is inconvenienced. A float anywhere in a vector
# file is a rejection — including in a field somebody thought was "just" a rate or
# a day count.
guard_no_float_in_vectors() {
  local bad=0 f
  while IFS= read -r f; do
    # Strip string literals first, then look for a decimal or exponent number.
    if perl -0pe 's/"(\\.|[^"\\])*"//g' "$f" | grep -Eq '[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]'; then
      warn "conformance: FLOAT-SHAPED NUMBER in $f"
      bad=1
    fi
  done < <(find "$STORE_ROOT" -name '*.json' -type f | sort)
  return "$bad"
}

# guard_no_float_in_harness: no floating-point identifier in the loanschedule Go
# tree. Implemented in Go (TestNoFloatInTheLoanScheduleTree) over the TOKEN
# stream, because the frozen contract's doc comments name the forbidden types in
# order to forbid them and a byte grep therefore fires on the prohibition itself.
# Repeated here only as a cross-check that skips comments the same way.
guard_no_float_in_harness() {
  local bad=0 f
  while IFS= read -r f; do
    # Drop // comments and /* */ comments, then look for a float identifier.
    if perl -0pe 's{//[^\n]*}{}g; s{/\*.*?\*/}{}gs' "$f" \
       | grep -Eq '\bfloat(32|64)\b|\bbig\.Float\b|\bcomplex(64|128)\b|\b(Parse|Format|Append)Float\b'; then
      warn "conformance: FLOATING-POINT IDENTIFIER in $f"
      bad=1
    fi
  done < <(find "$NEXUS_DIR/internal/apps/loanschedule" -name '*.go' -type f | sort)
  return "$bad"
}

# guard_gofmt: every file THIS HARNESS OWNS must be gofmt-clean.
#
# ONE FILE IS EXEMPT AND MUST STAY EXEMPT: the ratified DEC-1 artefact
# nexus/internal/apps/loanschedule/contract/contract.go.
#
# `gofmt -l` reports it. That is EXPECTED and recorded as gate G-3 in
# .softhouse/gates.md and .softhouse/reference-oracle.md: the diff is
# doc-comment list normalisation, it is semantically inert, and it is
# DELIBERATELY NOT APPLIED. Post-ratification, re-documenting any identifier in
# that package requires a gate — the doc comments ARE the specification, so a
# formatting rewrite of them is a rewrite of the spec. Every captured golden
# vector is expressed in those types.
#
# So this guard formats NOTHING (never `gofmt -w`, never `go fmt ./...`) and it
# checks only the files the harness introduced. If it checked contract.go it
# would either fail forever or tempt a later agent to "fix" a frozen artefact,
# and the second outcome is the dangerous one.
guard_gofmt() {
  local unformatted
  unformatted="$(gofmt -l "$HARNESS_PKG" "$NEXUS_DIR/internal/apps/loanschedule/conformance/cmd" 2>/dev/null \
                 | grep -v "/contract/contract.go$" || true)"
  if [ -n "$unformatted" ]; then
    warn "conformance: not gofmt-clean:"
    warn "$unformatted"
    return 1
  fi
  return 0
}

run_guards() {
  local failed=0
  guard_no_float_in_vectors || failed=1
  guard_no_float_in_harness || failed=1
  guard_gofmt               || failed=1
  if [ "$failed" -ne 0 ]; then
    warn "conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

# ---------------------------------------------------------------------------
# Reference-oracle probe
# ---------------------------------------------------------------------------
# Read-only, and it must stay read-only: do NOT restart, recreate or reconfigure
# the containers. Several captures' comparability rests on the running instance
# not having been restarted, and another task may be capturing against it in
# parallel. Self-signed TLS, hence -k, exactly as .softhouse/reference-oracle.md
# documents.
probe_oracle() {
  local body
  body="$(curl -sk --max-time 10 "$ORACLE_HEALTH_URL" 2>/dev/null || true)"
  case "$body" in
    *'"status":"UP"'*) printf 'up' ;;
    *)                 printf 'down' ;;
  esac
}

# ---------------------------------------------------------------------------
# Build and run
# ---------------------------------------------------------------------------
build_binary() {
  local out="$1"
  if ! ( cd "$NEXUS_DIR" && go build -o "$out" "$CMD_PKG" ) >&2; then
    warn "conformance: the harness does not build. EXIT 2. This is NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

main_grade() {
  local context="$1" self_test="$2"
  load_toolchain
  run_guards

  local probe rc
  CONF_BIN="$(mktemp -t conformance)" || exit "$EXIT_UNUSABLE"
  build_binary "$CONF_BIN"

  local args=()
  [ -n "$context" ] && args+=("-context=$context")

  if [ "$self_test" = "1" ]; then
    say "conformance: SELF-TEST MODE — grading the harness, not a port. Not a conformance PASS."
    "$CONF_BIN" -self-test "${args[@]+"${args[@]}"}"
    rc=$?
  else
    probe="$(probe_oracle)"
    say "conformance: reference oracle ($ORACLE_HEALTH_URL) probe = $probe"
    if [ "$probe" != "up" ]; then
      warn "conformance: the reference oracle is UNREACHABLE."
      warn "conformance: conformance reports EXIT 2, not a false PASS, and 2 never becomes 0."
    fi
    "$CONF_BIN" "-oracle-probe=$probe" "${args[@]+"${args[@]}"}"
    rc=$?
  fi
  return "$rc"
}

# ---------------------------------------------------------------------------
# --prove : the harness's own mutation proofs
# ---------------------------------------------------------------------------
# A harness whose author never demonstrated it can go RED is not finished. Each
# case states the exit code it demands and the run fails if the harness disagrees.
prove() {
  load_toolchain
  local rc pass=0 fail=0 bin tmp
  CONF_BIN="$(mktemp -t conformance)" || exit "$EXIT_UNUSABLE"
  CONF_TMP="$(mktemp -d -t conformance-prove)" || exit "$EXIT_UNUSABLE"
  bin="$CONF_BIN"; tmp="$CONF_TMP"
  build_binary "$bin"

  # expect_saying is expect plus a required substring of the output. The T20
  # structural rules all refuse for a REASON, and a proof that only checked the
  # exit code would pass if the vector were refused for some unrelated reason —
  # which is how a rule quietly stops being the rule that fires.
  expect_saying() { # expect_saying <wanted-code> <substring> <label> -- cmd...
    local want="$1" needle="$2" label="$3"; shift 4
    local out got ok
    out="$("$@" 2>&1)"; got=$?
    ok=0
    [ "$got" = "$want" ] && printf '%s' "$out" | grep -qF -- "$needle" && ok=1
    if [ "$ok" = 1 ]; then
      say "PROOF OK   exit $got (wanted $want)   $label"
      pass=$((pass+1))
    else
      say "PROOF FAIL exit $got (wanted $want)   $label"
      say "           the output had to contain: $needle"
      say "$out"
      fail=$((fail+1))
    fi
    say "--- last 6 lines of that run -------------------------------------------"
    printf '%s\n' "$out" | tail -6
    say ""
  }

  # assert_mutated refuses to run a proof whose perturbation did not apply. A
  # mutation proof over an unmutated file proves nothing and looks identical to
  # one that works.
  assert_mutated() { # assert_mutated <file> <needle>
    if ! grep -qF -- "$2" "$1"; then
      say "PROOF FAIL the perturbation did not apply to $1, so the proof would be vacuous"
      fail=$((fail+1))
      return 1
    fi
    return 0
  }

  expect() { # expect <wanted-code> <label> -- cmd...
    local want="$1" label="$2"; shift 3
    local got out
    out="$("$@" 2>&1)"; got=$?
    if [ "$got" = "$want" ]; then
      say "PROOF OK   exit $got (wanted $want)   $label"
      pass=$((pass+1))
    else
      say "PROOF FAIL exit $got (wanted $want)   $label"
      say "$out"
      fail=$((fail+1))
    fi
    say "--- last 6 lines of that run -------------------------------------------"
    printf '%s\n' "$out" | tail -6
    say ""
  }

  # 1. Nothing to grade, oracle claimed reachable: exit 2.
  #    Was "no implementation REGISTERED", which T10 negated by registering the
  #    port. The PROPERTY is unchanged and is what matters -- the harness refuses
  #    to grade when it has nothing to grade -- so it is now asserted by naming an
  #    implementation that does not exist, which does not depend on the store
  #    happening to be empty. Same defect class as D-6: a proof must assert a
  #    property, never a frozen fact about today's tree.
  expect 2 "no implementation named" -- \
    "$bin" -oracle-probe=up -impl=__none__

  # 2. Oracle unreachable: exit 2. Demonstrated by pointing the PROBE at a closed
  #    port and running this script for real, so the shell probe itself is what is
  #    proven. The live containers are NOT touched: several captures' comparability
  #    rests on that instance not having been restarted, and another task may be
  #    capturing against it in parallel.
  expect 2 "reference oracle unreachable (probe aimed at a closed port; live instance untouched)" -- \
    env CONFORMANCE_ORACLE_HEALTH_URL=https://127.0.0.1:1/health "${BASH_SOURCE[0]}"

  # 3. Self-test over the pristine store: exit 0, and the parity count stays 0.
  expect 0 "harness self-test over the pristine store" -- \
    "$bin" -self-test

  # 4. A CONSISTENT one-minor-unit perturbation of an expected value: exit 1.
  mkdir -p "$tmp/perturbed"
  cp -R "$STORE_ROOT/." "$tmp/perturbed/"
  perl -0pi -e 's/"principal_minor": "50000",\n(\s+)"interest_minor": "0",\n(\s+)"outstanding_principal_minor": "50000",\n(\s+)"principal_major_text": "500\.00",/"principal_minor": "50001",\n$1"interest_minor": "0",\n$2"outstanding_principal_minor": "50000",\n$3"principal_major_text": "500.01",/' \
    "$tmp/perturbed/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if ! grep -q '"50001"' "$tmp/perturbed/_selftest/SELFTEST-01-two-period-zero-rate.json"; then
    say "PROOF FAIL the perturbation did not apply, so the proof would be vacuous"
    fail=$((fail+1))
  else
    expect 1 "one-minor-unit perturbation of an expected value" -- \
      "$bin" -self-test "-store=$tmp/perturbed" "-replay-store=$STORE_ROOT"
  fi

  # 5. Only the integer perturbed, the oracle's wire text left alone: exit 2.
  #    Not a conformance failure — a TRANSCRIPTION error, which no other check
  #    in the harness could see.
  mkdir -p "$tmp/transcription"
  cp -R "$STORE_ROOT/." "$tmp/transcription/"
  perl -0pi -e 's/"principal_minor": "50000"/"principal_minor": "50001"/' \
    "$tmp/transcription/_selftest/SELFTEST-01-two-period-zero-rate.json"
  expect 2 "integer perturbed but the oracle wire text not (transcription error)" -- \
    "$bin" -self-test "-store=$tmp/transcription" "-replay-store=$STORE_ROOT"

  # 6. An empty vector store: exit 2, never a pass over zero work.
  mkdir -p "$tmp/empty"
  cp "$STORE_ROOT/PIN.json" "$STORE_ROOT/capabilities.json" "$tmp/empty/"
  expect 2 "empty vector store" -- \
    "$bin" -self-test "-store=$tmp/empty" "-replay-store=$STORE_ROOT"

  # 7. An absent vector store: exit 2.
  expect 2 "absent vector store" -- \
    "$bin" -self-test "-store=$tmp/does-not-exist" "-replay-store=$STORE_ROOT"

  # 8. The self-test fixture alone: it passes, and the run is STILL exit 2
  #    because a hand-authored fixture is not parity.
  expect 2 "self-test fixture excluded from the parity count" -- \
    "$bin" -oracle-probe=up -context=_selftest

  # 8b. The same fixture PASSING, and the parity count STILL zero. Exit codes alone
  #     cannot show this one, so the report text is asserted directly: the fixture
  #     is graded, it passes, and it buys no parity whatsoever.
  local out8 rc8
  out8="$("$bin" -self-test -context=_selftest 2>&1)"; rc8=$?
  if [ "$rc8" = 0 ] \
     && printf '%s' "$out8" | grep -q 'self-test fixtures      PASS 1' \
     && printf '%s' "$out8" | grep -q 'parity vectors          PASS 0' \
     && printf '%s' "$out8" | grep -q 'SELF-TEST FIXTURE' \
     && printf '%s' "$out8" | grep -q 'EXCLUDED from the parity count' \
     && printf '%s' "$out8" | grep -q 'NOT a conformance PASS'; then
    say "PROOF OK   exit $rc8               the fixture PASSES and parity stays 0, stamped NOT a conformance PASS"
    pass=$((pass+1))
  else
    say "PROOF FAIL exit $rc8               the fixture's pass/parity accounting is not as claimed"
    say "$out8"
    fail=$((fail+1))
  fi
  printf '%s\n' "$out8" | grep -E 'self-test fixtures|parity vectors|VERDICT'
  say ""

  # 9. A float token in a vector file: the HARD guard refuses. Run the guard
  #    against a doctored copy rather than the real store.
  mkdir -p "$tmp/floaty"
  cp -R "$STORE_ROOT/." "$tmp/floaty/"
  perl -0pi -e 's/"number_of_repayments": 2/"number_of_repayments": 2.0/' \
    "$tmp/floaty/_selftest/SELFTEST-01-two-period-zero-rate.json"
  expect 2 "float token in a vector file" -- \
    "$bin" -self-test "-store=$tmp/floaty" "-replay-store=$STORE_ROOT"

  # --- The T20 structural rules (T17 follow-ups F2, F5, F6 and driver finding
  #     D-4/D-5). Each one is demonstrated to REFUSE a doctored vector, with the
  #     refusal's own words asserted, and the D-5 case is demonstrated in the
  #     other direction: an unrecorded cell must NOT cost the vector.

  # 10. T17-F5: a money wire text with more fraction digits than the currency has
  #     minor units, NOT declared. Exact conversion or not, silence is refused —
  #     a rig that rounded it would grade the port against a number the oracle
  #     never produced.
  mkdir -p "$tmp/overscale"
  cp -R "$STORE_ROOT/." "$tmp/overscale/"
  perl -0pi -e 's/"principal_major_text": "1000\.00",/"principal_major_text": "1000.000",/' \
    "$tmp/overscale/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if assert_mutated "$tmp/overscale/_selftest/SELFTEST-01-two-period-zero-rate.json" '"1000.000"'; then
    expect_saying 2 "harness bug, not a rounding opportunity" \
      "T17-F5: an UNDECLARED over-scaled money wire text is inadmissible" -- \
      "$bin" -self-test "-store=$tmp/overscale" "-replay-store=$STORE_ROOT"
  fi

  # 11. T17-F6: a rate factor claiming to be exact. Every rate factor in the
  #     corpus is a 12-dp rounding, so a Go divergence in digits 13+ would pass
  #     silently against it; exact parity is TO_BE_CAPTURED and no vector may
  #     claim it.
  mkdir -p "$tmp/ratefactor"
  cp -R "$STORE_ROOT/." "$tmp/ratefactor/"
  perl -0pi -e 's/"unrecorded_fields": \[\],/"unrecorded_fields": [], "observed_rate_factor": { "text": "1.005833333333", "transcribed_at_scale": 12, "precision_status": "EXACT", "citation": "fabricated by the proof" },/' \
    "$tmp/ratefactor/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if assert_mutated "$tmp/ratefactor/_selftest/SELFTEST-01-two-period-zero-rate.json" '"precision_status": "EXACT"'; then
    expect_saying 2 "TO_BE_CAPTURED" \
      "T17-F6: a rate factor claiming exactness is inadmissible" -- \
      "$bin" -self-test "-store=$tmp/ratefactor" "-replay-store=$STORE_ROOT"
  fi

  # 12. T17-F2: a corroboration claiming a column the cross-check source does not
  #     print. The README's CI stdout block attests six of the ten period columns
  #     on a repayment row; total_outstanding_balance is not one of them.
  mkdir -p "$tmp/corroboration"
  cp -R "$STORE_ROOT/." "$tmp/corroboration/"
  perl -0pi -e 's/"kind": "hand-authored",/"kind": "hand-authored", "corroborated_by": [ { "source": "embeddable-readme-ci-stdout", "row_kind": "REPAYMENT", "columns": ["total_outstanding_balance"], "note": "fabricated by the proof" } ],/' \
    "$tmp/corroboration/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if assert_mutated "$tmp/corroboration/_selftest/SELFTEST-01-two-period-zero-rate.json" 'corroborated_by'; then
    expect_saying 2 "DOES NOT ATTEST" \
      "T17-F2: a corroboration claiming an unattested column is inadmissible" -- \
      "$bin" -self-test "-store=$tmp/corroboration" "-replay-store=$STORE_ROOT"
  fi

  # 13. D-4: a STRUCTURAL counterfactual naming a money column. The structural
  #     form exists for kills that move no money — a wrong due date, a wrong row
  #     order — and it must never become a way to avoid stating a real margin.
  mkdir -p "$tmp/structural"
  cp -R "$STORE_ROOT/." "$tmp/structural/"
  perl -0pi -e 's/"graded_against": \[\],/"graded_against": [ { "id": "MONEY-KILL-IN-A-STRUCTURAL-COAT", "kind": "structural", "capability": "schedule.core", "description": "fabricated by the proof", "margin_minor": "0", "divergent_cells": ["period[1].principal_minor"], "evidence": "observed 500.00; the wrong port emits 400.00 instead" } ],/' \
    "$tmp/structural/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if assert_mutated "$tmp/structural/_selftest/SELFTEST-01-two-period-zero-rate.json" 'MONEY-KILL-IN-A-STRUCTURAL-COAT'; then
    expect_saying 2 "money kill wearing a structural label" \
      "D-4: a structural counterfactual naming a money column is inadmissible" -- \
      "$bin" -self-test "-store=$tmp/structural" "-replay-store=$STORE_ROOT"
  fi

  # 14. D-5, in the OTHER direction: a money cell the capture never recorded must
  #     cost that CELL and nothing more. Before the fix the replay implementation
  #     dropped the whole vector and the run then reported "no vector carries this
  #     request" — absence of evidence dressed as evidence of absence. The proof
  #     therefore demands a GREEN run, and asserts the cell was counted as
  #     ungraded rather than quietly forgotten.
  mkdir -p "$tmp/unrecorded"
  cp -R "$STORE_ROOT/." "$tmp/unrecorded/"
  perl -0pi -e 's/"interest_minor": "0",\n(\s+)"outstanding_principal_minor": "100000",\n(\s+)"principal_major_text": "1000\.00",\n(\s+)"interest_major_text": "0\.00",\n(\s+)"outstanding_principal_major_text": "1000\.00",\n(\s+)"unrecorded_fields": \[\],/"interest_minor": "",\n$1"outstanding_principal_minor": "100000",\n$2"principal_major_text": "1000.00",\n$3"interest_major_text": "",\n$4"outstanding_principal_major_text": "1000.00",\n$5"unrecorded_fields": ["interest_minor"],/' \
    "$tmp/unrecorded/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if assert_mutated "$tmp/unrecorded/_selftest/SELFTEST-01-two-period-zero-rate.json" '"unrecorded_fields": ["interest_minor"]'; then
    # Scoped to the self-test context on purpose: the ungraded count is then
    # exactly the one cell this proof introduced, whatever the rest of the store
    # happens to contain today. A proof whose expected number moves when an
    # unrelated vector is promoted is a proof that will be deleted rather than
    # read.
    expect_saying 0 "1 ungraded" \
      "D-5: an unrecorded money cell costs the CELL, not the vector" -- \
      "$bin" -self-test "-store=$tmp/unrecorded" "-replay-store=$tmp/unrecorded" -context=_selftest
  fi


  # --- The T56 additions. Finding T9-F5: before these, ALL FIFTEEN proofs above
  #     perturbed one file — the hand-authored self-test fixture — so no proof
  #     touched a PARITY vector and no proof touched a DATE cell. The date-grading
  #     capability was real but only reading diffSchedule established it, and
  #     --prove is what a later agent runs INSTEAD of reasoning.

  # 15. T9-F5(a): a PARITY vector, money cell, perturbed CONSISTENTLY so the
  #     transcription cross-check cannot be what catches it. This is the review's
  #     mutation M2: P-03's last period, interest 12 -> 13 with the oracle's own
  #     wire text moved with it.
  mkdir -p "$tmp/parity-money"
  cp -R "$STORE_ROOT/." "$tmp/parity-money/"
  perl -0pi -e 's/"interest_minor": "12",/"interest_minor": "13",/; s/"interest_major_text": "0\.12",/"interest_major_text": "0.13",/' \
    "$tmp/parity-money/loanschedule/P-03-disbursement-on-repayment-due-date.json"
  if assert_mutated "$tmp/parity-money/loanschedule/P-03-disbursement-on-repayment-due-date.json" '"interest_minor": "13",'; then
    expect_saying 1 "row 6 interest_minor: expected 13 minor units, got 12" \
      "T9-F5: a one-minor-unit perturbation of a PARITY vector goes red" -- \
      "$bin" -self-test "-store=$tmp/parity-money" "-replay-store=$STORE_ROOT"
  fi

  # 16. T9-F5(b): a PARITY vector, DATE cell. The review's mutation M4, and the
  #     one the brief was rightly worried about: monthend.reanchor's counterfactual
  #     carries a margin_minor of exactly 0, so its whole kill lives in the date
  #     columns. If the harness could not go red here, that capability would be
  #     backed by nothing at all. P-02 period 2's due date is 2024-03-31 because
  #     the oracle RE-ANCHORS on the day-31 seed; the clamp-and-continue port the
  #     counterfactual names would emit 2024-03-29.
  mkdir -p "$tmp/parity-date"
  cp -R "$STORE_ROOT/." "$tmp/parity-date/"
  perl -0pi -e 's/"due_date": \{\n(\s+)"year": 2024,\n(\s+)"month": 3,\n(\s+)"day": 31/"due_date": {\n$1"year": 2024,\n$2"month": 3,\n$3"day": 29/' \
    "$tmp/parity-date/loanschedule/P-02-monthend-seed-day-31.json"
  if assert_mutated "$tmp/parity-date/loanschedule/P-02-monthend-seed-day-31.json" '"day": 29'; then
    expect_saying 1 "row 2 due_date: expected 2024-03-29, got 2024-03-31" \
      "T9-F5: a DATE cell of a PARITY vector goes red, naming the row and both dates" -- \
      "$bin" -self-test "-store=$tmp/parity-date" "-replay-store=$STORE_ROOT"
  fi

  # 17. T9-F1a: "marked unrecorded but carries a value" used to be enforced on the
  #     three money columns and nowhere else, so a DATE could be simultaneously
  #     populated and ungraded. Withdraw the disbursement row's due_date while
  #     leaving the observed 2024-01-31 sitting in the file. Nothing in the store
  #     names that cell as a divergent cell, so this isolates F-1a from F-1b.
  #     Before the fix this run exited 0.
  mkdir -p "$tmp/populated-unrecorded"
  cp -R "$STORE_ROOT/." "$tmp/populated-unrecorded/"
  perl -0pi -e 's/"installment_number",\n(\s+)"interest_minor"\n/"due_date",\n$1"installment_number",\n$1"interest_minor"\n/' \
    "$tmp/populated-unrecorded/loanschedule/P-02-monthend-seed-day-31.json"
  if assert_mutated "$tmp/populated-unrecorded/loanschedule/P-02-monthend-seed-day-31.json" '"due_date",'; then
    expect_saying 2 "is marked unrecorded but carries the date 2024-01-31" \
      "T9-F1a: a POPULATED non-money cell withdrawn from grading is inadmissible" -- \
      "$bin" -self-test "-store=$tmp/populated-unrecorded" "-replay-store=$STORE_ROOT"
  fi

  # 18. T9-F1b, the direction that must REFUSE. This is the review's exploit in
  #     miniature: take the cell MONTHEND-CONTINUE-FROM-CLAMPED-DAY names first,
  #     in both vectors that carry that kill, write garbage into it and withdraw
  #     it from grading. The full version — all nine cells, both files — produced
  #     "11/11 PASS, monthend.reanchor killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY,
  #     exit 0": a capability reported as killed by a counterfactual whose every
  #     named cell had been withdrawn.
  mkdir -p "$tmp/withdrawn-kill"
  cp -R "$STORE_ROOT/." "$tmp/withdrawn-kill/"
  perl -0pi -e 's/"due_date": \{\n(\s+)"year": 2024,\n(\s+)"month": 3,\n(\s+)"day": 31/"due_date": {\n$1"year": 1999,\n$2"month": 1,\n$3"day": 1/;
                s/"outstanding_principal_major_text": "67\.05",\n(\s+)"unrecorded_fields": \[\]/"outstanding_principal_major_text": "67.05",\n$1"unrecorded_fields": ["due_date"]/' \
    "$tmp/withdrawn-kill/loanschedule/P-02-monthend-seed-day-31.json"
  perl -0pi -e 's/"due_date": \{\n(\s+)"year": 2024,\n(\s+)"month": 3,\n(\s+)"day": 30/"due_date": {\n$1"year": 1999,\n$2"month": 1,\n$3"day": 1/;
                s/"outstanding_principal_major_text": "67\.05",\n(\s+)"unrecorded_fields": \[\]/"outstanding_principal_major_text": "67.05",\n$1"unrecorded_fields": ["due_date"]/' \
    "$tmp/withdrawn-kill/loanschedule/P-02b-monthend-seed-day-30.json"
  if assert_mutated "$tmp/withdrawn-kill/loanschedule/P-02-monthend-seed-day-31.json" '"unrecorded_fields": ["due_date"]' \
     && assert_mutated "$tmp/withdrawn-kill/loanschedule/P-02b-monthend-seed-day-30.json" '"unrecorded_fields": ["due_date"]'; then
    expect_saying 2 "WITHDRAWS from grading" \
      "T9-F1b: a structural kill naming a cell the vector withdrew is inadmissible" -- \
      "$bin" -self-test "-store=$tmp/withdrawn-kill" "-replay-store=$STORE_ROOT"
  fi

  # 19. T9-F1b, BOTH DIRECTIONS, asserted on the report text rather than the exit
  #     code — because the defect this closes was never visible in the exit code.
  #     Over the store from proof 18 the capability must be reported UNBACKED and
  #     the "killed by" line must be GONE; over the pristine store, where the same
  #     nine cells are recorded and graded, the same kill must still be credited.
  #     A rule that refused both would be a rule that had simply broken grading.
  local out19a rc19a out19b rc19b ok19
  out19a="$("$bin" -self-test "-store=$tmp/withdrawn-kill" "-replay-store=$STORE_ROOT" 2>&1)"; rc19a=$?
  out19b="$("$bin" -self-test 2>&1)"; rc19b=$?
  ok19=1
  [ "$rc19a" = 2 ] || ok19=0
  [ "$rc19b" = 0 ] || ok19=0
  # NOT "the capability becomes UNBACKED": that was only true while P-02/P-02b were
  # its ONLY backers. T58 promoted 16 more vectors, several of which legitimately
  # back monthend.reanchor, so the old assertion failed because COVERAGE WAS ADDED
  # (finding T58-N3, D-6's fourth recurrence -- in this very proof). Assert the
  # PROPERTY F-1b protects instead: the vector whose cells were withdrawn is
  # refused, by name, with the diagnostic that says why.
  printf '%s' "$out19a" | grep -q 'WITHDRAWS from grading' || ok19=0
  printf '%s' "$out19a" | grep -q 'P-02' || ok19=0
  # DELIBERATELY NOT asserted: that the store-wide "killed by
  # MONTHEND-CONTINUE-FROM-CLAMPED-DAY" line disappears. T58 promoted P-ME-* vectors
  # that carry the SAME counterfactual id and legitimately back it, so that line is
  # now printed by them and its presence says nothing about P-02. The store-wide
  # aggregate is the wrong place to assert a PER-VECTOR refusal; the two greps above
  # assert it where it actually lives, by vector name and with the diagnostic.
  printf '%s' "$out19b" | grep -q 'killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY' || ok19=0
  # NOT a frozen count: T57 moved the corpus 11 -> 13 and a literal here would go
  # stale on every promotion (finding D-6, third recurrence). Assert the PROPERTY --
  # the pristine store still grades clean with no failures.
  printf '%s' "$out19b" | grep -qE 'parity vectors +PASS [0-9]+ +FAIL 0' || ok19=0
  if [ "$ok19" = 1 ]; then
    say "PROOF OK   exit $rc19a/$rc19b       T9-F1b: withdrawn cells STOP backing the kill; recorded ones still back it"
    pass=$((pass+1))
  else
    say "PROOF FAIL exit $rc19a/$rc19b       T9-F1b coverage is not as claimed (want 2 then 0)"
    say "$out19a"
    say "$out19b"
    fail=$((fail+1))
  fi
  printf '%s\n' "$out19a" | grep -E 'UNBACKED|monthend.reanchor|VERDICT'
  printf '%s\n' "$out19b" | grep -E 'monthend.reanchor|parity vectors|VERDICT'
  say ""

  # 20. T60, closing finding T58-N2 — an unrecorded cell that a PROPERTY INVARIANT
  #     reads. Proof 14 covers the CELL DIFF's half of unrecorded_fields and that
  #     is the half that was never broken. The invariants' half is where the defect
  #     actually lived: diffSchedule honoured the withdrawal, all six invariants
  #     ignored it, and both read the SAME struct the replay had filled with
  #     stand-ins. The dangerous form is silent — withdraw the FINAL row's
  #     outstanding balance, the replay stands in 0, and 0 is precisely the value
  #     principal_amortizes_to_zero looks for, so the rig printed
  #     "principal_amortizes_to_zero  HOLD  final outstanding == 0" and exit 0 over
  #     a number NOBODY OBSERVED. A check quietly agreeing with a placeholder it was
  #     handed is worse than a red.
  #
  #     This class has now escaped twice (T58-N2 as a false red, T60 as the false
  #     green above). T60 added a Go package test; --prove is what the driver
  #     re-runs INSTEAD of reasoning, so the property is asserted here too.
  #
  #     The withdrawal is made through the store's OWN mechanism and not a side
  #     channel: value emptied, major text emptied, the field named in
  #     unrecorded_fields — exactly the three things admit.go demands of an honest
  #     withdrawal (admit.go:722-818). outstanding_principal_minor on a REPAYMENT
  #     row is deliberately NOT contract-fixed at 0 (registry.go
  #     contractFixesCellAtZero), so the replay's 0 is a placeholder, not an answer.
  #
  #     THE TWO WRONG ANSWERS FAIL THIS PROOF FOR DIFFERENT, NAMED REASONS:
  #       * FALSE HOLD — the pre-T60 rig. Mutation: registry.go stops declaring
  #         placeholders (drop the placeholders.Add call, or return a nil
  #         PlaceholderCells). The invariant then grades the stand-in, agrees with
  #         it, and reports HOLD. Caught by the "[N/A]", "NOT ASSERTED" and
  #         "NOT RUN" checks below, NOT by the exit code — the exit code stays 0,
  #         which is the whole reason this proof exists.
  #       * FALSE VIOLATION — the T58-N2 symptom. Mutation: invariants.go returns
  #         InvariantViolated instead of InvariantNoData on the placeholder branch
  #         of invPrincipalAmortizes. Caught by the exit-code check and by the
  #         "reported VIOLATED" check.
  #
  #     NO LITERAL VECTOR COUNT IS ASSERTED (pattern P-7; a frozen count is what
  #     went stale in proofs 8b and 19, finding D-6). The mutated run is scoped to
  #     _selftest so it speaks only about the one cell this proof withdrew, and
  #     every positive assertion is either per-vector or a ">= 1" regex. The
  #     control run at the end is the anti-no-op guard: over the PRISTINE store
  #     the same invariant must still be asserted and still hold, or "not asserted"
  #     has simply become a way to switch a check off. It asserts hold >= 1 and
  #     violated 0 — a property, which grows with the corpus instead of going stale.
  local out20 rc20 out20c rc20c ok20 why20
  mkdir -p "$tmp/unrecorded-invariant"
  cp -R "$STORE_ROOT/." "$tmp/unrecorded-invariant/"
  perl -0pi -e 's/"outstanding_principal_minor": "0",\n(\s+)"principal_major_text": "500\.00",\n(\s+)"interest_major_text": "0\.00",\n(\s+)"outstanding_principal_major_text": "0\.00",\n(\s+)"unrecorded_fields": \[\],/"outstanding_principal_minor": "",\n$1"principal_major_text": "500.00",\n$2"interest_major_text": "0.00",\n$3"outstanding_principal_major_text": "",\n$4"unrecorded_fields": ["outstanding_principal_minor"],/' \
    "$tmp/unrecorded-invariant/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if assert_mutated "$tmp/unrecorded-invariant/_selftest/SELFTEST-01-two-period-zero-rate.json" \
       '"unrecorded_fields": ["outstanding_principal_minor"]'; then
    out20="$("$bin" -self-test "-store=$tmp/unrecorded-invariant" \
             "-replay-store=$tmp/unrecorded-invariant" -context=_selftest 2>&1)"; rc20=$?
    out20c="$("$bin" -self-test 2>&1)"; rc20c=$?
    ok20=1; why20=""
    note20() { ok20=0; why20="${why20}
           * $1"; }

    # --- the FALSE VIOLATION direction ---
    [ "$rc20" = 0 ] || note20 \
      "FALSE VIOLATION: the run exited $rc20, wanted 0. An invariant went RED on a cell nobody observed."
    if printf '%s' "$out20" | grep -qF -- 'INVARIANT principal_amortizes_to_zero VIOLATED'; then
      note20 "FALSE VIOLATION: principal_amortizes_to_zero was reported VIOLATED against a stand-in."
    fi

    # --- the FALSE HOLD direction. Per-vector, so no corpus count is involved:
    #     an invariant has exactly ONE status per vector, and asserting it is N/A
    #     on this vector excludes HOLD on this vector. ---
    printf '%s' "$out20" \
      | grep -qE 'SELFTEST-01-two-period-zero-rate .* principal_amortizes_to_zero \[N/A\]' || note20 \
      "FALSE HOLD: principal_amortizes_to_zero did not report N/A for the vector whose final outstanding was withdrawn."
    printf '%s' "$out20" | grep -qF -- \
      'NOT ASSERTED: row 2: final outstanding == 0 cannot be asserted (outstanding_principal_minor never recorded by the capture' \
      || note20 "no NOT ASSERTED line names the withdrawn cell, so a reader cannot tell the check stopped checking."
    printf '%s' "$out20" | grep -qE 'invariant assertions +[1-9][0-9]* NOT RUN' || note20 \
      "the summary counted ZERO skipped assertions while a cell the invariants read was a placeholder."

    # --- the anti-no-op control, over the PRISTINE store ---
    [ "$rc20c" = 0 ] || note20 "control: the pristine store no longer self-tests clean (exit $rc20c, wanted 0)."
    printf '%s' "$out20c" | grep -qE 'principal_amortizes_to_zero +hold [1-9][0-9]* +violated 0' || note20 \
      "control: principal_amortizes_to_zero is no longer ASSERTED over the pristine store — the fix has become a no-op."

    if [ "$ok20" = 1 ]; then
      say "PROOF OK   exit $rc20/$rc20c       T58-N2/T60: a withdrawn cell an invariant reads is NOT RUN, not a HOLD and not a VIOLATION"
      pass=$((pass+1))
    else
      say "PROOF FAIL exit $rc20/$rc20c       T58-N2/T60: the unrecorded-cell path is not graded as claimed:$why20"
      say "$out20"
      say "$out20c"
      fail=$((fail+1))
    fi
    printf '%s\n' "$out20" | grep -E 'principal_amortizes_to_zero|NOT ASSERTED|invariant assertions|VERDICT'
    printf '%s\n' "$out20c" | grep -E 'principal_amortizes_to_zero|invariant assertions|VERDICT'
    say ""
  fi

  say "======================================================================="
  say "PROOFS: $pass passed, $fail failed"
  say "======================================================================="
  [ "$fail" -eq 0 ] || return 1
  return 0
}

# ---------------------------------------------------------------------------
case "${1:-}" in
  # `exit $?`, not `exit 0`: if usage() cannot find the sentinel that bounds its own
  # text it returns 1, and --help must not report success over output it could not
  # produce. (P-22 — a check that cannot fail is worse than no check.)
  --help|-h)   usage; exit $? ;;
  --prove)     prove; exit $? ;;
  --self-test) main_grade "${2:-}" 1; exit $? ;;
  --*)         warn "conformance: unknown option $1"; usage; exit "$EXIT_UNUSABLE" ;;
  *)           main_grade "${1:-}" 0; exit $? ;;
esac
