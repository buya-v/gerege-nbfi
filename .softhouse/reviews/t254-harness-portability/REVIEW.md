# T254 — INDEPENDENT REVIEW of T253 (harness host portability)

**VERDICT: MICRO-FIX.** The two assigned defects are really fixed, the fix is sound on both
implementations, and no parity claim is made anywhere. Three corrections must be applied before
merge; none of them is in the shipped code.

Reviewed branch `softhouse/T253-harness-portability` @ **`d7a7ea3`**.
Fork point **MEASURED, not assumed** (P-71): `git merge-base main softhouse/T253-harness-portability`
= **`a6bec723fd0769d5c5b6349a375756d1104a7c73`**, which is what T253's handoff claims. My branch
`softhouse/T254-review-portability` forked at `d7a7ea3`.
**`main` is at `d9f04df` and has moved 20 commits since T253's fork** — that fact produces two of
the three corrections below.

Every number here was measured by me on Linux (`bash 5.2.21`, GNU coreutils 9.4, `/bin/sh`→dash),
stamped with its commit. Reference oracle (Fineract) **UNREACHABLE** from this host; the harness's
own probe reads `probe = down`. **No parity verdict is available and none is claimed.** "The
oracle" is the Fineract reference implementation; **Oracle Database** is prohibited and appears
nowhere in this work.

---

## ANSWER TO THE QUESTION THAT MATTERS FIRST — IS THE MAC AT RISK?

**NO. On evidence stronger than T253's, and stronger than a man page.**

T253 could not execute the BSD arm and said so honestly, substituting a re-enacted *getopt parse*
built from two transcribed optstrings. That substitution was reasonable but it is not the program.
**I replaced it with the program.** `curl` reached `raw.githubusercontent.com` from this host
(T253's POSIX fetch had failed at 196 bytes, and it appears not to have retried a different
source), so I fetched **Apple's `shell_cmds/mktemp/mktemp.c`** — the exact source of
`/usr/bin/mktemp` on Buyan's Mac — **compiled it here and ran it.** Both C files are committed at
`evidence/`, the driver is `evidence/bsd-mktemp-proof.sh`, its transcript
`evidence/bsd-mktemp-proof.txt`: **12 OK / 0 FAIL.**

Three things settle it:

1. **The new form is accepted by the real BSD program.** `mktemp "$DIR/name.XXXXXXXXXX"` and its
   `-d` twin both succeed on the compiled Apple binary and on GNU 9.4. Traced through
   `mktemp.c`: with no `-t` and no `-p`, `tflag` stays 0, `argc` after `optind` is 1, so the
   implied-`-t` branch at `:127` is not taken, `name = strdup(argv[0])` at `:184`, then
   `mkstemp`/`mkdtemp`. **No option letter precedes the argument, so neither parser can read it
   as anything but a template.**
2. **The chosen template is byte-for-byte the one BSD mktemp builds for itself.** `mktemp.c:166,168`
   construct `"%s/%s.XXXXXXXXXX"` — **ten X's** — and hand it to the same `mkstemp`. Ten X's
   through Darwin's `mkstemp` is what `mktemp -t` has always done on that Mac. This is what
   closes the one gap my method leaves (I linked against glibc, not Darwin libc): if a ten-X
   template failed on Darwin, the OLD form would never have worked there either.
3. **The `__APPLE__` differences cannot be reached by the new form.** Every `#ifdef __APPLE__`
   block in that file (`confstr(_CS_DARWIN_USER_TEMP_DIR)`, `:94-98` and `:147-155`) sits inside
   `case 'p'` or inside `if (tflag)`. The new form passes neither `-t` nor `-p`. The Mac-specific
   code is on the path T253 **removed**, not the path it installed.

