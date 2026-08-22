# T253b — the BAR harness could only ever run on one host

**Branch:** `softhouse/T253b-harness-portability-mac`
**Commits:** `273d6eb` (the two fixes + red drives + Mac BAR), `3350785` (two inherited claims verified), plus the peer comparison commit below.
**Base:** `a71c140` (fire `20260822-060013` dispatch record).
**Host:** `Darwin 25.5.0 arm64`, macOS 26.5. Reference oracle (Fineract) REACHABLE.
**Vector store:** `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d` — UNMOVED, verified live with `git rev-parse HEAD:.softhouse/vectors` before and after.

---

## 1. The verdict, probe-line PRESENCE stated first

`bash .softhouse/conformance.sh` on this Mac, after the change. **Re-measured at the finished tree with every file of mine TRACKED** (P-69) — definitive log `evidence/80-BAR-mac-final.txt`; the earlier `evidence/40-BAR-mac-after.txt` was taken before the last instruments existed and agrees on every figure.

This re-measurement was not optional. The fail-open linter's corpus is `git ls-files`, so an untracked instrument is invisible to it — which is precisely how the cloud fire shipped a new frontier row and had to self-correct. Checked while untracked is *true when measured and stale when it matters*. With everything staged, the frontier is still **11 == 11** and none of my files is on it.

- **Probe line PRESENT** — line 92, tested for presence before value (P-83).
- Its value: `reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`.
- **VERDICT: PASS (exit 0)** — 46 parity vectors, 7884 cells compared.
- Fail-open frontier **11 == pinned 11**, all rows matched by path.
- All **9** exemption-census pins matched.
- `go-env.sh` printed **nothing** — the happy path is silent, so no BAR log byte moved on account of D2.

Identical to the driver's `c0e88c6` baseline on every figure. **No pin was moved and no guard was relaxed.** The diff to `conformance.sh` is exactly ten lines changed in place and nothing else; `FAILOPEN_PIN_FILE_LIST` is untouched.

This is the arm that matters most: this Mac is the only host that can capture vectors, and a fix that repaired Linux and broke it would be a high rejection.

---

## 2. D1 — `mktemp -t`, both terms counted

**Population: 10. Fixed: 10.** Enumerated with `python3 re` over the whole file (never a bare `grep`, never `rg` — P-75), at **my own commit**, not inherited from the brief:

| line | was |
|---|---|
| 1481, 1482, 1483, 1484 | inside `guard_no_fail_open_instruments` |
| 1831 | `gate_wrong_ledger_impls_die` |
| 1855 | same gate |
| 1930, 1945 | `main_grade` |
| 2003, 2004 | `prove` (2004 is the only `-d`) |

Every one of the ten `mktemp` sites in the file carried the `-t` form; the residual set is **empty**, and `20-apply-d1.py` **refuses to write** if population != rewritten, so "fixed only the one that fired" cannot pass silently.

The brief's line numbers (1438…1960, measured at `2b1e2e7`) had all moved. Re-measured, the population is the same size and the same sites.

**The irony, stated as instructed:** the first site reached on Linux is inside the fail-open guard. The guard that could not run is the fail-open detector.

**The fix:** `mktemp -t NAME` → `mktemp "${TMPDIR:-/tmp}/NAME.XXXXXXXXXX"`.

### Which arm is evidence and which is argument

**Both arms are EVIDENCE. Neither is argument.** That is better than the brief expected, and it is worth saying why:

- **BSD arm — executed natively.** This host's `/usr/bin/mktemp`, macOS 26.5.
- **GNU arm — executed, not argued.** No GNU coreutils is installed on this Mac (checked `gmktemp`, `/opt/homebrew/opt/coreutils/libexec/gnubin/mktemp`, `/usr/local/opt/coreutils/libexec/gnubin/mktemp`, `/opt/homebrew/bin/gmktemp`, `/usr/local/bin/gmktemp`, and `brew` itself — all absent; P-66, that is where I looked). But the Docker daemon is up and `postgres:16` is a local Debian bookworm image carrying **GNU coreutils 9.7**, so the GNU arm ran on a real GNU binary on real Linux.

Measured matrix (`evidence/10-mktemp-matrix.txt`):

| form | BSD | GNU |
|---|---|---|
| `mktemp -t NAME` | rc=0 — **this is why the defect is invisible here** | rc=1 `too few X's in template 'conformance-failopen'` — the Linux kill |
| `mktemp -d -t NAME` | rc=0 | rc=1, same |
| `mktemp "$TMPDIR/NAME.XXXXXXXXXX"` | rc=0 | rc=0 |
| `mktemp -d "$TMPDIR/NAME.XXXXXXXXXX"` | rc=0 | rc=0 |

