# T428 — INDEPENDENT REVIEW OF T421 (T406's six conditions on the accrual vectors)

**VERDICT: `APPROVED WITH CONDITIONS`.**

Four conditions, all **LOW**, each drivable, **none blocking the merge**. Every load-bearing
claim in T421's handoff was re-derived here from a fresh build and a fresh run, and every one
of them held — including the two the brief named as most worth attacking. Two of the four
conditions are the same *class* of defect T421 was created to fix in T391: a committed record
that says something the run did not do.

---

## 0. WHEN I OBSERVED, AND AGAINST WHAT

The reference oracle **edits itself** — T409 has just measured job 9 rewriting 91 pre-existing
journal entries in one minute, so `last_modified_by = 2` is now true of every row in
`acc_gl_journal_entry` and a changed `last_modified` is evidence of nothing. Every figure below
therefore carries the instant I read it.

| | |
|---|---|
| review worktree | `/Users/buv/gerege-nbfi/.claude/worktrees/agent-aba498d1a28770847` |
| review branch | `softhouse/T428-review-t421`, based on `057e8f74` |
| T421 under review | `softhouse/T421-t406-conditions` @ **`ffb52921`** |
| `main` at start | `057e8f74`; **`main` MOVED to `0040cdce` during this review** (T390 + T409 merged, G-22 escalated). `git diff --stat 057e8f74 main -- nexus/ .softhouse/conformance.sh .softhouse/vectors/ .softhouse/guards/` is **EMPTY**, so nothing I graded moved under me. |
| scratch trees | `/tmp/t428-t421tree` (detached @ `ffb52921`), `/tmp/t428-maintree` (detached @ `0040cdce`) — **outside the repo, deliberately** (see F-T428-0 note below) |
| pinned Fineract | `/Users/buv/fineract` @ **`426a23544e8426a38ae43ae404670a0a7e85b9eb`**, verified by `git -C … rev-parse` before a line number was read out of it |
| oracle health | `{"status":"UP","groups":["liveness","readiness"]}` at **`2026-08-28T18:58:47Z`** |
| database | PostgreSQL, container `fineract-db-1`, `fineract_gerege` |
| host UTC span | `2026-08-28T18:58Z … 19:13Z` |

**A note on my own instrument, because it bit me once.** My first baseline run put the scratch
worktree *inside* the review worktree. `guard_no_narrow_catch_in_capture_rigs` walks the whole
directory **recursively, not `git ls-files`**, so it saw the nested checkout's 126 `.java`
capture rigs as NEW and the bar exited 2 — a genuine HARD-guard failure, correctly reported,
caused by me. Both scratch trees were moved to `/tmp` and every figure in this review comes
from the re-run. The failed run is not cited anywhere as evidence. **The guard behaved
correctly; I record it because a reviewer who hides his own red run has no standing to grade
anyone else's.**

---

## 1. THE BAR — RE-BASELINED BY RUNNING, BOTH SIDES

`bash .softhouse/conformance.sh`, `bash` never `sh`, from a clean detached checkout of each
branch. Full transcripts: `out/T428-BAR-01-main-baseline.txt`, `out/T428-BAR-02-t421-tree.txt`.

| | `main` @ `0040cdce` | T421 @ `ffb52921` |
|---|---|---|
| exit | **0** | **0** |
| probe line | PRESENT, `probe = up` | PRESENT, `probe = up` |
| verdict | `PASS (exit 0) — 46 parity vectors … 7884 cells` | identical |
| ledger parity | PASS **10** FAIL 0 | identical |
| ledger oracle-refusal | PASS **6** FAIL 0 | identical |
| divergence | PASS **1** FAIL 0 | identical |
| LEDGER money cells compared | **63 == pinned 63** | identical |
| LEDGER parity vectors | **10 == pinned 10** | identical |
| LEDGER declared exemptions | **0 == pinned 0** | identical |
| deadOccurrences | **108** (at pin) | **108** (at pin) |
| wrong ledger implementations | **15**, all DIED | **16**, all DIED |
| started / finished | `19:03:35Z` / `19:04:55Z` | `19:00:34Z` / `19:01:58Z` |

