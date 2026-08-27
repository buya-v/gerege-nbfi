# T320 — INDEPENDENT REVIEW OF T305 (merged `6798b070`, branch tip `0c6a5206`)

**Reviewer:** T320, branch `softhouse/T320-review-t305`, run `2026-08-21-run2-tierA-gl-accounting-A2`.
**Method:** re-derivation from the pinned Fineract source and from the captured oracle bytes; a
mutant the reviewer wrote; the bar re-run on this worktree; read-only SQL against the standing
oracle. Nothing was written to the standing reference oracle. **No T287 probe was fired**
(`acc_gl_closure` re-read = **0**, so a2-01/a2-02 remain armed and untouched).

---

## VERDICT — SPLIT

| part | verdict |
|---|---|
| **`LDG-05` the vector, and every money cell in it** | **APPROVED.** Re-derived from the oracle bytes, not from the vector. Faithful, integer-only, balanced. **DO NOT RETIRE.** |
| **The four-part admissibility argument (`FINDING.md` §4b.6), as written** | **MICRO-FIX + follow-up.** The CONCLUSION is right; two of its four legs do not carry the weight put on them, and the argument omits the one property that actually makes the capture admissible. Prose only — no graded cell moves. |
| **The prose correction "all three places corrected"** | **MICRO-FIX (1 line, mechanical).** There is a **FOURTH** place, in the same file T305 edited, three lines above the paragraph it rewrote. |
| **`nexus/.../conformance/admit.go` (the declared scope incursion)** | **REJECTED IN PART — routed to T306, not fixable here.** The predicate claim is TRUE. But T305 introduced an **undeclared** widening, two defects, and no red-drive; and **T306 has already run**, and its narrowing would make `LDG-05` INADMISSIBLE. |
| **The orphaned-branch rebuild** | **APPROVED.** Nothing lost, nothing silently reverted. Two of the handoff's factual claims about it are wrong. |
| **The bar** | **APPROVED, reproduced independently.** exit 0, probe line PRESENT reading `up`, 46 parity / 7884 cells, `LDG-05` PASS 27 cells (8 money), 11/11 wrong impls died. |

**On the question the task put front and centre — should `LDG-05` be RETIRED rather than exempted?
NO, and retirement would be a mistake.** The reasoning is in §1. It is not "the argument is fine";
it is that the argument's real load-bearing property is one T305 never states, and that property
holds, verifiably and mechanically.

---

## 1. THE MAIN EVENT — attacking `FINDING.md` §4b.6

T305's argument: (a) same image bytes; (b) ratified tenant arithmetic; (c) usual byte provenance;
(d) committed deterministic recipe. I attacked each.

### 1.1 Leg (a) — "THE CODE IS THE SAME BYTES … which is a measurable fact and was measured"

**[REFUTED as stated — the measurement is not in any artefact.]**

I grepped the entire rig for `docker inspect`, `{{.Image}}` and the image id
`e596339626bf`. Every hit is **prose**: a comment in `docker-compose.t305.yml:14-16`, the
vector `_note`, `LDG-05-note.txt`, `capability-tail.txt`. **No script measures an image id, and
no `out/` artefact records one — not the standing container's, and not the throwaway's.**
`guard-throwaway-isolation.sh` is fail-closed on ports (I1), container names (I2), named volumes
(I3), mount modes (I4) and the standing baseline (I5). **There is no I6 on image identity.**
[VERIFIED: `grep -rn 'docker inspect\|{{.Image}}\|e596339626bf' .softhouse/capture/t305-.../throwaway/`
→ 3 hits, all comments/prose; `out/STANDING-baseline.txt` records I1–I5 and no image id.]

Worse for leg (d): the compose file pins **`image: fineract:latest`** — a **mutable tag**, not a
digest. [VERIFIED: `docker-compose.t305.yml`, `services.fineract.image`.] So the claim
"`run-all.sh` rebuilds the instance **from the same image**" is true only for as long as nobody
re-tags `latest`. This is the **P-92** shape by the store's own name — *"a probe whose safety comes
from an EXTERNAL PRECONDITION rather than from its own content is a loaded weapon"* — transposed
from safety to evidence: the rig's **reproducibility** comes from an external precondition (the tag
has not moved) rather than from its own content, and **the rig would not notice** if it had.

**Severity: MEDIUM on the ARGUMENT, LOW on the VECTOR** — because of §1.4.

### 1.2 Leg (b) — "THE TENANT ARITHMETIC IS THE RATIFIED ONE"

**[VERIFIED as a fact. REFUTED as a load-bearing reason for THIS vector — it is inert.]**

The rounding mode is genuinely seeded at 4 and genuinely read back from the target by fence F3.
But **`LDG-05` performs no rounding at any point.** The three amounts carry exactly two decimal
places; the oracle stores them at scale 6 as `250000.250000` / `100000.370000` / `350000.620000`,
i.e. with four trailing zeros; the conversion to minor units is an exact split with a
zero residue. `MathContext(19, HALF_UP)` and `MathContext(19, HALF_EVEN)` produce
**byte-identical** output for this capture. So leg (b) is true and contributes **nothing**.

This matters, because leg (b) is also the ground on which the store disqualifies tenant `default`.
I verified `default` read-only: `rounding-mode = 6`, `Asia/Kolkata`, **0 journal entries, 0 GL
accounts, no financial-activity-300 mapping**. [VERIFIED: `psql fineract_default`, this fire.]
`default` is disqualified — but **not by its rounding mode**, which is inert here. It is
disqualified by `:708` throwing on the missing type-300 mapping, and that gap was *curable* by the
same four API calls the throwaway needed. **The real argument against `default` is the one
`FINDING.md` §5 makes and §4b.6 does not: taking the capture there would have spent a one-shot
pristine accounting surface on six undeletable journal entries, permanently.** That argument is
sound. §4b.6 should be citing it and is not.

