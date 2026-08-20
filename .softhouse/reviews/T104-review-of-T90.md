# T104 — independent review of T90 (`softhouse/T90-report-determinism`)

**Reviewer:** T104, spawned fresh, no part in planning or executing T90.
**Branch under review:** `softhouse/T90-report-determinism` (tip `243306b`), merge-base `ab2de89`.
**Method:** re-measured from bytes. Nothing below is taken from T90's handoff; every number was
produced by a script I wrote, on binaries I built, and the transcripts are reproduced inline.

## VERDICT: **APPROVED**

Every executable claim T90 makes reproduced. The defect is real, the fix is real, the fix changed
no verdict, no outcome, no cell count and no exit code, and the three regression guards are not
vacuous — I drove all three red on `main`'s actual bytes and then drove each guard's *order*
sub-assertion red with a second, different mutation that T90 did not try.

Five findings follow. **None is a defect in the shipped code.** F-T104-1 is a false sentence in the
handoff; F-T104-2 and F-T104-4 are evidence-strength corrections; F-T104-3 is a live harness defect
that T90 correctly identified, correctly declined to fix in this task, and (in my view) understated.

---

## 0. Environment, and what I touched

* Toolchain `go1.26.6 darwin/arm64`, repo-local `GOROOT` per `.softhouse/bin/go-env.sh`. `[VERIFIED: go version]`
* Reference oracle (Fineract) probed **read-only**, twice: my own `curl -sk https://localhost:8443/fineract-provider/actuator/health` → `{"status":"UP",...}`, and `conformance.sh`'s own probe → `probe = up`. **No container restarted, rebuilt, re-seeded or stopped; no write of any kind to the oracle DB.** `[VERIFIED: my transcripts]`
* Working trees: `git archive main` → `/tmp/t104/main-tree`, `git archive softhouse/T90-report-determinism` → `/tmp/t104/t90-tree` and a pristine `/tmp/t104/t90-clean`. `main-tree/nexus` is `diff -r`-identical to this worktree's `nexus`. `[VERIFIED]`
* `main` never touched. Review committed to `softhouse/T104-review-t90`. A scratch merge branch was created, tested and deleted (§8).

---

## 1. Claim (a) — the brief's `files_hint` was wrong, `report.go:102` was right

**VERIFIED.** There is no `nexus/internal/apps/loanschedule/harness/` directory. The package is
`conformance/`. On `main`, `report.go:102` is `for capName, ids := range s.CounterfactualCoverage`,
and a type-aware census (§5) resolves `s.CounterfactualCoverage` to `map[string][]string`.
`[VERIFIED: type-check of the package, not a grep]`

---

## 2. Claim (e) — pre-fix nondeterminism, MY measurement

One binary built from `main`'s bytes, one store, one flag set
(`-oracle-probe=up -store=/tmp/t104/main-tree/.softhouse/vectors`).

```
=== prefix: distinct stdout sha256 over 30 runs ===
  28 adde39442de4095209d69ff72edd457564c945ebe66f952913516d51e36cb00c
   2 4c791721c392cc77938a27eff691ea5dd0bf3e585f2af25f1cb260ae6c322768
=== distinct stderr sha256 === 30 e3b0c442…852b855 (= empty)
=== distinct exit codes ===  30 0

=== prefix100: distinct stdout sha256 over 100 runs ===
  80 adde39442de4095209d69ff72edd457564c945ebe66f952913516d51e36cb00c
  20 4c791721c392cc77938a27eff691ea5dd0bf3e585f2af25f1cb260ae6c322768
```

**My split is 28/2 over 30, and 80/20 over 100** — 130 runs, **exactly two distinct outputs**, 108/22.
More than one distinct output pre-fix: **confirmed independently.** `[VERIFIED: my runs]`

T81's 23/7, T86's 27/3 and T90's 26/4 are `[UNVERIFIED]` by me — I did not re-run them and did not
need to.

`diff` between my two variants is **exactly two lines**, `69d68` / `70a70`, the `schedule.core`
coverage line moving across the `monthend.reanchor` line. Nothing else differs in either direction
across all 130 runs. `[VERIFIED: diff transcript]`