**Residual risk carried onto the Mac: none that I can name for D1.** One behavioural delta worth
recording rather than fearing: on a Mac session with `TMPDIR` unset (a launchd/cron context), the
old `-t` form would still have found the per-user Darwin temp dir via `confstr`, whereas
`conf_tmpdir()` falls back to `/tmp`. Scratch files move directory; `mkstemp` still creates them
0600. Not a failure, and not a money path.

**D2 is also safe on the Mac, and I drove it rather than reasoned it** (my first probe was broken
— a pipe subshelled the `source` and every `GOROOT` read `<unset>`; **P-72, the probe not the
code** — so this is the corrected drive, calibrated on a positive and a negative that
discriminate 15 stderr lines vs 0):

| drive | result |
|---|---|
| **A** main checkout, toolchain present — *Buyan's normal case* | `GOROOT=<main>/.softhouse/toolchain/go`, `pinned:…`, **0 substitution lines** |
| **B** isolated worktree, toolchain only in main — *the load-bearing case* | resolves to the **main** checkout, `pinned:…`, **0 substitution lines** |
| **C** NEGATIVE CONTROL: dir exists, `go/bin/go` not executable | falls back loudly, **GOROOT not exported**, 15 notice lines |
| **D** `CWD=/`, absolute path (launchd shape) | resolves from the script's own path, `pinned:…` |
| **E** `GEREGE_GO_STRICT=1`, toolchain absent | `refused:strict`, exports nothing |

On a host where the pinned toolchain is present — which is the *definition* of Buyan's Mac, since
that is where it was installed — **the derived value is identical to the old hardcoded one and the
script is silent.** The Mac's behaviour is unchanged.

*Stated, not glossed:* `zsh` is **ABSENT** on this host, so go-env.sh's `${(%):-%x}` arm is the one
thing in D2 I could not execute. It cannot affect the harness, which sources the file from **bash**
(`conformance.sh:656`, `BASH_VERSION` set, zsh branch never taken); it could only matter to a human
sourcing it from an interactive macOS zsh, where `_ge_dir`'s `$PWD/.softhouse/bin` fallback (`:89`)
and `_ge_here=$PWD` (`:94`) both still resolve from a checkout.

---

## THE CHECKS

### 1. Every `mktemp` site — enumerated, and the SELECTOR checked too (P-76 addendum)

**CONFIRMED, and the claim is exactly true as worded.** Enumerated with `python3 re`, never `grep`
(P-75).

* At **`main`**: `\bmktemp\b` matches **10** lines in `conformance.sh`, **all ten carry `-t`**, all
  ten with a zero-X argument. There was no eleventh site and no site that was already portable.
* At **`d7a7ea3`**: **0** non-comment lines match `\bmktemp\b` except the two helper definitions
  (`:619`, `:620`). `mktemp -t` survives on exactly **two lines, 573 and 585, both comments**
  explaining the defect. T253 said "*code* sites: 0" and that is precise: the comment mentions are
  documentation of the removed form, they are not executed, and keeping them is right — they are
  the reason the next author will not reintroduce it.
* All **10 call sites** are converted (`:1490-1493, 1839, 1863, 1938, 1953, 2011, 2012`), matching
  T253's table line-for-line. The two byte-identical lines (`1938`, `2011`) are both present and
  both converted — the hazard it flagged was real and it handled it.

**The selector, widened past the file T253 was asked about:**

* `check-ledger-invariants.sh:72` — the only other script the harness executes — uses bare
  `mktemp -d`, portable on both. `.softhouse/capture/lib/*` (the two guards run at `:1009`/`:1042`)
  contain no `mktemp`. **No script on the harness execution path still carries `mktemp -t`.**
* **Repo-wide, however:** 5,181 tracked files at `d7a7ea3` hold **50** `mktemp … -t` lines. Setting
  aside T253's own red driver (which must contain them), its transcripts, `tasks.json`, the handoff
  and the two comments, **19 live lines remain in 15 tracked capture instruments, every one with a
  zero-X argument, every one fatal on GNU** — `t46-negative-vacuity.sh:40`, `t108-grep` ×4,
  `t154-nofloat` ×5, `t243-wiring` ×2, `t248-failopen-widen/instruments/30-additivity.sh` ×5,
  `t74…/run-precondition-block.sh:38`, `tierA-a2/red-green-a2-15.sh:27`. Full list in
  §F-5. This is outside T253's write scope and outside its claim, but it is the same defect in
  the evidence corpus and nobody has named it.