**A future task must not cite "rounding mode" as a general off-tenant disqualifier.** For a vector
that does no rounding it disqualifies nothing.

### 1.3 Leg (c) — byte provenance

**[VERIFIED.]** I recomputed the sha256 of `OB-ACCEPT-01-readback-db.json` myself:
`aad8f3ed33ef50de87d9ee41d77ffbfdc74131561e955c5a4cf1ba05529abeff`, equal to both the recorded
`.sha256` sidecar and `provenance.capture_sha256` in the vector. Request bytes, response bytes,
status, `.http` sidecar and `captured-at-utc` are all present. Two INDEPENDENT oracle views agree:
the psql readback and `OB-ACCEPT-01-readback-rest.json` (which also carries the oracle's own
`currency.decimalPlaces: 2` for MNT — the minor-unit digit count is **observed**, not assumed).

### 1.4 THE ARGUMENT T305 DID NOT MAKE, AND IT IS THE ONE THAT DECIDES THE QUESTION

The task asks: *is a vector captured on a different tenant of a different instance admissible as
**parity** evidence for the `gerege` deployment?* The tenant seed differs — different GL account
ids, different codes, different office, an empty ledger against `gerege`'s 60 entries. That
objection is real and §4b.6 answers it only by disclaimer ("what is not claimed").

**The answer is mechanical, and T305 never states it: every graded cell of `LDG-05` is a function
of the vector's OWN INPUTS.** I checked all seven graded cell families against `grade.go:165-199`
and `impl.go:538-566`:

| graded cell | where its value comes from |
|---|---|
| `leg_count` | `request.legs` × the expansion rule |
| `legs[].gl_account_id`, `legs[].gl_account_code` | `request.legs[].gl_account_id` and `request.accounts` / `request.contra_gl_account_id` — the port reads `chart[req.ContraGLAccountID]` |
| `legs[].entry_side` | `request.legs[].entry_side` and `oppositeSide` |
| `legs[].amount_minor` | `request.legs[].amount_major_text` |
| `total_debits_minor`, `total_credits_minor` | sums of the above |