**Mechanism, which I add because it explains why every observer gets a different split.** The shipped
store's `CounterfactualCoverage` has **exactly two keys** — `monthend.reanchor` and `schedule.core`
(`grep -c "killed by"` on the report = 2). Two keys admit exactly `2! = 2` orderings, so the report
has exactly two reachable byte images, and the "split" is a biased Bernoulli over Go's per-range
start-offset randomisation. That is why 23/7, 27/3, 26/4, 28/2 and 80/20 are all the same finding,
and why no observer should expect to reproduce another's ratio. T90 did not claim otherwise.

---

## 3. Claim (f) — post-fix byte identity, and why my sha256 differs from T90's

```
=== postfix: distinct stdout sha256 over 30 runs ===   30 4c791721c392cc77938a27eff691ea5dd0bf3e585f2af25f1cb260ae6c322768
=== postfix100: distinct stdout sha256 over 100 runs === 100 4c791721c392cc77938a27eff691ea5dd0bf3e585f2af25f1cb260ae6c322768
=== distinct exit codes ===  130 0
```

**130 runs, exactly one sha256.** `[VERIFIED: my runs]`

It is **not** T90's `8c22938f…`, and the brief was right to demand the cause be established before
concluding anything. **The cause is the absolute store path, and I proved it rather than assumed it.**

1. The report embeds the store root at line 3 and nowhere else: running the post-fix binary against
   two byte-identical stores at different absolute paths produced reports differing in **exactly one
   line**, line 3. `[VERIFIED: diff]`
2. `git worktree list` puts T90's worktree at
   `/Users/buv/gerege-nbfi/.claude/worktrees/agent-a2b7a771c72bc75fd`. Substituting that path into
   line 3 of **my** post-fix report and hashing gives:

```
8c22938ffb027f4c25e5fa33b7341903521ee24cf750a761a508eac3c3d29992  /tmp/t104/out/post-as-t90path.txt
T90 claimed:  8c22938ffb027f4c25e5fa33b7341903521ee24cf750a761a508eac3c3d29992
```

**Exact match on all 64 hex digits.** So T90's reported sha256 is authentic, T90's store was the
committed store, and there is **no residual nondeterminism** — the only difference between T90's run
and mine is one filesystem path. This is a stronger result than "different store path, probably fine":
it reconstructs T90's exact bytes from mine. `[VERIFIED: sed + shasum transcript]`

This also independently confirms **F-T90-2**: reviewers cannot diff a worker's run against a `main`
run byte-for-byte until the report carries a repo-relative path. That follow-up should be raised to a
task, because this pipeline's whole review method depends on it.

---

## 4. Claim (g) — "nothing but line order moved", checked the hard way

```
cmp post.txt pre-minority.txt   → rc=0            IDENTICAL, byte for byte
cmp post.txt pre-majority.txt   → differ: char 5747, line 69
line counts: 146 / 146 / 146
```

**The post-fix bytes ARE one of the pre-fix runs.** `[VERIFIED: cmp]` The fix selected an order the
pre-fix code already produced (22 times in my 130), so every graded cell, margin and count in the
post-fix report is literally the same bytes the pre-fix binary emitted.

Independently, not relying on that argument:

* **Per-vector outcome table**, `CASE | CLASS | SEAM | OUTCOME | CELLS` extracted from `main`'s run and
  the post-fix run and `cmp`'d → **identical, 47 vector rows** (49 extracted lines including the header
  and the `VERDICT` line; T90's "49 rows" is the same artefact). `[VERIFIED: cmp]`
* **Whole-report diff**, `main` vs post-fix: `diff | grep -c '^[<>]'` → **2**, and both are the same
  `schedule.core` line. So *every* headline counter is untouched by construction, not by inspection.
  `[VERIFIED]`
