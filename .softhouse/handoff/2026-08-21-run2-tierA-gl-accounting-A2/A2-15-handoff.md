# A2-15 — the first vectors in this program that grade a journal entry

| | |
|---|---|
| Task | `A2-15` · `test_writer` · context `tierA-gl-accounting` |
| Branch | `softhouse/A2-15-ledger-parity-vectors` |
| Fork point | **`2d41838cdbbe5332bd62deb5cdec9f52f3df91f3`** — see *Discrepancy 1* below; the dispatch said `8611e754` |
| Reference oracle | LIVE, `{"status":"UP"}`, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb`, PostgreSQL `fineract-db-1` / `fineract_gerege` |
| Gate state relied on | **G-11 CLOSED — RATIFIED** (DEC-2 rev 5, `A2-33` clean). **G-10 OPEN** — honoured via option (c). **G-12 OPEN** — honoured by grading no balance at all. |

**What this task did, in one sentence.** It built the second vector schema, the second
comparator and the second capability registry that DEC-2 §5.2 specifies, promoted **six** ledger
vectors from the A2 captures, and left the 46 loanschedule parity vectors and their 7,884 graded
cells **byte-identical and untouched**.

**What a green ledger section means, stated first so nothing below can be read as more.** It means
*"the Go ledger package's money conversion, its double-entry sum, its split sum and its two
refusal rules match the reference oracle on six captured cases, within a graded domain that
excludes accrual, transfers, charge-off, multi-currency, opening balances and closures."* It is
**not** evidence about the ledger as a whole and it is **not** a cutover argument. Cutover remains
a hard `user` gate.

---

## 0. The BAR, measured

Baseline **`B`** was measured **in this worktree, immediately before the first edit**, at commit
`2d41838` (DEC-2 §5.2 requirement 2 requires `B` to be measured, not copied from the ADR):

```
B.parity   46      B.refusal 4      B.selftest 1
B.cells    7884 graded, 93 ungraded
B.kills    106 money, 7 structural
B.exempt   4 EXEMPTED / 4 DECLARED / 4 GROUNDED / 0 UNDETERMINED / 0 UNGROUNDED
B.files    50 .json under .softhouse/vectors/loanschedule/
B.store    git rev-parse HEAD:.softhouse/vectors = 73c3ea7b43dd75f04884072719a87fc8e1d255c1
```

Final state, after everything:

| BAR item | observed |
|---|---|
| probe line PRESENT, reads `up` | `conformance: reference oracle (https://localhost:8443/…/health) probe = up` |
| `VERDICT` | `PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared` |
| loanschedule parity | **46 PASS / 0 FAIL** — identical to `B` |
| loanschedule contract-refusal | **4 PASS / 0 FAIL** — identical to `B` |
| loanschedule self-test | **1 PASS / 0 FAIL** — identical to `B` |
| loanschedule cells | **7884 graded, 93 ungraded** — identical to `B` |
| loanschedule kills | **106 money, 7 structural** — identical to `B` |
| refused / inadmissible / harness errors | **0 / 0 / 0** |
| invariant violations | **0** |
| invariant assertions NOT RUN | **0** |
| exemption census | 4 / 4 / 4 / 0 / 0 — **all equal to the pins, unmoved** |
| **ledger parity** | **4 PASS / 0 FAIL** |
| **ledger oracle-refusal** | **2 PASS / 0 FAIL** |
| **ledger cells** | **70 graded, of which 21 are MONEY cells in int64 minor units** |
| **ledger kills** | **6 money, 10 structural** |
| **ledger invariants** | **0 violations, 11 non-vacuous assertions, 10 of them INDEPENDENT** |
| **ledger declared exemptions** | **0** (the schema admits none; gated at 0) |
| `--prove` | **23 passed, 0 failed** |
| `go build` / `go vet` | 0 / 0 |
| `go test -count=1 ./...` | ok (all 4 packages, including the new one) |
| `gofmt -l` | exactly `internal/apps/loanschedule/contract/contract.go` (G-3, expected) |
| `conformance.sh loanschedule` | **PASS exit 0**, 46 / 4 / 0, **7863 cells** — identical to `B`'s filtered run |
| **new vector-store digest** | **`git rev-parse HEAD:.softhouse/vectors` — stated in §9** |

---

## 1. Two discrepancies against the dispatch, reported before anything else

**Discrepancy 1 — the fork point I was told is not the fork point I have.** The dispatch stated
`8611e754`, "verified by the driver". Measured here:

```
git rev-parse HEAD          -> 2d41838cdbbe5332bd62deb5cdec9f52f3df91f3
git merge-base HEAD main    -> 2d41838cdbbe5332bd62deb5cdec9f52f3df91f3
git branch --show-current   -> worktree-agent-a698351e28b6ea99d
```

`2d41838` is `main`'s tip — the fire-close commit. `8611e754` does not appear in this worktree's
history. **This is P-71's corrected duty failing on its very next use**: the corrected rule says
*"the fork point is `git rev-parse HEAD` immediately before the `Agent` call"*, and the sha the
driver circulated was not that. It was harmless here — everything A2-15 needs (G-11's closure,
T230, T233, DEC-2 rev 5) is present at `2d41838` and I verified each one in the tree rather than
from the brief — but the mechanism that produced the wrong sha is still there.

**Discrepancy 2 — "Promoting a vector WILL move those pins" is FALSE for this submission, and I
was told to argue each new figure.** It did not move them, and §7 argues each figure at its
unchanged value and explains why. The prediction assumed the promotion would produce an exemption;
it produced none, for the reason §5 gives.

---

## 2. What was promoted, and why each one

Six vectors, all under `.softhouse/vectors/ledger/`, all schema `gerege.ledger.vector/v1`.

### LDG-01 — `LDG-01-manual-je-3leg-minor-units` · parity · `ledger_rest_posting`
A **manual** journal entry, **three legs**, a **non-round minor-unit amount on every one of
them**: debits `100000.250000` (GL 16) + `25000.370000` (GL 17) against a single credit
`125000.620000` (GL 21). **Why:** it is the smallest promoted case in which a port that dropped
minor units differs from a correct one on *every* leg, and it is a 3-leg entry, so it is one of
the shapes that did not exist in this corpus before A2-26.

### LDG-02 — `LDG-02-repayment-split-4leg-minor-units` · parity · `ledger_rest_posting`
The **accounting-path** entry for a split repayment on loan 7 / **product 55** (CASH BASED):
**four legs**, one debit `300000.000000` against credits `270450.580000` principal +
`22049.420000` interest + `7500.000000` penalty. **Why:** it is the entry that makes *"splits sum
to the whole"* a real assertion, and it is produced by the oracle's own loan accounting rather
than by a caller. Product 55 and not 22/23/24/27/28 — see §4.

### LDG-03 — `LDG-03-overpayment-4leg-minor-units` · parity · `ledger_rest_posting`
The **overpayment** entry on the same loan: four legs, one debit `1000000.000000` against
`889549.420000` principal + `20298.820000` interest + `90151.760000` to the **overpayment
liability** account (GL 6). **Why it is not a duplicate of LDG-02:** **all three** credit legs
carry non-zero minor units (42, 82, 76) and they sum to a whole tugrik, so a port that rounded
each leg independently would still balance and would still be wrong on every leg. LDG-02 has one
whole-tugrik credit and cannot make that discrimination. It is also the only promoted vector whose
splits reach a LIABILITY.

### LDG-04 — `LDG-04-header-account-accepted` · parity · `ledger_db_readback`
**The oracle ACCEPTS a posting to a summary (HEADER) account.** A2-345 posted a debit leg at GL 1
— `account_usage = 2`, the root `Assets` node — and the oracle returned **HTTP 200** and created
transaction `a28f573ffb9b`. **Why:** DEC-2 brief item (5), verbatim: *"A port that REFUSES
summary-account postings therefore DIVERGES FROM THE ORACLE. Do not 'improve on' the oracle."*
This is the only promoted vector on the `ledger_db_readback` seam, and §3 states why.

### LDG-REFUSE-01 — `LDG-REFUSE-01-unbalanced-by-one-minor-unit` · oracle-refusal
The oracle refuses an entry out by **exactly one minor unit** (`100000.25` debit vs `100000.24`
credit): **HTTP 403**, `error.msg.glJournalEntry.invalid.mismatch.debits.credits`. **Why one
minor unit and not a larger gap:** 1 is the smallest imbalance MNT can express, so a port with
*any* tolerance, epsilon or float comparison on the double-entry check accepts this request and
diverges. A larger gap would be killed by a sloppier implementation too and would grade less.

### LDG-REFUSE-02 — `LDG-REFUSE-02-manual-adjustments-not-permitted` · oracle-refusal
The oracle refuses a manual entry whose leg points at GL 18 (`manual_journal_entries_allowed =
false`): **HTTP 403**,
`error.msg.glJournalEntry.invalid.account.manual.adjustments.not.permitted`. The request is
otherwise **balanced**, which is what makes it a clean test of the permission rule alone.

**Both refusal vectors are graded on THREE cells** — status, globalisation code and message —
because a port returning 403 with an invented code is not matching the oracle, and the code is
the cell that tells one 403 from another.

---

## 3. Per-`case_id` byte provenance — where every promoted cell's bytes came from

Verified by an **independent program**, `.softhouse/capture/tierA-a2/verify-provenance-a2-15.py`,
which re-opens each vector, re-reads the artefact it cites, re-hashes it, and asserts that every
promoted major-unit text is **byte-present** in those bytes and that every promoted minor-unit
integer follows from that text by exact string arithmetic. Transcript:
`.softhouse/capture/tierA-a2/PROVENANCE-A2-15.txt`. **BYTE-PROVENANCE FAILURES: 0.**

| case_id | response artefact (the legs / the refusal) | request artefact (the wire bytes) |
|---|---|---|
| LDG-01 | `out/A2-347-je-manual-readback.json` | `out/A2-343-manual-je-3leg.req` |
| LDG-02 | `out/A2-338-je-after-repayment-coverage.json` | `out/A2-337-repayment-split.req` |
| LDG-03 | `out/A2-383-je-after-overpay.json` | `out/A2-382-repayment-overpay.req` |
| LDG-04 | `out/A2-390-db-ledger-state-a2-15.json` | `out/A2-345-manual-je-header.req` |
| LDG-REFUSE-01 | `out/A2-344-manual-je-unbalanced.json` | `out/A2-344-manual-je-unbalanced.req` |
| LDG-REFUSE-02 | `out/A2-346-manual-je-nomanual.json` | `out/A2-346-manual-je-nomanual.req` |

All paths are under `.softhouse/capture/tierA-a2/`. **Every vector cites BOTH a response artefact
and a REQUEST artefact**, which is DEC-2 brief item (2): only the 44 new A2-3xx HTTP captures
record wire bytes, and a vector citing a record with no request block is graded on less.

**The exact bytes.** The oracle emits at **scale 6**: `"amount":270450.580000`, not `270450.58`.
The vectors carry the oracle's own characters in `amount_major_text` and the graded integer in
`amount_minor`:

```
270450.580000 -> 27045058      22049.420000 -> 2204942       7500.000000 -> 750000
889549.420000 -> 88954942      20298.820000 -> 2029882      90151.760000 -> 9015176
100000.250000 -> 10000025      25000.370000 -> 2500037     125000.620000 -> 12500062
```

That pairing is DEC-2 §4.3 consequence 4 / T186 category (c): **the graded value is the minor-unit
integer string; the major-unit text is a transcription cross-check and is never a grading
standard.**

### A2-390 — the one capture this task took, and why

`LDG-04`'s legs are not observable from A2-345's HTTP response, which is
`{"officeId":1,"transactionId":"a28f573ffb9b"}` and carries no legs. They were observed instead
from the `ledger_db_readback` seam — one of DEC-2 §4.2 G-01's three — by
`sql/q7-a2-15-ledger-state-json.sql`, committed as `A2-390-db-ledger-state-a2-15.json` with an
`.http` sidecar recording the transport and a `.status` sidecar.

**This is also the P-69 re-run the brief required.** `A2-370` is a snapshot and `A2-29` moved the
oracle again after it. Re-measured today at the live oracle:

```
leg-count distribution:  2 legs x20 transactions,  3 legs x4,  4 legs x2
per-transaction, integer minor units, debit == credit on ALL 26 transactions, difference 0
L25            4 legs   30000000 / 30000000
L27            4 legs  100000000 / 100000000
a28f573f34c7   3 legs   12500062 / 12500062
a28f573ffb9b   2 legs   10000025 / 10000025
distinct currency codes across every journal entry: ["MNT"]
```

**Two facts A2-370 does not carry**, and both are recorded here rather than inherited: the tenant
now has **23** GL accounts (A2-29 added 33 and 34) and **60** journal-entry rows across **26**
transactions. Nothing in this handoff or in any promoted vector cites A2-370's numbers.

**Why the capture is `.json` and not the psql table.** The first attempt committed the `q4` psql
table and `conformance.sh` **REFUSED** it:
`REFUSED — a capture record cited by a stored vector is not parseable as JSON`, from
`check_wire_float_roundtrip.py`. The guard is right — the evidence a parity vector was transcribed
from is exactly what it exists to certify — so the query was re-emitted through `json_build_object`
rather than the guard being loosened. **`q7` deliberately does NOT project
`office_running_balance` or `organization_running_balance`**; see §8.

---

## 4. The `glAccountType` decision — option (a), EXCLUDE, and the instability is in the vector's own note

**Decision: (a), EXCLUDE the cell.** Every promoted leg carries
`"excluded_fields": ["gl_account_type"]`.

**The instability is recorded in each vector's own `_note`, not only here**, which the brief
demanded explicitly. It is **enforced**, not trusted: `admit.go` refuses a vector that excludes
`gl_account_type` whose `_note` does not mention `glAccountType`
(`TestGlAccountTypeMayNotBeGraded/an_exclusion_without_the_reason_in_the_note_is_refused`), and
the exclusion list is **CLOSED to that one cell** — excluding anything else is INADMISSIBLE, so
widening it is a source edit a reviewer sees rather than a JSON edit nobody does.

**Why (a) and not (b).** Option (b) — grade it against a separately captured `GET
/glaccounts/{id}` taken in the same window — was rejected because it makes the vector's truth
depend on two captures having been taken close enough together. That is a property of the capture
*session*, not of the oracle, and **nothing in the store could ever check that the window was
actually shared**. Excluding the cell states plainly that this corpus does not grade
classification — which is TRUE — instead of grading it against evidence nobody can re-derive.

**THE COST, STATED AND NOT NARROWED.** No vector in this store grades a GL account's
classification at all. A port that resolves an entry's classification **wrongly** is not caught
here. The classification each leg's account rendered at capture time is recorded in the note for
the record and is graded by nothing.

**`gl_account_type` is also refused as a perturbation cell.** `admit.go` refuses a
`graded_against` entry naming it, quoting DEC-2 §5.2 requirement 7: *a red on an unstable cell is
not a demonstration that the comparator works; it is a demonstration that the corpus is not
reproducible.* `TestCellVocabularyIsDerivedFromTheComparator` asserts the comparator does not emit
the cell at all.

**G-10 option (c) is enforced as DATA, not as a comment.** `PIN-ledger.json` carries
`"inadmissible_product_ids": [22, 23, 24, 27, 28]`, and a vector taken from one of them is
INADMISSIBLE with the reason printed. Both promoted accounting-path vectors are on **product 55**.

---

## 5. T230's `[UNVERIFIED]` claim — CONFIRMED AS NOT APPLICABLE, and this is a refutation, not a pass

T230's own words, carried in my dispatch: it *"did NOT read A2-15's brief or A2-26's observation,
so 'the fix matches A2-15's actual need' is `[UNVERIFIED]` on its side"*, and I was told to
confirm it against the real exclusion and to *"say so plainly as a finding"* if it did not fit.

**IT DOES NOT FIT, and the reason is structural rather than a defect in T230.**

T230's rework is about an **exemption** — an `invariant_exemptions` entry — paired with an
`unrecorded_fields` withdrawal, reclassified from INADMISSIBLE to
UNDETERMINED-ON-THE-RECORD. A2-15's actual exclusion is of a **CELL**, and the two are different
objects:

1. **What I exclude is a cell, not an invariant.** `gl_account_type` is withdrawn from *grading*.
   Nothing is switched off.
2. **No ledger invariant reads it.** DEC-2 §4.4 settles that exactly two invariants are gradeable
   in this context — **I-1** (debits equal credits) and **I-2** (splits sum to whole) — and
   neither reads a GL account's classification. So there is nothing for an exemption to excuse,
   and the classifier T230 reworked never runs on my path.
3. **Therefore my corpus declares ZERO exemptions**, and `UNDETERMINED-ON-THE-RECORD` stays at 0.

**This was tested, not asserted.** RED-drive **CASE 5** builds a real
`invariant_exemptions` entry on a real promoted ledger vector and runs it through
`bash .softhouse/conformance.sh`. It comes back **INADMISSIBLE** — *"this vector declares 1
invariant_exemptions and THIS SCHEMA ADMITS NONE"* — and the run is exit 2. That is the ledger
schema's own default-deny, not T230's classifier: **the ledger schema has no grounding classifier
at all**, so admitting an exemption would switch an invariant off with nothing checking that the
thing it excuses is visible in the record (P-8: *prefer re-observing to exempting*).

**What I am NOT claiming.** I am not claiming T230's rework is wrong or unnecessary. It is
correct for the loanschedule schema and I did not test it there. I am claiming, on measurement,
that **A2-15 was not the caller that needed it**, which is precisely the `[UNVERIFIED]` T230
raised. `[UNVERIFIED]` on my side: whether any *future* ledger vector will need an exemption. If
one does, the ledger schema needs a grounding classifier of its own first — and that is a task,
not a JSON edit.

---

## 6. The multi-leg / minor-unit census of the promoted set

Counted in the live artefacts by `verify-provenance-a2-15.py`, **both terms measured** (P-67):

| case_id | legs | DR | CR | money cells with NON-ZERO minor units |
|---|---|---|---|---|
| LDG-01 | **3** | 2 | 1 | **3 of 3** |
| LDG-02 | **4** | 1 | 3 | **2 of 4** |
| LDG-03 | **4** | 1 | 3 | **3 of 4** |
| LDG-04 | **2** | 1 | 1 | **2 of 2** |
| LDG-REFUSE-01 | 0 (refused) | — | — | 0 |
| LDG-REFUSE-02 | 0 (refused) | — | — | 0 |

**Totals: 13 legs across 4 entry-asserting vectors; 10 of the 13 promoted money cells carry
non-zero minor units. Leg distribution of the promoted set: two 4-leg, one 3-leg, one 2-leg.**

**Against the brief's failure condition**, which was *"promoting only two-leg whole-tugrik entries
re-creates exactly the vacuous corpus A2-26 just fixed"*: **both** four-leg transactions in the
oracle are promoted, the three-leg manual entry is promoted, and **not one promoted money cell is
a whole tugrik on a vector where a whole tugrik is the only value**. The single 2-leg vector
(LDG-04) exists for the header-account acceptance and its two legs are `100000.25`, i.e. not whole
tugriks either.

**The disbursement (L21) and fee (L23) entries were deliberately NOT promoted.** They are
two-leg, whole-tugrik entries; promoting them would have added vector count and graded nothing a
truncating port could fail. That refusal is recorded in `capabilities-ledger.json` under
`ledger.accounting.path.loan.repayment` so a later reader does not mistake their absence for an
oversight.

### The vacuity finding this task nearly shipped, and what was done about it

**On a journal entry with one leg on one side and N on the other, "splits sum to the whole" is
character-for-character the equation "debits equal credits" already asserts.** `whole` IS the lone
leg; `Σ splits` IS the other side. Both print HOLD, no implementation can fail one and pass the
other, and a reader counting two green invariant lines counts one assertion twice. That is not
vacuity in the "cannot fail" sense — it can fail — but it is **not independent evidence**, and
reporting it as a second invariant would have been exactly the shape P-22 warns about.

Fixed rather than papered over:

- the vector schema carries `transaction_amount_major_text` — **the amount the CALLER asked for**,
  read from the recorded `.req` bytes (`"transactionAmount": 300000` / `1000000`);
- on the two accounting-path vectors, I-2 now asserts that the oracle's credit legs sum to **the
  requested total**, which nothing in I-1 reads. That is genuinely independent;
- a registered wrong implementation, **`ledger-wrong-split-drift`**, keeps the entry internally
  balanced (I-1 HOLDS) and moves the requested total by one minor unit (I-2 goes RED). RED-drive
  **CASE 4** runs it and shows exactly that;
- the report prints **INDEPENDENT / DEPENDENT on every invariant line**, and a dependent HOLD says
  in its own text that it is not a second piece of evidence;
- the summary prints `11 non-vacuous assertion(s) made, of which 10 are INDEPENDENT`;
- `TestSplitsSumToWholeIsNotAlwaysARestatementOfDoubleEntry` fails the build if no vector asserts
  I-2 independently.

**The one DEPENDENT assertion is LDG-01's**, because a manual entry's request body enumerates both
sides and there is no independent second term to hold it against. The report says so on that line.

---

## 7. The `EXEMPTION_PIN_*` update — deliberate, and every figure argued

The five existing figures are **UNCHANGED**, which contradicts the dispatch's prediction. Each is
argued rather than left to speak for itself (the argument is also committed in
`conformance.sh`'s own comment block, where a reviewer sees it beside the constant):

| pin | value | argument |
|---|---|---|
| `EXEMPTED` | **4** | The four exempted *assertions* both belong to the two G-8 family-B **loanschedule** vectors `T116` promoted. A2-15 added no loanschedule vector, so this population could not move. |
| `DECLARED` | **4** | The same four counted as *declarations* in the loaded files: two vectors × two invariants. |
| `GROUNDED` | **4** | All four are GROUNDED — the recorded schedule genuinely violates the exempted invariant in both files. |
| `UNDETERMINED` | **0** | The figure the dispatch expected to move. It did not, for the reason §5 gives in full: A2-15's exclusion is of a CELL, not of an INVARIANT, and neither gradeable ledger invariant reads a GL account's classification. |
| `UNGROUNDED` | **0** | No exemption in the store is refuted by its own record. |

**Four NEW pinned figures**, each an EQUALITY (a floor closes one direction only), each argued:

| new pin | value | argument |
|---|---|---|
| `EXEMPTION_PIN_LEDGER_DECLARED` | **0** | The ledger schema REFUSES an exemption outright. "Refuses" is a property of the code; the POPULATION is a property of the corpus, and an uncounted population drifts in both directions with nothing noticing — T220-N1 and T160 in one sentence. So the report counts it every run and the pin compares it. |
| `EXEMPTION_PIN_LEDGER_PARITY` | **4** | LDG-01, LDG-02, LDG-03, LDG-04. |
| `EXEMPTION_PIN_LEDGER_REFUSAL` | **2** | LDG-REFUSE-01, LDG-REFUSE-02. |
| `EXEMPTION_PIN_LEDGER_MONEYCELLS` | **21** | Pinned SEPARATELY from the cell total because DEC-2 §5.5 warns that *"a ledger corpus whose money cells only ever kill structurally has graded no amount"*: a corpus that quietly stopped comparing money would keep every vector count and lose only this one. **Derivation: LDG-01 3 legs + 2 totals = 5; LDG-02 4 + 2 = 6; LDG-03 4 + 2 = 6; LDG-04 2 + 2 = 4; each refusal vector asserts no amount at all = 0. 5+6+6+4 = 21.** |

**Why the three population pins and not the exemption pin alone.** A pin on the exemption count
alone sits happily at 0 over a store from which **every ledger vector has been deleted**: the
loanschedule half is still green, the report prints its empty-store banner, and the verdict would
still be PASS. **RED-drive CASE 7 does exactly that deletion and shows the run refusing.**

**Not retro-fitted to what my run happened to print.** Each figure above was derived from the
corpus's own structure and written down *before* being compared; the inflation arm (CASE 6) and
the deflation arm (CASE 7) are both driven red, so the pins are demonstrably load-bearing in both
directions rather than transcriptions of one observation.

---

## 8. G-12 — no balance is graded, and the vector says so

`A2-29` MEASURED `acc_gl_journal_entry.{office,organization}_running_balance` to be a **SECOND
SOURCE OF TRUTH, not a cache**: made to disagree with the derived sum by MNT 2,000,000.00 on the
live oracle, surviving four organisation-wide recomputes, propagating into a **freshly computed
row** because the recompute seeds from its own prior output, and served at the contract boundary
flagged `runningBalanceComputed: true`.

Four independent ways this corpus cannot grade one, so that no single edit re-opens it:

1. **The schema has no field for a balance.** `PostedEntry` carries none, so a port cannot satisfy
   this harness by reading a stored balance, and no vector can express one.
2. **Every promoted vector's `_note` says so**, in the vector itself.
3. **`admit.go` refuses** a vector whose note claims to grade either column.
4. **The capture does not carry them.** `q7-a2-15-ledger-state-json.sql` deliberately does not
   project either column, and no capture sets `runningBalance=true` or `fetchRunningBalance=true`
   — the latter being HTTP 500 on PostgreSQL anyway
   (`GLAccountReadPlatformServiceImpl.java:127-131` emits MySQL-only `group by … desc`).

`TestCellVocabularyIsDerivedFromTheComparator` fails if the comparator ever emits
`office_running_balance`.

---

## 9. THE FIVE NAMED GAPS — stated explicitly and NOT silently narrowed (P-40)

They are in `capabilities-ledger.json` as `in_graded_domain: false` rows (so a vector claiming one
is REFUSED, default-deny), and the harness **prints all of them on every run, pass or fail**,
under `WHAT A GREEN LEDGER SECTION DOES **NOT** MEAN`. A guard that states its limits only when it
fails is indistinguishable from one that has none.

> **[CORRECTED BY T242 — A2-34 F-5. The sentence above was OVERSTATED WHEN WRITTEN.]** The harness
> did **not** print all of them. `capabilities-ledger.json` carried **eight** `in_graded_domain:
> false` rows and `report.go`'s block was **hardcoded prose listing six**. The two it dropped were
> `ledger.reversal.entry` and — **`ledger.slot.resolution`, the sixth gap this very section adds
> below.** T242 replaced the hardcoded block with one DERIVED from the registry, so the claim is
> now true by construction and a row added to that file prints itself. See `T242-handoff.md` §2.

1. **ACCRUAL IS ENTIRELY UNGRADED.** Product 28 is the only `ACCRUAL_PERIODIC` product, it **has
   no loan**, no accrual or COB job has ever run, and `INTEREST_RECEIVABLE` / `FEES_RECEIVABLE` /
   `PENALTIES_RECEIVABLE` (gl 18, 22, 16) have **zero** journal entries. Product 28's own mapping
   is inadmissible today (A2-314, 403). An accrual vector needs a **new** accrual product on clean
   accounts **plus a job run**. Neither is cheap and neither is in this task's scope.

   > **[CORRECTED BY T242 — A2-34 F-4. The struck clause is FALSE and was printed by the harness
   > as a measured fact on every run.]** Re-derived against the live PostgreSQL reference oracle:
   > **gl 18 → 0, gl 22 → 0, gl 16 → SIXTEEN** — more journal entries than any other account in
   > the tenant, and gl 16 is a promoted leg of **LDG-01, LDG-02 and LDG-03**, three of the four
   > parity vectors. **The conclusion "accrual is entirely ungraded" STANDS; the evidence clause
   > does not.** The error was structural, not clerical: **one GL account backs several slots.**
   > gl 16 is `PENALTIES_RECEIVABLE` (slot 9) on product 28 **and** `FUND_SOURCE` (slot 1) on
   > products 22, 27, 46, 54 and 55, and all sixteen of its rows arrive through the latter,
   > because product 28 has no loan. **The SLOT is unposted; the ACCOUNT is not empty.** The
   > registry now records the three slots as structured `unposted_slots` data and the harness
   > measures each backing account's activity against the promoted corpus on every run. Full
   > re-derivation, with the queries and the commit: `T242-handoff.md` §1.
2. **`TRANSFERS_SUSPENSE` (gl 17) IS REACHED ONLY AS A MANUAL TARGET.** LDG-01 promotes it as
   one. It has **no accounting-path entry at all**; the path that reaches it is **account
   transfers**, which slice A2 never exercised.
3. **CHARGE-OFF IS UNMAPPED ON BOTH ADMISSIBLE PRODUCTS.** Product 55 does not map
   `chargeOffExpenseAccountId`, so `command=charge-off` would 404 exactly as A2-224 did on product
   46. The charge-off income slots (14, 15, 18 in `CashAccountsForLoan`) are unreachable without a
   new product.
4. **MULTI-CURRENCY IS UNTOUCHED.** Every journal entry is MNT — re-confirmed today against the
   live oracle, `distinct_currency_codes` over `acc_gl_journal_entry` returns `["MNT"]` and
   nothing else. There is **no observation** of an entry whose legs are in different currencies.
5. **NO OPENING BALANCES AND NO `GLClosure`.** `validateBusinessRulesForJournalEntries` refuses an
   entry dated before the latest closure **and** refuses a future-dated entry
   [VERIFIED: `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:626-640`]. **Neither refusal
   is observed**, so neither is graded. Both are **cheap** captures and both belong in the
   `ledger.refusal.parity` class.

**A sixth gap that is not on the brief's list and is stated anyway**, because narrowing by
omission is the same defect: **slot RESOLUTION is not graded by any vector in this store.** The
four parity vectors assert a journal *entry* read back from the oracle; none asserts that a
(product, slot, payment type) triple resolves to a particular account. The resolver exists in the
Go port and A2-8 graded resolution against the product read-back, but that grading was never
promoted and this task did not promote it either — every multi-leg entry spans several slots, so
a request shape whose `slot_code` names ONE slot does not describe them.
`ledger.slot.resolution` is marked `in_graded_domain: false` so a vector claiming it is refused
rather than graded against nothing.

**A correction to DEC-2 §4.4, recorded rather than inherited.** §4.4 records **I-5** (corrections
are reversing entries) as ungraded because *"the A2 corpus contains no reversal"*. **That is no
longer true** — A2-348 reversed `a28f573f34c7` and A2-349 read the three legs back carrying
`reversed = true`, and today's re-run shows the reversal pair. What is still missing is the other
half of I-5's statement — *"a correction ADDS a leg pair; it never MUTATES one"* — which is **not
observable from a snapshot at all**: the read-back shows the `reversed` flag **set on the original
rows**, and telling "flags and adds" from "flags and rewrites" needs the write path. **I-5 stays
ungraded with a corrected reason, and no reversal vector is promoted.** DEC-2 is ratified and I
have not amended it; the correction lives in `invariants.go` and in
`capabilities-ledger.json`.

---

## 10. The RED drives (P-22) — 17 cases, transcript committed

Script: `.softhouse/capture/tierA-a2/red-green-a2-15.sh`. Transcript:
`.softhouse/capture/tierA-a2/RED-GREEN-A2-15.txt`. **17 passed, 0 failed.** Every case runs
through **`bash .softhouse/conformance.sh`** — the route that actually executes (P-45) — except
CASE 8, which must select an implementation by name and therefore drives the binary directly.
Every case asserts its **diagnostic line**, never its exit code (P-62: `exit 2` is overloaded
across at least five conditions). Every perturbation is checked to have applied before the case
runs (a mutation proof over an unmutated file proves nothing). The store's digest is compared
before and after and the revert is **verified**, not assumed.

```
GREEN OK   exit 0   control: the pristine committed store (anti-no-op)
RED  OK    exit 2   CASE 1 — ONE MINOR UNIT (27045058 -> 27045059) must be a MONEY kill with a non-zero margin
RED  OK    exit 2   CASE 2 — a resolved gl_account_code (10201 -> 10202) must be a STRUCTURAL kill
RED  OK    exit 2   CASE 3a — one credit leg moved by ONE MINOR UNIT: the port REFUSES an entry the oracle accepted
RED  OK    exit 2   CASE 4 — I-2 ALONE: splits_sum_to_whole VIOLATED while double_entry_balances still HOLDS
RED  OK    exit 2   CASE 5 — a declared invariant_exemptions entry must be INADMISSIBLE
RED  OK    exit 2   CASE 6 — INFLATION: a seventh ledger vector must fail the pinned ledger parity count
RED  OK    exit 2   CASE 7 — DEFLATION: with EVERY ledger vector deleted the run must REFUSE
RED  OK    exit 1   CASE 8/ledger-wrong-truncating            (money kill, margin -25 minor units)
RED  OK    exit 1   CASE 8/ledger-wrong-truncating            (I-1 VIOLATED: debits 30000000, credits 29999900)
RED  OK    exit 1   CASE 8/ledger-wrong-header-refusing
RED  OK    exit 1   CASE 8/ledger-wrong-manual-permission-ignored
RED  OK    exit 1   CASE 8/ledger-wrong-netting-totals
RED  OK    exit 1   CASE 8/ledger-wrong-code-ignored
RED  OK    exit 1   CASE 8/ledger-wrong-split-drift
REVERT OK  — the ledger vector set is byte-identical to where it started.
GREEN OK   exit 0   control: the pristine committed store, AFTER every drive
```

The two money margins, quoted from the transcript so the "money kill with a non-zero
`margin_minor`" half of DEC-2 §5.2 requirement 7 is not taken on trust:

```
legs[0].amount_minor: MONEY want 27045059, got 27045058 (margin -1 minor units)      <- CASE 1
legs[0].amount_minor: MONEY want 10000025, got 10000000 (margin -25 minor units)     <- CASE 8/truncating
```

and the structural one, reported as a **cell difference** and not as money:

```
legs[0].gl_account_code: want "10202", got "10201"                                   <- CASE 2
```

### Two cases that failed first, and what they measured

**Both are recorded rather than quietly rewritten**, because a red drive edited until it passes
has measured the edit and not the guard.

- **CASE 3 as first written did not fire.** It perturbed one credit leg and demanded
  `INVARIANT double_entry_balances VIOLATED`. The invariant never ran, because **the correct
  implementation REFUSES an unbalanced entry rather than posting one** — `GoPoster.PostEntry`
  calls `ledger.DoubleEntryBalances` and returns the oracle's own 403. That is the right
  behaviour, it is what LDG-REFUSE-01 grades, and it means I-1's VIOLATED branch is unreachable by
  perturbing a vector while the correct port is selected. The case is **split**: 3a asserts what
  actually happens (the port refuses), and 3b reaches the VIOLATED branch through
  `ledger-wrong-truncating`, whose truncated legs genuinely do not balance.
- **An earlier form of CASE 3 also revealed an admissibility rule working.** Perturbing only the
  *request* text made the vector INADMISSIBLE, because this schema refuses a vector whose
  `request.legs[i].amount_major_text` disagrees with its `expect.legs[i].amount_major_text` — both
  transcribe the same oracle characters, so a disagreement is a transcription defect and not a
  divergence to grade.

---

## 11. DEC-2 §5.2's seven requirements, discharged one by one

**Requirement 1 — before/after digests of EVERY `.json` under `.softhouse/vectors/loanschedule/`,
the DIRECTORY and not a count.** 50 files digested before the first edit and again at the end;
`diff` of the two digest lists is **empty**. **All 50 loanschedule vector files are
byte-identical**, including the four `contract-refusal` vectors revision 3's wording would have
left unprotected.

**Requirement 2 — unfiltered run before and after, same populations and the same cell count.**
`46 / 4 / 1`, `7884 graded, 93 ungraded`, `106 money / 7 structural kills`, `4 exempted` — every
figure identical to `B`. `B` was measured in this worktree at `2d41838`, not copied from the ADR.

**Requirement 3 — `conformance.sh loanschedule` before and after.** `PASS (exit 0)`, `46 / 4 / 0`,
**7863 cells** — identical to `B`'s filtered run. **The report gains three lines** (a
`LEDGER NOT SELECTED` banner naming the filter) and the census gate gains two lines saying the
ledger figures were not compared. **I am not claiming byte-identity of the filtered transcript,
and requirement 3 read literally asks for it**; every *graded figure* is identical and the added
lines are a banner that grades nothing. **This requirement also CAUGHT A REAL REGRESSION I had
introduced**: the ledger half initially ran under a `loanschedule` filter, found zero selected
vectors, and the capability-coverage rule correctly refused — turning a green filtered run into
exit 2. Every part of that was right and the conclusion was wrong: *"no ledger vector was
SELECTED"* is not *"no ledger vector KILLS"*. Fixed in `gradeLedger`, with the measurement
recorded in the code.

**Requirement 4 — no diff to `contract.go`, no DEC-1 amendment.** `git status` shows
`nexus/internal/apps/loanschedule/contract/contract.go` **unmodified**. No new sentinel was
added; the ledger schema defines its own refusal shape (an HTTP status + globalisation code +
message) which is not a contract sentinel and is not confusable with one.

**Requirement 5 — `bash`, never `sh`; never `gofmt -w contract.go`.** Every invocation used
`bash`. `gofmt -l` reports exactly `contract.go` and nothing else, which is G-3's expected state.

**Requirement 6a — SAME BYTES, BEFORE and AFTER.**

*BEFORE*, on today's harness, built from the tree with my Go changes **stashed** (so these are the
real pre-change bytes, not a description of them). Quoting the diagnostic and the surviving
population, never the exit code (P-62):

