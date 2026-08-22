# T276 — INDEPENDENT review of T275's A2 gap capture

Reviewer T276, branch `softhouse/t276-review-t275-capture`, local fire `20260822-060013b`.
Subject: `softhouse/t275-a2-gap-capture` @ `35721bb`, diffed `main...` (three dots).
Oracle REACHABLE this fire: `https://localhost:8443`, tenant `gerege`, container
`fineract-fineract-1` / `fineract-db-1` (PostgreSQL 18.3), pinned Fineract checkout
`/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` (`git rev-parse HEAD`,
confirmed by me).

I did not plan or take these captures. I started from the assumption that they contain a
synthesised value and tried to find it. I did not find one.

## VERDICT: **APPROVED**

The headline is **CORRECT and I reproduced it independently against the live oracle with my
own query**. The four load-bearing claims below it all hold. Six notes are recorded at the
end; none is a defect in a capture, none changes a finding, and one of them is a disclosure
about state *I* moved.

---

## 1. THE HEADLINE — re-issued by me, against the live oracle, with my own query. **CONFIRMED.**

T275 claims `CAPTURE-PLAN.md` §5's title "delete-then-recreate" is FALSE and that the oracle
**reconciles by key**. I did not read T275's `q8`; I wrote my own identity query
(`evidence/10-identity-query.sql` — `SELECT m.id, …` plus `max(id)` over the whole table) and my
own driver (`evidence/10-run.sh`, `evidence/11-run2.sh`). Full transcripts in
`evidence/10-*.txt` and `evidence/11-*.txt`.

**Before I sent anything**, the live table already stood exactly where T275's captures say it
was left — product 23 = ids 12–21 plus channel row **96** (`fat=1, pt=2, gl=17`),
`max(acc_product_mapping.id)` = **153**. That is a first, free corroboration: the recorded end
state is the state the oracle is actually in.

My own re-issue, each row an observation from the transcript:

| my step | request | row identity I observed |
|---|---|---|
| G1 | `PUT {fundSourceAccountId:18}` (generic slot, ASSET→ASSET) | **id 12 SURVIVES**, `gl` 16→18, `max(id)` **unmoved** at 156 |
| G2 | `PUT {fundSourceAccountId:21}` (ASSET→LIABILITY) | **id 12 SURVIVES**, `gl` 18→21, `max(id)` **unmoved** |
| S2 | `PUT paymentChannel[pt2→16]` — same key, new account | **id 96 SURVIVES**, `gl` 17→16, `max(id)` **unmoved** at 153 |
| S3 | `PUT {description}` — no accounting parameter at all | **11 ids in, 11 ids out, zero churn**, `max(id)` unmoved |
| S4 | `PUT paymentChannel[]` | row **96 DELETED**, **nothing recreated**, `max(id)` unmoved at 153 |
| S5 | re-add the same entry | **new id 154** — 96 is **not** reused |

Every one of T275's four identity claims reproduces. **§5's title is refuted and the port
implication is real**: a Go port written to "rebuild the mapping set on every product save"
would churn every `acc_product_mapping.id` on every save, and would look correct in `q2`'s
projection while doing it.

**Corroborated at source, which T275 deliberately did not claim.** T275 marked the JPA
mechanism `[UNVERIFIED]` and said Finding 1 is a statement about observed row identity only.
That restraint was right, and the source now independently agrees with the observation —
`fineract-accounting/.../ProductToGLAccountMappingHelper.java`:

- `:417` `deleteAll(existingPaymentChannelToFundSourceMappings)` — **only** when the input map is empty (my S4);
- `:435-436` `setGlAccount(...)` + `saveAndFlush(existing…)` — key present, GL differs → **update in place** (my S2);
- `:440` `delete(existing…)` — key **left** the list;
- `:447` `savePaymentChannelToFundSourceMapping(...)` — only for keys not already present (my S5).

Line numbers 417 and 440 as cited by T275: exact.

**Finding 2 (`changes` is an echo, not a delta, and is a JSON *string*) is also confirmed at
source**: `:404-405` does `changes.put(PAYMENT_CHANNEL_FUND_SOURCE_MAPPING, command.jsonFragment(...))`
— the submitted fragment, unconditionally. My S2/S4/S5/S6/S7 responses all carry it as an
escaped string, e.g. `"paymentChannelToFundSourceMappings":"[{\"paymentTypeId\":2,…}]"`.