`out/T428-BAR-04-figure-diff.txt` sorts every pinned/census/verdict line out of both transcripts
and diffs them. **The entire difference is three lines:** the new
`KILLED ledger-wrong-mapping-key-ignored — exit 1, ledger parity FAIL 3 + oracle-refusal FAIL 0`,
`15 → 16` on the population sentence, and the `T316-DEADPATH-CENSUS` row (`corpus`, `resolving`,
`indeterminate`, `prose`) — which are **derived READs, not pins**, and which differ mostly
because `main` is eighteen files ahead of T421's base. `deadOccurrences` — the graded figure —
is **108 on both**. **No pin moved except `EXEMPTION_PIN_LEDGER_WRONGIMPLS`.**

`go build ./...` **0**, `go vet ./...` **0**, `go test -count=1 ./...` **0** on T421's tree
(`out/T428-B01-build-vet-test.txt`; module root `nexus/`, four packages ok).

---

## 2. THE 16th WRONG IMPLEMENTATION — THE 36-CELL DIFFERENCE SET, RE-RUN

I built the conformance binary from T421's tree myself and ran **every** registered wrong
implementation against the full committed corpus (`bin` in `/tmp/t428work`, transcripts under
`/tmp/t428work/arms-t421`). Sixteen arms, sixteen `exit 1`, plus a control `ledger-go` at
`exit 0`.

### The difference set is EXACTLY 36, and nothing else moves

`out/T428-W01-36-cell-difference-set.txt` extracts **every format the report uses** — not just
`X: want …`, but also `X: MONEY want …` and `INVARIANT … VIOLATED`. This matters: three arms
(`netting-totals`, `split-drift`, `truncating`) report **zero** `want` lines and all their
differences in the `MONEY want` form, so a sweep that only matched `: want ` would have
mistaken a money kill for no kill at all.

```
non-money 'X: want' lines : 36
money     'X: MONEY want' : 0
INVARIANT VIOLATED lines  : 0

CELL NAMES (leg index collapsed)
  18 legs[i].gl_account_code
  18 legs[i].gl_account_id
```

**CONFIRMED: 36 cell differences in the whole run, 18 `gl_account_id` + 18 `gl_account_code`,
and not one other cell of any kind** — zero `slot_name`, zero sides, zero leg order, zero money,
zero invariant breaks. `ledger parity PASS 7 FAIL 3`, `oracle-refusal PASS 6 FAIL 0`,
`divergence PASS 1 FAIL 0`, exactly as T421 reports. The claim it grades is therefore **as sharp
as claimed, not blunter**.

**Re-derived from the oracle, not from T421.** My own read-only `SELECT` (§6) shows product 63's
mapping is a bijection with slot 1 → gl **35** / `T388-1000`, and slots 3,4,5,7,8,9 →
37,38,39,41,42,43. `mappingKeyIgnoringPoster` takes `ProductMappings[0]`, which is slot 1, so
every leg must land on 35 — and the transcript reads `got 35` / `got "T388-1000"` on all
eighteen legs, against `want 41,37,38,42,39,43`. The defect and the observation agree
independently of anything T421 wrote.

`ProductMapping` carries **only** `SlotCode` and `GLAccountID`, so the rewrite drops no field;
the code cell moves because the port *resolves* it from the id, which is the whole point.

### The other fifteen still die, and none died for a new reason

I ran all fifteen on `main` as well and compared, per arm, the **verbatim difference lines plus
the FAIL case rows** — not merely the FAIL counts, because two different defects can produce the
same count (`out/T428-W02-15-arms-same-reason.txt`):

```
ARMS COMPARED: identical=16 moved=0 onlyOnT421=1
```

Sixteen byte-identical (fifteen wrong implementations **plus the `ledger-go` control**), zero
moved, one new. **No arm's reason changed.**

### The pin — moved BY NAME, and DRIVEN, not computed

`git diff main...T421 -- .softhouse/conformance.sh` is **one hunk, 1 insertion / 1 deletion**,
`EXEMPTION_PIN_LEDGER_WRONGIMPLS=15` → `=16`, at **`:4476`**, with no surrounding comment
reflowed and no other pin touched. It is in commit **`ef4ae067`**, the same commit as the
`RegisterWrong` call and the three `graded_against` rows.