```
--- FILES THAT COULD NOT BE READ AS VECTORS (each one makes this run unusable) ---
    ledger/LDG-01-manual-je-3leg-minor-units.json: decode: json: unknown field "dec2_revision"
    ledger/LDG-02-repayment-split-4leg-minor-units.json: decode: json: unknown field "dec2_revision"
    ledger/LDG-03-overpayment-4leg-minor-units.json: decode: json: unknown field "dec2_revision"
    ledger/LDG-04-header-account-accepted.json: decode: json: unknown field "dec2_revision"
    ledger/LDG-REFUSE-01-unbalanced-by-one-minor-unit.json: decode: json: unknown field "dec2_revision"
    ledger/LDG-REFUSE-02-manual-adjustments-not-permitted.json: decode: json: unknown field "dec2_revision"

    parity vectors   PASS 46   FAIL 0
    inadmissible     0
    cells compared   7884 graded, 93 ungraded
```

The first ledger-only field the decoder meets is `dec2_revision`, and the loanschedule population
is intact at `B`. This is A2-28's measured BEFORE shape, on my own bytes.

*AFTER*, the same six files: **admitted, graded and reported**, in a `ledger`-context section
under their own comparator and their own counts — `ledger parity PASS 4`, `ledger oracle-refusal
PASS 2`, `70 graded cells / 21 money` — with **`parity vectors PASS 46`** and **`cells compared
7884`** unmoved. `B.parity` did **not** become `B.parity + 1`.

