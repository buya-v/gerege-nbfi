# A2-34 — INDEPENDENT review of A2-15, the first vectors in this program that grade a ledger

| | |
|---|---|
| Task | `A2-34` · `reviewer` · context `tierA-gl-accounting` · depends on `A2-15` |
| Subject | `.softhouse/vectors/ledger/` (six vectors), `.softhouse/vectors/{PIN-ledger,capabilities-ledger}.json`, `nexus/internal/apps/ledger/conformance/` |
| Branch | `softhouse/A2-34-review-a2-15` |
| **Fork point MEASURED** | **`2d41838cdbbe5332bd62deb5cdec9f52f3df91f3`** — NOT what the dispatch said. See **F-A2-34-1**. |
| Measured at | **`d039d29630b93a142f965b7936917c50e81aa6c2`** (`main` tip) after `git merge main` |
| Reference oracle | LIVE, `{"status":"UP","groups":["liveness","readiness"]}`, pinned checkout `426a23544`, PostgreSQL `fineract-db-1` (`postgres:18.3`, up 4 days), tenant `gerege` |

**VERDICT: ACCEPT.** No rejection-grade finding. **Zero synthesised cells** — all 27 promoted
cells re-derived byte-present from raw captures by an instrument I wrote, not A2-15's. All four
of A2-15's counter-claims against its brief are **CONFIRMED by re-derivation**. Eight findings
below, none HIGH against A2-15 itself; the one HIGH is against the **driver's own merge and
dispatch record** (F-A2-34-1).

**What a green ledger section means, and nothing more.** It means the Go ledger package's money
conversion, its double-entry sum, its split sum and its two refusal rules match the reference
oracle on **six captured cases**, within a graded domain that **excludes accrual, account
transfers, charge-off, multi-currency, opening balances, `GLClosure`, slot resolution, reversal
semantics and every running balance**. It is not evidence about the ledger as a whole and it is
not a cutover argument. Cutover is a hard `user` gate.

---

## 0. Tree state — read this before any other number

```
git rev-parse HEAD                      -> 2d41838cdbbe5332bd62deb5cdec9f52f3df91f3   (on arrival)
git merge-base HEAD main                -> 2d41838cdbbe5332bd62deb5cdec9f52f3df91f3
git rev-parse main                      -> d039d29630b93a142f965b7936917c50e81aa6c2
ls .softhouse/vectors/ledger/           -> No such file or directory                  (on arrival)
```

My worktree forked at **`2d41838`**, the previous fire-close commit — **not** at `d1f74ae` and
**not** at `main`. The subject was absent. Per the brief I ran `git merge main`, landed at
`d039d29`, and the six vectors and the seven-file conformance package appeared. **Every
measurement in this document was taken at `d039d29` unless stamped otherwise.** I never inferred
"absent" from the pre-merge tree (P-70 / P-66).

---

## F-A2-34-1 — HIGH (against the DRIVER, not against A2-15): `d1f74ae` is not on `main`, and the BAR was verified at an orphaned commit

**The brief asserts, twice and in bold: "A2-15 was merged to `main` at `d1f74ae`" and "BAR —
driver-verified on merged `main` at `d1f74ae`."** Measured:

```
git cat-file -t d1f74ae                       -> commit                     (it exists)
git merge-base --is-ancestor d1f74ae main     -> exit 1                     (it is NOT on main)
git branch -a --contains d1f74ae              -> (empty)                    (no ref reaches it)

git log -1 --format='%H %P %ci %s' d1f74ae
  d1f74ae74a…  a072ecd01a… 1325e8b904…  2026-08-22 16:40:04 +0800  merge A2-15: THE FIRST VECTORS…
git log -1 --format='%H %P %ci %s' d76594a
  d76594a24c…  a072ecd01a… 1325e8b904…  2026-08-22 16:40:19 +0800  merge A2-15: THE FIRST VECTORS…

git rev-parse d1f74ae^{tree}  -> 90514b2f66697e8b5edee41995d35c51efaaeafc
git rev-parse d76594a^{tree}  -> 90514b2f66697e8b5edee41995d35c51efaaeafc     IDENTICAL
git diff --stat d1f74ae d76594a -> (empty)
```

**There are TWO merge commits for A2-15, fifteen seconds apart, with identical trees and identical
parents.** `d1f74ae` is dangling; `d76594a` is the one on `main`. **Materially this changes
nothing** — the trees are byte-identical, so the driver's BAR run graded exactly the bytes that
are on `main`, and every number in the BAR is reproducible (I reproduced all of them, §2). But the
sha the driver circulated in this dispatch, and will cite in the fire record, **does not exist on
`main`** and a later reader running `git show d1f74ae` on a fresh clone will get nothing.

**And the fork point.** I was told nothing about my own fork point except by implication, and I
measured `2d41838` — the fifth consecutive worker whose measured fork point disagrees with what
its brief implies. **P-71 has now been stated two ways and falsified both times.** Both the
"session start" and the "dispatch commit" formulations are wrong here: my worktree forked from
neither `d1f74ae` (dispatch) nor `d039d29` (main at dispatch time), but from `2d41838`, the tip
`main` had **two commits earlier**. The only rule that survives contact with measurement is:
**a worker measures `git merge-base HEAD main` itself and states it, and the driver does not
predict it.**

**Severity HIGH** because it is the mechanism, not the instance: a driver that circulates and
records a commit id it did not read back from `main` will eventually circulate one whose tree is
*not* identical, and the next reviewer will grade different bytes without knowing it.

---

## F-A2-34-2 — PASS (no finding against the subject): every promoted cell is byte-present. 27 of 27. Zero synthesised.

This is the item the task calls "the single worst outcome available here". It did not happen.

**Instrument, engine and flags, stated per P-72.** I wrote my own re-derivation
(`rederive-provenance.sh`, committed beside this file) and did **not** run, source or read
A2-15's `verify-provenance-a2-15.py` for the verdict. Every sweep is
`LC_ALL=C /usr/bin/grep -c -aF <needle> <file>` — **BSD grep 2.6.0-FreeBSD**, `-F` fixed-string so
no regex metacharacter and no `\b` is involved at all, `-a` binary-safe, `LC_ALL=C` collation
pinned. Measured on this machine, this session:

```
/usr/bin/grep --version                      -> grep (BSD grep, GNU compatible) 2.6.0-FreeBSD
/usr/bin/grep -P 'a\wc'                      -> "grep: invalid option -- P", exit 2   (does not exist)
/usr/bin/grep -c '\bworld\b' <<< "hello world" -> 1, exit 0                            (honours \b)
git grep -c -E '\bledger\b' -- <one file>    -> exit 1, ZERO output                    (silent zero)
git grep -c -F 'ledger'     -- <same file>   -> 10, exit 0                             (same file, same word)
```

**Both engine claims in my brief are REPRODUCED**: `/usr/bin/grep -P` does not exist (exit 2,
usage banner), and `git grep -E` returns a silent zero for `\b` on a file that `git grep -F`
matches ten times.

**Calibration before any negative was believed (P-72):**