**I reproduced the P-83 evidence rather than reading T421's transcript of it**
(`out/T428-BAR-03-pin-at-15-drive.txt`). Pin set back to 15 in a scratch tree, bar run,
conformance.sh restored byte-for-byte under a digest-checking trap:

```
pin line now: 4476:EXEMPTION_PIN_LEDGER_WRONGIMPLS=15
line 200: conformance: reference oracle (https://localhost:8443/…/health) probe = up
line 733: conformance: WRONG-IMPLEMENTATION POPULATION 16, PINNED 15.
line 741: conformance: EXIT 2 — no verdict is available. This is NOT a pass.
EXIT=2
conformance.sh RESTORED byte-for-byte (9fdb7291…)
```

**Exit 2 WITH the probe line present, reading `up`.** That is the hard guard firing on a
population the pin does not cover — not an oracle outage — and it is the measurement that makes
`16` a number the run produced rather than a number someone added one to.

The `graded_against` emitter (`bin/80-…py`) **re-counts the transcript** and aborts unless the
cell-name set is exactly `{gl_account_id, gl_account_code}` and the counts are exactly 18/18/36.
I read it; the abort is real and it is not reachable past a wrong count.

---

## 3. THE PROVENANCE TIMESTAMPS — THE ORDERING, VERIFIED TWICE

### Hash before read: verified in the source, and re-derived without T421's digests

In `bin/60-apply-vector-corrections.py`, `http_instant()` reads the bytes, computes
`hashlib.sha256(raw).hexdigest()`, **asserts equality with the cited digest, and only then**
iterates the decoded lines looking for `captured-at-utc:`. Nothing is extracted from the record
before the assert. **The ordering is correct**, and it is the difference between provenance and
decoration.

But the digests in that script are **hard-coded in a Python dict**, not read from the vector.
So I wrote an independent checker that hard-codes nothing
(`/tmp/t428work/bin/t428-provenance-recheck.py`): for every ledger vector it reads
`provenance.request_capture_sha256` **out of the vector**, hashes the file named by
`provenance.request_capture_ref`, **refuses to open the header if the digest does not match**,
and compares the header with `oracle.captured_at` as a string. JSON decoded with
`parse_float=str` / `parse_int=str`.

```
LDG-ACC-01  digest OK   captured-at-utc 2026-08-28T17:10:23Z   == oracle.captured_at   MATCH
LDG-ACC-02  digest OK   captured-at-utc 2026-08-28T17:10:28Z   == oracle.captured_at   MATCH
LDG-ACC-03  digest OK   captured-at-utc 2026-08-28T17:10:28Z   == oracle.captured_at   MATCH
```

All three resolve, and the digest each vector cites is the digest the artefact actually has.
**Every one of the three replaced values is an observation, and I obtained it without trusting
a single constant T421 typed.**

### The sweep — re-run, 0 and 0

`out/T428-TS-01-sweep-t421-AFTER.txt`, T421's own `bin/timestamp-sweep.py` re-run by me at
`2026-08-28T19:06:29Z`:

```
FILES SCANNED: 72
FILES WITH >=1 capture timestamp: 63   timestamps found: 63
FILES WITH NONE (listed, not skipped): 9
   PIN-ledger.json, PIN.json, _selftest/SELFTEST-01…, capabilities-ledger.json,
   capabilities.json, loanschedule/REFUSE-01…04
ROUND-HOUR (mm:ss == 00:00): 0
FUTURE (> run instant): 0
VERDICT: CLEAN
```

**72 files, every key containing `captur` anywhere in the tree, the 9 carrying none NAMED, and
0/0.** The comparison really is string-only: `v[14:19] == "00:00"` for round hour and a
lexicographic compare of `Z`-suffixed ISO-8601 strings for future. No value is parsed as a
number. **No vector's `captured_at` postdates its own capture** — the three that did now read
`17:10:23Z` / `17:10:28Z` / `17:10:28Z` against captures taken at those same instants.