* Headline counters read off the post-fix report: `parity vectors PASS 42 FAIL 0`,
  `contract-refusal PASS 4 FAIL 0`, `self-test fixtures PASS 1 FAIL 0`, `refused 0`,
  `inadmissible 0`, `harness errors 0`, `cells compared 5576 graded, 84 ungraded`,
  `kills named 102 money, 7 structural`, `invariant violations 0`,
  `invariant assertions 0 NOT RUN`, `VERDICT: PASS (exit 0)`. `[VERIFIED]`

**Can the reordering change an outcome at all?** I traced the verdict path rather than trusting the
byte identity. `Summary.ExitCode()` keys on `len(s.FatalReasons) > 0` — a **count**, never a content or
an order (`grade.go:154-160`). Site 2's defects are appended one per `(rowKind, col)`, so reordering
changes the sequence and not the multiset. Site 3 returns `nil, err` on any bad entry and the caller
does `FatalReasons = append(...); return s, nil` (`grade.go:240-244`), so **which** entry is named
cannot change **whether** the registry is rejected. T90's claims on both points are correct.
`[VERIFIED: source read + the byte identity]`

---

## 5. Claim (b)/(c)/(d) — the sites, and whether the enumeration is complete

I did not grep. I wrote a **type-aware census** (`go/parser` + `go/types`, source importer) that
type-checks each package and reports every `range` whose subject's core type is a map, plus every
`sort.*` call site. It resolved **0 unresolved** range subjects, so its enumeration is exhaustive over
the code it type-checked.

`main`, package `conformance`, non-test — **exactly 7 map ranges**:

```
capability.go:140   range s.Status                   map[string]conformance.SeamStatus      <- FIXED (site 3)
capability.go:268   range covered                    map[string][]string                    <- left alone (site 6)
invariants.go:114   range p                          map[int]map[string]bool                <- left alone (site 8)
registry.go:57      range impls                      map[string]contract.ScheduleGenerator  <- left alone (site 7)
report.go:102       range s.CounterfactualCoverage   map[string][]string                    <- FIXED (site 1)
structural.go:211   range s.ColumnsByRowKind         map[string][]string                    <- left alone (site 5)
structural.go:475   range s.ColumnsByRowKind         map[string][]string                    <- FIXED (site 2)
```

T90 branch, same package — **5**, and the three fixed sites are gone; `report.go:325` is the new
`sortedKeys` helper (which sorts immediately).

Other packages in the tree: `loanschedule` **0 map ranges, 0 sort calls**; `contract` **0/0**;
`conformance/cmd/conformance` **0/0**. So T90's statement that the port itself contributes no
map-order surface is **VERIFIED by type information**, not by `grep 'map['`.

**T90's site enumeration for non-test code is complete and correctly classified.** There is no map
range in shipped code that T90 missed.

### The five left-alone sites, each reason re-verified from source

| Site | T90's reason | My check |
|---|---|---|
| `structural.go:211` `RowKinds()` | "already `sort.Strings`es before returning" | **CORRECT.** Ranges into `out`, `sort.Strings(out)`, `return out` (`:209-215`). |
| `capability.go:268` `for k := range covered` | "only *sorts each value*; writes nothing ordered" | **CORRECT in substance.** The body is `sort.Strings(covered[k])` — each iteration touches a disjoint key, so iteration order is unobservable. The sibling `uncovered` is built by ranging `r.GradedCapabilities()`, which ranges the **slice** `r.Capabilities` and sorts before returning (`:213-221`) — deterministic. *Wording nit:* the map itself **does** reach output (it becomes `Summary.CounterfactualCoverage`); it is this **loop's order** that does not. T90's table cell says "Reaches output? No", which is loose but not misleading in context. |
| `registry.go:57` `RegisteredNames()` | "already `sort.Strings`es before returning" | **CORRECT.** `:56-61`. |
| `invariants.go:114` `Count()` | "sums `len(row)`; addition is commutative" | **CORRECT.** `n += len(row)` over `map[int]map[string]bool`. |
| lookup-only maps (`grade.go`, `admit.go`, `invariants.go`, `registry.go`, `capability.go`) | "never appear as a ranged expression" | **CORRECT** — the census finds no range over any of them. I additionally checked `ContextsIn` (`grade.go:599-608`), which uses a map purely for dedup and builds its output slice in **vector order**; deterministic given `LoadStore`'s sort, and a genuine consumer of the comparator's totality. |

