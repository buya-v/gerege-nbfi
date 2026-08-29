# T422 — INDEPENDENT review of T416 (`softhouse/T416-t405-conditions`)

STATUS: COMPLETE. VERDICT: APPROVED WITH CONDITIONS (5 — two MINOR, three LOW; none blocks the merge).

Reviewer: T422, branch `softhouse/T422-review-t416`.
Subject: `softhouse/T416-t405-conditions`, 10 commits, tip `9f4fc247`. Merge-base with `main` is `e0eb4fe2`; `main` advanced from `e13966dc` to `e864dd3d` (T421 + T428) during this review, and section 7 uses the LATER value.
Scratch tree for every drive: `/tmp/t422/t416` (a `git clone --shared` of the repo, checked out at
T416's tip) — **outside the repository**, as T422's brief requires, so
`guard_no_narrow_catch_in_capture_rigs`'s recursive walk cannot see it.

Honesty convention: every material claim below is marked `[VERIFIED: …]` with the command or source
that produced it, or `[UNVERIFIED]`. Nothing here is inherited from T416's handoff without being
re-run.

---

## 1. F-T405-5 — THE MONEY VERDICT SENTENCE. CAUSE RE-DERIVED INDEPENDENTLY.

### 1.1 The cause, derived from source before reading T416's account of it

`ExitCode()` is `nexus/internal/apps/loanschedule/conformance/grade.go:288`. On `main` it reaches 1
through **two** structurally separate arms [VERIFIED: `grade.go:289-302` on `main`]:

```go
if s.ParityFail+s.ContractFail+s.SelfTestFail > 0 || s.InvariantViolations > 0 { return 1 }
...
if s.Ledger != nil {
    if s.Ledger.ParityFail+s.Ledger.RefusalFail > 0 || s.Ledger.InvariantViolations > 0 { return 1 }
```

The exit-1 verdict sentence on `main` is `report.go:621-622` and reads **only the first arm's
fields** [VERIFIED: `main:report.go:620-622`]:

```go
case code == 1:
    p("VERDICT: FAIL (exit 1) — %d mismatched vector(s), %d invariant violation(s).",
        s.ParityFail+s.ContractFail+s.SelfTestFail, s.InvariantViolations)
```

`s.Ledger.ParityFail`, `s.Ledger.RefusalFail` and `s.Ledger.InvariantViolations` contribute to none
of those four terms, and nothing else in the arm mentions the ledger. So any run reaching exit 1
**solely** through the ledger arm printed `— 0 mismatched vector(s), 0 invariant violation(s)`.
**T416's stated cause is correct and I re-derived it from the two files without using its account.**

### 1.2 The `:595` / `:592` line-number adjudication — CONFIRMED

`[VERIFIED: git show f952b5d2^:nexus/internal/apps/loanschedule/conformance/report.go]` — on
**pre-T397** `main` (T397 is `f952b5d2`):

| line | content |
|---|---|
| **592** | `p("         This means \"matches the reference oracle …\")` — the **exit-0** prose line, which is what T397 was tasked with and what T397 fixed |
| **594** | `case code == 1:` |
| **595** | the defective `VERDICT: FAIL (exit 1) — %d mismatched vector(s)…` sentence |

So the defect site is `:595`, not `:592`, on the tree those numbers were taken from, and T398's
attachment of the symptom to `:592` was wrong. **T405's correction and T416's confirmation of it both
hold.** T416 additionally declines to hard-code the number in the code comment and cites the site by
name (`the case code == 1: arm of WriteReport's verdict switch`) — correct, because on **today's**
`main` the same line is `:621-622`, i.e. the number has already moved twice
[VERIFIED: `main:report.go:620-622`]. Nothing in the T416 diff cites a line number that has rotted.

### 1.3 The corpus drive, re-run from scratch

Two binaries built by me in `/tmp/t422/t416`, differing **only** in `report.go`
(`/tmp/t422/conf-after` from T416's tip; `/tmp/t422/conf-before` from the same tree with
`git checkout main -- …/report.go` and nothing else — `git status --porcelain` showed exactly that
one file modified, and the tree was restored clean afterwards). Correct `ledger-go` port, **no
`-ledger-impl` flag**, `-oracle-probe=up`. Script: `/tmp/t422/drive.sh`. Store reverted with
`git checkout -- .softhouse/vectors` between arms; `store clean: 0 dirty` at the end.

**Unmutated control — both binaries green** `[VERIFIED: /tmp/t422/out/control-{BEFORE,AFTER}.log]`:

```
BEFORE  exit=0   ledger parity PASS 10 FAIL 0  | VERDICT: PASS (exit 0) — 46 parity vectors …, 7884 cells compared.
AFTER   exit=0   ledger parity PASS 10 FAIL 0  | VERDICT: PASS (exit 0) — 46 parity vectors …, 7884 cells compared.
```

**T416's three mutation classes, reproduced exactly** `[VERIFIED: /tmp/t422/out/{glcode,amountminor,totals}-{BEFORE,AFTER}.log]`:

| mutated cell | class | ledger census | BEFORE | AFTER |
|---|---|---|---|---|
| `legs[0].gl_account_code` 10300→10399 | structural | `parity PASS 9 FAIL 1` | `exit 1 — 0 mismatched vector(s)` | `exit 1 — 1 mismatched vector(s)` |
| `legs[0].amount_minor` 10000025→10000026 | **MONEY, −1 minor unit** | `parity PASS 9 FAIL 1` | `exit 1 — 0 mismatched vector(s)` | `exit 1 — 1 mismatched vector(s)` |
| `total_debits_minor` 12500062→12500063 | **MONEY, −1 minor unit** | `parity PASS 9 FAIL 1` | `exit 1 — 0 mismatched vector(s)` | `exit 1 — 1 mismatched vector(s)` |

The AFTER report on the money arm names the cell with its margin
`[VERIFIED: /tmp/t422/out/amountminor-AFTER.log]`:

```
LDG-01-manual-je-3leg-minor-units   parity   ledger_rest_posting   FAIL   18 cells (5 money)
    legs[0].amount_minor: MONEY want 10000026, got 10000025 (margin -1 minor units)
```

T416's post-merge census figures (`PASS 9 FAIL 1`, control `PASS 10 FAIL 0`) reproduce exactly.

### 1.4 THE CENTRAL CHECK — IS THE COUNT RIGHT, OR MERELY NON-ZERO?

This is the check T422 exists to perform, and T416 did **not** perform it: every one of its corpus
arms mutates exactly one vector, so "1" is indistinguishable from a hard-coded 1 or from `min(n,1)`.
I mutated **two** and then **three** money cells in **distinct** vectors, one minor unit each
`[VERIFIED: /tmp/t422/drive.sh PART B, /tmp/t422/out/{two_money,three_money}-{BEFORE,AFTER}.log]`:

| mutation | true count | census | BEFORE says | AFTER says |
|---|---|---|---|---|
| `LDG-01.legs[0].amount_minor` +1 | 1 | `ledger parity PASS 9 FAIL 1` | `0` | **`1`** |
| + `LDG-02.legs[0].amount_minor` 27045058→27045059 | 2 | `ledger parity PASS 8 FAIL 2` | `0` | **`2`** |
| + `LDG-03.legs[0].amount_minor` 88954942→88954943 | 3 | `ledger parity PASS 7 FAIL 3` | `0` | **`3`** |

and the per-vector rows in the n=3 report name all three
`[VERIFIED: /tmp/t422/out/three_money-AFTER.log]`:

```
LDG-01-manual-je-3leg-minor-units        parity  ledger_rest_posting  FAIL  18 cells (5 money)
LDG-02-repayment-split-4leg-minor-units  parity  ledger_rest_posting  FAIL  23 cells (6 money)
LDG-03-overpayment-4leg-minor-units      parity  ledger_rest_posting  FAIL  23 cells (6 money)
ledger parity           PASS 7    FAIL 3
```

**The reported count equals the true count at n = 1, 2 and 3, and equals the census's own
`FAIL` figure in each case. It is not merely non-zero.**

### 1.5 The ADDS-not-REPLACES claim, checked at CORPUS level as well as unit level

T416's control for "adds rather than replaces" is four loanschedule-only **unit** arms. That is a
weaker control than it sounds, because those arms construct a `Summary` by hand. I drove it on the
**real corpus** instead `[VERIFIED: /tmp/t422/mixed2.sh, /tmp/t422/out/{lsonly2,mixed2,noledger2}-*.log]`.

To produce a genuine loanschedule parity FAIL I had to mutate `P-00.expect.periods[1]` **consistently**
— `interest_minor`, `interest_major_text`, `observed_total_due_minor` and
`observed_total_interest_minor` together. My first attempt moved only `interest_minor` and the
harness correctly refused it as **INADMISSIBLE**, not FAIL:
`expect.periods[1].interest_minor is 59 minor units but the oracle's wire text "0.58" converts to 58:
a transcription error` `[VERIFIED: /tmp/t422/out/lsonly-AFTER.log]`. That is an unlooked-for but real
piece of evidence that the loanschedule admission path is doing its job, and it is recorded here
because it changed my method.

| arm | true state | BEFORE | AFTER |
|---|---|---|---|
| **A** loanschedule-only, 1 vector | LS 1 mismatch + 1 invariant, LEDGER 0 | `— 1 mismatched vector(s), 1 invariant violation(s).` | `— 1 mismatched vector(s), 1 invariant violation(s).`<br>`LEDGER 0 mismatch(es), 0 invariant violation(s) \| LOAN SCHEDULE 1 mismatch(es), 1 invariant violation(s).` |
| **B** MIXED: 1 loanschedule + 2 ledger | LS 1 + LEDGER 2 = **3** | `— 1 mismatched vector(s)` ← **undercount by 2** | `— 3 mismatched vector(s), 1 invariant violation(s).`<br>`LEDGER 2 mismatch(es), 0 invariant violation(s) \| LOAN SCHEDULE 1 mismatch(es), 1 invariant violation(s).` |
| **C** 2 loanschedule, `-context=loanschedule` (no ledger half) | LS 2, ledger absent | `— 2 mismatched vector(s), 2 invariant violation(s).` | `— 2 mismatched vector(s), 2 invariant violation(s).`<br>`no ledger half ran in this configuration, so this counts LOAN SCHEDULE only.` |

**Arm A is the control T416's unit arms were reaching for and it holds on the real corpus: the
loanschedule figure is byte-identical BEFORE and AFTER, so the ledger figures were ADDED, not
substituted.** Arm B is the arm nobody drove: the total is the **sum** of both halves and the split
line attributes each to the correct half, including the invariant-violation column
(`LS 1, LEDGER 0`). Arm C confirms the nil-ledger branch prints the "did not run" sentence rather
than a silent zero, and does not change the loanschedule count.

**No defect found in this area.** The count is right at every n I could construct, the split is
right, and the nil case is distinguished from the zero case.

---

## 2. THE UNIT DRIVE — 8 RED / 0 AFTER, AND THE FOUR CONTROL ARMS. CHECKED HARD.

Run by me against **pre-fix `report.go` bytes** and then against T416's, in the same tree, restoring
cleanly between the two (`/tmp/t422/units.sh`, transcripts `/tmp/t422/out/units-{RED,GREEN}-report.log`).

**RED, against `main`'s `report.go`** `[VERIFIED: /tmp/t422/out/units-RED-report.log, go test exit 1]` —
leaf subtests, `verdict_fail_ledger_test.go`:

| subtest | RED before | after |
|---|---|---|
| `TestTheExitOneVerdictCountsTheLedgerHalf/ledger_parity_fail_only` (**the MONEY row**) | FAIL | PASS |
| `.../ledger_refusal_fail_only` | FAIL | PASS |
| `.../ledger_divergence_fail_is_counted_once` | FAIL | PASS |
| `.../ledger_invariant_violation_only` | FAIL | PASS |
| `.../ledger_parity_and_refusal_and_invariant` | FAIL | PASS |
| `TestTheExitOneVerdictStillCountsTheLoanScheduleHalf/both_halves` | FAIL | PASS |
| `TestTheExitOneVerdictSaysWhichHalfFailed/ledger_only` | FAIL | PASS |
| `TestTheExitOneVerdictSaysWhichHalfFailed/no_ledger_half_says_so` | FAIL | PASS |
| **8 leaf subtests RED, 0 after** | | |
| `.../loanschedule_parity_only` | **PASS** | **PASS** |
| `.../loanschedule_contract_only` | **PASS** | **PASS** |
| `.../loanschedule_selftest_only` | **PASS** | **PASS** |
| `.../loanschedule_invariants_only` | **PASS** | **PASS** |

**T416's "8 RED before, 0 after" reproduces exactly, and so do the four loanschedule-only control
arms green in both directions.** The RED run also turns one further arm red —
`TestTheExitZeroVerdictNamesTheRecordedDivergences/a_zero_graded_divergence_run_does_not_claim_the_store_has_none`
— which belongs to F-T405-6, not F-T405-5, so the total leaf-RED for the run is 9 and T416's 8 is
correctly scoped to its own file. GREEN run: **0 FAIL, every arm PASS**
`[VERIFIED: /tmp/t422/out/units-GREEN-report.log, exit 0]`.

The "ADDS rather than REPLACES" claim is confirmed at unit level **and** independently at corpus
level (section 1.5 arm A), which is the stronger evidence, since the unit arms build a `Summary` by
hand and could in principle agree with a wrong implementation of the same shape.

---

## 3. THE ADMISSION CLASSIFIER. RE-MEASURED, AND ATTACKED FROM BOTH SIDES.

### 3.1 The alphabet, re-measured by me — direction confirmed, cardinals do NOT fully reproduce

`/tmp/t422/alphabet*.py`, over the artefacts the ledger vector store cites via any
`.softhouse/capture/...` string; maximal ASCII-digit runs; byte immediately left and right.

| reading | artefacts | distinct LEFT | distinct RIGHT | `,` right | `,` left |
|---|---|---|---|---|---|
| **T416's handoff claims** | **37** | **43** | **37** | **5,186** | **276** |
| T422, T416 tip (post-T391 merge), all cited artefacts | **44** | **50** | **37** ok | 1,415 | **276** ok |
| T422, T416's own pre-merge commit `bd86a5e7` | **37** ok | 50 | 35 | 1,087 | 168 |
| T422, `provenance.capture_ref` only, post-merge | 34 | 17 | 19 | 1,307 | 271 |
| T422, `.json` artefacts only, post-merge | 17 | 15 | 14 | 1,258 | 271 |

I also varied the definition of "numeric run" four ways (`[0-9]+`, `[0-9][0-9.]*`,
`[0-9][0-9,._ ]*[0-9]`, `[-+]?[0-9][0-9.]*`) on both trees; none produced 43 left, and none produced
5,186 commas to the right `[VERIFIED: /tmp/t422/alphabet5.py output]`.

**The DIRECTION of T416's argument is confirmed overwhelmingly and independently.** The old blacklist
named 4 bytes left and 4 right; the measured alphabet is 17–50 distinct bytes on each side under
every reading, so the great majority of observed neighbours were admitting by default. Measured on
the code rather than the corpus the sweep is blunter still
`[VERIFIED: TestT422_EveryByteBothSides in /tmp/t422/t422_attack_test.go]`: of the 256 possible single
neighbour bytes around a bare `100.125`, the **old** rule admitted **243 left / 243 right**; the new
rule admits **215 / 216**.

**But three of T416's five published cardinals do not reproduce, and one is stale.** "37 artefacts" is
the **pre-merge** artefact count (`bd86a5e7`); post-merge it is 44. The handoff states "**every drive
was re-run against the merged tree**" and "Nothing below is carried forward by arithmetic" — the
alphabet measurement is a counter-example to both. **F-T422-3, LOW** (below).

### 3.2 The twelve T405 rows — ALL TWELVE FLIP, plus both controls

`[VERIFIED: TestT422_T405TwelveRows in /tmp/t422/t422_attack_test.go — 14 rows, 0 divergences from my
own independently-stated expectation]`. Six former false admissions now REFUSE (`1,250,000.00`,
`1,100.12`, `100.12-`, `100.12+`, `1 250 000.00`, `100_125`); six former false refusals now ADMIT
(prose full stop, `paid+100.125`, `100.125EUR`, `id-100.125`, `50.00-100.125`,
`T352-amount-100.125.req`); `100.125MNT` still admits, so the currency pair is symmetric; and
`16,-100.125,DEBIT` still refuses. **All six F-T405-3 false refusals are CLOSED and I found none of
them left open.**

### 3.3 RED/GREEN on the new test file — BOTH CARDINALS REPRODUCE

`/tmp/t422/units2.sh`, `verbatimallowlist_test.go` run against `main`'s `admit.go` bytes and then
T416's, restoring cleanly between `[VERIFIED: /tmp/t422/out/admit-{RED,GREEN}.log]`:

- RED: `grep -cE '^ *--- FAIL:'` = **31**, exit 1 — which is **28 leaf subtests** (12 boundary rows +
  16 unnamed-byte rows) **plus 3 parent test lines**. T416 calls all 31 "subtests"; the number is
  right, the noun is loose. **No test outside the new file went red**, so T397's own rows survive the
  inversion untouched.
- GREEN: **0 FAIL**, exit 0; `--- PASS:` over the three new tests plus T397's
  `TestTheBoundaryRuleFormsNoNumber` and `TestThePrefixIsStillCaughtDownstreamIfAdmissionIsBypassed`
  = **31 + 17 + 1 + 17 + 1 = 67**. **T416's "67 PASS" reproduces exactly.**

### 3.4 ATTACKING THE NEW CLASSIFIER — what I found

My own table (`/tmp/t422/t422_attack_test.go`, run in the scratch clone only, never added to the
repo): 55 rows across three arms, plus an exhaustive 256-byte sweep and a side-by-side old-rule /
new-rule differ. **Two genuine holes and one design inconsistency.**

**(a) FALSE ADMISSION — an ISO date now admits where the old rule refused it.**
`[VERIFIED: TestT422_FalseAdmissionHunt and TestT422_WhereTheTwoRulesDisagree]`

```
{"transactionDate":"2026-01-15"}  cited "15"  ->  old=REFUSE   new=ADMIT
{"transactionDate":"2026-01-15"}  cited "01"  ->  old=REFUSE   new=ADMIT
```

`leftDelimits` treats `-` as a **separator** whenever `raw[i-2]` is a token byte, which is exactly the
rule that lets `id-100.125` and `50.00-100.125` through. A hyphenated date is the same shape, so a
cited amount text that happens to coincide with a date component resolves against the date and the
citation is declared verbatim. **This is the fail-OPEN direction — a wrong value accepted as the
reference oracle's own characters — the direction T416's own comma reasoning names as the more
expensive one; it accepted it here without saying so.** The old blacklist was fail-closed on this byte.

**Blast radius, measured — and it is why this is MINOR rather than MAJOR.**
`verbatimInCapture` has exactly two call sites and both are inside `divergenceReasons`
(`admit.go:1286`, `:1292`) `[VERIFIED: grep over admit.go on the T416 tree]`. The classifier therefore
gates only the DIVERGENCE class, and only two fields: `oracle_accepted.observed_amount_texts` and
`request.legs[].amount_major_text`. The first is protected by an earlier check —
`hasResidueBeyondMinorUnit` requires a non-zero digit past the currency's minor unit, so a bare `15`
cannot reach the classifier there. The second is not protected. Today's only divergence vector cites
`.softhouse/capture/t352-a2-next-tranche/out/T352-A01-residue-3dp.req`, whose date is
`"01 June 2026"` rather than ISO, and whose leg texts are `100.125`
`[VERIFIED: LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json and the artefact itself]`. **The
hole is latent, not live. It is one ISO-8601 capture away from being live.**

**(b) FALSE REFUSAL — a compact JSON array of numbers refuses on the RIGHT side.**
`[VERIFIED: TestT422_FalseAdmissionHunt, row "[100.125,200]"]`

```
[100.125,200]         cited "100.125"  ->  REFUSE
[100.125, 200]        cited "100.125"  ->  ADMIT
{"a":100.125,"b":2}   cited "100.125"  ->  ADMIT
```

`rightDelimits`'s comma branch is `!(digit(last) && digit(next))`, so `...125,2...` reads as a group
separator. `encoding/json.Marshal` with no indent emits exactly `[100.125,200]`, so **any future
capture artefact serialised compactly with an array of bare numbers refuses a citation of one of its
elements, at exit 2.** T416 records the digit-COMMA-digit refusal decision, and I agree with the
decision — but as recorded it names only the CSV/thousands case
(`TestTheAmbiguousGroupSeparatorResolvesTowardRefusal`), and that test's own "the unambiguous JSON
forms are unaffected" control set is `{"a":100.125,"b":2}`, `[16, 100.125]`, `{"a":100.125}` — **each
of which has a non-digit beside the comma. The compact-array shape is exactly the one the control
omits.**

**(c) FALSE REFUSAL — `digit SPACE digit` in columnar text.** `[VERIFIED: TestT422_FalseRefusalHunt]`
`row 1 100.125 end` and `row 12 100.125 end` REFUSE; `row A 100.125 end` ADMITs. A whitespace-aligned
`.txt` capture with a numeric column before an amount refuses. Same family as (b), same fail-closed
direction, and the honest cost of the group-separator rule. **Not a defect; it should be named
alongside the comma in the recorded decision.**

**What I checked and found CLEAN** — so silence here is distinguishable from not looking. Every
prefix/tail row still refuses (`100.12` in `100.125`, `100.125` in `1100.125`, `100.125` in
`100.1250` — T387's F-T387-2 intact). Every leading-sign row refuses (`-100.125`, `[-100.125]`,
`paid -100.125`, `x=-100.125`, `{"a":-100.125}`). Every exponent shape refuses (`100.12e3`,
`100.12E+3`, `100.125E5`) while `100.125EUR` admits and `100.12e` — not an exponent shape — admits.
Version strings refuse (`1.10.125`, `v100.125.3`). High bytes delimit on both sides (`₮100.125` and
`100.125₮` admit). Every C0 control byte and DEL refuses on both sides, which is the inversion's
stated property asserted directly rather than inferred. All 12 live-capture shapes I could construct
from my own alphabet measurement ADMIT. Each of my tables carries its own anti-vacuity arm and fails
if either direction is empty.

### 3.5 The digit-COMMA-digit decision — I JUDGE IT CORRECT

Refusing is fail-closed: exit 2 with a named reason a human fixes in the same fire, against a wrong
money value silently accepted as the oracle's own characters. The costs are genuinely asymmetric and
the call is right. **Nothing in today's corpus is refused by it** — the full store measures
`ledger inadmissible 0` on my own unmutated control run `[VERIFIED: /tmp/t422/out/control-AFTER.log]`,
across T391's three accrual vectors as well. It is recorded in a named test that a porting task will
meet, which is where such a decision belongs. **My only condition is that the record is incomplete:
it names the CSV case and neither of the two other shapes the same rule refuses, (b) and (c).**

---

## 4. NO FLOAT, NO PARSE — SWEPT INDEPENDENTLY, CLEAN.

Regex wider than the author's, over every added line of the Go diff:
`float|float32|float64|strconv|ParseFloat|ParseInt|Atoi|Itoa|big\.|math\.|json\.Number|decimal|Decimal|%f|%e|%g|/ *[0-9]|\* *0\.|\.Float|Sqrt|Pow|round|Round|ceil|floor`
→ **8 hits, every one comment or test-name text stating the prohibition; zero code hits**
`[VERIFIED: /tmp/t422/t416-go.diff]`.

Every arithmetic expression in the added code, exhaustively: `i-1`, `i-2`, `i >= 2`, `end-1`,
`end+1`, `end+2`, `end >= len(raw)`, `b >> 4`, `b & 0x0f` (hex naming in a test), and in `report.go`
`s.ParityFail+s.ContractFail+s.SelfTestFail+lm` and `s.InvariantViolations+lv`. **Every one is a byte
OFFSET or an int counter. Not one touches an amount.** The classifier's only tests are
`b >= '0' && b <= '9'`, `b >= 'a' && b <= 'z'`, `b >= 'A' && b <= 'Z'`, `b >= 0x80` and
`strings.IndexByte`. **No `int64` anywhere holds `100.125`; the amount stays bytes end to end.**
Added imports across the whole diff: `testing`, `fmt`, `strings` — nothing else
`[VERIFIED: /tmp/t422/t416-go.diff]`. **T416's claim that arithmetic occurs only on byte offsets is
correct.**

No MySQL / MariaDB / Oracle Database driver, dialect, `ojdbc`, `oracle.jdbc`, or port 1521 is
introduced. The only `MySQL` occurrences anywhere in the diff are 13 identical lines of an
**existing** harness report sentence replayed inside committed transcripts, observing that Fineract's
`GLAccountReadPlatformServiceImpl.java:127-131` emits MySQL-only SQL — a note ABOUT the reference
oracle, not a dependency `[VERIFIED: /tmp/t422/t416-full.diff]`. Money in the touched code is int64
minor units or plain counters; no posting, balance or hold code is in this diff, so the append-only
ledger and derived-balance rules are untouched by it.

### 4.1 A DEFECT THE SWEEP FOUND — the classifier's own explanation is now false

`admit.go`'s `verbatimInCapture` was **not** updated, and it is the entry point a porting task reads
first. Two places in it still describe the **superseded blacklist**
`[VERIFIED: the file as it stands on softhouse/T416-t405-conditions, lines 1366-1370 and 1406-1413]`:

- the doc comment: *"the match must not have a digit, a decimal point or a sign glued to its left, nor
  a digit, a decimal point or an exponent marker glued to its right"* — precisely the rule T416 deleted;
- **the refusal message a human reads**: *"...those bytes occur in %s ONLY GLUED TO A LONGER NUMBER —
  every occurrence has a digit, a decimal point or a sign immediately beside it..."*. Under the new
  rule that sentence is **false** for any refusal caused by an unnamed byte. I drove `100.125\x00`
  and `\x01100.125` to REFUSE and neither neighbour is a digit, a point or a sign
  `[VERIFIED: TestT422_FalseRefusalHunt rows NUL-right / SOH-left; T416's own
  TestAnUnnamedByteRefusesRatherThanAdmits asserts the same 16 refusals]`.

**This is the same class of defect as F-T405-5 itself, one file over**: the machine decision is right
and the sentence the human reads is wrong about why. T416 rewrote three hundred lines of comment on
the functions below and left the caller's account of them stale.

---

## 5. F-T405-4 — THE DIVERGENCE-CLASS PIN REQUEST. RE-DRIVEN. SAFE TO APPLY.

`.softhouse/conformance.sh` is **0 lines changed by T416** — confirmed: it does not appear in
`git diff --name-only <merge-base>..t416` `[VERIFIED: /tmp/t422/mergecheck.sh output]`. The request
ships as `.softhouse/capture/t416-t405-conditions/REQUEST-conformance-sh-divergence-pin.md`.

### 5.1 The bar reads neither figure — confirmed

`[VERIFIED: grep over /tmp/t422/t416/.softhouse/conformance.sh]`
`grep -c 'ledger inadmissible'` = **0**; `grep -c 'INADMISSIBLE'` = **0**;
`grep -c 'divergence vectors'` = **0**. Four `EXEMPTION_PIN_LEDGER_*` figures are compared
(`_DECLARED`, `_PARITY`, `_REFUSAL`, `_MONEYCELLS`, at `conformance.sh:4309-4312`) plus
`_WRONGIMPLS` at `:4499`. Neither proposed figure is among them.

### 5.2 T405's narrowing — CONFIRMED by my own drive, not inherited

`/tmp/t422/pinreq.sh`. I mutated the divergence vector's `observed_amount_texts`
(`100.125000` → `100.12500`) and, separately, broke a PARITY vector's `provenance.capture_ref` to a
non-existent artefact. Both proposed `sed` extractions were run **exactly as the REQUEST writes
them** against all three transcripts `[VERIFIED: /tmp/t422/out/pin-*.log]`:

| store state | exit | declared | parity | refusal | money cells | **inadm** | **divPASS** | the four existing pins |
|---|---|---|---|---|---|---|---|---|
| baseline | 0 | 0 | 10 | 6 | 63 | `0` | `1` | **GREEN, correctly** |
| **DIVERGENCE vector inadmissible** | 2 | 0 | 10 | 6 | 63 | `1` | `0` | **GREEN — every one of the four is byte-identical to baseline. This is the hole.** |
| PARITY vector inadmissible | 2 | 0 | **9** | 6 | **58** | `1` | `1` | **RED — two pins move; already caught** |

**T405's narrowing holds exactly and T416 reproduced it correctly.** Both proposed extractions
returned a non-empty value on all three rows, so neither would be a `_census_one` refusal.

### 5.3 IS THE REQUEST SAFE TO APPLY? YES — with one correction to how it is described.

**Safe.** The two pins are `0` and `1` at the current store, measured by running, and both hold on my
own bar runs (`ledger inadmissible 0`, `divergence vectors PASS 1 FAIL 0 (pinned 1)`)
`[VERIFIED: /tmp/t422/BAR-t416.log and /tmp/t422/BAR-merge.log]`. The patch adds two constants, two
`_census_one` extractions inside the existing `ledger_cmp` block and two `_cmp` lines; it touches
neither helper. `conformance.sh` is free — T404 released it — and current `main` has since edited it,
so the applier must re-anchor the three hunks by context rather than by the line numbers in the
request (`524`, and the `ledger_cmp` / `_cmp` blocks; on today's `main` the `_cmp` lines are at
`:4309-4312`).

**The correction: this pin is defence in depth, not the closure of a fail-open.** The REQUEST's
headline row says the four pins stay GREEN "and it should not be", which is true — but I measured
the run's **exit code in that state and it is 2, not 0**
`[VERIFIED: /tmp/t422/out/pin-divergence-inadmissible.log, exit=2]`. `Summary.ExitCode()` returns 2
on `s.Ledger.Inadmissible > 0`, so **nothing green is called green today**. The REQUEST does state
this counter-argument in its own words and answers it (one boolean, one Go function, no second
layer — the shape this program keeps paying for), and I agree with that answer. But the driver
should apply it knowing it is a **second layer under a working first layer**, not a hole through
which a vanished divergence record currently escapes. Applying it is cheap and correct; **not**
applying it does not leave a live fail-open.

**One operational note for whoever applies it:** `EXEMPTION_PIN_LEDGER_DIVERGENCE_PASS=1` pins a
GRADED figure, so it must be moved in the same commit as any added or removed divergence vector,
alongside `divergencePinCount` in `ledger/conformance/grade.go:750`. That is two pins on adjacent
facts and the request says so.

---

## 6. F-T405-6 — CORRECTING RATHER THAN DELETING. RIGHT CALL. ONE HONEST LIMIT.

**The comment T397 left was false and T405 is right about it, and I re-derived why**
`[VERIFIED: report.go on main vs T416; ledger/conformance/grade.go:748-750]`. `recordedDivergences()`
returns `s.Ledger.DivergencePass + s.Ledger.DivergenceFail` — GRADED counters. The census prints
`(pinned n)` from `DivergencePinCount()`, a `const divergencePinCount = 1` describing the population
the store is pinned to HOLD. Two different populations; they can disagree. The corrected comment now
claims only the narrower thing (this figure and the census's own PASS/FAIL pair read the same two
fields) and that narrower claim is true.

**Correcting rather than deleting was right, and the correction is stronger than what it replaced,
not weaker.** The old arm asserted two things. The new arm asserts three, and branches on
`DivergencePinCount()` instead of hard-coding today's value, so at a zero pin the original sentence
is asserted again `[VERIFIED: the diff of verdict_divergence_test.go]`. Deleting it would have
removed the only guard on the "there are none" / "nobody looked" distinction the arm existed for. A
test whose expectation is wrong is evidence about the expectation, not a reason to stop asserting.

**RED/GREEN driven by me**: the arm
`TestTheExitZeroVerdictNamesTheRecordedDivergences/a_zero_graded_divergence_run_does_not_claim_the_store_has_none`
is **FAIL against `main`'s `report.go` and PASS against T416's**
`[VERIFIED: /tmp/t422/out/units-{RED,GREEN}-report.log]`. The real store is unaffected: the exit-0
arm still prints `IT EXCLUDES 1 RECORDED DIVERGENCE(S)` and the bar is exit 0
`[VERIFIED: /tmp/t422/out/pin-baseline.log, /tmp/t422/BAR-t416.log]`.

**The honest limit, which the handoff does not state.** I tried to reach the new third branch on the
real corpus and **could not**. It requires exit 0 **and** `s.Ledger != nil` **and** pin > 0 **and**
zero graded divergences. Two other guards forbid every route I found:

- make the divergence vector inadmissible → `ExitCode()` returns **2** (`Ledger.Inadmissible > 0`)
  `[VERIFIED: /tmp/t422/out/pin-divergence-inadmissible.log]`;
- remove the divergence vector from the store → `LEDGER FATAL: DIVERGENCE POPULATION 0, PINNED 1`,
  exit **2** `[VERIFIED: /tmp/t422/out/f6-removed-AFTER.log:287]`;
- and the ledger `Summary` has no non-fatal "refused/skipped" outcome — the four outcomes are
  PASS / FAIL / INADMISSIBLE / ERROR (`grade.go:628-647`), so a loaded divergence vector always
  grades `[VERIFIED: grade.go]`.

So the new branch is **currently unreachable at exit 0**, and so was the false sentence it replaces.
T416's handoff writes "driven above: `divergence vectors PASS 0 FAIL 0 (pinned 1)`", and that state
WAS driven — but at exit 2, where neither sentence prints. The unit test constructs the state
directly and does prove the wording. **This is belt-and-braces and I judge it correct to have added
it** (P-45: a state protected only by two other guards is one refactor from being protected by
none), but the record should not imply the corpus exercised it. **F-T422-4, LOW.**

---

## 7. MERGE SAFETY — CLEAN, AND VERIFIED AGAINST **TODAY'S** `main`, NOT T416's.

`main` moved again while I worked: T416 merged `e0eb4fe2` (T391 + T411); `main` is now **`e864dd3d`**
(T421 + T428 merged on top). I checked the merge that matters — **current `main` + T416** — in
`/tmp/t422/merge`, a clone OUTSIDE the repository `[VERIFIED: /tmp/t422/mergecheck.sh]`.

| | files changed since merge-base `e0eb4fe2` |
|---|---|
| **`main`** | `.softhouse/conformance.sh`, `ledger/conformance/impl.go`, `ledger/conformance/slotadmission_test.go`, `ledger/conformance/vector.go` |
| **T416** | `ledger/conformance/admit.go`, `ledger/conformance/verbatimallowlist_test.go`, `loanschedule/conformance/report.go`, `loanschedule/conformance/verdict_divergence_test.go`, `loanschedule/conformance/verdict_fail_ledger_test.go` |

**The two sets are disjoint at FILE level, so the T391 line-range argument is now moot** — I did not
need to check 1332-1334 / 1342-1352 / 1354-1364 against 182-243 / 243-300 / 981, because T391 is
already in the merge base and no remaining `main` change touches `admit.go` at all.

- `git merge-tree --write-tree main t416` → **exit 0, tree `f990da2a`, zero conflict markers**.
- the merge itself → **exit 0, zero conflicted paths, clean working tree**.
- **T421 collision, checked as the brief asks:** T421/T428 land `impl.go`, `vector.go` and a new
  `slotadmission_test.go` in the **same Go package** as T416's `verbatimallowlist_test.go`. Git cannot
  see a duplicate-symbol collision, so I compiled it: `go build ./...` **exit 0**,
  `go vet ./...` **exit 0**, `go test -count=1 ./...` **exit 0, all four packages ok**
  `[VERIFIED: /tmp/t422/mergebuild.sh]`. **No collision.**
- T416 changes 0 lines of `.softhouse/conformance.sh`, which `main` has since edited — no conflict,
  and the F-T405-4 REQUEST is still unapplied.

---

## 8. THE BAR — RUN TWICE, FROM CLEAN TREES, BOTH OUTSIDE THE REPOSITORY.

`bash .softhouse/conformance.sh` (never `sh`), from `/tmp`, so
`guard_no_narrow_catch_in_capture_rigs`'s recursive walk cannot see a nested checkout.
**Probe-line PRESENCE tested before its value, as the brief requires.**

| | **T416's own tree** `/tmp/t422/t416` | **`main` + T416 merged** `/tmp/t422/merge` |
|---|---|---|
| **exit code** | **0** | **0** |
| **`grep -c 'probe = '`** | **1 — the line WAS printed** | **1 — the line WAS printed** |
| probe value | `probe = up` | `probe = up` |
| **VERDICT** | `PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` | identical |
| loanschedule parity | `PASS 46 FAIL 0`, `refused 0`, `inadmissible 0` | identical |
| ledger parity | `PASS 10 FAIL 0` == pinned 10 | `PASS 10 FAIL 0` == pinned 10 |
| ledger oracle-refusal | `PASS 6 FAIL 0` == pinned 6 | == pinned 6 |
| ledger money cells | `63` == pinned 63 | `63` == pinned 63 |
| ledger declared exemptions | `0` == pinned 0 | `0` == pinned 0 |
| ledger inadmissible / harness errors | `0` / `0` | `0` / `0` |
| divergence vectors | `PASS 1 FAIL 0 (pinned 1)` | identical |
| wrong ledger impls | 15 == pinned 15, **all died through the harness** | **16 == pinned 16**, all died through the harness |
| dead-path frontier | GREEN, 11 == pinned 11 | GREEN, 11 == pinned 11 |
| DEADPATH-CENSUS | `corpus=1428 deadFiles=75 deadOccurrences=108` | `corpus=1480 deadFiles=75 deadOccurrences=108` |
| exemption census (loanschedule) | graded 4 / loaded 4 / GROUNDED 4 / UNDETERMINED 0 / UNGROUNDED 0, all == pinned | identical |
| P-number citations | **VERDICT PASS** | **VERDICT PASS** |
| FAIL / HARD-guard lines | none | none |

**Exit 2 with no probe line — the HARD-guard failure mode the brief warns about — did not occur on
either run: the probe line was printed exactly once on each, before I looked at its value.**
`deadOccurrences` holds at **108** on both, and every count T416's handoff reports for its own tree
reproduces exactly. The two differences on the merged tree (`wrong impls` 15→16, `corpus` 1428→1480)
are `main`'s, from T421/T428, and both are `== pinned` there.

`go build ./...` exit 0 and `go test -count=1 ./...` exit 0 on **both** trees
`[VERIFIED: /tmp/t422/mergebuild.sh and the T416-tree run]`.

**MERGING IS SAFE.**

---

## 9. WHAT I CHECKED AND FOUND NOTHING — so silence is distinguishable from not looking

- **Money non-negotiables.** No float, no `strconv`, no `big.`, no `math.`, no division, no parse
  anywhere in the added code; every arithmetic expression enumerated in section 4. No `int64` holds
  `100.125`. Money in the touched code is int64 minor units or plain int counters.
- **Ledger invariants.** This diff contains no posting, balance, hold or reversal code, so
  append-only / derived-balances / holds-affect-available-only are untouched. The bar's own
  `ledger invariants 0 violation(s), 25 non-vacuous assertion(s)` line is green on both trees.
- **Idempotency-Key.** No money-movement endpoint is added or altered.
- **Database.** No MySQL/MariaDB/Oracle-Database driver, dialect, `ojdbc`, `oracle.jdbc` or port
  1521. The 13 `MySQL` strings in the diff are replayed lines of an existing harness report about
  Fineract's own SQL.
- **Frozen adapter contract.** Untouched — no file under `loanschedule/contract` is in the diff.
- **Scope.** Files changed outside T416's stated grant: **none**
  `[VERIFIED: /tmp/t422/mergecheck.sh file list]`. `.softhouse/conformance.sh`: 0 lines.
- **P-number citations.** T416 cites P-45, P-83, P-84, P-98 among others; all four exist in
  `.softhouse/patterns.md` (`:1503`, `:2806`, `:2813`, `:3411`), and the bar's `PNUMBER-CITATIONS`
  gate is `VERDICT PASS` on both trees.
- **T397's own tests.** Not one test outside T416's two new files goes red against `main`'s bytes,
  so the inversion did not silently relax an older assertion.
- **The divergence double-count.** `ledger_divergence_fail_is_counted_once` is RED before / PASS
  after, and I confirmed `grade.go:628-644` folds a divergence FAIL into `RefusalFail` as well as
  `DivergenceFail`, so omitting `DivergenceFail` from `ledgerMismatches()` is correct and not an
  oversight.
- **The split line's second count.** It is printed from the same two expressions the total is summed
  from (`lm`, `lv`), so it cannot drift from the total — I read the code and drove the mixed arm,
  where the split (`LEDGER 2 | LOAN SCHEDULE 1`) and the total (`3`) agree.

---

## 10. FINDINGS

| id | rating | area | one line |
|---|---|---|---|
| **F-T422-1** | **MINOR** | `admit.go` §4.1 | `verbatimInCapture`'s doc comment and its **refusal message** still describe the deleted blacklist, and the message is now demonstrably FALSE for an unnamed-byte refusal. |
| **F-T422-2** | **MINOR** | `admit.go` §3.4(a) | `leftDelimits`'s hyphen-as-separator rule opens a **false admission the old blacklist closed**: `{"transactionDate":"2026-01-15"}` now admits a citation of `15`. Fail-OPEN on money text. Latent, not live. |
| **F-T422-3** | **LOW** | handoff §3.1 | Three of five published alphabet cardinals do not reproduce, and "37 artefacts" is the **pre-merge** count — a counter-example to the handoff's own "every drive was re-run against the merged tree". |
| **F-T422-4** | **LOW** | `report.go` §6 | The new third exit-0 branch is **unreachable at exit 0** on the real corpus (two other guards force exit 2 first). Correct to add; the record should not imply the corpus exercised it. |
| **F-T422-5** | **LOW** | test §3.4(b)(c) | The recorded digit-COMMA-digit decision names only the CSV case; the same rule also refuses **compact JSON arrays** (`[100.125,200]`) and **`digit SPACE digit` columnar text**, and the test's own "unambiguous forms" control set omits exactly those shapes. |

**Nothing I found is a rejection.** No non-negotiable is violated, the money defect F-T405-5 was
fixed and the fixed count is RIGHT rather than merely non-zero, and both bars are exit 0 with every
pinned figure held.

---

## VERDICT: **APPROVED WITH CONDITIONS**

T416 closes all six of T405's conditions. The MAJOR money-reporting defect is genuinely fixed, and it
is fixed **correctly** — I drove the count to 1, 2 and 3 mismatched ledger vectors and the sentence
said 1, 2 and 3, and I drove a mixed 1-loanschedule + 2-ledger corpus where the old code said `1` and
the new code says `3` with the split attributing `LEDGER 2 | LOAN SCHEDULE 1`. The admission
classifier really is inverted, all twelve T405 rows flip, and no number is formed anywhere near an
amount. Merging onto today's `main` is clean, compiles, tests green and the bar is exit 0.

### Conditions

**C-T422-1 — MINOR. Correct the refusal message and doc comment `verbatimInCapture` still gives for
the rule T416 deleted.** `admit.go` ~`:1366-1370` (doc) and ~`:1406-1413` (the message a human
reads). The message asserts *"every occurrence has a digit, a decimal point or a sign immediately
beside it"*, which is false for any refusal caused by an unnamed byte. **This is the same class of
defect as F-T405-5 — a right machine decision under a false human sentence — and T416 should not
close a fire on it while leaving a second instance one file away.**

> **Drive.** RED-before: in the ledger conformance package, assert that a vector whose
> `request.legs[].amount_major_text` occurs in its `request_capture_ref` artefact **only** beside an
> unnamed byte (`"100.125"` followed by `\x00`) is refused, and that the refusal reason does NOT
> contain the substring `has a digit, a decimal point or a sign immediately beside it`. That arm is
> RED today — I confirmed the refusal itself fires
> `[VERIFIED: /tmp/t422/t422_attack_test.go row "NUL right", REFUSE]`. GREEN-after: the message names
> the actual class ("a byte this file has not NAMED as terminating a numeric token"). Control: the
> genuine glued-to-a-longer-number case (`100.12` against `100.125`) must still produce the
> prefix/tail wording, so the two reasons stay distinguishable.

**C-T422-2 — MINOR. Close or explicitly accept the hyphen false admission, in writing, with a test
either way.** `leftDelimits`'s `-`/`+` branch returns `i >= 2 && isTokenByte(raw[i-2])`, so
`2026-01-15` admits `15`. The old blacklist refused it. The blast radius today is one field
(`request.legs[].amount_major_text` on divergence vectors — the other field is shielded by
`hasResidueBeyondMinorUnit`), and today's only divergence artefact uses `"01 June 2026"`, so it is
latent. **It is one ISO-8601 capture from being live, and it is the fail-OPEN direction T416's own
comma reasoning names as the more expensive one.**

> **Drive.** RED-before, both directions, in one table:
> `tokenBoundedIndex([]byte(`{"transactionDate":"2026-01-15"}`), []byte("15"))` must be `< 0`
> (currently `>= 0` — RED `[VERIFIED: TestT422_FalseAdmissionHunt]`), while
> `tokenBoundedIndex([]byte("id-100.125"), []byte("100.125"))` and
> `[]byte("range 50.00-100.125")` must stay `>= 0` (the two F-T405-3 refusals this rule exists to
> close — they must NOT regress). A candidate discriminator that needs no parse: treat `-` as a
> separator only when the far side is a **letter or `_`**, not a digit; that keeps `id-100.125` and
> refuses `2026-01-15`, but it re-refuses `50.00-100.125`, so the range row is the one that decides
> the design. **If the decision is to ACCEPT the hyphen admission instead, that is defensible — but
> it must be a named test recording the choice, exactly as the comma ambiguity is, not a silence.**

**C-T422-3 — LOW. Re-measure the capture alphabet on the merged tree and correct the handoff's five
cardinals, or state the reading that produces them.** I get 44 artefacts / 50 left / 37 right /
1,415 commas-right / 276 commas-left on T416's tip, and 37 artefacts only at T416's **pre-merge**
commit. Two of the five reproduce; three do not. The finding does not depend on them — the direction
is confirmed under every reading I tried, including a 256-byte exhaustive sweep — but the handoff
asserts "every drive was re-run against the merged tree" and this one was not.

> **Drive.** Re-run the measurement script on the tip, print `artefacts=`, `left=`, `right=` and both
> comma counts, and commit the transcript. Control: run the same script on `bd86a5e7` and show the
> two readings side by side, so the difference is visibly the T391 merge and not a method change.

**C-T422-4 — LOW. Say in the record that the new exit-0 third branch is currently unreachable at
exit 0.** Two guards force exit 2 first: `Ledger.Inadmissible > 0` in `ExitCode()`, and the
`LEDGER FATAL: DIVERGENCE POPULATION n, PINNED m` check. Adding the branch is right (P-45), but the
handoff's "driven above" points at a transcript that exits 2, where neither sentence prints.

> **Drive.** Add one assertion to the new arm that documents the reachability, e.g. a comment plus a
> subtest naming the two guards that stand in front of it, and cite
> `/tmp/t422/out/f6-removed-AFTER.log:287` (`LEDGER FATAL: DIVERGENCE POPULATION 0, PINNED 1`) as the
> measurement. Nothing needs to change behaviourally.

**C-T422-5 — LOW. Widen the recorded ambiguity decision to the two other shapes the same rule
refuses.** `TestTheAmbiguousGroupSeparatorResolvesTowardRefusal` names only CSV. The rule also
refuses `[100.125,200]` — the exact output of `encoding/json.Marshal` without indent — and
`row 1 100.125 end`. Its "the unambiguous JSON forms are unaffected" control set
(`{"a":100.125,"b":2}`, `[16, 100.125]`, `{"a":100.125}`) contains only shapes with a **non-digit**
beside the comma, so it cannot see the case it omits.

> **Drive.** Add both rows to the ambiguity test with `want=false` and a comment saying the refusal is
> the accepted cost, so a future capture rig meets the decision instead of an unexplained exit 2.
> Control: keep `[100.125, 200]` (with the space) as a `want=true` row beside it, which is what makes
> the pair a rule rather than a blanket refusal.

### On the F-T405-4 REQUEST

**Safe to apply.** Both pin values (`0` and `1`) are measured by running and hold on both of my bar
runs; both `sed` extractions extract non-empty on all three drive transcripts; T405's narrowing
reproduces exactly. `conformance.sh` is free (T404 released it), but `main` has edited it since the
request was written, so **re-anchor the three hunks by context, not by the line numbers in the
request**. Apply it knowing it is a **second layer under a working first layer** — the state it pins
already exits 2 today — not the closure of a live fail-open.

### Merge recommendation

**MERGE.** Current `main` (`e864dd3d`) + T416 (`9f4fc247`): merge-tree exit 0, zero conflicts,
file-disjoint from T421/T428, `go build` / `go vet` / `go test -count=1 ./...` all exit 0, and
`bash .softhouse/conformance.sh` exit 0 with the probe line printed and every pinned figure held
(`wrong impls 16 == pinned 16` there, `15 == pinned 15` on T416's own tree — the difference is
`main`'s). All five conditions above are follow-ups; none of them blocks the merge, and none of them
touches money arithmetic.

---

## 11. THIS REVIEW BRANCH'S OWN BAR

`bash .softhouse/conformance.sh` on `softhouse/T422-review-t416` itself, from a clean clone at
`/tmp/t422/mine` — **outside the repository** `[VERIFIED: /tmp/t422/BAR-mine.log]`:

```
BAR exit=0
probe line PRESENCE first (P-84): grep -c 'probe = ' = 1
conformance: reference oracle (https://localhost:8443/...) probe = up
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
T316-DEADPATH-CENSUS: corpus=1453 deadFiles=75 deadOccurrences=108
dead-path frontier: GREEN — frontier == pinned (all 11 rows, by path)
exemption census READ: LEDGER parity 10 == 10, refusal 6 == 6, money cells 63 == 63, declared 0 == 0
all 15 wrong ledger implementations DIED through this harness, not by hand.
P-number citations: VERDICT PASS
```

This branch adds documentation only (`REVIEW.md` and two evidence files with inert `.txt`
extensions). It moves no pinned figure. `P-<n>` tokens used: **P-45, P-83, P-84, P-98** — all four
defined in `.softhouse/patterns.md` (`:1503`, `:2806`, `:2813`, `:3411`); the bar's
`PNUMBER-CITATIONS` gate is `VERDICT PASS`.

Its base is `e13966dc`, before T421/T428 landed, which is why `wrong impls` reads 15 here and 16 on
the merge-result run in section 8. Both are `== pinned` on their own tree.

### Evidence committed beside this review

| file | what |
|---|---|
| `t422-attack-drive.go.txt` | my adversarial classifier table — 55 rows, the old-rule/new-rule differ, the exhaustive 256-byte sweep. Drop it into `nexus/internal/apps/ledger/conformance/` as `*_test.go` **in a scratch tree only** and run `go test -run TestT422 -v`. `.txt` so it cannot join the module or a guard's recursive walk. |
| `t422-alphabet-measure.py.txt` | the capture-alphabet measurement, parameterised over two trees and four definitions of "numeric run", which is how F-T422-3 was found. |

The drive scripts themselves (`drive.sh`, `mixed2.sh`, `units.sh`, `units2.sh`, `pinreq.sh`, `f6.sh`,
`mergecheck.sh`) lived in `/tmp/t422/` and are **not** committed; every figure they produced is
transcribed above with the transcript path that produced it. **[UNVERIFIED after this session: those
`/tmp` transcripts do not survive a reboot. Every claim in this document is stated with the command
that reproduces it, so nothing here depends on them being still readable.]**
