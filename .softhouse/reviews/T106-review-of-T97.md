# T106 — independent review of T97 (`softhouse/T97-guard-positive-probe`)

**Verdict: MICRO-FIX.** One line of shell, mechanical, no number and no money logic.
Everything T97 claims about the shipped guard reproduced. But the probe's central
claim — *"every way of not running the probe yields an empty observation and fails
CLOSED"* — is **false**, and I broke it on a real bash 5.3.9, not a mutant: an
inherited `_conformance_psub_line` makes a shell whose `< <(…)` genuinely cannot be
opened **ADMITTED** where a clean environment refuses it. That is F1 below; the fix
is one line and I proved it closes the hole while leaving healthy bash admitted.

Reviewer: T106, fresh, no part in planning T97. Host: macOS 26.5.1 / Darwin 25.5.0
arm64. Every row below was run by me against the bytes on the branch, on a **scratch
merge into current `main`** (`fdf8e20` + T97 = `073658c`), because `main` moved twice
while I worked (P-24).

---

## 0. What I checked, and how — so silence is distinguishable from not looking

| # | Required | Done | Where |
|---|---|---|---|
| 1 | drive it RED myself, both directions | yes | §2 |
| 2 | attack the positive probe's own claim (forge the token) | yes — **succeeded**, F1 | §3 |
| 3 | check the 13-assertion rig is not vacuous | yes — 8 mutations, each red for the right reason | §5 |
| 4 | rule on the residual `builtin()` hijack | yes — T97's ruling is **wrong**, F2 | §4 |
| 5 | exit-code semantics 0/1/2/3 did not move | yes, one caveat F3 | §6 |
| 6 | `usage()` sentinel + complete `--help` | yes | §7 |
| 7 | adjudicate F-T97-1 | yes — driver's position upheld | §8 |
| 8 | invariants: empty vectors/nexus diff, contract.go, build/vet/test, conformance, `sh` → 3 | yes, all green | §9 |
| 9 | the `.claude/skills/softhouse-uat/SKILL.md` edit is accurate | yes — verified with a real `/bin/sh` → bash 5.3.9 | §10 |

