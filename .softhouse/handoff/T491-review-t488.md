# T491 — INDEPENDENT adversarial review of T488 (Tier D GL capture plan)

Task `T491` (`reviewer`), cloud fire, context `tierD-test-corpus`.
Branch `softhouse/T491-review-t488`. Reviewing `softhouse/T488-tierD-gl-corpus-capture-plan` @ `7a74ef5c`.

Full findings: **`.softhouse/reviews/t491-review-t488/REVIEW.md`**.

---

## Verdict

**ACCEPT WITH CONDITIONS.** 4 MAJOR, 9 MINOR. Citation support rate **66/67 = 98.5%** on a stated
67-citation sample checked for *support*, not resolution.

**Safe to hand to an oracle-reaching fire to execute unattended: YES**, once conditions 1–4 are applied —
all four are text edits requiring no oracle.

## The question that mattered most

**Does any row state a value the worker did not observe? NO.** I swept all 29 ids (27 cases + `TDG-00` +
de-scoped `TDG-B1`) and every prose section. There is no `expect` column and no value in an expectation
position. The `SOURCE-DERIVED HYPOTHESIS` rows — the ones most at risk — name shapes and branches, never
amounts, and each states a refutation condition. Values that appear are (a) `TEST-ASSERTION` literals
labelled with `FILE:LINE`, each of which I verified is genuinely what that file asserts, (b) ratified
`CLAUDE.md` tenant parameters, (c) one scale-6 format illustration marked "e.g.", (d) the pinned sha.

## The four MAJORs

- **F-1** — *"exactly one direct `POST /journalentries` call site, used by one test"* and the derived
  finding *"Fineract's own tests never post a manual journal entry for its own sake"* are **FALSE**. There
  are **three** in `integration-tests` (`GLAccountIntegrationTest.java:115`;
  `InitiateExternalAssetOwnerTransferTest.java:1315` and `:1349`) and two more in
  `fineract-e2e-tests-core/.../JournalEntriesStepDef.java:384,397`. `:1349` sits in a test named
  `addManualJournalEntriesWithAssetExternalization` that posts a manual JE, reads it back and asserts on the
  legs; `:1315` is a manual-JE **refusal** arm. The cited grep (`grep -rn "journalentries"`) is structurally
  blind to these call sites, and the universal claim was made over files §1.3 row 18 declares **NOT OPENED**.
  Two cheap in-scope cases (`externalAssetOwner` accept + refuse) were missed.
- **F-2** — TDG-C3's cited lines **do not support** its claim. `CreateJournalEntriesForChargeOffLoanTest.java:105-107`
  names `CHARGE_OFF_EXPENSE` in the very arm cited as showing the slot "is not reached". The claim is
  nonetheless **true** on main source (`AccrualBasedAccountingProcessorForLoan.java:909-928`). Worse: that
  mock test (Apr 2026) predates the processor's rework (Jul 2026) and verifies a 9-arg helper overload the
  charge-off path no longer calls — group C's hypotheses need re-anchoring to main source.
