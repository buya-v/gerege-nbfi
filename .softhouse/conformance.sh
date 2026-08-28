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
#      bash), `sh conformance.sh` is ADMITTED [VERIFIED: T97 — bash 5.2.37 and
#      5.3.9, argv[0]=sh; T113 re-measured on 5.3.9, argv[0]=sh, `--posix`,
#      argv[0]=sh + `--posix` and POSIXLY_CORRECT=1, all admitted]. Whether the
#      graded run then SUCCEEDS under a bash 5.x is [UNVERIFIED]: no complete
#      graded run under bash 5.x has ever been recorded — every green run on
#      record is macOS bash 3.2.57. ADMISSION is a claim about this guard only,
#      not about the 800 lines after it.
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
# and **exit 2** — and 2 is this harness's "unusable" code, which at the time was
# also, on its own, the /softhouse-program driver's oracle-is-down stop condition.
# So a one-word shell-selection typo was indistinguishable from a genuine oracle
# outage and could park every vector task in the program under a reason that was
# not true.
#
#   EXIT 2 IS FORMALLY AMBIGUOUS TODAY, AND THE DRIVER NO LONGER READS IT ALONE.
#   2 means "the ORACLE is unusable" OR "the CORPUS is unusable" — zero vectors,
#   an inadmissible vector, a refused vector, a failed HARD guard, and since T110
#   a duplicate `case_id`, which REFUSES the run at 2. A refusal read as an outage
#   is the same defect one level up, so the driver's park condition is now BOTH
#   `exit 2` AND `probe != up`, taken from the `reference oracle (…) probe = up|down`
#   line this harness prints unconditionally before the graded binary runs (see
#   `probe_oracle` below). Exit 2 with `probe = up` is a corpus defect to be FIXED
#   in the same fire, never a reason to park [.claude/skills/softhouse-program/
#   SKILL.md, the exit-code table]. Exit 3 stays outside all of this: it says
#   nothing about either the corpus or the oracle, because neither was reached.
#
# Under
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
#       shell's name. On Fedora/RHEL, where /bin/sh IS bash 5.x, `sh` is ADMITTED
#       [VERIFIED: T97 matrix — 5.2.37 and 5.3.9, plain, `--posix`, argv[0]=sh,
#       and argv[0]=sh + `--posix`: eight of eight ADMITTED; T113 re-ran the same
#       four shapes on 5.3.9]. That it then WORKS end to end is [UNVERIFIED] —
#       admission is measured, a complete graded run under bash 5.x is not.
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
#   compares equal to what was expected.
#
#   AND THE VARIABLE IS CLEARED FIRST — `_conformance_psub_line=`, on its own
#   line inside the eval, before the read. That line is not tidiness. Without it
#   the token is FORGEABLE, and this comment used to claim the opposite: that the
#   token "can reach the comparison by exactly one route — the construct working
#   — so every way of not running the probe yields an empty observation and FAILS
#   CLOSED". That sentence was FALSE (T106 refuted it while approving the rest).
#   It omitted the family "the redirection is attempted and FAILS AT RUN TIME",
#   as opposed to failing to parse. When `< <(…)` cannot be OPENED — a real bash
#   5.3.9 with /dev/fd removed does exactly this: `cat < <(printf x)` →
#   `/dev/fd/63: No such file or directory` — the eval string still PARSES,
#   `builtin read` runs and never assigns, and the next statement prints whatever
#   `$_conformance_psub_line` already held. It was the one probe variable never
#   initialised, so an INHERITED `_conformance_psub_line=conformance-psub-live`
#   made a psub-dead shell admit itself.
#   [VERIFIED: T106 found it; T113 reproduced it on real bash 5.3.9 with /dev/fd
#   removed against the UNMODIFIED pre-fix harness — clean env → exit 3 REFUSED,
#   `_conformance_psub_line=conformance-psub-live` exported → exit 0 ADMITTED;
#   with the assignment, exit 3 both ways. Rigs and transcripts:
#   .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T113-evidence/ .]
#   And the consequence was not cosmetic: a wrongly admitted run on a psub-dead
#   shell reaches the HARD guards below, whose `while read … done < <(find …)`
#   loops would then return 0 having inspected ZERO files — a guard certifying
#   "no floats" without opening a file. That is the P-22 failure mode ("a guard
#   that cannot fail is worse than none, because it is believed"), and it is what
#   makes THIS one different from the residual hijacks: a hijack refuses, and a
#   refusal cannot turn a red run green; a forged admission can.
#   [CORRECTED BY T154, and the correction NARROWS this paragraph rather than
#   retiring it. "Would then return 0 having inspected ZERO files" was true when
#   it was written and is now FALSE: both guards count what they inspected and
#   return 1 with a named error at zero, and the Go census in nofloat.go /
#   census.go does the same on its own two surfaces. So the psub-dead route no
#   longer reaches a vacuous float guard. Everything else here stands — the
#   interpreter guard is still the difference between a refusal and a forged
#   admission, and a forged admission still reaches the rest of this file.]
#   [CITATION CORRECTED BY T113: T106's review, and the first draft of this
#   paragraph, both said "the vacuous pass that line 53 of this file already warns
#   about". It does not. The block that line number pointed at is `WHY IT EXISTS`
#   above — named rather than numbered here, because the number is what drifted —
#   and it says the psub in `guard_no_float_in_vectors` DIED under `sh` and was
#   mistaken for an oracle outage. It says nothing about a guard returning 0 over
#   an EMPTY file set, which is the opposite failure and the one F1 enables. The
#   only P-22 sentence in this file before T113 was the `--help` comment far
#   below. A citation nobody re-opens is a claim, not a fact (P-16).]
#
#   WHAT THE ASSIGNMENT DOES, AND WHAT IT DOES NOT. It makes the observation
#   start from EMPTY, so the token can reach the comparison only by the read
#   actually succeeding. That closes the whole "the probe did not run, or ran and
#   failed" family — syntax error, refused redirection, failed open(), killed
#   subshell, a shell that never reached the line. It is a plain ASSIGNMENT, not
#   a command word, so no exported shell function can shadow it; that is why the
#   fix is `_conformance_psub_line=` and not `unset -v _conformance_psub_line`,
#   which would have been one more hijackable command word. It does NOT defend
#   against a hostile environment in general — see the next paragraph — and it
#   has one exotic cost, recorded rather than hidden: if this file is SOURCED
#   into a shell that has already made `_conformance_psub_line` READONLY, the
#   assignment fails, the subshell dies, and a healthy bash is REFUSED. Pre-fix
#   that same setup was ADMITTED, by forgery rather than by evidence.
#   [VERIFIED: T113 measured both, bash 3.2.57 and 5.3.9.] The trade is
#   deliberate and one-directional: a fail-closed refusal cannot turn a red run
#   green; a forged admission can.
#
#   Detail that matters, and the exact rock T86's own first draft split on:
#   `printf '%s\n'`, WITH the newline. A `while read -r x; do …; done < <(printf
#   %s value)` reads a final line that has no terminator, `read` returns non-zero,
#   the loop body never runs, and plain, healthy bash is REFUSED. This probe uses
#   a single `read` and grades the VARIABLE, not `read`'s status, so it is immune
#   to that either way — but the newline is there so nothing downstream inherits
#   the trap. `IFS=` is there so that no IFS in force when this file starts can
#   reach the `read` at all.
#
#   FIRST, BY WHAT ROUTE COULD ONE BE IN FORCE? Not the one every matrix in this
#   chain used. **bash resets IFS to the default ` \t\n` at startup and IGNORES an
#   inherited one**, so `env IFS=z bash conformance.sh` delivers nothing — the
#   child's `$IFS` is the 3-character default before line 1 runs, in plain mode,
#   under `--posix`, under `argv[0]=sh` and under `POSIXLY_CORRECT=1` alike. Every
#   `IFS=…` row T97, T106, T113 and T121 ran through the environment is therefore a
#   NULL CONTROL: it could not have failed, whatever the token was. Two routes DO
#   deliver: a **`BASH_ENV` startup file that assigns IFS** (bash sources it before
#   a non-interactive script), and this file being **SOURCED** into a shell that
#   has already set IFS. [VERIFIED: T130 enumerated all seven routes on bash
#   3.2.57, 4.4.0 and 5.3.9 — env / env+--posix / env+argv[0]=sh / env+POSIXLY_CORRECT
#   deliver the default on all three; BASH_ENV and sourcing deliver `IFS=z` on all
#   three.] So the threat is real and reachable — it is just not the one that was
#   being measured.
#   [SUPERSEDES: T97 "`IFS=oc`, `IFS=' '`, `IFS=$'\n'` in the environment, all
#   ADMITTED" and T113's re-measurement of the same four. Both readings are still
#   true as ADMISSIONS; neither is evidence about IFS.]
#   BUT THE PREFIX IS BELT-AND-BRACES FOR TODAY'S TOKEN, NOT A MEASURED SAVE —
#   and this file has now carried TWO different wrong reasons for that. T106 wrote
#   that `IFS=e` "would have been a false refusal without the prefix, so the prefix
#   earns its place", reasoning that the token `conformance-psub-live` contains an
#   `e`. T113 deleted the prefix, measured, and correctly withdrew that — then put
#   a SECOND false rule in its place: that `read` with a single variable "strips
#   only leading/trailing IFS *whitespace*, so a non-whitespace delimiter — even
#   as the token's first or last character — changes nothing". IT DOES NOT.
#   Counterexample, identical on three bash majors: `IFS=z`, line `abcz` → `abc`.
#
#   THE MEASURED RULE. `read -r` with a SINGLE variable assigns the whole line,
#   stripping leading and trailing IFS *whitespace* — AND ALSO stripping the final
#   character when that character is a NON-whitespace IFS delimiter AND that is the
#   ONLY position in the whole line holding ANY IFS delimiter. One further
#   delimiter occurrence anywhere — same character or a different IFS character —
#   and nothing is stripped: `abczz`, `zabcz` and `abzcz` all survive `IFS=z`, and
#   `abcze` survives `IFS=ze` while `abcz` does not.
#   [VERIFIED: T130 brute-forced that predicate against `read` itself over every
#   string of length 1..6 on {a,b} × IFS ∈ {a,b,ab} and every string of length 1..5
#   on {a,b,c} × IFS ∈ {a,b,c,ab,bc,abc,:,a:} — 3,282 cases, 0 disagreements, on
#   bash 3.2.57, 4.4.0 and 5.3.9 alike.]
#
#   WHY TODAY'S TOKEN SURVIVES, AND WHY THAT IS NOT A LICENCE TO RELAX.
#   `conformance-psub-live` ends in `e`, and `e` also occurs in `conformance`, so
#   the "sole delimiter, in final position" shape is unreachable for it under ANY
#   IFS at all — any IFS containing `e` finds two of them, and any IFS not
#   containing `e` does not touch the last character. THAT IS AN ACCIDENT OF HOW
#   THE TOKEN IS SPELLED, NOT A PROPERTY OF THE PROBE. Rename it
#   `conformance-psub-livz` — or anything whose last character does not occur
#   earlier in it — and `IFS=z` truncates the observation to `conformance-psub-liv`
#   and the comparison below fails. With the prefix in place that is harmless;
#   with the prefix deleted, over a route that delivers IFS, it REFUSES a perfectly
#   healthy bash at exit 3 [VERIFIED: T130, 3.2.57 / 4.4.0 / 5.3.9 — the table
#   below].
#   So the list of futures the prefix insures against has THREE entries, and the
#   third is the likeliest thing an editor actually does: someone later READS TWO
#   VARIABLES; someone PUTS WHITESPACE IN THE TOKEN; someone RENAMES THE TOKEN.
#
#   THE WHOLE THING, MEASURED RATHER THAN ARGUED — 2 token spellings x prefix
#   kept/dropped x 3 IFS routes, 12 cells, identical on bash 3.2.57, 4.4.0 and
#   5.3.9 [VERIFIED: T130]. ELEVEN cells ADMIT. Exactly one refuses:
#
#       token=conformance-psub-livz  prefix=DROPPED  route=BASH_ENV  -> exit 3
#
#   i.e. a false refusal of a perfectly healthy bash needs ALL THREE of a renamed
#   token, a deleted prefix, and a route that actually delivers IFS. Today's token
#   is immune on every route with or without the prefix — no IFS string mangles
#   `conformance-psub-live`, because its last character `e` is never a lone
#   delimiter. So the prefix is STILL not a measured save today, and it stops being
#   merely stylistic the moment anyone renames the token.
#
#   AND THE TOKEN INVARIANT IS ASSERTED, NOT NARRATED. Because that immunity is a
#   property of the spelling, it is checked by a test instead of promised by this
#   comment: section [6b] of .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/
#   T113-evidence/interpreter-matrix.sh reads CONFORMANCE_PSUB_TOKEN out of THIS
#   file and requires (i) that it contain no whitespace and (ii) that its last
#   character occur earlier in it — which together imply it round-trips through a
#   single-variable `read` under EVERY IFS — then re-measures that against `read`
#   itself for each character of the token's own alphabet, and end to end through a
#   prefix-DELETED copy of the harness over the BASH_ENV route.
#   [VERIFIED: T130 drove all three legs red by renaming the token to
#   `conformance-psub-livz` — the pre-T130 matrix reported 26 passed / 0 failed and
#   exit 0 on that same renamed harness, i.e. it silently admitted it — and green
#   again on restore.] The prefix still stays: it costs nothing, and it is what
#   makes such a rename merely a red row rather than a broken guard. It is
#   documented as insurance, because a guard credited with a save it never made is
#   the P-22 failure in miniature. And note this is a NORMALISATION, not a defence:
#   `IFS` is not a command word, but nothing here stops a hostile environment
#   either — see below.
#
#   Meanwhile `builtin` pins `eval`/`read`/`printf` to bash's own, so an exported function
#   of one of those names cannot quietly take their place. `builtin eval` is not
#   decoration: with a bare `eval`, an exported `eval()` function made bash
#   5.2.37 refuse the harness, and that WOULD have been a false refusal
#   [VERIFIED: T97 hostile-environment matrix, both readings; T113 re-measured on
#   5.3.9 — with `builtin eval`, both `eval() { return 1; }` and `eval() { echo
#   conformance-psub-live; }` leave a healthy bash ADMITTED and a psub-dead bash
#   REFUSED, i.e. the shield holds in both directions].
#
#   WHAT THIS GUARD DEFENDS AGAINST, AND WHAT IT DOES NOT. It defends against a
#   WRONG INVOCATION — this file handed to a shell that cannot run it. It does
#   NOT defend against a HOSTILE ENVIRONMENT, it cannot be made to, and the
#   sentence that used to sit here claimed otherwise on two counts, both false
#   (T106 refuted them; T113 re-measured every row):
#     * `builtin` was named as the one remaining hijackable name. It is not the
#       one. `[` is a command word too, and it is the FIRST command the guard
#       runs. An exported `[() { return 1; }` makes every test in the guard read
#       false, so the guard is SKIPPED and a psub-dead bash 5.3.9 is ADMITTED
#       [VERIFIED: T113]; `[() { return 0; }` makes them all read true and a
#       HEALTHY bash is REFUSED with text saying "BASH_VERSION is unset" when it
#       is not [VERIFIED: T113, 3.2.57 and 5.3.9].
#     * the residual hijack was called fail-CLOSED. It is not. `builtin() {
#       return 1; }` does refuse — that is the one body T97 tried — but
#       `builtin() { echo conformance-psub-live; }` FORGES the token outright and
#       a psub-dead bash 5.3.9 is ADMITTED [VERIFIED: T113]. Fail-closed was a
#       property of one function body, never of the family.
#   No fixed point exists. Function lookup precedes builtin lookup for every
#   command word, and `builtin` and `command` are themselves command words;
#   quoting does not help, because a backslash suppresses ALIAS expansion, not
#   function lookup. [VERIFIED: T113 — `builtin() { echo HIJACKED; }; builtin
#   echo hi` and `\builtin echo hi` both print HIJACKED, and the same holds for
#   `command`; bash 3.2.57.] `builtin` is kept anyway, because it removes the
#   accidental collisions a normal environment can produce — someone's exported
#   `eval`, `read` or `printf` helper — at zero cost. It is not a security
#   boundary and must not be read as one: anyone who can export a function into
#   this process can also edit this file.
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
      _conformance_psub_line=
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
# `_conformance_psub_line` is in this list even though the probe assigns it only
# inside a command substitution, i.e. in a subshell, so the parent normally never
# has it. It is here for the one case where the parent DOES: the caller exported
# it — which is exactly the forge above. Leaving an attacker-supplied name in the
# environment of the 700 lines below it is not a defect anyone has demonstrated,
# and it is not a defence either (`unset` is a command word and can be shadowed
# like any other; see the hijack paragraph above). It is hygiene, and it is
# written down as hygiene rather than dressed up as a control. (T106's companion
# recommendation to F1, applied by T113.)
unset conformance_shell_why conformance_psub_seen CONFORMANCE_PSUB_TOKEN _conformance_psub_line

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

# ---------------------------------------------------------------------------
# THE EXEMPTION CENSUS PIN  [T233, from T222's F-1 and T230's F-1]
# ---------------------------------------------------------------------------
# An `invariant_exemptions` entry switches a property invariant OFF for one vector.
# The Go report has counted them since T220-N1 and split them GROUNDED /
# UNDETERMINED-ON-THE-RECORD / UNGROUNDED since T230. NOTHING GATED EITHER NUMBER.
# The Go binary exits 0 whenever every declared exemption is admissible, and
# "admissible" says nothing about HOW MANY there are — so the corpus could drift in
# EITHER DIRECTION without a single number moving in anything that decides a
# verdict:
#
#   INFLATION  — a fifth exemption arrives, is individually grounded, and the
#                exempted count that this program quotes as evidence about how much
#                of the corpus is CHECKED silently rises. That is finding T220-N1's
#                actual complaint, one level up from the shape T222 closed.
#   DEFLATION  — an exemption (or the vector carrying it) is deleted and the count
#                silently FALLS. Nothing notices, because both of the harness's
#                enumerators walk WHAT IS THERE and therefore agree about what is
#                not. This is the T160 shape exactly; see the census discussion in
#                that task and in T233's handoff.
#
# THE PIN IS AN EQUALITY, NOT A FLOOR AND NOT A CAP, because only an equality
# closes both directions. The corpus is allowed to grow and shrink — it just has to
# do so in a commit that also edits this file, where a reviewer sees the two
# together. That is the whole mechanism: an EXPECTED value, committed APART from
# the thing it describes, compared for EQUALITY, fail-closed when the figure it
# needs is absent.
#
# WHY IT LIVES HERE AND NOT IN THE STORE. `.softhouse/vectors/PIN.json` is the
# natural home for a pin ABOUT THE VECTORS, and T160 proposes it for the store
# manifest. It is the wrong home for THIS pin for two reasons. (1) These figures
# are not properties of the vector FILES: GROUNDED / UNDETERMINED is a classification
# the HARNESS computes, and the classification itself changes when the harness does
# — T230 introduced UNDETERMINED-ON-THE-RECORD, which would have forced a
# vector-tree edit for a pure harness change. (2) PIN.json is inside
# `.softhouse/vectors/`, so a pin about the exemption corpus and the exemption
# corpus would live in one tree; the point of an expected value is that it is
# committed somewhere the thing it describes cannot take it down with it.
#
# WHY IT IS NOT A CAP INSIDE THE GO BINARY. exemption.go's doctrine block settles
# that: a hard cap in the binary refuses legitimate corpus growth at RUN time, for
# everybody, including the promoter who is deliberately adding one. A pin in the
# harness script refuses only the run that did not also update the pin.
#
# P-45: this is read by `gate_exemption_census`, which `main_grade` calls on the
# path `bash .softhouse/conformance.sh` actually executes — NOT from `go test`,
# which conformance.sh never invokes.
EXEMPTION_PIN_EXEMPTED=4
EXEMPTION_PIN_DECLARED=4
EXEMPTION_PIN_GROUNDED=4
EXEMPTION_PIN_UNDETERMINED=0
EXEMPTION_PIN_UNGROUNDED=0

# ---------------------------------------------------------------------------
# THE LEDGER EXEMPTION PIN  [A2-15]
# ---------------------------------------------------------------------------
# The five figures above are properties of the LOANSCHEDULE corpus, and they are
# unchanged by A2-15's promotion. That is a MEASUREMENT and not an assumption, and
# it is worth stating plainly because the dispatch predicted the opposite:
# promoting a vector was expected to move them. It did not, and each figure is
# argued rather than left to speak for itself:
#
#   EXEMPTED     = 4 -- the four exempted ASSERTIONS both belong to the two G-8
#                       family-B loanschedule vectors T116 promoted. A2-15 added
#                       no loanschedule vector at all, so this population could
#                       not move.
#   DECLARED     = 4 -- the same four, counted as DECLARATIONS in the loaded
#                       files. Two vectors x two invariants.
#   GROUNDED     = 4 -- all four are GROUNDED: the recorded schedule genuinely
#                       violates the exempted invariant in both files.
#   UNDETERMINED = 0 -- and this is the figure the dispatch expected to move,
#                       because T230 reworked the grounding rule so that an
#                       exemption paired with an `unrecorded_fields` entry is
#                       reported UNDETERMINED-ON-THE-RECORD instead of refused.
#                       A2-15 CONFIRMED THAT T230'S SHAPE DOES NOT FIT ITS NEED,
#                       which T230 itself had flagged [UNVERIFIED] on its side.
#                       A2-15's exclusion is of a CELL (`gl_account_type`), not of
#                       an INVARIANT, and neither of the two gradeable ledger
#                       invariants (I-1 debits==credits, I-2 splits sum to whole)
#                       reads a GL account's classification. So there is nothing
#                       for an exemption to switch off and no exemption is
#                       declared. T230's rework is correct and is simply not on
#                       A2-15's path. The full argument is in A2-15's handoff.
#   UNGROUNDED   = 0 -- no exemption in the store is refuted by its own record.
#
# WHAT IS NEW IS THE SIXTH FIGURE, and it closes for the ledger corpus exactly the
# hole T233 closed for the loanschedule one. The ledger schema REFUSES an
# `invariant_exemptions` entry outright (it has no grounding classifier, so
# admitting one would switch an invariant off with nothing checking that the thing
# it excuses is visible in the record). "Refuses" is a property of the code; the
# POPULATION is a property of the corpus, and an uncounted population drifts in
# both directions with nothing noticing -- which is T220-N1 and T160 in one
# sentence. So the ledger report COUNTS its declared exemptions on every run, and
# this pin compares that count for EQUALITY.
#
#   LEDGER_DECLARED = 0 -- the six promoted ledger vectors declare zero
#                          exemptions between them. Argued, not defaulted: an
#                          exemption here would be inadmissible, so a corpus with
#                          one would already be exit 2 -- but a corpus that LOST
#                          the refusal and gained an exemption would move this
#                          number, and a corpus whose ledger vectors were all
#                          deleted would leave it at 0 while the population
#                          vanished, which is why the ledger PARITY figures are
#                          pinned below it.
EXEMPTION_PIN_LEDGER_DECLARED=0

# ---------------------------------------------------------------------------
# THE LEDGER CORPUS PIN  [A2-15]
# ---------------------------------------------------------------------------
# DEFLATION IS THE HALF NOBODY NOTICES (the T160 shape, and the reason every pin
# in this file is an EQUALITY rather than a floor). A pin on the exemption count
# alone would sit happily at 0 over a store from which every ledger vector had
# been deleted -- the report would print the "NO LEDGER VECTOR IS IN THIS STORE"
# banner, the loanschedule half would still be green, and the verdict would still
# be PASS. So the ledger POPULATION is pinned too.
#
#   LEDGER_PARITY   = 4 -- LDG-01 (manual, 3 legs), LDG-02 (accounting path,
#                          4 legs), LDG-03 (accounting path, 4 legs, overpayment),
#                          LDG-04 (header account accepted, 2 legs).
#   LEDGER_REFUSAL  = 2 -- LDG-REFUSE-01 (unbalanced by one minor unit) and
#                          LDG-REFUSE-02 (manual adjustments not permitted), and
#                          LDG-REFUSE-03 (defining opening balances after journal
#                          entries have been posted) [T294: 2 -> 3], and
#                          LDG-REFUSE-04 (entry dated ON the latest closing date
#                          -- the INCLUSIVE boundary at :636, which the oracle's
#                          own "prior to" message contradicts) and LDG-REFUSE-05
#                          (entry dated one day after the business date, :629)
#                          [T295: 3 -> 5]. Both are PROMOTIONS OF T287's BYTES
#                          under T289's rule, with the business date and the
#                          closing date lifted out of prose and into the vector's
#                          inputs. NEITHER PROBE WAS RE-FIRED and neither may be:
#                          both bodies are valid, balanced, postable journal
#                          entries whose only defect is an ORACLE-SIDE
#                          precondition, and both preconditions have lapsed or
#                          lapse imminently -- guard-probe-expiry.sh in the rig
#                          exits 1 today.
#   LEDGER_MONEYCELLS = 21 -- the count of MONEY cells compared in int64 minor
#                          units. It is pinned SEPARATELY from the cell total
#                          because DEC-2 §5.5 warns that "a ledger corpus whose
#                          money cells only ever kill structurally has graded no
#                          amount": a corpus that quietly stopped comparing money
#                          would keep its vector counts and lose this one.
#                          Derivation: LDG-01 5 (3 legs + 2 totals), LDG-02 6
#                          (4 + 2), LDG-03 6 (4 + 2), LDG-04 4 (2 + 2), and 0 on
#                          each refusal vector, which asserts no amount at all.
#                          5 + 6 + 6 + 4 = 21.
#                          T294 ADDED A REFUSAL VECTOR AND THIS FIGURE DID NOT
#                          MOVE, deliberately and not by oversight. A refusal
#                          vector asserts no amount: diffRefusal compares three
#                          cells through cmpInt/cmpStr and cmpMoney is never
#                          reached on that path (grade.go), so LDG-REFUSE-03
#                          contributes 0 exactly as LDG-REFUSE-01 and -02 do.
#                          Its request legs carry amount_major_text tokens, which
#                          are the CALLER'S characters and are graded by nothing.
#                          If this number ever rises on a refusal vector, the
#                          comparator has started grading an amount nobody
#                          observed and THAT is the defect, not this pin.
#                          T295 ADDED TWO MORE REFUSAL VECTORS AND THIS FIGURE
#                          STILL DID NOT MOVE, for the same reason, argued in
#                          place rather than bumped for appearance: LDG-REFUSE-04
#                          and -05 both have expect.legs [] and both totals "",
#                          so grade.go routes them through diffRefusal and
#                          cmpMoney is unreachable on that path. The brief for
#                          T295 said to bump this pin if anything was promoted;
#                          bumping it would have recorded money cells that no
#                          comparison performs, which is the self-certifying
#                          shape this whole census exists to refuse. The pin is
#                          held at 21 and MEASURED at 21 on the run that promoted
#                          them.
#
# T305 MOVES TWO OF THESE THREE, AND THE MONEY-CELL ONE IS THE INTERESTING MOVE.
# LDG-05-openingbalance-accepted-empty-ledger is the first ACCEPTING-side
# opening-balance vector in this store: three request legs, and SIX expect legs,
# because saveAllDebitOrCreditOpeningBalanceEntries persists the leg at :791 AND
# its contra at :796 inside the per-leg loop. It grades 27 cells of which 8 are
# money -- six leg amounts and two totals -- so MONEYCELLS goes 21 -> 29 and
# PARITY goes 4 -> 5. THE COMPARISON REALLY IS PERFORMED, which is the property
# the note above insisted on when it DECLINED to bump this pin for two refusal
# vectors: ledger-wrong-truncating dies on all eight of them with measured
# margins -25, -25, -37, -37, -62, -62 and -124 twice.
#
# T328 MOVES TWO OF THE THREE AGAIN, AND THE ARITHMETIC IS RE-DERIVED FROM THE
# COMPARATOR RATHER THAN COPIED FROM T305's PARAGRAPH.
#
#   PARITY 5 -> 7. LDG-06-postclosure-entry-accepted-one-day-after-closing-date
#   and LDG-07-entry-on-the-business-date-accepted are the ACCEPTING sides of the
#   two DATE boundaries, promoted from T327's B-1 and B-2 arms (both HTTP 200 on
#   a throwaway instance). Before them the store pinned only the REFUSING side of
#   each rule, and `ledger-wrong-date-rules-always-refusing` -- a port that
#   refuses every DATED entry -- passed 5/5 parity and 5/5 refusal, exit 0
#   [out/10-mutant-SURVIVES-before.txt]. That is the same hole T305 closed for
#   opening balances, on a different rule.
#
#   REFUSAL 5 -> 5. NEITHER NEW VECTOR IS A REFUSAL. Stated rather than left to
#   be inferred, because this pin has now stayed still across three promotions
#   for three different reasons.
#
#   MONEYCELLS 29 -> 39, RE-DERIVED FROM diffEntry AND NOT GUESSED. grade.go
#   compares, per journal-entry vector: leg_count (cmpInt), then per leg
#   gl_account_id (cmpInt), gl_account_code (cmpStr), entry_side (cmpStr) and
#   amount_minor (cmpMoney), then total_debits_minor and total_credits_minor
#   (cmpMoney). So a vector with L legs grades 1 + 4L + 2 cells of which L + 2
#   are MONEY. Both new vectors carry L = 3 -- the plain create path (:146)
#   writes ONE entry per request leg, with no contra expansion, which is
#   defineOpeningBalance-only (:791/:796) -- so each adds 15 graded cells of
#   which 5 are money: 3 leg amounts (25000025, 10000037, 35000062) and 2 totals
#   (35000062 each). 29 + 5 + 5 = 39, and the run MEASURED 136 graded / 39 money.
#   T297's reasoning about diffRefusal does NOT apply here and the difference is
#   the point: cmpMoney is unreachable from diffRefusal (grade.go:202-221 calls
#   only cmpInt/cmpStr), which is why T294 and T295 correctly declined to move
#   this pin for three refusal vectors. These two are ACCEPTANCES routed through
#   diffEntry, the comparisons are really performed, and ledger-wrong-truncating
#   dies on all ten of them with measured margins -25, -37, -62 per vector on the
#   legs and -62 on each total.
#
# T307 MOVES EXACTLY ONE OF THE THREE, AND THE OTHER TWO ARE ARGUED IN PLACE
# RATHER THAN LEFT SILENT — this pin has now held still across four promotions
# for four different reasons and the reader should not have to guess which.
#
#   PARITY 7 -> 7. NOTHING WAS ACCEPTED. T307 fired NO probe at the reference
#   oracle: it promoted bytes T287 committed in August and that MANIFEST.sha256
#   still verifies 87/87. A vector promoted with no oracle contact cannot be an
#   acceptance, because an acceptance is an observation of a POST that wrote.
#
#   REFUSAL 5 -> 6. LDG-REFUSE-06-preclosure-entry-before-closing-date-echoes-
#   the-closing-date, promoted from T287's A2-02 under T295 backlog B-3. THIS IS
#   THE VECTOR T295 MEASURED AS UNPROMOTABLE AND SAID WHY: A2-02's captured
#   response body is BYTE-IDENTICAL to A2-01's (both sha256 c12e977f…) despite a
#   different transactionDate, so on the three cells the Refusal shape had it
#   could not diverge from LDG-REFUSE-04 and would have raised the corpus count
#   by one and the kill count by ZERO — corpus inflation, which this census
#   exists to catch. T307 added a FOURTH refusal cell and the count now moves for
#   a kill: ledger-wrong-accounting-closed-echoes-transaction-date dies on this
#   vector and on no other.
#   THE FOURTH CELL IS A SELECTOR, NOT A DATE, and that is what makes this a
#   promotion rather than a calendar dependency: expect.refusal.arg_echo names
#   WHICH declared input the oracle echoed ("latest_closing_date" on :637-638,
#   "transaction_date" on :631) and the comparator RESOLVES it from Request. No
#   date literal appears in any expectation, so the claim survives re-capture on
#   any dates whatsoever. T294's deliberate refusal to grade OB-01's own args —
#   26 LIVE TRANSACTION IDS — is UPHELD and is now enforced by admit.go on two
#   independent grounds rather than remembered: OB-01's args[0].value is a JSON
#   ARRAY and the selector vocabulary is closed to the two scalar dates, and
#   request.posted_non_contra_transaction_ids was itself transcribed FROM that
#   same wire field, so a selector resolving against it would compare the
#   captured body with a copy of itself.
#
#   MONEYCELLS 39 -> 39, AND THE REASON IS T297's, RE-CHECKED RATHER THAN
#   INHERITED. grade.go's diffRefusal reaches only cmpInt and cmpStr; the new
#   cell is compared with cmpStr, so cmpMoney is STILL unreachable from that
#   function and a refusal vector still contributes ZERO money cells. Bumping
#   this figure for LDG-REFUSE-06 would record money comparisons that no
#   comparison performs — the self-certifying shape the paragraphs above declined
#   three times. Held at 39 and MEASURED at 39 on the run that promoted it.
#
#   GRADED CELLS ARE NOT PINNED AND THIS IS WHERE THAT SHOWS. The arg cell adds
#   1 to LDG-REFUSE-04, 1 to LDG-REFUSE-05 and 4 to the new vector, so the
#   ledger's graded total rises; no pin in this file reads it. Recorded as
#   FU-T307-1 rather than pinned here, because adding a tenth census pin is a
#   change to this file's gate structure and not T307's to make in the same diff
#   that moves two of the existing nine.
EXEMPTION_PIN_LEDGER_PARITY=10
EXEMPTION_PIN_LEDGER_REFUSAL=6
EXEMPTION_PIN_LEDGER_MONEYCELLS=63

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
  end="$(LC_ALL=C grep -an '^#=END-OF-HELP=$' "$src" | head -1 | cut -d: -f1)"
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
  # D-2 (T155): the P-35 counter counts files ENUMERATED, not files SCANNED. Both
  # no-float shell guards pipe every file through perl; with perl truly absent they
  # enumerate, inspect nothing, print "inspected 1 files" and RETURN 0 on a plainly
  # visible float. Closing ABSENCE only — "perl ran and died on one file" is a
  # separate hole and stays open as a follow-up, not a micro-fix.
  if ! command -v perl >/dev/null 2>&1; then
    warn "conformance: no perl. Both no-float guards pipe every file through perl; without it they"
    warn "conformance: enumerate files and inspect none. EXIT 2 — the harness is unusable. NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
  # T173, same D-2 shape as perl above. The two CAPTURE-RIG guards are Python programs, and
  # ABSENCE of the interpreter must be an outright refusal rather than a skipped guard: a
  # `command -v python3 || return 0` would have turned "the interpreter is missing" into a
  # silent PASS on a wire-side float, which is the exact P-45 defect T173 exists to close.
  if ! command -v python3 >/dev/null 2>&1; then
    warn "conformance: no python3. The capture-rig guards (wire-float round trip, narrow seam"
    warn "conformance: handler) are Python; without it they inspect nothing and their absence"
    warn "conformance: would read as a pass. EXIT 2 — the harness is unusable. NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

# ---------------------------------------------------------------------------
# HARD guards. They prove the ABSENCE of known-bad patterns and nothing more.
# ---------------------------------------------------------------------------

# THE TWO TOKENS `LC_ALL=C` AND `-a` ON EVERY LOAD-BEARING grep IN THIS FILE.
#
# Both are required and they defend against TWO DIFFERENT PROGRAMS. On this host
# the token `grep` names two of them and which one you get depends on where it is
# typed [VERIFIED: T108's 360-cell matrix, .softhouse/capture/t108-grep/MATRIX.md;
# ruling recorded as P-33 in .softhouse/patterns.md]:
#
#   inside a script (what these guards are)  -> /usr/bin/grep, BSD grep
#       2.6.0-FreeBSD. Shell functions are NOT exported to a child, so a script
#       never sees the session's `grep`. In a UTF-8 locale BSD grep goes blind to
#       the part of ONE LINE at and to the RIGHT of an invalid byte: count 0,
#       exit 1, NO diagnostic. `LC_ALL=C` fixes that; `-a` does NOT.
#   typed into the Claude Code Bash tool     -> a shell function re-execing the
#       `claude` binary with argv[0]=ugrep, i.e. ugrep with `-I` hard-coded, which
#       skips the WHOLE FILE and prints nothing at all. `-a` fixes that;
#       `LC_ALL=C` does NOT.
#
# These guards fire only when they FIND something bad, so a blind grep is a
# SILENT PASS ON A FLOAT — the money non-negotiable at the top of CLAUDE.md,
# passing without having checked (P-34, P-35). Measured end to end before this
# fix: a single `.json` at the STORE ROOT carrying a float and one lone 0xE2
# earlier on the same line produced `VERDICT: PASS (exit 0) — 42 parity vectors
# … 5576 cells`, byte-identical to the clean run and with no warning anywhere
# [VERIFIED: .softhouse/capture/t154-nofloat/out/leg1-e2e-RED-before-fix.txt].
#
# DO NOT DROP EITHER TOKEN. A test that removes them is in drive-leg1.sh, and it
# runs both arms against the REAL pre-fix bytes at a pinned immutable sha.

