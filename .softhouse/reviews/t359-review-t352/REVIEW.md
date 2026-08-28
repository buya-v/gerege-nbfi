# T359 — independent review of T352 (`softhouse/T352-a2-next-tranche`, head `a67ccbdc`)

Fire `20260828-140005`. Reviewer branch `softhouse/T359-review-t352`. I did not plan T352
and I am not its author.

Oracle **UP and used**: `GET https://localhost:8443/fineract-provider/actuator/health` →
`{"status":"UP","groups":["liveness","readiness"]}`. PostgreSQL reachable
(`docker exec fineract-db-1 psql -U root -d fineract_gerege`). Pinned checkout
`/Users/buv/fineract` at `426a23544e8426a38ae43ae404670a0a7e85b9eb`, re-verified by
`git log -1`.

Bar, run by me on this branch **after** my own probe moved the oracle:
`bash .softhouse/conformance.sh` → **PASS, exit 0**. 46 parity / 0 FAIL, 0 inadmissible,
0 harness errors, ledger parity 7 == 7, oracle-refusal 6 == 6, money cells 39 == 39, 13/13
wrong ledger implementations died. Nine `exemption census READ` lines were confirmed
**PRINTED** before any value was read (P-83): `grep -c "exemption census READ"` = 9.
`out/T359-BAR.log`.

---

## THE SENTENCE THE DRIVER ASKED FOR

**G-19 was raised on a SOUND FACTUAL PREMISE — I re-derived the central claim against the
live oracle with my own transaction and it holds exactly — but its SECOND finding, the one
the gate says "may matter more than the first", is DIAGNOSED WRONGLY, and G-19 must not go
to Buyan carrying it as written.**

The first half is right and I strengthened it. The second half — "the vector schema cannot
represent the divergence", generalised in the gate to "the corpus is green partly because it
only admits shapes it can already represent" — is **false as stated**. The store already
carries the exact polarity (oracle accepts / port refuses) on four live vectors and five
registered wrong implementations, and the `HARNESS-ERROR` T352 drove is caused by **one line
of port code choosing the error return over the refusal return**, not by the schema. See
**F-T359-1**.

## VERDICT: **ACCEPT-WITH-CONDITIONS**

T352 did real, careful, honest work. It refuted its own brief correctly, it declined to
promote a vector it could not honestly promote, it stated its own limit on the residue
observation without being asked, and it declined a cheap accrual probe for a stated and
verifiable reason. Its central claim survives an independent probe. But three things must be
corrected before the gate reaches Buyan, and two of them are in the driver's own text.

**Conditions (all discharged by edits to `.softhouse/gates.md` § G-19, the T352 handoff and
`ORACLE-STATE-MOVED-BY-T352.md` — no vector, no bar movement, no `nexus/` change):**

- **C-1 — REWRITE G-19's second finding.** F-T359-1. Delete "the vector schema cannot
  represent the divergence" and "the corpus is green partly because it only admits shapes it
  can already represent". Replace with the measured cause: `impl.go:277-279` routes the
  residue refusal down `PostEntry`'s `error` return; `grade.go:539-543` converts any error to
  `HARNESS-ERROR` before the comparator runs; the same byte-identical candidate grades as a
  definite **FAIL, exit 1** if the refusal is returned as `(*Refusal, nil)` instead. The real
  schema gap is narrower and must be named as such (F-T359-1 §"what the real gap is").
- **C-2 — PUBLISH THE BLAST RADIUS.** F-T359-5. The declared radius is one item, that item's
  path does not exist, and the file it meant carries no MNT assertion. Two fail-closed rigs
  are now guaranteed to refuse. Nothing on `main` records that the oracle moved at all.
- **C-3 — SAY WHAT (a) COSTS AND WHAT IT ALREADY IS.** F-T359-7 and F-T359-8. DEC-2 §4.3
  normative consequence 2 **already ratifies option (a)**; and the caveat G-19 states in one
  sentence and then ignores is the difference between "(a) is free" and "(a) is a
  parallel-run hazard".

Nothing here blocks the program, and nothing here should stop the gate being put to Buyan —
it should stop it being put *as currently worded*.

---

# FINDINGS

## F-T359-1 — **MAJOR.** The schema CAN represent the divergence. The blocker is one line of PORT code, and the gate's generalisation is unsupported.

This is the finding the review exists for, because G-19 says this half "may matter more than
the first" and it is what `T360` was filed on.

**What T352 claimed** (handoff §4, quoted into G-19): *"`expect.legs[].amount_minor` must be
an int64 count of minor units (`admit.go:868`) … No int64 equals 100.125. The vector is
unrepresentable, and the harness is right to error rather than grade."*