**A refusal I hit by accident corroborates FINDING 6 verbatim.** My first attempt repointed the
generic slot to GL 2 and the oracle returned 403 with
`Passed in GLAccount fundSourceAccountId with Id 2maps to the account Fund Source of type INCOME…`
— **`2maps`**, the same missing space T275 recorded as `13maps`. Not a transcription artefact.

### NEW measurement — I closed two of T275's own `[UNVERIFIED]` items

T275 explicitly scoped Finding 1 to *value* changes at a *fixed* key and flagged key change and
multi-entry as not established. I sent both:

- **S6, key change pt2 → pt1:** row 154 **DELETED**, new row **155** created. So for a **key
  change** the behaviour *is* delete-and-recreate — which does **not** contradict Finding 1, it
  is what reconcile-by-key predicts, and T275's `[UNVERIFIED]` marking was honest and exactly
  right about its own scope.
- **S7, multi-entry `[pt1→16, pt2→17]`:** existing key pt1 row **155 SURVIVES** unchanged, new
  row **156** appended for pt2. Reconcile-by-key holds for multi-entry lists too.

These are additions for the promotion task, not corrections.

## 2. "q2 cannot answer its own question" — **CONFIRMED, in one read.**

`sql/q2-product-mapping-rows.sql` selects `m.product_id, p.accounting_type, m.product_type,
m.financial_account_type, m.payment_type, m.charge_id, m.gl_account_id, g.gl_code, g.name,
g.account_usage, g.classification_enum`. **`m.id` appears only in the `ORDER BY`, never in the
select list.** "Updated in place" and "deleted and reinserted" are therefore byte-identical in
its output. The previous fire's plan named the one query that could not have decided the
question it was posed. T275 is right, and right to have re-run q2 anyway (`A2-513`) because §5
asked for it.

## 3. The two §5 blockers T275 says did not hold — **BOTH CONFIRMED against the live instance.**

Measured by me, now, on `fineract_gerege`:

```
active_loan_charges | penalties | fees
                 18 |         2 |   16
```

§5's *"needs an `m_charge` fixture; none exists on `gerege`"* is **false at this fire**. T275
created no fixture and the charge dimension went from **0 to 7** charge-scoped rows. I confirmed
all seven on the live DB, and with them Findings 4, 5 and 7:

| row | product | fat | charge | `is_penalty` | gl |
|---|---|---|---|---|---|
| 107 | 56 | 5 (penalties) | 6 | **t** | 8 |
| 108 | 56 | 4 (fees) | 1 | f | 11 |
| 119 | **57** | 4 | 2 — **not attached to the product** | f | 11 |
| 130 | **58** | 5 (penalties) | 1 — a **non**-penalty charge | **f** | 8 |
| 131 | **58** | 4 (fees) | 6 — a **penalty** charge | **t** | 11 |
| 152 | **60** | 4 | 1 | f | 11 |
| 153 | **60** | 4 | 1 — **same chargeId, different account** | f | 8 |

FINDING 7's identity burn is real: `SELECT count(*) FROM m_product_loan WHERE id=59` → **0**, and
`count(*) FROM acc_product_mapping WHERE id BETWEEN 132 AND 141` → **0**. A refused create burned
both ranges.

The second blocker — *"a dangling write-off-reason id needs the fixture"* — is refuted by
definition and by observation: the fixture is what would make an id **resolve**, and `A2-540`
returns 400 `validation.msg.writeoffreason.invalid` without one. See §4 below: I re-issued it.

**The rows T275 left EXCLUDED are blocked on fixtures I measured myself this fire**, not
inherited:

```
 id |                   code_name                   | n_values
 26 | WriteOffReasons                               |        0
 39 | ChargeOffReasons                              |        0
 40 | capitalized_income_transaction_classification |        0
 41 | buydown_fee_transaction_classification        |        0
        total m_code_value rows: 22
```

So the *resolving* reason case and collision keys 22/24/25 are genuinely unreachable without
seeding. The savings/shares row is excluded on **policy**, correctly: A2 is loans, and
deposit-taking activation is prohibited under the ratified NBFI licence (CLAUDE.md; Law on
Non-Banking Financial Activities Art. 12.1.3/12.1.4). No exclusion covers an untaken capture.