# guard_no_float_in_vectors: no JSON number in any vector file may carry a '.',
# 'e' or 'E'. Every monetary value in the store is an integer STRING in minor
# units, so nothing legitimate is inconvenienced. A float anywhere in a vector
# file is a rejection — including in a field somebody thought was "just" a rate or
# a day count.
#
# PHRASED POSITIVELY (P-35): it reports how many files it INSPECTED, and zero
# inspected is an ERROR, not a pass. "I found nothing wrong" is vacuous on no
# input by construction, and this guard's `find` can return nothing for reasons
# that have nothing to do with the store being clean — a renamed store root, a
# typo in STORE_ROOT, a `find` that failed.
guard_no_float_in_vectors() {
  local bad=0 seen=0 f hits
  while IFS= read -r f; do
    seen=$((seen + 1))
    # Strip string literals first, then look for a decimal or exponent number.
    #
    # `grep -c`, NOT `grep -q` — AND THE REASON IS THE MONEY NON-NEGOTIABLE ITSELF.
    # `grep -q` exits 0 the instant it MATCHES. The upstream `perl` is then writing
    # into a closed pipe: for any post-strip output larger than one pipe buffer it is
    # still blocked in write(2) when that happens, takes SIGPIPE, and `set -o pipefail`
    # (line 396) promotes the PIPELINE's status to that non-zero value — so the
    # enclosing `if` evaluated FALSE ON A FLOAT IT HAD ACTUALLY FOUND. The guard behind
    # the first non-negotiable in CLAUDE.md went SILENT exactly when it had something to
    # say, and only on the big inputs. That is P-57, on a money path.
    # Two conditions are BOTH necessary and both are satisfied here: output larger than
    # the buffer, and a consumer that can STOP EARLY. (A 400 KB single-line JSON does not
    # reproduce it, because `grep -q` on one line cannot stop before EOF.)
    # Measured on this host: perl producer + /usr/bin/grep consumer inverts at 64776 B of
    # post-strip output; 64775 B still fires. `.softhouse/reviews/T191-probe/`.
    # `grep -c` consumes ALL of its input, so the producer never meets a closed pipe.
    #
    # -a AND LC_ALL=C ARE BOTH LOAD-BEARING AND NEITHER MAY BE DROPPED (P-33, P-58):
    # they defend against DIFFERENT programs, and inside this script `grep` is
    # /usr/bin/grep (BSD grep), not any interactive shell function of that name.
    # [T191]
    hits="$(perl -0pe 's/"(\\.|[^"\\])*"//g' "$f" \
            | LC_ALL=C grep -acE '[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]')" || true
    [ -n "$hits" ] || hits=0
    if [ "$hits" -gt 0 ]; then
      warn "conformance: FLOAT-SHAPED NUMBER in $f ($hits stripped line(s) matched)"
      bad=1
    fi
  done < <(find "$STORE_ROOT" -name '*.json' -type f | sort)
  if [ "$seen" -eq 0 ]; then
    warn "conformance: guard_no_float_in_vectors INSPECTED ZERO FILES under $STORE_ROOT."
    warn "conformance: a guard that inspects nothing passes everything. This is an ERROR, not a pass."
    return 1
  fi
  say "conformance: no-float guard — inspected $seen .json files under $STORE_ROOT"
  return "$bad"
}

# guard_no_float_in_harness: no floating-point identifier ANYWHERE in the Go
# module. Implemented in Go (TestNoFloatInTheGuardedGoTree, and — the part that
# actually gates a verdict — the census that grade.go runs inside the harness
# binary) over the TOKEN stream, because the frozen contract's doc comments name
# the forbidden types in order to forbid them and a byte grep therefore fires on
# the prohibition itself. Repeated here only as a cross-check that skips comments
# the same way.
#
# IT INSPECTS IDENTIFIERS, AND A FLOAT LITERAL IS NOT AN IDENTIFIER. `rate :=
# 0.036 / 12.0` carries no forbidden identifier at all, so neither this guard nor
# the Go test caught it until T154 added the LITERAL check on the Go side. That
# check is the one that covers literals; this one stays as written and covers
# identifiers.
#
# T166 WIDENED THE ROOT FROM ONE SUBTREE TO THE MODULE, AND ADDED A PACKAGE
# COUNT. Until T166 this find was rooted at "$NEXUS_DIR/internal/apps/loanschedule",
# as were the Go-side census root and guard_gofmt below. All three looked at one
# subtree, so a float64 on a money path in ANY other package — and a float in any
# SUBDIRECTORY of any package — passed every automated check in this repository.
# Measured, not theorised: with three floats planted under
# nexus/internal/apps/ledger/ (a literal, an identifier at the package root, and
# an identifier one directory deeper), a full run of this script produced output
# BYTE-IDENTICAL to the clean baseline — VERDICT: PASS, exit 0, 5664 cells, and
# the very same "24 .go files" line this function prints. Unchanged precisely
# because it never looked.
#
# THE ROOT IS NOW DERIVED, NOT ENUMERATED. `find` recurses by default, so rooting
# at "$NEXUS_DIR" — the Go module root — means a NEW PACKAGE IS COVERED BY
# DEFAULT, wherever in the module it lands and however deeply it nests. Adding
# `ledger` as a second hard-coded path would have reproduced the defect for the
# next package and every package after it (P-26: sweep the concept, not the
# sentence). There is deliberately NO exemption list: an allowlist outlives the
# reason it was added, and the one file in this module that must NAME the
# forbidden spellings in code — nofloat.go — instead splits them across string
# concatenations so the bytes never appear contiguously, which is the principled
# form of the same exemption and cannot rot.
#
# Same positive phrasing as above, now on BOTH counts: zero files inspected is an
# ERROR, and so is zero PACKAGES. A file count alone cannot tell a module-wide
# walk apart from a single-directory walk, and the single-directory walk is the
# state this guard was in while printing a healthy-looking number.
guard_no_float_in_harness() {
  local bad=0 seen=0 pkgs=0 f hits
  while IFS= read -r f; do
    seen=$((seen + 1))
    # Drop // comments and /* */ comments, then look for a float identifier.
    #
    # `grep -c`, NOT `grep -q`, for exactly the reason spelled out in
    # guard_no_float_in_vectors above: `grep -q` stops at the first match, `perl` dies of
    # EPIPE mid-write, `set -o pipefail` promotes that to the pipeline's status, and the
    # `if` reads FALSE ON A FLOAT IDENTIFIER IT FOUND. It is size-gated, so it is silent
    # on small files and wrong on large ones — the failure mode that survives review.
    # LATENT, NOT LIVE, IN TODAY'S TREE, and say so honestly: the largest post-strip .go
    # output in this module is conformance/structural_test.go at 44,941 B (raw 56,153),
    # against a 64,776 B inversion point measured on this host -- a 1.44x margin, not a
    # safety property. The frozen contract.go, the biggest file by raw bytes, clears it
    # only because it is almost entirely comment: 151,885 raw -> 5,690 stripped. One large
    # generated or table-driven .go file closes that margin and the guard goes quiet with
    # no other symptom. `grep -c` drains.
    # -a and LC_ALL=C stay (P-33, P-58 — different programs, different attacks). [T191]
    hits="$(perl -0pe 's{//[^\n]*}{}g; s{/\*.*?\*/}{}gs' "$f" \
            | LC_ALL=C grep -acE '\bfloat(32|64)\b|\bbig\.Float\b|\bcomplex(64|128)\b|\b(Parse|Format|Append)Float\b')" || true
    [ -n "$hits" ] || hits=0
    if [ "$hits" -gt 0 ]; then
      warn "conformance: FLOATING-POINT IDENTIFIER in $f ($hits uncommented line(s) matched)"
      bad=1
    fi
  done < <(find "$NEXUS_DIR" -name '*.go' -type f | sort)
  # The package count, derived from the same enumeration: distinct directories
  # holding at least one .go file.
  pkgs="$(find "$NEXUS_DIR" -name '*.go' -type f | sed 's|/[^/]*$||' | sort -u | LC_ALL=C grep -ac '' || true)"
  [ -n "$pkgs" ] || pkgs=0
  if [ "$seen" -eq 0 ] || [ "$pkgs" -eq 0 ]; then
    warn "conformance: guard_no_float_in_harness INSPECTED $pkgs PACKAGES / $seen FILES under $NEXUS_DIR."
    warn "conformance: a guard that inspects nothing passes everything. This is an ERROR, not a pass."
    return 1
  fi
  say "conformance: no-float guard — inspected $pkgs Go packages / $seen .go files under $NEXUS_DIR (recursive, whole module)"
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
# So this guard formats NOTHING (never `gofmt -w`, never `go fmt ./...`). If it
# formatted contract.go it would either fail forever or tempt a later agent to
# "fix" a frozen artefact, and the second outcome is the dangerous one.
#
# T166 WIDENED IT FROM TWO NAMED DIRECTORIES TO THE MODULE, for the same reason
# as guard_no_float_in_harness above: it named "$HARNESS_PKG" and one `cmd`
# directory, so every package outside those two — the whole ledger port included
# — was unchecked. `gofmt -l` on a directory recurses, so rooting at "$NEXUS_DIR"
# derives the set and a new package is covered by default. The contract.go
# exemption stays, and stays expressed as a path filter on the OUTPUT rather than
# as a narrowed root, so that widening the root can never silently re-include it
# and narrowing it can never silently drop everything else.
#
# Positively phrased, like its neighbours: it reports how many files it inspected,
# and zero is an ERROR.
guard_gofmt() {
  local unformatted seen
  seen="$(find "$NEXUS_DIR" -name '*.go' -type f | LC_ALL=C grep -ac '' || true)"
  [ -n "$seen" ] || seen=0
  if [ "$seen" -eq 0 ]; then
    warn "conformance: guard_gofmt INSPECTED ZERO FILES under $NEXUS_DIR."
    warn "conformance: a guard that inspects nothing passes everything. This is an ERROR, not a pass."
    return 1
  fi
  unformatted="$(gofmt -l "$NEXUS_DIR" 2>/dev/null \
                 | LC_ALL=C grep -av "/contract/contract.go$" || true)"
  if [ -n "$unformatted" ]; then
    warn "conformance: not gofmt-clean:"
    warn "$unformatted"
    return 1
  fi
  say "conformance: gofmt guard — inspected $seen .go files under $NEXUS_DIR (recursive, whole module; contract.go exempt, gate G-3)"
  return 0
}

# ---------------------------------------------------------------------------
# THE CAPTURE-RIG GUARDS (T173). Everything above this line inspects the VECTOR
# STORE and the GO MODULE. Nothing above it has ever opened a capture rig — and the
# capture rigs are what produce the vectors, so a defect there is upstream of every
# guard the harness already had.
#
# WHY THEY ARE HERE AND NOT IN A `go test` OR A README (P-45).
# T163 shipped a request-body float guard and an audit; T169 shipped a narrow-catch
# lint. Both are falsifiable and both were correct. NEITHER WAS INVOKED BY ANYTHING
# THAT RUNS. `conformance.sh` never runs `go test`, so a Go-test-only guard is not a
# guard here either; and a Python script a handoff recommends running is a
# recommendation, not a check. In that state the next capture rig can reintroduce the
# wire-side float round trip and every automated check in this repository stays green.
# This file is the path that actually executes, so this is where they go.
#
# THE INSPECTED SET IS DERIVED, EXACTLY AS T166 MADE THE GO-SIDE ROOTS DERIVED.
# Neither guard names a rig. The float guard walks `.softhouse/capture` recursively and
# takes every `*.json` under any directory named `req` plus every `*.req` wire-bytes
# artefact, at any depth; the narrow-catch lint walks the whole repository for `*.java`.
# A rig that does not exist yet is therefore covered on the day it lands. Hard-coding a
# subtree is precisely how T163's own audit came to inspect one rig out of six while
# printing a healthy-looking number, and how 7,018 lines of new money code got passed by
# never being looked at.
#
# EACH GUARD RUNS ITS OWN SELFTEST FIRST, IN THE SAME INVOCATION.
# A wired guard that has been quietly neutered is worse than an unwired one, because it
# is believed (P-22). So the selftest — which drives the guard RED on a planted defect
# AND requires it to stay GREEN on a clean tree (P-50) — runs on every conformance run,
# not on the day someone remembers. It is pure Python over temporary directories: it
# never reads the real tree, never contacts the reference oracle, and costs well under a
# second. Its output is captured and summarised to one line, and DUMPED IN FULL on
# failure, so a green run stays readable and a red run stays diagnosable.
#
# BOTH ARE HARD GUARDS: a failure exits 2 through run_guards, BEFORE the oracle probe
# line is printed. That is not an outage. The driver's park condition is `exit 2` AND
# `probe != up`, and on this path there is no probe line at all.

# census_inspected: read the census's SUBJECT COUNT off stdin — the FIRST `inspected N` on
# each CENSUS line — and print one figure per line. Factored out of _run_capture_guard so it
# can be driven RED and GREEN on synthetic lines by --prove; an extraction buried inside a
# guard is an extraction nothing can falsify.
#
# THE DEFECT IT REPLACES (T197 F-1, polarity established by T201 before the fix).
# The shipped expression was:
#     sed -n 's/^CENSUS .*inspected \([0-9][0-9]*\).*$/\1/p'
# `.*` is greedy, so the leading `.*` runs to the END of the line and backtracks — the
# capture therefore lands on the **LAST** `inspected N`, not the first. MEASURED, one line
# per case, /usr/bin/sed (BSD, this host), LC_ALL=C, input a plain text file:
#     `… inspected 7 rigs / inspected 320 tokens`   OLD -> 320   (subject count is 7)
#     `… inspected 320 bodies / inspected 7 rigs`   OLD -> 7     (subject count is 320)
#     `… inspected 57 .java under /x/inspected 0 fixtures/repo`  OLD -> 0  (count is 57)
#
# POLARITY, STATED BECAUSE T197 RECORDED IT AS UNKNOWN AND A FIX SHIPPED WITHOUT IT IS THE
# DEFECT CLASS THIS PROGRAM KEEPS FINDING. The figure feeds `[ "$inspected" -lt "$floor" ]`,
# refuse-if-below. So the direction is decided by which of the two figures is bigger:
#   * trailing figure LARGER  -> the floor is cleared by a number that is not the subject
#     count. FAIL-OPEN, SILENT PASS. A guard that opened 7 of 320 files is accepted because
#     an unrelated 320 sits later on the same line. This is the direction that matters.
#   * trailing figure SMALLER -> spurious refusal. FAIL-CLOSED, cry wolf, exit 2 over a
#     clean tree. Loud, and it needs NO code change to fire: a checkout path containing the
#     token `inspected 0` is enough (third case above), and the census line interpolates an
#     absolute path today.
# BOTH are reachable, and which one fires is chosen by the PROSE of a census line that no
# test constrains — one appended sub-count is the whole distance to the fail-open direction.
# Latent only because every census line currently carries exactly one `inspected N`; the
# live figures 320, 57 and 44 are unchanged by this fix, which is the point.
#
# HOW THE REPLACEMENT IS FIRST-WINS. `s///` without `g` rewrites the LEFTMOST match, and
# dropping the leading `.*` leaves nothing to backtrack over: the pattern must start at an
# `inspected ` that is actually followed by a digit, and the leftmost such position is the
# first one. `.*$` then eats the rest of the line, and `s/^.*[^0-9]//` (greedy, to the last
# NON-digit) strips the surviving prefix. The address keeps a CENSUS line carrying no
# `inspected N` producing no output, exactly as the old expression did.
#
# P-57: `sed` consumes all of stdin and never exits early, so this is not a member of the
# `| grep -q` / `| head` EPIPE family. P-58: measured under `bash` on this host, where `sed`
# is /usr/bin/sed (BSD); `LC_ALL=C` is kept so the byte semantics hold under any locale.
census_inspected() {
  LC_ALL=C sed -n '/^CENSUS .*inspected [0-9]/{
s/inspected \([0-9][0-9]*\).*$/\1/
s/^.*[^0-9]//
p
}'
}

# _run_capture_guard <script-basename> <human-label> <population-floor>
# Shared body, because the two guards differ only in which program they run. Written once
# rather than twice so that a later fix to the missing-script or empty-output handling
# cannot be applied to one guard and forgotten on the other.
#
# <population-floor> IS MANDATORY AND MUST BE DERIVED BY THE CALLER, never a literal. See
# the two callers below for how each derives its own, and the T194 block at the census
# test for why a literal would be a second silent pass in the costume of a check. Omitting
# it leaves `floor` empty, which this function treats as a FAILED DERIVATION and refuses —
# so a third guard added later cannot be wired up without measuring its population.
_run_capture_guard() {
  local script="$REPO_ROOT/.softhouse/capture/lib/$1" label="$2" floor="${3:-}"
  # T188 MICRO-FIX: `census_lines` (added by e93afc9) was the one variable in this
  # function left un-`local`. It leaked into the global scope of a script that calls
  # this function twice, for two different guards. Mechanical; no number changed.
  local out rc cases census_lines red green inspected ins_all

  # A MISSING GUARD IS AN ERROR, NOT A SKIP. `[ -f ... ] || return 0` would mean deleting
  # the file silently switches the check off and the run still says PASS.
  if [ ! -f "$script" ]; then
    warn "conformance: the $label guard is MISSING: expected $script"
    warn "conformance: a guard that is not there cannot pass. This is an ERROR, not a pass."
    return 1
  fi

  out="$(python3 "$script" --selftest 2>&1)"; rc=$?
  cases="$(printf '%s\n' "$out" | LC_ALL=C grep -ac '^  -> exit ' || true)"
  [ -n "$cases" ] || cases=0
  # A COUNT OF LINES IS NOT EVIDENCE OF A DEMONSTRATION. `cases` counts how many times the
  # selftest SPOKE, and ONE line satisfies `-ne 0`: a stub whose `--selftest` prints a single
  # `  -> exit 0` was accepted here as "selftest OK, 1 cases" where the real guard reports 5
  # and 8. That is the same defect as the census one below, one gate over — and fixing only
  # the census one would have converted a known hole into a hidden one.
  #
  # WHAT IS CHECKED INSTEAD IS THE CLAIM THE NEXT TWO LINES ALREADY PRINT. They have always
  # said the cases drive the guard RED on a planted defect AND GREEN on the clean equivalent
  # (P-22 with P-50's second half). Nothing checked it. So: at least one case must exit
  # NON-ZERO and at least one must exit ZERO. This is deliberately NOT a floor on the count —
  # a number here would go stale the day a case is added or retired, and a stale number is a
  # check that has stopped checking. Both polarities is a property of the demonstration, not
  # of the corpus, so it cannot go stale at all. RESIDUAL, stated rather than papered over: a
  # stub that prints exactly two lines, one of each polarity, still passes this gate; only
  # pinning the guard's bytes closes that, and that is T194's recorded follow-up.
  # [T194, from T184's FU-T184-1]
  red="$(printf '%s\n' "$out" | LC_ALL=C grep -ac '^  -> exit [1-9]' || true)"
  green="$(printf '%s\n' "$out" | LC_ALL=C grep -ac '^  -> exit 0$' || true)"
  [ -n "$red" ] || red=0
  [ -n "$green" ] || green=0
  if [ "$rc" -ne 0 ] || [ "$cases" -eq 0 ] || [ "$red" -eq 0 ] || [ "$green" -eq 0 ]; then
    warn "conformance: the $label guard FAILED ITS OWN SELFTEST (exit $rc, $cases cases observed,"
    warn "conformance:   $red drove it RED, $green drove it GREEN — both directions are required)."
    warn "conformance: it can no longer be shown to refuse the defect it exists to refuse."
    warn "$out"
    return 1
  fi
  say "conformance: $label guard — selftest OK, $cases cases ($red drive it RED on a planted"
  say "conformance:   defect, $green stay GREEN on the clean equivalent; both directions READ)"

  out="$(python3 "$script" "$REPO_ROOT" 2>&1)"; rc=$?
  # THE CENSUS LINE MUST BE PRESENT BEFORE ITS VALUE IS READ. Same discipline the
  # oracle probe follows: test for presence first, then value. A program that died
  # before printing anything must not be read as a clean tree, and a `rc -eq 0` test
  # on its own would do exactly that if the script were ever replaced by a stub.
  # `grep -q` exits on the FIRST match, and the census line is the FIRST line the guard
  # prints, so the upstream `printf` dies with EPIPE and `set -o pipefail` (line 396) makes
  # the whole pipeline non-zero -- inverting this test into "NO CENSUS LINE" WHEN THE LINE IS
  # PRESENT. That is this harness's own "never pipe into head" hazard (reading the wrong
  # process's status) turned against the P-35 machinery meant to catch a silent guard.
  # `grep -c` consumes all input, so nothing closes the pipe early.
  # [T173 merge defect B, found by the driver on merged main, local fire 20260821-054355]
  census_lines="$(printf '%s\n' "$out" | LC_ALL=C grep -ac '^CENSUS ' || true)"
  [ -n "$census_lines" ] || census_lines=0
  if [ "$census_lines" -eq 0 ]; then
    warn "conformance: the $label guard printed NO CENSUS LINE (exit $rc)."
    warn "conformance: without it there is no evidence anything was inspected. ERROR, not a pass."
    warn "$out"
    return 1
  fi
  # ...AND NOW ITS VALUE IS ACTUALLY READ. The comment above has said "BEFORE ITS VALUE IS
  # READ" since T173 and the value was never read: `census_lines` is the COUNT OF LINES
  # matching `^CENSUS `, so a guard replaced by a stub that prints `CENSUS 0 files / 0 dirs`
  # and exits 0 reached `return 0` and the whole harness reported VERDICT PASS. Verified end
  # to end by T184 (FU-T184-1) and re-driven by T194 against this file before the fix. The
  # machinery built to prove a guard is not silent proved only that it SPOKE.
  #
  # THE FLOOR IS DERIVED, AND THAT IS THE WHOLE POINT. A literal (`-lt 300`) would be a
  # second silent pass wearing the costume of a check: it goes stale the moment the corpus
  # grows or shrinks, and nothing tells the next reader it has. Each caller measures its own
  # population with `git ls-files` — a DIFFERENT program from the guard's `os.walk`, over the
  # same set — so the floor moves with the corpus by construction and can never be "the
  # number that was true in August".
  #
  # POLARITY, stated because P-57 rule 3 requires it. `>=`, not `==`, and the residual is
  # fail-OPEN in exactly one direction: `git ls-files` sees only TRACKED files, so an
  # untracked addition raises `inspected` above `floor` and is accepted. Everything else is
  # fail-CLOSED — no `inspected N` in the census, a non-numeric figure, or a floor that did
  # not derive all refuse. The cry-wolf case is a tracked file deleted from the working tree,
  # and refusing a half-deleted corpus is the correct answer anyway.
  #
  # `sed` (BSD, /usr/bin/sed) consumes all input and never exits early, so this adds no
  # member of the `| grep -q` / `| head` EPIPE family T191 repaired (P-57). Measured
  # programs (P-58): under `bash` on this host `grep` is /usr/bin/grep, BSD 2.6.0-FreeBSD;
  # `-a` and `LC_ALL=C` are kept on every expression so the same bytes hold if the ugrep
  # shell function (which re-execs with `-I`) is ever in scope instead. [T194]
  #
  # THE EXTRACTION IS NO LONGER WRITTEN HERE. It used to be a greedy one-liner that read the
  # LAST `inspected N` on the line instead of the first — see census_inspected above for the
  # measurement, the established polarity and why first-wins is the correct reading.
  # [T197 F-1, polarity established and fixed by T201]
  ins_all="$(printf '%s\n' "$out" | census_inspected)"
  inspected="${ins_all%%$'\n'*}"
  case "$inspected" in ''|*[!0-9]*) inspected=-1 ;; esac
  case "$floor"     in ''|*[!0-9]*) floor=-1 ;; esac
  if [ "$floor" -lt 1 ]; then
    warn "conformance: the $label guard's POPULATION FLOOR did not derive (caller passed '${3:-<nothing>}')."
    warn "conformance: a floor of zero would readmit exactly the vacuous pass this test exists to"
    warn "conformance:   refuse, so an underived floor is an ERROR, not a pass."
    return 1
  fi
  if [ "$inspected" -lt "$floor" ]; then
    warn "conformance: the $label guard's CENSUS FIGURE IS BELOW ITS DERIVED FLOOR:"
    warn "conformance:   census says inspected $inspected; git tracks $floor file(s) it must open."
    warn "conformance: a census line is not evidence unless its number is read. ERROR, not a pass."
    warn "$out"
    return 1
  fi
  printf '%s\n' "$out" | LC_ALL=C grep -a '^CENSUS ' | while IFS= read -r line; do
    say "conformance: $line"
  done
  say "conformance:   census figure READ: inspected $inspected >= $floor tracked by git (floor DERIVED, not pinned)"
  if [ "$rc" -ne 0 ]; then
    warn "conformance: the $label guard REFUSED:"
    warn "$(printf '%s\n' "$out" | LC_ALL=C grep -av '^CENSUS ')"
    return 1
  fi
  return 0
}

# guard_no_float_in_capture_requests: no numeric token in any capture REQUEST BODY may be
# rewritten by a binary-double round trip. That is T163's audit, generalised from one named
# rig to the derived whole-capture-tree set.
#
# WHAT IT IS NOT, STATED HERE SO NOBODY READS MORE INTO A GREEN RUN THAN IT MEANS. It is
# not "no float-shaped token on the wire". 221 of the 320 committed request bodies already
# carry one — 214 `interestRatePerPeriod` (a RATE), 53 charge `amount`, and 11 `principal`
# `1162502.5`, the T149/T153 half-cent TIE probes where the half-cent IS the observation.
# Refusing those would refuse the entire committed corpus on the first run and pin this
# harness at exit 2 forever; a guard that refuses everything is not a guard. The census
# line prints float-shaped tokens PRESENT and ALTERED as two separate numbers so the
# weaker property can never be mistaken for the stronger one. The stronger question —
# money on the wire as a float at all — is a T173 follow-up with its population measured,
# not a claim this guard makes.
guard_no_float_in_capture_requests() {
  # THE FLOOR, DERIVED BY A DIFFERENT PROGRAM OVER THE SAME POPULATION (T194). The guard's
  # own `derive()` takes every *.json whose DIRECT parent directory is named `req`, plus
  # every *.req wire-bytes artefact, at any depth under .softhouse/capture
  # [VERIFIED: .softhouse/capture/lib/check_wire_float_roundtrip.py, `derive()`]. `git
  # ls-files` is asked for the same set from the index instead of from `os.walk`, so the two
  # agree only if the guard actually opened the tree. Measured in this worktree: bodies 320.
  # Tracked is a SUBSET of walked (untracked files raise the guard's figure and never the
  # floor), which is why _run_capture_guard compares with `>=`.
  #
  # SECOND TERM — THE STORE-CITED CAPTURE RECORDS (T193). The guard's second arm opens every
  # file a stored vector names in `provenance.capture_ref` and grades the numeric tokens
  # inside its recorded-request blocks. 42 of the 43 parity vectors name a
  # `capture-prod3*-raw.json` and the 43rd names a Path B raw [re-derived by T193 by reading
  # provenance.capture_ref as a FIELD across .softhouse/vectors/**], and BEFORE T193 the
  # guard's walk reached ZERO of them — a `req/`-shaped walk cannot see a Path A capture
  # whose request is driven in-process by Capture3*.java and never committed under `req/`.
  #
  # The floor term is DERIVED BY A DIFFERENT PROGRAM AGAIN: `git grep` + `sed` over the
  # tracked vector store, against the guard's `os.walk` + `json.loads`. They agree only if
  # both actually read the citations. Distinct refs, because two vectors may cite one record
  # and the guard opens it once. The empty `capture_ref` a hand-authored or contract vector
  # carries is dropped by `grep -v '^$'` — admit.go requires the citation only of a PARITY
  # vector, so counting the empties would inflate the floor above what the guard can open and
  # cry wolf on a clean tree. Measured in this worktree: records 8, floor 320 + 8 = 328.
  #
  # WHY THE SUM AND NOT TWO FLOORS: the guard's FIRST census line carries the figure
  # `_run_capture_guard` reads (census_inspected is first-wins, per line, and takes the first
  # line's figure), and that line reports total DOCUMENTS opened. One number, one comparison.
  # The per-arm breakdown is on the later CENSUS lines, which are printed for the human.
  #
  # P-57: every stage here consumes all of its input — `git grep`, `sed`, `grep`, `sort`,
  # `wc` — so no member of the `| grep -q` / `| head` EPIPE family is introduced. P-58:
  # measured under `bash` on this host, where `grep`/`sed` are the BSD binaries in /usr/bin;
  # `LC_ALL=C` is on every expression so the same bytes hold if the ugrep shell function
  # (which re-execs with `-I`) is ever in scope instead.
  local floor bodies records
  bodies="$(git -C "$REPO_ROOT" ls-files -z -- .softhouse/capture 2>/dev/null \
           | LC_ALL=C tr '\0' '\n' \
           | LC_ALL=C grep -acE '(/req/[^/]+\.json|\.req)$' || true)"
  records="$(git -C "$REPO_ROOT" grep -h -E '"capture_ref"[[:space:]]*:' -- .softhouse/vectors 2>/dev/null \
           | LC_ALL=C sed -E 's/.*"capture_ref"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/' \
           | LC_ALL=C grep -av '^$' \
           | LC_ALL=C sort -u \
           | LC_ALL=C grep -ac . || true)"
  case "$bodies"  in ''|*[!0-9]*) bodies=0 ;; esac
  case "$records" in ''|*[!0-9]*) records=0 ;; esac
  floor=$((bodies + records))
  _run_capture_guard check_wire_float_roundtrip.py "wire-float round-trip" "$floor"
}

# guard_no_narrow_catch_in_capture_rigs: T169's lint, on the path that runs. A NEW capture
# rig may not wrap the measured seam in `catch (RuntimeException|Exception)` — java.lang.Error
# is exactly what the reference oracle throws, so a narrow handler silently converts a thrown
# outcome into no outcome at all.
#
# READ T169'S SELFTEST BEFORE PROBING THIS ONE (P-52). Cases (b) and (c) deliberately assert
# the lint must NOT be over-broad: a seam handler already widened to Throwable, and a narrow
# catch that is nowhere near the seam, must BOTH pass. A probe that plants a bare
# `catch (Exception e)` with no seam marker inside the try is a BAD PROBE, and reading its
# non-refusal as a vacuous guard is a cycle already burned once in this program.
guard_no_narrow_catch_in_capture_rigs() {
  # THE FLOOR, same derivation, this guard's population: every *.java in the repository
  # except the `.claude/worktrees` checkout root the lint excludes and NAMES
  # [VERIFIED: .softhouse/capture/lib/check_no_narrow_catch.py:104-136]. The exclusion
  # filter below is belt-and-braces — `.claude/worktrees/` is in .gitignore, so `git
  # ls-files` never lists one — and it is written out anyway so that un-ignoring those
  # trees would not silently push the floor above what the lint is willing to walk.
  # Measured in this worktree: guard 57, floor 57 (and 57 on the filesystem).
  local floor
  floor="$(git -C "$REPO_ROOT" ls-files -z -- '*.java' 2>/dev/null \
           | LC_ALL=C tr '\0' '\n' \
           | LC_ALL=C grep -av '^\.claude/worktrees/' \
           | LC_ALL=C grep -ac '\.java$' || true)"
  _run_capture_guard check_no_narrow_catch.py "narrow-catch" "$floor"
}

# guard_graded_root_is_this_tree: the tree the Go binary is about to GRADE must be the tree
# this harness just GUARDED.
#
# THE HOLE (T199 D-1; re-derived from source by T201 before it was fixed, not taken on
# trust). ResolveRepoRoot's precedence is `-repo-root`, then CONFORMANCE_REPO_ROOT, then the
# build anchor — ENV OUTRANKS THE ANCHOR [VERIFIED: nexus/internal/apps/loanschedule/
# conformance/reporoot.go:247 states it, and the switch at :281-294 implements it, testing
# `case envValue != ""` BEFORE `case r.AnchorRoot != ""`]. This script names NEITHER lever:
# `CONFORMANCE_REPO_ROOT` and `-repo-root` each occur ZERO times in it (measured on this
# file with /usr/bin/grep, BSD 2.6.0-FreeBSD, `LC_ALL=C grep -c`; both returned 0, exit 1).
# And lines 402-409 record, deliberately, that the frozen DEC-1 digest gate is delegated to
# the Go binary ALONE. So an exported environment variable moved the graded tree out from
# under every guard in this file AND out from under the digest gate, and the harness had
# nothing whatsoever to say about it.
#
# MEASURED END TO END (T201, this fire, on a tree whose contract.go had a single comment
# line appended and which was reverted and re-hashed to the pin afterwards):
#   bash .softhouse/conformance.sh
#     -> EXIT 2, "frozen contract … digest 4af70fa9… does not match the store pin 0db73d4a…"
#   CONFORMANCE_REPO_ROOT=<clean checkout> bash .softhouse/conformance.sh
#     -> EXIT 0, "parity vectors PASS 43 FAIL 0", "VERDICT: PASS (exit 0) … 5664 cells"
# T165 narrowed this from any accidental `cd` to a deliberate env var and made the second
# run print a five-line `*** OVERRIDE DIVERGES FROM THE COMPILED BYTES ***` banner in the
# report BODY. THE EXIT CODE STAYED 0. The driver, the launchd wrapper and every automation
# in this program read the exit code and the `probe = up|down` line, not the body.
#
# WHY REFUSE. Under THIS script the override can never be legitimate. build_binary compiles
# CMD_PKG from $NEXUS_DIR = $REPO_ROOT/nexus with no -trimpath, so the build anchor IS
# $REPO_ROOT on every run this file performs [MEASURED: the clean baseline report reads
# "resolved from the BUILD ANCHOR" with the anchor inside $REPO_ROOT/nexus]. The env var
# therefore has exactly one available effect here — point the grading away from the tree
# whose corpus, contract digest, no-float census and gofmt state were just checked — so
# refusing it forfeits no capability at all. An operator who genuinely wants another tree
# graded runs THAT tree's own .softhouse/conformance.sh, which then guards what it grades.
#
# REJECTED ALTERNATIVE — accept-and-report with a non-zero exit. Rejected on three counts.
#  (1) THERE IS NO HONEST CODE FOR IT. 1 is this file's GRADED FAIL, "a mismatch or a
#      violated property invariant, a definite reproducible defect"; an automation reading 1
#      would open a defect against the Go port when the fault is the invocation. 2 is what a
#      failed HARD guard already returns and does mean "no verdict is available" — but
#      "grade it anyway, then exit 2" still emits a full `parity vectors PASS 43` table over
#      a foreign tree, and T165 already proved that a banner standing next to those numbers
#      does not stop them being pasted into a handoff as parity evidence.
#  (2) IT MIXES EVIDENCE FROM TWO TREES. run_guards inspects $REPO_ROOT's vectors, capture
#      rigs, Java sources and Go sources; the binary would grade the OTHER checkout's corpus
#      and contract. No reader can afterwards attribute a cell to a tree.
#  (3) THE TEST IS WHAT AN AUTOMATION THAT READS ONLY THE EXIT CODE LEARNS. On refusal it
#      learns "this run produced nothing", which is true. On accept-and-report it learns "43
#      vectors were compared and something was wrong" — false in both halves.
#
# EXIT 2 THROUGH run_guards, and it cannot be misread as an oracle outage: this runs BEFORE
# probe_oracle, so the `reference oracle (…) probe = up|down` line is ABSENT, not `down`,
# and the driver parks only on `exit 2` AND a probe line PRESENT and reading `down`. It is
# the fifth member of the pre-probe exit-2 family already documented at lines 745-747.
guard_graded_root_is_this_tree() {
  local env_root="${CONFORMANCE_REPO_ROOT:-}" graded here
  # Unset or empty: the anchor decides, and the anchor is this tree. Nothing to say, and
  # saying something would be noise on every ordinary run.
  [ -n "$env_root" ] || return 0
  # PHYSICAL paths on BOTH sides. $REPO_ROOT is built by `cd … && pwd`, so a raw string
  # comparison would call a symlinked spelling of the SAME tree a divergence — cry wolf —
  # and would also split on a trailing slash. Each `cd` runs inside a command substitution,
  # i.e. a subshell: the harness's own working directory is never moved. That matters
  # because grading whichever tree the caller stood in is precisely the defect T165 removed,
  # and a guard against it must not reintroduce it.
  graded="$(cd "$env_root" 2>/dev/null && pwd -P)" || graded=""
  here="$(cd "$REPO_ROOT" 2>/dev/null && pwd -P)" || here=""
  if [ -z "$here" ]; then
    warn "conformance: this harness cannot resolve its OWN \$REPO_ROOT ('$REPO_ROOT') to a"
    warn "conformance: physical path, so it cannot be compared with CONFORMANCE_REPO_ROOT."
    warn "conformance: ERROR, not a pass — an unanswerable question is not a clean answer."
    return 1
  fi
  if [ -n "$graded" ] && [ "$graded" = "$here" ]; then
    say "conformance: CONFORMANCE_REPO_ROOT is set and names THIS tree ($here) — no divergence."
    return 0
  fi
  warn "conformance: CONFORMANCE_REPO_ROOT IS SET AND POINTS AWAY FROM THIS HARNESS."
  warn "conformance:   this harness guards:   $here"
  warn "conformance:   the binary would grade: ${graded:-<unresolvable: '$env_root'>}"
  warn "conformance: The frozen DEC-1 digest gate, the vector corpus, the no-float census and"
  warn "conformance: the gofmt state are ALL read from the GRADED root, so this run would"
  warn "conformance: certify a tree that none of the guards in this file inspected — and,"
  warn "conformance: before T201, would have exited 0 while doing it. REFUSED: no verdict is"
  warn "conformance: available. Unset CONFORMANCE_REPO_ROOT, or run the other checkout's own"
  warn "conformance: .softhouse/conformance.sh so that what is guarded is what is graded."
  return 1
}

