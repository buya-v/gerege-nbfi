# T155 — independent review of T154 (the no-float guards)

**Reviewer branch:** `softhouse/T155-review-t154` · **subject:** `softhouse/T154-nofloat-guards` (tip `e6ebf52`, fork point `187e972`)

## VERDICT: **MICRO-FIX**

Every guard T154 shipped was driven **RED by T155's own poison, written before reading a single
T154 fixture**, and **GREEN** after. Every count T154 quoted reproduced. Three self-corrections
T154 made against its own first draft (F-1, M-5, "21 files is 22") are each independently
confirmed. Its four provers re-run clean against a scratch merge into current `main`.

Two defects are nonetheless open, both in the *positive-assertion* half of the work rather than
the detection half, and both closable in five lines each. Neither is a wrong number, neither is a
regression against `main`, and neither is grounds to reject work that did what its brief asked.

| | |
|---|---|
| guards I could not drive red | **none** |
| T154 claims I tested | **11** — all reproduced |
| defects found | **2 material (D-1, D-2), 1 inherited hazard (D-3), 3 advisory (D-4..D-6)** |
| micro-fixes specified, driven red **and** green | 2 — **not applied by me**, see §7 |
| conformance on the merged tree | `VERDICT: PASS (exit 0) — 43 parity vectors … 5664 cells`, probe line **present**, reading **up** |

---

## 0. Apparatus, stated before any result (P-33, P-24)

- **PRE bytes are read from an immutable blob, never a copy.** `git show 187e972:.softhouse/conformance.sh`,
  sha `11d3729e…98853`, asserted at the top of every prover; the prover **refuses on mismatch** so it
  cannot drift into testing the fixed code. POST sha `a55d7f52…d27a7`.
- **`main` moved twice under me** — `82a9544` → `9e42bbc` → `843f650`. My first scratch merge was built
  against `9e42bbc` and was one commit stale by the time I finished. I rebuilt it against `843f650` and
  re-ran the control rather than arguing the difference away. The graded surface
  (`.softhouse/vectors`, `nexus/`, `.softhouse/conformance.sh`) is **byte-identical between the two
  merge trees** [VERIFIED: `git diff --name-only 0f0b0f9 5f3a711 -- …` empty]; only `tasks.json` and a
  driver note differ, and the harness reads neither. Control re-run on the fresh merge:
  **43 / 5664, exit 0, probe = up** — unchanged [VERIFIED: `out/…/POST2-clean`].
- **`grep` inside a script is `/usr/bin/grep`, BSD grep 2.6.0-FreeBSD; `LANG=C.UTF-8`, `LC_ALL` empty.**
  Measured, not assumed. This is what the guards get; the Bash tool's `grep` is a shell function
  re-execing ugrep and is **not** what these guards see, so every probe runs via `bash script.sh`.
- Scratch merge built with `git merge-tree --write-tree` + `git commit-tree` — nothing checked out,
  no branch moved.
- **No count is hard-coded anywhere in my provers.** Every arm measures its own baseline.

**One apparatus defect of my own, caught by cross-check and recorded rather than buried.** My first
conformance run reported `24 .go files` from the shell guard and `22 Go files` from the Go census on
the *same tree*. The cause is D-3 below: I had invoked a scratch tree's `conformance.sh` by absolute
path from a different working directory, and the Go binary resolves its repo root from **the caller's
CWD**. The run was grading my worktree's store while the shell guards printed the scratch tree's
paths. Fixed by `cd`-ing into the tree under test; every number in this review is post-fix.

---

## 1. (i) The invalid-byte bypass — **closed at both call sites** [VERIFIED]

My own corpus, byte **outside** any JSON string literal (the guard's `perl` stage deletes string
literals first, so a byte hidden inside one is deleted with it and proves nothing) and on the **same
line, before** the float. Pipelines lifted from the pinned blobs by anchored `awk`.

| fixture | PRE | POST | |
|---|---|---|---|
| clean float | FIRES | FIRES | positive control |
| **0xE2 before the float** | **SILENT** | **FIRES** | **the bypass** |
| 0xE2 **after** the float | FIRES | FIRES | BSD grep survives a byte to the right |
| clean integers | SILENT | SILENT | negative control |
| **0xE2 before an exponent `1e3`** | **SILENT** | **FIRES** | the bypass, exponent form |
| clean `float64` (Go) | FIRES | FIRES | positive control |
| **0xE2 before `float64` (Go)** | **SILENT** | **FIRES** | **the bypass, second call site** |
| clean `int64` (Go) | SILENT | SILENT | negative control |