### 2. The BSD arm — see the section above. Evidence, not assertion.

T253's substitution was **sound but weaker than it needed to be**, and one detail shows why
transcription is not sourcing: its GNU optstring `"dqut"` **is not the real one**. Measured from
coreutils source: **`"dp:qtuV"`**; installed GNU 9.4's own `--help` shows `-p DIR`. The
load-bearing fact — `t` carries **no** colon on GNU and **does** on BSD (`"dp:qt:u"`,
`mktemp.c:84`) — is correct, and no conclusion of T253's moves. But the model was reconstructed
from a printed synopsis when the source was one `curl` away.

### 3. The harness, re-run by me — and the third defect confirmed by a STRICTER experiment

`bash .softhouse/conformance.sh` at `d7a7ea3` (never `sh`; I confirmed `sh` still exits **3**):

* **`ledger-invariants` runs and reports `PASS`** — it did not compile at `a6bec72`. D2 works.
* **The fail-open guard runs**: `inspected 904 tracked .sh/.py file(s) … frontier 10, pinned at 10`.
  It could not run at all at `a6bec72`. D1 works.
* Then it **refuses**, on one row: `+TIER1 / -TIER2` for
  `t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh`. **EXIT 2. Probe line NOT
  printed.** Reproduced T253's §3.1 exactly.

**The third defect is real. I proved it more tightly than T253 did.** T253 reproduced the Mac's
state by *running the whole instrument*. I changed **one bit of host state and nothing else** —
`touch /tmp/t234_matrix2.txt`, a zero-byte file outside the repo — and re-ran:

```
frontier == pinned (all 10 rows, by path).
reference oracle (https://…/actuator/health) probe = down
```

**The probe line APPEARS**, `probe = down`, exit 2. Removing the file restores the refusal. The
mechanism is confirmed by reading, not inferred: `02-escape-matrix-fix.sh:6` is
`C=/tmp/t234_matrix2.txt` and `:7` redirects into `"$C"`; the linter's ownership test is
`re.search(RE_OWNED_HEAD + re.escape(p), txt)` (`50-failopen-lint.py:276`), which demands the
**literal** path after `>`/`rm`/`mkdir`/`touch`/`tee`/`mktemp` — the redirect goes through the
variable, so the literal never appears in an owned position — and deadness is `os.path.exists(p)`
at `:275`, **evaluated on the linting host**. Tier is a property of the machine, not the file.

**T253's decision to leave a correctly-functioning guard refusing rather than move the pin or
weaken it is CORRECT, and I would reject the alternatives it rejected.** TIER2 is the true
classification; pinning TIER1 would write a host artefact into the durable record and break the
Mac instead; comparing paths while ignoring tiers would destroy the TIER1/TIER2 distinction T248
built. An agent optimising for a green bar had an easy, invisible route here and did not take it.
**That is the strongest single piece of evidence in the branch that D2's fallback is not a
rationalisation** (see §4).

**No verdict is claimed anywhere.** I read T253's handoff for this specifically: §4.3 is labelled
`THIS IS A DIAGNOSTIC, NOT THE BAR, AND NOT A VERDICT`, the opening block says `NO PARITY VERDICT
IS CLAIMED, AND NONE IS AVAILABLE`, and §6 repeats it. **Clean on the rule that matters most.**

### 4. The D2 absent-toolchain decision — sound, but the audit trail it rests on is thinner than stated