# guard_ledger_invariants: the I-3/I-4 SOURCE GUARD that DEC-2 §4.4 requires — "balances are
# DERIVED, never written" (I-3) and "the ledger is append-only" (I-4), both first-tier CLAUDE.md
# non-negotiables. It declares SEVEN detection classes [VERIFIED: .softhouse/guards/ledgerguard/
# main.go, the `Class: "..."` literals — I3-FIELD-WRITE, I3-PKG-STATE, I3-SQL-BALANCE, I4-BUILDER,
# I4-DML, I6-HOLD-BALANCE, OPAQUE-SQL]. Its own PASS text, printed by this function below, states
# the limit precisely: "no violation is visible to a source-level guard over the Go tree" — NOT
# "the ledger tree is covered". DEC-2 §4.4 once recorded this guard as not existing — that was
# revision 2, true when written; DEC-2 §8.3 has since retracted it, and §4.4.1 and §8.1 fact 3
# describe the guard as it runs today, with the same PASS-text limit quoted above. A2-18 (commit
# 2a3eefd) BUILT and PROVED it
# and deliberately did not wire it, because T201 held this file the same fire; T208 is that
# wiring. Between those two commits the guard existed and enforced NOTHING at grade time, which
# is the P-22 failure this program keeps finding: a guard that only fails when invoked by hand.
#
# WHY NOT _run_capture_guard. Measured, not assumed: that helper resolves its script under
# "$REPO_ROOT/.softhouse/capture/lib/$1" (its first line), and this guard does not live there.
# It also demands a caller-derived population floor and parses the census itself — machinery
# this guard's own head already carries, and carries differently: the head derives its floor
# from `git ls-files` (the index) while the guard walks the filesystem, two programs over one
# population, and it PARSES the census figure rather than testing for its presence (T194).
# Duplicating that here would give one census two graders that could disagree.
#
# EXIT SEMANTICS — NOTHING TO CHANGE, AND NOTHING WAS CHANGED. The head returns 0 clean, 1 on
# refusal (a violation found, a census below its derived floor, no census at all, or a selftest
# that did not show BOTH polarities), 2 unusable (no Go toolchain, guard source missing, guard
# did not compile). run_guards maps ANY non-zero to failed=1 and then exits EXIT_UNUSABLE — the
# correct reading: a failed HARD guard means no verdict is available, not a FAIL verdict.
#
# THIS IS NOW A MEMBER OF THE PRE-PROBE EXIT-2 FAMILY (lines 745-747, 1043-1044). It runs
# BEFORE probe_oracle, so a ledger refusal exits 2 with the `reference oracle (…) probe = up|down`
# line ABSENT — not `down`. Oracle-down is exit 2 AND a probe line PRESENT AND reading `down`;
# test the line's PRESENCE first, or a balance write gets parked as an outage. Diagnosability on
# that path is the head's job and it does it: on a refusal it dumps the guard's full output to
# stderr — class, file and line — so the transcript says which invariant broke and where.
#
# IT IS NOT REACHED UNDER T201's REFUSAL, AND THAT IS DELIBERATE. guard_graded_root_is_this_tree
# short-circuits with `exit` before this line, so a run whose CONFORMANCE_REPO_ROOT points away
# still prints its eleven lines and nothing else. Correct: this guard's result would describe a
# tree the run was not going to grade. T208 verified that after wiring rather than assuming it.
#
# COST: 2.8-2.9 s wall, measured twice by T208 on this host (2.776 s, 2.912 s), agreeing with
# A2-18's 2.8 s — a `go build` of a dependency-free module, 15 selftest cases, one walk of
# nexus/. TRANSCRIPT COST — T208 recorded 26 lines (18 head + the 8 below) against a then
# 172-line green transcript. ⚠ CORRECTION (T227): T209 widened the head's pass-path filter, so
# the 33-line CANNOT-CATCH block now prints too. MEASURED on this branch's green run, not
# estimated: 62 lines of a 284-line transcript — 18 head lines before the block (selftest, two
# CENSUS headers, five covered-package lines, six DML-classified literals, one hold-named func,
# two NIL-COVERAGE notices, the census-figure-READ line), 33 CANNOT-CATCH lines, 3 PASS-text
# lines, and the 8 below. Recount it before quoting it; every figure in this paragraph has now
# been stale once.
guard_ledger_invariants() {
  local rc=0
  bash "$REPO_ROOT/.softhouse/guards/check-ledger-invariants.sh" || rc=$?

  # THE LIMITS MUST TRAVEL WITH THE VERDICT. THEY NOW ARRIVE TWICE, AND THAT IS THE STATE.
  #
  # HISTORY, KEPT BECAUSE IT EXPLAINS WHY THESE EIGHT LINES EXIST. T208 measured, correcting
  # A2-18's §7 as written, that the guard binary prints a 33-line CANNOT-CATCH block on every
  # one of ITS runs while its head, on the PASS path, re-printed only `^CENSUS ` and
  # `^NIL-COVERAGE ` lines. So the two NIL-COVERAGE notices reached this transcript verbatim
  # (this Go tree has no DB driver and no SQL, so the I-4 SQL classes are proven by the guard's
  # selftest and NOT by this tree) but the CANNOT-CATCH block did not — and did not standalone
  # either, so wiring was not what dropped it. T208 raised that as FU-T208-1 rather than fixing
  # a file outside its scope, and printed the 8-line condensation below meanwhile, stating the
  # trade rather than taking it silently: 8 lines naming the load-bearing limits, against 33.
  #
  # ⚠ CORRECTION (T227, 22 August 2026). FU-T208-1 IS CLOSED — T209 (commit 03e9094) widened
  # the head's pass-path filter, so the full 33-line block DOES reach every green transcript
  # [VERIFIED: check-ledger-invariants.sh, the `if [ "$rc" -eq 0 ]` awk extraction after the
  # `^CENSUS |^NIL-COVERAGE ` grep; and MEASURED on this branch's green run, where the block
  # prints in full immediately ABOVE these eight lines]. Until this correction the say line
  # below still named FU-T208-1 as an available fix and still said the head "DROPS" the block
  # on the pass path — a caveat outliving its defect, printed on every run, three lines under
  # the very block it claimed was absent. Same failure class A2-31 rejected DEC-2 rev 4 for.
  #
  # WHAT IS NOT DECIDED HERE. These eight lines are now a REDUNDANT condensation of a block the
  # transcript already carries in full. T209 raised that as FU-T209-1 and it is still open;
  # removing them changes the harness's OUTPUT, which is not a comment-only change and is not
  # T227's scope. They stay, correctly labelled, until FU-T209-1 is worked. Printed on BOTH
  # paths, pass or fail.
  # THE "33-LINE" FIGURE IS NOW READ FROM THE CONST, NOT TYPED BESIDE IT. [T300] It was ACCURATE
  # when T300 measured it (main.go:745-777 inclusive = 33 lines), and that is why it was
  # repaired: it is a cardinal about a collection in a file THIS SCRIPT DOES NOT OWN, restated
  # here, one edit away from being wrong on every run — P-80's shape ("A CORRECTED CARDINAL ROTS
  # IN EVERY PLACE IT WAS RESTATED. The count is the same defect as the line number"). The
  # paragraph above already says so in its own words: "Recount it before quoting it; every
  # figure in this paragraph has now been stale once."
  #
  # READ FROM THE SOURCE, NOT FROM THE BINARY'S OUTPUT, and the distinction is the claim being
  # made: this sentence asserts how big the CONST is, not how much of it the head's pass-path
  # filter let through. Counting what got printed would make the figure agree with a filter that
  # dropped half the block.
  #
  # PIPELINE, DELIBERATELY, AND IT IS THE ONE P-57 ENDORSES: the consumer is `grep -c`, which
  # DRAINS its input, so there is no early exit for `set -o pipefail` to invert ("Use grep -c
  # (consumes all input) and test the count"). A Go raw string cannot contain a backtick, so the
  # first line ending in one after the opener is the terminator.
  #
  # A DERIVATION THAT FAILS SAYS SO WHERE THE NUMBER WOULD HAVE BEEN. It does not fall back to a
  # figure and it does not fall back to 0. It does NOT change this guard's exit code either, and
  # that is a decision, not an oversight: the graded property here is the ledger walk's verdict,
  # and turning a rename of a documentation const into EXIT 2 for the whole bar would make the
  # run's colour depend on a doc string. The failure is loud instead — a warn on stderr and the
  # words NOT DERIVABLE printed inline, which no reader of the transcript can mistake for 33.
  local ccsrc="$REPO_ROOT/.softhouse/guards/ledgerguard/main.go" cc ccsize
  cc="$(LC_ALL=C sed -n '/^const cannotCatch = `/,/`$/p' "$ccsrc" | LC_ALL=C grep -ac '')"
  case "$cc" in ''|*[!0-9]*) cc=0 ;; esac
  if [ "$cc" -lt 2 ]; then
    ccsize="line count NOT DERIVABLE"
    warn "conformance: the CANNOT-CATCH block's size did not derive from $ccsrc — the"
    warn "conformance: \`const cannotCatch = \` opener was not found at its expected shape. The"
    warn "conformance: limits line below prints NOT DERIVABLE rather than a number that would be"
    warn "conformance: a guess. The ledger verdict itself is unaffected and is reported as measured."
  else
    ccsize="full $cc-line block"
  fi
  say "conformance: ledger-invariants LIMITS (CANNOT-CATCH, condensed; the $ccsize is"
  say "conformance:   the cannotCatch const in .softhouse/guards/ledgerguard/main.go, which its"
  say "conformance:   head prints IN FULL ABOVE since T209 — so this is a redundant restatement):"
  say "conformance:   the detection surface is the NAME, so RENAMING A BALANCE DEFEATS THIS GUARD;"
  say "conformance:   dynamic SQL is caught only through the call set it recognises; triggers,"
  say "conformance:   migrations and stored procedures are not walked at all; I-5's semantic half"
  say "conformance:   and non-Go callers are not covered. A PASS here means 'no violation is visible"
  say "conformance:   to a source-level guard over the Go tree', NOT 'the ledger tree is covered'."
  return "$rc"
}

# ---------------------------------------------------------------------------
# guard_no_fail_open_instruments: T238's FAIL-OPEN LINTER, WIRED.
#   [T243, closing T238 handoff §8 item 1 — which would otherwise have been the
#    FIFTH instance of P-45 in this program]
# ---------------------------------------------------------------------------
# T238 built a three-tier linter for the fail-OPEN dead-`cd` class and could not
# wire it, because this file was held by T243 and T226. It shipped saying so:
# "Nobody may cite it as an enforced control until it is wired." This is the
# wiring, and the guard below is DRIVEN RED through this route before it is
# claimed — a planted fail-open instrument turns a graded run to EXIT 2, and
# removing it turns the run back green (transcript:
# .softhouse/capture/t243-wiring/transcripts/20-failopen-red-drive.txt).
#
# WHY NOT T238's OWN CALL LINE, `python3 …/50-failopen-lint.py || return 1`.
# Because MEASURED at 693c768 the linter exits 1 on the tree it shipped into:
# NINE instruments are on its frontier, two Tier-1 and seven Tier-2. Wiring the
# refusal literally would make every graded run in this program EXIT 2 until
# nine files across four other tasks' FROZEN EVIDENCE directories were edited,
# and one of them must never be repaired at all —
# `evidence/red-drive/sweep-ORIGINAL.sh` is T238's preserved SPECIMEN of the
# defect, pinned by a literal sha256 that its own red drive asserts (P-24).
# Two ways out were available and only one is honest:
#   (a) narrow the linter's scope until it goes green — that is weakening a gate
#       to make the wiring easy, and it is forbidden;
#   (b) run the linter over the WHOLE tree, every run, and gate the FRONTIER for
#       EQUALITY against a pin held here. Nothing that is admissible today
#       becomes inadmissible, nothing inadmissible becomes admissible, and a
#       instrument BEYOND the pinned set — or a swap that keeps the total the
#       same — refuses. [T248: that set was nine when T243 wrote this and became
#       TEN. T252 made it ELEVEN. The count lives in FAILOPEN_PIN_FILE_LIST and
#       in the `say` line below, never in this prose — and the ONE place a stale
#       copy of it is known to survive is named in the T252 block at the bottom
#       of this comment, because "not found" would be a statement about my
#       search rather than about the tree (P-66/P-70).]
# (b) is what is implemented, and it is the same idiom as EXEMPTION_PIN_*
# twenty lines up: a population that can drift in both directions is pinned by
# IDENTITY, and moving it is a source edit a reviewer reads.
#
# THE PIN IS ALREADY EVIDENCE. T238's committed `evidence/lint.json` records
# THREE Tier-2 instruments. There are SEVEN. Five arrived with T239 in the same
# fire, after T238's measurement and before this wiring, and nothing noticed —
# which is the drift this gate exists to stop, observed once before it was
# switched on.
#
# FAIL-CLOSED, three ways, because this guard is about instruments that emit a
# negative they did not measure and it must not be one:
#   * the linter's own BANNER must be present in the output. A `cd` that failed,
#     a python that was not there, a linter that was deleted — all of those give
#     an empty or foreign output, and an empty frontier would otherwise read as
#     "no fail-open instruments", the exact reading this whole class produces;
#   * the linter's CORPUS line must report a non-zero file count (P-35);
#   * the linter's exit code must be 0 or 1. 2 is its own "could not reach the
#     corpus" refusal and anything else is a crash; both refuse here.
# NO PIPELINE ANYWHERE IN IT (P-57): the linter's output goes to a FILE and
# every read below is a `sed`/`grep` over that file.
#
# T248 -- THE FRONTIER MOVED, AND THAT IS THE POINT. [P-76]
#
# The driver drove THIS guard red and it DID NOT FIRE. T243's red drive planted the shape
# T238 wrote the rule FROM, so it proved the wiring and said nothing about the coverage.
# The second confirmed live site of the class -- `.softhouse/reviews/T138-evidence/
# r11-hygiene.sh:77-79`, the site T239 measured LIVE and the site that caused T238's brief
# to be widened in the first place -- was flagged ZERO times, because its reassurance is an
# UNCONDITIONAL echo on the next line rather than a `|| echo` arm, and because its dead path
# is `/tmp/T138-merge` while C1 only ever watched four roots (/Users /home /opt /var --
# MEASURED black-box, .softhouse/capture/t248-failopen-widen/transcripts/10-c1-characterise.txt).
# BOTH halves had to move: widening C2 alone was measured to land r11-hygiene.sh on the
# frontier at TIER 2, i.e. asserting "corpus reachable today" about a directory that has not
# existed for days (transcript 20, variant V1).
#
# THE ROW BELOW IS NEWLY VISIBLE, NOT NEWLY INTRODUCED, and the difference matters:
#   +TIER1 .softhouse/reviews/T138-evidence/r11-hygiene.sh
# The file is unchanged and has been fail-open since T138. What changed is that the linter
# can now see it. NOTHING was reclassified and NOTHING was lost -- the widening is proved
# ADDITIVE by running the shipped linter and the widened one over the same tree and diffing
# every detection (transcripts/30-additivity.txt: 20 detections -> 22, LOST = none).
#
# THE PIN REMAINS A FRONTIER, NOT AN AMNESTY. `sweep-ORIGINAL.sh` stays on it PERMANENTLY --
# it is T238's preserved SPECIMEN of the defect and repairing it would destroy the evidence.
# The other nine are unrepaired instruments in other tasks' frozen evidence directories, and
# `r11-hygiene.sh` now joins them on exactly those terms: recorded, visible, and refusing to
# grow. T248 did not touch any of the ten; that would be repairing files outside its scope.
#
# T252 -- THE FRONTIER IS ELEVEN, AND THE ELEVENTH IS A CONFIRMED LIVE FAIL-OPEN. [P-76]
#
# T248 reported a PROBABLE third live site and left the hedge unresolved. T252 resolved it by
# RUNNING it rather than reading it (.softhouse/capture/t252-tier3/transcripts/10-verify-third-
# site.txt): `.softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh` exits **0**, prints
# `PROMOTED CELLS SWEPT: 0   NOT BYTE-PRESENT / ARITHMETIC FAIL: 0`, and reached no corpus at
# all -- its worktree was pruned, its `cd "$R"` at :24 runs under `set -u` with no `-e` and no
# `||`, and its own P-72 calibration printed an EMPTY count and did not stop it. This row is
# therefore NEWLY VISIBLE, NOT NEWLY INTRODUCED, exactly as r11-hygiene.sh was: the file is
# unchanged and has been fail-open since its worktree died. What changed is that the linter
# can now see it.
#   +TIER1B .softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh
#
# WHY A NEW TIER RATHER THAN A WIDER VOCABULARY. Its false claim is a COUNT, not a sentence,
# and the obvious remedy -- teaching RE_REASSURE to recognise count shapes -- was BUILT AND
# MEASURED and is INERT: frontier 10 -> 10, GAINED 0, LOST 0, site still invisible
# (transcripts/20-numeric-vocab-probe.txt). It fails for two independent reasons: the print
# predicate is shell-only and the claim is a python `print(`, and the association window is 3
# code lines while the claim is 110 code lines downstream. C6 keys on CONTROL FLOW instead --
# entering a directory that is not there and not stopping -- and reads no output words at all,
# which is why it also catches a claim whose type is an EMPTY JSON LIST (red drive R7).
#
# ADDITIVE, PROVEN THE WAY T248 PROVED IT (transcripts/30-additivity.txt): shipped and widened
# linter over the same tree, detections keyed on (file, code, line) out of each run's JSON.
# 83 -> 86 detections, **LOST = none**, frontier 10 -> 11 rows, LOST = none. NO PINNED ROW
# MOVED -- all ten were re-checked tier-for-tier and every one is unchanged. C6 additionally
# fires on sweep-ORIGINAL.sh:14 and r11-hygiene.sh:77, which is corroboration rather than
# reclassification: both stay TIER1 because a file already on the frontier is never moved by
# new evidence about it.
#
# A STALE COPY OF THE OLD COUNT SURVIVES, AND IT IS NAMED HERE RATHER THAN LEFT TO BE FOUND.
# `.softhouse/capture/t243-wiring/instruments/20-failopen-red-drive.sh:74,152` assert
# `frontier == pinned (all 9 rows, by path).` That instrument has been wrong since T248 moved
# the frontier to ten -- T248 corrected the number where it is NAMED (this file) and not where
# it is RESTATED, which is the P-66 defect at program scale. T252 does not repair it: that
# file is outside T252's scope and repairing another task's instrument unasked is the error
# this program keeps punishing. It is recorded in T252's handoff as a follow-up.
FAILOPEN_PIN_FILE_LIST="TIER1 .softhouse/capture/t238-failopen/evidence/red-drive/sweep-ORIGINAL.sh
TIER1 .softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-32-evidence/sweep.sh
TIER1 .softhouse/reviews/T138-evidence/r11-hygiene.sh
TIER1B .softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh
TIER2 .softhouse/capture/t234-sweep-instrument-audit/instruments/00-engine-baseline.sh
TIER2 .softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh
TIER2 .softhouse/capture/t239-r11-rerun/instruments/00-engines.sh
TIER2 .softhouse/capture/t239-r11-rerun/instruments/10-population.sh
TIER2 .softhouse/capture/t239-r11-rerun/instruments/31-coverage.sh
TIER2 .softhouse/capture/t239-r11-rerun/instruments/50-red-drive.sh
TIER2 .softhouse/capture/t239-r11-rerun/instruments/51-run-r11-verbatim.sh"

guard_no_fail_open_instruments() {
  local lint="$REPO_ROOT/.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
  if [ ! -f "$lint" ]; then
    warn "conformance: THE FAIL-OPEN LINTER IS ABSENT: $lint"
    warn "conformance: it is wired into this guard, so its absence is a refusal and never a pass."
    return 1
  fi
  local out json want got rc corpus n p
  out="$(mktemp "${TMPDIR:-/tmp}/conformance-failopen.XXXXXXXXXX")"      || return 1
  json="$(mktemp "${TMPDIR:-/tmp}/conformance-failopen-json.XXXXXXXXXX")" || return 1
  want="$(mktemp "${TMPDIR:-/tmp}/conformance-failopen-want.XXXXXXXXXX")" || return 1
  got="$(mktemp "${TMPDIR:-/tmp}/conformance-failopen-got.XXXXXXXXXX")"   || return 1

  # The JSON is diverted to scratch. The linter's default destination is a
  # TRACKED file, and a harness that rewrote a tracked file on every graded run
  # would dirty the tree it is grading.
  ( cd "$REPO_ROOT" && FAILOPEN_LINT_JSON="$json" python3 "$lint" ) >"$out" 2>&1
  rc=$?

  if ! LC_ALL=C grep -aqF 'T238 FAIL-OPEN LINT' "$out"; then
    warn "conformance: the fail-open linter produced no banner (exit $rc). It did not run, or did not"
    warn "conformance: finish. An empty frontier from a linter that never ran reads exactly like a"
    warn "conformance: clean tree, which is the defect this guard exists to refuse."
    LC_ALL=C sed -n '1,12p' "$out" >&2
    rm -f "$out" "$json" "$want" "$got"
    return 1
  fi
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
    warn "conformance: the fail-open linter exited $rc, which is neither its clean (0) nor its"
    warn "conformance: violations (1) code. 2 is its own corpus refusal; anything else is a crash."
    LC_ALL=C sed -n '1,12p' "$out" >&2
    rm -f "$out" "$json" "$want" "$got"
    return 1
  fi
  corpus="$(LC_ALL=C sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p' "$out")"
  [ -n "$corpus" ] || corpus=0
  if [ "$corpus" -lt 1 ]; then
    warn "conformance: the fail-open linter reports a corpus of $corpus tracked .sh/.py files."
    warn "conformance: a linter that inspects nothing passes everything. This is an ERROR, not a pass."
    rm -f "$out" "$json" "$want" "$got"
    return 1
  fi

  LC_ALL=C sed -n 's/^FAILOPEN-FRONTIER //p' "$out" >"$got.raw"
  LC_ALL=C sort "$got.raw" >"$got"
  printf '%s\n' "$FAILOPEN_PIN_FILE_LIST" >"$want.raw"
  LC_ALL=C sort "$want.raw" >"$want"
  n="$(LC_ALL=C grep -ac '' "$got" || true)"
  [ -n "$n" ] || n=0

  # THE PIN CARDINAL IS DERIVED, for the same reason and by the same means as the host-state
  # census two hundred lines down. [T300] This one was ACCURATE on the day it was swept, and
  # that is precisely why it was repaired rather than left: it is a typed count sitting beside a
  # list whose length it restates, and this exact figure HAS already rotted once — T248 moved the
  # frontier 9 -> 10, T252 moved it 10 -> 11, and T252 found t243-wiring/instruments/
  # 20-failopen-red-drive.sh still asserting `frontier == pinned (all 9 rows, by path)` in two
  # live want_line checks (P-80 — "A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED...
  # The fix is never the new number — it is to make the second site READ the first"). Waiting for
  # the third move before deriving would buy exactly one cycle.
  p="$(LC_ALL=C grep -ac '' "$want")"
  case "$p" in ''|*[!0-9]*) p=-1 ;; esac
  if [ "$p" -lt 0 ]; then
    warn "conformance: the fail-open PIN CARDINAL did not derive from FAILOPEN_PIN_FILE_LIST. A"
    warn "conformance: frontier that cannot count its own pin may not print a figure beside it,"
    warn "conformance: and a fallback zero would read as 'nothing is pinned'. REFUSED."
    rm -f "$out" "$json" "$want" "$want.raw" "$got" "$got.raw"
    return 1
  fi
  say "conformance: CENSUS fail-open instruments — inspected $corpus tracked .sh/.py file(s) under"
  say "conformance:   $REPO_ROOT (git ls-files, whole repository); frontier $n, pinned at $p"
  say "conformance:   (DERIVED from FAILOPEN_PIN_FILE_LIST by counting it, never typed)."
  say "conformance:   TIER1 = dead path AND a printing failure arm (fail-open, live). TIER1B = enters a"
  say "conformance:   directory that is not there and carries on, whatever it prints afterwards. TIER2 ="
  say "conformance:   printing arm only, corpus reachable today. All are pinned by PATH, not by count."
  if ! diff -u "$want" "$got" >"$out.diff" 2>&1; then
    warn "conformance:"
    warn "conformance: THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER (- pinned, + measured):"
    LC_ALL=C sed -n '3,60p' "$out.diff" >&2
    warn "conformance:"
    warn "conformance: A '+' line is a NEW instrument that can print a negative it did not measure —"
    warn "conformance: repair it (T238's sweeplib.sh is the adoptable shape) rather than pinning it."
    warn "conformance: A '-' line is an instrument that was REPAIRED or DELETED: that is good news, and"
    warn "conformance: the pin must lose the row IN THE SAME COMMIT, or the pin starts excusing a"
    warn "conformance: weakness that is no longer there."
    warn "conformance: The pin is FAILOPEN_PIN_FILE_LIST in .softhouse/conformance.sh."
    warn "conformance: EXIT 2 — no verdict is available. This is NOT a pass."
    rm -f "$out" "$out.diff" "$json" "$want" "$want.raw" "$got" "$got.raw"
    return 1
  fi
  say "conformance:   frontier == pinned (all $n rows, by path)."
  rm -f "$out" "$out.diff" "$json" "$want" "$want.raw" "$got" "$got.raw"
  return 0
}


# ---------------------------------------------------------------------------
# guard_pnumber_citations: A CITED P-NUMBER MUST CARRY ITS OWN RULE'S SENTENCE.
# [T282 built and drove it; T331 wired it.]
# ---------------------------------------------------------------------------
# T282 — P-NUMBER CITATION DRIFT.  The predicate is the SENTENCE, never the id:
# a guard asking only "is P-n defined?" returns PASS on every recorded instance
# of this defect, because every drifted citation names an id that EXISTS.
# Demonstrated at .softhouse/capture/t282-pnumber-drift/red/20-existence-only-on-RED.txt.
#
# ===========================================================================================
# WIRED HARD, AND HERE IS THE ARGUMENT.  T331 was told not to inherit the tier, so it did not.
# ===========================================================================================
# THE OBJECTION, STATED AT ITS STRONGEST.  This defect's measured materiality was LOW twice,
# and for a specific reason: every prompt wrote the full rule text beside the id, so the number
# was decoration and the sentence carried the instruction. Not one worker was ever misdirected.
# A HARD guard exits 2 BEFORE the probe line prints. Does a citation-drift defect deserve that?
#
# FOUR MEASUREMENTS, taken by T331 at .softhouse/capture/t331-wire-pnumber-checker/out/, not
# reasoned about:
#
#  (1) THE BRIEF'S PREMISE ABOUT THE SIGNAL IS FALSE, and P-84's own text refutes it. P-84 is
#      "EXIT 2 WITH NO PROBE LINE" IS THE GUARD WORKING — READ THE ABSENCE, NOT THE VALUE:
#      it separates a HARD-guard refusal from an ORACLE OUTAGE, and says nothing about money.
#      The instance it was written from was p5-probe.sh moving the fail-open frontier 10 -> 11
#      — an instrument-hygiene guard of exactly this guard's class, not a money violation.
#      Eleven guards above already share this exit; gofmt is one of them.
#
#  (2) THERE IS NO SOFT TIER IN THIS FILE, AND INVENTING ONE IS THE DEFECT. A SOFT wiring
#      prints a line that nothing depends on — P-22, "a guard, a canary, or a control that
#      cannot fail is worse than none, because it is believed". That sentence is already the
#      argument this file records at the T323 block below, and a line scrolling past in a
#      3,800-line report is T165 verbatim: the true statement was in the output and the reader
#      took the summary instead.
#
#  (3) THE CHECKER IS ALREADY TWO-TIERED, so a SOFT wiring would be a THIRD tier that deletes
#      the second. Its REPORT tier is generous and prints on every run (81 findings today, in
#      committed evidence, ratified ADRs and orchestrator-owned files — all corrected FORWARD
#      in the patterns.md errata, never edited in place). Its FATAL tier is the DIRECTIVE zone
#      alone, which is the only class that is BOTH read as instruction by workers not yet born
#      AND lawfully repairable in place by an ordinary task. Wiring SOFT obtains the reporting
#      that wiring at all already obtains, and forfeits the only thing the tiers were built for.
#
#  (4) T326's LESSON CANNOT BITE HERE, and that was checked rather than hoped. "WIRING A GUARD
#      HARD IS THE FIRST TIME ANYONE FINDS OUT WHETHER ITS PIN IS A MEASUREMENT OR A SNAPSHOT
#      OF SOMEBODY'S DISK" — this guard HAS NO PIN. It derives its register from patterns.md
#      and its corpus from `git ls-files -z` [VERIFIED: check-pnumber-citations.py:719], never
#      from the disk, so the four-disk-conditions failure that aborted T323's first merge of
#      the frontier guard has no purchase on it.
#
# RESIDUAL RISK, MEASURED AND STATED SO IT IS NOT REDISCOVERED AS A SURPRISE — this is the real
# cost of HARD and it is not small. With the zone restriction LIFTED the fatal predicate fires
# on 41 of 9,016 sites tree-wide, of which only 10 are filed TRUE-DRIFT; 28 of the other 31 are
# in raw SWEEP OUTPUTS — dumps of citations gathered from elsewhere, where a citation is a
# MENTION and not a claim. So the DIRECTIVE zone is doing 100% of the work of keeping this
# guard honest, and the fatal scorer alone would be ~76% false positives.
# In the directive zone today: 6 findings, 0 fatal. The CLOSEST is IN THIS VERY FILE — the
# `P-66/P-70` citation in guard_no_host_state_in_lint_corpus's STATED SCOPE paragraph below,
# named by its text and not by its ordinal because inserting this block moved it :1866 -> :2008
# and a line number into a moving file is the same defect as a stale count. It scores 8 against
# a fatal floor of 9, ONE POINT below firing, and T331 adjudicated it a FALSE POSITIVE: it cites
# `P-66/P-70 — "not found" is a statement about the search`, which is CORRECT [VERIFIED:
# patterns.md defines P-70 as four ways this program stated a search result as a world fact, and
# restates "P-66 / P-70 — 'not found' is a statement about the search" verbatim], and the
# extractor merely swept the gloss past the citation's own sentence into the paragraph beneath
# it about population and corpus — which is P-76's subject, not P-70's.
# IT IS DELIBERATELY LEFT ALONE. Rewording a correct citation to move a heuristic score is
# fitting the tree to the guard, and this file already records that clearing a guard by removing
# its subject is the move a reviewer should distrust most.
# FILED: FU-T331-1 (the margin) and FU-T331-2 (MISDIRECTING has no declaration escape hatch, so
# a false positive inside patterns.md can only be answered by rewording the register of record).
#
# FAIL-CLOSED DIRECTION, FOR THIS GUARD ALONE: it fails closed towards "a DIRECTIVE file states
# one rule's sentence under another rule's number, near-verbatim, and states the cited rule not
# at all". It asserts nothing about evidence, nothing about ratified ADRs, nothing about
# orchestrator-owned files — P-31, never snapshot a file the orchestrator is actively editing —
# and nothing about whether an id merely exists.
#
# EXIT SEMANTICS, never conflated: 0 = no directive-zone fatal finding; 1 = there is one;
# 3 = the checker's own refusal to run (register unreadable, `git ls-files` failed). run_guards
# folds ANY non-zero into failed=1 and exits EXIT_UNUSABLE — "no verdict is available", never
# "FAIL".
#
# COST, WALL CLOCK, MEASURED ON THIS HOST BY T331 over a ~9,200-site corpus — not estimated:
#     --selftest (11 synthetic fixtures, reads no repo file)                0.14 s
#     the graded run (git ls-files, whole tree, sentence scoring)          17.26 s
#     TOTAL ADDED TO EVERY GRADED RUN                                      ~17.4 s
# That makes it the SECOND most expensive guard in this file, after guard_reconciler_ownership
# (30.3 s). The selftest is 0.8% of that and is not optional: a checker whose predicate has
# stopped discriminating reports a clean tree in exactly the same words as a clean tree.
#
# A TENSION, STATED RATHER THAN QUIETLY RESOLVED. T282's anchor 2 puts this call in the FIRST
# guard block, which is in historical order, so 17.4 s is now paid BEFORE guard_capture_namespace
# (0.4 s) and guard_dead_path_frontier (1.3 s) — and the T323 block below says in terms that its
# three are "registered CHEAPEST FIRST so a fast refusal prints before the 30-second one is paid
# for". T331 kept T282's position anyway: the wiring is then auditable line-for-line against the
# diff T282 published, and the cost of the wrong order is 1.7 s on runs that were going to refuse
# regardless. If a reviewer disagrees the fix is to move ONE LINE below guard_dead_path_frontier;
# nothing else depends on the position.
# ---------------------------------------------------------------------------
guard_pnumber_citations() {
  local chk="$REPO_ROOT/.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py"
  if [ ! -f "$chk" ]; then
    warn "conformance: THE P-NUMBER CITATION CHECKER IS ABSENT: $chk"
    warn "conformance: it is wired into this guard, so its absence is a REFUSAL and never a pass."
    return 1
  fi
  # THE INTERPRETER IS CHECKED BY NAME, SEPARATELY FROM THE SELFTEST.  T331 addition, and it is
  # a diagnosis fix rather than a strength change: without it an absent python3 makes the
  # subshell below exit 127 and this guard reports "FAILED ITS OWN SELFTEST" — fail-closed, but
  # naming the wrong cause. Same shape and same refusal as guard_reconciler_ownership.
  if [ ! -x /usr/bin/python3 ]; then
    warn "conformance: guard_pnumber_citations: /usr/bin/python3 is absent. The checker cannot"
    warn "conformance: run. It REFUSES rather than degrading to a smaller green."
    return 1
  fi
  local out rc
  out="$(mktemp "${TMPDIR:-/tmp}/conformance-pnumber.XXXXXXXXXX")" || return 1

  # SELFTEST FIRST. A checker whose predicate has stopped discriminating would
  # report a clean tree in exactly the same words as a clean tree (P-22: a guard,
  # a canary, or a control that cannot fail is worse than none, because it is
  # believed).
  if ! ( cd "$REPO_ROOT" && /usr/bin/python3 "$chk" --selftest ) >"$out" 2>&1; then
    warn "conformance: the P-number citation checker FAILED ITS OWN SELFTEST. Its verdict on this"
    warn "conformance: tree is worthless until that is fixed."
    LC_ALL=C sed -n '1,20p' "$out" >&2
    rm -f "$out"; return 1
  fi

  ( cd "$REPO_ROOT" && /usr/bin/python3 "$chk" ) >"$out" 2>&1
  rc=$?

  # PRESENCE BEFORE VALUE (P-84: "exit 2 with no probe line" is the guard working
  # — read the ABSENCE, not the value). A verdict line that was never PRINTED is a
  # crash, and it must never be read as a clean run.
  if ! LC_ALL=C grep -aqE '^PNUMBER-CITATIONS: VERDICT ' "$out"; then
    warn "conformance: the P-number citation checker printed NO VERDICT line (exit $rc). It did not"
    warn "conformance: run, or did not finish. Silence here reads exactly like a clean register."
    LC_ALL=C sed -n '1,20p' "$out" >&2
    rm -f "$out"; return 1
  fi
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
    warn "conformance: the P-number citation checker exited $rc, which is neither clean (0) nor"
    warn "conformance: violations (1). 3 is its own refusal-to-run; anything else is a crash."
    LC_ALL=C sed -n '1,20p' "$out" >&2
    rm -f "$out"; return 1
  fi

  LC_ALL=C grep -aE '^PNUMBER-CITATIONS: (register|sites|skipped|declared|  )' "$out" \
    | while IFS= read -r l; do say "conformance:   $l"; done
  if [ "$rc" -ne 0 ]; then
    warn "conformance: A CITED P-NUMBER CARRIES A RULE SENTENCE THAT patterns.md DEFINES UNDER A"
    warn "conformance: DIFFERENT NUMBER, in a DIRECTIVE file — a file that instructs future workers."
    LC_ALL=C grep -aE '^PNUMBER-CITATIONS: (FATAL|VERDICT)' "$out" >&2
    warn "conformance: The remedy is to write the sentence the rule wants: correct the id, or state"
    warn "conformance: the cited rule. EXIT 2 — no verdict is available. This is NOT a pass."
    rm -f "$out"; return 1
  fi
  say "conformance:   P-number citations: VERDICT PASS (evidence-zone drift is REPORTED, never"
  say "conformance:   fatal, and is corrected FORWARD in the patterns.md errata — never in place)."
  rm -f "$out"
  return 0
}
# ---------------------------------------------------------------------------
# guard_no_host_state_in_lint_corpus: THE FAIL-OPEN FRONTIER MUST BE A PROPERTY
# OF THE TREE AND NOT OF THIS MAC'S /tmp.  [T273]
# ---------------------------------------------------------------------------
# EVERY GREEN BAR THIS PROGRAM RECORDED BEFORE T273 WAS CONTINGENT ON A 24-BYTE
# FILE IN /tmp THAT NO COMMIT CONTAINED. Measured on merged main by the driver, and
# again first-hand in T273's own worktree, both directions, same tree, changing only
# whether `/tmp/t234_matrix2.txt` existed
# (.softhouse/capture/t273-residue/evidence/10-PREFIX-reproduction.txt):
#
#     residue PRESENT -> frontier 11 rows, ...02-escape-matrix-fix.sh at TIER2,
#                        frontier == pinned, VERDICT: PASS, exit 0, probe line count 1
#     residue ABSENT  -> frontier 11 rows, ...02-escape-matrix-fix.sh at TIER1,
#                        frontier != pinned, EXIT 2, PROBE LINE COUNT 0
#
# The count was 11 in both arms and the PATH SET was identical in both arms. What
# differed was the TIER TOKEN, and the pin carries the tier token, so the guard above
# refused — correctly. The mechanism: `02-escape-matrix-fix.sh` declared
# `C=/tmp/t234_matrix2.txt` and created it on the NEXT LINE through `> "$C"`. The
# linter's C1 rule reads the literal and asks `os.path.exists`; its ownership filter
# looks for a literal `> /tmp/t234_matrix2.txt` and never resolves the variable. So
# the answer to `exists` was YES only on a host where that instrument had already run
# once — and macOS clears /tmp on reboot, which made the FIRST FIRE AFTER A RESTART
# exit 2 with no probe line: the most ambiguous signal this harness can emit, since
# it reads the same as "the corpus is unusable" and as "the oracle is unreachable".
#
# T273 repaired the instrument — its fixture is now a `mktemp -d` scratch directory it
# owns and removes on EXIT, and `mktemp`'s XXXXXXXXXX template is not a path that any
# linter can resolve, so no classification can depend on it. THAT REPAIR IS ONE FILE.
# THIS GUARD IS THE CLASS (P-26), because a repair nothing enforces is the shape this
# program has now been punished for five times: manifest.py verify, t44_float_roundtrip
# _v3, T173's float guard, guard_ledger_invariants, and T238's own linter, each of them
# correct and each of them inert until someone wired it.
#
# THE RULE, STATED AS A PROPERTY AND NOT AS A LIST. A file that the fail-open linter
# CLASSIFIES may not assign a literal absolute path under a SHARED TEMPORARY ROOT
# (/tmp, /private/tmp, /var/tmp) to a name. Such a path is host state three times over:
# it is shared between every worktree on the machine, no commit records whether it
# exists, and the operating system deletes it on reboot. C1 and C6 both decide tier by
# asking whether a path EXISTS, so any such assignment is a shape CAPABLE of moving a
# tier without a single byte of the tree changing.
#
# THE PIN IS DELIBERATELY WIDER THAN THE DEFECT, AND SAYS SO. Some of the rows below
# are filtered by the linter's ownership rule today and therefore do NOT move a tier
# today — `t239-r11-rerun/instruments/50-red-drive.sh` is the clear case: it writes
# `export GIT_INDEX_FILE=/tmp/t239-red-index` at :35 and `rm -f /tmp/t239-red-index`
# at :42, and the literal `rm` makes C1's owned-path filter fire, which is why that
# file is pinned TIER2 even though the path does not exist right now [VERIFIED by
# reading both lines and by the frontier being TIER2 with the path absent]. This guard
# still lists it. Refusing the SHAPE rather than the currently-live subset is the
# choice, because "this one is filtered today" is a fact about the linter's current
# rules, and T266 is under way to change exactly those rules.
#
# THE POPULATION SELECTOR IS A MEASURED SUPERSET OF THE LINTER'S, NOT AN ASSUMED ONE.
# The linter selects repo-wide search instruments with a Python `re` over the whole
# file text; this guard uses `git grep -E`, which is POSIX ERE, line-based, and has no
# `\b`. Two engines and two spellings, so the agreement was MEASURED rather than
# asserted (.softhouse/capture/t273-residue/instruments/40-selector-agreement.py,
# evidence/40-selector-agreement.txt): linter 71 files, this guard 86, files the linter
# sees and this guard does not = ZERO. A superset is the property the guard needs; a
# subset would be a hole an author could walk through by choosing a spelling. Those two
# COUNTS will drift as instruments are written — the property that must not drift is the
# ZERO, and 40-selector-agreement.py exits 1 the moment it stops holding.
#
# FAIL-CLOSED, three ways, because a census that inspects nothing passes everything:
#   * `git grep` EXITS 1 ON NO MATCH AND >1 ON ERROR. Anything above 1 — including the
#     9 this guard's subshell raises when it cannot enter $REPO_ROOT — is an ERROR and
#     refuses. Treating any nonzero as "clean" is precisely how this class fails open;
#   * the SELECTOR must return at least one file. Zero repo-wide search instruments in
#     a 996-file corpus means the selector broke, not that the tree is clean (P-35);
#   * the guard PRINTS what it compared on the way past, every run, pass or fail. A
#     guard that speaks only when it fires cannot be told from one that never ran.
# NO PIPELINE ANYWHERE IN IT (P-57): every read is a `sed`/`grep` over a FILE.
#
# THE PIN IS A FRONTIER, NOT AN AMNESTY — the same terms as FAILOPEN_PIN_FILE_LIST
# twenty lines up. A '+' row is a NEW site: repair it with `mktemp` scratch rather than
# pinning it. A '-' row is a site that was REPAIRED or DELETED, which is good news, and
# the pin must lose that row IN THE SAME COMMIT or it starts excusing a weakness that
# is no longer there. T273 REMOVED EXACTLY ONE ROW IN THE COMMIT THAT EARNED IT: this
# census is EIGHTEEN at the parent commit and SEVENTEEN here [T293 CORRECTION: "SEVENTEEN here"
# was true of T273's commit and is NOT true of this one. The driver added T271's probe back at
# fire close, so the pin is EIGHTEEN rows at this commit. T273's sentence stands because it is
# the record of what T273 did; this bracket is the correction. The `say` line in the guard body
# below still prints the LITERAL "pinned at 17" and is therefore wrong on every run — REQUIRED
# FOLLOW-UP, T293 F5; not repaired here because that line is outside T293's declared file
# partition, and a reviewer that reaches outside its partition costs two tasks a clean merge]
# [T300 CLOSES T293 F5: there is no literal there any more. The `say` reads the pin's length
# with `grep -ac ''` over the same sorted file the diff compares, so the printed cardinal and
# the pinned list cannot disagree — see the block above that `say`. This bracket is left
# standing rather than deleted because it is the record of how the defect was found; only its
# present tense is now false, and this sentence is what makes that visible],
# and the row that left is
# `…/02-escape-matrix-fix.sh | C=/tmp/t234_matrix2.txt` [VERIFIED: the census expression
# run against HEAD prints that file's line 6 and exits 0; the same expression against
# the working tree exits 1, and `git grep` exits 1 on NO MATCH and >1 on ERROR, so the
# 1 is an ABSENCE and not a failure].
#
# Rows are `PATH | NAME=ABSPATH`, with the line NUMBER deliberately absent: line numbers
# rot on every insertion above them, and this program has already paid for a pin that
# was restated as line numbers in four places (T255/T258).
#
# WHAT THIS GUARD DOES NOT CLAIM. [T300: "the seventeen rows below" stood here and was a
# SECOND rot site for the same cardinal — spelled in words, so the numeric sweep that found
# `pinned at 17` could not see it, and it was wrong by one against an 18-row pin. The count is
# deleted rather than corrected: the list is nine lines further down and can be counted, and a
# restatement that cannot be wrong is a restatement that is not there (P-80 — "The fix is never
# the new number — it is to make the second site READ the first").]
# It does not claim the rows below currently
# move a tier — most do not, and the check that would say which is the linter's own,
# not this one's. It does not claim to have found every way a graded run can read state
# outside the repo: $HOME, an env var, a sibling worktree and a previously-run instrument
# are all still open, and T273's handoff lists what it looked at and what it did not
# (P-66/P-70 — "not found" is a statement about the search, never about the world).
# It claims exactly one thing: no NEW literal shared-temp assignment can enter the
# fail-open linter's corpus without a source edit to this file that a reviewer reads.
# T271's probe_tmp_dependency_t271.sh was ADDED to this census by the driver at the close of
# fire 20260823-080004, and the reasoning is recorded here rather than in a commit message because
# THIS is the file a future reviewer reads. The guard did its job: T273 installed it and T271's
# probe tripped it IN THE SAME FIRE, census 18 against a pin of 17.
#
# WHY PINNED RATHER THAN REPAIRED, which is the question the guard's own text asks: the adoptable
# `mktemp -d` shape is INAPPLICABLE BY CONSTRUCTION here. That probe's entire purpose is to measure
# whether the bar's colour depends on ONE SPECIFIC ABSOLUTE PATH that another instrument hard-codes
# (t234's 02-escape-matrix-fix.sh:6). Naming the path IS the measurement; a fresh mktemp path would
# measure nothing. The probe reads the path, records whether it was present, and RESTORES THE STATE
# IT FOUND -- it is a measurement, not a dependency.
#
# THIS IS NOT THE MOVE P-88 REJECTS, and the distinction matters. T271 refused to create the file
# or to move FAILOPEN_PIN_FILE_LIST to go green, because both would manufacture a green out of host
# state. This is a different pin: a CENSUS of known literal-temp assignments, whose stated purpose
# is that no new site enters without a source edit a reviewer reads. Adding a genuine new site with
# its justification is what the guard ASKS FOR; the failure mode it guards against is a site
# arriving unseen.
#
# ADJUDICATED BY T293: UPHELD-WITH-REPAIR. The row STAYS. The paragraphs above are the driver's
# and are left standing as the record; everything from here down is the reviewer's, and it does
# NOT defer to them — two of their load-bearing claims were measured FALSE.
#
# WHAT T293 CONFIRMED, BY DRIVING IT RATHER THAN READING IT:
#   * THE PIN MANUFACTURES NO GREEN. The bar is `PASS exit 0` with /tmp/t234_matrix2.txt PRESENT
#     and with it ABSENT — both arms measured this fire, same tree, changing only the file. That
#     is the decisive difference from P-88, where the bar was green IF AND ONLY IF the residue
#     existed. The driver argued this distinction; T293 MEASURED it, which is what makes it hold.
#   * THE ROW BELONGS IN A CENSUS OF THE SHAPE. The probe IS in the fail-open linter's corpus and
#     its classification IS decided by this host's /tmp: residue ABSENT it is TIER 3 (C1 :44 dead
#     absolute path), residue PRESENT it is unclassified — TIER 3 count 7 files/14 findings vs
#     6/13. TIER 3 is not on the frontier, so the row moves no GRADED figure today; but "a shape
#     CAPABLE of moving a tier" is the property this guard refuses, and the probe has it.
#   * `mktemp` REMAINS INAPPLICABLE, and the "parameterise it instead" repair is COSMETIC EVASION,
#     measured: a file carrying `TARGET="${1:-/tmp/t234_matrix2.txt}"` and `TMPROOT=/tmp` +
#     `"$TMPROOT/t234_matrix2.txt"` depends on the identical path and is INVISIBLE to this census
#     (18, unchanged) AND to C1 (frontier 11, unchanged) AND leaves the bar `exit 0`. Pinning
#     keeps the site visible; parameterising blinds both instruments. Pinning is strictly better.
#   * THE CENSUS STILL FIRES. A genuinely new accidental site was added and tracked; the bar went
#     EXIT 2 with a '+' row naming it and ZERO probe lines (P-84 — read the line's PRESENCE
#     first). Removing it returned exit 0. A census that no longer fires is not a census; this
#     one fires. [.softhouse/reviews/T293/evidence/40-red-drive.txt]
#
# WHAT T293 FOUND FALSE IN THE REASONING ABOVE, AND THIS IS WHY THE VERDICT CARRIES "WITH-REPAIR":
#   * THE CITED PREMISE NO LONGER EXISTS. The paragraph above says the probe measures "ONE
#     SPECIFIC ABSOLUTE PATH that another instrument hard-codes (t234's 02-escape-matrix-fix.sh:6)"
#     — present tense. T273 DELETED that hard-coding in commit 7e85a3e, in the same fire. Line 6
#     of that file is now the comment "# T273 — THE FIXTURE IS NOW SELF-OWNED SCRATCH, NOT A
#     LITERAL PATH IN /tmp." The justification was already false when it was written.
#   * "RESTORES THE STATE IT FOUND" WAS AN ASSERTION, NOT A MEASUREMENT — and it is the exact
#     claim the pin was rested on. The probe printed `restoredAsFound=1` as a HARD-CODED LITERAL,
#     before the EXIT trap that restores had run. Red-driven: trap deleted, probe found the file
#     PRESENT, left it ABSENT, still printed `restoredAsFound=1`. Also, restoration is not
#     universal — SIGKILL mid-run leaves the file PRESENT after finding it ABSENT (SIGTERM and
#     SIGINT restore). Both repaired in the probe by T293: the claim is now emitted by the trap
#     from a re-read (`T271-RESTORE: foundPresent=N nowPresent=M restored=0|1`) and SIGKILL is
#     disclosed rather than covered.
#
# THE ROW SURVIVES ANYWAY, AND ON A BETTER GROUND THAN THE ONE OFFERED. The probe's subject path
# must stay a literal not because another instrument still hard-codes it, but because the probe
# is now a REGRESSION TEST that T273's repair HOLDS: exit 1 = repair holds, exit 0 = a literal
# path is back in the linter's corpus. Naming the path is still the measurement — of the opposite
# proposition. A `mktemp` path would measure nothing, then as now.
#
# STATED SCOPE, so "18 sites" is not read as "every literal temp assignment in the repo" (P-66/
# P-70 — "not found" is a statement about the search). The population is the fail-open linter's
# corpus: files matching a repo-wide-search idiom. Measured consequences, both real:
#   - `.softhouse/capture/t253-portability/instruments/50-t234-residue-probe.sh:22` carries
#     `RESIDUE=/tmp/t234_matrix2.txt` — the same literal, the same shape — and is NOT censused,
#     because that file contains no repo-wide-search idiom (selector exits 1 on it).
#   - the T271 probe enters this census ONLY through line 30, a COMMENT quoting P-81's text
#     "`git grep`/`grep` exits 1 on NO MATCH". The probe performs no repo-wide search at all.
#     Rewording that comment would drop it out of both this census and the linter's corpus.
# Neither is a new hole — both follow from the population the guard already declares — but a
# census is only as wide as its selector, and the selector is a search instrument selector.
#
# DELIBERATELY LEFT UNWIRED, AND THE REASON IS A MEASUREMENT, NOT A COST ESTIMATE. The probe is
# a regression test that nothing calls (P-45) — but THIS CENSUS ALREADY IS THAT REGRESSION TEST.
# `02-escape-matrix-fix.sh` IS in this guard's population [`git grep -l -E <selector> -- <it>`
# exits 0], so putting `C=/tmp/t234_matrix2.txt` back into it makes the census ERE match, which is
# a '+' row, which is EXIT 2 — driven by T293, then restored and the restore verified by an empty
# `git diff --stat`. Reintroducing T273's exact defect therefore turns this bar red EVERY RUN
# through a guard that already runs. Wiring the probe on top would buy a redundant check for ~19s
# per bar. Its remaining value is diagnostic: it explains WHY a row is red, which a census row
# does not. A DECLARED orphan, with the reason, is what P-89 asks for; a silent one is not.
HOSTSTATE_PIN_TEMP_ASSIGN_LIST='.softhouse/capture/t116-familyb-promotion/src/run-harness-mutations-t116.sh | SCRATCH=/tmp/t116-harness
.softhouse/capture/t234-sweep-instrument-audit/instruments/01-escape-matrix.sh | C=/tmp/t234_matrix.txt
.softhouse/capture/t239-r11-rerun/instruments/50-red-drive.sh | GIT_INDEX_FILE=/tmp/t239-red-index
.softhouse/capture/t271-b1-t219/probe_tmp_dependency_t271.sh | TARGET=/tmp/t234_matrix2.txt
.softhouse/capture/t91/t115-drive-mf3-mf4.sh | S=/tmp/t115-mf34.$$
.softhouse/reviews/T138-evidence/r7-mf3-mf4.sh | B=/tmp/T138-mf2-post
.softhouse/reviews/T138-evidence/r7-mf3-mf4.sh | X=/tmp/T138-mf3
.softhouse/reviews/T138-evidence/r7b-census.sh | B=/tmp/T138-mf2-post
.softhouse/reviews/T155-probe/prove-ix-sweep-and-help.sh | POST=/tmp/t155/post
.softhouse/reviews/T155-probe/prove-ix-sweep-and-help.sh | PRE=/tmp/t155/pre
.softhouse/reviews/T155-probe/prove-xiv-sweep-coverage.sh | P=/tmp/t155/post2
.softhouse/reviews/T158-compare-enumerators.sh | C=/tmp/t158-clone
.softhouse/reviews/t246-dec2-rev6/drive-pin-red.sh | SCRATCH=/tmp/t246-pin-red
.softhouse/reviews/t260-dec2-rev8/instruments/50-collision-and-red-drive.sh | RED=/tmp/t260/red
.softhouse/reviews/t260-dec2-rev8/instruments/50-collision-and-red-drive.sh | SH=/tmp/t260/sh
.softhouse/reviews/t260-dec2-rev8/instruments/50-collision-and-red-drive.sh | p=/tmp/t260/red/.softhouse/conformance.sh
.softhouse/reviews/t260-dec2-rev8/instruments/50-collision-and-red-drive.sh | p=/tmp/t260/red/.softhouse/conformance.sh
.softhouse/reviews/t260-dec2-rev8/instruments/50-collision-and-red-drive.sh | p=/tmp/t260/red/.softhouse/conformance.sh'