**Reproduced first, then diagnosed.** The `HARNESS-ERROR` is real: extracting T352's banked
`red-drive/LDG-T352-CANDIDATE-residue-3dp.json.NOT-PROMOTED` into a scratch store and running
both the Go binary and `bash conformance.sh` reproduces, verbatim, `HARNESS-ERROR`, `exit 2`,
`ledger harness errors 1`, with the leg-0 residue message. Logs: `schema-drive/runA-baseline.log`,
`schema-drive/runA-candidate.log`, `schema-drive/runB-conformance-sh.log`. `admit.go:868` is
cited exactly; the field is declared `AmountMinor string` at `vector.go:535` and parsed to
`ledger.MinorUnits` (`type MinorUnits int64`, `money.go:86`) by `parseMinor`, so "must be an
int64" is true of the **graded value**, not the schema field — a small imprecision, not the
defect.

**The defect is the diagnosis. Three things falsify it, each read by me in the source:**

1. **The polarity already exists in the comparator.** `nexus/internal/apps/ledger/conformance/grade.go:551-556`:
   ```go
   if refusal != nil {
       s.diffs = append(s.diffs, fmt.Sprintf(
           "the implementation REFUSED a request the oracle ACCEPTED (HTTP %d %s): %s",
           refusal.HTTPStatus, refusal.Code, refusal.Message))
       s.cmpInt("leg_count", int64(len(v.Expect.Legs)), 0)
   ```
   On this path `diffEntry` is never called, so **`amount_minor` is never compared** — the
   int64 constraint T352 names as the cause is not load-bearing at grading time. The cell is
   `leg_count`, an integer.
2. **The store already uses it.** `LDG-06-postclosure-entry-accepted-one-day-after-closing-date.json`
   and `LDG-07-entry-on-the-business-date-accepted.json` quote that comparator sentence
   verbatim in their own notes; `LDG-04` and `LDG-05` are the same accepted-by-oracle class.
   Five registered wrong implementations are built on the polarity — the bar's own output on
   my run kills `ledger-wrong-header-refusing`, `ledger-wrong-openingbalance-always-refusing`,
   `ledger-wrong-date-rules-always-refusing` and others exactly that way (`out/T359-BAR.log`).
3. **`HARNESS-ERROR` is the port's routing choice, and the interface says so in terms.**
   `impl.go:36-44`:
   > *"A refusal is returned as `(*Refusal, nil)` rather than as an error … A returned error
   > means the implementation could not answer at all, which is a HARNESS-ERROR outcome and
   > never a pass."*

   And `impl.go:276-279` sends the residue refusal down the **error** leg:
   ```go
   amt, cerr := ledger.MinorUnitsFromDecimalText(l.AmountMajorText, req.Currency.MinorUnitDigits)
   if cerr != nil {
       return PostedEntry{}, nil, fmt.Errorf("leg %d: %w", i, cerr)
   }
   ```
   `grade.go:539-543` then turns that into `OutcomeError` before the switch at `:547` is ever
   reached.

**Measured, not argued.** In a `/tmp` copy of the repo — never in the worktree, never in
`nexus/` — the single return at `impl.go:276-279` was changed to hand the *identical* message
back as a `*Refusal`. The candidate vector file was **byte-identical**, `amount_minor: "10013"`
and all. Result (`schema-drive/runD-patched.log`):
```
LDG-T352-CANDIDATE-residue-3dp   parity  ledger_rest_posting  FAIL  1 cells (0 money)
    the implementation REFUSED a request the oracle ACCEPTED (HTTP 422 …): ledger: monetary
    text "100.125000" carries sub-minor-unit residue at scale 2 …
ledger parity PASS 7 FAIL 1 ; ledger harness errors 0 ; EXIT=1
```
The divergence grades as a definite, reproducible red **with no schema change whatsoever**.

**What the real gap is, since "not found" must be a statement about the search.** There *is*
a genuine schema gap and T352 did not name it. To author that vector at all you must write
*some* `amount_minor`, and none is correct — T352 wrote `10013`, a number neither system
produced. The ledger schema has **no sentinel for an unknowable money cell** and **no
recorded-but-never-graded decimal observation**. The loanschedule schema has both:
`UnrecordedFields` at `nexus/internal/apps/loanschedule/conformance/vector.go:408` and
`RateFactorObservation` at `:449`. The ledger's only withdrawal mechanism is `ExcludedFields`,
closed by `admit.go:111-115` to the single member `"gl_account_type"`. **That** is the finding
worth a task. It is not "the corpus only admits shapes it can already represent" — the
corpus's machinery is built around the opposite discipline.

**Consequence for G-19 and T360.** The gate's second finding, and the claim-limit written into
it, are wrong as stated. Both must be re-scoped to the routing decision plus the sentinel gap.