```
CAL+  grep -aF '"amount"'            in A2-347-je-manual-readback.json -> 1   (non-zero recall)
CAL-  grep -aF 'ZZZ_NOT_PRESENT_ZZZ' in the same file                  -> 0   (a true zero)
```

**Artefact resolution — 12 of 12, digest-exact.** Every one of the six vectors cites BOTH a
response artefact and a request artefact. All twelve exist, are non-empty, and their **sha256
matches the digest the vector records, character for character**:

| case_id | response artefact (bytes / sha16) | request artefact (bytes / sha16) |
|---|---|---|
| LDG-01 | `out/A2-347-je-manual-readback.json` 2213B `a942e4d2503fe97a` **MATCH** | `out/A2-343-manual-je-3leg.req` 385B `be692ac41b58081b` **MATCH** |
| LDG-02 | `out/A2-338-je-after-repayment-coverage.json` 5589B `cc2437b4b939bfb1` **MATCH** | `out/A2-337-repayment-split.req` 122B `dd56f6371aa5abac` **MATCH** |
| LDG-03 | `out/A2-383-je-after-overpay.json` 9753B `efc4bfa0dc39815a` **MATCH** | `out/A2-382-repayment-overpay.req` 121B `b93a498a4efb499f` **MATCH** |
| LDG-04 | `out/A2-390-db-ledger-state-a2-15.json` 28692B `d694d558fb5956cb` **MATCH** | `out/A2-345-manual-je-header.req` 348B `d2093f2a06fe2166` **MATCH** |
| LDG-REFUSE-01 | `out/A2-344-manual-je-unbalanced.json` 576B `a2162fcf5ff5c4e8` **MATCH** | `out/A2-344-manual-je-unbalanced.req` 354B `15b82c1c363e03e4` **MATCH** |
| LDG-REFUSE-02 | `out/A2-346-manual-je-nomanual.json` 595B `8c25952d36d3f210` **MATCH** | `out/A2-346-manual-je-nomanual.req` 372B `26d581ea3feeac7f` **MATCH** |

All paths under `.softhouse/capture/tierA-a2/`. **All six response artefacts carry an `.http`
sidecar**, i.e. all six are new A2-3xx wire captures, **not** one of the 147 pre-existing
observations that have no `.req`. Task item (6)'s "did it PREFER the A2-3xx captures" — **yes,
exclusively.**

**Per-cell sweep.** Every promoted `amount_major_text` was swept as a fixed string in the response
artefact, and the promoted `amount_minor` re-derived from it by **exact string concatenation at
2 decimal places** (no float anywhere in my checker either):

```
LDG-01  gl 16 10300 DEBIT   100000.250000 -> 10000025   grep -aF '"amount":100000.250000'  in A2-347 = 1
LDG-01  gl 17 10400 DEBIT    25000.370000 ->  2500037   grep -aF '"amount":25000.370000'   in A2-347 = 1
LDG-01  gl 21 99008 CREDIT  125000.620000 -> 12500062   grep -aF '"amount":125000.620000'  in A2-347 = 1
LDG-02  gl  4 10201 CREDIT  270450.580000 -> 27045058   grep -aF '"amount":270450.580000'  in A2-338 = 1
LDG-02  gl  8 40100 CREDIT   22049.420000 ->  2204942   grep -aF '"amount":22049.420000'   in A2-338 = 1
LDG-02  gl 10 40300 CREDIT    7500.000000 ->   750000   grep -aF '"amount":7500.000000'    in A2-338 = 1
LDG-02  gl 16 10300 DEBIT   300000.000000 -> 30000000   grep -aF '"amount":300000.000000'  in A2-338 = 1
LDG-03  gl  4 10201 CREDIT  889549.420000 -> 88954942   grep -aF '"amount":889549.420000'  in A2-383 = 1
LDG-03  gl  8 40100 CREDIT   20298.820000 ->  2029882   grep -aF '"amount":20298.820000'   in A2-383 = 1
LDG-03  gl  6 20100 CREDIT   90151.760000 ->  9015176   grep -aF '"amount":90151.760000'   in A2-383 = 1
LDG-03  gl 16 10300 DEBIT  1000000.000000 -> 100000000  grep -aF '"amount":1000000.000000' in A2-383 = 1
LDG-04  gl  1 10000 DEBIT   100000.250000 -> 10000025   grep -aF '100000.250000'           in A2-390 = 8
LDG-04  gl 21 99008 CREDIT  100000.250000 -> 10000025   (same artefact; see below)
```

`LDG-04`'s artefact is a DB read-back, not a REST body, so `"amount":…` does not occur in it; the
value occurs eight times as raw text. I therefore resolved LDG-04's two legs **by row**, not by
token count:

```
$.journal_entries[*] where transaction_id == "a28f573ffb9b"
  {"id":48, "type_enum":2, "account_id":1,  "gl_code":"10000", "amount_text":"100000.250000", …}
  {"id":49, "type_enum":1, "account_id":21, "gl_code":"99008", "amount_text":"100000.250000", …}
$.accounts[?(@.id==1)] -> {"gl_code":"10000","name":"Assets","account_usage":2, …}
```

`JournalEntryType` in the pinned checkout is `CREDIT(1) / DEBIT(2)`
[`fineract-core/.../journalentry/domain/JournalEntryType.java:22-23`], and `GLAccountUsage` is
`DETAIL(1) / HEADER(2)` [`fineract-core/.../glaccount/domain/GLAccountUsage.java:27-28`]. So
`type_enum 2` on `account_id 1` is a **DEBIT to a HEADER account**, exactly as LDG-04 promotes.

**Both totals on all four parity vectors recompute from the promoted legs**, in integer minor
units: `12500062 / 12500062`, `30000000 / 30000000`, `100000000 / 100000000`, `10000025 /
10000025`.

**Both refusal vectors' three cells are byte-present in their artefacts**, status also in the
`.status` sidecar:

```
LDG-REFUSE-01  403 / error.msg.glJournalEntry.invalid.mismatch.debits.credits
               / "Sum of All Debits must equal the sum of all Credits for a Journal Entry"   all found
LDG-REFUSE-02  403 / error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted
               / "Target account does not allow manual adjustments"                          all found
```

**PROMOTED CELLS SWEPT: 27. NOT BYTE-PRESENT OR ARITHMETIC-FAIL: 0.**

---

## F-A2-34-3 — LOW: PART TWO of the three-part citation resolves by FILE NAME on the three most important parity vectors

Task item (1) asks whether the exclusion carries T233's three-part citation that **resolves**.
It does — `citationReasons` at `nexus/internal/apps/ledger/conformance/admit.go:384-441` checks
all three parts and I drove the third red (RD-7 below). But **part two has a three-tier fallback**
that T233's loanschedule version does not: artefact bytes → `.http` sidecar → **file name**.
Measured, per component:

| case_id | RESP tier | REQ tier |
|---|---|---|
| LDG-01 | **3 FILE NAME** | 2 `.http` sidecar |
| LDG-02 | **3 FILE NAME** | 2 `.http` sidecar |
| LDG-03 | **3 FILE NAME** | 2 `.http` sidecar |
| LDG-04 | 1 artefact bytes | 2 `.http` sidecar |
| LDG-REFUSE-01 | 2 `.http` sidecar | 2 `.http` sidecar |
| LDG-REFUSE-02 | 2 `.http` sidecar | 2 `.http` sidecar |