TMPDIR honoured on the new form both set (`/var/tmp/...`) and unset (`/tmp/...`).

**Both man pages were read on this machine, not paraphrased.** BSD `man mktemp` (macOS 26.5, OpenBSD-derived) gives `mktemp /tmp/${tempfoo}.XXXXXX` as its own worked example. GNU's man page is **not** on this Mac; its `--help` was read out of the container and states verbatim: *"TEMPLATE must contain at least 3 consecutive 'X's in last component"* and marks `-t` **[deprecated]**. So the chosen form is the one both documents specify, not merely the one that works here.

One cosmetic consequence, measured not assumed: macOS sets `TMPDIR` with a trailing slash, so paths contain `//`. Verified to produce a real regular file; a non-leading `//` is not special in POSIX. See §6 — the peer branch strips it and that is tidier.

---

## 3. D2 — the derived toolchain, and the ENGINEERING decision

`.softhouse/bin/go-env.sh` hardcoded `GEREGE_TOOLCHAIN=/Users/buv/gerege-nbfi/.softhouse/toolchain` and exported a `GOROOT` under it unconditionally. Off this Mac that is a directory that does not exist, and the symptom surfaced far from the cause as `ledger-invariants: the guard DID NOT COMPILE … EXIT 2 — NOT a pass`.

**The guard's refusal was correct, is fail-closed, and is untouched.** The defect was the silence here.

Now: explicit `GEREGE_TOOLCHAIN` override → the **main checkout** via `git rev-parse --git-common-dir` → this checkout, each validated by `-x` on an actual `<cand>/go/bin/go`. A `GOROOT` that does not exist is never exported.

The worktree hop is load-bearing and **tested from inside a real worktree** (this one): `--git-common-dir` → `/Users/buv/gerege-nbfi/.git` → the shared toolchain, while this worktree has none of its own.

### The decision (ENGINEERING, `chosen_by: agent`, not escalated)

**CHOSEN — ANNOUNCED FALLBACK.** If the pinned toolchain is absent and a `go` is on PATH, use it and print an unmissable stderr banner naming the binary, its version, the paths searched, and the fact that it is not the pinned toolchain. `GEREGE_GO_SOURCE` = `pinned` | `fallback-path` | `absent`.

**REJECTED — HARD REFUSAL.** Two reasons, the second decisive:
1. It preserves the exact symptom this task exists to remove: on every non-Mac host the ledger-invariants guard still cannot run, while a serviceable `go` may be on PATH.
2. **It would not prevent the substitution, only the announcement of it.** Both consumers — `conformance.sh:load_toolchain` and `guards/check-ledger-invariants.sh:build_guard` — source this file and then run their own `command -v go`. With nothing exported they would find and use the PATH `go` anyway, and nobody would have said so. Refusing buys silence, not safety.

**Sub-decision — this file always returns 0.** It is sourced, so it must not `exit` and must not mutate the caller's shell options. This is the one file where the standing `set -euo pipefail` rule is deliberately **not** applied, and the reason is on the record in the file. Returning non-zero is also unsafe: a caller under `set -e` would abort at the `. go-env.sh` line, which is D1's failure mode (dying before the probe) by another route. Scenario S6 tests exactly that.

**Nothing here can make a guard pass.** Worst case: a guard compiles with an unpinned Go and then refuses on its own merits.

---

## 4. Red drives — a fix I have not seen fail is unverified

**D1** (`evidence/10-mktemp-matrix.txt`): old form green on BSD / **red on GNU**, new form green on both. The RED is a real GNU binary refusing, not a simulation.

**D2** (`evidence/30-d2-red-drive.txt`), six scenarios, all assertions held:

| | |
|---|---|
| S1 pinned present | exports the real GOROOT, **prints nothing** |
| S2 from this worktree | resolves the MAIN checkout, worktree has no toolchain of its own |
| S3 pinned absent + go | **OLD reproduces the defect**: hardcoded GOROOT, zero diagnostics. NEW: no GOROOT, announcement names binary + version + disclaimer |
| S4 pinned absent, no go | loud, exports nothing, caller's refusal stays fail-closed (calibrated: `/usr/bin:/bin` really has no `go`) |
| S5 inherited bogus GOROOT | dropped, and the drop announced |
| S6 sourced under `set -euo pipefail` | caller survives |

**Two of my own instruments were wrong first and the assertions caught them** — recorded rather than edited out, because the mis-selector is the interesting part (P-76 addendum):
- a command-prefix assignment (`TMPDIR=x cmd "${TMPDIR}"`) does not feed that command's own word expansion, so my TMPDIR check measured the inherited value and reported a false failure of the new form;
- S4/S6 first ran with a `PATH` containing no `bash`, so `env` died rc=127 and four assertions failed against a scenario that never happened. Now calibrated before it is trusted.