My independent raw-token cross-check (same file, §2) found **23 distinct `…T..:..:..Z` tokens**
in the store, 15 of them second-precision. That reconciles exactly with T421's reported "12
distinct instants": T421 measured that **before** its own edits, and its edits introduced three
new observed instants (`17:10:23Z`, `17:10:28Z`, `18:33:42Z`). 12 + 3 = 15. See F-T428-6 for
the one token the raw grep still finds.

---

## 4. ELEVEN ADMISSION DRIVES — RE-NEUTERED, AND THEN ATTACKED HARDER

### T421's drive, re-run verbatim

`out/T428-A01-neutering-rerun.txt`, `sh bin/50-red-drive-admission-arms.sh` on T421's tree:

```
admit.go original sha256: a02a9d41203da818cba448ca8cb45ba1cf11b15ae40d0ed732a21d2c0e7ca2fc
neutered 12 reason fragment(s) across 11 branches
go test exit: 1
sub-tests FAILED with the branches neutered: 11   (arms 1..11)
sub-tests PASSED with the branches neutered:  1   (the ADMITTED control)
admit.go RESTORED byte-for-byte (a02a9d41…)
```

**Reproduced exactly.** Eleven arms red, control green, restore verified.

### And then a strictly stronger drive of my own, because T421's is not the sharpest available

T421 neuters **all eleven at once**. That shows the eleven arms collectively depend on the
eleven messages; it does not show that **arm *k* depends on branch *k***. So I neutered **one
branch at a time**, eleven separate builds, and required *exactly one* sub-test to fail and it
to be that branch's own arm (`out/T428-A02-per-arm-neutering.txt`):

```
arms that died on EXACTLY their own branch: 11
arms with an UNEXPECTED outcome:            0
admit.go final sha256: a02a9d41…  (original a02a9d41…)
```

**Eleven for eleven.** No arm survives its own branch's neutering (so none is decoration,
**P-98**), and no arm dies on somebody else's (so none is mis-bound) — a property T421's
simultaneous drive could not have distinguished.

### The ELEVENTH branch: verified in source, and driven by DELETING it

`admit.go:288` really does carry a branch T406's ten omit:

```go
if m.GLAccountID <= 0 {
    add("request.product_mappings[%d].gl_account_id is %d", i, m.GLAccountID)
    continue
}
if !inChart[m.GLAccountID] { … off the chart … }
```

The `continue` skips the off-the-chart check, exactly as T421 says. I did not take that on
trust: I **deleted the four-line branch** and re-ran (`out/T428-A03-arm11-branch-deleted.txt`):

```
--- PASS: …/the_committed_accounting-path_vector_is_ADMITTED
--- PASS: …/1 … 10   (all ten)
--- FAIL: …/11._a_mapping_row_with_a_NON-POSITIVE_gl_account_id_REFUSES
    reasons = [request.product_mappings[0] resolves slot 1 to GL account 0, which is NOT in
               request.accounts. …]
```

Still **refused** — but by the **off-the-chart** reason. **"The right refusal for the wrong
reason", measured.** T421's eleventh-branch claim is not merely true, it is now demonstrated,
and arm 11 is the only thing in the corpus that would catch it. `admit.go` restored
byte-for-byte after every drive; `git status` in the scratch tree shows no modification to it.

**`git diff main -- admit.go` is 0 lines.** T421 changed no rule; it added a test file. The
T416 disjointness claim holds.

---

## 5. THE FOUR CORRECTIONS TO ITS OWN REVIEWER — ADJUDICATED, NOT ACCEPTED

| T421's correction | T406 said | T421 says | **T428 adjudication** |
|---|---|---|---|
| cells moved by the 16th | 12 + 12 | **18 + 18** | **T421 UPHELD.** Re-run from a fresh build: 36 lines, 18 + 18, and my extractor also covers the `MONEY want` and `INVARIANT` formats T421's did not need. Three vectors × six legs. T406's cardinal was wrong; the kill is the same. |
| vectors that predate T391 | seven | **fourteen** | **T421 UPHELD.** Independent census of all 17 ledger vectors (`out/T428-W03-vector-census.txt`): 3 carry `product_mappings` (13 rows each), **14 carry zero** — 7 parity, 6 oracle-refusal, 1 divergence. T406's "seven" counted only the parity class. |
| admission branches | ten | **eleven** | **T421 UPHELD**, and now driven by deletion (§4). The branch is at `admit.go:288` and is absent from T406's list. |
| T406's review on `main` | cited as on `main` | **was not** | **T421 UPHELD, and already actioned.** It was unmerged at `8c7d9cee` when T421 read it. `main` has since merged it (`d365cd5e` / `057e8f74`, whose message says so in terms), so `.softhouse/reviews/t406-review-t391/REVIEW.md` **is** on `main` now and I read it from there. |