**Nothing in `LDG-05` grades a cell that only `gerege`'s database could supply.** The chart is an
INPUT the vector carries; the ledger state is an INPUT (`posted_non_contra_transaction_ids`, empty);
the office is an INPUT. `T305-1000` versus `gerege`'s codes is a closed loop *inside the vector*.
Contrast the cells this store deliberately refuses to grade for exactly this reason:
`errors[0].args` (26 tenant-specific ids), `office_running_balance` (gate G-12), `glAccountType`
(the account's *current* classification). Had `LDG-05` graded any of those, it would be
inadmissible off-tenant. It grades none of them.

**So the correct general rule, and the one that should go into `reference-oracle.md`'s fifth fold,
is not "same image id" — which is unmeasured, unguarded and tied to a mutable tag — but:**

> **An off-tenant capture is admissible as parity evidence iff every GRADED cell is a function of
> the vector's own recorded inputs. A vector that grades any cell derivable only from the capture
> tenant's accumulated state is inadmissible off-tenant, however identical the image.**

That test is checkable by reading the vector, it does not decay when a tag moves, and it explains
*why* the disclaimer in §4b.6 is the right disclaimer instead of merely asserting it.

### 1.5 The keystone — can `gerege` ever produce this observation? RE-DERIVED, NOT ACCEPTED

I re-derived the JPQL myself rather than trusting the report. `JournalEntryRepository.java:33-34`:

```
select DISTINCT j.transactionId from JournalEntry j
where j.transactionId not in
  (select DISTINCT je.transactionId from JournalEntry je where je.glAccount.id = :contraId)
```
[VERIFIED: pinned `426a23544`.] I then ran that exact predicate against the live standing oracle,
**read-only**, with `gerege`'s real contra id:

```
financial_activity_type 300 -> gl_account_id 15
SELECT count(*) FROM (SELECT DISTINCT j.transaction_id FROM acc_gl_journal_entry j
  WHERE j.transaction_id NOT IN
   (SELECT DISTINCT je.transaction_id FROM acc_gl_journal_entry je WHERE je.account_id = 15)) x
->  26
```
[VERIFIED: `psql fineract_gerege`, this fire. Also re-read: journal entries **60**, distinct
transaction ids **26**, `acc_gl_closure` **0** — the driver's baseline is intact and I did not move
it.]

`26 ≠ 0`, so `:812 !CollectionUtils.isEmpty(transactionIds)` is permanently true on `gerege` and
`:813-814` always throws. The only way to change it is to delete posted journal entries, which
Fineract has no path for and which this project's append-only rule forbids outright. **`gerege` is
structurally incapable of producing this observation, now and forever. VERIFIED, by my own query,
not by the report.**

### 1.6 CONCLUSION ON ADMISSIBILITY

**ADMISSIBLE. RETIREMENT IS NOT WARRANTED AND WOULD BE A NET LOSS.**

Retiring `LDG-05` would withdraw the only vector in the corpus that kills T296 arm A, restoring the
state T296 measured as the defect: *a port that refuses every opening balance is green on the whole
ledger corpus*. The task correctly says an exemption would leave an irreproducible vector — but the
vector is not the problem. The **argument** is under-built in two places (§1.1, §1.2) and
mis-founded in one (§1.4), and all three are repairable prose. The observation itself is
corroborated by a source I re-derived independently (§2), by two independent oracle readbacks, and
by a mutant I wrote myself (§4).

**REQUIRED FOLLOW-UP (not a blocker on the vector):** add an image-identity fence to
`guard-throwaway-isolation.sh` (an `I6` that records `docker inspect -f '{{.Image}}'` for BOTH the
standing container and the throwaway into `out/`, and refuses on inequality), and pin the compose
`image:` by digest rather than by the `latest` tag. Until that exists, leg (a) and leg (d) of §4b.6
should be marked `[UNVERIFIED]` in the three places they are asserted. **This is a task, not a
micro-fix — it edits a fail-closed guard.**

---

## 2. RE-DERIVING THE MONEY FROM THE ORACLE BYTES

Done from `OB-ACCEPT-01-readback-db.json` and the `.req` wire bytes, **not** from the vector.
The readback is `j.amount::text` out of PostgreSQL — a `numeric` rendered as text, so **no float
exists anywhere in the capture path**. [VERIFIED: `capture.sh`, the `json_agg`/`row_to_json`
projection.]

### (a) `amount_minor` conversion — every leg, by hand, integer/string only

MNT minor-unit digits = **2**, and the oracle itself says so (`currency.decimalPlaces: 2` in the
REST readback). Split on `.`, keep 2, require the residue to be all zeros, `int(whole)*100 + int(keep)`:

| oracle text | whole | keep | residue | minor units | vector says |
|---|---|---|---|---|---|
| `250000.250000` | 250000 | `25` | `0000` ✓ | 250000·100 + 25 = **25000025** | `"25000025"` ✓ |
| `100000.370000` | 100000 | `37` | `0000` ✓ | 100000·100 + 37 = **10000037** | `"10000037"` ✓ |
| `350000.620000` | 350000 | `62` | `0000` ✓ | 350000·100 + 62 = **35000062** | `"35000062"` ✓ |

Stored as JSON **strings**. `build-vector.py` never calls `float()` on a money value and does not
import `decimal`; the one `json.load` float (the request body's `250000.25` literal) is used only to
walk to an account id, and the code says so at the line. [VERIFIED: read the whole script.]

### (b) Debits == credits — recomputed over the SIX oracle rows, by side

Side mapping re-derived from source, not assumed: `JournalEntryType.java:23-24` is
**`CREDIT(1)`, `DEBIT(2)`** [VERIFIED, pinned `426a23544`], matching `build-vector.py`'s
`SIDE = {1: "CREDIT", 2: "DEBIT"}` and matching the REST readback's `entryType` objects.

```
DEBIT : id1 GL2  25000025
        id3 GL3  10000037
        id6 GL1  35000062     sum = 70000124
CREDIT: id2 GL1  25000025
        id4 GL1  10000037
        id5 GL4  35000062     sum = 70000124
```
**70000124 == 70000124.** ✓ And `70000124 = 2 × 35000062`, which is the per-leg-contra signature.

### (c) `250000.25 + 100000.37 = 350000.62`, and the contra is PER LEG

`25000025 + 10000037 = 35000062` — exact, in integers. ✓ The borrowings leg (`GL 4`, `T305-2000`)
carries exactly `35000062` as a **CREDIT** (row id 5), and `GL 1` `T305-3000` carries `35000062` as
a **DEBIT** (row id 6). [VERIFIED: raw bytes.]

**Per leg, not summed — from the raw bytes, three ways:** the contra account `GL 1` appears on
**three separate rows** (ids 2, 4, 6) carrying `25000025`, `10000037` and `35000062` respectively —
i.e. one contra per leg, each matching its own leg's amount and opposite in side. A summed contra
would show `GL 1` at most twice. Source agrees:
`saveAllDebitOrCreditOpeningBalanceEntries` calls `helper.persistJournalEntry` twice **inside** the
per-leg `for` loop — the leg at **`:791`**, its contra at **`:796`** — and is itself called twice,
debits at **`:742`** then credits at **`:745`**. [VERIFIED: pinned `426a23544`,
`JournalEntryWritePlatformServiceJpaRepositoryImpl.java`. Every line number T305 cites — `:717`,
`:724`, `:729-735`, `:742`, `:745`, `:759`, `:791`, `:796`, `:810-814` — resolves correctly.]
**Three legs in, six entries out: CONFIRMED.**

### (d) IS THE VECTOR FAITHFUL TO WHAT THE ORACLE RETURNED?

**YES, on every graded cell.** Row-by-row against the raw bytes:

| oracle row | acct / code / type_enum / amount | vector `expect.legs[i]` |
|---|---|---|
| 1 | 2 / T305-1000 / 2=DEBIT / 250000.250000 | [0] 2, T305-1000, DEBIT, 25000025 ✓ |
| 2 | 1 / T305-3000 / 1=CREDIT / 250000.250000 | [1] 1, T305-3000, CREDIT, 25000025 ✓ |
| 3 | 3 / T305-1100 / 2=DEBIT / 100000.370000 | [2] 3, T305-1100, DEBIT, 10000037 ✓ |
| 4 | 1 / T305-3000 / 1=CREDIT / 100000.370000 | [3] 1, T305-3000, CREDIT, 10000037 ✓ |
| 5 | 4 / T305-2000 / 1=CREDIT / 350000.620000 | [4] 4, T305-2000, CREDIT, 35000062 ✓ |
| 6 | 1 / T305-3000 / 2=DEBIT / 350000.620000 | [5] 1, T305-3000, DEBIT, 35000062 ✓ |

`http_status` 200 matches `.status`. `transaction_id` matches the response body and is correctly
declared ungraded. The driver's arithmetic (debits 70,000,124 == credits 70,000,124;
`25000025 + 10000037 = 35000062`) is **independently confirmed** — but confirmed from the bytes,
which is the only reason it counts.

### (e) OBSERVATION — `request.legs[].amount_major_text` is NOT the request's own characters

The wire bytes say `250000.25`; the vector's **request** leg says `250000.250000`. The value is
taken from the *readback*, not the request. `build-vector.py` says so at the line and claims this
follows LDG-01's convention — **I checked, and the claim is true**: LDG-01's request legs carry
`100000.250000`, not `100000.25`. [VERIFIED.] So this is declared and consistent, not smuggled.
**But note the blind spot it creates:** if the oracle ever *rounded* a request amount, this
convention would record the rounded value in the request and the rounding would become invisible.
It does not bite here (the request already carries exactly 2 decimals, residue zero), and I raise it
only so the next capture author knows the convention has that edge. **Severity: INFORMATIONAL.**

### (f) DEFECT — a comment in `build-vector.py` that says something the code does not do

```python
MINOR_DIGITS = 2  # MNT, ISO 4217 numeric 496, minor unit 2. Read back below from the capture.
```
**It is never read back from the capture.** It is a hard-coded constant; no line of the script reads
`decimalPlaces` from `OB-ACCEPT-01-readback-rest.json` (which does carry it) or from anywhere else.
The **value is correct** — MNT minor unit 2 is a `CLAUDE.md` non-negotiable and the oracle's own
readback agrees — so nothing computed is wrong. But the comment asserts a provenance the code does
not have, in the one script whose entire justification is *"no graded cell in that file was typed by
a human"*. This is **P-11** — *"the code can be RIGHT and its stated reason WRONG, and the reason is
what the next contributor checks"* — inside the script that T305 wrote to enforce exactly that
discipline. **Severity: LOW. MICRO-FIX: delete the six words `Read back below from the capture.`,
or make the script read it.** Also dead code: the `scale6` dict is computed and never used.

---

## 3. THE HEADLINE BEHAVIOURAL CLAIM — RE-DERIVED FROM SOURCE

### 3.1 The claim is CORRECT

`findNonContraTransactionIds(contraId)` selects transaction ids **`not in`** the set of transaction
ids having any entry on `contraId`. So it **excludes** every contra-touching transaction.
[VERIFIED: `JournalEntryRepository.java:33-34`.] Every entry an opening balance writes shares one
transaction id (`generateTransactionId` once, at `:741`), and `:796` puts one entry of that
transaction on the contra account. **Therefore an opening balance's own transaction can never appear
in `findNonContraTransactionIds`, and opening balances cannot block each other.** The oracle's
message at `:814` — *"Defining Opening balances not allowed after journal entries posted"* — is
**overstated**, exactly as T305 says. The rule is "after a **NON-CONTRA** journal entry".

The ACCEPT → ACCEPT-with-reversal → REFUSE sequence is source-consistent:
`:729 findNonReversedContraTransactionIds` → `:734 revertJournalEntry` runs on every accept, so the
second identical POST reverses the first and posts anew; a plain `createJournalEntry` does **not**
route through `defineOpeningBalance` and so never calls `validateJournalEntriesArePostedBefore`,
which is why `MJE-ACCEPT-01` returned 200; and its transaction touches no contra account, so it
enters the non-contra set and the third identical POST draws 403. **The port's predicate
(`impl.go:376`, `req.Command == "defineOpeningBalance" && len(req.PostedNonContraTransactionIDs) > 0`)
is correct and unchanged.** [All VERIFIED against pinned `426a23544`.]

### 3.2 FINDING T320-1 — THE STORE WAS WRONG IN **FOUR** PLACES, AND ONLY THREE WERE CORRECTED

*"a store that was wrong in three places may be wrong in a fourth"* — it is.

`.softhouse/vectors/capabilities-ledger.json`, `capabilities[11].description`:

> "Opening balances, GLClosure, and the refusals each implies: **defining opening balances after
> journal entries have been posted**, an entry dated before the latest closure, and a future-dated
> entry."

**Unchanged by T305, unannotated, and carrying precisely the claim T305 proved false.**
[VERIFIED: `git diff 436fb372 0c6a5206 -- .softhouse/vectors/capabilities-ledger.json` touches
`capabilities[11].evidence` and the `ledger_db_readback` seam row — **and nothing else**. A JSON
walk of the file finds the phrase surviving at exactly one path: `/capabilities/11/description`.]

It is **three lines above** the `evidence` field T305 rewrote at length, in the same object, in the
same file, in the same diff. And it is the field a reader meets **first** — `description` is one
sentence; `evidence` is a ~6,000-character wall. The false statement survived in the most-read
field and was corrected in the least-read one.

I checked the other three and they are genuinely fixed: `LDG-REFUSE-03`'s `title` and `_note` carry
explicit `[CORRECTED BY T305 …]` blocks; `impl.go`'s STEP 1.5 opening sentence is left in place
**deliberately** with a `⚠ AND THE SENTENCE THIS COMMENT OPENS WITH IS WRONG …` correction below it
(`impl.go:346-357`), which is the store's stated convention and is fine. Remaining occurrences of
the phrase elsewhere are either the oracle's own transcribed message (correct to keep verbatim) or
quotations inside a correction block.

**Severity: LOW (prose, no graded cell). MICRO-FIX, 1 line, mechanical, no number and no money
logic:** append to that `description` — *"[CORRECTED T320/T305: the refusal fires after a NON-CONTRA
journal entry; opening balances do not block each other. See this row's evidence field.]"*

### 3.3 FINDING T320-2 — an asymmetry neither T305 nor the store has noticed

`findNonContraTransactionIds(contraId)` takes **only** `contraId` and is **global across offices**.
`findNonReversedContraTransactionIds(contraId, officeId)` takes an **`officeId`** and is **per
office**. [VERIFIED: `JournalEntryRepository.java:33-37`.] So on a multi-office tenant, the
*refusal* is decided organisation-wide while the *reversal* is decided per office: office B's plain
manual entry blocks office A's opening balance, but office A's opening balance is only reversed by a
new opening balance **in office A**.

Inert today — `m_office` is 1 on `gerege` — and `LDG-05` does not grade it. But this program's target
is a multi-branch NBFI, `ledger.opening.balance.and.closure` is `in_graded_domain: true`, and the
port's predicate reads a flat id list with no office dimension. **Severity: LOW today, MEDIUM at
multi-office. Recommend recording it as a backlog item on that capability row**, so it is not
discovered by a Go port that silently scopes the refusal per office.

---

## 4. NON-VACUITY OF THE KILLS — MEASURED, INCLUDING WITH A MUTANT I WROTE MYSELF

I did not accept the driver's transcript. I built the harness from a scratch copy of the tree
(`/tmp/T320-scratch`) and ran each implementation myself. Transcripts in
`.softhouse/reviews/T320/probe/`.

### 4.1 The three registered mutants — every declared number reproduces

| impl | my measurement | `graded_against` says | verdict |
|---|---|---|---|
| `ledger-wrong-openingbalance-always-refusing` | `LDG-05` **FAIL, 1 cell (0 money)**, `leg_count: want 6, got 0`, plus the detail line *"the implementation REFUSED a request the oracle ACCEPTED (HTTP 403 …)"*. **ledger parity PASS 4 FAIL 1, oracle-refusal PASS 5 FAIL 0** | 1 cell, `leg_count`, margin 0, passes every other ledger vector including `LDG-REFUSE-03` | ✓ **exact** |
| `ledger-wrong-openingbalance-no-contra` | `LDG-05` **FAIL, 15 cells (5 money)**; both totals `want 70000124, got 35000062, margin -35000062` | 15 cells, both totals, margin −35000062 | ✓ **exact** |
| `ledger-wrong-truncating` | `LDG-05` **FAIL, 27 cells (8 money)**; leg margins **−25, −25, −37, −37, −62, −62** and **−124** on each total | identical | ✓ **exact** |

**Is arm A's kill "incidental" because it lands on `leg_count`?** No. `gradeOne`
(`grade.go:513-523`) takes the "implementation refused an accept" branch: it records the refusal
verbatim as a failure detail **and** compares `leg_count` as the one cell that can be compared when
the implementation produced no entry at all. The cell is a *label*; the divergence is the whole
answer. And it is genuinely load-bearing — **`LDG-05` is the only vector arm A fails** (parity FAIL
**1**, refusal FAIL **0**), which is precisely T296's finding that nothing else could kill it. **The
kill is REAL and non-vacuous.**

### 4.2 A MUTANT THE AUTHOR DID NOT REGISTER, AND THE ONE THE VECTOR'S DESIGN CLAIMS TO CATCH

The stated reason `LDG-05`'s body carries **three** legs of three different amounts is that *"a
one-debit-one-credit body cannot distinguish a per-leg contra from a single netted one"*. **No
registered mutant tests that** — `no-contra` writes **zero** contra entries, which a two-leg body
would also catch. So I wrote the missing one: `t320-probe-openingbalance-summed-contra`, which emits
one contra per **side group** carrying that group's total (5 entries where the oracle wrote 6).
Source in `probe/t320_summed_contra_probe.go.txt`; transcript in `probe/RUN-summed-contra.txt`.

**Result: `LDG-05` FAIL, 23 cells (7 money); `leg_count want 6, got 5`; positional divergence on
legs[1]–[4]. Every other ledger vector PASSES (parity 4/1, refusal 5/0).**

**And the part that matters most:** on that mutant's output
`INVARIANT double_entry_balances HOLD … debits 70000124 == credits 70000124 (minor units), over 5
legs`, and **`total_debits_minor` and `total_credits_minor` are BOTH CORRECT**. A summed contra is
balanced, and its totals are right. **Neither invariant nor either total can see it — only the
captured per-leg cells can.** So the three-leg body is not decoration: it is the *only* thing in the
harness that separates the oracle's real behaviour from a plausible netted alternative.
**T305's design rationale is VERIFIED, by a mutant the author never wrote.**

I am **not** recommending this mutant be merged as part of this review — registering a twelfth wrong
implementation moves `EXEMPTION_PIN_LEDGER_WRONGIMPLS` and is a task of its own. **Recommendation:
file it.** It is a cheap, real, currently-unexercised defect class, and the vector that kills it
already exists.

---

## 5. THE SCOPE INCURSION INTO `admit.go` — AND A COLLISION T305 COULD NOT HAVE KNOWN ABOUT

### 5.1 The claim T305 asks to be checked — **[VERIFIED]**

*"the capability-scope predicate is byte-identical to what the driver merged; only its message
string changed."* Checked two ways on `git diff 436fb372 0c6a5206 -- …/admit.go`: (i) a whole-file
diff with comments stripped and string literals replaced by sentinels — the capability-scope block
does not appear in it at all; (ii) byte-exact extraction of the block from both blobs. The loop, the
`continue`, the `observedShape` disjunction (`v.Request.Command == "defineOpeningBalance" ||
v.Expect.Refusal.Code == codeAccountingClosed || v.Expect.Refusal.Code == codeFutureDate`), the
`if !observedShape`, and the comparison literals are **byte-identical**. Only the `add(...)` format
string and comments changed. **T305's claim is true as stated.**

The two leg rules are also correctly scoped: `want = 2 * len(v.Request.Legs)` is gated on
`v.Request.Command == "defineOpeningBalance" && v.Expect.Kind != "refusal"`, so for every other
command `want == len(v.Request.Legs)` and the predicate is logically unchanged. And `LDG-05` really
was inadmissible before, twice over (6 expect legs vs 3 request legs; and the positional
`amount_major_text` pairing put `expect.legs[1] = "250000.250000"` against
`request.legs[1] = "100000.370000"`). **The edit was necessary, and "stricter, not weaker" is true
of the length rule.**

### 5.2 FINDING T320-3 — an UNDECLARED widening

The positional check is now skipped when `command == "defineOpeningBalance"`. The multiset check
that replaces it is gated on `command == "defineOpeningBalance" **&& Kind != "refusal"**`. **The two
gates are not complements.** For a vector with `command == "defineOpeningBalance"` **and**
`expect.kind == "refusal"` **and** `len(expect.legs) > 0`, the `amount_major_text` request/expect
cross-check is now **absent entirely** — positional skipped, multiset skipped. Before T305 the
positional rule covered that case.

No such vector exists today (`LDG-REFUSE-03` has zero expect legs), so nothing is live. But T305
declared its incursion carefully and this relaxation is **not** among the things declared.
**Severity: MEDIUM (a gate hole in a fail-closed admissibility check).**

Two further defects in the new code, neither red-driven:
- **Garbled report.** A request amount occurring *fewer* than twice trips the first loop, then trips
  the second loop with a **negative count in a "more than" sentence** (`… -1 time(s) more than
  twice-per-request-leg allows`).
- **Non-determinism.** The surplus-reporting loop is `for text, left := range count` over a **Go
  map**, appending to the reason slice without sorting. With two or more surplus amounts, the
  admissibility reason ORDER varies run to run. In a harness whose entire discipline is byte-stable
  transcripts, that is a real defect. **Severity: LOW–MEDIUM.**
- **No red-drive for either new `admit.go` rule.** `openingbalance_accept_test.go` drives the
  *implementation's* contra expansion red and executes both kills — good — but nothing constructs a
  4-for-3 vector, or a once-occurring amount, and asserts `Admit` refuses it. T296 explicitly
  red-drove its version of this rule. This one was not. **P-22/P-36** — *"a control that cannot fire
  is worse than none, because it is believed."*

### 5.3 FINDING T320-4 — **THE LIVE ONE: T306 HAS ALREADY RUN, AND ITS RESULT COLLIDES WITH `LDG-05`**

The brief describes T306 as "still unrun". **It is not.** Branch
`softhouse/T306-adjudicate-admit-widening` carries **5 commits, unmerged**, head `f7a70b8f`
(*"T306 REVIEW: REJECTED and narrowed — the widened gate ADMITTED an acceptance (15 cells, 5 money)
and keyed two arms on an output"*).

T306 independently reached T305's conclusion by probe — an acceptance-shaped vector with
`command = defineOpeningBalance` **was admitted and graded, 15 cells / 5 money**, so the driver's
"an acceptance is still refused" had been false since T296. But T306 then **narrowed** the predicate
(`d1e78419`) by adding `v.Expect.Kind == "refusal" &&` in front of the disjunction.

**That narrowing would make `LDG-05` INADMISSIBLE.** `LDG-05`'s `expect.kind` is `journal-entry`
and it names `ledger.opening.balance.and.closure` in `capabilities_required`. T306's own comment
anticipated it: *"WHEN THE ACCEPTANCE SIDE IS CAPTURED … THIS is the line that widens, with the
capture in hand. Dropping the refusal precondition is that widening; it must not arrive as a side
effect of anything else."* **T305 has now supplied the capture — and if T306 is merged as it stands,
the corpus silently loses `LDG-05` and arm A comes back to life.**

**This is the single highest-risk item in this review.** It is not a defect in T305; it is a
sequencing hazard that only becomes visible when both branches are read together.

### 5.4 WHAT T306 MUST NOW RE-EXAMINE

1. **Its charter item 2 is settled the other way, by a committed vector.** "Build an
   acceptance-shaped vector for that row and check it is refused" — `LDG-05` **is** that vector, it
   is committed, admitted and graded. The acceptance hole is corpus now, not a probe.
2. **`d1e78419`'s narrowing must be redone.** The `defineOpeningBalance` arm must **drop** the
   `Kind == "refusal"` precondition or `LDG-05` dies. The two **date** arms should keep it — their
   accepting sides remain uncaptured (T295 backlog B-1/B-2).
3. **T306's finding that two arms key admissibility on an OUTPUT** (`expect.refusal.code`) rather
   than on the request is **untouched by T305 and still stands.** It is the right criticism.
4. **The new items T305 created in T306's file, which T306 now owns:** the refusal-shape
   amount-pairing hole (§5.2), the negative-count message, the map-iteration non-determinism, and
   the missing red-drives.
5. **T296's measurement instrument was edited.**
   `TestOpeningBalanceCapabilityIsScopedToTheObservedShape` had its anchor moved from an editorial
   sentence to a structural prefix — **stronger, not weaker**, and the right change — but it is an
   instrument T306's charter says to re-run, so re-run it in its new form. Likewise `LDG-05` sorts
   ahead of `LDG-REFUSE-03`, which silently switched three test arms onto the wrong vector until
   T305 introduced `pickOpeningBalance(t, vs, wantRefusal)`. **T306 must not re-introduce the old
   "first `defineOpeningBalance` vector" selector.**
6. **Expect a textual conflict on rebase**, confined to the `observedShape` block and its comment.

**Verdict on the incursion itself: DECLARED HONESTLY AND CORRECTLY ON THE PREDICATE; the edit was
necessary; but it carries one undeclared widening and two unguarded defects, and it must not be
merged past T306 without §5.3 being resolved first.**

---

## 6. THE ORPHANED-BRANCH REBUILD — NOTHING LOST

Compared against both rescue refs. `refs/rescue/20260827-230001/t305-loose-line` = `37d4c5bb` is
the **root commit of the orphan line itself**; `…/t305-packed-line` = `060f0033` is the **first T305
attempt** (7 non-merge commits + a merge), which is *not* orphaned (`merge-base main 060f0033` =
`5d2164e7`). Content nests strictly: packed ⊂ loose ⊂ orphan tip.

- `git merge-base main 31de1a1f` → **exit 1**: the orphan claim is **TRUE**. Its first commit is a
  root commit. [VERIFIED]
- **Path sets are exactly equal**: `git diff --name-only 5d2164e7 31de1a1f` = **137**;
  `git diff --name-only 436fb372 0c6a5206` = **137**; set difference **empty in both directions**.
- **Blob-level**: of the 137 T305 paths, **0 are absent from main**; 3 differ and main holds the
  **newer** content in every case (the handoff's own rebuild note `+25/-0`; the bar transcript
  re-run on the rebuilt tree, `+2/-2`, both re-measured census counters; that file's manifest line).
- **Whole-tree** `ls-tree -r` for the orphan tip **and both rescue refs** vs main: **0 paths absent
  from main in any of the three.** The 11 differing T305-owned blobs on the rescue refs are
  *earlier* revisions superseded on the orphan line itself before the rebuild — and main's
  `FINDING.md` quotes the retracted first-version conclusion verbatim in a block quote, so even the
  withdrawn finding survives.
- **The merge lost nothing**: `0c6a5206` vs main differ in exactly one blob, `.softhouse/tasks.json`,
  which is main's own later commit adding T320.

**Two of T305's factual claims about the rebuild are WRONG (neither is loss):**
- **T320-5a.** *"a **single** commit on top of `436fb372`"* — there are **two** (`bb72b57b`, the
  137-path deliverable, and `0c6a5206`, the handoff/bar refresh). Content is fine; the wording is not.
- **T320-5b.** *"the orphaned tip carried STALE copies of `.softhouse/RESUME.md` **and**
  `.softhouse/tasks.json`"* — **`RESUME.md` is byte-identical at `5d2164e7`, `436fb372`, `31de1a1f`
  and current main** (blob `3a103c186c…` everywhere). Nothing could have been reverted. Excluding it
  was harmless; the stated reason was false.
- **The `tasks.json` half is TRUE and UNDERSTATED**, which is the part worth keeping: the orphan's
  copy would have **deleted 10 task records** (`T310`–`T319`) and **reverted 7 statuses** from
  `done` (`T297`, `T298`, `T299`, `T302`, `T304`, `T308`, `T309`). The rebuilt branch touches neither
  file — `git diff 436fb372 0c6a5206 -- .softhouse/tasks.json .softhouse/RESUME.md` is **empty**.
  **The decision to exclude both was right; only its stated grounds were half wrong.**

**Hygiene, worth naming:** two branches differing only in case still exist —
`softhouse/T305-openingbalance-accepting-side` (`060f0033`, unmerged as commits) and
`softhouse/t305-openingbalance-accepting-side` (`0c6a5206`, merged). This is exactly the T312
collision shape. Content is fully subsumed by main, so it is a naming hazard, not data loss —
**but the first attempt's commits are unmerged and the repo's own rule says an unmerged branch must
end merged, explicitly abandoned with a reason, or re-dispatched.** Abandon `060f0033` explicitly.

---

## 7. THE BAR, RE-RUN BY ME ON MY OWN TREE

`bash .softhouse/conformance.sh` (bash, not `sh`). Transcript: `probe/RUN-BAR-T320.txt`.

**P-84 applied FIRST** — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT
THE VALUE"*: the probe line is **PRESENT**, at line 110, reading
`reference oracle (https://localhost:8443/…/actuator/health) probe = up`. Only then did I read its
value. **Exit 0.**

```
parity vectors          PASS 46   FAIL 0        cells compared  7884 graded
LEDGER parity vectors   = 5  == pinned 5        LEDGER money cells = 29 == pinned 29
LEDGER declared exemptions = 0 == pinned 0      LEDGER oracle-refusal = 5 == pinned 5
LDG-05-openingbalance-accepted-empty-ledger   parity  PASS  27 cells (8 money)
ACCEPTING-SIDE GAP: accepting opening-balance vector found: LDG-05… (two-way guard CLOSED)
CENSUS wrong ledger implementations — discovered 11 … pinned at 11
  all 11 wrong ledger implementations DIED through this harness, not by hand.
invariant violations 0 · inadmissible 0 · harness errors 0
no-float census: 0 forbidden identifiers, 0 floating-point LITERALS, 0 forbidden imports
```
Also `go test ./internal/apps/ledger/...` → both packages **ok**; `gofmt -l internal/apps/ledger/`
**empty**. **Every census figure T305 reported reproduces on my tree. The driver's transcript was
not accepted; it was re-derived, and it is accurate.**

**Incidental, recorded because a reader will meet it:** the harness's store-file census does **not**
walk a symlinked vector-store root and refuses with `VERDICT: UNUSABLE (exit 2)` /
*"THE STORE FILE CENSUS SAW ZERO .json FILES … A census that inspects nothing accounts for
everything"*. Together with the build-anchor repo-root guard (which refused to grade a different
checkout's corpus), these are two fail-closed guards **working correctly** under adversarial use.

---

## FINDINGS, BY SEVERITY

| id | severity | finding | reproduction |
|---|---|---|---|
| **T320-4** | **HIGH (sequencing)** | **T306 has already run (5 commits, `f7a70b8f`, unmerged) and its narrowing `v.Expect.Kind == "refusal" &&` would make `LDG-05` INADMISSIBLE**, silently withdrawing the only kill of T296 arm A | `git log --oneline main..softhouse/T306-adjudicate-admit-widening`; `git show d1e78419 -- nexus/internal/apps/ledger/conformance/admit.go`; compare with `LDG-05`'s `expect.kind` and `capabilities_required` |
| **T320-3** | **MEDIUM** | Undeclared widening in `admit.go`: for `command == defineOpeningBalance` **and** `kind == "refusal"` **and** `len(expect.legs) > 0`, the `amount_major_text` cross-check is now **absent entirely** (positional gated on command, multiset additionally gated on kind) | `git diff 436fb372 0c6a5206 -- …/admit.go`, the two leg-rule hunks; the gates are not complements |
| **T320-A** | **MEDIUM (argument, not vector)** | §4b.6 leg (a) "the same image id … was measured" is **unsupported by any artefact**; `guard-throwaway-isolation.sh` has no image-identity fence; the compose pins the **mutable tag** `fineract:latest`, so leg (d)'s determinism claim decays silently if the tag moves | `grep -rn 'docker inspect\|{{.Image}}\|e596339626bf' .softhouse/capture/t305-…/throwaway/` → 3 hits, all prose; `out/STANDING-baseline.txt` records I1–I5 only |
| **T320-B** | **MEDIUM** | §4b.6 leg (b) is **inert for this vector** — `LDG-05` performs no rounding, so `HALF_UP` and `HALF_EVEN` are indistinguishable on it. `default` is disqualified by the **missing type-300 mapping and by irreversibility**, not by its rounding mode | `psql fineract_default` → `rounding-mode 6 \| 0 journal entries \| 0 GL accounts \| 0 type-300 mappings`; all three capture amounts have residue `0000` |
| **T320-1** | **LOW (prose)** | **The FOURTH place.** `capabilities-ledger.json` → `capabilities[11].description` still reads *"defining opening balances after journal entries have been posted"*, unannotated, three lines above the `evidence` T305 rewrote | JSON walk of the file for the phrase → exactly one surviving path, `/capabilities/11/description`; the T305 diff touches only `evidence` and the seam row |
| **T320-3b** | **LOW–MED** | `admit.go`'s new surplus loop iterates a **Go map** and appends unsorted → admissibility reason ORDER is non-deterministic across runs; and a shortfall prints a **negative count in a "more than" sentence**. Neither is red-driven | read the multiset hunk; no test in `openingbalance_accept_test.go` constructs a 4-for-3 vector or a once-occurring amount |
| **T320-2** | **LOW now / MED at multi-office** | `findNonContraTransactionIds(contraId)` is **global**; `findNonReversedContraTransactionIds(contraId, officeId)` is **per office**. Refusal is organisation-wide, reversal is per office. Port predicate has no office dimension | `JournalEntryRepository.java:33-37`, pinned `426a23544` |
| **T320-f** | **LOW** | `build-vector.py`'s `MINOR_DIGITS = 2  # … Read back below from the capture.` — **it never is**. Value correct, comment false, in the one script whose justification is "nothing was typed by a human". P-11 inside the P-11 fix. Also: `scale6` dict computed and unused | read the script; grep it for `decimalPlaces` → no hit |
| **T320-5a** | **LOW (factual)** | Handoff says the rebuilt branch is *"a single commit"*; it is **two** (`bb72b57b`, `0c6a5206`) | `git rev-list --count 436fb372..0c6a5206` → 2 |
| **T320-5b** | **LOW (factual)** | Handoff says the orphan carried a **stale `RESUME.md`** a merge would have reverted. **False** — blob `3a103c186c…` is identical at every revision involved. The `tasks.json` half is true and **understated**: 10 task records deleted, 7 `done` statuses reverted | `git rev-parse 5d2164e7:.softhouse/RESUME.md 436fb372:… 31de1a1f:… main:…` → one hash |
| **T320-6** | **INFO (opportunity)** | No registered mutant tests **per-leg vs SUMMED** contra — the sole stated reason `LDG-05` carries three legs. I wrote one; it dies on `LDG-05` (23 cells, 7 money) and passes everything else, **while `double_entry_balances` HOLDS and BOTH TOTALS ARE CORRECT**. Recommend filing it | `.softhouse/reviews/T320/probe/` — source, README recipe, transcript |
| **T320-e** | **INFO** | `request.legs[].amount_major_text` carries the **readback's** scale-6 text, not the request's wire characters. Declared, and the stated LDG-01 precedent is **true** — but it would make an oracle-side rounding of a request invisible | compare `OB-ACCEPT-01-…​.req` (`250000.25`) with the vector's request leg (`250000.250000`); `LDG-01` request legs carry `100000.250000` |

**No floating-point defect was found anywhere in the T305 diff, the capture rig, the vector, or the
port change.** I checked: the capture's psql projection (`j.amount::text`), `build-vector.py`
(no `float()` on money, `decimal` not imported), the vector (money as integer-minor-unit **strings**),
`impl.go` STEP 4 (three `ledger.MinorUnits` additions), and the bar's own no-float census
(6 packages / 59 files / 128,292 tokens, **0** forbidden identifiers, **0** float literals, **0**
forbidden imports). **The only decimals in the diff are the oracle's own transcribed characters.**

*(P-86 — "an ID IS A CARDINAL … cite the id AND its sentence together so a shifted number is
self-correcting" — so each P-number above is written with its rule text.
P-11 = "the code can be RIGHT and its stated reason WRONG, and the reason is what the next
contributor checks" (`patterns.md`). P-22/P-36 = "a control that cannot fire is worse than none,
because it is believed" (`patterns.md`). P-84 = "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING.
READ THE ABSENCE, NOT THE VALUE" (`patterns.md`). P-92 = "a probe whose safety comes from an
EXTERNAL PRECONDITION rather than from its own content is a loaded weapon" (`patterns.md`).)*

---

## RECOMMENDED DISPOSITION

1. **KEEP `LDG-05`.** Do not retire, do not exempt. Its money is re-derived and correct, its
   graded cells are faithful to the oracle bytes, its kill of arm A is real and unique, and its
   three-leg design is vindicated by a mutant the author never wrote.
2. **BLOCK T306's merge until §5.4 item 2 is resolved.** This is the one item that can silently
   undo T305's whole contribution.
3. **MICRO-FIX (≤10 lines, mechanical, no numbers, no money logic), safe to apply now:**
   `capabilities[11].description` correction note (T320-1); the six-word comment deletion in
   `build-vector.py` (T320-f); the handoff's "single commit" → "two commits" and its `RESUME.md`
   sentence (T320-5a/5b).
4. **NEW TASKS (not micro-fixes — they edit a fail-closed guard or the mutant population):**
   image-identity fence `I6` + digest-pinned compose (T320-A); register the summed-contra mutant
   (T320-6); red-drive the two new `admit.go` rules and fix the map non-determinism (T320-3b).
5. **`reference-oracle.md`'s fifth fold should record the rule in §1.4**, not "same image id":
   *an off-tenant capture is admissible as parity evidence iff every graded cell is a function of
   the vector's own recorded inputs.* That test is mechanical, does not decay, and is what actually
   makes `LDG-05` sound.