## F-T359-2 — **MINOR.** `FU-T352-1`'s own suggested remedy cannot work.

`FU-T352-1` offers, as one of two routes, *"a declared over-scaled-money class as the
loanschedule corpus already has"*. The class is real, but it **refuses non-zero excess digits
by construction** [VERIFIED: `nexus/internal/apps/loanschedule/conformance/admit.go:869-886`
— *"If any extra digit is non-zero the value is an INTERMEDIATE that escaped rounding and
belongs in a decimal observation, never in a money column"*; declared at
`loanschedule/conformance/vector.go:410-432`]. `100.125000` has a non-zero excess digit. The
remedy T352 names would refuse the very vector it is proposed for. The *other* loanschedule
mechanism — the decimal observation the message itself points at — is the right precedent, and
is what F-T359-1 recommends.

## F-T359-3 — **POSITIVE. The central claim survives an independent probe, and T352's rounding attribution is now demonstrated rather than inferred.**

**My own probe, my own value, my own comment string.** `POST /journalentries`, MNT, debit gl 16
/ credit gl 21, **`300.6255545`** — chosen so the digit kept at scale 6 is `4` (EVEN) and the
residue is exactly half, which separates HALF_UP (`300.625555`) from **both** HALF_EVEN and
truncation (`300.625554`). T352's `100.1234565` cuts after an even digit too but is a different
value, so agreement is a re-derivation and not a replay.

- **HTTP 200**, txn `a29bd5eaeb1b` (`out/T359-P03-residue-post.json`, wire bytes
  `out/T359-P03-residue-post.req`, sha256 recorded by the transport).
- REST readback: **`"amount": 300.625555`** with the response's own
  `"currency":{"code":"MNT",…,"decimalPlaces":2}` (`out/T359-P04-residue-readback.json`).
- Database: ids 74/75, `amount 300.625555`, `scale(amount) = 6`, column
  `numeric, precision 19, scale 6` (`out/T359-Q5-my-probe-and-attribution.txt`,
  `out/T359-Q2-column-currency.txt`).