- **F-3** — the savings/deposit rejection is labelled **LEGAL** and declared *"on grounds no later agent may
  re-litigate"*. That reads an **activation gate as a scope block**, contrary to `CLAUDE.md` ("a licensing
  gate on the ACTIVATION, not a scope block on the PORT"), and applies a POLICY bullet scoped to the
  **SHARED** oracle (`reference-oracle.md:1115,1163`) to a throwaway — while treating the neighbouring
  bullets in the same list as standing-only. The **outcome is right** on PRODUCT/ENGINEERING grounds
  (an NBFI deployment exposes no deposit endpoint; DEC-2's graded domain is loan/GL); the label and the
  finality are wrong.
- **F-4** — a copy-from-Fineract hazard exactly parallel to the plan's own §1.4(b), unflagged and sitting in
  the corpus §8 item 2 names as the top follow-up: `JournalEntriesStepDef.java:366` sets
  `runningBalance=true` on every journal-entry read-back. Under `admit.go:141` →
  `oraclederived.go:230-243`, a capture carrying those response fields is **INADMISSIBLE**.

## What I re-derived and AGREE with (independently, before reading T488)

`320,601` test LOC / `1,254` files (exact); `158` `.feature` files / `200,763` LOC (exact); `1,427` journal
lines (exact); `533` / `192,234` integration-tests (exact); `30` / `33,910` `JournalEntryHelper` users
(exact); `fineract-accounting/src/test` = 1 file / 88 LOC (exact); 16 float-widening sites at identical line
numbers; 14 capabilities / 6 not in graded domain; 17 ledger vectors, `dec2_revision: 5`;
savings/deposit JE tests **7,755 LOC / 98 `@Test`** (T488: 7,489 / 97 — within one).
Pin verified: `426a23544e8426a38ae43ae404670a0a7e85b9eb`, tree clean, untouched.

**Both de-scopes are CORRECT and better-founded than stated.** `ledger.multi.currency.entry` — re-derived
from source: `SingleDebitOrCreditEntryCommand.java:33-35` (no currency field), `JournalEntryCommand.java:40`
(one scalar); plus `admit.go:165-172` refuses non-MNT outright. `ledger.running.balance` — G-12 open and no
schema field both confirmed (`admit.go:128-149`); the MySQL-only `group by … desc` confirmed at
`GLAccountReadPlatformServiceImpl.java:129,131`. Two caveats: the **"HTTP 500"** half is a runtime claim
carried without an `[UNVERIFIED]` tag, and it is true of `/glaccounts` only —
`GET /journalentries?runningBalance=true` **does** work on PostgreSQL and was captured by T429. A **fourth,
stronger blocker** goes unnamed: `admit.go:141`'s `CaptureRuleReasons`. **No third capability is unreachable
and none is wrongly planned.** The self-caught `is_deleted` correction is **RIGHT** (`acc_gl_account`
`0001_initial_schema.xml:49-75`, eleven columns, no marker; `acc_gl_closure` has one at `GLClosure.java:50-51`).
The instrument correction is **CONFIRMED** both ways (`cap8.sh:82-86` sends no key; `cap11.sh:53` refuses
without one). Tenant parameters are pinned for every capture and `TDG-X2` correctly **re-takes** T352's
non-attested residue observation rather than reusing it.

## Conditions

1. F-1 — correct the call-site claim and the "never for its own sake" finding; add the two
   `externalAssetOwner` manual-JE cases.
2. F-2 — re-cite TDG-C3 to `AccrualBasedAccountingProcessorForLoan.java:909-928`; note the mock corpus's
   staleness; re-anchor group C to main source.
3. F-3 — re-label PRODUCT, keep the exclusion, strike "no later agent may re-litigate", record that porting
   deposit code stays in Tier B scope.
4. F-4 — add the `runningBalance=true` copy-hazard to §1.4(b) and §8 item 2.
5. F-5/F-6/F-7 — fix three mining numbers/scopes (48 vs 56 feature files; 6/4/1 not 5/5/1; widen the
   `glclosures` search).
6. F-9 — align §10 and the handoff to §8 item 7's accurate wording so TDG-A1's `403` cannot read as a target.
7. F-10/F-12 — relabel `TDG-00` item 1 a checkout fact; record that snake_case SQL columns do not trip the
   camelCase capture scanner.

## Scope and limits of this review

No oracle, no PostgreSQL, no Docker daemon in this sandbox. **I executed no capture and claim none.** Every
runtime statement is a statement about code I read. I **confirmed** the pin, nine of ten mining measurements,
the reversal write path's six source claims, the four-command POST surface, the tenant-`default` defect, the
`is_deleted` correction, the multi-currency seam impossibility, the running-balance SQL, both instruments,
the tenant pins and the rig template. I **refuted** the manual-JE call-site claim and TDG-C3's citation. I
was **unable to falsify and did not confirm** any runtime behaviour, including the "HTTP 500" status, the
predicted refusal branches, and throwaway bring-up cost.

Nothing was promoted, no vector created, no DEC-n or capability file amended, no Go written, `nexus/`
untouched, `/home/user/fineract` read-only and unmodified.