**The file-name tier is tautological**: `capture_ref`'s basename and `capture_case_id` are both
authored by the promoter from the same string, so a citation can satisfy tier 3 by construction.
Three of twelve components land there, and they are the response artefacts of the three
multi-leg parity vectors.

**Why this is LOW and not MEDIUM.** The `sha256` check in the same function is the real anchor and
it is exact — a mis-cited artefact fails on the digest long before the case-id tier is reached, and
I confirmed all twelve digests match. The fallback is also *documented and argued* in
`vector.go:153-157` ("a JSON response body does not name its own case id"), which is true: I
verified `A2-347`, `A2-338` and `A2-383` do not contain their own case id in their bytes, and
their `.http` sidecars do not either. So tier 3 is not laziness; it is the only tier those
artefacts can reach. **The finding is that the report should not describe part two as equivalent
to T233's "found at byte offset N", because for these three it is not.**

---

## F-A2-34-4 — MEDIUM: a gap sentence the harness PRINTS ON EVERY RUN is measurably FALSE

`report.go:835-837` prints, unconditionally, pass or fail:

> `* ACCRUAL IS ENTIRELY UNGRADED. … and INTEREST_RECEIVABLE / FEES_RECEIVABLE /`
> `PENALTIES_RECEIVABLE (gl 18, 22, 16) have ZERO journal entries.`

Measured on the live oracle **today, at `d039d29`**, whole table, not a sample:

```sql
SELECT account_id, count(*) FROM acc_gl_journal_entry GROUP BY account_id ORDER BY account_id;
  gl 18 ->  0 rows
  gl 22 ->  0 rows          (absent from the result set entirely)
  gl 16 -> 16 rows          <-- the MOST of any account in the ledger
```

**`gl 16` is not merely non-zero: it has more journal entries than any other account, and it is a
promoted leg of LDG-01, LDG-02 and LDG-03** — three of the four parity vectors this same report
has just printed as PASS, four lines above.

The *intended* claim is true. `gl 16` is mapped to slot **9 = `PENALTIES_RECEIVABLE`** on product
28 only (`AccountingConstants.AccrualAccountsForLoan`, `PENALTIES_RECEIVABLE(9)`,
[`fineract-core/.../common/AccountingConstants.java:105`]), and to slot **1 = `FUND_SOURCE`** on
products 46 and 55. All 16 of its rows arrive through `FUND_SOURCE`; **zero arrive through the
receivable slot**, and product 28 has no loan (`m_loan` carries no `product_id = 28`; loans 1–7 are
products 22, 22, 27, 24, 46, 46, 55). So *accrual is entirely ungraded* stands.

**But the sentence as printed is a claim about journal-entry counts on three accounts, and it is
wrong on one of them, in the direction that understates activity.** A reader calibrating the
harness's limits from this block would conclude gl 16 is untouched when it is the account this
corpus exercises most. The same sentence is in `capabilities-ledger.json`
(`ledger.accrual.entry.evidence`: *"gl 18, 22 and 16 carry ZERO journal entries"*) and in the
handoff §9 gap 1, so it is wrong in three places.

**MEDIUM, not LOW**, because P-40 makes the printed statement of limits the one thing that may not
be narrowed or fudged, and this is the block that carries it. **Not HIGH**: no graded cell, no
money value and no verdict depends on it.

**A2-15 got the neighbouring one RIGHT, against its own brief.** My brief called gl 17
*"INTEREST_RECEIVABLE/FEES_RECEIVABLE_SUSPENSE"*; A2-15 wrote **`TRANSFERS_SUSPENSE`**, and the
source agrees — `TRANSFERS_SUSPENSE(10)` and `acc_product_mapping` maps gl 17 at
`financial_account_type = 10` on all eight products. gl 17's **4** journal-entry rows (ids 34, 39,
46, 51) are **all `manual_entry = t`**, so *"reached only as a MANUAL target, no accounting-path
entry"* is confirmed by measurement.

---

## F-A2-34-5 — MEDIUM: the SIXTH gap A2-15 added itself is NOT printed on every run, contrary to the handoff

Task item (4), and the brief's *"a gap that quietly vanished between brief and handoff is a
finding"*. A2-15's handoff §9 states the five brief gaps, then adds a sixth of its own — **slot
resolution is graded by nothing** — and says of the set: *"the harness prints all of them on every
run, pass or fail."*

`capabilities-ledger.json` carries **eight** `in_graded_domain: false` rows:

```
ledger.slot.resolution        ledger.accrual.entry           ledger.transfers.suspense
ledger.charge.off             ledger.multi.currency.entry    ledger.opening.balance.and.closure
ledger.reversal.entry         ledger.running.balance
```

The printed block (`report.go:834-849`) carries **six bullets**: accrual, transfers-suspense,
charge-off, multi-currency, opening-balances/`GLClosure`, and no-balance-graded (G-12). Swept the
full 412-line transcript of my own run:

```
LC_ALL=C /usr/bin/grep -n -aiF 'slot' /tmp/a234-run-full.txt
  37:  ledger-invariants: CENSUS hold-named func: …/slots_test.go:187 …
  67:  ledger-invariants: …/slots_test.go:187 TestPlaceholderDisjointnessHolds is counted
 365:  * CHARGE-OFF IS UNMAPPED on both admissible products, so the charge-off income slots are
```

**`ledger.slot.resolution` is never named in the report.** Neither is `ledger.reversal.entry`.
Two of eight not-graded capabilities are invisible to a reader of the run.

**The structural half is the real finding.** `report.go:834-849` is **hardcoded prose**, not
derived from `capabilities-ledger.json`. Nothing ties the printed block to the capability rows, so
a future task can add a `in_graded_domain: false` row and the printed limits will not move — which
is the "gap quietly vanishes" defect one level in, sitting inside the mechanism built to prevent
it. `TestCellVocabularyIsDerivedFromTheComparator` derives the *cell* vocabulary from the
comparator; there is no equivalent deriving the *gap* block from the registry.

The gap is genuinely **stated** — in `capabilities-ledger.json`, in the handoff, and enforced as a
default-deny (a vector claiming `ledger.slot.resolution` is refused). So this is not a vanished
gap. It is an **overstated handoff sentence** plus an **underived report block**.

---

## F-A2-34-6 — LOW: the pin gate's diagnostic prints an EMPTY measured value when the ledger population is zero

Driving RD-10 (every ledger vector deleted), the gate refuses correctly — but reads:

```
conformance:   exemption census MISMATCH: LEDGER parity vectors        = , but this file pins 4.
conformance:   exemption census MISMATCH: LEDGER money cells compared  = , but this file pins 21.
conformance: EXIT 2 — no verdict is available. This is NOT a pass.
```

The measured term is the empty string, not `0`. The **gate still fires** (empty ≠ 4), so it is
load-bearing in the direction that matters, and the report does separately print
`NO LEDGER VECTOR IS IN THIS STORE, so NOTHING in this run grades a GL account, a mapping, …`.
But a diagnostic whose measured value is blank is one string-comparison change away from
`[ "" = "" ]` semantics somewhere. LOW.