## 4. The re-issue prover — **RUN BY ME, and I tried four ways to make it lie.**

`python3 prove-t275-reissue.py` from a `git archive` of the branch: **exit 0**, LEG 1 32/32
VERIFIED, LEG 1b 10/10 UNVERIFIABLE, LEG 1c D-1 reproduced from committed bytes, LEG 2 STALE on
exactly the one mutated byte and VERIFIED on the other 31, LEG 3 all six green against the live
oracle. Transcript: `evidence/20-prover-rerun-by-reviewer.txt`.

| my attempt to make it lie | result |
|---|---|
| **A.** Mutate a captured RESPONSE (`A2-521…json`, `"id":23`→`24`) | **exit 1**, 3 FAILs. LEG 3 caught it directly, **and both SUPERSEDED_READ assertions caught it too** |
| **B.** Delete a recipe (`A2-502….http`) | **exit 1** — `LEG 1 STALE … no .http and no .psql record at all`. Does not silently pass |
| **C.** Delete an auto-discovered SQL record (`A2-503….psql`) | **exit 0**, population silently 32→31. `manifest.py verify` catches it: `MISSING out/A2-503-….psql`, **exit 1**. See note N-4 |
| **D.** Mutate a *mutating* capture's response (`A2-502….json`) | prover exit 0 — and it **says in terms** that it makes no response claim for the 16 mutating captures. `manifest.py verify` catches it: `CHANGED`, **exit 1** |

**Did it invert or loosen? It INVERTED.** Test A settles this by measurement. A *loosened*
check would have been "a fresh read must merely DIFFER from the snapshot" — under which
mutating the current-state file changes nothing. The committed assertion is
`fresh != old AND fresh == current`, and in test A the second conjunct **fired on both
A2-501 and A2-512**: `re-issued bytes matching NEITHER the snapshot nor the current-state
capture`. That is a strictly stronger assertion than the one whose failure prompted it. The
disclosure is accurate.

**Byte-traceability of the recorded responses — the direct test.** I re-sent the **committed wire
bytes** (`out/NAME.req`, not the `req/` file the recipe names) for all five REFUSAL captures and
diffed against the recorded response:

```
A2-526  403 -> 403  RESPONSE BYTE-IDENTICAL
A2-540  400 -> 400  RESPONSE BYTE-IDENTICAL
A2-541  400 -> 400  RESPONSE BYTE-IDENTICAL
A2-542  400 -> 400  RESPONSE BYTE-IDENTICAL
A2-543  400 -> 400  RESPONSE BYTE-IDENTICAL
```

Five refusals, five byte-identical replays. A composed response does not do that. Every quoted
string in the handoff matches the committed JSON verbatim, including `13maps`, `[4, 2]`,
`parameterName: writeOffReasonsToExpenseMappings` with `args: []`, and A2-541's **account error
first, reason error second** — Finding 8's accumulation and ordering.

**`capsql.sh`'s transport-failure handler CAN FIRE** — the precedent defect (D-2, a handler that
could not) is closed, and I proved it rather than read it. Pointing a scratch copy at a
non-existent container: exit **1**, `TRANSPORT FAILURE … NO OBSERVATION WAS MADE`, all four
pre-existing artefacts **named and left byte-intact** (`cmp` clean).

**Other guards, re-run by me at the branch HEAD:**
`manifest.py verify` → `OK: 1138 files match MANIFEST.sha256`, exit 0.
`guard-parse-float-ast.py` → 21 call sites, 15 with `parse_float=`, 6 declared, **0 violations**, exit 0.

## 5. The PIN decision — **all four points verified in git by me. CORRECT, and the stake is measured.**