guard_no_host_state_in_lint_corpus() {
  local rw as list raw got want rc n m p self f
  local -a corpus
  self='.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py'
  # The linter's repo-wide-instrument selector, transliterated to POSIX ERE.
  rw='(git[[:space:]]+(-[A-Za-z][[:space:]]+[^[:space:]]+[[:space:]]+|--[A-Za-z-]+=[^[:space:]]+[[:space:]]+|-[A-Za-z]+[[:space:]]+)*(grep|ls-files)|grep[[:space:]]+-[a-zA-Z]*[rR])'
  # A NAME assigned a literal absolute path under a shared temporary root. Anchored at
  # the start of the line, so a `#` comment can never match: `#` is not [A-Za-z_].
  as='^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*=["'"'"']?/(tmp|private/tmp|var/tmp)/'

  list="$(mktemp "${TMPDIR:-/tmp}/conformance-hoststate-list.XXXXXXXXXX")" || return 1
  raw="$(mktemp  "${TMPDIR:-/tmp}/conformance-hoststate-raw.XXXXXXXXXX")"  || return 1
  got="$(mktemp  "${TMPDIR:-/tmp}/conformance-hoststate-got.XXXXXXXXXX")"  || return 1
  want="$(mktemp "${TMPDIR:-/tmp}/conformance-hoststate-want.XXXXXXXXXX")" || return 1

  ( cd "$REPO_ROOT" || exit 9; LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' ) >"$list.raw" 2>/dev/null
  rc=$?
  if [ "$rc" -gt 1 ]; then
    warn "conformance: the host-state selector exited $rc. \`git grep\` exits 1 on NO MATCH and >1 on"
    warn "conformance: ERROR — 9 is this guard's own code for 'could not enter $REPO_ROOT'. An error is"
    warn "conformance: never an empty result, and an empty result here would read as a clean tree."
    rm -f "$list" "$list.raw" "$raw" "$got" "$want" "$want.raw"
    return 1
  fi
  # The linter never lints ITSELF; neither does this guard, for the same reason and so
  # that the two populations stay comparable.
  LC_ALL=C grep -v -x -F "$self" "$list.raw" >"$list" 2>/dev/null || true
  n="$(LC_ALL=C grep -ac '' "$list" || true)"
  [ -n "$n" ] || n=0
  if [ "$n" -lt 1 ]; then
    warn "conformance: the host-state selector matched ZERO repo-wide search instruments in a corpus"
    warn "conformance: that has hundreds. The selector is broken, not the tree clean (P-35). REFUSED."
    rm -f "$list" "$list.raw" "$raw" "$got" "$want" "$want.raw"
    return 1
  fi

  corpus=()
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    corpus[${#corpus[@]}]="$f"
  done <"$list"

  ( cd "$REPO_ROOT" || exit 9; LC_ALL=C git grep -n -E "$as" -- "${corpus[@]}" ) >"$raw" 2>/dev/null
  rc=$?
  if [ "$rc" -gt 1 ]; then
    warn "conformance: the host-state census exited $rc from \`git grep\`. >1 is an ERROR, and this"
    warn "conformance: guard will not read an error as 'no sites found'."
    rm -f "$list" "$list.raw" "$raw" "$got" "$want" "$want.raw"
    return 1
  fi

  # PATH | NAME=ABSPATH. The line NUMBER is dropped on purpose (it rots on every
  # insertion above it, and this program has already paid for a pin restated as line
  # numbers in four places — T255/T258). Quotes around the value are dropped and the
  # rest of the line — `; rm -rf …`, a trailing comment — is dropped with them, so a
  # row is the assignment and nothing else.
  LC_ALL=C sed -n 's%^\([^:]*\):[0-9][0-9]*:[[:space:]]*\(export[[:space:]][[:space:]]*\)\{0,1\}\([A-Za-z_][A-Za-z0-9_]*\)=["'"'"']\{0,1\}\(/[^;()&|[:space:]"'"'"']*\).*$%\1 | \3=\4%p' "$raw" >"$got.raw"
  # A `sed -n …p` DROPS what it cannot match, and a dropped row is a site that leaves
  # the census silently — the fail-open shape this whole guard exists to refuse. So the
  # two line counts are COMPARED, and a normalisation that lost anything refuses.
  rc="$(LC_ALL=C grep -ac '' "$raw" || true)";     [ -n "$rc" ] || rc=0
  m="$(LC_ALL=C grep -ac '' "$got.raw" || true)";  [ -n "$m" ]  || m=0
  if [ "$rc" -ne "$m" ]; then
    warn "conformance: the host-state census matched $rc line(s) but could normalise only $m."
    warn "conformance: a row this guard cannot read is a row that would leave the census silently."
    LC_ALL=C sed -n '1,12p' "$raw" >&2
    rm -f "$list" "$list.raw" "$raw" "$got" "$got.raw" "$want" "$want.raw"
    return 1
  fi
  LC_ALL=C sort "$got.raw" >"$got"
  if [ -n "$HOSTSTATE_PIN_TEMP_ASSIGN_LIST" ]; then
    printf '%s\n' "$HOSTSTATE_PIN_TEMP_ASSIGN_LIST" >"$want.raw"
  else
    : >"$want.raw"
  fi
  LC_ALL=C sort "$want.raw" >"$want"
  m="$(LC_ALL=C grep -ac '' "$got" || true)"
  [ -n "$m" ] || m=0

  # THE PIN CARDINAL IS DERIVED FROM THE PIN, NEVER TYPED BESIDE IT. [T300, closing T293 F5]
  # Until this commit the line below printed the LITERAL "pinned at 17" against an 18-row pin,
  # on EVERY run, pass or fail, while the list-diff underneath it was green — so nothing in the
  # transcript ever contradicted it. That is P-80 exactly ("A CORRECTED CARDINAL ROTS IN EVERY
  # PLACE IT WAS RESTATED. The count is the same defect as the line number"), landing inside the
  # one guard whose stated purpose is that no new site enters unseen. The cost is not being
  # wrong once: a census that misreports its own size teaches every reader to discount its
  # numbers, and this guard has nothing to offer a reader who discounts its numbers.
  #
  # WHY NO LITERAL SURVIVES, AND WHY NO SECOND EQUALITY TEST WAS BOLTED ON TOP. `diff -u` below
  # compares the two SORTED files for CONTENT; content equality implies length equality, so $m
  # and $p CANNOT differ on any path that reaches the pass line. A literal kept "for safety"
  # would then be the only thing in this guard capable of disagreeing with the pin — it would be
  # the defect, not the safeguard — and an added `[ "$m" -ne "$p" ]` refusal would be a branch no
  # reachable input can enter, which is a guard nobody can ever watch fail (P-45 — "a guard that
  # only works when someone remembers to run it enforces nothing"; its point is that an
  # unexercised guard enforces nothing, and a branch with no reachable input is unexercisable by
  # construction). What IS checked is the DERIVATION: a cardinal that does not derive refuses
  # rather than falling back to 0, because a fallback zero is the vacuous pass this whole file
  # exists to refuse (P-35). Driven red in .softhouse/capture/t300-census-cardinal/red/.
  p="$(LC_ALL=C grep -ac '' "$want")"
  case "$p" in ''|*[!0-9]*) p=-1 ;; esac
  if [ "$p" -lt 0 ]; then
    warn "conformance: the host-state PIN CARDINAL did not derive from the pinned list. A census"
    warn "conformance: that cannot count its own pin may not print a figure beside it, and a"
    warn "conformance: fallback zero would read as 'nothing is pinned'. REFUSED, not defaulted."
    rm -f "$list" "$list.raw" "$raw" "$got" "$got.raw" "$want" "$want.raw"
    return 1
  fi
  say "conformance: CENSUS host state in the lint corpus — $n repo-wide search instrument(s)"
  say "conformance:   read from git grep over tracked *.sh/*.py under $REPO_ROOT; sites that assign a"
  say "conformance:   literal /tmp, /private/tmp or /var/tmp path to a name: $m, pinned at $p"
  say "conformance:   (DERIVED from HOSTSTATE_PIN_TEMP_ASSIGN_LIST by counting it, never typed)."
  say "conformance:   Such a path is host state — shared across worktrees, absent from every commit,"
  say "conformance:   and deleted on reboot — and C1/C6 decide TIER by asking whether a path EXISTS."
  if ! diff -u "$want" "$got" >"$raw.diff" 2>&1; then
    warn "conformance:"
    warn "conformance: THE HOST-STATE CENSUS IS NOT THE PINNED CENSUS (- pinned, + measured):"
    LC_ALL=C sed -n '3,60p' "$raw.diff" >&2
    warn "conformance:"
    warn "conformance: A '+' line is a NEW instrument whose fail-open TIER can be decided by this"
    warn "conformance: host's /tmp instead of by the tree. Repair it — \`D=\$(mktemp -d \"\${TMPDIR:-/tmp}/"
    warn "conformance: name.XXXXXXXXXX\")\` with a \`trap 'rm -rf \"\$D\"' EXIT\` is the adoptable shape, and"
    warn "conformance: an XXXXXXXXXX template is not a path any linter can resolve — rather than pinning it."
    warn "conformance: A '-' line is a site that was REPAIRED or DELETED: that is good news, and the pin"
    warn "conformance: must lose the row IN THE SAME COMMIT, or it starts excusing a weakness that is"
    warn "conformance: no longer there."
    warn "conformance: The pin is HOSTSTATE_PIN_TEMP_ASSIGN_LIST in .softhouse/conformance.sh."
    warn "conformance: EXIT 2 — no verdict is available. This is NOT a pass."
    rm -f "$list" "$list.raw" "$raw" "$raw.diff" "$got" "$got.raw" "$want" "$want.raw"
    return 1
  fi
  say "conformance:   census == pinned (all $m site(s), by path and source line)."
  rm -f "$list" "$list.raw" "$raw" "$raw.diff" "$got" "$got.raw" "$want" "$want.raw"
  return 0
}

# ---------------------------------------------------------------------------
# guard_accepting_side_gap_declared: THE OPENING-BALANCE ACCEPTING-SIDE HOLE IS
# DECLARED WHILE IT IS OPEN, AND THE DECLARATION IS REMOVED WHEN IT CLOSES. [T305]
# ---------------------------------------------------------------------------
# WHAT HOLE. T296 mutated the PORT rather than arguing about it and measured four arms.
# Arm E (the opening-balance rule moved below the balance check) DIES, which vindicates
# T294's precedence claim. But arm A -- a port that matches on
# `req.Command == "defineOpeningBalance"` ALONE and NEVER reads the posted-id list, so it
# refuses EVERY opening balance including on an empty ledger where the reference oracle
# ACCEPTS (JournalEntryWritePlatformServiceJpaRepositoryImpl.java:812, the CollectionUtils
# .isEmpty fall-through) -- SURVIVES the whole ledger corpus. That is the headerRefusingPoster
# class this store already names and already kills elsewhere: LDG-04 exists precisely because
# the reasonable-looking port REFUSES a HEADER account, and diverging from the oracle BY
# REFUSING is still diverging.
#
# WHY NO REFUSAL VECTOR CAN CLOSE IT, stated here because the cheap wrong move is to add one:
# every refusal capture in this corpus AGREES with arm A. The closer is an ACCEPTING-side
# observation and nothing else.
#
# THE HOLE IS NOW CLOSED, AND THIS GUARD IS WHAT NOTICED. [T305] The paragraph that used to
# stand here said T305 "measured whether one can be taken safely and concluded it CANNOT on
# this rig". That was true of both REGISTERED TENANTS of the standing reference oracle and it
# is still true of them -- guard-accepting-capture.sh still exits 1, and is still the fence
# that keeps anyone from posting an undeletable journal entry into gerege or default. What it
# was NOT true of is a THROWAWAY INSTANCE: same docker image as the standing oracle, tenant
# seeded at Asia/Ulaanbaatar and rounding-mode 4 from environment variables, empty ledger by
# construction, destroyed in the same run. The capture is
# LDG-05-openingbalance-accepted-empty-ledger (HTTP 200, six journal entries for three request
# legs) and arm A is registered as ledger-wrong-openingbalance-always-refusing and dies to it.
#
# SO THE FOUR-CELL TABLE BELOW IS NOW IN ITS BOTTOM-RIGHT CELL, and the guard stays exactly as
# it is: it goes red again the moment somebody deletes the accepting vector without restoring
# a declaration, which is the direction that matters from here.
#
# WHY THIS IS A GUARD AND NOT A SENTENCE. P-89: "PROSE DOES NOT FIRE ON THE NEXT FIRE -- a
# limit written into a handoff, a review, or a `## Backlog` heading is invisible to the
# scheduler." T294 wrote its own widening risk into a backlog heading and it took a whole
# review fire to convert that into a measurement. This guard is the conversion, done up front.
#
# IT IS DELIBERATELY TWO-WAY, because a one-way guard becomes the next stale claim (A2-34
# F-4: a false sentence the harness prints on every run as a measured fact). It compares two
# facts the tree can supply for itself:
#
#   VECTORS  the number of ledger vectors that assert an ACCEPTED defineOpeningBalance --
#            i.e. carry that command and are NOT of expect kind "refusal".
#   MARKER   whether capabilities-ledger.json still carries the token T305-ACCEPTING-SIDE-GAP.
#
#   VECTORS=0, MARKER present  -> ok. The hole is open and the store says so.
#   VECTORS=0, MARKER absent   -> FAIL. The hole is open and NOTHING declares it any more.
#   VECTORS>0, MARKER present  -> FAIL. The hole is CLOSED and the declaration is now a lie.
#   VECTORS>0, MARKER absent   -> ok. Closed, and the declaration was removed with it.
#
# AND ONE MORE THING IT REFUSES: a COMMITTED disposability attestation. T305's gate treats
# `attest/<tenant>.disposable` as the one condition no measurement can supply -- permission to
# mutate a tenant irreversibly. Such a file in the TRACKED tree is a standing authorisation to
# post journal entries that can never be deleted, and it must be an explicit, reviewed act,
# never something that arrives inside somebody's capture rig. Read through `git ls-files` on
# purpose: an untracked scratch file (red-drive-gate.sh creates one and deletes it) is not an
# authorisation, and a tracked one is.
guard_accepting_side_gap_declared() {
  local vecdir="$REPO_ROOT/.softhouse/vectors/ledger"
  local capfile="$REPO_ROOT/.softhouse/vectors/capabilities-ledger.json"
  local rc=0 vectors=0 marker=0 f

  if [ ! -d "$vecdir" ] || [ ! -f "$capfile" ]; then
    warn "conformance: ACCEPTING-SIDE GAP guard: the ledger vector directory or"
    warn "conformance: capabilities-ledger.json is MISSING. Fail-closed: this guard cannot"
    warn "conformance: report on a tree it cannot read, and silence would read as a pass."
    return 1
  fi

  for f in "$vecdir"/*.json; do
    [ -f "$f" ] || continue
    LC_ALL=C grep -q '"command"[[:space:]]*:[[:space:]]*"defineOpeningBalance"' "$f" || continue
    LC_ALL=C grep -q '"kind"[[:space:]]*:[[:space:]]*"refusal"' "$f" && continue
    vectors=$((vectors + 1))
    say "conformance:   ACCEPTING-SIDE GAP: accepting opening-balance vector found: ${f##*/}"
  done

  LC_ALL=C grep -q 'T305-ACCEPTING-SIDE-GAP' "$capfile" && marker=1

  say "conformance: CENSUS opening-balance ACCEPTING side — accepting vectors $vectors,"
  say "conformance:   capabilities-ledger declaration $( [ "$marker" -eq 1 ] && echo PRESENT || echo ABSENT )."

  if [ "$vectors" -eq 0 ] && [ "$marker" -eq 0 ]; then
    warn "conformance: THE ACCEPTING-SIDE HOLE IS OPEN AND NOTHING DECLARES IT."
    warn "conformance: No ledger vector asserts an ACCEPTED defineOpeningBalance, so T296 arm A —"
    warn "conformance: a port that refuses EVERY opening balance, including where the oracle"
    warn "conformance: accepts at :812 — is UNKILLED; and the token T305-ACCEPTING-SIDE-GAP has"
    warn "conformance: been removed from capabilities-ledger.json, so the store no longer says so."
    warn "conformance: Restore the declaration, or CLOSE the hole with an accepting capture."
    rc=1
  elif [ "$vectors" -gt 0 ] && [ "$marker" -eq 1 ]; then
    warn "conformance: THE ACCEPTING-SIDE DECLARATION IS NOW STALE."
    warn "conformance: $vectors ledger vector(s) assert an ACCEPTED defineOpeningBalance, so the"
    warn "conformance: hole is CLOSED — but capabilities-ledger.json still carries"
    warn "conformance: T305-ACCEPTING-SIDE-GAP and the harness would go on printing it as a"
    warn "conformance: measured limit. That is the A2-34 F-4 defect: a caveat outliving its"
    warn "conformance: defect. Remove the token IN THE SAME DIFF that promotes the vector."
    rc=1
  elif [ "$vectors" -eq 0 ]; then
    say "conformance:   OPEN AND DECLARED. T296 arm A is UNKILLED and the store says so. The only"
    say "conformance:   thing that closes it is an ACCEPTING observation; every refusal capture in"
    say "conformance:   this corpus AGREES with arm A, so no number of them can substitute."
  else
    say "conformance:   CLOSED, and the declaration was removed with it."
  fi

  local attest
  attest="$(cd "$REPO_ROOT" && git ls-files -- '.softhouse/capture/*/attest/*.disposable' 2>/dev/null || true)"
  if [ -n "$attest" ]; then
    warn "conformance: A TRACKED DISPOSABILITY ATTESTATION IS PRESENT IN THIS TREE:"
    printf '%s\n' "$attest" | while IFS= read -r a; do warn "conformance:   $a"; done
    warn "conformance: That file is a standing authorisation to post journal entries into a"
    warn "conformance: reference-oracle tenant, and A POSTED JOURNAL ENTRY HAS NO DELETE PATH IN"
    warn "conformance: FINERACT AT ALL. It must be an explicit reviewed act, not a file that"
    warn "conformance: arrived inside a capture rig. Remove it, or route the decision as a task."
    rc=1
  else
    say "conformance:   no tracked disposability attestation — nothing authorises an irreversible"
    say "conformance:   accepting capture in this tree."
  fi
  return "$rc"
}

# ===========================================================================================
# T323 — THE WIRING OF THREE GUARDS THAT SHIPPED ENFORCING NOTHING.
# ===========================================================================================
# Three tasks in ONE fire (T299, T316, T319) each built a guard, drove it red AND green, and
# each then wrote — independently, none having read the others — that until it was wired its
# work enforced nothing. That is P-45 restated three times in a single fire:
#
#   P-45 — "A test-only guard is not a guard. T154's float-literal census is called from `Run`,
#   not only from the Go test, because `conformance.sh` never invokes `go test` — a test-only
#   fix would have left the third silent green standing while looking fixed. Rule: when
#   hardening a check, verify the path that ACTUALLY EXECUTES in CI/conformance calls it, not
#   merely that a test does."   [VERIFIED: .softhouse/patterns.md:1472]
#
# The root was measured by T302, re-run by T319, and re-run again by T323 on this branch:
#     grep -c 'fire-program\|ready-tasks\|reconcile\|in_progress' .softhouse/conformance.sh
# returned 0 over 3,101 lines (T319's checkout) and 0 over 3,253 lines (T323's, immediately
# before this block) — in a file whose own block headed "EACH GUARD RUNS ITS OWN SELFTEST
# FIRST, IN THE SAME INVOCATION" requires the selftest to run on every conformance run, "not
# on the day someone remembers". GREP THAT HEADING (P-86): T323 cited it as "line 909" and
# T326 measured it at :920 — stale by 11 within one fire.
#
# ALL THREE ARE HARD. None is advisory. A SOFT wiring prints a line that nothing depends on,
# which is P-22 — "a guard, a canary, or a control that cannot fail is worse than none, because
# it is believed" — and that is the sentence the three authors already wrote, with extra steps.
#
# EACH GUARD DECLARES ITS OWN FAIL-CLOSED DIRECTION, BELOW, AND NOT ONE PREDICATE IS WIDENED
# TO SERVE TWO PURPOSES. That widening is the shape T292 identified as the root of a five-fix
# losing streak, and three guards landing in one commit is exactly when it would happen.
#
# P-84 SURVIVES ALL THREE BY CONSTRUCTION, AND IT WAS VERIFIED RATHER THAN ASSUMED. run_guards
# is called on main_grade's second line; probe_oracle is not reached for ~25 lines after it. So
# a refusal from any guard here exits 2 with the `reference oracle (…) probe = up|down` line
# ABSENT — not `down`. "P-84 — 'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE
# ABSENCE, NOT THE VALUE." [VERIFIED: .softhouse/patterns.md:2782]. The driver's park condition
# is `exit 2` AND a probe line PRESENT AND reading `down`; test the line's PRESENCE first, or a
# guard refusal gets parked as somebody else's server being down.
#
# COST, WALL CLOCK, MEASURED ON THIS HOST BY T323 (not estimated, not copied forward):
#     conformance.sh, this tree, BEFORE this block          15.9 s
#       guard_capture_namespace                              0.4 s
#       guard_dead_path_frontier                             1.3 s
#       guard_reconciler_ownership                          30.3 s   (26 cells, both legs)
#     conformance.sh, this tree, AFTER this block           see the figure recorded in T323's
#       handoff; it is re-measured there rather than predicted here.
# The reconciler guard is twice the cost of everything else in this file combined, and it is
# kept anyway. The argument is T319's and it is not a preference: it is the only automated
# thing standing between a broken ownership predicate and DESTROYED LIVE WORK, and the version
# before it shipped 8/8 green while carrying a discriminator that would have demoted seven live
# workers of the fire then holding the lock. Fifty seconds is a bar a person will wait for; a
# destroyed worktree is not recoverable at any price.
#
# ===========================================================================================
# T326 — AND THE SENTENCE THIS BLOCK COST TO LEARN.
# ===========================================================================================
# T323's first merge of this block was ABORTED. The bar came back EXIT 2 with ZERO probe lines
# and `T316-DEADPATH-FRONTIER: REFUSED rows=78 pinned=98 added=4 removed=24` — a FAILED HARD
# GUARD under P-84, which is what a driver is trained to read as A MONEY NON-NEGOTIABLE
# VIOLATION. The cause was not in the wiring. It was that T316's pin had been derived with
# `os.path.exists()`, so 23 of its rows named an untracked, `.gitignore`d directory that exists
# on Buyan's Mac and in no worktree, and a 24th named scratch a previous run had left behind.
#
# SO: **WIRING A GUARD HARD IS THE FIRST TIME ANYONE FINDS OUT WHETHER ITS PIN IS A MEASUREMENT
# OR A SNAPSHOT OF SOMEBODY'S DISK.** T316, T299 and T319 each drove their guard red AND green
# and each was honest; not one of them could have found this, because a GREEN BAR IS A CLAIM
# ABOUT THE TREE **AND** THE HOST IT RAN ON, and only a second condition separates the two. The
# three authors' shared finding — P-45 restated three times in one fire — has a fourth term:
# a guard nobody has run in a second condition has not been driven, only exercised.
#
# T326 rebuilt the census to resolve against `git ls-files` and NEVER the disk, regenerated the
# pin from it, and proved the property BY CONSTRUCTION rather than by waiting for the other
# fire: four disk conditions including a real clone, plus the WHOLE BAR run twice, whose two
# transcripts came out BYTE IDENTICAL. The drives live under the T326 capture directory and the
# argument for calling an untracked path DEAD is in the pin's own header.
# ===========================================================================================

# -------------------------------------------------------------------------------------------
# guard_capture_namespace — T299's capture/review namespace guard, wired HARD.   [T323]
# -------------------------------------------------------------------------------------------
# WHAT IT ENFORCES: a task id that prefixes MORE THAN ONE evidence directory under
# .softhouse/{capture,reviews} must carry an `OWNER*.md` in at least N-1 of them. Documented
# collisions PASS — the rule is "say who owns it", never "never collide", because renaming a
# committed evidence directory breaks every transcript and instrument that cites it by path
# (T299 measured 49 files / 182 occurrences for ONE directory, and two guards went red).
#
# HARD, AND HERE IS THE ARGUMENT, because a threshold guard deserves one. The objection is
# real: a HARD guard on a heuristic threshold blocks every graded run the first time somebody
# names a directory reasonably. It is ANSWERED BY MEASUREMENT rather than by assertion. T323
# counted the whole HISTORY, not merely today's tree:
#
#     git log --format= --name-only --diff-filter=A -- .softhouse/capture .softhouse/reviews
#       -> distinct evidence directories EVER created in this repository:   READBACK
#       -> of them carrying a t<n> id prefix:                               READBACK
#       -> ids prefixing MORE THAN ONE directory, over that history:        READBACK
#       -> and EVERY one of them is DECLARED — the guard prints each collision with the
#          OWNER*.md that claims it, or names the UNCLAIMED directory and refuses.
#
# THE CARDINALS ARE NOT RETYPED HERE ANY MORE. T358 said that was the fix and then retyped one
# more pair on its way out; T375 finishes the job, and the reason is that the retyped pair had
# ALREADY ROTTED BY THE TIME THE INK DRIED.
#
# THE ROT, WITH NO NUMBERS IN IT, because a history of rotted cardinals must not be told in
# cardinals. Iteration 1 of T323 wrote a directory count, an id-prefixed count and "exactly ONE
# colliding id". T323 iteration 3 re-derived all three and got two different counts and the same
# "exactly ONE". T358 re-derived them one fire later and got two different counts again and
# **TWO** colliding ids — t255 and t256 — because t255-frontier-rot had merged in the meantime
# with its OWNER-IS-T258-NOT-T255.md, so "exactly ONE" was being cited as load-bearing two
# iterations after it went false. T364 re-derived them a THIRD time on the branch and got two
# further different counts. T375 re-derived them a FOURTH time and got two more. FIVE
# derivations, five different pairs of counts, and the ONLY figure that has held is the one that
# is not a count of the corpus at all: the collision list, which the guard MEASURES on every run.
#
# So there is nothing left here to correct, only something to delete. A cardinal restated in a
# comment beside a guard that MEASURES IT LIVE is a second source of truth with no owner — P-80,
# "A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED. The count is the same defect as the
# line number." [VERIFIED: .softhouse/patterns.md:2775]. The guard prints
# "corpus <N> tracked paths -> <D> evidence directories", "<P> carry a t<n> id prefix", and one
# line per colliding id with the OWNER*.md that claims it, a few lines into its own output.
# READ THAT. Any figure a task needs belongs in that task's own dated handoff, never here.
#
# THE CLAIM THAT ACTUALLY CARRIES THE HARD ARGUMENT is not a count at all: it is that EVERY
# collision this predicate has ever fired on was a TRUE positive with an IN-GRANT remedy — one
# OWNER*.md, inside a directory the tripping task already owns. That has held across all three
# measurements and does not rot when the corpus grows.
#
# ONE TRAP IN RE-DERIVING IT, recorded because iteration 3 fell into it. A naive id regex of
# `^(t|a)[0-9]+` reports TWO colliding ids — t256 and `a2`, the latter with SEVEN directories.
# `a2` is an artifact of the SELECTOR, not a collision in the tree: T299 had already separated
# the a2-<n> id space precisely because folding it produced false collisions (noted below). The
# guard is right and the crude re-derivation was wrong. P-70 — a count is a statement about the
# search, never about the world.
#
# THE FALSE-POSITIVE COUNT BELOW IS SCOPED, AND THE SCOPE IS THE LOAD-BEARING PART OF IT
# [T337 F-T337-5; corpus named, and the cardinal itself re-derived, by T358].
#
#   OVER HEAD'S ANCESTRY — the only corpus a run of this bar can be about — the false-positive
#   count of this predicate is ZERO. Its TRUE-positive count is whatever the guard's own live
#   readback says a few lines into its output, and DELIBERATELY IS NOT RESTATED HERE. T323 wrote
#   "exactly ONE colliding id" and that had already rotted by the next fire, so the sentence
#   T337 proposed as the one-line repair — "say `over HEAD's ancestry` and it is true" — would
#   have shipped a SECOND stale cardinal, correcting the scope of the first clause while leaving
#   a false count standing in the second. A volatile count restated in prose rots; the SCOPE of
#   the claim does not. State the scope, cite the readback, never retype the number. [T375: the
#   re-derivation method is the `git log --diff-filter=A` query printed at the top of this block,
#   ids folded case-insensitively off `^t[0-9]+`; run it, do not read a number here.]
#
#   OVER THE REPOSITORY'S FULL REF SPACE (`git log --all`) there is AT LEAST ONE FURTHER
#   colliding id that HEAD's ancestry cannot see, and it is NAMED rather than counted, because
#   a name does not rot and a count does: **t286**, whose second directory (leaf
#   `t286-rvpa-retry`, written without its prefix so this comment creates no dead-path literal)
#   lives only on an unmerged rescued-WIP branch. A READER PLANNING A MERGE NEEDS THAT NAME,
#   because merging that branch turns this bar red on arrival. IT DOES NOT OVERTURN HARD: it is
#   a TRUE positive — an undocumented collision is exactly what this guard is for — and its
#   remedy is one OWNER*.md inside a directory the merging task already owns, which is in-grant.
#   The full-ref query above lists every such id on the day it is run; that is the readback, and
#   "how many" is a question for the run and not for this comment. [T248 / T258 / T340 — correct
#   where NAMED, never where RESTATED.]
#
# The remaining risk is prospective, not historical: a future task that legitimately wants two
# directories of its own. For that case the threshold is ALREADY N-1 rather than N — T299
# lowered it because its own first draft went red against a correctly-named directory — and the
# remedy the guard PRINTS is to add one file, inside a directory the worker already owns, whose
# entire content is the sentence the rule is asking for. A guard whose remedy is "write the
# sentence the rule wants" is not a blocker; it is the rule. SOFT was rejected because SOFT is
# precisely the defect this task exists to remove.
#
# RESIDUAL RISK, STATED HERE SO IT IS NOT REDISCOVERED AS A SURPRISE: the id space is folded
# across capture/ AND reviews/, so a future `reviews/T<n>/` directory beside a `capture/t<n>-…/`
# directory WOULD collide. That shape does not exist today — no tracked review DIRECTORY shares
# an id with a capture directory — but the premise it used to rest on, "reviews are
# overwhelmingly FLAT .md files", is WEAKENING: review directories are now being created
# (t337-review-t323 is one), and each is a candidate for exactly this collision. [T358, 28 Aug
# 2026.] Should reviews become directories by convention, this guard
# needs its two namespaces separated, the way T299 already separated the a2-<n> id space after
# folding it produced FOUR false collisions.
#
# THE CWD DEFECT THIS WIRING REPAIRS, WHICH IS NOT COSMETIC AND IS NOT A REDESIGN OF T299'S
# GUARD. The guard resolves its own root with `git rev-parse --show-toplevel`, which answers a
# question about the CALLER'S WORKING DIRECTORY and not about $REPO_ROOT. T323 MEASURED the
# divergence rather than reasoning about it: invoked from /Users/buv/gerege-nbfi with the
# guard's own path pointing into a worktree, it printed
#     namespace:   root    /Users/buv/gerege-nbfi
# i.e. it graded a different tree from the one conformance.sh was grading. Wired naively that
# reintroduces the exact divergence guard_graded_root_is_this_tree exists to refuse (T165/T201:
# "this run would certify a tree that none of the guards in this file inspected"). So this
# wiring (a) runs the guard in a SUBSHELL pinned to $REPO_ROOT — the harness's own working
# directory is never moved — and (b) DOES NOT TAKE ITS WORD FOR IT: it reads back the
# `namespace:   root` line the guard prints and REFUSES unless it names $REPO_ROOT. Physical
# paths (`pwd -P`) on both sides, so a symlinked spelling of one tree is not called a divergence.
#
# FAIL-CLOSED DIRECTION, FOR THIS GUARD ALONE: it fails closed towards "an UNDOCUMENTED ID
# COLLISION, or a corpus this guard could not verify it was reading, is a refusal". It asserts
# nothing about a directory's CONTENT, nothing about dead paths, and nothing about ownership
# predicates — those belong to the two guards below and they have their own directions.
#
# EXIT SEMANTICS, never conflated: 0 = every collision is documented; 1 = an undocumented
# collision exists; 2 = the guard could not reach or CALIBRATE its corpus. The calibration is
# P-72 and it runs BEFORE any verdict: the guard must re-find the known T256/T259 collision or
# it aborts, because a guard that cannot re-find the defect it was written for is not measuring
# the tree. run_guards folds ANY non-zero into failed=1 and exits EXIT_UNUSABLE — the correct
# reading is "no verdict is available", never "FAIL".
#
# COST: 0.4 s wall, measured on this host by T323.
guard_capture_namespace() {
  local g="$REPO_ROOT/.softhouse/guards/check-capture-namespace.sh"
  if [ ! -f "$g" ]; then
    warn "conformance: guard_capture_namespace: MISSING $g"
    warn "conformance: the capture/review namespace rule is UNGRADED. That is a HARD failure and"
    warn "conformance: never a pass: a guard that cannot reach what it grades has not graded it,"
    warn "conformance: and must not report PASS for lack of anything to check."
    return 1
  fi
  local here
  here="$(cd "$REPO_ROOT" 2>/dev/null && pwd -P)" || here=""
  if [ -z "$here" ]; then
    warn "conformance: guard_capture_namespace: cannot resolve \$REPO_ROOT ('$REPO_ROOT') to a"
    warn "conformance: physical path, so it cannot be compared with the tree the guard reports"
    warn "conformance: grading. An unanswerable question is not a clean answer. REFUSED."
    return 1
  fi
  # A FILE, not a pipe. `set -o pipefail` is in force at line 396 and every reader below is a
  # `sed`/`grep` over this file, so there is no early-exiting consumer for pipefail to invert
  # (P-57). The subshell is the cwd repair described above.
  local tf rc
  tf="$(mktemp "${TMPDIR:-/tmp}/conf-namespace.XXXXXXXXXX")" || {
    warn "conformance: guard_capture_namespace: could not create a scratch file. REFUSED."
    return 1
  }
  ( cd "$REPO_ROOT" && bash "$g" ) >"$tf" 2>&1
  rc=$?

  # WHICH TREE DID IT ACTUALLY GRADE? Read back, never assumed. An ABSENT root line is an
  # instrument failure and not a pass (P-81: an error is never an empty result).
  local claimed claimed_p
  claimed="$(LC_ALL=C sed -n 's/^namespace:   root    //p' "$tf")"
  if [ -z "$claimed" ]; then
    warn "conformance: guard_capture_namespace: the guard printed NO 'namespace:   root' line, so"
    warn "conformance: this harness cannot tell which tree it inspected. That is an INSTRUMENT"
    warn "conformance: FAILURE, not an absence of findings. REFUSED — full transcript follows."
    cat "$tf" >&2
    rm -f "$tf"
    return 1
  fi
  claimed_p="$(cd "$claimed" 2>/dev/null && pwd -P)" || claimed_p=""
  if [ "$claimed_p" != "$here" ]; then
    warn "conformance: guard_capture_namespace: THE NAMESPACE GUARD GRADED A DIFFERENT TREE."
    warn "conformance:   this harness grades: $here"
    warn "conformance:   the guard inspected: ${claimed_p:-<unresolvable: '$claimed'>}"
    warn "conformance: The guard resolves its root from 'git rev-parse --show-toplevel', which"
    warn "conformance: answers about the CALLER's working directory. This is T165/T201's defect"
    warn "conformance: and its result would describe a tree this run was not going to grade."
    cat "$tf" >&2
    rm -f "$tf"
    return 1
  fi

  if [ "$rc" -ne 0 ]; then
    cat "$tf" >&2
    warn "conformance: guard_capture_namespace FAILED (rc=$rc). Full transcript above."
    warn "conformance: rc=1 is an UNDOCUMENTED id collision; rc=2 is a corpus the guard could not"
    warn "conformance: reach or CALIBRATE. Neither is a FAIL verdict and neither is an oracle"
    warn "conformance: outage: run_guards exits 2 BEFORE the probe line is printed (P-84)."
    rm -f "$tf"
    return 1
  fi
  # The census line is echoed on the green path too. A guard that speaks only when it fires
  # cannot be told apart from one that never ran (P-22, P-35).
  LC_ALL=C sed -n 's/^/conformance:   /p' "$tf"
  rm -f "$tf"
  return 0
}

# -------------------------------------------------------------------------------------------
# guard_dead_path_frontier — T316's dead-path frontier guard, wired HARD.        [T323]
# -------------------------------------------------------------------------------------------
# WHAT IT ENFORCES: the set of tracked `.softhouse/` instruments naming a repo-relative path
# WHICH DOES NOT EXIST is PINNED, and it may not grow. Not zero — zero would be red on its
# first run and pinned away within a fire — but NO GROWTH, the same terms as
# FAILOPEN_PIN_FILE_LIST (line 1546) and HOSTSTATE_PIN_TEMP_ASSIGN_LIST (line 1852).
#
# THE SELF-REFERENTIAL PROPERTY IS THE WHOLE POINT AND IT WAS RE-VERIFIED THROUGH THE WIRING,
# NOT INHERITED. T316's guard checks EVERY path it itself depends on — the census instrument,
# the pin file, the scratch destination — and exits 2 if one does not resolve; it never passes
# for lack of anything to check. T323 did not take that on faith after wiring: it removed the
# census, and separately the pin, in a scratch clone and ran the WHOLE BAR, confirming exit 2
# with the oracle probe line ABSENT in each case. Evidence:
#   .softhouse/capture/t323-wire-the-unwired-guards/evidence/
#
# THE PIN AND THIS TREE DISAGREE, AND THE DISAGREEMENT IS P-83 EXACTLY — MEASURED, NOT COMPUTED.
#   P-83 — "TWO INDEPENDENT MOVEMENTS OF ONE PINNED NUMBER RECONCILE BY RUNNING, NEVER BY
#   ARITHMETIC."   [VERIFIED: .softhouse/patterns.md:2775]
# T316 re-derived its pin at 98 rows in commit 5b4f6702. T305's red drive
# `.softhouse/capture/t305-openingbalance-accepting-side/red-drive-conformance-guard.sh` landed
# separately in bb72b57b and names FOUR paths that do not resolve. T323 verified the two could
# not see each other: `git cat-file -e 5b4f6702:<that path>` reports the file ABSENT from the
# commit that set the pin at 98. On the merged tree the guard therefore reports
#     T316-DEADPATH-FRONTIER: REFUSED rows=102 pinned=98 added=4 removed=0
# and 102 is a MEASUREMENT taken by running the guard on the merge result — it is not 98 + 4.
#
# WHAT THE FOUR ROWS ARE, INSPECTED AND NOT INFERRED. All four belong to one file, T305's RED
# DRIVE, and all four are paths that drive CREATES at run time inside a throwaway clone:
#     :58  writes an ACCEPT ledger vector into  "$1/.softhouse/vectors/…/ACCEPT.json"
#     :59  writes a REFUSE ledger vector into   "$1/.softhouse/vectors/…/REFUSE.json"
#     :101 mkdir -p                             "$T6/.softhouse/capture/…/attest"
#     :102 echo "authorised" >                  "$T6/.softhouse/capture/…/attest/gerege.disposable"
#
# THOSE FOUR QUOTATIONS CARRY AN ELLIPSIS ON PURPOSE, AND THE REASON IS THIS GUARD CATCHING THIS
# COMMIT. T323's first draft quoted T305's lines VERBATIM, and the very first graded run after
# wiring went red with `added=7` rather than 4 — three of the new rows attributed to
# THIS FILE, because the census's selector matches any quoted string containing a
# `.softhouse/` path and this comment had become an instrument naming dead paths. The rule the
# guard prints was applied as written — "a '+' row is a NEW site: REPAIR it rather than pinning
# it" — so the quotations were repaired rather than the list widened to excuse them. The census
# treats `…` (ELLIPSIS_RE, census_dead_paths.py:73 — grep the SYMBOL, the line moves; T326
# rebuilt the resolver above it and this citation was stale at :66 within one fire) as "not a
# literal path", which is exactly
# what a shape-illustrating quotation is. This is the guard doing its job on its own wiring
# commit, recorded here rather than quietly fixed.
# A red drive plants a file that MUST NOT exist in a clean tree — that is what makes it a red
# drive — and `t999-rig` is a deliberately fictional task id. These are dead-by-design literals,
# the class T316's own header says must be "inspected once, by a human, and then either repaired
# or pinned with its reason". They are pinned here, with the reason, and the inspection above is
# the human one.
#
# WHY THE RECONCILIATION LIVES IN THIS FILE AND NOT IN THE PIN, STATED PLAINLY. The correct home
# for these four rows is `.softhouse/guards/dead-path-frontier.pin`. That file is OUTSIDE T323's
# edit grant (.softhouse/conformance.sh and .softhouse/capture/t323-wire-the-unwired-guards/),
# and wandering outside a grant is the scope violation this program treats as a rejection — the
# same constraint that left these three guards unwired in the first place. So the delta is
# carried HERE, in the file T323 does hold, in the shape of the two pins already in this file.
# WHOEVER NEXT HOLDS THE PIN SHOULD FOLD THESE FOUR ROWS INTO IT AND EMPTY THE LIST BELOW; the
# guard below FAILS if that is done without emptying the list, so it cannot rot into a double
# amnesty.
#
# IT IS A FRONTIER, NOT AN AMNESTY, AND THE LIST BELOW IS HELD TO THE SAME RULE (grep this
# file for the heading THE PIN IS A FRONTIER, NOT AN AMNESTY — T323 cited it as "line 1715"
# and T326 measured it at :1727, stale by 12; the line moves, the sentence does not. Quoted
# because the rule is that pin's and not this one's): "A '+' row is a NEW site: repair it
# … rather than pinning it. A '-' row is a site that was REPAIRED or DELETED, which is good
# news, and the pin must lose that row IN THE SAME COMMIT or it starts excusing a weakness that
# is no longer there." Concretely, this wiring REFUSES on every one of:
#   * the guard goes GREEN while the list below is non-empty  — the list has gone stale and is
#     now excusing rows that no longer exist. This is the anti-amnesty arm and it is why the
#     list cannot quietly outlive its subject;
#   * ANY row is REMOVED from the frontier (removed>0) — good news the pin must absorb;
#   * ANY added row is not, byte for byte, a member of the list below;
#   * the list below has a member that is not among the added rows;
#   * the guard's own `added=` cardinal disagrees with the number of '+' rows it printed — the
#     guard truncates its listing at 40 rows, and comparing against a TRUNCATED set would let
#     row 41 through. An unreadable listing is an ERROR, never a smaller set.
#
# FAIL-CLOSED DIRECTION, FOR THIS GUARD ALONE: it fails closed towards "any movement of the
# dead-path frontier that is not the one recorded and reasoned about here is a refusal". It does
# NOT judge whether a dead literal is a fail-open — T316 measured that it usually is not — and
# this wiring inherits that restraint rather than widening the predicate. P-95: "a dead literal
# is equally consistent with a fail-open and with an announced fallback, so it can never be
# classified by reading — only by removing every candidate and observing the exit."
# [VERIFIED: .softhouse/patterns.md:3084]. This guard COUNTS; it does not classify.
#
# WHY THIS GUARD GETS NO ROOT READBACK AND guard_capture_namespace DOES. A fair reviewer question,
# because the asymmetry looks like an oversight and is not. T299's guard resolves its root from
# `git rev-parse --show-toplevel`, i.e. from the CALLER'S WORKING DIRECTORY, which is a runtime
# fact this harness cannot constrain by construction — hence the subshell AND the readback. THIS
# guard derives its root from `$0`: dirname(dirname(dirname(script))). This wiring hands it
# "$REPO_ROOT/.softhouse/guards/check-dead-path-frontier.sh", so its root is $REPO_ROOT
# STRUCTURALLY, for every cwd, and a readback would be asserting a property of this line rather
# than measuring anything. Verified rather than assumed: run from a foreign cwd with the guard's
# path pointing into a worktree, it reported that WORKTREE's pin, where T299's guard reported the
# caller's tree [VERIFIED: T323 ran both].
#
# EXIT SEMANTICS: 0 frontier == pin; 1 a real measured movement; 2 a path this guard depends on
# did not resolve, or the census refused. T316's probe line `T316-DEADPATH-FRONTIER:` is printed
# on every path that REACHES A VERDICT and never on exit 2, so PRESENCE-BEFORE-VALUE applies to
# it exactly as P-84 requires, and this wiring tests presence first.
#
# COST: 1.3 s wall, measured on this host by T323.

# FOUR ROWS, ALL T305's, DERIVED by running the guard on the merged tree (P-83) and never typed
# from arithmetic. Empty this list in the same commit that folds the rows into
# .softhouse/guards/dead-path-frontier.pin.
#
# THE TEST FOR ANY ROW SOMEBODY WANTS TO ADD HERE, and T323 had to apply it to itself twice:
#
#     CAN THE INSTRUMENT STILL DO ITS JOB IF THE LITERAL GOES AWAY?
#       YES -> it is INCIDENTAL.  REPAIR it. Do not add a row.
#       NO  -> it is FUNCTIONAL.  Pin it, and write down which operation needs it.
#
# BOTH OF T323'S OWN CANDIDATES TURNED OUT TO BE INCIDENTAL, and finding that out cost two red
# runs, which is the reason the test is written here rather than assumed.
#
#   (a) This file's own PROSE. The frontier went red at added=7 because T323's comment quoted
#       T305's lines verbatim, making conformance.sh an instrument naming dead paths. The comment
#       illustrated a SHAPE and lost nothing by carrying an ellipsis. Repaired.
#
#   (b) T323's RED DRIVE, `.softhouse/capture/t323-wire-the-unwired-guards/drive-red-t323.sh`. It
#       is a tracked instrument, and it must name paths that do not resolve — planting them is its
#       function — so it looked FUNCTIONAL and was pinned at five rows. That was wrong, and the
#       drive itself proved it: arm `T299-02` CREATES the collision directory, so those literals
#       suddenly RESOLVED, the frontier LOST three rows, and this guard correctly refused with
#       "row(s) GONE from the frontier". The drive was perturbing the frontier its own sibling arm
#       was measuring. The DRIVE needs *a* directory and *a* non-resolving path; it never needed
#       those spellings. They are assembled at run time now, and the five rows are gone.
#
# The distinction that survives: (b) would have been genuinely functional if the literal had been
# the thing under test rather than a name chosen for it. Rewriting a literal into a runtime string
# to make a census go quiet, when the census is right, is defeating the instrument to flatter its
# own number — that is the pinning-away this frontier exists to prevent, and it is NOT what
# happened here. The check on that claim is arm `T316-05`, which still drives this guard red on a
# planted dead path; if the repair had blinded the census, that arm would have gone green.
# EMPTIED BY T326, IN THE SAME COMMIT THAT FOLDED THE FOUR ROWS INTO THE PIN. The pin was
# outside T323's edit grant and is inside T326's, so the handover T323 asked for above is done:
# the pin moved 98 -> 104 (T305's 4, plus 2 for T326's own cross-host drive), and the anti-amnesty
# arm below — which REFUSES if the guard is GREEN while this list is non-empty — is what makes
# "fold it in and empty the list" a single indivisible commit rather than a note somebody honours.
# THE LIST IS NOT DELETED, only emptied, so the arm keeps running and the next person who needs
# to carry a delta out of grant has the shape and the rules already written above.
DEADPATH_T323_RECONCILE_LIST=''

guard_dead_path_frontier() {
  local g="$REPO_ROOT/.softhouse/guards/check-dead-path-frontier.sh"
  if [ ! -f "$g" ]; then
    warn "conformance: guard_dead_path_frontier: MISSING $g"
    warn "conformance: the dead-path frontier is UNGRADED. HARD failure, never a pass."
    return 1
  fi
  local d rc
  d="$(mktemp -d "${TMPDIR:-/tmp}/conf-deadpath.XXXXXXXXXX")" || {
    warn "conformance: guard_dead_path_frontier: could not create a scratch directory. REFUSED."
    return 1
  }
  bash "$g" >"$d/out" 2>&1
  rc=$?

  # PRESENCE BEFORE VALUE (P-84). The probe line is printed on 0 and on 1 and never on 2, so its
  # absence together with rc!=2 is an instrument failure, not a finding.
  local probe
  probe="$(LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER: //p' "$d/out")"
  if [ "$rc" -ge 2 ]; then
    cat "$d/out" >&2
    warn "conformance: guard_dead_path_frontier REFUSED (rc=$rc): a path this guard DEPENDS ON did"
    warn "conformance: not resolve, or the census refused. This is the guard's self-referential"
    warn "conformance: arm working — it never reports PASS for lack of anything to check. It is"
    warn "conformance: NOT an oracle outage: this exits 2 before the probe line (P-84)."
    rm -rf "$d"
    return 1
  fi
  if [ -z "$probe" ]; then
    cat "$d/out" >&2
    warn "conformance: guard_dead_path_frontier: the guard exited $rc but printed NO probe line, so"
    warn "conformance: it did not reach a verdict. INSTRUMENT FAILURE, not an absence of findings."
    rm -rf "$d"
    return 1
  fi

  # The reconciliation list, normalised to one row per line, blank lines dropped.
  printf '%s\n' "$DEADPATH_T323_RECONCILE_LIST" >"$d/rec.raw"
  LC_ALL=C grep -v '^[[:space:]]*$' "$d/rec.raw" >"$d/rec.unsorted" 2>/dev/null || :
  [ -f "$d/rec.unsorted" ] || : >"$d/rec.unsorted"
  LC_ALL=C sort "$d/rec.unsorted" >"$d/rec"
  local rec_n
  rec_n="$(LC_ALL=C grep -ac '' "$d/rec" || true)"; [ -n "$rec_n" ] || rec_n=0

  if [ "$rc" -eq 0 ]; then
    if [ "$rec_n" -ne 0 ]; then
      cat "$d/out" >&2
      warn "conformance: guard_dead_path_frontier: THE T323 RECONCILIATION LIST HAS GONE STALE."
      warn "conformance: The guard is GREEN — frontier == pin — yet DEADPATH_T323_RECONCILE_LIST"
      warn "conformance: still carries $rec_n row(s) it is excusing. A pin is a frontier, not an"
      warn "conformance: amnesty (grep this file for THE PIN IS A FRONTIER, NOT AN AMNESTY — the"
      warn "conformance: line moves): a row that is no longer there must be dropped IN THE"
      warn "conformance: SAME COMMIT, or it starts excusing a weakness that no longer exists."
      warn "conformance: THE FIX: set DEADPATH_T323_RECONCILE_LIST='' in .softhouse/conformance.sh."
      rm -rf "$d"
      return 1
    fi
    say "conformance:   dead-path frontier: GREEN, and the T323 reconciliation list is empty."
    LC_ALL=C sed -n 's/^T316-DEADPATH-CENSUS:/conformance:   T316-DEADPATH-CENSUS:/p' "$d/out"
    rm -rf "$d"
    return 0
  fi

  # rc == 1: the frontier moved. It is admissible ONLY if the movement is exactly the recorded
  # one — nothing removed, and the added set equal to the reconciliation list, byte for byte.
  local added_n removed_n
  LC_ALL=C sed -n 's/.*added=\([0-9][0-9]*\).*/\1/p' "$d/out" >"$d/added_n"
  LC_ALL=C sed -n 's/.*removed=\([0-9][0-9]*\).*/\1/p' "$d/out" >"$d/removed_n"
  added_n="$(LC_ALL=C tail -1 "$d/added_n")"
  removed_n="$(LC_ALL=C tail -1 "$d/removed_n")"
  [ -n "$added_n" ]   || added_n=-1
  [ -n "$removed_n" ] || removed_n=-1
  LC_ALL=C sed -n 's/^> //p' "$d/out" >"$d/added.unsorted"
  LC_ALL=C sort -u "$d/added.unsorted" >"$d/added"
  local printed_n
  printed_n="$(LC_ALL=C grep -ac '' "$d/added" || true)"; [ -n "$printed_n" ] || printed_n=0

  local bad=0
  if [ "$added_n" -lt 0 ] || [ "$removed_n" -lt 0 ]; then
    warn "conformance: guard_dead_path_frontier: could not read the added=/removed= cardinals from"
    warn "conformance: the probe line. An unreadable measurement is an ERROR, never a zero (P-81)."
    bad=1
  elif [ "$printed_n" -ne "$added_n" ]; then
    warn "conformance: guard_dead_path_frontier: the guard reports added=$added_n but printed"
    warn "conformance: $printed_n '+' row(s). Its listing truncates at 40 rows, so the set this"
    warn "conformance: harness can see is INCOMPLETE and comparing against it would let row 41"
    warn "conformance: through. A truncated listing is an ERROR, never a smaller set. REFUSED."
    bad=1
  elif [ "$removed_n" -ne 0 ]; then
    warn "conformance: guard_dead_path_frontier: $removed_n row(s) GONE from the frontier. That is"
    warn "conformance: GOOD NEWS and the PIN must absorb it — a frontier, not an amnesty. This"
    warn "conformance: harness cannot absorb it for you: the pin is a TRACKED file, and folding a"
    warn "conformance: removed row into it belongs in the same commit that removed the path, so a"
    warn "conformance: reviewer sees the repair and the shrink together. [T358: this line used to"
    warn "conformance: say 'the pin is outside T323's edit grant', which stopped being true when"
    warn "conformance: T326 regenerated the pin — a false statement inside a refusal message.]"
    bad=1
  elif ! LC_ALL=C diff "$d/rec" "$d/added" >"$d/diff" 2>&1; then
    warn "conformance: guard_dead_path_frontier: THE FRONTIER MOVED IN A WAY NOBODY RECORDED."
    warn "conformance: The added rows are not the $rec_n row(s) DEADPATH_T323_RECONCILE_LIST"
    warn "conformance: reconciles. '>' below is a NEW dead path nobody has inspected — REPAIR it"
    warn "conformance: rather than pinning it; '<' is a recorded row that is no longer added and"
    warn "conformance: must be dropped from the list in the same commit."
    LC_ALL=C sed -n '1,40p' "$d/diff" >&2
    bad=1
  fi

  if [ "$bad" -ne 0 ]; then
    cat "$d/out" >&2
    warn "conformance: guard_dead_path_frontier FAILED. Full guard transcript above."
    rm -rf "$d"
    return 1
  fi

  say "conformance:   dead-path frontier: moved by exactly the $rec_n row(s) T323 recorded and"
  say "conformance:   inspected (T305's red drive, which CREATES those paths at run time), and by"
  say "conformance:   nothing else. removed=0. Fold them into the pin and empty the list."
  LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER:/conformance:   T316-DEADPATH-FRONTIER:/p' "$d/out"
  rm -rf "$d"
  return 0
}

# -------------------------------------------------------------------------------------------
# guard_reconciler_ownership — T319's reconciler selftest, wired HARD.           [T323]
# -------------------------------------------------------------------------------------------
# This is T319's own patch, from .softhouse/capture/t319-reconciler-f5/CONFORMANCE-WIRING.md,
# applied as written. T319 specified the guard body, the registration line, the measured cost
# and the argument for why `--selftest` cannot be optional. T323 did not redesign it.
#
# WHY IT IS HERE AT ALL. `.softhouse/bin/ready-tasks.py --reconcile` decides whether to rewrite
# `in_progress` tasks to `needs_retry`. Getting that wrong in the DEMOTING direction DESTROYS
# LIVE WORK AND CANNOT BE UNDONE. Until this commit not one line of conformance.sh mentioned
# `fire-program`, `ready-tasks`, `reconcile` or `in_progress` — measured, `grep -c` => 0, over
# 3,253 lines — so three consecutive attempts at that predicate shipped with NO automated
# coverage, and the third would have demoted seven live workers of the fire holding the lock.
#
# THE GUARD IS THE MATRIX, AND THE MATRIX CARRIES ITS OWN RED/GREEN. `--selftest` plants T309's
# shipped single-term predicate into a COPY of ready-tasks.py and REQUIRES cell B' — the cell
# whose clock advances across a re-dispatch — to go RED against it and GREEN against the shipped
# tool. It also refuses to run at all if no cell in its table advances the clock across a
# re-dispatch (`_assert_matrix_can_see_a_redispatch`, run-ownership-matrix.py:390, called at
# :434), so DELETING the cell that catches this class is a RED run rather than a smaller green
# one. T323 verified that assertion still fires THROUGH this wiring by neutering the redispatch
# cells in a scratch clone and running the whole bar; evidence in
# .softhouse/capture/t323-wire-the-unwired-guards/evidence/.
#
# `--selftest` IS NOT OPTIONAL, AND MAKING IT OPTIONAL WOULD REBUILD THE DEFECT. T319's argument,
# which T323 read before deciding and accepts: the RED leg is the ONLY thing distinguishing this
# guard from one that cannot fail (P-22), and a flag somebody sets on good days is P-45 by
# another name — "a guard that only works when someone remembers to run it enforces nothing".
# The whole reason this task exists is three guards that were correct and unreached.
#
# IT NEEDS A C COMPILER, AND FAILS RATHER THAN DEGRADING WITHOUT ONE. The matrix compiles a
# four-line exec shim so each cell can CONSTRUCT the `claude` / non-`claude` ancestry that
# selects `in_session` vs `wrapper` mode. Without it every cell would silently run in whatever
# mode the ambient process tree happened to give — green in one hand, meaningless in the other.
# /usr/bin/cc and /usr/bin/python3 are present on this host [VERIFIED: T323, `ls -la`].
#
# FAIL-CLOSED DIRECTION, FOR THIS GUARD ALONE: it fails closed towards "the ownership predicate
# that can demote live work is UNGRADED, or grades wrongly, is a refusal". It says nothing about
# namespaces and nothing about dead paths.
#
# A NON-ZERO EXIT MEANS THE PREDICATE IS UNGRADED. That is not a FAIL verdict and it is not an
# oracle outage: it exits 2 through run_guards BEFORE the `reference oracle (…) probe = …` line
# is printed, so the driver's park condition (exit 2 AND a probe line PRESENT reading `down`) is
# not met. P-84 — read the ABSENCE, not the value.
#
# COST, MEASURED [T319 in .softhouse/capture/t319-reconciler-f5/, re-measured by T323 here]:
#   green leg only          14.7 s  (13 cells)         [T319]
#   with --selftest         29.9 s  (26 cells)         [T319]
#   with --selftest         30.3 s  (26 cells)         [T323, this host, this tree]
# It is by a wide margin the most expensive guard in this file and it is the only one standing
# between a broken predicate and destroyed work.
guard_reconciler_ownership() {
  local rig="$REPO_ROOT/.softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py"
  local tool="$REPO_ROOT/.softhouse/bin/ready-tasks.py"
  if [ ! -f "$rig" ]; then
    warn "conformance: guard_reconciler_ownership: $rig is MISSING. The reconciler's ownership"
    warn "conformance: predicate is UNGRADED. This is a HARD failure, not a pass: the last three"
    warn "conformance: versions of that predicate each shipped able to demote live workers, and"
    warn "conformance: the rig is what catches it."
    return 1
  fi
  if [ ! -f "$tool" ]; then
    warn "conformance: guard_reconciler_ownership: $tool is MISSING. There is nothing to grade,"
    warn "conformance: which is a REFUSAL and never a pass."
    return 1
  fi
  if [ ! -x /usr/bin/python3 ]; then
    warn "conformance: guard_reconciler_ownership: /usr/bin/python3 is absent. The matrix cannot"
    warn "conformance: run. It REFUSES rather than degrading to a smaller green."
    return 1
  fi
  local tf rc
  tf="$(mktemp "${TMPDIR:-/tmp}/conf-reconciler.XXXXXXXXXX")" || {
    warn "conformance: guard_reconciler_ownership: could not create a scratch file. REFUSED."
    return 1
  }
  /usr/bin/python3 "$rig" --repo "$REPO_ROOT" --tool "$tool" --selftest >"$tf" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ]; then
    cat "$tf" >&2
    warn "conformance: guard_reconciler_ownership FAILED (rc=$rc). Full transcript above."
    warn "conformance: Either a cell of the ownership matrix disagreed with the shipped tool, or"
    warn "conformance: the planted T309 defect FAILED TO DRIVE THE MATRIX RED — a guard that"
    warn "conformance: cannot fail is worse than none (P-22) — or the matrix refused because no"
    warn "conformance: cell in its table can see a re-dispatch."
    rm -f "$tf"
    return 1
  fi
  # PRESENCE BEFORE VALUE. The rig's terminal attestation must be there; a zero exit with no
  # attestation is an instrument failure, not a pass.
  if ! LC_ALL=C grep -q '^SELFTEST OK:' "$tf"; then
    cat "$tf" >&2
    warn "conformance: guard_reconciler_ownership: the matrix exited 0 but printed NO 'SELFTEST OK'"
    warn "conformance: attestation, so both legs did not run. INSTRUMENT FAILURE, not a pass."
    rm -f "$tf"
    return 1
  fi
  local green red
  green="$(LC_ALL=C sed -n 's/^GREEN LEG (shipped tool): //p' "$tf")"
  red="$(LC_ALL=C sed -n 's/^RED LEG (planted T309 defect): //p' "$tf")"
  say "conformance:   reconciler ownership: GREEN ${green:-<unreported>} / RED ${red:-<unreported>}"
  say "conformance:   (the planted T309 single-term predicate drives cell B-prime RED; the shipped"
  say "conformance:   tool keeps it GREEN. Both legs ran here — --selftest is not optional.)"
  rm -f "$tf"
  return 0
}

