# T422 — INDEPENDENT review of T416 (`softhouse/T416-t405-conditions`)

STATUS: IN PROGRESS — committed incrementally. The VERDICT section is written last.

Reviewer: T422, branch `softhouse/T422-review-t416`.
Subject: `softhouse/T416-t405-conditions`, 10 commits, tip `9f4fc247`, merge-base current `main` (`e13966dc`).
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