**A correction to my own expectation, not to T154.** I predicted a **NUL** byte would blind the guard
too. It does not — PRE **FIRES** on NUL. The blindness is specific to an invalid *multi-byte*
sequence in a UTF-8 locale, not to "binary-looking" input generally. T154 never claimed otherwise;
I record it because a later worker reaching for NUL as a probe would get a false negative.

**The sweep.** All grep invocation sites in `conformance.sh` carry **both** `LC_ALL=C` and `-a`;
sites lacking either: **zero** [VERIFIED]. No `egrep`/`fgrep`/`zgrep` spelling anywhere. Exactly one
unhardened grep remains in `.softhouse/bin` — `fire-program.sh:224` — precisely as T154 disclosed,
and I confirmed its direction is **fail-closed**: a blind `grep -v` fails to match, the line is
*kept*, `DIRTY` is non-empty and the rescue path runs. The blind grep can only cause a spurious
DIRTY, never a skipped rescue [VERIFIED]. `--help` still exits 0 with no raw shell and no sentinel
leak; the committed sweeper is **idempotent** (re-running it hardens 0 sites).

## 2. (ii) Float and imaginary LITERALS — **caught on the path `conformance.sh` actually executes** [VERIFIED]

Three probe sources of mine, each declaring **zero** forbidden identifiers, injected into the
loanschedule tree; the question asked is not "does `go test` fail" but "does `bash conformance.sh`
go non-zero", because `conformance.sh` never runs `go test` (P-45).

| probe | PRE `conformance.sh` | POST `conformance.sh` |
|---|---|---|
| `r := 0.036` (`token.FLOAT`) | **exit 0 — `VERDICT: PASS`** | **exit 2**, names `t155_probe.go:6:7: floating-point literal "0.036"` |
| `z := 3i` (`token.IMAG`) | **exit 0 — `VERDICT: PASS`** | **exit 2**, names `"3i"` |
| `r := 0x1p-2` (hex float) | **exit 0 — `VERDICT: PASS`** | **exit 2**, names `"0x1p-2"` |

The third is mine, not T154's, and it is the sharpest of the three: a hexadecimal float literal
contains **neither a `.` followed by a digit nor an `e`/`E` exponent**, so the shell guard's byte
regex could never see it even if it were looking for literals. Only the token-stream census catches
it. T154's design choice — token stream over byte grep — is load-bearing, and now demonstrably so.

