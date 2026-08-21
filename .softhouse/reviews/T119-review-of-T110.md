# T119 — INDEPENDENT review of T110 (`softhouse/T110-duplicate-caseid-refusal`, commit `105589b`)

**Verdict: MICRO-FIX.**

Every load-bearing claim T110 makes reproduced, on my own trees, with my own binaries, from
`git archive` bytes. The behaviour of the fix is correct, the guard is genuinely red on `main`, and
the mutation set is real — including the one that matters (M3). Three defects found, **all in stated
rationale rather than in behaviour**, plus one required edit that belongs to the *driver* and not to
this diff. Nothing here justifies a rejection or a retry of the code.

- **Branch reviewed:** `softhouse/T110-duplicate-caseid-refusal` @ `105589b`, 1 commit, 4 files.
- **Baseline:** `main` @ `41132e5`. `git merge-base main <branch>` = `8faee44`. `main` has moved since
  the fork by exactly three files — `.softhouse/patterns.md`, `.softhouse/state/fire-20260821-080001.STATE.json`,
  `.softhouse/tasks.json` — **disjoint** from T110's four, so the merge is trivially clean (P-24 check below).
- **Toolchain:** `go1.26.6 darwin/arm64`, repo-local per `.softhouse/bin/go-env.sh`.
- **Reference oracle (Fineract):** UP; probed read-only by `conformance.sh`'s own probe → `probe = up`.
  No container restarted, rebuilt, re-seeded or written. Oracle Database appears nowhere; PostgreSQL only.
- **Scratch:** everything under `/tmp/t119/`. `git diff -- .softhouse/vectors/` is **empty**; no vector
  JSON, `PIN.json` or `capabilities.json` was touched; `.softhouse/conformance.sh` was *executed*, never edited.

---

## 1. Claim-by-claim re-derivation

### Claim 1 — the pre-fix green. **REPRODUCED EXACTLY.**

Built from `main`'s bytes, not by hand-editing the fixed file:

```
$ git archive main | tar -x -C /tmp/t119/main-tree
$ (cd /tmp/t119/main-tree/nexus && go build -o /tmp/t119/conf-main ./internal/apps/loanschedule/conformance/cmd/conformance)   # rc=0
$ cp .../P-00-baseline-6x7pct.json .../AAA-duplicate-caseid-of-P-00.json
$ grep -h '"case_id"' .../AAA-duplicate-caseid-of-P-00.json .../P-00-baseline-6x7pct.json
  "case_id": "P-00",
  "case_id": "P-00",
$ /tmp/t119/conf-main -oracle-probe=up -store=/tmp/t119/dup-store ; echo exit=$?
    parity vectors          PASS 43   FAIL 0
    self-test fixtures      PASS 1    FAIL 0
    inadmissible            0
    harness errors          0
    cells compared          5623 graded, 86 ungraded
VERDICT: PASS (exit 0) — 43 parity vectors match the pinned reference oracle, 5623 cells compared.
exit=0
stderr bytes: 0
grep -Eic 'duplicate|WARN' over the whole report = 0
10:P-00                         parity           path_a_e... PASS             47        2
11:P-00                         parity           path_a_e... PASS             47        2
```

43 / 5623 / PASS / exit 0, empty stderr, zero warning lines, and the P-00 row printed **twice**, at
report lines 10 and 11. `[VERIFIED: my run]` Unperturbed store, same binary: **42 / 5576 / PASS / exit 0.**

### Claim 2 — the channel choice. **ARGUMENT VERIFIED FROM SOURCE. Ruling in §3.**

T110's rejection of `Summary.Errored` is correct and I re-derived it:

- `grade.go:318-319` — `switch r.Outcome { case OutcomeError: s.Errored++ }`, and that `switch` is inside
  `for _, v := range vectors { r := gradeVector(...) ... }`. Routing the refusal there **requires grading
  to have already run**, which is the one thing that must not happen.