**The decision is right.** Fall back loudly rather than refuse; keep the refusal reachable behind
`GEREGE_GO_STRICT=1`; export nothing when there is no toolchain. Exporting a nonexistent `GOROOT`
was the whole defect, and neither no-toolchain arm does it (verified, drives C and E).

**Is P-77 applied soundly, or is it a rationalisation for making its own run possible?** Sound —
but **narrower than its own wording**. The two guards it points at (`check-ledger-invariants.sh`,
`conformance.sh:load_toolchain`) close **"there is no compiler."** They say nothing about **"there
is a *different* compiler."** Substitution is a *new* state neither guard covers, so the
second-source-of-truth argument does not actually transfer to it; what covers it is the printing.
Not a rationalisation, on two pieces of evidence: T253 had a far cheaper route to a green run
(set `GEREGE_TOOLCHAIN`) and did not take it, and it **left its own BAR red at §4** rather than
touch a pin it could have moved unnoticed.

**But the printing is where the claim overreaches, and this is my one code-adjacent finding.**
Measured at `d7a7ea3`:

* the substitution notice appears **32 times on stderr and 0 times on stdout**;
* `GEREGE_GO_SOURCE` — exported "so any consumer can report it mechanically" — has **zero
  consumers** in 5,181 tracked files outside `go-env.sh` itself and T253's own red driver.
  `conformance.sh` never reads it, and the verdict block never names the toolchain.

So "*a substitution that is printed is auditable evidence in the BAR*" holds only for a capturer
who writes `2>&1`. T253's own transcript does (32 hits), and `softhouse-uat/SKILL.md:23` documents
a bare terminal invocation where a human sees both streams. But a BAR captured the ordinary way —
`bash .softhouse/conformance.sh > bar.txt` — **contains no trace of which Go built the binary.**
The dangerous shape T253 names in its own rationale (a green parity BAR produced by an unpinned
toolchain with nobody noticing) is closed on stderr and open on stdout. **Prophylactic today** —
the only host that captures vectors has the pinned toolchain — and cheap to close. See F-3.

### 5. Vector-store digest — read live, three ways

```
git rev-parse HEAD:.softhouse/vectors   -> 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
git rev-parse main:.softhouse/vectors   -> 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
git rev-parse a6bec72:.softhouse/vectors-> 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
```

**UNMOVED**, and unmoved across the 20 commits `main` gained since the fork. Claim confirmed.

### 6. The self-reported frontier regression — repaired, by path, with no amnesty

T253 squashed to a single commit, so the offending first commit is not on the branch; what is
reviewable is the end state, and the end state is correct. At `d7a7ea3`:

* `FAILOPEN_PIN_FILE_LIST` (`conformance.sh:1471`) holds **10 rows**; **`30-proposed-linter-fix.py`
  is not among them**, and **T253 did not touch the pin** (absent from the three-dot diff).
* Measured frontier: **10 rows**, and the harness prints `frontier == pinned (all 10 rows, by
  path)` once the host-state confound of §3 is removed.
* **No amnesty.** The file is still in the corpus and still inspected; its two suppressions are
  reported at `:211` and `:230` under `### SUPPRESSIONS IN FORCE (every one is listed; they never
  go quiet)`, each carrying a reason. The `# lint-failopen: ok -- <reason>` marker is the
  **linter's own pre-existing mechanism** — present at `main:…/50-failopen-lint.py:196,200`
  (`RE_SUPPRESS`), not invented by T253 to excuse itself.
* The linter is **byte-identical** at `a6bec72` and `d7a7ea3`:
  `472f8112c73193c81fbf185983c33c7dc6b826890eaecd50ab922901c177b104`. T253's `30-…-fix.py` applies
  nothing; I ran it (**5/5 PASS**) and re-hashed after: unchanged.