---

## 5. LINE-DELTA REPORT FOR T255 — read this one

**`.softhouse/conformance.sh`: 10 insertions, 10 deletions, NET ZERO. No line number in the file moves.**

Every edit is line-for-line in place at 1481, 1482, 1483, 1484, 1831, 1855, 1930, 1945, 2003, 2004. Nothing was inserted, nothing removed, no function added. The file is 2617 lines before and after. `20-apply-d1.py` refuses to write if the line count changes.

**T255's DEC-2 revision 8 citations into `conformance.sh`, above and below my sites, are unaffected and need no re-derivation** — provided the driver takes *this* implementation. See §6: the peer implementation inserts 52 lines at ~line 570 and shifts everything below it.

`.softhouse/bin/go-env.sh`: 17 lines → 190 (a rewrite; no other file cites its line numbers).

---

## 6. PEER COMPARISON — an independent T253 exists

The driver disclosed mid-task that the cloud branch survived after all: `origin/softhouse/T253-harness-portability` @ `d7a7ea3`. **I finished and committed my own fix before reading a byte of theirs** (`273d6eb` predates the fetch). What follows is measured, not read — `instruments/70-cross-impl-compare.sh` runs both implementations against the same scenarios; their branch is never checked out or modified.

### Where we independently agree — corroboration nobody paid for

- **The same ten sites.** Same set, found independently. Neither found an eleventh.
- The same replacement shape: drop `-t`, one positional template, ten X's.
- The same D2 resolution order: override → `--git-common-dir` → own checkout, validated on an **executable** `go/bin/go` rather than a directory.
- **The same ENGINEERING decision** — announced fallback over hard refusal — reached separately, with the same core reason (the fail-closed property already lives in the guards).
- Both refused to move the pin or weaken a guard.

### Where we differ

**(a) Line delta — decisive for THIS fire.** Theirs adds `conf_tmpdir` / `conf_mktemp` / `conf_mktemp_d` helpers, +52 lines at ~570, and rewrites the sites as calls: **+72/−21 on `conformance.sh`**, shifting every line below 570 by ~52. Mine is net zero.
*On the merits their helper is the better long-run design* — DRY, one place to change. But T255 is landing DEC-2 revision 8 citations into this same file in this same fire. **If the driver takes theirs, T255's line citations must be re-derived; if it takes mine, they must not.**

**(b) Trailing slash — theirs better.** They strip `TMPDIR`'s trailing slash; I leave the `//` and proved it harmless. Cosmetic, and theirs is tidier.

**(c) The BSD arm — mine better, and it is the arm they could not reach.** They state plainly they had no BSD host and did **not** claim BSD as executed, substituting an executed `getopt` optstring parse. I executed it natively. Conversely they executed GNU natively on a real Linux host and give the deeper mechanism (the optstring difference: BSD's `-t` *consumes* the next word, GNU's `-t` is an argument-less deprecated flag). **Between the two fires both arms are now executed and the mechanism is explained.**

**(d) `GEREGE_GO_STRICT=1` — THEIRS BETTER, and I would adopt it.** Their opt-in hard refusal makes the *rejected* alternative reachable as configuration rather than as a patch. Mine has no such switch. Their `GEREGE_GO_SOURCE` is also richer (`pinned:<path>`, `substituted:<path>`, `refused:strict`, `absent:no-go-on-path`) versus my bare tokens.

**(e) A stale inherited `GOROOT` — MINE better, and this one is a live defect in theirs.** Measured, not asserted (`evidence/70-cross-impl-compare.txt`). Scenario: pinned toolchain absent, a working `go` on PATH, and the shell already carrying a stale `GOROOT` — *which is the state of any shell that sourced the OLD `go-env.sh` once*, i.e. exactly a host mid-migration.

| | final `GOROOT` | does `go` work? |
|---|---|---|
| T253b (mine) | `<unset>` — dropped, and the drop announced | **YES** |
| `d7a7ea3` | `/nonexistent/stale/goroot` — left in place | **NO** — `go: cannot find GOROOT directory` |

Theirs exports no `GOROOT` but does not clear an inherited one, so it announces a fallback to a `go` that then cannot run — failing with the very error its own header comment describes. Their diagnostic does surface the error text, so it is loud rather than silent, but the substitution it announces does not work. Conditional on an inherited `GOROOT`, but that condition is the normal one during a migration.