**Requirement 6b — the admission-layer refusals, on DIFFERENT bytes, and the design question
answered in writing.**

*BEFORE* (pre-change tree, a loanschedule-decodable vector wearing a ledger label): both mandated
refusals fire together, `inadmissible 1`, parity unmoved at 46:

```
schema "gerege.ledger.vector/v1", want "gerege.loanschedule.vector/v1"
context "ledger" is not a context this harness grades — "gerege.loanschedule.vector/v1" accepts
only _selftest, loanschedule …
    parity vectors   PASS 46   FAIL 0
    inadmissible     1
```

**The design question, answered.** *"State which refusal 6b's bytes hit after the change and why
it is still the right one."* After the change those bytes hit a **different and better** refusal,
and the reason is P-9's obligation transferring exactly as DEC-2 predicted. There are now two
distinct files and I planted both:

- **6b-i, the costume file** (loanschedule content, `schema: gerege.ledger.vector/v1`): it is no
  longer *"a vector whose schema is not `gerege.loanschedule.vector/v1`"* — it **is** a vector of
  the other schema, so `admit.go:109-110` is the wrong refusal for it and no longer fires. The
  routing probe hands it to the **ledger** loader, which reports it **BY NAME** and makes the run
  unusable: `LEDGER FILE THAT COULD NOT BE READ: ledger/REQ6B-COSTUME-…: decode: json: unknown
  field "dec1_revision"`. **This is the right refusal**: the file claims a schema, that schema's
  loader owns it, and it dies there with its own name on it rather than being reported as a
  misspelling in somebody else's schema.