**I applied the same discipline to myself.** My own review files were **`git add`-ed before** I
measured the frontier — the precise reason T253's first check was stale — and re-measured against
**both** linters: fork-linter frontier **10**, main-linter frontier **11** (main's pin also has 11,
including T252's new `TIER1B` row), **zero `t254-harness-portability` rows on either.** Corpus
904 → 905.

### 7. The three deferrals — all three real, one of them badly counted, one of them stale

**(a) The variable-indirect ownership blind spot — REAL, and correctly scoped out of T253's write
scope.** Verified by reading the rule and by execution. **But the deferral target no longer
exists**: see F-2.

**(b) The same shape one file over, and the opposite host-dependence — BOTH REAL.**
`01-escape-matrix.sh:7` carries the identical `C=/tmp/t234_matrix.txt` idiom (read at `:6-7`), and
the fork linter names it: `01-escape-matrix.sh :7 dead absolute path: /tmp/t234_matrix.txt`. It is
TIER3, off-frontier, so it moves no pin today — correctly scoped.
`12-sweep-census.py:74,76` are host-dependent in the **other** direction, confirmed verbatim:
both regexes match `/Users/buv/gerege-nbfi/.claude/worktrees/…` and the result is fed to
`os.path.isdir` — dead here, live on the Mac. T253's generalisation ("C1's `os.path.exists()`
makes tier assignment a property of the LINTING HOST") is the right level to fix at.

**(c) The Mac-hardcoded `go-env.sh` population — REAL, and the count is wrong by ~5×.** See F-1.

---

## CORRECTIONS THE DRIVER MUST APPLY

### F-1 — MEDIUM. The residual population is **40 files / 29 instruments**, not "six other tracked files"

T253 §5.4 names six instruments plus `reference-oracle.md:616`. **All seven are real** — I checked
every one verbatim at its stated line and each is a literal
`. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`. **The population is not.** Counted myself
(P-67, both terms), regex `/Users/[^/]+/…go-env\.sh` over `git ls-files`:

| | `d7a7ea3` (T253) | `d9f04df` (main) |
|---|---|---|
| tracked files carrying the literal | **40** | **40** |
| of those, executable `.sh`/`.py` instruments | **29** | **30** |
| denominator: tracked files | 5,181 | 5,216 |

The broader term — **any** `/Users/buv/` literal — is **716 files / 2,855 lines / 189 executable
instruments**. T253's list is a *sample presented as a count*; it is the only materially wrong
number in the document.

**The driver already caught this independently** — `main` carries `8a5db63 Driver re-counts T253's
residual: 30 instruments hardcode the Mac toolchain, not six`, and **my independent count at main
is exactly 30.** So the correction is only to the handoff text, which still says six.

*Correction:* amend T253's §5.4 to "40 tracked files, of which 29 are executable instruments (30 at
`main`)", and let the existing driver commit stand as the authority.

### F-2 — MEDIUM. **`T252` has already landed and did NOT fix the linter.** The deferral is stale