- `LoadError` reaches exit 2 (`grade.go:158` — `len(s.LoadErrors) > 0`) but **does not return early**;
  `Run` sets `s.LoadErrors` and falls through to the loop. So a `LoadError` gives the right exit code and
  still prints 43/5623. That is not a hypothetical: it is mutation **M3**, and M3 is red (§Claim 3).
- A fifth exit code would contradict the four-code table stated in three places: `conformance.sh:11-22`,
  `grade.go:139-153`, and `.softhouse/vectors/README.md`.
- `FatalReasons` → exit 2 is the existing channel and already carries **eight or more** distinct
  unusable conditions (`grade.go:228, 234, 238, 242, 250, 255, 261, 268, 277, 346, 357`), including
  `ZERO VECTORS FOUND` — the other way a store lies about its size.

### Claim 3 — the refusal runs BEFORE grading. **RE-RUN. CONFIRMED, and M3 is the proof.**

The early return is at `grade.go:270-278` on the branch; the grading loop begins at `:288`. The
mutation matters more than the reading. Full transcript in §2 — the decisive row:

```
########## M3 (warn only: record as a LoadError, keep grading) ##########
    store_integrity_test.go:148: the refusal must fire BEFORE grading: got 48 results,
        5623 graded cells, 43 parity passes, 1 self-test passes — the control graded 47
        vectors, so these numbers were computed and could be quoted
```

M3 fails at **line 148 (the counts assertion), not line 145 (the exit-code assertion)** — i.e. the exit
code *was* 2 and the guard caught it anyway. T110's central claim about its own guard is exactly right.

### Claim 4 — the byte-identical baseline. **VERIFIED BY `cmp`. The comparison was SOUND.**

```
$ /tmp/t119/conf-main -oracle-probe=up -store=/tmp/t119/pristine > pre-pristine.txt   # exit 0
$ /tmp/t119/conf-fix  -oracle-probe=up -store=/tmp/t119/pristine > post-pristine.txt  # exit 0
$ cmp pre-pristine.txt post-pristine.txt        ->  no output, BYTE-IDENTICAL
729e75ac7cd4b1e3aca1bc9f2ab7bb9baa80549b525a2aeaaf5a77387fd55a2f  pre-pristine.txt
729e75ac7cd4b1e3aca1bc9f2ab7bb9baa80549b525a2aeaaf5a77387fd55a2f  post-pristine.txt
```

My sha differs from T110's `db047faa…` **for the reason the brief anticipated**, and this is the
answer to how T110 got a byte-identical result anyway:

```
$ sed -n '1,4p' pre-pristine.txt
=== GOLDEN-VECTOR CONFORMANCE — Fineract reference oracle vs Go module ===
    store           /tmp/t119/pristine          <-- the ABSOLUTE store path, T105's defect
    implementation  loanschedule-go
    oracle probe    UP
```

The report embeds the absolute **store** path and nothing else path-shaped — the *repo* root is not
printed, even though the two binaries were run with different working directories inside different
trees. T110 therefore pointed **both binaries at one scratch store** (`/tmp/t110/…`) rather than at
each worktree's own store, so the one path-dependent field was held constant and the comparison
isolates the binary. That is the correct construction, and T105's defect does not weaken it. My sha
is different only because my scratch store is `/tmp/t119/pristine`.

I also verified the code-level claim that the moved assignment is a no-op on every pre-existing path:
`LoadStore`'s two other error returns are `vector.go:824` and `:839`, and **both return `nil` for
`loadErrs`**. So `s.LoadErrors = loadErrs` above the `err != nil` check cannot change any pre-existing
behaviour — not merely "when `err == nil`", as T110 more weakly claimed.

### Claim 5 — the four mutations. **ALL FOUR RE-RUN, ALL FOUR REPRODUCE.**

Full output in §2. The RED leg reproduces too: `store_integrity_test.go` copied **byte-identically**
(`cmp`) into `/tmp/t119/main-tree`, `go vet` rc 0 → **it compiles on `main`**, and:

```
    --- PASS: .../control_unique_store_loads_and_grades          <-- control PASSES on main
        store_integrity_test.go:100: control: 47 vectors, 5576 graded cells, exit 0
    --- FAIL: .../load_store_refuses_and_names_both_files
    --- FAIL: .../run_refuses_before_any_vector_is_graded
    --- FAIL: .../duplicate_across_context_directories_is_refused
    --- FAIL: .../refusal_message_is_deterministic
FAIL	github.com/gerege/nexus/internal/apps/loanschedule/conformance	2.300s
```

The test fails on `main` **by construction**, as claimed: every assertion goes through `LoadStore` and
`Run`, never through `DuplicateCaseIDs`, and all six helpers it uses (`repoRoot`, `storeRoot`,
`copyStore`, `mustRun`, `render`, `NewReplayImplementation`, `SelfTestDir`) exist on `main`.
`sortedKeys` is likewise pre-existing (`report.go:323`).

### Claim 6 — self-caught vacuity. **CONFIRMED CLEAN.**

`grep -rn 't\.Skip|Skipf|SkipNow|testing.Short'` over `store_integrity_test.go` → **one hit, and it is
inside a comment** (`:202`, describing the draft that was removed). No `t.Skip` anywhere else in the
`conformance` package. The anti-vacuity assertions are real and each one is load-bearing:

- `:44` — fixture aborts if `P-00-baseline-6x7pct.json` stops declaring `case_id P-00`.
- `:73`, `:90` — the control `t.Fatal`s on zero vectors and on zero graded cells, so the later
  "0 results / 0 cells / 0 parity" assertions cannot be vacuously satisfied.
- `:66-79` — the control also fails loudly if the **committed** store ever acquires a duplicate.
- `:198-212` — the determinism sub-test derives its three files from `LoadStore`'s own output and
  `t.Fatal`s below three vectors, instead of hard-coding names.
- `:232-234` — asserts the single distinct message actually says `is declared by 2 files` three times,
  so "one distinct message" cannot be satisfied by a message naming nothing.

M0 (unmutated) is green on all five sub-tests; M1 (the check never runs) is red on four. The guard has
been driven red on the real pre-fix bytes and on a no-op mutation. **P-22 satisfied.**

---

## 2. Transcripts

### The five mutations, re-run by me on the fixed tree

| # | mutation | my result |
|---|---|---|
| **M0** | none | `ok … 12.728s` — all 5 sub-tests PASS |
| **M1** | `DuplicateCaseIDs` returns `nil` unconditionally | **RED**, 4 sub-tests; control still PASS |
| **M2** | silently de-duplicate instead of refusing | **RED** — `it loaded 47 vectors and the run would have graded P-00 TWICE`; the dedup restores the *count* and is still caught |
| **M3** | warn only: record a `LoadError`, keep grading | **RED at line 148, not 145** — exit code was 2; caught on `got 48 results, 5623 graded cells, 43 parity passes` |
| **M4** | key on `(context, case_id)` | **RED on exactly one sub-test** (`duplicate_across_context_directories_is_refused`); the other four PASS |
| **M5** *(mine, new)* | delete the outer `sort.Slice` entirely | `refusal_message_is_deterministic` **still PASSES 50/50** → see F-T119-2 |

### Attacks T110 did not run — three of its `[UNVERIFIED]` items are now closed