- **6b-ii, the allowlist file** (`schema: gerege.loanschedule.vector/v1`, `context: ledger`): the
  loanschedule context allowlist still fires, verbatim and undiminished —
  `context "ledger" is not a context this harness grades … accepts only _selftest, loanschedule`,
  `inadmissible 1`, `parity vectors PASS 46`. **The allowlist was not weakened while a schema was
  added beside it**, which is 6b's whole purpose.

Both probe files were removed; the `ledger/` directory contains exactly the six promoted vectors.

**Requirement 7 — the four-cell matrix, all four stated.**

| | pristine expectation | perturbed expectation |
|---|---|---|
| **correct implementation** (`ledger-go`) | **GREEN** — `ledger parity PASS 4`, `oracle-refusal PASS 2`, 0 violations | **RED** — RED-drive CASES 1–4, both a **structural** cell and a **money** cell perturbed by exactly ONE MINOR UNIT, reported as a money kill with `margin -1 minor units` |
| **named wrong implementation** | **RED** — RED-drive CASE 8, **six** registered wrong implementations, each selected by name with `-ledger-impl` and each shown going red | not required |

The **conjunction** revision 4 replaced the disjunction with is satisfied: **(i)** a structural
cell (`legs[0].gl_account_code`) **and (ii)** a money cell perturbed by exactly one minor unit,
reported as a **money** kill with a non-zero `margin_minor`. `glAccountType` is not the
perturbation cell and cannot be — `admit.go` refuses it as a `divergent_cells` entry.