**A fifth correction T421 makes in passing is also right.** T406 gives the `CashAccountsForLoan`
constants as `:38-61`; `:38` is blank and they are `:39-61`. I re-read the pinned checkout at
`426a23544` myself: `:37` is the enum declaration, `:39-61` the constants (values 1-6 and 10-26,
`FEES_RECEIVABLE(25)` at `:60`, `PENALTIES_RECEIVABLE(26)` at `:61`, **no 7, 8 or 9**), `:79-89`
is `intToEnumMap` + `fromInt` with no constant in it, `:95` is `AccrualAccountsForLoan` with
`INTEREST_RECEIVABLE(7)` `:103`, `FEES_RECEIVABLE(8)` `:104`, `PENALTIES_RECEIVABLE(9)` `:105`.
**F-T406-3 is correctly closed, and closed in the durable form** — the range is deleted and the
citation names the symbol. `slots.go:170` still cites `:79-89` and is **correct**, because it is
describing `fromInt`. The two residual out-of-grant occurrences T421 flags are real; there is a
third, `.softhouse/tasks.json`, which is T421's own brief quoting the bad range in order to
name it, and is driver-owned.

**F-T406-4 and F-T406-5 also check out live.** Each vector now names its own first amount
(`24000.0` / `20195.38` / `12356.34` against tokens `24000.000000` / `20195.380000` /
`12356.340000` — confirmed against the database in §6), and my own read-only query returns
**exactly the ten** cash products `22 23 27 46 54 55 56 57 58 60` at slot 1 plus accrual product
**28** at slot 9 — eleven rows, ten cash products, which is what the corrected prose now says.

---

## 6. NO ORACLE STATE MOVED — VERIFIED INDEPENDENTLY

* **No `curl`, no write verb, anywhere in T421's rig.**
  `grep -rnE '\-X *(POST|PUT|DELETE|PATCH)|--data|-d @|curl|INSERT |UPDATE |DELETE |TRUNCATE |ALTER |CREATE '`
  over `.softhouse/capture/t421-t406-conditions/` returns **only** the guard's own keyword list,
  its RED-drive fixtures, and prose inside bar transcripts. There is no `curl` at all.
* **I drove the read-only guard RED myself** (`out/T428-G01-readonly-guard-red-drive.txt`, at
  `2026-08-28T19:12:10Z`): five write shapes — `UPDATE`, `DELETE`, `INSERT`, `DROP`, and an
  `UPDATE` hidden behind a `--` comment — all **REFUSED at exit 2 with nothing executed**, and a
  bare `SELECT 1;` **ADMITTED at exit 0**. The guard discriminates; it does not refuse
  everything.
* **The counters, read by me through that guard at `2026-08-28T19:12:20Z`**
  (`out/T428-S01-counters.txt` / `.psql`):

```
command_source 379 / max id 379     journal entries 109 / max id 113     loan txns 24 / max id 34
```

  **Identical to T421's readings at `18:33:42Z` and `18:51:25Z`, and to T406's before them.**

* **No promoted account moved.** gl 41/42/43 and 37/38/39 carry **six** journal entries each;
  gl 18, 22, 40, 44, 45, 46, 47 carry **zero**; gl 16 carries **21**. Product 63's mapping is
  still the 13-row bijection 1→35 … 13→47.
* **The amounts as stored**, read as `::text` and never as a float:
  `L29` 24000.000000 ×2 / 2500.000000 ×2 / 1200.000000 ×2; `L30` 20195.380000 ×2 / …;
  `L32` 12356.340000 ×2 / …. **Six legs × three transactions = the 18 amount tokens** that
  cannot be byte-preserved by an ordinary JSON renderer, which is T421's informational
  explanation of the READ census `+18` — and my `main` baseline prints exactly
  `T391-A01…x6; T391-A02…x6; T391-A04…x6` inside its `104 … NOT byte-preserved` line. **Counted,
  not reasoned.**