**Noted alongside it, and it validates A2-15's own §7 argument:** with all six ledger vectors
deleted the **VERDICT LINE STILL READS `PASS (exit 0)`** and only the population pins turn the run
red. A2-15 predicted exactly this and pinned the population for exactly this reason. Confirmed by
driving.

---

## F-A2-34-7 — LOW: the six registered WRONG ledger implementations are not reachable through `conformance.sh`

```
$ bash .softhouse/conformance.sh --ledger-impl ledger-wrong-truncating
conformance: unknown option --ledger-impl
$ bash .softhouse/conformance.sh -ledger-impl ledger-wrong-truncating
conformance: unknown option -ledger-impl
```

`-ledger-impl` is a flag on the Go binary only. And `conformance.sh` **never runs `go test`** —
stated in its own comment at line 856, as a deliberate P-45 position. So DEC-2 precondition P-10's
"executable counterfactual" machinery is exercised by `TestEveryWrongImplementationIsKilled` under
`go test ./...`, which is a **separate BAR line** from the harness run.

This is **disclosed** — A2-15's handoff §10 says its CASE 8 "must select an implementation by name
and therefore drives the binary directly". It is not a defect: `go test -count=1 ./...` is in the
BAR and it is green. The finding is for the reader: **a green `conformance.sh` run does not
execute a single one of the six wrong implementations.** Anyone who equates "the harness" with
`conformance.sh` will overrate what a green run proves.

I drove all six myself through the binary — see §3.

---

## F-A2-34-8 — LOW: "money cells" is used with two different denominators in one handoff (P-67)

Handoff §6 reports *"10 of the 13 promoted money cells carry non-zero minor units"*. Handoff §7
pins `EXEMPTION_PIN_LEDGER_MONEYCELLS = 21` and derives it as legs + totals. The harness reports
**21**. Both are correct about different populations; the same two words name both.

**I counted both terms in the live artefacts** (`census-nonvacuity.py`, committed):

| case_id | class | legs | DR | CR | money cells | with non-zero minor units |
|---|---|---:|---:|---:|---:|---:|
| LDG-01 | parity | **3** | 2 | 1 | 5 | 5 |
| LDG-02 | parity | **4** | 1 | 3 | 6 | 2 |
| LDG-03 | parity | **4** | 1 | 3 | 6 | 3 |
| LDG-04 | parity | **2** | 1 | 1 | 4 | 4 |
| LDG-REFUSE-01 | oracle-refusal | 0 | — | — | 0 | 0 |
| LDG-REFUSE-02 | oracle-refusal | 0 | — | — | 0 | 0 |

- **13 legs** across 4 entry-asserting vectors. Leg distribution: **two 4-leg, one 3-leg, one 2-leg**.
- **21 promoted money cells** (13 legs + 8 totals) — matches the pin and the harness exactly.
- **10 of the 13 legs** carry non-zero minor units. **14 of the 21 money cells** do. 7 of 21 are whole tugriks.
- **3 of 4** entry-asserting vectors have more than two legs.

---

## 1. The nine graded items

### (1) `glAccountType` — EXCLUDED, and the instability is in the VECTOR'S OWN note. CONFIRMED.

A2-15 took option **(a)**. Measured in the files, not the handoff:

```
LDG-01  excluded_fields per leg: [['gl_account_type'], ['gl_account_type'], ['gl_account_type']]
LDG-02  [['gl_account_type'] x4]      LDG-03  [['gl_account_type'] x4]      LDG-04  [['gl_account_type'] x2]
LDG-REFUSE-01 []      LDG-REFUSE-02 []      (no legs, so nothing to exclude)
```

**Every parity vector's own `_note` carries the observation**, not only the handoff — swept per
vector as fixed strings:

| vector | `glAccountType` | `A2-088` | `G-12` | `running_balance` | `NO BALANCE IS GRADED` | `fetchRunningBalance=true is HTTP 500` |
|---|---|---|---|---|---|---|
| LDG-01 / 02 / 03 / 04 | Y | Y | Y | Y | Y | Y |
| LDG-REFUSE-01 / 02 | N | N | **Y** | **Y** | **Y** | **Y** |

The refusal vectors legitimately omit the classification sentences (they have no legs) and
**still carry all four G-12 sentences**.

**The cost is stated and not narrowed**, in the vector: *"no vector in this store grades a GL
account's classification at all, so a port that resolves the entry's classification WRONGLY is not
caught here."* The classification each account rendered at capture time is recorded for the record
and graded by nothing. I confirmed those recorded classifications against the live oracle:
gl 4 = 1 (ASSET), gl 8 = 4 (INCOME), gl 10 = 4, gl 16 = 1, gl 17 = 1, gl 21 = 2 (LIABILITY),
gl 6 = 2, gl 1 = 1 — every one matches its note.

**The exclusion is CLOSED and ENFORCED, driven red by me** (RD-6, RD-7 below).

### (2) NON-VACUITY. CONFIRMED, and the corpus A2-26 fixed was not re-created.

Numbers in F-A2-34-8. **Both** four-leg transactions in the oracle are promoted, the three-leg
manual entry is promoted, and both promoted 2-leg-equivalent amounts carry minor units. The two
whole-tugrik two-leg entries (`L21` disbursement, `L23` fee) were deliberately **not** promoted
and the refusal is recorded in `capabilities-ledger.json`.

**Driven red — see §3 RD-1 and RD-2.** One minor unit on a promoted leg is a MONEY kill with
`margin -1 minor units` through `bash .softhouse/conformance.sh`, and I-2 alone goes VIOLATED
while I-1 HOLDS.

### (3) INTEGER MINOR UNITS. CONFIRMED across ALL SIX, not a sample.

Parsed every scalar in all six vectors with `json.loads(..., parse_float=…)`, which tags **any**
decimal-pointed or exponent JSON number:

```
decimal-pointed JSON NUMBERS across the six ledger vectors: 0
python-float-typed values across the six ledger vectors:   0
```

Every money-bearing field is a **JSON string**: 13 `amount_minor` (`"27045058"`), 13 request +
13 expect `amount_major_text` (`"270450.580000"`, the oracle's own scale-6 characters preserved as
text), 12 totals, 6 `transaction_amount_major_text`. **`type=str` on every one, all 60 fields
listed in `check-money-and-additive.sh`'s output.**

Go side: `AmountMinor string \`json:"amount_minor"\`` (`vector.go:360`),
`TotalDebitsMinor string` (`vector.go:416`). The only `float64` tokens anywhere in the new package
are **two comments** (`impl.go:33`, `vector.go:250`) warning against it. `go vet` clean;
the harness's own `no-float census` inspected **6 Go packages / 54 Go files / 116 692 tokens /
240 import specs** under `nexus` and reports **0 forbidden identifiers, 0 floating-point or
imaginary LITERALS, 0 forbidden imports, 0 unscannable files**, with
`covered: nexus/internal/apps/ledger/conformance` printed by name.