T253 routes the §4.4 fix to T252 three times ("T252 owns landing this", "the RESUME assigns the
fail-open follow-ups to T252"). **True at the fork, stale against `main`** — P-71 in its
sharpest form:

* `main` contains `2674f7c merge T252-failopen-counts` and `63555c1 T252: the third site is real…`,
  which **is** the only commit since `a6bec72` to touch `50-failopen-lint.py`.
* The linter grew 476 → **722 lines**; sha `472f8112…` → `99ebea35…`.
* **I ran main's post-T252 linter over this tree: it still classifies
  `02-escape-matrix-fix.sh` as TIER1 on a clean host.** The blind spot is untouched.

So merging T253 leaves the harness **still refusing at the fail-open guard on any host without
`/tmp/t234_matrix2.txt`**, with no task owning the fix. (T253's change remains a strict improvement
— two guards that could not run now run, and `ledger-invariants` reports PASS — but the probe stays
unreachable on a clean Linux host.)

*Correction:* **file a new task** for the variable-indirect ownership fix, seeded with
`.softhouse/capture/t253-portability/src/30-proposed-linter-fix.py`, and **re-verify that patch
against main's 722-line linter, not the 476-line one it was proved against.** Its 5/5 PASS is a
result about a file that no longer exists on `main`. Do not merge on the belief that T252 has this.

### F-3 — MICRO. State the toolchain on **stdout**, in the verdict block

`GEREGE_GO_SOURCE` is exported and read by nobody; the substitution notice is stderr-only. Add one
line to `conformance.sh`'s summary block, beside the vector-store digest, on **stdout**:

```
conformance: toolchain  ${GEREGE_GO_SOURCE:-unknown}
```

Then a BAR captured with `>` carries its own toolchain provenance, `GEREGE_GO_SOURCE` acquires the
consumer it was built for, and T253's stated rationale becomes true as written. **This is a
`conformance.sh` edit and therefore serialises** with the other `conformance.sh` holders
(`T226`, `T235`, `T250`). It is prophylactic, not urgent: on the only host that captures vectors
the toolchain is pinned and the notice never fires.

### F-5 — LOW, no action required at merge. 19 more `mktemp -t` sites, same defect, unnamed

Not T253's scope and not contradicted by anything it claimed, but the population is now measured
and should be recorded rather than rediscovered. All zero-X, all fatal on GNU:

```
capture/mathcontext/src/t46-negative-vacuity.sh:40
capture/t108-grep/{capture-env.sh:73, probe-conformance-guards.sh:27,
                   replicate-t91-g4.sh:27, run-matrix.sh:97}
capture/t154-nofloat/{drive-leg1-e2e.sh:29, drive-leg1.sh:31, drive-leg2.sh:31,
                      drive-leg3.sh:36, regen-leg1-red.sh:12}
capture/t243-wiring/instruments/{10-wrongimpl-red-drive.sh:39, 30-citation-red-drive.sh:52}
capture/t248-failopen-widen/instruments/30-additivity.sh:26,37,38,39,40
capture/t74-multiplesof/T82-guard-proofs/run-precondition-block.sh:38
capture/tierA-a2/red-green-a2-15.sh:27
```

`conf_mktemp`'s shape is the drop-in fix. **These overlap the F-1 population** — `t154 drive-leg2`,
`drive-leg3` and `t243`'s drivers appear in both — so "cannot re-run off Buyan's Mac" is one
finding with two mechanisms, and a task that fixes only one mechanism will not make those files
runnable.

---

## What I reproduced of T253's own numbers

| claim | reproduced |
|---|---|
| D1 red/green **14 OK / 0 FAIL** | **14 / 0**, exit 0 |
| D2 red/green **24 OK / 0 FAIL** | **24 / 0**, exit 0 |
| proposed linter fix **5/5**, applies nothing | **5/5**, sha `472f8112…` unchanged after |
| `ledger-invariants` PASS, fail-open guard reaches a frontier | both, verbatim |
| frontier 10 == pinned 10, corpus 904 | both |
| vector store `13b8342e…` UNMOVED | confirmed at HEAD, `main`, and the fork |
| no verdict claimed | confirmed by reading the whole handoff |

**Not one of T253's reproducible numbers was wrong.** Its defects are a stale deferral it could not
have known about, an undercounted population, and a claim about where its own output is printed.

## Hygiene

`git status --porcelain` checked before finishing and after every instrument I ran by hand. The
fail-open linter's tracked JSON sidecar (`t238-failopen/evidence/lint.json` — the file T253 caught
itself dirtying) was **diverted via `FAILOPEN_LINT_JSON` on every one of my nine linter runs** and
was never written. `/tmp/t234_matrix2.txt`, created for the §3 discrimination probe, was
**removed**, restoring clean-host state so the next agent sees the defect rather than my artefact.
Nothing outside `.softhouse/reviews/t254-harness-portability/` and my handoff was written.
`conformance.sh`, `go-env.sh`, `capture/t253-portability/`, `vectors/`, `nexus/`, `docs/adr/`,
`gates.md`, `program.json`, `tasks.json`: **untouched.**