# -------------------------------------------------------------------------------------------
# guard_guards_dir_registration — THE CANONICAL GUARDS DIRECTORY IS ITSELF GRADED.      [T323]
# -------------------------------------------------------------------------------------------
# WHY THIS EXISTS, and why it is WIRING rather than a new detector. T323 was filed because THREE
# workers in one fire each built a guard, drove it red and green, and shipped it reaching
# nothing. That is P-45 — "A test-only guard is not a guard. … Rule: when hardening a check,
# verify the path that actually executes in CI/conformance calls it, not merely that a test
# does." [VERIFIED: .softhouse/patterns.md:1503]. The three were wired above, one at a time, by
# hand. NOTHING IN THIS FILE STOPPED A FOURTH, and the fix for "someone must remember" is never
# a better memo.
#
# So this grades the one population where grading it is cheap AND honest: the tracked shell
# checkers sitting DIRECTLY IN .softhouse/guards, the directory this program has made the home
# of its checkers. Every member must either be INVOKED BY THIS FILE, or carry a DECLARATION in
# the table below saying what its relation to the harness actually is — and the declaration is
# VERIFIED, never believed: the witness file must exist and the naming must be real, in the
# stated direction. A declaration whose SUBJECT HAS VANISHED is also a failure, so the table
# cannot rot into a blanket suppressor. That is the mechanism T145's float guard uses for its
# two declared sites and the one patterns.md uses for its declared-collision register.
#
# SELECTOR, PRINTED BESIDE THE FIGURE, because a count is a statement about a search and never
# about the world — P-70, "'Latent', 'not promoted', 'can never resolve', 'no guard exists' —
# four ways this program stated a search result as a world fact, in one fire"
# [VERIFIED: .softhouse/patterns.md:1931]:
#
#     POPULATION = git ls-files, ':(glob)' magic, over the TRACKED '*.sh' / '*.py' / '*.go'
#                  files at ANY DEPTH under the canonical guards directory, from $REPO_ROOT.
#     INVOKED    = the member's REPO-RELATIVE PATH occurs on a NON-COMMENT line of this file.
#                  NOT its basename — a basename is shared, a path identifies. [T375, T364 F-1.]
#     DECLARED   = a row in the table inside this function (directions CALLER and SUBJECT).
#     REACHED-BY = a row in the MEMBER'S OWN header, naming a tracked witness that names it.
#                  The witness path is NORMALISED by git before it is compared to anything,
#                  so './M', 'a/../M' and the absolute spelling are all the same path as 'M'
#                  and a member cannot vouch for itself in a different spelling. [T375, T364 F-2.]
#
# WHAT THE SELECTOR DOES NOT REACH, stated in the same breath as what it does, because the
# previous wording of this block did not and a reader concluded a class was closed that was not
# [T337 F-T337-3, repaired by T358]. It does not reach: any checker written in a language other
# than shell, Python or Go; any committed binary; and anything outside this one directory.
#
# THE TWO THINGS T375 CHANGED HERE, both of them fail-OPENs T364 found by FORGING them through
# the whole bar against controls, and both of them wrong PASSes about THIS GUARD'S OWN COVERAGE
# rather than about money or any graded quantity:
#   1. INVOKED matched the member's BASENAME. `main.go` occurs on two non-comment lines of this
#      file where a different guard reads that file's text, so ANY unwired Go checker named
#      `main.go`, at any depth here, read INVOKED and the bar stayed GREEN — while the identical
#      file under a unique basename was refused. Closing `.go` was T358's whole point and this
#      missed it by one identifier. INVOKED now matches the member's repo-relative PATH.
#   2. The REACHED-BY self-certification test was a RAW STRING COMPARE while every other step in
#      that chain normalised, so the rule this guard PRINTS — "a file may not vouch for itself" —
#      was defeated by a leading './'. The compare is now on the path GIT resolves.
# Both are driven RED, in both directions, with controls, by T375's red drive.
#
# THE THREE THINGS T358 CHANGED HERE, each of which was a defect in what this block CLAIMED
# rather than in what the code did — which is the more dangerous kind, because the claim is
# what the next author builds on:
#   1. The pathspec had no ':(glob)' magic, so '*' crossed '/' and the search was ALREADY
#      any-depth while the printed line said "the members of" one directory. An ordinary Go
#      test fixture under the ledgerguard module therefore took the whole bar to exit 2.
#   2. The population was '*.sh' alone while the handoff claimed "a fourth unwired checker
#      cannot land". A Go checker lives in this directory today and Python checkers are
#      routine here; both were outside the population by construction.
#   3. Every remedy the guard printed required editing THIS file, which the program serialises.
#      See the REACHED-BY block inside the function for that argument in full.
#
# THE SECOND CLAUSE IS NOT PEDANTRY. Every unwired guard this program has shipped was MENTIONED
# somewhere — T257's own finding is that `git grep -n manifest -- conformance.sh` returned ONE
# hit and it was a COMMENT at :450. A predicate that accepts a mention would have called that
# guard wired. Comment lines are therefore excluded from the invocation test, and the DECLARED
# rows below are matched BEFORE it so that this guard's own table cannot vouch for itself.
#
# IT IS DELIBERATELY NARROW AND THE NARROWNESS IS MEASURED, not timid. It does NOT claim to find
# every unwired checker in this repository. T323 ran four of them by hand on this tree and every
# one is invoked by nothing automatic:
#     .softhouse/capture/t145-analysis-float/bin/guard-float-decides-money.py     exit 0 (GREEN)
#     .softhouse/capture/t284-schema2-callsites/instruments/10-callsite-registry.py exit 1 (RED)
#     .softhouse/capture/t287-closure-refusals/guard-probe-expiry.sh              exit 1 (RED)
#     .softhouse/capture/tierA-a2/manifest.py verify                              exit 1 (RED)
# Three of those four are RED ON TODAY'S TREE, so a selector wide enough to reach them would
# make this guard red on arrival — the "switched off within two fires" outcome T323 already
# refused once, for T304's destructive-site census. Their wiring is one named task each
# (T333, T303, T311, T257) and each needs its own tier argument and its own repair first.
#
# WHAT IT DOES CLAIM, exactly one thing, AND THE SCOPE OF THE CLAIM IS PART OF THE CLAIM: NO NEW
# TRACKED SHELL, PYTHON OR GO FILE CAN ENTER THE CANONICAL GUARDS DIRECTORY, AT ANY DEPTH,
# WITHOUT EITHER BEING RUN BY THIS FILE, BEING DECLARED IN THE TABLE BELOW, OR CARRYING A
# VERIFIED REACHED-BY ROW IN ITS OWN HEADER — IN A DIFF A REVIEWER READS.
#
# It does NOT claim that "a fourth unwired checker cannot land", which is how T323's handoff put
# it and which is false in two directions: a checker in a fourth language is outside the
# population, and a file inside the population is only proven NAMED, never proven EXECUTED.
#
# THE "NAMED, NOT EXECUTED" GAP HAS A CONCRETE INSTANCE ON THIS TREE, and it is written down
# rather than left for the next reader to trip over [T337 F-T337-4, instanced by T358].
# `.softhouse/guards/ledgerguard/main.go` is a checker that this harness NEVER RUNS — it is
# built and run by check-ledger-invariants.sh — yet its FULL REPO-RELATIVE PATH occurs on a
# non-comment line here at conformance.sh:1484, `local ccsrc="$REPO_ROOT/…/ledgerguard/main.go"`,
# where a DIFFERENT guard reads its text. Absent its REACHED-BY row, main.go would read INVOKED
# off that assignment — and it still would after T375 tightened the test from basename to path,
# because that line does spell this member's own path. The row records the truth; the invocation
# test would have accepted a convenient fiction. Tightening the test to require an executed call
# is NOT done here: two of the three genuinely-invoked members are reached through `bash "$g"`
# after a `local g=` assignment, so an execution test needs dataflow this harness has no business
# growing. The honest move is to say what the test measures, which the printed selector does.
#
# WHAT T375's PATH TIGHTENING DID AND DID NOT DO TO THIS GAP, because the two are one word apart.
# It did NOT close "named, not executed" — the line above is exactly that gap and it survives. It
# DID close the strictly larger hole T364 found underneath it: before T375 the test matched the
# BASENAME, so this ONE line about THIS ONE file absolved EVERY file called `main.go` anywhere
# under the guards directory. The gap is now confined to the file the line actually names.
#
# WHY THIS POPULATION IS PINNABLE WHERE T304'S WAS NOT — the question T323 had to answer before
# it was allowed to build this at all. T323's refusal of T304's census rested on a MEASURED
# property: T304 classifies a site by RESOLVING its target against the whole tracked corpus, so
# rows move for reasons no diff contains (three instruments last touched days before T304's
# census began contributing hard sites without a byte of them changing). This population has no
# such property. Membership is "a tracked file of one of three extensions, under one directory",
# so a row can appear or disappear ONLY in the commit that adds, removes or renames that file.
# Attributable by construction, which is the whole difference — and widening the population from
# one extension to three in T358 does not touch that property, because it is a property of how
# membership is DECIDED and not of how many files satisfy it.
#
# FAIL-CLOSED DIRECTION, FOR THIS GUARD ALONE, and not widened to serve a second purpose: it
# fails closed towards "a checker sitting in the guards directory that this harness does not
# run, and that does not say what does, is a refusal". It asserts nothing about what any checker
# checks, nothing about namespaces, dead paths or ownership predicates — those are the three
# guards above and they have their own directions — and nothing whatever about money.
#
# CALIBRATION BEFORE VERDICT. If NOT ONE member is found invoked by this file, the reading
# mechanism is broken rather than the tree being clean: three members are invoked verbatim a few
# hundred lines above. Zero invoked is a REFUSAL, never a green.
#
# THE CALIBRATION EARNED ITS KEEP ON THE FIRST GRADED RUN, and the episode is recorded rather
# than tidied away. T323's first version tested invocation with `printf … | grep -qF`. Standalone
# it printed three INVOKED and a PASS. Through the bar it reported ALL THREE genuinely invoked
# checkers as unwired and refused at the calibration: `grep -q` exits on the first match, `printf`
# dies of SIGPIPE, and `set -o pipefail` (conformance.sh:396) turns the pipeline's 141 into a
# MISS. That is P-57's EPIPE family, in a guard written a few hundred lines under a comment
# warning about it. Two lessons are load-bearing here. (1) A standalone green says nothing about
# the wired route — which is the whole thesis of T323 — and here the standalone leg was green
# while the wired leg refused. (2) The refusal was the guard's OWN vacuity arm, not a downstream
# symptom: without it the run would have printed three plausible "IS INVOKED BY NOTHING" findings
# about correctly wired checkers, and the next worker would have "fixed" the tree.
#
# P-84 SURVIVES UNCHANGED, AND T358 RE-VERIFIED IT STRUCTURALLY AFTER EDITING, NOT FROM
# TRANSCRIPTS [P-45 — cite the call site by file and line]:
#   run_guards is DEFINED at conformance.sh:4090 and CALLED at exactly one site, :4585, as a
#   bare command — not in a subshell and not in a command substitution — so the two `exit`s
#   inside it, the short-circuit at :4109 and the tally at :4143, terminate the whole shell
#   rather than returning a status;
#   probe_oracle is invoked at exactly one site, :4610, and the probe line is printed at :4611,
#   both strictly DOWNSTREAM of :4585.
#   guard_cost_census is called from run_guards at :4140, upstream of the tally exit at :4143,
#   so a WALL-CLOCK CEILING BREACH is also exit 2 with NO probe line and is read by P-84's rule
#   exactly like any other HARD refusal.
#
#   [RE-DERIVED BY T375 PASS 2 AFTER ITS OWN EDITS, WHICH MOVED EVERY ONE OF THESE NUMBERS AGAIN
#   — pass 1 re-derived them once and pass 2 shifted them by a further ~90 lines, so the figures
#   pass 1 wrote were already citations to nothing by the time pass 2 committed. P-45 cites a
#   call site by line; a line cited before the edit that shifts it is a citation to nothing, and
#   THIS BLOCK HAS NOW ROTTED TWICE INSIDE ONE TASK. That is not an argument for re-deriving
#   more carefully; it is the standing evidence for the rule the driver adopted in this fire
#   after measuring a 546-line shift in this same file: MATCH BY NAME, NEVER BY LINE. Every
#   identifier above is unique in this file and `grep -n` re-derives the whole block in one
#   command. T364's NOTE-2 is also settled here: T358's block named a single exit that was
#   guard_graded_root_is_this_tree's SHORT-CIRCUIT, not the TALLY exit a failed
#   guard_guards_dir_registration actually takes. BOTH are named above, because both are inside
#   run_guards and either one is upstream of the probe — which is the property that matters and
#   the reason T364 graded it mechanical.]
# There is therefore no path on which a HARD guard fails and the probe line is printed.
# This returns 1 into run_guards' tally, which exits EXIT_UNUSABLE
# BEFORE probe_oracle prints, so a failure here is exit 2 with NO probe line — "'EXIT 2 WITH NO
# PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."
# [VERIFIED: .softhouse/patterns.md:2813]. That is a failed HARD guard and NOT an oracle outage;
# the driver's park condition needs exit 2 AND a probe line PRESENT reading down. P-84 draws
# that one distinction and says nothing about money in either direction.
#
# COST: MEASURED AND PRINTED ON EVERY RUN by guard_cost_census, which reports this function's
# elapsed wall clock beside a ceiling that REFUSES. THE NUMBER IS NOT RETYPED HERE, and its
# absence is the repair, not an omission [T375, FU-T358-1 / C-T364-4].
#
# THE HISTORY THAT MADE THAT THE RIGHT CALL, kept because it is the whole argument. This comment
# used to carry a hand-written figure: T323 wrote 0.16 s, T337 independently measured 0.064 s for
# the operations as they then stood, T358 measured 0.23 s after widening the population, T364
# re-measured 0.297 s under contention from its own drive. Four numbers, four authors, none of
# them checked by anything. And in the very fire that produced the last two, the first version of
# the table-cut block below ran at 99.7% CPU FOR OVER NINE MINUTES and had to be killed — while
# this comment still read 0.23 s. A cost claim nothing measures is not a weak guard; it is a
# claim with no arm at all, and the only detector of that spin was a human noticing.
#
# The operations whose cost the census now reports, listed because the SHAPE is what a reader
# needs and the shape does not rot: one `git ls-files` with three pathspecs, one comment-stripping
# grep over this file, one `grep -vF` per DECLARATION TABLE row to cut the table out of the
# haystack, one marker grep per member, one witness grep and one `git ls-files --error-unmatch`
# per DECLARED or REACHED-BY row. No temporary file, no pipeline, no second process in the
# invocation test.
guard_guards_dir_registration() {
  local gdrel=".softhouse/guards"
  local gd="$REPO_ROOT/$gdrel"
  local conf="$REPO_ROOT/.softhouse/conformance.sh"
  if [ ! -d "$gd" ]; then
    warn "conformance: guard_guards_dir_registration: $gd is MISSING. The canonical guards"
    warn "conformance: directory IS the thing this grades; with it absent there is nothing to"
    warn "conformance: check, which is a REFUSAL and never a pass."
    return 1
  fi
  if [ ! -f "$conf" ]; then
    warn "conformance: guard_guards_dir_registration: $conf is MISSING, so this harness cannot"
    warn "conformance: read itself and cannot say which checkers it invokes. REFUSED."
    return 1
  fi

  # The pathspec is ASSEMBLED AT RUN TIME rather than spelled as one literal. Not cosmetic: this
  # file sits in T316's dead-path corpus, and a glob spelled whole reads there as a path that
  # resolves to nothing. T323's own red drive learned that the expensive way — its first version
  # put five rows on the frontier.
  #
  # ':(glob)' MAGIC IS LOAD-BEARING AND IS NOT A NARROWING [T358, from T337 F-T337-1].
  # A git pathspec WITHOUT ':(glob)' is fnmatch WITHOUT FNM_PATHNAME, so '*' matches '/' as
  # well. T323 wrote the selector as one trailing '*.sh' and PRINTED it as "the members of"
  # this one directory, while the search it actually ran swept every tracked shell file at ANY
  # DEPTH beneath it — including inside the ledgerguard GO MODULE that lives here. An ordinary
  # Go test fixture, `ledgerguard/testdata/setup.sh`, therefore turned the WHOLE BAR to exit 2.
  # [T358 MEASURED on this tree with that fixture planted: the un-magic pathspec returns 6
  # members, ':(glob)' with a single trailing segment returns 5, ':(glob)' with '**/' returns 6.]
  #
  # THE DEPTH IS KEPT, DELIBERATELY, and this is where T358 declines the one-token patch T337
  # offered. Spelling the pathspec as one trailing segment fixes the misdescription by DELETING
  # the coverage: a genuine unwired checker one directory down would then be invisible, which
  # trades T337's F-1 for a larger F-3. So the glob says '**/' — the depth is now DECLARED
  # rather than inherited from an fnmatch accident — and the friction the depth creates is
  # answered by the REACHED-BY direction below, which is a remedy the tripping task can perform
  # inside its own edit grant. Coverage is paid for with an in-grant remedy, never with a
  # narrower search.
  #
  # THE POPULATION IS NO LONGER SHELL-ONLY [T358, from T337 F-T337-3]. T323's handoff claimed
  # "a fourth unwired checker cannot land"; the population was '*.sh' alone, and this directory
  # contains a Go checker TODAY (the ledgerguard module) plus this program writes checkers in
  # Python routinely. Shell, Python and Go are all in the population now. WHAT IS STILL OUTSIDE,
  # stated because a count is a statement about the search: any other language, and any
  # committed binary. The class closed is "tracked .sh / .py / .go sources under this directory,
  # at any depth" — NOT "every checker".
  local pop
  pop="$( cd "$REPO_ROOT" 2>/dev/null && git ls-files -- \
            ":(glob)$gdrel/"'**/*.sh' \
            ":(glob)$gdrel/"'**/*.py' \
            ":(glob)$gdrel/"'**/*.go' 2>/dev/null )"
  if [ -z "$pop" ]; then
    warn "conformance: guard_guards_dir_registration: the population is EMPTY. That is a SELECTOR"
    warn "conformance: failure, not a clean tree — this repository tracks shell checkers in"
    warn "conformance: $gdrel and always has. An empty census passes everything. REFUSED."
    return 1
  fi

  # This file with every comment line removed. The invocation test reads THIS, not the file, so
  # a checker that is only ever discussed is not counted as run.
  local code
  code="$(LC_ALL=C grep -v '^[[:space:]]*#' "$conf")"
  if [ -z "$code" ]; then
    warn "conformance: guard_guards_dir_registration: stripping comments from $conf left NOTHING."
    warn "conformance: That is an instrument failure — this file is mostly executable text — and"
    warn "conformance: an empty haystack would report every checker unwired. REFUSED."
    return 1
  fi

  # DECLARATION TABLE. One row per member this file does NOT invoke, in the form
  #   <basename>|<direction>|<witness path, repo-relative>|<token that must be present>
  # direction CALLER  — the witness is what RUNS the member; the WITNESS must name the token.
  # direction SUBJECT — the member is not a guard but an instrument ABOUT the witness; the
  #                     MEMBER must name the token.
  # Both are verified below. Neither is a suppression: if the witness disappears, or stops
  # naming the token, or the declared member itself leaves the population, this guard goes RED.
  #
  # ────────────────────────────────────────────────────────────────────────────────────────
  # THERE IS A THIRD DIRECTION AND ITS ROW DOES NOT LIVE IN THIS FILE. Read this before
  # touching either of the two rows below. [T358, answering T337 F-T337-2.]
  #
  # THE DEFECT: both remedies T323's guard printed — "call it from run_guards" and "add its row
  # to the DECLARATION TABLE" — require editing .softhouse/conformance.sh, and this program
  # SERIALISES this file to one holder per batch. So the task that trips the guard could not
  # lawfully fix it. That is not hypothetical: check-capture-namespace.sh's own header says
  # wiring itself here "would be the scope violation this program treats as a rejection", which
  # is the entire reason T299's guard sat unwired until T323 was granted this file.
  #
  # T323's argument for HARD — "a guard whose remedy is 'say the thing the rule is asking for'
  # is not a blocker, it is the rule" — is SOUND FOR T299, whose remedy is an OWNER*.md inside
  # the tripping task's own directory. It DOES NOT TRANSFER to a guard whose only remedies are
  # edits to a file the tripping task is forbidden to open. A HARD guard whose remedy is
  # out-of-grant is not a bar; it is a bar that gets switched off, and the guard would then be
  # the very thing it was written to prevent.
  #
  # THE FIX IS THE REMEDY, NOT THE SEVERITY. Direction REACHED-BY lets the MEMBER carry its own
  # row, in its own header, on one line:
  #
  #     GUARDS-DIR-REGISTRATION: REACHED-BY <witness path, repo-relative>
  #
  # and the guard then verifies, below, that the witness EXISTS, is TRACKED, is A REGULAR FILE
  # AND NOT A SYMLINK, is NOT the member itself IN ANY SPELLING, is NOT A COPY OR HARD LINK OF
  # the member, and NAMES THE MEMBER'S BASENAME. That is the same evidentiary standard as a CALLER
  # row — the row's LOCATION moved, its burden of proof did not — and the excuse now travels in
  # the same diff as the file it excuses, which is a strictly smaller blast radius than a table
  # in this file where one task can excuse another task's file.
  #
  # ALTERNATIVES REJECTED, named so this is not re-litigated as a preference:
  #   * MAKE IT SOFT. Rejected. The defect T323 existed to close is three finished guards that
  #     reached nothing and nobody noticed for three fires. A warning nobody must act on is
  #     that same non-event with a line of output. SOFT is also what T299 explicitly rejected
  #     for its own guard, on the identical ground.
  #   * MOVE THE WHOLE REGISTRATION RECORD OUT, into a shared .softhouse registry file.
  #     Rejected on three counts. (1) It only relocates the serialisation point — a single
  #     shared registry becomes the next contended file. (2) It is a suppression LIST: it lets
  #     one task excuse a file it does not own, and it grows without the excuse ever appearing
  #     beside the thing excused. (3) It has a bootstrap hole — the registry would itself sit
  #     in this directory, and nothing would guard the guard's own registry.
  #   * DROP THE DEPTH so fixtures cannot trip it (T337's one-token patch, applied alone).
  #     Rejected above at the selector: it buys the remedy problem away by not looking.
  #
  # WHAT REACHED-BY IS NOT: it is not proof of execution, and it is not self-certification. A
  # member may not vouch for itself, and a witness that stops naming the member turns this
  # guard RED at the next graded run — the declaration is re-verified every run, never trusted
  # once.
  #
  # "A MEMBER MAY NOT VOUCH FOR ITSELF" HAS NOW BEEN FALSIFIED AS IMPLEMENTED FOUR TIMES, AND
  # THE COUNT IS KEPT HERE BECAUSE IT IS THE ARGUMENT. T364 forged the row with a leading './'
  # and with an interior '/../' — a raw string compare where every other step normalised. T375
  # pass 1 fixed the compare and, asking what its OWN arms missed by one, T375 pass 2 found
  # THREE MORE, all measured with the whole bar GREEN: a witness that is a SYMLINK to the
  # member (git resolves a symlink to its own path, `grep` dereferences), a HARD LINK to it,
  # and a plain COPY of it (one blob under two names). Each was one line inside the tripping
  # task's own grant. THE LESSON THAT GENERALISES, and the reason every one of these is now
  # driven by its own arm rather than argued: THE WITNESS IS IDENTIFIED BY A PATH, AND A PATH
  # IS NOT A FILE — every fix so far tightened the resolution of the NAME while leaving open
  # another route by which the member's own bytes come back as somebody else's testimony. The
  # next reader should assume there is a fifth and go looking for it, not conclude from this
  # paragraph that the class is now shut.
  # ────────────────────────────────────────────────────────────────────────────────────────
  #
  # ROW 1 — repo-state-attest.sh [T318 / FU-T304-2, adopted by T325]. A DIFFERENTIAL repo-state
  # attestation, used AROUND an operation (snapshot, run, compare against the operation's writ).
  # It cannot be a verdict guard in a harness that grades ONE state; its caller is the fire
  # driver, which is where the before/after pair exists.
  # ROW 2 — drive-red-ledger-invariants.sh. NOT a guard: it is the P-22 RED DRIVE for
  # ledgerguard, planting one violation per class into a scratch copy of nexus/. Calling it from
  # run_guards would mean every graded run drives its own money guard red on purpose.
  local DECLARED
  DECLARED="repo-state-attest.sh|CALLER|.softhouse/bin/fire-program.sh|repo-state-attest.sh
drive-red-ledger-invariants.sh|SUBJECT|.softhouse/guards/ledgerguard/main.go|ledgerguard"

  local total=0 invoked=0 decl_ok=0 selfdecl=0 unwired=0 bad=0
  # SYMLINK MEMBERS GET THEIR OWN COUNTER RATHER THAN JOINING `unwired`. [T375 pass 2.] They are
  # not "invoked by nothing" — they are not gradeable at all — and folding a second finding into
  # an existing cardinal is how a census stops showing what it found. IT IS PRINTED AT THE END
  # OF THE CENSUS LINE, DELIBERATELY: every arm in the T323, T358 and T375 drives matches that
  # line by a substring ending at `invoked-by-nothing=N`, so appending cannot silently retune an
  # older arm — a new field in the MIDDLE would have.
  local symlinked=0
  local rel base row rowbase dir witness token found
  local self_row self_wit self_norm self_multi
  local self_stat self_mode self_blob member_stat member_mode member_blob
  # One literal newline, so the multi-line test below is a `case` pattern and starts no second
  # process. Spelled once, here, rather than inside the pattern where it reads as a typo.
  local CONF_LF
  CONF_LF="$(printf '\nx')"; CONF_LF="${CONF_LF%x}"

  # THE DECLARATION TABLE'S OWN TEXT IS CUT OUT OF THE HAYSTACK BEFORE THE INVOCATION TEST.
  # [T358.] T323 already matched DECLARED rows first "so that the table's own text cannot
  # satisfy the invocation test below and vouch for its own SUBJECT" — but that only protects
  # the row's subject. A row also names a WITNESS PATH, and the invocation test is a substring
  # match, so row 2's witness column (`…/ledgerguard/main.go`) would report main.go INVOKED —
  # i.e. one member absolved because a DIFFERENT member's excuse happens to name it. Nothing in
  # the table is a call site, so nothing in the table belongs in the haystack.
  #
  # `grep -vF` OVER A HERE-STRING, AND THE FIRST ATTEMPT IS RECORDED BECAUSE IT WAS A DISASTER
  # AND ONLY THE WIRED RUN CAUGHT IT. T358 first wrote this as pure parameter expansion,
  # `code="${code//"$row"/}"`, reasoning that no second process means no pipeline and no P-57
  # EPIPE surface. That reasoning was right and the code was still unusable: bash's pattern
  # substitution over a ~200 KB string is quadratic, and the guard — advertised in run_guards at
  # under a fifth of a second — SPUN AT 99.7% CPU FOR OVER NINE MINUTES on two rows before it
  # was killed. A grading instrument nobody will wait for is a grading instrument that gets
  # bypassed, which is the same failure as switching the guard off. THE LESSON IS THE ROUTE, NOT
  # THE IDIOM: the standalone reasoning was clean and the whole-bar run refused to finish, which
  # is T323's own thesis pointed back at T358.
  #
  # AND THE SECOND LESSON, WHICH IS THE ONE T375 ACTED ON: the only detector of that nine-minute
  # spin was a human noticing. The advertised figure was a comment, and a comment is not an arm.
  # `guard_cost_census` now measures this function's wall clock on every graded run and REFUSES
  # over a ceiling, so a spin that RETURNS is a named refusal rather than a silent pass. It still
  # cannot interrupt one that never returns — see that function's own statement of its limit.
  #
  # A HERE-STRING IS NOT A PIPELINE, so this keeps the P-57 property the parameter expansion was
  # chosen for: there is no upstream writer to take EPIPE, and `grep -v` consumes all of its
  # input rather than exiting on first match. Two rows, two greps, milliseconds.
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    code="$(LC_ALL=C grep -vF -- "$row" <<<"$code")"
  done <<TABLETEXT
$DECLARED
TABLETEXT
  if [ -z "$code" ]; then
    warn "conformance: guard_guards_dir_registration: cutting the DECLARATION TABLE out of the"
    warn "conformance: haystack left NOTHING. That is an instrument failure — an empty haystack"
    warn "conformance: would report every member unwired. REFUSED."
    return 1
  fi

  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    total=$((total + 1))
    base="${rel##*/}"

    # THE MEMBER'S OWN INDEX ENTRY IS READ FIRST, AND A MEMBER THAT IS A SYMLINK IS REFUSED
    # BEFORE ANY OTHER TEST TOUCHES IT. [T375 pass 2. DRIVEN: arm T375-30 was written expecting
    # this to be fail-CLOSED already, and it FAILED — exit 0, probe PRESENT — which is how this
    # was found. The arm is kept at its original expectation and now passes for the right
    # reason.]
    #
    # THE DEFECT, AND IT IS THE WORST OF THE FOUR IN THIS CLASS. Every test below reads the
    # member THROUGH THE FILESYSTEM: the REACHED-BY directive is grepped out of
    # "$REPO_ROOT/$rel", and `-f` and `grep` both DEREFERENCE. But git tracks a symlink as a
    # blob containing its TARGET PATH, so for a symlink member the bytes graded are some other
    # file's. MEASURED: a tracked symlink `zz-t375-symmember/main.go -> ../ledgerguard/main.go`
    # INHERITED the real main.go's REACHED-BY row wholesale — the guard read the target's
    # directive, resolved the target's witness, found that witness names the basename `main.go`,
    # and PASSED the planted file. Whole bar exit 0, `reached-by=2`, `invoked-by-nothing=0`.
    # An unwired checker could land in this directory GREEN by being a symlink to a registered
    # one, which is the exact class T323 built this guard to make impossible.
    #
    # WHY REFUSE RATHER THAN READ THE BLOB. Reading the tracked blob instead would make the
    # guard grade the string "../ledgerguard/main.go" as if it were a checker's source, which
    # is meaningless. A symlink is not a checker. It also cannot be executed as one on a host
    # whose checkout does not materialise symlinks. The population is "tracked .sh/.py/.go
    # SOURCES under this directory"; a link is not a source, and saying so is narrower and more
    # honest than inventing a reading for it. THE REFUSAL IS DELIBERATELY NOT WAIVABLE BY A
    # REACHED-BY ROW, because the row would be read through the link too.
    member_stat=""; member_mode=""; member_blob=""
    member_stat="$( cd "$REPO_ROOT" 2>/dev/null && \
      git ls-files -s -- "$rel" 2>/dev/null )" || member_stat=""
    member_mode="${member_stat%% *}"
    member_blob="${member_stat#* }"; member_blob="${member_blob%% *}"
    if [ "$member_mode" = "120000" ]; then
      bad=1
      symlinked=$((symlinked + 1))
      warn "conformance: guard_guards_dir_registration: $rel IS A SYMLINK, and a symlink is not"
      warn "conformance: a checker. What git tracks at that path is the TARGET PATH STRING,"
      warn "conformance: while every test in this guard reads the file through the filesystem"
      warn "conformance: and therefore grades the TARGET's bytes. A tracked symlink to an"
      warn "conformance: already-registered member INHERITED that member's REACHED-BY row and"
      warn "conformance: landed GREEN [T375 pass 2, arm T375-30]. This refusal is NOT waivable"
      warn "conformance: by a REACHED-BY row, because that row would be read through the link"
      warn "conformance: too. Commit a real file, or move it out of $gdrel. REFUSED."
      continue
    fi

    # DECLARED ROWS ARE MATCHED FIRST, so that the table's own text cannot satisfy the
    # invocation test below and vouch for its own subject.
    found=""
    while IFS= read -r row; do
      [ -n "$row" ] || continue
      rowbase="${row%%|*}"
      if [ "$rowbase" = "$base" ]; then found="$row"; fi
    done <<INNER
$DECLARED
INNER

    if [ -z "$found" ]; then
      # ── DIRECTION 3: REACHED-BY, the row the MEMBER carries in its own header. [T358]
      # Read BEFORE the invocation test, for the same reason the table is: a member that
      # declares itself must be adjudicated on the declaration, not accidentally absolved by
      # its basename appearing somewhere in this file.
      #
      # THE DIRECTIVE IS MATCHED ANCHORED TO ITS OWN MARKER, not by a loose grep, and the
      # marker is long enough that no file mentions it by accident. `grep -m1` here is NOT in
      # a pipeline, and that is the same discipline the rest of this function keeps — P-57,
      # "THE MACHINERY THAT EXISTS TO CATCH A SILENT GUARD CAN INVERT ITSELF, AND IT INVERTS ON
      # EXACTLY THE INPUTS THAT MATTER" [VERIFIED: .softhouse/patterns.md:1654], whose worked
      # example is a `printf … | grep -q` that reports a MISS on a MATCH because grep exits
      # first, printf takes EPIPE and `pipefail` propagates the 141. That family already cost
      # this guard its first graded run. A miss here is a plain exit 1 that `|| self_row=""`
      # absorbs under `set -u -o pipefail`.
      self_row=""
      self_row="$(LC_ALL=C grep -m1 -E \
        'GUARDS-DIR-REGISTRATION:[[:space:]]+REACHED-BY[[:space:]]+[^[:space:]]+' \
        "$REPO_ROOT/$rel" 2>/dev/null)" || self_row=""
      if [ -n "$self_row" ]; then
        self_wit="${self_row##*REACHED-BY}"
        self_wit="${self_wit#"${self_wit%%[![:space:]]*}"}"
        self_wit="${self_wit%%[[:space:]]*}"

        # THE WITNESS PATH IS NORMALISED BEFORE IT IS COMPARED TO ANYTHING. [T375, closing
        # T364's F-T364-2, which was DRIVEN through the whole bar with a control before it
        # was reported and is driven red again here.]
        #
        # THE DEFECT: the self-certification test below used to be a RAW STRING COMPARE,
        # `[ "$self_wit" = "$rel" ]`, and it was the only step in this chain that did not
        # normalise. Every other step handed the path to git or to the filesystem, both of
        # which resolve `./p` and `a/../p` to `p`. So the sentence this guard PRINTS in its
        # own refusal — "a file may not vouch for itself" — was true of exactly ONE spelling
        # of the member's path and false of every other. T364 forged two of them (`./M` and
        # `.../x/../M`), each in ONE LINE inside the tripping task's own edit grant, and the
        # whole bar stayed GREEN while the guard printed "(verified: it names …)".
        #
        # THE FIX IS TO ASK GIT, WHICH IS ALREADY BEING ASKED. `git ls-files --error-unmatch`
        # was already run on the witness to prove it TRACKED; it was run with its output
        # discarded. Its output IS the canonical repo-relative path, so capturing it costs
        # nothing and closes the class rather than a spelling. MEASURED on this tree [T375]:
        # `M`, `./M`, `.//M`, `./././M`, `a/./M`, `a/x/../M` and the ABSOLUTE path all
        # normalise to the identical `.softhouse/guards/ledgerguard/main.go`. The absolute
        # spelling is one T364 did not test and this compare closes it too.
        #
        # WHAT DELIBERATELY DID NOT MOVE. The `-f` existence test still runs on the TYPED
        # spelling, so the two refusals T364 verified fail-closed by inspection — a witness
        # that is a DIRECTORY, and a witness carrying PATHSPEC MAGIC such as ":(glob)*" —
        # still refuse there and refuse first. Normalising before `-f` without that would
        # have let `:(glob)…` through git and then past `-f` on the resolved path, i.e. this
        # repair could have opened a hole while closing one. It does not; the magic spelling
        # is driven red as its own arm.
        #
        # A WITNESS THAT RESOLVES TO MORE THAN ONE PATH IS NOW A REFUSAL. `git ls-files` over
        # a pathspec can print many lines; "the witness" would then be whichever line came
        # first, which is not a measurement — the same reasoning `_census_one` uses for an
        # ambiguous sed match. No pipeline is used to count them (P-57 — "THE MACHINERY THAT
        # EXISTS TO CATCH A SILENT GUARD CAN INVERT ITSELF, AND IT INVERTS ON EXACTLY THE
        # INPUTS THAT MATTER" [VERIFIED: .softhouse/patterns.md:1654]); a `case` on an
        # embedded newline starts no second process at all.
        self_norm=""
        if [ -n "$self_wit" ]; then
          self_norm="$( cd "$REPO_ROOT" 2>/dev/null && \
            git ls-files --error-unmatch -- "$self_wit" 2>/dev/null )" || self_norm=""
        fi
        self_multi=0
        case "$self_norm" in
          *"$CONF_LF"*) self_multi=1 ;;
        esac

        # THE WITNESS MUST BE AN INDEPENDENT TRACKED FILE, AND `grep` MUST READ THE BYTES GIT
        # TRACKS AT THAT PATH. [T375 pass 2, closing three fail-opens of F-T364-2's OWN class
        # that pass 1's normalisation does not reach. All three were DRIVEN GREEN — i.e. the
        # whole bar exited 0 with `VERDICT: PASS` — before this block was written, and are
        # driven RED by arms T375-18..21 after it.]
        #
        # THE DEFECT. Pass 1 fixed the SPELLING of the witness path and stopped there. But
        # `self_norm` names a PATH, and a path is not a file: three different constructions let
        # the member's own bytes come back as "some other file that names me", and the guard
        # then printed `(verified: it names <base>)` while the bar stayed GREEN.
        #
        #   SYMLINK.   `git ls-files` resolves a symlink to ITS OWN PATH, never to its target,
        #              so `self_norm != rel` and the self-reference compare above is satisfied.
        #              `-f` and `grep` both DEREFERENCE. So a member `m.sh` plus a tracked
        #              symlink `w.txt -> m.sh` made `m.sh` vouch for itself. MEASURED: exit 0,
        #              probe PRESENT, `reached-by=2`.
        #   HARD LINK. `ln m.sh w.txt` — two tracked paths, ONE inode, one blob. Same result.
        #   PLAIN COPY. `cp m.sh w.txt` — two inodes, still ONE blob, because the witness holds
        #              nothing but the member's own text. "Another file names me" satisfied by
        #              my own words retyped is self-certification with an extra step.
        #
        # WHY TWO TESTS AND NOT ONE. They fail differently and neither subsumes the other:
        # a symlink's tracked blob is the TARGET PATH STRING, so it does NOT collide with the
        # member's blob and no content compare can catch it; a hard link and a copy are
        # ordinary regular files, so no mode check can catch them.
        #
        #   (1) MODE. A symlink witness is refused outright, and the reason is independent of
        #       self-reference: what git tracks at that path is the target path string, while
        #       `grep` reads the DEREFERENCED file's bytes. The bytes graded are then not the
        #       bytes committed at that path, and the target may not be in this repository at
        #       all — which is the identical objection this direction already prints for an
        #       untracked witness, "it is absent from every commit and cannot be reviewed".
        #   (2) BLOB. A witness whose tracked blob IS the member's tracked blob is the member.
        #       Comparing object ids compares what is COMMITTED, not what is on this host, so
        #       it is stable across checkouts and it catches copy and hard link with one test.
        #
        # MEASURED ON THIS TREE BEFORE THE CHANGE [T375 pass 2]: the guards directory tracks no
        # symlink and no two identical blobs, so neither test refuses anything standing today —
        # verified by `git ls-files -s .softhouse/guards`, and by arm T375-09, the legitimate
        # `./`-spelled witness, which stays ACCEPTED.
        #
        # NO PIPELINE, for the reason P-57 gives and this function keeps everywhere else
        # [VERIFIED: .softhouse/patterns.md:1654]. `git ls-files -s` prints
        # `<mode> <objectid> <stage>\t<path>`; the two fields are taken with shell parameter
        # expansion, which starts no second process and cannot EPIPE.
        # `member_blob` is ALREADY IN HAND — it was read at the top of this loop iteration, by
        # the symlink refusal above, from the same `git ls-files -s` call. It is not re-read
        # here: two reads of one quantity are two chances to disagree.
        self_stat=""; self_mode=""; self_blob=""
        if [ -n "$self_norm" ] && [ "$self_multi" -eq 0 ]; then
          self_stat="$( cd "$REPO_ROOT" 2>/dev/null && \
            git ls-files -s -- "$self_norm" 2>/dev/null )" || self_stat=""
          self_mode="${self_stat%% *}"
          self_blob="${self_stat#* }"; self_blob="${self_blob%% *}"
        fi
        if [ -z "$self_wit" ]; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel carries a REACHED-BY directive"
          warn "conformance: with NO witness path after it. An unreadable declaration is an"
          warn "conformance: ERROR, never a pass."
        elif [ "$self_multi" -ne 0 ]; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel declares REACHED-BY $self_wit,"
          warn "conformance: which resolves to MORE THAN ONE TRACKED PATH. A witness is one file"
          warn "conformance: that names this member; 'whichever path git listed first' is not a"
          warn "conformance: measurement and cannot be reviewed. Name the one file. REFUSED."
        elif [ "$self_wit" = "$rel" ] || [ "$self_norm" = "$rel" ]; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel declares REACHED-BY ITSELF. A"
          warn "conformance: file may not vouch for itself — that is self-certification, which"
          warn "conformance: is exactly the amnesty this direction was built to avoid. REFUSED."
          if [ "$self_wit" != "$rel" ]; then
            warn "conformance: (the row spells it '$self_wit', which git resolves to '$self_norm'."
            warn "conformance: The COMPARE IS ON THE RESOLVED PATH — T364's F-T364-2, closed by"
            warn "conformance: T375 — so a leading './', an interior '/../' or an absolute path"
            warn "conformance: is the same self-reference and is refused as one.)"
          fi
        elif [ ! -f "$REPO_ROOT/$self_wit" ]; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel declares REACHED-BY $self_wit,"
          warn "conformance: and THAT REACHED-BY WITNESS DOES NOT EXIST. A declaration whose"
          warn "conformance: witness is gone is an amnesty, not a record. REFUSED."
        elif [ -z "$self_norm" ]; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel declares REACHED-BY $self_wit,"
          warn "conformance: which is NOT TRACKED. An untracked witness is host state — it is"
          warn "conformance: absent from every commit and cannot be reviewed. REFUSED."
          warn "conformance: (READ THIS BEFORE CONCLUDING THE GUARD IS WRONG. The file EXISTS on"
          warn "conformance: disk — the existence test above passed — yet git will not resolve"
          warn "conformance: the spelling. The usual cause is CASE: this program's macOS hosts"
          warn "conformance: mount a case-INSENSITIVE filesystem, so '-f' accepts a wrong-case"
          warn "conformance: path that git, which indexes case-SENSITIVELY, does not. Spell the"
          warn "conformance: witness exactly as 'git ls-files' prints it. The other cause is a"
          warn "conformance: path reaching THROUGH a symlinked directory, which git never"
          warn "conformance: indexes. Either way the refusal stands: a spelling git cannot"
          warn "conformance: resolve cannot be re-verified on another checkout [T375 pass 2].)"
        elif [ "$self_mode" = "120000" ]; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel declares REACHED-BY $self_wit,"
          warn "conformance: and THAT WITNESS IS A SYMLINK. What git tracks at that path is the"
          warn "conformance: TARGET PATH STRING; the test below would follow the link and grade"
          warn "conformance: bytes that are not committed at that path — and the target may not"
          warn "conformance: be in this repository at all. A symlink to the member ITSELF made"
          warn "conformance: this file vouch for itself and the bar stayed GREEN [T375 pass 2,"
          warn "conformance: the same class as T364's F-T364-2]. Name a real tracked file."
          warn "conformance: REFUSED."
        elif [ -n "$member_blob" ] && [ "$self_blob" = "$member_blob" ]; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel declares REACHED-BY $self_wit,"
          warn "conformance: and THAT WITNESS IS BYTE-IDENTICAL TO THIS MEMBER — same git object"
          warn "conformance: $member_blob. A copy or a hard link of the member is the member: it"
          warn "conformance: names $base only because the member's own text names it. That is"
          warn "conformance: self-certification with an extra step, which is exactly the amnesty"
          warn "conformance: this direction exists to refuse [T375 pass 2]. REFUSED."
        elif ! LC_ALL=C grep -qF -- "$base" "$REPO_ROOT/$self_norm"; then
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel declares REACHED-BY $self_wit,"
          warn "conformance: and THAT REACHED-BY WITNESS DOES NOT NAME $base. The declaration is"
          warn "conformance: an unverified assertion, and this direction exists precisely so that"
          warn "conformance: it never is. REFUSED."
        else
          selfdecl=$((selfdecl + 1))
          say "conformance:     REACHED-BY $rel — declared in its own header, reached by"
          say "conformance:                $self_norm (verified: it names $base)"
        fi
        continue
      fi

      # THE INVOCATION TEST MATCHES THE MEMBER'S REPO-RELATIVE PATH, NOT ITS BARE BASENAME.
      # [T375, closing T364's F-T364-1 — which T364 DROVE with a control, and which is driven
      # red here in both directions.]
      #
      # THE DEFECT T364 FOUND, and it was a hole in the very claim T358 was commissioned to
      # repair. The test was `case "$code" in *"$base"*)`, i.e. the member's BASENAME anywhere
      # on a non-comment line. `main.go` occurs on two non-comment lines of this file — at the
      # `local ccsrc=` assignment and the `say` beneath it, where a DIFFERENT guard reads that
      # file's TEXT — so a genuinely unwired Go checker named `main.go`, in ANY subdirectory
      # under the guards directory, read INVOKED and the whole bar stayed GREEN. The same file
      # under a unique basename was correctly refused; the basename was the entire difference.
      # T358 widened the population to `.go` precisely so an unwired Go checker could not land
      # unseen, and `main.go` is the single most likely filename for the next one, in a
      # directory whose only Go checker is already called that. The population widened and the
      # predicate did not follow it.
      #
      # WHY THE PATH IS THE RIGHT PREDICATE AND NOT MERELY A TIGHTER ONE. A basename is not an
      # identifier: it is shared by every file that happens to be called that, so a mention of
      # ANOTHER file absolves this one. A repo-relative path IS an identifier — it names one
      # tracked file and no other. MEASURED on this tree before the change was made [T375], so
      # this is a calibration and not a hope: all three genuinely-invoked members are named by
      # their FULL repo-relative path on the line that runs them —
      #     .softhouse/guards/check-ledger-invariants.sh   `bash "$REPO_ROOT/…"`
      #     .softhouse/guards/check-capture-namespace.sh   `local g="$REPO_ROOT/…"`
      #     .softhouse/guards/check-dead-path-frontier.sh  `local g="$REPO_ROOT/…"`
      # — so `invoked` is unchanged at 3 and the CALIBRATION arm below is not weakened by this.
      #
      # THIS IS STILL A NAMING TEST AND STILL NOT PROOF OF EXECUTION, and T358's reason for
      # refusing to make it one is untouched: two of those three are reached through `bash "$g"`
      # after a `local g=` assignment, so an execution test needs dataflow this harness has no
      # business growing. What changed is WHICH STRING counts as naming this member. The gap
      # that remains is one order of magnitude narrower and is stated in the printed selector:
      # a non-comment line that spells THIS MEMBER'S OWN PATH while not calling it still
      # absolves it. `.softhouse/guards/ledgerguard/main.go` is such a line today, which is why
      # main.go carries a REACHED-BY row recording what actually reaches it — the row is read
      # ABOVE this test, so the truthful record wins over the convenient fiction either way.
      #
      # NO PIPELINE HERE, AND THAT IS NOT A STYLE CHOICE. `printf … | grep -q` is a member of
      # the EPIPE family P-57 names: grep -q exits on its FIRST match, printf then dies of
      # SIGPIPE, and under `set -o pipefail` — which this file sets at the top — the pipeline
      # reports 141, so A MATCH READS AS A MISS. T323 wrote it that way, and the guard's own
      # CALIBRATION arm refused the very first graded run, reporting all three genuinely
      # invoked checkers as unwired. A shell `case` starts no second process and cannot EPIPE.
      case "$code" in
      *"$rel"*)
        invoked=$((invoked + 1))
        say "conformance:     INVOKED    $rel"
        ;;
      *)
        unwired=$((unwired + 1))
        bad=1
        warn "conformance: guard_guards_dir_registration: $rel IS INVOKED BY NOTHING."
        warn "conformance: It sits in the canonical guards directory and no non-comment line of"
        warn "conformance: this file names it, so it enforces nothing — P-45, 'A test-only guard"
        warn "conformance: is not a guard … verify the path that actually executes in"
        warn "conformance: CI/conformance calls it, not merely that a test does.'"
        warn "conformance:"
        # THE DIAGNOSTIC THAT NAMES T364's F-T364-1 OUT LOUD, because the reader who trips this
        # arm on a file called `main.go` will otherwise search this harness, find its basename,
        # and conclude the guard is broken. It is not: the occurrence names a DIFFERENT file.
        case "$code" in
        *"$base"*)
          warn "conformance: NOTE — the BASENAME '$base' DOES occur on a non-comment line of this"
          warn "conformance: harness, and that is NOT a registration. The occurrence names some"
          warn "conformance: OTHER file with the same basename; this member's own path,"
          warn "conformance: $rel, does not occur. Until T375 the bare"
          warn "conformance: basename absolved, so an unwired checker named 'main.go' was"
          warn "conformance: reported INVOKED and the bar stayed GREEN [T364 F-T364-1]. Use the"
          warn "conformance: REACHED-BY row below to record what actually reaches this file."
          warn "conformance:"
          ;;
        esac
        warn "conformance: THE FIX YOU CAN ALMOST CERTAINLY MAKE YOURSELF, without holding"
        warn "conformance: this file: if $base is reached by something OTHER than this harness"
        warn "conformance: — a test, a build script, the fire driver, a Go module's own runner"
        warn "conformance: — put ONE LINE in $rel's own header:"
        warn "conformance:"
        warn "conformance:     GUARDS-DIR-REGISTRATION: REACHED-BY <witness path, repo-relative>"
        warn "conformance:"
        warn "conformance: The witness must be TRACKED; must be a REGULAR FILE, never a symlink;"
        warn "conformance: must not be $rel in ANY"
        warn "conformance: spelling — a leading './', an interior '/../' and an absolute path all"
        warn "conformance: resolve to the same file and are refused as the same self-reference;"
        warn "conformance: must not be a COPY or a HARD LINK of it, which git shows as the same"
        warn "conformance: object id; and must NAME $base. This guard re-verifies EVERY ONE of"
        warn "conformance: those every run, so it is a record and not an amnesty — each was a"
        warn "conformance: way to forge this row and each is now driven RED by its own arm"
        warn "conformance: [T364 F-T364-2; T375 passes 1 and 2]."
        warn "conformance: Both files are yours; no edit to this harness is"
        warn "conformance: needed, which is the point: the two older remedies below both require"
        warn "conformance: editing a file this program serialises to one holder per batch."
        warn "conformance:"
        warn "conformance: THE OTHER TWO FIXES, which need whoever holds this harness: call it"
        warn "conformance: from run_guards, or add its row to the DECLARATION TABLE in this"
        warn "conformance: function, naming the witness that runs it. A comment saying it is"
        warn "conformance: run is not a row."
        ;;
      esac
      continue
    fi

    dir="${found#*|}"; dir="${dir%%|*}"
    witness="${found#*|*|}"; witness="${witness%%|*}"
    token="${found##*|}"
    if [ ! -f "$REPO_ROOT/$witness" ]; then
      bad=1
      warn "conformance: guard_guards_dir_registration: $rel is DECLARED against the witness"
      warn "conformance: $witness, and that file DOES NOT EXIST. A declaration whose witness is"
      warn "conformance: gone is an amnesty, not a record. REFUSED."
      continue
    fi
    case "$dir" in
      CALLER)
        if LC_ALL=C grep -qF -- "$token" "$REPO_ROOT/$witness"; then
          decl_ok=$((decl_ok + 1))
          say "conformance:     DECLARED   $rel — run by $witness (verified: it names $token)"
        else
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel is DECLARED as being run by"
          warn "conformance: $witness, and that file NO LONGER NAMES $token. The declaration is"
          warn "conformance: FALSE and the checker is unwired again. REFUSED."
        fi
        ;;
      SUBJECT)
        if LC_ALL=C grep -qF -- "$token" "$REPO_ROOT/$rel"; then
          decl_ok=$((decl_ok + 1))
          say "conformance:     DECLARED   $rel — not a guard: the red drive for $token (verified)"
        else
          bad=1
          warn "conformance: guard_guards_dir_registration: $rel is DECLARED as the red drive for"
          warn "conformance: $token and NO LONGER NAMES IT. Either it stopped being that, or the"
          warn "conformance: declaration was wrong. Both are refusals, never a pass."
        fi
        ;;
      *)
        bad=1
        warn "conformance: guard_guards_dir_registration: $rel carries an unreadable declaration"
        warn "conformance: direction '$dir'. An unreadable table row is an ERROR, never a pass."
        ;;
    esac
  done <<POPULATION