**(f) Frontier base.** Theirs reports `frontier 10 == pinned 10` at corpus 904 — its base predates T252's eleventh row. Current main and my branch are at **11 == 11**. Their branch needs that reconciliation before it can merge; mine does not.

**(g) They went further on the third defect.** They proved a two-line linter fix against a copy and applied it nowhere. I did not propose a fix; I measured the residue-dependence and added the frontier-invariance fact below.

**Recommendation, on the merits and not on seniority:** take **mine** for `conformance.sh` (net-zero delta protects T255 in this fire) and take **their `GEREGE_GO_STRICT`** and trailing-slash strip into `go-env.sh`, keeping my inherited-`GOROOT` drop. The two are complementary; neither is a superset.

---

## 7. Two inherited claims I checked rather than inherited

**The t234 `/tmp` residue claim is REAL — I reproduced it on this Mac** (`evidence/50-t234-residue-probe.txt`). `02-escape-matrix-fix.sh` line 6 names `/tmp/t234_matrix2.txt` and line 7 creates it. Moving the residue aside and re-linting flips it **TIER2 → TIER1**. A fail-open *classification* that depends on filesystem residue.

**One thing the cloud did not state, and it changes the urgency:** the frontier **count is 11 in both arms** and the row **set is identical by path**. The harness pins by path, not by tier (`frontier == pinned (all 11 rows, by path)`), so this **does not move the frontier and does not fail the BAR on either host**. It is a defect in the recorded classification, not in the pin. Out of my `files_hint`; reported, not fixed.

**The residual count — and it RECONCILES EXACTLY with the driver's 30 once the selectors are aligned.** (`evidence/60-hardcoded-toolchain-census.txt`.)

I measured two different literals, because "hardcodes the Mac toolchain" is ambiguous between them and the number depends entirely on which you mean:

| selector (tracked `*.sh`/`*.py`) | runnable | prose |
|---|---|---|
| `/Users/buv/gerege-nbfi/.softhouse/toolchain` (the toolchain dir) | 29 on `main` | 23 |
| `/Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh` (the activation path) | **29** | 7 |

`*.zsh`/`*.bash` searched separately for both, matched nothing (`git grep` rc=1 — a measured negative, not an error; P-80).

The driver's commit `8a5db63` says "30 … (29 besides go-env.sh)" under the **activation-path** selector. **My 29 is exactly that 29.** The reason mine does not say 30 is that my `go-env.sh` no longer contains the literal at all — its usage comment is now generic — so the file that used to be the 30th has removed itself from its own population. The two independent measurements agree precisely; only the denominator's membership changed, and it changed because of this task.

So the corrected statement is: **the "30" is right, "six" was the undercount, and this task takes it to 29** — all of which are `reviews/`-heavy (`T155-probe` ×14, `T184-evidence` ×8) and out of my scope. The driver has filed them as **T256**.

The driver also names a sharper one that is not an instrument at all: `reference-oracle.md:616` states the activation line as an absolute Mac path — prescriptive text in the pin file. I did not touch it; it is T256's.

**A correction to my own instrument, left visible.** The census first asserted "go-env.sh is NO LONGER among them". Its own selector contradicted that and the selector was right: the Mac path still occurs in go-env.sh's *explanatory comment* and in the red-drive that *reproduces the old file deliberately*. Neither is a live hardcode — but a text search cannot tell the difference and mine should not have claimed it could.

---

## 8. My own instruments, checked before anything else (P-80)

The fail-open linter's corpus is `git ls-files`, so my instruments enter it the moment they are tracked — the trap that caught the cloud fire. Run after staging: **frontier 11, pinned 11, none of my files on it**. No `|| true`, no `|| echo`, no bare `grep`, no `rg` in anything I committed; `set -euo pipefail` in every standalone script; `mktemp` in my own instruments uses the portable form; traps cover `QUIT`. `go-env.sh` is the one deliberate exception to `set -euo pipefail` and says why in the file. No `# lint-failopen: ok` hatch was used anywhere.

## 9. What I could not verify

- **No Linux end-to-end run.** I fixed the Linux failure but cannot observe the repaired Linux BAR: the oracle is bound to this host. I proved the *cause* is gone on a real GNU binary; I did not watch `conformance.sh` reach the probe line on Linux. **The cloud fire did observe that** (their transcript reports the fail-open guard running for the first time on that host, 901 files, and `ledger-invariants` compiling). Between the two fires the claim is covered; from mine alone it is not.
- Sites 1831–2004 are latent on GNU by the same mechanism as 1481; only 1481 was ever *observed* to fire, because it kills the run first. Their portability is argued from the shared mechanism plus the executed matrix, not from ten separate observed deaths.
- `GEREGE_GO_STRICT` is theirs, not mine — I did not implement or test it.