* **I wrote nothing.** Every database access in this review went through T421's write-refusing
  wrapper; the only files I created inside a Fineract-adjacent path are three read-only capture
  records under the scratch worktree's `out/`, which are untracked and were copied out.

**Per the T409 caveat:** I make no claim from `last_modified`. The counters and the per-account
leg counts are the evidence, and they are unchanged across four independent readings spanning
`18:16Z` (T406) → `19:12Z` (me).

---

## 7. FLOAT SWEEP — WIDER REGEX, AND NOTHING BECAME A FLOAT IN THE CHECKING

`out/T428-F01-float-sweep.txt`, over **all 6,078 added lines** of the `main...T421` diff.

| pattern | hits | adjudication |
|---|---|---|
| T421's own regex (`float64\|float32\|big.Float\|ParseFloat\|FormatFloat\|%f\|Double\|math.Round`) | **1** | the handoff sentence **quoting the regex itself** |
| float verbs `%g %e %E %.Nf` | **0** | — |
| constructors `float( \| Atof \| json.Number \| strconv.Parse \| decimal. \| big.Float \| complex64/128` | **2** | one is a comment saying *"this script does not call float()"*; one is the header of the deliberately-labelled counterexample artefact (F-T428-7) |
| any `float` token, any case | 101 | all prose, `parse_float=str`, or bar output |
| decimal literals / exponent literals | 158 / 0 | all inside prose, oracle text tokens, or bar transcripts |
| **added non-comment GO lines** | **178** | **ZERO float-shaped hits** |

**`go vet` clean, and the bar's own guards agree**: *0 forbidden identifiers, 0 floating-point
or imaginary LITERALS, 0 forbidden imports* over 66 `.go` files, and *CENSUS float-shaped tokens
… ALTERED by a binary-double round trip 0*.

**And the money itself, checked by integer string surgery**
(`out/T428-F02-money-integer-check.txt`). JSON decoded with `parse_float=str` **and**
`parse_int=str`, integrality decided by `str.isdigit()`, residue read as the last two
*characters*. `int()`, `float()` and `Decimal()` are never called:

```
*_minor leaves inspected   : 123
   integer or absent       : 123
   NOT integer minor units : 0
residues: 00 x24 · 62 x15 · 25 x10 · 34 x6 · 38 x6 · 37 x5 · 24 x3 · 42 x2 · 58 x2 · 82 x2 · 76 x1
VERDICT: CLEAN
```

**Residues 38 and 34 are present, six each** — the ACC-02 and ACC-03 minor-unit tails — and
every one of them lives in an integer string. **`100.125` occurs in exactly three places in the
whole ledger store**, and all three are raw oracle *text* fields
(`request.legs[0..1].amount_major_text`, `oracle_accepted.observed_amount_texts[0]` on
`LDG-DIV-01`). **No `int64` holds `100.125`, and no `*_minor` field is anything but digits.**
The sibling `*_major_text` fields are strings by design — T186 §7 A4 forbids re-scaling an
oracle observation — and are reported separately rather than counted as offenders; my first
pass wrongly flagged all 115 of them and is superseded by the scoped one.

---

## FINDINGS

### F-T428-1 — **LOW** — the RED-drive script and the handoff both say the mutation lived in a "scratch copy". It lived in the working tree.

`bin/50-red-drive-admission-arms.sh` sets `ADMIT="$ROOT/nexus/…/admit.go"` and mutates **that
file in place**; the `mktemp` copy is the *backup*, not the thing edited. Its own header says
*"neuter the eleven `add(...)` calls in admit.go IN A SCRATCH COPY"*, and T421's handoff §4
repeats *"the RED drive's mutation of `admit.go` lived for the length of one `go test` inside a
scratch copy"*. It did not: it lived in the real `admit.go` for the length of one `go test`,
protected by a `trap` and a digest check that I re-verified fires
(`out/T428-A01-neutering-rerun.txt` ends `RESTORED byte-for-byte`).