Also re-verified: `sort.SliceStable` at `invariants.go:765` is stable and its input is a slice built
in schedule order, so ties preserve a deterministic order. `[VERIFIED: source]`

### My own sweep for other order-dependence (and what it could NOT find)

Searched across the whole non-test `loanschedule` tree:
`time.Now|time.Since|math/rand|crypto/rand|rand.|go func|go X(|select {|sync.|filepath.Walk|WalkDir|filepath.Glob|os.Getenv|os.Environ|%p|unsafe.|runtime.|reflect.|iter.Seq|maps.Keys`
→ **exactly one hit: `conformance/registry.go:27  implMu sync.RWMutex`** — a lock, not concurrency.
No clock, no randomness, no goroutine, no environment read, no pointer printing, no `maps.Keys`.
`os.ReadDir` twice (`vector.go:822,837`, documented sorted by filename); **no** `filepath.Walk`,
`WalkDir` or `Glob`; **no** `json.Marshal`/`Encoder` in non-test code, so no Go-map-to-JSON surface
at all; **no** `os.Create`/`WriteFile` — the harness writes no files. `[VERIFIED: my greps]`

**What my sweep could NOT have found (P-12):**

1. **Order-dependence reachable only through cgo, linker order or a non-Go layer.** Out of scope of a type-check.
2. **Anything in `conformance.sh` beyond what I ran.** I ran the default mode and `--prove`; I did not audit `--self-test` or every branch of the script.
3. **Any other Go version, OS or architecture.** Map-iteration randomisation and `sort.Slice`'s algorithm are runtime properties. Everything here is go1.26.6 darwin/arm64.
4. **A future contributor ranging a map directly.** `sortedKeys` is a convention with no enforcement (T90's own F-T90-3, still open and worth doing).
5. **Sections of the report that no input I constructed ever fired.** I closed the load-error block by measurement (§6); the refusal-detail and NOT-ASSERTED blocks I only *read*, exactly as T90 did.

---

## 6. Sites 2 and 3 — the ones no measurement of shipped data can reach

**T90's claim (c) is VERIFIED first:** on the shipped store the conformance report contains
`0` occurrences of `HARNESS DECLARATION DEFECT` and `0` of `capability registry:`. Both loops emit
nothing, so T90's own 130-run byte-identity evidence genuinely **cannot** cover them. Right call by
T90 to say so; the brief was right to make them the focus.

So I constructed inputs and **measured**, on both trees, with my own probe (not T90's test — a
*counting* probe, so a "stable" result is a number rather than a pass):

**Site 2 — `declarationDefects`, an `AttestationSource` with FOUR bogus row kinds:**

```
MAIN  (pre-fix):  500 iterations produced 4 DISTINCT defect orderings
                   x317 first-defect: … row kind "T104_ZEBRA" …
                   x70  first-defect: … row kind "T104_QUAGGA" …
                   x62  first-defect: … row kind "T104_MIDDLE" …
                   x51  first-defect: … row kind "T104_AARDV" …
T90   (post-fix): 500 iterations produced 1 DISTINCT defect ordering
                   x500 first-defect: … row kind "T104_AARDV" …     (lexicographically first)
```

**Site 3 — `LoadCapabilityRegistry`, a registry with FOUR unknown capabilities on one seam:**

```
MAIN  (pre-fix):  500 iterations produced 4 DISTINCT error strings
                   x303 … unknown capability "zzz.bad"
                   x72  … unknown capability "qqq.bad"
                   x63  … unknown capability "aaa.bad"
                   x62  … unknown capability "mmm.bad"
T90   (post-fix): 500 iterations produced 1 DISTINCT error string
                   x500 … unknown capability "aaa.bad"              (lexicographically first)
```

**`main` genuinely names one at random; T90's is deterministic and names the documented one.** Both
of T90's unmeasurable claims are now measured. `[VERIFIED: my probe, both trees]`

---

## 7. `vector.go:854` — the comparator, scrutinised separately

T90 labels this "hardening, not a defect I observed", "inert today", and adds `path` as a third key.
I attacked it three ways.

**(i) Is `path` actually unique?** `rel = filepath.Join(ctx, f.Name())` and `os.ReadDir` yields unique
names within a directory, directories unique within the store ⇒ `Path` is unique across the store.
Note `Vector.Context` is read from the JSON `"context"` field (`vector.go:693`), **not** from the
directory name — so two files in different directories may share a `Context`; their `Path`s still
differ. The comparator is **total** either way. `[VERIFIED: source]`

**(ii) Is the store free of duplicates today?** 47 files, 47 `case_id` lines, **47 distinct values**,
0 repeated `(context, case_id)` pairs. T90's "all 47 case_ids distinct" is **VERIFIED**.

**(iii) Is the key inert today?** I built T90's tree with **only** `vector.go` reverted to `main`'s
comparator and ran it against the shipped store: sha256 `4c791721…`, `cmp`-identical to the full
post-fix report. **Inert: VERIFIED**, by construction rather than by assertion.

**(iv) Does a duplicate `case_id` actually reorder?** I built one — copied `P-00-baseline-6x7pct.json`
to `AAA-duplicate-caseid-of-P-00.json`, same `case_id`, same context, 48 files.

```
dup-store, main binary (pre-fix)                     : 30 runs → 25/5, TWO distinct sha256
dup-store, T90 minus the tie-break (map fixes only)  : 40 runs → 40/40, ONE distinct sha256
dup-store, T90 full                                  : 30 runs → 30/30, ONE distinct sha256, same sha
```

**Finding: the tie-break did NOT go red.** The 25/5 on `main` is entirely the `report.go:102` map
defect; with the map fixes in and the tie-break reverted, a genuine `(context, case_id)` tie is
**deterministic across 40 runs**. The reason is that the pre-sort order comes from `os.ReadDir`
(filename-sorted) and Go's `sort.Slice`/pdqsort is a deterministic algorithm, so a tie resolves the
same way every run on this toolchain. `[VERIFIED: my runs]`

**Is T90 wrong?** No. Its wording is "decided by an **unspecified rule** rather than by the data" —
which is exactly right, and it explicitly declined to call this a defect it observed. But a reader
skimming the four-item list will read site 4 as a fourth fixed nondeterminism, and it is not one:
it is protection against `sort.Slice`'s implementation or the input order changing later. Recorded as
**F-T104-2** so the record is unambiguous. No guard was shipped for it, so nothing is *believed*
without evidence and P-22 is not breached — but P-22's spirit says label it, and I am labelling it.

**(v) Does the new comparator still GRADE correctly, and does it mask the real defect?**
Grading is per-vector; `s.Results[i]` stays paired with `vectors[i]` under any permutation, and every
aggregate is a sum (`CounterfactualsNamed += …`, `MoneyKills++`, `StructuralKills++`). Order affects
presentation and `ContextsIn`, nothing arithmetic. `[VERIFIED: source]`

**But the duplicate store exposes something worth escalating** — see F-T104-3.

---

## 8. Claim (h) — the three guards, and whether they can fail

**Driven RED by me on `main`'s real bytes**, by copying T90's `report_determinism_test.go` unchanged
into `/tmp/t104/main-tree` and running it:

```
--- FAIL: TestReportIsByteIdenticalAcrossRenders
    WriteReport is NOT byte-reproducible: render 1 differs from render 0.
--- FAIL: TestDeclarationDefectsAreReportedInAStableOrder
    declarationDefects is not order-stable: call 3 differs.
--- FAIL: TestCapabilityRegistryErrorNamesTheSameDefectEveryTime
    the error must name the lexicographically first offending capability,
      got: … unknown capability "mmm.unknown.capability"
    LoadCapabilityRegistry names a different defect between runs
FAIL  github.com/gerege/nexus/internal/apps/loanschedule/conformance  0.247s
```

Each fails **for the right reason** — the message names the map-order defect, not an unrelated error,
and guard 3 trips both of its assertions. `[VERIFIED: my run]`

**Then a second, different mutation T90 did not try**, because "driven red against the unsorted loop"
only proves a guard detects *instability* — it does not prove the guard pins the *documented* order.
I made `sortedKeys` and `RowKinds()`-in-`declarationDefects` **stable but DESCENDING**:

```
--- FAIL: TestReportIsByteIdenticalAcrossRenders
    coverage lines are not in ascending capability order: [zeroprincipal.guard seam.pathb schedule.core …]
--- FAIL: TestDeclarationDefectsAreReportedInAStableOrder
    row kinds are reported in [BOGUS_ZEBRA BOGUS_MIDDLE BOGUS_AARDV], want ascending order
--- FAIL: TestCapabilityRegistryErrorNamesTheSameDefectEveryTime
    the error must name the lexicographically first offending capability, got: … "zzz.unknown.capability"
```

And a third, reversing only the **ids within a line**:

```
--- FAIL: TestReportIsByteIdenticalAcrossRenders
    counterfactual ids for "schedule.core" are not in ascending order: [Z-KILL M-KILL [structural] A-KILL]
```

**All three guards fail on both a stability mutation and an order mutation. None is vacuous.**
Their structural anti-vacuity checks are also present and functional: guard 1 asserts
`len(printedKeys) == len(coverage)` (catches the section silently vanishing), guard 2 asserts
`len(first) >= 3` (catches the validator silently emitting nothing), guard 3 asserts `err != nil`
(catches the registry silently accepting a bad seam). `[VERIFIED: source + my mutation runs]`

**No P-24 time bomb.** `grep -nE "git |merge-base|main:|exec.Command"` on the new test file → nothing.
The guards are pure in-memory unit tests with no moving baseline ref.

**P-24 standing step performed anyway.** `git diff ab2de89 main` touches only
`.softhouse/state/fire-*.STATE.json` and `.softhouse/tasks.json` — disjoint from T90's six files. I
made a scratch branch off current `main` (`cc80688`), merged T90 in cleanly, confirmed
`diff -r nexus /tmp/t104/t90-clean/nexus` → **identical**, and ran the full gate set on the
**post-merge** tree. Branch deleted afterwards; `main` untouched.

---

## 9. Invariants and gates

Run on a pristine `git archive` of the branch, and again on the post-merge scratch tree — same results.

| Gate | Expected | Measured |
|---|---|---|
| `git diff main...branch -- .softhouse/vectors/` | empty | **empty** ✓ |
| `PIN.json`, `capabilities.json` | untouched | both live under `.softhouse/vectors/`, untouched ✓ |
| `contract.go` | byte-identical to main | `cmp` → **identical** ✓ |
| `gofmt -l ./internal` | names exactly `contract/contract.go` (G-3) | **exactly that, on both main and branch** — not "fixed" ✓ |
| `go build ./...` | 0 | **0** ✓ |
| `go vet ./...` | 0 | **0** ✓ |
| `go test ./... -count=1` | ok | **ok** (`loanschedule` 8.2 s, `conformance` 9.4 s) ✓ |
| `bash .softhouse/conformance.sh` | PASS, exit 0 | **exit 0**, `probe = up` ✓ |
| parity vectors | 42 | **42 PASS / 0 FAIL** ✓ |
| graded cells | 5576 | **5576 graded, 84 ungraded** ✓ |
| invariant violations | 0 | **0** ✓ |
| invariant assertions NOT RUN | 0 | **0** ✓ |
| refused / inadmissible / harness errors | 0/0/0 | **0/0/0** ✓ |
| `bash .softhouse/conformance.sh --prove` | 21 | **21 passed, 0 failed**, exit 0 ✓ |

Run with **`bash`**, never `sh`. Exit 3 was never seen.

Files changed by the branch: exactly six — one handoff `.md` and five files under
`nexus/internal/apps/loanschedule/conformance/`. No scope breach.

**Additional measurement, closing part of T90's sweep limitation 1.** T90 said the load-error block
was *read*, not *measured*. I measured it: a store with four malformed `.json` files across two
context directories, post-fix binary, **30 runs → 1 distinct sha256, exit 2 on all 30**, and the block
printed sorted by `(context dir, filename)`:

```
--- FILES THAT COULD NOT BE READ AS VECTORS (each one makes this run unusable) ---
    _selftest/MMM-bad-three.json: …
    loanschedule/AAA-bad-two.json: …
    loanschedule/MMM-bad-four.json: …
    loanschedule/ZZZ-bad-one.json: …
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

---

## 10. Money

**Nothing in this diff touches money arithmetic, and there is nothing to re-derive.** The executable
change is: three loops that now iterate sorted keys, one added string comparator key, one defensive
`sort.Strings` on a **copy** of a `[]string` of counterfactual **names**, and one new test file.

* No arithmetic operator, no rounding, no `setScale`, no `MathContext`-bearing field, no `int64` cell,
  no `MinorText` in the diff. `[VERIFIED: read every added line]`
* `grep '^+' | grep -E 'float|float32|float64|math\.'` over the diff → the only hits are the literal
  strings `26/4`, `23/7`, `27/3` inside comments. **No float type anywhere.** `[VERIFIED]`
* Non-test `float32|float64` in the whole tree → four **prose** mentions inside `contract.go`
  forbidding them. `TestNoFloatInTheLoanScheduleTree` runs and passes. `[VERIFIED]`
* The `sort.Strings(ids)` in `report.go` operates on `append([]string(nil), …)` — a copy — so it cannot
  mutate `Summary.CounterfactualCoverage` for any later consumer, and `grep` shows the only consumers
  are `report.go:99` and `:102`. `[VERIFIED: source]`
* The decisive evidence is not this argument but the `cmp` of §4: the post-fix report **is** a pre-fix
  report, so every money cell in it is the same bytes `main` emitted.

---

## Findings

### F-T104-1 — P2. T90's sweep claim about test files is false as written

T90's sweep section states:

> `_test.go` files, for map ranges — **none** (the three `range` hits there are slice ranges).

**That is wrong.** On `main`, `grep -rn "range " --include='*_test.go'` returns **40** hits, not three,
and the type-aware census finds **three map ranges** among them:

* `structural_test.go:116` `for c := range want` (`map[string]bool`)
* `structural_test.go:121` `for c := range got` (`map[string]bool`)
* `structural_test.go:954` `func keysOf(m map[string]bool) []string` — returns keys **unsorted**, and
  its result is interpolated into a `t.Errorf` message at `:114`.

The sentence appears to describe T90's **own new file** (`report_determinism_test.go` has exactly three
`range` hits, and those three genuinely are slice ranges) while the wording scopes it to all
`_test.go` files.

**Consequence: nil for the harness.** All three are test-only and reachable only on a *failing*
assertion; none can reach the conformance report, a verdict, an exit code or a money cell. What is
damaged is the sweep-completeness claim in a handoff whose subject is sweep completeness — P-21's
exact shape. **Recommend the driver amend that line at source when merging**, rather than let the next
sweep inherit it. Not a rejection: the shipped code and every code comment I checked are accurate.

### F-T104-2 — P2. Site 4 is hardening, and it did not go red

See §7(iv). With T90's map fixes in and only the `path` key reverted, a constructed duplicate
`case_id` produced **40/40 byte-identical** reports. T90's own wording is careful and correct
("hardening, not a defect I observed", "inert today", "an unspecified rule"), and no guard was shipped
for it — so nothing is believed on faith. Recorded so that no later reader promotes site 4 to "a
fourth nondeterminism that was fixed". The change is still worth keeping: it makes the row order a
function of the store's contents rather than of pdqsort's behaviour on a tie.

### F-T104-3 — P1. A duplicate `case_id` is silently GRADED and inflates the headline evidence

On my duplicate store the harness reports:

```
parity vectors  PASS 43   FAIL 0
cells compared  5623 graded, 86 ungraded
inadmissible    0        harness errors 0
VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5623 cells compared.
```

**No warning, no refusal, no fatal reason** — the duplicate is graded a second time and both the vector
count and the cell count move. Those two numbers are exactly what this program quotes as its evidence
of coverage ("42 parity vectors, 5,576 graded cells" appears in postmortems, gates and briefs). A
corpus that accidentally acquires a duplicate would report *more* coverage than it has, and the report
gives a reader nothing to notice it by.

T90 identified this (**F-T90-1**), correctly declined to fix it inside a determinism task (a rejection
check can turn exit 0 into exit 2, which would have destroyed this task's own proof), and filed it as a
follow-up. I agree with the decision and disagree with the severity: this is not a hygiene item, it is
a way for the headline coverage number to be wrong while every gate stays green — P-22's failure mode
one level up, in the corpus rather than in a guard. **Recommend raising F-T90-1 to a task**, and that
the rejection be a `LoadStore` fatal reason (exit 2), not a silent dedup.

T90's comparator change does **not** mask it: the count moves with or without the `path` key.

### F-T104-4 — advisory. The 30-run binary experiment is the weakest instrument in this proof

Because the shipped coverage map has only two keys, the pre-fix defect is a single biased coin flip per
run. Observed minority frequencies: T81 23 %, T86 10 %, T90 13 %, T104 **6.7 %** (2/30) and **20 %**
(20/100) — my own two batches differ by a factor of three. At the low end, a 30-run batch has roughly a
one-in-eight chance of showing a **single** sha256 and thus falsely certifying `main` as deterministic.

Anyone re-running this should use **N ≥ 100**, or better, use the unit guard: with twelve keys and 200
renders, `TestReportIsByteIdenticalAcrossRenders` fails on `main` essentially with certainty, and it
failed at render 1 for me. The guard is the reliable instrument; the binary experiment is the
illustrative one. This does not weaken T90 — its guard is the strong artefact and it shipped it.

### F-T104-5 — nit, no action required

`report.go`'s new comment freezes `split 26/4` into source. Mine were 28/2 and 80/20. The same sentence
also cites 23/7 and 27/3, so a reader can see the ratio varies; but "the split is not reproducible;
what is reproducible is that more than one output exists" would be the safer sentence. Comments do not
affect report bytes, so this is a safe edit if the driver wants it. I am **not** raising it to a
MICRO-FIX — T90's proof rests on the fixed sites, not on this ratio.

---

## What I checked and found nothing wrong with

So that silence is distinguishable from not looking:

* Every added line of the diff, read individually — no arithmetic, no float, no money field.
* All 7 non-test map ranges in `main`'s `conformance` package, by type-check; all 5 in T90's.
* All 4 other packages in the `loanschedule` tree — 0 map ranges, 0 sort calls.
* The five sites T90 left alone — each reason re-derived from the source, all five correct.
* `sort.SliceStable` at `invariants.go:765` and every other `sort.*` call site, for tie-freedom.
* `ExitCode()` and the `FatalReasons` append path, to prove sites 2 and 3 cannot move a verdict.
* `ContextsIn`, a second consumer of the comparator's totality.
* Clock, randomness, goroutine, `select`, `sync`, env, `filepath.Walk`/`WalkDir`/`Glob`,
  `json.Marshal`, `os.Create`/`WriteFile`, `unsafe`, `reflect`, `maps.Keys` — one hit in total, a mutex.
* Uniqueness of all 47 `case_id`s and all 47 `(context, case_id)` pairs in the shipped store.
* `contract.go` byte identity; `gofmt -l` G-3 state on both trees; the six-file scope.
* The post-merge state, via a real scratch merge into current `main`.

---

## Recommendation

**APPROVED — merge.** Carry F-T104-1 as a one-line correction to T90's handoff, and raise
**F-T90-1** (reject duplicate `case_id`) and **F-T90-2** (repo-relative store path in the report) to
tasks: the first protects the headline coverage numbers, the second is a precondition for the
cross-worktree byte-diffs this pipeline's review method already assumes it can do.

*Per P-19: conformance PASS here means "matches the reference oracle where the 42 vectors look."
T90 changed neither the corpus nor the graded domain, so this review says nothing about any region
no vector reaches.*