---

## 12. DEC-2 §5.3's preconditions — where each one landed

| # | precondition | discharged |
|---|---|---|
| **P-6** | where ledger capability rows live | **DECIDED**: a separate `.softhouse/vectors/capabilities-ledger.json`, schema `gerege.ledger.capabilities/v1`. Rejected alternative recorded in `capability.go`: appending to `capabilities.json` would put a **DEC-1 revision number** in charge of DEC-2 data and leave a file whose schema string names a context half its rows do not belong to. |
| **P-1** | a ledger vector schema covering product id, product type, accounting rule, slot family, slot code, payment type id, seam | **BUILT.** All seven are present on `Request`. They are populated on an accounting-path vector and zero/empty on a manual one — a schema that omits a field for the case that does not use it cannot express the case that does. `slot_code = 0` on a multi-slot entry means *"not a single-slot entry"*, stated in the vector's note. |
| **P-7** | what contract revision a non-loanschedule vector declares | **DECIDED**: `dec2_revision`, checked against `PIN-ledger.json`, never `dec1_revision`. The pin carries **no contract digest and no slot for one** — DEC-2 §1.1: there is no counterpart Go file for this context, and a slot for a digest that does not exist invites somebody to fill it with the wrong file. |
| **P-2** | an oracle-faithful refusal shape, not confusable with a contract sentinel | **BUILT**: `Refusal{http_status, code, message}`, graded as three cells. Deliberately not called `contract-refusal`, since in the other store that name means *derived from the contract, nothing observed* — the opposite provenance rule. |
| **P-3** | a class an observed non-schedule oracle answer can be filed under | **BUILT**: `oracle-refusal`. |
| **P-4** | a comparator, and a cell whitelist DERIVED from it | **BUILT.** `CellFields()` is **computed** by running the comparator over a probe and collecting what it emitted — a cell the comparator stops comparing disappears from the vocabulary automatically, and a cell added to a list without being wired cannot appear at all. The 10 cells: `leg_count`, `legs[].gl_account_id`, `legs[].gl_account_code`, `legs[].entry_side`, `legs[].amount_minor`, `total_debits_minor`, `total_credits_minor`, `refusal.http_status`, `refusal.code`, `refusal.message`. |
| **P-5** | money cells as int64 minor-unit STRINGS, paired with the oracle's own characters | **BUILT**, and the pairing is enforced at admission in both directions. |
| **P-9** | the ledger schema declares its own contexts | **BUILT**: `SchemaContexts() = {"ledger"}`, enforced in `Admit`, tested by `TestContextAllowlist`. |
| **P-10** | a mechanism that actually RUNS a named wrong implementation | **BUILT**: `RegisterWrong` + `-ledger-impl`. `admit.go` **refuses** a `graded_against` entry naming an implementation that is not registered, or one registered as *correct*. `TestEveryWrongImplementationIsKilled` fails the build if a registered wrong implementation survives the corpus — because a wrong implementation nothing kills is the same defect as a `graded_against` row nothing executes, one level in. |
| **P-8** | the I-3/I-4 source guard | **LANDED** before this task (A2-18 / T208). Its residue is unchanged and is restated in `invariants.go`: **both** I-4 arms (`I4-DML` and `I4-BUILDER`) inspect an **empty** population in this Go tree, so neither form of I-4 detection is exercised by this tree at all. |