Nothing was lost and no commit captured a neutered file — I checked `git status` in the scratch
tree after every drive of my own. But a record that says the working tree was never touched,
when it was, is precisely the class of statement this whole task existed to remove from T391's
artefacts, and the window is real: a concurrent `go build`, a `git add -A`, or a killed shell
during that second would see or freeze a neutered `admit.go`.

**DRIVE:** reword the script header and handoff §4 to *"mutates `admit.go` IN PLACE and restores
it from a backup under a digest-checking `trap`"*; or make the description true by copying the
module to a temp dir and running `go test -C` there. Either closes it; the first is honest and
costs one line.

### F-T428-2 — **LOW** — two committed evidence transcripts disagree with the committed registration on the exact cardinal T421 corrected in T406.

`out/T421-W01-list-implementations.txt:10` and `out/T421-W02-arm-mapping-key-ignored.txt:247`
both print the `RegisterWrong` description as:

> *"It is INERT on all **thirteen** vectors that predate T391, which carry no product_mappings"*

while the shipped string in `impl.go` reads **FOURTEEN** *(7 parity, 6 oracle-refusal, 1
divergence)* — and fourteen is what I counted (§5). Both artefacts and `impl.go` are in the same
commit `ef4ae067`, so the text was corrected **after** the captures and the captures were not
re-taken. The result: the committed RED evidence for the sixteenth implementation states a
cardinal that is (a) superseded and (b) **wrong**, in a task whose §2 is a correction of exactly
that failure mode one artefact over.

The kill is unaffected — I re-ran it and measured 18 + 18 — so this is a record defect, not a
behaviour defect.

**DRIVE:** re-run `-list-implementations` and the `-ledger-impl ledger-wrong-mapping-key-ignored`
arm on the final tree and recommit both transcripts. The check that it stayed closed is a `diff`
of the description line in `T421-W01-list-implementations.txt` against the binary's current
`-list-implementations` output; they must be byte-identical.

### F-T428-3 — **LOW** — the neutering needle for arm 11 matches a branch outside the eleven, and the script's own "12 across 11" is unexplained.