$pop
POPULATION

  # A DECLARED ROW WHOSE SUBJECT HAS LEFT THE POPULATION is a stale amnesty. Checked here rather
  # than in the loop above, which only ever sees members that still exist.
  # Same P-57 discipline as above: no pipeline, so no `grep -q` EPIPE under `pipefail`. The
  # membership test is EXACT BASENAME EQUALITY rather than a suffix match, so a declaration for
  # `x.sh` is not satisfied by a `zzx.sh` that happens to be in the directory.
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    rowbase="${row%%|*}"
    found=""
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      if [ "${rel##*/}" = "$rowbase" ]; then found=1; fi
    done <<POPCHECK
$pop
POPCHECK
    if [ -z "$found" ]; then
      bad=1
      warn "conformance: guard_guards_dir_registration: the DECLARATION TABLE still carries"
      warn "conformance: $rowbase, which is NO LONGER IN THE POPULATION. A row that excuses a"
      warn "conformance: file that is gone starts excusing the next file to take that name. Drop"
      warn "conformance: it in the same commit that removed the file."
    fi
  done <<STALE
$DECLARED
STALE

  if [ "$invoked" -eq 0 ]; then
    warn "conformance: guard_guards_dir_registration: CALIBRATION FAILED — NOT ONE member of the"
    warn "conformance: population was found on a non-comment line of this file, yet three of them"
    warn "conformance: are invoked verbatim a few hundred lines above. The reading mechanism is"
    warn "conformance: broken, not the tree. A guard that cannot re-find what it knows is there"
    warn "conformance: is not measuring anything. REFUSED."
    return 1
  fi

  say "conformance:   GUARDS-DIR-REGISTRATION: population=$total invoked=$invoked declared=$decl_ok reached-by=$selfdecl invoked-by-nothing=$unwired symlink-members=$symlinked"
  say "conformance:   (selector: git ls-files with ':(glob)' magic over the TRACKED '*.sh', '*.py'"
  say "conformance:   and '*.go' files at ANY DEPTH under $gdrel, from \$REPO_ROOT. NOT closed over"
  say "conformance:   other languages or committed binaries — this is a count over that search.)"
  say "conformance:   (INVOKED means the member's REPO-RELATIVE PATH appears on a NON-COMMENT line"
  say "conformance:   of this file — NOT its bare basename. [T375, closing T364 F-T364-1: a"
  say "conformance:   basename is shared, so a mention of ANOTHER file absolved this one, and an"
  say "conformance:   unwired checker named 'main.go' read INVOKED with the bar GREEN.] It is"
  say "conformance:   still a NAMING test and still NOT proof of execution: two of the three"
  say "conformance:   members that read INVOKED today are named on a 'local g=' assignment and the"
  say "conformance:   call is a variable expansion this test cannot see. [T337 F-T337-4, corrected"
  say "conformance:   by T358 — the old wording said 'never a mention', which overstated it.] What"
  say "conformance:   remains open, stated so nobody concludes more than was closed: a non-comment"
  say "conformance:   line spelling THIS member's own path without calling it still absolves it.)"
  if [ "$bad" -ne 0 ]; then
    warn "conformance: guard_guards_dir_registration FAILED. A checker in the canonical guards"
    warn "conformance: directory is unreached, or a declaration about one is no longer true."
    return 1
  fi
  say "conformance:   guards-dir registration: PASS — every member of $gdrel is invoked by this"
  say "conformance:   file, DECLARED against a verified witness, or carries a verified REACHED-BY."
  return 0
}