`guard_no_float_in_vectors` is a HARD guard preceding the probe line. **I tested probe PRESENCE
first, per the brief**: line 85 of my transcript reads
`conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`.
So exit 0 here is a real pass, not a silent guard failure.

### (4) THE DECLARED GAPS. Five stated and printed; the sixth stated but not printed — F-A2-34-5. One printed sentence false — F-A2-34-4.

Independently re-measured against the live oracle:

1. **Accrual** — product 28 is the only `accounting_type = 3` (ACCRUAL_PERIODIC) product; `m_loan` has **no** row with `product_id = 28`. gl 18 and gl 22 have **0** journal entries. **gl 16 has 16** — F-A2-34-4.
2. **`TRANSFERS_SUSPENSE` gl 17** — 4 rows, **all `manual_entry = t`**. Confirmed.
3. **Charge-off** — `acc_product_mapping` for product 55 lists `financial_account_type` ∈ {1,2,3,4,5,6,10,11,12,13}. **`CHARGE_OFF_EXPENSE(16)` is absent**, as are 14/15/17/18. Confirmed unmapped.
4. **Multi-currency** — `SELECT DISTINCT currency_code FROM acc_gl_journal_entry` over all 60 rows returns `MNT` and nothing else. Confirmed.
5. **No opening balances / no `GLClosure`** — neither refusal is in the capture corpus. Confirmed by absence of any such artefact under `.softhouse/capture/tierA-a2/out/`; scope stated: that directory only.
6. **Slot resolution** — stated in `capabilities-ledger.json`, **not printed**. F-A2-34-5.

### (5) G-12 / RUNNING BALANCES. Both halves CONFIRMED, and I re-measured the third claim myself.

**Half one — nothing is graded.** Four independent mechanisms, all verified in the tree:

- the schema has **no field** for either column (`PostedEntry` carries none);
- every vector's `_note` says so — **6 of 6**, table in (1) above;
- `admit.go:107` refuses a vector whose note claims to grade `office_running_balance` or `organization_running_balance`;
- `conformance_test.go:238-239` fails the build if the comparator ever emits the cell.

**Half two — the vector says so.** Confirmed, all six, including both refusal vectors.

**`fetchRunningBalance=true` — I did not inherit this, I issued it.** Live, today, `d039d29`:

```
curl -sk -u mifos:password -H "Fineract-Platform-TenantId: gerege" \
  "https://localhost:8443/fineract-provider/api/v1/glaccounts?fetchRunningBalance=true"
-> HTTP 500
   {"timestamp":"2026-08-22T08:59:44.313Z","status":500,"error":"Internal Server Error",
    "path":"/fineract-provider/api/v1/glaccounts"}
```

Source cause confirmed at
`fineract-accounting/.../GLAccountReadPlatformServiceImpl.java:128-131` —
`group by account_id desc, id` and `group by t2.account_id desc`, **MySQL-only `GROUP BY … DESC`**,
invalid on PostgreSQL. **The endpoint has therefore never worked on the only database this program
permits, and A2-15 built nothing on it.** Its capture `q7-a2-15-ledger-state-json.sql` deliberately
does not project either column; I confirmed `A2-390`'s `journal_entries` rows carry no
running-balance key (keys are `id, transaction_id, transaction_date, type_enum, account_id,
gl_code, gl_name, gl_classification_today, amount_text, currency_code, manual_entry, reversed,
reversal_id, entity_type_enum, entity_id, loan_transaction_id`).

### (6) ADMISSIBILITY. Nothing from an inadmissible product. A2-3xx captures preferred, exclusively.

```
LDG-01 product_id=0    (manual)     LDG-02 product_id=55   ADMISSIBLE
LDG-03 product_id=55   ADMISSIBLE   LDG-04 product_id=0    (manual)
LDG-REFUSE-01 / -02    product_id=0 (manual)
PIN-ledger.json inadmissible_product_ids = [22, 23, 24, 27, 28]
```

**The denylist is enforced as DATA**, not a comment (G-10 option (c)), and `TestInadmissible
ProductsAreRefused` exists. The live oracle confirms the denylist's ground: `acc_product_mapping`
shows products **22, 23, 24, 27, 28** — and only those — still pointing `financial_account_type = 1`
at **gl 2**, whose `classification_enum` is now **4 (INCOME)** after the G-10 retype. Loan 7 →
product 55 → `accounting_type = 2` (CASH_BASED), matching the vector.

Every vector cites a `.req` (or `.http` request block). **None of the 147 no-`.req` observations is
cited.**

*[UNVERIFIED BY ME]* I did **not** re-POST the five inadmissible mappings to re-observe the 403.
Re-sending a mapping mutates the oracle, and a reviewer doing that would contaminate the corpus its
subject was graded on. A2-26's observation (A2-300..A2-315) is inherited; the *ground* for it —
gl 2 retyped to INCOME under five live mappings — I measured directly, above.

### (7) THE HEADER-ACCOUNT ACCEPTANCE. CONFIRMED; the corpus does not "improve on" the oracle.

```
A2-345-manual-je-header.req    debits [{glAccountId: 1, amount: 100000.25}]
                               credits[{glAccountId: 21, amount: 100000.25}]
A2-345-manual-je-header.status 200
A2-345-manual-je-header.json   {"officeId":1,"transactionId":"a28f573ffb9b"}
acc_gl_account id=1 -> gl_code 10000, "Assets", account_usage = 2 (HEADER), parent_id NULL
```

`LDG-04` encodes `http_status: 200` and the two legs the oracle actually created. There is **no
contract-refusal** for header postings anywhere in the ledger schema. **A port that refuses is
killed**: driving `-ledger-impl ledger-wrong-header-refusing` gives
`ledger parity PASS 3 FAIL 1`, with `LDG-04-header-account-accepted … FAIL 1 cells`. §3 RD-C2.

### (8) THE EXEMPTION CENSUS. Pins DELIBERATE and ARGUED, not retro-fitted. CONFIRMED.

**The test for "argued, not retro-fitted" is whether a reviewer can recompute the figure from the
corpus's structure without running the harness.** I did:

| pin | value in `conformance.sh` | my independent recomputation from the six .json files |
|---|---|---|
| `EXEMPTION_PIN_LEDGER_DECLARED` | 0 | 0 — every vector's `invariant_exemptions` is `[]` |
| `EXEMPTION_PIN_LEDGER_PARITY` | 4 | 4 — `class == "parity"` |
| `EXEMPTION_PIN_LEDGER_REFUSAL` | 2 | 2 — `class == "oracle-refusal"` |
| `EXEMPTION_PIN_LEDGER_MONEYCELLS` | **21** | **21** — 3+2, 4+2, 4+2, 2+2, 0, 0 |

Each carries a written derivation **in `conformance.sh` beside the constant** (lines 500-553),
including the deflation argument for why the population is pinned and not only the exemption count.

**Both drift directions driven red by me**, through `bash .softhouse/conformance.sh`:

```
RD-4 DEFLATION (delete LDG-04):
  exemption census MISMATCH: LEDGER parity vectors       = 3, but this file pins 4.
  exemption census MISMATCH: LEDGER money cells compared = 17, but this file pins 21.
RD-5 INFLATION (plant a 7th vector):
  exemption census MISMATCH: LEDGER parity vectors       = 5, but this file pins 4.
  exemption census MISMATCH: LEDGER money cells compared = 26, but this file pins 21.
```