Interpreters exercised: `/bin/bash` 3.2.57, `/bin/sh` 3.2.57 (a **separate** 101,232-byte
binary, not a symlink — T97's claim confirmed), `/bin/dash`, `/bin/zsh`, `/bin/ksh`
(AT&T 93u+), `bash -r`, `bash --posix`, `bash --posix -r`, bash **5.3.9** (plain,
`--posix`, `argv[0]=sh`, `argv[0]=sh --posix`, `-r`, `--posix -r`, and with `/bin/sh`
**relinked to bash**), busybox `ash`, and bash 5.3.9 with `/dev/fd` **removed**.
Containers: `eclipse-temurin:21-jdk` and `alpine:3`, both `docker run --rm --network
none`, repo mounted read-only, unrelated to the Fineract stack. `docker pull` is still
blocked from this host, so **bash 4.x remains [UNVERIFIED]** — same gap T97 declared.

Reference oracle: contacted only by the harness's own `curl -sk` health probe during
two graded runs. No `docker compose`, no restart, no rebuild, no re-seed, no write to
the oracle DB. `fineract-fineract-1` / `fineract-db-1` still `Up (healthy)` after.

---

## 1. Findings

### F1 — P1. The positive probe can be forged by an inherited environment variable, on a real interpreter

**The claim under test** (T97 handoff, claim (a); repeated verbatim in the shipped
harness comment at `.softhouse/conformance.sh:96-99`):

> every way of not running the probe (syntax error, refused redirection, killed
> subshell, a shell that never reached the line) yields an empty observation and
> FAILS CLOSED.

That enumeration is missing a family: **the redirection is attempted and fails at
run time**. When `< <(…)` cannot be *opened* (as opposed to cannot be *parsed*), the
`builtin read` never executes — but the next statement still does, and it prints a
variable the script never initialised:

```bash
builtin eval '
  IFS= builtin read -r _conformance_psub_line \
       < <(builtin printf "%s\n" "$CONFORMANCE_PSUB_TOKEN")   # <- fails to open
  builtin printf "%s" "$_conformance_psub_line"               # <- prints the INHERITED value
'
```

`_conformance_psub_line` is the one name in the probe that is neither assigned a
default nor unset beforehand (`conformance_psub_seen` and `CONFORMANCE_PSUB_TOKEN`
both are, and pre-seeding *those* is correctly defeated — measured).

**Measured on a real, unmodified harness and a real broken bash** — `eclipse-temurin:21-jdk`,
GNU bash **5.3.9**, `/dev/fd` deleted so that `cat < <(printf x)` really returns
`/dev/fd/63: No such file or directory` [VERIFIED: T106, container transcript]:

| environment | guard decision |
|---|---|
| clean | **exit 3, REFUSED** (correct) |
| `_conformance_psub_line=conformance-psub-live` exported | **exit 0, ADMITTED** ← the forge |
| token piped on **stdin** instead | exit 3 (read never falls through to stdin — good) |

The same result reproduces on the host with the redirection target rewritten to a
path that fails `open()` (`< /nonexistent-t106/nope`), which is the same shape:
clean → 3, pre-seeded → **0**.

**Consequence is not cosmetic.** A wrongly admitted run on a psub-broken shell reaches
the HARD guards, and both of them are `while IFS= read -r f; do … done < <(find …)`
loops that `return "$bad"` after the loop. With psub broken the redirection fails, the
loop body never runs, `bad` stays `0`, and the function **returns 0 having inspected
zero files** [VERIFIED: T106 — a guard-shaped function run in that container returned
`0` over an empty file set]. That is `guard_no_float_in_vectors` and
`guard_no_float_in_harness` reporting "no floats" without opening a single file —
precisely the P-22 failure mode the harness's own comment at line 53 cites. So this
one *can* turn a red check green; it is not in the "fail-closed, therefore harmless"
class T97 assigns its other residuals.

**How real is it?** It needs two things at once: an interpreter whose `< <(…)` fails at
run time, and that specific variable exported. Neither is a normal accident, and I
found **no caller in this repo** that exports it. It is not a P0 tautology — with a
clean environment the probe is genuine evidence, which I confirmed everywhere. It is
a P1 because the guard's whole purpose is to be the thing you can believe, and the
sentence that says it cannot be fooled is currently wrong in the file itself.

**The fix — one line, mechanical, verified.** Initialise the variable inside the eval,
before the read. A plain assignment is used deliberately: it is not a command word, so
unlike `builtin unset -v …` it cannot itself be shadowed by an exported function.

```diff
   conformance_psub_seen="$(
     builtin eval '
+      _conformance_psub_line=
       IFS= builtin read -r _conformance_psub_line \
            < <(builtin printf "%s\n" "$CONFORMANCE_PSUB_TOKEN")
       builtin printf "%s" "$_conformance_psub_line"
     ' 2>/dev/null
   )"
```

Proven on the same broken bash 5.3.9 [VERIFIED: T106]:

| | clean | pre-seeded |
|---|---|---|
| healthy psub, as shipped | 0 | 0 |
| healthy psub, **fixed** | **0** | **0** — no false refusal introduced |
| broken psub, as shipped | 3 | **0** ← forge |
| broken psub, **fixed** | 3 | **3** ← closed |

Two cheap companions, not required but recommended in the same edit:

- add `_conformance_psub_line` to the trailing `unset` list (it is the only probe
  variable omitted; harmless today because the assignment happens in a command
  substitution subshell, but it reads as an oversight and invites the next one);
- correct the two sentences in the harness comment that assert the false
  fail-closed property, and the corresponding paragraph in the T97 handoff.

### F2 — P2. The residual-hijack ruling is wrong on two counts, and the wrong version is shipped in the harness

`.softhouse/conformance.sh:113-118` says, of an exported `builtin()` function:

> That is one name instead of three, the refusal is fail-CLOSED, and no fail-closed
> refusal can turn a red run green — which is why the trade is taken in this direction.

Both halves fail measurement.

**(i) It is not one name. `[` is a second one, and T97 never enumerated it.** Bash
imports a function under that name and it takes precedence over the builtin
[VERIFIED: T106 — `env 'BASH_FUNC_[%%=() { return 0; }' bash -c 'if [ -z x ]; then
echo SHADOWED; fi'` prints `SHADOWED` on 5.3.9]. The guard uses `[` four times, and it
decides the outcome:

| exported function | guard, healthy bash 5.3.9 | guard, psub-broken bash 5.3.9 |
|---|---|---|
| `[() { return 0; }` | exit 3 REFUSED | exit 3 |
| `[() { return 1; }` | exit 0 | **exit 0 ADMITTED** ← fail-OPEN |

**(ii) The hijacks are not fail-closed; they are whatever the attacker's function body
says.** T97 only ever tried a body printing `hijacked`, which refuses. A body printing
the token admits:

| exported function, `/dev/fd` removed (psub genuinely dead) | decision |
|---|---|
| none (control) | exit 3 REFUSED |
| `builtin() { echo hijacked; }` | exit 3 (T97's row, reproduced) |
| `builtin() { echo conformance-psub-live; }` | **exit 0 ADMITTED** |
| `[() { return 1; }` | **exit 0 ADMITTED** |

[VERIFIED: T106, single container transcript, all rows same shell, same harness bytes.]

**My ruling on the question asked ("is the argument sound? is there a construction that
avoids it entirely?").**

- *No fixed point exists* — that half of T97's argument is **correct, and for a reason
  it did not state**: in bash, function lookup precedes builtin lookup for **every**
  command word, and the only two bypasses (`builtin`, `command`) are themselves command
  words. Any probe built out of commands is shadowable. I could construct no
  command-free way to move a byte through `< <(…)`.
- *The trade is still the right one*: `builtin eval` fixed a genuine, non-adversarial
  false refusal (an exported `eval()` — I reproduced T97's before/after on 5.3.9), and
  it costs nothing.
- *But the defence written down is wrong and must be replaced*, because the honest
  statement is stronger and simpler: **an environment that can export shell functions
  into this harness has already won** — it can equally shadow `find`, `perl`, `grep`,
  `sed` and `go` further down the file, where nothing checks anything. (I demonstrated
  the tail of that: an exported `grep()` breaks `usage()` at line 246; an exported
  `sed()` makes `--help` print the attacker's text and still exit 0.) The guard is not,
  and cannot be, a defence against a hostile environment; it is a defence against a
  **wrong invocation**, and it should say exactly that. F1, by contrast, needs no
  function export at all — which is why F1 is the one that gets code.

Suggested replacement for the claim (docs only, no behaviour change):

> `builtin` pins `eval`/`read`/`printf` to bash's own, which closes a real false
> refusal (an exported `eval()`). It is not a security boundary and cannot be: an
> exported `builtin()` or `[()` function decides this guard in either direction
> [VERIFIED: T106], and the same environment could shadow `find`/`perl`/`grep`/`go`
> further down this file where nothing is checked at all. This guard defends against a
> **wrong invocation**, never against a hostile environment.

### F3 — P3. `--help` can now exit **1**, which is the graded FAIL code

`--help|-h) usage; exit $?` is the right instinct (P-22), but `usage()` returns `1`
when the sentinel is missing, and `1` is this harness's "at least one graded vector
FAILED" code. The adjacent arm already uses the right code for this class:
`--*) warn …; usage; exit "$EXIT_UNUSABLE"`. A broken `--help` is "the harness is
unusable", not a verdict. Recommend `return "$EXIT_UNUSABLE"` in `usage()`
(`EXIT_UNUSABLE` is assigned at line 214, well before any call site — in scope).
Not blocking: zero verdict tokens are printed on that path, and no grading caller
passes `--help`. Same root as T97's own F-T97-3.

### F4 — P3. "admitted **and works**" claims more than anyone has observed

`SKILL.md` and the drop-in text parked for `.softhouse/vectors/README.md` both say
that where `/bin/sh` is a bash 5.x, `sh conformance.sh` is "admitted **and works**".
T97's own *Unverified* section says there has been **no complete graded run under bash
5.x at all**. I improved the evidence but did not close it: with `/bin/sh` relinked to
bash 5.3.9 in a container, `sh conformance.sh` is admitted, `--help` exits 0, and the
graded path proceeds to `no Go toolchain. Expected /repo/.softhouse/bin/go-env.sh` —
i.e. `SCRIPT_DIR` resolved **correctly**, which is more than T97 measured. But the
container has no Go toolchain and no route to the oracle, so "works" end-to-end is
still [UNVERIFIED]. Say "admitted, and the harness starts normally".

### F5 — P3 (rig gap, not a defect in the harness). The 13-assertion rig cannot see F1

Row [5] neuters the probe with `< /dev/null` — the one broken shape where the
inherited variable is irrelevant, because `read` *succeeds* and overwrites it with the
empty string. A rig row that would have caught F1 is four lines; suggested text in the
handoff.

---

## 2. Driven RED myself, both directions (required item 1)

**Post-fix, `bash -r`** — the motivating case, real harness, scratch merge into current
main [VERIFIED: T106]:

```
$ bash -r .softhouse/conformance.sh ; echo exit=$?
.softhouse/conformance.sh: line 136: /dev/null: restricted: cannot redirect output
conformance: WRONG INTERPRETER — this harness requires bash, and the shell that …
conformance:   this IS bash 3.2.57(1)-release, but the process-substitution probe did not
               deliver its token: expected [conformance-psub-live], observed []. … It is the
               latter: this is a RESTRICTED shell ($- = hrB, i.e. 'bash -r'). …
exit=3
$ bash -r .softhouse/conformance.sh 2>&1 | grep -cE 'VERDICT|PASS|FAIL'
0
```

**ZERO verdict tokens**, exit 3. Same on bash 5.3.9 in a container (exit 3, 0 tokens),
and for `bash --posix -r`, `/bin/sh`, `bash --posix`, `dash`, `zsh`, `ksh93`, busybox
`ash` — all exit 3, all 0 tokens.

**Pre-fix, from `main`'s ACTUAL bytes** (not the branch, not a summary): I materialised
`git show main:.softhouse/conformance.sh` inside `.softhouse/` so `SCRIPT_DIR` resolves
the same way, and ran it. `main`'s bytes hash
`225181baeff9a0f5df51646157a7f93174e05859e80df8fd032cb06725a70000` — **identical** to
the immutable commit `ab2de89` T97 pinned, so the pin and today's `main` still name the
same pre-fix file [VERIFIED: T106, `cmp` and `shasum`].

```
$ bash -r .softhouse/T106-prefix-main.sh
… line 79: /dev/null: restricted: cannot redirect output
… line 106: cd: restricted
… line 107: cd: restricted
conformance: no Go toolchain. Expected /.softhouse/bin/go-env.sh to put one on PATH.
conformance: EXIT 2 — the harness is unusable. This is NOT a pass.
exit=2
```

Admitted, then exit **2** — the oracle-outage code — blaming a toolchain at a path
that exists nowhere. The defect is real, it is what T97 says it is, and the change is a
**fix, not a no-op**: same invocation, same host, 2 → 3.

`bash -r`'s own capability, checked because T97 volunteered it against its own interest:
`bash -r -c 'IFS= read -r v < <(printf "%s\n" TOKEN-ARRIVED); printf %s "$v"'` →
`TOKEN-ARRIVED`, rc 0, and `bash -r -c 'cd /tmp'` → `cd: restricted`, rc 1
[VERIFIED: T106]. So claim (h) is true: process substitution works there, the probe is
what cannot run (the `2>/dev/null` on the command substitution is refused at line 136),
and refusing it is still correct because `cd` is refused and `SCRIPT_DIR` comes out
empty — which the pre-fix transcript above demonstrates rather than asserts.

---

## 3. The hunt for a WRONGLY REFUSED interpreter (primary job)

**I found none beyond the one T97 already reports.** Every refusal I could produce was
either true (the shell genuinely cannot deliver the token) or an exported-function
hijack (F2). What I did find is the opposite failure — a wrongly *admitted* one (F1).

**Host, GNU bash 3.2.57 — 26 environments, `--help` exit 0 = admitted:**

`env -i`, `IFS=oc`, `IFS=' '`, `IFS=$'\n'`, `IFS=e`, `SHELLOPTS=nounset`,
`SHELLOPTS=noclobber`, `SHELLOPTS=errexit:nounset`, `BASHOPTS=nullglob`, `bash -u`,
`bash -e`, `bash -C`, `bash -f`, `bash -p`, `--noprofile --norc`, `LC_ALL=C`,
`LC_ALL=en_US.UTF-8`, `LANG/LC_ALL=tr_TR.UTF-8` (the dotless-ı locale, a classic
case-folding trap), `TMPDIR=/nonexistent`, `TMPDIR=` a read-only directory,
`BASH_ENV=/dev/null`, a non-writable CWD, and all three pre-seeded probe variables —
**all ADMITTED**. Only `POSIXLY_CORRECT=1` refused, and that refusal is **true**:
`POSIXLY_CORRECT=1 bash -c 'cat < <(printf …)'` is a **syntax error** on 3.2
[VERIFIED: T106]. `IFS=e` is worth naming: `e` occurs in the token, so without the
`IFS=` prefix in the probe this would have been a false refusal — that prefix earns
its place.

**bash 5.3.9 — 25 environments:** same list, all admitted, including `POSIXLY_CORRECT=1`
(5.x keeps psub in POSIX mode), `argv[0]=sh`, `argv[0]=sh --posix`, `SHELLOPTS=errexit:nounset:pipefail`.
`PATH=/nonexistent` is not a guard decision (`env` cannot find `bash` at all).
`/dev/fd` removed → refused, and **verified not false**: psub is genuinely dead there.

**Exported functions — every name the guard's own code path invokes.** I enumerated
them from the bytes rather than from the handoff: `[` (×4), `builtin`, `eval`, `read`,
`printf` (probe and banner), `case`/`esac`/`if`/`elif`/`fi` (reserved words — **not
shadowable**, checked), `unset`, `exit`, and downstream `cd`, `grep`, `sed`, `head`,
`cut`, `find`, `perl`. Results: `eval`, `read`, `printf`, `test`, `cd`, `exit`, `unset`,
`set` shadows are all harmless to the guard's decision (`builtin` does its job).
`builtin` and `[` decide it — F2. `grep`/`head`/`cut` shadows break `usage()` loudly
(exit 1). No name produced a *false refusal* that `builtin` was not already covering.

---

## 4. Ruling on the residual hijack

See F2. **The argument as written is unsound and must be replaced**; the code choice it
defends is nonetheless correct and should stand. No construction avoids function
shadowing inside a bash probe, for the reason given. The correct framing is that the
guard defends against a wrong *invocation*, not a hostile *environment*.

---

## 5. Is the 13-assertion rig vacuous? No — mutation-tested

`bash …/T97-evidence/prove-interpreter-guard.sh` → **13 passed, 0 failed**, exit 0, on
the scratch merge into current main. Then I broke each assertion's **subject** and
required the row to go red for the right reason (harness/rig restored with
`git checkout --` after every run; working tree verified clean afterwards):

| mutation applied | rows that went red | right reason? |
|---|---|---|
| M-A guard block deleted entirely | 7 red: both `bash -r` rows, dash/zsh, `/bin/sh` + `--posix` capability rows, row [5] | yes |
| M-B token comparison `!=` → `=` | 7 red incl. `/bin/bash: psub capability=yes but guard exit=3` | yes — this is the *false-refusal* detector firing |
| M-C old negative probe restored | 3 red: both `bash -r` rows and row [5] | yes — the rig detects the exact regression |
| M-D `#=END-OF-HELP=` deleted from the harness | 2 red: `sentinel` and `/bin/bash` (its `--help` now exits 1) | yes |
| M-E probe's psub text reworded | 1 red: *"the sed did not change anything — this row is now inert"* | yes — the rig's own anti-vacuity check works |
| M-F header trimmed so the retired `2,34p` coincides again | 1 red: *"drift demo … proves nothing today"* | yes |
| M-G rig's `PREFIX_SHA256` falsified | 1 red: `pre-fix bytes` | yes |
| M-H rig pinned to the **post-fix** commit | 2 red: `pre-fix bytes` and `PRE-FIX bash -r` | yes — P-24 pin cannot silently follow the fix |

Every assertion has a discriminating subject; two rows are themselves guarded against
becoming inert. This rig is **not** in the P-22 family. Its one blind spot is F5.

---

## 6. Exit-code semantics (required item 5)

- Shell side: the only literal exits are `exit "$EXIT_WRONG_INTERPRETER"` (3),
  `exit "$EXIT_UNUSABLE"` (2, six sites), and `exit $?` for `--help`, `--prove`,
  `--self-test`, and the graded path. No new numeric exit was introduced — with the
  caveat that `usage()`'s `return 1` can now surface as an exit 1 on the `--help`
  path (F3).
- Go side: `Summary.ExitCode()` returns **1, 2, 2, 0** and nothing else
  [VERIFIED: `nexus/internal/apps/loanschedule/conformance/grade.go:154-172`];
  `cmd/conformance/main.go` adds only `os.Exit(2)` and `os.Exit(summary.ExitCode())`.
  **3 is genuinely free and unambiguous.** `git diff main...T97 -- nexus/` is empty, so
  none of this could have moved anyway.
- Doctrine preserved in fact, not just in prose: exit 3 emitted **0** `VERDICT|PASS|FAIL`
  tokens on every one of the 12 refusal invocations I ran across three bash versions.

---

## 7. `usage()` (required item 6)

- Sentinel present exactly once, anchored, at line 42; the mention inside `usage()`'s
  own comment does not match [VERIFIED: `grep -c '^#=END-OF-HELP=$'` = 1].
- Deleted → `--help` **errors at exit 1** with `conformance: --help is broken: the
  '#=END-OF-HELP=' sentinel …` instead of printing a wrong span [VERIFIED: rig row [6]
  and my own M-D run].
- `--help` prints the **complete** header: 40 lines, first line the title, last line
  *"PostgreSQL is the only permitted database."*, and it contains both capability
  clarifications (`CAPABILITY test` and `ADMITTED and works`) that the retired `2,34p`
  would have truncated — the drift was real, and the demo is computed live so it
  cannot rot into a tautology.

---

## 8. Adjudication of F-T97-1 (required item 7)

**The driver's position is upheld, on all three points, and I would have ruled the same
way with no prompting.**

1. **Obeying the literal constraint was right.** T97's brief said, under *YOU MUST NOT
   CHANGE*, that `git diff main...HEAD -- .softhouse/vectors/` must be empty. A worker
   that reinterprets an explicit prohibition in its own favour — however sensible the
   reinterpretation — destroys the only cheap scope check this pipeline has
   (`git diff --stat main..<branch>`), and the next worker learns that prohibitions are
   negotiable. T97 obeyed, flagged the conflict, wrote the replacement text, and
   invited the overrule. That is the behaviour P-20 asks for, applied in the direction
   that is *harder* for the author.
2. **The constraint protects vector JSON / `PIN.json` / `capabilities.json`, not README
   prose** — and the precedent is already on the record (T81's prose edits to the same
   file were accepted). The right remedy is the one taken: re-scope, don't retro-license.
3. **The fix belongs to T93, and it is genuinely parked there** — I checked the artefact
   rather than the claim: `.softhouse/tasks.json`, task `T93`, `status: pending`, note
   *"local fire 20260820-230001: SCOPE EXTENDED by F-T97-1 … T93 now owns BOTH the
   36-vs-42 census AND T97's drop-in replacement text"* [VERIFIED]. So this is a
   deferred edit, not a lost one.

**Is the parked text correct as written?** Measured against my own runs, yes with one
exception. Verified true: `dash`, `zsh`, `ksh`, busybox `ash` refused; bash 3.2 in POSIX
mode is what **both** `sh conformance.sh` and `bash --posix conformance.sh` give you on
macOS, and both are refused; `bash -r` "stops the probe running at all" (exactly — the
`2>/dev/null` at line 136 is refused before the probe body runs); `sh conformance.sh`
admitted where `/bin/sh` is bash 5.x. The exception is **F4**: drop "and works" or
downgrade it to "and the harness starts normally", because no graded run under bash 5.x
exists yet. T93 should apply the text **with that word changed**.

---

## 9. Invariants (required item 8) — all verified on the scratch merge into current `main`

| check | result |
|---|---|
| `git diff main...softhouse/T97-guard-positive-probe -- .softhouse/vectors/ nexus/` | **empty** |
| `contract.go` byte-identical to `main` | sha256 `0db73d4a…f139` both sides |
| `gofmt -l .` | names **exactly** `internal/apps/loanschedule/contract/contract.go` (G-3, expected) |
| `go build ./...` / `go vet ./...` | exit 0 / exit 0 |
| `go test ./... -count=1` | ok `loanschedule` 7.6s, ok `…/conformance` 7.6s, exit 0 |
| `bash .softhouse/conformance.sh` | **VERDICT: PASS, exit 0, 42 parity vectors, 5576 graded cells, 0 invariant violations, 0 assertions NOT RUN** |
| `bash .softhouse/conformance.sh --prove` | PROOFS: 21 passed, 0 failed |
| `sh .softhouse/conformance.sh` | exit **3**, **0** verdict tokens |
| T97's own rig | 13 passed, 0 failed |

Diff scope: 4 files, 806 insertions / 28 deletions — `conformance.sh`,
`softhouse-uat/SKILL.md`, the new evidence script, the handoff. Nothing outside them.
No money path, no vector, no schema, no Go. Grep for the project's known-bad patterns
over the diff: no float, no `first_name`/`last_name`, no MySQL/MariaDB/Oracle-Database
token, no hard-coded offset or rail threshold. The only "oracle" in the diff is the
Fineract reference implementation, correctly named.

---

## 10. The `softhouse-uat/SKILL.md` edit (required item 9)

Accurate, and the specific sentence I was told to test is **true**: I relinked
`/bin/sh → /bin/bash` (5.3.9) inside a throwaway container and ran `sh conformance.sh`
— **admitted**, `--help` exit 0, graded path advancing to the toolchain check with a
correctly resolved `SCRIPT_DIR` [VERIFIED: T106]. The earlier over-generalisation
("`sh`, `dash`, `zsh` and `bash --posix` are refused") was indeed false on any distro
that links `sh` to bash, and replacing a shell-name rule with a capability rule is the
right correction. The old text's other content (exit-3-is-not-an-outage, never park a
task on it) survives intact. Only F4's "and works" overreaches.

---

## Verdict

**MICRO-FIX** — required before merge:

1. **F1**, one line: `_conformance_psub_line=` as the first statement inside the eval.
   Mechanical, no number, no money logic. Proven to close the forge and proven not to
   introduce a false refusal.
2. **F2**, comment only: replace the "one name instead of three / fail-CLOSED" defence
   with the accurate statement, and stop asserting the probe cannot be fooled.
   (`[` is a second hijackable name; hijacks admit as readily as they refuse.)

Recommended, not blocking: F3 (`usage()` → `EXIT_UNUSABLE`), F4 (drop "and works",
here and in the text T93 will apply), F5 (a 14th rig row for the forge).

Everything else in T97 stands up: the defect is real and reproduced from `main`'s own
bytes, the fix moves exactly two rows of the interpreter matrix, the rig is honest,
the exit-code contract is intact, `usage()` is genuinely self-locating, the doc
correction is true, and the corpus is untouched with conformance still PASS at 42
vectors / 5576 cells.