Every POST arm printed the probe line reading `up` before exiting 2, so these are guard refusals and
not oracle outages [VERIFIED — I test for the line's **presence** first, then its value].

## 3. (iii) The census — **all five refused, separately, each naming its own file** [VERIFIED]

Design choice that makes this an honest test: wherever possible my fixture contains **no float at
all**. `conformance.sh` runs `run_guards` *before* the binary, so a refusal on a float-carrying
fixture could be the shell guard's and would say nothing about the census.

| attack | PRE | POST | who refused, in the harness's own words |
|---|---|---|---|
| symlinked **extra** context, float inside | **exit 0 · 42 · 5576** | exit 2 | `STORE FILE CENSUS … "evilctx" is a SYMLINK` |
| symlinked **whole** context | exit 2 · 0 · 21 (**loud**) | exit 2 | `… "loanschedule" is a SYMLINK` |
| nested subdir, **clean** vector | **exit 0 · 42 · 5576** | exit 2 | `… "loanschedule/sub" is a directory INSIDE a context directory` |
| `T155-UPPER.JSON`, **clean** vector | **exit 0 · 42 · 5576** | exit 2 | `… DID NOT LOAD` |
| case-only `case_id` (`P-00`/`p-00`) | **exit 0 · 43 · 5623** | exit 2 | `CASE_ID INTEGRITY — … differing only in letter case` |
| NFC + NFD spellings of one id | **exit 0 · 44 · 5670** | exit 2 | `CASE_ID INTEGRITY — … must match [A-Za-z0-9._-]+` |
| store-root `.json`, **no float** | **exit 0 · 42 · 5576** | exit 2 | `… sits at the STORE ROOT` |
| store-root `.json`, float behind 0xE2 | **exit 0 · 42 · 5576** | exit 2 | shell guard (float now visible) |
| store-root `.json`, plain float | exit 2 | exit 2 | shell guard, **even pre-fix — not the hole** |

**T154's `43/5623` and `44/5670` reproduce to the digit.**

**The silent float, reproduced from immutable bytes.** The pre-fix run with a float planted at the
store root behind one 0xE2 is **byte-identical to the clean run** — `diff` reports no difference at
all [VERIFIED: `diff out/iii-PRE-control.txt out/iii-PRE-C8.txt` empty]. `VERDICT: PASS (exit 0) —
42 parity vectors … 5576 cells`, no diagnostic anywhere.

**Structural closure of M-5, with the shell out of the circuit.** Running the harness **binary**
directly, no shell guards involved:

| fixture | PRE binary | POST binary |
|---|---|---|
| store-root `.json`, no float | **exit 0** | **exit 2** — `STORE FILE CENSUS … STORE ROOT` |
| store-root `.json`, float behind 0xE2 | **exit 0** | **exit 2** — same |
| store-root `.json`, plain float | **exit 0** | **exit 2** — same |

**Anti-vacuity, the row that matters most.** A second copy of a vector carrying a *different*
`case_id` — a legitimate shape — still **PASSES at 44 parity vectors, exit 0**. The census does not
refuse everything. Six further attacks of mine (malformed vector, hard link inside a context dir,
hard link at the root, hidden dot-context, plant under `-context=` filter, directory named
`*.json`) are all refused, each for its own stated reason. The `-context=` row confirms T123's rule
holds: **the filter narrows what is graded, never what is checked**.

**T154's F-1 correction is right, and the brief was wrong.** A symlinked *whole* context exits 2
loudly (`0 · 21`) because the corpus collapses. The genuinely **silent** variant is a symlinked
*extra* context, which grades `42 / 5576` with a float in it. Confirmed both ways.

**T154's M-5 correction is right.** "The shell guard is the only float check for store-root JSON" is
true only **off** the allowlist. Driven, not argued: injecting a plain float into `PIN.json` or
`capabilities.json` takes the **pre-fix** binary to exit 2 with `store pin: FLOAT TOKEN "3.6"` /
`capability registry: FLOAT TOKEN "3.6"` [VERIFIED: `LoadPin` at `admit.go:53-59`,
`LoadCapabilityRegistry` at `capability.go:105-111`, both calling `RejectFloatTokens` at the fork
point already].

## 4. (iv) Zero files inspected — **an ERROR in both guards, and in the Go census** [VERIFIED]

Guard *functions* lifted whole from the pinned blobs by anchored `awk` (never a `sed` range — a
`sed` range will not close on the line that opened it, which is how T154's own first extractor
silently turned every row into a null control).

| input | PRE | POST |
|---|---|---|
| both trees hold a float | refuses / refuses | refuses / refuses |
| both trees clean | passes / passes | passes / passes |
| **both trees empty** | **passes / passes** | **refuses / refuses** |
| store empty only | passes / passes | **refuses** / passes |
| Go tree empty only | passes / passes | passes / **refuses** |

POST wording: *"INSPECTED ZERO FILES … a guard that inspects nothing passes everything. This is an
ERROR, not a pass."* The Go census refuses an empty tree too, from `Run` and from its own test.

## 5. (v) The legitimate store is untouched and unchanged [VERIFIED]

| | current `main` | scratch merge of T154 into current `main` |
|---|---|---|
| verdict | `PASS (exit 0)` | `PASS (exit 0)` |
| parity vectors | **43** | **43** |
| graded cells | **5664** | **5664** |
| probe line | present, `up` | present, `up` |

`go build` 0 · `go vet` 0 · `go test ./...` **ok** · `--prove` **21 passed, 0 failed** exit 0 ·
`gofmt -l` names **exactly** `internal/apps/loanschedule/contract/contract.go` and nothing else
(gate G-3, expected; never `gofmt -w`).

**Nothing forbidden was touched.** `git diff --name-status main...T154` over `.softhouse/vectors`,
`contract/`, and `docs/adr` is **empty**. `PIN.json` and `capabilities.json` unmodified. The ten
files changed outside T154's own evidence directory are the two shell scripts, the guard register,
and six Go files in `conformance/`.

**Store census, re-taken on current `main` as asked.** T154's fork-point numbers hold exactly, and
the merge shifts them by exactly the one parity vector `main` promoted:

| | fork point (T154's census) | current `main` / merged |
|---|---|---|
| `.json` under the store root | 49 | **50** |
| store root (`PIN.json`, `capabilities.json`) | 2 | 2 |
| `loanschedule/` | 46 | **47** |
| `_selftest/` | 1 | 1 |
| vector files | 47 | **48** |
| parity / contract-refusal / self-test | 42 / 4 / 1 | **43** / 4 / 1 |
| `case_id`s outside `[A-Za-z0-9._-]` | 0 | 0 |

Arithmetic closes on both. `LoadStore` loads 47 → **48**.

## 6. P-24: T154's own provers, re-run against a scratch merge into current `main`

Not against the branch tip, where a stale baseline is invisible. All four, in a worktree checked out
at the merge commit:

| prover | rows | red | note |
|---|---|---|---|
| `drive-leg1.sh` | 12 | **0** | |
| `drive-leg1-e2e.sh` | 7 | **0** | |
| `drive-leg2.sh` | 18 | **0** | |
| `drive-leg3.sh` | 26 | **0** | `BASELINE: 43 parity vectors, 5664 graded cells` — **measured**, not literal |

**63 rows, 0 red**, and the store was not mutated (`git status --porcelain` clean afterwards).
I grepped all seven driver scripts for surviving literals (`42|43|44|5576|5623|5664|5670|…`): every
hit is inside a **comment explaining the removal**. Expectations are `BASE`, `BASE+1`, `BASE+2`,
`BASE_CELLS`, `>BASE_CELLS`, resolved from a measured control. **No hard-coded expectation survives
anywhere in T154's provers.**

---

## 7. Defects

### D-1 — MATERIAL, introduced by T154. The new P-35 report line is printed but never asserted.

T154 added `no-float census   N Go files / T tokens inspected` to the report as its positive
assertion, and `report.go`'s own comment states the rule: *"A run showing `0 files` here has checked
nothing and is exit 2."* **Nothing enforces that sentence.** `Summary.NoFloatCensus` is a plain
struct field; if the `Run` call site is removed it stays zero-valued and the report prints the
tell-tale next to a PASS.

Driven, on the merged tree with a float literal `0.036` planted in the loanschedule tree and the
census call site deleted from `grade.go`:

```
go build exit=0
conformance.sh exit=0
    conformance: reference oracle (…/actuator/health) probe = up
    no-float census         0 Go files / 0 tokens inspected under nexus/internal/apps/loanschedule
    VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5664 cells compared.
```

This is sharper than T154's own follow-up F-6 ("nothing demonstrates it goes red on a doctored
guard"): the harness **prints `0 Go files`, states in its source that `0` means exit 2, and exits 0
anyway**. `go test -run TestNoFloat` *does* catch the deletion (exit 1) — but `conformance.sh` does
not run `go test`, which is the exact P-45 shape T154 was dispatched to close.

**Micro-fix, 5 code lines, driven both ways** [`out/probe-xi.txt`]. In `grade.go`, immediately after
the census block and as a **separate statement**, so a minimal deletion of the call site leaves it
behind:

```go
	if s.NoFloatCensus.FilesScanned == 0 {
		s.FatalReasons = append(s.FatalReasons,
			"THE NO-FLOAT CENSUS INSPECTED ZERO GO FILES: a guard that inspects nothing passes everything, "+
				"so this is an ERROR and not a pass")
	}
```

| arm | result |
|---|---|
| fix applied, tree clean | **exit 0**, `43 / 5664`, census `24 files / 56295 tokens` — **no vector, cell or money number moves** |
| fix applied, call site deleted + float planted | **exit 2**, `* THE NO-FLOAT CENSUS INSPECTED ZERO GO FILES` |
| no fix, call site deleted + float planted | **exit 0, `VERDICT: PASS`** — the defect as it stands |

### D-2 — MATERIAL, inherited, but T154 claimed this row closed. The counter counts files *enumerated*, not files *scanned*.

Both shell guards increment `seen` once per file returned by `find`, **before** `perl` runs. Their
pipeline is `perl … | grep …` under `set -o pipefail`; if `perl` cannot run, the pipeline yields
nothing, the `if` is false, the counter still increments, and the guard prints `inspected N files`
and **returns success**.

Driven with `perl` **truly absent** from `PATH` (my first attempt put a `perl` that exits 127 on
`PATH` — that is *not* absence, `command -v` finds it, and that arm proved nothing; recorded rather
than deleted):

```
--- with perl TRULY ABSENT, over a store holding a PLAIN, PLAINLY VISIBLE float ---
    /tmp/t155/guards-post.sh: line 11: perl: command not found
    conformance: no-float guard — inspected 1 .json files under …/badstore
    conformance: no-float guard — inspected 1 .go files under …/badgo/…
    RC vectors=0 harness=0        <-- VACUOUS PASS ON A FLOAT
```

So the P-35 remediation is real for the `find`-returns-nothing case and **not** for the
`perl`-returns-nothing case. `load_toolchain` checks for `go` and not for `perl`.

**Micro-fix, 5 lines**, next to the existing `go` precondition in `load_toolchain`:

```sh
  if ! command -v perl >/dev/null 2>&1; then
    warn "conformance: no perl. Both no-float guards pipe every file through perl; without it they"
    warn "conformance: enumerate files and inspect none. EXIT 2 — the harness is unusable. NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
```

**Residual, stated plainly: this closes ABSENCE only.** It does **not** close "perl ran and died on
one particular file". The complete fix is to make the guard assert per-file that the scan produced
output — larger than a micro-fix, and raised as a follow-up rather than attempted here.

### D-3 — INHERITED HAZARD, newly load-bearing. The census's root is CWD-derived.

`cmd/conformance/main.go:38` is `conformance.FindRepoRoot(".")` — unchanged by T154 [VERIFIED:
identical at `187e972`; `registry.go` not in the diff]. The Go binary therefore resolves its repo
root from the **caller's working directory**, while `conformance.sh` derives `STORE_ROOT` and
`NEXUS_DIR` from the **script's own location**. Invoke a scratch tree's `conformance.sh` by absolute
path from elsewhere and the shell guards report the scratch tree's paths while the binary grades a
different store and censuses a different Go tree. This bit me directly (§0) and the 22-vs-24
file-count mismatch is what exposed it.

T154's follow-up **F-3 frames this as safe** — *"`FindRepoRoot` walks up for `.softhouse/vectors`,
so the repo is present by construction"*. That is true and beside the point: the repo it finds may
not be the repo under test. The wording should be corrected, and the durable fix is for
`conformance.sh` to pass `$REPO_ROOT` to the binary explicitly. Not T154's to fix; it should not be
left reading as reassurance.

### D-4 — ADVISORY. A test file's header now asserts something false about itself.

`store_integrity_test.go`'s header says, of the **whole file**: *"This file must COMPILE ON MAIN …
the whole file is therefore a valid main test, and on main it fails."* T154 added `TestStoreFileCensus`
to that file, which calls `StoreFileCensus` — a function `main` does not have.

Driven: dropping T154's `store_integrity_test.go` onto `main`'s tree gives
`vet: store_integrity_test.go:476:13: undefined: StoreFileCensus`, exit 1. Same for
`conformance_test.go`: `undefined: LoanScheduleTreeRel` at `:780`. The control (main's own tree)
vets clean.

The T110 design rule — keep the test compilable on `main` so it can be driven red on the bytes that
had the defect — **cannot** hold for the new sub-tests, and T154 substitutes `drive-leg3.sh` against
a `git archive` of the fork point, which is an adequate substitute. The sentence should be narrowed
in place, exactly as T154 correctly narrowed the stale paragraphs at `conformance.sh:141` and in
`vector.go`. It missed this one, in the file it was editing.

### D-5 — ADVISORY. The appended register baseline carries no sha.

`nonnegotiable-guard-audit.md`'s T154 section records the baseline as `42 parity vectors / 5576
cells`. That is the **fork point**. On merge a reader will see `43 / 5664` from a run and `42 / 5576`
in the register, dated the same day, with nothing to reconcile them. Add `@187e972` to the sentence.
The append itself is correctly append-only (P-27) and every figure in it reproduced.

### D-6 — ADVISORY. The census root is a fixed path.

`LoanScheduleTreeRel` is `nexus/internal/apps/loanschedule`. Today that is the **whole Go module** —
24 `.go` files in the module, 24 inside the censused tree, **0 outside** [VERIFIED]. The coverage
gap is zero files today and grows silently the moment a second Go package is added. Every remaining
`float32|float64|complex64|complex128` hit in the module is inside a **comment stating the
prohibition** — precisely the case the token-stream census exists to skip.

---

## 8. The driver's question: does leg 3 close the **deflated** direction?

**No. It closes inflation only, and the reading in the driver's message is correct.** Measured, not
reasoned, on the merged tree:

| store | exit | parity | cells | verdict |
|---|---|---|---|---|
| intact (control) | 0 | 43 | 5664 | PASS |
| **one parity vector file removed** | **0** | **42** | **5533** | **PASS — no warning anywhere** |
| **five parity vectors removed** | **0** | **38** | **5345** | **PASS — no warning anywhere** |
| whole `loanschedule/` context removed | 2 | 0 | 21 | UNUSABLE — corpus collapsed, not counted |
| one extra unloaded `.json` (inflation) | 2 | 0 | 0 | UNUSABLE — `STORE FILE CENSUS` names it |

*(T156 reports `42 / 5576` for the one-removed case; I get `42 / 5533` because I deleted a different
victim — `P-01`, worth 131 cells, against the T149 vector's 88. The direction and the silence are
identical; the exact cell count is a function of which vector is deleted.)*

**Why it is structural, with the lines.** `StoreFileCensus(storeRoot string, loaded []*Vector,
accountedErrs []LoadError)` takes only **what is** — never what *ought* to be. `seenJSON++` and every
`problems = append(…)` occur inside the `filepath.WalkDir` callback, so the function can only ever
speak about files it **found**; its own error text says so — *"N .json files were found … and M of
them are unaccounted for."* A deleted file is walked by nothing, counted in nothing, and both
enumerators agree it is absent, so the census is satisfied. `CaseIDIntegrity(vectors []*Vector)` has
the same shape: it can see two ids that collide, never an id that is missing.

**Nothing else in the store supplies the missing side.** `PIN.json` carries `schema`,
`fineract_commit`, `contract_file`, `mode`, `production_rounding`, `rate_factor_scale`,
`significant_digits`, `never_promotable_capture_case_ids`, `note` — **no expected corpus size and no
expected id set**. `conformance.sh` has no `expected_vector`, `manifest`, or `corpus_size` notion
[VERIFIED: grep empty].

**This is not grounds to reject T154.** Its brief asked for a census that *"REFUSES any `.json` under
the store root the harness did not load"* — inflation by construction. T154 delivered exactly that,
and delivered it well. The deflation gap is a **separate, pre-existing hole that T154 neither opened
nor was asked to close**.

**Scoping note for the driver's new task, offered because it is the same trap this whole review is
about.** A committed manifest of expected `case_id`s is the right shape — it is the only artefact
that can distinguish *"this store is complete"* from *"this store is self-consistent"*. Three
constraints, each the P-22 shape in a new costume:

1. **It must never be regenerated from the store.** A manifest derived from what is on disk is a
   tautology that passes by construction.
2. **A missing or empty manifest must be an ERROR, not a pass** — and the check must report the
   count it compared, positively, or it is the same vacuity one level up.
3. **It must not be deletable in the same edit as the vector.** If it lives beside the vectors, a
   worker removing a vector removes its row too and the check stays green. `PIN.json` is a natural
   home: it is already on the census allowlist and already float-checked by `LoadPin`, so the
   existing machinery covers it.

---

## 9. P-40 — what this review swept, and what it did not

| ground | size | covered |
|---|---|---|
| `.softhouse/conformance.sh` | 1 file, 30 grep lines | **every grep site**, PRE and POST |
| `.softhouse/bin/*.sh` | 4 files | **every grep site** |
| T154's own drivers | 7 files | **all re-run post-merge** |
| Go, inside the censused tree | 24 files | **all** (by the harness's own census, and by my probes) |
| Go, in the module outside that tree | **0 files** | n/a today — see D-6 |

**Skipped, deliberately:** ~200 historical evidence scripts under `.softhouse/reviews/*-evidence/`
and `.softhouse/handoff/*-evidence/` — committed transcripts of past measurements, editing them
falsifies the evidence they record (T154's reasoning, which I accept); **292 Python files** —
different encoding behaviour from BSD grep, and T156 swept that ground, so I did not re-do it; any
grep on an unmerged sibling branch; any grep constructed at runtime from a variable, which no
lexical sweep can see. Totals for context: 215 `.sh`, 292 `.py`, 1 `.pl`, 3,336 files under
`.softhouse/`.

**T156 states Go files are invisible to its `.sh`/`.py` sweep. The no-float guard surface I reviewed
is Go, and it is covered above: 24 of 24 files.**

---

## 10. Why I did not apply the two micro-fixes myself

Both are ≤10 lines, mechanical, and touch no number and no money logic, so both are within a
reviewer's remit. I did not apply them because **my branch is forked from `main`, which does not
carry T154's version of `grade.go` or `conformance.sh`.** Editing either file here would produce a
merge conflict at best and, at worst, silently revert T154's own hunk — the P-41 hazard in reverse,
and precisely the failure mode this review exists to catch. Both patches are given verbatim above
and driven red **and** green in `out/probe-xi.txt` and `out/probe-xii-true-absence.txt`. The
established precedent is the driver applying them on the subject branch at merge (`12a7f8d`, "Apply
A2-10's micro-fix").

## 11. What I checked and found nothing wrong with

So that silence is distinguishable from not looking: the sweeper's idempotency; `--help` output
integrity after the sentinel grep was swept; the absence of `egrep`/`fgrep`/`zgrep` spellings; the
token-stream exemptions for comments and for decimals inside string literals (both asserted by
T154's own test, and both re-checked by me); `--prove`'s 21 cases; determinism of the refusal
messages; the census under a context filter; hard links in both positions; the `accountedErrs`
escape route (load errors are fatal, so it is not one); the guard register's append-only discipline;
and that no ratified DEC-n, contract, vector, `PIN.json` or `capabilities.json` byte was touched.

## 12. Provers

All under `.softhouse/reviews/T155-probe/`, transcripts in `out/`. Every one reads pre-fix bytes
from an immutable git blob and **refuses on sha mismatch**.

`make-poison.sh` · `prove-i-invalid-byte.sh` · `prove-ii-literals.sh` · `prove-iii-census.sh` ·
`prove-iiib-binary-direct.sh` · `prove-iv-zero-input.sh` · `prove-v-census-counts.sh` ·
`prove-vi-build-test-prove.sh` · `prove-vii-residual-attacks.sh` · `prove-viii-compiles-on-main.sh` ·
`prove-ix-sweep-and-help.sh` · `prove-x-removal-and-failclosed.sh` · `prove-xi-microfix.sh` ·
`prove-xii-perl-microfix.sh` (superseded) · `prove-xii-perl-true-absence.sh` ·
`prove-xiii-deflation.sh` · `prove-xiv-sweep-coverage.sh` · `rerun-t154-provers-postmerge.sh` ·
`run-conformance.sh` · `show-refusals.sh`

## 13. Unverified

- **`[UNVERIFIED]`** — behaviour on any host but this one. Every grep result is BSD grep
  2.6.0-FreeBSD, `LANG=C.UTF-8`, invoked from inside a `bash` script. I did not re-run T108's ugrep
  half of the two-token argument; I inherit it, as T154 did.
- **`[UNVERIFIED]`** — filesystem sensitivity of the `UPPER.JSON` and NFC/NFD rows. Both driven on
  APFS, case-insensitive and normalisation-preserving. The census's rules are filesystem-independent
  by construction, but the measurement is single-platform.
- **`[UNVERIFIED]`** — that an invalid byte could actually reach a committed vector via the capture
  pipeline. What is measured is that the guard went blind on such a file, not that the pipeline can
  produce one. Fail-closed does not depend on the answer, and the store-root case needs no pipeline.
- **`[UNVERIFIED]`** — whether `perl` dying on one *particular* file (as opposed to being absent)
  produces the same vacuous pass. The mechanism is identical and I did not construct an input that
  kills `perl`.