`50-red-drive-admission-arms.sh` neuters `gl_account_id is %d`, which occurs **twice** in
`admit.go`: at `:288` (arm 11's branch) and at `:326`, in the unrelated `contra_gl_account_id`
branch, whose message contains it as a substring. The script prints *"neutered 12 reason
fragment(s) across 11 branches"* and neither it nor the handoff accounts for the twelfth. So a
drive that declares an extent of eleven branches silently mutates a twelfth.

The collateral is harmless **here** — I re-drove arm 11 with the tighter needle
`].gl_account_id is %d`, which matches one place, and arm 11 still dies alone
(`out/T428-A02-per-arm-neutering.txt`) — but the same substring relation means arm 11's *test*
needle, `"gl_account_id is 0"`, would also be satisfied by a contra-account reason reading
`contra_gl_account_id is 0`. Today no fixture can produce that; tomorrow's might.

**DRIVE:** tighten the script's needle to `].gl_account_id is %d`, assert
`n == len(NEEDLES)` so an over-broad needle aborts the drive instead of being counted, and
tighten arm 11's test needle to `product_mappings[0].gl_account_id is 0`.

### F-T428-4 — **LOW** — F-T406-1 is closed by a one-shot script, not by a guard, in a task that invokes P-45 to justify registering the sixteenth implementation.

T421's argument for `ledger-wrong-mapping-key-ignored` is that *"a throwaway probe is not a
guard (P-45)"* — T406 proved the gap by hand, so T421 registered it permanently. The same
reasoning is not applied one finding over: `bin/timestamp-sweep.py` lives in a capture rig,
is wired into nothing, and `.softhouse/conformance.sh` would not notice the **seventeenth**
synthesised `captured_at`. The store is clean today (0 round-hour, 0 future, verified §3); it is
held that way by nobody.

T406's DRIVE asked only for the values to be corrected and the bar re-run, so **this is not a
failure to close the condition** — it is the asymmetry the review exists to name.

**DRIVE:** move the sweep to `.softhouse/guards/check-vector-capture-instants.sh`, wire it into
the bar with a probe line (presence before value, P-84), and give it a RED arm: plant a
round-hour and a future `captured_at` in a scratch copy of the store and require the guard to
refuse, with a clean control that stays green.

### F-T428-5 — **INFORMATIONAL** — fourteen of the seventeen ledger vectors carry a `captured_at` that cannot be re-derived from the artefact they cite.

The three ACC vectors now resolve end-to-end (§3). The other fourteen name a `.req` file as
`provenance.request_capture_ref` — and those files are **bare JSON request bodies with no
headers at all**, so there is no `captured-at-utc` in them and the method T421 established
cannot be applied. Their `captured_at` values are plausible second-precision instants and none
is round-hour or future, but none is *checkable*. This predates T421 entirely and is outside its
grant. Recorded so the next task does not mistake "the sweep is clean" for "every instant is
re-derivable".

**DRIVE:** for each of the fourteen, either point `request_capture_ref` at a record that carries
the instant, or state in `provenance.citation` that the instant is not re-derivable from the
cited artefact and name where it did come from.

### F-T428-6 — **INFORMATIONAL** — `2026-08-29T09:00:00Z` still occurs once per ACC vector, now as prose.

The corrected `provenance.citation` names the old value in order to say what was wrong with it,
so a raw-token grep over `.softhouse/vectors` still returns a future round hour. T421's sweep is
scoped to keys whose **name** contains `captur`, and `.provenance.citation` is not one, so the
sweep correctly reads 0/0 — but T421's handoff cites a raw `grep -rhoE` cross-check as
corroboration, and a later reader running that same grep on the current store will get a hit and
have to work out why. Not a defect; a trap for the next reader.

**DRIVE:** one clause in the handoff, or in the guard of F-T428-4, distinguishing an *asserting*
timestamp from a *quoted* one — the same distinction T421 already drew for the
`AccountingConstants.java:79-89` string.

### F-T428-7 — **INFORMATIONAL, ADJUDICATED NOT A VIOLATION** — T421 did call `float()` once, deliberately, and said so.

`out/T421-F04-float-renderings.txt` records `repr(float(token))` for the three amount tokens, to
obtain the wrong answers the corrected sentences warn about (`20195.38`, `12356.34`). I confirm
this is **not** a non-negotiable breach: the values are produced only to be *named as wrong*,
they are never used as money, never compared with a money cell, never stored in a `*_minor`
field, and the artefact's header says all of that. The resulting strings sit in `_note` prose,
which `guard_no_float_in_vectors` passes over correctly — bar exit 0 with the strings in place.
Recorded because a future sweep will find `float(` in a capture rig and should find this
adjudication next to it rather than re-litigate it.

---

## WHAT I DID NOT DO

* **I did not write to the reference oracle.** Every query went through the write-refusing
  wrapper, which I drove RED first. No promoted account moved; counters identical at `19:12:20Z`
  to T421's and T406's.
* **I did not modify T421's branch**, and nothing in this review is committed to it. Both scratch
  worktrees are detached checkouts under `/tmp`; the pin edit and every `admit.go` mutation were
  restored under digest-checking traps and re-verified.
* **I did not merge anything to `main`.**
* **I did not inherit a figure.** Every number above came from a run I started, except where the
  table explicitly attributes one to T406 or T421 in order to adjudicate it.

## FOR THE DRIVER

1. **Merge T421.** All six of T406's conditions are closed, the two hardest claims reproduce
   exactly, and the four findings above are record-quality, not correctness.
2. `git merge-tree --write-tree main softhouse/T421-t406-conditions` exits **0** against the
   *current* `main` (`0040cdce`), which moved twice during T421 and once more during this
   review without touching `nexus/`, the bar, the vectors or the guards.
3. **`main` is now three moves stale in the `EXEMPTION_PIN_LEDGER_WRONGIMPLS` comment block**
   (T360 13→14, T391 14→15, T421 15→16 all unnarrated). T421 correctly refused to widen its own
   grant to fix it. It needs a task with a `conformance.sh` comment grant.
4. **The T406-review-on-`main` problem is fixed** — it is on `main` now. T421's complaint was
   valid when it was written.