| T275's point | my verification |
|---|---|
| `admit.go:51-52` compares vector-to-pin, never reads the ADR | **Exact.** `grep -n DEC2Revision` → `51: if v.DEC2Revision != opts.Pin.DEC2Revision {` / `52: add("dec2_revision %d but the store pins %d", …)`. Nothing under `nexus/` or `conformance.sh` reads `DEC-2-gl-accounting` at all (0 matches) |
| rev 6's commit message says "DELIBERATELY NOT BUMPED" | **Verbatim** in `8e8d65d`: `vector store 13b8342e… UNMOVED` / `.softhouse/vectors/PIN-ledger.json dec2_revision: 5 DELIBERATELY NOT BUMPED`. `--stat -- docs/adr/DEC-2…` = 1 file, 10 insertions, 3 deletions, as claimed |
| rev 7 was never applied | **Confirmed.** `208f51c` "PREPARED, NOT LANDED", `5c5b97f` "revision 7 REJECTED", `bf04272` "rev 7 is not landable". `git log -- docs/adr/DEC-2-gl-accounting-adapter.md` lists revisions 1,2,3,4,5,6,8 — **no revision-7 commit touches the file** |
| rev 8's diffstat touches nothing under `.softhouse/vectors/` | **Confirmed.** `ed686d7` = 18 files: the ADR, 16 under `.softhouse/capture/t255-dec2-rev8/`, 1 handoff. No `.softhouse/vectors/`, no `conformance.sh` |

The ADR:232 quote, the `PIN-ledger.json` `_note` tying re-stamping to a **contract freeze**, and
the G-13 / G-14 "Do NOT bump" warnings (`gates.md:35`, `:3876`, `:3969`) are all present as
quoted. All eight files carrying `dec2_revision` say **5**; pin and corpus agree exactly.

**The stake is not asserted, it is measured.** I ran the existing
`.softhouse/reviews/t246-dec2-rev6/drive-pin-red.sh` (exit 0, `evidence/50-*.txt`):

```
GREEN   pin=5 vectors=5  ->  inspected=6 inadmissible=0
RED-A   pin=6 vectors=5  ->  inspected=6 inadmissible=6   (all six: "dec2_revision 5 but the store pins 6")
RED-B   pin=5 vectors=6  ->  inspected=6 inadmissible=6
GREEN2  pin=6 vectors=6  ->  inspected=6 inadmissible=0
```

**Bumping the pin alone would make all six ledger vectors inadmissible.** T275's decision to
leave it at 5, and not to edit it, is correct and fully earned. The promotion task should leave
it at 5 and cite this.

## 6. The standing checks

- **No float.** 0 float tokens in T275's 12 new request bodies (`grep -oE '[0-9]+\.[0-9]+' req/t275-*.json` → 0).
  `prove-t275-reissue.py:242` is the only new `json.load` call site and it passes `parse_float=str`.
  No `float`, `round(`, `Decimal` or `%f` in `capsql.sh`, `mkreq-t275.py`, `t275-mapping-diff.py`.
  `digitsAfterDecimal: 2` is an integer. Money is untouched by this diff entirely.
- **No synthesised oracle response.** Five refusals replay byte-identically from committed wire
  bytes; four idempotent captures replayed byte-identically before I moved state; the live DB
  independently carries every row id, every id gap and every fixture count the handoff claims.
- **Refusals recorded as observed, not paraphrased.** Every quoted error string is verbatim in
  the committed JSON, missing space and all.