---

## 13. Everything I am leaving `[UNVERIFIED]`

1. **The precedence between the two manual-entry refusals.** A2-346's request is *balanced* and
   A2-344's legs are both on manual-permitted accounts, so **no captured request violates both
   rules** and nothing in this corpus can order them. `GoPoster` checks manual permission first
   only because that is the order the observed pair is consistent with. **A port that checks them
   in the other order passes both promoted refusal vectors.** Stated in `impl.go`, in
   LDG-REFUSE-02's note and in `capabilities-ledger.json`.
2. **The residue half of G-08.** No capture carries a non-zero digit beyond two decimal places, so
   the *refusal* rule — `ErrInvalidRequest` rather than truncate-or-round — is specified from
   source and **killed by nothing**. A2-8 said as much and it is still true.
3. **Whether a HEADER account would be refused at PRODUCT CREATE time.** A2-312 threw on gl 2
   first and never reached `loanPortfolioAccountId: 1`. LDG-04 settles the POSTING question only.
4. **Whether any future ledger vector will need an invariant exemption.** If one does, this schema
   needs a grounding classifier of its own first.
5. **`ACCRUAL_UPFRONT` (accountingRule 4).** Refused for one reason and it is EVIDENTIAL, not
   source-based: **no capture exists at 4**. DEC-2 §4.2 already established that the loan-side
   switch falls through to the full accrual mapping set; admitting the value on a source reading
   would be the move this program forbids.