| probe | `main` | fixed |
|---|---|---|
| **hard-linked** duplicate (T110 UNVERIFIED #5) | `exit 0`, **43 / 5623 PASS** | **`exit 2`**, refused |
| duplicates that **DISAGREE** in content (UNVERIFIED #4) — same `case_id`, different `title` | `exit 0`, **43 / 5623 PASS** — a *different* claim graded as if it were the same case | **`exit 2`**, both paths named |
| two vectors with an **empty** `case_id` | — | **`exit 2`**, legible: `"" is declared by 2 files: loanschedule/E1.json AND loanschedule/E2.json`. No crash. |
| cross-context duplicate **with `-context=loanschedule`** | — | **`exit 0`, 42 parity, no refusal** → **F-T119-1** |

### Post-merge verification (P-24)

`store_integrity_test.go` contains no `git`, no `main:`, no `merge-base` — its baseline is the working
tree's own store, not a moving ref, so the P-24 time bomb is structurally absent. Verified anyway on a
scratch merged tree (`main`'s tree + T110's four files; the two changed-file sets are disjoint, and
`diff -r merged/nexus fix-tree/nexus` → IDENTICAL):

```
go build ./...              rc=0
go vet ./...                rc=0
gofmt -l ./internal      -> internal/apps/loanschedule/contract/contract.go     (the complete list)
go test ./... -count=1   -> ok loanschedule 8.536s ; ok conformance 22.136s ; 0 failures

bash .softhouse/conformance.sh          exit=0   probe = up   42 parity / 5576 cells   VERDICT: PASS
bash .softhouse/conformance.sh --prove  exit=0   PROOFS: 21 passed, 0 failed
```

`gofmt -l` names **exactly** `contract/contract.go` — the expected G-3 state — and **none** of T110's
three source files. Gate G-3 respected; `gofmt -w` was never run.

---

## 3. Ruling — the exit-2 conflation

**The channel is correct. ACCEPT it. But the conflation is real, and the required edit is in the
DRIVER, not in this diff.**

Why exit 2 is right:

1. Exit 2 is **not** the oracle-outage code. It is already an umbrella over "no Go toolchain, no
   implementation to grade, an unreachable oracle, zero parity vectors, an inadmissible vector, a
   refused vector, a load error" (`conformance.sh:14-16`), plus a `PIN.json` failure, a
   capability-registry failure and a harness-declaration defect. The duplicate refusal joins a crowd;
   it does not create the ambiguity.
2. Every alternative is worse, and I verified each from source, not from T110's table:
   `Summary.Errored` needs grading to have run (`grade.go:318-319`); `LoadError` gives exit 2 **without**
   the early return, so the inflated counts still print — that is mutation M3 and it is red; a fifth
   exit code contradicts a four-code table restated in three files and read by every gate write-up.
3. `ZERO VECTORS FOUND` — the *other* way a store lies about its size — is already on this channel.
   Reporting the two the same way, at the same point, with the same code is a consistency gain.

Why the conflation still costs something, and what closes it:

4. `conformance.sh:296` prints `conformance: reference oracle (…) probe = <up|down>` **unconditionally,
   before** handing to the binary. So `probe = up` together with `exit 2` cannot be an oracle outage.
   The disambiguating information is always present in the transcript. **The exit code alone is not
   sufficient; the exit code plus the probe line is.**
5. What is *not* solved is the driver's written rule.
   `.claude/skills/softhouse-program/SKILL.md:108` keys "Park all vector/conformance tasks" on the event
   *Oracle unreachable*, and `:109` states **"Only exit 2 is the oracle-is-down stop condition"** —
   which invites keying on the bare code. `conformance.sh:46-48` says the same in prose. T110 has just
   added a new way to reach exit 2 with `probe = up`, so a driver following `:109` literally would park
   every vector task in the program under a reason that is false and go looking at Fineract instead of
   at the store.
6. **This is exactly the failure the exit-3 interpreter guard was written for** (`conformance.sh:38-52`:
   "a one-word shell-selection typo was indistinguishable from a genuine oracle outage and could park
   every vector task in the program under a reason that was not true"), reappearing one level up. The
   remedy there was not a new exit code either — it was a distinct, unmissable diagnosis plus an
   explicit driver row. The same remedy applies here.

> **Required (follow-up task, not T110):** amend `.claude/skills/softhouse-program/SKILL.md` so the
> parking rule reads **`exit 2 AND probe ≠ up` → park on an oracle reason; `exit 2 AND probe = up` →
> the harness or the corpus is defective, fix it, park nothing on the oracle.** Add a row for it beside
> the existing exit-3 row. This is a one-paragraph doc change and it removes the whole cost of the
> conflation without touching an exit code.

I also note, for the follow-up brief, that the new refusal is **not** in `conformance.sh --prove`'s
proof set (8 `expect` rows; 21 proofs total). T110 was correctly told to stay out of `conformance.sh`
this fire. Once it is free, add `expect 2 "a duplicate case_id in the store"`.

---

## 4. Ruling — the census question

**Verified independently. A census refusal is the right fix, and the charset rule is sound. Two
corrections to the brief T110 wrote for it.**

The shared root reproduces exactly as stated:

- `LoadStore` (`vector.go:820-847`): `os.ReadDir(storeRoot)` then `if !e.IsDir() { continue }` — a
  **symlinked** context directory reports `IsDir() == false` and the whole context is skipped in
  silence. Inner loop: `if f.IsDir() || !strings.HasSuffix(f.Name(), ".json") { continue }` — **one
  level deep**, **byte-exact** suffix.
- `conformance.sh:189`: `find "$STORE_ROOT" -name '*.json' -type f | sort` — **recursive**, does **not**
  follow symlinks, and `-name` is **case-sensitive**.

Measured by me, scratch stores under `/tmp`, both binaries, `-oracle-probe=up`, baseline 42 / 5576:

| probe | `main` | fixed | what `find` sees |
|---|---|---|---|
| E2 symlinked context dir `linkedctx -> loanschedule` | 42 / 5576 exit 0 | 42 / 5576 exit 0 | 49 (invisible to `find` too) |
| E3 nested `loanschedule/sub/NESTED.json` | 42 / 5576 exit 0 | unchanged | **50** — float-scanned, never graded |
| E4 `UPPER.JSON` | 42 / 5576 exit 0 | unchanged | **49** — matched by neither component |
| E5 `p-00` vs `P-00` | **43 / 5623 exit 0** | 43 / 5623 exit 0 | 50 |
| E6 NFC vs NFD `case_id` | **44 / 5670 exit 0** | **44 / 5670 exit 0** | 50 |

E6 reproduces T110's worst number, **44 / 5670**, and the rendering claim holds — the two rows print as
identical glyphs:

```
11:P-00-café                   parity  path_a_e... PASS  47  2
12:P-00-café                    parity  path_a_e... PASS  47  2
```

(The one-column offset is byte-width padding, not a distinguishable identifier. A reader sees two
identical case names and two identical result rows.)

**Ruling: yes, a census refusal — refuse any `.json` under the store root the harness did not load — is
the right fix.** Two corrections to how T110 framed it:

1. **The two enumerations already disagree on the CLEAN store**, so a naive "the counts must match"
   census is red on day one: `find` returns **49**, `LoadStore` loads **47**, because `PIN.json` and
   `capabilities.json` sit at the root and are loaded by `LoadPin`/`LoadCapabilityRegistry` instead.
   The census predicate must be `{everything under the root} − {PIN.json, capabilities.json, README.md}
   == {what LoadStore loaded}`, with that exemption list **explicit and short**, or it will be widened
   later until it exempts the defect.
2. **Implement the census in Go, inside `LoadStore` — not in `conformance.sh`.** A census written in
   the shell can only check the shell's own view of the store, and the defect *is* that the two views
   differ; it would also miss E2 outright, since `find … -type f` cannot see through the symlinked
   directory either. A Go census (`filepath.WalkDir`, with symlinked directories detected and refused
   rather than followed) makes `LoadStore` the single authority on what is in the store, which removes
   the disagreement instead of measuring it. This also means the census inherits the refusal channel
   T110 just built, and the guard for it can be written the same way — through `LoadStore` and `Run`,
   so it compiles and goes red on today's bytes.

**Charset `[A-Za-z0-9._-]`: SOUND.** Measured over the committed store — 47 `case_id`s, **0** outside
the charset, **0** non-ASCII bytes, 47 distinct, and still 47 distinct after case-folding. Verified
across **all 15** historical commits too (§5). It closes F-T110-5 outright (any NFD id carries U+0301,
outside the set) and F-T110-4's realistic form, with no `golang.org/x/text` dependency. One constraint
for the implementer: the charset rule is a property of **one file**, so it must be raised as a
`LoadError`, not routed through `DuplicateCaseIDs` — and it must be driven red on a scratch store
carrying `P-00-café` before it is believed.

---

## 5. Ruling — blast radius. **ANSWERED: NO.**

T110 left this `[UNVERIFIED]` (#7). I audited it. Every commit in this repo's history that touches
`.softhouse/vectors` was reconstructed from its git tree and checked for all five defects — exact
duplicate `case_id` store-wide, case-fold variants, NFC/NFD variants, non-charset ids, and the
enumeration defects (symlink mode `120000`, nested paths, non-exact `.json` suffix). Integer counts and
string comparison only; **no floating point anywhere in the script** (P-25).

```
commits touching .softhouse/vectors: 15

COMMIT     DATE                 FILES  LOAD   IDS  DEFECTS
----------------------------------------------------------
716138c9ff 2026-08-19T17:37:19      7     5     5  clean
e27b584ffb 2026-08-19T17:45:48      8     5     5  clean
2d7bb6fd23 2026-08-19T17:53:32      8     5     5  clean
5a1295453f 2026-08-19T17:54:43      8     5     5  clean
12b957847b 2026-08-19T20:15:53     19    16    16  clean
d289d7bb52 2026-08-19T20:40:27      8     5     5  clean
79233cab70 2026-08-19T20:41:35     19    16    16  clean
9551ec42de 2026-08-19T21:24:38     21    18    18  clean
7cc62e4d50 2026-08-19T23:04:05     37    34    34  clean
a9be32e3da 2026-08-20T08:21:15     37    34    34  clean
0e75bef2b6 2026-08-20T08:53:29     40    37    37  clean
f2ed4bf4a6 2026-08-20T12:01:57     44    41    41  clean
d4bfff1363 2026-08-20T17:39:05     50    47    47  clean
25661fb659 2026-08-20T17:46:41     50    47    47  clean
0c12a35017 2026-08-20T20:19:29     50    47    47  clean

VERDICT: NO commit in history carried any T110-family store defect
```

`LOAD` is what `LoadStore` would enumerate at that commit; `IDS` is the number of **distinct**
`case_id`s among them. **`LOAD == IDS` on every single commit** — the two columns can only agree when
no duplicate exists, so the table is its own check rather than a bare assertion.

Two corroborating facts:

- **The class breakdown closes the arithmetic.** At HEAD, git says 47 loadable vector files, and the
  report says 42 parity + 4 contract-refusal + 1 self-test = **47**. A duplicate would break that
  identity, and it holds.
- **Every "43 parity" figure in the whole program record is a labelled demonstration.** `grep -rl` over
  `.softhouse/` finds exactly three files quoting 43 — `tasks.json`, `.softhouse/reviews/T104-review-of-T90.md`
  and `.softhouse/handoff/…/T104.md` — and in each it is explicitly "on my duplicate store". No genuine
  run ever quoted an inflated number. Every real headline figure in the record (42, 36, 32, 29, 13, 11)
  is at or below the loadable count at the corresponding time.

**Answer: no historical run in this repo was taken on a store carrying any of these defects.** The
program's headline coverage numbers are not retroactively contaminated. What T110 fixed is a defect
the corpus could have acquired at any time, not one it had.

**Scope of that answer**, stated so it is not over-read: it covers **committed** stores only. A run
taken against an uncommitted scratch store, or against a store in a worker's worktree that was never
pushed, is outside git's record and outside this audit. It also does not verify that each historical
handoff's *quoted* numbers were produced by the store at that commit — that is a different question and
I did not ask it.

---

## 6. Findings

### F-T119-1 (P2) — `vector.go:908`: "The key is the `case_id` ALONE, **store-wide**" is false under `-context`

`DuplicateCaseIDs` runs over the vectors `LoadStore` **loaded**, and `LoadStore` filters by
`contextFilter` at `vector.go:830-832` *before* collecting them. So the property is "unique across every
context this run loaded", not "store-wide". Measured:

```
cross-context duplicate (loanschedule/P-00 + _selftest/ZZZ-crossdir.json, both case_id P-00):
  no filter              -> exit=2, refused, 1 DUPLICATE line
  -context=loanschedule  -> exit=0, parity vectors PASS 42, 0 DUPLICATE lines
```

The **behaviour** is defensible — with a filter only one row prints, so no reader is misled about that
run's numbers, and the gate path (`conformance.sh`, unfiltered) is fully covered. The **claim** is not:
it is an unqualified universal in the doc comment that a future reader will rely on, and T110's own
sub-test (3) exercises only the unfiltered path, so nothing would catch the drift.

**Edit:** reword `vector.go:908` to "The key is the `case_id` alone across **every context this run
loads**, not `(context, case_id)`", and add one sentence: "a `-context` filter narrows the set this runs
over; the unfiltered run that `conformance.sh` performs is the one that sees the whole store." No code
change.

### F-T119-2 (P3) — `vector.go:858-860`: the stated reason for the sort's position is not the operative one

The comment says the path key exists "…and the sort runs BEFORE the duplicate check **so that the
refusal itself names its files in a deterministic order**." I mutated it (M5): deleted the outer
`sort.Slice` **entirely** and re-ran the 50-iteration determinism sub-test.

```
  sort.Slice occurrences left: 0
--- PASS: TestDuplicateCaseIDRefusesTheRun/refusal_message_is_deterministic (13.67s)
```

Still 50/50 identical. The refusal message's determinism comes from `sortedKeys(byCase)`
(`vector.go:924`) and `sort.Strings(paths)` (`:929`) **inside** `DuplicateCaseIDs`, which is where
T110's own second doc comment (`:915-917`) correctly locates it. The outer sort's *other* stated reason
— T90's total row order — remains true and the sort must stay. This is a rationale that reads as
load-bearing and is not, in a file whose whole subject is guards that are believed because of what they
say about themselves.

**Edit:** delete the clause "and the sort runs BEFORE the duplicate check so that the refusal itself
names its files in a deterministic order" from `vector.go:858-860`. Optionally replace with: "the
refusal's own ordering does not depend on this sort — see `sortedKeys`/`sort.Strings` in
`DuplicateCaseIDs`." No code change.

### F-T119-3 (P3) — `.softhouse/vectors/README.md:424` still states the weaker, now-wrong rule

```
  "case_id": "...",                  // stable, unique within the context
```

This is the store's own field reference — the artefact a vector author reads. It documents exactly the
`(context, case_id)` key that T110 deliberately **rejected**, and that mutation **M4** is red against.
An author who follows it literally and files `loanschedule/X` alongside `newcontext/X` now earns exit 2
with no warning from the document that told them it was allowed. This is P-21 in its plainest form: the
correction landed where the defect was named and not where the rule is restated. It is the only place in
the repo that restates it (`grep -rn 'unique' .softhouse/vectors/README.md` → this one line).

**Edit:** `unique within the context` → `unique across the whole store, not merely within the context —
a duplicate case_id REFUSES the run (exit 2); see DuplicateCaseIDs in vector.go`. One line.

### Not findings — checked and clean

- **F-T110-6 is genuinely pre-existing, as T110 said.** I drove a *pre-existing* early return on
  `main`'s binary (removed `PIN.json`) and the same sentence prints: `NONE — every invariant assertion
  ran, on cells somebody actually observed` over a run that graded nothing, alongside
  `invariant violations 0`. Not introduced by this diff. It is a true-sounding sentence about a run that
  did no work, and it belongs in the census follow-up.
- **Money.** Nothing in this diff touches monetary arithmetic. `git diff main…branch | grep '^+' |
  grep -E 'float32|float64|math\.'` → no hits. The executable change is a `map[string][]string`, two
  sorts, an `fmt.Errorf` and one moved assignment. The decisive evidence is not inspection: the pristine
  report is **byte-identical** between the two binaries, so every money cell is the bytes `main` emitted.
  My own audit script (§5) is integer- and string-only (P-25).
- **Store integrity.** `git diff -- .softhouse/vectors/` empty on both branches; `PIN.json` and
  `capabilities.json` untouched; every perturbed store was a scratch copy under `/tmp/t119/`.
- **Scope.** Three source files, all under `nexus/internal/apps/loanschedule/conformance/`, plus one
  handoff. No sibling worker's path touched. `.softhouse/conformance.sh` executed, never edited.
- **T105 rebases cleanly.** T110 touches `grade.go` and `vector.go`; T105's defect is the absolute store
  path in `report.go`. Disjoint files; confirmed by the diff.

---

## 7. `[UNVERIFIED]` — mine

1. **Any toolchain, OS or architecture other than `go1.26.6 darwin/arm64` on a case-INSENSITIVE
   macOS filesystem.** `os.ReadDir` ordering, symlink `DirEntry` typing and the E4/E5 case behaviour are
   filesystem and runtime properties. I did not test a case-sensitive filesystem, and I inherit T110's
   caveat unchanged.
2. **T104's own transcript.** I reproduced the *numbers* (43 / 5623 / PASS / exit 0) on my own tree with
   my own binary built from `main`'s bytes. I did not re-run T104's scripts and did not compare
   byte-for-byte with its output.
3. **That the E-series enumeration is complete.** I re-measured T110's eight and added four attacks of my
   own; I have no argument that no thirteenth way exists for a store to lie about its size.
4. **Whether any historical handoff's quoted figures were actually produced by the store at that
   commit.** §5 proves no historical store *could* have inflated a count; it does not re-run history.
5. **Runs taken against uncommitted or never-pushed scratch stores.** Outside git's record and therefore
   outside §5's audit.
6. **`conformance.sh` branches other than the default run and `--prove`.** Both exit 0 on the merged tree;
   I did not exercise `--self-test` independently or any other flag.
7. **The census fix I recommend in §4.** It is a design ruling derived from measurement, not an
   implementation I have built or driven red. The implementer must drive it red before it is believed.

---

## 8. Verdict

**MICRO-FIX** — three edits, all documentation, none behavioural, none blocking a merge:

| edit | file:line | change |
|---|---|---|
| 1 | `nexus/internal/apps/loanschedule/conformance/vector.go:908` | qualify "store-wide" → "across every context this run loads"; note the `-context` narrowing |
| 2 | `nexus/internal/apps/loanschedule/conformance/vector.go:858-860` | delete the false "…so that the refusal itself names its files in a deterministic order" clause |
| 3 | `.softhouse/vectors/README.md:424` | `unique within the context` → unique across the whole store; a duplicate REFUSES the run |

And one edit that is **not** T110's and must be raised as its own task:

| edit | file:line | change |
|---|---|---|
| 4 | `.claude/skills/softhouse-program/SKILL.md:108-109` | the parking rule must be `exit 2 AND probe ≠ up`; `exit 2 AND probe = up` is a harness/corpus defect, park nothing on the oracle |

The fix itself is correct, the guard is real and red on `main`, the mutation set is honest, and the
byte-identical baseline holds. The follow-up brief for the census is set in §4: **a Go-side census in
`LoadStore` with an explicit three-file exemption, plus a per-file `[A-Za-z0-9._-]` charset LoadError**,
each driven red before it is believed.
