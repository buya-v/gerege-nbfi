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
  # [VERIFIED: .softhouse/capture/lib/check_wire_float_roundtrip.py:78-102]. `git ls-files`
  # is asked for the same set from the index instead of from `os.walk`, so the two agree
  # only if the guard actually opened the tree. Measured in this worktree: guard 320,
  # floor 320. Tracked is a SUBSET of walked (untracked files raise the guard's figure and
  # never the floor), which is why _run_capture_guard compares with `>=`.
  local floor
  floor="$(git -C "$REPO_ROOT" ls-files -z -- .softhouse/capture 2>/dev/null \
           | LC_ALL=C tr '\0' '\n' \
           | LC_ALL=C grep -acE '(/req/[^/]+\.json|\.req)$' || true)"
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

run_guards() {
  local failed=0
  # FIRST, and it SHORT-CIRCUITS rather than joining the `failed=1` tally the others use.
  # Two reasons, both learned the expensive way. (1) Every guard below answers a question
  # about $REPO_ROOT; until it is settled that $REPO_ROOT is the tree being GRADED, none of
  # their answers is about the run in progress, and a dozen green census lines printed under
  # a refusal read as "mostly fine". That is the T165 failure mode exactly — the true
  # statement was in the output and the reader took the summary instead. (2) The tally style
  # exists so that one bad guard does not hide another; here there is nothing to hide, the
  # divergence subsumes every downstream result.
  guard_graded_root_is_this_tree || {
    warn "conformance: EXIT 2 — no verdict is available, and NO other guard was run: their"
    warn "conformance: results would describe a tree this run was not going to grade."
    exit "$EXIT_UNUSABLE"
  }
  guard_no_float_in_vectors           || failed=1
  guard_no_float_in_harness           || failed=1
  guard_gofmt                         || failed=1
  guard_no_float_in_capture_requests  || failed=1
  guard_no_narrow_catch_in_capture_rigs || failed=1
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
  # --prove does NOT go through run_guards, but it does build_binary and then run that
  # binary — which resolves its repo root from CONFORMANCE_REPO_ROOT exactly as a graded run
  # does. Guarding only main_grade would have converted a known hole into a hidden one, which
  # is the same mistake the census block above records at "fixing only the census one".
  guard_graded_root_is_this_tree || exit "$EXIT_UNUSABLE"
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
    say "--- last 6 lines of that run -------------------------------------------"
    printf '%s\n' "$out" | tail -6
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