6. **`MANIFEST.sha256`** in `.softhouse/capture/tierA-a2/` was **not** updated for A2-390. I
   looked: nothing in `conformance.sh` or `.softhouse/capture/lib/*.py` references it
   (`grep -rn 'MANIFEST'` over both, zero hits), so it is not a gate — but it is now
   incomplete, and I am naming that rather than leaving it to be discovered.
7. **The `gofmt`/no-float/ledger-invariant guards over my new package** all pass, and the ledger
   guard's own limits are unchanged and unimproved by this task: the detection surface is the
   NAME, so renaming a balance defeats it; triggers, migrations and stored procedures are not
   walked; I-5's semantic half and non-Go callers are not covered.

### Where I looked before recording an absence (P-66 / P-70)

- *"No ledger invariant reads `glAccountType`"* — scope: `AssertInvariants` and both assertion
  functions in `nexus/internal/apps/ledger/conformance/invariants.go`, read in full; and DEC-2
  §4.4's I-1…I-7 table, read in full. Those two are the complete population of invariants this
  context has.
- *"Nothing verifies `MANIFEST.sha256`"* — scope: `.softhouse/conformance.sh` and
  `.softhouse/capture/lib/*.py`, `grep -rn 'MANIFEST'`, ugrep 7.5.0 on `PATH`. **It is not a
  repository-wide sweep** and I am not claiming one.