# ===========================================================================================
# THE BAR MEASURES ITS OWN WALL-CLOCK COST, PER GUARD, AND REFUSES ON A CEILING.
#   [T375, closing FU-T358-1 / C-T364-4.]
# ===========================================================================================
# WHY THIS EXISTS, and it is not a performance feature. T358 wrote four lines of this function
# as bash parameter substitution over a ~94 KB string. That substitution is quadratic; the
# guard — ADVERTISED IN THIS FUNCTION'S OWN COMMENT AT 0.23 s — spun at 99.7% CPU for 9m43s and
# had to be killed. T364 reproduced the idiom gap independently and off the bar: the delivered
# `grep -vF` here-string form did the identical job in 0.144 s while the rejected form was still
# running after 40 s and was killed.
#
# THE FINDING IS NOT THE BUG. The bug was fixed in one line. The finding is that NOTHING IN THIS
# HARNESS MEASURED IT. Four hand-written cost comments sat in this function — 0.23 s, 0.4 s,
# 1.3 s, 30.3 s — and not one of them was checked by anything, so a guard whose comment said
# 0.23 s and whose real cost was unbounded was caught by A HUMAN NOTICING that a 75-second run
# had not returned in ten minutes. That is P-45 in its purest form: "A test-only guard is not a
# guard. … when hardening a check, verify the path that actually executes in CI/conformance
# calls it, not merely that a test does." [VERIFIED: .softhouse/patterns.md:1503]. A comment is
# not even a test-only guard; it is a claim with no arm at all. And the consequence is the one
# this file already argues about severity, one level down: A GRADING INSTRUMENT NOBODY WILL WAIT
# FOR GETS BYPASSED, which is indistinguishable from switching it off.
#
# WHAT IS MEASURED AND WHAT IS PINNED — read this before "fixing" a breach by raising a number.
# The ELAPSED SECONDS ARE NOT PINNED and must never be: a wall-clock figure is a statement about
# the host as much as the tree, and a bar that goes red because somebody else's build was
# running is a bar that gets bypassed — which is the same failure the ceiling exists to prevent.
# T358 raised exactly that objection against building a timing gate at all and it is correct, so
# it is this instrument's FIRST DESIGN CONSTRAINT rather than an afterthought. What IS pinned,
# in the way every other frontier in this file is pinned — BY NAME, never by magnitude — is:
#   * every guard run through this function HAS A BUDGET ROW (an unbudgeted guard REFUSES), and
#   * every budget row WAS ACTUALLY TIMED (a row for a guard that no longer runs REFUSES, the
#     same stale-amnesty shape the DECLARATION TABLE above refuses), and
#   * AT LEAST ONE guard was timed (an empty census passes everything — the vacuity arm this
#     file already applies to the guards-directory population, to T362's corpus guard and to
#     the pre-fire lock control, all three of which reported a population of ZERO and PASSED).
#
# HOW THE BUDGETS WERE SET, so the next author can re-derive them instead of guessing:
#   budget = max(60, 10 x the elapsed seconds MEASURED by this instrument on an idle host),
# rounded up to a round number. Ten times, because the defect class is an UNBOUNDED SPIN — 583 s
# against an advertised 0.23 s, a factor of ~2500 — and not a 30% regression; a ceiling that
# fires on a factor of two would fire on a loaded host and teach the next reader to ignore it.
# A floor of 60 s, because every sub-second guard would otherwise have a budget inside the
# resolution of the clock. The 9m43s spin breaches the smallest of these budgets nine times over.
# `guard_ledger_invariants` is the one exception to the arithmetic and it is deliberate: it
# measures 2 s here on a WARM Go build cache and a cold one is a different order of magnitude, so
# its ceiling is set for the cold case rather than for the measurement.
#
# THE FIRST RUN OF THIS INSTRUMENT ALREADY FOUND TWO WRONG COST CLAIMS, which is the whole
# argument for it and is recorded rather than tidied away. (1) `guard_reconciler_ownership`
# measured **41 s** against the 30.3 s its hand-written comment had claimed since T323 — a third
# high, never noticed, because nothing read it. (2) `guard_pnumber_citations` measured **21 s**
# and HAD NO COST CLAIM AT ALL: it is the second most expensive guard in this function and no
# reader of this file could have known that. Both figures are now printed by the census on every
# run and neither is retyped here as a cardinal to maintain.
#
# WHAT THIS DOES NOT DO, STATED PLAINLY BECAUSE THE HONEST LIMIT IS SMALLER THAN THE FEATURE
# SOUNDS. It does NOT interrupt a running guard. A guard is a shell function that must be called
# in THIS shell — running it under `timeout` or in a background subshell would break the `exit`
# that `guard_graded_root_is_this_tree` takes and would discard every `failed=1` the others set
# — so the elapsed time is read AFTER the guard returns. A guard that never returns still hangs
# the bar forever. WHAT CHANGES IS THAT A SPIN THAT DOES RETURN IS NOW A REFUSAL WITH A NAMED
# GUARD AND A MEASURED COST, instead of a silent PASS that only a watching human ever caught.
# Bounding a non-returning guard needs a subprocess architecture this function does not have and
# is recorded as a follow-up, not smuggled in here.
#
# RESOLUTION IS ONE SECOND, from bash's `SECONDS`. Deliberate: `EPOCHREALTIME` is bash 5 only
# (this host's /bin/bash is 3.2) and its value carries a decimal point that would have to be
# taken apart in a file whose no-float guards read every line here. Integer seconds cannot
# express 0.23 s and this instrument does not pretend to — it prints `0` and means "under one
# second". The defect class it exists for is three orders of magnitude away from that.
#
# P-84 IS UNAFFECTED AND WAS RE-DERIVED AFTER THIS BLOCK WAS INSERTED, not before. Every line
# added here executes INSIDE run_guards, which is called at exactly one site as a bare command,
# strictly upstream of the single site that prints the oracle probe line. A cost refusal is
# therefore exit 2 with NO probe line — "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ
# THE ABSENCE, NOT THE VALUE." [VERIFIED: .softhouse/patterns.md:2813]. The two call sites are
# re-cited by line at the foot of guard_cost_census, AFTER these lines shifted them.
GUARD_COST_BUDGETS="guard_graded_root_is_this_tree|60
guard_no_float_in_vectors|60
guard_no_float_in_harness|60
guard_gofmt|60
guard_no_float_in_capture_requests|60
guard_no_narrow_catch_in_capture_rigs|60
guard_ledger_invariants|300
guard_no_fail_open_instruments|60
guard_no_host_state_in_lint_corpus|60
guard_pnumber_citations|300
guard_accepting_side_gap_declared|60
guard_guards_dir_registration|60
guard_capture_namespace|60
guard_dead_path_frontier|60
guard_reconciler_ownership|500"

GUARD_COST_ROWS=""
GUARD_COST_TIMED=0
GUARD_COST_TOTAL=0
GUARD_COST_BREACH=0
GUARD_COST_UNBUDGETED=0

# timed_guard <guard-function-name>
# Calls the guard AS A BARE COMMAND IN THIS SHELL — no subshell, no command substitution, no
# `timeout` — so an `exit` inside a guard still terminates the run and every global a guard sets
# still lands. Returns the guard's own status unchanged; a budget breach is recorded here and
# ADJUDICATED in guard_cost_census, so that a slow guard and a failing guard stay two separate
# findings and neither can mask the other.
timed_guard() {
  local gname="$1" budget="" row t0 elapsed rc=0
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    if [ "${row%%|*}" = "$gname" ]; then budget="${row##*|}"; fi
  done <<COSTBUDGETS
$GUARD_COST_BUDGETS
COSTBUDGETS
  t0=$SECONDS
  "$gname" || rc=1
  elapsed=$((SECONDS - t0))
  GUARD_COST_TIMED=$((GUARD_COST_TIMED + 1))
  GUARD_COST_TOTAL=$((GUARD_COST_TOTAL + elapsed))
  if [ -z "$budget" ]; then
    GUARD_COST_UNBUDGETED=$((GUARD_COST_UNBUDGETED + 1))
    GUARD_COST_ROWS="$GUARD_COST_ROWS$gname|$elapsed|NO-BUDGET-ROW
"
    warn "conformance: guard-cost: $gname ran with NO BUDGET ROW in GUARD_COST_BUDGETS. An"
    warn "conformance: unbudgeted guard is an unmeasured one, and this instrument exists because"
    warn "conformance: an unmeasured guard spun the whole bar for 9m43s. Add its row."
  else
    GUARD_COST_ROWS="$GUARD_COST_ROWS$gname|$elapsed|$budget
"
    if [ "$elapsed" -gt "$budget" ]; then
      GUARD_COST_BREACH=$((GUARD_COST_BREACH + 1))
      warn "conformance: guard-cost: $gname took ${elapsed}s, over its ${budget}s CEILING."
      warn "conformance: This is not a performance complaint. A guard nobody will wait for is a"
      warn "conformance: guard that gets bypassed, and the last time one ran away it spun at"
      warn "conformance: 99.7% CPU for 9m43s while its own comment advertised 0.23 s. REFUSED."
    fi
  fi
  return "$rc"
}

# The census. Prints EVERY row on EVERY run, pass or fail — a guard that speaks only when it
# fires cannot be told apart from one that never ran (P-22 — "A guard, a canary, or a control
# that cannot fail is worse than none — because it is believed"
# [VERIFIED: .softhouse/patterns.md:473]).
guard_cost_census() {
  local row name elapsed budget bad=0 stale=0 rows=0 seen
  if [ "$GUARD_COST_TIMED" -eq 0 ]; then
    warn "conformance: guard-cost: NOT ONE guard was timed. That is a SELECTOR failure, not a"
    warn "conformance: cheap run — this function calls fifteen guards. An empty census passes"
    warn "conformance: everything. REFUSED."
    return 1
  fi
  say "conformance:   GUARD-COST CENSUS: $GUARD_COST_TIMED guards timed, ${GUARD_COST_TOTAL}s total wall,"
  say "conformance:   ceiling breaches $GUARD_COST_BREACH, unbudgeted guards $GUARD_COST_UNBUDGETED."
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    rows=$((rows + 1))
    name="${row%%|*}"
    budget="${row##*|}"
    elapsed="${row#*|}"; elapsed="${elapsed%%|*}"
    say "conformance:     COST ${elapsed}s / ceiling ${budget}s   $name"
  done <<COSTROWS
$GUARD_COST_ROWS
COSTROWS
  # A BUDGET ROW THAT WAS NEVER TIMED is a row for a guard this function no longer runs. Same
  # refusal, and the same reason, as a DECLARATION TABLE row whose subject has left the
  # population: a stale row starts excusing the next guard to take that name.
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    name="${row%%|*}"
    seen=""
    while IFS= read -r elapsed; do
      [ -n "$elapsed" ] || continue
      if [ "${elapsed%%|*}" = "$name" ]; then seen=1; fi
    done <<COSTSEEN
$GUARD_COST_ROWS
COSTSEEN
    if [ -z "$seen" ]; then
      stale=$((stale + 1))
      bad=1
      warn "conformance: guard-cost: GUARD_COST_BUDGETS carries a row for $name, which this run"
      warn "conformance: NEVER TIMED. A budget for a guard that no longer runs is a row that will"
      warn "conformance: start excusing the next guard to take that name. Drop it in the same"
      warn "conformance: commit that removed the guard."
    fi
  done <<COSTSTALE
$GUARD_COST_BUDGETS
COSTSTALE
  say "conformance:   (RESOLUTION 1 s, from bash SECONDS; a 0 means UNDER ONE SECOND. The elapsed"
  say "conformance:   figures are RECORDED and NOT PINNED — wall clock is a fact about the host as"
  say "conformance:   well as the tree. What is pinned, by NAME: every guard has a ceiling row,"
  say "conformance:   every ceiling row was timed, and at least one guard was timed. The ceiling is"
  say "conformance:   read AFTER the guard returns, so it turns a spin that RETURNS into a named"
  say "conformance:   refusal; it does not interrupt one that never does. [T375, FU-T358-1.])"
  if [ "$GUARD_COST_BREACH" -ne 0 ] || [ "$GUARD_COST_UNBUDGETED" -ne 0 ] || [ "$bad" -ne 0 ]; then
    warn "conformance: guard_cost_census FAILED: $GUARD_COST_BREACH ceiling breach(es),"
    warn "conformance: $GUARD_COST_UNBUDGETED unbudgeted guard(s), $stale stale budget row(s)."
    return 1
  fi
  say "conformance:   guard-cost: PASS — every guard timed, every ceiling row used, none breached."
  return 0
}