**So the oracle accepts a sub-minor-unit residue in a 2-minor-digit currency, does not round
it to the minor unit, and serves it back. Independently confirmed.** And read-only against the
live database, all four of T352's transactions exist with exactly the amounts, scales and
currencies it reported (`out/T359-Q1-t352-txns.txt`); before T352 there were **zero** legs in
the whole tenant with a trimmed scale above 2 (`out/T359-Q2-column-currency.txt` — six now, all
T352's).

**The attribution, which T352 could only infer, is now positive.** T352 said the
`100.1234565 → 100.123457` rounding is PostgreSQL's `numeric(19,6)` coercion and **may not** be
cited as witnessing `MoneyHelper`'s ratified HALF_UP, reasoning from a source *absence*. I asked
the engine directly, with no Java anywhere in the path
(`sql/t359-q5-my-probe-and-attribution.sql`, output in `out/`):

```
 t359_probe_coerced | t352_probe_coerced | negative_coerced | what_half_even_would_give
         300.625555 |         100.123457 |      -300.625555 |                300.625554
```

**PostgreSQL alone reproduces both stored values exactly.** T352's attribution is correct and
is now demonstrated, not inferred. Two refinements: HALF_EVEN and truncation are both refuted
by my probe as well as T352's; and T352's remark that *"a positive-amount probe cannot separate
them and this corpus posts no negative leg"* is moot — PostgreSQL rounds half **away from zero**
on negatives too (`-300.625555` above), exactly as Java `HALF_UP` does, so **no** probe of
either sign could separate them. The separation is only available from source, which is the
route T352 in fact took.

## F-T359-4 — **MODERATE (P-22).** T352's own oracle-state record is internally inconsistent at gl 21, and the wrong column is the inherited one.

`ORACLE-STATE-MOVED-BY-T352.md` tabulates gl 21 as **7 → 12**. T352 wrote **four** legs to gl 21
(one in each of its four transactions — confirmed row by row, `out/T359-Q4-gl21-forensics.txt`).
7 + 4 = 11, not 12.

Re-derived rather than inherited: the ledger is append-only, so counting gl 21's legs excluding
T352's four transaction ids gives the pre-T352 count. It is **8**
(`out/T359-Q3-account-counts.txt`: `legs_now 12 / legs_excluding_t352 8`), and the eight rows are
ids 35, 37, 40, 42, 44, 47, 49, 52, all created 2026-08-22 02:14–02:21 by A2-26. gl 16 (16 → 20)
and gl 17 (4 → 5) reconcile exactly.

The table's own header says the "before" column is *"T242's measurement"* — so T352 **inherited**
a figure instead of measuring it, in the same file whose stated purpose is *"the difference
between a moved baseline and an unexplained discrepancy"*, and in the same handoff that
(correctly, §5) criticises the T248/T258/T340 restatement-rot mechanism. `7` is reachable only as
a transient during A2-26's own 02:21 batch, between ids 49 and 52.

**gl 18 → 0 and gl 22 → 0 — the pair the accrual argument actually rests on — CONFIRMED
unmoved**, and by T359 too: `GROUP BY account_id` over 16, 17, 18, 21, 22 returns no row for 18
or 22 at all, before or after my probe.

## F-T359-5 — **MAJOR (process).** The declared blast radius is INCOMPLETE, and its single item is mis-cited twice over.

T352 declares exactly one downstream casualty: *"A2-15's `sql/q4-a2-26-ledger-state.sql`
assertion that every row is MNT is now false."*

- **The path does not exist.** `.softhouse/reviews/A2-15/sql/q4-a2-26-ledger-state.sql` — no such
  file (`ls`, and a repo-wide `find` returns only
  `.softhouse/capture/tierA-a2/sql/q4-a2-26-ledger-state.sql`).
- **The file it meant makes no such assertion.** `grep -i 'currency\|MNT'` over
  `.softhouse/capture/tierA-a2/sql/q4-a2-26-ledger-state.sql` returns two lines: `:23` projects
  `j.currency_code` as a column, `:30` is an `\echo` about minor units. There is no
  currency predicate in it. (T352 inherited this citation from `capabilities-ledger.json`'s own
  A2-15 text without checking it — the rot mechanism it names elsewhere.)
- **The real site is elsewhere and is digest-pinned.** The live MNT assertion is
  `.softhouse/capture/tierA-a2/sql/q7-a2-15-ledger-state-json.sql:74-75`
  (`SELECT json_agg(DISTINCT currency_code) FROM acc_gl_journal_entry`), and its committed output
  `.softhouse/capture/tierA-a2/out/A2-390-db-ledger-state-a2-15.json:109` reads
  `"distinct_currency_codes" : ["MNT"]` — **pinned by digest** at
  `.softhouse/capture/tierA-a2/MANIFEST.sha256:447` (`d694d558…`) and cited as the
  `ledger_db_readback` provenance of `LDG-04-header-account-accepted.json`.

**And six further artefacts are affected, two of them fail-closed.** Live counters now read
`acc_gl_journal_entry = 71/75`, `distinct_transaction_id = 31`, currencies `MNT, USD`
(`out/T359-Q5-…txt`; they were `69/73`/`30` after T352 and `60/64`/`26` before it):

| artefact | what breaks |
|---|---|
| `.softhouse/capture/t305-openingbalance-accepting-side/throwaway/out/STANDING-baseline.txt:20,22` and `.softhouse/capture/t327-closure-accepting-side/throwaway/out/STANDING-baseline.txt:20,22` | pin `60/64` and `26`, compared by **string equality** and refused at `t305/throwaway/capture.sh:77`, `capture2.sh:59`, `down.sh:52`, `t327/throwaway/capture.sh:82`, `down.sh:54` — *"F5 … STANDING ORACLE MOVED"*. **Both rigs fail closed on their next run.** |
| `.softhouse/observations/20260827-chain2-standing-oracle-baseline.md:21` | the **driver's own** independent baseline, written so a capture task's "I did not move the oracle" is checkable against a figure it did not supply |
| `.softhouse/reference-oracle.md:907, 917, 1001` | `acc_gl_journal_entry` recorded as 60 rows / max id 64, *"never moved"* — the file every capture task reads to learn the current state |
| `.softhouse/vectors/capabilities-ledger.json` | corrected by T352 **on its branch** in house style (original sentence retained, correction appended: *"WAS TRUE WHEN WRITTEN AND IS NOW FALSE"*; `gl 16 → SIXTEEN` restated to TWENTY). Verified — but **unmerged**, so on `main` the harness still prints falsified live-derived facts on every green run |

**The structural point.** `eca270a9` on `main` touched only `gates.md` and `tasks.json`.
`ORACLE-STATE-MOVED-BY-T352.md` lives on an unmerged branch. So **as of right now, nothing a
future capture task would read records that the reference oracle moved at all** — the precise
condition the T276 precedent was created to prevent. T359 adds its own
`ORACLE-STATE-MOVED-BY-T359.md`; both need to reach `main`, and the two `STANDING-baseline.txt`
files need re-baselining with a note saying which task moved them and why.

## F-T359-6 — **MODERATE (G-19 wording, driver's text).** "The Go port refuses it" is stronger than what was measured.

G-19 says: *"The oracle neither refuses the sub-minor-unit residue nor rounds it away. **The Go
port refuses it.** Port and reference oracle demonstrably diverge on this input."*

T352 was precise — it named the function. The gate dropped the name, and the sentence now
invites the reading that a live Go endpoint rejects a POST. It does not, because there is no such
endpoint: `grep -rn 'MinorUnitsFromDecimalText' --include='*.go' nexus/` returns exactly **two
non-test call sites**, both inside the conformance reference implementation —
`nexus/internal/apps/ledger/conformance/impl.go:261` and `:276`. `money.go:178-181` says the write
path *"belongs to slice A1"*, and it does not exist yet.

**The refusal is real and is for the reason claimed** — I re-derived it rather than reading the
comment. Running the port's converter over the oracle's own readback characters, on a copy of
`nexus/internal/apps/ledger/money.go` verified byte-identical by sha256
(`bd919399ada4ed1cd82155f30a97f398a8bf8b95512810857851375cb9974da4`), gives
(`out/T359-PORT-01-money-reader.txt`):

```
REFUSED  100.125000   scale=2   … carries sub-minor-unit residue at scale 2 (digit "5" beyond 2 decimal places) …
REFUSED  0.125000     scale=2   … (digit "5" …) …
REFUSED  100.123457   scale=2   … (digit "3" …) …
ACCEPTED 0.250000     scale=2   -> 25 minor units
ACCEPTED 12.340000    scale=2   -> 1234 minor units
ACCEPTED 1200000.000000 scale=2 -> 120000000 minor units
```

Not a validation-ordering artefact, not a parse error, not a missing field: the controls convert.
The refusal fires at `money.go:144-151`, the residue branch, exactly as claimed.

**Why the wording still matters.** What diverges is the port's **money reader**, on the oracle's
**own output**. Read that way the divergence is if anything *more* serious than a rejected input —
it says the port cannot ingest what the reference implementation emits — and Buyan should be told
that, not a picture of two endpoints disagreeing. G-19 should name the function and say there is
no Go write path yet.

## F-T359-7 — **MODERATE (G-19).** The gate states its own caveat and then reasons as if it did not exist; and the question cannot be answered from this context at all.

G-19 states the limit correctly: *"the third decimal was supplied by the prober … This is 'the
oracle accepts residue', not yet 'the oracle produces residue'."* Then it demotes it to *"would
strengthen it and does not block it"*, and recommends **(a)** on a rationale that never engages
with it. **The caveat is load-bearing, and the gate understates its weight:**

- If the oracle only ever *accepts* supplied residue, (a) costs nothing operationally — the
  refusal is input validation at the adapter boundary and no oracle output ever trips it.
- If the oracle's own arithmetic *generates* residue, (a) means **the port refuses to read the
  reference implementation's own output during a parallel run**, and the parity corpus can grade
  no such entry. That is a cutover hazard, not a policy footnote.

**And it cannot be settled here — by construction, not for want of effort.** The manual
journal-entry seam performs **no arithmetic on the amount at all**. Traced end to end at the pin:
`JournalEntryCommandFromApiJsonDeserializer.java:81,128` →
`fromApiJsonHelper.extractBigDecimalNamed` → `JsonParserHelper.java:152`
(`primitive.getAsBigDecimal()`, exact from the characters, no double) →
`SingleDebitOrCreditEntryCommand.amount` → `checkDebitAndCreditAmounts`
(`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:306-326`, `add` and `compareTo` only, and
its sum is never stored) → `saveAllDebitOrCreditEntries` (`:674-676`, the command's amount handed
straight to `JournalEntry.createNew`) → `@Column(name = "amount", scale = 6, precision = 19)`
(`JournalEntry.java:91`). **No computation on this path ever writes an amount**, so no probe at
`ledger_rest_posting` can ever observe the oracle generating residue. `FU-T352-2` therefore belongs
to a seam that computes — loan schedule, interest, charges — and CLAUDE.md's one-bounded-context
scope guard means it cannot be worked under `tierA-gl-accounting`. G-19's "what unblocks it"
section should say so, or a future fire will scope it into the ledger context and it will produce
nothing.

## F-T359-8 — **MODERATE (G-19, procedural).** DEC-2 already ratifies option (a), and §6.6 already rules on `FU-T352-2`.

G-19 asks Buyan to *"Amend **DEC-2** to state which of these is the ratified position"*, and offers
(a) *"the port's refusal is CORRECT and stands"* as the driver's recommendation. **DEC-2 already
says exactly that**, as ratified normative text:

> **`docs/adr/DEC-2-gl-accounting-adapter.md:971-976`**, §4.3 "Money representation", normative
> consequence 2: *"**Refuse residue; do not truncate and do not round.** Predicate **G-08**: a wire
> text carrying a non-zero digit beyond the currency's minor unit is **`ErrInvalidRequest`**, not a
> value."*

and the predicate is in the §4.2 graded-domain table at `:834`. Nothing T352 observed falsifies
that rule, or any other DEC-2 sentence I could find: `:851` and `:2649` scope their MNT statements
to *the corpus*, which is still all-MNT because nothing was promoted.

So raising the gate is **procedurally defensible** — any text change to a ratified DEC-n needs
Buyan, and (a) does need the *rationale* reworded, since "no vector proves the truncation rule"
(`:975-976`) was written under an ignorance that no longer holds. But Buyan should be told the
decision is **cheap and mostly confirmatory**: choosing (a) changes no normative rule; only (b) and
(c) are real amendments.

**Related, and T352 got it backwards.** `FU-T352-2` asserts *"Widening [G-07's MNT pin] is a DEC-2
amendment."* DEC-2 anticipated a second currency and ruled the opposite:
`docs/adr/DEC-2-gl-accounting-adapter.md:2644-2653`, §6.6 — *"It is a **value-domain widening, not
a shape change**, so it is not an amendment."* `FU-T352-2` must at minimum cite §6.6 and say why it
disagrees. T352's underlying observation is sound and I verified it: USD is 2 legs / 1 transaction,
the only non-MNT rows in the tenant (`out/T359-Q2-column-currency.txt`), and G-07's pin is enforced
in the store at `nexus/internal/apps/ledger/conformance/admit.go:156-162`, whose own message —
*"the only currency any captured journal entry is denominated in"* — is now the falsified part.

## F-T359-9 — **POSITIVE.** The transport is byte-identical to the audited chain. Verified by digest, with one limit stated.

T270 graded `.softhouse/reviews/A2-11/resolve7.py` a MATERIAL P-25 float site on an evidence
transport, so this had to be checked rather than accepted. Extracting T352's three scripts from its
branch and hashing them against `.softhouse/capture/tierA-a2/`:

```
6db87360002d3f3e4d4a7a7810e55eaff9af7f95dd91ebd9acdd6a17f4c46cf3  cap11.sh   == cap10.sh
faf58253b95a3dfa75c87785f26b21fee31fc8039499a193e71c700691304c9a  capsql.sh  == capsql.sh
6fdd81ea9990b37edf74cbda22cff261c5052237182a381067441cd2429d1d7b  env.sh     == env.sh
```

All three **byte-identical**, and the digests match T352's own stated values to the character.
`cap10.sh` is the current head of the audited chain `cap.sh → cap8.sh → cap9.sh → cap10.sh`
(`.softhouse/capture/tierA-a2/SUPERSEDED.txt`). Both are pure `sh` + `curl`/`psql`; neither contains
`json.load`, `json.dumps` or any numeric parse; `cap10.sh` sends with `--data-binary` and commits
`out/NAME.req` + sha256 as the wire bytes. **I used the same three scripts for my own probe**,
copied and re-hashed identical into `.softhouse/reviews/t359-review-t352/`.

**Limit, stated because P-22 requires the measurement to be mine.** I could **not** reproduce
T352's *"530 documents / 372 float-shaped tokens / ALTERED 0"* census figure. The census population
is derived from `.softhouse/capture/**` (`conformance.sh:1250-1262`), T352's rig is on an unmerged
branch, and my bar run therefore reports the untouched baseline `522 documents / 354 tokens /
ALTERED 0` (`out/T359-BAR.log:6-7`). T352's figure is self-consistent with its own logs and the
floor is a derived `>=`, not a pin, so I have no reason to doubt it — but I did not re-measure it,
and **the same limit applies to my own captures**: they live under `.softhouse/reviews/`, which the
census does not scan, so nothing automatic has inspected them either. Both are read-only-verifiable
by hand: every request body in `req/` is hand-typed literal JSON and `out/*.req` are the exact wire
bytes.

## F-T359-10 — **MINOR (P-45 / P-86).** The grep behind "no `setScale`, no `RoundingMode` anywhere" was narrower than the claim. The claim survives a wider sweep.

T352 wrote, and G-19 repeats without any scope at all: *"Confirmed in the journal-entry package: no
`setScale`, no `RoundingMode` anywhere."* The cited grep covers only
`fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/` — **39 files**,
which is the service implementation and **not** the entity, the commands or the deserializer. Those
live in a different Gradle module: `fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/`.

I swept all four journal-entry source packages at `426a23544` and the deserializer's own conversion
path. **Nothing found, and here is where I looked:**

| package | files | `setScale|RoundingMode|MathContext|MoneyHelper` |
|---|---|---|
| `fineract-provider/…/accounting/journalentry/` | 39 | none (T352's grep, reproduced) |
| `fineract-accounting/…/accounting/journalentry/` | 22 | none |
| `fineract-core/…/accounting/journalentry/` | — | none |
| `fineract-investor/…/investor/accounting/journalentry/` | — | none |

plus `JsonParserHelper.java:142-163` — the JSON number path is `primitive.getAsBigDecimal()`, exact
from the characters. (Noted in passing, not a defect here: `JsonParserHelper.java:737` has a
`BigDecimal.valueOf(parsedNumber.doubleValue())` fallback, reachable only for a **quoted** numeric
string whose locale parse does not yield a `BigDecimal`. The residue probes send bare JSON numbers
and do not reach it. Worth a follow-up for any future capture that quotes an amount.)

**Verdict: claim upheld, evidence widened.** But as filed, the *evidence* was narrower than the
*claim*, and the gate restates the claim with no scope, on a path that reaches a `@Column(scale = 6,
precision = 19)` annotation the cited grep could not have seen.

## F-T359-11 — **MINOR (P-45).** `FU-T352-4`'s logic is SOUND; two of its three citations are stale.

The refutation itself holds. `EXEMPTION_PIN_LEDGER_PARITY=7`, `_REFUSAL=6`,
`_MONEYCELLS=39` are literals at `.softhouse/conformance.sh:681-683` — **confirmed exactly** — and
they are compared by strict equality (`_cmp` uses `-eq`, defined at `:3399-3406`), with the failure
text at `:3487-3488` quoted word for word. The pins read PASS counts out of the graded report
(`:3448-3459`) and map one-to-one onto the 7 + 6 vector files in `.softhouse/vectors/ledger/`, so
**any** new ledger vector does move a pin. `FU-T352-4` is right and should be actioned.

Two corrections:

- **The comparison sites are at `:3469-3471`, not `:3160-3162`.** `:3160-3162` is the correct
  numbering for the tree *before* the T323 merge (`74ed1253^1`); T323 inserted +309 lines above the
  block. The pin declarations at 681-683 survived the shift; the comparisons did not. A driver
  acting on `:3160-3162` today lands in an unrelated guard.
- **T323 is already merged into `main`.** `git diff main...softhouse/T323-wire-unwired-guards --
  .softhouse/conformance.sh` — T352's cited witness — returns **empty**. Against the correct base the
  hunks are exactly `@@ -2464`, `@@ -2955`, `@@ -2985` as T352 reports, and its conclusion (none near
  line 681) is right.
- **Refinement.** T352 treats the three pins as one bundle. A new **oracle-refusal** vector moves
  `_REFUSAL` but **not** `_MONEYCELLS` — `diffRefusal` reaches only `cmpInt`/`cmpStr`, never
  `cmpMoney` (`conformance.sh:667-673`). Only a parity vector with money cells moves both.

## F-T359-12 — **CONFIRMED, and T352 understated it.** The `ledger.accrual.entry` row's reason really is FALSE.

Re-derived against the live database (`out/T359-Q6-accrual-claims.txt`):

- **Jobs.** `Add Accrual Transactions` (11) and `…For Loans With Income Posted As Transactions` (22)
  active, last run `2026-08-27 16:01`; `Add Periodic Accrual Transactions` (16) active, last run
  `2026-08-27 16:02`. **Exactly as T352 reported.** COB jobs 33 and 34 inactive with null
  `previous_run_start_time` — also exactly as reported. So *"no accrual or COB job has ever run"* is
  false on the accrual half and true on the COB half, precisely as T352 split it.
  **Understated:** two further accrual jobs, 39 (`Accrual Activity Posting`) and 42 (`Add Accrual
  Transactions For Savings`), are inactive but **have run** (`2026-08-18 16:01`). Five accrual jobs
  have run, not three.
- **Product 28.** `accounting_type = 3` and the **only** row in `m_product_loan` with that value —
  confirmed across all 33 products. All thirteen `financial_account_type` slots 1..13 mapped,
  including **7 → gl 18, 8 → gl 22, 9 → gl 16**, character for character. A `LEFT JOIN` over every
  product confirms **zero loans** on 28. So *"needs a NEW accrual product PLUS a job run"* is indeed
  overstated: the periodic job is already live and the missing ingredient is a loan.
- **The stated reason for not firing it holds.** Slot 9 → gl 16, and gl 16 **is** a promoted leg of
  LDG-01, LDG-02 and LDG-03 [VERIFIED: `"gl_account_id": 16` at
  `LDG-01-…json:74,95`, `LDG-02-…json:97,138`, `LDG-03-…json:97,138`].

## F-T359-13 — **MINOR (judgement).** The cost/benefit test T352 used to decline the accrual probe was not applied to the four probes it fired.

T352 declined the accrual probe partly because it would post *"into an account three graded vectors
read … for evidence that cannot be promoted anyway"*. It then posted **eight legs into that same
gl 16 and into gl 21**, for evidence that (§4) also could not be promoted. The two probes are not
equivalent — the residue probes discharged a standing `[UNVERIFIED]` that `money.go:71-81` explicitly
asked a future fire to settle, which is a far higher return — so I do not grade this a defect. But
the asymmetry should have been stated rather than left for a reviewer, and the *real* reason the
accrual probe was rightly declined is the one T352 gives second: product 28's mapping is inadmissible
(A2-314, 403), so the evidence would be unusable on its own terms.

**On whether firing at all was the right call: yes.** The probes were cheap, permanent, honest and
answered a question the port's own source had been asking in writing for weeks. What was *not* right
was landing them without publishing the blast radius (F-T359-5) — and I hold myself to the same
standard: `ORACLE-STATE-MOVED-BY-T359.md` records my one transaction and lists what it breaks.

---

## WHAT I CHECKED AND FOUND NOTHING WRONG WITH

Recorded so "not found" is a statement about the search.

- **The balance-check-at-full-scale claim (§3.2).** Both halves hold. `checkDebitAndCreditAmounts`
  (`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:306-326`) sums raw `BigDecimal`s with
  `add` and compares with `compareTo`; there is no scaling anywhere on the path. And the row is in
  the database: `a29bca9bf813` = `0.125000 + 0.125000` debit against `0.250000` credit, all at scale
  6, HTTP 200 (`out/T359-Q1-t352-txns.txt`). Per-leg HALF_UP would give `0.13 + 0.13 = 0.26` and
  `DEBIT_CREDIT_SUM_MISMATCH`. I did **not** re-fire this probe — the row already exists and re-firing
  would move shared state for no new information.
- **The multi-currency inexpressibility argument (§3.3).** Citations exact:
  `SingleDebitOrCreditEntryCommand.java:33-35` carries `glAccountId`, `amount`, `comments` and no
  currency; `JournalEntryCommand.java:40` holds `currencyCode` as a single scalar on the enclosing
  command. A leg genuinely cannot name a currency at this seam.
- **The `numeric(19,6)` column.** `information_schema`: `numeric`, precision 19, scale 6
  (`out/T359-Q2-column-currency.txt`), matching `JournalEntry.java:91`'s
  `@Column(name = "amount", scale = 6, precision = 19, nullable = false)`.
- **"No pin was moved / nothing promoted."** T352's diff touches exactly one file outside its own
  capture directory — `.softhouse/vectors/capabilities-ledger.json` — and no file was added under
  `.softhouse/vectors/ledger/`. The candidate is banked with a `.NOT-PROMOTED` suffix so it cannot
  load. My bar run confirms 7 == 7, 6 == 6, 39 == 39.
- **"The harness does not read the oracle's database when it renders a report."** Positively tested:
  I ran the full bar **after** my probe moved the ledger and it is PASS, exit 0, with every ledger
  figure unchanged.
- **P-80, this deliverable against its own rules.** No vector promoted; no `nexus/` file, no
  `.softhouse/conformance.sh`, no `.softhouse/bin/fire-program.sh`, no `.softhouse/vectors/**` and no
  `.softhouse/reviews/A2-11/` byte modified — the `impl.go` experiment in F-T359-1 exists only in a
  `/tmp` copy. Money touched in this review is integer minor units or the oracle's own literal
  characters; no float type appears in any script, query or Go file I wrote. The one Go program I ran
  (`portprobe/`) takes only string literals and prints `int64`. Oracle state I moved is recorded in
  `ORACLE-STATE-MOVED-BY-T359.md`.

## ARTEFACTS

All under `.softhouse/reviews/t359-review-t352/`.

| file | what it is |
|---|---|
| `ORACLE-STATE-MOVED-BY-T359.md` | the one transaction I wrote, the counters after it, and what it breaks |
| `cap10.sh` / `capsql.sh` / `env.sh` | the audited transport, copied and re-hashed identical |
| `req/T359-R01..R03-*.json` | hand-typed request bodies (R01/R02 were refused on comment length) |
| `sql/t359-q1..q6-*.sql` | the six queries, committed as executed by `capsql.sh` |
| `out/T359-Q1..Q6-*` | psql output, query bytes, digests and `.psql` records |
| `out/T359-P01..P04-*` | HTTP captures: two 400s, the accepted POST, the REST readback |
| `out/T359-PORT-01-money-reader.txt` | the port's converter run against the oracle's own characters |
| `out/T359-BAR.log` | the full conformance run, PASS exit 0 |
| `portprobe/` | the standalone module used for `out/T359-PORT-01`, with `money.go` sha256-verified against `nexus/` |
| `schema-drive/` | the F-T359-1 reproduction: T352's extracted candidate plus runs A (baseline/candidate), B (`conformance.sh`), C (wrong-impl polarity), D (patched routing) |