- *"Every journal entry is MNT"* — scope: `SELECT json_agg(DISTINCT currency_code) FROM
  acc_gl_journal_entry` on the live oracle today, all 60 rows. That is the whole table, not a
  sample.
- **Calibration (P-72):** the byte-provenance sweep was calibrated on known positives before its
  negatives were believed — it reported **2 failures** on its first run (the refusal-status check
  looked for `"httpStatusCode": "403"` with a space; the artefact has none), which is the
  instrument demonstrating non-zero recall on a real mismatch. The checker was corrected and the
  transcript is committed at 0 failures.
- **Regex engines.** I did not rely on `\b` anywhere. Every sweep in the committed scripts uses
  `grep -aF` (fixed strings, `LC_ALL=C`) or a `sed` expression with explicit character classes,
  so the three-engines-three-answers hazard T232 measured does not arise. The commands are
  **committed**, not described (P-72 corollary 2).

---

## 14. Files

**New**
```
.softhouse/vectors/ledger/LDG-01-manual-je-3leg-minor-units.json
.softhouse/vectors/ledger/LDG-02-repayment-split-4leg-minor-units.json
.softhouse/vectors/ledger/LDG-03-overpayment-4leg-minor-units.json
.softhouse/vectors/ledger/LDG-04-header-account-accepted.json
.softhouse/vectors/ledger/LDG-REFUSE-01-unbalanced-by-one-minor-unit.json
.softhouse/vectors/ledger/LDG-REFUSE-02-manual-adjustments-not-permitted.json
.softhouse/vectors/PIN-ledger.json
.softhouse/vectors/capabilities-ledger.json
nexus/internal/apps/ledger/conformance/{vector,impl,grade,invariants,admit,capability}.go
nexus/internal/apps/ledger/conformance/conformance_test.go
.softhouse/capture/tierA-a2/sql/q7-a2-15-ledger-state-json.sql
.softhouse/capture/tierA-a2/out/A2-390-db-ledger-state-a2-15.{json,http,status}
.softhouse/capture/tierA-a2/red-green-a2-15.sh
.softhouse/capture/tierA-a2/RED-GREEN-A2-15.txt
.softhouse/capture/tierA-a2/verify-provenance-a2-15.py
.softhouse/capture/tierA-a2/PROVENANCE-A2-15.txt
```

**Modified** — every edit additive; no loanschedule vector, and no line of `contract.go`, changed.
```
.softhouse/conformance.sh                                          (4 new pinned figures + the gate)
nexus/internal/apps/loanschedule/conformance/vector.go             (schema routing)
nexus/internal/apps/loanschedule/conformance/census.go             (variadic alsoClaimed; 2 root files)
nexus/internal/apps/loanschedule/conformance/grade.go              (Summary.Ledger, gradeLedger, exit)
nexus/internal/apps/loanschedule/conformance/report.go             (the ledger section)
nexus/internal/apps/loanschedule/conformance/cmd/conformance/main.go (-ledger-impl)
nexus/internal/apps/loanschedule/conformance/store_integrity_test.go (census hand-over)
nexus/internal/apps/loanschedule/conformance/coverage_refusal_test.go (skip ledger-schema files)
```