run_guards() {
  local failed=0
  # EVERY GUARD BELOW IS CALLED THROUGH `timed_guard`, which wraps it WITHOUT a subshell so the
  # short-circuit `exit` immediately below still terminates the run. The cost census is folded
  # into the same `failed` tally as the guards themselves, at the end, so that a ceiling breach
  # and a guard verdict are two separate findings in the transcript and one cannot hide the
  # other. [T375, FU-T358-1 / C-T364-4.]
  #
  # FIRST, and it SHORT-CIRCUITS rather than joining the `failed=1` tally the others use.
  # Two reasons, both learned the expensive way. (1) Every guard below answers a question
  # about $REPO_ROOT; until it is settled that $REPO_ROOT is the tree being GRADED, none of
  # their answers is about the run in progress, and a dozen green census lines printed under
  # a refusal read as "mostly fine". That is the T165 failure mode exactly — the true
  # statement was in the output and the reader took the summary instead. (2) The tally style
  # exists so that one bad guard does not hide another; here there is nothing to hide, the
  # divergence subsumes every downstream result.
  timed_guard guard_graded_root_is_this_tree || {
    warn "conformance: EXIT 2 — no verdict is available, and NO other guard was run: their"
    warn "conformance: results would describe a tree this run was not going to grade."
    exit "$EXIT_UNUSABLE"
  }
  timed_guard guard_no_float_in_vectors           || failed=1
  timed_guard guard_no_float_in_harness           || failed=1
  timed_guard guard_gofmt                         || failed=1
  timed_guard guard_no_float_in_capture_requests  || failed=1
  timed_guard guard_no_narrow_catch_in_capture_rigs || failed=1
  timed_guard guard_ledger_invariants             || failed=1
  timed_guard guard_no_fail_open_instruments      || failed=1
  timed_guard guard_no_host_state_in_lint_corpus  || failed=1
  timed_guard guard_pnumber_citations             || failed=1   # T282, wired HARD by T331
  timed_guard guard_accepting_side_gap_declared   || failed=1
  # T323 — the three guards T299, T316 and T319 each built, drove red AND green, and could not
  # wire because this file was assigned to somebody else. Each joins the `failed=1` tally rather
  # than short-circuiting: unlike guard_graded_root_is_this_tree none of them invalidates the
  # other guards' answers, and one bad guard must not hide another. Registered CHEAPEST FIRST so
  # a fast refusal prints before the 30-second one is paid for.
  #
  # THE PER-GUARD COST FIGURES THAT USED TO SIT IN THIS COLUMN AS COMMENTS ARE GONE, AND THAT IS
  # THE POINT OF T375, NOT AN OMISSION. They read 0.23 s / 0.4 s / 1.3 s / 30.3 s; not one of
  # them was checked by anything; and one of the four was wrong by a factor of ~2500 for nine
  # minutes and forty-three seconds while still reading 0.23 s. A cardinal maintained by hand
  # beside an instrument that MEASURES IT LIVE is a second source of truth with no owner — the
  # identical defect T358 removed from guard_capture_namespace one iteration earlier, and P-80's
  # own prescription: "A CORRECTED CARDINAL ROTS IN EVERY PLACE IT WAS RESTATED. The count is the
  # same defect as the line number." [VERIFIED: .softhouse/patterns.md:2775]. The costs are now
  # PRINTED, EVERY RUN, by guard_cost_census below. READ THAT.
  timed_guard guard_guards_dir_registration       || failed=1   # T323 iter 2, T358, T375
  timed_guard guard_capture_namespace             || failed=1   # T299, wired by T323
  timed_guard guard_dead_path_frontier            || failed=1   # T316, wired by T323
  timed_guard guard_reconciler_ownership          || failed=1   # T319, wired by T323
  guard_cost_census                               || failed=1   # T375, FU-T358-1 / C-T364-4
  if [ "$failed" -ne 0 ]; then
    warn "conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

# ---------------------------------------------------------------------------
# gate_exemption_census: the exemption figures the report prints are COMPARED,
# not merely printed.  [T233 — T222 F-1, T230 F-1]
# ---------------------------------------------------------------------------
# Argument: a file holding the graded run's whole output. A FILE and not a pipe,
# deliberately — every read below is a `sed`/`grep` over that file, so there is no
# early-exiting consumer for `set -o pipefail` to invert (P-57, which cost this
# harness a guard that reported "NO CENSUS LINE" about line 1).
#
# FAIL-CLOSED, in the three ways this program has learned to demand:
#   * a figure that is ABSENT is an ERROR, never a 0 and never a skip. A missing
#     line means the report changed shape and this gate is no longer reading what it
#     thinks it is reading;
#   * a figure that matches MORE THAN ONE line is an ERROR, because "the value" of
#     an ambiguous match is whichever line sed reached last, and that is not a
#     measurement (T201/T197-F-1, the same defect one census over);
#   * the gate PRINTS WHAT IT COMPARED on the way past, every run, pass or fail. A
#     guard that speaks only when it fires cannot be told apart from one that never
#     ran (P-22, P-35).
#
# It returns 0 on agreement and 1 on any disagreement; main_grade turns that into
# EXIT_UNUSABLE, because a run whose corpus is not the pinned corpus has not graded
# the thing the pin describes and its PASS is not about that corpus.
_census_field() {
  # $1 = report file, $2 = sed expression yielding one figure per matching line.
  # Prints every match, one per line. Reads a FILE; no pipeline.
  LC_ALL=C sed -n "$2" "$1"
}

_census_one() {
  # $1 = report file, $2 = sed expr, $3 = human name of the figure.
  # Prints the figure on stdout and returns 0 only when EXACTLY ONE line matched.
  local hits n
  hits="$(_census_field "$1" "$2")"
  if [ -z "$hits" ]; then
    warn "conformance: the exemption census gate could not find the $3 figure in the run's report."
    warn "conformance: an absent figure is an ERROR, not a zero: the report has changed shape and this"
    warn "conformance: gate is no longer reading the number it names."
    return 1
  fi
  n="$(printf '%s\n' "$hits" | LC_ALL=C grep -ac .)"
  if [ "$n" -ne 1 ]; then
    warn "conformance: the exemption census gate matched $n lines for the $3 figure; it requires exactly 1."
    warn "conformance: an ambiguous match has no value — whichever line came last is not a measurement."
    warn "$hits"
    return 1
  fi
  printf '%s' "$hits"
  return 0
}

gate_exemption_census() {
  local report="$1"
  local exempted declared grounded ungrounded undetermined nil_cov rc=0

  # THE NIL-COVERAGE ARM IS A REAL CORPUS STATE, NOT AN ABSENT LINE. When the store
  # declares no exemption at all the report prints the NIL-COVERAGE notice and no
  # INSPECTED line, so the four grounding figures are legitimately 0 — and the gate
  # must still COMPARE them, because a pin of 4 over a corpus that lost every
  # exemption is exactly the deflation this gate exists to catch.
  nil_cov="$(LC_ALL=C grep -ac '^    NIL-COVERAGE — no vector in this store exempts any invariant' "$report" || true)"
  [ -n "$nil_cov" ] || nil_cov=0

  if [ "$nil_cov" -gt 0 ]; then
    declared=0; grounded=0; ungrounded=0; undetermined=0
    say "conformance:   exemption census: the report declares NIL-COVERAGE — this store exempts nothing."
  else
    declared="$(_census_one "$report" \
      's/^ *INSPECTED [0-9][0-9]* loaded vector(s); [0-9][0-9]* of them exempt at least one invariant; \([0-9][0-9]*\) exemption declaration(s) examined\.$/\1/p' \
      'declared-exemptions')" || rc=1
    grounded="$(_census_one "$report" \
      's/^ *\([0-9][0-9]*\) GROUNDED (the recorded schedule VIOLATES the exempted invariant), [0-9][0-9]* UNGROUNDED\.$/\1/p' \
      'GROUNDED')" || rc=1
    ungrounded="$(_census_one "$report" \
      's/^ *[0-9][0-9]* GROUNDED (the recorded schedule VIOLATES the exempted invariant), \([0-9][0-9]*\) UNGROUNDED\.$/\1/p' \
      'UNGROUNDED')" || rc=1
    undetermined="$(_census_one "$report" \
      's/^ *\([0-9][0-9]*\) UNDETERMINED-ON-THE-RECORD (a cell the invariant reads was never recorded.*$/\1/p' \
      'UNDETERMINED-ON-THE-RECORD')" || rc=1
  fi

  exempted="$(_census_one "$report" \
    's/^ *invariant assertions  *\([0-9][0-9]*\) EXEMPTED BY A VECTOR.*$/\1/p' \
    'EXEMPTED-BY-A-VECTOR')" || rc=1

  if [ "$rc" -ne 0 ]; then
    warn "conformance: the exemption census gate could not READ the corpus it is meant to compare."
    warn "conformance: EXIT 2. A figure this gate cannot read is not a figure it may pass."
    return 1
  fi

  # THE COMPARISON. Equality on every figure, both directions, each stated.
  local ok=1
  _cmp() { # $1 name, $2 observed, $3 pinned
    if [ "$2" -eq "$3" ]; then
      say "conformance:   exemption census READ: $1 = $2 == pinned $3"
    else
      ok=0
      warn "conformance:   exemption census MISMATCH: $1 = $2, but this file pins $3."
    fi
  }
  # THE LEDGER FIGURES. Read with the same fail-closed `_census_one` -- an ABSENT
  # figure is an ERROR and never a 0, and a figure matching more than one line is
  # an ERROR because "the value" of an ambiguous match is whichever line sed
  # reached last. A store that LOST every ledger vector prints the empty-store
  # banner and NONE of these four lines, so all four reads fail and the run is
  # exit 2 -- which is the deflation arm, working.
  #
  # THE ONE STATE THAT IS SKIPPED, AND WHY IT IS SAFE TO SKIP IT. `--self-test`
  # grades the HARNESS by replaying the loanschedule store; the ledger half does
  # not run at all, so there is no ledger figure to compare and demanding one
  # would refuse every self-test run. The report announces that state on its own
  # dedicated line -- deliberately NOT the empty-store banner, because if the two
  # were indistinguishable here the deflation arm above would be dead. The skip is
  # PRINTED, so a run that skipped and a run that compared cannot be confused
  # (P-35), and this arm was found by `--prove` case 21's GREEN control refusing
  # after the ledger pins were added, which is that control doing its job.
  # TWO states skip, and each announces itself on its OWN line so that neither can
  # be confused with the third -- an empty ledger corpus -- which must still refuse.
  local selftest_ledger filtered_ledger ledger_cmp=1
  selftest_ledger="$(LC_ALL=C grep -ac '^    LEDGER NOT RUN IN SELF-TEST MODE' "$report" || true)"
  [ -n "$selftest_ledger" ] || selftest_ledger=0
  filtered_ledger="$(LC_ALL=C grep -ac '^    LEDGER NOT SELECTED' "$report" || true)"
  [ -n "$filtered_ledger" ] || filtered_ledger=0
  if [ "$filtered_ledger" -gt 0 ]; then selftest_ledger=1; fi

  local l_declared="" l_parity="" l_refusal="" l_money=""
  if [ "$selftest_ledger" -gt 0 ]; then
    say "conformance:   exemption census: the report declares the ledger half NOT RUN (self-test mode) or"
    say "conformance:     NOT SELECTED (a context filter naming another context), so the four LEDGER"
    say "conformance:     figures are NOT COMPARED on this run. They ARE compared on every unfiltered"
    say "conformance:     graded run, which is the run a verdict is quoted from. An EMPTY ledger corpus is"
    say "conformance:     a THIRD state and is NOT skipped: it refuses."
    # NO FIGURE IS ASSIGNED HERE, and the four _cmp lines below are SKIPPED rather
    # than fed the pin's own values. Seeding them from the pin would print
    # "LEDGER parity vectors = 4 == pinned 4" on a run that measured nothing --
    # a comparison of a constant with itself, printed in the same words as a real
    # measurement. That is the self-certifying shape P-22 and P-35 are about, and
    # it is worse here than silence because it reads as evidence.
    ledger_cmp=0
  else
    ledger_cmp=1
    l_declared="$(_census_one "$report" \
      's/^ *ledger exemptions  *\([0-9][0-9]*\) DECLARED.*$/\1/p' \
      'LEDGER-declared-exemptions')" || rc=1
    l_parity="$(_census_one "$report" \
      's/^ *ledger parity  *PASS \([0-9][0-9]*\)  *FAIL [0-9][0-9]*$/\1/p' \
      'LEDGER-parity-PASS')" || rc=1
    l_refusal="$(_census_one "$report" \
      's/^ *ledger oracle-refusal  *PASS \([0-9][0-9]*\)  *FAIL [0-9][0-9]*.*$/\1/p' \
      'LEDGER-oracle-refusal-PASS')" || rc=1
    l_money="$(_census_one "$report" \
      's/^ *ledger cells compared  *[0-9][0-9]* graded, of which \([0-9][0-9]*\) are MONEY cells.*$/\1/p' \
      'LEDGER-money-cells')" || rc=1
  fi

  _cmp "exempted assertions (graded)" "$exempted"     "$EXEMPTION_PIN_EXEMPTED"
  _cmp "declared exemptions (loaded)" "$declared"     "$EXEMPTION_PIN_DECLARED"
  _cmp "GROUNDED                    " "$grounded"     "$EXEMPTION_PIN_GROUNDED"
  _cmp "UNDETERMINED-ON-THE-RECORD  " "$undetermined" "$EXEMPTION_PIN_UNDETERMINED"
  _cmp "UNGROUNDED                  " "$ungrounded"   "$EXEMPTION_PIN_UNGROUNDED"
  if [ "$ledger_cmp" -eq 1 ]; then
    _cmp "LEDGER declared exemptions  " "$l_declared"   "$EXEMPTION_PIN_LEDGER_DECLARED"
    _cmp "LEDGER parity vectors       " "$l_parity"     "$EXEMPTION_PIN_LEDGER_PARITY"
    _cmp "LEDGER oracle-refusal vector" "$l_refusal"    "$EXEMPTION_PIN_LEDGER_REFUSAL"
    _cmp "LEDGER money cells compared " "$l_money"      "$EXEMPTION_PIN_LEDGER_MONEYCELLS"
  else
    say "conformance:   exemption census: LEDGER figures NOT COMPARED on this run (see above). Nothing"
    say "conformance:     is printed as a match, because a constant compared with itself is not one."
  fi

  if [ "$ok" -ne 1 ]; then
    warn "conformance:"
    warn "conformance: THE EXEMPTION CORPUS IS NOT THE PINNED CORPUS. Every figure above is an EQUALITY"
    warn "conformance: because the corpus can drift in BOTH directions and neither direction moved a"
    warn "conformance: number that decided a verdict before this gate existed: an added exemption"
    warn "conformance: inflates the count this program quotes as evidence of how much is CHECKED"
    warn "conformance: (finding T220-N1), and a deleted one deflates it with nothing to notice, because"
    warn "conformance: both of the harness's enumerators walk what is THERE and so agree about what is"
    warn "conformance: not (the T160 shape)."
    warn "conformance:"
    warn "conformance: If the change is DELIBERATE, edit EXEMPTION_PIN_* at the top of this file IN THE"
    warn "conformance: SAME COMMIT as the vector that moved it, so a reviewer sees both. Do not"
    warn "conformance: regenerate the pin from the store: a pin derived from the thing it describes is a"
    warn "conformance: tautology that passes by construction."
    warn "conformance: EXIT 2 — no verdict is available. This is NOT a pass."
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# gate_wrong_ledger_impls_die: THE SIX WRONG LEDGER IMPLEMENTATIONS, WIRED.
#   [T243, closing A2-34's F-7 — the FOURTH instance of P-45 in this program]
# ---------------------------------------------------------------------------
# A2-15 registered six DELIBERATELY WRONG ledger implementations so that a
# `graded_against` row would be EXECUTABLE rather than a sentence (DEC-2 §5.2
# requirement 7, precondition P-10). A2-34 confirmed all six die — and then
# found that they die only when the Go binary is driven BY HAND:
#
#   $ bash .softhouse/conformance.sh --ledger-impl ledger-wrong-truncating
#   conformance: unknown option --ledger-impl
#
# `-ledger-impl` is a flag on the BINARY, this script never passed it, and this
# script never runs `go test` either — so `TestEveryWrongImplementationIsKilled`
# was equally unreachable from here. A GREEN RUN OF THIS HARNESS EXECUTED NONE
# OF THE SIX. P-45: a guard that only fails when invoked by hand enforces
# nothing. This gate is that route, and it has been driven red through itself
# (.softhouse/capture/t243-wiring/transcripts/10-wrongimpl-red-drive.txt).
#
# WHAT IT ASSERTS, AND WHY EACH PART IS THERE
#   * THE POPULATION IS DISCOVERED, NOT LISTED. The names come from the binary's
#     own `-list-implementations`, so a seventh wrong implementation is executed
#     the day it is registered and cannot be forgotten here. The COUNT is pinned
#     (both directions), so a wrong implementation that is DELETED — the way a
#     kill quietly stops being backed — refuses instead of shrinking the loop.
#   * EACH ONE MUST EXIT 1, not merely "non-zero". 2 is this harness's unusable
#     code: an implementation that made the run refuse for some unrelated reason
#     would satisfy "non-zero" while killing nothing (P-62 — assert the
#     diagnostic, never the code alone).
#   * THE KILL MUST LAND IN THE LEDGER HALF. `ledger parity FAIL` plus
#     `ledger oracle-refusal FAIL` must be >= 1. Without this a wrong LEDGER
#     implementation could be "killed" by an unrelated loanschedule failure and
#     the gate would still be green. Note that the six are NOT alike here:
#     ledger-wrong-manual-permission-ignored passes all four parity vectors and
#     dies on an ORACLE-REFUSAL vector alone, which is why the sum is what is
#     asserted and not the parity count.
#   * THE BANNER MUST NAME IT. The report's "THIS IS A DELIBERATELY WRONG
#     IMPLEMENTATION" line proves the flag was actually honoured rather than
#     ignored, which is the failure mode that would make every arm below pass
#     against the CORRECT implementation.
#   * THE ANTI-NO-OP CONTROL IS THE RUN ITSELF. This gate is called only after
#     the graded run has already been performed with the CORRECT implementation,
#     so "these implementations always go red" and "everything goes red" are
#     distinguished by the verdict this run is about to return.
#
# COST: six extra in-process gradings of the committed store, measured at about
# 1.3 s each on this host, and no contact with the reference oracle beyond the
# probe this run already made. NOT RUN in self-test mode (the ledger half does
# not run at all there) and NOT RUN when the probe says the oracle is down (the
# run is already refusing; a gate that manufactured a second verdict out of that
# would be reading its own refusal as evidence). Both skips SAY SO.
#
# [T294: 6 -> 7.] ledger-wrong-openingbalance-posted-entries-ignored joins them —
# a port that implements defineOpeningBalance without ever reaching
# validateJournalEntriesArePostedBefore (:717/:810-816). It is the SECOND member
# of the family the bullet above singles out: like
# ledger-wrong-manual-permission-ignored it passes all four parity vectors and
# dies on an ORACLE-REFUSAL vector alone (LDG-REFUSE-03), which is why this gate
# asserts the SUM of the two ledger FAIL counts and not the parity count.
#
# [T295: 7 -> 9.] Two more join, and both are members of that same family —
# they pass all four parity vectors and die on an ORACLE-REFUSAL vector alone:
#
#   ledger-wrong-future-date-ignored          dies on LDG-REFUSE-05 alone.
#     Never compares the transaction date with the tenant's BUSINESS DATE (:629,
#     DateUtils.isDateInTheFuture -> isAfterBusinessDate). The business date is
#     tenant ambient state and appears nowhere in the request body, so a port can
#     be complete against the API documentation and still have the rule missing.
#
#   ledger-wrong-closure-boundary-exclusive   dies on LDG-REFUSE-04 alone.
#     THIS IS THE MONEY-PATH ONE. It implements the accounting-closure boundary
#     the way the oracle's OWN ERROR MESSAGE describes it — strictly "prior to"
#     the closing date — where :636 is !DateUtils.isBefore(closingDate,
#     transactionDate) and refuses transactionDate <= closingDate, INCLUSIVE. The
#     message and the code disagree about exactly one day, and that day is THE
#     CLOSING DATE ITSELF, which is the day a period-end adjustment carries. It
#     agrees with the correct port on every entry dated strictly before the
#     closing date, so only a capture taken ON the boundary kills it — and
#     LDG-REFUSE-04 is that capture.
#
#   ledger-wrong-openingbalance-always-refusing  [T305, and it is T296's ARM A]
#     THE ONE THIS CORPUS COULD NOT KILL UNTIL NOW. It refuses EVERY
#     defineOpeningBalance, including on an EMPTY ledger where the reference
#     oracle ACCEPTS (:812's CollectionUtils.isEmpty fall-through into the writes
#     at :742/:745). T296 measured it surviving the whole corpus, because every
#     refusal capture here AGREES with it; only an ACCEPTING-side observation can
#     kill it, and LDG-05 is that observation. It passes LDG-REFUSE-03 exactly.
#
#   ledger-wrong-openingbalance-no-contra        [T305]
#     Accepts the opening balance and writes only the caller legs, missing the
#     CONTRA entry :796 writes for each. Its output still satisfies
#     double_entry_balances, so no invariant can see it -- only the captured
#     cells can, and both totals are short by the entire opening position
#     (-35000062 minor units).
#
#   ledger-wrong-date-rules-always-refusing      [T328, and it is T296's ARM A on
#                                                 the DATE rules instead of the
#                                                 command]
#     11 -> 12. THE SECOND ONE THIS CORPUS COULD NOT KILL, AND ITS SURVIVAL WAS
#     MEASURED BEFORE IT WAS FIXED, which is the half that carries the argument.
#     It REFUSES EVERY DATED ENTRY: both date guards fire on the PRESENCE of the
#     state they read -- a GLClosure exists so the ledger is closed (:636), a
#     business date exists so the entry is in the future (:629-631) -- and
#     neither ever performs its comparison. It keeps both globalisation codes and
#     both messages, so LDG-REFUSE-04 and LDG-REFUSE-05 cannot tell it from a
#     correct port. RUN AGAINST THE STORE AS IT STOOD AT 136a2be6, BEFORE THE
#     PROMOTION: ledger parity PASS 5 FAIL 0, ledger oracle-refusal PASS 5 FAIL 0,
#     VERDICT PASS, EXIT 0
#     [.softhouse/capture/t328-date-rule-promotion/out/10-mutant-SURVIVES-before.txt].
#     Killed by LDG-06 and LDG-07 -- ONE GUARD EACH, and neither vector is
#     decorative: withdrawing either revives the other guard, measured arm by arm
#     in out/60-load-bearing-one-vector-at-a-time.txt.
#     WHY THE PRE-EXISTING DATE IMPLEMENTATIONS DID NOT COVER THIS.
#     ledger-wrong-future-date-ignored and ledger-wrong-closure-boundary-exclusive
#     both FAIL OPEN -- they post where the oracle refuses -- and refusal vectors
#     are exactly what kills those. This one FAILS CLOSED, and no refusal vector
#     can see it. Opposite errors on the same two rules, and until T328 the corpus
#     graded only one direction.
#
# T307 MOVES IT 12 -> 13.  ledger-wrong-accounting-closed-echoes-transaction-date
#     GETS THE CLOSURE BOUNDARY EXACTLY RIGHT AND QUOTES THE WRONG DATE BACK. It
#     refuses precisely the requests the oracle refuses, with the oracle's status,
#     globalisation code and message, and puts the SUBMITTED transactionDate in
#     errors[0].args[0].value where :637-638 constructs ACCOUNTING_CLOSED with
#     latestGLClosure.getClosingDate(). :631, five lines above, DOES echo the
#     transaction date -- for the OTHER date refusal -- so a porter who reads one
#     throw site and generalises writes exactly this.
#     WHY IT IS NOT A DUPLICATE OF ledger-wrong-closure-boundary-exclusive: that
#     one gets the BOUNDARY wrong and dies on LDG-REFUSE-04. This one is
#     INDISTINGUISHABLE from the reference implementation on LDG-REFUSE-04,
#     because A2-01 was posted ON the closing date and the two dates are EQUAL
#     there. It dies on LDG-REFUSE-06 alone, on ONE cell, refusal.arg0_value.
#     WHY IT COULD NOT HAVE BEEN REGISTERED BEFORE: nothing in this harness could
#     have killed it. The Refusal shape had three cells, A2-02's captured body is
#     BYTE-IDENTICAL to A2-01's on all three, and T295 correctly refused to
#     promote a vector no implementation could fail independently. T307 added the
#     fourth cell as a SELECTOR (expect.refusal.arg_echo), which is what makes
#     A2-02's bytes gradeable without pinning anything to a calendar.
EXEMPTION_PIN_LEDGER_WRONGIMPLS=15

gate_wrong_ledger_impls_die() {
  local bin="$1" probe="$2"
  local list out names n bad=0 impl rc kills banner pfail rfail

  if [ "$probe" != "up" ]; then
    say "conformance: wrong-ledger-implementation gate NOT RUN: the reference oracle probe reads"
    say "conformance:   '$probe', so this run is already refusing and every arm below would go red"
    say "conformance:   for that reason instead of for the one it tests. Nothing is claimed."
    return 0
  fi

  list="$(mktemp "${TMPDIR:-/tmp}/conformance-implist.XXXXXXXXXX")" || return 1
  "$bin" -list-implementations >"$list" 2>&1
  # The wrong ones are exactly the rows the binary itself marks. Read from a
  # FILE with sed; no pipeline, no early-exiting consumer (P-57).
  names="$(LC_ALL=C sed -n 's/^\([a-z0-9-][a-z0-9-]*\)   \[-ledger-impl\] DELIBERATELY WRONG:.*$/\1/p' "$list")"
  n=0
  for impl in $names; do n=$((n + 1)); done
  say "conformance: CENSUS wrong ledger implementations — discovered $n registered as DELIBERATELY"
  say "conformance:   WRONG from the binary's own -list-implementations; pinned at"
  say "conformance:   $EXEMPTION_PIN_LEDGER_WRONGIMPLS."
  if [ "$n" -ne "$EXEMPTION_PIN_LEDGER_WRONGIMPLS" ]; then
    warn "conformance: WRONG-IMPLEMENTATION POPULATION $n, PINNED $EXEMPTION_PIN_LEDGER_WRONGIMPLS."
    warn "conformance: An added one must be executed here in the same commit that registers it; a"
    warn "conformance: DELETED one silently withdraws a kill that vectors still cite. Both directions"
    warn "conformance: move EXEMPTION_PIN_LEDGER_WRONGIMPLS in .softhouse/conformance.sh, deliberately."
    warn "conformance: THE REPORT ABOVE MAY CARRY THE BINARY'S OWN 'VERDICT: PASS (exit 0)' LINE. IT IS"
    warn "conformance: WITHDRAWN BY THIS GATE. That line is the BINARY's verdict over the corpus; this"
    warn "conformance: gate runs after it, like gate_exemption_census, and can only make a verdict"
    warn "conformance: worse. The verdict of the RUN is this one, and it is EXIT 2."
    warn "conformance: EXIT 2 — no verdict is available. This is NOT a pass."
    rm -f "$list"
    return 1
  fi

  out="$(mktemp "${TMPDIR:-/tmp}/conformance-wrongimpl.XXXXXXXXXX")" || return 1
  for impl in $names; do
    "$bin" "-oracle-probe=$probe" "-ledger-impl=$impl" >"$out" 2>&1
    rc=$?
    banner=0
    LC_ALL=C grep -aqF 'THIS IS A DELIBERATELY WRONG IMPLEMENTATION' "$out" && banner=1
    pfail="$(LC_ALL=C sed -n 's/^ *ledger parity  *PASS [0-9][0-9]*  *FAIL \([0-9][0-9]*\)$/\1/p' "$out")"
    rfail="$(LC_ALL=C sed -n 's/^ *ledger oracle-refusal  *PASS [0-9][0-9]*  *FAIL \([0-9][0-9]*\).*$/\1/p' "$out")"
    [ -n "$pfail" ] || pfail=0
    [ -n "$rfail" ] || rfail=0
    kills=$((pfail + rfail))
    if [ "$rc" -eq 1 ] && [ "$banner" -eq 1 ] && [ "$kills" -ge 1 ]; then
      say "conformance:   KILLED  $impl — exit 1, ledger parity FAIL $pfail + oracle-refusal FAIL $rfail"
    else
      bad=1
      warn "conformance:   SURVIVED $impl — exit $rc (wanted 1), wrong-implementation banner $banner"
      warn "conformance:            (wanted 1), ledger FAILs $kills (wanted >= 1)."
      LC_ALL=C sed -n 's/^\( *ledger \(parity\|oracle-refusal\|inadmissible\|harness errors\).*\)$/\1/p' "$out" >&2
    fi
  done
  rm -f "$list" "$out"

  if [ "$bad" -ne 0 ]; then
    warn "conformance:"
    warn "conformance: A DELIBERATELY WRONG LEDGER IMPLEMENTATION SURVIVED THE CORPUS."
    warn "conformance: Every ledger vector's graded_against row claims a wrong implementation it can"
    warn "conformance: kill. One that survives means the corpus no longer discriminates: the claim is"
    warn "conformance: still written down and is no longer true. Either the vector that backed the kill"
    warn "conformance: was weakened, or the wrong implementation stopped being wrong. Do not 'fix' this"
    warn "conformance: by deleting the implementation — that removes the evidence, not the defect."
    warn "conformance: THE REPORT ABOVE MAY CARRY THE BINARY'S OWN 'VERDICT: PASS (exit 0)' LINE. IT IS"
    warn "conformance: WITHDRAWN BY THIS GATE. That line is the BINARY's verdict over the corpus; this"
    warn "conformance: gate runs after it, like gate_exemption_census, and can only make a verdict"
    warn "conformance: worse. The verdict of the RUN is this one, and it is EXIT 2."
    warn "conformance: EXIT 2 — no verdict is available. This is NOT a pass."
    return 1
  fi
  say "conformance:   all $n wrong ledger implementations DIED through this harness, not by hand."
  return 0
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
  CONF_BIN="$(mktemp "${TMPDIR:-/tmp}/conformance.XXXXXXXXXX")" || exit "$EXIT_UNUSABLE"
  build_binary "$CONF_BIN"

  local args=()
  [ -n "$context" ] && args+=("-context=$context")

  # THE REPORT IS CAPTURED TO A FILE AND THEN PRINTED, rather than streamed. Two
  # reasons, and the second is the load-bearing one. (1) gate_exemption_census has
  # to READ the figures the report prints, and a figure nobody reads is not a gate
  # (T194's rule, one census over). (2) It must NOT be a pipeline: `"$CONF_BIN" |
  # tee` would hand `$?` to tee, and any `grep -q`-shaped consumer under
  # `set -o pipefail` poisons the status of the producer (P-57). A file has neither
  # hazard. The full output is printed unmodified either way, so a reader loses
  # nothing but the interleaving of two streams that were already separate.
  local report
  report="$(mktemp "${TMPDIR:-/tmp}/conformance-report.XXXXXXXXXX")" || exit "$EXIT_UNUSABLE"

  if [ "$self_test" = "1" ]; then
    say "conformance: SELF-TEST MODE — grading the harness, not a port. Not a conformance PASS."
    "$CONF_BIN" -self-test "${args[@]+"${args[@]}"}" >"$report" 2>&1
    rc=$?
  else
    probe="$(probe_oracle)"
    say "conformance: reference oracle ($ORACLE_HEALTH_URL) probe = $probe"
    if [ "$probe" != "up" ]; then
      warn "conformance: the reference oracle is UNREACHABLE."
      warn "conformance: conformance reports EXIT 2, not a false PASS, and 2 never becomes 0."
    fi
    "$CONF_BIN" "-oracle-probe=$probe" "${args[@]+"${args[@]}"}" >"$report" 2>&1
    rc=$?
  fi
  cat "$report"

  # THE CENSUS GATE RUNS WHATEVER THE BINARY SAID, and it can only make a verdict
  # WORSE. On an already-failing run its refusal is folded into the existing exit;
  # on a PASSING run it is the whole point, because the drift it catches is
  # invisible to every check the binary makes — each exemption individually
  # admissible, the population wrong.
  if ! gate_exemption_census "$report"; then
    rm -f "$report"
    return "$EXIT_UNUSABLE"
  fi
  rm -f "$report"

  # THE SIX WRONG LEDGER IMPLEMENTATIONS, EXECUTED ON THE AUTOMATIC PATH.
  # Placed AFTER the graded run for two reasons: the run above is this gate's
  # anti-no-op control (it is the CORRECT implementation going green over the
  # same corpus), and the probe it measured is the one passed on, so no arm
  # below asserts a reachability this run did not observe. Like the census gate,
  # it can only make a verdict WORSE.
  if [ "$self_test" = "1" ]; then
    say "conformance: wrong-ledger-implementation gate NOT RUN: this is SELF-TEST mode, in which the"
    say "conformance:   ledger half is not graded at all, so there is nothing for a wrong ledger"
    say "conformance:   implementation to fail. Nothing is claimed about the six."
  elif ! gate_wrong_ledger_impls_die "$CONF_BIN" "$probe"; then
    return "$EXIT_UNUSABLE"
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
  # --prove does NOT go through run_guards, but it does build_binary and then run that
  # binary — which resolves its repo root from CONFORMANCE_REPO_ROOT exactly as a graded run
  # does. Guarding only main_grade would have converted a known hole into a hidden one, which
  # is the same mistake the census block above records at "fixing only the census one".
  guard_graded_root_is_this_tree || exit "$EXIT_UNUSABLE"
  local rc pass=0 fail=0 bin tmp
  # ONE SOURCE FOR THE PROOF TAIL. [T300] `expect` and `expect_saying` below each said
  # "--- last 6 lines of that run ---" and then ran `tail -6` on the NEXT line: two literals,
  # four sites, able to disagree with each other and with nothing to notice if they did. Same
  # class as the census cardinals this commit derives — P-80, "A CORRECTED CARDINAL ROTS IN
  # EVERY PLACE IT WAS RESTATED. The count is the same defect as the line number." Here the
  # heading now READS the value the tail uses, so a change to one is a change to both.
  local proof_tail=6
  CONF_BIN="$(mktemp "${TMPDIR:-/tmp}/conformance.XXXXXXXXXX")" || exit "$EXIT_UNUSABLE"
  CONF_TMP="$(mktemp -d "${TMPDIR:-/tmp}/conformance-prove.XXXXXXXXXX")" || exit "$EXIT_UNUSABLE"
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
    [ "$got" = "$want" ] && printf '%s' "$out" | LC_ALL=C grep -aqF -- "$needle" && ok=1
    if [ "$ok" = 1 ]; then
      say "PROOF OK   exit $got (wanted $want)   $label"
      pass=$((pass+1))
    else
      say "PROOF FAIL exit $got (wanted $want)   $label"
      say "           the output had to contain: $needle"
      say "$out"
      fail=$((fail+1))
    fi
    say "--- last $proof_tail lines of that run ------------------------------------"
    printf '%s\n' "$out" | tail -"$proof_tail"
    say ""
  }

  # assert_mutated refuses to run a proof whose perturbation did not apply. A
  # mutation proof over an unmutated file proves nothing and looks identical to
  # one that works.
  assert_mutated() { # assert_mutated <file> <needle>
    if ! LC_ALL=C grep -aqF -- "$2" "$1"; then
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
    say "--- last $proof_tail lines of that run ------------------------------------"
    printf '%s\n' "$out" | tail -"$proof_tail"
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
  if ! LC_ALL=C grep -aq '"50001"' "$tmp/perturbed/_selftest/SELFTEST-01-two-period-zero-rate.json"; then
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
     && printf '%s' "$out8" | LC_ALL=C grep -aq 'self-test fixtures      PASS 1' \
     && printf '%s' "$out8" | LC_ALL=C grep -aq 'parity vectors          PASS 0' \
     && printf '%s' "$out8" | LC_ALL=C grep -aq 'SELF-TEST FIXTURE' \
     && printf '%s' "$out8" | LC_ALL=C grep -aq 'EXCLUDED from the parity count' \
     && printf '%s' "$out8" | LC_ALL=C grep -aq 'NOT a conformance PASS'; then
    say "PROOF OK   exit $rc8               the fixture PASSES and parity stays 0, stamped NOT a conformance PASS"
    pass=$((pass+1))
  else
    say "PROOF FAIL exit $rc8               the fixture's pass/parity accounting is not as claimed"
    say "$out8"
    fail=$((fail+1))
  fi
  printf '%s\n' "$out8" | LC_ALL=C grep -aE 'self-test fixtures|parity vectors|VERDICT'
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
  printf '%s' "$out19a" | LC_ALL=C grep -aq 'WITHDRAWS from grading' || ok19=0
  printf '%s' "$out19a" | LC_ALL=C grep -aq 'P-02' || ok19=0
  # DELIBERATELY NOT asserted: that the store-wide "killed by
  # MONTHEND-CONTINUE-FROM-CLAMPED-DAY" line disappears. T58 promoted P-ME-* vectors
  # that carry the SAME counterfactual id and legitimately back it, so that line is
  # now printed by them and its presence says nothing about P-02. The store-wide
  # aggregate is the wrong place to assert a PER-VECTOR refusal; the two greps above
  # assert it where it actually lives, by vector name and with the diagnostic.
  printf '%s' "$out19b" | LC_ALL=C grep -aq 'killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY' || ok19=0
  # NOT a frozen count: T57 moved the corpus 11 -> 13 and a literal here would go
  # stale on every promotion (finding D-6, third recurrence). Assert the PROPERTY --
  # the pristine store still grades clean with no failures.
  printf '%s' "$out19b" | LC_ALL=C grep -aqE 'parity vectors +PASS [0-9]+ +FAIL 0' || ok19=0
  if [ "$ok19" = 1 ]; then
    say "PROOF OK   exit $rc19a/$rc19b       T9-F1b: withdrawn cells STOP backing the kill; recorded ones still back it"
    pass=$((pass+1))
  else
    say "PROOF FAIL exit $rc19a/$rc19b       T9-F1b coverage is not as claimed (want 2 then 0)"
    say "$out19a"
    say "$out19b"
    fail=$((fail+1))
  fi
  printf '%s\n' "$out19a" | LC_ALL=C grep -aE 'UNBACKED|monthend.reanchor|VERDICT'
  printf '%s\n' "$out19b" | LC_ALL=C grep -aE 'monthend.reanchor|parity vectors|VERDICT'
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
  local out20 rc20 out20c rc20c ok20 why20 violated_hits
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
    # `grep -c`, NOT `grep -q`. THIRD SITE OF THE SAME FAIL-OPEN SHAPE (T191), and the
    # only one of the three whose producer is the bash BUILTIN `printf` rather than
    # `perl` — the builtin dies of SIGPIPE just the same, measured on this host at
    # 65,549 B of `$out20` versus 65,548 B still clean. `$out20` is a whole harness run's
    # combined stdout+stderr, so it grows with the corpus: this is the site of the three
    # MOST likely to cross the buffer on its own, and when it does, `grep -q` matching
    # 'INVARIANT ... VIOLATED' on line 1 kills the printf, pipefail makes the pipeline
    # non-zero, the `if` reads FALSE, and note20 is never called — the proof would
    # report OK on the very FALSE VIOLATION it exists to detect. Polarity matters: the
    # neighbouring `... || note20 ...` checks fail CLOSED under the same defect (a killed
    # producer reads as "needle absent" -> note20 -> FAIL), which is a false alarm, not a
    # silent pass. This one, and only this one in the block, fails OPEN.
    violated_hits="$(printf '%s' "$out20" \
                     | LC_ALL=C grep -acF -- 'INVARIANT principal_amortizes_to_zero VIOLATED')" || true
    [ -n "$violated_hits" ] || violated_hits=0
    if [ "$violated_hits" -gt 0 ]; then
      note20 "FALSE VIOLATION: principal_amortizes_to_zero was reported VIOLATED against a stand-in."
    fi

    # --- the FALSE HOLD direction. Per-vector, so no corpus count is involved:
    #     an invariant has exactly ONE status per vector, and asserting it is N/A
    #     on this vector excludes HOLD on this vector. ---
    printf '%s' "$out20" \
      | LC_ALL=C grep -aqE 'SELFTEST-01-two-period-zero-rate .* principal_amortizes_to_zero \[N/A\]' || note20 \
      "FALSE HOLD: principal_amortizes_to_zero did not report N/A for the vector whose final outstanding was withdrawn."
    printf '%s' "$out20" | LC_ALL=C grep -aqF -- \
      'NOT ASSERTED: row 2: final outstanding == 0 cannot be asserted (outstanding_principal_minor never recorded by the capture' \
      || note20 "no NOT ASSERTED line names the withdrawn cell, so a reader cannot tell the check stopped checking."
    printf '%s' "$out20" | LC_ALL=C grep -aqE 'invariant assertions +[1-9][0-9]* NOT RUN' || note20 \
      "the summary counted ZERO skipped assertions while a cell the invariants read was a placeholder."

    # --- the anti-no-op control, over the PRISTINE store ---
    [ "$rc20c" = 0 ] || note20 "control: the pristine store no longer self-tests clean (exit $rc20c, wanted 0)."
    printf '%s' "$out20c" | LC_ALL=C grep -aqE 'principal_amortizes_to_zero +hold [1-9][0-9]* +violated 0' || note20 \
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
    printf '%s\n' "$out20" | LC_ALL=C grep -aE 'principal_amortizes_to_zero|NOT ASSERTED|invariant assertions|VERDICT'
    printf '%s\n' "$out20c" | LC_ALL=C grep -aE 'principal_amortizes_to_zero|invariant assertions|VERDICT'
    say ""
  fi

  # 21. CONFORMANCE_REPO_ROOT MUST NOT BE ABLE TO MOVE THE GRADED TREE. [T201, from T199 D-1]
  #     RED and GREEN, at the function AND at the whole-harness level (P-56: the guard is
  #     tested where it runs, not only where it is defined).
  #
  #     The stand-in root is built to be VALID — `.softhouse/vectors/` and `nexus/go.mod`,
  #     the two things reporoot.go's validateExplicitRoot stats. That is deliberate: if the
  #     refusal only fired on a malformed path it would be proving the wrong thing. It fires
  #     because the root DIVERGES, not because it is broken.
  #
  #     `--self-test` is used for the end-to-end arms because it exercises the identical
  #     load_toolchain -> run_guards path a graded run takes, contacts NO oracle, and costs
  #     about 7s. The RED arm must also show it never reached the guards downstream of the
  #     divergence check — a refusal printed AFTER a census would mean the census had already
  #     read the wrong tree.
  do_prove21() {
    local other="$tmp/other-checkout" script="$REPO_ROOT/.softhouse/conformance.sh"
    local ok21=1 why21="" out rc
    mkdir -p "$other/.softhouse/vectors" "$other/nexus" || { say "PROOF FAIL could not build the stand-in root"; fail=$((fail+1)); return; }
    printf 'module stand-in\n\ngo 1.22\n' > "$other/nexus/go.mod"
    note21() { ok21=0; why21="$why21 [$1]"; }

    # --- GREEN: unset. The anchor decides and the anchor is this tree. ---
    ( unset CONFORMANCE_REPO_ROOT; guard_graded_root_is_this_tree ) >/dev/null 2>&1 \
      || note21 "GREEN(unset): the guard refused a run that set nothing at all."
    # --- GREEN: set, but naming THIS tree, including a trailing-slash spelling. `pwd -P` on
    #     both sides must make those the same tree, or the guard is a cry-wolf machine. ---
    ( CONFORMANCE_REPO_ROOT="$REPO_ROOT"  guard_graded_root_is_this_tree ) >/dev/null 2>&1 \
      || note21 "GREEN(same): the guard refused CONFORMANCE_REPO_ROOT set to its OWN root."
    ( CONFORMANCE_REPO_ROOT="$REPO_ROOT/" guard_graded_root_is_this_tree ) >/dev/null 2>&1 \
      || note21 "GREEN(same+slash): a trailing slash was treated as a different tree."
    # --- RED: a different, VALID checkout root. ---
    if ( CONFORMANCE_REPO_ROOT="$other" guard_graded_root_is_this_tree ) >/dev/null 2>&1; then
      note21 "RED(diverged): the guard ACCEPTED a valid root that is not this tree."
    fi
    # --- RED: a path that does not exist. Unresolvable is not clean. ---
    if ( CONFORMANCE_REPO_ROOT="$tmp/no-such-tree" guard_graded_root_is_this_tree ) >/dev/null 2>&1; then
      note21 "RED(missing): the guard ACCEPTED a CONFORMANCE_REPO_ROOT that does not exist."
    fi

    # --- RED, END TO END: the whole harness, invoked the way the driver invokes it. ---
    out="$(CONFORMANCE_REPO_ROOT="$other" bash "$script" --self-test 2>&1)"; rc=$?
    [ "$rc" = "$EXIT_UNUSABLE" ] || note21 "RED(e2e): exit $rc, wanted $EXIT_UNUSABLE — THIS IS THE WHOLE DEFECT: T199 measured exit 0 here."
    printf '%s\n' "$out" | LC_ALL=C grep -aqF 'CONFORMANCE_REPO_ROOT IS SET AND POINTS AWAY FROM THIS HARNESS' \
      || note21 "RED(e2e): refused without naming the divergence, so a reader cannot tell why."
    if printf '%s\n' "$out" | LC_ALL=C grep -aqE '^conformance: CENSUS '; then
      note21 "RED(e2e): a guard downstream of the divergence check still ran and censused a tree."
    fi
    # --- GREEN, END TO END: the anti-no-op control. If this arm ever fails, the guard has
    #     stopped being a guard and started being an unconditional refusal. ---
    out="$(CONFORMANCE_REPO_ROOT="$REPO_ROOT" bash "$script" --self-test 2>&1)"; rc=$?
    [ "$rc" = 0 ] || note21 "GREEN(e2e): exit $rc over its OWN root — the guard now refuses everything."
    printf '%s\n' "$out" | LC_ALL=C grep -aqF 'names THIS tree' \
      || note21 "GREEN(e2e): the guard did not record that it had checked and agreed."
    printf '%s\n' "$out" | LC_ALL=C grep -aqF 'SELF-TEST PASS' \
      || note21 "GREEN(e2e): the run did not complete, so the guard cannot be shown to be pass-through."

    if [ "$ok21" = 1 ]; then
      say "PROOF OK   T201/T199-D1: CONFORMANCE_REPO_ROOT cannot move the graded tree — RED on a diverged root (exit $EXIT_UNUSABLE, not 0), GREEN on its own"
      pass=$((pass+1))
    else
      say "PROOF FAIL T201/T199-D1: the repo-root divergence refusal is not as claimed:$why21"
      fail=$((fail+1))
    fi
    say ""
  }
  do_prove21

  # 22. THE CENSUS FIGURE MUST BE THE FIRST `inspected N`, NOT THE LAST. [T201, from T197 F-1]
  #     Both directions, and the RED arm is run against the EXACT expression this file used
  #     to ship, inline, so the proof demonstrates it would have caught the old code rather
  #     than merely agreeing with the new code.
  do_prove22() {
    local ok22=1 why22="" cases old new
    note22() { ok22=0; why22="$why22 [$1]"; }
    # Line shapes: the two the live guards actually print (subject counts 320 and 57), then
    # a two-figure ASCENDING line (the FAIL-OPEN direction), a two-figure DESCENDING line and
    # a line whose interpolated PATH carries the token (both FAIL-CLOSED), then a CENSUS line
    # with no figure at all, which must yield nothing from either expression.
    cases="$(printf '%s\n' \
      'CENSUS wire-float round-trip — inspected 320 request bodies / 3976 numeric tokens across 6 capture rigs / 10 req directories under /x/.softhouse/capture (recursive, whole capture tree)' \
      'CENSUS narrow-catch — inspected 57 .java files across 20 directories under /x (recursive, whole repository; EXCLUDED 0 other checkout root(s): none)' \
      'CENSUS ascending — inspected 7 rigs / inspected 320 tokens' \
      'CENSUS descending — inspected 320 bodies / inspected 7 rigs' \
      'CENSUS pathword — inspected 57 .java files under /x/inspected 0 fixtures/repo (recursive)' \
      'CENSUS no-figure — nothing was counted here')"

    # GREEN: the shipped extraction reads the subject count on every shape.
    new="$(printf '%s\n' "$cases" | census_inspected | LC_ALL=C tr '\n' ' ')"
    [ "$new" = "320 57 7 320 57 " ] \
      || note22 "GREEN: census_inspected read [$new], wanted the first figure of each line [320 57 7 320 57 ]."

    # RED: the same input through the greedy expression this file shipped until T201. It must
    # DISAGREE, or the fix is a no-op and this proof is decoration.
    old="$(printf '%s\n' "$cases" | LC_ALL=C sed -n 's/^CENSUS .*inspected \([0-9][0-9]*\).*$/\1/p' | LC_ALL=C tr '\n' ' ')"
    [ "$old" != "$new" ] || note22 "RED: the greedy expression and the fixed one agree on every case — the proof cannot fail, so it proves nothing."
    [ "$old" = "320 57 320 7 0 " ] \
      || note22 "RED: the greedy expression read [$old]; the recorded defect is [320 57 320 7 0 ] (last-wins)."
    # The fail-OPEN member, named on its own so the polarity is asserted and not merely implied:
    # on the ascending line the old expression returns a figure ABOVE the subject count, which
    # is how a guard that inspected 7 of 320 files clears a floor of 320.
    printf '%s\n' 'CENSUS ascending — inspected 7 rigs / inspected 320 tokens' \
      | LC_ALL=C sed -n 's/^CENSUS .*inspected \([0-9][0-9]*\).*$/\1/p' \
      | LC_ALL=C grep -aqx '320' \
      || note22 "the FAIL-OPEN case no longer reproduces against the old expression; the polarity claim in census_inspected's header is stale."
    # A CENSUS line with no figure must stay silent, not become 0 — 0 would be P-35's vacuous
    # pass arriving through the front door.
    if printf '%s\n' 'CENSUS no-figure — nothing was counted here' | census_inspected | LC_ALL=C grep -aq .; then
      note22 "a CENSUS line carrying no 'inspected N' produced a figure; it must produce nothing."
    fi

    if [ "$ok22" = 1 ]; then
      say "PROOF OK   T201/T197-F-1: the census figure is the FIRST 'inspected N' — new [$new] vs the shipped greedy [$old]"
      pass=$((pass+1))
    else
      say "PROOF FAIL T201/T197-F-1: the census extraction is not as claimed:$why22"
      fail=$((fail+1))
    fi
    say ""
  }
  do_prove22

  say "======================================================================="
  say "PROOFS: $pass passed, $fail failed"
  say "======================================================================="
  [ "$fail" -eq 0 ] || return 1
  return 0
}

# ---------------------------------------------------------------------------
case "${1:-}" in
  # Not `exit 0`: if usage() cannot find the sentinel that bounds its own text it
  # fails, and --help must not report success over output it could not produce.
  # (P-22 — a check that cannot fail is worse than no check.)
  # Not `exit $?` either, which is what it used to be. That propagated usage()'s
  # `return 1` — and 1 is this file's GRADED FAIL code, "a mismatch or a violated
  # property invariant, a definite reproducible defect". A broken help text is
  # not a failed vector; it is the harness being unusable, which is 2 by this
  # file's own EXIT CODES table. Reported as 1, `--help` on a file with a damaged
  # header would have looked exactly like a real conformance failure to any
  # caller that reads exit codes — the same class of confusion exit 3 exists to
  # abolish, one code over. (T106 F3, applied by T113.)
  #
  # T130 (T121's F-T121-3): true, and worth saying in full. 2 is not a private
  # bucket — see the WHY IT EXISTS block near the top of this file. It is
  # deliberately AMBIGUOUS between "the oracle is unusable" and "the corpus is
  # unusable", and this arm is the eighth member of that existing polysemy rather
  # than a new collision. It is still right: no grading caller passes `--help`,
  # the stderr text names the missing sentinel, and 1 must stay reserved for a
  # graded FAIL. What disambiguates 2 for a reader is NOT this arm but the
  # `probe = up|down` line printed unconditionally before the graded binary runs;
  # the driver parks only on `exit 2` AND `probe != up`.
  --help|-h)   usage || exit "$EXIT_UNUSABLE"; exit 0 ;;
  --prove)     prove; exit $? ;;
  --self-test) main_grade "${2:-}" 1; exit $? ;;
  --*)         warn "conformance: unknown option $1"; usage; exit "$EXIT_UNUSABLE" ;;
  *)           main_grade "${1:-}" 0; exit $? ;;
esac