The five **original** pins are unchanged at 4/4/4/0/0 and all read `== pinned` in my run.

### (9) THE 46 loanschedule VECTORS UNDISTURBED, AND THE CHANGE PURELY ADDITIVE. CONFIRMED by re-running, and by tree hash.

**Verified by re-running** (task item 9's requirement), not by reading the diff:

```
unfiltered:  parity 46 PASS / 0 FAIL · contract-refusal 4 / 0 · self-test 1 / 0
             cells compared 7884 graded, 93 ungraded · kills 106 money, 7 structural
             refused 0 · inadmissible 0 · harness errors 0
filtered:    bash .softhouse/conformance.sh loanschedule -> PASS exit 0, 46 / 4 / 0, 7863 cells
```

**And by tree hash**, across the A2-15 merge `a072ecd → d76594a`:

```
.softhouse/vectors/loanschedule   before ee2461724df0  after ee2461724df0   IDENTICAL   HEAD ee2461724df0
.softhouse/vectors/_selftest      before 1e1e29f9b952  after 1e1e29f9b952   IDENTICAL   HEAD 1e1e29f9b952
.softhouse/vectors                before 73c3ea7b43dd  after 8968c559fa61   MOVED       HEAD 8968c559fa61
.json count under vectors/loanschedule: before 50, after 50
```

**Purely additive under `.softhouse/vectors`** — `git diff --name-status a072ecd d76594a --
.softhouse/vectors` gives **eight lines, every one an `A`**, zero `M`, zero `D`:

```
A .softhouse/vectors/PIN-ledger.json
A .softhouse/vectors/capabilities-ledger.json
A .softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json
A .softhouse/vectors/ledger/LDG-02-repayment-split-4leg-minor-units.json
A .softhouse/vectors/ledger/LDG-03-overpayment-4leg-minor-units.json
A .softhouse/vectors/ledger/LDG-04-header-account-accepted.json
A .softhouse/vectors/ledger/LDG-REFUSE-01-unbalanced-by-one-minor-unit.json
A .softhouse/vectors/ledger/LDG-REFUSE-02-manual-adjustments-not-permitted.json
```

**The store digest moved for the vectors A2-15 added AND FOR NOTHING ELSE.**
`git diff --stat a072ecd d76594a -- nexus/internal/apps/loanschedule/contract/contract.go` is
**empty**; `-- docs/adr/` is **empty**.

---

## 2. THE BAR — every line OBSERVED by me at `d039d29`

| BAR item | brief says | I OBSERVED |
|---|---|---|
| probe line PRESENT, reads `up` | yes | **PRESENT**, transcript line 85, `probe = up` |
| `VERDICT` | PASS exit 0 | **`VERDICT: PASS (exit 0)`**, `EXIT=0` |
| loanschedule parity / cells | 46 / 7884 | **46 PASS 0 FAIL** / **7884 graded, 93 ungraded** |
| contract-refusal / self-test | 4 / 1 | **4 PASS 0 FAIL** / **1 PASS 0 FAIL** |
| ledger parity / oracle-refusal / money cells | 4 / 2 / 21 | **4 PASS 0 FAIL** / **2 PASS 0 FAIL** / **70 graded, 21 MONEY** |
| refused / inadmissible / harness errors | 0 / 0 / 0 | **0 / 0 / 0** |
| invariant violations | 0 | **0** |
| invariant assertions NOT RUN | 0 | **0** (`NONE — every invariant assertion ran`) |
| original census pins | 4/4/4/0/0 `== pinned` | **4/4/4/0/0, all `== pinned`** |
| new ledger pins | 0 / 4 / 2 / 21 `== pinned` | **0 / 4 / 2 / 21, all `== pinned`** |
| `--prove` | 23 / 0 | **`PROOFS: 23 passed, 0 failed`**, exit 0 |
| `go build ./...` | 0 | **exit 0** |
| `go vet ./...` | 0 | **clean** |
| `go test -count=1 ./...` | ok | **ok** — ledger 0.545s, ledger/conformance 2.952s, loanschedule 8.042s, loanschedule/conformance 71.195s |
| `gofmt -l` | exactly `contract.go` | **exactly `internal/apps/loanschedule/contract/contract.go`** (never `gofmt -w`, G-3 honoured) |
| store digest | `8968c559…` | **`8968c559fa613e8642ab030bd0a029c17d147054`** |
| ledger invariants | — | **0 violations, 11 non-vacuous assertions, 10 INDEPENDENT** |
| ledger kills named | — | **6 money, 10 structural** |

**Every BAR figure the driver circulated is reproduced.** The one line that differs from the
dispatch is the commit id it was measured at — F-A2-34-1.

---

## 3. THE RED DRIVES — mine, not A2-15's

Instruments: `red-drive-a2-34.sh`, `red-drive-b-a2-34.sh`, `red-drive-c-a2-34.sh`, committed
beside this file; transcripts under `/tmp/a234-red/`. I did **not** run, source or read
`red-green-a2-15.sh` for any verdict. Every perturbation is **proven applied** before its case
runs; every case asserts a **diagnostic line**, not an exit code alone (P-62); the revert is
**proven by digest**, not assumed.

```
START ledger vector digest 265ebedf0499cadd
END   ledger vector digest 265ebedf0499cadd     revert VERIFIED byte-identical
git status --porcelain .softhouse/vectors/  ->  (empty)
CONTROL 0 (before) PASS exit 0 · CONTROL 1 (after) PASS exit 0     — anti-no-op, both ends
```

**Through `bash .softhouse/conformance.sh`:**

```
RD-1  ONE MINOR UNIT on a promoted expectation leg (LDG-02 principal 27045058 -> 27045059)
      RED, exit 2:  legs[0].amount_minor: MONEY want 27045059, got 27045058 (margin -1 minor units)
                    ledger parity           PASS 3    FAIL 1
      >>> the double-entry / money assertion is WIRED and I have SEEN IT FAIL.

RD-2  I-2 ALONE. LDG-03's recorded requested total 1000000 -> 1000000.01
      RED, exit 2:  INVARIANT splits_sum_to_whole      VIOLATED
                    INVARIANT double_entry_balances    HOLD      <-- I-1 still green
      >>> I-2 is NOT a restatement of I-1. Driven, not asserted.

RD-4  DEFLATION: delete LDG-04  -> LEDGER parity vectors = 3 vs pinned 4; money cells 17 vs 21. exit 2.
RD-5  INFLATION: plant a 7th    -> LEDGER parity vectors = 5 vs pinned 4; money cells 26 vs 21. exit 2.
RD-10 delete ALL SIX            -> "NO LEDGER VECTOR IS IN THIS STORE"; pins refuse; exit 2.
                                   (verdict line still read PASS — the pins are what turn it red)

RD-6  EXCLUSION IS CLOSED: add "amount_minor" beside "gl_account_type" in excluded_fields
      RED, exit 2:  LDG-01 … INADMISSIBLE  0 cells (0 money) · ledger inadmissible 1
      >>> widening the exclusion is a REFUSAL, not a silent ungrading.

RD-7  THE NOTE REQUIREMENT IS ENFORCED: strip the reason from LDG-01's _note, keep the exclusion
      RED, exit 2:  LDG-01 … INADMISSIBLE · ledger inadmissible 1
      >>> the "instability is in the vector's own note" rule is code, not convention.

RD-8  A DECLARED EXEMPTION ON A LEDGER VECTOR (this is what A2-15's counter-claim 1 rests on)
      RED, exit 2:  LDG-02 … INADMISSIBLE
        "this vector declares 1 invariant_exemptions and THIS SCHEMA ADMITS NONE. The loanschedule
         schema has a grounding classifier behind its exemptions (T222/T225/T230/T233) …; this
         schema has no such classifier, so admitting an exemption would switch an invariant off
         with nothing checking that the thing it excuses is visible in the record.
         Re-observe rather than exempt (P-8)"
        ledger exemptions  1 DECLARED …
      >>> a REAL default-deny, quoted from the ledger section, not from the stock summary line.
```

**Through the binary** (`-ledger-impl`; see F-A2-34-7 for why this route is separate). Control
first: the CORRECT implementation on the same route is **exit 0, `ledger parity PASS 4 FAIL 0`**.

```
ledger-wrong-truncating            exit 1  parity PASS 0 FAIL 4
   legs[0].amount_minor: MONEY want 10000025, got 10000000 (margin -25 minor units)
   legs[1].amount_minor: MONEY want  2500037, got  2500000 (margin -37 minor units)
   legs[2].amount_minor: MONEY want 12500062, got 12500000 (margin -62 minor units)
   INVARIANT double_entry_balances VIOLATED: debits  30000000, credits  29999900   (LDG-02)
   INVARIANT double_entry_balances VIOLATED: debits 100000000, credits  99999800   (LDG-03)
   >>> I-1's VIOLATED branch REACHED. Both invariants have now been seen red.

ledger-wrong-header-refusing       exit 1  parity PASS 3 FAIL 1   LDG-04 FAIL   (item 7)
ledger-wrong-manual-permission-ignored exit 1  oracle-refusal PASS 1 FAIL 1
   refusal.code: want "…manual.adjustments.not.permitted", got ""
ledger-wrong-netting-totals        exit 1  parity PASS 0 FAIL 4
   total_debits_minor: MONEY want 12500062, got 0 (margin -12500062 minor units)
ledger-wrong-code-ignored          exit 1  parity PASS 0 FAIL 4
   legs[0].gl_account_code: want "10300", got ""                  (STRUCTURAL, not money)
ledger-wrong-split-drift           exit 1  parity PASS 2 FAIL 2
   INVARIANT splits_sum_to_whole VIOLATED: splits sum to  30000000, whole is  30000001
   INVARIANT splits_sum_to_whole VIOLATED: splits sum to 100000000, whole is 100000001
   >>> and double_entry_balances HOLDS on both. The I-2 independence proof, re-driven.
```

**All six registered wrong implementations die, each in the way its `graded_against` row claims.**
DEC-2 §5.2 requirement 7's conjunction is satisfied: a **structural** cell
(`legs[].gl_account_code`) **and** a **money** cell perturbed by exactly one minor unit, reported
as a money kill with a non-zero `margin_minor`.

---

## 4. A2-15's FOUR COUNTER-CLAIMS — adjudicated

### Claim 1 — *"Promoting a vector WILL move `EXEMPTION_PIN_*`" is FALSE.* **CONFIRMED. The argument is sound and the four new pins are ARGUED, not retro-fitted.**

**The argument.** A2-15 excludes a **cell** (`gl_account_type`), not an **invariant**. DEC-2 §4.4
makes exactly two invariants gradeable in this context — I-1 (debits == credits) and I-2 (splits
sum to whole). I read both assertion functions in `invariants.go` in full: **neither reads a GL
account's classification.** So there is nothing for an exemption to excuse, the ledger corpus
declares zero exemptions, and `UNDETERMINED-ON-THE-RECORD` stays at 0. **Sound.**

Independently: the five original pins read `4 / 4 / 4 / 0 / 0`, `== pinned`, in my own run.

**Retro-fitted or argued?** The discriminating test is whether a reviewer can recompute each figure
from the corpus's structure without running the harness. **I did, and all four matched** — table in
item (8). Each also carries a written derivation in `conformance.sh` beside the constant, and
**both drift directions are driven red** (RD-4, RD-5, RD-10). This is the opposite of retro-fitting.

The claim rests on the ledger schema's default-deny being real. **I drove it** — RD-8 above: a
planted `invariant_exemptions` entry on a real promoted vector comes back **INADMISSIBLE** with the
schema's own reason.

### Claim 2 — *"T230's rework does not fit A2-15's need."* **CONFIRMED, and stated plainly: T230's merged change serves no committed vector today.**

A2-15's reasoning is structural and correct: T230 reworked the **exemption grounding classifier**
(reclassifying a capture gap from INADMISSIBLE to `UNDETERMINED-ON-THE-RECORD`); A2-15 withdrew a
**cell** from grading. Different objects. **The ledger schema has no grounding classifier at all**
— confirmed by reading it and by RD-8's refusal text, which says so in its own words.

**And measured, in the whole store:**

```
conformance: exemption census READ: UNDETERMINED-ON-THE-RECORD = 0 == pinned 0
report:      0 UNDETERMINED-ON-THE-RECORD (a cell the invariant reads was never recorded; admitted, not evidence)
```

**Zero vectors in the committed store — loanschedule or ledger — are in the state T230's rework
exists to classify.** So T230's merged change is, today, serving nobody in the corpus. It is not
*unwired*: `exemption_test.go:303, 501, 555, 698` exercise it on synthetic fixtures, so the
classifier has real coverage. **It is unused.** T230 flagged the fit question `[UNVERIFIED]`
against itself; the answer is that A2-15 was not the caller, and no other caller exists yet.

### Claim 3 — *"I-2 was a restatement of I-1 and I fixed it."* **CONFIRMED, by driving it two ways.**

The vacuity is real and A2-15 found it before shipping: on an entry with one leg on one side and N
on the other, "splits sum to the whole" is character-for-character the equation I-1 asserts. The
fix carries the caller's **requested** transaction amount from the recorded `.req` bytes
(`"transactionAmount": 300000` / `1000000`) and holds the credit splits against **that**, which
nothing in I-1 reads.

**Driven by me, independently, two ways:**
- **RD-2** (my own perturbation): `1000000 -> 1000000.01` on LDG-03's requested total →
  `splits_sum_to_whole VIOLATED` while `double_entry_balances HOLD`.
- **`ledger-wrong-split-drift`**: keeps the entry internally balanced and moves the requested total
  by one minor unit → I-2 RED on LDG-02 **and** LDG-03, I-1 green on both.

**The honesty is also enforced in the report**, which I verified in my own run: LDG-01's I-2 line
prints `(1 assertion(s), DEPENDENT)` with a ⚠ and the sentence *"NOT a second piece of evidence"*,
and LDG-04's prints `N/A (0 assertion(s))` because a 2-leg entry is not a split shape. The summary
reads **`11 non-vacuous assertion(s) made, of which 10 are INDEPENDENT`**. A reader cannot count
two green lines as two assertions.

### Claim 4 — *"DEC-2 §4.4's reason for I-5 is stale, and I did not amend DEC-2."* **CONFIRMED on both halves. The restraint was CORRECT.**

**It really did not amend it.**

```
git log --oneline -3 -- docs/adr/DEC-2-gl-accounting-adapter.md
  cab9e82  A2-32: DEC-2 revision 5 — A2-31's two rejection-grade findings, and nothing else
  1b6b3cf  A2-28: DEC-2 revision 4 …
  ead328a  A2-21: DEC-2 revision 3 …
git diff --name-only 1325e8b~1 1325e8b -- docs/   -> (empty)
git diff --stat a072ecd d76594a -- docs/adr/      -> (empty)
```

**The stale sentence is still there**, at `docs/adr/DEC-2-gl-accounting-adapter.md:823`:

> **I-5** … **UNGRADED TODAY.** The A2 corpus contains **no reversal**: `A2-150`'s journal dump does
> not project `reversed` or `reversal_id` …

**It is false today.** Re-run of `q4-a2-26-ledger-state.sql` against the live oracle returns a
**reversal-pair projection with 8 rows**, three distinct reversal transactions:

```
original 33/34/35 (a28f54bfdaf3) reversed=t -> 38/39/40 (a28f54c1db73)
original 45/46/47 (a28f573f34c7) reversed=t -> 50/51/52 (a28f57412abb)
original 59/60    (a28f605fcdeb) reversed=t -> 63/64    (a28f614e0263)
```

The corrected reason lives in `invariants.go:36-46` and in `capabilities-ledger.json`
(`ledger.reversal.entry`), naming A2-348/A2-349 and stating what is still missing: I-5's semantic
half — *"a correction ADDS a leg pair; it never MUTATES one"* — is **not observable from a
snapshot**, because the read-back shows `reversed = true` **set on the original rows** and telling
"flags and adds" from "flags and rewrites" needs the write path. I confirmed that from the same
projection: `original_reversed = t` on rows 33/34/35/45/46/47/59/60, i.e. the original rows were
touched.

**Was the restraint correct? YES, and unambiguously.** DEC-2 rev 5 is **RATIFIED**. `CLAUDE.md`:
*"a ratified DEC-n still cannot be amended by an agent without raising a gate"*, and *"Any change
to a ratified DEC-n or the frozen adapter contract"* is a `user` gate. A test_writer amending a
ratified ADR mid-task would have been a rejection.

**Does the stale sentence warrant raising a gate? My recommendation: NO — it warrants a TASK, not a
gate.** The gate class for "amend a ratified DEC-n" exists to stop an agent changing what the ADR
*obliges*. This sentence changes nothing DEC-2 obliges: I-5 was ungraded before and is ungraded
now, `ErrNoDiscriminatingVector` is still the right refusal, and the graded domain does not move.
What is wrong is the **stated evidential reason**, which is now contradicted by the corpus — and a
future task reading §4.4 would go looking for a reversal capture that already exists. That is
**exactly the P-69 snapshot defect** DEC-2 itself warns about. The right disposal is a registered
task to carry the correction into DEC-2 §4.4 as **revision 6** through the normal ADR route, which
is what every previous DEC-2 revision (3, 4, 5) went through — each with a paired independent
review. **I did not amend it and I am not proposing an agent do so unilaterally.** A2-15's
placement of the correction in code, where it is beside the thing it describes and cannot be missed,
is the best available holding position.

---

## 5. WHAT I DID NOT VERIFY — marked, not hidden

1. **`[UNVERIFIED]` — the 403 on products 22/23/24/27/28.** I did not re-POST the five mappings; doing so mutates the oracle a reviewer is grading against. Inherited from A2-26 (A2-300..A2-315). I *did* measure the ground for it: `acc_product_mapping` still points those five, and only those five, at gl 2, whose `classification_enum` is now 4 (INCOME).
2. **`[UNVERIFIED]` — A2-29's MNT 2,000,000.00 running-balance drift.** Inherited. I did not re-drive the four organisation-wide recomputes. I verified the *consequences* A2-15 drew from it (nothing graded, four mechanisms, HTTP 500 on the endpoint) directly.
3. **`[UNVERIFIED]` — "no accrual or COB job has ever run."** I measured that product 28 has no loan and that gl 18/22 have zero journal entries, which is sufficient for the gap; I did not inspect job-execution tables.
4. **`[UNVERIFIED]` — the precedence between the two manual-entry refusals.** A2-15 flagged this itself and I **confirm the flag is warranted by measurement**: A2-344's legs are gl 16 and gl 21, both `manual_journal_entries_allowed = t`, and A2-346's request is *balanced* (100000.25 vs 100000.25) with gl 18 at `manual_journal_entries_allowed = f`. **No captured request violates both rules**, so nothing in this corpus can order them, and a port checking them in the other order passes both refusal vectors.
5. **`[UNVERIFIED]` — `MANIFEST.sha256` in `.softhouse/capture/tierA-a2/`.** A2-15 disclosed that it did not update it for A2-390 and that nothing gates on it. I did not re-sweep the repository for a consumer; A2-15's own scope statement (`.softhouse/conformance.sh` and `.softhouse/capture/lib/*.py`) stands unchallenged and unextended.
6. **`[UNVERIFIED]` — G-8's residue rule.** No capture carries a non-zero digit beyond two decimal places, so the truncate-or-round refusal is specified from source and killed by nothing. Unchanged by A2-15, restated here so it is not lost.

## 6. GAPS I LEAVE BEHIND

- The graded ledger domain is **six cases**. Accrual, account transfers, charge-off, multi-currency, opening balances, `GLClosure`, **slot resolution** and **reversal semantics** are ungraded — eight `in_graded_domain: false` rows, of which the report prints six (F-A2-34-5).
- **No vector in this store grades a GL account's classification.** A port that resolves classification wrongly is not caught. Stated in every vector.
- **No vector grades any balance.** By design, while G-12 is open.
- **Amount diversity is thin.** `100000.25` is leg[0] of LDG-01, **both** legs of LDG-04, and the request leg of both refusal vectors. A port with that value hard-coded passes more cells than it has earned. Not a defect in A2-15 — it is what the oracle contains — but a reason not to read "21 money cells" as 21 independent discriminations.
- **F-A2-34-4** (the false gl-16 sentence) and **F-A2-34-5** (the underived gap block) are the two I would register as follow-up tasks. Neither is a money defect. **I did not fix either** — A2-34 may not fix A2-15's work.
- **F-A2-34-1** is for the driver: reconcile `d1f74ae` against `main`, and stop predicting fork points.

---

*Every measured claim above was taken at `d039d29630b93a142f965b7936917c50e81aa6c2` against the
live reference oracle (Fineract, pinned `426a23544`) on PostgreSQL `fineract-db-1`, on 2026-08-22.
No number in this document was copied from A2-15's handoff without being re-measured.*
