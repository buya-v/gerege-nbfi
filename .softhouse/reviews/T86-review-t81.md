# T86 — independent review of T81 (`softhouse/T81-conformance-shell-guard`)

Run `2026-08-17-run1-harness-schedule-poc` · reviewer branch `softhouse/T86-review-t81`
· executed 2026-08-20 on the local Mac fire, isolated worktree
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-aaf7c13d1ce9e87f4` (forked from `main` @ `c148617`).
Reference oracle **UP** before and after; no container was restarted, rebuilt, brought down or re-seeded.

Every transcript cited is committed under `.softhouse/reviews/T86-transcripts/`.

---

## VERDICT: **APPROVED**

The guard does what it claims, exactly where it claims, and I could not make it
turn a red run green or swallow a verdict. I ran the harness eleven times across
six interpreters, forced a genuine red and reverted it, measured the report's
nondeterminism myself, and verified the one claim T81 could not verify.

**What would have made me reject:** if `bash .softhouse/conformance.sh` on T81's
branch had produced anything other than the byte-identical `VERDICT: PASS (exit 0)
— 42 parity vectors … 5576 cells` that main produces, or if the guard had appeared
anywhere on the exit-1 path over a deliberately broken vector store. Neither
happened; both were measured, not read.

Six findings follow. **None is a merge blocker.** Finding 1 is a real residual hole
in the guard and should become its own task; findings 2–3 are accuracy defects in
prose; 4–6 are cosmetic or bookkeeping.

---

## 1. Exit-code integrity — VERIFIED, no renumbering

| claim | how I checked | result |
|---|---|---|
| every `exit` on main is `0`, `$?` or `$EXIT_UNUSABLE` | `grep -nE '\bexit\b'` over main's `conformance.sh` — 15 hits, all `0` / `$?` / `"$EXIT_UNUSABLE"`; `EXIT_UNUSABLE=2` at line 47 | **confirmed** |
| no literal `exit 3` on main | `grep -rnE '(exit|Exit)[( ]"?3"?\b'` over main's script → none | **confirmed** |
| the Go binary emits only 0/1/2 | read `grade.go:154-172` — returns `1`, `2`, `2`, `0` and nothing else; `grep -n 'os.Exit'` over `…/conformance/cmd/conformance/main.go` → four `os.Exit(2)` plus `os.Exit(summary.ExitCode())` | **confirmed** |
| the shell propagates only that | `main_grade` does `return "$rc"` where `rc` is the binary's status; dispatch is `exit $?` / `exit 0` / `exit "$EXIT_UNUSABLE"` | **confirmed** |
| 0/1/2 keep their exact meanings | ran all three on T81's branch: PASS exit 0 (E5), FAIL exit 1 over a perturbed vector (E5), `UNUSABLE (exit 2) … the reference oracle is UNREACHABLE` with `CONFORMANCE_ORACLE_HEALTH_URL` aimed at a closed port, 0 guard traces | **confirmed** |
| 3 vs the shell's reserved codes | 126 / 127 / 128+n / 255 are untouched; 3 is inside the 3–125 application range | **confirmed** — but see **finding 3** |

The three-dot diff renumbers nothing. The only new exit is the guard's own.

## 2. Guard placement — VERIFIED from source

`grep -n -v -E '^\s*(#|$)'` over T81's file: **the first executable line in the file
is line 68, `EXIT_WRONG_INTERPRETER=3`**. Lines 1–67 are the shebang and comments.
The guard occupies 68–103; `set -u -o pipefail` is 104, `SCRIPT_DIR=` is 106, the
store root 108, the Go toolchain load and the `curl` oracle probe are hundreds of
lines further down inside `main_grade`. The two surviving `done < <(find "$STORE_ROOT" …)`
process substitutions are at 188 and 206.

So the guard runs **before** any shell option, any path resolution, any vector read,
any toolchain lookup, any oracle contact, and any line that prints a verdict. Its only
outcomes are `exit 3` or fall-through; it contains no `exit 0`, no `return`, and its
only residue is `EXIT_WRONG_INTERPRETER` left set (harmless — grepped, used nowhere
else) and `unset conformance_shell_why`.

## 3. THE CENTRAL PROPERTY — reproduced independently (E5)

I made my own red rather than trusting T81's. Same vector, same shape:
`P-03-disbursement-on-repayment-due-date.json`, `interest_minor` `"12"→"13"` **and**
`interest_major_text` `"0.12"→"0.13"` moved together so the transcription cross-check
is not what catches it.

- `bash` + **main's** script over the perturbed store → **exit 1**, `VERDICT: FAIL (exit 1) — 1 mismatched vector(s), 0 invariant violation(s).`
- `bash` + **T81's** script over the same store → **exit 1**, same VERDICT line, `5576 graded` unchanged, and `grep -cE 'WRONG INTERPRETER|EXIT 3|conformance_shell'` → **0**. The guard is nowhere on the failure path.
- `sh` + T81's script over the **same red store** → **exit 3**, and `grep -cE 'VERDICT|PASS|FAIL'` → **0**. It prints no verdict of any kind, so it cannot be misread as the PASS the corpus does not deserve.
- Perturbation reverted; the vectors path shows no modification in `git status --short`.
- The three-dot diff over `nexus/` is **empty**; over `.softhouse/vectors/**/*.json` and `.softhouse/vectors/*.json` it is **empty**; `PIN.json` and `capabilities.json` untouched. The only change under `.softhouse/vectors/` is `README.md`, +33 lines, prose.

## 4. Both ways, byte-for-byte (E1, E5)

Both scripts were run **from the same worktree path** so `SCRIPT_DIR`/`REPO_ROOT`/`STORE_ROOT`
resolve identically (I swapped the file in place and restored it from the index afterwards).

```
bash + main's script  -> exit 0  sha256 3b7c96fd…d630a0ce  19790 bytes
bash + T81's script   -> exit 0  sha256 3b7c96fd…d630a0ce  19790 bytes   diff: EMPTY
VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle, 5576 cells compared.
    parity vectors   PASS 42   FAIL 0
    cells compared   5576 graded, 84 ungraded (never recorded by the capture)
```

**Byte-identical with no normalisation at all**, which is a stronger result than T81
reported. `sh` → exit 3 with the new message, no `line 104`, no `syntax error`, and it
never reaches the process substitution. `--prove` → `PROOFS: 21 passed, 0 failed`, exit 0.
`--help` → exit 0 and now ends exactly at the header block instead of trailing raw shell.

## 5. Can the guard fire spuriously? — attacked, one residual found

**False refusal (a legitimate interpreter the guard rejects): none found, and I closed
T81's own open question.** T81 marked "a bash ≥ 5.1 in POSIX mode is not rejected" as
`[UNVERIFIED]` because the machine has only bash 3.2. I verified it in throwaway
containers built from images already present locally (`--network none`; the shared
fineract containers were not touched):

- `postgres:18.3` → **GNU bash 5.2.37**: the guard **ADMITS** under `--posix`, under `argv[0]=sh`, and plain — and real `< <(…)` genuinely works in all three.
- `eclipse-temurin:21-jdk` → **GNU bash 5.3.9**: same, **and `bash --posix -n` over T81's whole conformance.sh exits 0**, i.e. POSIX-mode bash 5.3 parses the entire harness.

So the capability test is the right test: the shells it refuses genuinely cannot run
the file, and the modern bash it must not refuse, it does not refuse. T81's
`[UNVERIFIED]` can be upgraded to `[VERIFIED: T86, bash 5.2.37 and 5.3.9 in containers]`.

**False admission: one, `bash -r`.** See finding 1. Also, a non-bash shell with
`BASH_VERSION` deliberately exported: `BASH_VERSION=9.9-fake dash` still fires (dash
cannot eval the construct), but `BASH_VERSION=9.9-fake ksh` is **admitted** — ksh93 has
its own process substitution — and ksh then dies on `BASH_SOURCE`. Contrived (nothing
exports `BASH_VERSION`), recorded for completeness only. Unexported, `ksh` is refused
correctly.

## 6. The two adjudications the brief demanded

### (a) T81 says the driver's brief was WRONG. **T81 IS RIGHT. Say so plainly.**

Measured on the actual binaries on this machine:

```
/bin/sh --version    -> GNU bash, version 3.2.57(1)-release (arm64-apple-darwin25)
ls -l /bin/sh        -> 101232 bytes, a SEPARATE BINARY, not a symlink to /bin/bash (1293840)
/bin/sh   psub.sh    -> BASH_VERSION=3.2.57(1)-release  THEN  syntax error near unexpected token `<'   exit 2
bash --posix psub.sh -> BASH_VERSION=3.2.57(1)-release  THEN  syntax error near unexpected token `<'   exit 2
/bin/bash psub.sh    -> GOT:hello  exit 0
```

The brief's constraint 4 — that bash-invoked-as-`sh` and `bash --posix` are legitimate
runs the guard must not trip — is **false on this machine**. Both are bash by every name
test and both die at the first `< <(…)`. On main they die at line 104 with **exit 2**,
the oracle-unusable code. There is nothing to "let through": refusing them with exit 3
and "re-run under bash" converts a run that was already failing under the wrong code with
a message about a shell token into one that fails under its own code naming the cause and
the fix. **A worker that re-derived its instruction, found it wrong, and reported the
refutation instead of complying is the control working**, and it is the second time in
two fires (cf. T47, T76) that this has caught the driver. Record it as such.

I also reproduced the zsh pathology that is the strongest argument for the whole task:
main under `zsh` prints **the harness's own** `conformance: EXIT 2 — the harness is unusable.
This is NOT a pass.` over a completely fabricated `no Go toolchain` diagnosis, because
`BASH_SOURCE` is unset and `SCRIPT_DIR` resolved to a directory that does not exist.

### (b) The report is not byte-reproducible on main. **REAL — reproduced.**

`report.go:99-104` ranges `s.CounterfactualCoverage`, typed `map[string][]string` at
`grade.go:115`, with no sort. I built the binary once and ran it 30 times:

```
  27  schedule.core,monthend.reanchor
   3  monthend.reanchor,schedule.core
```

(T81 measured 23/30 vs 7/30 on its own 30 runs — same phenomenon, different draw.) I hit
it live: my two exit-1 runs differed by exactly one line's position and nothing else.

**Is T81's sorted normalisation honest?** Yes, and it is corroborative rather than
load-bearing:

1. The map has exactly **two** keys, so only two orderings exist and both lines are
   diagnostics — the SUMMARY block, the cell counts and the VERDICT line are in fixed
   positions and never move.
2. My unsorted diff of the divergent pair showed a **pure transposition** (line deleted
   at 73, the identical line re-added at 74), and `sort` vs `sort` was empty — identical
   multisets, not a hidden value change.
3. Independently of any normalisation, my **green** pair was byte-identical with equal
   sha256 and equal byte count, so the byte-identity claim stands unnormalised.
4. The three-dot diff over `nexus/` is empty, so the graded numbers cannot have moved by
   construction.

The one honest criticism of whole-file `sort` is that it would also mask a *genuine*
reordering of graded rows. It does not do so here (points 1–4), but a future reviewer
should not adopt whole-file sort as a general normalisation. Fixing `report.go` is
already registered as **T90**; this is not T81's to carry and is not grounds to reject it.

## 7. The out-of-`files_hint` edits the driver already accepted

Not re-litigated. Reviewed for correctness:

- **`.claude/skills/softhouse-program/SKILL.md`** — the new never-halt row is placed
  immediately after the **Oracle unreachable** row, which is the exact row a false 2
  would have triggered, and it says `**NOT an oracle outage — do not park anything.** …
  Only exit **2** is the oracle-is-down stop condition.` That is **accurate and it does
  tell the driver never to park on exit 3.** It adds no fourth stop condition, so it does
  not contradict CLAUDE.md's "stop conditions are exactly three".
- **`.claude/skills/softhouse-uat/SKILL.md`** — line 26's `Exit 0 = PASS, 1 = FAIL, 2 =
  could not run` correctly gains 3, and the invocation becomes `bash .softhouse/conformance.sh`.
  Line 49's surviving "if the oracle is down, `conformance` reports exit 2, not a false
  PASS" remains true and does not contradict the new text. The `2 = could not run` gloss
  is unchanged, so exit 2 is not redefined. See **finding 2** for the one over-generalisation.
- **`.softhouse/vectors/README.md`** — I confirmed the hunk is **+33 lines and 0 deletions,
  entirely prose and one markdown table**; the 4-row exit table's rows for 0/1/2 restate
  the existing semantics verbatim and add no new claim. Every vector JSON, `PIN.json` and
  `capabilities.json` is byte-untouched (§3 above). T81's F-2 is discharged.
- **`.softhouse/reference-oracle.md`** — +6 lines, correct: "only exit 2 means this".
- **`.softhouse/conformance.sh` header** — the code-3 paragraph and the rewritten
  "0, 1 and 2 are the verdict codes" paragraph are accurate, and unlike the two doc sites
  the header correctly qualifies the claim with "on bash 3.2 (macOS)".

I did **not** run `gofmt -w` on anything. `guard_gofmt` is untouched by the diff and its
`contract.go` exemption (gate G-3) is intact; the harness ran green through it.

---

## Findings

**1 — [P2, follow-up] The capability probe cannot distinguish "process substitution works"
from "the probe never ran", and `bash -r` slips through into a fabricated exit 2.**
[VERIFIED: E6.] `bash -r .softhouse/conformance.sh` → the guard **ADMITS**, and the run
then dies with `conformance: no Go toolchain. Expected /.softhouse/bin/go-env.sh …` and
**exit 2** — the exact defect class T81 was dispatched to close. Mechanism: line 77's
`>/dev/null` redirection is refused by the restricted shell, so `( eval … )` never
executes, yet the compound's status is 0 and `! 0` is false. The probe is a *negative*
test ("no error occurred"), so any environment that prevents the probe from running reads
as success — restricted bash today, a missing or unwritable `/dev/null` in a broken
chroot tomorrow.
*Not a regression* (main behaves identically), *not reachable* by any invocation in this
repo, and it **cannot turn red green** — it lands on an exit-2 failure, never a verdict.
A positive-evidence probe closes it; I measured a working form across nine interpreters
in E6. I am deliberately **not** prescribing it as a micro-fix: my own first draft of that
one line falsely refused plain bash (`printf %s ok` has no trailing newline, so
`while read` never runs its body), which is precisely why a change to the gatekeeper of
the grading harness deserves its own task and its own review.

**2 — [P3] Two doc sites over-generalise "`sh` is refused" into a universal claim.**
[VERIFIED: bash 5.2.37 / 5.3.9 containers, E1.] `softhouse-uat/SKILL.md` ("`sh`, `dash`,
`zsh` and `bash --posix` are refused up front with exit 3") and `vectors/README.md`
("`sh conformance.sh`, `bash --posix conformance.sh`, `dash` and `zsh` are all refused up
front with **exit 3**") state without qualification something that is true only where
`/bin/sh` is bash 3.2 or dash. On Fedora/RHEL, where `/bin/sh` **is** bash 5.x,
`sh conformance.sh` is **admitted** and works. `conformance.sh`'s own header gets this
right ("on bash 3.2 (macOS)"); the two doc sites should borrow that qualifier. The error
is in the harmless direction — it predicts a refusal that does not happen, never a safety
that does not exist.

**3 — [P3] The collision analysis is complete for POSIX conventions but missed one real
second owner of 3: ksh93 uses exit status 3 for a script syntax error.**
[VERIFIED: `/bin/ksh -c 'foo('` → exit 3; ksh over main's `conformance.sh` → exit 3 with
`syntax error at line 203`.] T81's handoff says "3 has no such second owner". It has one.
**This is harmless and arguably fortunate** — an unguarded ksh run and a guarded ksh run
both yield 3, and both mean "wrong interpreter", so the semantics coincide rather than
conflict. Worth correcting in the record because the *reasoning* was stated as exhaustive
and is not.

**4 — [P4, follow-up] `usage()`'s `sed -n '2,34p'` is still a hard-coded line bound.**
T81 re-anchored it accurately (line 34 is indeed the last header line — verified, and
`--help` now ends exactly there with exit 0), and fixed the pre-existing bug where
`2,30p` against a 24-line block trailed raw shell. But the *next* header edit will drift
it again, in either direction: truncating the exit-code table, or leaking shell into
`--help`. A block-anchored form (stop at the first non-`#` line) removes the class. Same
"frozen fact about today's tree" pattern as T81's own F-3.

**5 — [P4] Cosmetic overcount.** The handoff says main's `--help` trailed "six lines of
raw shell" and lists five (`set -u -o pipefail`, `SCRIPT_DIR`, `REPO_ROOT`, `STORE_ROOT`,
`NEXUS_DIR`). It is 5 shell lines plus 1 blank = 6 lines of output. Immaterial; noted only
because the honesty rule makes counts load-bearing.

**6 — [P4, orchestrator bookkeeping] T81's F-5 pointer is stale.** The standing workaround
sentence is at **`.softhouse/RESUME.md:42`**, not `:111` as the handoff says — the dispatch
commit rewrote the file after T81 read it. T81's substantive claim holds and I re-checked
it: **no script in the repo invokes the harness with `sh`**; the one executing call site,
`.softhouse/capture/t64-zeroprincipal/src/run-harness-mutations.sh:83`, uses `bash`, and
`.softhouse/handoff/T8-run-conformance.sh:8` executes it via its shebang. The orchestrator
should retire the RESUME.md sentence on merge, as T81 asked.

---

## What I ran, so silence is distinguishable from not looking

Eleven full harness runs (7 × `bash` green, 2 × `bash` red over a perturbed store, 1 ×
`--prove`, 1 × oracle-down), six refusal runs (`sh`, `bash --posix`, `dash`, `zsh`, `ksh`,
`bash -r`), 2 × `--help`, 30 direct runs of one built binary for the order probe, 9
interpreter probes for the hardened-guard candidate, and 5 container runs across bash
5.2.37 / 5.3.9. Source read, not summarised: `conformance.sh` on both sides in full,
`grade.go:110-172`, `report.go:88-110`, `cmd/conformance/main.go` exit sites,
`softhouse-program/SKILL.md` STEP 4, `softhouse-uat/SKILL.md`.

## Non-collision — the shared reference oracle

Read-only. No `docker compose` command; no restart, rebuild, `down` or re-seed of the
shared instance. The only contact with it was the harness's own `curl -sk` health probe.
Two throwaway `docker run --rm --network none` containers were created from images already
present locally (`postgres:18.3`, `eclipse-temurin:21-jdk`) purely to obtain a bash ≥ 5.1;
they touched nothing shared.

| | `fineract-fineract-1` | `fineract-db-1` |
|---|---|---|
| **before** | `Up 2 days (healthy)` | `Up 3 days (healthy)` |
| **after** | `Up 2 days (healthy)` | `Up 3 days (healthy)` |

`fineract-db-1` is `postgres:18.3` — **PostgreSQL, the only permitted database.** No Oracle
Database, MySQL or MariaDB anywhere in this task; "the oracle" throughout means the
**Fineract reference implementation**. Health after all runs:
`{"status":"UP","groups":["liveness","readiness"]}`.