- **Scope.** `git diff main...` name-only → **0** paths matching `.softhouse/vectors/`,
  `conformance.sh`, `tasks.json`, `LOCK`. `CAPTURE-PLAN.md` is **append-only** (§7 added at the
  end; §5's original text is not rewritten, it is corrected in an addendum). Confirms the
  driver's mechanical check, which I did not otherwise re-do.
- **Artefact completeness.** All 34 `A2-5xx` capture groups carry a complete artefact set — every
  HTTP capture has `.http`/`.json`/`.status` and, where a body was sent, `.req` + `.req.sha256`;
  every SQL capture has `.psql`/`.txt`/`.sql`/`.sql.sha256`. Zero incomplete sets.

---

## Notes recorded — none is a rejection, none touches a captured value

**N-1 — the handoff says "32 captures"; 34 `A2-5xx` capture groups are committed.** 32 is the
prover's population. `A2-504-loanproduct23-after-repoint` and `A2-507-loanproduct23-after-channel`
are committed GET captures that sit in none of the prover's three lists and are not reachable by
its `.psql` auto-discovery, so nothing re-issue-checks them. **I checked whether that concealed a
failure: it did not.** Applying the prover's own `SUPERSEDED_READ` assertion to both by hand
(`evidence/40-uncovered-get-captures.py`), both PASS — each differs from its own snapshot and
equals the current-state capture. The handoff's own Group A/A2/B/C tables enumerate all 34; only
the prose total says 32.

**N-2 — "All seven files that carry the field say 5" should be eight.** The enumeration right
beside it is complete and correct (`PIN-ledger.json` + six `LDG-*.json` + `capabilities-ledger.json`
= 8); `grep -rl dec2_revision .softhouse/vectors/` returns 8. A miscount in a count word, with
the correct list next to it. The conclusion is unaffected.

**N-3 — `prove-t275-reissue.py` LEG 2 dies with an unhandled traceback**, rather than a clean
`FAIL`, if the hardcoded victim's `.http` is missing (my test B). It still exits non-zero, so it
cannot pass silently; this is robustness, not correctness.

**N-4 — LEG 1's SQL population is self-derived from the artefacts it checks.** Deleting one
`.psql` shrinks the denominator from 32 to 31 and the prover still exits 0 (my test C). Defence
in depth holds — `manifest.py verify` reports `MISSING` and exits 1 — but the prover alone would
not catch a deletion. Worth a fixed expected count in whatever succeeds it.

**N-5 — DISCLOSURE: this review moved oracle state, and here is exactly what moved.** Verifying
the headline required sending the writes. I restored every **value**: product 23's generic
`FUND_SOURCE` is back on GL 16, the channel list is back to the single entry `pt2 → GL 17`, the
description is back to T275's string. `A2-521`'s GET **re-issues byte-identical again**
(`81032da4449d68ac`). What could not be restored is the **surrogate key**: the channel mapping
row is now id **156**, not 96, and `max(acc_product_mapping.id)` is **156**, not 153 — an
unavoidable consequence of the key-change probe, and itself a demonstration of Finding 1.
Concretely, `A2-544-db-mapping-after-reason-probes` no longer re-issues byte-identically; the
`diff` is **exactly three lines** — the row-id cell 96→156 (all other columns identical) and the
`max(id)` cell 153→156. Nothing else in the corpus is affected. A later fire should expect this
rather than read it as drift.

**N-6 — T275's `[UNVERIFIED]` list is now two items shorter**, by my measurement, not its own:
payment-type **key change** deletes-and-recreates (S6: row 154 gone, 155 created), and
**multi-entry** lists reconcile by key like single-entry ones (S7: row 155 survives, 156
appended). Both extend §7.5; neither contradicts anything T275 claimed.

---

## What I ran, so silence is distinguishable from not looking

```
git diff main...softhouse/t275-a2-gap-capture --stat / --name-only     (172 files; 0 scope hits)
git show softhouse/t275-a2-gap-capture:.softhouse/handoff/…/T275.md
cat sql/q2-product-mapping-rows.sql                                    (claim 2 — no m.id)
curl -sk …/actuator/health                                             (200; oracle reachable)
docker exec fineract-db-1 psql …                                       (pre-state, fixtures, charge rows, id gaps)
sh evidence/10-run.sh  +  sh evidence/11-run2.sh                        (my own 13-step re-issue, own query)
python3 prove-t275-reissue.py                                          (exit 0, all legs)
  + adversarial A/B/C/D above                                          (exit 1, 1, 0, 0 respectively)
sh evidence/30-reissue-refusals.sh                                     (5/5 byte-identical from wire bytes)
python3 manifest.py verify                                             (exit 0, 1138 files)
python3 guard-parse-float-ast.py                                       (exit 0, 21 sites, 0 violations)
sh capsql.sh with DBC=no-such-container                                (exit 1, handler fires, artefacts intact)
grep -n DEC2Revision nexus/internal/apps/ledger/conformance/admit.go   (51-52)
git show 8e8d65d / ed686d7 --stat ; git log -- docs/adr/DEC-2-…        (rev 6, 7, 8)
sh .softhouse/reviews/t246-dec2-rev6/drive-pin-red.sh                  (exit 0; pin=6/vectors=5 -> 6 inadmissible)
grep -n deleteAll/delete ProductToGLAccountMappingHelper.java          (417, 440 — exact)
grep -n …CODE_VALUE_ID AccountingConstants.java                        (188, 189 — parameter names as cited)
python3 evidence/41-artefact-completeness-sweep.py                     (34 groups, 0 incomplete)
```

**I found no synthesised value, no unreachable handler, no false recipe, and no eleventh
`attempt1-*`.** The one behavioural claim a Go port will be built on — reconcile by key, not
delete-then-recreate — I reproduced myself, with my own query, against the live oracle, and then
found it written in the Fineract source.
